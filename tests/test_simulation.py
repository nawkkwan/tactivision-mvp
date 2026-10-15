from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.app.schemas import SimulateRequest
from backend.app.services.simulation import _risk_percent_from_margin, simulate_pass


def request_with(defender_y: float, ball_speed: float = 18) -> SimulateRequest:
    return SimulateRequest.model_validate(
        {
            "players": [
                {"id": "p1", "team_id": "team_a", "position": {"x": 10, "y": 34}},
                {"id": "p2", "team_id": "team_a", "position": {"x": 40, "y": 34}},
                {"id": "p3", "team_id": "team_b", "position": {"x": 25, "y": defender_y}},
            ],
            "ball_carrier_id": "p1",
            "target": {
                "type": "receiver",
                "receiver_id": "p2",
                "position": {"x": 40, "y": 34},
            },
            "parameters": {"ball_speed": ball_speed},
        }
    )


def test_defender_on_path_is_high_risk() -> None:
    result = simulate_pass(request_with(34))
    assert result.risk == "high"
    assert result.risk_percent >= 75
    assert result.interceptor_id == "p3"
    assert result.pass_distance == 30
    assert result.interceptors[0].player_id == "p3"
    assert result.interceptors[0].time_margin <= 0.15


def test_distant_defender_is_low_risk() -> None:
    result = simulate_pass(request_with(60))
    assert result.risk == "low"
    assert result.risk_percent < 25
    assert result.interceptor_id is None
    assert result.intercept_point is None
    assert result.interceptors == []


def test_opponent_cannot_be_receiver() -> None:
    source = request_with(40).model_dump()
    source["target"] = {
        "type": "receiver",
        "receiver_id": "p3",
        "position": {"x": 25, "y": 40},
    }
    payload = SimulateRequest.model_validate(source)
    with pytest.raises(HTTPException) as error:
        simulate_pass(payload)
    assert error.value.status_code == 422


def test_receiver_position_comes_from_calibrated_player() -> None:
    source = request_with(60).model_dump()
    source["target"]["position"] = {"x": 70, "y": 10}
    payload = SimulateRequest.model_validate(source)

    result = simulate_pass(payload)

    assert result.pass_distance == 30


def test_interceptors_are_sorted_by_time_margin() -> None:
    source = request_with(34).model_dump()
    source["players"].append(
        {"id": "p4", "team_id": "team_b", "position": {"x": 20, "y": 35}}
    )
    payload = SimulateRequest.model_validate(source)

    result = simulate_pass(payload)

    assert [item.player_id for item in result.interceptors] == ["p3", "p4"]
    assert result.interceptors[0].time_margin <= result.interceptors[1].time_margin


def test_fast_ball_reduces_risk() -> None:
    slow = simulate_pass(request_with(40, ball_speed=8))
    fast = simulate_pass(request_with(40, ball_speed=30))

    assert slow.minimum_margin is not None
    assert fast.minimum_margin is not None
    assert fast.minimum_margin > slow.minimum_margin
    assert fast.risk_percent < slow.risk_percent


def test_risk_percent_matches_existing_risk_thresholds() -> None:
    assert _risk_percent_from_margin(0.15) == 75
    assert _risk_percent_from_margin(0.45) == 50
    assert _risk_percent_from_margin(0.75) == 25


def test_unassigned_player_cannot_be_ball_carrier() -> None:
    source = request_with(34).model_dump()
    source["players"][0]["team_id"] = "unassigned"
    payload = SimulateRequest.model_validate(source)

    with pytest.raises(HTTPException) as error:
        simulate_pass(payload)

    assert error.value.status_code == 422

