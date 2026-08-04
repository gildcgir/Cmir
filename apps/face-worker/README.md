# Cmir Face Worker

Детекция лиц и privacy-маски на видеопотоке (файл / RTSP → MP4 / RTMP).

## Движок

По умолчанию `--detector auto`:

1. **SCRFD (InsightFace `buffalo_l`)** — мелкие лица / толпа / RTSP общие планы  
   - SAHI-тайлинг (`--tile`, `--tile-grid 2x2`)  
   - ByteTrack-style трекинг + EMA сглаживание  
   - маска глаз по 5 keypoints с поворотом (affine) и `--bbox-pad 0.2`
2. **MediaPipe** — fallback, если InsightFace не установлен

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# файл
python -m cmir_face.worker --input ../ingest/samples/demo.mp4 --output /tmp/cmir_out.mp4 \
  --detector auto --mask eye-rect --bbox-pad 0.2

# RTSP → RTMP (lab)
python -m cmir_face.worker --input rtsp://127.0.0.1:8554/gopro \
  --output rtmp://127.0.0.1:1935/gopro_avatar \
  --detector scrfd --tile --tile-grid 2x2 --bbox-pad 0.2 --mask eye-rect
```

Первый запуск SCRFD скачает модели InsightFace (`~/.insightface/models/buffalo_l`).

## Флаги

| Флаг | Смысл |
|------|--------|
| `--detector auto\|scrfd\|mediapipe` | Движок детекции |
| `--tile` / `--no-tile` | Тайлинг для мелких лиц |
| `--tile-grid 2x2` | Сетка плиток |
| `--bbox-pad 0.2` | Запас +20% вокруг лица/глаз |
| `--track-smooth 0.45` | EMA сглаживание треков |
| `--mask eye-rect\|face-bar\|emoji` | Тип маски |
