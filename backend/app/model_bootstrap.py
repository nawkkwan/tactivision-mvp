from __future__ import annotations

import hashlib
import os
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(path: Path, expected_sha256: str | None) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Model file is missing or empty: {path}")
    if expected_sha256:
        actual = sha256_file(path)
        if actual.lower() != expected_sha256.lower():
            raise RuntimeError(
                f"Model checksum mismatch: expected {expected_sha256}, got {actual}"
            )


def ensure_model() -> Path:
    target = Path(os.getenv("MODEL_PATH", "backend/models/best.pt")).resolve()
    expected_sha256 = os.getenv("MODEL_SHA256") or None

    if target.is_file():
        _verify(target, expected_sha256)
        print(f"Model ready: {target}")
        return target

    raise RuntimeError(f"Model not found at {target}")


if __name__ == "__main__":
    ensure_model()
