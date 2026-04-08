# AGENTS.md

This file defines repository-wide guidance for Codex and other coding agents working in **FastSlideMaker**.

## Core principles
- **Preserve JSON as the source of truth.** Treat slide/content JSON as canonical; do not introduce alternate authoritative representations.
- **Keep business semantics separate from layout logic.** Domain/content meaning belongs in data/services; positioning/styling belongs in rendering/layout layers.
- **Prefer deterministic rendering over generative layout.** Given the same input JSON, produce the same structure/output unless explicitly configured otherwise.
- **Never export slides as screenshots.** Do not flatten slide content into images as an export strategy.
- **Preserve editability in PPTX exports.** Export real, editable PPTX objects (text boxes, shapes, tables, etc.), not rasterized artifacts.
- **Use modular Python.** Favor small, focused modules/functions over monolithic scripts.
- **Keep vanilla JS lightweight and understandable.** Prefer clear DOM/state logic without heavy abstractions.
- **Avoid unnecessary dependencies.** Add packages only when clearly justified and document why.
- **Run and verify the app after changes when practical.** Execute relevant run/test checks for touched areas.
- **Keep comments useful but not excessive.** Explain intent/invariants, not obvious line-by-line behavior.
- **Document assumptions clearly.** Record non-obvious constraints and tradeoffs near the relevant code/docs.

## Repo layout
- `app/` — application package
  - `app/models/` — schemas and data structures
  - `app/services/` — generation and business/service logic
- `static/` — frontend assets
  - `static/js/` — vanilla JavaScript UI logic
  - `static/css/` — styling
- `project_store.py` — project persistence/state entry point
- `README.md` — project overview and usage
- `pytest.ini` — test configuration

## Run commands
Use these as defaults (adapt if README or tooling changes):
- Install dependencies: `pip install -r requirements.txt`
- Run app (dev): `python -m app` *(or the documented entrypoint in `README.md`)*
- Run tests: `pytest`

If a command differs in this repo, update this section when you discover the canonical command.

## Coding conventions
### Python
- Keep modules cohesive and composable; extract helpers instead of growing large functions.
- Keep semantic/content transforms independent from rendering/layout transforms.
- Prefer explicit data contracts via existing schema/model layer.
- Minimize global mutable state.

### JavaScript (vanilla)
- Keep functions short and named by behavior.
- Prefer straightforward event handling and DOM updates.
- Avoid framework-like complexity in plain JS files.

### Cross-cutting
- Maintain deterministic behavior for the same inputs.
- Add dependencies only with clear technical need.
- Write comments for intent, assumptions, and edge cases.

## Done criteria
A change is considered done when all applicable items are satisfied:
1. JSON remains the canonical source for slide/content data.
2. Business semantics and layout logic are cleanly separated.
3. Rendering/export behavior remains deterministic for identical inputs.
4. PPTX output remains editable and is not image/screenshot-based.
5. Code follows modular Python and lightweight vanilla JS expectations.
6. Relevant tests/checks are run; app is manually verified when practical.
7. Assumptions and notable tradeoffs are documented.

## Do-not rules
- Do **not** treat generated layout artifacts as source-of-truth state.
- Do **not** couple domain/business rules directly to presentation coordinates/styles.
- Do **not** introduce non-deterministic layout behavior by default.
- Do **not** export slides as screenshots or flattened images.
- Do **not** sacrifice PPTX editability for convenience.
- Do **not** add heavyweight dependencies without strong justification.
- Do **not** add noisy or redundant comments.
- Do **not** ship changes without verification when practical.
