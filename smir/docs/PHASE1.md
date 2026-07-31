# Фаза 1 — MVP (8–12 недель)

**Старт:** после [PHASE0.md](PHASE0.md).  
**Пошаговый гайд:** [GUIDE.md](GUIDE.md).

## Чеклист по неделям

### Недели 1–2 — Registry & admin

- [x] [GOPRO13.md](GOPRO13.md)
- [x] API: PATCH camera/POI, health, DELETE camera
- [x] `apps/admin`
- [x] MediaMTX `gopro_main` + docker-compose
- [x] E2E admin (`e2e_phase1_admin.py`)
- [ ] **Пилот с GoPro 13** — вручную по [GUIDE.md](GUIDE.md) шаг 9

### Недели 3–4 — Ingest + egress

- [x] `scripts/publish_demo_to_mediamtx.sh`, `gopro_usb_publish.sh`
- [x] Web: live HLS (hls.js) + `GET /cameras/{id}/playback`
- [x] `scripts/health_poll.py` + `POST /admin/health-snapshot`

### Недели 5–6 — Face pipeline + consent

- [x] Face-worker: RTSP + `--max-frames`, `--consent-threshold`
- [x] `DELETE /pois/{id}/consent/latest` (revoke embedding)
- [x] `scripts/live_face_pipeline.sh`

### Недели 7–8 — Карта + гео

- [x] POI `city` / `country`
- [x] Топы с `?city=&country=`
- [x] Web: фильтр на главной

### Недели 9–12 — Wallet, airtime, донаты

- [x] Mock wallet `GET /wallets/{address}`
- [x] Airtime `POST/GET .../airtime`
- [x] Donations `POST/GET /donations` (pending_moderation)
- [x] Web: кошелёк, донат, revoke consent

## Lab-скрипты

| Скрипт | Назначение |
|--------|------------|
| `scripts/start-lab.sh` | Всё сразу |
| `scripts/stop-lab.sh` | Остановка |
| `scripts/run_all_checks.sh` | E2E 0 + 1 |
| [GUIDE.md](GUIDE.md) | Полная инструкция |

## Критерии выхода Фазы 1

| # | Критерий | Статус |
|---|----------|--------|
| 1 | Admin + 3 view_mode | OK |
| 2 | Live HLS в браузере | OK (нужен publish) |
| 3 | Consent → revoke → снова avatar | OK (API) |
| 4 | GoPro pilot | **Частично** (lab / Webcam) |
| 5 | Wallet + airtime + donate | OK (mock) + Phase2 face UT |

## Следующая фаза

[PHASE2.md](PHASE2.md)
