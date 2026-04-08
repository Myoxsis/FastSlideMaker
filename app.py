from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from deck_planner import build_deck_plan
from layout_engine import to_view_model
from pptx_exporter import PptxExporter
from project_store import list_projects, load_project, save_project
from request_interpreter import interpret_request
from schema import GenerationRequest, GenerationResponse
from slide_generator import generate_semantic_deck
from validator import validate_and_normalize

app = FastAPI(title="Fast Slide Maker")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest):
    interpreted = interpret_request(req.prompt)
    plan = build_deck_plan(objective=interpreted.objective, slide_count=interpreted.slide_count)
    raw = generate_semantic_deck(prompt=req.prompt, model=req.model, plan=plan)
    validation = validate_and_normalize(raw)
    if not validation.valid or not validation.normalized_deck:
        raise HTTPException(status_code=422, detail={"errors": validation.errors})

    record = save_project(validation.normalized_deck)
    return GenerationResponse(project_id=record.project_id, deck=record.deck)


@app.get("/api/projects")
def projects():
    return list_projects()


@app.get("/api/projects/{project_id}")
def project(project_id: str):
    record = load_project(project_id)
    return record.model_dump()


@app.get("/api/projects/{project_id}/preview")
def preview(project_id: str):
    record = load_project(project_id)
    return [to_view_model(s) for s in record.deck.slides]


@app.get("/api/projects/{project_id}/export")
def export_pptx(project_id: str):
    record = load_project(project_id)
    out_path = Path("samples/exports") / f"{project_id}.pptx"
    exporter = PptxExporter()
    exporter.export(record.deck, out_path)
    return FileResponse(
        str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{project_id}.pptx",
    )
