"""Ollama client with prompt templating and mock fallback.

This module keeps all LLM-specific behavior in one place.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class LLMConfig:
    """Runtime model configuration for Ollama."""

    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.2
    max_tokens: int = 1800
    endpoint: str = "/api/chat"
    timeout_seconds: float = 45.0


class OllamaClient:
    """Small wrapper for structured JSON generation via local Ollama."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = httpx.get(f"{self.config.base_url}/api/tags", timeout=3)
            resp.raise_for_status()
            return True, "Ollama reachable"
        except Exception as exc:  # noqa: BLE001
            return False, f"Ollama unavailable: {exc}"

    def _build_messages(self, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate_structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Generate JSON from Ollama and parse response safely."""
        ok, reason = self.health_check()
        if not ok:
            raise RuntimeError(reason)

        messages = self._build_messages(system_prompt, user_prompt)

        payload = {
            "model": self.config.model,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
            "format": "json",
        }

        if self.config.endpoint == "/api/chat":
            payload["messages"] = messages
        else:
            payload["prompt"] = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            resp = client.post(f"{self.config.base_url}{self.config.endpoint}", json=payload)
            resp.raise_for_status()
            data = resp.json()

        raw = self._extract_text(data)
        return self._coerce_json(raw)

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        if "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content", "")
        if "response" in data:
            return data["response"]
        return "{}"

    @staticmethod
    def _coerce_json(raw: str) -> dict[str, Any]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()
        return json.loads(raw)


class MockLLMClient:
    """Offline fallback used when Ollama is not running."""

    def generate_structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        _ = system_prompt
        return {
            "presentation": {
                "title": "Order-to-Cash Process and Target IT Architecture",
                "theme": "consulting",
                "description": user_prompt,
            },
            "slides": [
                {
                    "id": "s1",
                    "title": "Executive Summary",
                    "objective": "Align leaders on process pain points and target-state direction.",
                    "slide_type": "executive summary",
                    "audience": "Executive sponsors",
                    "summary": "Current order-to-cash cycle is fragmented; target architecture improves cycle time and control.",
                    "content_blocks": [
                        {"type": "key_message", "text": "Cycle time reduction through integrated platform"},
                        {"type": "fact", "text": "Current handoffs create delays and rework"},
                    ],
                    "diagram_data": {"nodes": [], "edges": []},
                    "layout_hints": {"density": "low", "emphasis": "headline"},
                    "audience_takeaway": "Approve target-state initiative.",
                    "key_entities": ["Sales", "Finance", "Customer"],
                    "relationships": ["Sales hands order to fulfillment and billing"],
                    "priority_of_information": ["decision", "risks", "next steps"],
                },
                {
                    "id": "s2",
                    "title": "Order-to-Cash Process Flow",
                    "objective": "Show end-to-end process and failure points.",
                    "slide_type": "process flow",
                    "audience": "Process owners",
                    "summary": "Six-step flow from order capture to cash application.",
                    "content_blocks": [{"type": "note", "text": "Manual checks at billing create bottlenecks."}],
                    "diagram_data": {
                        "nodes": [
                            {"id": "n1", "label": "Capture Order", "type": "process"},
                            {"id": "n2", "label": "Validate Credit", "type": "process"},
                            {"id": "n3", "label": "Fulfill Order", "type": "process"},
                            {"id": "n4", "label": "Issue Invoice", "type": "process"},
                            {"id": "n5", "label": "Collect Cash", "type": "process"},
                        ],
                        "edges": [
                            {"from": "n1", "to": "n2", "label": "submitted"},
                            {"from": "n2", "to": "n3", "label": "approved"},
                            {"from": "n3", "to": "n4", "label": "shipped"},
                            {"from": "n4", "to": "n5", "label": "due"},
                        ],
                    },
                    "layout_hints": {"density": "medium", "emphasis": "flow"},
                    "audience_takeaway": "Focus automation on invoice and cash steps.",
                    "key_entities": ["ERP", "CRM", "Billing"],
                    "relationships": ["CRM sends order to ERP", "ERP sends invoice to billing"],
                    "priority_of_information": ["critical path", "bottlenecks", "handoffs"],
                },
                {
                    "id": "s3",
                    "title": "Target Layered Architecture",
                    "objective": "Describe future-state platform stack.",
                    "slide_type": "layered architecture",
                    "audience": "IT architecture board",
                    "summary": "Channel, process, integration, data, and platform layers with clear ownership.",
                    "content_blocks": [{"type": "principle", "text": "API-led integration with master data governance."}],
                    "diagram_data": {
                        "layers": [
                            {"id": "l1", "label": "Experience", "items": ["Portal", "Sales UI"]},
                            {"id": "l2", "label": "Process", "items": ["Order Mgmt", "Billing"]},
                            {"id": "l3", "label": "Integration", "items": ["API Gateway", "Event Bus"]},
                            {"id": "l4", "label": "Data", "items": ["Customer MDM", "AR Data Mart"]},
                        ]
                    },
                    "layout_hints": {"density": "medium", "emphasis": "stack"},
                    "audience_takeaway": "Validate investment in integration and data layers.",
                    "key_entities": ["API gateway", "ERP", "MDM"],
                    "relationships": ["Process layer consumes integration services"],
                    "priority_of_information": ["platform layers", "interfaces", "ownership"],
                },
            ],
        }
