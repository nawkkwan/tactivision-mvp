"""Download the pinned Roboflow Sports ball weights explicitly, never during API calls."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

from .model_bootstrap import _verify

# Source: https://github.com/roboflow/sports/blob/main/examples/soccer/setup.sh
BALL_MODEL_ID = "1isw4wx-MK9h9LMr36VvIWlJD6ppUvw7V"
BALL_MODEL_SHA256 = "678fbad05134f19c5094cb8d273812ec9c6691228180d46832551ecf99ed2912"


def download_ball_model(target: Path) -> Path:
    target = target.resolve()
    if target.is_file():
        _verify(target, BALL_MODEL_SHA256)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    # Trust Windows' certificate store without disabling HTTPS validation.
    if os.name == "nt":
        import truststore
        truststore.inject_into_ssl()
    import gdown

    with tempfile.NamedTemporaryFile(prefix="ball-download-", suffix=".pt", dir=target.parent, delete=False) as handle:
        temporary_path = Path(handle.name)
    try:
        downloaded = gdown.download(id=BALL_MODEL_ID, output=str(temporary_path), quiet=False)
        if not downloaded:
            raise RuntimeError("Ball model download failed")
        _verify(temporary_path, BALL_MODEL_SHA256)
        if target.exists():
            _verify(target, BALL_MODEL_SHA256)
        else:
            temporary_path.replace(target)
    finally:
        temporary_path.unlink(missing_ok=True)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(os.getenv("BALL_MODEL_PATH") or "backend/models/football-ball-detection.pt"))
    args = parser.parse_args()
    print(f"Ball model ready: {download_ball_model(args.output)}")
