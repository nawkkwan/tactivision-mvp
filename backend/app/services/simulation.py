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
    apex_height = (
        payload.parameters.chip_apex_height
        if payload.pass_type == "chip"
        else payload.parameters.long_ball_apex_height
    )
    return 4 * apex_height * path_progress_ratio * (
        1 - path_progress_ratio
    )


def _ball_speed(payload: SimulateRequest) -> float:
    if payload.pass_type == "ground":
        return payload.parameters.ball_speed
    if payload.pass_type == "chip":
        return payload.parameters.chip_speed
    return payload.parameters.long_ball_speed


def _intercept_height(defender: SimulationPlayer) -> float:
    return (
        GOALKEEPER_INTERCEPT_HEIGHT
        if defender.class_name == "goalkeeper"
        else PLAYER_INTERCEPT_HEIGHT
    )


def _arrival_time(
    player: SimulationPlayer,
    point: Point2D,
    speed: float,
    reaction_time: float,
    reach_radius: float,
) -> float:
    run_distance = max(0.0, _distance(player.position, point) - reach_radius)
    return reaction_time + run_distance / speed


def _best_interception_attempt(
    carrier_position: Point2D,
    target: Point2D,
    defender: SimulationPlayer,
    teammates: list[SimulationPlayer],
    payload: SimulateRequest,
    pass_distance: float,
    sample_count: int,
) -> SimulationInterceptor:
    parameters = payload.parameters
    ball_speed = _ball_speed(payload)
    minimum_margin = math.inf
    best_point = target
    best_ratio = 1.0
    best_height = 0.0
    best_ball_time = 0.0
    best_defender_time = 0.0
    best_teammate: SimulationPlayer | None = None
    best_teammate_time: float | None = None
    best_ball_margin = math.inf
    best_teammate_margin: float | None = None

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
        defender_time = _arrival_time(
            defender,
            point,
            parameters.defender_speed,
            parameters.reaction_time,
            parameters.reach_radius,
        )
        ball_margin = defender_time - ball_time
        fastest_teammate: SimulationPlayer | None = None
        fastest_teammate_time: float | None = None
        if teammates:
            teammate_times = [
                (
                    teammate,
                    _arrival_time(
                        teammate,
                        point,
                        parameters.attacker_speed,
                        parameters.reaction_time,
                        parameters.reach_radius,
                    ),
                )
                for teammate in teammates
            ]
            fastest_teammate, fastest_teammate_time = min(
                teammate_times, key=lambda item: item[1]
            )
        teammate_margin = (
            defender_time - fastest_teammate_time
            if fastest_teammate_time is not None
            else None
        )
        # A defender must both meet the ball and beat the nearest supporting
        # teammate. The larger margin represents the harder of those two tests.
        margin = (
            max(ball_margin, teammate_margin)
            if teammate_margin is not None
            else ball_margin
        )
        if margin < minimum_margin:
            minimum_margin = margin
            best_point = point
            best_ratio = ratio
            best_height = ball_height
            best_ball_time = ball_time
            best_defender_time = defender_time
            best_teammate = fastest_teammate
            best_teammate_time = fastest_teammate_time
            best_ball_margin = ball_margin
            best_teammate_margin = teammate_margin

    return SimulationInterceptor(
        player_id=defender.id,
        intercept_point=Point2D(x=round(best_point.x, 3), y=round(best_point.y, 3)),
        time_margin=round(minimum_margin, 3),
        path_progress_ratio=round(best_ratio, 3),
        ball_height=round(best_height, 3),
        ball_time=round(best_ball_time, 3),
        defender_time=round(best_defender_time, 3),
        teammate_id=best_teammate.id if best_teammate else None,
        teammate_time=round(best_teammate_time, 3) if best_teammate_time is not None else None,
        ball_time_margin=round(best_ball_margin, 3),
        teammate_time_margin=(
            round(best_teammate_margin, 3) if best_teammate_margin is not None else None
        ),
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
    selected_receiver: SimulationPlayer | None = None
    if payload.target.type in {"receiver", "through_ball"}:
        receiver = players_by_id.get(payload.target.receiver_id or "")
        if receiver is None:
            raise HTTPException(status_code=422, detail="ไม่พบผู้รับบอลที่เลือก")
        if receiver.team_id != carrier.team_id:
            raise HTTPException(status_code=422, detail="เลือกผู้เล่นฝ่ายตรงข้ามเป็นผู้รับบอลไม่ได้")
        if receiver.id == carrier.id:
            raise HTTPException(status_code=422, detail="Ball Carrier ไม่สามารถส่งบอลให้ตัวเอง")
        # Normal passes use the calibrated player location; through balls use
        # the user-selected lead point and this player as the intended runner.
        if payload.target.type == "receiver":
            target = receiver.position
        selected_receiver = receiver
        selected_receiver = receiver

    if not _is_on_pitch(target):
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่นอกขอบเขตสนาม 105 × 68 เมตร")

    pass_distance = _distance(carrier.position, target)
    if pass_distance < 0.25:
        raise HTTPException(status_code=422, detail="เป้าหมายอยู่ใกล้ Ball Carrier เกินไป")

    parameters = payload.parameters
    ball_speed = _ball_speed(payload)
    ball_time_total = pass_distance / ball_speed
    opponents = [
        player
        for player in payload.players
        if player.team_id != carrier.team_id and player.team_id.value != "unassigned"
    ]
    teammates = [
        player
        for player in payload.players
        if player.team_id == carrier.team_id and player.id != carrier.id
    ]
    eligible_teammates = [selected_receiver] if selected_receiver else teammates
    receiver: SimulationPlayer | None = None
    receiver_arrival_time: float | None = None
    if eligible_teammates:
        receiver, receiver_arrival_time = min(
            [
                (
                    teammate,
                    _arrival_time(
                        teammate,
                        target,
                        parameters.attacker_speed,
                        parameters.reaction_time,
                        parameters.reach_radius,
                    ),
                )
                for teammate in eligible_teammates
            ],
            key=lambda item: item[1],
        )
    receiver_ball_margin = (
        receiver_arrival_time - ball_time_total
        if receiver_arrival_time is not None
        else None
    )

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
            receiver_id=receiver.id if receiver else None,
            receiver_arrival_time=(
                round(receiver_arrival_time, 3) if receiver_arrival_time is not None else None
            ),
            receiver_ball_margin=(
                round(receiver_ball_margin, 3) if receiver_ball_margin is not None else None
            ),
            interceptors=[],
            explanation="ความเสี่ยง 0% — ไม่มีผู้เล่นฝ่ายตรงข้ามที่มีพิกัดพร้อมสำหรับการคำนวณ",
        )

    sample_count = max(2, min(400, math.ceil(pass_distance / parameters.sample_step)))
    attempts = [
        _best_interception_attempt(
            carrier_position=carrier.position,
            target=target,
            defender=defender,
            teammates=eligible_teammates,
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
    pass_label = {
        "ground": "ลูกเรียด",
        "chip": "ลูกชิพ",
        "long_ball": "ลูกเปิดยาว",
    }[payload.pass_type]
    if payload.target.type == "through_ball":
        pass_label = f"แทงทะลุช่อง ({pass_label})"
    receiver_detail = (
        f" โดย {receiver.id} เป็นผู้เล่นฝ่ายเดียวกันที่ถึงจุดรับเร็วที่สุด "
        f"({receiver_arrival_time:.2f} วินาที)"
        if receiver is not None and receiver_arrival_time is not None
        else " โดยไม่พบเพื่อนร่วมทีมที่เข้าถึงจุดรับ"
    )
    explanation = (
        f"{pass_label}: ดัชนีความเสี่ยงถูกตัดบอล {risk_percent}% ({risk.title()}) — {subject} {detail} "
        f"ภายใต้สมมติฐานที่กำหนด{receiver_detail}"
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
        receiver_id=receiver.id if receiver else None,
        receiver_arrival_time=(
            round(receiver_arrival_time, 3) if receiver_arrival_time is not None else None
        ),
        receiver_ball_margin=(
            round(receiver_ball_margin, 3) if receiver_ball_margin is not None else None
        ),
        interceptors=interceptors,
        explanation=explanation,
    )

