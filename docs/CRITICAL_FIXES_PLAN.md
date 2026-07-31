# План исправлений — 6 приоритетных пунктов аудита

Источник: `docs/APPS_AUDIT_REPORT.md` (Critical + Priority).

| # | Проблема | Решение | Статус |
|---|----------|---------|--------|
| C1 | Публичный dump `/consented-faces`, `/embeddings` | Worker-token для векторов; `POST /api/v1/face-match` для браузера | done |
| C2 | Plaintext templates + слабый ключ | Encrypt `face_templates`/`poi_embeddings`; `CMIR_DATA_KEY` обязателен в prod | done |
| C3 | Presence без auth вне prod | Всегда worker-token **или** JWT только для self | done |
| C4 | Acquire/release + public `force` | `force` → admin; prod acquire/release → auth; USB via `browser_usb` | done |
| C5 | Revoke оставляет embedding; admin/admin; слабые пороги | Wipe `face_embedding`; `CMIR_ADMIN_PASSWORD`; thresholds 0.82/0.75 | done |
| C6 | MediaPipe leak; lock на wait HLS | `detector.close()`; wait HLS вне lock | done |
