"""POC + multi-pose face signatures for consent matching.

Matching: best cosine score across all enrolled pose templates per user.
Patch pipeline uses histogram equalization for lighting robustness.
Optional InsightFace/ArcFace can be wired later; multi-pose templates are
the primary fix for angled heads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

PATCH_SIZE = 32
MATCH_THRESHOLD = 0.82  # multi-pose templates allow slightly lower than single-pose 0.85
CONSENT_CAM_THRESHOLD = 0.88
HOLD_FRAMES = 18  # hysteresis: keep consented after a hit to avoid flicker masks


def patch_from_bbox(frame: np.ndarray, x: int, y: int, bw: int, bh: int) -> np.ndarray:
    """Extract normalized grayscale signature from face bounding box."""
    h, w = frame.shape[:2]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w, x + bw)
    y2 = min(h, y + bh)
    if x2 <= x1 or y2 <= y1:
        return np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    crop = frame[y1:y2, x1:x2]
    import cv2

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        gray = clahe.apply(gray)
    except Exception:
        gray = cv2.equalizeHist(gray)
    resized = cv2.resize(gray, (PATCH_SIZE, PATCH_SIZE))
    vec = resized.astype(np.float32).flatten() / 255.0
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec /= norm
    return vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return 0.0
    return float(np.dot(a, b))


def _vectors_for_face(face: dict) -> List[np.ndarray]:
    out: List[np.ndarray] = []
    for key in ("embeddings",):
        for item in face.get(key) or []:
            vec = np.array(item, dtype=np.float32)
            if vec.size == PATCH_SIZE * PATCH_SIZE:
                n = np.linalg.norm(vec)
                out.append(vec / n if n > 1e-6 else vec)
    for tpl in face.get("templates") or []:
        raw = tpl.get("embedding") if isinstance(tpl, dict) else tpl
        vec = np.array(raw or [], dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            n = np.linalg.norm(vec)
            out.append(vec / n if n > 1e-6 else vec)
    if not out and face.get("embedding") is not None:
        vec = np.array(face.get("embedding") or [], dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            n = np.linalg.norm(vec)
            out.append(vec / n if n > 1e-6 else vec)
    return out


def best_match_score(signature: np.ndarray, face: dict) -> float:
    best = 0.0
    for vec in _vectors_for_face(face):
        best = max(best, cosine_similarity(signature, vec))
    return best


def is_consented(
    signature: np.ndarray,
    consented: Sequence,
    threshold: float = MATCH_THRESHOLD,
) -> bool:
    faces: List[dict] = []
    for item in consented:
        if isinstance(item, dict):
            faces.append(item)
        else:
            faces.append({"embedding": np.asarray(item, dtype=np.float32).tolist()})
    return match_consented_face(signature, faces, threshold=threshold) is not None


def load_embeddings_json(path: str) -> List[np.ndarray]:
    p = Path(path)
    if not p.is_file():
        return []
    data = json.loads(p.read_text())
    out: List[np.ndarray] = []
    for item in data.get("embeddings", []):
        vec = np.array(item, dtype=np.float32)
        if vec.size == PATCH_SIZE * PATCH_SIZE:
            out.append(vec)
    return out


def match_consented_name(
    signature: np.ndarray,
    faces: List[dict],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[str]:
    hit = match_consented_face(signature, faces, threshold=threshold)
    return hit.get("display_name") if hit else None


def match_consented_face(
    signature: np.ndarray,
    faces: List[dict],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[dict]:
    """Best-of-all-pose-templates per user; supports many simultaneous faces."""
    best = None
    best_score = threshold
    for face in faces:
        score = best_match_score(signature, face)
        if score >= best_score:
            best_score = score
            best = {**face, "match_score": score}
    return best


def post_face_presence(api_url: str, camera_id: str, presence: List[dict], worker_token: str = "") -> None:
    """Отчёт секунд присутствия в кадре (face-worker → API)."""
    if not api_url or not camera_id or not presence:
        return
    try:
        import urllib.request

        payload = json.dumps({"camera_id": camera_id, "presence": presence}).encode()
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/api/v1/face-presence",
            data=payload,
            headers={
                "Content-Type": "application/json",
                **({"X-Smir-Worker": worker_token} if worker_token else {}),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
    except Exception as e:
        print(f"Warning: face-presence report failed: {e}")


def fetch_consented_faces_from_api(api_url: str) -> List[dict]:
    try:
        import urllib.request

        url = f"{api_url.rstrip('/')}/api/v1/consented-faces"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return list(data.get("data", {}).get("faces", []))
    except Exception as e:
        print(f"Warning: could not fetch consented faces: {e}")
        return []


def fetch_embeddings_from_api(api_url: str, poi_id: str) -> List[np.ndarray]:
    try:
        import urllib.request

        url = f"{api_url.rstrip('/')}/api/v1/pois/{poi_id}/embeddings"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        out: List[np.ndarray] = []
        for item in data.get("data", {}).get("embeddings", []):
            vec = np.array(item, dtype=np.float32)
            if vec.size == PATCH_SIZE * PATCH_SIZE:
                out.append(vec)
        return out
    except Exception as e:
        print(f"Warning: could not fetch embeddings: {e}")
        return []
