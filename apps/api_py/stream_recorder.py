"""Запись и нарезка стримов с маскированных камер (общий план / перфоманс)."""
from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Dict, Optional

from database import db_path
from stream_paths import poi_stream_name

FFMPEG = __import__("shutil").which("ffmpeg") or "/usr/local/bin/ffmpeg"


def recording_dir(recording_id: str) -> Path:
    d = db_path().parent / "recordings" / recording_id.replace("-", "")
    d.mkdir(parents=True, exist_ok=True)
    return d


class StreamRecorder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._procs: Dict[str, subprocess.Popen] = {}
        self._raw_paths: Dict[str, Path] = {}

    def start(self, recording_id: str, poi_id: str) -> Path:
        stream = poi_stream_name(poi_id) + "_avatar"
        rtsp = f"rtsp://127.0.0.1:8554/{stream}"
        out_dir = recording_dir(recording_id)
        raw = out_dir / "raw.mp4"
        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            rtsp,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(raw),
        ]
        with self._lock:
            old = self._procs.pop(recording_id, None)
            if old and old.poll() is None:
                old.terminate()
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._procs[recording_id] = proc
            self._raw_paths[recording_id] = raw
        print(f"[recorder] started {recording_id[:8]}… -> {raw}")
        return raw

    def stop(self, recording_id: str) -> Optional[Path]:
        with self._lock:
            proc = self._procs.pop(recording_id, None)
            raw = self._raw_paths.get(recording_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
        if raw and raw.is_file() and raw.stat().st_size > 0:
            return raw
        return None

    def process_clip(self, recording_id: str, raw: Path) -> Optional[Path]:
        if not raw.is_file() or raw.stat().st_size == 0:
            return None
        clip = raw.parent / "clip.mp4"
        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(clip),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return raw if raw.is_file() else None
        return clip if clip.is_file() and clip.stat().st_size > 0 else raw

    def process_tail_clip(self, recording_id: str, raw: Path, seconds: int = 300) -> Optional[Path]:
        """Cut the last `seconds` of a recording for post-stream map linger."""
        if not raw.is_file() or raw.stat().st_size == 0:
            return None
        out = raw.parent / f"linger_{int(seconds)}s.mp4"
        # -sseof seeks from end; re-encode for broad player compatibility
        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-sseof",
            f"-{max(1, int(seconds))}",
            "-i",
            str(raw),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return self.process_clip(recording_id, raw)
        if out.is_file() and out.stat().st_size > 0:
            return out
        return self.process_clip(recording_id, raw)

    def process_async(self, recording_id: str, raw: Path, on_done) -> None:
        def _run() -> None:
            clip = self.process_clip(recording_id, raw)
            on_done(clip or raw)

        threading.Thread(target=_run, daemon=True).start()


RECORDER = StreamRecorder()
