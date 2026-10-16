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
    def __init__(
        self,
        model_path: str,
        *,
        ball_model_path: str | None = None,
        confidence: float = 0.25,
        ball_confidence: float = 0.15,
        imgsz: int = 1280,
    ) -> None:
        self.model_path = model_path
        self.ball_model_path = ball_model_path
        self.confidence = confidence
        self.ball_confidence = ball_confidence
        self.imgsz = imgsz
        self._model = None
        self._ball_model = None
        self._lock = Lock()
        self._inference_lock = Lock()
        self.load_error: str | None = None
        self.ball_load_error: str | None = None

    @property
    def mode(self) -> str:
        return "fine_tuned" if Path(self.model_path).name.lower() == "best.pt" else "generic"

    @property
    def metadata(self) -> DetectorMetadata:
        return DetectorMetadata(model=Path(self.model_path).name, mode=self.mode)  # type: ignore[arg-type]

    @property
    def loaded(self) -> bool:
        return self._model is not None

    @property
    def ball_status(self) -> dict[str, object]:
        if not self.ball_model_path:
            mode = "disabled"
        elif self.ball_load_error:
            mode = "fallback"
        elif self._ball_model is None:
            mode = "lazy"
        else:
            mode = "ready"
        return {
            "model": Path(self.ball_model_path).name if self.ball_model_path else None,
            "mode": mode,
            "loaded": self._ball_model is not None,
            "source": "specialized" if mode == "ready" else "combined" if mode in {"disabled", "fallback"} else "pending",
            "confidence": self.ball_confidence,
            "error": self.ball_load_error,
        }

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

    def _load_ball(self):
        if not self.ball_model_path:
            return None
        if self._ball_model is not None:
            return self._ball_model
        with self._lock:
            if self._ball_model is not None:
                return self._ball_model
            try:
                path = Path(self.ball_model_path)
                if not path.is_file() or path.stat().st_size == 0:
                    raise FileNotFoundError("ไม่พบไฟล์โมเดลบอล ให้รัน python -m backend.app.download_ball_model")
                # The primary model has initialized Ultralytics' local config.
                # Do not auto-download weights inside an API request.
                from ultralytics import YOLO

                model = YOLO(str(path))
                names = model.names.values() if isinstance(model.names, dict) else model.names
                if not any(CLASS_ALIASES.get(str(name).lower().strip()) == "ball" for name in names):
                    raise ValueError("โมเดลบอลไม่มีคลาส ball หรือ sports ball")
                self._ball_model = model
                self.ball_load_error = None
            except Exception as exc:
                self.ball_load_error = str(exc)
        return self._ball_model

    @staticmethod
    def _read_results(results) -> list[tuple[str, list[float], float]]:
        if not results:
            return []
        result = results[0]
        boxes = result.boxes
        if boxes is None:
            return []
        records = []
        for xyxy, confidence, class_index in zip(
            boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy(), boxes.cls.cpu().numpy()
        ):
            raw_name = str(result.names[int(class_index)]).lower().strip()
            class_name = CLASS_ALIASES.get(raw_name)
            if class_name is not None:
                records.append((class_name, [float(value) for value in xyxy], float(confidence)))
        return records

    def predict(self, image: np.ndarray) -> list[Detection]:
        # Ultralytics caches predictor state. Serialize calls to shared models.
        with self._inference_lock:
            model = self._load()
            results = model.predict(
                source=image, conf=self.confidence, imgsz=self.imgsz, iou=0.55, verbose=False
            )
            records = self._read_results(results)
            ball_model = self._load_ball()
            if ball_model is not None:
                try:
                    ball_results = ball_model.predict(
                        source=image, conf=self.ball_confidence, imgsz=self.imgsz, iou=0.55, verbose=False
                    )
                    specialized_balls = [item for item in self._read_results(ball_results) if item[0] == "ball"]
                    # A successful dedicated pass is authoritative, including
                    # when it finds no ball. Never concatenate both sources.
                    records = [item for item in records if item[0] != "ball"] + specialized_balls
                    self.ball_load_error = None
                except Exception as exc:
                    # Keep original primary-model balls only on failure.
                    self.ball_load_error = f"Ball inference failed: {exc}"
        return self._to_detections(records, image.shape[1], image.shape[0])

    @staticmethod
    def _to_detections(records, image_width: int, image_height: int) -> list[Detection]:
        detections: list[Detection] = []
        player_index = 0
        ball_index = 0
        for class_name, xyxy, confidence in records:
            if not np.isfinite([*xyxy, confidence]).all() or not 0 <= confidence <= 1:
                continue
            x1, y1, x2, y2 = xyxy
            x1, x2 = np.clip([x1, x2], 0, image_width).tolist()
            y1, y2 = np.clip([y1, y2], 0, image_height).tolist()
            width, height = x2 - x1, y2 - y1
            if width <= 0 or height <= 0:
                continue
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

