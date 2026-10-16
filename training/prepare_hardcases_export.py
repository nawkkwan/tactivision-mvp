"""Restore frozen splits and move user-confirmed new Test images to Validation.

Creates a new copy, never overwrites source data. Malformed new labels remain
intact unless an exact, user-reviewed polygon conversion has been supplied.
data.yaml is withheld while unresolved annotation issues remain.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from io import BytesIO
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
from zipfile import ZipFile

from PIL import Image

try:
    from .prepare_roboflow_export import EXPECTED_NAMES, duplicate_boxes
except ImportError:
    from prepare_roboflow_export import EXPECTED_NAMES, duplicate_boxes


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_unique_members(archive):
    members = {}
    for member in archive.infolist():
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename or ":" in member.filename:
            raise ValueError(f"Unsafe ZIP member: {member.filename}")
        if member.is_dir():
            continue
        if member.filename in members:
            if archive.read(member) != archive.read(members[member.filename]):
                raise ValueError(f"Conflicting duplicate ZIP member: {member.filename}")
        else:
            members[member.filename] = member
    return members


def read_boxes(raw: bytes):
    boxes, issues = [], []
    for number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        try:
            if len(fields) != 5:
                raise ValueError(f"Expected 5 detection fields, found {len(fields)}; review annotation shape and position")
            class_id = int(fields[0])
            x, y, w, h = map(float, fields[1:])
            if class_id not in range(4) or not all(math.isfinite(value) for value in (x, y, w, h)):
                raise ValueError("Invalid class or nonfinite coordinates")
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                raise ValueError("Coordinates outside normalized ranges")
            if min(x - w / 2, y - h / 2) < -.002 or max(x + w / 2, y + h / 2) > 1.002:
                raise ValueError("Box exceeds image bounds")
            boxes.append((class_id, x, y, w, h))
        except ValueError as exc:
            issues.append({"line": number, "message": str(exc)})
    if not boxes and not issues:
        issues.append({"line": None, "message": "Empty label needs human review"})
    return boxes, issues


def equivalent(a, b):
    return len(a) == len(b) and all(
        x[0] == y[0] and all(math.isclose(i, j, abs_tol=1e-10, rel_tol=0) for i, j in zip(x[1:], y[1:]))
        for x, y in zip(a, b)
    )


def convert_reviewed_polygons(raw, filename, approvals):
    """Change annotation representation only, never guess an object's location."""
    lines = raw.decode("utf-8-sig").splitlines(keepends=True)
    changes = []
    for approval in approvals:
        number = approval["line"]
        if not isinstance(number, int) or number < 1 or number > len(lines):
            raise ValueError(f"Reviewed polygon line not found: {filename}")
        original = lines[number - 1]
        line = original.strip()
        if digest(line.encode("utf-8")) != approval["original_line_sha256"]:
            raise ValueError(f"Reviewed polygon line checksum mismatch: {filename}:{number}")
        fields = line.split()
        if len(fields) < 7 or len(fields) % 2 != 1:
            raise ValueError("Approved polygon must contain at least three XY points")
        class_id = int(fields[0])
        if class_id not in range(4) or class_id != approval["class_id"]:
            raise ValueError("Reviewed polygon class mismatch")
        values = list(map(float, fields[1:]))
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
            raise ValueError("Invalid reviewed polygon coordinates")
        xs, ys = values[::2], values[1::2]
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        if left >= right or top >= bottom:
            raise ValueError("Reviewed polygon has zero-area bounds")
        box = [(left + right) / 2, (top + bottom) / 2, right - left, bottom - top]
        ending = "\r\n" if original.endswith("\r\n") else "\n" if original.endswith("\n") else ""
        lines[number - 1] = f"{class_id} " + " ".join(f"{value:.17g}" for value in box) + ending
        changes.append({"filename": filename, "line": number, "action": "user_reviewed_polygon_to_enclosing_box",
                        "position_confirmed_by": "user", "original_line_sha256": approval["original_line_sha256"],
                        "class_id": class_id, "bbox_normalized_xywh": box,
                        "note": "Preserves the original polygon bounds; no relocation or prediction-based correction"})
    prefix = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return prefix + "".join(lines).encode("utf-8"), changes


