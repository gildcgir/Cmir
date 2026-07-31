#!/usr/bin/env bash
# Cmir Phase 0 — start API + static web
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

API_PID=""
if command -v cargo >/dev/null 2>&1; then
  echo "==> Cmir API (Rust, port 8090)"
  (cd "$ROOT/apps/api" && cargo run) &
  API_PID=$!
else
  echo "==> Cmir API (Python, port 8090)"
  python3 "$ROOT/apps/api_py/server.py" &
  API_PID=$!
fi

sleep 1
echo "==> Cmir Web (port 3000)"
(cd "$ROOT/apps/web" && python3 -m http.server 3000) &
WEB_PID=$!

echo ""
echo "  Web:   http://localhost:3000"
echo "  Admin: http://localhost:3000/../admin/index.html"
echo "  Kiosk: http://localhost:3000/../consent-kiosk/index.html"
echo "  API:   http://localhost:8090/health"
echo ""
echo "Video POC: bash scripts/phase0_pipeline.sh"
echo "Press Ctrl+C to stop."

trap '[[ -n "${API_PID:-}" ]] && kill $API_PID 2>/dev/null; kill $WEB_PID 2>/dev/null' EXIT
wait
