from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
import pytest

from training.prepare_hardcases_export import convert_reviewed_polygons, digest, prepare


LABEL = b"2 0.5 0.5 0.2 0.4\n"


def jpeg(color):
    stream = BytesIO()
    Image.new("RGB", (100, 50), color).save(stream, format="JPEG")
    return stream.getvalue()


def fixture(root, new_label=LABEL, old_test_label=LABEL, extra=None):
    frozen = root / "frozen"
    rows, test_rows = [], []
    old = []
    for split, color in (("train", "green"), ("valid", "blue"), ("test", "red")):
        image = jpeg(color)
        name = f"old_{split}.jpg"
        for kind in ("images", "labels"):
            (frozen / split / kind).mkdir(parents=True)
        (frozen / split / "images" / name).write_bytes(image)
        (frozen / split / "labels" / f"old_{split}.txt").write_bytes(LABEL)
        row = dict(filename=name, split=split, sha256=digest(image), clip=split)
        (test_rows if split == "test" else rows).append(row)
        source_split = "test" if split == "test" else "train"
        label = old_test_label if split == "test" else LABEL * 2 if split == "train" else LABEL
        old.append((source_split, name, image, label))
    (frozen / "training_split_manifest.json").write_text(json.dumps(rows))
    (frozen / "test_manifest.json").write_text(json.dumps(test_rows))
    source = root / "input.zip"
    with ZipFile(source, "w") as archive:
        archive.writestr("data.yaml", "names: ['ball', 'goalkeeper', 'player', 'referee']\n")
        for split, name, image, label in old + [
            ("train", "new_train.jpg", jpeg("yellow"), new_label),
            ("test", "new_valid.jpg", jpeg("purple"), LABEL),
        ]:
            archive.writestr(f"{split}/images/{name}", image)
            archive.writestr(f"{split}/labels/{Path(name).stem}.txt", label)
        if extra:
            archive.writestr(extra, "unsafe")
    return source, frozen


def test_restores_splits_and_only_known_duplicate_labels(tmp_path):
    source, frozen = fixture(tmp_path)
    original = source.read_bytes()
    output = tmp_path / "out"
    report = prepare(source, frozen, output, new_test_is_validation=True)
    assert {k: v["images"] for k, v in report["splits"].items()} == dict(train=2, valid=2, test=1)
    assert report["training_ready"]
    assert report["changes"][0]["duplicate_boxes_removed"] == 1
    assert (output / "train/labels/old_train.txt").read_bytes() == LABEL
    assert (output / "valid/images/old_valid.jpg").is_file()
    assert (output / "valid/images/new_valid.jpg").is_file()
    assert (output / "test/labels/old_test.txt").read_bytes() == LABEL
    assert source.read_bytes() == original
    config = json.loads((output / "data.yaml").read_text())
    assert "test" not in config
    with ZipFile(output.with_suffix(".zip")) as archive:
        assert archive.testzip() is None


def test_polygon_is_preserved_and_training_config_is_withheld(tmp_path):
    polygon = b"0 0.1 0.2 0.2 0.3 0.3 0.1\n"
    source, frozen = fixture(tmp_path, new_label=polygon)
    output = tmp_path / "review"
    report = prepare(source, frozen, output, new_test_is_validation=True)
    assert not report["training_ready"]
    assert report["blocking_issues"][0]["line"] == 1
    assert (output / "train/labels/new_train.txt").read_bytes() == polygon
    assert not (output / "data.yaml").exists()
    assert "NOT READY TO TRAIN" in (output / "READ_BEFORE_TRAINING.txt").read_text()


def test_old_test_labels_cannot_be_rewritten(tmp_path):
    source, frozen = fixture(tmp_path, old_test_label=b"0 0.5 0.5 0.2 0.2\n")
    with pytest.raises(ValueError, match="old label changed"):
        prepare(source, frozen, tmp_path / "out", new_test_is_validation=True)
    assert not (tmp_path / "out").exists()


def test_new_test_move_requires_confirmation(tmp_path):
    with pytest.raises(ValueError, match="Explicit confirmation"):
        prepare(tmp_path / "absent.zip", tmp_path / "absent", tmp_path / "out")


def test_unsafe_zip_is_rejected_before_output(tmp_path):
    source, frozen = fixture(tmp_path, extra="../outside.txt")
    with pytest.raises(ValueError, match="Unsafe ZIP"):
        prepare(source, frozen, tmp_path / "out", new_test_is_validation=True)
    assert not (tmp_path / "out").exists()


def test_frozen_source_must_not_change(tmp_path):
    source, frozen = fixture(tmp_path)
    (frozen / "valid/images/old_valid.jpg").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Frozen file checksum mismatch"):
        prepare(source, frozen, tmp_path / "out", new_test_is_validation=True)


def approval_file(root, source, polygon):
    path = root / "review.json"
    path.write_text(json.dumps({"source_sha256": digest(source.read_bytes()), "approvals": [{
        "filename": "new_train.jpg", "line": 2, "class_id": 0,
        "original_line_sha256": digest(polygon.strip()), "position_confirmed_by": "user",
    }]}))
    return path


def test_reviewed_polygon_keeps_bounds_other_rows_and_source(tmp_path):
    polygon = b"0 0.1 0.2 0.2 0.3 0.3 0.1\n"
    source, frozen = fixture(tmp_path, new_label=LABEL + polygon)
    original = source.read_bytes()
    review = approval_file(tmp_path, source, polygon)
    output = tmp_path / "ready"
    report = prepare(source, frozen, output, new_test_is_validation=True, approved_polygons=review)
    assert report["training_ready"]
    assert report["user_reviewed_polygon_conversions"] == 1
    assert not report["new_labels_unchanged"]
    rows = (output / "train/labels/new_train.txt").read_bytes().splitlines(keepends=True)
    assert rows[0] == LABEL
    assert list(map(float, rows[1].split())) == pytest.approx([0, .2, .2, .2, .2])
    assert source.read_bytes() == original
    assert (output / "data.yaml").exists()


def test_reviewed_polygon_line_checksum_is_required(tmp_path):
    polygon = b"0 0.1 0.2 0.2 0.3 0.3 0.1\n"
    source, frozen = fixture(tmp_path, new_label=LABEL + polygon)
    review = approval_file(tmp_path, source, b"a different label")
    with pytest.raises(ValueError, match="line checksum mismatch"):
        prepare(source, frozen, tmp_path / "out", new_test_is_validation=True, approved_polygons=review)
    assert not (tmp_path / "out").exists()


def test_reviewed_polygon_source_checksum_is_required(tmp_path):
    polygon = b"0 0.1 0.2 0.2 0.3 0.3 0.1\n"
    source, frozen = fixture(tmp_path, new_label=LABEL + polygon)
    review = approval_file(tmp_path, source, polygon)
    content = json.loads(review.read_text())
    content["source_sha256"] = "0" * 64
    review.write_text(json.dumps(content))
    with pytest.raises(ValueError, match="source ZIP checksum mismatch"):
        prepare(source, frozen, tmp_path / "out", new_test_is_validation=True, approved_polygons=review)


def test_reviewed_polygon_rejects_zero_area_and_invalid_coordinates():
    for row in (b"0 .1 .2 .1 .3 .1 .4\n", b"0 nan .2 .2 .3 .3 .4\n", b"0 1.1 .2 .2 .3 .3 .4\n"):
        approval = {"line": 1, "class_id": 0, "original_line_sha256": digest(row.strip())}
        with pytest.raises(ValueError):
            convert_reviewed_polygons(row, "image.jpg", [approval])
