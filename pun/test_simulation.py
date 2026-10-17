"""
test_simulation.py
Unit Tests สำหรับตรวจสอบความถูกต้องของ calibration.py และ simulation.py
รันทดสอบด้วยคำสั่ง: pytest -v
"""

import pytest
from calibration import (
    CalibrationError,
    bbox_to_foot_pixel,
    calculate_homography,
    calibrate_players,
    field_to_pixel,
    pixel_to_field,
)
from pitch_config import ROBOFLOW_PITCH_VERTICES_32
from simulation import SimulationError, run_simulation_from_request, simulate_pass


# ==========================================
# Part A: ทดสอบ Pitch Calibration (งาน 3.1 - 3.3)
# ==========================================

def test_bbox_to_foot_pixel():
    bbox = [450, 260, 490, 360]
    assert bbox_to_foot_pixel(bbox) == [470.0, 360.0]


def test_valid_homography_and_pixel_to_field():
    # จุดอ้างอิงจำลอง 4 มุมเขตโทษฝั่งซ้าย
    image_pts = [
        [120.0, 180.0],  # จุดตัดเขตโทษซ้ายบนกับเส้นหลัง (0, 13.84)
        [380.0, 195.0],  # มุมเขตโทษซ้ายบน (16.5, 13.84)
        [340.0, 520.0],  # มุมเขตโทษซ้ายล่าง (16.5, 54.16)
        [80.0, 500.0],   # จุดตัดเขตโทษซ้ายล่างกับเส้นหลัง (0, 54.16)
    ]
    field_pts = [
        [0.0, 13.84],
        [16.5, 13.84],
        [16.5, 54.16],
        [0.0, 54.16],
    ]

    H, metrics = calculate_homography(image_pts, field_pts)
    assert metrics["inliers"] == 4
    assert metrics["reprojection_rmse_m"] < 0.05

    # ทดสอบแปลงจุดกลับไป-กลับมา (Round-trip test)
    converted_field = pixel_to_field(image_pts, H)
    for (fx, fy), (ex, ey) in zip(converted_field, field_pts):
        assert abs(fx - ex) < 0.1
        assert abs(fy - ey) < 0.1

    converted_pixel = field_to_pixel(field_pts, H)
    for (u, v), (eu, ev) in zip(converted_pixel, image_pts):
        assert abs(u - eu) < 0.5
        assert abs(v - ev) < 0.5


def test_calibration_rejects_fewer_than_4_points():
    with pytest.raises(CalibrationError, match="อย่างน้อย 4 จุด"):
        calculate_homography(
            [[100, 100], [200, 100], [300, 200]],
            [[0, 0], [10, 0], [10, 10]],
        )


def test_calibration_rejects_collinear_points():
    # จุดทั้ง 4 เรียงอยู่บนเส้นตรงเดียวกัน (Y = 200 ทั้งหมด)
    collinear_img = [[100, 200], [200, 200], [300, 200], [400, 200]]
    collinear_fld = [[0, 0], [10, 0], [20, 0], [30, 0]]
    with pytest.raises(CalibrationError, match="เส้นตรงเดียวกัน"):
        calculate_homography(collinear_img, collinear_fld)


def test_calibrate_from_roboflow_32_keypoints():
    # จำลองผลลัพธ์จากโมเดล football-field-detection-f07vi ที่มี 32 จุด
    # โดยให้มี 5 จุดที่มี confidence สูง (> 0.5)
    active_indices = [1, 4, 9, 12, 8]  # กรอบเขตโทษซ้าย + จุดโทษซ้าย
    fake_keypoints = []
    for idx in range(32):
        fx, fy = ROBOFLOW_PITCH_VERTICES_32[idx]
        if idx in active_indices:
            # สมมติสมการโปรเจกชันง่ายๆ u = 20*fx + 100, v = 10*fy + 50
            fake_keypoints.append({
                "x": 20.0 * fx + 100.0,
                "y": 10.0 * fy + 50.0,
                "confidence": 0.92,
            })
        else:
            fake_keypoints.append({"x": 0.0, "y": 0.0, "confidence": 0.05})

    mock_rf_response = {"predictions": [{"keypoints": fake_keypoints}]}
    players = [{"id": 1, "class": "player", "bbox": [300, 290, 340, 390], "team_id": "A"}]

    res = calibrate_players(players=players, roboflow_result=mock_rf_response, conf_threshold=0.5)
    assert res["calibration_mode"] == "roboflow_auto"
    # foot_pixel คือ [320, 390] -> fx = (320-100)/20 = 11.0, fy = (390-50)/10 = 34.0 (จุดโทษพอดี)
    assert res["players"][0]["field_position"] == [11.0, 34.0]


