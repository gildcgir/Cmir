#!/usr/bin/env bash
# Live: GoPro USB → MediaMTX → HLS + короткий face-worker с RTSP
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${SMIR_API_URL:-http://localhost:8090}"
HLS="${SMIR_HLS:-http://127.0.0.1:8888/gopro_main/index.m3u8}"
RTSP="rtsp://127.0.0.1:8554/gopro_main"
LIVE_SEC="${GOPRO_LIVE_SEC:-20}"
MAX_FRAMES="${SMIR_MAX_FRAMES:-450}"
GOPRO_FPS="${GOPRO_FPS:-30}"
FFMPEG="${FFMPEG:-/usr/local/bin/ffmpeg}"

log() { echo ""; echo "==> $*"; }

log "1/6 Проверка API и MediaMTX"
curl -sf "$API/health" >/dev/null || { echo "API не запущен: python3 apps/api_py/server.py"; exit 1; }
docker ps --format '{{.Names}}' | grep -q smir-mediamtx || {
  echo "MediaMTX не запущен: cd apps/ingest && docker compose up -d"
  exit 1
}

log "2/6 Остановка старых ffmpeg-паблишеров"
pkill -f "rtmp://127.0.0.1:1935/gopro_main" 2>/dev/null || true
sleep 1

log "3/6 Публикация с GoPro USB или stub-webcam (${LIVE_SEC}s)"
export GOPRO_FPS
# gopro_usb_publish.sh сам переключается на веб-камеру, если GoPro нет
bash "$ROOT/scripts/gopro_usb_publish.sh" &
PUB_PID=$!
sleep 6

# Если устройств не было — запасной loop файла
if ! kill -0 "$PUB_PID" 2>/dev/null; then
  echo "Камера недоступна — loop gopro_cv.mp4 → RTMP"
  /usr/local/bin/ffmpeg -re -stream_loop -1 -i "$ROOT/apps/web/media/gopro_cv.mp4" \
    -c:v libx264 -preset veryfast -tune zerolatency -f flv rtmp://127.0.0.1:1935/gopro_main &
  PUB_PID=$!
  sleep 4
fi

log "4/6 Проверка HLS"
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if curl -Ls "$HLS" 2>/dev/null | head -1 | grep -q EXT; then
    echo "HLS OK: $HLS"
    break
  fi
  sleep 1
  if [[ "$i" -eq 10 ]]; then
    kill "$PUB_PID" 2>/dev/null || true
    echo "HLS не отвечает: $HLS"
    exit 1
  fi
done

log "5/6 Face-worker с RTSP (до $MAX_FRAMES кадров)"
cd "$ROOT/apps/face-worker"
source .venv/bin/activate
export SMIR_RTSP="$RTSP"
export SMIR_MAX_FRAMES="$MAX_FRAMES"
python -m smir_face.worker \
  --input "$RTSP" \
  --output "$ROOT/apps/web/media/live_processed.mp4" \
  --max-frames "$MAX_FRAMES" \
  --mask face-bar --track-smooth 0.55 || WORKER_RC=$?
WORKER_RC=${WORKER_RC:-0}

kill "$PUB_PID" 2>/dev/null || true
wait "$PUB_PID" 2>/dev/null || true
[[ "$WORKER_RC" -eq 0 ]] || exit "$WORKER_RC"

log "6/6 Итог"
echo "  HLS live:  $HLS"
echo "  Web:       http://localhost:3000  → блок Live HLS → GoPro"
echo "  Обработка: $ROOT/apps/web/media/live_processed.mp4"
echo ""
echo "Для длительного live в отдельном терминале:"
echo "  bash scripts/gopro_usb_publish.sh"
