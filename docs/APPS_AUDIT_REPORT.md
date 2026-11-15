# Cmir — повторный аудит `apps/` (2026-08-14)

Дата: 2026-08-14 (re-audit после закрытия 5 Critical + 5 High). Scope: `api_py`, `face-worker`, `web`/`consent-kiosk`, `android`.

Метод: статическая проверка фиксов + HTTP smoke на lab API `:8090` + pytest `tests/functional` + `tests/unit` (77 passed).

---

## Верификация прошлых Critical / Priority

| # | Было | Статус | Доказательство |
|---|------|--------|----------------|
| C1 | Публичный dump embeddings | **FIXED** | `GET /consented-faces` → 401 без worker token |
| C2 | Plaintext templates / слабый ключ | **FIXED** | `encrypt_embedding`; `CMIR_DATA_KEY` обязателен в prod |
| C3 | Presence без auth | **FIXED** | Worker token или JWT self |
| C4 | Acquire/release + public `force` | **FIXED** | `force` → admin; `browser_usb` → host/admin; GET playback/kiosk **не** acquire |
| C5 | Revoke / admin/admin / пороги | **FIXED** | `face_embedding = NULL`; `CMIR_ADMIN_PASSWORD` в prod |
| C6 | MediaPipe leak / lock на HLS | **PARTIAL** | LiveCamera `detector.close()` + stderr drain. Остаётся: kiosk Landmarker / mask-preview без `.close()` |

---

## Critical (были open 2026-07-31) — закрыты

1. **Public `POST /face-match` identity oracle** — **FIXED**. Rate-limit по IP (40/мин). Prod: JWT или worker. Lab anon: `{matched: true/false}` без `user_id` / `display_name` / `score`. JWT/worker получают identity. Smoke: anon match без PII.

2. **Worker revoke-cache `if fresh:`** — **FIXED**. `fetch_consented_faces_from_api` → `None` при ошибке, `[]` при HTTP 200 empty. `reload_consented` назначает, если `fresh is not None`.

3. **Unauthenticated airtime mint** — **FIXED**. `POST /pois/{id}/airtime` → admin. `GET` → любой auth user. Smoke: POST без токена → 401.

4. **`CMIR_ENV` defaults to `test`** — **FIXED**. `app_env()` без переменной → `prod` (fail-closed). `main()` отказывается биндить `0.0.0.0` без явного `CMIR_ENV`. Prod требует `CMIR_DATA_KEY`, `CMIR_ADMIN_PASSWORD`, `CMIR_WORKER_TOKEN`. Lab-скрипты задают `CMIR_ENV=test`.

5. **RTMP `stderr=PIPE` без reader** — **FIXED**. Drain-thread в `rtmp_writer.py` и `local_relay.py` (publisher + mask worker).

---

## High (были open #6–#10) — закрыты / принятый остаток

6. **`browser_usb` stealth `force_stop`** — **FIXED**. Нужен JWT + admin или POI host. Smoke: 401 без auth.

7. **C4 bypass: GET playback / kiosk-stream acquire** — **FIXED**. GET больше не вызывает `LOCAL_RELAY.acquire`. `stream_url` / `rtsp_url` убраны из playback.

8. **Open HLS / preview-clip / mask-image / CORS `*`** — **PARTIAL (принято)**. RTSP/direct URL закрыты. Публичный **masked HLS** и CORS `*` оставлены сознательно: карта/WebView смотрят защищённый поток без логина. Preview-clip и mask-image — публичные артефакты маски, не сырой RTSP.

9. **Donations / health-*** — **FIXED**. POST donations → user. GET donations / health-all / health / health-history / health-snapshot → admin. `stream_url` из health-ответов убран. GET `/cameras/{id}` стрипает `stream_url`/`device_id` для не-admin.

10. **Wallet lookup с PII** — **FIXED**. `get_wallet` отдаёт только address / user_id / balances / created_at (без email / display_name).

---

## High (ещё открыты)

11. **Kiosk register + temp password на экране**; enrollment timeout 9s = success (`face-enroll.js`).
12. **OAuth `state` без server store**; debug Android cleartext (release: `usesCleartextTraffic=false`; debug NSC разрешает cleartext).
13. **Orphan ffmpeg / double-worker race / no RTSP reconnect** (`local_relay`, `rtsp_capture`).
14. **Client-controlled `ad_revenue` on views** → UT inflation (`POST /views`).
15. **XSS via `innerHTML`** (admin/kiosk/user strings); kiosk `api()` без JWT на части вызовов.

---

## Medium (без изменений в этом проходе)

- Kiosk FaceLandmarker / `mask-preview.js` detector без `.close()`.
- PrivacyGate `frame.copy()` bounded RAM.
- Gallery cache ~150 кадров после revoke (~5s).
- Presence check-then-insert race.
- stdlib single-thread `HTTPServer` + blocking probes.
- Token в localStorage; длинные сессии.

---

## Memory leaks / races

| Область | Находка | Severity |
|---------|---------|----------|
| Browser LiveCamera | `detector.close()` на stop; stream больше не теряется, если MediaPipe падает | OK |
| RTMP / relay stderr | Drain thread | OK (was hang) |
| Gallery reload | Empty list now applied; lag ~reload interval | Medium |
| Kiosk enroll Landmarker | не закрывается | Medium |
| acquire browser_usb | host/admin only | OK |
| XSS innerHTML | admin/user/kiosk | High |

---

## Video bottlenecks (без изменений)

1. Тройное кодирование USB → RTMP → decode → MediaPipe → RTMP → HLS.  
2. PrivacyGate delay.  
3. Browser face-match RTT.  
4. PreviewBuffer ffmpeg.  
5. Blocking HLS probes в HTTP handlers.  
6. MediaPipe cold-start.  
7. Single USB device holder.

Дополнительно 2026-08-14: на Android камера открывается **до** MediaPipe; при падении detector — blur fallback (не чёрный экран / не повторный getUserMedia).

---

## Что относительно ок

- PBKDF2, session tokens через `secrets`.  
- Worker-token на biometric dump; templates encrypted at rest.  
- Face-match больше не identity oracle для анонимов.  
- Airtime mint, donations, health, browser_usb, GET acquire закрыты.  
- Wallet без email/display_name.  
- Fail-closed `CMIR_ENV` + bind guard.  
- ffmpeg stderr drain.  
- LiveCamera: getUserMedia first, no stream leak, mobile junk-ID filter.

---

## Приоритет следующих фиксов

1. XSS `innerHTML` + kiosk JWT.  
2. Enrollment timeout ≠ success; temp password не на экране.  
3. Cap/ignore client `ad_revenue`.  
4. OAuth state store; debug cleartext только localhost.  
5. Landmarker/mask-preview `.close()`; RTSP reconnect / process-group kill.  
6. Опционально: сузить CORS и preview-clip в prod.

Источники: code review + HTTP smoke 2026-08-14 + pytest 77 passed.
