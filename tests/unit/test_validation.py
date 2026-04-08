from app.models.schemas import Deck, Slide
from app.services.validation import ValidationService


def test_validation_removes_blank_bullets() -> None:
    deck = Deck(title="Demo", slides=[Slide(title="S1", bullets=["", "  ", "Item"])])
    validated = ValidationService().validate(deck)
    assert validated.slides[0].bullets == ["Item"]
    assert validated.metadata["validated"] is True
