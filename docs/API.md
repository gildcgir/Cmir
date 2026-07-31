# Cmir API (Phase 0–2)

Base URL: `http://localhost:8090`  
Реализация: `apps/api_py/server.py` (SQLite, Phase 2 core).

## Health

`GET /health` → `version: 0.3.0`, `phase: 2-core`

## Auth (Phase 2)

| Method | Path | Описание |
|--------|------|----------|
| POST | `/api/v1/auth/register` | email, password (≥8), display_name |
| POST | `/api/v1/auth/login` | → `{ token }` |
| POST | `/api/v1/auth/logout` | Bearer token |
| GET | `/api/v1/auth/me` | user, wallet, consents |

Consent и отзыв требуют заголовок `Authorization: Bearer <token>`.

## POI

| Method | Path | Описание |
|--------|------|----------|
| GET | `/api/v1/pois` | Список POI с камерами и stats |
| POST | `/api/v1/pois` | Создать POI |
| GET | `/api/v1/pois/{id}` | Один POI |
| POST | `/api/v1/pois/{id}/cameras` | Добавить камеру |
| POST | `/api/v1/pois/{id}/consent` | Consent + wallet (auth) |
| DELETE | `/api/v1/pois/{id}/consent/latest` | Отозвать последнее согласие (auth) |
| PATCH | `/api/v1/pois/{id}` | Обновить POI |
| GET | `/api/v1/cameras/{id}` | Одна камера |
| PATCH | `/api/v1/cameras/{id}` | Обновить камеру (`view_mode`, `stream_url`, …) |
| DELETE | `/api/v1/cameras/{id}` | Удалить камеру |
| GET | `/api/v1/cameras/{id}/health` | Проверка доступности `stream_url` |
| GET | `/api/v1/pois/{id}/embeddings` | Embeddings (POC) |
| GET | `/api/v1/pois/{id}/scene` | Описание сцены |

### Create POI body

```json
{
  "name": "My venue",
  "poi_type": "social_event",
  "latitude": 41.71,
  "longitude": 44.82,
  "description": "optional",
  "promo_description": "optional"
}
```

`poi_type`: `live_cam` | `social_event` | `venue`

### Create camera body

```json
{
  "name": "Cam 1",
  "stream_url": "rtsp://...",
  "role": "general",
  "view_mode": "standard"
}
```

`role`: `general` | `consent`  
`view_mode`: `fisheye` | `standard` | `zoom2x`

## Tops

| Method | Path |
|--------|------|
| GET | `/api/v1/tops/consent` |
| GET | `/api/v1/tops/participants` |
