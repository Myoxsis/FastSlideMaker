"""Local Ollama HTTP client for deck planning and slide JSON generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


class LLMClientError(RuntimeError):
    """Base error for local LLM client failures."""


class OllamaUnavailableError(LLMClientError):
    """Raised when Ollama is unreachable or not running."""


@dataclass(slots=True)
class LLMClientConfig:
    """Configuration for the Ollama LLM client."""

    host: str = "http://localhost:11434"
    model: str = "llama3.1"
    temperature: float = 0.4
    max_tokens: int = 1200
    system_prompt: str = (
        "You are a reliable assistant for generating presentation planning and slide JSON. "
        "Always prefer valid JSON when asked."
    )
    timeout_seconds: float = 20.0
    use_chat_api: bool = True
    enable_mock_mode: bool = False


class OllamaLLMClient:
    """Production-sensible local HTTP client for Ollama.

    Supports both `/api/chat` and `/api/generate`, with graceful fallback to mock mode
    when configured.
    """

    def __init__(self, config: LLMClientConfig | None = None) -> None:
        self.config = config or LLMClientConfig()

    async def plan_deck(self, *, topic: str, audience: str, tone: str, slide_count: int) -> str:
        """Create a high-level deck plan in JSON."""
        prompt = (
            "Return ONLY valid JSON with keys: title, theme, outline. "
            "`outline` must be an array of objects with keys: slide_number, title, objective, bullets. "
            f"Topic: {topic}\n"
            f"Audience: {audience}\n"
            f"Tone: {tone}\n"
            f"Slide count: {slide_count}"
        )
        return await self._complete(prompt, task_name="deck planning")

    async def generate_slide_json(self, *, plan_json: str, slide_count: int) -> str:
        """Generate full deck JSON for slide rendering."""
        prompt = (
            "Using the provided plan, return ONLY valid JSON with keys: title, theme, slides. "
            "`slides` must contain objects with keys: title, bullets, notes. "
            f"Target slide count: {slide_count}.\n"
            f"Plan JSON:\n{plan_json}"
        )
        return await self._complete(prompt, task_name="slide JSON generation")

    async def repair_json(self, *, malformed_json: str, expected_shape_hint: str = "") -> str:
        """Repair malformed model output into valid JSON, preserving meaning."""
        shape_hint = f"Expected shape: {expected_shape_hint}\n" if expected_shape_hint else ""
        prompt = (
            "Fix the following malformed JSON. Return ONLY valid JSON and do not add explanation.\n"
            f"{shape_hint}"
            f"Malformed JSON:\n{malformed_json}"
        )
        return await self._complete(prompt, task_name="JSON repair")

    async def _complete(self, prompt: str, *, task_name: str) -> str:
        """Run a completion against Ollama with fallback behavior."""
        try:
            if self.config.use_chat_api:
                return await self._chat_completion(prompt)
            return await self._generate_completion(prompt)
        except OllamaUnavailableError:
            if self.config.enable_mock_mode:
                return self._mock_response(task_name)
            raise

    async def _chat_completion(self, prompt: str) -> str:
        body: dict[str, Any] = {
            "model": self.config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        payload = await self._post_json("/api/chat", body)
        message = payload.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise LLMClientError("Ollama chat response format was unexpected.")
        return message["content"].strip()

    async def _generate_completion(self, prompt: str) -> str:
        body: dict[str, Any] = {
            "model": self.config.model,
            "stream": False,
            "system": self.config.system_prompt,
            "prompt": prompt,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        payload = await self._post_json("/api/generate", body)
        response_text = payload.get("response")
        if not isinstance(response_text, str):
            raise LLMClientError("Ollama generate response format was unexpected.")
        return response_text.strip()

    async def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        timeout = httpx.Timeout(
            connect=min(10.0, self.config.timeout_seconds),
            read=self.config.timeout_seconds,
            write=min(10.0, self.config.timeout_seconds),
            pool=min(10.0, self.config.timeout_seconds),
        )

        try:
            async with httpx.AsyncClient(base_url=self.config.host, timeout=timeout) as client:
                response = await client.post(path, json=body)
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise OllamaUnavailableError(
                "Cannot connect to Ollama at http://localhost:11434. "
                "Please start Ollama (e.g. `ollama serve`) or enable mock mode."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMClientError(
                f"Request to Ollama timed out after {self.config.timeout_seconds:.1f}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else ""
            raise LLMClientError(
                f"Ollama returned HTTP {exc.response.status_code}: {detail}".strip()
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(f"Ollama request failed: {exc}") from exc

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise LLMClientError("Ollama returned a non-JSON response.") from exc

        if not isinstance(payload, dict):
            raise LLMClientError("Ollama returned an unexpected payload type.")
        return payload

    def _mock_response(self, task_name: str) -> str:
        if task_name == "deck planning":
            return json.dumps(
                {
                    "title": "Mock Deck Plan",
                    "theme": "clean-blue",
                    "outline": [
                        {
                            "slide_number": 1,
                            "title": "Overview",
                            "objective": "Set context",
                            "bullets": ["Goal", "Audience needs", "Outcome"],
                        }
                    ],
                }
            )

        if task_name == "JSON repair":
            return "{}"

        return json.dumps(
            {
                "title": "Mock Slide Deck",
                "theme": "clean-blue",
                "slides": [
                    {
                        "title": "Intro",
                        "bullets": ["Mock mode enabled", "Ollama unavailable"],
                        "notes": "Replace with live generation when Ollama is running.",
                    }
                ],
            }
        )
