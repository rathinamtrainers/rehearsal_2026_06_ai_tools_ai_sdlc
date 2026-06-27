"""Export the live OpenAPI spec to ``docs/openapi.json`` at the repo root.

Run from the ``backend/`` directory so ``app`` is importable:

    python -m scripts.export_openapi

The committed ``docs/openapi.json`` is a snapshot of ``GET /openapi.json``;
re-run this whenever an endpoint or schema changes so the snapshot stays current.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.main import app

# backend/scripts/export_openapi.py -> parents[2] is the repository root.
OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()
    OUTPUT.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} (OpenAPI {spec.get('openapi')}, {len(spec.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
