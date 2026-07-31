#!/usr/bin/env bash
# GoPro / USB webcam → RTMP MediaMTX (macOS AVFoundation)
# Если GoPro не найдена — заглушка: встроенная / USB веб-камера.
set -euo pipefail
FFMPEG="${FFMPEG:-/usr/local/bin/ffmpeg}"
# Индекс: FaceTime=0, OBS=1, GoPro Webcam=2 (типично). Пусто → авто-поиск GoPro → webcam.
GOPRO_INDEX="${GOPRO_DEVICE_INDEX:-}"
GOPRO_FPS="${GOPRO_FPS:-30}"
VIDEO_SIZE="${GOPRO_VIDEO_SIZE:-}"
SOURCE_NAME="GoPro Webcam"
STUB=0

pick_avfoundation_index() {
  # args: mode = gopro | webcam
  local mode="$1"
  { "$FFMPEG" -f avfoundation -list_devices true -i "" 2>&1 || true; } | python3 -c '
import re, sys
mode = sys.argv[1]
text = sys.stdin.read()
in_v = False
devices = []
for line in text.splitlines():
    if "AVFoundation video devices" in line:
        in_v = True
        continue
    if "AVFoundation audio devices" in line:
        in_v = False
        continue
    if not in_v:
        continue
    m = re.search(r"\[(\d+)\]\s+(.+)", line)
    if m:
        devices.append((int(m.group(1)), m.group(2).strip()))

def skip(name: str) -> bool:
    low = name.lower()
    return any(
        x in low
        for x in ("obs", "virtual", "continuity", "iphone", "blackhole", "capture screen")
    )

if mode == "gopro":
    for idx, name in devices:
        if "gopro" in name.lower():
            print(f"{idx}\t{name}")
            raise SystemExit(0)
    raise SystemExit(1)

# webcam stub: prefer FaceTime / built-in (iMac) / USB cam, skip virtual
ranked = []
for idx, name in devices:
    if skip(name):
        continue
    if "gopro" in name.lower():
        continue
    low = name.lower()
    score = 0
    if "facetime" in low or "built-in" in low or "встроенн" in low:
        score = 3
    elif "webcam" in low or "usb" in low or "camera" in low or "камер" in low:
        score = 1
    ranked.append((score, idx, name))
ranked.sort(key=lambda t: (-t[0], t[1]))
if ranked:
    _, idx, name = ranked[0]
    print(f"{idx}\t{name}")
    raise SystemExit(0)
raise SystemExit(1)
' "$mode"
}

if [[ -z "$GOPRO_INDEX" ]]; then
  if FOUND=$(pick_avfoundation_index gopro 2>/dev/null); then
    GOPRO_INDEX="${FOUND%%$'\t'*}"
    SOURCE_NAME="${FOUND#*$'\t'}"
  elif FOUND=$(pick_avfoundation_index webcam 2>/dev/null); then
    GOPRO_INDEX="${FOUND%%$'\t'*}"
    SOURCE_NAME="${FOUND#*$'\t'}"
    STUB=1
  fi
fi

if [[ -z "$GOPRO_INDEX" ]]; then
  echo "Ни GoPro, ни веб-камера не найдены. Список:"
  "$FFMPEG" -f avfoundation -list_devices true -i "" 2>&1 | grep -E 'AVFoundation|^\[' || true
  echo "Подключите камеру или см. docs/GOPRO13.md"
  exit 1
fi

if [[ -z "$VIDEO_SIZE" ]]; then
  if [[ "$STUB" -eq 1 ]]; then
    VIDEO_SIZE="1280x720"
  else
    VIDEO_SIZE="1920x1080"
  fi
fi

RTMP="${CMIR_RTMP:-rtmp://127.0.0.1:1935/gopro_main}"

if ! command -v "$FFMPEG" >/dev/null 2>&1 && ! [[ -x "$FFMPEG" ]]; then
  echo "Установите ffmpeg: brew install ffmpeg"
  exit 1
fi

if [[ "$STUB" -eq 1 ]]; then
  echo "⚠ GoPro не обнаружена — заглушка: веб-камера «${SOURCE_NAME}» (index $GOPRO_INDEX)"
else
  echo "Источник: $SOURCE_NAME (avfoundation index $GOPRO_INDEX)"
fi
echo "RTMP: $RTMP  size=$VIDEO_SIZE fps=$GOPRO_FPS"
echo "Список: $FFMPEG -f avfoundation -list_devices true -i \"\""
echo "Ctrl+C для остановки"
echo ""

exec "$FFMPEG" -f avfoundation -pixel_format uyvy422 -framerate "$GOPRO_FPS" -video_size "$VIDEO_SIZE" -i "${GOPRO_INDEX}:none" \
  -an -pix_fmt yuv420p -c:v libx264 -preset veryfast -tune zerolatency -g 60 -f flv "$RTMP"
