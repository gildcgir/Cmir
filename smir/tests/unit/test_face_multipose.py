"""Тесты multi-pose enrollment + multi-face matching."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api_py"))
sys.path.insert(0, str(ROOT / "apps" / "face-worker"))
sys.path.insert(0, str(ROOT / "scripts"))

from e2e_helpers import multi_pose_embeddings, normalized_embedding  # noqa: E402
from face_profiles import REQUIRED_POSES, normalize_face_templates  # noqa: E402
from smir_face.embeddings import (  # noqa: E402
    MATCH_THRESHOLD,
    best_match_score,
    match_consented_face,
)
from store import PATCH_DIM, Store  # noqa: E402

DOC_OK = {
    "terms_of_service": True,
    "privacy_policy": True,
    "personal_data_consent": True,
    "biometric_data_consent": True,
    "wallet_agreement": True,
}


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("SMIR_ENV", "test")
    monkeypatch.setenv("SMIR_DATA_DIR", str(tmp_path))
    return Store()


def test_normalize_requires_five_poses():
    with pytest.raises(ValueError, match="need at least"):
        normalize_face_templates(normalized_embedding(), require_multi=True)


def test_normalize_multi_pose_ok():
    tpls = normalize_face_templates(None, multi_pose_embeddings(), require_multi=True)
    assert len(tpls) == 5
    assert {t["pose"] for t in tpls} == set(REQUIRED_POSES)


def test_kiosk_multi_pose_stores_templates(store):
    poi = store.create_poi({"name": "Pose Lab", "poi_type": "social_event", "latitude": 1, "longitude": 2})
    poses = multi_pose_embeddings(0.11)
    data = store.kiosk_register(
        poi.id,
        "Pose User",
        "+995599000111",
        "Кофе",
        poses[0]["embedding"],
        DOC_OK,
        embeddings=poses,
        require_multi=True,
    )
    assert data["consent"]["template_count"] == 5
    faces = store.global_consented_faces()
    me = next(f for f in faces if f["user_id"] == data["user_id"])
    assert len(me["embeddings"]) == 5
    assert len(me["templates"]) == 5
    assert {t["pose"] for t in me["templates"]} == set(REQUIRED_POSES)


def test_match_uses_angled_template_not_only_center():
    center = np.zeros(PATCH_DIM, dtype=np.float32)
    center[0] = 1.0
    left = np.zeros(PATCH_DIM, dtype=np.float32)
    left[10] = 1.0
    faces = [
        {
            "user_id": "u1",
            "display_name": "Алиса",
            "embedding": center.tolist(),
            "embeddings": [center.tolist(), left.tolist()],
            "templates": [
                {"pose": "center", "embedding": center.tolist()},
                {"pose": "left", "embedding": left.tolist()},
            ],
        }
    ]
    # probe looks like left pose — must still match via multi-template
    hit = match_consented_face(left, faces, threshold=0.99)
    assert hit is not None
    assert hit["display_name"] == "Алиса"
    assert best_match_score(left, faces[0]) == pytest.approx(1.0, abs=1e-5)


def test_match_many_simultaneous_faces_independent():
    a = np.zeros(PATCH_DIM, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(PATCH_DIM, dtype=np.float32)
    b[1] = 1.0
    stranger = np.zeros(PATCH_DIM, dtype=np.float32)
    stranger[2] = 1.0
    faces = [
        {"user_id": "a", "display_name": "A", "embeddings": [a.tolist()]},
        {"user_id": "b", "display_name": "B", "embeddings": [b.tolist()]},
    ]
    assert match_consented_face(a, faces, threshold=0.99)["user_id"] == "a"
    assert match_consented_face(b, faces, threshold=0.99)["user_id"] == "b"
    assert match_consented_face(stranger, faces, threshold=MATCH_THRESHOLD) is None


def test_revoke_removes_face_templates(store):
    poi = store.create_poi({"name": "Revoke Pose", "poi_type": "live_cam", "latitude": 1, "longitude": 2})
    poses = multi_pose_embeddings(0.2)
    data = store.kiosk_register(
        poi.id,
        "Temp",
        "+995599000222",
        "Чай",
        poses[0]["embedding"],
        DOC_OK,
        embeddings=poses,
        require_multi=True,
    )
    assert store.conn.execute(
        "SELECT COUNT(*) AS c FROM face_templates WHERE user_id = ?", (data["user_id"],)
    ).fetchone()["c"] == 5
    store.revoke_consent(poi.id, data["consent"]["id"], data["user_id"])
    assert store.conn.execute(
        "SELECT COUNT(*) AS c FROM face_templates WHERE user_id = ?", (data["user_id"],)
    ).fetchone()["c"] == 0
    faces = store.global_consented_faces()
    assert not any(f["user_id"] == data["user_id"] for f in faces)
