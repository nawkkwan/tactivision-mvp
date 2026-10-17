from __future__ import annotations

import cv2
import numpy as np

from backend.app.schemas import Detection
from backend.app.services import team_classifier
from backend.app.services.team_classifier import classify_teams


def make_player(identifier: str, x: int) -> Detection:
    return Detection.model_validate(
        {
            "id": identifier,
            "class_name": "player",
            "confidence": 0.9,
            "bbox": {"x": x, "y": 50, "width": 60, "height": 140},
            "foot_pixel": {"x": x + 30, "y": 190},
        }
    )


def test_siglip_and_color_features_split_two_teams(monkeypatch) -> None:
    image = np.zeros((260, 420, 3), dtype=np.uint8)
    image[:] = (35, 125, 45)
    detections = []
    for index, (x, color) in enumerate(
        [
            (25, (220, 60, 30)),
            (105, (220, 60, 30)),
            (225, (30, 40, 225)),
            (305, (30, 40, 225)),
        ],
        start=1,
    ):
        cv2.rectangle(image, (x, 50), (x + 60, 125), color, -1)
        detections.append(make_player(f"p{index}", x))

    monkeypatch.setattr(
        team_classifier,
        "_siglip_features",
        lambda shirts: np.repeat([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]], 1, axis=0),
    )
    result = classify_teams(image, detections)
    assert result[0].team_id in {"team_a", "team_b"}
    assert result[1].team_id == result[0].team_id
    assert result[2].team_id in {"team_a", "team_b"}
    assert result[3].team_id == result[2].team_id
    assert result[0].team_id != result[2].team_id
    assert result[0].team_confidence is not None


def test_team_classifier_does_not_guess_with_too_few_players() -> None:
    image = np.zeros((260, 420, 3), dtype=np.uint8)
    image[:] = (35, 125, 45)
    cv2.rectangle(image, (50, 50), (110, 125), (220, 60, 30), -1)
    cv2.rectangle(image, (280, 50), (340, 125), (30, 40, 225), -1)

    result = classify_teams(image, [make_player("p1", 50), make_player("p2", 280)])
    assert all(item.team_id == "unassigned" for item in result)

