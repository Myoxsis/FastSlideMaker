"""Small JSON parsing helpers shared by generation and storage flows."""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(payload: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from raw model output."""
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(cleaned[start : end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
