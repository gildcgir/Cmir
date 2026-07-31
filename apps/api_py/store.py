"""Persistent store — SQLite backend for Cmir core."""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from auth import hash_password, is_blocked, is_session_valid, new_session_token, session_expires, verify_password
from compliance import (
    LEGAL_VERSION,
    audit_log,
    blockchain_record,
    decrypt_embedding,
    encrypt_embedding,
    ensure_legal_documents,
    list_legal_documents,
    normalize_phone,
    phone_to_email,
    require_data_key_in_prod,
    validate_acceptances,
)
from database import app_env, connect, masks_dir, row_to_dict
from face_profiles import MIN_TEMPLATES, REQUIRED_POSES, normalize_face_templates
from stream_paths import poi_rtmp_url
from stream_recorder import RECORDER

PATCH_DIM = 32 * 32
# Доля рекламного бюджета, распределяемая зрителям-в-кадре (utility tokens)
AD_USER_POOL_RATIO = 0.5
# 1 единица денежной выручки рекламы → столько UT при полном пуле
AD_UT_PER_REVENUE = 100.0
VIEW_MODES = frozenset({"fisheye", "standard", "zoom2x"})
CAMERA_ROLES = frozenset({"general", "consent", "performance"})


class PoiType(str, Enum):
    LIVE_CAM = "live_cam"
    SOCIAL_EVENT = "social_event"
    VENUE = "venue"

    def min_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 1, PoiType.SOCIAL_EVENT: 2, PoiType.VENUE: 3}[self]

    def min_consent_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 0, PoiType.SOCIAL_EVENT: 1, PoiType.VENUE: 1}[self]

    def min_performance_cameras(self) -> int:
        return {PoiType.LIVE_CAM: 0, PoiType.SOCIAL_EVENT: 0, PoiType.VENUE: 1}[self]


POI_TYPES = {e.value: e for e in PoiType}

DEMO_POI_NAMES = (
    "Demo: Social Event — Пингвинья вечеринка",
    "Тестовое место",
)


@dataclass
class Poi:
    id: str
    name: str
    description: str
    poi_type: str
    latitude: float
    longitude: float
    promo_description: str
    city: str
    country: str
    created_at: str
    updated_at: str


@dataclass
class Camera:
    id: str
    poi_id: str
    name: str
    stream_url: str
    role: str
    view_mode: str
    is_active: bool
    created_at: str
    device_id: str = ""
    device_label: str = ""
    slot_index: int = 0
    is_preview: bool = False
    source_type: str = "rtsp"


