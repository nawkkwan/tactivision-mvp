from __future__ import annotations

import math

import cv2
import numpy as np

from ..schemas import (
    CalibrationResult,
    CalibrateRequest,
    CalibrateResponse,
    Detection,
    Point2D,
)


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
MAX_MANUAL_REPROJECTION_ERROR = 2.0
FIELD_EDGE_TOLERANCE = 1.0


def _apply_homography(point: Point2D, matrix: np.ndarray) -> Point2D | None:
    source = np.array([[[point.x, point.y]]], dtype=np.float64)
    transformed = cv2.perspectiveTransform(source, matrix)[0][0]
    x, y = float(transformed[0]), float(transformed[1])
    if not np.isfinite([x, y]).all():
        return None
    if (
        x < -FIELD_EDGE_TOLERANCE
        or x > PITCH_LENGTH + FIELD_EDGE_TOLERANCE
        or y < -FIELD_EDGE_TOLERANCE
        or y > PITCH_WIDTH + FIELD_EDGE_TOLERANCE
    ):
        return None
    # Small RANSAC errors near a touchline should not create markers outside the
    # playable area. Larger errors are rejected above instead of being snapped.
    return Point2D(
        x=round(min(PITCH_LENGTH, max(0.0, x)), 3),
        y=round(min(PITCH_WIDTH, max(0.0, y)), 3),
    )


def _with_field_positions(detections: list[Detection], matrix: np.ndarray) -> list[Detection]:
    updated: list[Detection] = []
    for detection in detections:
        field_position = _apply_homography(detection.foot_pixel, matrix)
        updated.append(detection.model_copy(update={"field_position": field_position}))
    return updated


def _field_markings() -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """A lightweight FIFA-pitch line template used only to validate auto calibration."""
    markings: list[tuple[tuple[float, float], tuple[float, float]]] = [
        ((0, 0), (105, 0)),
        ((105, 0), (105, 68)),
        ((105, 68), (0, 68)),
        ((0, 68), (0, 0)),
        ((52.5, 0), (52.5, 68)),
        ((0, 13.84), (16.5, 13.84)),
        ((16.5, 13.84), (16.5, 54.16)),
        ((16.5, 54.16), (0, 54.16)),
        ((105, 13.84), (88.5, 13.84)),
        ((88.5, 13.84), (88.5, 54.16)),
        ((88.5, 54.16), (105, 54.16)),
    ]
    circle = [
        (52.5 + 9.15 * math.cos(index * math.tau / 48),
         34 + 9.15 * math.sin(index * math.tau / 48))
        for index in range(49)
    ]
    markings.extend((circle[index], circle[index + 1]) for index in range(48))
    return markings


def _marking_support(
    white_mask: np.ndarray, field_to_image: np.ndarray
) -> tuple[float, float]:
    """Return observed-line support and the fraction of template samples in-frame."""
    height, width = white_mask.shape
    distance = cv2.distanceTransform(
        cv2.bitwise_not(white_mask), cv2.DIST_L2, 3
    )
    supported = 0
    visible = 0
    total = 0
    for start, end in _field_markings():
        length = math.dist(start, end)
        count = max(2, int(length * 4))
        field_points = np.array(
            [
                [
                    start[0] + (end[0] - start[0]) * index / count,
                    start[1] + (end[1] - start[1]) * index / count,
                ]
                for index in range(count + 1)
            ],
            dtype=np.float32,
        ).reshape(-1, 1, 2)
        image_points = cv2.perspectiveTransform(field_points, field_to_image).reshape(-1, 2)
        finite = np.isfinite(image_points).all(axis=1)
        in_frame = (
            finite
            & (image_points[:, 0] >= 0)
            & (image_points[:, 0] < width)
            & (image_points[:, 1] >= 0)
            & (image_points[:, 1] < height)
        )
        total += len(image_points)
        visible += int(in_frame.sum())
        if in_frame.any():
            pixels = np.rint(image_points[in_frame]).astype(int)
            supported += int((distance[pixels[:, 1], pixels[:, 0]] <= 6).sum())
    return supported / max(visible, 1), visible / max(total, 1)


