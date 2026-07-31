"""Unit-тесты сценариев USE_CASES.md (UC-01 … UC-10)."""
from __future__ import annotations

from store import PATCH_DIM


DOC_OK = {
    "terms_of_service": True,
    "privacy_policy": True,
    "personal_data_consent": True,
    "biometric_data_consent": True,
    "wallet_agreement": True,
}


def _emb(seed: float = 0.1):
    return [seed] * PATCH_DIM


def _demo_poi(store):
    store.ensure_demo_fixtures()
    return next(p for p in store.list_pois() if "Пингвинья" in p["name"])


def _preview_cam(poi: dict):
    cams = poi.get("cameras") or []
    return next((c for c in cams if c.get("is_preview")), None) or next(
        (c for c in cams if c.get("role") == "general"), None
    )


# --- UC-01 ---
def test_uc01_guest_sees_pois_on_map(store):
    pois = store.list_pois()
    assert len(pois) >= 1
    assert all("latitude" in p and "longitude" in p for p in pois)
    assert all(p.get("name") for p in pois)


def test_uc01_preview_target_seconds_is_10():
    from preview_buffer import PREVIEW_SECONDS, PREVIEW_TARGET_SEC

    assert PREVIEW_SECONDS == 10
    assert PREVIEW_TARGET_SEC == 10


# --- UC-02 ---
def test_uc02_kiosk_register_creates_wallet_consent_and_temp_password(store):
    poi = _demo_poi(store)
    data = store.kiosk_register(
        poi["id"], "Гость Киоск", "+995555111222", "Пицца", _emb(0.11), DOC_OK
    )
    assert data["wallet"]["address"]
    assert data["auth"]["token"]
    assert data["temporary_password"]
    assert data["consent"]["id"]
    faces = store.global_consented_faces()
    assert any(f["display_name"] == "Гость Киоск" for f in faces)


# --- UC-03 ---
def test_uc03_user_with_consent_listed_and_kiosk_logic_flags(store):
    poi = _demo_poi(store)
    data = store.kiosk_register(
        poi["id"], "Повтор", "+995555333444", "Салат", _emb(0.12), DOC_OK
    )
    user = store.user_public(store.get_user(data["user_id"]))
    assert len(user["consents"]) >= 1
    # повторная регистрация того же телефона обновляет профиль, согласие остаётся
    data2 = store.kiosk_register(
        poi["id"], "Повтор", "+995555333444", "Салат", _emb(0.12), DOC_OK
    )
    assert data2["user_id"] == data["user_id"]
    assert "temporary_password" not in data2


# --- UC-04 ---
def test_uc04_login_email_or_phone_after_kiosk(store):
    poi = _demo_poi(store)
    data = store.kiosk_register(
        poi["id"], "Логин Юзер", "+995555666777", "Кофе", _emb(0.13), DOC_OK
    )
    by_phone = store.login_user("+995555666777", data["temporary_password"])
    assert by_phone["token"]
    by_email = store.login_user(data["login_email"], data["temporary_password"])
    assert by_email["user"]["id"] == data["user_id"]


# --- UC-05 ---
def test_uc05_consented_face_matches_globally_not_poi_bound(store):
    poi = _demo_poi(store)
    data = store.kiosk_register(
        poi["id"], "Глобал", "+995555888999", "Десерт", _emb(0.14), DOC_OK
    )
    faces = store.global_consented_faces()
    hit = next(f for f in faces if f["user_id"] == data["user_id"])
    assert hit["display_name"] == "Глобал"
    assert len(hit["embedding"]) == PATCH_DIM


# --- UC-06 ---
def test_uc06_revoke_removes_face_and_allows_reregister(store):
    poi = _demo_poi(store)
    data = store.kiosk_register(
        poi["id"], "Отзыв", "+995555000111", "Бургер", _emb(0.15), DOC_OK
    )
    cid = data["consent"]["id"]
    store.revoke_consent(poi["id"], cid, user_id=data["user_id"])
    assert not any(f["user_id"] == data["user_id"] for f in store.global_consented_faces())
    pub = store.user_public(store.get_user(data["user_id"]))
    assert pub["consents"] == []
    again = store.kiosk_register(
        poi["id"], "Отзыв", "+995555000111", "Бургер", _emb(0.15), DOC_OK
    )
    assert again["consent"]["id"] != cid


# --- UC-07 ---
def test_uc07_performance_camera_exists_on_demo(store):
    poi = _demo_poi(store)
    roles = {c["role"] for c in poi["cameras"]}
    assert "performance" in roles


# --- UC-08 ---
def test_uc08_admin_login_and_stats(store):
    logged = store.login_user("admin", "admin")
    assert logged["user"]["role"] == "admin"
    stats = store.admin_stats()
    assert "users_total" in stats
    assert "cameras_by_role" in stats


# --- UC-09 ---
def test_uc09_logout_invalidates_session(store):
    user = store.register_user("logout@test.local", "password123", "Out")
    logged = store.login_user("logout@test.local", "password123")
    token = logged["token"]
    assert store.user_from_token(token)
    store.logout_user(token)
    assert store.user_from_token(token) is None


