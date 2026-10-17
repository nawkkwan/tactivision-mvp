"""Exercise the actual notebook's fixed-threshold matcher without loading YOLO."""
import json
from pathlib import Path
import unittest


notebook = json.loads((Path(__file__).resolve().parents[1] / "training/confidence_sweep.ipynb").read_text(encoding="utf-8"))
source = "".join(next(cell for cell in notebook["cells"] if cell.get("id") == "matching")["source"])
namespace = {}
exec(compile(source, "confidence_sweep.ipynb:matching", "exec"), namespace)
count = namespace["counts_at_threshold"]
iou = namespace["box_iou"]
rates = namespace["precision_recall"]


def prediction(class_id=2, confidence=.8, xyxy=(0,0,10,10)):
    return {"class_id":class_id,"confidence":confidence,"xyxy":xyxy}


def answer(class_id=2, xyxy=(0,0,10,10)):
    return {"class_id":class_id,"xyxy":xyxy}


class ConfidenceSweepTests(unittest.TestCase):
    def test_threshold_can_remove_false_positive_and_true_positive(self):
        predictions=[prediction(confidence=.4),prediction(confidence=.2,xyxy=(20,20,30,30))]
        low=count(predictions,[answer()],.15)[2]
        medium=count(predictions,[answer()],.3)[2]
        high=count(predictions,[answer()],.5)[2]
        self.assertEqual(low,{"tp":1,"fp":1,"fn":0})
        self.assertEqual(medium,{"tp":1,"fp":0,"fn":0})
        self.assertEqual(high,{"tp":0,"fp":0,"fn":1})

    def test_wrong_class_remains_wrong_at_high_confidence(self):
        result=count([prediction(class_id=1,confidence=.95)],[answer()],.5)
        self.assertEqual(result[1],{"tp":0,"fp":1,"fn":0})
        self.assertEqual(result[2],{"tp":0,"fp":0,"fn":1})

    def test_only_one_detection_matches_each_answer(self):
        result=count([prediction(confidence=.9),prediction(confidence=.8)],[answer()],.15)
        self.assertEqual(result[2],{"tp":1,"fp":1,"fn":0})

    def test_iou_requirement_and_boundary(self):
        self.assertEqual(iou((0,0,10,10),(20,20,30,30)),0)
        self.assertEqual(iou((0,0,10,10),(0,0,10,10)),1)
        result=count([prediction(xyxy=(0,0,5,10))],[answer()],.15,match_iou=.5)
        self.assertEqual(result[2]["tp"],1)
        result=count([prediction(xyxy=(0,0,4,10))],[answer()],.15,match_iou=.5)
        self.assertEqual(result[2],{"tp":0,"fp":1,"fn":1})

    def test_no_predictions_and_empty_answers(self):
        self.assertEqual(count([],[answer()],.15)[2],{"tp":0,"fp":0,"fn":1})
        self.assertEqual(count([prediction()],[],.15)[2],{"tp":0,"fp":1,"fn":0})
        self.assertEqual(rates({"tp":0,"fp":0,"fn":0}),{"precision":0,"recall":0})

    def test_threshold_includes_equality_and_matches_by_confidence(self):
        result=count([prediction(confidence=.3)],[answer()],.3)
        self.assertEqual(result[2]["tp"],1)
        self.assertEqual(rates({"tp":2,"fp":2,"fn":6}),{"precision":.5,"recall":.25})


if __name__ == "__main__":
    unittest.main()
