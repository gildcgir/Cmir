#!/usr/bin/env python3
"""Clear all POI from test database (CMIR_ENV=test only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("CMIR_ENV", "test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api_py"))

from store import Store  # noqa: E402


def main() -> int:
    store = Store()
    n = store.clear_all_pois()
    print(f"Cleared {n} POI(s) from test environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
