"""Dataset splitting must preserve annotations and keep held-out matches separate."""
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from prepare_roboflow_export import prepare, duplicate_boxes


class PrepareExportTests(unittest.TestCase):
    def fixture(self, root, train_label="2 0.5 0.5 0.2 0.4\n", extra_member=None):
        source = root / "input.zip"
        with ZipFile(source, "w") as z:
            z.writestr("data.yaml", "names: ['ball', 'goalkeeper', 'player', 'referee']\n")
            for clip, color, label in [("PFYsHN24C3k", "green", train_label), ("tJnScrAKJfI", "blue", "0 0.5 0.5 0.1 0.1\n")]:
                name = f"{clip}_00-12-00_jpg.rf.example"
                stream = BytesIO()
                Image.new("RGB", (1280, 720), color).save(stream, format="JPEG")
                z.writestr(f"train/images/{name}.jpg", stream.getvalue())
                z.writestr(f"train/labels/{name}.txt", label)
            if extra_member:
                z.writestr(extra_member, "bad")
        return source

    def test_holds_out_whole_clip_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root)
            original = source.read_bytes()
            output = root / "prepared"
            report = prepare(source, output, "tJnScrAKJfI", root / "review")
            self.assertEqual(report["splits"]["train"]["clips"], ["PFYsHN24C3k"])
            self.assertEqual(report["splits"]["valid"]["clips"], ["tJnScrAKJfI"])
            self.assertEqual(source.read_bytes(), original)
            config = json.loads((output / "data.yaml").read_text())
            self.assertNotIn("test", config)
            self.assertTrue((output / config["val"]).is_dir())
            self.assertTrue(output.with_suffix(".zip").is_file())

    def test_duplicate_removal_is_opt_in_and_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root, "2 0.5 0.5 0.2 0.4\n2 0.5 0.5 0.2 0.4\n")
            kept = prepare(source, root / "kept", "tJnScrAKJfI", root / "review1")
            cleaned = prepare(source, root / "cleaned", "tJnScrAKJfI", root / "review2", True)
            self.assertEqual(kept["splits"]["train"]["boxes"]["player"], 2)
            self.assertEqual(cleaned["splits"]["train"]["boxes"]["player"], 1)
            self.assertEqual(cleaned["removed_duplicate_boxes"], 1)
            label = next((root / "cleaned/train/labels").glob("*.txt"))
            self.assertEqual(len(label.read_text().splitlines()), 1)

    def test_overlap_alone_does_not_remove_different_objects(self):
        self.assertEqual(duplicate_boxes([(2,.5,.5,.2,.4), (2,.51,.5,.2,.4), (3,.5,.5,.2,.4)], 1280, 720), [])

    def test_rejects_invalid_box_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root, "2 nan 0.5 0.2 0.4\n")
            with self.assertRaises(ValueError):
                prepare(source, root / "out", "tJnScrAKJfI", root / "review")
            self.assertFalse((root / "out").exists())

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root, extra_member="../escape.txt")
            with self.assertRaises(ValueError):
                prepare(source, root / "out", "tJnScrAKJfI", root / "review")


if __name__ == "__main__":
    unittest.main()
