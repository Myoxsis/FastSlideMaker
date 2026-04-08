from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from schema import Deck, ProjectRecord

DATA_DIR = Path("samples/projects")


def save_project(deck: Deck) -> ProjectRecord:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    project_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    record = ProjectRecord(project_id=project_id, created_at=created_at, deck=deck)
    path = DATA_DIR / f"{project_id}.json"
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return record


def load_project(project_id: str) -> ProjectRecord:
    path = DATA_DIR / f"{project_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProjectRecord.model_validate(payload)


def list_projects() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    projects = []
    for file in sorted(DATA_DIR.glob("*.json")):
        payload = json.loads(file.read_text(encoding="utf-8"))
        projects.append(
            {
                "project_id": payload["project_id"],
                "created_at": payload["created_at"],
                "prompt": payload["deck"]["request"],
            }
        )
    return projects
