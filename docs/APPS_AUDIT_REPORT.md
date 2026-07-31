# Cmir — повторный аудит `apps/` (после C1–C6)

Дата: 2026-07-31 (re-audit). Scope: `api_py`, `face-worker`, `web`/`consent-kiosk`, `android`.

Контекст: критичные пункты прошлого аудита закрыты. Ниже — **верификация фиксов** и **оставшийся** риск (security / architecture / bugs / performance). Lab-стек; Critical особенно опасны вне localhost.

---

## Верификация прошлых Critical / Priority

| # | Было | Статус | Доказательство |
|---|------|--------|----------------|
| C1 | Публичный dump embeddings | **FIXED** | `GET /consented-faces` → 401 без `X-Cmir-Worker`; браузер → `POST /face-match` |
| C2 | Plaintext templates / слабый ключ | **FIXED** | `encrypt_embedding` на `poi_embeddings`/`face_templates`; `CMIR_DATA_KEY` обязателен в prod |
| C3 | Presence без auth | **FIXED** | Worker token **или** JWT self; браузер шлёт только self |
| C4 | Acquire/release + public `force` | **PARTIALLY FIXED** | `force` → admin; prod auth на acquire/release. Остаётся: lab anon acquire; `browser_usb` → `force_stop` любому auth-user в prod |
| C5 | Revoke / admin/admin / пороги | **FIXED** | `face_embedding = NULL`; `CMIR_ADMIN_PASSWORD` в prod; thresholds 0.82/0.75 |
| C6 | MediaPipe leak / lock на HLS | **PARTIALLY FIXED** | `LiveCameraView.detector.close()` OK; wait HLS вне lock. Остаётся: kiosk `FaceLandmarker` / `mask-preview` без `.close()`; worker `stderr=PIPE` |

---

## Critical (открытые)

1. **Public `POST /face-match` identity oracle** (побочный эффект C1) — без auth возвращает `user_id` / `display_name` / `score` (`server.py` ~1070).  
   **Fix:** JWT/viewer-token + rate-limit; не отдавать identity анонимам.

2. **Worker revoke-cache bug** — `reload_consented`: `if fresh:` не обновляет gallery при пустом списке → после полного revoke старые векторы остаются до рестарта (`worker.py` ~133–138).  
   **Fix:** различать fetch fail vs authenticated empty; всегда назначать при HTTP 200.

3. **Unauthenticated airtime mint** — `POST /pois/{id}/airtime` начисляет ST/UT без auth (`server.py` ~1168).  
   **Fix:** admin/worker only или удалить в пользу face-presence.

4. **`CMIR_ENV` defaults to `test`** — prod-гейты (data key, admin pwd, acquire auth) легко пропустить (`database.py`).  
   **Fix:** fail-closed на `0.0.0.0` без явного `CMIR_ENV=prod` + обязательных секретов.

5. **RTMP `stderr=PIPE` без reader** — риск deadlock ffmpeg (`rtmp_writer.py`; также relay worker PIPE).

---

## High

6. **`browser_usb` = stealth force_stop** — обход admin-only `force` (`server.py` ~833).

7. **C4 bypass: GET playback / kiosk-stream** — unauth `LOCAL_RELAY.acquire` + HLS URLs (`server.py` ~459, ~601).

8. **Open HLS / preview-clip / mask-image** — без auth; CORS `*`.

9. **Donations / health-snapshot / health-history / health-all** — слабый или нулевой auth; stream URLs наружу.

10. **Wallet lookup с PII** — email + display_name.

11. **Kiosk register + temp password на экране**; enrollment timeout 9s = success.

12. **OAuth `state` без server store**; Android cleartext + WebView over-grant.

13. **Orphan ffmpeg / double-worker race / no RTSP reconnect** (`local_relay`, `rtsp_capture`).

14. **Client-controlled `ad_revenue` on views** → UT inflation.

15. **XSS via `innerHTML`** (admin/kiosk/user strings); kiosk `api()` без JWT.

