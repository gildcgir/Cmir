#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="python3"
if [[ -x "$ROOT/apps/face-worker/.venv/bin/python" ]]; then
  PY="$ROOT/apps/face-worker/.venv/bin/python"
fi

"$PY" -m pip install -q -r requirements-dev.txt
export CMIR_ENV=test
export CMIR_WORKER_TOKEN="${CMIR_WORKER_TOKEN:-test-worker-token}"
export CMIR_DATA_KEY="${CMIR_DATA_KEY:-test-data-key-not-for-prod-use!!}"
export CMIR_ADMIN_PASSWORD="${CMIR_ADMIN_PASSWORD:-admin}"
"$PY" -m pytest tests/ -v --tb=short "$@"
