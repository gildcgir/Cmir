"""Unit-тесты платформенных адаптеров."""
from __future__ import annotations

from platforms import PLATFORMS, get_adapter


def test_platforms_list():
    assert "youtube" in PLATFORMS
    assert "twitch" in PLATFORMS
    assert len(PLATFORMS) == 4


def test_authorize_url():
    adapter = get_adapter("youtube")
    url = adapter.authorize_url("http://localhost/cb", "state123")
    assert "client_id" in url
    assert "redirect_uri" in url


def test_unknown_platform():
    import pytest

    with pytest.raises(ValueError):
        get_adapter("unknown")
