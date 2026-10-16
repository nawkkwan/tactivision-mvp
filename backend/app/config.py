from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model_path: str = os.getenv("MODEL_PATH", "backend/models/yolo11n.pt")
    ball_model_path: str | None = os.getenv(
        "BALL_MODEL_PATH", "backend/models/football-ball-detection.pt"
    ).strip() or None
    detection_confidence: float = float(os.getenv("DETECTION_CONFIDENCE", "0.25"))
    ball_confidence: float = float(os.getenv("BALL_CONFIDENCE", "0.15"))
    detection_imgsz: int = int(os.getenv("DETECTION_IMGSZ", "1280"))
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

    def __post_init__(self) -> None:
        for name in ("detection_confidence", "ball_confidence"):
            if not 0 < getattr(self, name) <= 1:
                raise ValueError(f"{name} must be greater than 0 and at most 1")
        if self.detection_imgsz <= 0:
            raise ValueError("detection_imgsz must be positive")


settings = Settings()

