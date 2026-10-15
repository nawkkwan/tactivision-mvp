"""
calibration.py
โมดูลสำหรับคำนวณ Homography Matrix และแปลงพิกัดระหว่าง Pixel กับ Meter (สนาม 105 x 68 ม.)
รองรับทั้ง:
1. Auto Keypoints จากโมเดล Roboflow (football-field-detection-f07vi)
2. Manual Calibration (รับคู่จุดอ้างอิงอย่างน้อย 4 จุดจากผู้ใช้)
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import cv2
import numpy as np

from pitch_config import (
    NAMED_LANDMARKS,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    ROBOFLOW_PITCH_VERTICES_32,
)


class CalibrationError(ValueError):
    """Exception สำหรับแจ้งข้อผิดพลาดเมื่อทำ Pitch Calibration ไม่สำเร็จ"""
    pass


def bbox_to_foot_pixel(bbox: Sequence[float]) -> List[float]:
    """
    คำนวณตำแหน่งเท้านักเตะโดยประมาณ (กึ่งกลางขอบล่างของ Bounding Box)
    bbox: [x1, y1, x2, y2]
    คืนค่า: [foot_x, foot_y]
    """
    if len(bbox) != 4:
        raise CalibrationError("Bounding box must have 4 elements: [x1, y1, x2, y2]")
    x1, y1, x2, y2 = map(float, bbox)
    if x2 <= x1 or y2 <= y1:
        raise CalibrationError(f"Invalid bounding box coordinates: {bbox}")
    return [round((x1 + x2) / 2.0, 2), round(y2, 2)]


def _are_points_collinear(points: np.ndarray, tol: float = 1e-3) -> bool:
    """
    ตรวจสอบว่าจุดทั้งหมดเรียงอยู่ในแนวเส้นตรงเดียวกัน (หรือเกือบเป็นเส้นตรงเดียวกัน) หรือไม่
    โดยคำนวณพื้นที่สามเหลี่ยมจากชุดจุด 3 จุดใดๆ
    """
    n = len(points)
    if n < 3:
        return True

    # ปรับสเกลข้อมูลชั่วคราวให้อยู่ในช่วง [0, 1] เพื่อไม่ให้ค่าพิกัด Pixel กับ Meter ต่างกันเกินไป
    span = np.ptp(points, axis=0)
    max_span = float(np.max(span))
    if max_span < 1e-6:
        return True
    norm_pts = (points - np.min(points, axis=0)) / max_span

    max_area2 = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                v1 = norm_pts[j] - norm_pts[i]
                v2 = norm_pts[k] - norm_pts[i]
                area2 = abs(float(v1[0] * v2[1] - v1[1] * v2[0]))
                if area2 > max_area2:
                    max_area2 = area2

    return max_area2 < tol


def _has_Minimum_unique_points(points: np.ndarray, min_dist: float = 1e-2) -> bool:
    """ตรวจสอบว่ามีจุดที่ไม่ซ้ำกันอย่างน้อย 4 จุด"""
    unique_pts = []
    for pt in points:
        if not any(np.linalg.norm(pt - u) < min_dist for u in unique_pts):
            unique_pts.append(pt)
    return len(unique_pts) >= 4


def calculate_homography(
    image_points: Sequence[Sequence[float]],
    field_points: Sequence[Sequence[float]],
    use_ransac: bool = True,
    ransac_thresh: float = 1.5,
    max_reprojection_rmse_m: float = 3.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    คำนวณ Homography Matrix (H) สำหรับแปลงพิกัดภาพ (Pixel) -> พิกัดสนาม (Meter)
    พร้อมตรวจสอบความถูกต้องและคำนวณ Reprojection Error (RMSE หน่วยเมตร)
    """
    src = np.asarray(image_points, dtype=np.float32)
    dst = np.asarray(field_points, dtype=np.float32)

    if src.ndim != 2 or dst.ndim != 2 or src.shape[1] != 2 or dst.shape[1] != 2:
        raise CalibrationError("Point arrays must have shape (N, 2).")

    if len(src) != len(dst):
        raise CalibrationError("image_points and field_points must have the same length.")

    if len(src) < 4:
        raise CalibrationError("ต้องระบุจุดอ้างอิงอย่างน้อย 4 จุดเพื่อคำนวณ Homography")

    if not _has_Minimum_unique_points(src, min_dist=2.0):
        raise CalibrationError("พบจุดอ้างอิงบนภาพซ้ำกันหรืออยู่ใกล้กันเกินไป (ต้องมีอย่างน้อย 4 จุดที่ต่างกัน)")

    if not _has_Minimum_unique_points(dst, min_dist=0.1):
        raise CalibrationError("พบจุดอ้างอิงบนสนามซ้ำกัน (ต้องมีอย่างน้อย 4 จุดที่ต่างกัน)")

    if _are_points_collinear(src, tol=0.01) or _are_points_collinear(dst, tol=0.01):
        raise CalibrationError(
            "จุดอ้างอิงเรียงอยู่ในแนวเส้นตรงเดียวกัน (Collinear) กรุณาเลือกจุดที่กระจายตัวครอบคลุมพื้นที่สนาม"
        )

    method = cv2.RANSAC if (use_ransac and len(src) > 4) else 0
    H, mask = cv2.findHomography(src, dst, method=method, ransacReprojThreshold=ransac_thresh)

    if H is None or not np.all(np.isfinite(H)):
        raise CalibrationError("ไม่สามารถคำนวณ Homography Matrix ได้จากจุดที่ระบุ")

    # ตรวจสอบว่า Matrix สามารถ Invert ได้จริง (ไม่เป็น Singular Matrix)
    det = float(np.linalg.det(H))
    if abs(det) < 1e-12:
        raise CalibrationError("Homography Matrix มีค่า Degenerate (ไม่สามารถแปลงพิกัดได้อย่างแม่นยำ)")

    # คำนวณ Reprojection Error (หน่วยเมตร)
    projected_field = pixel_to_field(src.tolist(), H)
    projected_arr = np.asarray(projected_field, dtype=np.float32)
    errors = np.linalg.norm(projected_arr - dst, axis=1)

    if mask is not None:
        inliers = mask.ravel().astype(bool)
        inlier_errors = errors[inliers] if np.any(inliers) else errors
        inlier_count = int(np.sum(inliers))
    else:
        inlier_errors = errors
        inlier_count = len(src)

    rmse_m = float(np.sqrt(np.mean(inlier_errors ** 2)))
    max_error_m = float(np.max(inlier_errors))

    if inlier_count < 4:
        raise CalibrationError("จำนวนจุดอ้างอิงที่สอดคล้องกัน (Inliers) มีไม่ถึง 4 จุด")

    if rmse_m > max_reprojection_rmse_m:
        raise CalibrationError(
            f"ความคลาดเคลื่อนของการแปลงพิกัดสูงเกินไป (RMSE = {rmse_m:.2f} เมตร > {max_reprojection_rmse_m} เมตร) "
            "กรุณาตรวจสอบการจับคู่จุดอ้างอิงอีกครั้ง"
        )

    metrics = {
        "num_points": len(src),
        "inliers": inlier_count,
        "reprojection_rmse_m": round(rmse_m, 3),
        "max_error_m": round(max_error_m, 3),
    }

    return H, metrics


