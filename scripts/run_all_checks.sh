#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0
run() {
  echo ""
  echo "=== $1 ==="
  if "$2"; then echo "OK: $1"; else echo "FAIL: $1"; fail=1; fi
}

run "e2e phase0" "python3 scripts/e2e_phase0.py"
run "e2e phase1 admin" "python3 scripts/e2e_phase1_admin.py"
run "e2e phase1 full" "python3 scripts/e2e_phase1_full.py"

if [[ $fail -eq 0 ]]; then
  echo ""
  echo "All checks passed."
else
  echo ""
  echo "Some checks failed."
  exit 1
fi
