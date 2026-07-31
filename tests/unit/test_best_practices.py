"""Дополнительные тесты по best practices (auth isolation, privacy, invariants)."""
from __future__ import annotations

import pytest

from store import PATCH_DIM


DOC_OK = {
    "terms_of_service": True,
    "privacy_policy": True,
    "personal_data_consent": True,
    "biometric_data_consent": True,
    "wallet_agreement": True,
}


def test_bp_invalid_login_rejected(store):
    store.register_user("bp@test.local", "password123", "BP")
    with pytest.raises(ValueError):
        store.login_user("bp@test.local", "wrong-password")


def test_bp_short_password_rejected(store):
    with pytest.raises(ValueError):
        store.register_user("short@test.local", "123", "Short")


def test_bp_consent_requires_full_acceptances(store):
    store.ensure_demo_fixtures()
    poi = store.list_pois()[0]
    with pytest.raises(ValueError):
        store.kiosk_register(
            poi["id"],
            "No Docs",
            "+995500000001",
            "Кофе",
            [0.01] * PATCH_DIM,
            {"terms_of_service": True},
        )


def test_bp_face_presence_requires_consent(store):
    user = store.register_user("noconsent@test.local", "password123", "NoC")
    store.ensure_demo_fixtures()
    cam = next(c for p in store.list_pois() for c in p["cameras"] if c.get("is_preview"))
    with pytest.raises(ValueError, match="consent"):
        store.record_face_presence(user["id"], cam["id"], 5.0)


def test_bp_face_presence_accumulates(store):
    store.ensure_demo_fixtures()
    poi = next(p for p in store.list_pois() if p["cameras"])
    cam = next(c for c in poi["cameras"] if c.get("is_preview")) or poi["cameras"][0]
    data = store.kiosk_register(
        poi["id"], "Acc", "+995500000002", "Кофе", [0.03] * PATCH_DIM, DOC_OK
    )
    store.record_face_presence(data["user_id"], cam["id"], 5.0, period_key="bp-acc")
    store.record_face_presence(data["user_id"], cam["id"], 7.0, period_key="bp-acc")
    rows = store.list_face_presence(user_id=data["user_id"], period_key="bp-acc")
    assert len(rows) == 1
    assert rows[0]["seconds"] == 12.0


def test_bp_revoke_deletes_embeddings_only_for_that_consent(store):
    store.ensure_demo_fixtures()
    poi = store.list_pois()[0]
    a = store.kiosk_register(poi["id"], "A", "+995500000003", "Кофе", [0.04] * PATCH_DIM, DOC_OK)
    b = store.kiosk_register(poi["id"], "B", "+995500000004", "Чай", [0.05] * PATCH_DIM, DOC_OK)
    store.revoke_consent(poi["id"], a["consent"]["id"], user_id=a["user_id"])
    faces = store.global_consented_faces()
    ids = {f["user_id"] for f in faces}
    assert a["user_id"] not in ids
    assert b["user_id"] in ids
    row = store.conn.execute(
        "SELECT face_embedding FROM consents WHERE id = ?", (a["consent"]["id"],)
    ).fetchone()
    assert row["face_embedding"] is None


def test_bp_match_consented_face_prefers_best_score():
    from cmir_face.embeddings import match_consented_face
    import numpy as np

    sig = np.ones(PATCH_DIM, dtype=np.float32)
    sig /= np.linalg.norm(sig)
    weak = (sig * 0.8).astype(np.float32)
    weak /= np.linalg.norm(weak)
    faces = [
        {"user_id": "1", "display_name": "Weak", "embedding": weak.tolist()},
        {"user_id": "2", "display_name": "Strong", "embedding": sig.tolist()},
    ]
    hit = match_consented_face(sig, faces, threshold=0.5)
    assert hit["user_id"] == "2"
