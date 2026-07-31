# Фаза 0 — Discovery & POC



**Срок:** 2–3 недели  

**Цель выхода:** 1 POI в lab, end-to-end consent → реальное лицо на general cam, публичный стрим с аватарами, latency целевой &lt; 3 с на consent-путь.



## Чеклист



### Неделя 1 — Основа



- [x] Репозиторий `smir`, план и архитектура

- [x] Скелет `apps/api`: POI + Camera registry (CRUD, валидация типов POI)

- [x] Описание API в `docs/API.md`

- [x] Seed: 1 demo POI типа `social_event` (2 general + 1 consent)

- [x] `apps/ingest`: конфиг MediaMTX (`mediamtx.yml`)



### Неделя 2 — Видео POC



- [x] `apps/face-worker`: detect faces (MediaPipe POC)

- [x] Overlay placeholder на bbox без consent (ellipse «penguin»)

- [x] In-memory consent store + match по embedding (упрощённый POC, Python API + patch 32×32)

- [x] Выход: MP4 тестовый поток (`scripts/generate_demo_video.py`, `apps/web/media/`)

- [x] `apps/web`: карта + топы + кнопка consent + плеер потоков



### Неделя 3 — Consent & интеграция



- [x] `apps/consent-kiosk`: минимальный UI «Даю разрешение»

- [x] API: `POST /consent` → запись embedding + mock wallet address (`apps/api_py`)

- [x] E2E: consent → лицо без аватара на general (`scripts/phase0_pipeline.sh`, 200/200 кадров)

- [x] Замер latency, запись в `docs/PHASE0_RESULTS.md`

- [x] Юридический черновик текста согласия в `docs/CONSENT_TEXT_DRAFT.md`



### Опционально (не блокирует POC)



- [ ] Rust `cargo test` в `apps/api` (нужен `rustup` на машине)

- [ ] RTSP/HLS через MediaMTX в lab (конфиг есть, поток не поднят)



## Критерии приёмки Фазы 0



| # | Критерий | Метод проверки | Статус |

|---|----------|----------------|--------|

| 1 | POI `social_event` не создаётся без ≥2 камер, ≥1 consent | Unit test API | POC Python + Rust тест в коде |

| 2 | Режимы камеры: `fisheye`, `standard`, `zoom2x` сохраняются | API + manual | OK (demo seed) |

| 3 | Без consent все лица с аватаром | `stream_avatar.mp4` | OK |

| 4 | После consent лицо того же человека без аватара | `stream_mixed.mp4` | OK |

| 5 | Mock wallet выдаётся при consent | API response | OK |

| 6 | Главная web показывает demo POI и % consent (mock) | Manual | OK |



## Не входит в Фазу 0



- Продакшен blockchain / ЦФА

- Карта мира и геолокация

- Донаты и goals

- GPU farm / K8s prod



## Следующая фаза



После закрытия чеклиста → **Фаза 1 MVP** (см. [PLAN.md](PLAN.md#6-фазы-разработки)).

