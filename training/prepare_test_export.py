"""Create a frozen Test evaluation bundle without loading or training any model."""
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

from prepare_roboflow_export import EXPECTED_NAMES, TIMESTAMP, duplicate_boxes, corners


def read_unique_members(archive: ZipFile) -> dict[str, object]:
    members = {}
    for member in archive.infolist():
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
            raise ValueError(f"Unsafe ZIP member: {member.filename}")
        if member.is_dir():
            continue
        if member.filename in members:
            # Roboflow v2 includes two identical data.yaml entries. Accept only
            # identical contents rather than letting ZIP extraction choose one.
            if archive.read(members[member.filename]) != archive.read(member):
                raise ValueError(f"Conflicting duplicate ZIP member: {member.filename}")
        else:
            members[member.filename] = member
    return members


def prepare_test(source: Path, frozen_dataset: Path, trained_results: Path, output: Path, review: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"Choose a new output folder: {output}")
    frozen_manifest = json.loads((frozen_dataset / "split_manifest.json").read_text(encoding="utf-8"))
    known_hashes = {row["sha256"] for row in frozen_manifest}
    known_clips = {row["clip"] for row in frozen_manifest}
    with ZipFile(trained_results) as trained_zip:
        trained_manifest = json.loads(trained_zip.read("split_manifest.json"))
        if trained_manifest != frozen_manifest:
            raise ValueError("Frozen dataset differs from the dataset used to train best.pt")
        model_bytes = trained_zip.read("best.pt")
    pixel_hashes = set()
    for row in frozen_manifest:
        image_path = frozen_dataset / row["split"] / "images" / row["filename"]
        if hashlib.sha256(image_path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Training/Validation image changed: {image_path.name}")
        with Image.open(image_path) as image:
            pixel_hashes.add(hashlib.sha256(image.convert("RGB").tobytes()).hexdigest())

    records = []
    label_bytes_by_name = {}
    image_bytes_by_name = {}
    with ZipFile(source) as archive:
        members = read_unique_members(archive)
        config_text = archive.read(members["data.yaml"]).decode("utf-8-sig")
        names_match = re.search(r"^names:\s*(\[.*\])\s*$", config_text, re.M)
        if not names_match or ast.literal_eval(names_match.group(1)) != EXPECTED_NAMES:
            raise ValueError("Class names/order differ from best.pt training data")
        image_names = sorted(name for name in members if name.startswith("test/images/") and PurePosixPath(name).suffix.lower() in {".jpg", ".jpeg", ".png"})
        if not image_names:
            raise ValueError("No Test images found")
        seen_hashes = set()
        seen_pixels = set()
        matched_labels = set()
        for name in image_names:
            path = PurePosixPath(name)
            stamp = TIMESTAMP.match(path.name)
            if not stamp or stamp["clip"] != "idq95Xp5RI0" or stamp["clip"] in known_clips:
                raise ValueError(f"Unexpected Test source clip: {path.name}")
            label_name = "test/labels/" + path.stem + ".txt"
            if label_name not in members:
                raise ValueError(f"Missing Test label: {path.name}")
            matched_labels.add(label_name)
            image_bytes = archive.read(members[name])
            digest = hashlib.sha256(image_bytes).hexdigest()
            with Image.open(BytesIO(image_bytes)) as image:
                image.load()
                width, height = image.size
                pixels = hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()
            if digest in known_hashes or pixels in pixel_hashes:
                raise ValueError(f"Test image also occurs in Train/Validation: {path.name}")
            if digest in seen_hashes or pixels in seen_pixels:
                raise ValueError(f"Duplicate Test image: {path.name}")
            seen_hashes.add(digest)
            seen_pixels.add(pixels)
            raw_labels = archive.read(members[label_name])
            boxes = []
            for line_number, line in enumerate(raw_labels.decode("utf-8-sig").splitlines(), 1):
                if not line.strip():
                    continue
                fields = line.split()
                if len(fields) != 5:
                    raise ValueError(f"Invalid YOLO box: {label_name}:{line_number}")
                class_id = int(fields[0])
                x, y, w, h = map(float, fields[1:])
                if class_id not in range(4) or not all(math.isfinite(value) for value in (x,y,w,h)):
                    raise ValueError(f"Invalid class/coordinate: {label_name}:{line_number}")
                if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                    raise ValueError(f"Invalid normalized coordinates: {label_name}:{line_number}")
                if min(x-w/2,y-h/2) < -0.002 or max(x+w/2,y+h/2) > 1.002:
                    raise ValueError(f"Box outside image: {label_name}:{line_number}")
                boxes.append((class_id,x,y,w,h))
            if not boxes:
                raise ValueError(f"Empty Test label requires human verification: {label_name}")
            pairs = duplicate_boxes(boxes, width, height)
            if pairs:
                raise ValueError(f"Review duplicate boxes before freezing Test: {path.name}: {pairs}")
            records.append({"filename":path.name,"label":PurePosixPath(label_name).name,"clip":stamp["clip"],"sha256":digest,
                            "label_sha256":hashlib.sha256(raw_labels).hexdigest(),"width":width,"height":height,"boxes":boxes})
            image_bytes_by_name[path.name] = image_bytes
            label_bytes_by_name[PurePosixPath(label_name).name] = raw_labels
        if matched_labels != {name for name in members if name.startswith("test/labels/") and name.endswith(".txt")}:
            raise ValueError("Unmatched Test label files")

    counts = Counter(EXPECTED_NAMES[box[0]] for row in records for box in row["boxes"])
    summary = {"purpose":"held_out_test_evaluation", "test_images":len(records), "nonempty_test_labels":len(records),
               "classes":EXPECTED_NAMES,"test_boxes_by_class":dict(counts),"test_clip":"idq95Xp5RI0",
               "class_order_matches_training":True,"exact_image_overlap_with_train_valid":False,"duplicate_test_box_candidates":0,
               "best_model_sha256":hashlib.sha256(model_bytes).hexdigest(),"labels_changed":False,
               "source_export":source.name,"trained_results":trained_results.name,
               "note":"File validation is not a guarantee of human annotation accuracy. Test scores are not computed by this script."}
    output.mkdir(parents=True)
    for split in ("train","valid"):
        shutil.copytree(frozen_dataset / split, output / split)
    for kind in ("images","labels"):
        (output / "test" / kind).mkdir(parents=True)
    for filename, content in image_bytes_by_name.items():
        (output / "test/images" / filename).write_bytes(content)
    for filename, content in label_bytes_by_name.items():
        (output / "test/labels" / filename).write_bytes(content)
    (output / "models").mkdir()
    (output / "models/best.pt").write_bytes(model_bytes)
    config = {"train":"train/images","val":"valid/images","test":"test/images","nc":4,"names":EXPECTED_NAMES}
    (output / "data.yaml").write_text(json.dumps(config,indent=2)+"\n",encoding="utf-8")
    (output / "test_audit.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    manifest = [{key:value for key,value in row.items() if key != "boxes"} for row in records]
    (output / "test_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    shutil.copy2(frozen_dataset / "split_manifest.json", output / "training_split_manifest.json")
    review.mkdir(parents=True,exist_ok=True)
    # Annotated answer-key previews, never predictions and never fed to YOLO.
    colors = ["red","cyan","yellow","magenta"]
    for page in range(math.ceil(len(records)/6)):
        rows = records[page*6:(page+1)*6]
        sheet = Image.new("RGB",(1280,390*math.ceil(len(rows)/2)),"white")
        for i,row in enumerate(rows):
            with Image.open(output / "test/images" / row["filename"]) as image:
                frame = image.convert("RGB")
            draw = ImageDraw.Draw(frame)
            for box in row["boxes"]:
                xy = corners(box,row["width"],row["height"])
                draw.rectangle(xy,outline=colors[box[0]],width=2)
                draw.text((xy[0],max(0,xy[1]-12)),EXPECTED_NAMES[box[0]],fill=colors[box[0]])
            frame.thumbnail((640,360))
            left,top = (i%2)*640,(i//2)*390
            sheet.paste(frame,(left,top+25))
            ImageDraw.Draw(sheet).text((left+5,top+5),row["filename"].split("_jpg")[0],fill="black")
        sheet.save(review / f"test_labels_{page+1}.jpg",quality=95)
    shutil.make_archive(str(output),"zip",output)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip",type=Path,required=True)
    parser.add_argument("--frozen-dataset",type=Path,required=True)
    parser.add_argument("--trained-results",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--review",type=Path,default=Path("training/artifacts/test_label_review"))
    args = parser.parse_args()
    print(json.dumps(prepare_test(args.zip,args.frozen_dataset,args.trained_results,args.output,args.review),indent=2))
