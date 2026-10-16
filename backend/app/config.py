from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("MODEL_PATH", "backend/models/yolo11n.pt")
    inference_confidence_threshold: float = float(
        os.getenv("INFERENCE_CONFIDENCE_THRESHOLD", "0.15")
    )
    person_confidence_threshold: float = float(
        os.getenv("PERSON_CONFIDENCE_THRESHOLD", "0.50")
    )
    ball_confidence_threshold: float = float(
        os.getenv("BALL_CONFIDENCE_THRESHOLD", "0.15")
    )
    inference_iou_threshold: float = float(os.getenv("INFERENCE_IOU_THRESHOLD", "0.55"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173,http://127.0.0.1:4173",
        ).split(",")
        if origin.strip()
    )
    cors_origin_regex: str | None = os.getenv("CORS_ORIGIN_REGEX") or None


settings = Settings()

