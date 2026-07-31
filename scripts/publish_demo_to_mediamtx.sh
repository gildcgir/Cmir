#!/usr/bin/env bash
# Публикует demo.mp4 в MediaMTX path gopro_main (loop)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO="$ROOT/apps/ingest/samples/demo.mp4"
RTMP="${CMIR_RTMP:-rtmp://127.0.0.1:1935/gopro_main}"

if [[ ! -f "$VIDEO" ]]; then
  python3 "$ROOT/scripts/generate_demo_video.py"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found."
  echo "Install: brew install ffmpeg"
  echo "Or use imageio in face-worker only for file POC."
  exit 1
fi

echo "Publishing $VIDEO -> $RTMP (loop, Ctrl+C to stop)"
exec ffmpeg -re -stream_loop -1 -i "$VIDEO" \
  -c:v libx264 -preset veryfast -tune zerolatency -f flv "$RTMP"