def load_frozen(dataset: Path):
    rows = json.loads((dataset / "training_split_manifest.json").read_text(encoding="utf-8"))
    rows += [{**row, "split": "test"} for row in json.loads((dataset / "test_manifest.json").read_text(encoding="utf-8"))]
    frozen = {}
    for row in rows:
        filename = row["filename"]
        if filename != PurePosixPath(filename).name or "\\" in filename or ":" in filename:
            raise ValueError("Unsafe filename in frozen manifest")
        split = row["split"]
        if split not in {"train", "valid", "test"} or filename in frozen:
            raise ValueError("Invalid frozen split or duplicate filename")
        image = (dataset / split / "images" / filename).read_bytes()
        labels = (dataset / split / "labels" / (Path(filename).stem + ".txt")).read_bytes()
        if digest(image) != row["sha256"] or (row.get("label_sha256") and digest(labels) != row["label_sha256"]):
            raise ValueError(f"Frozen file checksum mismatch: {filename}")
        boxes, issues = read_boxes(labels)
        if issues:
            raise ValueError(f"Frozen label needs review: {filename}")
        frozen[filename] = {"split": split, "image": image, "labels": labels, "boxes": boxes, "clip": row["clip"]}
    if {row["split"] for row in frozen.values()} != {"train", "valid", "test"}:
        raise ValueError("Frozen data must contain Train, Validation and Test")
    return frozen


