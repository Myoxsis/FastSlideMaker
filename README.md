# Fast Slide Maker

Fast Slide Maker is a lightweight FastAPI app for generating, editing, and exporting semantic slide decks.

## Reliability-focused behavior

- Startup boot sequence wires core services and validates mock prompt/template consistency.
- LLM generation supports graceful fallback to deterministic mock mode.
- JSON parsing is validated for model output and project files.
- Export writes deterministic artifacts under `artifacts/`.
- Semantic decks pass through a deterministic designer phase (validator -> designer -> renderer/exporter).
- Frontend surfaces save/load/export failures instead of silently ignoring them.

## Quickstart

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment (optional)

Create `.env`:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TEMPERATURE=0.4
OLLAMA_TOP_P=0.9
OLLAMA_MAX_TOKENS=1200
ENABLE_MOCK_MODE=true
REQUEST_TIMEOUT_SECONDS=20
```

### 3) Run the app

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

### 4) Verify health + sample prompts

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/mock-mode/examples
```

### 5) Run tests

```bash
pytest -q
```

## Practical flows to verify

### App boot sequence
- Start the server and check `/health` returns `"status": "ok"`.
- Confirm startup created `generation_service`, `project_store`, and `ollama_available` app state (covered by tests).

### Export path
- Save a project in the UI.
- Export JSON/PPTX from the header buttons.
- Confirm files are downloaded and JSON artifacts appear in `artifacts/`.

### Single-slide regeneration
- Unit tests cover `SlideGenerator.regenerate_semantic_slide` end-to-end for one-slide regeneration with normalization and fallback behavior.

## Project layout

```text
app/
  api/
  core/
  models/
  services/
  utils/json_utils.py
project_store.py
templates/index.html
static/js/app.js
static/js/editor_state.js
static/js/selection_manager.js
static/js/toolbar.js
static/js/inspector.js
static/js/shape_factory.js
samples/
tests/
```

## Designer phase

A deterministic Python designer phase runs before semantic rendering and PPTX export. It applies spacing, fit, overlap, and density rules from `app/services/design_rules.json` and writes `layout_hints` + normalized `diagram_data` per slide.

Pipeline: `LLM -> JSON -> validator -> designer -> renderer -> PPTX exporter`.

See `samples/designer_transformation.sample.json` for a before/after transformation example.


## Presentation editor capabilities

The web UI now includes a structured presentation-editor layer with:
- Top toolbar for arrangement actions and inserting deterministic shapes/icons/callouts/dividers.
- Left slide thumbnail manager with add/duplicate/delete controls.
- Center slide canvas with element selection highlighting and inline text editing.
- Right inspector panel for text and shape properties (size, weight, colors, alignment, opacity, borders, spacing, padding, bullet style, casing, lock flag).
- JSON-first state updates: edits are written back to semantic slide JSON (`text_blocks.style`, `visual_elements`, `layout_hints`, `user_locked`, `user_modified`).
- Regeneration lock behavior: `user_locked` slides/elements are preserved during regeneration, and manual visual overrides are retained where possible.
- PPTX export maps edited text/shape styles to native editable PowerPoint primitives (text formatting, fill, border, alignment, order).

### Current limitations
- Multi-select is basic (shift-select tracks IDs but arrangement is primarily single-element actions).
- Direct drag-and-drop is intentionally limited; inspector + nudge controls are the primary editing path.
- Shape set is intentionally constrained to keep rendering deterministic and schema-safe.
