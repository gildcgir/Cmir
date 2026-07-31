"""Одна чёрная плашка на лицо (полицейская хроника) — keypoints MediaPipe."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import math

Box = Tuple[int, int, int, int]


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(12, bw), max(10, bh)
    x = max(0, min(x, fw - 1))
    y = max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


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
    import numpy as np

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
    Ширина ~1.25× расстояние между глазами, высота ~0.55× ширины.
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
    # чуть выше центра глаз — типичная «хроника»
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
