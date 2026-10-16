from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from prepare_roboflow_export import prepare
from prepare_test_export import prepare_test, read_unique_members


def jpeg(color):
    stream = BytesIO()
    Image.new("RGB", (1280,720), color).save(stream, format="JPEG")
    return stream.getvalue()


class TestExportTests(unittest.TestCase):
    def fixture(self, root, test_label="2 0.5 0.5 0.2 0.4\n", test_color="red"):
        source = root / "train.zip"
        config = "names: ['ball', 'goalkeeper', 'player', 'referee']\n"
        with ZipFile(source,"w") as z:
            z.writestr("data.yaml",config)
            for clip,color in [("PFYsHN24C3k","green"),("tJnScrAKJfI","blue")]:
                name = f"{clip}_00-12-00"
                z.writestr(f"train/images/{name}.jpg",jpeg(color))
                z.writestr(f"train/labels/{name}.txt","2 0.5 0.5 0.2 0.4\n")
        frozen = root / "frozen"
        prepare(source,frozen,"tJnScrAKJfI",root/"preview")
        results = root / "results.zip"
        with ZipFile(results,"w") as z:
            z.writestr("split_manifest.json",(frozen/"split_manifest.json").read_bytes())
            z.writestr("best.pt",b"model artifact placeholder - never executed")
        test_zip = root / "test.zip"
        with ZipFile(test_zip,"w") as z, warnings.catch_warnings():
            warnings.simplefilter("ignore",UserWarning)
            z.writestr("data.yaml",config)
            z.writestr("data.yaml",config)
            z.writestr("test/images/idq95Xp5RI0_00-12-00.jpg",jpeg(test_color))
            z.writestr("test/labels/idq95Xp5RI0_00-12-00.txt",test_label)
        return test_zip,frozen,results

    def test_preserves_test_labels_and_includes_frozen_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source,frozen,results=self.fixture(root)
            original=source.read_bytes()
            output=root/"out"
            report=prepare_test(source,frozen,results,output,root/"review")
            self.assertEqual(report["test_images"],1)
            self.assertFalse(report["labels_changed"])
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual((output/"test/labels/idq95Xp5RI0_00-12-00.txt").read_text(),"2 0.5 0.5 0.2 0.4\n")
            self.assertTrue((output/"models/best.pt").is_file())
            self.assertEqual(json.loads((output/"data.yaml").read_text())["test"],"test/images")
            with ZipFile(str(output)+".zip") as z:
                self.assertIsNone(z.testzip())

    def test_rejects_test_overlap_with_training_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source,frozen,results=self.fixture(root,test_color="green")
            with self.assertRaisesRegex(ValueError,"Train/Validation"):
                prepare_test(source,frozen,results,root/"out",root/"review")
            self.assertFalse((root/"out").exists())

    def test_rejects_empty_test_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source,frozen,results=self.fixture(root,test_label="")
            with self.assertRaisesRegex(ValueError,"Empty Test label"):
                prepare_test(source,frozen,results,root/"out",root/"review")

    def test_rejects_conflicting_duplicate_config(self):
        stream=BytesIO()
        with ZipFile(stream,"w") as z, warnings.catch_warnings():
            warnings.simplefilter("ignore",UserWarning)
            z.writestr("data.yaml","one")
            z.writestr("data.yaml","two")
        stream.seek(0)
        with ZipFile(stream) as z, self.assertRaisesRegex(ValueError,"Conflicting duplicate"):
            read_unique_members(z)


if __name__ == "__main__":
    unittest.main()
