from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from backend.app.services.detection import Detector


class FakeModel:
    def __init__(self, results: list[object] | None = None) -> None:
        self.call: dict[str, object] | None = None
        self.results = results or []

    def predict(self, **kwargs: object) -> list[object]:
        self.call = kwargs
        return self.results


class FakeTensor:
    def __init__(self, values: object) -> None:
        self.values = np.asarray(values)

    def cpu(self) -> "FakeTensor":
        return self

    def numpy(self) -> np.ndarray:
        return self.values


def test_detector_uses_configured_web_inference_thresholds() -> None:
    detector = Detector(
        "best.pt",
        confidence_threshold=0.15,
        person_confidence_threshold=0.50,
        ball_confidence_threshold=0.15,
        iou_threshold=0.61,
    )
    model = FakeModel()
    detector._model = model

    assert detector.predict(np.zeros((4, 4, 3), dtype=np.uint8)) == []
    assert model.call is not None
    assert model.call["conf"] == 0.15
    assert model.call["iou"] == 0.61
    assert detector.metadata.confidence_threshold == 0.15
    assert detector.metadata.person_confidence_threshold == 0.50
    assert detector.metadata.ball_confidence_threshold == 0.15


def test_detector_filters_people_and_ball_with_separate_thresholds() -> None:
    boxes = SimpleNamespace(
        xyxy=FakeTensor(
            [
                [0, 0, 10, 20],
                [10, 0, 20, 20],
                [20, 0, 25, 5],
                [25, 0, 30, 5],
            ]
        ),
        conf=FakeTensor([0.49, 0.50, 0.14, 0.15]),
        cls=FakeTensor([0, 0, 1, 1]),
    )
    result = SimpleNamespace(names={0: "person", 1: "ball"}, boxes=boxes)
    model = FakeModel([result])
    detector = Detector("best.pt")
    detector._model = model

    detections = detector.predict(np.zeros((40, 40, 3), dtype=np.uint8))

    assert [(item.id, item.class_name, item.confidence) for item in detections] == [
        ("p1", "player", 0.50),
        ("b1", "ball", 0.15),
    ]


@pytest.mark.parametrize("value", (-0.01, 1.01))
def test_detector_rejects_invalid_confidence_threshold(value: float) -> None:
    with pytest.raises(ValueError, match="confidence_threshold"):
        Detector("best.pt", confidence_threshold=value)


@pytest.mark.parametrize(
    ("argument", "value"),
    (("person_confidence_threshold", -0.01), ("ball_confidence_threshold", 1.01)),
)
def test_detector_rejects_invalid_class_threshold(argument: str, value: float) -> None:
    with pytest.raises(ValueError, match=argument):
        Detector("best.pt", **{argument: value})


def test_detector_rejects_inference_threshold_above_class_threshold() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        Detector(
            "best.pt",
            confidence_threshold=0.25,
            person_confidence_threshold=0.50,
            ball_confidence_threshold=0.15,
        )
