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
"$PY" -m pytest tests/ -v --tb=short "$@"
