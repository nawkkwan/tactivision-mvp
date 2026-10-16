"""Compare ball detections on the frozen Validation split, never Train/Test.

Run from the repository root:
    python training/compare_ball_detectors.py
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import gc
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import time
import zipfile

from PIL import Image, ImageDraw


THRESHOLDS = (0.15, 0.30, 0.50)
MAIN_SHA256 = "da6a85a5230e4acfdb4bb10a82b6bb148eadfcf51f7f4ae8787e40cb25e5f47f"
BALL_SHA256 = "678fbad05134f19c5094cb8d273812ec9c6691228180d46832551ecf99ed2912"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def box_iou(a, b) -> float:
    overlap = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    union = area_a + area_b - overlap
    return overlap / union if union > 0 else 0.0


def score_balls(predictions, truth, threshold, match_iou=0.5):
    """Confidence-ordered, one-to-one matching, same rule as confidence_sweep."""
    accepted = sorted(
        (p for p in predictions if p["confidence"] >= threshold),
        key=lambda p: p["confidence"], reverse=True,
    )
    used = set()
    matched = []
    for pred in accepted:
        candidates = [(box_iou(pred["xyxy"], box), i) for i, box in enumerate(truth) if i not in used]
        # Stable first-index tie breaking, matching the earlier notebook.
        overlap, index = max(candidates, key=lambda item: item[0], default=(-1, None))
        correct = index is not None and overlap >= match_iou
        if correct:
            used.add(index)
        matched.append({**pred, "correct": correct})
    tp = len(used)
    fp, fn = len(accepted) - tp, len(truth) - tp
    return {"tp": tp, "fp": fp, "fn": fn}, matched


def metrics(counts):
    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
    return {
        **counts,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
    }


def load_validation(dataset: Path):
    """Read only valid records/files; exclude other splits even if present."""
    manifest = json.loads((dataset / "split_manifest.json").read_text(encoding="utf-8"))
    rows = [row for row in manifest if row["split"] == "valid"]
    if len(rows) != 36 or any(row["clip"] != "tJnScrAKJfI" for row in rows):
        raise ValueError("Expected the frozen 36-image tJnScrAKJfI Validation split")
    names = {row["filename"] for row in rows}
    paths = sorted((dataset / "valid/images").glob("*.jpg"))
    if len(names) != 36 or {path.name for path in paths} != names:
        raise ValueError("Validation image files do not match the frozen manifest")
    by_name = {row["filename"]: row for row in rows}
    images = []
    for path in paths:
        if sha256(path) != by_name[path.name]["sha256"]:
            raise ValueError(f"Validation image checksum mismatch: {path.name}")
        with Image.open(path) as image:
            width, height = image.size
        truth = []
        label_path = dataset / "valid/labels" / (path.stem + ".txt")
        for line in label_path.read_text().splitlines():
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 5:
                raise ValueError(f"Invalid label: {label_path.name}")
            class_id = int(fields[0])
            x, y, w, h = map(float, fields[1:])
            if class_id not in range(4) or not all(math.isfinite(v) for v in (x, y, w, h)):
                raise ValueError(f"Invalid class/coordinates: {label_path.name}")
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                raise ValueError(f"Invalid normalized box: {label_path.name}")
            if class_id == 0:
                truth.append([(x - w / 2) * width, (y - h / 2) * height,
                              (x + w / 2) * width, (y + h / 2) * height])
        images.append({"path": path, "truth": truth})
    return images


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def draw_boxes(image, records, ground_truth=False):
    draw = ImageDraw.Draw(image)
    for record in records:
        box = record if ground_truth else record["xyxy"]
        color = "#00ff80" if ground_truth or record["correct"] else "#ff5252"
        x1, y1, x2, y2 = box
        draw.rectangle(box, outline=color, width=2)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), outline=color, width=2)
        text = "GT" if ground_truth else f"{record['confidence']:.2f} {'TP' if record['correct'] else 'FP'}"
        tx, ty = min(max(0, x1), max(0, image.width - 90)), max(0, y1 - 15)
        draw.rectangle((tx, ty, tx + 90, ty + 13), fill="black")
        draw.text((tx + 2, ty), text, fill=color)


def make_panel(path, truth, old, new, threshold, match_iou):
    old_counts, old_matched = score_balls(old, truth, threshold, match_iou)
    new_counts, new_matched = score_balls(new, truth, threshold, match_iou)
    with Image.open(path) as source:
        image = source.convert("RGB")
    width, height = image.size
    panel = Image.new("RGB", (width * 3, height + 60), "white")
    captions = [f"Ground truth: {len(truth)} balls",
                f"OLD best.pt conf={threshold:.2f} | {old_counts}",
                f"NEW ball model conf={threshold:.2f} | {new_counts}"]
    for column, records in enumerate((truth, old_matched, new_matched)):
        view = image.copy()
        draw_boxes(view, records, ground_truth=column == 0)
        panel.paste(view, (width * column, 60))
        ImageDraw.Draw(panel).text((width * column + 10, 8), captions[column], fill="black")
    ImageDraw.Draw(panel).text((10, 32), "Green = matched label; red = unmatched prediction. Circles highlight small boxes, not ball size.", fill="black")
    return panel


def run(args):
    os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".cache/ultralytics").resolve()))
    import torch
    from ultralytics import YOLO

    images = load_validation(args.dataset)
    paths = {"old_best": args.primary_model, "new_ball": args.ball_model}
    hashes = {name: sha256(path) for name, path in paths.items()}
    if hashes != {"old_best": MAIN_SHA256, "new_ball": BALL_SHA256}:
        raise ValueError("Model hashes differ from the frozen comparison models")
    output = args.output or Path("training/artifacts") / ("ball_comparison_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    output.mkdir(parents=True, exist_ok=False)
    predictions, timings = {}, {}
    print(f"Validation: {len(images)} images; {sum(len(row['truth']) for row in images)} labeled balls", flush=True)
    print(f"Output: {output.resolve()}", flush=True)
    for name, path in paths.items():
        model = YOLO(str(path))
        ball_ids = [int(i) for i, label in model.names.items() if str(label).strip().lower() in {"ball", "sports ball"}]
        if not ball_ids:
            raise ValueError(f"No ball class in {path}")
        predictions[name], timings[name] = {}, []
        for index, item in enumerate(images, 1):
            start = time.perf_counter()
            result = model.predict(str(item["path"]), imgsz=args.imgsz, conf=min(THRESHOLDS),
                                   iou=args.nms_iou, max_det=300, rect=True, augment=False,
                                   device=args.device, save=False, verbose=False)[0].cpu()
            elapsed = time.perf_counter() - start
            balls = [{"xyxy": row[:4], "confidence": float(row[4])} for row in result.boxes.data.tolist()
                     if int(row[5]) in ball_ids]
            predictions[name][item["path"].name] = balls
            timings[name].append(elapsed)
            print(f"{name} [{index}/{len(images)}] {item['path'].name.split('_jpg')[0]}: {len(balls)} candidates, {elapsed:.2f}s", flush=True)
        (output / f"{name}_predictions.json").write_text(json.dumps(predictions[name], indent=2), encoding="utf-8")
        del result, model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    summary, per_image = [], []
    for name in paths:
        for threshold in THRESHOLDS:
            total = dict(tp=0, fp=0, fn=0)
            for item in images:
                counts, _ = score_balls(predictions[name][item["path"].name], item["truth"], threshold, args.match_iou)
                for key in total:
                    total[key] += counts[key]
                per_image.append({"model": name, "conf": threshold, "filename": item["path"].name, **counts})
            summary.append({"model": name, "conf": threshold, **metrics(total)})
    for threshold in THRESHOLDS:
        panels = output / "comparison" / f"conf_{threshold:.2f}"
        panels.mkdir(parents=True)
        for item in images:
            name = item["path"].name
            panel = make_panel(item["path"], item["truth"], predictions["old_best"][name],
                               predictions["new_ball"][name], threshold, args.match_iou)
            panel.save(panels / name, quality=92)
    write_csv(output / "ball_summary.csv", summary)
    write_csv(output / "ball_per_image.csv", per_image)
    report = {
        "split": "validation", "clip": "tJnScrAKJfI", "images": len(images),
        "ground_truth_balls": sum(len(item["truth"]) for item in images),
        "thresholds": list(THRESHOLDS), "imgsz": args.imgsz, "nms_iou": args.nms_iou,
        "match_iou": args.match_iou, "max_det": 300, "rect": True, "augment": False,
        "model_sha256": hashes, "device": args.device,
        "matching": "confidence-ordered greedy, one-to-one, ball class only; not mAP",
        "inference": "both models rerun in same environment, full frame, no tiling; infer once at .15 and filter post-NMS outputs",
        "scope": "Validation only; no training, no Test evaluation, no backend configuration changes",
        "summary": summary,
        "timing_seconds": {name: {"total": sum(values), "first_image": values[0],
                                   "mean_excluding_first": sum(values[1:]) / len(values[1:])}
                           for name, values in timings.items()},
        "environment": {package: version(package) for package in ("ultralytics", "torch", "torchvision", "numpy", "pillow")},
    }
    (output / "ball_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with zipfile.ZipFile(output.with_suffix(".zip"), "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(output.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(output))
    print(json.dumps(summary, indent=2), flush=True)
    print(f"ZIP: {output.with_suffix('.zip').resolve()}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("training/data/prepared/football-v1-ready"))
    parser.add_argument("--primary-model", type=Path, default=Path("backend/models/best.pt"))
    parser.add_argument("--ball-model", type=Path, default=Path("backend/models/football-ball-detection.pt"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--nms-iou", type=float, default=0.70)
    parser.add_argument("--match-iou", type=float, default=0.50)
    args = parser.parse_args()
    if args.imgsz <= 0 or not 0 < args.nms_iou <= 1 or not 0 < args.match_iou <= 1:
        parser.error("Image size must be positive and IoU values must be in (0, 1]")
    run(args)


if __name__ == "__main__":
    main()
