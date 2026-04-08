"""Validation stage for generated decks."""

from app.models.schemas import Deck, Slide


class ValidationService:
    def validate(self, deck: Deck) -> Deck:
        sanitized_slides: list[Slide] = []
        for slide in deck.slides:
            bullets = [bullet.strip() for bullet in slide.bullets if bullet.strip()]
            if not bullets:
                bullets = ["Content pending."]
            sanitized_slides.append(Slide(title=slide.title.strip(), bullets=bullets, notes=slide.notes))

        deck.slides = sanitized_slides
        deck.metadata["validated"] = True
        return deck
