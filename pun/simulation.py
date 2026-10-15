"""
simulation.py
โมดูลจำลองความเสี่ยงในการถูกตัดบอล (Pass Interception Risk Simulation)
คำนวณจากพิกัดสนามหน่วยเมตรหลังผ่าน Pitch Calibration แล้ว
"""

from typing import Any, Dict, List, Optional, Sequence
import numpy as np

from calibration import field_to_pixel, pixel_to_field
from pitch_config import PITCH_LENGTH_M, PITCH_WIDTH_M


class SimulationError(ValueError):
    """Exception สำหรับแจ้งข้อผิดพลาดในการจำลองการจ่ายบอล"""
    pass


# ค่าเริ่มต้นตามเอกสารสมมติฐานของทีม
DEFAULT_BALL_SPEED_MPS: float = 12.0       # ความเร็วบอลเริ่มต้น (m/s)
DEFAULT_DEFENDER_SPEED_MPS: float = 6.0    # ความเร็วกองหลังเริ่มต้น (m/s)
DEFAULT_REACTION_TIME_S: float = 0.5       # เวลาตอบสนองของกองหลัง (s)
DEFAULT_REACH_RADIUS_M: float = 0.7        # ระยะเหยียดเท้าตัดบอล (m)
MEDIUM_RISK_MARGIN_THRESHOLD_S: float = 0.25  # หากกองหลังช้ากว่าบอลไม่เกิน 0.25s ถือว่า Medium Risk
NUM_PATH_SAMPLES: int = 101                # จำนวนจุดตัวอย่างตลอดเส้นทางการจ่ายบอล


