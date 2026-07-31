"""Unit-тесты Store и бизнес-логики API."""
from __future__ import annotations

import pytest

from store import PATCH_DIM


def test_register_and_login(store):
    user = store.register_user("u1@test.local", "password123", "User One")
    assert user["email"] == "u1@test.local"
    logged = store.login_user("u1@test.local", "password123")
    assert logged["token"]
    assert logged["user"]["display_name"] == "User One"


def test_global_consented_faces_empty(store):
    assert store.global_consented_faces() == []


def test_global_consented_faces_with_consent(store):
    user = store.register_user("face@test.local", "password123", "Иван Тест")
    poi = store.create_poi(
        {
            "name": "Test POI",
            "latitude": 41.7,
            "longitude": 44.8,
            "address": "Tbilisi",
        }
    )
    emb = [0.1] * PATCH_DIM
    store.grant_consent(poi.id, user["id"], emb)
    faces = store.global_consented_faces()
    assert len(faces) == 1
    assert faces[0]["display_name"] == "Иван Тест"
    assert len(faces[0]["embedding"]) == PATCH_DIM


def test_sync_poi_cameras_roles(store):
    poi = store.create_poi({"name": "Cam POI", "latitude": 41.0, "longitude": 44.0})
    cams = store.sync_poi_cameras(
        poi.id,
        [
            {
                "slot_index": 0,
                "name": "General",
                "role": "general",
                "device_id": "dev1",
                "is_active": True,
                "is_preview": True,
            },
            {
                "slot_index": 1,
                "name": "Performance",
                "role": "performance",
                "device_id": "dev2",
                "is_active": True,
                "is_preview": False,
            },
        ],
    )
    roles = {c["role"] for c in cams}
    assert roles == {"general", "performance"}


def test_admin_stats(store):
    store.register_user("stats@test.local", "password123", "Stats")
    stats = store.admin_stats()
    assert stats["users_total"] >= 1
    assert "cameras_by_role" in stats


def test_list_pois_restores_demo_after_clear(store):
    store.clear_all_pois()
    pois = store.list_pois()
    names = {p["name"] for p in pois}
    assert "Demo: Social Event — Пингвинья вечеринка" in names
    assert "Тестовое место" in names
    assert len(pois) >= 2


def test_ensure_demo_fixtures(store):
    created = store.ensure_demo_fixtures()
    names = {p["name"] for p in store.list_pois()}
    assert "Demo: Social Event — Пингвинья вечеринка" in names
    demo = next(p for p in store.list_pois() if "Пингвинья" in p["name"])
    roles = {c["role"] for c in demo["cameras"]}
    assert "general" in roles
    assert "consent" in roles
    assert "performance" in roles
    # idempotent
    assert store.ensure_demo_fixtures() == [] or created


def test_platform_link_username(store):
    user = store.register_user("plat@test.local", "password123", "Plat")
    link = store.link_platform_username(user["id"], "youtube", "mychannel")
    assert link["username"] == "mychannel"
    links = store.list_platform_links(user["id"])
    assert any(l["platform"] == "youtube" for l in links)


def test_kiosk_register_temp_password_and_phone_login(store):
    store.ensure_demo_fixtures()
    poi = next(p for p in store.list_pois() if "Пингвинья" in p["name"])
    emb = [0.05] * PATCH_DIM
    data = store.kiosk_register(
        poi["id"],
        "Киоск Юзер",
        "+995555123456",
        "Бургер",
        emb,
        {
            "terms_of_service": True,
            "privacy_policy": True,
            "personal_data_consent": True,
            "biometric_data_consent": True,
            "wallet_agreement": True,
        },
    )
    assert data["auth"]["token"]
    assert data["temporary_password"]
    assert data["login_email"].endswith("@kiosk.cmir.ge")
    logged = store.login_user("+995555123456", data["temporary_password"])
    assert logged["user"]["display_name"] == "Киоск Юзер"
    faces = store.global_consented_faces()
    assert any(f["display_name"] == "Киоск Юзер" for f in faces)


def test_revoke_consent_removes_from_global_faces(store):
    user = store.register_user("revoke@test.local", "password123", "Revoke Me")
    poi = store.create_poi({"name": "Revoke POI", "latitude": 41.1, "longitude": 44.1})
    emb = [0.2] * PATCH_DIM
    consent = store.grant_consent(poi.id, user["id"], emb)
    assert any(f["display_name"] == "Revoke Me" for f in store.global_consented_faces())
    store.revoke_consent(poi.id, consent["id"], user_id=user["id"])
    assert not any(f["display_name"] == "Revoke Me" for f in store.global_consented_faces())
    pub = store.user_public(store.get_user(user["id"]))
    assert pub["consents"] == []
