from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


MAP_EVALUATION_CONFIDENCE_THRESHOLD = 0.001


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate detector mAP independently from the web inference threshold."
    )
    parser.add_argument("--model", default="backend/models/best.pt")
    parser.add_argument("--data", default="training/data.yaml")
    parser.add_argument("--split", default="val", choices=("val", "test"))
    parser.add_argument(
        "--conf",
        type=float,
        default=MAP_EVALUATION_CONFIDENCE_THRESHOLD,
        help="Minimum confidence retained while building the PR curve (default: 0.001).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0 <= args.conf <= 1:
        raise SystemExit("--conf must be between 0 and 1")

    config_dir = Path(os.getenv("YOLO_CONFIG_DIR", ".cache/ultralytics")).resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config_dir)
    from ultralytics import YOLO

    metrics = YOLO(args.model).val(
        data=args.data,
        split=args.split,
        conf=args.conf,
        plots=True,
    )
    summary = {
        "model": str(Path(args.model)),
        "data": str(Path(args.data)),
        "split": args.split,
        "map_evaluation_confidence_threshold": args.conf,
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