def calibrate_manual(payload: CalibrateRequest) -> CalibrateResponse:
    source = np.array(
        [[pair.image.x, pair.image.y] for pair in payload.correspondences], dtype=np.float64
    )
    destination = np.array(
        [[pair.field.x, pair.field.y] for pair in payload.correspondences], dtype=np.float64
    )

    if (
        np.any(source[:, 0] < 0)
        or np.any(source[:, 0] > payload.image_width)
        or np.any(source[:, 1] < 0)
        or np.any(source[:, 1] > payload.image_height)
    ):
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=0,
            message="มีจุดอ้างอิงอยู่นอกขอบภาพ กรุณาเลือกจุดบนภาพใหม่",
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)

    if (
        np.any(destination[:, 0] < 0)
        or np.any(destination[:, 0] > PITCH_LENGTH)
        or np.any(destination[:, 1] < 0)
        or np.any(destination[:, 1] > PITCH_WIDTH)
    ):
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=0,
            message="พิกัดอ้างอิงต้องอยู่ในสนาม 105 × 68 เมตร",
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)

    source_area = cv2.contourArea(cv2.convexHull(source.astype(np.float32)))
    destination_area = cv2.contourArea(cv2.convexHull(destination.astype(np.float32)))
    minimum_source_area = payload.image_width * payload.image_height * 0.0005
    if source_area < minimum_source_area or destination_area < 5:
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=0,
            message="จุดอ้างอิงในภาพอยู่ใกล้แนวเดียวกันเกินไป กรุณาเลือกจุดที่กระจายมากขึ้น",
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)

    matrix, inlier_mask = cv2.findHomography(source, destination, cv2.RANSAC, 3.0)
    if matrix is None or inlier_mask is None or int(inlier_mask.sum()) < 4:
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=0,
            message="ไม่สามารถคำนวณ Homography จากจุดที่เลือกได้",
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)

    matrix_scale = matrix[2, 2]
    if abs(matrix_scale) < 1e-12:
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=0,
            message="Homography ไม่เสถียร กรุณาเลือกจุดที่กระจายรอบภาพมากขึ้น",
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)
    matrix = matrix / matrix_scale
    projected = cv2.perspectiveTransform(source.reshape(-1, 1, 2), matrix).reshape(-1, 2)
    errors = np.linalg.norm(projected - destination, axis=1)
    rmse = float(math.sqrt(float(np.mean(np.square(errors)))))
    inlier_ratio = float(inlier_mask.mean())
    confidence = max(0.0, min(1.0, inlier_ratio * math.exp(-rmse / 3.0)))

    if not np.isfinite(matrix).all() or rmse > MAX_MANUAL_REPROJECTION_ERROR:
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=round(confidence, 3),
            reprojection_error=round(rmse, 3),
            message=(
                f"Reprojection Error {rmse:.2f} เมตร สูงเกินเกณฑ์ "
                f"{MAX_MANUAL_REPROJECTION_ERROR:.1f} เมตร กรุณาเลือกจุดที่กระจายและตรงเส้นจริงใหม่"
            ),
        )
        return CalibrateResponse(calibration=result, detections=payload.detections)

    result = CalibrationResult(
        status="success",
        method="manual",
        confidence=round(confidence, 3),
        reprojection_error=round(rmse, 3),
        matrix=matrix.tolist(),
        message="Manual Calibration สำเร็จ",
    )
    return CalibrateResponse(
        calibration=result,
        detections=_with_field_positions(payload.detections, matrix),
    )


