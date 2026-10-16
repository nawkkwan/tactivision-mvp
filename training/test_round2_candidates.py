"""Compare frozen round-one/two weights on the original candidate Test frames.

Run from the repository root: python -m training.test_round2_candidates
Never trains, changes thresholds, edits source images/labels or replaces backend weights.
"""
from __future__ import annotations

from datetime import datetime
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import time
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

from training.round2_workflow import (
    DISPLAY_THRESHOLDS, EXPECTED, INITIAL_SHA256, file_sha256, fixed_counts,
    metric_summary, parse_labels, write_csv, write_json,
)


ROOT = Path(__file__).resolve().parents[1]
ROUND2_SHA256 = "b490d9e1f8ff613f61b2d8a8522200b4ce43b613a7544708753e812f9589ec38"


def stage_candidates(candidates, frozen, destination):
    """Require a complete one-to-one match and unchanged labels; copy only to a new run."""
    records = json.loads((frozen / "test_manifest.json").read_text(encoding="utf-8"))
    images = sorted(candidates.rglob("*.jpg"))
    by_name = {p.name: p for p in images}
    expected = {r["filename"].split("_jpg.rf.")[0] + ".jpg" for r in records}
    if len(records) != 30 or len(by_name) != len(images) or set(by_name) != expected:
        raise ValueError("Expected exactly the 30 original reserved Test frames, with unique names")
    rows = []
    for record in records:
        name = record["filename"].split("_jpg.rf.")[0] + ".jpg"
        candidate = by_name[name]
        reference = frozen / "test/images" / record["filename"]
        label = frozen / "test/labels" / record["label"]
        if file_sha256(reference) != record["sha256"] or file_sha256(label) != record["label_sha256"]:
            raise ValueError("Frozen Test checksum mismatch")
        with Image.open(candidate) as a, Image.open(reference) as b:
            if a.size != b.size or a.size != (record["width"], record["height"]):
                raise ValueError(f"Image dimensions changed: {name}")
            means = ImageStat.Stat(ImageChops.difference(a.convert("RGB"), b.convert("RGB"))).mean
        # Roboflow has re-encoded the frame. Reject visibly different frames;
        # no scaling, translation or guessed timestamp matching is permitted.
        if max(means) > 8:
            raise ValueError(f"Candidate does not align with labeled reference: {name}")
        parse_labels(label.read_bytes(), record["width"], record["height"])
        target_image = destination / "images" / name
        target_label = destination / "labels" / (Path(name).stem + ".txt")
        target_image.parent.mkdir(parents=True, exist_ok=True)
        target_label.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate, target_image)
        shutil.copyfile(label, target_label)
        rows.append({"filename": name, "source": str(candidate),
                     "sha256": file_sha256(candidate), "label_sha256": file_sha256(label),
                     "reference_filename": record["filename"],
                     "reference_sha256": record["sha256"], "pixel_mae_rgb": means,
                     "width": record["width"], "height": record["height"]})
    return rows


def read_predictions(path, width, height):
    if not path.exists():
        return []
    boxes = []
    for line in path.read_text().splitlines():
        c, x, y, w, h, confidence = map(float, line.split())
        boxes.append({"class_id": int(c), "confidence": confidence,
                      "xyxy": [(x-w/2)*width, (y-h/2)*height, (x+w/2)*width, (y+h/2)*height]})
    return boxes


def displayed(predictions):
    return [p for p in predictions if p["confidence"] >= DISPLAY_THRESHOLDS[EXPECTED[p["class_id"]]]]


def render(image, boxes, font):
    image = image.copy()
    draw = ImageDraw.Draw(image)
    colors = ["#00ffff", "#ffff00", "#00ff66", "#ff44ff"]
    for box in boxes:
        x1, y1, x2, y2 = box["xyxy"]
        c = box["class_id"]
        draw.rectangle((x1, y1, x2, y2), outline=colors[c], width=2)
        text = EXPECTED[c] + (f" {box['confidence']:.2f}" if "confidence" in box else "")
        draw.text((max(0, x1), max(0, y1-16)), text, fill=colors[c], font=font,
                  stroke_width=1, stroke_fill="black")
    return image


