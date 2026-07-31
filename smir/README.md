# Smir

Система мониторинга точек интереса (POI): live-камеры, автозамена лиц без согласия, consent-киоск, карта и топы, донаты и блокчейн-вознаграждение за время в кадре.

## Документация

| Документ | Описание |
|----------|----------|
| [docs/PLAN.md](docs/PLAN.md) | Полный план: фазы, тесты, релиз |
| [docs/USE_CASES.md](docs/USE_CASES.md) | **Сценарии пользователя (RU)** |
| [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) | Таблица приёмки |
| [docs/PHASE0.md](docs/PHASE0.md) | Фаза 0 — POC (закрыта) |
| [docs/GUIDE.md](docs/GUIDE.md) | **Пошаговый гайд (весь план)** |
| [docs/PHASE1.md](docs/PHASE1.md) | **Фаза 1 — MVP (текущая)** |
| [docs/GOPRO13.md](docs/GOPRO13.md) | Подключение GoPro HERO13 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура |
| [docs/API.md](docs/API.md) | REST API |

## Структура

```
smir/
├── apps/
│   ├── api/           # REST API (Rust)
│   ├── api_py/        # REST API (Python, Phase 0–1)
│   ├── admin/         # Admin UI: POI + камеры
│   ├── face-worker/   # CV: детект, аватары, match
│   ├── ingest/        # MediaMTX + docker-compose
│   ├── web/           # Карта, топы, плеер
│   └── consent-kiosk/
├── scripts/
└── docs/
```

## Быстрый старт

```bash
# Полная lab-среда (рекомендуется)
bash scripts/start-lab.sh

# Или только API + web
bash scripts/start-phase0.sh

# Admin: http://localhost:3000/../admin/index.html
# GoPro ingest (опционально):
cd apps/ingest && docker compose up -d

# E2E
python3 scripts/e2e_phase0.py
python3 scripts/e2e_phase1_admin.py
```

API: `http://localhost:8090`

## Текущий статус

- **Фаза 0** — закрыта ([PHASE0_RESULTS.md](docs/PHASE0_RESULTS.md))
- **Фаза 1 MVP** — закрыта по чеклисту ([PHASE1.md](docs/PHASE1.md), [ACCEPTANCE.md](docs/ACCEPTANCE.md)); пилот GoPro — ручной шаг
- **Фаза 2** — частично (auth/wallets/consents); остальное в [PHASE2.md](docs/PHASE2.md)
- **Use-cases:** [docs/USE_CASES.md](docs/USE_CASES.md)

## Тесты

```bash
cd smir && SMIR_ENV=test python3 -m pytest tests/ -v
# unit + functional (DOM/API static). E2E scripts требуют запущенный API:
# bash scripts/start-lab.sh && bash scripts/run_all_checks.sh
```

## Лицензия

Proprietary — Smir project.
