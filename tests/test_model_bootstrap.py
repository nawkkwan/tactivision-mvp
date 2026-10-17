from __future__ import annotations

import hashlib

import pytest

from backend.app.model_bootstrap import ensure_model, sha256_file


def test_sha256_file(tmp_path) -> None:
    model = tmp_path / "best.pt"
    model.write_bytes(b"fine-tuned-model")

    assert sha256_file(model) == hashlib.sha256(b"fine-tuned-model").hexdigest()


def test_existing_model_is_verified(tmp_path, monkeypatch) -> None:
    model = tmp_path / "best.pt"
    model.write_bytes(b"fine-tuned-model")
    monkeypatch.setenv("MODEL_PATH", str(model))
    monkeypatch.setenv("MODEL_SHA256", hashlib.sha256(model.read_bytes()).hexdigest())
    monkeypatch.delenv("MODEL_SOURCE_URL", raising=False)

    assert ensure_model() == model.resolve()


def test_existing_model_rejects_wrong_checksum(tmp_path, monkeypatch) -> None:
    model = tmp_path / "best.pt"
    model.write_bytes(b"fine-tuned-model")
    monkeypatch.setenv("MODEL_PATH", str(model))
    monkeypatch.setenv("MODEL_SHA256", "0" * 64)

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        ensure_model()
