"""Export stage placeholder for pptx/pdf generation."""

from pathlib import Path

from app.models.schemas import Deck


class ExportService:
    def export(self, deck: Deck) -> dict:
        output_dir = Path("artifacts")
        output_dir.mkdir(exist_ok=True)

        json_path = output_dir / "last_generated_deck.json"
        json_path.write_text(deck.model_dump_json(indent=2), encoding="utf-8")

        return {
            "json": str(json_path),
            "pptx": None,
            "pdf": None,
        }