def prepare(source: Path, frozen_dataset: Path, output: Path, *, new_test_is_validation=False, approved_polygons: Path | None = None):
    if not new_test_is_validation:
        raise ValueError("Explicit confirmation required: new source-Test images are Validation, not held-out Test")
    if output.exists() or output.with_suffix(".zip").exists():
        raise FileExistsError("Choose a new output directory and ZIP name")
    source_hash = digest(source.read_bytes())
    approvals, used_approvals = {}, set()
    if approved_polygons is not None:
        review = json.loads(approved_polygons.read_text(encoding="utf-8"))
        if review["source_sha256"] != source_hash:
            raise ValueError("Reviewed polygon source ZIP checksum mismatch")
        keys = set()
        for approval in review["approvals"]:
            key = (approval["filename"], approval["line"])
            if approval.get("position_confirmed_by") != "user" or key in keys:
                raise ValueError("Polygon conversion requires unique, explicit user review")
            keys.add(key)
            approvals.setdefault(approval["filename"], []).append(approval)
    frozen = load_frozen(frozen_dataset)
    records, seen_old, seen_names = [], set(), set()
    file_hashes, pixel_hashes = {}, {}
    changes, polygon_changes, blocking_issues = [], [], []
    origin_counts = Counter()
    with ZipFile(source) as archive:
        members = read_unique_members(archive)
        config = archive.read(members["data.yaml"]).decode("utf-8-sig")
        names = re.search(r"^names:\s*(\[.*\])\s*$", config, re.M)
        if not names or ast.literal_eval(names[1]) != EXPECTED_NAMES:
            raise ValueError("Class order differs from the frozen four-class model")
        matched_labels = set()
        for member in sorted(members):
            path = PurePosixPath(member)
            if "/images/" not in member or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            if len(path.parts) != 3 or path.parts[0] not in {"train", "valid", "test"} or ":" in path.name:
                raise ValueError(f"Unexpected image path: {member}")
            if path.name in seen_names:
                raise ValueError(f"Repeated image basename: {path.name}")
            seen_names.add(path.name)
            label_member = str(path.parent.parent / "labels" / (path.stem + ".txt"))
            if label_member not in members:
                raise ValueError(f"Missing label: {member}")
            matched_labels.add(label_member)
            image = archive.read(members[member])
            labels = archive.read(members[label_member])
            if path.name in approvals:
                if path.name in frozen:
                    raise ValueError("Reviewed polygon conversions cannot rewrite frozen labels")
                labels, converted = convert_reviewed_polygons(labels, path.name, approvals[path.name])
                polygon_changes.extend(converted)
                used_approvals.update((path.name, entry["line"]) for entry in approvals[path.name])
            with Image.open(BytesIO(image)) as decoded:
                decoded.load()
                width, height = decoded.size
                pixels = digest(decoded.convert("RGB").tobytes())
            image_hash = digest(image)
            if image_hash in file_hashes or pixels in pixel_hashes:
                raise ValueError(f"Duplicate image bytes/pixels: {member}")
            file_hashes[image_hash], pixel_hashes[pixels] = member, member
            boxes, issues = read_boxes(labels)
            source_split = path.parts[0]
            if path.name in frozen:
                previous = frozen[path.name]
                seen_old.add(path.name)
                if image != previous["image"]:
                    raise ValueError(f"Old image bytes changed: {member}")
                target_split = previous["split"]
                origin, clip = "frozen", previous["clip"]
                if labels != previous["labels"]:
                    if target_split != "train" or issues:
                        raise ValueError(f"Frozen Validation/Test or unsupported old label changed: {member}")
                    removed = {i for _, i in duplicate_boxes(boxes, width, height)}
                    cleaned = [box for i, box in enumerate(boxes) if i not in removed]
                    if not removed or not equivalent(cleaned, previous["boxes"]):
                        raise ValueError(f"Old label changes exceed known duplicate restoration: {member}")
                    labels, boxes = previous["labels"], previous["boxes"]
                    changes.append({"filename": path.name, "action": "restore_frozen_train_label", "duplicate_boxes_removed": len(removed)})
            else:
                if source_split not in {"train", "test"}:
                    raise ValueError("This plan expects new Train images plus confirmed new-Test-as-Validation")
                target_split = "valid" if source_split == "test" else "train"
                origin, clip = "new", None
                for issue in issues:
                    blocking_issues.append({"filename": path.name, "split": target_split, **issue})
                duplicates = duplicate_boxes(boxes, width, height)
                if duplicates:
                    blocking_issues.append({"filename": path.name, "split": target_split, "message": "New duplicate boxes require human review", "pairs": duplicates})
            origin_counts[f"{origin}_{source_split}_to_{target_split}"] += 1
            records.append({"filename": path.name, "source_member": member, "source_split": source_split,
                            "split": target_split, "origin": origin, "clip": clip, "width": width, "height": height,
                            "sha256": image_hash, "label_sha256": digest(labels), "boxes": boxes,
                            "image": image, "labels": labels})
        if seen_old != set(frozen):
            raise ValueError("Some frozen Train/Validation/Test images are missing from the export")
        if matched_labels != {name for name in members if "/labels/" in name and name.endswith(".txt")}:
            raise ValueError("Orphan labels in export")
        if used_approvals != {(filename, entry["line"]) for filename, entries in approvals.items() for entry in entries}:
            raise ValueError("Some reviewed polygons were not found in the export")
    ready = not blocking_issues
    report = {
        "source_zip": source.name, "source_sha256": source_hash,
        "classes": EXPECTED_NAMES, "images": len(records), "training_ready": ready,
        "training_started": False, "source_modified": False, "new_test_is_validation_confirmed": True,
        "origin_counts": dict(origin_counts), "changes": changes + polygon_changes, "blocking_issues": blocking_issues,
        "splits": {split: {"images": sum(row["split"] == split for row in records),
                             "parsed_box_counts": dict(Counter(EXPECTED_NAMES[box[0]] for row in records if row["split"] == split for box in row["boxes"]))}
                   for split in ("train", "valid", "test")},
        "old_validation_and_test_labels_unchanged": True,
        "new_labels_unchanged": not polygon_changes, "new_match_ids_available": False,
        "user_reviewed_polygon_conversions": len(polygon_changes),
        "note": "New split assignments follow user confirmation; generic filenames do not independently prove match separation. Format checks cannot prove semantic label accuracy. Parsed counts exclude unsupported rows.",
    }
    for split in ("train", "valid", "test"):
        for kind in ("images", "labels"):
            (output / split / kind).mkdir(parents=True, exist_ok=False)
    for row in records:
        (output / row["split"] / "images" / row["filename"]).write_bytes(row["image"])
        (output / row["split"] / "labels" / (Path(row["filename"]).stem + ".txt")).write_bytes(row["labels"])
    manifest = [{k: v for k, v in row.items() if k not in {"image", "labels", "boxes"}} for row in records]
    (output / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if ready:
        # No Test key: Test data must never be selected for model tuning.
        config = {"train": "train/images", "val": "valid/images", "nc": 4, "names": EXPECTED_NAMES}
        (output / "data.yaml").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (output / "READ_BEFORE_TRAINING.txt").write_text(
        ("FORMAT CHECKS PASSED. Manually review annotation quality before training.\n" if ready else
         "NOT READY TO TRAIN. data.yaml is intentionally absent. Fix blocking_issues in audit.json before training.\n")
        + "Frozen Test is included for split inspection only; never use it for model/confidence selection.\n"
        + "Source ZIP is unchanged. Only exact, user-reviewed polygons may be converted to enclosing boxes; other malformed labels remain for review.\n",
        encoding="utf-8",
    )
    shutil.make_archive(str(output), "zip", output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--frozen-dataset", type=Path, default=Path("training/data/prepared/football-v2-test-ready"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--new-test-is-validation", action="store_true")
    parser.add_argument("--approved-polygons", type=Path, help="Source/line-checksummed JSON recording explicit user review")
    args = parser.parse_args()
    print(json.dumps(prepare(args.zip, args.frozen_dataset, args.output,
                             new_test_is_validation=args.new_test_is_validation,
                             approved_polygons=args.approved_polygons), indent=2))
