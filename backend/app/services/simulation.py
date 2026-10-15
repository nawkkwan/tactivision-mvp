from __future__ import annotations

import math

from fastapi import HTTPException

from ..schemas import (
    Point2D,
    SimulateRequest,
    SimulateResponse,
    SimulationInterceptor,
    SimulationPlayer,
)


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
HIGH_RISK_MARGIN = 0.15
MEDIUM_RISK_MARGIN = 0.75
RISK_CURVE_CENTER = (HIGH_RISK_MARGIN + MEDIUM_RISK_MARGIN) / 2
RISK_CURVE_STEEPNESS = math.log(3) / (RISK_CURVE_CENTER - HIGH_RISK_MARGIN)
PLAYER_INTERCEPT_HEIGHT = 2.1
GOALKEEPER_INTERCEPT_HEIGHT = 2.8


def _distance(a: Point2D, b: Point2D) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _is_on_pitch(point: Point2D) -> bool:
    return 0 <= point.x <= PITCH_LENGTH and 0 <= point.y <= PITCH_WIDTH


def _risk_percent_from_margin(time_margin: float) -> int:
    """Map the simulated time margin to a bounded, non-empirical risk index."""
    score = 100 / (
        1 + math.exp(RISK_CURVE_STEEPNESS * (time_margin - RISK_CURVE_CENTER))
    )
    return round(score)


def _ball_height(payload: SimulateRequest, path_progress_ratio: float) -> float:
    if payload.pass_type == "ground":
        return 0.0
    return 4 * payload.parameters.chip_apex_height * path_progress_ratio * (
        1 - path_progress_ratio
    )


def _intercept_height(defender: SimulationPlayer) -> float:
    return (
        GOALKEEPER_INTERCEPT_HEIGHT
        if defender.class_name == "goalkeeper"
        else PLAYER_INTERCEPT_HEIGHT
    )


def _best_interception_attempt(
    carrier_position: Point2D,
    target: Point2D,
    defender: SimulationPlayer,
    payload: SimulateRequest,
    pass_distance: float,
    sample_count: int,
) -> SimulationInterceptor:
    parameters = payload.parameters
    ball_speed = (
        parameters.chip_speed if payload.pass_type == "chip" else parameters.ball_speed
    )
    minimum_margin = math.inf
    best_point = target
    best_ratio = 1.0
    best_height = 0.0

    for index in range(1, sample_count + 1):
        ratio = index / sample_count
        point = Point2D(
            x=carrier_position.x + (target.x - carrier_position.x) * ratio,
            y=carrier_position.y + (target.y - carrier_position.y) * ratio,
        )
        ball_height = _ball_height(payload, ratio)
        if ball_height > _intercept_height(defender):
            continue
        ball_time = (pass_distance * ratio) / ball_speed
        run_distance = max(0.0, _distance(defender.position, point) - parameters.reach_radius)
        defender_time = parameters.reaction_time + run_distance / parameters.defender_speed
        margin = defender_time - ball_time
        if margin < minimum_margin:
            minimum_margin = margin
            best_point = point
            best_ratio = ratio
            best_height = ball_height

    return SimulationInterceptor(
        player_id=defender.id,
        intercept_point=Point2D(x=round(best_point.x, 3), y=round(best_point.y, 3)),
        time_margin=round(minimum_margin, 3),
        path_progress_ratio=round(best_ratio, 3),
        ball_height=round(best_height, 3),
    )


