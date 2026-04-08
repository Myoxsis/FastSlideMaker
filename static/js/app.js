import { ensureDeckDefaults, getSelectedSlide, state, updateSelection } from "./editor_state.js";
import { applySelectionClass, attachSelectionHandlers } from "./selection_manager.js";
import { attachInspectorHandlers, updateInspectorFromSelection } from "./inspector.js";
import { attachToolbarHandlers } from "./toolbar.js";
import { attachCanvasManipulationHandlers } from "./canvas_manipulation.js";

const deckList = document.getElementById("deck-list");
const slidePreview = document.getElementById("slide-preview");
const slideTitleLabel = document.getElementById("slide-title-label");
const jsonOutput = document.getElementById("json-output");
const saveButton = document.getElementById("save-deck");
const exportJsonButton = document.getElementById("export-json");
const exportPptxButton = document.getElementById("export-pptx");
const projectNameInput = document.getElementById("project-name");
const projectGalleryList = document.getElementById("project-gallery-list");
const promptInput = document.getElementById("prompt-input");
const promptUpdatedAt = document.getElementById("prompt-updated-at");
const updatePromptButton = document.getElementById("update-prompt");
const regenerateDeckButton = document.getElementById("regenerate-deck");
const regenerateSlideButton = document.getElementById("regenerate-slide");
const toolbar = document.getElementById("editor-toolbar");
const inspector = document.getElementById("inspector-panel");

let statusTimeout = null;

function setStatus(message, isError = false) {
  if (!message) return;
  clearTimeout(statusTimeout);
  slideTitleLabel.textContent = message;
  slideTitleLabel.style.color = isError ? "#b42318" : "";
  statusTimeout = setTimeout(() => {
    const slide = getSelectedSlide();
    slideTitleLabel.textContent = slide ? `${slide.order}. ${slide.title}` : "";
    slideTitleLabel.style.color = "";
  }, 2600);
}

async function parseJsonResponse(response) {
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch (_error) {}
    throw new Error(detail);
  }
  return response.json();
}

const escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");

function renderProjectGallery() {
  if (!state.projects.length) {
    projectGalleryList.innerHTML = '<li><small class="muted">No saved projects yet.</small></li>';
    return;
  }
  projectGalleryList.innerHTML = state.projects
    .map((project) => `<li class="project-item"><div><strong>${escapeHtml(project.name)}</strong><small>${escapeHtml(project.source)} · ${escapeHtml(project.updated_at || "")}</small></div><button type="button" data-load-project-id="${project.project_id}">Load</button></li>`)
    .join("");
}

function renderDeckList() {
  if (!state.deck) return;
  deckList.innerHTML = state.deck.slide_order
    .map((slideId) => state.deck.slides.find((item) => item.id === slideId))
    .filter(Boolean)
    .map(
      (slide) => `<li><button class="deck-item ${slide.id === state.selectedSlideId ? "active" : ""}" data-slide-id="${slide.id}"><span class="deck-item-order">${slide.order}</span><span><strong>${escapeHtml(slide.title)}</strong><small>${escapeHtml(slide.type.replaceAll("_", " "))}</small></span></button></li>`
    )
    .join("");
}

function blockStyle(style = {}) {
  return `font-size:${style.font_size || 16}px;font-weight:${style.font_weight === "bold" ? 700 : 400};font-style:${style.italic ? "italic" : "normal"};color:${style.text_color || "#111827"};text-align:${style.text_align || "left"};line-height:${style.line_spacing || 1.2};padding:${style.padding || 8}px;text-transform:${style.text_case === "uppercase" ? "uppercase" : "none"};font-family:${style.font_family || state.deck?.theme?.font_family || "Inter"};`;
}

