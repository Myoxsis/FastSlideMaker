"""Rendering stage that enriches deck structure for front-end or exporter use."""

from app.models.schemas import Deck


class RenderingService:
    def render(self, deck: Deck) -> Deck:
        for position, slide in enumerate(deck.slides, start=1):
            slide.notes = (slide.notes or "") + f" [Render position: {position}]"
        deck.metadata["rendered"] = True
        return deck
