#!/usr/bin/env python3
"""Generate a short demo video with a moving 'face' region for Phase 0 POC."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/ingest/samples/demo.mp4"
W, H, FPS, SECONDS = 640, 480, 25, 8


def frames():
    total = FPS * SECONDS
    for i in range(total):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = (40, 45, 55)
        t = i / max(total - 1, 1)
        cx = int(W * (0.25 + 0.5 * t))
        cy = H // 2
        cv2.ellipse(frame, (cx, cy), (55, 70), 0, 0, 360, (220, 180, 140), -1)
        cv2.circle(frame, (cx - 20, cy - 25), 8, (30, 30, 30), -1)
        cv2.circle(frame, (cx + 20, cy - 25), 8, (30, 30, 30), -1)
        cv2.ellipse(frame, (cx, cy + 15), (18, 10), 0, 0, 180, (80, 50, 50), 2)
        cv2.putText(
            frame,
            "Cmir demo feed",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2,
        )
        yield frame


def write_mp4(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import imageio.v3 as iio

        iio.imwrite(path, list(frames()), fps=FPS, codec="libx264")
        if path.is_file() and path.stat().st_size > 0:
            return
    except Exception as e:
        print(f"imageio mp4 failed ({e}), trying AVI…", file=sys.stderr)

    avi = path.with_suffix(".avi")
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(avi), fourcc, FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError("Cannot open video writer")
    for frame in frames():
        writer.write(frame)
    writer.release()
    if not avi.is_file():
        raise RuntimeError(f"Failed to write {avi}")
    print(f"Wrote {avi} (use this path if .mp4 unavailable)")


def main() -> int:
    write_mp4(OUT)
    if OUT.is_file():
        print(f"Wrote {OUT} ({FPS * SECONDS} frames)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
