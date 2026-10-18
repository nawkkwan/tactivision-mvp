from __future__ import annotations

from backend.app.schemas import CalibrateRequest
from backend.app.services.calibration import calibrate_manual


def test_manual_calibration_maps_known_rectangle() -> None:
    payload = CalibrateRequest.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "correspondences": [
                {"image": {"x": 100, "y": 100}, "field": {"x": 0, "y": 0}},
                {"image": {"x": 900, "y": 100}, "field": {"x": 105, "y": 0}},
                {"image": {"x": 900, "y": 600}, "field": {"x": 105, "y": 68}},
                {"image": {"x": 100, "y": 600}, "field": {"x": 0, "y": 68}},
            ],
            "detections": [
                {
                    "id": "p1",
                    "class_name": "player",
                    "confidence": 0.9,
                    "team_id": "team_a",
                    "bbox": {"x": 480, "y": 300, "width": 40, "height": 50},
                    "foot_pixel": {"x": 500, "y": 350},
                }
            ],
        }
    )
    response = calibrate_manual(payload)
    assert response.calibration.status == "success"
    assert response.detections[0].field_position is not None
    assert abs(response.detections[0].field_position.x - 52.5) < 0.1
    assert abs(response.detections[0].field_position.y - 34) < 0.1


def test_collinear_points_are_rejected() -> None:
    payload = CalibrateRequest.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "correspondences": [
                {"image": {"x": 100, "y": 100}, "field": {"x": 0, "y": 0}},
                {"image": {"x": 200, "y": 100}, "field": {"x": 20, "y": 0}},
                {"image": {"x": 300, "y": 100}, "field": {"x": 40, "y": 0}},
                {"image": {"x": 400, "y": 100}, "field": {"x": 60, "y": 0}},
            ],
            "detections": [],
        }
    )
    response = calibrate_manual(payload)
    assert response.calibration.status == "needs_manual"


def test_points_outside_image_are_rejected() -> None:
    payload = CalibrateRequest.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "correspondences": [
                {"image": {"x": -1, "y": 100}, "field": {"x": 0, "y": 0}},
                {"image": {"x": 900, "y": 100}, "field": {"x": 105, "y": 0}},
                {"image": {"x": 900, "y": 600}, "field": {"x": 105, "y": 68}},
                {"image": {"x": 100, "y": 600}, "field": {"x": 0, "y": 68}},
            ],
            "detections": [],
        }
    )
    response = calibrate_manual(payload)
    assert response.calibration.status == "needs_manual"
    assert "นอกขอบภาพ" in response.calibration.message


def test_mapped_detection_far_outside_pitch_is_not_used() -> None:
    payload = CalibrateRequest.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "correspondences": [
                {"image": {"x": 100, "y": 100}, "field": {"x": 0, "y": 0}},
                {"image": {"x": 900, "y": 100}, "field": {"x": 105, "y": 0}},
                {"image": {"x": 900, "y": 600}, "field": {"x": 105, "y": 68}},
                {"image": {"x": 100, "y": 600}, "field": {"x": 0, "y": 68}},
            ],
            "detections": [
                {
                    "id": "p1",
                    "class_name": "player",
                    "confidence": 0.9,
                    "team_id": "team_a",
                    "bbox": {"x": 0, "y": 300, "width": 20, "height": 50},
                    "foot_pixel": {"x": 10, "y": 350},
                }
            ],
        }
    )
    response = calibrate_manual(payload)
    assert response.calibration.status == "success"
    assert response.detections[0].field_position is None


def test_manual_calibration_reports_inconsistent_point_indices() -> None:
    payload = CalibrateRequest.model_validate(
        {
            "image_width": 1000,
            "image_height": 700,
            "correspondences": [
                {"image": {"x": 100, "y": 100}, "field": {"x": 0, "y": 0}},
                {"image": {"x": 900, "y": 100}, "field": {"x": 105, "y": 0}},
                {"image": {"x": 900, "y": 600}, "field": {"x": 105, "y": 68}},
                {"image": {"x": 100, "y": 600}, "field": {"x": 0, "y": 68}},
                {"image": {"x": 500, "y": 350}, "field": {"x": 10, "y": 10}},
            ],
            "detections": [],
        }
    )

    response = calibrate_manual(payload)

    assert response.calibration.status == "needs_manual"
    assert response.calibration.reprojection_error is not None
    assert response.calibration.reprojection_error > 2
    assert response.calibration.outlier_indices == [4]

