"""
pitch_detector.py
เชื่อมต่อโมเดล Roboflow Keypoint Detection (football-field-detection-f07vi)
เพื่อดึงจุดอ้างอิงสนามอัตโนมัติสำหรับทำ Pitch Calibration
"""

import os
from typing import Any, Dict, Optional
from calibration import calibrate_players, extract_correspondences_from_roboflow

DEFAULT_MODEL_ID = "football-field-detection-f07vi/14"


def detect_pitch_keypoints_roboflow(
    image_path: str,
    api_key: Optional[str] = None,
    model_id: str = DEFAULT_MODEL_ID,
) -> Dict[str, Any]:
    """
    เรียกใช้ Roboflow Serverless API เพื่อตรวจจับ 32 Keypoints บนสนามฟุตบอล
    """
    from inference_sdk import InferenceHTTPClient

    key = api_key or os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        raise ValueError(
            "กรุณาตั้งค่า ROBOFLOW_API_KEY หรือส่ง api_key เข้ามาในฟังก์ชัน "
            "(ดู API Key ได้ที่หน้า Settings ของ Roboflow)"
        )

    client = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=key,
    )
    return client.infer(image_path, model_id=model_id)


def auto_calibrate_image_and_players(
    image_path: str,
    players: list,
    api_key: Optional[str] = None,
    conf_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    รันตรวจจับ Keypoints สนามจากภาพ แล้วคำนวณ Homography แปลงพิกัดนักเตะทุกคนเป็นเมตรทันที
    """
    rf_result = detect_pitch_keypoints_roboflow(image_path=image_path, api_key=api_key)
    return calibrate_players(
        players=players,
        roboflow_result=rf_result,
        conf_threshold=conf_threshold,
    )