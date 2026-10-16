from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

from train_detector import validate_dataset_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ประเมิน best.pt บน Test Set")
    parser.add_argument("--model", required=True, help="ตำแหน่ง best.pt")
    parser.add_argument("--data", required=True, help="ตำแหน่ง data.yaml")
    parser.add_argument(
        "--output",
        default="training/reports/metrics.json",
        help="ไฟล์เก็บผล Metrics",
    )
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model).resolve()
    data_yaml = Path(args.data).resolve()
    output_path = Path(args.output).resolve()

    if not model_path.is_file():
        raise FileNotFoundError(f"ไม่พบโมเดล: {model_path}")
    class_names = validate_dataset_config(data_yaml)

    model = YOLO(str(model_path))
    val_args = {"data": str(data_yaml), "split": "test", "verbose": True}
    if args.device:
        val_args["device"] = args.device
    metrics = model.val(**val_args)

    per_class_map = {
        class_names[index]: round(float(value), 6)
        for index, value in enumerate(metrics.box.maps)
        if index < len(class_names)
    }
    report = {
        "model": str(model_path),
        "data": str(data_yaml),
        "precision": round(float(metrics.box.mp), 6),
        "recall": round(float(metrics.box.mr), 6),
        "map50": round(float(metrics.box.map50), 6),
        "map50_95": round(float(metrics.box.map), 6),
        "map50_95_by_class": per_class_map,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"บันทึกผลที่: {output_path}")


if __name__ == "__main__":
    main()
