from types import SimpleNamespace
import sys

import numpy as np
import pytest

from backend.app.config import Settings
from backend.app.services.detection import Detector


class Tensor:
    def __init__(self, data):
        self.data = np.asarray(data)

    def cpu(self):
        return self

    def numpy(self):
        return self.data


class FakeModel:
    def __init__(self, names, records):
        self.names = names
        self.records = records
        self.calls = []
        self.error = None

    def predict(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return [SimpleNamespace(names=self.names, boxes=SimpleNamespace(
            xyxy=Tensor([r[0] for r in self.records]),
            conf=Tensor([r[1] for r in self.records]),
            cls=Tensor([r[2] for r in self.records]),
        ))]


IMAGE = np.zeros((100, 200, 3), dtype=np.uint8)


def make_detector(ball_records=None):
    detector = Detector("best.pt", ball_model_path="ball.pt")
    detector._model = FakeModel(
        {0: "ball", 1: "player", 2: "goalkeeper", 3: "referee"},
        [([10, 20, 30, 70], .9, 1), ([40, 20, 60, 70], .8, 2),
         ([70, 20, 90, 70], .7, 3), ([5, 5, 9, 9], .4, 0)],
    )
    detector._ball_model = FakeModel(
        {7: "sports ball", 8: "player"},
        ball_records if ball_records is not None else [([100, 50, 108, 58], .6, 7)],
    )
    return detector


def test_specialized_balls_replace_primary_balls_and_keep_people():
    detector = make_detector([([100, 50, 108, 58], .6, 7), ([1, 1, 5, 10], .9, 8)])
    detections = detector.predict(IMAGE)
    assert [(d.id, d.class_name) for d in detections] == [
        ("p1", "player"), ("p2", "goalkeeper"), ("p3", "referee"), ("b1", "ball")
    ]
    assert detections[0].foot_pixel.model_dump() == {"x": 20, "y": 70}
    assert detections[-1].foot_pixel.model_dump() == {"x": 104, "y": 54}
    assert detector._model.calls[0]["conf"] == .25
    assert detector._ball_model.calls[0]["conf"] == .15
    assert detector.ball_status["mode"] == "ready"


def test_successful_empty_ball_result_does_not_restore_primary_ball():
    assert not any(d.class_name == "ball" for d in make_detector([]).predict(IMAGE))


def test_ball_works_even_if_primary_finds_nothing():
    detector = make_detector()
    detector._model.records = []
    assert [(d.id, d.class_name) for d in detector.predict(IMAGE)] == [("b1", "ball")]


def test_ball_inference_failure_falls_back_and_can_recover():
    detector = make_detector()
    detector._ball_model.error = RuntimeError("out of memory")
    balls = [d for d in detector.predict(IMAGE) if d.class_name == "ball"]
    assert balls[0].bbox.x == 5
    assert detector.ball_status["mode"] == "fallback"
    assert "out of memory" in detector.ball_status["error"]
    detector._ball_model.error = None
    detector.predict(IMAGE)
    assert detector.ball_status["mode"] == "ready"


def test_missing_ball_model_falls_back_without_loading_yolo(tmp_path, monkeypatch):
    detector = make_detector()
    detector._ball_model = None
    detector.ball_model_path = str(tmp_path / "missing.pt")
    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(
        YOLO=lambda *_: pytest.fail("missing ball weights must not trigger a download")
    ))
    assert any(d.class_name == "ball" for d in detector.predict(IMAGE))
    assert detector.ball_status["mode"] == "fallback"


def test_disabled_ball_model_uses_primary():
    detector = make_detector()
    detector.ball_model_path = None
    assert [d.bbox.x for d in detector.predict(IMAGE) if d.class_name == "ball"] == [5]
    assert detector.ball_status["mode"] == "disabled"


@pytest.mark.parametrize("names,raises", [({0: "ball"}, False), ({0: "player"}, False), ({0: "ball"}, True)])
def test_ball_loading_cached_or_fallback(tmp_path, monkeypatch, names, raises):
    path = tmp_path / "ball.pt"
    path.write_bytes(b"fake weights")
    detector = make_detector()
    model = detector._ball_model
    model.names = names
    model.records = []
    detector._ball_model = None
    detector.ball_model_path = str(path)
    calls = []

    def load(source):
        calls.append(source)
        if raises:
            raise ValueError("corrupt model")
        return model

    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=load))
    detector.predict(IMAGE)
    if names == {0: "ball"} and not raises:
        detector.predict(IMAGE)
        assert len(calls) == 1
        assert detector.ball_status["mode"] == "ready"
    else:
        assert detector.ball_status["mode"] == "fallback"


def test_boxes_are_clipped_and_invalid_boxes_are_skipped():
    records = [("ball", [-5, -5, 10, 10], .5), ("player", [1, 1, 1, 5], .9),
               ("ball", [0, 0, float("nan"), 5], .5)]
    detections = Detector._to_detections(records, 200, 100)
    assert len(detections) == 1
    assert detections[0].bbox.model_dump() == {"x": 0, "y": 0, "width": 10, "height": 10}


@pytest.mark.parametrize("kwargs", [dict(ball_confidence=0), dict(ball_confidence=float("nan")),
                                    dict(detection_confidence=1.1), dict(detection_imgsz=0)])
def test_invalid_inference_settings(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)
