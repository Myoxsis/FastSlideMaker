from pathlib import Path

import pytest

from app.models.schemas import SemanticPresentation
from project_store import ProjectStore


def _semantic_fixture() -> SemanticPresentation:
    return SemanticPresentation.model_validate(
        {
            "metadata": {"title": "Demo Deck", "audience": "Team", "purpose": "Review"},
            "user_prompt": "Store fixture prompt",
            "prompt_last_updated_at": "2026-01-01T00:00:00+00:00",
            "slide_order": ["s1"],
            "slides": [
                {
                    "id": "s1",
                    "order": 1,
                    "type": "content",
                    "title": "Overview",
                    "text_blocks": [{"id": "t1", "role": "body", "text": "Simple and readable project file."}],
                }
            ],
        }
    )


def test_save_load_and_export_json(tmp_path: Path) -> None:
    store = ProjectStore(
        projects_dir=tmp_path / "projects",
        samples_dir=tmp_path / "samples",
        exports_dir=tmp_path / "exports",
    )

    saved = store.save_project("Demo", _semantic_fixture())
    loaded = store.load_project(saved["project_id"])
    exported = store.export_project_json(saved["project_id"])

    assert loaded["project_id"] == saved["project_id"]
    assert loaded["name"] == "Demo"
    assert loaded["deck"]["metadata"]["title"] == "Demo Deck"
    assert loaded["deck"]["user_prompt"] == "Store fixture prompt"
    assert exported.exists()
    assert exported.read_text(encoding="utf-8").startswith("{")


def test_export_pptx_creates_file(tmp_path: Path) -> None:
    pytest.importorskip("pptx")

    store = ProjectStore(
        projects_dir=tmp_path / "projects",
        samples_dir=tmp_path / "samples",
        exports_dir=tmp_path / "exports",
    )
    saved = store.save_project("Demo", _semantic_fixture())

    output = store.export_project_pptx(saved["project_id"])

    assert output.exists()
    assert output.suffix == ".pptx"
    assert output.stat().st_size > 0


def test_load_project_raises_for_invalid_json(tmp_path: Path) -> None:
    store = ProjectStore(
        projects_dir=tmp_path / "projects",
        samples_dir=tmp_path / "samples",
        exports_dir=tmp_path / "exports",
    )
    project_id = "broken"
    (tmp_path / "projects" / f"{project_id}.json").write_text("{not valid", encoding="utf-8")

    with pytest.raises(ValueError):
        store.load_project(project_id)
