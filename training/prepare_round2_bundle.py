"""Build one Colab input ZIP: Train/Validation plus the frozen initial model, no Test files."""
import argparse
from pathlib import Path

try:
    from .round2_workflow import build_training_bundle
except ImportError:
    from round2_workflow import build_training_bundle


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("training/data/prepared/football-v3-ready"))
    parser.add_argument("--model", type=Path, default=Path("backend/models/best.pt"))
    parser.add_argument("--output", type=Path, default=Path("training/data/prepared/football-v3-training-ready.zip"))
    parser.add_argument("--review", type=Path, default=Path("training/hardcases_v3_label_review.json"))
    args = parser.parse_args()
    manifest = build_training_bundle(args.dataset, args.model, args.output, args.review)
    print("Prepared:", args.output.resolve())
    print("Counts:", manifest["counts"], "Test included:", manifest["test_images_included"])
