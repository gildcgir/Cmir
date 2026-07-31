# Smir — пошаговый гайд (весь план)

Выполняйте **по порядку**. Каждый шаг ссылается на скрипт или URL.  
GoPro HERO13 — в [GOPRO13.md](GOPRO13.md).

---

## Шаг 0. Один раз: зависимости

```bash
cd /Users/kit/RustProject/smir

# Python face-worker
cd apps/face-worker && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..

# Docker (для ingest) — установите Docker Desktop, если ещё нет
docker --version
```

Опционально: `brew install ffmpeg` — для публикации с GoPro/USB.

---

## Шаг 1. Запуск всей lab-среды

```bash
bash scripts/start-lab.sh
```

Поднимется:

| Сервис | URL |
|--------|-----|
| API | http://localhost:8090/health |
| Web | http://localhost:3000 |
| Admin | http://localhost:3000/../admin/index.html |
| Kiosk | http://localhost:3000/../consent-kiosk/index.html |
| MediaMTX HLS | http://127.0.0.1:8888/gopro_main/index.m3u8 |

Остановка: `bash scripts/stop-lab.sh`

---

## Шаг 2. Фаза 0 — проверка POC (уже сделано в коде)

```bash
python3 scripts/e2e_phase0.py
bash scripts/phase0_pipeline.sh
```

Откройте http://localhost:3000 — должны играть `stream_avatar.mp4` и `stream_mixed.mp4`.

---

## Шаг 3. Фаза 1 нед. 1–2 — Admin + GoPro POI

1. Admin → создайте POI **Pilot GoPro**, тип `social_event`, город Tbilisi.
2. Добавьте камеры:
   - **GoPro General** — `rtsp://127.0.0.1:8554/gopro_main`, `fisheye`
   - **General B** — `rtsp://127.0.0.1:8554/demo_general_b`, `zoom2x`
   - **Consent** — `rtsp://127.0.0.1:8554/gopro_consent`, `standard`
3. **Проверить поток** на каждой (до publish будет `unreachable` — нормально).

```bash
python3 scripts/e2e_phase1_admin.py
```

---

## Шаг 4. Фаза 1 нед. 3–4 — Ingest + live HLS

### 4a. Тест без GoPro (демо-файл в MediaMTX)

```bash
bash scripts/publish_demo_to_mediamtx.sh
```

### 4b. С GoPro по USB (когда камера под рукой)

```bash
# Отредактируйте имя устройства в скрипте при необходимости
bash scripts/gopro_usb_publish.sh
```

### 4c. Live на сайте

1. http://localhost:3000 → блок **Live HLS**
2. Выберите POI и камеру → **Смотреть live**
3. Должен играть поток `gopro_main` (если publish запущен).

### 4d. Health polling (фон)

```bash
python3 scripts/health_poll.py
# в другом терминале, раз в 60 с пишет снимок в API
```

---

## Шаг 5. Фаза 1 нед. 5–6 — Face pipeline на RTSP

```bash
# 30 секунд с RTSP → файл с аватарами
bash scripts/live_face_pipeline.sh

# С API consent (подставьте POI_ID из admin)
export SMIR_POI_ID=<uuid>
bash scripts/live_face_pipeline.sh --with-consent
```

На киоске дайте согласие → повторите pipeline → больше зелёных рамок.

Отзыв согласия (снова аватар):

```bash
curl -X DELETE "http://localhost:8090/api/v1/pois/$SMIR_POI_ID/consent/latest"
```

---

## Шаг 6. Фаза 1 нед. 7–8 — Гео-фильтр топов

1. На главной выберите **Город: Tbilisi**, **Страна: GE**.
2. Топы пересчитаются только по POI в этом регионе.

---

## Шаг 7. Фаза 1 нед. 9–12 — Wallet, airtime, донаты

1. Kiosk → согласие → в ответе `wallet_address`.
2. Главная → карточка **Кошелёк** → баланс ST/UT (mock).
3. **Донат** → форма на главной → `POST /api/v1/donations`.
4. Airtime: после live pipeline `GET /api/v1/pois/{id}/airtime`.

---

## Шаг 8. Все автопроверки

```bash
bash scripts/run_all_checks.sh
```

---

## Шаг 9. GoPro 13 — день съёмки (чеклист)

- [ ] Зарядка + питание от сети
- [ ] `docker compose` в `apps/ingest` работает
- [ ] Mac и GoPro в одной Wi‑Fi **или** USB webcam
- [ ] `gopro_usb_publish.sh` или RTMP URL в Quik
- [ ] Admin: health **reachable**
- [ ] Kiosk: consent с камеры ноутбука/телефона
- [ ] Live HLS на web без аватара после consent

---

## Дальше: Фаза 2–3

- [PHASE2.md](PHASE2.md) — beta, GDPR, нагрузка
- [PHASE3.md](PHASE3.md) — prod, ЦФА, mobile
