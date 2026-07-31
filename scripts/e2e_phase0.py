#!/usr/bin/env python3
"""Cmir Phase 0 E2E checks (run while API is up)."""
from __future__ import annotations

import sys
import time
from pathlib import Path
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_helpers import api_call, ensure_admin, ensure_auth, normalized_embedding  # noqa: E402

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8090"


def main() -> int:
    results = []
    t0 = time.time()

    try:
        h = api_call(API, "GET", "/health")
        results.append(("health", h.get("status") == "healthy"))
    except urllib.error.URLError as e:
        print(f"API not reachable at {API}: {e}")
        return 1

    token = ensure_auth(API)

    admin_token = ensure_admin(API)

    poi = api_call(
        API,
        "POST",
        "/api/v1/pois",
        {
            "name": "Phase0 E2E POI",
            "poi_type": "social_event",
            "latitude": 41.7151,
            "longitude": 44.8271,
            "city": "Tbilisi",
            "country": "GE",
            "promo_description": "E2E test venue",
        },
        token=admin_token,
    )["data"]
    poi_id = poi["id"]
    results.append(("create_poi", bool(poi_id)))

    for name, role, mode in [
        ("General A", "general", "fisheye"),
        ("General B", "general", "zoom2x"),
        ("Consent", "consent", "standard"),
    ]:
        cam = api_call(
            API,
            "POST",
            f"/api/v1/pois/{poi_id}/cameras",
            {
                "name": name,
                "stream_url": f"rtsp://127.0.0.1:8554/demo_{name.lower().replace(' ', '_')}",
                "role": role,
                "view_mode": mode,
            },
            token=admin_token,
        )["data"]
        results.append((f"camera_{name}", cam["view_mode"] == mode))

    emb_before = api_call(API, "GET", f"/api/v1/pois/{poi_id}/embeddings")["data"]["count"]

    consent = api_call(
        API,
        "POST",
        f"/api/v1/pois/{poi_id}/consent",
        {"face_embedding": normalized_embedding()},
        token=token,
    )
    results.append(("consent_wallet", consent["data"]["wallet_address"].startswith("0x")))

    emb_after = api_call(API, "GET", f"/api/v1/pois/{poi_id}/embeddings")["data"]["count"]
    results.append(("embedding_stored", emb_after == emb_before + 1))

    scene = api_call(API, "GET", f"/api/v1/pois/{poi_id}/scene")["data"]
    results.append(("scene_mood", scene["mood"] in ("fun", "promo")))

    tops = api_call(API, "GET", "/api/v1/tops/consent")["data"]
    results.append(("tops_consent", any(x["id"] == poi_id for x in tops)))

    latency_ms = int((time.time() - t0) * 1000)
    print(f"E2E completed in {latency_ms} ms\n")
    failed = 0
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            failed += 1

    out_path = str(Path(__file__).resolve().parents[1] / "docs" / "PHASE0_RESULTS.md")
    try:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"\n## E2E run {time.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"- API: `{API}`\n")
            f.write(f"- Duration: {latency_ms} ms\n")
            for name, ok in results:
                f.write(f"- {name}: {'ok' if ok else 'FAIL'}\n")
    except OSError:
        pass

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
