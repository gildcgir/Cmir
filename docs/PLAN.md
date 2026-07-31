# Cmir — план реализации

Полная версия плана продукта. Текущий прогресс: [PHASE0.md](PHASE0.md).

---

## 1. Продукт

- Камеры в POI → live с **аватарами** для несогласивших.
- Consent-камера + кнопка → запоминание лица + **кошелёк**.
- Описание сцены: юмор vs промо по доле реальных лиц.
- Карта + топы (% согласий, участники).
- Донаты, сообщения, цели персоналу.
- Учёт **времени в кадре** → доля дохода; **ST** (ЦФА) + **UT** (лояльность).

---

## 2. Фазы

### Фаза 0 — Discovery & POC (2–3 недели)

См. [PHASE0.md](PHASE0.md).

**Выход:** 1 POI lab, consent E2E, стрим с аватарами.

### Фаза 1 — MVP (8–12 недель)

| Недели | Deliverable |
|--------|-------------|
| 1–2 | POI/Camera registry, admin, 3 режима |
| 3–4 | Ingest + egress, web player |
| 5–6 | Face pipeline + consent |
| 7–8 | Карта + 2 топа + гео |
| 9–10 | Wallet testnet, airtime |
| 11–12 | Донаты fiat, модерация |

### Фаза 2 — Beta (6–8 недель)

Масштаб CV, scene narrator, UT, staff goals, нагрузка, GDPR tooling.

### Фаза 3 — Production

ST/ЦФА, revenue split, edge agents, mobile stores.

---

## 3. Что программировать

| Модуль | Функции |
|--------|---------|
| poi-service | CRUD POI, гео, типы, валидация камер |
| camera-service | Подключение RTSP, режимы, health |
| stream-ingest | MediaMTX, FFmpeg, очередь кадров |
| face-pipeline | Detect, track, embed, avatar, airtime |
| consent-service | Кнопка, embedding, wallet trigger |
| scene-narrator | Метрики → текст |
| tops-api | Сортировки, bbox фильтр |
| staff-engagement | Донаты, goals, chat |
| wallet + chain | Кошелёк, ST/UT ledger |
| privacy | Retention, delete, audit |

Детали: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 4. Стек

| Слой | Технологии |
|------|------------|
| API | Rust, Axum, SQLx, PostGIS |
| CV | Python, FastAPI, MediaPipe/ONNX |
| Video | MediaMTX, FFmpeg |
| DB | PostgreSQL, Redis |
| Web | React/Next, Mapbox |
| Mobile | Flutter |
| Infra | Docker, K8s / Fly.io, Prometheus |

---

## 5. Тестирование

| Уровень | Объект |
|---------|--------|
| Unit | Правила POI, consent rate, crop modes |
| Integration | API + DB, mock RTSP |
| CV golden | Кадры → ожидаемый overlay |
| E2E | Consent → лицо без аватара |
| Load | N потоков 720p |
| Privacy | Delete consent → снова avatar |

KPI: consent &lt; 2 с до real face; match &gt; 95% на валидации; ingest 99.5%.

---

## 6. Релиз и хостинг

**Окружения:** dev → staging (1 pilot POI) → prod.

| Компонент | Хостинг |
|-----------|---------|
| API | K8s / Fly.io |
| CV GPU | Node pool L4/T4 |
| Media | MediaMTX + CDN HLS |
| DB | Managed PostgreSQL |
| Web | Vercel / Cloudflare Pages |

**CI/CD:** PR → tests → Docker → staging smoke → canary prod.

---

## 7. Риски

- Биометрия / закон — юрист, минимизация данных.
- Latency — edge + WebRTC для premium.
- False match — высокий threshold + re-verify на consent cam.
- Crypto/ЦФА — отдельный legal track.

---

## 8. Первые шаги

1. [x] Репозиторий + docs
2. [x] POC видео (face-worker + file pipeline)
3. [x] Consent + mock wallet
4. [ ] Pilot POI с GoPro 13 ([GOPRO13.md](GOPRO13.md)) — ручной шаг на железе
5. [x] Фаза 1 MVP (admin, ingest, face, карта, wallet API, kiosk, preview 10с, revoke)
6. [~] Фаза 2 — частично (auth/SQLite); остальное в PHASE2.md
7. [ ] Фаза 3 — Production
