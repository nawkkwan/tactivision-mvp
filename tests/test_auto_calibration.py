from __future__ import annotations

import cv2
import numpy as np

from backend.app.services.calibration import attempt_auto_calibration


def test_wide_pitch_with_clear_lines_can_produce_experimental_calibration() -> None:
    image = np.zeros((500, 800, 3), dtype=np.uint8)
    cv2.rectangle(image, (45, 35), (755, 465), (45, 130, 55), -1)
    cv2.rectangle(image, (45, 35), (755, 465), (245, 245, 245), 5)
    cv2.line(image, (400, 35), (400, 465), (245, 245, 245), 5)
    cv2.circle(image, (400, 250), 70, (245, 245, 245), 5)
    cv2.rectangle(image, (45, 145), (180, 355), (245, 245, 245), 5)
    cv2.rectangle(image, (620, 145), (755, 355), (245, 245, 245), 5)

    calibration, _ = attempt_auto_calibration(image, [])
    assert calibration.status == "success"
    assert calibration.method == "auto"
    assert calibration.confidence >= 0.7
    assert calibration.matrix is not None