def simulate_pass(
    passer_pos: Sequence[float],
    target_pos: Sequence[float],
    defenders: List[Dict[str, Any]],
    ball_speed: float = DEFAULT_BALL_SPEED_MPS,
    defender_speed: float = DEFAULT_DEFENDER_SPEED_MPS,
    reaction_time: float = DEFAULT_REACTION_TIME_S,
    reach_radius: float = DEFAULT_REACH_RADIUS_M,
    medium_margin_threshold: float = MEDIUM_RISK_MARGIN_THRESHOLD_S,
    num_samples: int = NUM_PATH_SAMPLES,
    homography_matrix: Optional[Sequence[Sequence[float]]] = None,
) -> Dict[str, Any]:
    """
    คำนวณระยะการจ่ายบอล เวลาที่บอลเคลื่อนที่ จุดที่กองหลังอาจเข้าตัดบอล และระดับความเสี่ยง
    - passer_pos: [x, y] พิกัดเมตรของคนถือบอลเดิม
    - target_pos: [x, y] พิกัดเมตรของผู้รับบอลหรือพื้นที่ว่าง
    - defenders: รายการกองหลัง [{"id": 7, "field_position": [x, y]}, ...]
    """
    if ball_speed <= 0 or defender_speed <= 0:
        raise SimulationError("ความเร็วลูกบอลและความเร็วกองหลังต้องมีค่ามากกว่า 0 m/s")
    if reaction_time < 0 or reach_radius < 0:
        raise SimulationError("reaction_time และ reach_radius ต้องไม่ติดลบ")

    start = np.asarray(passer_pos, dtype=np.float64)
    end = np.asarray(target_pos, dtype=np.float64)

    if start.shape != (2,) or end.shape != (2,):
        raise SimulationError("พิกัดผู้จ่ายและเป้าหมายต้องเป็น [x, y] หน่วยเมตร")

    # ตรวจสอบกรณีส่งพิกัด Pixel (เช่น > 120) มาแทนพิกัดเมตรโดยไม่ได้ Calibrate
    if np.any(start > 120.0) or np.any(end > 120.0) or np.any(start < -15.0) or np.any(end < -15.0):
        raise SimulationError(
            f"ตรวจพบพิกัดนอกขอบเขตสนามมาตรฐาน ({start.tolist()} -> {end.tolist()}) "
            "กรุณาใช้พิกัดหน่วยเมตรที่ผ่านการ Calibrate แล้วเท่านั้น (ห้ามใช้พิกัด Pixel)"
        )

    distance_m = float(np.linalg.norm(end - start))
    if distance_m < 0.05:
        raise SimulationError("ตำแหน่งผู้รับบอลหรือพื้นที่เป้าหมายต้องไม่เป็นจุดเดียวกับผู้ถือบอล")

    ball_time_s = distance_m / float(ball_speed)
    alphas = np.linspace(0.0, 1.0, max(11, num_samples))

    interceptors: List[Dict[str, Any]] = []

    for defender in defenders:
        def_id = defender.get("id", defender.get("player_id"))
        raw_pos = defender.get("field_position", defender.get("position"))
        if raw_pos is None:
            continue

        def_pos = np.asarray(raw_pos, dtype=np.float64)
        if def_pos.shape != (2,):
            continue

        best_margin = float("inf")
        best_point = None
        best_alpha = 0.0

        # ตรวจจุดตัวอย่างตลอดเส้นทางบอล (ข้าม alpha = 0.0 ที่เท้าคนจ่ายเล็กน้อยเพื่อความสมจริง)
        for alpha in alphas[1:]:
            point = start + alpha * (end - start)
            t_ball = alpha * ball_time_s

            d_def = float(np.linalg.norm(def_pos - point))
            effective_dist = max(0.0, d_def - float(reach_radius))
            t_def = float(reaction_time) + (effective_dist / float(defender_speed))

            # margin < 0 แปลว่ากองหลังไปถึงจุดตัดก่อนลูกบอล!
            margin = t_def - t_ball
            if margin < best_margin:
                best_margin = margin
                best_point = [round(float(point[0]), 2), round(float(point[1]), 2)]
                best_alpha = float(alpha)

        if best_point is not None and best_margin <= medium_margin_threshold:
            interceptor_entry: Dict[str, Any] = {
                "player_id": def_id,
                "intercept_point": best_point,
                "time_margin_s": round(float(best_margin), 2),
                "path_progress_ratio": round(best_alpha, 2),
            }
            if homography_matrix is not None:
                px_pt = field_to_pixel([best_point], homography_matrix)[0]
                interceptor_entry["intercept_pixel"] = px_pt

            interceptors.append(interceptor_entry)

    # เรียงลำดับคนที่มีโอกาสตัดบอลได้เร็วที่สุดขึ้นก่อน (time_margin_s น้อยสุด)
    interceptors.sort(key=lambda item: item["time_margin_s"])

    # กำหนดระดับความเสี่ยง (Low / Medium / High)
    if any(item["time_margin_s"] < 0.0 for item in interceptors):
        risk_level = "high"
        top_def = interceptors[0]
        explanation = (
            f"Defender {top_def['player_id']} may reach the passing lane before the ball "
            f"(margin: {top_def['time_margin_s']:+.2f}s)."
        )
        explanation_th = (
            f"Pass Risk: High — กองหลังหมายเลข {top_def['player_id']} อาจเข้าถึงเส้นจ่ายบอลก่อนลูกบอล "
            f"({abs(top_def['time_margin_s']):.2f} วินาที) ภายใต้สมมติฐานที่กำหนด"
        )
    elif len(interceptors) > 0:
        risk_level = "medium"
        top_def = interceptors[0]
        explanation = (
            f"Defender {top_def['player_id']} can closely contest the passing lane "
            f"(margin: +{top_def['time_margin_s']:.2f}s)."
        )
        explanation_th = (
            f"Pass Risk: Medium — กองหลังหมายเลข {top_def['player_id']} อาจวิ่งเข้ากดดันใกล้เส้นจ่ายบอลได้ทัน "
            f"(ช้ากว่าบอลเพียง {top_def['time_margin_s']:.2f} วินาที) ภายใต้สมมติฐานที่กำหนด"
        )
    else:
        risk_level = "low"
        explanation = "No opposing defender can reach the passing lane in time under current assumptions."
        explanation_th = (
            "Pass Risk: Low — ไม่มีกองหลังฝ่ายตรงข้ามในระยะที่เข้าตัดบอลทันภายใต้สมมติฐานที่กำหนด"
        )

    return {
        "distance_m": round(distance_m, 2),
        "ball_time_s": round(ball_time_s, 2),
        "risk_level": risk_level,
        "interceptors": interceptors,
        "explanation": explanation,
        "explanation_th": explanation_th,
    }


