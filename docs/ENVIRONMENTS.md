# Cmir — test и production

## Контуры

| Контур | Переменная | База данных |
|--------|------------|-------------|
| **test** (текущая работа) | `CMIR_ENV=test` | `apps/api_py/data/cmir_test.db` |
| **production** (слепок в конце этапа) | `CMIR_ENV=prod` | `apps/api_py/data/cmir_prod.db` |

Тестовые POI и камеры **не попадают** в production. Перед релизом:

```bash
CMIR_ENV=prod python3 apps/api_py/server.py
# или копия БД: cp data/cmir_test.db data/cmir_prod.db  (после очистки тестового мусора)
```

## Очистка тестовых мест

```bash
CMIR_ENV=test python3 scripts/reset_test_pois.py
```

Удаляет все POI из **test** БД. В `prod` скрипт отказывается работать.

## Запуск lab (test)

```bash
export CMIR_ENV=test
bash scripts/start-lab.sh
```
