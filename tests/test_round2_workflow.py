import hashlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from PIL import Image
import numpy as np
import pytest

from training import round2_workflow as workflow


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "COUNTS", {"train": 1, "valid": 2})
    monkeypatch.setattr(workflow, "VALIDATION_GROUP_COUNTS", {"old36": 1, "new35": 1})
    dataset = tmp_path / "dataset"
    rows = []
    for split, origin, name, color, clip in (("train", "frozen", "train.jpg", "green", "PFYsHN24C3k"),
                                          ("valid", "frozen", "old.jpg", "blue", "tJnScrAKJfI"),
                                          ("valid", "new", "new.jpg", "yellow", None)):
        image, label = dataset / split / "images" / name, dataset / split / "labels" / (Path(name).stem + ".txt")
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (100, 50), color).save(image)
        label.write_text("2 0.5 0.5 0.2 0.4\n")
        rows.append(dict(filename=name, split=split, origin=origin, clip=clip, width=100, height=50,
                         sha256=workflow.file_sha256(image), label_sha256=workflow.file_sha256(label)))
    # Held-out images exist in the source prepared directory, but must not be
    # read or packaged. Deliberately use non-image content to detect access.
    (dataset / "test/images").mkdir(parents=True)
    (dataset / "test/images/idq95Xp5RI0.jpg").write_bytes(b"never read me")
    (dataset / "split_manifest.json").write_text(json.dumps(rows + [dict(split="test", filename="idq95Xp5RI0.jpg")]))
    audit = dict(training_ready=True, blocking_issues=[], classes=workflow.EXPECTED,
                 source_zip="original.zip", source_sha256="source-hash", changes=[], note="fixture")
    (dataset / "audit.json").write_text(json.dumps(audit))
    model = tmp_path / "best.pt"
    model.write_bytes(b"round-one-model")
    monkeypatch.setattr(workflow, "INITIAL_SHA256", workflow.file_sha256(model))
    review = tmp_path / "review.json"
    review.write_text("{}")
    return dataset, rows, model, review


def test_bundle_excludes_test_and_can_be_staged_twice(tmp_path, prepared):
    dataset, rows, model, review = prepared
    output = tmp_path / "bundle.zip"
    workflow.build_training_bundle(dataset, model, output, review)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert not any("test" in Path(name).parts for name in archive.namelist())
        assert not any(name.endswith(".py") for name in archive.namelist())
        assert len(json.loads(archive.read("split_manifest.json"))) == 3
    staged, _ = workflow.stage_training_bundle(output, tmp_path / "staged")
    assert len(staged) == 3
    workflow.stage_training_bundle(output, tmp_path / "staged")
    assert not (tmp_path / "staged/test").exists()
    groups, configs = workflow.make_validation_configs(tmp_path / "staged", staged, tmp_path / "groups")
    assert {k: len(v) for k, v in groups.items()} == {"all71": 2, "old36": 1, "new35": 1}
    assert all("test" not in json.loads(path.read_text()) for path in configs.values())


