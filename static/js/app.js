const appState = {
  deck: null,
  selectedSlideId: null,
};

const deckList = document.getElementById("deck-list");
const slidePreview = document.getElementById("slide-preview");
const slideTitleLabel = document.getElementById("slide-title-label");
const jsonOutput = document.getElementById("json-output");
const saveButton = document.getElementById("save-deck");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getSelectedSlide() {
  if (!appState.deck || !appState.selectedSlideId) return null;
  return appState.deck.slides.find((slide) => slide.id === appState.selectedSlideId) || null;
}

function renderDeckList() {
  if (!appState.deck) return;

  const listMarkup = appState.deck.slide_order
    .map((slideId) => appState.deck.slides.find((candidate) => candidate.id === slideId))
    .filter(Boolean)
    .map((slide) => {
      const isActive = slide.id === appState.selectedSlideId;
      return `
      <li>
        <button class="deck-item ${isActive ? "active" : ""}" data-slide-id="${slide.id}">
          <span class="deck-item-order">${slide.order}</span>
          <span>
            <strong>${escapeHtml(slide.title)}</strong>
            <small>${escapeHtml(slide.type.replaceAll("_", " "))}</small>
          </span>
        </button>
      </li>
    `;
    })
    .join("");

  deckList.innerHTML = listMarkup;
}

function renderTextBlocks(textBlocks) {
  if (!textBlocks || textBlocks.length === 0) return "";
  return `
    <section class="content-group">
      ${textBlocks
        .map(
          (block) => `
          <article class="text-card" data-bind-path="text_blocks.${block.id}">
            ${
              block.label
                ? `<div class="block-label" contenteditable="true" data-edit-type="block-label" data-block-id="${block.id}">${escapeHtml(block.label)}</div>`
                : ""
            }
            <p contenteditable="true" data-edit-type="block-text" data-block-id="${block.id}">${escapeHtml(block.text)}</p>
          </article>`
        )
        .join("")}
    </section>
  `;
}

function renderProcessSlide(slide) {
  const steps = slide.process?.steps || [];
  return `
    <section class="process-grid">
      ${steps
        .map(
          (step) => `
        <article class="process-step">
          <h4 contenteditable="true" data-edit-type="process-label" data-step-id="${step.id}">${escapeHtml(step.label)}</h4>
          <p contenteditable="true" data-edit-type="process-description" data-step-id="${step.id}">${escapeHtml(step.description || "")}</p>
          <div class="meta-row">
            <span class="chip" contenteditable="true" data-edit-type="process-owner" data-step-id="${step.id}">${escapeHtml(step.owner || "Unassigned")}</span>
          </div>
        </article>
      `
        )
        .join("")}
    </section>
    ${renderTextBlocks(slide.text_blocks)}
  `;
}

function renderArchitectureSlide(slide) {
  const layers = slide.architecture?.layers || [];
  const integrations = slide.architecture?.integrations || [];

  return `
    <section class="architecture-stack">
      ${layers
        .map(
          (layer) => `
          <article class="arch-layer">
            <h4 contenteditable="true" data-edit-type="layer-name" data-layer-id="${layer.id}">${escapeHtml(layer.name)}</h4>
            <p contenteditable="true" data-edit-type="layer-responsibility" data-layer-id="${layer.id}">${escapeHtml(layer.responsibility)}</p>
            <div class="token-row">
              ${layer.components
                .map(
                  (component, index) =>
                    `<span class="token" contenteditable="true" data-edit-type="layer-component" data-layer-id="${layer.id}" data-component-index="${index}">${escapeHtml(component)}</span>`
                )
                .join("")}
            </div>
          </article>
        `
        )
        .join("")}
    </section>
    <section class="integration-list">
      <h3>Integrations</h3>
      ${integrations
        .map(
          (integration) => `
          <article class="integration-item">
            <strong contenteditable="true" data-edit-type="integration-system" data-integration-id="${integration.id}">${escapeHtml(integration.system)}</strong>
            <p contenteditable="true" data-edit-type="integration-purpose" data-integration-id="${integration.id}">${escapeHtml(integration.purpose)}</p>
          </article>
        `
        )
        .join("")}
    </section>
    ${renderTextBlocks(slide.text_blocks)}
  `;
}

function renderRoadmapSlide(slide) {
  const phases = slide.roadmap?.phases || [];
  return `
    <section class="roadmap-grid">
      ${phases
        .map(
          (phase) => `
          <article class="roadmap-phase">
            <h4 contenteditable="true" data-edit-type="phase-name" data-phase-id="${phase.id}">${escapeHtml(phase.name)}</h4>
            <p contenteditable="true" data-edit-type="phase-objective" data-phase-id="${phase.id}">${escapeHtml(phase.objective)}</p>
            <ul>
              ${phase.milestones
                .map(
                  (milestone) => `
                  <li>
                    <span class="status ${milestone.status}">${escapeHtml(milestone.status.replaceAll("_", " "))}</span>
                    <span contenteditable="true" data-edit-type="milestone-label" data-phase-id="${phase.id}" data-milestone-id="${milestone.id}">${escapeHtml(milestone.label)}</span>
                    <small contenteditable="true" data-edit-type="milestone-period" data-phase-id="${phase.id}" data-milestone-id="${milestone.id}">${escapeHtml(milestone.target_period)}</small>
                  </li>
                `
                )
                .join("")}
            </ul>
          </article>
      `
        )
        .join("")}
    </section>
    ${renderTextBlocks(slide.text_blocks)}
  `;
}

