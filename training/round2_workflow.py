"""Self-contained, testable helpers embedded in the round-two Colab notebook.

This module imports no YOLO model at import time and never starts training.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path, PurePosixPath
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw


EXPECTED = ["ball", "goalkeeper", "player", "referee"]
INITIAL_SHA256 = "da6a85a5230e4acfdb4bb10a82b6bb148eadfcf51f7f4ae8787e40cb25e5f47f"
COUNTS = {"train": 141, "valid": 71}
VALIDATION_GROUP_COUNTS = {"old36": 36, "new35": 35}
THRESHOLDS = (.15, .30, .50)
DISPLAY_THRESHOLDS = {"ball": .15, "goalkeeper": .50, "player": .50, "referee": .50}


def file_sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path, value):
    Path(path).write_bytes(json_bytes(value))


def parse_labels(raw, width, height):
    truth = []
    for number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"Label line {number} is not a five-field detection box")
        class_id = int(fields[0])
        x, y, w, h = map(float, fields[1:])
        if class_id not in range(4) or not all(math.isfinite(v) for v in (x, y, w, h)):
            raise ValueError("Invalid label class/coordinates")
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            raise ValueError("Invalid normalized label box")
        if min(x - w / 2, y - h / 2) < -.002 or max(x + w / 2, y + h / 2) > 1.002:
            raise ValueError("Label box exceeds the image")
        truth.append({"class_id": class_id, "xyxy": [(x - w / 2) * width, (y - h / 2) * height,
                                                       (x + w / 2) * width, (y + h / 2) * height]})
    if not truth:
        raise ValueError("Unexpected empty label in this prepared dataset")
    return truth


def validate_records(root, rows):
    root = Path(root)
    if Counter(row["split"] for row in rows) != Counter(COUNTS):
        raise ValueError("Expected exactly 141 Train / 71 Validation records, without Test records")
    seen, file_hashes, pixel_hashes = set(), set(), set()
    class_counts = {split: Counter() for split in COUNTS}
    for row in rows:
        name, split = row["filename"], row["split"]
        if name in seen or PurePosixPath(name).name != name or ":" in name or "\\" in name:
            raise ValueError("Duplicate or unsafe dataset filename")
        seen.add(name)
        if "idq95Xp5RI0" in name or row.get("clip") == "idq95Xp5RI0":
            raise ValueError("Reserved Test match cannot be used for round-two training/selection")
        image = root / split / "images" / name
        label = root / split / "labels" / (Path(name).stem + ".txt")
        image_hash = file_sha256(image)
        if image_hash != row["sha256"] or file_sha256(label) != row["label_sha256"]:
            raise ValueError(f"Prepared file checksum mismatch: {name}")
        with Image.open(image) as decoded:
            width, height = decoded.size
            pixels = hashlib.sha256(decoded.convert("RGB").tobytes()).hexdigest()
        if image_hash in file_hashes or pixels in pixel_hashes:
            raise ValueError(f"Duplicate image in training/validation: {name}")
        file_hashes.add(image_hash)
        pixel_hashes.add(pixels)
        if (width, height) != (row["width"], row["height"]):
            raise ValueError("Prepared image dimensions changed")
        truth = parse_labels(label.read_bytes(), width, height)
        class_counts[split].update(EXPECTED[item["class_id"]] for item in truth)
    for split in COUNTS:
        expected_images = {r["filename"] for r in rows if r["split"] == split}
        actual_images = {p.name for p in (root / split / "images").iterdir() if p.is_file()}
        expected_labels = {Path(name).stem + ".txt" for name in expected_images}
        actual_labels = {p.name for p in (root / split / "labels").iterdir() if p.is_file()}
        if actual_images != expected_images or actual_labels != expected_labels:
            raise ValueError("Image/label inventory differs from the manifest")
    valid = [r for r in rows if r["split"] == "valid"]
    if (sum(r["origin"] == "frozen" for r in valid) != VALIDATION_GROUP_COUNTS["old36"] or
            sum(r["origin"] == "new" for r in valid) != VALIDATION_GROUP_COUNTS["new35"]):
        raise ValueError("Expected old Validation 36 + new Validation 35")
    if any(r["origin"] == "frozen" and r["clip"] != "tJnScrAKJfI" for r in valid):
        raise ValueError("The original Validation match has changed")
    return {split: dict(counts) for split, counts in class_counts.items()}


def build_training_bundle(dataset, initial_model, output, review_path):
    dataset, initial_model, output = Path(dataset), Path(initial_model), Path(output)
    if output.exists():
        raise FileExistsError("Choose a new bundle filename; existing ZIPs are never overwritten")
    audit = json.loads((dataset / "audit.json").read_text(encoding="utf-8"))
    if not audit["training_ready"] or audit["blocking_issues"] or audit["classes"] != EXPECTED:
        raise ValueError("Dataset is not ready for training")
    rows = [r for r in json.loads((dataset / "split_manifest.json").read_text()) if r["split"] in COUNTS]
    class_counts = validate_records(dataset, rows)
    if file_sha256(initial_model) != INITIAL_SHA256:
        raise ValueError("Initial weights are not the frozen round-one best.pt")
    payload = {}
    for row in rows:
        for kind, name in (("images", row["filename"]), ("labels", Path(row["filename"]).stem + ".txt")):
            member = f"{row['split']}/{kind}/{name}"
            payload[member] = dataset / member
    config = {"train": "train/images", "val": "valid/images", "nc": 4, "names": EXPECTED}
    metadata = {
        "purpose": "round2_train_validation_only", "training_ready": True,
        "source_zip": audit["source_zip"], "source_sha256": audit["source_sha256"],
        "counts": COUNTS, "class_counts": class_counts, "changes": audit["changes"],
        "excluded_test_images": 30, "initial_model_sha256": INITIAL_SHA256,
        "new_match_ids_available": False, "note": audit["note"],
    }
    # Strip source_member/source_split: new Validation was accidentally marked
    # Test in Roboflow; only the final confirmed split belongs in this bundle.
    kept = ("filename", "split", "origin", "clip", "width", "height", "sha256", "label_sha256")
    payload.update({"initial_model.pt": initial_model, "data.yaml": json_bytes(config),
                    "dataset_audit.json": json_bytes(metadata),
                    "split_manifest.json": json_bytes([{k: row[k] for k in kept} for row in rows]),
                    "label_review.json": Path(review_path)})
    hashes = {name: file_sha256(value) if isinstance(value, Path) else hashlib.sha256(value).hexdigest()
              for name, value in payload.items()}
    manifest = {"purpose": "tactivision_round2_training_bundle", "counts": COUNTS,
                "initial_model_sha256": INITIAL_SHA256, "files": hashes,
                "test_images_included": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for name, value in payload.items():
            if isinstance(value, Path):
                archive.write(value, name)
            else:
                archive.writestr(name, value)
        archive.writestr("bundle_manifest.json", json_bytes(manifest))
    return manifest


def stage_training_bundle(archive_path, destination):
    """Extract only allowlisted data, with hashes verified before any writes."""
    destination = Path(destination)
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP members")
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "test" in path.parts or "\\" in name or ":" in name:
                raise ValueError("Unsafe or Test-containing training ZIP")
        manifest = json.loads(archive.read("bundle_manifest.json"))
        if manifest["purpose"] != "tactivision_round2_training_bundle" or manifest["counts"] != COUNTS or manifest["test_images_included"]:
            raise ValueError("Use the prepared football-v3-training-ready.zip")
        expected_files = manifest["files"]
        if set(names) != set(expected_files) | {"bundle_manifest.json"}:
            raise ValueError("Bundle inventory mismatch")
        metadata_names = {"initial_model.pt", "data.yaml", "dataset_audit.json", "split_manifest.json", "label_review.json"}
        for name, expected in expected_files.items():
            path = PurePosixPath(name)
            is_data = (len(path.parts) == 3 and path.parts[0] in COUNTS and
                       ((path.parts[1] == "images" and path.suffix.lower() == ".jpg") or
                        (path.parts[1] == "labels" and path.suffix == ".txt")))
            if name not in metadata_names and not is_data:
                raise ValueError("Unexpected file type in training bundle")
            hasher = hashlib.sha256()
            with archive.open(name) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            if hasher.hexdigest() != expected:
                raise ValueError(f"Bundle checksum mismatch: {name}")
        if expected_files["initial_model.pt"] != INITIAL_SHA256 or manifest["initial_model_sha256"] != INITIAL_SHA256:
            raise ValueError("Wrong initial model")
        # A repeat of the upload cell can reuse identical files, never overwrite
        # divergent files left in the dataset folder.
        if (destination / "test").exists():
            raise ValueError("Use a new run folder without Test data")
        for name, expected in expected_files.items():
            target = destination / name
            if target.exists() and file_sha256(target) != expected:
                raise ValueError(f"Existing staged file differs; rerun setup for a fresh run: {name}")
        for name in names:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if name == "bundle_manifest.json" and target.read_bytes() != archive.read(name):
                    raise ValueError("Existing bundle manifest differs")
                continue
            with archive.open(name) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    rows = json.loads((destination / "split_manifest.json").read_text())
    validate_records(destination, rows)
    return rows, manifest


def make_validation_configs(root, rows, config_dir):
    root, config_dir = Path(root).resolve(), Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    groups = {"all71": [r for r in rows if r["split"] == "valid"],
              "old36": [r for r in rows if r["split"] == "valid" and r["origin"] == "frozen"],
              "new35": [r for r in rows if r["split"] == "valid" and r["origin"] == "new"]}
    configs = {}
    for name, group in groups.items():
        image_list = (config_dir / f"{name}.txt").resolve()
        image_list.write_text("".join(str(root / "valid/images" / r["filename"]) + "\n" for r in group), encoding="utf-8")
        config = {"path": str(root), "train": "train/images", "val": str(image_list), "nc": 4, "names": EXPECTED}
        configs[name] = (config_dir / f"{name}.yaml").resolve()
        write_json(configs[name], config)
    return groups, configs


def metric_summary(metrics):
    per_class = {name: None for name in EXPECTED}
    for position, class_id in enumerate(metrics.box.ap_class_index):
        per_class[EXPECTED[int(class_id)]] = {
            "precision": float(metrics.box.p[position]), "recall": float(metrics.box.r[position]),
            "mAP50": float(metrics.box.ap50[position]), "mAP50_95": float(metrics.box.ap[position]),
        }
    return {"precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
            "mAP50": float(metrics.box.map50), "mAP50_95": float(metrics.box.map), "per_class": per_class}


def evaluate_groups(model, configs, evaluation_args, run_root, phase):
    scores = {}
    for group, config in configs.items():
        metrics = model.val(data=str(config), project=str(Path(run_root) / "evaluations"),
                            name=f"{phase}_{group}", exist_ok=True, **evaluation_args)
        scores[group] = metric_summary(metrics)
        write_json(Path(run_root) / f"{phase}_metrics.json", scores)
    return scores


def collect_predictions(model, paths, output, *, imgsz, device):
    output = Path(output)
    rendered = output / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    if [model.names[i] for i in range(4)] != EXPECTED:
        raise ValueError("Model class mapping differs")
    predictions = {}
    for index, path in enumerate(paths, 1):
        result = model.predict(str(path), conf=min(THRESHOLDS), iou=.7, imgsz=imgsz,
                               max_det=300, rect=True, augment=False, device=device,
                               save=False, verbose=False)[0].cpu()
        predictions[path.name] = [{"xyxy": row[:4], "confidence": float(row[4]), "class_id": int(row[5])}
                                   for row in result.boxes.data.tolist()]
        mask = result.boxes.conf > 1.0
        for class_id, name in enumerate(EXPECTED):
            mask |= (result.boxes.cls == class_id) & (result.boxes.conf >= DISPLAY_THRESHOLDS[name])
        image = Image.fromarray(result[mask].plot(line_width=1)[:, :, ::-1])
        image.save(rendered / path.name, quality=95)
        print(f"[{index}/{len(paths)}] {path.name}", flush=True)
    write_json(output / "predictions.json", predictions)
    return predictions


def box_iou(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = max(0, a[2] - a[0]) * max(0, a[3] - a[1]) + max(0, b[2] - b[0]) * max(0, b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def fixed_counts(predictions, truth, threshold):
    counts = [{"tp": 0, "fp": 0, "fn": 0} for _ in EXPECTED]
    used = set()
    for pred in sorted((p for p in predictions if p["confidence"] >= threshold), key=lambda p: p["confidence"], reverse=True):
        candidates = [(box_iou(pred["xyxy"], answer["xyxy"]), i) for i, answer in enumerate(truth)
                      if i not in used and answer["class_id"] == pred["class_id"]]
        overlap, index = max(candidates, key=lambda pair: pair[0], default=(-1, None))
        if index is not None and overlap >= .5:
            used.add(index)
            counts[pred["class_id"]]["tp"] += 1
        else:
            counts[pred["class_id"]]["fp"] += 1
    for index, answer in enumerate(truth):
        if index not in used:
            counts[answer["class_id"]]["fn"] += 1
    return counts


def fixed_threshold_report(root, groups, predictions_by_phase):
    rows = []
    for phase, predictions in predictions_by_phase.items():
        for group, records in groups.items():
            for threshold in THRESHOLDS:
                totals = [{"tp": 0, "fp": 0, "fn": 0} for _ in EXPECTED]
                for row in records:
                    label = Path(root) / "valid/labels" / (Path(row["filename"]).stem + ".txt")
                    truth = parse_labels(label.read_bytes(), row["width"], row["height"])
                    counts = fixed_counts(predictions[row["filename"]], truth, threshold)
                    for class_id in range(4):
                        for key in totals[class_id]:
                            totals[class_id][key] += counts[class_id][key]
                for class_id, counts in enumerate(totals):
                    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
                    rows.append({"phase": phase, "group": group, "conf": threshold, "class": EXPECTED[class_id], **counts,
                                 "precision": tp / (tp + fp) if tp + fp else 0.0,
                                 "recall": tp / (tp + fn) if tp + fn else 0.0})
    return rows


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def comparison_panels(root, rows, before_dir, after_dir, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    colors = ["#00ffff", "#ffff00", "#00ff66", "#ff44ff"]
    saved = []
    for row in sorted((r for r in rows if r["split"] == "valid"), key=lambda r: r["filename"]):
        path = Path(root) / "valid/images" / row["filename"]
        with Image.open(path) as source:
            reference = source.convert("RGB")
        width, height = reference.size
        truth = parse_labels((Path(root) / "valid/labels" / (path.stem + ".txt")).read_bytes(), width, height)
        draw = ImageDraw.Draw(reference)
        for answer in truth:
            box, class_id = answer["xyxy"], answer["class_id"]
            draw.rectangle(box, outline=colors[class_id], width=2)
            draw.text((max(0, box[0]), max(0, box[1] - 12)), EXPECTED[class_id], fill=colors[class_id], stroke_fill="black", stroke_width=1)
        panel = Image.new("RGB", (width * 3, height + 50), "white")
        panel.paste(reference, (0, 50))
        for column, directory in ((1, before_dir), (2, after_dir)):
            with Image.open(Path(directory) / path.name) as rendered:
                panel.paste(rendered.convert("RGB"), (column * width, 50))
        draw = ImageDraw.Draw(panel)
        for column, title in enumerate(("LABEL REFERENCE", "BEFORE - round 1 best.pt", "AFTER - round 2 best.pt")):
            draw.text((column * width + 10, 8), title, fill="black")
        draw.text((10, 28), "Display: people conf >= 0.50; ball >= 0.15, identical for BEFORE/AFTER. Metrics are reported separately.", fill="black")
        target = destination / path.name
        panel.save(target, quality=95)
        saved.append(target)
    return saved


def package_results(run_root, data_root, train_dir, new_model, report):
    run_root, data_root, train_dir, new_model = map(Path, (run_root, data_root, train_dir, new_model))
    if not new_model.is_file():
        raise ValueError("No completed round-two model to package")
    write_json(run_root / "round2_report.json", report)
    output = run_root / "tactivision_round2_results.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(new_model, "best_round2.pt")
        for name in ("round2_report.json", "before_metrics.json", "after_metrics.json", "map_comparison.csv", "fixed_threshold_comparison.csv"):
            archive.write(run_root / name, name)
        for name in ("dataset_audit.json", "split_manifest.json", "bundle_manifest.json", "label_review.json", "data.yaml"):
            archive.write(data_root / name, "input_metadata/" + name)
        for directory, prefix in ((run_root / "comparisons", "comparisons"), (run_root / "evaluations", "evaluations"),
                                  (run_root / "groups", "validation_groups"), (train_dir, "training")):
            for file in sorted(directory.rglob("*")):
                if file.is_file() and file.suffix.lower() in {".png", ".jpg", ".csv", ".yaml", ".json", ".txt"}:
                    archive.write(file, str(PurePosixPath(prefix) / file.relative_to(directory).as_posix()))
        for phase in ("before", "after"):
            archive.write(run_root / phase / "predictions.json", f"{phase}/predictions.json")
    return output