def _row_to_camera(row: sqlite3.Row) -> Camera:
    return Camera(
        id=row["id"],
        poi_id=row["poi_id"],
        name=row["name"],
        stream_url=row["stream_url"] or "",
        role=row["role"],
        view_mode=row["view_mode"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        device_id=row["device_id"] if "device_id" in row.keys() else "",
        device_label=row["device_label"] if "device_label" in row.keys() else "",
        slot_index=int(row["slot_index"]) if "slot_index" in row.keys() else 0,
        is_preview=bool(row["is_preview"]) if "is_preview" in row.keys() else False,
        source_type=row["source_type"] if "source_type" in row.keys() else "rtsp",
    )


@dataclass
class ConsentRecord:
    id: str
    poi_id: str
    user_id: str
    wallet_address: str
    consented_at: str
    consent_text_version: str
    has_embedding: bool


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self) -> None:
        require_data_key_in_prod()
        self.conn = connect()
        self.health_snapshots: Dict[str, List[dict]] = {}
        self.last_consent_id: Dict[str, str] = {}
        self._reload_last_consents()
        self._ensure_admin_user()
        if app_env() != "prod":
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass

    def _ensure_admin_user(self) -> None:
        import os

        pwd = os.environ.get("CMIR_ADMIN_PASSWORD", "").strip()
        if app_env() == "prod":
            if not pwd:
                raise RuntimeError("CMIR_ADMIN_PASSWORD is required in production")
        else:
            pwd = pwd or "admin"
        row = self.conn.execute("SELECT id FROM users WHERE email = ?", ("admin",)).fetchone()
        if row:
            self.conn.execute(
                "UPDATE users SET role = 'admin', password_hash = ? WHERE email = ?",
                (hash_password(pwd), "admin"),
            )
            self.conn.commit()
            self._ensure_wallet(row["id"])
            return
        uid = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO users (id, email, password_hash, display_name, role, blocked_until, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'admin', NULL, ?, ?)
            """,
            (uid, "admin", hash_password(pwd), "Administrator", t, t),
        )
        self.conn.commit()
        self._ensure_wallet(uid)

    def _camera_dict(self, row: sqlite3.Row) -> dict:
        d = row_to_dict(row) or {}
        d["is_active"] = bool(d.get("is_active", 0))
        d["is_preview"] = bool(d.get("is_preview", 0))
        return d

    def get_preview_camera(self, poi_id: str) -> Optional[dict]:
        row = self.conn.execute(
            """
            SELECT * FROM cameras
            WHERE poi_id = ? AND role = 'general' AND is_active = 1 AND is_preview = 1
            LIMIT 1
            """,
            (poi_id,),
        ).fetchone()
        if not row:
            row = self.conn.execute(
                """
                SELECT * FROM cameras
                WHERE poi_id = ? AND role = 'general' AND is_active = 1
                ORDER BY slot_index, created_at
                LIMIT 1
                """,
                (poi_id,),
            ).fetchone()
        return self._camera_dict(row) if row else None

    def _reload_last_consents(self) -> None:
        rows = self.conn.execute(
            """
            SELECT poi_id, id FROM consents
            WHERE revoked_at IS NULL
            ORDER BY consented_at ASC
            """
        ).fetchall()
        self.last_consent_id = {}
        for r in rows:
            self.last_consent_id[r["poi_id"]] = r["id"]

    # --- Auth ---

    def register_user(self, email: str, password: str, display_name: str = "") -> dict:
        email = email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("invalid email")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        uid = str(uuid.uuid4())
        t = now_iso()
        try:
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (uid, email, hash_password(password), display_name or email.split("@")[0], t, t),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("email already registered")
        self._ensure_wallet(uid)
        self.conn.commit()
        return self.user_public(self.get_user(uid))

    def login_user(self, email: str, password: str) -> dict:
        """Вход по email или телефону (киоск создаёт аккаунт вида +995…@kiosk.cmir.ge)."""
        ident = (email or "").strip()
        candidates = []
        if ident:
            candidates.append(ident.lower())
        if ident and ident.lower() != "admin":
            try:
                candidates.append(phone_to_email(ident).lower())
            except ValueError:
                pass
        row = None
        for cand in candidates:
            row = self.conn.execute("SELECT * FROM users WHERE email = ?", (cand,)).fetchone()
            if row:
                break
        if not row or not verify_password(password, row["password_hash"]):
            raise ValueError("invalid credentials")
        if is_blocked(row["blocked_until"]):
            raise ValueError("account blocked until " + (row["blocked_until"] or ""))
        token = new_session_token()
        t = now_iso()
        exp = session_expires()
        self.conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, row["id"], exp, t),
        )
        self.conn.commit()
        return {
            "token": token,
            "expires_at": exp,
            "user": self.user_public(row_to_dict(row)),
        }

    def logout_user(self, token: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.conn.commit()

    def user_from_token(self, token: str) -> Optional[dict]:
        if not token:
            return None
        row = self.conn.execute(
            """
            SELECT u.*, s.expires_at AS session_expires
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if not row or not is_session_valid(row["session_expires"]):
            return None
        return row_to_dict(row)

    def get_user(self, user_id: str) -> Optional[dict]:
        return row_to_dict(self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    def user_public(self, user: Optional[dict]) -> dict:
        if not user:
            raise KeyError("user not found")
        wallet = self.conn.execute(
            "SELECT address, balance_st, balance_ut, created_at FROM wallets WHERE user_id = ?",
            (user["id"],),
        ).fetchone()
        consents = self.conn.execute(
            """
            SELECT id, poi_id, wallet_address, consented_at, consent_text_version,
                   CASE WHEN face_embedding IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
            FROM consents WHERE user_id = ? AND revoked_at IS NULL
            ORDER BY consented_at DESC
            """,
            (user["id"],),
        ).fetchall()
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "role": user.get("role") or "user",
            "blocked_until": user.get("blocked_until"),
            "created_at": user["created_at"],
            "wallet": row_to_dict(wallet),
            "consents": [row_to_dict(c) for c in consents],
            "profile": self.get_user_profile(user["id"]),
        }

    def is_admin(self, user: dict) -> bool:
        return (user.get("role") or "user") == "admin"

    # --- Admin: users ---

    def list_users(self) -> List[dict]:
        rows = self.conn.execute(
            "SELECT id, email, display_name, role, blocked_until, created_at, updated_at FROM users ORDER BY created_at"
        ).fetchall()
        out = []
        for r in rows:
            d = row_to_dict(r)
            w = self.conn.execute(
                "SELECT address, balance_st, balance_ut FROM wallets WHERE user_id = ?", (d["id"],)
            ).fetchone()
            d["wallet"] = row_to_dict(w)
            out.append(d)
        return out

    def create_user_admin(self, body: dict) -> dict:
        email = body.get("email", "").strip().lower()
        password = body.get("password", "")
        display_name = body.get("display_name", "") or email.split("@")[0]
        role = body.get("role", "user")
        if role not in ("user", "admin"):
            raise ValueError("role must be user or admin")
        if email == "admin":
            raise ValueError("reserved email")
        if not email or ("@" not in email and role != "admin"):
            raise ValueError("invalid email")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        uid = str(uuid.uuid4())
        t = now_iso()
        try:
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, role, blocked_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (uid, email, hash_password(password), display_name, role, t, t),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("email already registered")
        return row_to_dict(self.get_user(uid))

    def update_user_admin(self, user_id: str, body: dict) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        fields, vals = [], []
        if "email" in body:
            email = body["email"].strip().lower()
            if email == "admin" and row["email"] != "admin":
                raise ValueError("reserved email")
            fields.append("email = ?")
            vals.append(email)
        if "display_name" in body:
            fields.append("display_name = ?")
            vals.append(body["display_name"])
        if "password" in body and body["password"]:
            if len(body["password"]) < 8:
                raise ValueError("password must be at least 8 characters")
            fields.append("password_hash = ?")
            vals.append(hash_password(body["password"]))
        if "role" in body:
            if body["role"] not in ("user", "admin"):
                raise ValueError("role must be user or admin")
            if row["email"] == "admin" and body["role"] != "admin":
                raise ValueError("cannot demote default admin")
            fields.append("role = ?")
            vals.append(body["role"])
        if not fields:
            return row_to_dict(row)
        fields.append("updated_at = ?")
        vals.append(now_iso())
        vals.append(user_id)
        self.conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", vals)
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    def delete_user(self, user_id: str) -> None:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        if row["email"] == "admin":
            raise ValueError("cannot delete default admin")
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def block_user(self, user_id: str, until: str) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        if row["email"] == "admin":
            raise ValueError("cannot block admin")
        self.conn.execute(
            "UPDATE users SET blocked_until = ?, updated_at = ? WHERE id = ?",
            (until, now_iso(), user_id),
        )
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    def unblock_user(self, user_id: str) -> dict:
        row = self.get_user(user_id)
        if not row:
            raise KeyError("user not found")
        self.conn.execute(
            "UPDATE users SET blocked_until = NULL, updated_at = ? WHERE id = ?",
            (now_iso(), user_id),
        )
        self.conn.commit()
        return row_to_dict(self.get_user(user_id))

    # --- POI / cameras ---

    def poi_payload(self, poi_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        p = row_to_dict(row)
        cams = [
            self._camera_dict(c)
            for c in self.conn.execute(
                "SELECT * FROM cameras WHERE poi_id = ? ORDER BY slot_index, created_at",
                (poi_id,),
            ).fetchall()
        ]
        rate = float(p["consent_rate"])
        return {
            **{k: p[k] for k in (
                "id", "name", "description", "poi_type", "latitude", "longitude",
                "promo_description", "city", "country", "created_at", "updated_at",
            )},
            "address": p.get("address") or "",
            "comment": p.get("comment") or "",
            "mask_image_url": f"/api/v1/pois/{poi_id}/mask-image" if p.get("mask_image") else None,
            "cameras": cams,
            "stats": {
                "poi_id": poi_id,
                "consent_rate_percent": rate,
                "participant_count_24h": int(p["participants_24h"]),
                "avatar_faces_ratio": 1.0 - rate / 100.0,
            },
        }

    def list_pois(self) -> List[dict]:
        self._maybe_restore_demo_fixtures()
        ids = [r["id"] for r in self.conn.execute("SELECT id FROM pois ORDER BY created_at").fetchall()]
        return [self.poi_payload(pid) for pid in ids]

    def _maybe_restore_demo_fixtures(self) -> None:
        """В test-среде восстанавливает демо-места, если карта пуста или нет эталонных POI."""
        if app_env() == "prod":
            return
        count = int(self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"])
        missing_demo = any(not self._poi_id_by_name(name) for name in DEMO_POI_NAMES)
        if count == 0 or missing_demo:
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass

    def create_poi(self, body: dict) -> Poi:
        poi_id = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO pois (id, name, description, poi_type, latitude, longitude,
                promo_description, city, country, address, comment, consent_rate, participants_24h, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """,
            (
                poi_id,
                body["name"],
                body.get("description", body.get("comment", "")),
                body.get("poi_type", "live_cam"),
                float(body["latitude"]),
                float(body["longitude"]),
                body.get("promo_description", ""),
                body.get("city", ""),
                body.get("country", ""),
                body.get("address", ""),
                body.get("comment", body.get("description", "")),
                t,
                t,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        return Poi(**{k: row[k] for k in (
            "id", "name", "description", "poi_type", "latitude", "longitude",
            "promo_description", "city", "country", "created_at", "updated_at",
        )})

    def validate_cameras(self, poi_id: str) -> Optional[str]:
        pt = PoiType(self.conn.execute("SELECT poi_type FROM pois WHERE id = ?", (poi_id,)).fetchone()["poi_type"])
        cams = self.conn.execute("SELECT role FROM cameras WHERE poi_id = ?", (poi_id,)).fetchall()
        if len(cams) < pt.min_cameras():
            return f"requires at least {pt.min_cameras()} cameras"
        consent = sum(1 for c in cams if c["role"] == "consent")
        if consent < pt.min_consent_cameras():
            return f"requires at least {pt.min_consent_cameras()} consent cameras"
        perf = sum(1 for c in cams if c["role"] == "performance")
        if perf < pt.min_performance_cameras():
            return f"requires at least {pt.min_performance_cameras()} performance cameras"
        return None

    def add_camera(self, poi_id: str, body: dict) -> Camera:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        cid = str(uuid.uuid4())
        t = now_iso()
        is_active = 1 if body.get("is_active", True) else 0
        is_preview = 1 if body.get("is_preview") else 0
        if is_preview:
            self.conn.execute(
                "UPDATE cameras SET is_preview = 0 WHERE poi_id = ? AND role = 'general'",
                (poi_id,),
            )
        self.conn.execute(
            """
            INSERT INTO cameras (id, poi_id, name, stream_url, role, view_mode, is_active,
                device_id, slot_index, is_preview, source_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                poi_id,
                body["name"],
                body.get("stream_url", ""),
                body.get("role", "general"),
                body.get("view_mode", "standard"),
                is_active,
                body.get("device_id", ""),
                int(body.get("slot_index", 0)),
                is_preview,
                body.get("source_type", "rtsp"),
                t,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (cid,)).fetchone()
        return _row_to_camera(row)

    def update_poi(self, poi_id: str, body: dict) -> Poi:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        fields = []
        vals: list[Any] = []
        for key in ("name", "description", "promo_description", "city", "country", "address", "comment"):
            if key in body:
                fields.append(f"{key} = ?")
                vals.append(body[key])
        if "latitude" in body:
            fields.append("latitude = ?")
            vals.append(float(body["latitude"]))
        if "longitude" in body:
            fields.append("longitude = ?")
            vals.append(float(body["longitude"]))
        fields.append("updated_at = ?")
        vals.append(now_iso())
        vals.append(poi_id)
        self.conn.execute(f"UPDATE pois SET {', '.join(fields)} WHERE id = ?", vals)
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        return Poi(**{k: row[k] for k in (
            "id", "name", "description", "poi_type", "latitude", "longitude",
            "promo_description", "city", "country", "created_at", "updated_at",
        )})

    def update_camera(self, camera_id: str, body: dict) -> Camera:
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            raise KeyError("camera not found")
        fields, vals = [], []
        for key in ("name", "stream_url", "role", "view_mode", "device_id", "source_type"):
            if key in body:
                if key == "role" and body["role"] not in CAMERA_ROLES:
                    raise ValueError(f"role must be one of {sorted(CAMERA_ROLES)}")
                if key == "view_mode" and body["view_mode"] not in VIEW_MODES:
                    raise ValueError(f"view_mode must be one of {sorted(VIEW_MODES)}")
                fields.append(f"{key} = ?")
                vals.append(body[key])
        if "slot_index" in body:
            fields.append("slot_index = ?")
            vals.append(int(body["slot_index"]))
        if "is_active" in body:
            fields.append("is_active = ?")
            vals.append(1 if body["is_active"] else 0)
        if body.get("is_preview"):
            self.conn.execute(
                "UPDATE cameras SET is_preview = 0 WHERE poi_id = ? AND role = 'general'",
                (row["poi_id"],),
            )
            fields.append("is_preview = ?")
            vals.append(1)
        elif "is_preview" in body:
            fields.append("is_preview = ?")
            vals.append(0)
        if fields:
            vals.append(camera_id)
            self.conn.execute(f"UPDATE cameras SET {', '.join(fields)} WHERE id = ?", vals)
            self.conn.commit()
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        return _row_to_camera(row)

    def delete_camera(self, camera_id: str) -> str:
        row = self.conn.execute("SELECT poi_id FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            raise KeyError("camera not found")
        self.conn.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
        self.conn.commit()
        return row["poi_id"]

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        row = self.conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            return None
        return _row_to_camera(row)

    def sync_poi_cameras(self, poi_id: str, cameras: List[dict]) -> List[dict]:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        if len(cameras) > 5:
            raise ValueError("max 5 cameras per poi")
        self.conn.execute("DELETE FROM cameras WHERE poi_id = ?", (poi_id,))
        t = now_iso()
        preview_marked = False
        for i, cam in enumerate(cameras):
            role = cam.get("role", "general")
            if role not in CAMERA_ROLES:
                raise ValueError(f"role must be one of {sorted(CAMERA_ROLES)}")
            cid = str(uuid.uuid4())
            is_preview = bool(cam.get("is_preview")) and not preview_marked and role == "general"
            if is_preview:
                preview_marked = True
            device_id = cam.get("device_id", "")
            device_label = cam.get("device_label", "")
            source_type = cam.get("source_type", "local_usb" if device_id else "rtsp")
            if device_id and is_preview:
                stream_url = poi_rtmp_url(poi_id)
            elif device_id:
                stream_url = cam.get("stream_url") or f"local://{device_id}"
            else:
                stream_url = cam.get("stream_url") or ""
            self.conn.execute(
                """
                INSERT INTO cameras (id, poi_id, name, stream_url, role, view_mode, is_active,
                    device_id, device_label, slot_index, is_preview, source_type, created_at)
                VALUES (?, ?, ?, ?, ?, 'standard', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    poi_id,
                    cam.get("name") or f"Камера {i + 1}",
                    stream_url,
                    role,
                    1 if cam.get("is_active", True) else 0,
                    device_id,
                    device_label,
                    int(cam.get("slot_index", i)),
                    1 if is_preview else 0,
                    source_type,
                    t,
                ),
            )
        self.conn.commit()
        rows = self.conn.execute(
            "SELECT * FROM cameras WHERE poi_id = ? ORDER BY slot_index, role",
            (poi_id,),
        ).fetchall()
        return [self._camera_dict(r) for r in rows]

    def network_quality(self) -> dict:
        from camera_health import probe_stream_url

        rows = self.conn.execute("SELECT * FROM cameras WHERE is_active = 1").fetchall()
        items = []
        for row in rows:
            cam = self._camera_dict(row)
            probe = probe_stream_url(cam["stream_url"])
            items.append({**cam, **probe})
        scores = [int(x.get("quality_score", 0)) for x in items]
        aggregate = round(sum(scores) / len(scores), 1) if scores else 0.0
        if aggregate >= 85:
            grade = "excellent"
        elif aggregate >= 65:
            grade = "good"
        elif aggregate >= 40:
            grade = "fair"
        else:
            grade = "poor"
        return {
            "environment": app_env(),
            "cameras": items,
            "aggregate_score": aggregate,
            "grade": grade,
            "camera_count": len(items),
        }

    def _period_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    def record_view(
        self, user_id: str, camera_id: str, seconds: float, ad_revenue: float = 0.01
    ) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        if self.is_admin(user):
            wallet = self._ensure_wallet(user_id)
            return {
                "recorded": False,
                "reason": "admin views excluded",
                "wallet_address": wallet,
            }
        cam = self.get_camera(camera_id)
        if not cam or not cam.is_active:
            raise KeyError("camera not found")
        wallet = self._ensure_wallet(user_id)
        period = self._period_key()
        unique_before = self.conn.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM view_events WHERE period_key = ?",
            (period,),
        ).fetchone()["c"]
        seen = self.conn.execute(
            "SELECT 1 FROM view_events WHERE period_key = ? AND user_id = ? LIMIT 1",
            (period, user_id),
        ).fetchone()
        unique = unique_before if seen else unique_before + 1
        ut = round((float(ad_revenue) / 2.0) * (1.0 / max(unique, 1)), 6)
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO view_events (user_id, camera_id, poi_id, seconds, ad_revenue, period_key, ut_earned, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, camera_id, cam.poi_id, seconds, ad_revenue, period, ut, t),
        )
        self.conn.execute(
            "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
            (ut, user_id),
        )
        self.conn.commit()
        return {
            "recorded": True,
            "ut_earned": ut,
            "unique_viewers_in_period": unique,
            "wallet_address": wallet,
            "period_key": period,
        }

    def clear_all_pois(self) -> int:
        """Test env cleanup — remove all POI (and cascaded cameras)."""
        if app_env() == "prod":
            raise ValueError("refusing to clear POIs in production")
        n = self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"]
        self.conn.execute("DELETE FROM pois")
        self.conn.commit()
        deleted = int(n)
        if app_env() != "prod":
            try:
                self.ensure_demo_fixtures()
            except Exception:
                pass
        return deleted

    def ensure_demo_fixtures(self) -> List[str]:
        """Идемпотентно восстанавливает демо-места для test-среды (карта, киоск, перфоманс)."""
        if app_env() == "prod":
            return []
        created: List[str] = []
        created.extend(self._ensure_demo_social_event())
        created.extend(self._ensure_demo_test_place())
        return created

    def _poi_id_by_name(self, name: str) -> Optional[str]:
        row = self.conn.execute("SELECT id FROM pois WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else None

    def _camera_exists(self, poi_id: str, role: str, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM cameras WHERE poi_id = ? AND role = ? AND name = ?",
            (poi_id, role, name),
        ).fetchone()
        return row is not None

    def _ensure_demo_social_event(self) -> List[str]:
        name = "Demo: Social Event — Пингвинья вечеринка"
        poi_id = self._poi_id_by_name(name)
        created: List[str] = []
        if not poi_id:
            poi = self.create_poi(
                {
                    "name": name,
                    "description": "Тестовая точка для Фазы 0",
                    "comment": "Демо: общий план, согласие, перфоманс",
                    "poi_type": "venue",
                    "latitude": 41.7151,
                    "longitude": 44.8271,
                    "promo_description": "Лучшее место в городе для live-трансляций.",
                    "address": "Тбилиси, проспект Руставели 1",
                    "city": "Tbilisi",
                    "country": "GE",
                }
            )
            poi_id = str(poi.id)
            created.append(name)
            self.conn.execute(
                "UPDATE pois SET consent_rate = 42, participants_24h = 17 WHERE id = ?",
                (poi_id,),
            )
            self.conn.commit()
        specs = [
            ("General A", "general", "fisheye", "rtsp://127.0.0.1:8554/gopro_main", True, 0),
            ("General B", "general", "zoom2x", "rtsp://127.0.0.1:8554/demo_general_b", False, 1),
            ("Consent kiosk", "consent", "standard", "rtsp://127.0.0.1:8554/demo_consent", False, 2),
            ("Performance table", "performance", "standard", "rtsp://127.0.0.1:8554/demo_performance", False, 3),
        ]
        for cam_name, role, mode, url, is_preview, slot in specs:
            if self._camera_exists(poi_id, role, cam_name):
                continue
            self.add_camera(
                poi_id,
                {
                    "name": cam_name,
                    "stream_url": url,
                    "role": role,
                    "view_mode": mode,
                    "slot_index": slot,
                    "is_preview": is_preview,
                    "is_active": True,
                    "source_type": "rtsp",
                },
            )
            created.append(f"{name} / {cam_name}")
        return created

    def _ensure_demo_test_place(self) -> List[str]:
        name = "Тестовое место"
        poi_id = self._poi_id_by_name(name)
        created: List[str] = []
        if not poi_id:
            poi = self.create_poi(
                {
                    "name": name,
                    "address": "Тбилиси, Руставели 1",
                    "comment": "Демо для админ-панели",
                    "poi_type": "live_cam",
                    "latitude": 41.7089,
                    "longitude": 44.7989,
                    "city": "Tbilisi",
                    "country": "GE",
                }
            )
            poi_id = str(poi.id)
            created.append(name)
        if not self._camera_exists(poi_id, "general", "Камера 1"):
            self.add_camera(
                poi_id,
                {
                    "name": "Камера 1",
                    "stream_url": "rtsp://127.0.0.1:8554/gopro_main",
                    "role": "general",
                    "view_mode": "standard",
                    "slot_index": 0,
                    "is_preview": True,
                    "is_active": True,
                    "source_type": "rtsp",
                },
            )
            created.append(f"{name} / Камера 1")
        return created

    # --- Consent + wallet (linked to user) ---

    def _ensure_wallet(self, user_id: str) -> str:
        row = self.conn.execute("SELECT address FROM wallets WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return row["address"]
        addr = f"0xcmir{uuid.uuid4().hex}"
        t = now_iso()
        self.conn.execute(
            "INSERT INTO wallets (address, user_id, balance_st, balance_ut, created_at) VALUES (?, ?, 0, 100, ?)",
            (addr, user_id, t),
        )
        return addr

    def delete_poi(self, poi_id: str) -> None:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        self.delete_mask_image(poi_id)
        self.conn.execute("DELETE FROM pois WHERE id = ?", (poi_id,))
        self.conn.commit()

    def save_mask_image(self, poi_id: str, data: bytes, ext: str = "png") -> str:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        self.delete_mask_image(poi_id, keep_db=False)
        fname = f"{poi_id}.{ext}"
        path = masks_dir() / fname
        path.write_bytes(data)
        self.conn.execute(
            "UPDATE pois SET mask_image = ?, updated_at = ? WHERE id = ?",
            (fname, now_iso(), poi_id),
        )
        self.conn.commit()
        return fname

    def get_mask_image_path(self, poi_id: str) -> Optional[Path]:
        row = self.conn.execute("SELECT mask_image FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row or not row["mask_image"]:
            return None
        path = masks_dir() / row["mask_image"]
        return path if path.is_file() else None

    def delete_mask_image(self, poi_id: str, keep_db: bool = True) -> None:
        path = self.get_mask_image_path(poi_id)
        if path:
            path.unlink(missing_ok=True)
        if keep_db:
            self.conn.execute(
                "UPDATE pois SET mask_image = NULL, updated_at = ? WHERE id = ?",
                (now_iso(), poi_id),
            )
            self.conn.commit()

    def grant_consent(
        self,
        poi_id: str,
        user_id: str,
        embedding: Optional[List[float]] = None,
        embeddings: Optional[List[Any]] = None,
        *,
        require_multi: bool = False,
    ) -> dict:
        user = self.get_user(user_id)
        if user and is_blocked(user.get("blocked_until")):
            raise ValueError("account blocked")
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        templates = normalize_face_templates(
            embedding, embeddings, require_multi=require_multi
        )
        wallet = self._ensure_wallet(user_id)
        cid = str(uuid.uuid4())
        t = now_iso()
        primary = templates[0]["embedding"]
        emb_json = encrypt_embedding(primary)
        self.conn.execute(
            """
            INSERT INTO consents (id, user_id, poi_id, wallet_address, face_embedding,
                consent_text_version, consented_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (cid, user_id, poi_id, wallet, emb_json, LEGAL_VERSION, t),
        )
        self.conn.execute(
            "INSERT INTO poi_embeddings (poi_id, consent_id, embedding_json) VALUES (?, ?, ?)",
            (poi_id, cid, emb_json),
        )
        for tpl in templates:
            self.conn.execute(
                """
                INSERT INTO face_templates
                    (id, user_id, consent_id, poi_id, pose, yaw, pitch, embedding_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    cid,
                    poi_id,
                    tpl["pose"],
                    tpl.get("yaw"),
                    tpl.get("pitch"),
                    encrypt_embedding(tpl["embedding"]),
                    t,
                ),
            )
        row = self.conn.execute("SELECT consent_rate, participants_24h FROM pois WHERE id = ?", (poi_id,)).fetchone()
        rate = min(100.0, float(row["consent_rate"]) + 5.0)
        parts = int(row["participants_24h"]) + 1
        self.conn.execute(
            "UPDATE pois SET consent_rate = ?, participants_24h = ?, updated_at = ? WHERE id = ?",
            (rate, parts, t, poi_id),
        )
        self.conn.commit()
        self.last_consent_id[poi_id] = cid
        return {
            "id": cid,
            "poi_id": poi_id,
            "user_id": user_id,
            "wallet_address": wallet,
            "consented_at": t,
            "consent_text_version": LEGAL_VERSION,
            "has_embedding": True,
            "template_count": len(templates),
            "poses": [t["pose"] for t in templates],
        }

    def poi_menu_items(self, poi_id: str) -> List[str]:
        row = self.conn.execute("SELECT menu_items_json FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        try:
            items = json.loads(row["menu_items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
        if not items:
            items = ["Бургер", "Пицца", "Коктейль", "Салат", "Десерт", "Кофе"]
        return items

    def kiosk_register(
        self,
        poi_id: str,
        full_name: str,
        phone: str,
        favorite_menu_item: str,
        embedding: Optional[List[float]],
        acceptances: dict,
        client_meta: Optional[dict] = None,
        embeddings: Optional[List[Any]] = None,
        *,
        require_multi: bool = False,
    ) -> dict:
        validate_acceptances(acceptances)
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        if not (full_name or "").strip():
            raise ValueError("full_name required")
        if not (favorite_menu_item or "").strip():
            raise ValueError("favorite_menu_item required")
        # Валидация поз до создания пользователя
        normalize_face_templates(embedding, embeddings, require_multi=require_multi)

        ensure_legal_documents(self.conn)
        docs = {d["doc_type"]: d for d in list_legal_documents(self.conn)}
        phone_norm = normalize_phone(phone)
        email = phone_to_email(phone_norm)
        t = now_iso()

        row = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        temporary_password: Optional[str] = None
        if row:
            user_id = row["id"]
            self.conn.execute(
                "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
                (full_name.strip(), t, user_id),
            )
        else:
            user_id = str(uuid.uuid4())
            temporary_password = secrets.token_urlsafe(12)
            self.conn.execute(
                """
                INSERT INTO users (id, email, password_hash, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, email, hash_password(temporary_password), full_name.strip(), t, t),
            )
            self._ensure_wallet(user_id)

        prof = self.conn.execute("SELECT 1 FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if prof:
            self.conn.execute(
                """
                UPDATE user_profiles SET full_name = ?, phone = ?, favorite_menu_item = ?,
                    registered_via = 'kiosk', updated_at = ? WHERE user_id = ?
                """,
                (full_name.strip(), phone_norm, favorite_menu_item.strip(), t, user_id),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO user_profiles (user_id, full_name, phone, favorite_menu_item, registered_via, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'kiosk', ?, ?)
                """,
                (user_id, full_name.strip(), phone_norm, favorite_menu_item.strip(), t, t),
            )

        consent = self.grant_consent(
            poi_id,
            user_id,
            embedding,
            embeddings,
            require_multi=require_multi,
        )
        for doc_type in acceptances:
            if doc_type not in docs:
                continue
            doc = docs[doc_type]
            self.conn.execute(
                """
                INSERT INTO consent_document_acceptances
                    (id, consent_id, doc_type, doc_version, content_hash, accepted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    consent["id"],
                    doc_type,
                    doc["version"],
                    doc["content_hash"],
                    t,
                ),
            )

        chain = blockchain_record(
            self.conn,
            user_id,
            {
                "event": "user_registered",
                "poi_id": poi_id,
                "consent_id": consent["id"],
                "legal_version": LEGAL_VERSION,
                "phone_hash": hashlib.sha256(phone_norm.encode()).hexdigest(),
            },
        )
        audit_log(
            self.conn,
            "kiosk_register",
            user_id=user_id,
            poi_id=poi_id,
            details={"consent_id": consent["id"], "client": client_meta or {}},
        )
        self.conn.commit()
        wallet = self.conn.execute(
            "SELECT address, balance_st, balance_ut FROM wallets WHERE user_id = ?", (user_id,)
        ).fetchone()
        token = new_session_token()
        exp = session_expires()
        self.conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, exp, t),
        )
        self.conn.commit()
        out = {
            "user_id": user_id,
            "display_name": full_name.strip(),
            "phone": phone_norm,
            "login_email": email,
            "favorite_menu_item": favorite_menu_item.strip(),
            "consent": consent,
            "wallet": row_to_dict(wallet),
            "blockchain": chain,
            "auth": {"token": token, "expires_at": exp},
            "account_url": "/index.html#account",
            "message": "Регистрация завершена. Маска будет снята при распознавании лица на камерах.",
        }
        if temporary_password:
            out["temporary_password"] = temporary_password
            out["message"] += (
                f" Сохраните вход: телефон {phone_norm} (или {email})"
                f" и пароль {temporary_password}."
            )
        return out

    def revoke_consent(self, poi_id: str, consent_id: str, user_id: Optional[str] = None) -> dict:
        if consent_id == "latest":
            consent_id = self.last_consent_id.get(poi_id, "")
        q = "SELECT * FROM consents WHERE poi_id = ? AND id = ? AND revoked_at IS NULL"
        params: list[Any] = [poi_id, consent_id]
        if user_id:
            q += " AND user_id = ?"
            params.append(user_id)
        row = self.conn.execute(q, params).fetchone()
        if not row:
            raise KeyError("consent not found")
        t = now_iso()
        self.conn.execute(
            "UPDATE consents SET revoked_at = ?, face_embedding = NULL WHERE id = ?",
            (t, consent_id),
        )
        self.conn.execute(
            "DELETE FROM poi_embeddings WHERE poi_id = ? AND consent_id = ?",
            (poi_id, consent_id),
        )
        self.conn.execute("DELETE FROM face_templates WHERE consent_id = ?", (consent_id,))
        remaining = self.conn.execute(
            "SELECT COUNT(*) AS c FROM poi_embeddings WHERE poi_id = ?", (poi_id,)
        ).fetchone()["c"]
        prow = self.conn.execute("SELECT consent_rate FROM pois WHERE id = ?", (poi_id,)).fetchone()
        rate = max(0.0, float(prow["consent_rate"]) - 5.0)
        self.conn.execute("UPDATE pois SET consent_rate = ?, updated_at = ? WHERE id = ?", (rate, t, poi_id))
        self.conn.commit()
        return {"poi_id": poi_id, "consent_id": consent_id, "embeddings_remaining": remaining}

    def poi_embeddings(self, poi_id: str) -> List[List[float]]:
        rows = self.conn.execute(
            """
            SELECT e.embedding_json FROM face_templates e
            JOIN consents c ON c.id = e.consent_id
            WHERE e.poi_id = ? AND c.revoked_at IS NULL
            """,
            (poi_id,),
        ).fetchall()
        out = []
        for r in rows:
            emb = decrypt_embedding(r["embedding_json"] or "")
            if emb and len(emb) == PATCH_DIM:
                out.append(emb)
        if out:
            return out
        rows = self.conn.execute(
            """
            SELECT e.embedding_json FROM poi_embeddings e
            JOIN consents c ON c.id = e.consent_id
            WHERE e.poi_id = ? AND c.revoked_at IS NULL
            """,
            (poi_id,),
        ).fetchall()
        for r in rows:
            emb = decrypt_embedding(r["embedding_json"] or "")
            if emb and len(emb) == PATCH_DIM:
                out.append(emb)
        return out

    def global_consented_faces(self) -> List[dict]:
        """Один пользователь → все pose-шаблоны для устойчивого матчинга на потоке."""
        rows = self.conn.execute(
            """
            SELECT u.id AS user_id,
                   COALESCE(NULLIF(p.full_name, ''), u.display_name) AS display_name,
                   t.pose,
                   t.yaw,
                   t.pitch,
                   t.embedding_json
            FROM face_templates t
            JOIN consents c ON c.id = t.consent_id
            JOIN users u ON u.id = c.user_id
            LEFT JOIN user_profiles p ON p.user_id = u.id
            WHERE c.revoked_at IS NULL
            ORDER BY u.id, t.created_at
            """
        ).fetchall()
        by_user: Dict[str, dict] = {}
        for r in rows:
            uid = r["user_id"]
            emb = decrypt_embedding(r["embedding_json"] or "")
            if not emb or len(emb) != PATCH_DIM:
                continue
            entry = by_user.setdefault(
                uid,
                {
                    "user_id": uid,
                    "display_name": r["display_name"] or "",
                    "embedding": emb,
                    "embeddings": [],
                    "templates": [],
                },
            )
            entry["embeddings"].append(emb)
            entry["templates"].append(
                {
                    "pose": r["pose"],
                    "yaw": r["yaw"],
                    "pitch": r["pitch"],
                    "embedding": emb,
                }
            )

        legacy = self.conn.execute(
            """
            SELECT u.id AS user_id,
                   COALESCE(NULLIF(p.full_name, ''), u.display_name) AS display_name,
                   e.embedding_json
            FROM poi_embeddings e
            JOIN consents c ON c.id = e.consent_id
            JOIN users u ON u.id = c.user_id
            LEFT JOIN user_profiles p ON p.user_id = u.id
            WHERE c.revoked_at IS NULL
            """
        ).fetchall()
        for r in legacy:
            uid = r["user_id"]
            if uid in by_user:
                continue
            emb = decrypt_embedding(r["embedding_json"] or "")
            if not emb or len(emb) != PATCH_DIM:
                continue
            by_user[uid] = {
                "user_id": uid,
                "display_name": r["display_name"] or "",
                "embedding": emb,
                "embeddings": [emb],
                "templates": [{"pose": "center", "embedding": emb}],
            }

        return list(by_user.values())

    def match_face_embedding(
        self,
        embedding: List[float],
        *,
        threshold: float = 0.82,
        hold_threshold: float = 0.75,
        prior_user_id: str = "",
    ) -> Optional[dict]:
        """Server-side match — returns identity without exposing gallery vectors."""
        if not embedding or len(embedding) != PATCH_DIM:
            return None

        def _norm(v: List[float]) -> List[float]:
            n = sum(x * x for x in v) ** 0.5
            if n < 1e-9:
                return v
            return [x / n for x in v]

        def _cosine(a: List[float], b: List[float]) -> float:
            if len(a) != len(b):
                return 0.0
            return float(sum(x * y for x, y in zip(a, b)))

        query = _norm(embedding)
        faces = self.global_consented_faces()
        best: Optional[dict] = None
        best_score = hold_threshold if prior_user_id else threshold
        for face in faces:
            thr = hold_threshold if prior_user_id and face["user_id"] == prior_user_id else threshold
            score = 0.0
            for emb in face.get("embeddings") or []:
                score = max(score, _cosine(query, _norm(emb)))
            if not face.get("embeddings") and face.get("embedding"):
                score = _cosine(query, _norm(face["embedding"]))
            if score >= thr and score >= best_score:
                best_score = score
                best = {
                    "matched": True,
                    "user_id": face["user_id"],
                    "display_name": face.get("display_name") or "",
                    "score": round(score, 4),
                }
        return best

    def filter_poi_ids(self, city: Optional[str], country: Optional[str]) -> List[str]:
        q = "SELECT id, city, country FROM pois"
        out = []
        for r in self.conn.execute(q).fetchall():
            if city and (r["city"] or "").lower() != city.lower():
                continue
            if country and (r["country"] or "").upper() != country.upper():
                continue
            out.append(r["id"])
        return out

    def sorted_tops(self, key: str, city: Optional[str], country: Optional[str]) -> List[dict]:
        ids = self.filter_poi_ids(city, country)
        items = [self.poi_payload(pid) for pid in ids]
        if key == "consent":
            items.sort(key=lambda x: x["stats"]["consent_rate_percent"], reverse=True)
        else:
            items.sort(key=lambda x: x["stats"]["participant_count_24h"], reverse=True)
        return items

    def get_wallet(self, address: str) -> Optional[dict]:
        row = self.conn.execute(
            """
            SELECT w.*, u.email, u.display_name
            FROM wallets w JOIN users u ON u.id = w.user_id
            WHERE w.address = ?
            """,
            (address,),
        ).fetchone()
        if not row:
            return None
        d = row_to_dict(row)
        return {
            "address": d["address"],
            "user_id": d["user_id"],
            "email": d["email"],
            "display_name": d["display_name"],
            "balance_st": d["balance_st"],
            "balance_ut": d["balance_ut"],
            "created_at": d["created_at"],
        }

    def add_airtime(self, poi_id: str, wallet: str, seconds: float) -> dict:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        t = now_iso()
        self.conn.execute(
            "INSERT INTO airtime (poi_id, wallet_address, seconds, recorded_at) VALUES (?, ?, ?, ?)",
            (poi_id, wallet, seconds, t),
        )
        w = self.conn.execute("SELECT balance_st, balance_ut FROM wallets WHERE address = ?", (wallet,)).fetchone()
        if w:
            st = round(float(w["balance_st"]) + seconds * 0.01, 4)
            ut = round(float(w["balance_ut"]) + seconds * 0.05, 2)
            self.conn.execute(
                "UPDATE wallets SET balance_st = ?, balance_ut = ? WHERE address = ?",
                (st, ut, wallet),
            )
        self.conn.commit()
        return {"wallet": wallet, "seconds": seconds, "at": t}

    def record_face_presence(
        self, user_id: str, camera_id: str, seconds: float, period_key: Optional[str] = None
    ) -> dict:
        """Накопить секунды присутствия зарегистрированного лица на камере (период = час UTC)."""
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        if self.is_admin(user):
            return {"recorded": False, "reason": "admin excluded"}
        cam = self.get_camera(camera_id)
        if not cam or not cam.is_active:
            raise KeyError("camera not found")
        # Только пользователи с активным согласием
        consent = self.conn.execute(
            "SELECT 1 FROM consents WHERE user_id = ? AND revoked_at IS NULL LIMIT 1",
            (user_id,),
        ).fetchone()
        if not consent:
            raise ValueError("active consent required")
        period = period_key or self._period_key()
        t = now_iso()
        existing = self.conn.execute(
            """
            SELECT id, seconds FROM face_presence
            WHERE user_id = ? AND camera_id = ? AND period_key = ?
            """,
            (user_id, camera_id, period),
        ).fetchone()
        if existing:
            new_sec = float(existing["seconds"]) + float(seconds)
            self.conn.execute(
                "UPDATE face_presence SET seconds = ?, updated_at = ? WHERE id = ?",
                (new_sec, t, existing["id"]),
            )
        else:
            new_sec = float(seconds)
            self.conn.execute(
                """
                INSERT INTO face_presence (user_id, camera_id, poi_id, period_key, seconds, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, camera_id, cam.poi_id, period, new_sec, t),
            )
        self.conn.execute(
            """
            INSERT INTO face_presence_events (user_id, camera_id, poi_id, seconds, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, camera_id, cam.poi_id, float(seconds), t),
        )
        self.conn.commit()
        return {
            "recorded": True,
            "user_id": user_id,
            "camera_id": camera_id,
            "poi_id": cam.poi_id,
            "period_key": period,
            "seconds_total": new_sec,
            "seconds_added": float(seconds),
        }

    def list_face_presence(
        self,
        user_id: Optional[str] = None,
        camera_id: Optional[str] = None,
        period_key: Optional[str] = None,
    ) -> List[dict]:
        q = """
            SELECT fp.*, u.display_name, c.name AS camera_name
            FROM face_presence fp
            JOIN users u ON u.id = fp.user_id
            LEFT JOIN cameras c ON c.id = fp.camera_id
            WHERE 1=1
        """
        params: list[Any] = []
        if user_id:
            q += " AND fp.user_id = ?"
            params.append(user_id)
        if camera_id:
            q += " AND fp.camera_id = ?"
            params.append(camera_id)
        if period_key:
            q += " AND fp.period_key = ?"
            params.append(period_key)
        q += " ORDER BY fp.updated_at DESC"
        return [row_to_dict(r) for r in self.conn.execute(q, params).fetchall()]

    def distribute_ad_revenue(
        self,
        camera_id: str,
        ad_amount: float,
        period_key: Optional[str] = None,
        user_pool_ratio: float = AD_USER_POOL_RATIO,
    ) -> dict:
        """
        Работодатель оплатил рекламу на трансляции камеры.
        Пул user_pool = ad_amount * user_pool_ratio конвертируется в UT и делится
        пропорционально секундам присутствия лиц в кадре за period_key (час).
        """
        if ad_amount <= 0:
            raise ValueError("ad_amount must be positive")
        cam = self.get_camera(camera_id)
        if not cam:
            raise KeyError("camera not found")
        period = period_key or self._period_key()
        rows = self.conn.execute(
            """
            SELECT user_id, seconds FROM face_presence
            WHERE camera_id = ? AND period_key = ? AND seconds > 0
            """,
            (camera_id, period),
        ).fetchall()
        total_sec = sum(float(r["seconds"]) for r in rows)
        payout_id = str(uuid.uuid4())
        t = now_iso()
        user_pool = float(ad_amount) * float(user_pool_ratio)
        ut_pool = user_pool * AD_UT_PER_REVENUE
        self.conn.execute(
            """
            INSERT INTO ad_payouts (id, camera_id, poi_id, period_key, ad_amount, user_pool, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payout_id, camera_id, cam.poi_id, period, float(ad_amount), user_pool, t),
        )
        shares: List[dict] = []
        if total_sec <= 0 or not rows:
            self.conn.commit()
            return {
                "payout_id": payout_id,
                "camera_id": camera_id,
                "period_key": period,
                "ad_amount": float(ad_amount),
                "user_pool": user_pool,
                "ut_pool": ut_pool,
                "total_presence_seconds": 0.0,
                "shares": [],
                "message": "Нет присутствия в кадре за период — UT не начислены",
            }
        for r in rows:
            sec = float(r["seconds"])
            share = sec / total_sec
            ut = round(ut_pool * share, 6)
            uid = r["user_id"]
            self.conn.execute(
                """
                INSERT INTO ad_payout_shares (payout_id, user_id, seconds, share, ut_earned)
                VALUES (?, ?, ?, ?, ?)
                """,
                (payout_id, uid, sec, share, ut),
            )
            self._ensure_wallet(uid)
            self.conn.execute(
                "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
                (ut, uid),
            )
            shares.append(
                {
                    "user_id": uid,
                    "seconds": sec,
                    "share": round(share, 6),
                    "ut_earned": ut,
                }
            )
        self.conn.commit()
        return {
            "payout_id": payout_id,
            "camera_id": camera_id,
            "poi_id": cam.poi_id,
            "period_key": period,
            "ad_amount": float(ad_amount),
            "user_pool": user_pool,
            "ut_pool": ut_pool,
            "total_presence_seconds": total_sec,
            "shares": shares,
        }

    def list_airtime(self, poi_id: str) -> List[dict]:
        return [
            row_to_dict(r)
            for r in self.conn.execute(
                "SELECT wallet_address AS wallet, seconds, recorded_at AS at FROM airtime WHERE poi_id = ? ORDER BY id",
                (poi_id,),
            ).fetchall()
        ]

    def add_donation(self, poi_id: str, amount: float, message: str, donor: str) -> dict:
        if not self.conn.execute("SELECT 1 FROM pois WHERE id = ?", (poi_id,)).fetchone():
            raise KeyError("poi not found")
        did = str(uuid.uuid4())
        t = now_iso()
        self.conn.execute(
            """
            INSERT INTO donations (id, poi_id, amount, currency, message, donor, status, created_at)
            VALUES (?, ?, ?, 'GEL', ?, ?, 'pending_moderation', ?)
            """,
            (did, poi_id, amount, message, donor, t),
        )
        self.conn.commit()
        return {
            "id": did,
            "poi_id": poi_id,
            "amount": amount,
            "currency": "GEL",
            "message": message,
            "donor": donor,
            "status": "pending_moderation",
            "created_at": t,
        }

    def list_donations(self, poi_id: Optional[str] = None) -> List[dict]:
        if poi_id:
            rows = self.conn.execute("SELECT * FROM donations WHERE poi_id = ? ORDER BY created_at DESC", (poi_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM donations ORDER BY created_at DESC").fetchall()
        return [row_to_dict(r) for r in rows]

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        return row_to_dict(
            self.conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        )

    def update_user_profile(self, user_id: str, body: dict) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise KeyError("user not found")
        t = now_iso()
        if "email" in body:
            email = body["email"].strip().lower()
            if not email or "@" not in email:
                raise ValueError("invalid email")
            self.conn.execute("UPDATE users SET email = ?, updated_at = ? WHERE id = ?", (email, t, user_id))
        prof = self.get_user_profile(user_id)
        phone = body.get("phone")
        fav = body.get("favorite_menu_item")
        if phone:
            phone = normalize_phone(phone)
        if prof:
            self.conn.execute(
                """
                UPDATE user_profiles SET
                    phone = COALESCE(?, phone),
                    favorite_menu_item = COALESCE(?, favorite_menu_item),
                    updated_at = ?
                WHERE user_id = ?
                """,
                (phone, fav.strip() if fav else None, t, user_id),
            )
        elif phone or fav:
            self.conn.execute(
                """
                INSERT INTO user_profiles (user_id, full_name, phone, favorite_menu_item, registered_via, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'web', ?, ?)
                """,
                (user_id, user.get("display_name", ""), phone or "", (fav or "").strip(), t, t),
            )
        self.conn.commit()
        return {
            "user": self.user_public(self.get_user(user_id)),
            "profile": self.get_user_profile(user_id),
        }

    def admin_stats(self) -> dict:
        users = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        wallets = self.conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(balance_st),0) AS st, COALESCE(SUM(balance_ut),0) AS ut FROM wallets"
        ).fetchone()
        pois = self.conn.execute("SELECT COUNT(*) AS c FROM pois").fetchone()["c"]
        cams = self.conn.execute(
            "SELECT role, COUNT(*) AS c FROM cameras WHERE is_active = 1 GROUP BY role"
        ).fetchall()
        consents = self.conn.execute(
            "SELECT COUNT(*) AS c FROM consents WHERE revoked_at IS NULL"
        ).fetchone()["c"]
        profiles = self.conn.execute("SELECT COUNT(*) AS c FROM user_profiles").fetchone()["c"]
        perf_streams = self.conn.execute("SELECT COUNT(*) AS c FROM performance_streams").fetchone()["c"]
        bindings = self.conn.execute(
            "SELECT COUNT(*) AS c FROM signature_bindings WHERE active = 1"
        ).fetchone()["c"]
        views = self.conn.execute("SELECT COALESCE(SUM(seconds),0) AS s FROM view_events").fetchone()["s"]
        quality = self.network_quality()
        top_pois = self.sorted_tops("consent", None, None)[:5]
        return {
            "users_total": users,
            "wallets_total": wallets["c"],
            "balance_st_total": float(wallets["st"]),
            "balance_ut_total": float(wallets["ut"]),
            "pois_total": pois,
            "consents_active": consents,
            "profiles_total": profiles,
            "performance_streams_total": perf_streams,
            "signature_bindings_active": bindings,
            "view_seconds_total": float(views),
            "cameras_by_role": {r["role"]: r["c"] for r in cams},
            "network_quality": quality,
            "top_pois_consent": top_pois,
        }

    def bind_signature(self, user_id: str, poi_id: str) -> dict:
        row = self.conn.execute(
            """
            SELECT id FROM consents WHERE user_id = ? AND poi_id = ? AND revoked_at IS NULL
            ORDER BY consented_at DESC LIMIT 1
            """,
            (user_id, poi_id),
        ).fetchone()
        if not row:
            raise ValueError("no active consent for this poi")
        t = now_iso()
        self.conn.execute(
            "UPDATE signature_bindings SET active = 0 WHERE user_id = ? AND poi_id = ?",
            (user_id, poi_id),
        )
        bid = str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO signature_bindings (id, user_id, poi_id, consent_id, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (bid, user_id, poi_id, row["id"], t),
        )
        self.conn.commit()
        audit_log(self.conn, "signature_bind", user_id=user_id, poi_id=poi_id, details={"binding_id": bid})
        self.conn.commit()
        return {"binding_id": bid, "poi_id": poi_id, "consent_id": row["id"], "active": True}

    def performance_stream_list(self, user_id: str, camera_id: str) -> List[dict]:
        rows = self.conn.execute(
            """
            SELECT * FROM performance_streams
            WHERE user_id = ? AND camera_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, camera_id),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def performance_stream_start(self, user_id: str, camera_id: str, title: str = "") -> dict:
        cam = self.get_camera(camera_id)
        if not cam or cam.role != "performance":
            raise ValueError("camera must be performance role")
        t = now_iso()
        sid = str(uuid.uuid4())
        rid = str(uuid.uuid4())
        RECORDER.start(rid, cam.poi_id)
        self.conn.execute(
            """
            INSERT INTO performance_streams
                (id, user_id, poi_id, camera_id, title, status, started_at, ended_at,
                 created_at, updated_at, recording_id, clip_path, clip_status)
            VALUES (?, ?, ?, ?, ?, 'live', ?, NULL, ?, ?, ?, NULL, 'recording')
            """,
            (sid, user_id, cam.poi_id, camera_id, title or "Эфир", t, t, t, rid),
        )
        self.conn.execute(
            """
            INSERT INTO stream_recordings
                (id, stream_id, user_id, poi_id, camera_id, camera_role, title, status,
                 started_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'performance', ?, 'recording', ?, ?, ?)
            """,
            (rid, sid, user_id, cam.poi_id, camera_id, title or "Эфир", t, t, t),
        )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (sid,)).fetchone())

    @staticmethod
    def _parse_iso(ts: str) -> datetime:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def reward_stream_participants(
        self,
        stream_id: str,
        camera_id: str,
        started_at: str,
        ended_at: Optional[str] = None,
    ) -> dict:
        """
        После эфира: 1 UT = полное время стрима.
        Участник получает долю: presence_seconds / stream_duration (макс. 1 UT).
        """
        finished = ended_at or now_iso()
        try:
            stream_duration = max(
                0.0,
                (self._parse_iso(finished) - self._parse_iso(started_at)).total_seconds(),
            )
        except ValueError:
            stream_duration = 0.0

        existing = self.conn.execute(
            """
            SELECT r.user_id, r.presence_seconds, r.ut_earned, u.display_name
            FROM stream_presence_rewards r
            JOIN users u ON u.id = r.user_id
            WHERE r.stream_id = ?
            ORDER BY u.display_name
            """,
            (stream_id,),
        ).fetchall()
        if existing:
            return {
                "stream_id": stream_id,
                "stream_duration_seconds": stream_duration,
                "full_stream_ut": 1.0,
                "participants": [row_to_dict(r) for r in existing],
                "already_rewarded": True,
            }

        rows = self.conn.execute(
            """
            SELECT e.user_id, SUM(e.seconds) AS presence_seconds, u.display_name
            FROM face_presence_events e
            JOIN users u ON u.id = e.user_id
            WHERE e.camera_id = ? AND e.recorded_at >= ? AND e.recorded_at <= ?
            GROUP BY e.user_id, u.display_name
            ORDER BY u.display_name
            """,
            (camera_id, started_at, finished),
        ).fetchall()
        participants = []
        for r in rows:
            uid = r["user_id"]
            reward_id = str(uuid.uuid4())
            seconds = float(r["presence_seconds"])
            if stream_duration <= 0:
                ut = 0.0
            else:
                ut = round(min(1.0, seconds / stream_duration), 6)
            if ut <= 0:
                continue
            self._ensure_wallet(uid)
            self.conn.execute(
                "UPDATE wallets SET balance_ut = ROUND(balance_ut + ?, 4) WHERE user_id = ?",
                (ut, uid),
            )
            self.conn.execute(
                """
                INSERT INTO stream_presence_rewards
                    (id, stream_id, user_id, camera_id, presence_seconds, ut_earned, rewarded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (reward_id, stream_id, uid, camera_id, seconds, ut, finished),
            )
            participants.append(
                {
                    "user_id": uid,
                    "display_name": r["display_name"],
                    "presence_seconds": seconds,
                    "share": round(seconds / stream_duration, 6) if stream_duration > 0 else 0.0,
                    "ut_earned": ut,
                }
            )
        self.conn.commit()
        return {
            "stream_id": stream_id,
            "stream_duration_seconds": stream_duration,
            "full_stream_ut": 1.0,
            "participants": participants,
            "already_rewarded": False,
        }

    def performance_stream_stop(self, user_id: str, stream_id: str) -> dict:
        row = self._perf_stream_owned(user_id, stream_id)
        t = now_iso()
        clip_path = None
        clip_status = "saved"
        recording_id = row.get("recording_id")
        if recording_id:
            raw = RECORDER.stop(recording_id)
            if raw:
                clip = RECORDER.process_clip(recording_id, raw)
                clip_path = str(clip) if clip else str(raw)
                clip_status = "ready"
                self.conn.execute(
                    """
                    UPDATE stream_recordings SET raw_path = ?, clip_path = ?, status = ?,
                        ended_at = ?, updated_at = ? WHERE id = ?
                    """,
                    (str(raw), clip_path, clip_status, t, t, recording_id),
                )
            else:
                clip_status = "failed"
                self.conn.execute(
                    "UPDATE stream_recordings SET status = 'failed', ended_at = ?, updated_at = ? WHERE id = ?",
                    (t, t, recording_id),
                )
        self.conn.execute(
            """
            UPDATE performance_streams SET status = 'saved', ended_at = ?, updated_at = ?,
                clip_path = ?, clip_status = ? WHERE id = ?
            """,
            (t, t, clip_path, clip_status, stream_id),
        )
        self.conn.commit()
        rewards = self.reward_stream_participants(
            stream_id,
            row["camera_id"],
            row["started_at"],
            t,
        )
        result = row_to_dict(
            self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (stream_id,)).fetchone()
        )
        result["rewards"] = rewards
        return result

    def general_stream_start(self, user_id: str, camera_id: str, title: str = "") -> dict:
        cam = self.get_camera(camera_id)
        if not cam or cam.role != "general":
            raise ValueError("camera must be general role")
        consent = self.conn.execute(
            "SELECT 1 FROM consents WHERE user_id = ? AND poi_id = ? AND revoked_at IS NULL",
            (user_id, cam.poi_id),
        ).fetchone()
        if not consent:
            raise ValueError("active consent required for this poi")
        t = now_iso()
        rid = str(uuid.uuid4())
        RECORDER.start(rid, cam.poi_id)
        self.conn.execute(
            """
            INSERT INTO stream_recordings
                (id, stream_id, user_id, poi_id, camera_id, camera_role, title, status,
                 started_at, created_at, updated_at)
            VALUES (?, NULL, ?, ?, ?, 'general', ?, 'recording', ?, ?, ?)
            """,
            (rid, user_id, cam.poi_id, camera_id, title or "Запись", t, t, t),
        )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM stream_recordings WHERE id = ?", (rid,)).fetchone())

    def general_stream_stop(self, user_id: str, recording_id: str) -> dict:
        row = self.conn.execute(
            "SELECT * FROM stream_recordings WHERE id = ? AND user_id = ?", (recording_id, user_id)
        ).fetchone()
        if not row:
            raise KeyError("recording not found")
        t = now_iso()
        raw = RECORDER.stop(recording_id)
        clip_path = None
        status = "failed"
        if raw:
            clip = RECORDER.process_clip(recording_id, raw)
            clip_path = str(clip) if clip else str(raw)
            status = "ready"
        self.conn.execute(
            """
            UPDATE stream_recordings SET raw_path = ?, clip_path = ?, status = ?,
                ended_at = ?, updated_at = ? WHERE id = ?
            """,
            (str(raw) if raw else None, clip_path, status, t, t, recording_id),
        )
        self.conn.commit()
        rewards = self.reward_stream_participants(
            recording_id,
            row["camera_id"],
            row["started_at"],
            t,
        )
        result = row_to_dict(
            self.conn.execute("SELECT * FROM stream_recordings WHERE id = ?", (recording_id,)).fetchone()
        )
        result["rewards"] = rewards
        return result

    def list_user_recordings(self, user_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM stream_recordings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def list_platform_links(self, user_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT id, platform, username, external_user_id, linked_at, updated_at FROM platform_links WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]

    def link_platform_username(self, user_id: str, platform: str, username: str) -> dict:
        from platforms import PLATFORMS

        if platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}")
        if not (username or "").strip():
            raise ValueError("username required")
        t = now_iso()
        existing = self.conn.execute(
            "SELECT id FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE platform_links SET username = ?, updated_at = ? WHERE id = ?",
                (username.strip(), t, existing["id"]),
            )
            lid = existing["id"]
        else:
            lid = str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO platform_links (id, user_id, platform, username, linked_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (lid, user_id, platform, username.strip(), t, t),
            )
        self.conn.commit()
        return row_to_dict(self.conn.execute("SELECT * FROM platform_links WHERE id = ?", (lid,)).fetchone())

    def unlink_platform(self, user_id: str, platform: str) -> None:
        self.conn.execute("DELETE FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform))
        self.conn.commit()

    def platform_oauth_complete(self, user_id: str, platform: str, token_data: dict) -> dict:
        from platforms import PLATFORMS

        if platform not in PLATFORMS:
            raise ValueError(f"platform must be one of {PLATFORMS}")
        t = now_iso()
        username = token_data.get("username") or token_data.get("login") or ""
        ext_id = token_data.get("external_user_id") or ""
        access = token_data.get("access_token") or ""
        refresh = token_data.get("refresh_token") or ""
        existing = self.conn.execute(
            "SELECT id FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE platform_links SET username = ?, external_user_id = ?, oauth_token = ?,
                    refresh_token = ?, updated_at = ? WHERE id = ?
                """,
                (username, ext_id, access, refresh, t, existing["id"]),
            )
            lid = existing["id"]
        else:
            lid = str(uuid.uuid4())
            self.conn.execute(
                """
                INSERT INTO platform_links
                    (id, user_id, platform, username, external_user_id, oauth_token, refresh_token, linked_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lid, user_id, platform, username, ext_id, access, refresh, t, t),
            )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id, platform, username, external_user_id, linked_at FROM platform_links WHERE id = ?",
            (lid,),
        ).fetchone()
        return row_to_dict(row)

    def sync_platform_comments(self, user_id: str, platform: str, broadcast_id: str) -> List[dict]:
        from platforms import get_adapter

        link = self.conn.execute(
            "SELECT * FROM platform_links WHERE user_id = ? AND platform = ?", (user_id, platform)
        ).fetchone()
        if not link or not link["oauth_token"]:
            raise ValueError("platform not linked with oauth")
        adapter = get_adapter(platform)
        comments = adapter.fetch_comments(link["oauth_token"], broadcast_id)
        t = now_iso()
        out = []
        for c in comments:
            cid = str(uuid.uuid4())
            ext = c.get("id", str(uuid.uuid4()))
            self.conn.execute(
                """
                INSERT OR IGNORE INTO platform_comments
                    (id, platform, external_comment_id, author_username, text, direction, synced_at)
                VALUES (?, ?, ?, ?, ?, 'inbound', ?)
                """,
                (cid, platform, ext, c.get("author", ""), c.get("text", ""), t),
            )
            out.append(c)
        self.conn.commit()
        return out

    def performance_stream_delete(self, user_id: str, stream_id: str) -> None:
        self._perf_stream_owned(user_id, stream_id)
        self.conn.execute("DELETE FROM performance_streams WHERE id = ?", (stream_id,))
        self.conn.commit()

    def _perf_stream_owned(self, user_id: str, stream_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM performance_streams WHERE id = ?", (stream_id,)).fetchone()
        if not row or row["user_id"] != user_id:
            raise KeyError("stream not found")
        return row_to_dict(row)

    def scene_description(self, poi_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM pois WHERE id = ?", (poi_id,)).fetchone()
        if not row:
            raise KeyError("poi not found")
        rate = float(row["consent_rate"])
        avatar_ratio = 1.0 - rate / 100.0
        real_ratio = rate / 100.0
        if avatar_ratio > real_ratio:
            mood = "fun"
            text = "Сейчас в кадре в основном гости с плашками — заходите, тут оживлённо!"
        else:
            mood = "promo"
            text = row["promo_description"] or f"Загляните в {row['name']} — лучшее место в районе."
        return {
            "poi_id": poi_id,
            "mood": mood,
            "description": text,
            "consent_rate_percent": rate,
            "avatar_ratio": avatar_ratio,
        }

    def record_health_snapshot(self, camera_id: str, status: str, detail: str) -> dict:
        snap = {"at": now_iso(), "status": status, "detail": detail}
        self.health_snapshots.setdefault(camera_id, []).append(snap)
        self.health_snapshots[camera_id] = self.health_snapshots[camera_id][-50:]
        return snap
