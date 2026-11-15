#!/usr/bin/env python3
"""Poll all active cameras and POST health snapshots to Cmir API."""
from __future__ import annotations

import json
import os
import time
import urllib.request

API = os.environ.get("CMIR_API", "http://localhost:8090")
INTERVAL = int(os.environ.get("CMIR_HEALTH_INTERVAL", "60"))
ADMIN_PASSWORD = os.environ.get("CMIR_ADMIN_PASSWORD", "admin")


def _token() -> str:
    req = urllib.request.Request(
        f"{API}/api/v1/auth/login",
        data=json.dumps({"email": "admin", "password": ADMIN_PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())["data"]["token"]


def get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def post(path: str, body: dict, token: str) -> None:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=15)


def main() -> None:
    print(f"Health poll -> {API} every {INTERVAL}s")
    while True:
        try:
            token = _token()
            pois = get("/api/v1/pois", token)["data"]
            n = 0
            for p in pois:
                for c in p.get("cameras", []):
                    if not c.get("is_active", True):
                        continue
                    h = get(f"/api/v1/cameras/{c['id']}/health", token)["data"]
                    post(
                        "/api/v1/admin/health-snapshot",
                        {"camera_id": c["id"], "status": h["status"], "detail": h.get("detail", "")},
                        token,
                    )
                    n += 1
            print(f"  snapshot {n} cameras ok")
        except Exception as e:
            print(f"  warn: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
