from __future__ import annotations

from io import BytesIO
from tempfile import SpooledTemporaryFile

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from backend.app.main import detect, health


def test_health_reports_modules() -> None:
    data = health()
    assert data["status"] == "ok"
    assert data["modules"]["simulation"] == "ready"
    assert data["modules"]["ball_detection"]["mode"] in {
        "lazy", "ready", "disabled", "fallback",
    }
    assert data["modules"]["team_classification"]["mode"] in {
        "lazy",
        "siglip_ready",
        "color_fallback",
    }


def test_detect_rejects_wrong_content_type() -> None:
    upload = UploadFile(
        file=BytesIO(b"hello"),
        filename="notes.txt",
        headers=Headers({"content-type": "text/plain"}),
    )
    with pytest.raises(HTTPException) as error:
        detect(upload).send(None)
    assert error.value.status_code == 415


def test_detect_returns_merged_ball_with_unchanged_contract(monkeypatch) -> None:
    import cv2
    import numpy as np
    from backend.app import main
    from backend.app.schemas import CalibrationResult, Detection, DetectorMetadata

    detection = Detection(
        id="b1", class_name="ball", confidence=.6,
        bbox={"x": 20, "y": 30, "width": 4, "height": 4},
        foot_pixel={"x": 22, "y": 32},
    )
    class FakeDetector:
        metadata = DetectorMetadata(model="best.pt", mode="fine_tuned")

        def predict(self, image):
            return [detection]

    calibration = CalibrationResult(
        status="needs_manual", method="auto", confidence=0, message="test"
    )
    monkeypatch.setattr(main, "detector", FakeDetector())
    monkeypatch.setattr(main, "classify_teams", lambda image, items: items)
    monkeypatch.setattr(main, "attempt_auto_calibration", lambda image, items: (calibration, items))
    success, encoded = cv2.imencode(".png", np.zeros((100, 200, 3), dtype=np.uint8))
    assert success
    image_file = SpooledTemporaryFile(max_size=1024 * 1024)
    image_file.write(encoded.tobytes())
    image_file.seek(0)
    upload = UploadFile(
        file=image_file, filename="pitch.png",
        headers=Headers({"content-type": "image/png"}),
    )
    # In-memory UploadFile reads complete synchronously; avoid creating a
    # Windows event loop (and its sockets) for this small endpoint unit test.
    with pytest.raises(StopIteration) as result:
        main.detect(upload).send(None)
    response = result.value.value
    assert set(response.model_dump()) == {"image", "detector", "detections", "calibration"}
    assert response.detections == [detection]
    assert response.image.width == 200
    image_file.close()

