"""Multi-pose face enrollment helpers (shared validation + normalize)."""
from __future__ import annotations

from typing import Any, List, Optional

PATCH_DIM = 32 * 32
REQUIRED_POSES = ("center", "left", "right", "up", "down")
MIN_TEMPLATES = 5


def _valid_vec(vec: Any) -> Optional[List[float]]:
    if not isinstance(vec, list) or len(vec) != PATCH_DIM:
        return None
    try:
        out = [float(x) for x in vec]
    except (TypeError, ValueError):
        return None
    return out


def normalize_face_templates(
    face_embedding: Any = None,
    face_embeddings: Any = None,
    *,
    require_multi: bool = False,
) -> List[dict]:
    """
    Приводит вход киоска к списку шаблонов:
    [{pose, embedding, yaw, pitch}, ...]
    """
    templates: List[dict] = []

    if isinstance(face_embeddings, list) and face_embeddings:
        for i, item in enumerate(face_embeddings):
            if isinstance(item, dict):
                vec = _valid_vec(item.get("embedding") or item.get("face_embedding"))
                pose = str(item.get("pose") or REQUIRED_POSES[min(i, len(REQUIRED_POSES) - 1)])
                yaw = item.get("yaw")
                pitch = item.get("pitch")
            else:
                vec = _valid_vec(item)
                pose = REQUIRED_POSES[min(i, len(REQUIRED_POSES) - 1)]
                yaw = pitch = None
            if not vec:
                continue
            templates.append(
                {
                    "pose": pose.lower().strip() or "center",
                    "embedding": vec,
                    "yaw": float(yaw) if yaw is not None else None,
                    "pitch": float(pitch) if pitch is not None else None,
                }
            )

    if not templates:
        vec = _valid_vec(face_embedding)
        if vec:
            templates.append({"pose": "center", "embedding": vec, "yaw": 0.0, "pitch": 0.0})

    if require_multi:
        poses = {t["pose"] for t in templates}
        missing = [p for p in REQUIRED_POSES if p not in poses]
        if len(templates) < MIN_TEMPLATES:
            raise ValueError(
                f"need at least {MIN_TEMPLATES} face poses (center/left/right/up/down), got {len(templates)}"
            )
        if missing:
            raise ValueError(f"missing face poses: {', '.join(missing)}")

    if not templates:
        raise ValueError(f"face_embedding must be {PATCH_DIM} floats or face_embeddings multi-pose list")

    return templates
