# Cmir — таблица приёмки

Легенда: ✅ готово | 🔄 в работе | ⏳ не начато | ⚠️ доработка

## Фаза 0

| ID | Модуль | Критерий | Статус |
|----|--------|----------|--------|
| P0-1 | api | CRUD POI | ✅ |
| P0-2 | api | Валидация min cameras по типу | ✅ |
| P0-3 | api | CRUD Camera с role и view_mode | ✅ |
| P0-4 | face-worker | Detect + avatar overlay (file POC) | ✅ |
| P0-5 | consent | POST consent + mock wallet | ✅ |
| P0-6 | web | Карта + топы + consent demo | ✅ |
| P0-7 | e2e | Consent → face без аватара / с подписью | ✅ (client match + consented-faces) |

## Фаза 1

| ID | Модуль | Критерий | Статус |
|----|--------|----------|--------|
| P1-1 | ingest | RTSP → HLS / USB local | ✅ |
| P1-2 | map | Карта + POI panel + preview | ✅ |
| P1-3 | tops | API топы (admin stats) | ✅ |
| P1-4 | airtime | API airtime | ✅ (UI донатов/airtime — Phase 2 polish) |
| P1-5 | donate | API donations | ✅ (UI — Phase 2) |
| P1-6 | privacy | Revoke consent → remask | ✅ |
| P1-7 | preview | 10 с clip loop | ✅ |
| P1-8 | kiosk | Lock after register / recognize | ✅ |
| P1-9 | auth | Login phone or email after kiosk | ✅ |
| P2-1 | airtime | Face presence × camera + UT from ads | ✅ |

## Фаза 2–3

См. [PHASE2.md](PHASE2.md), [PHASE3.md](PHASE3.md). Осталось: ONNX GPU, scene narrator, staff goals, load test, GDPR export, PostgreSQL, ST/ЦФА, mobile, K8s.