# --- Phase 2: face presence + proportional UT (1 UT = full stream) ---
def test_uc10_stream_reward_is_share_of_one_ut(store):
    poi = _demo_poi(store)
    cam = _preview_cam(poi)
    assert cam, "preview camera required"
    a = store.kiosk_register(poi["id"], "Алиса", "+995511111111", "Кофе", _emb(0.21), DOC_OK)
    b = store.kiosk_register(poi["id"], "Боб", "+995522222222", "Чай", _emb(0.22), DOC_OK)
    store.record_face_presence(a["user_id"], cam["id"], 30.0, period_key="2026-07-17T01")
    store.record_face_presence(b["user_id"], cam["id"], 10.0, period_key="2026-07-17T01")
    # события presence должны попасть в окно стрима
    store.conn.execute(
        "UPDATE face_presence_events SET recorded_at = ? WHERE camera_id = ?",
        ("2026-07-17T01:00:30Z", cam["id"]),
    )
    store.conn.commit()
    rows = store.list_face_presence(camera_id=cam["id"], period_key="2026-07-17T01")
    assert len(rows) == 2
    before_a = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (a["user_id"],)
    ).fetchone()["balance_ut"]
    before_b = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (b["user_id"],)
    ).fetchone()["balance_ut"]
    # стрим 100 с → Алиса 30% = 0.3 UT, Боб 10% = 0.1 UT
    rewards = store.reward_stream_participants(
        "stream-uc10",
        cam["id"],
        "2026-07-17T01:00:00Z",
        "2026-07-17T01:01:40Z",
    )
    assert rewards["stream_duration_seconds"] == 100.0
    by_user = {r["user_id"]: r for r in rewards["participants"]}
    assert abs(by_user[a["user_id"]]["ut_earned"] - 0.3) < 1e-6
    assert abs(by_user[b["user_id"]]["ut_earned"] - 0.1) < 1e-6
    assert by_user[a["user_id"]]["presence_seconds"] == 30.0
    assert by_user[b["user_id"]]["presence_seconds"] == 10.0
    after_a = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (a["user_id"],)
    ).fetchone()["balance_ut"]
    after_b = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (b["user_id"],)
    ).fetchone()["balance_ut"]
    assert abs(after_a - (before_a + 0.3)) < 1e-4
    assert abs(after_b - (before_b + 0.1)) < 1e-4

    again = store.reward_stream_participants(
        "stream-uc10",
        cam["id"],
        "2026-07-17T01:00:00Z",
        "2026-07-17T01:01:40Z",
    )
    assert again["already_rewarded"] is True
    balance_a = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (a["user_id"],)
    ).fetchone()["balance_ut"]
    assert abs(balance_a - after_a) < 1e-9


def test_uc10_no_presence_no_ut(store):
    poi = _demo_poi(store)
    cam = _preview_cam(poi)
    rewards = store.reward_stream_participants(
        "empty-stream",
        cam["id"],
        "2000-01-01T00:00:00Z",
        "2000-01-01T00:00:01Z",
    )
    assert rewards["participants"] == []


def test_uc10_performance_stop_rewards_proportionally(store, monkeypatch):
    import store as store_module

    poi = _demo_poi(store)
    cam = next(c for c in poi["cameras"] if c["role"] == "performance")
    owner = store.kiosk_register(
        poi["id"], "Ведущий", "+995544411100", "Кофе", _emb(0.31), DOC_OK
    )
    guest = store.kiosk_register(
        poi["id"], "Участник", "+995544411101", "Чай", _emb(0.32), DOC_OK
    )
    monkeypatch.setattr(store_module.RECORDER, "start", lambda *_: None)
    monkeypatch.setattr(store_module.RECORDER, "stop", lambda *_: None)

    stream = store.performance_stream_start(owner["user_id"], cam["id"], "Тест")
    store.conn.execute(
        "UPDATE performance_streams SET started_at = ? WHERE id = ?",
        ("2026-07-17T02:00:00Z", stream["id"]),
    )
    store.conn.commit()
    monkeypatch.setattr(store_module, "now_iso", lambda: "2026-07-17T02:00:25Z")
    store.record_face_presence(guest["user_id"], cam["id"], 25.0)
    before = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (guest["user_id"],)
    ).fetchone()["balance_ut"]

    monkeypatch.setattr(store_module, "now_iso", lambda: "2026-07-17T02:00:50Z")
    stopped = store.performance_stream_stop(owner["user_id"], stream["id"])
    participants = stopped["rewards"]["participants"]
    assert len(participants) == 1
    assert participants[0]["user_id"] == guest["user_id"]
    # 25с из 50с стрима → 0.5 UT
    assert abs(participants[0]["ut_earned"] - 0.5) < 1e-6
    after = store.conn.execute(
        "SELECT balance_ut FROM wallets WHERE user_id = ?", (guest["user_id"],)
    ).fetchone()["balance_ut"]
    assert abs(after - (before + 0.5)) < 1e-4
