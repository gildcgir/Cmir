#!/usr/bin/env bash
# Натуральный тест Smir с GoPro USB (HERO13 Webcam)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${SMIR_API_URL:-http://localhost:8090}"
FFMPEG="${FFMPEG:-/usr/local/bin/ffmpeg}"
GOPRO_DEV="${GOPRO_DEVICE_INDEX:-}"  # auto-detect if empty
GOPRO_FPS="${GOPRO_FPS:-30}"
RECORD_SEC="${GOPRO_RECORD_SEC:-15}"
MEDIA="$ROOT/apps/web/media"
POI_NAME="GoPro Lab $(date +%H:%M)"

log() { echo ""; echo "==> $*"; }

need_api() {
  curl -sf "$API/health" >/dev/null || {
    echo "API не запущен. В другом терминале: python3 apps/api_py/server.py"
    exit 1
  }
}

log "1/7 Проверка GoPro в системе"
system_profiler SPCameraDataType 2>/dev/null | grep -A2 "GoPro" || true
if [[ -z "$GOPRO_DEV" ]]; then
  GOPRO_DEV=$("$FFMPEG" -f avfoundation -list_devices true -i "" 2>&1 \
    | grep -oE '\[[0-9]+\] GoPro Webcam' | head -1 | grep -oE '[0-9]+' || true)
fi
echo "GoPro avfoundation index: ${GOPRO_DEV:-NOT FOUND}"
[[ -z "$GOPRO_DEV" ]] && exit 1

need_api

log "2/7 Создание pilot POI + камеры GoPro"
POI_JSON=$(curl -sf -X POST "$API/api/v1/pois" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$POI_NAME\",\"poi_type\":\"social_event\",\"latitude\":41.7151,\"longitude\":44.8271,\"city\":\"Tbilisi\",\"country\":\"GE\",\"promo_description\":\"GoPro HERO13 live pilot\"}")
POI_ID=$(python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])" <<<"$POI_JSON")
echo "POI_ID=$POI_ID"

add_cam() {
  local name="$1" role="$2" mode="$3" url="$4"
  curl -sf -X POST "$API/api/v1/pois/$POI_ID/cameras" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\",\"stream_url\":\"$url\",\"role\":\"$role\",\"view_mode\":\"$mode\"}" >/dev/null
}

add_cam "GoPro General" general fisheye "rtsp://127.0.0.1:8554/gopro_main"
add_cam "General B" general zoom2x "rtsp://127.0.0.1:8554/demo_general_b"
add_cam "Consent cam" consent standard "rtsp://127.0.0.1:8554/gopro_consent"
echo "Камеры добавлены."

log "3/7 Запись ${RECORD_SEC}s с GoPro → файл"
mkdir -p "$MEDIA"
RAW_FULL="$MEDIA/gopro_raw_$(date +%Y%m%d_%H%M%S).mp4"
RAW_720="$MEDIA/gopro_720p_latest.mp4"
RAW="$MEDIA/gopro_cv.mp4"
# avfoundation: video index : no audio
"$FFMPEG" -y -f avfoundation -framerate "$GOPRO_FPS" -video_size 1920x1080 -i "${GOPRO_DEV}:none" \
  -t "$RECORD_SEC" -c:v libx264 -preset ultrafast "$RAW_FULL"
"$FFMPEG" -y -i "$RAW_FULL" -vf scale=1280:720 -pix_fmt yuv420p -c:v libx264 -preset fast "$RAW_720"
"$FFMPEG" -y -i "$RAW_720" -pix_fmt yuv420p -c:v libx264 -preset fast "$RAW"
echo "Записано: $RAW_FULL → $RAW (yuv420p для OpenCV)"

log "4/7 Face-worker: аватары (без consent)"
cd "$ROOT/apps/face-worker"
source .venv/bin/activate
python -m smir_face.worker --input "$RAW" --output "$MEDIA/gopro_avatar.mp4" \
  --mask face-bar --track-smooth 0.55

log "5/7 Consent + face-worker с match"
python3 << PY
import json, urllib.request, urllib.error, cv2
import mediapipe as mp
from smir_face.embeddings import patch_from_bbox

api = "$API"
poi_id = "$POI_ID"
raw = "$RAW"
email, password = "gopro@smir.test", "testpass123"
try:
    urllib.request.urlopen(urllib.request.Request(
        f"{api}/api/v1/auth/register",
        data=json.dumps({"email": email, "password": password, "display_name": "GoPro Lab"}).encode(),
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
cap = cv2.VideoCapture(raw)
ok, frame = cap.read()
cap.release()
if not ok:
    raise SystemExit("no frame")
h, w = frame.shape[:2]
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
det = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.4).process(rgb)
sig = None
if det.detections:
    b = det.detections[0].location_data.relative_bounding_box
    x, y = int(b.xmin * w), int(b.ymin * h)
    bw, bh = int(b.width * w), int(b.height * h)
    sig = patch_from_bbox(frame, x, y, bw, bh).tolist()
if sig is None:
    raise SystemExit("no face for consent embedding — наведите лицо при записи")

req = urllib.request.Request(
    f"{api}/api/v1/pois/{poi_id}/consent",
    data=json.dumps({"face_embedding": sig}).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST",
)
r = json.load(urllib.request.urlopen(req))
print("Wallet:", r["data"]["wallet_address"])
PY

python -m smir_face.worker \
  --input "$RAW" \
  --output "$MEDIA/gopro_consented.mp4" \
  --api-url "$API" \
  --poi-id "$POI_ID" \
  --consent-threshold 0.88 \
  --mask face-bar --track-smooth 0.55

log "6/7 API checks"
curl -sf "$API/api/v1/pois/$POI_ID/scene" | python3 -m json.tool | head -15
CAM_ID=$(curl -sf "$API/api/v1/pois/$POI_ID" | python3 -c "import json,sys; c=json.load(sys.stdin)['data']['cameras']; print([x['id'] for x in c if x['role']=='general'][0])")
echo "Camera health:"
curl -sf "$API/api/v1/cameras/$CAM_ID/health" | python3 -m json.tool

log "7/7 Итог"
echo ""
echo "  POI_ID=$POI_ID"
echo "  Сырьё:     $RAW"
echo "  Аватары:   $MEDIA/gopro_avatar.mp4"
echo "  Consent:   $MEDIA/gopro_consented.mp4"
echo "  Web:       http://localhost:3000"
echo "  Admin:     проверьте POI: $POI_NAME"
echo ""
if docker info >/dev/null 2>&1; then
  echo "  Для LIVE: в отдельном терминале:"
  echo "    bash scripts/gopro_usb_publish.sh"
  echo "  Затем на сайте: Смотреть live"
else
  echo "  Docker не запущен — live RTMP/HLS после: open -a Docker && cd apps/ingest && docker compose up -d"
fi
