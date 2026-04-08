from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.models.schemas import SemanticPresentation


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


@dataclass(frozen=True)
class ProjectIndexItem:
    project_id: str
    name: str
    created_at: str
    updated_at: str
    source: str


class ProjectStore:
    """Simple file-based store for semantic deck projects."""

    def __init__(
        self,
        *,
        projects_dir: Path | str = Path("data/projects"),
        samples_dir: Path | str = Path("samples/projects"),
        exports_dir: Path | str = Path("artifacts"),
    ) -> None:
        self.projects_dir = Path(projects_dir)
        self.samples_dir = Path(samples_dir)
        self.exports_dir = Path(exports_dir)

        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[ProjectIndexItem]:
        items = [
            *self._scan_directory(self.samples_dir, source="sample"),
            *self._scan_directory(self.projects_dir, source="saved"),
        ]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def save_project(self, name: str, deck: SemanticPresentation) -> dict:
        project_id = str(uuid4())
        now = _utc_now_iso()
        record = {
            "project_id": project_id,
            "name": name.strip() or "Untitled Project",
            "created_at": now,
            "updated_at": now,
            "deck": deck.normalized().model_dump(mode="json"),
        }
        path = self.projects_dir / f"{project_id}-{_slugify(record['name'])}.json"
        self._write_json(path, record)
        return record

    def load_project(self, project_id: str) -> dict:
        path = self._find_project_file(project_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["deck"] = SemanticPresentation.model_validate(payload["deck"]).normalized().model_dump(mode="json")
        return payload

    def export_project_json(self, project_id: str) -> Path:
        source = self._find_project_file(project_id)
        destination = self.exports_dir / f"{source.stem}.json"
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        return destination

    def export_project_pptx(self, project_id: str) -> Path:
        from app.services.pptx_exporter import export_semantic_deck_to_pptx

        payload = self.load_project(project_id)
        deck = SemanticPresentation.model_validate(payload["deck"])
        output_path = self.exports_dir / f"{project_id}.pptx"
        return export_semantic_deck_to_pptx(deck, output_path)

    def _find_project_file(self, project_id: str) -> Path:
        for directory in (self.projects_dir, self.samples_dir):
            for candidate in directory.glob(f"{project_id}*.json"):
                return candidate
            direct = directory / f"{project_id}.json"
            if direct.exists():
                return direct
        raise FileNotFoundError(f"Project '{project_id}' not found")

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _scan_directory(self, directory: Path, *, source: str) -> list[ProjectIndexItem]:
        projects: list[ProjectIndexItem] = []
        for file in directory.glob("*.json"):
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
                item = ProjectIndexItem(
                    project_id=payload["project_id"],
                    name=payload.get("name", "Untitled Project"),
                    created_at=payload.get("created_at", ""),
                    updated_at=payload.get("updated_at", payload.get("created_at", "")),
                    source=source,
                )
                projects.append(item)
            except (json.JSONDecodeError, KeyError):
                continue
        return projects
