"""Интеграции YouTube, Twitch, Instagram, TikTok — OAuth, стримы, комментарии, статистика."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List

PLATFORMS = ("youtube", "twitch", "instagram", "tiktok")


class PlatformAdapter(ABC):
    name: str

    @abstractmethod
    def authorize_url(self, redirect_uri: str, state: str) -> str:
        ...

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    def fetch_comments(self, access_token: str, broadcast_id: str, limit: int = 50) -> List[dict]:
        ...

    @abstractmethod
    def post_comment(self, access_token: str, broadcast_id: str, text: str) -> dict:
        ...

    @abstractmethod
    def fetch_user_stats(self, access_token: str, external_user_id: str) -> dict:
        ...

    @abstractmethod
    def start_multicast(self, access_token: str, ingest_url: str, title: str) -> dict:
        ...


class _StubAdapter(PlatformAdapter):
    """Каркас адаптера: OAuth-ключи через env SMIR_{PLATFORM}_CLIENT_ID / _SECRET."""

    def __init__(self, name: str, oauth_base: str, api_base: str) -> None:
        self.name = name
        self.oauth_base = oauth_base
        self.api_base = api_base

    def _client_id(self) -> str:
        return os.environ.get(f"SMIR_{self.name.upper()}_CLIENT_ID", "")

    def _client_secret(self) -> str:
        return os.environ.get(f"SMIR_{self.name.upper()}_CLIENT_SECRET", "")

    def authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._client_id() or f"smir-{self.name}-demo",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "read write broadcast",
        }
        return f"{self.oauth_base}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self._client_id():
            return {
                "access_token": f"demo-{self.name}-{code[:8]}",
                "refresh_token": "",
                "external_user_id": f"demo_{self.name}",
                "username": f"demo_{self.name}",
            }
        data = urllib.parse.urlencode(
            {
                "client_id": self._client_id(),
                "client_secret": self._client_secret(),
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.api_base}/oauth/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())

    def fetch_comments(self, access_token: str, broadcast_id: str, limit: int = 50) -> List[dict]:
        return []

    def post_comment(self, access_token: str, broadcast_id: str, text: str) -> dict:
        return {"id": f"local-{self.name}", "text": text, "status": "queued"}

    def fetch_user_stats(self, access_token: str, external_user_id: str) -> dict:
        return {"platform": self.name, "followers": 0, "views": 0, "external_user_id": external_user_id}

    def start_multicast(self, access_token: str, ingest_url: str, title: str) -> dict:
        return {
            "platform": self.name,
            "status": "pending_credentials" if not self._client_id() else "starting",
            "ingest_url": ingest_url,
            "title": title,
        }


ADAPTERS: Dict[str, PlatformAdapter] = {
    "youtube": _StubAdapter("youtube", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com"),
    "twitch": _StubAdapter("twitch", "https://id.twitch.tv/oauth2/authorize", "https://id.twitch.tv/oauth2"),
    "instagram": _StubAdapter("instagram", "https://api.instagram.com/oauth/authorize", "https://api.instagram.com"),
    "tiktok": _StubAdapter("tiktok", "https://www.tiktok.com/v2/auth/authorize", "https://open.tiktokapis.com"),
}


def get_adapter(platform: str) -> PlatformAdapter:
    if platform not in ADAPTERS:
        raise ValueError(f"unsupported platform: {platform}")
    return ADAPTERS[platform]