---

## Medium

12. **Kiosk FaceLandmarker без `.close()`** — `stopLive()` не закрывает landmarker (`kiosk/index.html`).
13. **`mask-preview.js` detector без `.close()`** в `stop()`.
14. **face-worker / relay `stderr=PIPE` без reader** — риск блокировки ffmpeg/worker (`rtmp_writer.py`, `local_relay._ensure_worker`).
15. **PrivacyGate `frame.copy()`** — буфер ~delay_frames полных кадров в RAM (`privacy_gate.py`).
16. **Gallery cache до ~150 кадров** после revoke (~5s @30fps) — окно unmask после отзыва (`worker.py` reload).
17. **Presence reward check-then-insert** без жёсткой транзакции/UNIQUE race (`store.record_face_presence`).
18. **Enrollment timeout 9s** засчитывает позу как успех (`face-enroll.js` `_waitPose`).
19. **stdlib single-thread `HTTPServer`** + блокирующие HLS probes в request path.
20. **Token в localStorage**, CORS `*`, длинные сессии.
21. **Demo/constant seed embeddings** после L2-norm kollапсируют → ложные матчи в тестах/демо.

---

## Memory leaks / races (фокус)

| Область | Находка | Severity |
|---------|---------|----------|
| Browser LiveCamera | `detector.close()` на stop | OK (fixed) |
| Kiosk enroll | Landmarker не закрывается | Medium |
| mask-preview | Detector не закрывается | Medium |
| PrivacyGate | Копии кадров в deque | Medium (by design, bounded) |
| RTMP writer | stderr PIPE без drain | Medium (hang risk) |
| Relay worker | stderr PIPE | Medium |
| Gallery reload | Race: revoke vs in-memory faces | Medium (bounded lag) |
| acquire browser_usb | Race/abuse vs viewers | High |
| SQLite presence | TOCTOU insert | Medium |
| PreviewBuffer | stop unlink clip; thread Event | OK-ish |

---

## Video bottlenecks

1. **Тройное кодирование:** USB → ffmpeg RTMP → MediaMTX → decode (worker) → MediaPipe → re-encode RTMP → HLS.  
2. **PrivacyGate delay** (по умолчанию 250–900ms кадров в RAM).  
3. **Browser face-match RTT** каждые ~400ms на трек (новый путь после C1) — CPU + API load.  
4. **PreviewBuffer** — ещё один ffmpeg с HLS.  
5. **Blocking `hls_playlist_ready`** в HTTP handlers (`playback`/`acquire` wait).  
6. **CDN MediaPipe** cold-start в браузере.  
7. **Single USB device holder** — сериализация POI на одной камере.

---

## Что относительно ок

- PBKDF2 пароли, session tokens через `secrets`.  
- Worker-token на biometric dump; templates encrypted at rest.  
- Revoke чистит templates + NULL `face_embedding`.  
- Presence auth закрыт.  
- `force` admin-only.  
- LiveCamera MediaPipe close + thresholds выровнены.  
- Relay больше не sleep’ит на HLS под `_lock` при acquire.  
- Multi-pose enrollment — правильное направление.  
- Admin mutations в целом gated; prod блокирует clear/demo seed и требует data/admin keys.

---

## Приоритет следующих фиксов

1. Auth/rate-limit **face-match**; fix worker `if fresh:` revoke cache.  
2. Auth/disable **airtime**; fail-closed `CMIR_ENV` + secrets.  
3. Drain **stderr PIPE**; process-group kill; `detector.close()` в worker.  
4. Закрыть GET playback/kiosk/HLS/preview; ограничить **browser_usb**.  
5. Auth donations/health; убрать wallet PII; OAuth state store.  
6. Enrollment timeout ≠ success; landmarker/mask-preview `.close()`; escape `innerHTML`.  
7. Android cleartext off (release); cut frame copies / async gallery refresh.

Источники re-audit: parallel explore — API, face-worker, web/kiosk/android (2026-07-31).
