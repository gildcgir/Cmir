#!/usr/bin/env python3
"""Phase 1 admin API checks."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_helpers import api_call, ensure_admin  # noqa: E402

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8090"


def main() -> int:
    failed = 0
    checks = []

    h = api_call(API, "GET", "/health")
    checks.append(("health", h.get("status") == "healthy"))

    admin_token = ensure_admin(API)

    poi = api_call(
        API,
        "POST",
        "/api/v1/pois",
        {
            "name": "E2E GoPro Pilot",
            "poi_type": "social_event",
            "latitude": 41.0,
            "longitude": 44.0,
        },
        token=admin_token,
    )
    poi_id = poi["data"]["id"]
    checks.append(("create_poi", bool(poi_id)))

    for name, role, mode, url in [
        ("G1", "general", "fisheye", "rtsp://127.0.0.1:8554/gopro_main"),
        ("G2", "general", "zoom2x", "rtsp://127.0.0.1:8554/demo_general_b"),
        ("Kiosk", "consent", "standard", "rtsp://127.0.0.1:8554/gopro_consent"),
    ]:
        cam = api_call(
            API,
            "POST",
            f"/api/v1/pois/{poi_id}/cameras",
            {"name": name, "stream_url": url, "role": role, "view_mode": mode},
            token=admin_token,
        )
        checks.append((f"camera_{name}", cam["data"]["view_mode"] == mode))

    cam_id = cam["data"]["id"]
    health = api_call(API, "GET", f"/api/v1/cameras/{cam_id}/health")
    checks.append(("camera_health", "status" in health["data"]))

    patched = api_call(
        API,
        "PATCH",
        f"/api/v1/cameras/{cam_id}",
        {"view_mode": "standard", "name": "Kiosk updated"},
        token=admin_token,
    )
    checks.append(("patch_camera", patched["data"]["view_mode"] == "standard"))

    for name, ok in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"  [{tag}] {name}")
        if not ok:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
