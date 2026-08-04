"""SQLite persistence for Cmir core (users, sessions, consents, wallets, POI)."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "cmir_test.db"


def app_env() -> str:
    return os.environ.get("CMIR_ENV", "test").lower()


def db_path() -> Path:
    explicit = os.environ.get("CMIR_DB_PATH", "")
    if explicit:
        return Path(explicit)
    base = Path(__file__).resolve().parent / "data"
    if app_env() == "prod":
        return base / "cmir_prod.db"
    return base / "cmir_test.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance_st REAL NOT NULL DEFAULT 0,
    balance_ut REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pois (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    poi_type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    promo_description TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    consent_rate REAL NOT NULL DEFAULT 0,
    participants_24h INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cameras (
    id TEXT PRIMARY KEY,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    stream_url TEXT NOT NULL,
    role TEXT NOT NULL,
    view_mode TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    wallet_address TEXT NOT NULL REFERENCES wallets(address),
    face_embedding TEXT,
    consent_text_version TEXT NOT NULL,
    consented_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS poi_embeddings (
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    embedding_json TEXT NOT NULL,
    PRIMARY KEY (poi_id, consent_id)
);

CREATE TABLE IF NOT EXISTS face_templates (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    pose TEXT NOT NULL DEFAULT 'center',
    yaw REAL,
    pitch REAL,
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_face_templates_user ON face_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_face_templates_consent ON face_templates(consent_id);

CREATE TABLE IF NOT EXISTS donations (
    id TEXT PRIMARY KEY,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'GEL',
    message TEXT NOT NULL DEFAULT '',
    donor TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending_moderation',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airtime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    wallet_address TEXT NOT NULL,
    seconds REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_consents_user ON consents(user_id);
CREATE INDEX IF NOT EXISTS idx_consents_poi ON consents(poi_id);
CREATE INDEX IF NOT EXISTS idx_cameras_poi ON cameras(poi_id);

CREATE TABLE IF NOT EXISTS view_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    seconds REAL NOT NULL,
    ad_revenue REAL NOT NULL,
    period_key TEXT NOT NULL,
    ut_earned REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_view_events_period ON view_events(period_key);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    favorite_menu_item TEXT NOT NULL DEFAULT '',
    registered_via TEXT NOT NULL DEFAULT 'web',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id TEXT PRIMARY KEY,
    doc_type TEXT NOT NULL,
    version TEXT NOT NULL,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    file_path TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(doc_type, version)
);

CREATE TABLE IF NOT EXISTS consent_document_acceptances (
    id TEXT PRIMARY KEY,
    consent_id TEXT NOT NULL REFERENCES consents(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    doc_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    user_id TEXT,
    poi_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blockchain_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tx_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_user ON blockchain_records(user_id);

CREATE TABLE IF NOT EXISTS performance_streams (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'idle',
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signature_bindings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    consent_id TEXT REFERENCES consents(id) ON DELETE SET NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_perf_streams_user ON performance_streams(user_id);
CREATE INDEX IF NOT EXISTS idx_signature_user ON signature_bindings(user_id);

CREATE TABLE IF NOT EXISTS stream_recordings (
    id TEXT PRIMARY KEY,
    stream_id TEXT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    camera_role TEXT NOT NULL DEFAULT 'performance',
    title TEXT NOT NULL DEFAULT '',
    raw_path TEXT,
    clip_path TEXT,
    status TEXT NOT NULL DEFAULT 'recording',
    duration_sec REAL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS platform_links (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    username TEXT NOT NULL DEFAULT '',
    external_user_id TEXT,
    oauth_token TEXT,
    refresh_token TEXT,
    scopes TEXT,
    linked_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, platform)
);

CREATE TABLE IF NOT EXISTS platform_comments (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    external_comment_id TEXT NOT NULL,
    stream_recording_id TEXT,
    performance_stream_id TEXT,
    author_username TEXT,
    author_external_id TEXT,
    text TEXT NOT NULL,
    direction TEXT NOT NULL DEFAULT 'inbound',
    synced_at TEXT NOT NULL,
    UNIQUE(platform, external_comment_id)
);

CREATE TABLE IF NOT EXISTS platform_stream_targets (
    id TEXT PRIMARY KEY,
    stream_recording_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    external_broadcast_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recordings_user ON stream_recordings(user_id);
CREATE INDEX IF NOT EXISTS idx_platform_links_user ON platform_links(user_id);

CREATE TABLE IF NOT EXISTS face_presence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    seconds REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, camera_id, period_key)
);

CREATE INDEX IF NOT EXISTS idx_face_presence_cam_period ON face_presence(camera_id, period_key);
CREATE INDEX IF NOT EXISTS idx_face_presence_user ON face_presence(user_id);

CREATE TABLE IF NOT EXISTS face_presence_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    seconds REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_presence_events_camera_time
    ON face_presence_events(camera_id, recorded_at);

CREATE TABLE IF NOT EXISTS ad_payouts (
    id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    poi_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    ad_amount REAL NOT NULL,
    user_pool REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ad_payout_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payout_id TEXT NOT NULL REFERENCES ad_payouts(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seconds REAL NOT NULL,
    share REAL NOT NULL,
    ut_earned REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS stream_presence_rewards (
    id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    camera_id TEXT NOT NULL,
    presence_seconds REAL NOT NULL,
    ut_earned REAL NOT NULL DEFAULT 1,
    rewarded_at TEXT NOT NULL,
    UNIQUE(stream_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_stream_rewards_stream ON stream_presence_rewards(stream_id);
CREATE INDEX IF NOT EXISTS idx_stream_rewards_user ON stream_presence_rewards(user_id);

CREATE TABLE IF NOT EXISTS poi_chat_messages (
    id TEXT PRIMARY KEY,
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS poi_chat_mutes (
    poi_id TEXT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    muted_until TEXT,
    muted_by TEXT,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    PRIMARY KEY (poi_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_poi_created ON poi_chat_messages(poi_id, created_at);
"""


MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
    "ALTER TABLE users ADD COLUMN blocked_until TEXT",
    "ALTER TABLE pois ADD COLUMN address TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN comment TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN mask_image TEXT",
    "ALTER TABLE cameras ADD COLUMN device_id TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE cameras ADD COLUMN slot_index INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE cameras ADD COLUMN is_preview INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE cameras ADD COLUMN source_type TEXT NOT NULL DEFAULT 'rtsp'",
    "ALTER TABLE cameras ADD COLUMN device_label TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE pois ADD COLUMN menu_items_json TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE performance_streams ADD COLUMN recording_id TEXT",
    "ALTER TABLE performance_streams ADD COLUMN clip_path TEXT",
    "ALTER TABLE performance_streams ADD COLUMN clip_status TEXT",
    "ALTER TABLE pois ADD COLUMN status TEXT NOT NULL DEFAULT 'published'",
    "ALTER TABLE pois ADD COLUMN submitted_by TEXT",
    "ALTER TABLE pois ADD COLUMN facing_mode TEXT NOT NULL DEFAULT 'user'",
    "ALTER TABLE pois ADD COLUMN linger_until TEXT",
    "ALTER TABLE pois ADD COLUMN replay_clip_path TEXT",
    "ALTER TABLE pois ADD COLUMN live_ended_at TEXT",
]


def migrate(conn: sqlite3.Connection) -> None:
    user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    poi_cols = {r[1] for r in conn.execute("PRAGMA table_info(pois)")}
    cam_cols = {r[1] for r in conn.execute("PRAGMA table_info(cameras)")}
    for sql in MIGRATIONS:
        col = sql.split("ADD COLUMN ")[1].split()[0]
        if col in ("role", "blocked_until") and col in user_cols:
            continue
        if col in ("address", "comment", "mask_image") and col in poi_cols:
            continue
        if col in ("device_id", "slot_index", "is_preview", "source_type", "device_label") and col in cam_cols:
            continue
        if col == "menu_items_json" and col in poi_cols:
            continue
        if col in ("status", "submitted_by", "facing_mode", "linger_until", "replay_clip_path", "live_ended_at") and col in poi_cols:
            continue
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    migrate(conn)
    return conn


def masks_dir() -> Path:
    d = db_path().parent / "masks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)
