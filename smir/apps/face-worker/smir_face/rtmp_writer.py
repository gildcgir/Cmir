"""Publish processed BGR frames to RTMP (MediaMTX)."""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional

import numpy as np


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"


class FfmpegRtmpWriter:
    def __init__(self, url: str, width: int, height: int, fps: float = 30.0) -> None:
        self.url = url
        self.width = width
        self.height = height
        self.fps = fps if 5 <= fps <= 60 else 30.0
        self._cmd = [
            _ffmpeg(),
            "-nostdin",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(self.fps),
            "-i",
            "pipe:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            str(int(self.fps)),
            "-f",
            "flv",
            url,
        ]
        self._proc: Optional[subprocess.Popen] = subprocess.Popen(
            self._cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write(self, frame: np.ndarray) -> bool:
        if self._proc is None or self._proc.stdin is None:
            return False
        if self._proc.poll() is not None:
            return False
        if frame.shape[0] != self.height or frame.shape[1] != self.width:
            return False
        try:
            self._proc.stdin.write(frame.tobytes())
            return True
        except (BrokenPipeError, ValueError):
            return False

    def close(self) -> None:
        if self._proc is None:
            return
        if self._proc.stdin:
            try:
                self._proc.stdin.close()
            except Exception:
                pass
        try:
            self._proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        self._proc = None
