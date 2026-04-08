"""Rendering stage that enriches deck structure for front-end or exporter use."""

from app.models.schemas import Deck, SemanticPresentation
from app.services.designer import DesignerService


class RenderingService:
    def render(self, deck: Deck) -> Deck:
        for position, slide in enumerate(deck.slides, start=1):
            slide.notes = (slide.notes or "") + f" [Render position: {position}]"
        deck.metadata["rendered"] = True
        return deck

    def render_semantic(self, deck: SemanticPresentation) -> SemanticPresentation:
        """Ensure semantic decks are render-safe by applying deterministic layout hints."""

        designed = DesignerService().design_presentation(deck)
        return designed.model_copy(update={"metadata": designed.metadata.model_copy(update={"version": "1.0-designed"})})
