"""Deck generation service with Ollama + mock fallback support."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import Deck, DeckRequest, Slide


class GenerationService:
    async def check_ollama(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{settings.ollama_host}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def generate(self, payload: DeckRequest) -> Deck:
        if await self.check_ollama():
            deck = await self._generate_with_ollama(payload)
            if deck:
                return deck

        if settings.enable_mock_mode:
            return self._generate_mock(payload)

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

    def _generate_mock(self, payload: DeckRequest) -> Deck:
        slides = [
            Slide(
                title=f"{payload.topic} — Slide {index}",
                bullets=[
                    f"Key point {index}.1 for {payload.audience}",
                    f"Key point {index}.2 with {payload.tone.lower()} tone",
                    f"Action item {index}.3",
                ],
                notes="Generated in mock mode because Ollama is unavailable.",
            )
            for index in range(1, payload.slide_count + 1)
        ]
        return Deck(
            title=f"{payload.topic} Overview",
            theme="clean-blue",
            slides=slides,
            metadata={"mode": "mock", "model": settings.ollama_model},
        )
