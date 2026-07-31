"""USB-камера → RTMP MediaMTX → HLS для пользовательского контура."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Set

from preview_buffer import PreviewBuffer
from stream_paths import hls_playlist_ready, poi_hls_url, poi_rtmp_url, poi_stream_name

ROOT = Path(__file__).resolve().parents[2]
FACE_WORKER = ROOT / "apps" / "face-worker"
FFMPEG = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg")
RELEASE_GRACE_SEC = 0.4


class LocalRelay:
    def __init__(self, store) -> None:
        self.store = store
        self._lock = threading.Lock()
        self._publishers: Dict[str, subprocess.Popen] = {}
        self._workers: Dict[str, subprocess.Popen] = {}
        self._consumers: Dict[str, Set[str]] = {}
        self._release_timers: Dict[str, threading.Timer] = {}
        self._preview = PreviewBuffer()
        self._device_cache: list[tuple[int, str]] = []
        self._device_cache_at = 0.0
        self._device_holder: Dict[int, str] = {}  # avfoundation index → poi_id

    @property
    def preview(self) -> PreviewBuffer:
        return self._preview

    def acquire(self, poi_id: str, client_id: str, wait_hls: bool = False) -> bool:
        if not client_id:
            client_id = "anonymous"
        with self._lock:
            timer = self._release_timers.pop(poi_id, None)
            if timer:
                timer.cancel()
            self._consumers.setdefault(poi_id, set()).add(client_id)
            row = self._row_for_poi(poi_id)
            if not row:
                return False
            self._ensure_poi(row, wait_hls=wait_hls)
            self._preview.start_capture(poi_id)
        if wait_hls:
            return hls_playlist_ready(poi_hls_url(poi_id), timeout=3.0)
        return True

    def release(self, poi_id: str, client_id: str) -> None:
        if not client_id:
            client_id = "anonymous"
        with self._lock:
            clients = self._consumers.get(poi_id)
            if clients:
                clients.discard(client_id)
                if clients:
                    return
                self._consumers.pop(poi_id, None)
            # сразу гасим камеру — на iMac один device, нельзя оставлять ffmpeg
            self._stop_poi(poi_id)
            self._preview.stop_capture(poi_id)
            print(f"[relay] camera off poi {poi_id[:8]}… (release)")

    def force_stop(self, poi_id: str) -> None:
        """Полная остановка без ожидания клиентов (закрытие панели / смена страницы)."""
        with self._lock:
            timer = self._release_timers.pop(poi_id, None)
            if timer:
                timer.cancel()
            self._consumers.pop(poi_id, None)
            self._stop_poi(poi_id)
            self._preview.stop_capture(poi_id)

    def active_clients(self, poi_id: str) -> int:
        with self._lock:
            return len(self._consumers.get(poi_id, set()))

    def refresh(self) -> None:
        """Синхронизация конфигурации без автозапуска камер."""
        with self._lock:
            rows = self._local_camera_rows()
            configured = {r["poi_id"] for r in rows}
            for poi_id in list(self._publishers):
                if poi_id not in configured and not self._consumers.get(poi_id):
                    self._stop_poi(poi_id)

    def ensure_poi(self, poi_id: str, wait_hls: bool = True) -> bool:
        """Запуск только при наличии активных потребителей."""
        if self.active_clients(poi_id) == 0:
            return False
        row = self._row_for_poi(poi_id)
        if not row:
            return False
        with self._lock:
            self._ensure_poi(row, wait_hls=wait_hls)
        if wait_hls:
            return hls_playlist_ready(poi_hls_url(poi_id), timeout=2.5)
        return True

    def restart_poi(self, poi_id: str) -> None:
        with self._lock:
            self._stop_poi(poi_id)
        if self.active_clients(poi_id) > 0:
            self.ensure_poi(poi_id, wait_hls=False)

    def _schedule_stop(self, poi_id: str) -> None:
        old = self._release_timers.pop(poi_id, None)
        if old:
            old.cancel()

        def _stop() -> None:
            with self._lock:
                if self._consumers.get(poi_id):
                    return
                self._stop_poi(poi_id)
                self._preview.stop_capture(poi_id)
                print(f"[relay] camera off poi {poi_id[:8]}… (no viewers)")

        t = threading.Timer(RELEASE_GRACE_SEC, _stop)
        self._release_timers[poi_id] = t
        t.start()

    def _local_camera_rows(self):
        return self.store.conn.execute(
            """
            SELECT c.id AS camera_id, c.poi_id, c.device_id, c.device_label, c.stream_url, p.mask_image
            FROM cameras c
            JOIN pois p ON p.id = c.poi_id
            WHERE c.source_type = 'local_usb' AND c.is_active = 1 AND c.is_preview = 1
              AND (c.stream_url LIKE 'rtmp://%' OR c.stream_url LIKE 'local://%')
            """
        ).fetchall()

    def _row_for_poi(self, poi_id: str):
        return self.store.conn.execute(
            """
            SELECT c.id AS camera_id, c.poi_id, c.device_id, c.device_label, c.stream_url, p.mask_image
            FROM cameras c
            JOIN pois p ON p.id = c.poi_id
            WHERE c.poi_id = ? AND c.source_type = 'local_usb' AND c.is_active = 1 AND c.is_preview = 1
            LIMIT 1
            """,
            (poi_id,),
        ).fetchone()

    def _stop_poi(self, poi_id: str) -> None:
        for idx, holder in list(self._device_holder.items()):
            if holder == poi_id:
                self._device_holder.pop(idx, None)
        for bucket in (self._workers, self._publishers):
            proc = bucket.pop(poi_id, None)
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    try:
                        proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        pass

    def _publisher_alive(self, poi_id: str) -> bool:
        pub = self._publishers.get(poi_id)
        return pub is not None and pub.poll() is None

    def _ensure_poi(self, row, wait_hls: bool = True) -> None:
        poi_id = row["poi_id"]
        if self._publisher_alive(poi_id):
            hls_url = poi_hls_url(poi_id)
            stale = wait_hls and not hls_playlist_ready(hls_url, timeout=1.2)
            if stale:
                print(f"[relay] stale publisher for poi {poi_id[:8]}… — restarting ffmpeg")
                self._stop_poi(poi_id)
            else:
                threading.Thread(
                    target=self._ensure_worker,
                    args=(poi_id, row["mask_image"], row["camera_id"] if "camera_id" in row.keys() else ""),
                    daemon=True,
                ).start()
                return

        if self._publishers.get(poi_id) and self._publishers[poi_id].poll() is not None:
            self._publishers.pop(poi_id, None)

        resolved = self._resolve_device_index(row["device_label"] or "", row["device_id"] or "")
        if resolved is None:
            print(f"[relay] USB not found for poi {poi_id[:8]}… label={row['device_label']!r}")
            return
        idx, source_name, stub = resolved
        # Одна физическая камера — не держим два ffmpeg на одном index
        holder = self._device_holder.get(idx)
        if holder and holder != poi_id:
            print(f"[relay] device {idx} held by {holder[:8]}… — stopping previous")
            self._stop_poi(holder)
            self._consumers.pop(holder, None)
            self._preview.stop_capture(holder)
        if stub:
            print(
                f"[relay] GoPro не найдена — заглушка webcam «{source_name}» "
                f"(index {idx}) poi {poi_id[:8]}…"
            )

        rtmp = poi_rtmp_url(poi_id)
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "avfoundation",
            "-pixel_format",
            "uyvy422",
            "-framerate",
            "30",
            "-video_size",
            "1280x720",
            "-i",
            f"{idx}:none",
            "-an",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-f",
            "flv",
            rtmp,
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            self._publishers[poi_id] = proc
            self._device_holder[idx] = poi_id
            print(f"[relay] publish poi {poi_id[:8]}… -> {rtmp} (device {idx} «{source_name}»)")
        except OSError as e:
            print(f"[relay] ffmpeg failed: {e}")
            return

        if wait_hls:
            for _ in range(12):
                if hls_playlist_ready(poi_hls_url(poi_id), timeout=1.0):
                    break
                if proc.poll() is not None:
                    err = (proc.stderr.read() if proc.stderr else b"").decode(errors="replace")[:200]
                    print(f"[relay] ffmpeg exited: {err}")
                    self._publishers.pop(poi_id, None)
                    return
                time.sleep(0.3)

        threading.Thread(
            target=self._ensure_worker,
            args=(poi_id, row["mask_image"], row["camera_id"] if "camera_id" in row.keys() else ""),
            daemon=True,
        ).start()

    def _ensure_worker(self, poi_id: str, mask_image: Optional[str], camera_id: str = "") -> None:
        raw_url = poi_hls_url(poi_id)
        for _ in range(16):
            if hls_playlist_ready(raw_url, timeout=1.0):
                break
            time.sleep(0.3)
        else:
            print(f"[relay] raw HLS not ready for {poi_id[:8]}…, skip mask worker")
            return

        worker = self._workers.get(poi_id)
        if worker and worker.poll() is None:
            return

        py = FACE_WORKER / ".venv" / "bin" / "python"
        if not py.is_file():
            py = Path(sys.executable)
        stream = poi_stream_name(poi_id)
        rtsp_in = f"rtsp://127.0.0.1:8554/{stream}"
        rtmp_out = f"rtmp://127.0.0.1:1935/{stream}_avatar"
        cmd = [
            str(py),
            "-m",
            "smir_face.worker",
            "--input",
            rtsp_in,
            "--output",
            rtmp_out,
            "--api-url",
            os.environ.get("SMIR_API_URL", "http://127.0.0.1:8090"),
            "--poi-id",
            poi_id,
            "--mask",
            "face-bar",
            "--track-smooth",
            "0.35",
            "--output-delay-ms",
            os.environ.get("SMIR_PRIVACY_DELAY_MS", "250"),
        ]
        if camera_id:
            cmd.extend(["--camera-id", camera_id])
        mask_path = self.store.get_mask_image_path(poi_id) if mask_image else None
        if mask_path and mask_path.is_file():
            cmd.extend(["--mask-image", str(mask_path)])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(FACE_WORKER)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(FACE_WORKER),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._workers[poi_id] = proc
            print(f"[relay] mask worker poi {poi_id[:8]}… -> {stream}_avatar")
        except OSError as e:
            print(f"[relay] worker failed: {e}")

    def _resolve_device_index(self, label: str, device_id: str) -> Optional[tuple[int, str, bool]]:
        """
        Возвращает (avfoundation_index, name, stub).
        stub=True если искали GoPro, но взяли обычную веб-камеру.
        """
        devices = self._list_avfoundation_devices()
        if not devices:
            return None

        wants_gopro = "gopro" in (label or "").lower()
        gopro = next(((i, n) for i, n in devices if "gopro" in n.lower()), None)
        if gopro:
            return (gopro[0], gopro[1], False)

        label_l = (label or "").strip().lower()
        if label_l and not wants_gopro:
            for idx, name in devices:
                if label_l in name.lower() or name.lower() in label_l:
                    return (idx, name, False)
        if device_id and not wants_gopro:
            tail = device_id[-8:].lower()
            for idx, name in devices:
                if tail in name.lower():
                    return (idx, name, False)

        stub = self._pick_stub_webcam(devices)
        if stub:
            return (stub[0], stub[1], True)
        return None

    @staticmethod
    def _pick_stub_webcam(devices: list[tuple[int, str]]) -> Optional[tuple[int, str]]:
        skip_tokens = ("obs", "virtual", "continuity", "iphone", "blackhole", "capture screen")
        ranked: list[tuple[int, int, str]] = []
        for idx, name in devices:
            low = name.lower()
            if "gopro" in low:
                continue
            if any(t in low for t in skip_tokens):
                continue
            score = 0
            if "facetime" in low or "built-in" in low or "встроенн" in low:
                score = 3
            elif "webcam" in low or "usb" in low or "camera" in low or "камер" in low:
                score = 1
            ranked.append((score, idx, name))
        if not ranked:
            # крайний случай — первая камера из списка
            return devices[0]
        ranked.sort(key=lambda t: (-t[0], t[1]))
        _, idx, name = ranked[0]
        return (idx, name)

    def _list_avfoundation_devices(self) -> list[tuple[int, str]]:
        now = time.time()
        if self._device_cache and now - self._device_cache_at < 30:
            return self._device_cache
        if not Path(FFMPEG).exists() and not shutil.which(FFMPEG):
            return []
        try:
            out = subprocess.run(
                [FFMPEG, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=8,
            )
            text = (out.stderr or "") + (out.stdout or "")
        except (OSError, subprocess.TimeoutExpired):
            return []
        devices: list[tuple[int, str]] = []
        in_video = False
        for line in text.splitlines():
            if "AVFoundation video devices" in line:
                in_video = True
                continue
            if "AVFoundation audio devices" in line:
                in_video = False
                continue
            if not in_video:
                continue
            m = re.search(r"\[(\d+)\]\s+(.+)", line)
            if m:
                devices.append((int(m.group(1)), m.group(2).strip()))
        self._device_cache = devices
        self._device_cache_at = now
        return devices
