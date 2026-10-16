from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


EXPECTED_CLASSES = {"player", "goalkeeper", "referee", "ball"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune YOLO11n สำหรับ TactiVision")
    parser.add_argument("--data", required=True, help="ตำแหน่ง data.yaml จาก Dataset Export")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="smoke")
    parser.add_argument("--device", default=None, help="เช่น 0, cpu หรือ mps")
    return parser.parse_args()


def read_class_names(data_yaml: Path) -> list[str]:
    with data_yaml.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    names = config.get("names") if isinstance(config, dict) else None
    if isinstance(names, dict):
        return [str(names[key]).strip() for key in sorted(names, key=lambda value: int(value))]
    if isinstance(names, list):
        return [str(name).strip() for name in names]
    raise ValueError("data.yaml ไม่มี names ที่อ่านได้")


def validate_dataset_config(data_yaml: Path) -> list[str]:
    if not data_yaml.is_file():
        raise FileNotFoundError(f"ไม่พบ data.yaml: {data_yaml}")
    names = read_class_names(data_yaml)
    actual = {name.lower() for name in names}
    if actual != EXPECTED_CLASSES:
        raise ValueError(
            "Dataset ต้องมี 4 คลาส player, goalkeeper, referee, ball "
            f"แต่พบ: {', '.join(names)}"
        )
    return names


def main() -> None:
    args = parse_args()
    data_yaml = Path(args.data).resolve()
    names = validate_dataset_config(data_yaml)
    print(f"Dataset classes: {names}")

    project_dir = Path("training/runs").resolve()
    model = YOLO(args.model)
    train_args = {
        "data": str(data_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": str(project_dir),
        "name": args.name,
        "exist_ok": True,
        "seed": 42,
        "deterministic": True,
        "patience": 15,
        "workers": 2,
    }
    if args.device:
        train_args["device"] = args.device

    results = model.train(**train_args)
    best_path = Path(results.save_dir) / "weights" / "best.pt"
    print(f"Training เสร็จแล้ว: {results.save_dir}")
    print(f"โมเดลที่ต้องส่งต่อ: {best_path}")


if __name__ == "__main__":
    main()
