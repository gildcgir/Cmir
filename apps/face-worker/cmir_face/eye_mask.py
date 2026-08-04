"""Одна чёрная плашка на лицо / глаза — keypoints (MediaPipe или SCRFD)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math

import numpy as np

Box = Tuple[int, int, int, int]


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(12, bw), max(10, bh)
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def eye_bar_from_kps(
    kps: np.ndarray,
    frame_w: int,
    frame_h: int,
    pad: float = 0.22,
) -> Tuple[Tuple[float, float], float, float, float]:
    """
    Returns (center_xy, width, height, angle_rad) for a rotated eye bar.
    Uses left/right eye keypoints; pad expands size for profile fail-safe.
    """
    pts = np.asarray(kps, dtype=np.float32).reshape(-1, 2)
    if len(pts) < 2:
        raise ValueError("need eye keypoints")
    p0, p1 = pts[0], pts[1]
    if p0[0] <= p1[0]:
        left, right = p0, p1
    else:
        left, right = p1, p0
    dx, dy = float(right[0] - left[0]), float(right[1] - left[1])
    eye_dist = math.hypot(dx, dy) or 1.0
    angle = math.atan2(dy, dx)
    cx = (left[0] + right[0]) / 2.0
    cy = (left[1] + right[1]) / 2.0
    scale = 1.0 + max(0.0, pad)
    bar_w = max(28.0, eye_dist * 1.55 * scale)
    bar_h = max(16.0, bar_w * 0.48)
    cy -= bar_h * 0.06
    return (cx, cy), bar_w, bar_h, angle


def draw_rotated_eye_bar(
    frame,
    kps: np.ndarray,
    pad: float = 0.22,
    color: Tuple[int, int, int] = (0, 0, 0),
) -> bool:
    """Affine / rotated solid bar covering both eyes. Returns True if drawn."""
    import cv2

    fh, fw = frame.shape[:2]
    try:
        (cx, cy), bar_w, bar_h, angle = eye_bar_from_kps(kps, fw, fh, pad=pad)
    except Exception:
        return False
    rect = ((cx, cy), (bar_w, bar_h), math.degrees(angle))
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    cv2.fillConvexPoly(frame, box, color)
    pts = np.asarray(kps, dtype=np.float32).reshape(-1, 2)
    p0, p1 = pts[0], pts[1]
    thickness = max(8, int(bar_h * 0.55))
    cv2.line(
        frame,
        (int(p0[0]), int(p0[1])),
        (int(p1[0]), int(p1[1])),
        color,
        thickness=thickness,
        lineType=cv2.LINE_AA,
    )
    return True


def draw_eye_privacy(
    frame,
    bbox: Box,
    kps: Optional[np.ndarray] = None,
    pad: float = 0.22,
) -> None:
    """Prefer keypoint-aligned bar; fall back to horizontal box over upper face."""
    import cv2

    if kps is not None and len(np.asarray(kps).reshape(-1, 2)) >= 2:
        if draw_rotated_eye_bar(frame, kps, pad=pad):
            return
    x, y, bw, bh = bbox
    bar_y = y + int(bh * 0.22)
    bar_h = max(16, int(bh * 0.38 * (1 + pad)))
    bar_x = max(0, x - int(bw * pad * 0.5))
    bar_w = min(frame.shape[1] - bar_x, int(bw * (1 + pad)))
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 0, 0), thickness=-1)


def eye_rects_from_detection(det, frame_w: int, frame_h: int) -> List[Box]:
    """Два чёрных прямоугольника на глаза."""
    loc = det.location_data
    kps = loc.relative_keypoints
    w, h = frame_w, frame_h
    rb = loc.relative_bounding_box
    rects: List[Box] = []

    if len(kps) >= 2:
        eyes = [(kps[0].x * w, kps[0].y * h), (kps[1].x * w, kps[1].y * h)]
        rx, ry = eyes[0]
        lx, ly = eyes[1]
        eye_dist = math.hypot(lx - rx, ly - ry)
        ew = max(14, int(eye_dist * 0.42))
        eh = max(10, int(ew * 0.55))
        for ex, ey in eyes:
            rects.append(_clamp_box(int(ex - ew / 2), int(ey - eh / 2), ew, eh, w, h))
        return rects

    bx, by = int(rb.xmin * w), int(rb.ymin * h)
    bw, bh = int(rb.width * w), int(rb.height * h)
    ew, eh = max(14, bw // 5), max(10, bh // 8)
    rects.append(_clamp_box(bx + bw // 4 - ew // 2, by + bh // 3, ew, eh, w, h))
    rects.append(_clamp_box(bx + 3 * bw // 4 - ew // 2, by + bh // 3, ew, eh, w, h))
    return rects


def eye_rects_from_detections(detections, frame_w: int, frame_h: int) -> List[Box]:
    out: List[Box] = []
    for det in detections:
        out.extend(eye_rects_from_detection(det, frame_w, frame_h))
    return out


def draw_eye_rects(frame, rects: List[Box]) -> None:
    import cv2

    for x, y, bw, bh in rects:
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)


def draw_mask_image(frame, bar: Box, image_bgra) -> None:
    """Наложить картинку маски вместо чёрного прямоугольника."""
    import cv2

    x, y, bw, bh = bar
    if image_bgra is None or bw < 4 or bh < 4:
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)
        return
    resized = cv2.resize(image_bgra, (bw, bh), interpolation=cv2.INTER_AREA)
    if resized.shape[2] == 4:
        alpha = resized[:, :, 3:4] / 255.0
        roi = frame[y : y + bh, x : x + bw]
        if roi.shape[0] == bh and roi.shape[1] == bw:
            blended = (alpha * resized[:, :, :3] + (1 - alpha) * roi).astype(np.uint8)
            frame[y : y + bh, x : x + bw] = blended
    else:
        frame[y : y + bh, x : x + bw] = resized[:, :, :3]


def face_bar_from_detection(det, frame_w: int, frame_h: int) -> Box | None:
    """
    Горизонтальная плашка по центру лица: закрывает глаза и верхнюю часть лица.
    """
    loc = det.location_data
    kps = loc.relative_keypoints
    w, h = frame_w, frame_h
    rb = loc.relative_bounding_box

    if len(kps) >= 2:
        rx, ry = kps[0].x * w, kps[0].y * h
        lx, ly = kps[1].x * w, kps[1].y * h
        eye_dist = math.hypot(lx - rx, ly - ry)
        cx = (rx + lx) / 2
        cy = (ry + ly) / 2
    else:
        bx, by = int(rb.xmin * w), int(rb.ymin * h)
        bw, bh = int(rb.width * w), int(rb.height * h)
        eye_dist = bw * 0.55
        cx = bx + bw / 2
        cy = by + bh * 0.42

    if eye_dist < 10:
        bw = max(int(rb.width * w), 48)
        eye_dist = bw * 0.55
        cx = int(rb.xmin * w) + bw / 2
        cy = int(rb.ymin * h) + int(rb.height * h) * 0.42

    bar_w = max(36, int(eye_dist * 1.28))
    bar_h = max(22, int(bar_w * 0.52))
    cy = cy - bar_h * 0.08

    return _clamp_box(int(cx - bar_w / 2), int(cy - bar_h / 2), bar_w, bar_h, w, h)


def face_bars_from_detections(detections, frame_w: int, frame_h: int) -> List[Box]:
    out: List[Box] = []
    for det in detections:
        bar = face_bar_from_detection(det, frame_w, frame_h)
        if bar:
            out.append(bar)
    return out


def draw_face_bar(frame, bar: Box) -> None:
    import cv2

    x, y, bw, bh = bar
    cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 0), thickness=-1)


def bbox_from_detection(det, frame_w: int, frame_h: int) -> Box:
    rb = det.location_data.relative_bounding_box
    w, h = frame_w, frame_h
    x = int(rb.xmin * w)
    y = int(rb.ymin * h)
    bw = int(rb.width * w)
    bh = int(rb.height * h)
    return _clamp_box(x, y, bw, bh, w, h)


@dataclass
class _BarTrack:
    box: Box
    missed: int = 0
    smooth: Box = field(default_factory=lambda: (0, 0, 0, 0))

    def __post_init__(self) -> None:
        self.smooth = self.box

    @property
    def center(self) -> Tuple[float, float]:
        x, y, bw, bh = self.smooth
        return x + bw / 2, y + bh / 2


class FaceBarTracker:
    """Сглаживание одной плашки на лицо."""

    def __init__(self, pos_smooth: float = 0.55, size_smooth: float = 0.35, max_missed: int = 15) -> None:
        self.pos_smooth = pos_smooth
        self.size_smooth = size_smooth
        self.max_missed = max_missed
        self._tracks: List[_BarTrack] = []
        self._fw = 0
        self._fh = 0

    def _smooth_box(self, old: Box, new: Box) -> Box:
        ox, oy, ow, oh = old
        nx, ny, nw, nh = new
        ap, az = self.pos_smooth, self.size_smooth
        cx = int(ap * (nx + nw / 2) + (1 - ap) * (ox + ow / 2))
        cy = int(ap * (ny + nh / 2) + (1 - ap) * (oy + oh / 2))
        nw2 = int(az * nw + (1 - az) * ow)
        nh2 = int(az * nh + (1 - az) * oh)
        return _clamp_box(cx - nw2 // 2, cy - nh2 // 2, nw2, nh2, self._fw, self._fh)

    def update(self, bars: List[Box], frame_w: int, frame_h: int) -> List[Box]:
        self._fw, self._fh = frame_w, frame_h
        used = [False] * len(bars)

        for track in self._tracks:
            tcx, tcy = track.center
            best_i, best_d = -1, 1e9
            for i, bar in enumerate(bars):
                if used[i]:
                    continue
                bx, by, bw, bh = bar
                cx, cy = bx + bw / 2, by + bh / 2
                d = math.hypot(cx - tcx, cy - tcy)
                if d < best_d:
                    best_d, best_i = d, i

            max_d = max(frame_w, frame_h) * 0.14
            if best_i >= 0 and best_d < max_d:
                used[best_i] = True
                track.box = bars[best_i]
                track.smooth = self._smooth_box(track.smooth, track.box)
                track.missed = 0
            else:
                track.missed += 1

        for i, bar in enumerate(bars):
            if not used[i]:
                t = _BarTrack(box=bar)
                t.smooth = bar
                self._tracks.append(t)

        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return [t.smooth for t in self._tracks]
