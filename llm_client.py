from __future__ import annotations

import json
from typing import Any, Dict

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


class OllamaClient:
    def __init__(self, model: str):
        self.model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        prompt = f"{system_prompt}\n\nUser Request:\n{user_prompt}\n\nReturn JSON only."
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        body = response.json()
        return json.loads(body.get("response", "{}"))


def mock_slide_payload(plan: dict, prompt: str, model: str) -> Dict[str, Any]:
    slides = []
    for idx, slide_type in enumerate(plan["slide_types"], start=1):
        slide = {
            "id": f"slide_{idx}",
            "slide_type": slide_type,
            "title": f"{slide_type.replace('_', ' ').title()}",
            "subtitle": "Auto-generated mock content",
            "metadata": {"theme": "blue_enterprise"},
        }
        if slide_type == "executive_summary":
            slide["narrative"] = [
                "Lead-to-cash cycle spans lead capture to invoice settlement.",
                "Target architecture improves visibility and automation.",
            ]
        elif slide_type == "process_flow":
            slide["flow_steps"] = [
                {"id": "s1", "title": "Lead", "detail": "Capture and qualify demand."},
                {"id": "s2", "title": "Quote", "detail": "Generate commercial offer."},
                {"id": "s3", "title": "Order", "detail": "Convert accepted quote."},
                {"id": "s4", "title": "Cash", "detail": "Invoice and collect payment."},
            ]
        elif slide_type == "layered_architecture":
            slide["layers"] = [
                {"name": "Channels", "components": ["Partner Portal", "Sales Console"]},
                {"name": "Business Apps", "components": ["CRM", "CPQ", "ERP"]},
                {"name": "Data", "components": ["MDM", "Data Warehouse"]},
            ]
        elif slide_type == "roadmap":
            slide["roadmap_phases"] = [
                {
                    "name": "Foundation",
                    "timeframe": "Q1",
                    "outcomes": ["Process baseline", "Integration standards"],
                },
                {
                    "name": "Scale",
                    "timeframe": "Q2-Q3",
                    "outcomes": ["Deploy CPQ", "Automate order orchestration"],
                },
                {
                    "name": "Optimize",
                    "timeframe": "Q4",
                    "outcomes": ["Predictive analytics", "Cycle-time reduction"],
                },
            ]
        slides.append(slide)

    return {
        "request": prompt,
        "model": model,
        "plan": plan,
        "slides": slides,
        "warnings": ["Generated with local mock fallback."],
    }
