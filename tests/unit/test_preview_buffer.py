"""Unit-тесты preview buffer."""
from __future__ import annotations

from preview_buffer import PREVIEW_SECONDS, PREVIEW_TARGET_SEC, PreviewBuffer


def test_preview_constants():
    assert PREVIEW_SECONDS == 10
    assert PREVIEW_TARGET_SEC == 10


def test_preview_status_not_ready():
    buf = PreviewBuffer()
    st = buf.status("nonexistent-poi-id")
    assert st["ready"] is False
    assert st["target_seconds"] == 10
    assert st.get("error") is None
