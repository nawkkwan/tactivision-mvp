from __future__ import annotations

import math

from fastapi import HTTPException

from ..schemas import Point2D, SimulateRequest, SimulateResponse


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0


def _distance(a: Point2D, b: Point2D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def simulate_pass(payload: SimulateRequest) -> SimulateResponse:
    players_by_id = {player.id: player for player in payload.players}
    carrier = players_by_id.get(payload.ball_carrier_id)
    if carrier is None:
        raise HTTPException(status_code=422, detail="ไม่พบ Ball Carrier ในรายชื่อผู้เล่น")

    target = payload.target.position
    if not (0 <= target.x <= PITCH_LENGTH and 0 <= target.y <= PITCH_WIDTH):
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่นอกขอบเขตสนาม 105 × 68 เมตร")

    if payload.target.type == "receiver":
        receiver = players_by_id.get(payload.target.receiver_id or "")
        if receiver is None:
            raise HTTPException(status_code=422, detail="ไม่พบผู้รับบอลที่เลือก")
        if receiver.team_id != carrier.team_id:
            raise HTTPException(status_code=422, detail="เลือกผู้เล่นฝ่ายตรงข้ามเป็นผู้รับบอลไม่ได้")
        if receiver.id == carrier.id:
            raise HTTPException(status_code=422, detail="Ball Carrier ไม่สามารถส่งบอลให้ตัวเอง")

    pass_distance = _distance(carrier.position, target)
    if pass_distance < 0.25:
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่ใกล้ Ball Carrier เกินไป")

    parameters = payload.parameters
    ball_time_total = pass_distance / parameters.ball_speed
    opponents = [
        player
        for player in payload.players
        if player.team_id != carrier.team_id and player.team_id.value != "unassigned"
    ]

    if not opponents:
        return SimulateResponse(
            risk="low",
            pass_distance=round(pass_distance, 3),
            ball_time=round(ball_time_total, 3),
            interceptor_id=None,
            intercept_point=None,
            minimum_margin=None,
            explanation="Pass Risk: Low — ไม่มีผู้เล่นฝ่ายตรงข้ามที่มีพิกัดพร้อมสำหรับการคำนวณ",
        )

    sample_count = max(2, min(400, math.ceil(pass_distance / parameters.sample_step)))
    minimum_margin = math.inf
    interceptor_id: str | None = None
    intercept_point: Point2D | None = None

    for index in range(1, sample_count + 1):
        ratio = index / sample_count
        point = Point2D(
            x=carrier.position.x + (target.x - carrier.position.x) * ratio,
            y=carrier.position.y + (target.y - carrier.position.y) * ratio,
        )
        ball_time = (pass_distance * ratio) / parameters.ball_speed

        for defender in opponents:
            run_distance = max(0.0, _distance(defender.position, point) - parameters.reach_radius)
            defender_time = parameters.reaction_time + run_distance / parameters.defender_speed
            margin = defender_time - ball_time
            if margin < minimum_margin:
                minimum_margin = margin
                interceptor_id = defender.id
                intercept_point = point

    if minimum_margin <= 0.15:
        risk = "high"
        detail = "อาจเข้าถึงแนวจ่ายบอลได้ก่อนหรือใกล้เคียงกับเวลาที่บอลมาถึง"
    elif minimum_margin <= 0.75:
        risk = "medium"
        detail = "อยู่ใกล้แนวจ่ายบอลและมีช่วงเวลาสำรองไม่มาก"
    else:
        risk = "low"
        detail = "ต้องใช้เวลาเข้าถึงแนวจ่ายบอลมากกว่าเวลาที่บอลมาถึง"

    explanation = (
        f"Pass Risk: {risk.title()} — ผู้เล่น {interceptor_id} {detail} "
        f"ภายใต้สมมติฐานที่กำหนด"
    )
    return SimulateResponse(
        risk=risk,
        pass_distance=round(pass_distance, 3),
        ball_time=round(ball_time_total, 3),
        interceptor_id=interceptor_id,
        intercept_point=(
            Point2D(x=round(intercept_point.x, 3), y=round(intercept_point.y, 3))
            if intercept_point
            else None
        ),
        minimum_margin=round(minimum_margin, 3),
        explanation=explanation,
    )

