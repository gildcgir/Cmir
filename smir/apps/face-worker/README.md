# Smir Face Worker (Phase 0 POC)

Детекция лиц и наложение аватаров на видеопоток.

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m smir_face.worker --input ../ingest/samples/demo.mp4 --output /tmp/smir_out.mp4
```

## Следующие шаги

- [ ] MediaPipe face detection
- [ ] Overlay PNG avatars
- [ ] Consent embedding match (stub)
- [ ] Push to RTSP/HLS
