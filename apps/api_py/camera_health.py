"""Lightweight stream URL reachability probe (Phase 1 — no ffmpeg required)."""
from __future__ import annotations

import socket
import urllib.error
import urllib.request
from typing import Any, Dict
from urllib.parse import urlparse


def probe_stream_url(url: str, timeout: float = 2.5) -> Dict[str, Any]:
    if not url or not url.strip():
        return {"status": "invalid", "detail": "empty stream_url", "quality_score": 0}

    if url.startswith("local://"):
        return {"status": "local", "detail": "USB camera (local)", "quality_score": 95}

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()

    if scheme in ("rtsp", "rtsps"):
        host = parsed.hostname
        if not host:
            return {"status": "invalid", "detail": "missing host"}
        port = parsed.port or (322 if scheme == "rtsps" else 554)
        return _with_score(_tcp_probe(host, port, timeout, label=f"{scheme}://{host}:{port}"))

    if scheme in ("http", "https"):
        return _with_score(_http_probe(url, timeout))

    if scheme == "rtmp":
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 1935
        return _with_score(_tcp_probe(host, port, timeout, label=f"rtmp://{host}:{port}"))

    if scheme in ("file", ""):
        return {"status": "skipped", "detail": f"scheme {scheme or '(none)'} not probed in POC", "quality_score": 50}

    return {"status": "unknown", "detail": f"unsupported scheme: {scheme}", "quality_score": 0}


def _with_score(result: Dict[str, Any]) -> Dict[str, Any]:
    status = result.get("status", "unknown")
    scores = {
        "reachable": 92,
        "local": 95,
        "skipped": 50,
        "invalid": 0,
        "unreachable": 0,
        "unknown": 20,
    }
    result["quality_score"] = scores.get(status, 30)
    return result


def _tcp_probe(host: str, port: int, timeout: float, label: str) -> Dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"status": "reachable", "detail": f"TCP ok ({label})"}
    except OSError as e:
        return {"status": "unreachable", "detail": f"{label}: {e}"}


def _http_probe(url: str, timeout: float) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "status": "reachable",
                "detail": f"HTTP {resp.status}",
            }
    except urllib.error.HTTPError as e:
        if e.code < 500:
            return {"status": "reachable", "detail": f"HTTP {e.code}"}
        return {"status": "unreachable", "detail": str(e)}
    except Exception as e:
        return {"status": "unreachable", "detail": str(e)}
