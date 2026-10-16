"""Test ball scoring without loading model weights or running inference."""
import json
from pathlib import Path

from PIL import Image
import pytest

from training.compare_ball_detectors import box_iou, load_validation, metrics, score_balls, sha256


def pred(confidence=.8, box=(0, 0, 10, 10)):
    return {"xyxy": list(box), "confidence": confidence}


def test_duplicate_predictions_match_once():
    counts, matched = score_balls([pred(.8), pred(.9)], [[0, 0, 10, 10]], .15)
    assert counts == dict(tp=1, fp=1, fn=0)
    assert [p["correct"] for p in matched] == [True, False]
    assert matched[0]["confidence"] == .9


def test_confidence_and_iou_boundaries():
    counts, _ = score_balls([pred(.3, (0, 0, 5, 10))], [[0, 0, 10, 10]], .3)
    assert counts == dict(tp=1, fp=0, fn=0)
    counts, _ = score_balls([pred(.29)], [[0, 0, 10, 10]], .3)
    assert counts == dict(tp=0, fp=0, fn=1)
    assert box_iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0


def test_empty_predictions_or_labels():
    assert score_balls([], [[0, 0, 10, 10]], .15)[0] == dict(tp=0, fp=0, fn=1)
    assert score_balls([pred()], [], .15)[0] == dict(tp=0, fp=1, fn=0)
    assert metrics(dict(tp=0, fp=0, fn=0))["f1"] == 0


def test_same_matching_as_previous_notebook():
    notebook = json.loads((Path(__file__).resolve().parents[1] / "training/confidence_sweep.ipynb").read_text(encoding="utf-8"))
    namespace = {}
    exec("".join(next(c for c in notebook["cells"] if c["id"] == "matching")["source"]), namespace)
    predictions = [pred(.15), pred(.3), pred(.5, (30, 30, 40, 40)), pred(.9, (60, 60, 70, 70))]
    truth = [[0, 0, 10, 10], [30, 30, 40, 40], [90, 90, 100, 100]]
    for threshold in (.15, .3, .5):
        expected = namespace["counts_at_threshold"](
            [{**p, "class_id": 0} for p in predictions],
            [{"xyxy": box, "class_id": 0} for box in truth], threshold,
        )[0]
        assert score_balls(predictions, truth, threshold)[0] == expected


@pytest.fixture
def validation_dataset(tmp_path):
    images = tmp_path / "valid/images"
    labels = tmp_path / "valid/labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    manifest = []
    for i in range(36):
        image = images / f"valid_{i}.jpg"
        Image.new("RGB", (100, 50)).save(image)
        (labels / f"valid_{i}.txt").write_text("0 0.5 0.5 0.1 0.2\n2 0.2 0.2 0.1 0.1\n")
        manifest.append(dict(filename=image.name, split="valid", clip="tJnScrAKJfI", sha256=sha256(image)))
    # These records must be ignored; the referenced files deliberately do not exist.
    manifest.extend([dict(filename="absent.jpg", split="train"), dict(filename="absent.jpg", split="test")])
    (tmp_path / "split_manifest.json").write_text(json.dumps(manifest))
    return tmp_path


def test_loader_only_reads_frozen_validation_and_ball_labels(validation_dataset):
    records = load_validation(validation_dataset)
    assert len(records) == 36
    for record in records:
        assert len(record["truth"]) == 1
        assert record["truth"][0] == pytest.approx([45, 20, 55, 30])


def test_loader_rejects_modified_validation_images(validation_dataset):
    (validation_dataset / "valid/images/valid_0.jpg").write_bytes(b"changed image")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_validation(validation_dataset)
