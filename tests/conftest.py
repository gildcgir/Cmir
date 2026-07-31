"""Общие фикстуры для unit и functional тестов Cmir."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API_PY = ROOT / "apps" / "api_py"
WEB = ROOT / "apps" / "web"
FACE_WORKER = ROOT / "apps" / "face-worker"

if str(API_PY) not in sys.path:
    sys.path.insert(0, str(API_PY))
if str(FACE_WORKER) not in sys.path:
    sys.path.insert(0, str(FACE_WORKER))


@pytest.fixture()
def tmp_db_path(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Path(path)
    monkeypatch.setenv("CMIR_ENV", "test")
    monkeypatch.setenv("CMIR_DB_PATH", str(db))
    yield db
    if db.is_file():
        db.unlink(missing_ok=True)


@pytest.fixture()
def store(tmp_db_path):
    from store import Store

    return Store()


@pytest.fixture(scope="module")
def api_server():
    """HTTP API на свободном порту (один на модуль)."""
    from http.server import HTTPServer

    import server as api_server_mod

    os.environ.setdefault("CMIR_ENV", "test")
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["CMIR_DB_PATH"] = path
    from store import Store

    api_server_mod.STORE = Store()
    api_server_mod.LOCAL_RELAY = api_server_mod.LocalRelay(api_server_mod.STORE)

    httpd = HTTPServer(("127.0.0.1", 0), api_server_mod.Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    _wait_http(f"{base}/api/v1/pois")
    yield base
    httpd.shutdown()
    Path(path).unlink(missing_ok=True)


def _wait_http(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError(f"server not ready: {url}")


@pytest.fixture()
def api_get(api_server):
    def _get(path: str):
        with urllib.request.urlopen(f"{api_server}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode())

    return _get


@pytest.fixture()
def web_root():
    return WEB