def main():
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".cache/ultralytics"))
    os.environ.pop("SSLKEYLOGFILE", None)
    from ultralytics import YOLO
    import torch

    run = ROOT / "training/artifacts" / datetime.now().strftime("candidate_test_round2_%Y%m%d_%H%M%S_%f")
    run.mkdir(parents=True, exist_ok=False)
    candidates = ROOT / "training/data/candidates/test"
    frozen = ROOT / "training/data/prepared/football-v2-test-ready"
    rows = stage_candidates(candidates, frozen, run / "dataset")
    write_json(run / "candidate_manifest.json", rows)
    config = run / "candidate_test.yaml"
    write_json(config, {"path": str(run / "dataset"), "train": "images", "val": "images",
                        "test": "images", "nc": 4, "names": EXPECTED})
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    models = {
        "round1": (ROOT / "backend/models/best.pt", INITIAL_SHA256),
        "round2": (ROOT / "training/artifacts/round2_review/best_round2.pt", ROUND2_SHA256),
    }
    scores, all_predictions, fixed_rows = {}, {}, []
    per_image = []
    eval_args = dict(split="test", imgsz=1280, batch=1, conf=.001, iou=.7, rect=True,
                     augment=False, half=False, max_det=300, device="cpu", workers=0,
                     seed=42, deterministic=True, save_txt=True, save_conf=True,
                     plots=True, verbose=True)
    for phase, (model_path, expected_hash) in models.items():
        if file_sha256(model_path) != expected_hash:
            raise ValueError(f"Unexpected model checksum: {phase}")
        print(f"START {phase} on {len(rows)} candidate frames", flush=True)
        model = YOLO(str(model_path))
        if [model.names[i] for i in range(4)] != EXPECTED:
            raise ValueError("Unexpected model class mapping")
        started = time.perf_counter()
        metrics = model.val(data=str(config), project=str(run / "evaluations"),
                            name=phase, exist_ok=False, **eval_args)
        scores[phase] = {**metric_summary(metrics), "wall_seconds": time.perf_counter()-started,
                         "speed_ms_per_image": metrics.speed, "model_sha256": expected_hash}
        prediction_dir = Path(metrics.save_dir) / "labels"
        predictions = {}
        totals = [{"tp": 0, "fp": 0, "fn": 0} for _ in EXPECTED]
        (run / phase).mkdir()
        for row in rows:
            name, width, height = row["filename"], row["width"], row["height"]
            pred = read_predictions(prediction_dir / (Path(name).stem + ".txt"), width, height)
            predictions[name] = pred
            truth = parse_labels((run / "dataset/labels" / (Path(name).stem + ".txt")).read_bytes(), width, height)
            accepted = displayed(pred)
            counts = fixed_counts(accepted, truth, 0)
            for c in range(4):
                for key in totals[c]:
                    totals[c][key] += counts[c][key]
                per_image.append({"model": phase, "filename": name, "class": EXPECTED[c], **counts[c]})
            with Image.open(run / "dataset/images" / name) as image:
                render(image.convert("RGB"), accepted, font).save(run / phase / name, quality=95)
        for c, counts in enumerate(totals):
            tp, fp, fn = (counts[key] for key in ("tp", "fp", "fn"))
            fixed_rows.append({"model": phase, "class": EXPECTED[c], "conf": DISPLAY_THRESHOLDS[EXPECTED[c]],
                               **counts, "precision": tp/(tp+fp) if tp+fp else 0.,
                               "recall": tp/(tp+fn) if tp+fn else 0.})
        all_predictions[phase] = predictions
        write_json(run / "metrics.json", scores)
        write_json(run / phase / "predictions.json", predictions)
        print(f"DONE {phase}: {json.dumps(scores[phase])}", flush=True)
        del model, metrics

    comparison_dir = run / "comparisons"
    comparison_dir.mkdir()
    for row in rows:
        name, width, height = row["filename"], row["width"], row["height"]
        with Image.open(run / "dataset/images" / name) as image:
            truth = parse_labels((run / "dataset/labels" / (Path(name).stem + ".txt")).read_bytes(), width, height)
            reference = render(image.convert("RGB"), truth, font)
        panel = Image.new("RGB", (width*3, height+70), "white")
        panel.paste(reference, (0,70))
        for i, phase in enumerate(models, 1):
            with Image.open(run / phase / name) as image:
                panel.paste(image, (width*i,70))
        draw = ImageDraw.Draw(panel)
        for i, title in enumerate(("LABEL REFERENCE", "ROUND 1", "ROUND 2")):
            draw.text((width*i+10, 7), title, font=title_font, fill="black")
        draw.text((10,40), name + " | People >= 0.50; ball >= 0.15; same settings for both models", font=font, fill="black")
        panel.save(comparison_dir / name, quality=92)
    # Three manageable review pages, not just the first three result images.
    for page in range(3):
        sheet = Image.new("RGB", (1280, 5*392), "white")
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(rows[page*10:(page+1)*10]):
            x, y = (index%2)*640, (index//2)*392
            with Image.open(run / "round2" / row["filename"]) as image:
                sheet.paste(image.resize((640,360)), (x,y+32))
            draw.text((x+5,y+5), row["filename"], font=font, fill="black")
        sheet.save(run / f"round2_overview_{page+1}.jpg", quality=92)
    write_csv(run / "fixed_threshold_comparison.csv", fixed_rows)
    write_csv(run / "per_image_counts.csv", per_image)
    report = {"purpose": "frozen_model_comparison_on_original_candidate_test_pixels",
              "images": len(rows), "classes": EXPECTED, "display_thresholds": DISPLAY_THRESHOLDS,
              "evaluation_args": eval_args, "scores": scores, "fixed_threshold_counts": fixed_rows,
              "environment": {"ultralytics": version("ultralytics"), "torch": torch.__version__},
              "caveats": ["Same 30 Test scenes evaluated previously; not a new independent match.",
                          "Original candidate JPEGs differ from Roboflow re-encoded JPEGs; same-coordinate frozen labels reused after alignment checks.",
                          "No Test-based parameter selection, retraining, dedicated ball model or team classifier.",
                          "Fixed counts use confidence-ordered same-class one-to-one IoU >= 0.50 matching; labels may be imperfect."]}
    write_json(run / "report.json", report)
    # Verify no input images or backend weights were changed during evaluation.
    for row in rows:
        if file_sha256(Path(row["source"])) != row["sha256"]:
            raise ValueError("Source candidate changed during evaluation")
    if file_sha256(models["round1"][0]) != INITIAL_SHA256:
        raise ValueError("Backend model changed during evaluation")
    archive_path = run.with_suffix(".zip")
    with ZipFile(archive_path, "x", compression=ZIP_DEFLATED) as archive:
        for file in sorted(run.rglob("*")):
            relative = file.relative_to(run)
            if file.is_file() and relative.parts[0] != "dataset":
                archive.write(file, relative.as_posix())
    print(f"RESULT_DIRECTORY={run}", flush=True)
    print(f"RESULT_ZIP={archive_path}", flush=True)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