function renderSlideCanvas(slide) {
  const textBlocks = (slide.text_blocks || [])
    .map((block) => `<article class="text-card canvas-element" data-element-key="text:${block.id}" style="${blockStyle(block.style)}"><strong contenteditable="true" data-edit-type="block-label" data-block-id="${block.id}">${escapeHtml(block.label || "")}</strong><p contenteditable="true" data-edit-type="block-text" data-block-id="${block.id}">${escapeHtml(block.text || "")}</p></article>`)
    .join("");

  const shapes = (slide.visual_elements || [])
    .sort((a, b) => (a.z_index || 0) - (b.z_index || 0))
    .map((shape) => {
      const style = shape.style || {};
      return `<div class="shape-element canvas-element shape-${shape.type}" data-element-key="shape:${shape.id}" style="left:${shape.x || 0}px;top:${shape.y || 0}px;width:${shape.w || 120}px;height:${shape.h || 60}px;z-index:${shape.z_index || 1};background:${style.fill_color || "transparent"};border:${style.border_width || 1}px solid ${style.border_color || "#64748b"};opacity:${style.opacity ?? 1};border-radius:${style.corner_radius || 0}px;"><span>${escapeHtml(shape.label || shape.type)}</span></div>`;
    })
    .join("");

  return `<div class="canvas ${slide.layout_hints.grid_visible ? "with-grid" : ""} ${slide.layout_hints.safe_bounds_visible ? "with-safe-bounds" : ""}"><header class="slide-heading canvas-element" data-element-key="title:slide-title"><h3 contenteditable="true" data-edit-type="slide-title">${escapeHtml(slide.title)}</h3><p contenteditable="true" data-edit-type="slide-objective" data-element-key="objective:slide-objective">${escapeHtml(slide.objective || "")}</p></header><section class="content-group">${textBlocks}</section>${shapes}</div>`;
}

function renderPromptPanel() {
  if (!state.deck) return;
  promptInput.value = state.deck.user_prompt || "";
  promptUpdatedAt.textContent = state.deck.prompt_last_updated_at ? `Last updated: ${state.deck.prompt_last_updated_at}` : "Last updated: never";
}

function renderJsonModel() {
  jsonOutput.textContent = JSON.stringify(state.deck, null, 2);
}

function renderSlidePreview() {
  const slide = getSelectedSlide();
  if (!slide) {
    slidePreview.innerHTML = "<p>Select a slide.</p>";
    return;
  }
  slideTitleLabel.textContent = `${slide.order}. ${slide.title}`;
  slidePreview.innerHTML = renderSlideCanvas(slide);
  applySelectionClass(slidePreview);
}

function refreshUi() {
  renderProjectGallery();
  renderDeckList();
  renderPromptPanel();
  renderSlidePreview();
  renderJsonModel();
  updateInspectorFromSelection(inspector);
}

function persistEdit(element) {
  const slide = getSelectedSlide();
  if (!slide) return;
  const textValue = element.textContent.trim();
  const editType = element.dataset.editType;

  if (editType === "slide-title") slide.title = textValue;
  else if (editType === "slide-objective") slide.objective = textValue;
  else if (editType === "block-label") {
    const block = slide.text_blocks.find((item) => item.id === element.dataset.blockId);
    if (block) block.label = textValue;
  } else if (editType === "block-text") {
    const block = slide.text_blocks.find((item) => item.id === element.dataset.blockId);
    if (block) block.text = textValue;
  }

  slide.user_modified = true;
  refreshUi();
}

async function loadDeck() {
  const response = await fetch("/api/semantic-deck");
  state.deck = ensureDeckDefaults(await parseJsonResponse(response));
  state.selectedSlideId = state.deck.slide_order[0];
  projectNameInput.value = state.deck.metadata?.title || "";
  refreshUi();
}

async function loadProjects() {
  const response = await fetch("/api/projects");
  state.projects = (await parseJsonResponse(response)).projects || [];
  refreshUi();
}

async function saveDeck() {
  const name = projectNameInput.value.trim() || state.deck.metadata?.title || "Untitled Project";
  const response = await fetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, deck: state.deck }),
  });
  const project = await parseJsonResponse(response);
  state.selectedProjectId = project.project_id;
  await loadProjects();
}

async function loadProject(projectId) {
  const response = await fetch(`/api/projects/${projectId}`);
  const payload = await parseJsonResponse(response);
  state.deck = ensureDeckDefaults(payload.deck);
  state.selectedSlideId = state.deck.slide_order[0];
  state.selectedProjectId = payload.project_id;
  refreshUi();
}

