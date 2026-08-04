# Cmir — сводный план (сайт + Android + продукт)

Обновлено: **2026-08-04**. Источники: `docs/PLAN.md`, `docs/PHASE0.md`, `apps/android/PLAY_STORE.md`, lab-работа по карте/маскам.

---

## 1. Цель продукта (коротко)

Live-карта мест с **приватностью лиц** (маска на глаза / подпись после согласия), киоск согласия, аккаунт, админка.  
Мобильный клиент — WebView-оболочка `com.cmir.app` вокруг того же web-контура.

---

## 2. Что уже сделано (lab / MVP-ядро)

| Область | Статус |
|---------|--------|
| API Python + SQLite (auth, POI, камеры, consent, face-match) | ✅ lab |
| Web: карта Leaflet, POI-превью, киоск, аккаунт, админка | ✅ lab |
| Маски MediaPipe (область глаз), privacy-first composite | ✅ браузер |
| Face-worker: SCRFD + тайлинг + ByteTrack/EMA + eye keypoints | ✅ (RTSP/толпа) |
| Android debug + `adb reverse`, offline/retry, camera disclosure | ✅ |
| Adaptive icon (заглушка), cleartext off, Target API 35 | ✅ |
| Fullscreen stream в WebView | ✅ |
| Privacy/Terms черновики в UI | ✅ |
| **Чат у места** (API + UI, админ: delete/mute) | ✅ добавлено |
| **Заявки на новые места** (submit → admin approve + facing cam) | ✅ добавлено |
| **Post-stream linger** (30 мин + replay ~5 мин, авто-удаление) | ✅ |
| **Киоск: отсчёт 3-2-1-0** перед каждым ракурсом | ✅ |
| **Роль Host** (владелец места: эфир, метаданные, mute чата) | ✅ |
| Instagram (Stories / Reels / Direct) | ⏸ отложено |
| GoPro / MediaMTX / face-worker production pipeline | ⏳ lab частично |
| Публичный HTTPS сайт | ❌ |
| Google Play listing / AAB signing | ❌ |

---

## 3. Большие задачи: запуск сайта на недорогом хостинге

### 3.1 Рекомендуемый дешёвый контур

| Компонент | Вариант A (самый простой) | Вариант B (чуть мощнее) |
|-----------|---------------------------|-------------------------|
| Статика `apps/web` | Cloudflare Pages / Netlify / Nginx на VPS | тот же |
| API `apps/api_py` | **VPS 1 vCPU / 1–2 GB** (Hetzner CX22, Timeweb, Selectel) ~3–6 $/мес | Fly.io / Railway |
| HTTPS | Caddy или Nginx + Let's Encrypt | провайдер TLS |
| БД | SQLite на диске VPS (MVP) | позже Postgres |
| Медиа (RTSP/HLS) | отдельный маленький VPS + MediaMTX **или** только device-camera на старте | Docker Compose |

**Минимальный запуск без RTSP:** сайт + API на одном VPS, эфир с вебкамеры/телефона (как сейчас в lab) — этого достаточно для первого публичного теста.

### 3.2 Чеклист выкладки сайта

1. [ ] Домен (например `app.cmir.live`) + DNS A/AAAA на VPS  
2. [ ] Systemd (или docker) для `server.py` на `:8090`, static на `:443`  
3. [ ] `CMIR_ENV=prod`, `CMIR_DATA_KEY`, `CMIR_ADMIN_PASSWORD`, `CMIR_WORKER_TOKEN`  
4. [ ] CORS / cookie / HTTPS-only cookies при необходимости  
5. [ ] В Android `cmir_web_base` → `https://app.cmir.live/` (уже черновик)  
6. [ ] Финальные `privacy.html` / `terms.html` на том же домене  
7. [ ] Бэкап SQLite (cron)  
8. [ ] Мониторинг `/health`

### 3.3 Оценка стоимости (ориентир)

- VPS: **$4–8 / мес**  
- Домен: **$10–15 / год**  
- Play Console: **$25 разово**  
- MediaMTX/RTSP (опционально): +$4–8 / мес  

---

## 4. Большие задачи: Google Play

См. детальный статус: [`apps/android/PLAY_STORE.md`](../apps/android/PLAY_STORE.md).

### Порядок

1. [x] Target API 35, debug lab, camera disclosure, icon stub  
2. [ ] Рабочий production HTTPS (блокер для release WebView)  
3. [ ] Финальный Privacy Policy URL в Console  
4. [ ] Data safety + IARC  
5. [ ] Upload key + `./gradlew bundleRelease`  
6. [ ] Скриншоты (карта, киоск, маска, чат)  
7. [ ] Internal testing → closed → production  
8. [ ] Прогон Pixel + mid-range Samsung  

---

## 5. Ближайший продуктовый backlog

### P0 — стабильность масок
- [x] Строгий фильтр keypoints (не грудь)  
- [x] Confirm-to-show, hold при потере трека  
- [ ] Доп. калибровка на реальных selfie/crowd сценах  

### P0 — соц. функции (сейчас)
- [x] Чат POI + админ delete/mute  
- [x] User submit POI + admin approve/reject + facing mode  
- [ ] Уведомление заявителю об аппруве (email/push — позже)  
- [ ] Rate-limit чата / антиспам  

### P1 — медиа
- [ ] Production HLS/masked pipeline или осознанный MVP «только device camera»  
- [ ] Маска/чат на защищённом HLS (серверный worker)  

### P2 — из исходного PLAN.md
- Wallet ST/UT testnet, донаты, tops, scene narrator, edge agents  

---

## 6. Фазы (сверка с PLAN.md)

| Фаза | Смысл | Где мы |
|------|-------|--------|
| 0 POC | 1 POI lab, consent, маски | **пройдена в lab** |
| 1 MVP | registry, player, map, wallet-lite | **~70% lab**, без публичного хоста |
| 1b Launch | cheap hosting + Play internal | **следующий фокус** |
| 2 Beta | scale CV, UT, GDPR tooling | впереди |
| 3 Prod | stores full, revenue split | впереди |

---

## 7. Следующий шаг — кто что делает

**Сейчас фокус: публичный HTTPS (дешёвый хостинг), потом Play internal testing.**  
Instagram-интеграция — после стабильного прод-контура.

### Вам (аккаунт / деньги / доступы)
1. Купить/выбрать **домен** (или подтвердить `app.cmir.live`).
2. Заказать **VPS** (~$4–8/мес: Hetzner / Timeweb / Selectel) и прислать: IP, SSH-доступ (user + ключ или пароль), домен с DNS A-записью на IP.
3. Завести **Google Play Console** ($25 разово), если ещё нет — аккаунт разработчика.
4. Решить: на старте **только камера телефона/ПК** (быстрее) или сразу нужен MediaMTX/RTSP (дороже/сложнее).

### Я (код / деплой / приложение)
1. Скрипты деплоя: systemd/Caddy (или Nginx) для `apps/web` + `api_py`, HTTPS, env prod.
2. Подключить домен, проверить `/health`, карту, чат, заявки мест, Host на HTTPS.
3. Прописать production URL в Android `cmir_web_base`, собрать `bundleRelease`.
4. Подготовить черновик листинга Play + Data safety / IARC.
5. Instagram — отдельным этапом после launch.

---

Мобильное приложение **не требует отдельного бэкенда** — оно грузит тот же сайт; после HTTPS lab-`adb reverse` для релиза не нужен.

