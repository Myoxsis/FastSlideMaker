from pathlib import Path

from app.models.schemas import Deck, Slide
from app.services.export import ExportService


def test_export_service_writes_json_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    deck = Deck(title="Demo", slides=[Slide(title="S1", bullets=["A"])])

    artifacts = ExportService().export(deck)

    json_path = Path(artifacts["json"])
    assert json_path.exists()
    assert json_path.parent.name == "artifacts"
