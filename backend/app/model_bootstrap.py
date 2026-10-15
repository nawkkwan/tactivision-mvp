from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
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


def _download(source_url: str, output_dir: Path) -> Path:
    import gdown

    if "/folders/" in source_url:
        downloaded = gdown.download_folder(
            url=source_url,
            output=str(output_dir),
            quiet=False,
            use_cookies=False,
        )
        candidates = [Path(item) for item in downloaded or []]
        candidates.extend(output_dir.rglob("best.pt"))
        for candidate in candidates:
            if candidate.name.lower() == "best.pt" and candidate.is_file():
                return candidate
        raise RuntimeError("Google Drive folder does not contain best.pt")

    destination = output_dir / "best.pt"
    downloaded = gdown.download(
        url=source_url,
        output=str(destination),
        quiet=False,
        fuzzy=True,
        use_cookies=False,
    )
    if not downloaded:
        raise RuntimeError("Model download failed")
    return Path(downloaded)


def ensure_model() -> Path:
    target = Path(os.getenv("MODEL_PATH", "backend/models/best.pt")).resolve()
    expected_sha256 = os.getenv("MODEL_SHA256") or None

    if target.is_file():
        _verify(target, expected_sha256)
        print(f"Model ready: {target}")
        return target

    source_url = os.getenv("MODEL_SOURCE_URL")
    if not source_url:
        raise RuntimeError(
            f"Model not found at {target} and MODEL_SOURCE_URL is not configured"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="model-download-", dir=target.parent) as temp:
        downloaded = _download(source_url, Path(temp))
        _verify(downloaded, expected_sha256)
        staged = target.with_suffix(".pt.part")
        shutil.copy2(downloaded, staged)
        os.replace(staged, target)

    _verify(target, expected_sha256)
    print(f"Model downloaded and verified: {target}")
    return target


if __name__ == "__main__":
    ensure_model()