def run_simulation_from_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ฟังก์ชัน Wrapper สำหรับ Endpoint POST /simulate (ให้คนที่ 5 เรียกใช้จาก FastAPI ได้ทันที)
    รองรับโครงสร้าง JSON ตาม API Contract ทั้งการจ่ายให้เพื่อนร่วมทีม (type="player")
    และการจ่ายไปยังพื้นที่ว่าง (type="space")
    """
    carrier_id = request_data.get("carrier_id")
    if carrier_id is None:
        raise SimulationError("ต้องระบุ carrier_id (นักเตะที่ถือบอล)")

    players = request_data.get("players", [])
    if not players:
        raise SimulationError("ไม่พบรายการข้อมูลนักเตะ (players)")

    player_map: Dict[Any, Dict[str, Any]] = {p.get("id"): p for p in players}
    if carrier_id not in player_map:
        raise SimulationError(f"ไม่พบข้อมูลนักเตะที่ถือบอล (carrier_id={carrier_id}) ในรายการ players")

    carrier = player_map[carrier_id]
    carrier_team = carrier.get("team_id")
    carrier_pos = carrier.get("field_position")

    if carrier_pos is None:
        raise SimulationError("นักเตะที่ถือบอลยังไม่มีพิกัดสนาม (field_position) กรุณาทำ Calibration ก่อน")
    if carrier_team not in ("A", "B"):
        raise SimulationError(f"นักเตะที่ถือบอลต้องสังกัด Team A หรือ Team B (ปัจจุบันคือ '{carrier_team}')")

    target_info = request_data.get("target")
    if not target_info or not isinstance(target_info, dict):
        raise SimulationError("ต้องระบุข้อมูลเป้าหมายการจ่ายบอล (target)")

    target_type = target_info.get("type", "player")
    H = request_data.get("homography_matrix")

    if target_type == "player":
        receiver_id = target_info.get("player_id")
        if receiver_id is None:
            raise SimulationError("กรณี target.type = 'player' ต้องระบุ target.player_id")
        if receiver_id == carrier_id:
            raise SimulationError("ไม่สามารถเลือกผู้รับบอลเป็นคนเดียวกับผู้ถือบอลได้")
        if receiver_id not in player_map:
            raise SimulationError(f"ไม่พบผู้รับบอล (player_id={receiver_id}) ในรายการ players")

        receiver = player_map[receiver_id]
        if receiver.get("team_id") != carrier_team:
            raise SimulationError(
                f"ผู้รับบอล (Team {receiver.get('team_id')}) ต้องอยู่ทีมเดียวกับผู้ถือบอล (Team {carrier_team})"
            )
        target_pos = receiver.get("field_position")
        if target_pos is None:
            raise SimulationError(f"ผู้รับบอล (player_id={receiver_id}) ยังไม่มีพิกัดสนาม (field_position)")

    elif target_type == "space":
        target_pos = target_info.get("field_position")
        # กรณีที่ Frontend ส่งมาเป็นพิกัด Pixel ของจุดที่คลิกบนสนาม ให้แปลงเป็นเมตรอัตโนมัติ
        if target_pos is None and target_info.get("pixel_position") is not None and H is not None:
            target_pos = pixel_to_field([target_info["pixel_position"]], H)[0]
        if target_pos is None:
            raise SimulationError(
                "กรณี target.type = 'space' ต้องระบุ target.field_position [x, y] หน่วยเมตร"
            )
    else:
        raise SimulationError(f"ไม่รองรับ target.type = '{target_type}' (ต้องเป็น 'player' หรือ 'space')")

    # คัดกรองเฉพาะผู้เล่นฝ่ายตรงข้าม (Team ตรงข้ามกับคนถือบอล) มาเป็น Defenders
    opposing_team = "B" if carrier_team == "A" else "A"
    defenders = [
        p for p in players
        if p.get("team_id") == opposing_team and p.get("field_position") is not None
    ]

    # รองรับทั้งชื่อ key แบบสั้นและแบบมีหน่วย (_mps, _s) ตาม API Contract ทั้งสองส่วน
    ball_speed = float(
        request_data.get("ball_speed", request_data.get("ball_speed_mps", DEFAULT_BALL_SPEED_MPS))
    )
    defender_speed = float(
        request_data.get(
            "defender_speed", request_data.get("defender_speed_mps", DEFAULT_DEFENDER_SPEED_MPS)
        )
    )
    reaction_time = float(
        request_data.get(
            "reaction_time", request_data.get("reaction_time_s", DEFAULT_REACTION_TIME_S)
        )
    )
    reach_radius = float(request_data.get("reach_radius", DEFAULT_REACH_RADIUS_M))

    result = simulate_pass(
        passer_pos=carrier_pos,
        target_pos=target_pos,
        defenders=defenders,
        ball_speed=ball_speed,
        defender_speed=defender_speed,
        reaction_time=reaction_time,
        reach_radius=reach_radius,
        homography_matrix=H,
    )

    result["carrier_id"] = carrier_id
    result["target"] = {
        "type": target_type,
        "player_id": target_info.get("player_id") if target_type == "player" else None,
        "field_position": [round(float(target_pos[0]), 2), round(float(target_pos[1]), 2)],
    }

    return result