# ==========================================
# Part B: ทดสอบ Pass Simulation (งาน 3.4 - 3.6)
# ==========================================

def test_pass_simulation_high_risk_when_defender_on_lane():
    # จ่ายจาก [45, 24] ไป [60, 30] มีกองหลังดักตรงกลางที่ [53, 27] (ตามตัวอย่างใน API Contract)
    res = simulate_pass(
        passer_pos=[45.0, 24.0],
        target_pos=[60.0, 30.0],
        defenders=[{"id": 7, "field_position": [53.0, 27.0]}],
        ball_speed=12.0,
        defender_speed=6.0,
        reaction_time=0.5,
    )
    assert res["distance_m"] == 16.16
    assert res["ball_time_s"] == 1.35
    assert res["risk_level"] == "high"
    assert len(res["interceptors"]) == 1
    assert res["interceptors"][0]["player_id"] == 7
    assert res["interceptors"][0]["time_margin_s"] < 0


def test_pass_simulation_low_risk_when_no_defender_near():
    res = simulate_pass(
        passer_pos=[30.0, 34.0],
        target_pos=[50.0, 34.0],
        defenders=[{"id": 9, "field_position": [35.0, 60.0]}],  # อยู่ห่างออกไป 26 เมตร
        ball_speed=14.0,
        defender_speed=6.0,
        reaction_time=0.5,
    )
    assert res["risk_level"] == "low"
    assert len(res["interceptors"]) == 0


def test_fast_ball_reduces_risk_compared_to_slow_ball():
    defenders = [{"id": 4, "field_position": [50.0, 28.5]}]
    slow_res = simulate_pass([40.0, 25.0], [60.0, 25.0], defenders, ball_speed=8.0)
    fast_res = simulate_pass([40.0, 25.0], [60.0, 25.0], defenders, ball_speed=20.0)

    assert slow_res["risk_level"] == "high"
    assert fast_res["risk_level"] == "low"


def test_what_if_switching_receivers_keeps_carrier_unchanged():
    """
    ทดสอบ Flow หลักของ TactiVision MVP:
    คนถือบอล (ID 1) คงเดิม แต่สลับเป้าหมายจาก ผู้รับ A (ID 2) -> ผู้รับ B (ID 3) -> พื้นที่ว่าง (space)
    """
    scene_players = [
        {"id": 1, "team_id": "A", "field_position": [35.0, 25.0]},  # คนถือบอล
        {"id": 2, "team_id": "A", "field_position": [55.0, 30.0]},  # เพื่อนร่วมทีม A (มีกองหลังดัก)
        {"id": 3, "team_id": "A", "field_position": [40.0, 10.0]},  # เพื่อนร่วมทีม B (โล่ง)
        {"id": 7, "team_id": "B", "field_position": [46.0, 27.5]},  # กองหลังคู่แข่ง
    ]

    # ทางเลือกที่ 1: จ่ายให้ผู้รับ A (ID 2)
    req_a = {
        "carrier_id": 1,
        "target": {"type": "player", "player_id": 2},
        "players": scene_players,
        "ball_speed": 12.0,
        "defender_speed": 6.0,
        "reaction_time": 0.5,
    }
    res_a = run_simulation_from_request(req_a)
    assert res_a["carrier_id"] == 1
    assert res_a["risk_level"] == "high"

    # ทางเลือกที่ 2: เปลี่ยนไปจ่ายให้ผู้รับ B (ID 3) โดยใช้ scene_players เดิม
    req_b = {
        "carrier_id": 1,
        "target": {"type": "player", "player_id": 3},
        "players": scene_players,
        "ball_speed": 12.0,
        "defender_speed": 6.0,
        "reaction_time": 0.5,
    }
    res_b = run_simulation_from_request(req_b)
    assert res_b["carrier_id"] == 1
    assert res_b["risk_level"] == "low"

    # ทางเลือกที่ 3: เปลี่ยนไปจ่ายเข้าพื้นที่ว่าง (Open Space) ที่ [50.0, 12.0]
    req_space = {
        "carrier_id": 1,
        "target": {"type": "space", "field_position": [50.0, 12.0]},
        "players": scene_players,
        "ball_speed": 12.0,
        "defender_speed": 6.0,
        "reaction_time": 0.5,
    }
    res_space = run_simulation_from_request(req_space)
    assert res_space["carrier_id"] == 1
    assert res_space["risk_level"] == "low"
    assert res_space["target"]["type"] == "space"


def test_reject_pixel_coordinates_in_simulation():
    with pytest.raises(SimulationError, match="พิกัดหน่วยเมตร"):
        simulate_pass(
            passer_pos=[470.0, 360.0],  # เผลอส่งค่า Pixel มาแทนเมตร
            target_pos=[680.0, 410.0],
            defenders=[],
        )