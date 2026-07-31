# Smir — результаты Фазы 0

Замеры latency и прогон E2E. Обновляется скриптами `scripts/e2e_phase0.py` и `scripts/phase0_pipeline.sh`.

## Целевые метрики

| Метрика | Цель | Факт (2026-05-23) |
|---------|------|-------------------|
| Consent API (киоск → wallet) | &lt; 3 с | E2E ~18 ms; киоск UI — &lt; 500 ms (локально) |
| E2E API checks | все PASS | 7/7 PASS |
| Лица без consent | аватар на general | 200/200 кадров с аватаром (`stream_avatar.mp4`) |
| После consent + match | реальное лицо (зелёная рамка) | 200/200 кадров без аватара (`stream_mixed.mp4`) |

## Видео POC

| Файл | Описание |
|------|----------|
| `apps/ingest/samples/demo.mp4` | Исходный синтетический поток (8 с, 25 fps) |
| `apps/web/media/stream_avatar.mp4` | Обработка без consent — все лица с «пингвином» |
| `apps/web/media/stream_mixed.mp4` | После `POST /consent` + match по embedding — зелёная рамка |

**Примечание:** на macOS без ffmpeg запись MP4 через `imageio-ffmpeg`; MediaPipe не детектит синтетическое лицо — в pipeline используется `--demo-fallback` (bbox как в генераторе).

## Как воспроизвести

```bash
# Терминал 1
python3 apps/api_py/server.py

# Терминал 2
bash scripts/phase0_pipeline.sh

# Терминал 3
cd apps/web && python3 -m http.server 3000
# Открыть http://localhost:3000 и ../consent-kiosk/index.html

# E2E
python3 scripts/e2e_phase0.py
```

## Rust API (опционально)

На машине разработки `cargo` не установлен. Для unit-тестов API: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` → `cd apps/api && cargo test`.

## Прогоны

### E2E run 2026-05-23 12:25

- API: `http://localhost:8090`
- Duration: 18 ms
- health: ok
- list_pois: ok
- social_event_cameras: ok
- consent_wallet: ok
- embedding_stored: ok
- scene_mood: ok
- tops_consent: ok

### Video pipeline 2026-05-23 12:28

- Input: `demo.mp4` (200 frames)
- Without consent: avatars=200, real=0
- With consent + API embeddings: avatars=0, real=200
- Wallet example: `0xsmircd55de83336f49c794728790341487e9`

## E2E run 2026-05-23 12:42
- API: `http://localhost:8090`
- Duration: 15 ms
- health: ok
- list_pois: ok
- social_event_cameras: ok
- consent_wallet: ok
- embedding_stored: ok
- scene_mood: ok
- tops_consent: ok

## E2E run 2026-05-23 22:05
- API: `http://localhost:8090`
- Duration: 165 ms
- health: ok
- create_poi: ok
- camera_General A: ok
- camera_General B: ok
- camera_Consent: ok
- consent_wallet: ok
- embedding_stored: ok
- scene_mood: ok
- tops_consent: ok

## E2E run 2026-06-19 14:24
- API: `http://localhost:8090`
- Duration: 284 ms
- health: ok
- create_poi: ok
- camera_General A: ok
- camera_General B: ok
- camera_Consent: ok
- consent_wallet: ok
- embedding_stored: ok
- scene_mood: ok
- tops_consent: ok

## E2E run 2026-06-19 16:29
- API: `http://localhost:8090`
- Duration: 244 ms
- health: ok
- create_poi: ok
- camera_General A: ok
- camera_General B: ok
- camera_Consent: ok
- consent_wallet: ok
- embedding_stored: ok
- scene_mood: ok
- tops_consent: ok
