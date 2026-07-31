# Smir — архитектура

## Контекст

Smir агрегирует видеопотоки с камер в точках интереса (POI), обрабатывает лица по политике согласия, формирует описание сцены и показывает рейтинги на карте. Участники с согласием получают кошелёк и учёт времени в кадре для доли дохода; токены ST (ЦФА) и UT (лояльность) — отдельный контур.

## Диаграмма

```
[Cameras] → [Ingest] → [Face Worker] → [Egress HLS/WebRTC]
                ↓              ↑
         [Consent Kiosk] → [Consent API] → [Embedding DB]
                ↓
         [Wallet Service] → [Chain Adapter]

[Web / Mobile] → [API] → PostgreSQL + PostGIS
                      → Redis (sessions, cache)
```

## Сервисы

| Сервис | Ответственность | Стек (целевой) |
|--------|-----------------|----------------|
| **api** | POI, cameras, consent, tops, airtime | Rust, Axum, SQLx |
| **face-worker** | Detect, track, embed, avatar, metrics | Python, ONNX |
| **ingest** | RTSP in, relay | MediaMTX, FFmpeg |
| **stream-egress** | HLS/WebRTC out | FFmpeg, CDN |
| **consent-kiosk** | UI согласия | Flutter / Electron |
| **web** | Карта, топы, плеер | Next.js / React |
| **wallet-service** | Создание кошелька при consent | Rust + chain RPC |
| **privacy** | Retention, delete, audit | Policy + jobs |

## Модель POI и камер

### Типы POI

| Тип | Min cameras | Min consent cameras |
|-----|-------------|---------------------|
| `live_cam` | 1 | 0 |
| `social_event` | 2 | 1 |
| `venue` | 3 | 2 |

### Роли камер

- `general` — публичный поток с аватарами
- `consent` — кнопка согласия, захват embedding

### Режимы изображения

- `fisheye` — коррекция рыбьего глаза
- `standard` — без трансформации
- `zoom2x` — центральный crop ×2

## Поток согласия

1. Посетитель подходит к consent-камере.
2. Нажимает «Даю разрешение» → API сохраняет embedding + создаёт wallet (mock/testnet на POC).
3. Face-worker обновляет кэш разрешённых лиц для POI.
4. На general-камерах track с match больше не получает avatar overlay.
5. Airtime ledger пишет интервалы `visitor_seen` / `visitor_left`.

## Описание сцены

Каждые N секунд:

- `consent_rate = real_faces / total_faces`
- Если `avatar_faces > real_faces` → юмористический шаблон / LLM
- Иначе → промо-описание POI из CMS

## Топы на главной

1. По **% согласий** (выше — лучше).
2. По **числу участников** (уникальные за окно 24h).

Фильтр: район / город / страна / мир (геолокация пользователя).

## Безопасность и PII

- Embeddings шифруются at rest; TTL и право удаления.
- Сырой видеоархив — opt-in, короткий retention.
- Consent text version в каждой записи.
- Admin RBAC, audit log доступа к PII.

## Связь с The Hot Pot Spot

Переиспользуем **паттерны** (consent API, JWT, ST/UT), не код 1:1. Smir — отдельный продукт и репозиторий.
