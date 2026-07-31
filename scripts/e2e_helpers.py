"""Shared helpers for Cmir E2E scripts (auth + API calls)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

PATCH_DIM = 32 * 32


def api_call(
    api: str,
    method: str,
    path: str,
    body: dict | None = None,
    token: str = "",
) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{api}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def ensure_admin(api: str) -> str:
    login = api_call(api, "POST", "/api/v1/auth/login", {"email": "admin", "password": "admin"})
    return login["data"]["token"]


def ensure_auth(api: str, email: str = "e2e@cmir.test", password: str = "testpass123") -> str:
    try:
        api_call(
            api,
            "POST",
            "/api/v1/auth/register",
            {"email": email, "password": password, "display_name": "E2E User"},
        )
    except urllib.error.HTTPError:
        pass
    login = api_call(api, "POST", "/api/v1/auth/login", {"email": email, "password": password})
    return login["data"]["token"]


def normalized_embedding(seed: float = 0.01) -> list[float]:
    emb = [seed] * PATCH_DIM
    n = sum(x * x for x in emb) ** 0.5 or 1.0
    return [x / n for x in emb]


def multi_pose_embeddings(seed: float = 0.01) -> list[dict]:
    """5 ракурсов для kiosk-register / unit-тестов."""
    poses = ("center", "left", "right", "up", "down")
    yaw = {"center": 0.0, "left": 30.0, "right": -30.0, "up": 0.0, "down": 0.0}
    pitch = {"center": 0.0, "left": 0.0, "right": 0.0, "up": -25.0, "down": 25.0}
    out = []
    for i, pose in enumerate(poses):
        out.append(
            {
                "pose": pose,
                "embedding": normalized_embedding(seed + i * 0.002),
                "yaw": yaw[pose],
                "pitch": pitch[pose],
            }
        )
    return out
