# Фаза 2 — Beta

**Старт:** после закрытия [PHASE1.md](PHASE1.md).  
**GoPro pilot:** считается **частично пройденным** (lab USB/Webcam + скрипты; полный полевой прогон — по мере площадок).

## Чеклист

- [x] SQLite users, sessions, wallets, consents (`apps/api_py/`)
- [x] Auth API + web/kiosk login (телефон / email + временный пароль)
- [x] **UT loyalty: face presence × camera + доля от 1 UT после эфира**
  - `POST /api/v1/face-presence` — секунды лица в кадре
  - face-worker / LiveCameraView шлют presence при match
  - `POST .../streams/{id}/stop` — `ut = min(1, presence / stream_duration)`
- [ ] ONNX / GPU face pipeline (улучшение match; POC 32×32 остаётся)
- [ ] Scene narrator (LLM шаблоны)
- [ ] Staff goals + chat
- [ ] Load test N×720p
- [x] GDPR: revoke consent (+ UI); export — ещё нет
- [ ] PostgreSQL + PostGIS (миграция с SQLite)

## Модель UT

1. Face-worker / клиент копит **секунды присутствия** `(user_id, camera_id)`.
2. На остановке stream: длительность `T`, у участника `t_i`.
3. Начисление: `ut_i = min(1, t_i / T)` — **1 UT = весь стрим**.
4. `stream_presence_rewards` UNIQUE `(stream_id, user_id)` — без повторного начисления.

## Выход фазы

3–5 pilot POI, staging SLA, privacy audit draft; стабильный airtime→UT на lab.