def test_stage_rejects_modified_payload_before_writing(tmp_path, prepared):
    dataset, _, model, review = prepared
    original, broken = tmp_path / "original.zip", tmp_path / "broken.zip"
    workflow.build_training_bundle(dataset, model, original, review)
    with ZipFile(original) as source, ZipFile(broken, "w") as target:
        for name in source.namelist():
            target.writestr(name, b"changed" if name == "valid/labels/old.txt" else source.read(name))
    with pytest.raises(ValueError, match="checksum mismatch"):
        workflow.stage_training_bundle(broken, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_stage_rejects_test_or_unsafe_members(tmp_path, prepared):
    dataset, _, model, review = prepared
    original = tmp_path / "original.zip"
    workflow.build_training_bundle(dataset, model, original, review)
    for index, name in enumerate(("test/images/a.jpg", "../outside.txt", "scripts/run.py")):
        broken = tmp_path / f"bad_{index}.zip"
        with ZipFile(original) as source, ZipFile(broken, "w") as target:
            for member in source.namelist():
                target.writestr(member, source.read(member))
            target.writestr(name, "bad")
        with pytest.raises(ValueError):
            workflow.stage_training_bundle(broken, tmp_path / f"out_{index}")


def test_builder_requires_exact_initial_weights(tmp_path, prepared):
    dataset, _, model, review = prepared
    model.write_bytes(b"some other model")
    with pytest.raises(ValueError, match="round-one best.pt"):
        workflow.build_training_bundle(dataset, model, tmp_path / "bundle.zip", review)


def test_fixed_threshold_counts_wrong_class_duplicates_and_missing():
    truth = [{"class_id": 2, "xyxy": [0, 0, 10, 10]}]
    predictions = [{"class_id": 1, "xyxy": [0, 0, 10, 10], "confidence": .95},
                   {"class_id": 2, "xyxy": [0, 0, 10, 10], "confidence": .3},
                   {"class_id": 2, "xyxy": [0, 0, 10, 10], "confidence": .2}]
    low = workflow.fixed_counts(predictions, truth, .15)
    assert low[1] == dict(tp=0, fp=1, fn=0)
    assert low[2] == dict(tp=1, fp=1, fn=0)
    assert workflow.fixed_counts(predictions, truth, .5)[2] == dict(tp=0, fp=0, fn=1)


def test_metric_summary_uses_real_class_indices():
    box = SimpleNamespace(ap_class_index=[0, 2], p=[.4, .8], r=[.5, .9],
                          ap50=[.3, .7], ap=[.2, .6], mp=.6, mr=.7, map50=.5, map=.4)
    result = workflow.metric_summary(SimpleNamespace(box=box))
    assert result["per_class"]["player"]["mAP50_95"] == .6
    assert result["per_class"]["goalkeeper"] is None


def test_comparison_saves_all_validation_images_without_changing_inputs(tmp_path, prepared):
    dataset, rows, _, _ = prepared
    before, after = tmp_path / "before", tmp_path / "after"
    before.mkdir()
    after.mkdir()
    for row in rows:
        if row["split"] == "valid":
            for directory in (before, after):
                Image.new("RGB", (100, 50), "red").save(directory / row["filename"])
    output = tmp_path / "panels"
    saved = workflow.comparison_panels(dataset, rows, before, after, output)
    assert len(saved) == 2
    assert all(Image.open(path).size == (300, 100) for path in saved)
    workflow.validate_records(dataset, rows)


def test_notebook_helpers_and_cell_syntax_match_source():
    root = Path(__file__).resolve().parents[1]
    notebook = json.loads((root / "training/finetune_round2.ipynb").read_text(encoding="utf-8"))
    helper = next(cell for cell in notebook["cells"] if cell["id"] == "helpers")
    assert "".join(helper["source"]) == (root / "training/round2_workflow.py").read_text(encoding="utf-8")
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and cell["id"] != "install":
            compile("".join(cell["source"]), f"notebook:{cell['id']}", "exec")
    training = "".join(next(cell for cell in notebook["cells"] if cell["id"] == "train")["source"])
    assert "YOLO(str(INITIAL_MODEL))" in training
    assert "resume=False" in training


def test_evaluate_groups_preserves_shared_settings_and_uses_validation(tmp_path):
    metrics = SimpleNamespace(box=SimpleNamespace(ap_class_index=[2], p=[.8], r=[.9], ap50=[.7], ap=[.6],
                                                mp=.8, mr=.9, map50=.7, map=.6))
    calls = []
    class Model:
        def val(self, **kwargs):
            calls.append(kwargs)
            return metrics
    args = dict(split="val", imgsz=1280, conf=.001, iou=.7)
    configs = {"all71": tmp_path / "all.yaml", "old36": tmp_path / "old.yaml", "new35": tmp_path / "new.yaml"}
    scores = workflow.evaluate_groups(Model(), configs, args, tmp_path, "before")
    assert set(scores) == set(configs)
    assert all(all(call[key] == value for key, value in args.items()) for call in calls)
    assert (tmp_path / "before_metrics.json").is_file()


def test_collection_uses_class_specific_display_but_keeps_raw_predictions(tmp_path):
    calls, masks = [], []
    data = np.array([[1, 1, 5, 5, .2, 0], [10, 10, 20, 20, .2, 2],
                     [20, 20, 30, 30, .6, 2], [30, 30, 40, 40, .2, 3]])
    class Result:
        boxes = SimpleNamespace(data=data, conf=data[:, 4], cls=data[:, 5])
        def cpu(self):
            return self
        def __getitem__(self, mask):
            masks.append(mask.tolist())
            return self
        def plot(self, **kwargs):
            return np.zeros((50, 100, 3), dtype=np.uint8)
    class Model:
        names = dict(enumerate(workflow.EXPECTED))
        def predict(self, path, **kwargs):
            calls.append(kwargs)
            return [Result()]
    predictions = workflow.collect_predictions(Model(), [Path("a.jpg"), Path("b.jpg")], tmp_path / "before", imgsz=1280, device="cpu")
    assert len(predictions) == 2 and len(predictions["a.jpg"]) == 4
    assert masks == [[True, False, True, False]] * 2
    assert all(call["conf"] == .15 and call["iou"] == .7 and call["augment"] is False for call in calls)
    assert len(list((tmp_path / "before/rendered").glob("*.jpg"))) == 2


def test_packaged_results_include_model_reports_and_every_panel_not_input_weights(tmp_path):
    run, data_root = tmp_path / "run", tmp_path / "dataset"
    train_dir = run / "finetune_round2"
    model = train_dir / "weights/best.pt"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"round-two-weights")
    (train_dir / "args.yaml").write_text("epochs: 40\n")
    (train_dir / "weights/last.pt").write_bytes(b"do not duplicate this checkpoint")
    for name in ("before_metrics.json", "after_metrics.json", "map_comparison.csv", "fixed_threshold_comparison.csv"):
        (run / name).write_text("fixture")
    data_root.mkdir()
    for name in ("dataset_audit.json", "split_manifest.json", "bundle_manifest.json", "label_review.json", "data.yaml"):
        (data_root / name).write_text("{}")
    (data_root / "initial_model.pt").write_bytes(b"do not include old weights")
    for phase in ("before", "after"):
        (run / phase).mkdir()
        (run / phase / "predictions.json").write_text("{}")
    for directory in ("comparisons", "evaluations", "groups"):
        (run / directory).mkdir()
    for name in ("a.jpg", "b.jpg"):
        Image.new("RGB", (10, 10)).save(run / "comparisons" / name)
    archive_path = workflow.package_results(run, data_root, train_dir, model, {"test_images_used": 0})
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert archive.read("best_round2.pt") == b"round-two-weights"
        assert "comparisons/a.jpg" in archive.namelist() and "comparisons/b.jpg" in archive.namelist()
        assert not any(name.endswith("last.pt") or name.endswith("initial_model.pt") for name in archive.namelist())
        assert json.loads(archive.read("round2_report.json"))["test_images_used"] == 0
