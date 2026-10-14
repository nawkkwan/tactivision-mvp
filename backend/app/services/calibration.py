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


def _apply_homography(point: Point2D, matrix: np.ndarray) -> Point2D:
    source = np.array([[[point.x, point.y]]], dtype=np.float64)
    transformed = cv2.perspectiveTransform(source, matrix)[0][0]
    return Point2D(x=round(float(transformed[0]), 3), y=round(float(transformed[1]), 3))


def _with_field_positions(detections: list[Detection], matrix: np.ndarray) -> list[Detection]:
    updated: list[Detection] = []
    for detection in detections:
        field_position = _apply_homography(detection.foot_pixel, matrix)
        updated.append(detection.model_copy(update={"field_position": field_position}))
    return updated


def calibrate_manual(payload: CalibrateRequest) -> CalibrateResponse:
    source = np.array(
        [[pair.image.x, pair.image.y] for pair in payload.correspondences], dtype=np.float64
    )
    destination = np.array(
        [[pair.field.x, pair.field.y] for pair in payload.correspondences], dtype=np.float64
    )

    if cv2.contourArea(cv2.convexHull(source.astype(np.float32))) < 25:
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

    projected = cv2.perspectiveTransform(source.reshape(-1, 1, 2), matrix).reshape(-1, 2)
    errors = np.linalg.norm(projected - destination, axis=1)
    rmse = float(math.sqrt(float(np.mean(np.square(errors)))))
    inlier_ratio = float(inlier_mask.mean())
    confidence = max(0.0, min(1.0, inlier_ratio * math.exp(-rmse / 3.0)))

    if not np.isfinite(matrix).all() or rmse > 4.0:
        result = CalibrationResult(
            status="needs_manual",
            method="manual",
            confidence=round(confidence, 3),
            reprojection_error=round(rmse, 3),
            message="ความคลาดเคลื่อนของจุดอ้างอิงสูงเกินไป กรุณาเลือกจุดใหม่",
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
        message="Auto Calibration ยังไม่พบขอบเขตและเส้นสนามที่น่าเชื่อถือ กรุณาใช้ Manual Calibration",
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
    field_corners = np.array([[0, 0], [105, 0], [105, 68], [0, 68]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(ordered, field_corners)
    confidence = min(0.86, 0.45 + green_coverage * 0.35 + min(line_count, 12) / 200)

    if confidence < 0.7:
        return failure.model_copy(update={"confidence": round(confidence, 3)}), detections

    result = CalibrationResult(
        status="success",
        method="auto",
        confidence=round(confidence, 3),
        reprojection_error=round((1 - confidence) * 5, 3),
        matrix=matrix.tolist(),
        message="Auto Calibration แบบทดลองสำเร็จ กรุณาตรวจตำแหน่งบนสนามก่อนใช้ผล",
    )
    return result, _with_field_positions(detections, matrix)

