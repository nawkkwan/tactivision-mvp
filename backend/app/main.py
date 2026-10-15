from __future__ import annotations

import hashlib

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .schemas import (
    CalibrateRequest,
    CalibrateResponse,
    DetectResponse,
    ImageMetadata,
    SimulateRequest,
    SimulateResponse,
)
from .services.calibration import attempt_auto_calibration, calibrate_manual
from .services.detection import Detector, ModelUnavailableError
from .services.simulation import simulate_pass
from .services.team_classifier import classify_teams


app = FastAPI(
    title="TactiVision API",
    version="0.1.0",
    description="Pass Interception Risk Simulation จากภาพนิ่งฟุตบอล",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
detector = Detector(settings.model_path)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "model": detector.metadata.model,
        "model_mode": detector.metadata.mode,
        "model_loaded": detector.loaded,
        "model_error": detector.load_error,
        "modules": {
            "detection": "ready",
            "team_classification": "ready",
            "calibration": "ready",
            "simulation": "ready",
        },
    }


@app.post("/detect", response_model=DetectResponse)
async def detect(file: UploadFile = File(...)) -> DetectResponse:
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="รองรับเฉพาะไฟล์ JPEG, PNG และ WebP")

    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="ไฟล์ภาพต้องมีขนาดไม่เกิน 10 MB")
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=422, detail="ไม่สามารถอ่านข้อมูลภาพได้")

    try:
        detections = detector.predict(image)
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    detections = classify_teams(image, detections)
    calibration, calibrated_detections = attempt_auto_calibration(image, detections)
    height, width = image.shape[:2]
    return DetectResponse(
        image=ImageMetadata(
            width=width,
            height=height,
            fingerprint=hashlib.sha256(content).hexdigest(),
        ),
        detector=detector.metadata,
        detections=calibrated_detections,
        calibration=calibration,
    )


@app.post("/calibrate", response_model=CalibrateResponse)
def calibrate(payload: CalibrateRequest) -> CalibrateResponse:
    return calibrate_manual(payload)


@app.post("/simulate", response_model=SimulateResponse)
def simulate(payload: SimulateRequest) -> SimulateResponse:
    return simulate_pass(payload)

