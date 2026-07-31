"""Stable face tracking: IoU + center distance, separate position/size smoothing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import math

Box = Tuple[int, int, int, int]


def _iou(a: Box, b: Box) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    return inter / (aw * ah + bw * bh - inter)


def _center(b: Box) -> Tuple[float, float]:
    x, y, w, h = b
    return x + w / 2, y + h / 2


def _center_dist(a: Box, b: Box) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return math.hypot(ax - bx, ay - by)


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(20, bw), max(20, bh)
    x, y = max(0, min(x, fw - 1)), max(0, min(y, fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


@dataclass
class _Track:
    box: Box
    missed: int = 0
    age: int = 0
    smooth: Box = field(default_factory=lambda: (0, 0, 0, 0))

    def __post_init__(self) -> None:
        self.smooth = self.box


class FaceTracker:
    def __init__(
        self,
        pos_smooth: float = 0.42,
        size_smooth: float = 0.28,
        iou_match: float = 0.08,
        center_match_ratio: float = 0.55,
        max_missed: int = 18,
    ) -> None:
        self.pos_smooth = pos_smooth
        self.size_smooth = size_smooth
        self.iou_match = iou_match
        self.center_match_ratio = center_match_ratio
        self.max_missed = max_missed
        self._tracks: List[_Track] = []
        self._fw = 0
        self._fh = 0

    def _match_score(self, track: _Track, det: Box) -> float:
        iou = _iou(track.smooth, det)
        if iou >= self.iou_match:
            return iou + 0.5
        tw = track.smooth[2]
        dist = _center_dist(track.smooth, det)
        if tw > 0 and dist < tw * self.center_match_ratio:
            return 0.4 + iou
        return iou

    def _smooth_box(self, old: Box, new: Box) -> Box:
        ox, oy, ow, oh = old
        nx, ny, nw, nh = new
        ap, az = self.pos_smooth, self.size_smooth
        cx = int(ap * (nx + nw / 2) + (1 - ap) * (ox + ow / 2))
        cy = int(ap * (ny + nh / 2) + (1 - ap) * (oy + oh / 2))
        nw2 = int(az * nw + (1 - az) * ow)
        nh2 = int(az * nh + (1 - az) * oh)
        return _clamp_box(cx - nw2 // 2, cy - nh2 // 2, nw2, nh2, self._fw, self._fh)

    def update(self, detections: List[Box], frame_w: int, frame_h: int) -> List[Box]:
        self._fw, self._fh = frame_w, frame_h
        dets = [_clamp_box(*d, frame_w, frame_h) for d in detections]
        used = [False] * len(dets)

        for track in self._tracks:
            best_i, best_s = -1, 0.0
            for i, det in enumerate(dets):
                if used[i]:
                    continue
                s = self._match_score(track, det)
                if s > best_s:
                    best_s, best_i = s, i
            if best_i >= 0 and best_s >= 0.35:
                used[best_i] = True
                track.box = dets[best_i]
                track.smooth = self._smooth_box(track.smooth, track.box)
                track.missed = 0
                track.age += 1
            else:
                track.missed += 1

        for i, det in enumerate(dets):
            if not used[i]:
                t = _Track(box=det)
                t.smooth = det
                self._tracks.append(t)

        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return [t.smooth for t in self._tracks]
