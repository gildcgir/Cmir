"""RTSP capture via ffmpeg (OpenCV often fails on macOS)."""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional, Tuple

import numpy as np


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or "/usr/local/bin/ffprobe"


def probe_stream(url: str) -> Tuple[int, int, float]:
    cmd = [
        _ffprobe(),
        "-rtsp_transport",
        "tcp",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate",
        "-of",
        "csv=p=0",
        url,
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    parts = out.split(",")
    w, h = int(parts[0]), int(parts[1])
    fps = 25.0
    if len(parts) > 2 and parts[2]:
        num, _, den = parts[2].partition("/")
        try:
            fps = float(num) / float(den or "1")
        except ValueError:
            fps = 25.0
    if fps > 60 or fps < 5:
        fps = 30.0
    return w, h, fps


class FfmpegRtspCapture:
    def __init__(self, url: str) -> None:
        self.url = url
        self.width, self.height, self.fps = probe_stream(url)
        self._cmd = [
            _ffmpeg(),
            "-nostdin",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            url,
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "pipe:1",
        ]
        self._proc = subprocess.Popen(
            self._cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._frame_bytes = self.width * self.height * 3

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self._proc.stdout is None:
            return False, None
        raw = self._proc.stdout.read(self._frame_bytes)
        if len(raw) < self._frame_bytes:
            return False, None
        frame = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 3).copy()
        return True, frame

    def release(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
