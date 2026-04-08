from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InterpretedRequest:
    prompt: str
    slide_count: int
    objective: str


def interpret_request(prompt: str) -> InterpretedRequest:
    count_match = re.search(r"(\d+)\s*-?slide", prompt, flags=re.IGNORECASE)
    slide_count = int(count_match.group(1)) if count_match else 5
    slide_count = max(3, min(12, slide_count))

    objective = prompt.strip().rstrip(".")
    if objective.lower().startswith("create"):
        objective = objective[6:].strip()

    return InterpretedRequest(prompt=prompt, slide_count=slide_count, objective=objective)
