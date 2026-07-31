#!/usr/bin/env python3
"""Phase 1 full API checks (weeks 3-12 features)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_helpers import api_call, ensure_admin, ensure_auth, normalized_embedding  # noqa: E402

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8090"


def main() -> int:
    failed = 0
    checks = []

    h = api_call(API, "GET", "/health")
    checks.append(("health", h.get("status") == "healthy"))

    token = ensure_auth(API, email="e2e-full@smir.test")
    admin_token = ensure_admin(API)

    poi = api_call(
        API,
        "POST",
        "/api/v1/pois",
        {
            "name": "Geo Test POI",
            "poi_type": "live_cam",
            "latitude": 41.7,
            "longitude": 44.8,
            "city": "Tbilisi",
            "country": "GE",
        },
        token=admin_token,
    )["data"]
    pid = poi["id"]

    tops = api_call(API, "GET", "/api/v1/tops/consent?city=Tbilisi&country=GE")
    checks.append(("geo_filter", any(x["id"] == pid for x in tops["data"])))

    cam = api_call(
        API,
        "POST",
        f"/api/v1/pois/{pid}/cameras",
        {
            "name": "HLS cam",
            "stream_url": "rtsp://127.0.0.1:8554/gopro_main",
            "role": "general",
            "view_mode": "standard",
        },
        token=admin_token,
    )["data"]
    cid = cam["id"]

    pb = api_call(API, "GET", f"/api/v1/cameras/{cid}/playback")["data"]
    checks.append(("playback_hls", pb.get("hls_url", "").endswith(".m3u8")))

    api_call(
        API,
        "POST",
        "/api/v1/admin/health-snapshot",
        {"camera_id": cid, "status": "reachable", "detail": "test"},
        token=admin_token,
    )
    hist = api_call(API, "GET", f"/api/v1/admin/{cid}/health-history")["data"]
    checks.append(("health_history", len(hist) >= 1))

    consent = api_call(
        API,
        "POST",
        f"/api/v1/pois/{pid}/consent",
        {"face_embedding": normalized_embedding()},
        token=token,
    )["data"]
    wallet = consent["wallet_address"]
    checks.append(("wallet", wallet.startswith("0x")))

    w = api_call(API, "GET", f"/api/v1/wallets/{wallet}")["data"]
    checks.append(("wallet_balance", "balance_ut" in w))

    api_call(API, "POST", f"/api/v1/pois/{pid}/airtime", {"wallet": wallet, "seconds": 120})
    air = api_call(API, "GET", f"/api/v1/pois/{pid}/airtime")["data"]
    checks.append(("airtime", len(air) >= 1))

    don = api_call(
        API,
        "POST",
        "/api/v1/donations",
        {"poi_id": pid, "amount": 25, "message": "test", "donor": "e2e"},
    )["data"]
    checks.append(("donation", don["status"] == "pending_moderation"))

    revoke = api_call(
        API,
        "DELETE",
        f"/api/v1/pois/{pid}/consent/latest",
        token=token,
    )["data"]
    checks.append(("revoke_consent", "embeddings_remaining" in revoke))

    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
