"""Соответствие требованиям Грузии по персональным и биометрическим данным (PDPL)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from database import app_env, db_path

LEGAL_VERSION = "1.0.0-ge"
DOC_TYPES = (
    "terms_of_service",
    "privacy_policy",
    "personal_data_consent",
    "biometric_data_consent",
    "wallet_agreement",
)

DOC_TITLES = {
    "terms_of_service": "Пользовательское соглашение (Terms of Service)",
    "privacy_policy": "Политика конфиденциальности (Privacy Policy)",
    "personal_data_consent": "Согласие на обработку персональных данных",
    "biometric_data_consent": "Согласие на обработку биометрических данных",
    "wallet_agreement": "Договор об открытии электронного кошелька",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def legal_dir() -> Path:
    d = db_path().parent / "legal"
    d.mkdir(parents=True, exist_ok=True)
    return d


def require_data_key_in_prod() -> None:
    if app_env() == "prod" and not os.environ.get("CMIR_DATA_KEY", "").strip():
        raise RuntimeError("CMIR_DATA_KEY is required in production")


def _fernet():
    import base64

    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    key = os.environ.get("CMIR_DATA_KEY", "").strip()
    if not key:
        if app_env() == "prod":
            return None
        # lab/test only: stable key derived from DB path (not for production)
        seed = hashlib.sha256(str(db_path()).encode()).digest()
        key = base64.urlsafe_b64encode(seed).decode()
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        digest = hashlib.sha256(key.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_embedding(vec: list[float]) -> str:
    f = _fernet()
    if f is None:
        if app_env() == "prod":
            raise RuntimeError("cryptography/Fernet unavailable; cannot store biometrics")
        return json.dumps(vec)
    return f.encrypt(json.dumps(vec).encode()).decode()


def decrypt_embedding(blob: str) -> Optional[list[float]]:
    if not blob:
        return None
    # legacy plaintext JSON
    try:
        data = json.loads(blob)
        if isinstance(data, list):
            return [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    f = _fernet()
    if f is None:
        return None
    try:
        return json.loads(f.decrypt(blob.encode()).decode())
    except Exception:
        return None


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("995") and len(digits) >= 12:
        return "+" + digits
    if len(digits) == 9:
        return "+995" + digits
    if digits:
        return "+" + digits
    raise ValueError("invalid phone")


def phone_to_email(phone: str) -> str:
    digits = re.sub(r"\D", "", normalize_phone(phone))
    return f"+{digits}@kiosk.cmir.ge"


def default_legal_text(doc_type: str) -> str:
    base = DOC_TITLES.get(doc_type, doc_type)
    return (
        f"{base}\n"
        f"Версия документа: {LEGAL_VERSION}\n"
        f"Дата вступления в силу: 2026-05-23\n\n"
        "Настоящий документ регулирует обработку персональных и биометрических данных "
        "в соответствии с Законом Грузии «О защите персональных данных» (PDPL), "
        "включая принципы законности, прозрачности, минимизации данных, ограничения цели "
        "и срока хранения. Оператор: Cmir Platform. Территория обработки: Грузия.\n\n"
        "Продолжая регистрацию, вы подтверждаете, что ознакомились с условиями документа "
        f"«{base}» и даёте информированное согласие в объёме, указанном в документе."
    )


def ensure_legal_documents(conn) -> None:
    for doc_type in DOC_TYPES:
        row = conn.execute(
            "SELECT id FROM legal_documents WHERE doc_type = ? AND version = ?",
            (doc_type, LEGAL_VERSION),
        ).fetchone()
        if row:
            continue
        text = default_legal_text(doc_type)
        fname = f"{doc_type}_{LEGAL_VERSION}.txt"
        path = legal_dir() / fname
        path.write_text(text, encoding="utf-8")
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        conn.execute(
            """
            INSERT INTO legal_documents (id, doc_type, version, title, content_hash, file_path, effective_from, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_type,
                LEGAL_VERSION,
                DOC_TITLES[doc_type],
                content_hash,
                fname,
                "2026-05-23",
                now_iso(),
            ),
        )
    conn.commit()


def list_legal_documents(conn) -> list[dict[str, Any]]:
    ensure_legal_documents(conn)
    rows = conn.execute(
        "SELECT doc_type, version, title, content_hash, effective_from FROM legal_documents ORDER BY doc_type"
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        path = legal_dir() / conn.execute(
            "SELECT file_path FROM legal_documents WHERE doc_type = ? AND version = ?",
            (r["doc_type"], r["version"]),
        ).fetchone()["file_path"]
        d["content"] = path.read_text(encoding="utf-8") if path.is_file() else ""
        out.append(d)
    return out


def validate_acceptances(acceptances: dict) -> None:
    missing = [k for k in DOC_TYPES if not acceptances.get(k)]
    if missing:
        raise ValueError("all legal documents must be accepted: " + ", ".join(missing))


def audit_log(conn, action: str, user_id: str = "", poi_id: str = "", details: Optional[dict] = None) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (id, action, user_id, poi_id, details_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(uuid.uuid4()), action, user_id or None, poi_id or None, json.dumps(details or {}), now_iso()),
    )


def blockchain_record(conn, user_id: str, payload: dict) -> dict:
    """Запись о регистрации пользователя (заглушка распределённого реестра)."""
    tx_hash = "0x" + hashlib.sha256(
        json.dumps({"user_id": user_id, **payload, "nonce": secrets.token_hex(8)}, sort_keys=True).encode()
    ).hexdigest()
    rid = str(uuid.uuid4())
    t = now_iso()
    conn.execute(
        """
        INSERT INTO blockchain_records (id, user_id, tx_hash, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (rid, user_id, tx_hash, json.dumps(payload), t),
    )
    return {"record_id": rid, "tx_hash": tx_hash, "created_at": t, "network": "cmir-ledger-stub"}
