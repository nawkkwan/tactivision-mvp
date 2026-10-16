import json

from PIL import Image
import pytest

from training import test_round2_candidates as candidate


def test_saved_yolo_predictions_are_restored_to_pixels(tmp_path):
    path = tmp_path / "predictions.txt"
    path.write_text("2 0.5 0.5 0.2 0.4 0.75\n")
    assert candidate.read_predictions(path, 100, 50) == [
        {"class_id": 2, "confidence": .75, "xyxy": [40., 15., 60., 35.]}
    ]
    assert candidate.read_predictions(tmp_path / "empty.txt", 100, 50) == []


def test_display_uses_frozen_class_specific_thresholds():
    predictions = [dict(class_id=0, confidence=.15), dict(class_id=0, confidence=.149),
                   dict(class_id=2, confidence=.49), dict(class_id=2, confidence=.50)]
    assert candidate.displayed(predictions) == [predictions[0], predictions[3]]


@pytest.fixture
def input_frames(tmp_path):
    candidates, frozen = tmp_path / "candidates", tmp_path / "frozen"
    candidates.mkdir()
    (frozen / "test/images").mkdir(parents=True)
    (frozen / "test/labels").mkdir()
    records = []
    for index in range(30):
        name = f"idq95Xp5RI0_{index:02}.jpg"
        reference_name = name[:-4] + "_jpg.rf.hash.jpg"
        source = candidates / name
        reference = frozen / "test/images" / reference_name
        label = frozen / "test/labels" / (reference.stem + ".txt")
        Image.new("RGB", (100, 50), (index, 100, 50)).save(source)
        reference.write_bytes(source.read_bytes())
        label.write_text("2 0.5 0.5 0.2 0.4\n")
        records.append(dict(filename=reference_name, label=label.name, width=100, height=50,
                            sha256=candidate.file_sha256(reference), label_sha256=candidate.file_sha256(label)))
    (frozen / "test_manifest.json").write_text(json.dumps(records))
    return candidates, frozen


def test_stage_preserves_candidate_and_frozen_label_bytes(tmp_path, input_frames):
    candidates, frozen = input_frames
    rows = candidate.stage_candidates(candidates, frozen, tmp_path / "run")
    assert len(rows) == 30
    for row in rows:
        name = row["filename"]
        assert (tmp_path / "run/images" / name).read_bytes() == (candidates / name).read_bytes()
        assert candidate.file_sha256(tmp_path / "run/labels" / (name[:-4]+".txt")) == row["label_sha256"]


def test_stage_rejects_changed_labels(tmp_path, input_frames):
    candidates, frozen = input_frames
    next((frozen / "test/labels").glob("*.txt")).write_text("3 0.5 0.5 0.2 0.4\n")
    with pytest.raises(ValueError, match="checksum"):
        candidate.stage_candidates(candidates, frozen, tmp_path / "run")


def test_stage_rejects_different_scene(tmp_path, input_frames):
    candidates, frozen = input_frames
    Image.new("RGB", (100,50), "white").save(next(candidates.glob("*.jpg")))
    with pytest.raises(ValueError, match="does not align"):
        candidate.stage_candidates(candidates, frozen, tmp_path / "run")


def test_stage_rejects_missing_image(tmp_path, input_frames):
    candidates, frozen = input_frames
    next(candidates.glob("*.jpg")).unlink()
    with pytest.raises(ValueError, match="exactly"):
        candidate.stage_candidates(candidates, frozen, tmp_path / "run")
