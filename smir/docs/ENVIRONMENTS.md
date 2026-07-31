# Smir — test и production

## Контуры

| Контур | Переменная | База данных |
|--------|------------|-------------|
| **test** (текущая работа) | `SMIR_ENV=test` | `apps/api_py/data/smir_test.db` |
| **production** (слепок в конце этапа) | `SMIR_ENV=prod` | `apps/api_py/data/smir_prod.db` |

Тестовые POI и камеры **не попадают** в production. Перед релизом:

```bash
SMIR_ENV=prod python3 apps/api_py/server.py
# или копия БД: cp data/smir_test.db data/smir_prod.db  (после очистки тестового мусора)
```

## Очистка тестовых мест

```bash
SMIR_ENV=test python3 scripts/reset_test_pois.py
```

Удаляет все POI из **test** БД. В `prod` скрипт отказывается работать.

## Запуск lab (test)

```bash
export SMIR_ENV=test
bash scripts/start-lab.sh
```
