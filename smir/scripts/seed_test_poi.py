#!/usr/bin/env python3
"""Восстановить демо-места в test DB (идемпотентно)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SMIR_ENV", "test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api_py"))

from store import Store  # noqa: E402


def main() -> int:
    store = Store()
    created = store.ensure_demo_fixtures()
    pois = store.list_pois()
    print(f"POI on map: {len(pois)}")
    for p in pois:
        roles = ", ".join(f"{c['role']}" for c in p.get("cameras", []))
        print(f"  - {p['name']} ({len(p.get('cameras', []))} cam: {roles})")
    if created:
        print(f"Added: {', '.join(created)}")
    else:
        print("Demo fixtures already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
