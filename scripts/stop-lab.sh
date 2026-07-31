#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT/.lab-pids"

for f in api web health camera; do
  if [[ -f "$PID_DIR/$f.pid" ]]; then
    kill "$(cat "$PID_DIR/$f.pid")" 2>/dev/null || true
    rm -f "$PID_DIR/$f.pid"
  fi
done
pkill -f "apps/api_py/server.py" 2>/dev/null || true
pkill -f "scripts/health_poll.py" 2>/dev/null || true
pkill -f "rtmp://127.0.0.1:1935/gopro_main" 2>/dev/null || true
pkill -f "scripts/gopro_usb_publish.sh" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  (cd "$ROOT/apps/ingest" && docker compose down) 2>/dev/null || true
fi
echo "Cmir lab stopped."
