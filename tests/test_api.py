from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from backend.app.main import detect, health


def test_health_reports_modules() -> None:
    data = health()
    assert data["status"] == "ok"
    assert data["modules"]["simulation"] == "ready"


def test_detect_rejects_wrong_content_type() -> None:
    upload = UploadFile(
        file=BytesIO(b"hello"),
        filename="notes.txt",
        headers=Headers({"content-type": "text/plain"}),
    )
    with pytest.raises(HTTPException) as error:
        detect(upload).send(None)
    assert error.value.status_code == 415

