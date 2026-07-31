#!/usr/bin/env bash
# RTSP live → face-worker → MP4 (Phase 1 weeks 5-6)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="${CMIR_RTSP:-rtsp://127.0.0.1:8554/gopro_main}"
OUT="$ROOT/apps/web/media/live_processed.mp4"
API="${CMIR_API_URL:-http://localhost:8090}"
MAX_FRAMES="${CMIR_MAX_FRAMES:-300}"
POI_ID="${CMIR_POI_ID:-}"

cd "$ROOT/apps/face-worker"
source .venv/bin/activate

ARGS=(--input "$INPUT" --output "$OUT" --max-frames "$MAX_FRAMES")
if [[ "$*" == *"--with-consent"* ]] && [[ -n "$POI_ID" ]]; then
  ARGS+=(--api-url "$API" --poi-id "$POI_ID" --consent-threshold 0.92)
elif [[ -n "$POI_ID" ]]; then
  ARGS+=(--api-url "$API" --poi-id "$POI_ID")
fi

echo "Input: $INPUT -> $OUT (max $MAX_FRAMES frames)"
python -m cmir_face.worker "${ARGS[@]}"
echo "Done: file://$OUT"