def simulate_pass(payload: SimulateRequest) -> SimulateResponse:
    players_by_id = {player.id: player for player in payload.players}
    carrier = players_by_id.get(payload.ball_carrier_id)
    if carrier is None:
        raise HTTPException(status_code=422, detail="ไม่พบ Ball Carrier ในรายชื่อผู้เล่น")
    if carrier.team_id.value == "unassigned":
        raise HTTPException(status_code=422, detail="Ball Carrier ต้องอยู่ใน Team A หรือ Team B")
    if not _is_on_pitch(carrier.position):
        raise HTTPException(status_code=422, detail="Ball Carrier อยู่นอกขอบเขตสนาม 105 × 68 เมตร")

    target = payload.target.position
    if payload.target.type == "receiver":
        receiver = players_by_id.get(payload.target.receiver_id or "")
        if receiver is None:
            raise HTTPException(status_code=422, detail="ไม่พบผู้รับบอลที่เลือก")
        if receiver.team_id != carrier.team_id:
            raise HTTPException(status_code=422, detail="เลือกผู้เล่นฝ่ายตรงข้ามเป็นผู้รับบอลไม่ได้")
        if receiver.id == carrier.id:
            raise HTTPException(status_code=422, detail="Ball Carrier ไม่สามารถส่งบอลให้ตัวเอง")
        # Use the calibrated player position as the source of truth instead of
        # trusting a second, client-provided copy of the receiver position.
        target = receiver.position

    if not _is_on_pitch(target):
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่นอกขอบเขตสนาม 105 × 68 เมตร")

    pass_distance = _distance(carrier.position, target)
    if pass_distance < 0.25:
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่ใกล้ Ball Carrier เกินไป")

    parameters = payload.parameters
    ball_speed = parameters.chip_speed if payload.pass_type == "chip" else parameters.ball_speed
    ball_time_total = pass_distance / ball_speed
    opponents = [
        player
        for player in payload.players
        if player.team_id != carrier.team_id and player.team_id.value != "unassigned"
    ]

    if not opponents:
        return SimulateResponse(
            pass_type=payload.pass_type,
            risk="low",
            risk_percent=0,
            pass_distance=round(pass_distance, 3),
            ball_time=round(ball_time_total, 3),
            interceptor_id=None,
            intercept_point=None,
            minimum_margin=None,
            interceptors=[],
            explanation="ความเสี่ยง 0% — ไม่มีผู้เล่นฝ่ายตรงข้ามที่มีพิกัดพร้อมสำหรับการคำนวณ",
        )

    sample_count = max(2, min(400, math.ceil(pass_distance / parameters.sample_step)))
    attempts = [
        _best_interception_attempt(
            carrier_position=carrier.position,
            target=target,
            defender=defender,
            payload=payload,
            pass_distance=pass_distance,
            sample_count=sample_count,
        )
        for defender in opponents
    ]
    attempts.sort(key=lambda attempt: attempt.time_margin)
    closest_attempt = attempts[0]
    minimum_margin = closest_attempt.time_margin
    risk_percent = _risk_percent_from_margin(minimum_margin)
    interceptors = [
        attempt for attempt in attempts if attempt.time_margin <= MEDIUM_RISK_MARGIN
    ]

    if minimum_margin <= HIGH_RISK_MARGIN:
        risk = "high"
        detail = "อาจเข้าถึงแนวจ่ายบอลได้ก่อนหรือใกล้เคียงกับเวลาที่บอลมาถึง"
    elif minimum_margin <= MEDIUM_RISK_MARGIN:
        risk = "medium"
        detail = "อยู่ใกล้แนวจ่ายบอลและมีช่วงเวลาสำรองไม่มาก"
    else:
        risk = "low"
        detail = "ต้องใช้เวลาเข้าถึงแนวจ่ายบอลมากกว่าเวลาที่บอลมาถึง"

    interceptor_id = closest_attempt.player_id if risk != "low" else None
    intercept_point = closest_attempt.intercept_point if risk != "low" else None
    subject = f"ผู้เล่น {closest_attempt.player_id}" if risk != "low" else "ผู้เล่นฝ่ายตรงข้ามที่ใกล้ที่สุด"
    pass_label = "ลูกชิพ" if payload.pass_type == "chip" else "ลูกเรียด"
    explanation = (
        f"{pass_label}: ดัชนีความเสี่ยงถูกตัดบอล {risk_percent}% ({risk.title()}) — {subject} {detail} "
        f"ภายใต้สมมติฐานที่กำหนด"
    )
    return SimulateResponse(
        pass_type=payload.pass_type,
        risk=risk,
        risk_percent=risk_percent,
        pass_distance=round(pass_distance, 3),
        ball_time=round(ball_time_total, 3),
        interceptor_id=interceptor_id,
        intercept_point=intercept_point,
        minimum_margin=round(minimum_margin, 3),
        interceptors=interceptors,
        explanation=explanation,
    )