function renderSlidePreview() {
  const slide = getSelectedSlide();
  if (!slide) {
    slidePreview.innerHTML = "<p>Select a slide to begin.</p>";
    return;
  }

  slideTitleLabel.textContent = `${slide.order}. ${slide.title}`;

  let body = "";
  if (slide.type === "process") body = renderProcessSlide(slide);
  else if (slide.type === "architecture") body = renderArchitectureSlide(slide);
  else if (slide.type === "roadmap") body = renderRoadmapSlide(slide);
  else body = renderTextBlocks(slide.text_blocks);

  slidePreview.innerHTML = `
    <header class="slide-heading">
      <h3 contenteditable="true" data-edit-type="slide-title">${escapeHtml(slide.title)}</h3>
      <p contenteditable="true" data-edit-type="slide-objective">${escapeHtml(slide.objective || "")}</p>
    </header>
    ${body}
  `;
}

function renderJsonModel() {
  jsonOutput.textContent = JSON.stringify(appState.deck, null, 2);
}

function refreshUi() {
  renderDeckList();
  renderSlidePreview();
  renderJsonModel();
}

function persistEdit(element) {
  const slide = getSelectedSlide();
  if (!slide) return;

  const textValue = element.textContent.trim();
  const editType = element.dataset.editType;

  if (editType === "slide-title") {
    slide.title = textValue;
  } else if (editType === "slide-objective") {
    slide.objective = textValue;
  } else if (editType === "block-label") {
    const block = slide.text_blocks.find((item) => item.id === element.dataset.blockId);
    if (block) block.label = textValue;
  } else if (editType === "block-text") {
    const block = slide.text_blocks.find((item) => item.id === element.dataset.blockId);
    if (block) block.text = textValue;
  } else if (editType === "process-label") {
    const step = slide.process?.steps.find((item) => item.id === element.dataset.stepId);
    if (step) step.label = textValue;
  } else if (editType === "process-description") {
    const step = slide.process?.steps.find((item) => item.id === element.dataset.stepId);
    if (step) step.description = textValue;
  } else if (editType === "process-owner") {
    const step = slide.process?.steps.find((item) => item.id === element.dataset.stepId);
    if (step) step.owner = textValue;
  } else if (editType === "layer-name") {
    const layer = slide.architecture?.layers.find((item) => item.id === element.dataset.layerId);
    if (layer) layer.name = textValue;
  } else if (editType === "layer-responsibility") {
    const layer = slide.architecture?.layers.find((item) => item.id === element.dataset.layerId);
    if (layer) layer.responsibility = textValue;
  } else if (editType === "layer-component") {
    const layer = slide.architecture?.layers.find((item) => item.id === element.dataset.layerId);
    const index = Number(element.dataset.componentIndex);
    if (layer && Number.isInteger(index) && index >= 0) layer.components[index] = textValue;
  } else if (editType === "integration-system") {
    const item = slide.architecture?.integrations.find((integration) => integration.id === element.dataset.integrationId);
    if (item) item.system = textValue;
  } else if (editType === "integration-purpose") {
    const item = slide.architecture?.integrations.find((integration) => integration.id === element.dataset.integrationId);
    if (item) item.purpose = textValue;
  } else if (editType === "phase-name") {
    const phase = slide.roadmap?.phases.find((item) => item.id === element.dataset.phaseId);
    if (phase) phase.name = textValue;
  } else if (editType === "phase-objective") {
    const phase = slide.roadmap?.phases.find((item) => item.id === element.dataset.phaseId);
    if (phase) phase.objective = textValue;
  } else if (editType === "milestone-label") {
    const phase = slide.roadmap?.phases.find((item) => item.id === element.dataset.phaseId);
    const milestone = phase?.milestones.find((item) => item.id === element.dataset.milestoneId);
    if (milestone) milestone.label = textValue;
  } else if (editType === "milestone-period") {
    const phase = slide.roadmap?.phases.find((item) => item.id === element.dataset.phaseId);
    const milestone = phase?.milestones.find((item) => item.id === element.dataset.milestoneId);
    if (milestone) milestone.target_period = textValue;
  }

  refreshUi();
}

async function loadDeck() {
  const response = await fetch("/api/semantic-deck");
  appState.deck = await response.json();
  appState.selectedSlideId = appState.deck.slide_order[0];
  refreshUi();
}

async function saveDeck() {
  saveButton.disabled = true;
  saveButton.textContent = "Saving...";

  const response = await fetch("/api/semantic-deck", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(appState.deck),
  });

  appState.deck = await response.json();
  saveButton.disabled = false;
  saveButton.textContent = "Save JSON Model";
  refreshUi();
}

deckList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-slide-id]");
  if (!button) return;
  appState.selectedSlideId = button.dataset.slideId;
  refreshUi();
});

slidePreview.addEventListener("blur", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement) || !target.dataset.editType) return;
  persistEdit(target);
}, true);

saveButton.addEventListener("click", saveDeck);

loadDeck();
