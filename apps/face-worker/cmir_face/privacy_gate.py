"""Задержанный выход: кадр анализируется и маскируется до попадания в поток."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Tuple

import numpy as np

Box = Tuple[int, int, int, int]


@dataclass
class TrackedFace:
    box: Box
    ttl: int = 8


@dataclass
class PrivacyGate:
    """Держит кадры в буфере, на выход — детекция + маска (fail-safe)."""

    delay_frames: int = 24
    face_ttl: int = 10
    expand: float = 1.15
    _raw: Deque[np.ndarray] = field(default_factory=deque)
    _tracks: List[TrackedFace] = field(default_factory=list)

    def ingest(self, frame: np.ndarray) -> List[np.ndarray]:
        """Принять кадр; вернуть кадры, готовые к публикации."""
        self._raw.append(frame.copy())
        out: List[np.ndarray] = []
        while len(self._raw) > self.delay_frames:
            out.append(self._raw.popleft())
        return out

    def expand_box(self, x: int, y: int, bw: int, bh: int, w: int, h: int) -> Box:
        cx, cy = x + bw / 2, y + bh / 2
        bw2 = int(bw * self.expand)
        bh2 = int(bh * self.expand)
        nx = int(cx - bw2 / 2)
        ny = int(cy - bh2 / 2)
        nx = max(0, min(nx, w - 1))
        ny = max(0, min(ny, h - 1))
        return nx, ny, min(bw2, w - nx), min(bh2, h - ny)

    def update_tracks(self, boxes: List[Box]) -> List[Box]:
        if boxes:
            self._tracks = [TrackedFace(box=b, ttl=self.face_ttl) for b in boxes]
        else:
            for t in self._tracks:
                t.ttl -= 1
            self._tracks = [t for t in self._tracks if t.ttl > 0]
        return [t.box for t in self._tracks]

    def flush(self) -> List[np.ndarray]:
        out = list(self._raw)
        self._raw.clear()
        return out
