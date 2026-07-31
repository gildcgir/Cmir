"""Stylized static emoji avatars for privacy overlay."""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

EMOJI_IDS = ("stylized", "cool", "grin", "smile", "neutral")
_CACHE: Dict[Tuple[str, int], np.ndarray] = {}

# Между компактным (≈1.0) и крупным (≈1.82): закрывает лицо без «шлема»
DEFAULT_OVERLAY_SCALE = 1.48


def _draw_stylized_mascot(size: int) -> np.ndarray:
    """Стикер-стиль: градиент, обводка, звёздные глаза, улыбка с языком."""
    import cv2

    img = np.zeros((size, size, 4), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    r = int(size * 0.44)

    # мягкий градиент (оранжево-жёлтый)
    for y in range(size):
        t = y / max(size - 1, 1)
        col = (
            int(70 + 40 * t),
            int(190 + 30 * t),
            int(255 - 20 * t),
            255,
        )
        cv2.ellipse(img, (cx, cy), (r, r), 0, 0, 360, col, -1, lineType=cv2.LINE_AA)

    # блик
    cv2.ellipse(
        img,
        (cx - r // 3, cy - r // 3),
        (r // 3, r // 4),
        0,
        0,
        360,
        (200, 240, 255, 255),
        -1,
        lineType=cv2.LINE_AA,
    )

    # толстая обводка
    cv2.circle(img, (cx, cy), r, (20, 80, 160, 255), max(3, size // 32), lineType=cv2.LINE_AA)
    cv2.circle(img, (cx, cy), r - 2, (40, 120, 200, 255), 1, lineType=cv2.LINE_AA)

    # румянец
    cheek_y = cy + int(size * 0.05)
    for dx in (-int(size * 0.22), int(size * 0.22)):
        cv2.ellipse(
            img,
            (cx + dx, cheek_y),
            (int(size * 0.07), int(size * 0.05)),
            0,
            0,
            360,
            (120, 140, 255, 255),
            -1,
            lineType=cv2.LINE_AA,
        )

    # звёздные глаза
    eye_y = cy - int(size * 0.1)
    eye_dx = int(size * 0.17)

    def star(ex: int, ey: int, rad: int) -> None:
        pts = []
        for i in range(10):
            ang = i * np.pi / 5 - np.pi / 2
            rr = rad if i % 2 == 0 else rad * 0.45
            pts.append([int(ex + rr * np.cos(ang)), int(ey + rr * np.sin(ang))])
        cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], (30, 30, 40, 255), lineType=cv2.LINE_AA)
        cv2.circle(img, (ex, ey), max(2, rad // 3), (255, 255, 255, 255), -1, lineType=cv2.LINE_AA)

    star(cx - eye_dx, eye_y, int(size * 0.065))
    star(cx + eye_dx, eye_y, int(size * 0.065))

    # рот + язык
    mouth_y = cy + int(size * 0.16)
    cv2.ellipse(
        img,
        (cx, mouth_y),
        (int(size * 0.2), int(size * 0.11)),
        0,
        0,
        180,
        (40, 30, 30, 255),
        -1,
        lineType=cv2.LINE_AA,
    )
    cv2.ellipse(
        img,
        (cx, mouth_y + int(size * 0.06)),
        (int(size * 0.07), int(size * 0.05)),
        0,
        0,
        180,
        (80, 100, 255, 255),
        -1,
        lineType=cv2.LINE_AA,
    )
    return img


def _draw_vector_smiley(size: int, style: str) -> np.ndarray:
    if style == "stylized":
        return _draw_stylized_mascot(size)
    import cv2

    img = np.zeros((size, size, 4), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    r = int(size * 0.46)
    cv2.circle(img, (cx, cy), r, (80, 210, 255, 255), -1, lineType=cv2.LINE_AA)
    return img


def get_sprite(emoji_id: str = "stylized", size: int = 384) -> np.ndarray:
    emoji_id = emoji_id if emoji_id in EMOJI_IDS else "stylized"
    key = (emoji_id, size)
    if key in _CACHE:
        return _CACHE[key]
    sprite = _draw_vector_smiley(size, emoji_id)
    _CACHE[key] = sprite
    return sprite


def overlay_sprite(
    frame: np.ndarray,
    x: int,
    y: int,
    bw: int,
    bh: int,
    sprite: np.ndarray,
    scale: float = DEFAULT_OVERLAY_SCALE,
) -> None:
    """Непрозрачный оверлей: сплошной диск + жёсткая маска спрайта (лицо не просвечивает)."""
    import cv2

    fh, fw = frame.shape[:2]
    base = max(bw, bh, 28)
    side = int(base * scale)
    resized = cv2.resize(sprite, (side, side), interpolation=cv2.INTER_LINEAR)

    cx = x + bw // 2
    cy = y + int(bh * 0.46)
    x1, y1 = cx - side // 2, cy - side // 2
    x2, y2 = x1 + side, y1 + side

    if x2 <= 0 or y2 <= 0 or x1 >= fw or y1 >= fh:
        return

    # Сплошной фон под маской — закрывает лицо даже в прозрачных зонах спрайта
    backing_r = max(12, int(side * 0.44))
    cv2.circle(
        frame,
        (cx, cy),
        backing_r,
        (55, 175, 250),
        -1,
        lineType=cv2.LINE_AA,
    )

    sx1, sy1 = max(0, -x1), max(0, -y1)
    dx1, dy1 = max(0, x1), max(0, y1)
    sx2 = sx1 + min(fw, x2) - dx1
    sy2 = sy1 + min(fh, y2) - dy1
    if sx2 <= sx1 or sy2 <= sy1:
        return

    patch = resized[sy1:sy2, sx1:sx2]
    roi = frame[dy1 : dy1 + patch.shape[0], dx1 : dx1 + patch.shape[1]]
    if patch.shape[2] == 4:
        alpha = patch[:, :, 3]
        bgr = patch[:, :, :3]
        mask = alpha > 20
        roi[mask] = bgr[mask]
    else:
        roi[:] = patch
