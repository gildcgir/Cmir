#!/usr/bin/env bash
# GoPro USB → MediaMTX (raw) → face-worker → RTMP gopro_avatar → HLS в браузере
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${CMIR_API_URL:-http://localhost:8090}"
RTSP_IN="${CMIR_RTSP:-rtsp://127.0.0.1:8554/gopro_main}"
RTMP_OUT="${CMIR_RTMP_AVATAR:-rtmp://127.0.0.1:1935/gopro_avatar}"
HLS_AVATAR="${CMIR_HLS_AVATAR:-http://127.0.0.1:8888/gopro_avatar/index.m3u8}"

log() { echo ""; echo "==> $*"; }

log "1/5 API + MediaMTX"
curl -sf "$API/health" >/dev/null || {
  echo "Запустите API: python3 apps/api_py/server.py"
  exit 1
}
docker ps --format '{{.Names}}' | grep -q cmir-mediamtx || {
  echo "MediaMTX: cd apps/ingest && docker compose up -d"
  exit 1
}

log "2/5 Остановка старых ffmpeg / worker"
pkill -f "rtmp://127.0.0.1:1935/gopro_main" 2>/dev/null || true
pkill -f "rtmp://127.0.0.1:1935/gopro_avatar" 2>/dev/null || true
pkill -f "cmir_face.worker.*gopro_avatar" 2>/dev/null || true
sleep 1

log "3/5 GoPro → RTMP gopro_main (фон)"
export GOPRO_FPS="${GOPRO_FPS:-30}"
bash "$ROOT/scripts/gopro_usb_publish.sh" > /tmp/cmir_gopro_pub.log 2>&1 &
PUB_PID=$!
echo "  publish PID=$PUB_PID (лог: /tmp/cmir_gopro_pub.log)"

for i in $(seq 1 25); do
  if /usr/local/bin/ffmpeg -rtsp_transport tcp -i "$RTSP_IN" -frames:v 1 -f null - 2>/dev/null; then
    echo "  RTSP gopro_main OK"
    break
  fi
  sleep 1
  if [[ "$i" -eq 25 ]]; then
    echo "RTSP не готов. Проверьте GoPro Webcam + Show Preview."
    tail -20 /tmp/cmir_gopro_pub.log
    kill "$PUB_PID" 2>/dev/null || true
    exit 1
  fi
done

log "4/5 Face-worker → RTMP gopro_avatar (чёрные плашки на глаза)"
cd "$ROOT/apps/face-worker"
source .venv/bin/activate
python -m cmir_face.worker \
  --input "$RTSP_IN" \
  --output "$RTMP_OUT" \
  --mask eye-rect \
  --track-smooth 0.55 \
  > /tmp/cmir_avatar_worker.log 2>&1 &
WORKER_PID=$!
echo "  worker PID=$WORKER_PID (лог: /tmp/cmir_avatar_worker.log)"

for i in $(seq 1 20); do
  if curl -Ls "$HLS_AVATAR" 2>/dev/null | head -1 | grep -q EXT; then
    echo "  HLS gopro_avatar OK"
    break
  fi
  sleep 1
done

log "5/5 Готово"
echo ""
echo "  Смотреть LIVE (плашки на глаза):"
echo "    $HLS_AVATAR"
echo ""
echo "  Web: http://localhost:3000"
echo "       → кнопка «Live с аватарами» (поток gopro_avatar)"
echo ""
echo "  Сырой поток (без аватаров):"
echo "    http://127.0.0.1:8888/gopro_main/index.m3u8"
echo ""
echo "  Остановка:"
echo "    kill $PUB_PID $WORKER_PID"
echo "    pkill -f gopro_main; pkill -f gopro_avatar"
echo ""
echo "  Логи: tail -f /tmp/cmir_avatar_worker.log"
echo ""
echo "Держите GoPro в кадре — глаза закрываются чёрными прямоугольниками."
