# GoPro HERO13 Black — тестирование со Cmir

Да, **GoPro 13 подойдёт** для lab-тестов Cmir: это отличный источник широкоугольного live-видео с хорошей стабилизацией. Cmir не подключается к камере напрямую — поток идёт через **ingest** (MediaMTX), затем face-worker и web.

## Что поддерживает HERO13 (практично для нас)

| Способ | Для Cmir | Сложность |
|--------|----------|-----------|
| **Live stream (Wi‑Fi)** → RTMP на ваш сервер | ✅ основной путь | Средняя |
| **USB webcam** (Mac/PC) → FFmpeg → RTMP | ✅ самый простой в lab | Низкая |
| **HDMI + capture card** | ✅ стабильный продакшен | Выше |
| Нативный RTSP с камеры | ❌ обычно нет | — |

Рекомендуем для первого теста: **USB webcam** или **RTMP в MediaMTX**, когда поднят `apps/ingest`.

## Архитектура в Cmir

```
[GoPro 13] --Wi‑Fi/USB--> [RTMP publish] --> [MediaMTX path gopro_main]
                                                  |
                    rtsp://localhost:8554/gopro_main (read)
                                                  |
                              [face-worker] --> [HLS / web player]
```

В admin укажите для general-камеры:

```text
rtsp://127.0.0.1:8554/gopro_main
```

или после HLS:

```text
http://127.0.0.1:8888/gopro_main/index.m3u8
```

## Шаг 1 — поднять ingest

```bash
cd apps/ingest
docker compose up -d
```

Порты по умолчанию:

| Сервис | Порт | Назначение |
|--------|------|------------|
| RTMP | 1935 | приём с GoPro / FFmpeg |
| RTSP | 8554 | чтение для face-worker |
| HLS | 8888 | браузер |
| API MediaMTX | 9997 | статус paths |

## Шаг 2 — вариант A: Live stream с GoPro (Wi‑Fi)

1. Установите **GoPro Quik** на телефон, сопрягите HERO13.
2. В настройках камеры включите **Live Stream** (если доступно в вашем регионе/прошивке).
3. Укажите **Custom** RTMP URL (нужен публичный IP или tailscale на Mac):

   ```text
   rtmp://ВАШ_IP:1935/gopro_main
   ```

4. На Mac откройте firewall для порта **1935** или используйте VPN (Tailscale) — GoPro и Mac должны видеть друг друга.

5. Проверка:

   ```bash
   curl -s http://127.0.0.1:9997/v3/paths/list | python3 -m json.tool
   ```

   Path `gopro_main` должен быть `ready` с publisher.

## Шаг 3 — вариант B: USB webcam (проще в комнате)

**Важно:** надпись «USB подключено» на камере — это не режим записи на SD. Нужно приложение **GoPro Webcam** (App Store на macOS 13+), синяя точка в меню Mac, превью через **Show Preview**.

1. Установите и **запустите** [GoPro Webcam](https://apps.apple.com/app/gopro-webcam/id6477835262).
2. Подключите HERO13 по USB‑C, включите камеру.
3. В меню Mac (иконка GoPro) → **Show Preview** — должна появиться картинка.
4. Проверьте индекс: `ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep GoPro` (часто `[2]`).
5. Публикуйте в MediaMTX:

   ```bash
   export GOPRO_FPS=30
   bash scripts/gopro_usb_publish.sh
   ```

   Скрипт сам найдёт `GoPro Webcam`. Или вручную:


   ```bash
   # macOS — часто AVFoundation
   ffmpeg -f avfoundation -framerate 30 -video_size 1920x1080 -i "GoPro Webcam" \
     -c:v libx264 -preset veryfast -tune zerolatency -f flv rtmp://127.0.0.1:1935/gopro_main
   ```

3. Для **fisheye** в admin выберите `view_mode: fisheye` — в Фазе 1.2 добавим коррекцию в face-worker; пока режим сохраняется в registry.

## Шаг 4 — зарегистрировать камеру в Cmir

1. `bash scripts/start-phase0.sh` (или API + web отдельно).
2. Откройте **Admin**: http://localhost:3000/../admin/index.html
3. Создайте POI типа `social_event`, добавьте:
   - **General** — `rtsp://127.0.0.1:8554/gopro_main`, `view_mode` по сценарию
   - **Consent** — URL киоска / вторая камера
4. Нажмите **Проверить поток** — health должен быть `reachable`.

## Шаг 5 — face-worker на live (недели 3–4)

Сейчас worker умеет **файл**; для GoPro добавим:

```bash
python -m cmir_face.worker \
  --input rtsp://127.0.0.1:8554/gopro_main \
  --output apps/web/media/gopro_live.mp4 \
  --api-url http://localhost:8090 --poi-id <uuid>
```

(появится в спринте ingest + egress.)

## Советы по съёмке для consent/match

- Consent-камера: лицо крупно, фронтально, стабильный свет.
- General (GoPro): не ставьте ultra-wide слишком близко — match хуже; для POC лучше 1–3 м.
- После consent подождите 1–2 с (кэш embeddings в API).

## Ограничения POC

- Нет официального RTSP с GoPro — только RTMP/USB/HDMI.
- Задержка Wi‑Fi Live Stream выше USB; целевой consent &lt; 3 с проверяем на USB или локальной сети.
- Батарея и перегрев при длительном stream — питание от сети.

## Чеклист перед выездом в lab

- [ ] `docker compose` ingest работает
- [ ] Тестовый publish (FFmpeg или GoPro) → path `gopro_main` ready
- [ ] Admin: POI + камера с правильным `stream_url`
- [ ] Health `reachable`
- [ ] Kiosk consent + general в одной Wi‑Fi сети
