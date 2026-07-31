#!/usr/bin/env bash
# Cmir Phase 0 — full video pipeline (order: sample → process → serve)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${CMIR_API_URL:-http://localhost:8090}"
OUT_DIR="$ROOT/apps/web/media"
SAMPLES="$ROOT/apps/ingest/samples"
DEMO_IN="$SAMPLES/demo.mp4"
if [[ ! -f "$DEMO_IN" && -f "$SAMPLES/demo.avi" ]]; then
  DEMO_IN="$SAMPLES/demo.avi"
fi
DEMO_OUT="$OUT_DIR/stream_avatar.mp4"
DEMO_CONSENTED="$OUT_DIR/stream_mixed.mp4"

echo "==> 1/4 Generate demo input video"
python3 "$ROOT/scripts/generate_demo_video.py"

echo "==> 2/4 Face worker — all avatars (no consent)"
mkdir -p "$OUT_DIR"
(
  cd "$ROOT/apps/face-worker"
  if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
  source .venv/bin/activate
  pip install -q -r requirements.txt
  python -m cmir_face.worker --input "$DEMO_IN" --output "$DEMO_OUT" --demo-fallback
)

echo "==> 3/4 Fetch demo POI id"
POI_ID=$(python3 -c "
import json, urllib.request
d=json.load(urllib.request.urlopen('$API_URL/api/v1/pois'))
print(d['data'][0]['id'])
")
echo "POI_ID=$POI_ID"

echo "==> 4/4 Register consent embedding (demo bbox) + re-process"
(
  cd "$ROOT/apps/face-worker"
  source .venv/bin/activate
  python3 << PY
import json, urllib.request, urllib.error, cv2
from cmir_face.embeddings import patch_from_bbox

api = "$API_URL"
poi_id = "$POI_ID"
email, password = "phase0@cmir.test", "testpass123"
try:
    urllib.request.urlopen(urllib.request.Request(
        f"{api}/api/v1/auth/register",
        data=json.dumps({"email": email, "password": password, "display_name": "Phase0"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    ))
except urllib.error.HTTPError:
    pass
login = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{api}/api/v1/auth/login",
    data=json.dumps({"email": email, "password": password}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)))
token = login["data"]["token"]
cap = cv2.VideoCapture("$DEMO_IN")
_, frame = cap.read()
cap.release()
h, w = frame.shape[:2]
x, y, bw, bh = int(w * 0.25) - 55, h // 2 - 70, 110, 140
sig = patch_from_bbox(frame, x, y, bw, bh).tolist()

req = urllib.request.Request(
    f"{api}/api/v1/pois/{poi_id}/consent",
    data=json.dumps({"face_embedding": sig}).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST",
)
resp = json.load(urllib.request.urlopen(req))
print("Consent:", resp.get("data", {}).get("wallet_address", "?"))
PY
)

(
  cd "$ROOT/apps/face-worker"
  source .venv/bin/activate
  python -m cmir_face.worker \
    --input "$DEMO_IN" \
    --output "$DEMO_CONSENTED" \
    --api-url "$API_URL" \
    --poi-id "$POI_ID" \
    --demo-fallback
)

echo ""
echo "Done."
echo "  Avatar-only:  file://$DEMO_OUT"
echo "  With consent: file://$DEMO_CONSENTED"
echo "  Web: http://localhost:3000 (run: cd apps/web && python3 -m http.server 3000)"
echo "  API must be running: python3 apps/api_py/server.py"
