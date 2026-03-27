from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from layout_engine import layout_for_slide
from llm_client import LLMConfig, MockLLMClient, OllamaClient
from project_store import list_projects, load_project, save_project
from prompt_parser import build_system_prompt, build_user_prompt
from slide_planner import normalize_deck, select_template_for_slide

app = FastAPI(title="Fast Slide Maker", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

INDEX_HTML = Path("templates/index.html").read_text(encoding="utf-8")


class GenerateRequest(BaseModel):
    prompt: str
    slide_count: int = 6
    model: str = "llama3"
    temperature: float = 0.2
    max_tokens: int = 1800
    use_mock: bool = False


class RegenerateSlideRequest(BaseModel):
    prompt: str
    deck: dict[str, Any]
    slide_id: str
    model: str = "llama3"
    temperature: float = 0.2
    max_tokens: int = 800
    use_mock: bool = False


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


def _get_llm(req_model: str, temperature: float, max_tokens: int, use_mock: bool):
    if use_mock:
        return MockLLMClient(), "mock"

    client = OllamaClient(
        LLMConfig(
            model=req_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    )
    ok, reason = client.health_check()
    if not ok:
        return MockLLMClient(), f"fallback:{reason}"
    return client, "ollama"


@app.post("/api/generate")
def generate(req: GenerateRequest):
    llm, mode = _get_llm(req.model, req.temperature, req.max_tokens, req.use_mock)
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(req.prompt, req.slide_count)

    try:
        candidate = llm.generate_structured_json(system_prompt, user_prompt)
        deck = normalize_deck(candidate)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to generate deck: {exc}") from exc

    payload = deck.model_dump(by_alias=True)
    for slide in payload["slides"]:
        slide["template"] = select_template_for_slide(slide["slide_type"])
        slide["render_layout"] = layout_for_slide(slide)

    return {"mode": mode, "deck": payload}


@app.post("/api/regenerate-slide")
def regenerate_slide(req: RegenerateSlideRequest):
    llm, mode = _get_llm(req.model, req.temperature, req.max_tokens, req.use_mock)

    target = next((s for s in req.deck.get("slides", []) if s.get("id") == req.slide_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="slide_id not found")

    context = json.dumps({"presentation": req.deck.get("presentation"), "target_slide": target}, indent=2)
    system_prompt = build_system_prompt()
    user_prompt = (
        build_user_prompt(req.prompt, 1)
        + "\nRegenerate ONLY one slide with matching id and compatible narrative context.\n"
        + context
    )

    try:
        candidate = llm.generate_structured_json(system_prompt, user_prompt)
        regen_deck = normalize_deck(candidate).model_dump(by_alias=True)
        replacement = regen_deck["slides"][0]
        replacement["id"] = req.slide_id
        replacement["template"] = select_template_for_slide(replacement["slide_type"])
        replacement["render_layout"] = layout_for_slide(replacement)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to regenerate slide: {exc}") from exc

    return {"mode": mode, "slide": replacement}


@app.post("/api/save/{project_name}")
def save(project_name: str, payload: dict[str, Any]):
    path = save_project(payload, project_name)
    return {"saved": str(path)}


@app.get("/api/load/{project_name}")
def load(project_name: str):
    try:
        return load_project(project_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc


@app.get("/api/projects")
def projects():
    return {"projects": list_projects()}