function addSlide() {
  const newId = `slide-${Date.now()}`;
  state.deck.slides.push({
    id: newId,
    order: state.deck.slides.length + 1,
    type: "content",
    title: "New Slide",
    objective: "",
    text_blocks: [{ id: `tb-${Date.now()}`, role: "body", text: "Add content", style: { font_size: 16, font_weight: "regular", text_color: "#111827", text_align: "left", line_spacing: 1.2, padding: 8 } }],
    visual_elements: [],
    layout_hints: { grid_visible: true, safe_bounds_visible: true, snap_to_grid: true, show_guides: true, margin_x: 36, margin_y: 24, spacing_density: "standard", template_variant: "default" },
  });
  state.deck.slide_order.push(newId);
  state.selectedSlideId = newId;
  refreshUi();
}

function duplicateSlide() {
  const slide = getSelectedSlide();
  if (!slide) return;
  const clone = structuredClone(slide);
  clone.id = `${slide.id}-copy-${Date.now()}`;
  clone.title = `${slide.title} (copy)`;
  state.deck.slides.push(clone);
  state.deck.slide_order.push(clone.id);
  reindexSlides();
  state.selectedSlideId = clone.id;
  refreshUi();
}

function deleteSlide() {
  if (state.deck.slides.length <= 1) return;
  const id = state.selectedSlideId;
  state.deck.slides = state.deck.slides.filter((slide) => slide.id !== id);
  state.deck.slide_order = state.deck.slide_order.filter((slideId) => slideId !== id);
  reindexSlides();
  state.selectedSlideId = state.deck.slide_order[0];
  refreshUi();
}

function reindexSlides() {
  state.deck.slide_order.forEach((id, index) => {
    const slide = state.deck.slides.find((item) => item.id === id);
    if (slide) slide.order = index + 1;
  });
}

document.getElementById("add-slide").addEventListener("click", addSlide);
document.getElementById("duplicate-slide").addEventListener("click", duplicateSlide);
document.getElementById("delete-slide").addEventListener("click", deleteSlide);

deckList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-slide-id]");
  if (!button) return;
  state.selectedSlideId = button.dataset.slideId;
  updateSelection(null);
  refreshUi();
});
projectGalleryList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-load-project-id]");
  if (!button) return;
  loadProject(button.dataset.loadProjectId).catch((error) => setStatus(error.message, true));
});
slidePreview.addEventListener("blur", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement) || !target.dataset.editType) return;
  persistEdit(target);
}, true);

saveButton.addEventListener("click", () => saveDeck().then(() => setStatus("Project saved.")).catch((error) => setStatus(error.message, true)));
exportJsonButton.addEventListener("click", () => window.location.assign(`/api/projects/${state.selectedProjectId}/export/json`));
exportPptxButton.addEventListener("click", () => window.location.assign(`/api/projects/${state.selectedProjectId}/export/pptx`));
updatePromptButton.addEventListener("click", async () => {
  const response = await fetch("/api/semantic-deck/prompt", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_prompt: promptInput.value }) });
  state.deck = ensureDeckDefaults(await parseJsonResponse(response));
  refreshUi();
});
regenerateDeckButton.addEventListener("click", async () => {
  const response = await fetch("/api/semantic-deck/regenerate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_prompt: promptInput.value }) });
  state.deck = ensureDeckDefaults(await parseJsonResponse(response));
  refreshUi();
});
regenerateSlideButton.addEventListener("click", async () => {
  const response = await fetch("/api/semantic-deck/regenerate-slide", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ slide_id: state.selectedSlideId, user_prompt: promptInput.value }) });
  state.deck = ensureDeckDefaults(await parseJsonResponse(response));
  refreshUi();
});

attachSelectionHandlers(slidePreview, () => {
  applySelectionClass(slidePreview);
  updateInspectorFromSelection(inspector);
});
attachCanvasManipulationHandlers(
  slidePreview,
  () => {
    applySelectionClass(slidePreview);
    updateInspectorFromSelection(inspector);
  },
  refreshUi
);
attachInspectorHandlers(inspector, refreshUi);
attachToolbarHandlers(toolbar, refreshUi);

loadDeck().catch((error) => setStatus(`Failed to load deck: ${error.message}`, true));
loadProjects().catch((error) => setStatus(`Failed to load projects: ${error.message}`, true));
