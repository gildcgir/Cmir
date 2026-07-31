"""10-секундный зацикленный клип превью — запись сразу после старта маскированного потока."""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from database import db_path
from stream_paths import hls_playlist_ready, poi_masked_hls_url, poi_stream_name

PREVIEW_SECONDS = 10
PRIVACY_WARMUP_SEC = 1.0
PREVIEW_TARGET_SEC = PREVIEW_SECONDS
HLS_WAIT_SEC = 45.0
FFMPEG = __import__("shutil").which("ffmpeg") or "/usr/local/bin/ffmpeg"


def clip_path(poi_id: str) -> Path:
    d = db_path().parent / "buffers" / poi_id.replace("-", "")
    d.mkdir(parents=True, exist_ok=True)
    return d / "preview_loop.mp4"


class PreviewBuffer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._threads: Dict[str, threading.Thread] = {}
        self._stop: Dict[str, threading.Event] = {}
        self._started_at: Dict[str, float] = {}
        self._recording_at: Dict[str, float] = {}
        self._ready: Dict[str, bool] = {}
        self._error: Dict[str, str] = {}

    def start_capture(self, poi_id: str) -> None:
        with self._lock:
            alive = poi_id in self._threads and self._threads[poi_id].is_alive()
            if alive and self._ready.get(poi_id):
                return
            if alive:
                return
            self._threads.pop(poi_id, None)
            self._ready.pop(poi_id, None)
            self._error.pop(poi_id, None)
            self._recording_at.pop(poi_id, None)
            self._started_at[poi_id] = time.time()
            ev = threading.Event()
            self._stop[poi_id] = ev
            t = threading.Thread(target=self._run, args=(poi_id, ev), daemon=True)
            self._threads[poi_id] = t
            t.start()

    def stop_capture(self, poi_id: str) -> None:
        with self._lock:
            ev = self._stop.pop(poi_id, None)
            if ev:
                ev.set()
            self._threads.pop(poi_id, None)
            self._started_at.pop(poi_id, None)
            self._recording_at.pop(poi_id, None)
            self._ready.pop(poi_id, None)
            self._error.pop(poi_id, None)
        path = clip_path(poi_id)
        path.unlink(missing_ok=True)

    def status(self, poi_id: str) -> dict:
        with self._lock:
            started = self._started_at.get(poi_id)
            recording = self._recording_at.get(poi_id)
            ready = self._ready.get(poi_id, False)
            err = self._error.get(poi_id)
        path = clip_path(poi_id)
        if ready and path.is_file() and path.stat().st_size > 0:
            buffered = PREVIEW_SECONDS
        elif recording:
            buffered = min(PREVIEW_SECONDS, int(time.time() - recording))
        elif started:
            buffered = 0
        else:
            buffered = 0
        return {
            "ready": ready and path.is_file() and path.stat().st_size > 0,
            "buffered_seconds": buffered,
            "target_seconds": PREVIEW_TARGET_SEC,
            "recording": bool(recording) and not ready,
            "error": err,
            "clip_url": f"/api/v1/pois/{poi_id}/preview-clip.mp4" if ready else None,
        }

    def _fail(self, poi_id: str, message: str) -> None:
        with self._lock:
            self._error[poi_id] = message
            self._recording_at.pop(poi_id, None)

    def _run(self, poi_id: str, stop: threading.Event) -> None:
        masked_hls = poi_masked_hls_url(poi_id)
        deadline = time.time() + HLS_WAIT_SEC
        while time.time() < deadline:
            if stop.is_set():
                return
            if hls_playlist_ready(masked_hls, timeout=0.8):
                break
            time.sleep(0.25)
        else:
            self._fail(poi_id, "Маскированный поток не готов — проверьте MediaMTX и face-worker")
            return

        if PRIVACY_WARMUP_SEC > 0:
            time.sleep(PRIVACY_WARMUP_SEC)
            if stop.is_set():
                return

        stream = poi_stream_name(poi_id) + "_avatar"
        rtsp = f"rtsp://127.0.0.1:8554/{stream}"
        out = clip_path(poi_id)
        tmp = out.with_suffix(".tmp.mp4")
        with self._lock:
            self._recording_at[poi_id] = time.time()

        cmd = [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "32768",
            "-analyzeduration",
            "500000",
            "-i",
            rtsp,
            "-t",
            str(PREVIEW_SECONDS),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(tmp),
        ]
        try:
            proc = subprocess.run(cmd, timeout=PREVIEW_SECONDS + 35, capture_output=True, text=True)
            if stop.is_set():
                tmp.unlink(missing_ok=True)
                return
            if proc.returncode == 0 and tmp.is_file() and tmp.stat().st_size > 0:
                tmp.replace(out)
                with self._lock:
                    self._ready[poi_id] = True
                    self._recording_at.pop(poi_id, None)
                    self._error.pop(poi_id, None)
                print(f"[preview] clip ready poi {poi_id[:8]}… ({PREVIEW_SECONDS}s)")
            else:
                tmp.unlink(missing_ok=True)
                detail = (proc.stderr or "").strip().splitlines()[-1] if proc.stderr else ""
                self._fail(poi_id, detail or "ffmpeg не записал превью")
        except (OSError, subprocess.TimeoutExpired) as e:
            tmp.unlink(missing_ok=True)
            self._fail(poi_id, str(e))
        finally:
            with self._lock:
                self._recording_at.pop(poi_id, None)
