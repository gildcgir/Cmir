#!/usr/bin/env python3
"""
Cmir API — Python (Phase 2 core: SQLite users, auth, consents, wallets).
Port 8090.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import http.cookiejar
import urllib.parse
import urllib.request
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from database import app_env  # noqa: E402
from camera_health import probe_stream_url  # noqa: E402
from local_relay import LocalRelay  # noqa: E402
from store import CAMERA_ROLES, PATCH_DIM, VIEW_MODES, Store  # noqa: E402
from stream_paths import (
    hls_direct_to_proxy,
    hls_playlist_ready,
    hls_proxy_url,
    masked_stream_hls,
    poi_hls_proxy_url,
    poi_hls_url,
    poi_masked_hls_proxy_url,
    poi_masked_hls_url,
    poi_stream_name,
    stream_url_to_hls,
)  # noqa: E402

HOST, PORT = "0.0.0.0", 8090
STORE = Store()
LOCAL_RELAY = LocalRelay(STORE)
_MTX_JAR = http.cookiejar.CookieJar()
_MTX_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_MTX_JAR))


_TILE_CACHE: dict[str, tuple[float, bytes, str]] = {}
_TILE_CACHE_MAX = 512
_TILE_TTL = 3600.0


def public_base_url(handler: BaseHTTPRequestHandler) -> str:
    host = handler.headers.get("Host") or f"localhost:{PORT}"
    return f"http://{host}"


def proxy_map_tile(handler: BaseHTTPRequestHandler, z: str, x: str, y: str) -> None:
    """Proxy raster tiles over HTTP so Android WebView need not hit HTTPS CDNs."""
    try:
        zi, xi, yi = int(z), int(x), int(y)
    except ValueError:
        return json_response(handler, 400, {"success": False, "error": "bad tile coords"})
    if zi < 0 or zi > 19 or xi < 0 or yi < 0:
        return json_response(handler, 400, {"success": False, "error": "tile out of range"})

    cache_key = f"v2/{zi}/{xi}/{yi}"
    now = __import__("time").time()
    cached = _TILE_CACHE.get(cache_key)
    if cached and now - cached[0] < _TILE_TTL:
        data, ctype = cached[1], cached[2]
        handler.send_response(200)
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.send_header("Content-Type", ctype)
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)
        return

    # Bright street map (OSM / Carto light) — not dark_all / dark voyager
    upstreams = [
        f"https://tile.openstreetmap.org/{zi}/{xi}/{yi}.png",
        f"https://a.basemaps.cartocdn.com/light_all/{zi}/{xi}/{yi}.png",
        f"https://b.basemaps.cartocdn.com/light_all/{zi}/{xi}/{yi}.png",
        f"https://a.basemaps.cartocdn.com/rastertiles/voyager/{zi}/{xi}/{yi}.png",
    ]
    last_err = "tile fetch failed"
    for url in upstreams:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CmirMapTileProxy/1.0 (lab; +https://github.com/gildcgir/Cmir)",
                    "Accept": "image/png,image/*;q=0.8,*/*;q=0.5",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "image/png")
            if len(_TILE_CACHE) >= _TILE_CACHE_MAX:
                _TILE_CACHE.pop(next(iter(_TILE_CACHE)), None)
            _TILE_CACHE[cache_key] = (now, data, ctype)
            handler.send_response(200)
            handler.send_header("Access-Control-Allow-Origin", "*")
            handler.send_header("Content-Type", ctype)
            handler.send_header("Cache-Control", "public, max-age=3600")
            handler.send_header("Content-Length", str(len(data)))
            handler.end_headers()
            handler.wfile.write(data)
            return
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            continue
    return json_response(handler, 502, {"success": False, "error": last_err})


def preview_clip_public_url(handler: BaseHTTPRequestHandler, clip_path: str) -> str:
    return f"{public_base_url(handler)}{clip_path}"


def proxy_hls_response(handler: BaseHTTPRequestHandler, rel_path: str) -> None:
    from urllib.parse import urljoin

    upstream = f"http://127.0.0.1:8888/{rel_path}"
    try:
        with _MTX_OPENER.open(upstream, timeout=15) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            loc = e.headers["Location"]
            if loc.startswith("/"):
                loc = urljoin(upstream, loc)
            try:
                with _MTX_OPENER.open(loc, timeout=15) as resp:
                    data = resp.read()
                    ctype = resp.headers.get("Content-Type", "application/octet-stream")
            except (urllib.error.URLError, OSError, TimeoutError) as err:
                return json_response(handler, 502, {"success": False, "error": str(err)})
        else:
            body = e.read()
            handler.send_response(e.code)
            handler.send_header("Access-Control-Allow-Origin", "*")
            handler.send_header("Content-Type", e.headers.get("Content-Type", "text/plain"))
            handler.send_header("Content-Length", str(len(body)))
            handler.end_headers()
            handler.wfile.write(body)
            return
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return json_response(handler, 502, {"success": False, "error": str(e)})

    if rel_path.endswith(".m3u8"):
        base = rel_path.split("?")[0].rsplit("/", 1)[0]
        lines = []
        for line in data.decode(errors="replace").splitlines():
            if line.startswith("#") or not line.strip():
                lines.append(line)
                continue
            uri = line.strip()
            if uri.startswith("http://") or uri.startswith("https://"):
                parsed = urlparse(uri)
                seg = parsed.path.lstrip("/")
                if parsed.query:
                    seg += "?" + parsed.query
                lines.append(hls_proxy_url(seg))
            elif uri.startswith("/"):
                lines.append(hls_proxy_url(uri.lstrip("/")))
            else:
                lines.append(hls_proxy_url(f"{base}/{uri}"))
        data = "\n".join(lines).encode()

    handler.send_response(200)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Type", ctype if rel_path.endswith(".m3u8") else ctype)
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def json_response(handler: BaseHTTPRequestHandler, code: int, body: dict) -> None:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def bearer_token(handler: BaseHTTPRequestHandler) -> str:
    auth = handler.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def require_user(handler: BaseHTTPRequestHandler) -> Optional[dict]:
    user = STORE.user_from_token(bearer_token(handler))
    if not user:
        json_response(handler, 401, {"success": False, "error": "unauthorized"})
        return None
    return user


def require_admin(handler: BaseHTTPRequestHandler) -> Optional[dict]:
    user = require_user(handler)
    if user is None:
        return None
    if not STORE.is_admin(user):
        json_response(handler, 403, {"success": False, "error": "admin required"})
        return None
    return user


def _worker_authorized(handler: BaseHTTPRequestHandler) -> bool:
    """Face-worker: X-Cmir-Worker must match CMIR_WORKER_TOKEN (always required)."""
    expected = os.environ.get("CMIR_WORKER_TOKEN", "").strip()
    got = (handler.headers.get("X-Cmir-Worker") or "").strip()
    if not expected or not got:
        return False
    return secrets.compare_digest(expected, got)


def parse_multipart(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    """Minimal multipart parser for single file upload."""
    ctype = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in ctype:
        return {}
    m = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', ctype)
    if not m:
        return {}
    boundary = (m.group(1) or m.group(2)).encode()
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length)
    parts = body.split(b"--" + boundary)
    out: dict[str, Any] = {}
    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        header, _, data = part.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2]
        hdr = header.decode("utf-8", errors="replace")
        name_m = re.search(r'name="([^"]+)"', hdr)
        file_m = re.search(r'filename="([^"]*)"', hdr)
        if not name_m:
            continue
        name = name_m.group(1)
        if file_m and file_m.group(1):
            out[name] = {"filename": file_m.group(1), "data": data}
        else:
            out[name] = data.decode("utf-8", errors="replace").strip()
    return out


def handle_mask_image_upload(handler: BaseHTTPRequestHandler, poi_id: str) -> bool:
    """POST multipart mask — must run before JSON body read. Returns True if handled."""
    if require_admin(handler) is None:
        return True
    form = parse_multipart(handler)
    file_part = form.get("image") or form.get("file")
    if not isinstance(file_part, dict) or not file_part.get("data"):
        json_response(handler, 400, {"success": False, "error": "image file required"})
        return True
    fname = file_part.get("filename", "mask.png")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "png"
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "png"
    try:
        STORE.save_mask_image(poi_id, file_part["data"], ext)
    except KeyError:
        json_response(handler, 404, {"success": False, "error": "poi not found"})
        return True
    LOCAL_RELAY.restart_poi(poi_id)
    json_response(
        handler,
        200,
        {"success": True, "data": {"mask_image_url": f"/api/v1/pois/{poi_id}/mask-image"}},
    )
    return True


def geocode_query(q: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "json", "limit": 1, "q": q}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Cmir/0.4.0 (local dev)"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read())
    if not data:
        raise ValueError("address not found")
    hit = data[0]
    return {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "display_name": hit.get("display_name", q),
    }


def reverse_geocode(lat: float, lon: float) -> dict:
    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(
        {"format": "json", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Cmir/0.4.0 (local dev)"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read())
    if not data or "error" in data:
        raise ValueError("location not found")
    addr = data.get("address") or {}
    house = addr.get("house_number", "")
    road = addr.get("road") or addr.get("pedestrian") or addr.get("footway") or ""
    street = f"{road} {house}".strip() if road or house else ""
    return {
        "lat": float(data.get("lat", lat)),
        "lon": float(data.get("lon", lon)),
        "display_name": data.get("display_name") or street or f"{lat:.6f}, {lon:.6f}",
        "street": street,
        "building": addr.get("building") or addr.get("amenity") or "",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[api] {args[0]}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        qs = parse_qs(urlparse(self.path).query)
        city = qs.get("city", [None])[0]
        country = qs.get("country", [None])[0]

        if path == "/health":
            return json_response(
                self,
                200,
                {"status": "healthy", "service": "cmir-api-py", "version": "0.4.0", "phase": "2-core", "environment": app_env()},
            )

        # /api/v1/map-tiles/{z}/{x}/{y}.png — HTTP proxy for Leaflet (Android WebView)
        if len(parts) == 6 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "map-tiles":
            yname = parts[5]
            y = yname[:-4] if yname.endswith(".png") else yname
            return proxy_map_tile(self, parts[3], parts[4], y)

        if path == "/api/v1/geocode":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return json_response(self, 400, {"success": False, "error": "q required"})
            try:
                data = geocode_query(q)
            except ValueError as e:
                return json_response(self, 404, {"success": False, "error": str(e)})
            except OSError as e:
                return json_response(self, 502, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/reverse-geocode":
            try:
                lat = float(qs.get("lat", [""])[0])
                lon = float(qs.get("lon", [""])[0])
            except (TypeError, ValueError):
                return json_response(self, 400, {"success": False, "error": "lat and lon required"})
            try:
                data = reverse_geocode(lat, lon)
            except ValueError as e:
                return json_response(self, 404, {"success": False, "error": str(e)})
            except OSError as e:
                return json_response(self, 502, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/me":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.user_public(user)})

        if path == "/api/v1/legal/documents":
            from compliance import list_legal_documents

            return json_response(
                self, 200, {"success": True, "data": list_legal_documents(STORE.conn)}
            )

        if len(parts) >= 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "hls":
            rel = "/".join(parts[3:])
            q = urlparse(self.path).query
            if q:
                rel = f"{rel}?{q}"
            return proxy_hls_response(self, rel)

        if path == "/api/v1/auth/platforms":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_platform_links(user["id"])})

        if path == "/api/v1/auth/recordings":
            user = require_user(self)
            if user is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_user_recordings(user["id"])})

        if len(parts) == 5 and parts[2] == "recordings" and parts[4] == "clip.mp4":
            user = require_user(self)
            if user is None:
                return
            rec = STORE.conn.execute(
                "SELECT clip_path FROM stream_recordings WHERE id = ? AND user_id = ?",
                (parts[3], user["id"]),
            ).fetchone()
            if not rec or not rec["clip_path"]:
                return json_response(self, 404, {"success": False, "error": "clip not found"})
            from pathlib import Path

            path = Path(rec["clip_path"])
            if not path.is_file():
                return json_response(self, 404, {"success": False, "error": "file missing"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "authorize":
            user = require_user(self)
            if user is None:
                return
            from platforms import get_adapter

            platform = parts[3]
            try:
                adapter = get_adapter(platform)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            redirect = f"http://127.0.0.1:{PORT}/api/v1/platforms/{platform}/oauth-callback"
            state = f"{user['id']}:{secrets.token_urlsafe(8)}"
            return json_response(
                self,
                200,
                {"success": True, "data": {"authorize_url": adapter.authorize_url(redirect, state), "state": state}},
            )

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "oauth-callback":
            qs = parse_qs(urlparse(self.path).query)
            code = (qs.get("code") or [""])[0]
            state = (qs.get("state") or [""])[0]
            platform = parts[3]
            user_id = state.split(":")[0] if state else ""
            if not code or not user_id:
                return json_response(self, 400, {"success": False, "error": "invalid oauth callback"})
            from platforms import get_adapter

            try:
                adapter = get_adapter(platform)
                redirect = f"http://127.0.0.1:{PORT}/api/v1/platforms/{platform}/oauth-callback"
                token_data = adapter.exchange_code(code, redirect)
                data = STORE.platform_oauth_complete(user_id, platform, token_data)
            except (ValueError, KeyError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            self.send_response(302)
            self.send_header("Location", "/index.html#account")
            self.end_headers()
            return

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "comments":
            user = require_user(self)
            if user is None:
                return
            qs = parse_qs(urlparse(self.path).query)
            broadcast_id = (qs.get("broadcast_id") or [""])[0]
            try:
                data = STORE.sync_platform_comments(user["id"], parts[3], broadcast_id)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "preview-clip":
            poi_id = parts[3]
            st = LOCAL_RELAY.preview.status(poi_id)
            if st.get("clip_url"):
                st = {
                    **st,
                    "clip_url": preview_clip_public_url(self, st["clip_url"]),
                }
            return json_response(self, 200, {"success": True, "data": st})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "preview-clip.mp4":
            from preview_buffer import clip_path

            path = clip_path(parts[3])
            if not path.is_file():
                return json_response(self, 404, {"success": False, "error": "preview not ready"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "replay-clip.mp4":
            try:
                payload = STORE.poi_payload(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            if payload.get("status") not in ("lingering", "published"):
                return json_response(self, 404, {"success": False, "error": "replay not available"})
            clip = STORE.get_replay_clip_path(parts[3])
            if not clip:
                return json_response(self, 404, {"success": False, "error": "replay not ready"})
            path = Path(clip)
            if not path.is_file():
                return json_response(self, 404, {"success": False, "error": "replay file missing"})
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Cache-Control", "public, max-age=60")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "menu-items":
            try:
                items = STORE.poi_menu_items(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": items})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "kiosk-stream":
            poi_id = parts[3]
            cam = STORE.conn.execute(
                """
                SELECT id FROM cameras WHERE poi_id = ? AND role = 'consent' AND is_active = 1
                ORDER BY slot_index LIMIT 1
                """,
                (poi_id,),
            ).fetchone()
            if not cam:
                cam = STORE.conn.execute(
                    """
                    SELECT id FROM cameras WHERE poi_id = ? AND is_active = 1 AND is_preview = 1
                    LIMIT 1
                    """,
                    (poi_id,),
                ).fetchone()
            if not cam:
                return json_response(self, 404, {"success": False, "error": "no camera"})
            cam_obj = STORE.get_camera(cam["id"])
            is_local = cam_obj.source_type == "local_usb" or cam_obj.stream_url.startswith("local://")
            client_id = qs.get("client_id", [""])[0] or "kiosk"
            if is_local:
                LOCAL_RELAY.acquire(poi_id, client_id, wait_hls=True)
            masked_direct = masked_stream_hls(cam_obj.stream_url, poi_id)
            raw_direct = stream_url_to_hls(cam_obj.stream_url, poi_id)
            if is_local:
                masked = poi_masked_hls_proxy_url(poi_id)
                raw = poi_hls_proxy_url(poi_id)
                m_ready = hls_playlist_ready(poi_masked_hls_url(poi_id))
                r_ready = hls_playlist_ready(poi_hls_url(poi_id))
            else:
                masked = hls_direct_to_proxy(masked_direct)
                raw = hls_direct_to_proxy(raw_direct)
                m_ready = hls_playlist_ready(masked_direct) if masked_direct else False
                r_ready = hls_playlist_ready(raw_direct) if raw_direct else False
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "masked_hls_url": masked if m_ready else None,
                        "hls_url": None,
                        "live_hls_url": masked if m_ready else None,
                        "stream_ready": m_ready,
                        "masked_ready": m_ready,
                        "privacy_buffered": m_ready,
                    },
                },
            )

        if path == "/api/v1/consented-faces":
            if not _worker_authorized(self):
                return json_response(self, 401, {"success": False, "error": "worker token required"})
            return json_response(
                self,
                200,
                {"success": True, "data": {"faces": STORE.global_consented_faces()}},
            )

        if path == "/api/v1/face-presence":
            user = require_user(self)
            if user is None:
                return
            qs_cam = qs.get("camera_id", [None])[0]
            qs_period = qs.get("period_key", [None])[0]
            if STORE.is_admin(user):
                qs_user = qs.get("user_id", [None])[0]
                data = STORE.list_face_presence(user_id=qs_user, camera_id=qs_cam, period_key=qs_period)
            else:
                data = STORE.list_face_presence(user_id=user["id"], camera_id=qs_cam, period_key=qs_period)
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/pois":
            want_all = qs.get("all", ["0"])[0] in ("1", "true", "yes")
            status = qs.get("status", [None])[0]
            user = STORE.user_from_token(bearer_token(self))
            if want_all or status == "pending":
                if not user or not STORE.is_admin(user):
                    return json_response(self, 403, {"success": False, "error": "admin required"})
                data = STORE.list_pois(include_all=want_all, status=None if want_all else status)
            else:
                data = STORE.list_pois(status="published")
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "chat":
            poi_id = parts[3]
            since = qs.get("since", [None])[0]
            try:
                data = STORE.list_chat(poi_id, since=since)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/tops/consent":
            items = STORE.sorted_tops("consent", city, country)
            return json_response(
                self, 200, {"success": True, "data": items, "filter": {"city": city, "country": country}}
            )

        if path == "/api/v1/tops/participants":
            items = STORE.sorted_tops("participants", city, country)
            return json_response(
                self, 200, {"success": True, "data": items, "filter": {"city": city, "country": country}}
            )

        if path == "/api/v1/donations":
            poi_f = qs.get("poi_id", [None])[0]
            return json_response(self, 200, {"success": True, "data": STORE.list_donations(poi_f)})

        if len(parts) == 4 and parts[0] == "api" and parts[1] == "v1" and parts[2] == "pois":
            poi_id = parts[3]
            try:
                data = STORE.poi_payload(poi_id)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "embeddings":
            if not (_worker_authorized(self) or STORE.is_admin(STORE.user_from_token(bearer_token(self)) or {})):
                return json_response(self, 401, {"success": False, "error": "worker or admin required"})
            poi_id = parts[3]
            try:
                embs = STORE.poi_embeddings(poi_id)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(
                self,
                200,
                {"success": True, "data": {"poi_id": poi_id, "embeddings": embs, "count": len(embs)}},
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "scene":
            try:
                data = STORE.scene_description(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "cameras":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            return json_response(self, 200, {"success": True, "data": asdict(cam)})

        if len(parts) == 5 and parts[2] == "cameras" and parts[4] == "health":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            probe = probe_stream_url(cam.stream_url)
            data = {
                "camera_id": cam.id,
                "poi_id": cam.poi_id,
                "stream_url": cam.stream_url,
                "is_active": cam.is_active,
                **probe,
            }
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "cameras" and parts[4] == "playback":
            cam = STORE.get_camera(parts[3])
            if not cam:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            is_local = cam.source_type == "local_usb" or cam.stream_url.startswith("local://")
            client_id = qs.get("client_id", [""])[0] or "playback-anon"
            if is_local:
                LOCAL_RELAY.acquire(cam.poi_id, client_id, wait_hls=True)
            hls_direct = stream_url_to_hls(cam.stream_url, cam.poi_id)
            masked_direct = masked_stream_hls(cam.stream_url, cam.poi_id)
            stream_ready = hls_playlist_ready(hls_direct) if hls_direct else False
            masked_ready = hls_playlist_ready(masked_direct) if masked_direct else False
            if is_local:
                hls = poi_hls_proxy_url(cam.poi_id)
                masked = poi_masked_hls_proxy_url(cam.poi_id)
            else:
                hls = hls_direct_to_proxy(hls_direct)
                masked = hls_direct_to_proxy(masked_direct)
            preview = LOCAL_RELAY.preview.status(cam.poi_id) if is_local else {"ready": False}
            if preview.get("clip_url"):
                preview = {**preview, "clip_url": preview_clip_public_url(self, preview["clip_url"])}
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "camera_id": cam.id,
                        "poi_id": cam.poi_id,
                        "stream_url": cam.stream_url,
                        "source_type": cam.source_type,
                        "hls_url": hls if (masked_ready or not is_local) and stream_ready else None,
                        "masked_hls_url": masked if masked_ready else None,
                        "fallback_hls_url": None,
                        "live_hls_url": masked if masked_ready else None,
                        "stream_ready": masked_ready if is_local else stream_ready,
                        "masked_ready": masked_ready,
                        "privacy_buffered": masked_ready,
                        "preview_clip": preview,
                        "rtsp_url": cam.stream_url if cam.stream_url.startswith("rtsp") else None,
                    },
                },
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            path = STORE.get_mask_image_path(parts[3])
            if not path:
                return json_response(self, 404, {"success": False, "error": "no mask image"})
            data = path.read_bytes()
            ext = path.suffix.lower()
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
            }.get(ext, "image/png")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/api/v1/admin/network-quality":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.network_quality()})

        if path == "/api/v1/admin/stats":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.admin_stats()})

        if path == "/api/v1/admin/users":
            if require_admin(self) is None:
                return
            return json_response(self, 200, {"success": True, "data": STORE.list_users()})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "airtime":
            try:
                data = STORE.list_airtime(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "wallets":
            w = STORE.get_wallet(parts[3])
            if not w:
                return json_response(self, 404, {"success": False, "error": "wallet not found"})
            return json_response(self, 200, {"success": True, "data": w})

        if path == "/api/v1/cameras/health-all":
            data = []
            for row in STORE.conn.execute("SELECT id FROM cameras WHERE is_active = 1").fetchall():
                cam = STORE.get_camera(row["id"])
                if cam:
                    probe = probe_stream_url(cam.stream_url)
                    data.append(
                        {
                            "camera_id": cam.id,
                            "poi_id": cam.poi_id,
                            "stream_url": cam.stream_url,
                            "is_active": cam.is_active,
                            **probe,
                        }
                    )
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "admin" and parts[4] == "health-history":
            hist = STORE.health_snapshots.get(parts[3], [])
            return json_response(self, 200, {"success": True, "data": hist})

        if path == "/api/v1/performance/streams":
            user = require_user(self)
            if user is None:
                return
            qs = parse_qs(urlparse(self.path).query)
            camera_id = (qs.get("camera_id") or [""])[0]
            if not camera_id:
                return json_response(self, 400, {"success": False, "error": "camera_id required"})
            return json_response(
                self,
                200,
                {"success": True, "data": STORE.performance_stream_list(user["id"], camera_id)},
            )

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            handle_mask_image_upload(self, parts[3])
            return

        # Host ends broadcast (optional clip upload) — must run before JSON body read
        if (
            len(parts) == 6
            and parts[2] == "pois"
            and parts[4] == "broadcast"
            and parts[5] == "end"
            and "multipart/form-data" in (self.headers.get("Content-Type") or "")
        ):
            user = require_user(self)
            if user is None:
                return
            poi_id = parts[3]
            form = parse_multipart(self)
            uploaded = None
            file_part = form.get("clip") or form.get("file")
            raw = file_part.get("data") if isinstance(file_part, dict) else None
            if raw:
                from tempfile import NamedTemporaryFile

                tf = NamedTemporaryFile(delete=False, suffix=".mp4")
                tf.write(raw)
                tf.close()
                uploaded = Path(tf.name)
            try:
                data = STORE.end_user_broadcast(user, poi_id, uploaded_clip=uploaded)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except PermissionError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            finally:
                if uploaded:
                    try:
                        uploaded.unlink(missing_ok=True)
                    except OSError:
                        pass
            LOCAL_RELAY.force_stop(poi_id)
            return json_response(self, 200, {"success": True, "data": data})

        body = self._read_json()

        if path == "/api/v1/auth/register":
            try:
                user = STORE.register_user(
                    body.get("email", ""),
                    body.get("password", ""),
                    body.get("display_name", ""),
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if path == "/api/v1/auth/login":
            try:
                data = STORE.login_user(body.get("email", ""), body.get("password", ""))
            except ValueError as e:
                return json_response(self, 401, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/logout":
            STORE.logout_user(bearer_token(self))
            return json_response(self, 200, {"success": True, "message": "logged out"})

        if path == "/api/v1/pois":
            if require_admin(self) is None:
                return
            try:
                poi = STORE.create_poi({**body, "status": body.get("status", "published")})
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": asdict(poi)})

        if path == "/api/v1/pois/submit":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.submit_poi(user, body)
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "chat":
            user = require_user(self)
            if user is None:
                return
            try:
                msg = STORE.post_chat(parts[3], user, body.get("body") or body.get("text") or "")
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except PermissionError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": msg})

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "chat" and parts[5] == "mute":
            user = require_user(self)
            if user is None:
                return
            if not STORE.is_admin(user) and not STORE.is_poi_host(user, parts[3]):
                return json_response(self, 403, {"success": False, "error": "host or admin required"})
            try:
                data = STORE.mute_chat_user(
                    parts[3],
                    body.get("user_id", ""),
                    user["id"],
                    hours=body.get("hours"),
                    reason=body.get("reason") or "",
                )
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "approve":
            if require_admin(self) is None:
                return
            try:
                data = STORE.set_poi_status(parts[3], "published")
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "reject":
            if require_admin(self) is None:
                return
            try:
                data = STORE.set_poi_status(parts[3], "rejected")
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/admin/users":
            if require_admin(self) is None:
                return
            try:
                user = STORE.create_user_admin(body)
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 6 and parts[2] == "admin" and parts[3] == "users" and parts[5] == "block":
            if require_admin(self) is None:
                return
            user_id = parts[4]
            hours = float(body.get("hours", 24))
            from datetime import datetime, timedelta, timezone

            until = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
            if body.get("until"):
                until = body["until"]
            try:
                user = STORE.block_user(user_id, until)
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 6 and parts[2] == "admin" and parts[3] == "users" and parts[5] == "unblock":
            if require_admin(self) is None:
                return
            try:
                user = STORE.unblock_user(parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            return json_response(self, 200, {"success": True, "data": user})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "cameras":
            if require_admin(self) is None:
                return
            poi_id = parts[3]
            if body.get("view_mode") not in VIEW_MODES:
                return json_response(
                    self, 400, {"success": False, "error": f"view_mode must be one of {sorted(VIEW_MODES)}"}
                )
            if body.get("role") not in CAMERA_ROLES:
                return json_response(
                    self, 400, {"success": False, "error": f"role must be one of {sorted(CAMERA_ROLES)}"}
                )
            try:
                cam = STORE.add_camera(poi_id, body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            warn = STORE.validate_cameras(poi_id)
            payload = asdict(cam)
            if warn:
                payload["validation_warning"] = warn
            return json_response(self, 200, {"success": True, "data": payload})

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "stream" and parts[5] == "acquire":
            poi_id = parts[3]
            if app_env() == "prod" and require_user(self) is None:
                return
            cid = body.get("client_id") or "anonymous"
            wait = bool(body.get("wait_hls", True))
            # browser_usb: клиент держит FaceTime через getUserMedia — освобождаем ffmpeg
            if body.get("browser_usb") or body.get("publish") is False:
                LOCAL_RELAY.force_stop(poi_id)
                return json_response(
                    self,
                    200,
                    {
                        "success": True,
                        "data": {
                            "acquired": True,
                            "local_usb": True,
                            "browser_usb": True,
                            "clients": LOCAL_RELAY.active_clients(poi_id),
                        },
                    },
                )
            row = LOCAL_RELAY._row_for_poi(poi_id)
            if not row:
                return json_response(
                    self,
                    200,
                    {"success": True, "data": {"acquired": True, "local_usb": False, "clients": 0}},
                )
            ok = LOCAL_RELAY.acquire(poi_id, cid, wait_hls=wait)
            preview = LOCAL_RELAY.preview.status(poi_id)
            if preview.get("clip_url"):
                preview = {**preview, "clip_url": preview_clip_public_url(self, preview["clip_url"])}
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": {
                        "acquired": ok,
                        "local_usb": True,
                        "clients": LOCAL_RELAY.active_clients(poi_id),
                        "preview_clip": preview,
                    },
                },
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "stream" and parts[5] == "release":
            poi_id = parts[3]
            cid = body.get("client_id") or "anonymous"
            if body.get("force"):
                if require_admin(self) is None:
                    return
                LOCAL_RELAY.force_stop(poi_id)
            else:
                if app_env() == "prod" and require_user(self) is None:
                    return
                LOCAL_RELAY.release(poi_id, cid)
            return json_response(
                self,
                200,
                {"success": True, "data": {"clients": LOCAL_RELAY.active_clients(poi_id)}},
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "broadcast" and parts[5] == "end":
            user = require_user(self)
            if user is None:
                return
            poi_id = parts[3]
            uploaded = None
            ctype = self.headers.get("Content-Type", "")
            if "multipart/form-data" in ctype:
                form = parse_multipart(self)
                file_part = form.get("clip") or form.get("file")
                raw = None
                if isinstance(file_part, dict):
                    raw = file_part.get("data")
                elif isinstance(file_part, (bytes, bytearray)):
                    raw = file_part
                if raw and len(raw) > 0:
                    from tempfile import NamedTemporaryFile

                    tf = NamedTemporaryFile(delete=False, suffix=".mp4")
                    tf.write(raw)
                    tf.close()
                    uploaded = Path(tf.name)
            try:
                data = STORE.end_user_broadcast(user, poi_id, uploaded_clip=uploaded)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except PermissionError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            finally:
                if uploaded:
                    try:
                        uploaded.unlink(missing_ok=True)
                    except OSError:
                        pass
            LOCAL_RELAY.force_stop(poi_id)
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "kiosk-register":
            poi_id = parts[3]
            emb = body.get("face_embedding")
            embs = body.get("face_embeddings")
            acceptances = body.get("acceptances") or {}
            try:
                data = STORE.kiosk_register(
                    poi_id,
                    body.get("full_name", ""),
                    body.get("phone", ""),
                    body.get("favorite_menu_item", ""),
                    emb if isinstance(emb, list) else None,
                    acceptances,
                    client_meta={"ip": self.client_address[0]},
                    embeddings=embs if isinstance(embs, list) else None,
                    require_multi=True,
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            LOCAL_RELAY.restart_poi(poi_id)
            return json_response(
                self,
                200,
                {"success": True, "data": data, "message": data.get("message", "")},
            )

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "signature-bind":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.bind_signature(user["id"], parts[3])
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/performance/streams":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.performance_stream_start(
                    user["id"],
                    body.get("camera_id", ""),
                    body.get("title", ""),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/general/streams":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.general_stream_start(
                    user["id"],
                    body.get("camera_id", ""),
                    body.get("title", ""),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 6 and parts[2] == "general" and parts[3] == "streams" and parts[5] == "stop":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.general_stream_stop(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "recording not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/auth/platforms/link":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.link_platform_username(
                    user["id"], body.get("platform", ""), body.get("username", "")
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "platforms" and parts[4] == "comment":
            user = require_user(self)
            if user is None:
                return
            from platforms import get_adapter

            platform = parts[3]
            try:
                link = STORE.conn.execute(
                    "SELECT oauth_token FROM platform_links WHERE user_id = ? AND platform = ?",
                    (user["id"], platform),
                ).fetchone()
                if not link or not link["oauth_token"]:
                    raise ValueError("platform oauth required")
                adapter = get_adapter(platform)
                data = adapter.post_comment(
                    link["oauth_token"], body.get("broadcast_id", ""), body.get("text", "")
                )
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 6 and parts[2] == "performance" and parts[3] == "streams" and parts[5] == "stop":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.performance_stream_stop(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "stream not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "consent":
            user = require_user(self)
            if user is None:
                return
            poi_id = parts[3]
            emb = body.get("face_embedding")
            if isinstance(emb, list) and len(emb) != PATCH_DIM:
                return json_response(
                    self,
                    400,
                    {"success": False, "error": f"face_embedding must be {PATCH_DIM} floats"},
                )
            try:
                rec = STORE.grant_consent(poi_id, user["id"], emb)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "data": rec,
                    "message": "Consent recorded; linked to your wallet",
                },
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "cameras" and parts[5] == "sync":
            if require_admin(self) is None:
                return
            try:
                data = STORE.sync_poi_cameras(parts[3], body.get("cameras", []))
            except (KeyError, ValueError) as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            LOCAL_RELAY.refresh()
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/views":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.record_view(
                    user["id"],
                    body.get("camera_id", ""),
                    float(body.get("seconds", 0)),
                    float(body.get("ad_revenue", 0.01)),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        if path == "/api/v1/face-match":
            emb = body.get("embedding")
            if not isinstance(emb, list):
                return json_response(self, 400, {"success": False, "error": "embedding required"})
            try:
                vec = [float(x) for x in emb]
            except (TypeError, ValueError):
                return json_response(self, 400, {"success": False, "error": "invalid embedding"})
            hit = STORE.match_face_embedding(
                vec,
                prior_user_id=str(body.get("prior_user_id") or ""),
            )
            if not hit:
                return json_response(self, 200, {"success": True, "data": {"matched": False}})
            return json_response(self, 200, {"success": True, "data": hit})

        if path == "/api/v1/face-presence":
            # face-worker: пакет presence с worker-token; пользователь — только self
            items = body.get("presence")
            if items is None and body.get("user_id") and body.get("camera_id"):
                items = [
                    {
                        "user_id": body.get("user_id"),
                        "camera_id": body.get("camera_id"),
                        "seconds": body.get("seconds", 0),
                    }
                ]
            if not isinstance(items, list) or not items:
                return json_response(self, 400, {"success": False, "error": "presence[] required"})
            worker_ok = _worker_authorized(self)
            user = None
            if not worker_ok:
                user = require_user(self)
                if user is None:
                    return
            results = []
            for it in items:
                uid = it.get("user_id") or (user["id"] if user else "")
                if user and not STORE.is_admin(user) and uid != user["id"]:
                    return json_response(self, 403, {"success": False, "error": "forbidden"})
                try:
                    results.append(
                        STORE.record_face_presence(
                            uid,
                            it.get("camera_id") or body.get("camera_id", ""),
                            float(it.get("seconds", 0)),
                            it.get("period_key"),
                        )
                    )
                except KeyError:
                    return json_response(self, 404, {"success": False, "error": "not found"})
                except ValueError as e:
                    return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": {"results": results}})

        if path == "/api/v1/admin/reset-test-pois":
            if require_admin(self) is None:
                return
            try:
                n = STORE.clear_all_pois()
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": {"deleted": n}})

        if path == "/api/v1/admin/seed-demo":
            if require_admin(self) is None:
                return
            try:
                created = STORE.ensure_demo_fixtures()
            except ValueError as e:
                return json_response(self, 403, {"success": False, "error": str(e)})
            return json_response(
                self,
                200,
                {"success": True, "data": {"created": created, "pois": STORE.list_pois()}},
            )

        if path == "/api/v1/admin/health-snapshot":
            snap = STORE.record_health_snapshot(
                body.get("camera_id", ""),
                body.get("status", "unknown"),
                body.get("detail", ""),
            )
            return json_response(self, 200, {"success": True, "data": snap})

        if path == "/api/v1/donations":
            poi_id = body.get("poi_id", "")
            try:
                d = STORE.add_donation(
                    poi_id,
                    float(body.get("amount", 0)),
                    body.get("message", ""),
                    body.get("donor", "anonymous"),
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": d})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "airtime":
            try:
                entry = STORE.add_airtime(
                    parts[3], body.get("wallet", ""), float(body.get("seconds", 0))
                )
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "data": entry})

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        body = self._read_json()

        if path == "/api/v1/auth/profile":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.update_user_profile(user["id"], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "pois":
            user = require_user(self)
            if user is None:
                return
            poi_id = parts[3]
            if not STORE.is_admin(user) and not STORE.is_poi_host(user, poi_id):
                return json_response(self, 403, {"success": False, "error": "host or admin required"})
            # Hosts may only edit safe metadata fields
            if not STORE.is_admin(user):
                allowed = {
                    k: body[k]
                    for k in (
                        "name", "description", "promo_description", "city", "country",
                        "address", "comment", "facing_mode", "latitude", "longitude",
                    )
                    if k in body
                }
                body = allowed
            try:
                STORE.update_poi(poi_id, body)
                data = STORE.poi_payload(poi_id)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": data})

        if len(parts) == 4 and parts[2] == "cameras":
            if require_admin(self) is None:
                return
            try:
                cam = STORE.update_camera(parts[3], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            warn = STORE.validate_cameras(cam.poi_id)
            payload = asdict(cam)
            if warn:
                payload["validation_warning"] = warn
            return json_response(self, 200, {"success": True, "data": payload})

        if len(parts) == 5 and parts[2] == "admin" and parts[3] == "users":
            if require_admin(self) is None:
                return
            try:
                user = STORE.update_user_admin(parts[4], body)
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "data": user})

        json_response(self, 404, {"success": False, "error": "not found"})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]

        if len(parts) == 4 and parts[2] == "pois":
            if require_admin(self) is None:
                return
            try:
                STORE.delete_poi(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "poi not found"})
            return json_response(self, 200, {"success": True, "message": "poi deleted"})

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "chat":
            user = require_user(self)
            if user is None:
                return
            if not STORE.is_admin(user) and not STORE.is_poi_host(user, parts[3]):
                return json_response(self, 403, {"success": False, "error": "host or admin required"})
            try:
                STORE.delete_chat_message(parts[3], parts[5])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "message not found"})
            return json_response(self, 200, {"success": True, "message": "deleted"})

        if len(parts) == 7 and parts[2] == "pois" and parts[4] == "chat" and parts[5] == "mute":
            user = require_user(self)
            if user is None:
                return
            if not STORE.is_admin(user) and not STORE.is_poi_host(user, parts[3]):
                return json_response(self, 403, {"success": False, "error": "host or admin required"})
            STORE.unmute_chat_user(parts[3], parts[6])
            return json_response(self, 200, {"success": True, "message": "unmuted"})

        if len(parts) == 5 and parts[2] == "pois" and parts[4] == "mask-image":
            if require_admin(self) is None:
                return
            # fall through to existing mask delete below — keep original handler
            STORE.delete_mask_image(parts[3])
            LOCAL_RELAY.restart_poi(parts[3])
            return json_response(self, 200, {"success": True, "message": "mask removed"})

        if len(parts) == 5 and parts[2] == "admin" and parts[3] == "users":
            if require_admin(self) is None:
                return
            try:
                STORE.delete_user(parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "user not found"})
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "message": "user deleted"})

        if len(parts) == 5 and parts[2] == "auth" and parts[3] == "platforms":
            user = require_user(self)
            if user is None:
                return
            try:
                STORE.unlink_platform(user["id"], parts[4])
            except ValueError as e:
                return json_response(self, 400, {"success": False, "error": str(e)})
            return json_response(self, 200, {"success": True, "message": "platform unlinked"})

        if len(parts) == 5 and parts[2] == "performance" and parts[3] == "streams":
            user = require_user(self)
            if user is None:
                return
            try:
                STORE.performance_stream_delete(user["id"], parts[4])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "stream not found"})
            return json_response(self, 200, {"success": True, "message": "stream deleted"})

        if len(parts) == 4 and parts[2] == "cameras":
            if require_admin(self) is None:
                return
            try:
                poi_id = STORE.delete_camera(parts[3])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "camera not found"})
            warn = STORE.validate_cameras(poi_id)
            return json_response(
                self, 200, {"success": True, "message": "camera deleted", "validation_warning": warn}
            )

        if len(parts) == 6 and parts[2] == "pois" and parts[4] == "consent":
            user = require_user(self)
            if user is None:
                return
            try:
                data = STORE.revoke_consent(parts[3], parts[5], user_id=user["id"])
            except KeyError:
                return json_response(self, 404, {"success": False, "error": "not found"})
            return json_response(self, 200, {"success": True, "data": data})

        json_response(self, 404, {"success": False, "error": "not found"})


def main() -> None:
    print(f"Cmir API (Python) http://{HOST}:{PORT} — SQLite core")
    HTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
