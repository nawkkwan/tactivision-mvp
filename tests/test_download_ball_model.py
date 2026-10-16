import hashlib
import sys
from types import SimpleNamespace

import pytest

from backend.app import download_ball_model as downloader


@pytest.fixture
def fake_download(monkeypatch):
    payload = b"pinned ball weights"
    monkeypatch.setattr(downloader, "BALL_MODEL_SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setitem(sys.modules, "truststore", SimpleNamespace(inject_into_ssl=lambda: None))
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        from pathlib import Path
        Path(kwargs["output"]).write_bytes(payload)
        return kwargs["output"]

    monkeypatch.setitem(sys.modules, "gdown", SimpleNamespace(download=download))
    return calls


def test_download_is_verified_and_existing_file_is_reused(tmp_path, fake_download):
    target = tmp_path / "models" / "ball.pt"
    assert downloader.download_ball_model(target) == target.resolve()
    assert downloader.download_ball_model(target) == target.resolve()
    assert len(fake_download) == 1
    assert list(target.parent.iterdir()) == [target]


def test_existing_invalid_model_is_not_overwritten(tmp_path, fake_download):
    target = tmp_path / "ball.pt"
    target.write_bytes(b"another model")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        downloader.download_ball_model(target)
    assert target.read_bytes() == b"another model"
    assert fake_download == []


def test_failed_checksum_cleans_temporary_download(tmp_path, fake_download, monkeypatch):
    monkeypatch.setattr(downloader, "BALL_MODEL_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        downloader.download_ball_model(tmp_path / "ball.pt")
    assert list(tmp_path.iterdir()) == []
