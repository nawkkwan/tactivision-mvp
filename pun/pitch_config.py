"""
pitch_config.py
กำหนดระบบพิกัดสนามมาตรฐาน IFAB (105 x 68 เมตร)
และพิกัดอ้างอิง 32 จุดที่ตรงกับโมเดล Roboflow (football-field-detection-f07vi)
"""

from typing import Dict, List, Tuple

# ขนาดสนามมาตรฐาน IFAB (หน่วย: เมตร)
PITCH_LENGTH_M: float = 105.0  # แกน X: 0.0 (ซ้ายสุด) ถึง 105.0 (ขวาสุด)
PITCH_WIDTH_M: float = 68.0    # แกน Y: 0.0 (บนสุด) ถึง 68.0 (ล่างสุด)

# สัดส่วนเขตโทษและจุดสำคัญตามมาตรฐาน IFAB (หน่วย: เมตร)
PENALTY_BOX_LENGTH_M: float = 16.5
PENALTY_BOX_WIDTH_M: float = 40.32
GOAL_BOX_LENGTH_M: float = 5.5
GOAL_BOX_WIDTH_M: float = 18.32
PENALTY_SPOT_DISTANCE_M: float = 11.0
CENTER_CIRCLE_RADIUS_M: float = 9.15

# คำนวณระยะขอบบน-ล่างของเขตโทษและกรอบ 6 หลา
_PENALTY_Y_TOP: float = (PITCH_WIDTH_M - PENALTY_BOX_WIDTH_M) / 2.0      # 13.84 m
_PENALTY_Y_BOTTOM: float = (PITCH_WIDTH_M + PENALTY_BOX_WIDTH_M) / 2.0   # 54.16 m
_GOAL_Y_TOP: float = (PITCH_WIDTH_M - GOAL_BOX_WIDTH_M) / 2.0            # 24.84 m
_GOAL_Y_BOTTOM: float = (PITCH_WIDTH_M + GOAL_BOX_WIDTH_M) / 2.0         # 43.16 m
_HALF_X: float = PITCH_LENGTH_M / 2.0                                    # 52.50 m
_HALF_Y: float = PITCH_WIDTH_M / 2.0                                     # 34.00 m