def attempt_auto_calibration(
    image: np.ndarray, detections: list[Detection]
) -> tuple[CalibrationResult, list[Detection]]:
    height, width = image.shape[:2]
    scale = min(1.0, 1280.0 / max(width, height))
    working = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1 else image.copy()
    hsv = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, np.array([28, 30, 25]), np.array([95, 255, 255]))
    kernel = np.ones((9, 9), dtype=np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    failure = CalibrationResult(
        status="needs_manual",
        method="auto",
        confidence=0,
        message="Auto Calibration ยังยืนยันเส้นสนามได้ไม่พอ กรุณาเลือกจุดอ้างอิงด้วย Manual Calibration",
    )
    if not contours:
        return failure, detections

    largest = max(contours, key=cv2.contourArea)
    image_area = float(working.shape[0] * working.shape[1])
    green_coverage = cv2.contourArea(largest) / image_area
    perimeter = cv2.arcLength(largest, True)
    polygon = cv2.approxPolyDP(largest, 0.025 * perimeter, True)

    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
    white_mask = cv2.inRange(hsv, np.array([0, 0, 150]), np.array([179, 95, 255]))
    edges = cv2.Canny(cv2.bitwise_and(gray, gray, mask=white_mask), 60, 150)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=max(40, int(min(working.shape[:2]) * 0.08)),
        minLineLength=max(35, int(min(working.shape[:2]) * 0.12)),
        maxLineGap=25,
    )
    line_count = 0 if lines is None else len(lines)

    if len(polygon) != 4 or green_coverage < 0.35 or line_count < 4:
        confidence = min(0.49, green_coverage * 0.7 + min(line_count, 4) * 0.04)
        return failure.model_copy(update={"confidence": round(confidence, 3)}), detections

    points = polygon.reshape(4, 2).astype(np.float32) / scale
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).reshape(-1)
    ordered = np.array(
        [
            points[np.argmin(sums)],
            points[np.argmin(differences)],
            points[np.argmax(sums)],
            points[np.argmax(differences)],
        ],
        dtype=np.float32,
    )
    # If the visible turf touches the frame edge, it may be a cropped portion of
    # the pitch. Mapping that crop to a full 105 x 68 m field would be misleading.
    edge_margin_x = max(3, int(width * 0.015))
    edge_margin_y = max(3, int(height * 0.015))
    if (
        np.any(ordered[:, 0] <= edge_margin_x)
        or np.any(ordered[:, 0] >= width - edge_margin_x)
        or np.any(ordered[:, 1] <= edge_margin_y)
        or np.any(ordered[:, 1] >= height - edge_margin_y)
    ):
        return failure.model_copy(
            update={"message": "ภาพอาจเห็นสนามไม่ครบ จึงไม่เดาขนาดสนามเต็มให้อัตโนมัติ กรุณาเลือกจุดอ้างอิงด้วยตนเอง"}
        ), detections

    field_corners = np.array([[0, 0], [105, 0], [105, 68], [0, 68]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(ordered, field_corners)
    if not np.isfinite(matrix).all():
        return failure, detections

    field_to_image = np.linalg.inv(matrix)
    line_support, template_visibility = _marking_support(white_mask, field_to_image)
    # This is an evidence score, not a statistically calibrated probability.
    confidence = min(0.95, 0.2 + line_support * 0.75 + min(green_coverage, 0.8) * 0.0625)

    if confidence < 0.72 or line_support < 0.55 or template_visibility < 0.8:
        return failure.model_copy(
            update={
                "confidence": round(confidence, 3),
                "message": "เส้นสนามที่ตรวจพบไม่สอดคล้องกับแบบจำลองสนามเต็มพอ ระบบจึงไม่ใช้ Auto และขอให้กำหนดจุดอ้างอิงเอง",
            }
        ), detections

    result = CalibrationResult(
        status="success",
        method="auto",
        confidence=round(confidence, 3),
        matrix=matrix.tolist(),
        message="Auto Calibration ผ่านการตรวจแนวเส้นสนามแล้ว (คะแนนนี้เป็นคะแนนหลักฐานแบบทดลอง ไม่ใช่ความแม่นยำเชิงสถิติ) กรุณาตรวจตำแหน่งก่อนใช้ผล",
    )
    return result, _with_field_positions(detections, matrix)

