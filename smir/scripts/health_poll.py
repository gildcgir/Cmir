#!/usr/bin/env python3
"""Poll all active cameras and POST health snapshots to Smir API."""
from __future__ import annotations

import json
import time
import urllib.request

API = "http://localhost:8090"
INTERVAL = int(__import__("os").environ.get("SMIR_HEALTH_INTERVAL", "60"))


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=15) as r:
        return json.loads(r.read())


def post(path: str, body: dict) -> None:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=15)


def main() -> None:
    print(f"Health poll -> {API} every {INTERVAL}s")
    while True:
        try:
            pois = get("/api/v1/pois")["data"]
            n = 0
            for p in pois:
                for c in p.get("cameras", []):
                    if not c.get("is_active", True):
                        continue
                    h = get(f"/api/v1/cameras/{c['id']}/health")["data"]
                    post(
                        "/api/v1/admin/health-snapshot",
                        {"camera_id": c["id"], "status": h["status"], "detail": h.get("detail", "")},
                    )
                    n += 1
            print(f"  snapshot {n} cameras ok")
        except Exception as e:
            print(f"  warn: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