# พิกัด 32 Keypoints (Index 0 ถึง 31) ตามโครงสร้างของ roboflow-jvuqo/football-field-detection-f07vi
# แต่ละจุดคือ (x_meter, y_meter) บนสนาม 105 x 68 เมตร
ROBOFLOW_PITCH_VERTICES_32: List[Tuple[float, float]] = [
    # ฝั่งซ้าย: เส้นหลังประตูซ้าย (X = 0.0)
    (0.0, 0.0),                                              # Index 0  (Label 01): มุมธงซ้ายบน
    (0.0, _PENALTY_Y_TOP),                                   # Index 1  (Label 02): จุดตัดเส้นเขตโทษซ้ายบนกับเส้นหลัง
    (0.0, _GOAL_Y_TOP),                                      # Index 2  (Label 03): จุดตัดกรอบ 6 หลาซ้ายบนกับเส้นหลัง
    (0.0, _GOAL_Y_BOTTOM),                                   # Index 3  (Label 04): จุดตัดกรอบ 6 หลาซ้ายล่างกับเส้นหลัง
    (0.0, _PENALTY_Y_BOTTOM),                                # Index 4  (Label 05): จุดตัดเส้นเขตโทษซ้ายล่างกับเส้นหลัง
    (0.0, PITCH_WIDTH_M),                                    # Index 5  (Label 06): มุมธงซ้ายล่าง

    # ฝั่งซ้าย: กรอบ 6 หลา & จุดโทษ (X = 5.5, 11.0)
    (GOAL_BOX_LENGTH_M, _GOAL_Y_TOP),                        # Index 6  (Label 07): มุมกรอบ 6 หลาซ้ายบน
    (GOAL_BOX_LENGTH_M, _GOAL_Y_BOTTOM),                     # Index 7  (Label 08): มุมกรอบ 6 หลาซ้ายล่าง
    (PENALTY_SPOT_DISTANCE_M, _HALF_Y),                      # Index 8  (Label 09): จุดโทษฝั่งซ้าย

    # ฝั่งซ้าย: เส้นหน้าเขตโทษ (X = 16.5)
    (PENALTY_BOX_LENGTH_M, _PENALTY_Y_TOP),                  # Index 9  (Label 10): มุมเขตโทษซ้ายบน
    (PENALTY_BOX_LENGTH_M, _GOAL_Y_TOP),                     # Index 10 (Label 11): จุดตัดหัวกะโหลกซ้ายด้านบน
    (PENALTY_BOX_LENGTH_M, _GOAL_Y_BOTTOM),                  # Index 11 (Label 12): จุดตัดหัวกะโหลกซ้ายด้านล่าง
    (PENALTY_BOX_LENGTH_M, _PENALTY_Y_BOTTOM),               # Index 12 (Label 13): มุมเขตโทษซ้ายล่าง

    # เส้นกลางสนาม (X = 52.5)
    (_HALF_X, 0.0),                                          # Index 13 (Label 15): จุดตัดเส้นกลางสนามด้านบน
    (_HALF_X, _HALF_Y - CENTER_CIRCLE_RADIUS_M),             # Index 14 (Label 16): จุดตัดวงกลมกลางสนามด้านบน
    (_HALF_X, _HALF_Y + CENTER_CIRCLE_RADIUS_M),             # Index 15 (Label 17): จุดตัดวงกลมกลางสนามด้านล่าง
    (_HALF_X, PITCH_WIDTH_M),                                # Index 16 (Label 18): จุดตัดเส้นกลางสนามด้านล่าง

    # ฝั่งขวา: เส้นหน้าเขตโทษ (X = 88.5)
    (PITCH_LENGTH_M - PENALTY_BOX_LENGTH_M, _PENALTY_Y_TOP),    # Index 17 (Label 20): มุมเขตโทษขวาบน
    (PITCH_LENGTH_M - PENALTY_BOX_LENGTH_M, _GOAL_Y_TOP),       # Index 18 (Label 21): จุดตัดหัวกะโหลกขวาด้านบน
    (PITCH_LENGTH_M - PENALTY_BOX_LENGTH_M, _GOAL_Y_BOTTOM),    # Index 19 (Label 22): จุดตัดหัวกะโหลกขวาด้านล่าง
    (PITCH_LENGTH_M - PENALTY_BOX_LENGTH_M, _PENALTY_Y_BOTTOM), # Index 20 (Label 23): มุมเขตโทษขวาล่าง

    # ฝั่งขวา: จุดโทษ & กรอบ 6 หลา (X = 94.0, 99.5)
    (PITCH_LENGTH_M - PENALTY_SPOT_DISTANCE_M, _HALF_Y),        # Index 21 (Label 24): จุดโทษฝั่งขวา
    (PITCH_LENGTH_M - GOAL_BOX_LENGTH_M, _GOAL_Y_TOP),          # Index 22 (Label 25): มุมกรอบ 6 หลาขวาบน
    (PITCH_LENGTH_M - GOAL_BOX_LENGTH_M, _GOAL_Y_BOTTOM),       # Index 23 (Label 26): มุมกรอบ 6 หลาขวาล่าง

    # ฝั่งขวา: เส้นหลังประตูขวา (X = 105.0)
    (PITCH_LENGTH_M, 0.0),                                   # Index 24 (Label 27): มุมธงขวาบน
    (PITCH_LENGTH_M, _PENALTY_Y_TOP),                        # Index 25 (Label 28): จุดตัดเส้นเขตโทษขวาบนกับเส้นหลัง
    (PITCH_LENGTH_M, _GOAL_Y_TOP),                           # Index 26 (Label 29): จุดตัดกรอบ 6 หลาขวาบนกับเส้นหลัง
    (PITCH_LENGTH_M, _GOAL_Y_BOTTOM),                        # Index 27 (Label 30): จุดตัดกรอบ 6 หลาขวาล่างกับเส้นหลัง
    (PITCH_LENGTH_M, _PENALTY_Y_BOTTOM),                     # Index 28 (Label 31): จุดตัดเส้นเขตโทษขวาล่างกับเส้นหลัง
    (PITCH_LENGTH_M, PITCH_WIDTH_M),                         # Index 29 (Label 32): มุมธงขวาล่าง

    # จุดขอบซ้าย-ขวาของวงกลมกลางสนาม
    (_HALF_X - CENTER_CIRCLE_RADIUS_M, _HALF_Y),             # Index 30 (Label 14): ขอบซ้ายสุดของวงกลมกลางสนาม
    (_HALF_X + CENTER_CIRCLE_RADIUS_M, _HALF_Y),             # Index 31 (Label 19): ขอบขวาสุดของวงกลมกลางสนาม
]

