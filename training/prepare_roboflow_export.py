"""Validate a Roboflow YOLO export and hold out a complete source video.

Reads ZIP members as data only. Does not execute files from the archive.
Requires Pillow for image decoding; uses the Python standard library otherwise.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
from zipfile import ZipFile

from PIL import Image, ImageDraw

EXPECTED_NAMES = ["ball", "goalkeeper", "player", "referee"]
TIMESTAMP = re.compile(r"^(?P<clip>[A-Za-z0-9_-]{11})_(?P<h>\d{2})-(?P<m>\d{2})-(?P<s>\d{2})")


def corners(box: tuple, width: int, height: int) -> tuple:
    _, x, y, w, h = box
    return ((x-w/2)*width, (y-h/2)*height, (x+w/2)*width, (y+h/2)*height)


def duplicate_boxes(boxes: list, width: int, height: int) -> list[tuple[int, int]]:
    pairs = []
    for i, box in enumerate(boxes):
        a = corners(box, width, height)
        for j in range(i):
            if box[0] != boxes[j][0]:
                continue
            b = corners(boxes[j], width, height)
            intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
            union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
            if union and intersection/union >= 0.8 and max(abs(x-y) for x, y in zip(a, b)) <= 2.01:
                pairs.append((j, i))
    return pairs


def prepare(source: Path, output: Path, valid_clip: str, review: Path, deduplicate: bool = False) -> dict:
    if output.exists():
        raise FileExistsError(f"Output already exists; use a new folder: {output}")
    records = []
    with ZipFile(source) as archive:
        members = archive.namelist()
        if len(members) != len(set(members)):
            raise ValueError("Duplicate ZIP member names")
        for name in members:
            parts = PurePosixPath(name).parts
            if name.startswith(("/", "\\")) or ".." in parts or "\\" in name:
                raise ValueError(f"Unsafe archive member: {name}")
        configs = [name for name in members if PurePosixPath(name).name == "data.yaml"]
        if len(configs) != 1:
            raise ValueError("Expected exactly one data.yaml")
        match = re.search(r"^names:\s*(\[.*\])\s*$", archive.read(configs[0]).decode("utf-8-sig"), re.M)
        if not match or ast.literal_eval(match.group(1)) != EXPECTED_NAMES:
            raise ValueError("Class order differs from the original football player model")

        image_names = sorted(name for name in members if "/images/" in name and PurePosixPath(name).suffix.lower() in {".jpg", ".jpeg", ".png"})
        labels_seen = set()
        image_hashes = set()
        pixel_hashes = set()
        basenames = set()
        for name in image_names:
            path = PurePosixPath(name)
            if path.parts[-3] != "train":
                raise ValueError("This tool expects an all-Train export; preserve existing test/valid splits separately")
            stamp = TIMESTAMP.match(path.name)
            if not stamp:
                raise ValueError(f"Cannot identify source video: {path.name}")
            label = str(path.parent.parent / "labels" / (path.stem + ".txt"))
            if label not in members:
                raise ValueError(f"Missing label: {label}")
            if path.name in basenames:
                raise ValueError(f"Duplicate image basename: {path.name}")
            basenames.add(path.name)
            labels_seen.add(label)
            image_bytes = archive.read(name)
            digest = hashlib.sha256(image_bytes).hexdigest()
            if digest in image_hashes:
                raise ValueError(f"Duplicate image content: {path.name}")
            image_hashes.add(digest)
            with Image.open(BytesIO(image_bytes)) as image:
                image.load()
                width, height = image.size
                pixel_digest = hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
                if pixel_digest in pixel_hashes:
                    raise ValueError(f"Duplicate decoded image: {path.name}")
                pixel_hashes.add(pixel_digest)
            boxes = []
            for line_number, line in enumerate(archive.read(label).decode("utf-8-sig").splitlines(), 1):
                if not line.strip():
                    continue
                fields = line.split()
                if len(fields) != 5:
                    raise ValueError(f"Not a YOLO box: {label}:{line_number}")
                class_id = int(fields[0])
                x, y, box_w, box_h = map(float, fields[1:])
                if class_id not in range(4) or not all(math.isfinite(v) for v in (x, y, box_w, box_h)):
                    raise ValueError(f"Invalid class or number: {label}:{line_number}")
                if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < box_w <= 1 and 0 < box_h <= 1):
                    raise ValueError(f"Invalid normalized box: {label}:{line_number}")
                if min(x - box_w / 2, y - box_h / 2) < -0.002 or max(x + box_w / 2, y + box_h / 2) > 1.002:
                    raise ValueError(f"Box exceeds image: {label}:{line_number}")
                boxes.append((class_id, x, y, box_w, box_h))
            seconds = int(stamp["h"]) * 3600 + int(stamp["m"]) * 60 + int(stamp["s"])
            pairs = duplicate_boxes(boxes, width, height)
            removed = sorted({i for _, i in pairs}) if deduplicate else []
            boxes = [box for i, box in enumerate(boxes) if i not in removed]
            records.append({"image": name, "label": label, "filename": path.name, "clip": stamp["clip"], "seconds": seconds,
                            "split": "valid" if stamp["clip"] == valid_clip else "train", "width": width, "height": height,
                            "sha256": digest, "boxes": boxes, "duplicate_box_pairs": pairs, "removed_label_lines": [i+1 for i in removed]})
        archive_labels = {name for name in members if "/labels/" in name and name.endswith(".txt")}
        if archive_labels != labels_seen:
            raise ValueError("Orphan labels in export")
        if not records or not {"train", "valid"}.issubset({row["split"] for row in records}):
            raise ValueError("Need both train and valid source clips")
        source_clips = {row["clip"] for row in records}
        if "idq95Xp5RI0" in source_clips:
            raise ValueError("Reserved test match must not enter Train/Validation")

        # Write only verified images and YOLO labels, never arbitrary archive files.
        for split in ("train", "valid"):
            for kind in ("images", "labels"):
                (output / split / kind).mkdir(parents=True, exist_ok=False)
        for row in records:
            (output / row["split"] / "images" / row["filename"]).write_bytes(archive.read(row["image"]))
            label_path = output / row["split"] / "labels" / PurePosixPath(row["label"]).name
            if row["removed_label_lines"]:
                label_path.write_text("".join(f"{box[0]} " + " ".join(f"{value:.12g}" for value in box[1:]) + "\n" for box in row["boxes"]), encoding="utf-8")
            else:
                label_path.write_bytes(archive.read(row["label"]))

    # JSON is also valid YAML. Relative paths resolve from this data.yaml.
    config = {"train": "train/images", "val": "valid/images", "nc": 4, "names": EXPECTED_NAMES}
    (output / "data.yaml").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    summary = {"source_zip": source.name, "classes": EXPECTED_NAMES, "image_count": len(records),
               "splits": {}, "reserved_test_clip": "idq95Xp5RI0", "test_included": False,
               "note": "Whole source videos are separated. Manual review is still needed; format validation cannot prove annotation accuracy."}
    for split in ("train", "valid"):
        rows = [row for row in records if row["split"] == split]
        counts = Counter(EXPECTED_NAMES[box[0]] for row in rows for box in row["boxes"])
        summary["splits"][split] = {"images": len(rows), "clips": sorted({row["clip"] for row in rows}), "boxes": dict(counts)}
    review.mkdir(parents=True, exist_ok=True)
    review_rows = [row for row in records if sum(box[0] == 0 for box in row["boxes"]) > 1]
    summary["multiple_ball_images"] = [row["filename"] for row in review_rows]
    summary["duplicate_box_images"] = [{"filename": row["filename"], "pairs": row["duplicate_box_pairs"]} for row in records if row["duplicate_box_pairs"]]
    summary["removed_duplicate_boxes"] = sum(len(row["removed_label_lines"]) for row in records)
    summary["deduplication_rule"] = "Opt-in: same class, IoU >= 0.8, and all box corners within 2 pixels"
    # Produce an audit page of ball boxes. This does not modify training images.
    if review_rows:
        sheet = Image.new("RGB", (1280, 390 * math.ceil(len(review_rows) / 2)), "white")
        for index, row in enumerate(review_rows):
            with Image.open(output / row["split"] / "images" / row["filename"]) as original:
                frame = original.convert("RGB")
            draw = ImageDraw.Draw(frame)
            for box in row["boxes"]:
                class_id, x, y, box_w, box_h = box
                if class_id == 0:
                    coords = ((x - box_w/2)*row["width"], (y - box_h/2)*row["height"], (x + box_w/2)*row["width"], (y + box_h/2)*row["height"])
                    draw.rectangle(coords, outline="red", width=3)
            frame.thumbnail((640, 360))
            left, top = index % 2 * 640, index // 2 * 390
            sheet.paste(frame, (left, top + 25))
            ImageDraw.Draw(sheet).text((left + 5, top + 5), row["filename"].split("_jpg")[0], fill="black")
        sheet.save(review / "multiple_ball_review.jpg", quality=95)
    manifest = [{key: value for key, value in row.items() if key not in {"boxes", "image", "label"}} for row in records]
    (output / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    shutil.make_archive(str(output), "zip", output)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--valid-clip", required=True)
    parser.add_argument("--review", type=Path, default=Path("training/artifacts/label_review"))
    parser.add_argument("--deduplicate", action="store_true", help="Remove near-identical same-class boxes in the output copy; review candidates first")
    args = parser.parse_args()
    print(json.dumps(prepare(args.zip, args.output, args.valid_clip, args.review, args.deduplicate), indent=2))
