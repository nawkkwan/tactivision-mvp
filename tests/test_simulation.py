from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.app.schemas import SimulateRequest
from backend.app.services.simulation import simulate_pass


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
    assert result.interceptor_id == "p3"
    assert result.pass_distance == 30


def test_distant_defender_is_low_risk() -> None:
    result = simulate_pass(request_with(60))
    assert result.risk == "low"


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

