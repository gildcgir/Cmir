"""Функциональные HTTP-тесты API."""
from __future__ import annotations


def test_health_pois(api_get):
    data = api_get("/api/v1/pois")
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_consented_faces_requires_worker_token(api_server):
    import json
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen(f"{api_server}/api/v1/consented-faces", timeout=5)
        assert False, "expected 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401

    req = urllib.request.Request(
        f"{api_server}/api/v1/consented-faces",
        headers={"X-Cmir-Worker": "test-worker-token"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    assert data["success"] is True
    assert "faces" in data["data"]


def test_admin_stats_requires_auth(api_server):
    import urllib.error
    import urllib.request

    url = f"{api_server}/api/v1/admin/stats"
    try:
        urllib.request.urlopen(url, timeout=5)
        assert False, "expected 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401


def test_admin_login_and_stats(api_server):
    import json
    import urllib.request

    login_body = json.dumps({"email": "admin", "password": "admin"}).encode()
    req = urllib.request.Request(
        f"{api_server}/api/v1/auth/login",
        data=login_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        token = json.loads(resp.read().decode())["data"]["token"]

    req2 = urllib.request.Request(
        f"{api_server}/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req2, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    assert data["success"] is True
    assert "users_total" in data["data"]


def test_face_presence_http(api_server):
    import json
    import sys
    import urllib.error
    import urllib.request
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from e2e_helpers import multi_pose_embeddings

    with urllib.request.urlopen(f"{api_server}/api/v1/pois", timeout=5) as resp:
        pois = json.loads(resp.read().decode())["data"]
    poi = next(p for p in pois if p.get("cameras"))
    cam = next((c for c in poi["cameras"] if c.get("is_preview")), poi["cameras"][0])

    docs = {
        "terms_of_service": True,
        "privacy_policy": True,
        "personal_data_consent": True,
        "biometric_data_consent": True,
        "wallet_agreement": True,
    }
    poses = multi_pose_embeddings(0.07)
    body = json.dumps(
        {
            "full_name": "HTTP Air",
            "phone": "+995533344455",
            "favorite_menu_item": "Кофе",
            "face_embedding": poses[0]["embedding"],
            "face_embeddings": poses,
            "acceptances": docs,
        }
    ).encode()
    req = urllib.request.Request(
        f"{api_server}/api/v1/pois/{poi['id']}/kiosk-register",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        reg = json.loads(resp.read().decode())["data"]
    uid = reg["user_id"]

    # unauthenticated presence must fail
    pres = json.dumps(
        {
            "presence": [
                {"user_id": uid, "camera_id": cam["id"], "seconds": 20, "period_key": "http-p1"}
            ]
        }
    ).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{api_server}/api/v1/face-presence",
                data=pres,
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=5,
        )
        assert False, "expected 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401

    reqp = urllib.request.Request(
        f"{api_server}/api/v1/face-presence",
        data=pres,
        headers={
            "Content-Type": "application/json",
            "X-Cmir-Worker": "test-worker-token",
        },
        method="POST",
    )
    with urllib.request.urlopen(reqp, timeout=5) as resp:
        assert json.loads(resp.read().decode())["success"] is True

    req_get = urllib.request.Request(
        f"{api_server}/api/v1/face-presence?camera_id={cam['id']}",
        headers={"Authorization": f"Bearer {reg['auth']['token']}"},
    )
    with urllib.request.urlopen(req_get, timeout=5) as resp:
        rows = json.loads(resp.read().decode())["data"]
    assert len(rows) == 1
    assert rows[0]["user_id"] == uid
    assert rows[0]["seconds"] == 20.0


def test_face_match_and_force_release_auth(api_server):
    import json
    import sys
    import urllib.error
    import urllib.request
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from e2e_helpers import multi_pose_embeddings

    with urllib.request.urlopen(f"{api_server}/api/v1/pois", timeout=5) as resp:
        pois = json.loads(resp.read().decode())["data"]
    poi = next(p for p in pois if p.get("cameras"))

    docs = {
        "terms_of_service": True,
        "privacy_policy": True,
        "personal_data_consent": True,
        "biometric_data_consent": True,
        "wallet_agreement": True,
    }
    poses = multi_pose_embeddings(0.19)
    # Make center template unique (constant seeds collapse after L2-norm)
    uniq = [((i % 31) + 1) * 0.017 for i in range(len(poses[0]["embedding"]))]
    n = sum(x * x for x in uniq) ** 0.5
    uniq = [x / n for x in uniq]
    poses[0]["embedding"] = uniq
    body = json.dumps(
        {
            "full_name": "Match User",
            "phone": "+995533344456",
            "favorite_menu_item": "Чай",
            "face_embedding": uniq,
            "face_embeddings": poses,
            "acceptances": docs,
        }
    ).encode()
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{api_server}/api/v1/pois/{poi['id']}/kiosk-register",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        ),
        timeout=5,
    ) as resp:
        reg = json.loads(resp.read().decode())["data"]

    match_body = json.dumps({"embedding": uniq}).encode()
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{api_server}/api/v1/face-match",
            data=match_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        ),
        timeout=5,
    ) as resp:
        hit = json.loads(resp.read().decode())["data"]
    assert hit["matched"] is True
    assert hit["user_id"] == reg["user_id"]
    assert hit["score"] >= 0.99

    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{api_server}/api/v1/pois/{poi['id']}/stream/release",
                data=json.dumps({"client_id": "x", "force": True}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=5,
        )
        assert False, "expected 401 for force without admin"
    except urllib.error.HTTPError as e:
        assert e.code == 401