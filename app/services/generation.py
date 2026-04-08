"""Deck generation service with Ollama detection + deterministic mock mode."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Deck, DeckRequest
from app.services.mock_mode import build_mock_deck


class GenerationService:
    async def check_ollama(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.ollama_host}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, payload: DeckRequest) -> Deck:
        ollama_available = await self.check_ollama()

        if ollama_available:
            deck = await self._generate_with_ollama(payload)
            if deck:
                return deck

        if settings.enable_mock_mode:
            return build_mock_deck(payload, ollama_available=ollama_available)

        raise RuntimeError("Ollama is unavailable and mock mode is disabled.")

    async def _generate_with_ollama(self, payload: DeckRequest) -> Deck | None:
        prompt = (
            "Create a slide deck in JSON with keys: title, theme, slides. "
            f"Topic: {payload.topic}. Audience: {payload.audience}. Tone: {payload.tone}. "
            f"Slide count: {payload.slide_count}."
        )

        body: dict[str, Any] = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.ollama_temperature,
                "top_p": settings.ollama_top_p,
                "num_predict": settings.ollama_max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(f"{settings.ollama_host}/api/generate", json=body)
                response.raise_for_status()
                content = response.json().get("response", "")
        except (httpx.HTTPError, ValueError):
            return None

        # TODO: replace with robust JSON extraction/parsing logic.
        if not content:
            return None

        return None
