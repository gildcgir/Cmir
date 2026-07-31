#!/usr/bin/env python3
"""E2E: users, auth, consent → wallet linkage."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import urllib.error
import urllib.request

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8090"
PATCH_DIM = 32 * 32
sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_helpers import ensure_admin  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_helpers import ensure_admin  # noqa: E402


def req(method: str, path: str, body: dict | None = None, token: str = "") -> dict:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read())


def main() -> int:
    checks = []
    email = "lab@cmir.test"
    password = "testpass123"

    # register (ignore if exists)
    try:
        req("POST", "/api/v1/auth/register", {"email": email, "password": password, "display_name": "Lab User"})
        checks.append(("register", True))
    except urllib.error.HTTPError as e:
        checks.append(("register", e.code in (400, 200)))

    login = req("POST", "/api/v1/auth/login", {"email": email, "password": password})
    token = login["data"]["token"]
    checks.append(("login", bool(token)))

    me = req("GET", "/api/v1/auth/me", token=token)
    user_id = me["data"]["id"]
    checks.append(("me", me["data"]["email"] == email))

    admin_token = ensure_admin(API)

    poi = req(
        "POST",
        "/api/v1/pois",
        {
            "name": "Auth Lab POI",
            "poi_type": "live_cam",
            "latitude": 41.71,
            "longitude": 44.82,
            "city": "Tbilisi",
            "country": "GE",
        },
        token=admin_token,
    )
    poi_id = poi["data"]["id"]
    checks.append(("create_poi", bool(poi_id)))

    emb = [0.01] * PATCH_DIM
    consent = req(
        "POST",
        f"/api/v1/pois/{poi_id}/consent",
        {"face_embedding": emb},
        token=token,
    )
    wallet = consent["data"]["wallet_address"]
    checks.append(("consent_wallet", wallet.startswith("0xcmir")))

    me2 = req("GET", "/api/v1/auth/me", token=token)
    checks.append(("wallet_linked", me2["data"]["wallet"]["address"] == wallet))
    checks.append(("consent_linked", any(c["poi_id"] == poi_id for c in me2["data"]["consents"])))

    w = req("GET", f"/api/v1/wallets/{wallet}")
    checks.append(("wallet_user", w["data"]["user_id"] == user_id))

    # consent without auth → 401
    try:
        req("POST", f"/api/v1/pois/{poi_id}/consent", {"face_embedding": emb})
        checks.append(("consent_requires_auth", False))
    except urllib.error.HTTPError as e:
        checks.append(("consent_requires_auth", e.code == 401))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} PASS")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
