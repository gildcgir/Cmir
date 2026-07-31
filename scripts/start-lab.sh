#!/usr/bin/env bash
# Cmir — поднять полную lab-среду (ingest + API + web + health poll)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT/.lab-pids"
mkdir -p "$PID_DIR"

echo "==> Cmir lab start (CMIR_ENV=${CMIR_ENV:-test})"
export CMIR_ENV="${CMIR_ENV:-test}"

if command -v docker >/dev/null 2>&1; then
  echo "==> MediaMTX (docker)"
  (cd "$ROOT/apps/ingest" && docker compose up -d) || echo "WARN: docker compose failed"
else
  echo "WARN: docker not found — ingest/HLS недоступен (см. docs/GUIDE.md)"
fi

if [[ ! -d "$ROOT/apps/face-worker/.venv" ]]; then
  echo "==> face-worker venv"
  python3 -m venv "$ROOT/apps/face-worker/.venv"
  "$ROOT/apps/face-worker/.venv/bin/pip" install -q -r "$ROOT/apps/face-worker/requirements.txt"
fi

echo "==> API :8090"
if pgrep -f "apps/api_py/server.py" >/dev/null 2>&1; then
  echo "    (restarting for fresh code)"
  pkill -f "apps/api_py/server.py" || true
  sleep 1
fi
nohup env CMIR_ENV="${CMIR_ENV:-test}" python3 "$ROOT/apps/api_py/server.py" >"$PID_DIR/api.log" 2>&1 &
echo $! >"$PID_DIR/api.pid"
disown || true

sleep 1
echo "==> Demo POI (test DB)"
CMIR_ENV="${CMIR_ENV:-test}" python3 "$ROOT/scripts/seed_test_poi.py" || echo "WARN: seed_test_poi failed"

echo "==> Web :3000"
ln -sfn "$ROOT/apps/consent-kiosk" "$ROOT/apps/web/kiosk" 2>/dev/null || true
if pgrep -f "http.server 3000" >/dev/null 2>&1; then
  echo "    (already running)"
else
  (
    cd "$ROOT/apps/web"
    nohup python3 -m http.server 3000 --bind 127.0.0.1 >"$PID_DIR/web.log" 2>&1 &
    echo $! >"$PID_DIR/web.pid"
  )
  disown || true
fi

echo "==> Health poll (background)"
if [[ -f "$PID_DIR/health.pid" ]] && kill -0 "$(cat "$PID_DIR/health.pid")" 2>/dev/null; then
  echo "    (already running)"
else
  nohup python3 "$ROOT/scripts/health_poll.py" >"$PID_DIR/health.log" 2>&1 &
  echo $! >"$PID_DIR/health.pid"
  disown || true
fi

echo "==> Camera → MediaMTX"
# Вечный FaceTime→gopro_main ломает local_usb / браузер: на iMac камера одна.
# Публикуем только если реально есть GoPro; иначе браузер берёт FaceTime напрямую.
if pgrep -f "rtmp://127.0.0.1:1935/gopro_main" >/dev/null 2>&1; then
  echo "    (publisher already running)"
elif /usr/local/bin/ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 | grep -qi "gopro"; then
  nohup bash "$ROOT/scripts/gopro_usb_publish.sh" >"$PID_DIR/camera-publish.log" 2>&1 &
  echo $! >"$PID_DIR/camera.pid"
  sleep 2
  if kill -0 "$(cat "$PID_DIR/camera.pid")" 2>/dev/null; then
    echo "    GoPro → rtmp://127.0.0.1:1935/gopro_main"
  else
    echo "    WARN: GoPro publish failed (см. .lab-pids/camera-publish.log)"
  fi
else
  # на всякий случай гасим старый stub-publish, чтобы не держать FaceTime
  pkill -f "rtmp://127.0.0.1:1935/gopro_main" 2>/dev/null || true
  echo "    GoPro нет — FaceTime остаётся свободной для браузера / local_usb"
fi

echo ""
echo "  API:    http://localhost:8090/health"
echo "  Web:    http://localhost:3000"
echo "  Admin:  http://localhost:3000/admin.html"
echo "  Kiosk:  http://localhost:3000/kiosk/index.html"
echo "  HLS:    http://127.0.0.1:8888/gopro_main/index.m3u8  (только с GoPro)"
echo ""
echo "  Camera: GoPro → MediaMTX; иначе веб-камера iMac в браузере (без вечного ffmpeg)"
echo "  Stop:   bash scripts/stop-lab.sh"