# Dictionary จุดอ้างอิงหลักพร้อมชื่อภาษาอังกฤษ/ไทย เพื่อให้ Frontend (คนที่ 4) นำไปทำ UI เลือกจุดได้ง่าย
NAMED_LANDMARKS: Dict[str, Dict[str, object]] = {
    "top_left_corner": {"name_th": "มุมธงซ้ายบน", "coords": [0.0, 0.0], "rf_index": 0},
    "bottom_left_corner": {"name_th": "มุมธงซ้ายล่าง", "coords": [0.0, 68.0], "rf_index": 5},
    "left_penalty_top_edge": {"name_th": "จุดตัดเขตโทษซ้ายบนกับเส้นหลัง", "coords": [0.0, 13.84], "rf_index": 1},
    "left_penalty_bottom_edge": {"name_th": "จุดตัดเขตโทษซ้ายล่างกับเส้นหลัง", "coords": [0.0, 54.16], "rf_index": 4},
    "left_penalty_box_top_corner": {"name_th": "มุมเขตโทษซ้ายบน", "coords": [16.5, 13.84], "rf_index": 9},
    "left_penalty_box_bottom_corner": {"name_th": "มุมเขตโทษซ้ายล่าง", "coords": [16.5, 54.16], "rf_index": 12},
    "left_goal_box_top_corner": {"name_th": "มุมกรอบ 6 หลาซ้ายบน", "coords": [5.5, 24.84], "rf_index": 6},
    "left_goal_box_bottom_corner": {"name_th": "มุมกรอบ 6 หลาซ้ายล่าง", "coords": [5.5, 43.16], "rf_index": 7},
    "left_penalty_spot": {"name_th": "จุดโทษฝั่งซ้าย", "coords": [11.0, 34.0], "rf_index": 8},
    "halfway_top": {"name_th": "จุดตัดเส้นกลางสนามด้านบน", "coords": [52.5, 0.0], "rf_index": 13},
    "halfway_bottom": {"name_th": "จุดตัดเส้นกลางสนามด้านล่าง", "coords": [52.5, 68.0], "rf_index": 16},
    "center_spot": {"name_th": "จุดกึ่งกลางสนาม (Kick-off)", "coords": [52.5, 34.0], "rf_index": None},
    "center_circle_top": {"name_th": "จุดตัดวงกลมกลางสนามด้านบน", "coords": [52.5, 24.85], "rf_index": 14},
    "center_circle_bottom": {"name_th": "จุดตัดวงกลมกลางสนามด้านล่าง", "coords": [52.5, 43.15], "rf_index": 15},
    "center_circle_left": {"name_th": "ขอบซ้ายวงกลมกลางสนาม", "coords": [43.35, 34.0], "rf_index": 30},
    "center_circle_right": {"name_th": "ขอบขาวงกลมกลางสนาม", "coords": [61.65, 34.0], "rf_index": 31},
    "right_penalty_box_top_corner": {"name_th": "มุมเขตโทษขวาบน", "coords": [88.5, 13.84], "rf_index": 17},
    "right_penalty_box_bottom_corner": {"name_th": "มุมเขตโทษขวาล่าง", "coords": [88.5, 54.16], "rf_index": 20},
    "right_goal_box_top_corner": {"name_th": "มุมกรอบ 6 หลาขวาบน", "coords": [99.5, 24.84], "rf_index": 22},
    "right_goal_box_bottom_corner": {"name_th": "มุมกรอบ 6 หลาขวาล่าง", "coords": [99.5, 43.16], "rf_index": 23},
    "right_penalty_spot": {"name_th": "จุดโทษฝั่งขวา", "coords": [94.0, 34.0], "rf_index": 21},
    "right_penalty_top_edge": {"name_th": "จุดตัดเขตโทษขวาบนกับเส้นหลัง", "coords": [105.0, 13.84], "rf_index": 25},
    "right_penalty_bottom_edge": {"name_th": "จุดตัดเขตโทษขวาล่างกับเส้นหลัง", "coords": [105.0, 54.16], "rf_index": 28},
    "top_right_corner": {"name_th": "มุมธงขวาบน", "coords": [105.0, 0.0], "rf_index": 24},
    "bottom_right_corner": {"name_th": "มุมธงขวาล่าง", "coords": [105.0, 68.0], "rf_index": 29},
}