def pixel_to_field(
    points: Sequence[Sequence[float]],
    H: Sequence[Sequence[float]] | np.ndarray,
    clip_to_pitch: bool = False,
) -> List[List[float]]:
    """
    แปลงรายการพิกัด Pixel [[u, v], ...] ให้เป็นพิกัดสนามหน่วยเมตร [[x, y], ...]
    """
    if len(points) == 0:
        return []

    H_mat = np.asarray(H, dtype=np.float64)
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(pts, H_mat).reshape(-1, 2)

    if not np.all(np.isfinite(transformed)):
        raise CalibrationError("เกิดค่าพิกัดไม่ถูกต้อง (NaN/Inf) ระหว่างการแปลงเป็นพิกัดสนาม")

    result: List[List[float]] = []
    for x, y in transformed:
        fx, fy = float(x), float(y)
        if clip_to_pitch:
            fx = max(0.0, min(PITCH_LENGTH_M, fx))
            fy = max(0.0, min(PITCH_WIDTH_M, fy))
        result.append([round(fx, 2), round(fy, 2)])

    return result


def field_to_pixel(
    field_points: Sequence[Sequence[float]],
    H: Sequence[Sequence[float]] | np.ndarray,
) -> List[List[float]]:
    """
    แปลงรายการพิกัดสนามหน่วยเมตร [[x, y], ...] กลับเป็นพิกัดภาพ Pixel [[u, v], ...]
    (ช่วยให้ Frontend วาดจุดเข้าตัดบอล intercept_point หรือเส้นทางบอลลงบน Canvas ได้ทันที)
    """
    if len(field_points) == 0:
        return []

    H_mat = np.asarray(H, dtype=np.float64)
    try:
        H_inv = np.linalg.inv(H_mat)
    except np.linalg.LinAlgError as exc:
        raise CalibrationError("ไม่สามารถคำนวณ Inverse Homography ได้") from exc

    pts = np.asarray(field_points, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(pts, H_inv).reshape(-1, 2)

    return [[round(float(u), 2), round(float(v), 2)] for u, v in transformed]


def extract_correspondences_from_roboflow(
    roboflow_result: Dict[str, Any],
    conf_threshold: float = 0.5,
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    ดึงคู่พิกัด (image_points, field_points) จาก JSON ผลลัพธ์ของโมเดล
    roboflow-jvuqo/football-field-detection-f07vi โดยกรองเฉพาะจุดที่มี confidence >= conf_threshold
    """
    predictions = roboflow_result.get("predictions", [])
    if not predictions:
        raise CalibrationError("ไม่พบผลลัพธ์การตรวจจับสนามจาก Roboflow Keypoint Model")

    keypoints = predictions[0].get("keypoints", [])
    if not keypoints:
        raise CalibrationError("ไม่พบข้อมูล Keypoints ในผลลัพธ์จากโมเดล")

    image_points: List[List[float]] = []
    field_points: List[List[float]] = []

    for idx, kp in enumerate(keypoints):
        conf = float(kp.get("confidence", 0.0))
        if conf < conf_threshold:
            continue

        u = float(kp.get("x", 0.0))
        v = float(kp.get("y", 0.0))

        # จับคู่ตามลำดับ Index มาตรฐาน 32 จุดของ Roboflow
        if idx < len(ROBOFLOW_PITCH_VERTICES_32):
            fx, fy = ROBOFLOW_PITCH_VERTICES_32[idx]
            image_points.append([u, v])
            field_points.append([fx, fy])

    if len(image_points) < 4:
        raise CalibrationError(
            f"โมเดลตรวจพบจุดอ้างอิงสนามที่มีความมั่นใจสูงเพียง {len(image_points)} จุด "
            "(ต้องการอย่างน้อย 4 จุด) กรุณาใช้โหมด Manual Calibration กดเลือกจุดบนภาพ"
        )

    return image_points, field_points


def calibrate_players(
    players: List[Dict[str, Any]],
    image_points: Optional[Sequence[Sequence[float]]] = None,
    field_points: Optional[Sequence[Sequence[float]]] = None,
    roboflow_result: Optional[Dict[str, Any]] = None,
    conf_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    ฟังก์ชันหลักสำหรับ Endpoint POST /calibrate (ให้คนที่ 5 เรียกใช้ได้ทันที)
    รับรายชื่อ players และจุดอ้างอิง (จาก Manual หรือจาก Roboflow Keypoints)
    แล้วอัปเดต field_position (หน่วยเมตร) ให้ผู้เล่นทุกคน
    """
    if roboflow_result is not None and (image_points is None or field_points is None):
        img_pts, fld_pts = extract_correspondences_from_roboflow(
            roboflow_result, conf_threshold=conf_threshold
        )
        mode = "roboflow_auto"
    elif image_points is not None and field_points is not None:
        img_pts = [list(map(float, p)) for p in image_points]
        fld_pts = [list(map(float, p)) for p in field_points]
        mode = "manual"
    else:
        raise CalibrationError("กรุณาส่งคู่พิกัด (image_points, field_points) หรือ roboflow_result")

    H, metrics = calculate_homography(img_pts, fld_pts)
    H_inv = np.linalg.inv(H)

    updated_players: List[Dict[str, Any]] = []
    foot_pixels: List[List[float]] = []

    for p in players:
        player_copy = dict(p)
        if player_copy.get("foot_pixel") is not None:
            fp = list(map(float, player_copy["foot_pixel"]))
        elif player_copy.get("bbox") is not None:
            fp = bbox_to_foot_pixel(player_copy["bbox"])
            player_copy["foot_pixel"] = fp
        else:
            raise CalibrationError(f"Player ID {player_copy.get('id')} ไม่มีทั้ง foot_pixel และ bbox")

        foot_pixels.append(fp)
        updated_players.append(player_copy)

    if foot_pixels:
        field_positions = pixel_to_field(foot_pixels, H)
        for player_copy, f_pos in zip(updated_players, field_positions):
            player_copy["field_position"] = f_pos
            player_copy[" is_on_pitch"] = (
                -2.0 <= f_pos[0] <= PITCH_LENGTH_M + 2.0
                and -2.0 <= f_pos[1] <= PITCH_WIDTH_M + 2.0
            )

    return {
        "calibration_mode": mode,
        "homography_matrix": H.tolist(),
        "inverse_homography_matrix": H_inv.tolist(),
        "metrics": metrics,
        "players": updated_players,
    }