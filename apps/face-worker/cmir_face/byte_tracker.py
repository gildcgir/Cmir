"""
Lightweight ByteTrack-style association + EMA / Kalman-ish coasting for face boxes + keypoints.

High-score detections claim tracks first; low-score detections fill unmatched tracks.
Missed tracks coast with velocity so masks do not flicker off for a frame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from cmir_face.scrfd_detector import FaceHit, pad_box

Box = Tuple[int, int, int, int]


def _iou(a: Box, b: Box) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter <= 0:
        return 0.0
    return inter / float(aw * ah + bw * bh - inter)


def _center(b: Box) -> Tuple[float, float]:
    x, y, w, h = b
    return x + w / 2.0, y + h / 2.0


def _clamp_box(x: int, y: int, bw: int, bh: int, fw: int, fh: int) -> Box:
    bw, bh = max(8, bw), max(8, bh)
    x = max(0, min(int(x), fw - 1))
    y = max(0, min(int(y), fh - 1))
    return x, y, min(bw, fw - x), min(bh, fh - y)


def _ema_box(old: Box, new: Box, pos_a: float, size_a: float, fw: int, fh: int) -> Box:
    ox, oy, ow, oh = old
    nx, ny, nw, nh = new
    ocx, ocy = ox + ow / 2.0, oy + oh / 2.0
    ncx, ncy = nx + nw / 2.0, ny + nh / 2.0
    cx = pos_a * ncx + (1 - pos_a) * ocx
    cy = pos_a * ncy + (1 - pos_a) * ocy
    w = size_a * nw + (1 - size_a) * ow
    h = size_a * nh + (1 - size_a) * oh
    return _clamp_box(int(cx - w / 2), int(cy - h / 2), int(w), int(h), fw, fh)


def _ema_kps(old: Optional[np.ndarray], new: Optional[np.ndarray], a: float) -> Optional[np.ndarray]:
    if new is None:
        return old.copy() if old is not None else None
    new = np.asarray(new, dtype=np.float32).reshape(-1, 2)
    if old is None:
        return new.copy()
    old = np.asarray(old, dtype=np.float32).reshape(-1, 2)
    n = min(len(old), len(new))
    out = new.copy()
    out[:n] = a * new[:n] + (1 - a) * old[:n]
    return out


@dataclass
class TrackedFace:
    track_id: int
    box: Box
    smooth: Box
    score: float = 1.0
    kps: Optional[np.ndarray] = None
    smooth_kps: Optional[np.ndarray] = None
    embedding: Optional[np.ndarray] = None
    missed: int = 0
    age: int = 0
    vx: float = 0.0
    vy: float = 0.0
    hits: int = 1


@dataclass
class ByteFaceTracker:
    """ByteTrack-inspired multi-face tracker with EMA smoothing."""

    pos_smooth: float = 0.45
    size_smooth: float = 0.32
    kps_smooth: float = 0.5
    high_thresh: float = 0.45
    low_thresh: float = 0.22
    match_iou: float = 0.15
    max_missed: int = 22
    bbox_pad: float = 0.2
    _next_id: int = 1
    _tracks: List[TrackedFace] = field(default_factory=list)
    _fw: int = 0
    _fh: int = 0

    def _match(self, tracks: List[TrackedFace], dets: List[FaceHit], iou_thr: float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        if not tracks or not dets:
            return [], list(range(len(tracks))), list(range(len(dets)))
        pairs: List[Tuple[float, int, int]] = []
        for ti, tr in enumerate(tracks):
            for di, det in enumerate(dets):
                score = _iou(tr.smooth, det.bbox)
                if score < iou_thr:
                    tcx, tcy = _center(tr.smooth)
                    dcx, dcy = _center(det.bbox)
                    dist = ((tcx - dcx) ** 2 + (tcy - dcy) ** 2) ** 0.5
                    if dist < max(tr.smooth[2], 24) * 0.65:
                        score = max(score, 0.22)
                pairs.append((score, ti, di))
        pairs.sort(reverse=True)
        used_t, used_d = set(), set()
        matches: List[Tuple[int, int]] = []
        min_accept = min(iou_thr, 0.2)
        for score, ti, di in pairs:
            if score < min_accept:
                continue
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            matches.append((ti, di))
        u_t = [i for i in range(len(tracks)) if i not in used_t]
        u_d = [i for i in range(len(dets)) if i not in used_d]
        return matches, u_t, u_d

    def _update_track(self, tr: TrackedFace, det: FaceHit) -> None:
        old_c = _center(tr.smooth)
        tr.box = det.bbox
        tr.smooth = _ema_box(tr.smooth, det.bbox, self.pos_smooth, self.size_smooth, self._fw, self._fh)
        new_c = _center(tr.smooth)
        tr.vx = 0.65 * (new_c[0] - old_c[0]) + 0.35 * tr.vx
        tr.vy = 0.65 * (new_c[1] - old_c[1]) + 0.35 * tr.vy
        tr.score = det.score
        tr.kps = det.kps
        tr.smooth_kps = _ema_kps(tr.smooth_kps, det.kps, self.kps_smooth)
        if det.embedding is not None:
            tr.embedding = det.embedding
        tr.missed = 0
        tr.age += 1
        tr.hits += 1

    def _coast(self, tr: TrackedFace) -> None:
        tr.missed += 1
        x, y, w, h = tr.smooth
        cx, cy = x + w / 2.0 + tr.vx, y + h / 2.0 + tr.vy
        # slight inflate while lost — privacy fail-safe
        grow = 1.0 + min(0.35, tr.missed * 0.025)
        nw, nh = int(w * grow), int(h * grow)
        tr.smooth = _clamp_box(int(cx - nw / 2), int(cy - nh / 2), nw, nh, self._fw, self._fh)
        tr.vx *= 0.88
        tr.vy *= 0.88
        if tr.smooth_kps is not None:
            tr.smooth_kps = tr.smooth_kps.copy()
            tr.smooth_kps[:, 0] += tr.vx
            tr.smooth_kps[:, 1] += tr.vy

    def update(self, hits: Sequence[FaceHit], frame_w: int, frame_h: int) -> List[TrackedFace]:
        self._fw, self._fh = frame_w, frame_h
        dets = [
            FaceHit(
                bbox=_clamp_box(*h.bbox, frame_w, frame_h),
                score=h.score,
                kps=h.kps,
                embedding=h.embedding,
            )
            for h in hits
        ]
        high = [d for d in dets if d.score >= self.high_thresh]
        low = [d for d in dets if self.low_thresh <= d.score < self.high_thresh]

        touched: set[int] = set()

        matches_h, u_t, u_d_h = self._match(self._tracks, high, self.match_iou)
        for ti, di in matches_h:
            self._update_track(self._tracks[ti], high[di])
            touched.add(id(self._tracks[ti]))

        unmatched_tracks = [self._tracks[i] for i in u_t]
        matches_l, _, _ = self._match(unmatched_tracks, low, max(0.1, self.match_iou - 0.05))
        for local_i, di in matches_l:
            tr = unmatched_tracks[local_i]
            self._update_track(tr, low[di])
            touched.add(id(tr))

        for tr in self._tracks:
            if id(tr) not in touched:
                self._coast(tr)

        for di in u_d_h:
            det = high[di]
            box = det.bbox
            tr = TrackedFace(
                track_id=self._next_id,
                box=box,
                smooth=box,
                score=det.score,
                kps=det.kps,
                smooth_kps=None if det.kps is None else np.asarray(det.kps, dtype=np.float32).copy(),
                embedding=det.embedding,
            )
            self._next_id += 1
            self._tracks.append(tr)

        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return list(self._tracks)

    def padded_boxes(self, tracks: Optional[Sequence[TrackedFace]] = None) -> List[Box]:
        tracks = tracks if tracks is not None else self._tracks
        return [pad_box(t.smooth, self.bbox_pad, self._fw, self._fh) for t in tracks]
