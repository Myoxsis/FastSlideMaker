from __future__ import annotations

from typing import Dict

from schema import Slide


PALETTE = {
    "bg": "#f8fafc",
    "primary": "#1d4ed8",
    "secondary": "#0f172a",
    "accent": "#0ea5e9",
    "muted": "#475569",
}


def to_view_model(slide: Slide) -> Dict:
    return {
        "id": slide.id,
        "type": slide.slide_type,
        "title": slide.title,
        "subtitle": slide.subtitle,
        "palette": PALETTE,
        "content": slide.model_dump(),
    }
