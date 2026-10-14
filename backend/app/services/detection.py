from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

import numpy as np

from ..schemas import BoundingBox, Detection, DetectorMetadata, Point2D


CLASS_ALIASES = {
    "person": "player",
    "player": "player",
    "goalkeeper": "goalkeeper",
    "goalie": "goalkeeper",
    "referee": "referee",
    "sports ball": "ball",
    "ball": "ball",
}


class ModelUnavailableError(RuntimeError):
    pass


class Detector:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self._model = None
        self._lock = Lock()
        self.load_error: str | None = None

    @property
    def mode(self) -> str:
        return "fine_tuned" if Path(self.model_path).name.lower() == "best.pt" else "generic"

    @property
    def metadata(self) -> DetectorMetadata:
        return DetectorMetadata(model=Path(self.model_path).name, mode=self.mode)  # type: ignore[arg-type]

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def _load(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                config_dir = Path(os.getenv("YOLO_CONFIG_DIR", ".cache/ultralytics")).resolve()
                config_dir.mkdir(parents=True, exist_ok=True)
                os.environ["YOLO_CONFIG_DIR"] = str(config_dir)
                from ultralytics import YOLO

                self._model = YOLO(self.model_path)
                self.load_error = None
            except Exception as exc:  # dependency/download errors need a clear API response
                self.load_error = str(exc)
                raise ModelUnavailableError(
                    "ไม่สามารถโหลดโมเดลตรวจจับได้ ตรวจ MODEL_PATH และการเชื่อมต่ออินเทอร์เน็ตครั้งแรก"
                ) from exc
        return self._model

    def predict(self, image: np.ndarray) -> list[Detection]:
        model = self._load()
        results = model.predict(source=image, conf=0.25, iou=0.55, verbose=False)
        if not results:
            return []

        result = results[0]
        names = result.names
        detections: list[Detection] = []
        player_index = 0
        ball_index = 0
        boxes = result.boxes
        if boxes is None:
            return []

        for xyxy, confidence, class_index in zip(
            boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy(), boxes.cls.cpu().numpy()
        ):
            raw_name = str(names[int(class_index)]).lower().strip()
            class_name = CLASS_ALIASES.get(raw_name)
            if class_name is None:
                continue
            x1, y1, x2, y2 = [float(value) for value in xyxy]
            width = max(1.0, x2 - x1)
            height = max(1.0, y2 - y1)
            if class_name == "ball":
                ball_index += 1
                identifier = f"b{ball_index}"
            else:
                player_index += 1
                identifier = f"p{player_index}"
            foot = (
                Point2D(x=x1 + width / 2, y=y1 + height / 2)
                if class_name == "ball"
                else Point2D(x=x1 + width / 2, y=y2)
            )
            detections.append(
                Detection(
                    id=identifier,
                    class_name=class_name,  # type: ignore[arg-type]
                    confidence=round(float(confidence), 4),
                    bbox=BoundingBox(x=x1, y=y1, width=width, height=height),
                    foot_pixel=foot,
                )
            )
        return detections

