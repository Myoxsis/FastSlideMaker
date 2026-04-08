"""Local Ollama HTTP client with multi-step prompting for semantic slide generation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """Base error for local LLM client failures."""


class OllamaUnavailableError(LLMClientError):
    """Raised when Ollama is unreachable or not running."""


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@dataclass(slots=True)
class LLMClientConfig:
    """Configuration for the Ollama LLM client."""

    host: str = "http://localhost:11434"
    model: str = "llama3.1"
    temperature: float = 0.2
    max_tokens: int = 1800
    timeout_seconds: float = 30.0
    use_chat_api: bool = True
    enable_mock_mode: bool = False
    system_prompt: str = field(default_factory=lambda: _load_prompt("system_prompt.txt"))


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise LLMClientError(f"Prompt file is missing: {path}")
    return path.read_text(encoding="utf-8").strip()


class OllamaLLMClient:
    """Production-sensible local HTTP client for Ollama."""

    def __init__(self, config: LLMClientConfig | None = None) -> None:
        self.config = config or LLMClientConfig()
        self._deck_planning_prompt = _load_prompt("deck_planning_prompt.txt")
        self._slide_generation_prompt = _load_prompt("slide_generation_prompt.txt")
        self._json_repair_prompt = _load_prompt("json_repair_prompt.txt")

    async def generate_deck_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate a deck plan JSON with retry + repair fallback."""
        prompt = self._build_deck_plan_prompt(request)
        raw = await self._complete(prompt, task_name="deck planning")
        parsed = self._parse_json(raw)
        if parsed is not None:
            return parsed

        LOGGER.warning("Deck planning JSON parse failed; running repair prompt.")
        return await self.repair_json(
            raw,
            schema_hint={
                "deck_title": "string",
                "audience": "string",
                "deck_objective": "string",
                "slides": [
                    {
                        "id": "s1",
                        "slide_type": "executive_summary|process_flow|layered_architecture|roadmap",
                        "objective": "string",
                        "key_message": "string",
                    }
                ],
            },
        )

    async def generate_slide(
        self,
        deck_context: dict[str, Any],
        slide_plan_item: dict[str, Any],
        previous_slides: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate one semantic slide JSON with retry + repair fallback."""
        prompt = self._build_slide_prompt(deck_context, slide_plan_item, previous_slides or [])
        raw = await self._complete(prompt, task_name="slide generation")
        parsed = self._parse_json(raw)
        if parsed is not None:
            return parsed

        LOGGER.warning("Slide JSON parse failed for %s; running repair prompt.", slide_plan_item.get("id"))
        schema_hint = {
            "id": slide_plan_item.get("id", "s1"),
            "order": slide_plan_item.get("order", 1),
            "type": self._to_schema_slide_type(str(slide_plan_item.get("slide_type", "executive_summary"))),
            "title": "string",
            "objective": str(slide_plan_item.get("objective", "")),
        }
        return await self.repair_json(raw, schema_hint=schema_hint)

    async def repair_json(
        self,
        broken_output: str | None = None,
        schema_hint: dict[str, Any] | None = None,
        *,
        malformed_json: str | None = None,
        expected_shape_hint: str = "",
    ) -> dict[str, Any]:
        """Repair malformed JSON into valid schema-compliant JSON."""
        normalized_broken_output = broken_output if broken_output is not None else malformed_json
        if normalized_broken_output is None:
            raise LLMClientError("repair_json requires broken_output or malformed_json.")

        if schema_hint is None and expected_shape_hint:
            schema_hint = {"expected_shape_hint": expected_shape_hint}

        payload = {
            "broken_output": normalized_broken_output,
            "target_schema_hint": schema_hint or {},
        }
        prompt = f"{self._json_repair_prompt}\n\nINPUT_JSON:\n{json.dumps(payload, ensure_ascii=False)}"
        repaired_raw = await self._complete(prompt, task_name="JSON repair")
        repaired = self._parse_json(repaired_raw)
        if repaired is None:
            LOGGER.error("JSON repair failed; unable to parse repaired output.")
            raise LLMClientError("LLM output could not be parsed after repair attempt.")
        return repaired

    async def plan_deck(self, *, topic: str, audience: str, tone: str, slide_count: int) -> str:
        """Backwards-compatible wrapper returning a JSON string."""
        plan = await self.generate_deck_plan(
            {
                "user_request": topic,
                "constraints": {"audience": audience, "tone": tone, "slide_count": slide_count},
            }
        )
        return json.dumps(plan)

    async def generate_slide_json(self, *, plan_json: str, slide_count: int) -> str:
        """Backwards-compatible wrapper returning exactly one slide JSON string."""
        parsed_plan = self._parse_json(plan_json)
        if not parsed_plan:
            repaired_plan = await self.repair_json(plan_json)
            parsed_plan = repaired_plan

        deck_context = parsed_plan.get("deck_context") if isinstance(parsed_plan, dict) else None
        if not isinstance(deck_context, dict):
            deck_context = {
                "deck_title": parsed_plan.get("deck_title", "Generated Deck") if isinstance(parsed_plan, dict) else "Generated Deck",
                "audience": parsed_plan.get("audience", "Stakeholders") if isinstance(parsed_plan, dict) else "Stakeholders",
                "deck_objective": parsed_plan.get("current_slide_objective", "") if isinstance(parsed_plan, dict) else "",
            }

        slide_plan_item: dict[str, Any] = {
            "id": parsed_plan.get("target_slide", {}).get("id", "s1") if isinstance(parsed_plan, dict) else "s1",
            "order": parsed_plan.get("target_slide", {}).get("order", 1) if isinstance(parsed_plan, dict) else 1,
            "slide_type": parsed_plan.get("selected_slide_type", "executive_summary") if isinstance(parsed_plan, dict) else "executive_summary",
            "objective": parsed_plan.get("current_slide_objective", "") if isinstance(parsed_plan, dict) else "",
            "key_message": parsed_plan.get("target_slide", {}).get("title", "") if isinstance(parsed_plan, dict) else "",
        }

        slide = await self.generate_slide(deck_context=deck_context, slide_plan_item=slide_plan_item)
        return json.dumps(slide)

    async def _complete(self, prompt: str, *, task_name: str) -> str:
        """Run a completion against Ollama with fallback behavior."""
        LOGGER.debug("Running LLM task=%s model=%s", task_name, self.config.model)
        try:
            if self.config.use_chat_api:
                return await self._chat_completion(prompt)
            return await self._generate_completion(prompt)
        except OllamaUnavailableError:
            if self.config.enable_mock_mode:
                LOGGER.warning("Ollama unavailable; using mock response for task=%s", task_name)
                return self._mock_response(task_name)
            raise

    def _build_deck_plan_prompt(self, request: dict[str, Any]) -> str:
        return (
            f"{self._deck_planning_prompt}\n\n"
            f"INPUT_JSON:\n{json.dumps(request, ensure_ascii=False)}"
        )

    def _build_slide_prompt(
        self,
        deck_context: dict[str, Any],
        slide_plan_item: dict[str, Any],
        previous_slides: list[dict[str, Any]],
    ) -> str:
        normalized_plan = dict(slide_plan_item)
        normalized_plan["type"] = self._to_schema_slide_type(str(slide_plan_item.get("slide_type", "executive_summary")))
        input_payload = {
            "deck_context": deck_context,
            "slide_plan_item": normalized_plan,
            "previous_slides": previous_slides,
        }
        return (
            f"{self._slide_generation_prompt}\n\n"
            f"INPUT_JSON:\n{json.dumps(input_payload, ensure_ascii=False)}"
        )

    def _to_schema_slide_type(self, slide_type: str) -> str:
        mapping = {
            "executive_summary": "summary",
            "process_flow": "process",
            "layered_architecture": "architecture",
            "roadmap": "roadmap",
            "summary": "summary",
            "process": "process",
            "architecture": "architecture",
        }
        return mapping.get(slide_type, "content")

    def _parse_json(self, payload: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        return None

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
                    "deck_title": "Order-to-Cash Improvement Plan",
                    "audience": "Executive stakeholders",
                    "deck_objective": "Align on process, architecture, and transformation roadmap.",
                    "slides": [
                        {
                            "id": "s1",
                            "slide_type": "executive_summary",
                            "objective": "Summarize business case",
                            "key_message": "Current flow creates avoidable margin leakage.",
                        },
                        {
                            "id": "s2",
                            "slide_type": "process_flow",
                            "objective": "Show bottlenecks",
                            "key_message": "Manual handoffs slow cycle time.",
                        },
                        {
                            "id": "s3",
                            "slide_type": "layered_architecture",
                            "objective": "Define target capabilities",
                            "key_message": "Platform-based services decouple channels and core systems.",
                        },
                    ],
                }
            )

        if task_name == "JSON repair":
            return "{}"

        return json.dumps(
            {
                "id": "s1",
                "order": 1,
                "type": "summary",
                "title": "Executive Summary",
                "objective": "Highlight the primary decision and next step.",
                "text_blocks": [
                    {"id": "tb1", "role": "bullet", "text": "Cycle time is too long."},
                    {"id": "tb2", "role": "bullet", "text": "Automate credit checks and invoicing."},
                    {"id": "tb3", "role": "bullet", "text": "Launch phased rollout over 2 quarters."},
                ],
            }
        )
