"""Simple local persistence for generated projects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STORE_DIR = Path("samples")
STORE_DIR.mkdir(parents=True, exist_ok=True)


def save_project(project: dict[str, Any], name: str) -> Path:
    path = STORE_DIR / f"{name}.json"
    path.write_text(json.dumps(project, indent=2), encoding="utf-8")
    return path


def load_project(name: str) -> dict[str, Any]:
    path = STORE_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_projects() -> list[str]:
    return sorted([p.stem for p in STORE_DIR.glob("*.json")])
