"""Shared schema objects across generation pipeline stages."""

from typing import Any

from pydantic import BaseModel, Field


class DeckRequest(BaseModel):
    topic: str = Field(..., description="Topic for the generated presentation.")
    audience: str = Field(default="General", description="Target audience.")
    tone: str = Field(default="Professional", description="Narrative tone.")
    slide_count: int = Field(default=6, ge=3, le=30)


class Slide(BaseModel):
    title: str
    bullets: list[str]
    notes: str | None = None


class Deck(BaseModel):
    title: str
    theme: str = "clean-blue"
    slides: list[Slide]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeckResponse(BaseModel):
    deck: Deck
    export: dict[str, Any]
