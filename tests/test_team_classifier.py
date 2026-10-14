from __future__ import annotations

import cv2
import numpy as np

from backend.app.schemas import Detection
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


def test_jersey_colors_are_split_into_two_teams() -> None:
    image = np.zeros((260, 420, 3), dtype=np.uint8)
    image[:] = (35, 125, 45)
    cv2.rectangle(image, (50, 50), (110, 125), (220, 60, 30), -1)
    cv2.rectangle(image, (280, 50), (340, 125), (30, 40, 225), -1)

    result = classify_teams(image, [make_player("p1", 50), make_player("p2", 280)])
    assert result[0].team_id in {"team_a", "team_b"}
    assert result[1].team_id in {"team_a", "team_b"}
    assert result[0].team_id != result[1].team_id

