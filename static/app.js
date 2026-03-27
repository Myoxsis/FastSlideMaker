let state = { deck: null, selected: 0 };

const el = (id) => document.getElementById(id);

function setStatus(text) {
  el("status").textContent = text;
}

function getConfig() {
  return {
    prompt: el("promptInput").value.trim(),
    slide_count: Number(el("slideCountInput").value || 6),
    model: el("modelInput").value.trim() || "llama3",
    temperature: Number(el("tempInput").value || 0.2),
    max_tokens: Number(el("maxTokensInput").value || 1800),
    use_mock: el("mockInput").checked,
  };
}

async function callApi(url, method = "GET", body = null) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : null,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function renderTabs() {
  const tabs = el("slideTabs");
  tabs.innerHTML = "";
  if (!state.deck) return;
  state.deck.slides.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = `tab ${i === state.selected ? "active" : ""}`;
    b.textContent = `${i + 1}. ${s.title}`;
    b.onclick = () => {
      state.selected = i;
      renderAll();
    };
    tabs.appendChild(b);
  });
}

function renderDiagram(slide) {
  const t = slide.template;
  if (t === "process_flow") {
    const nodes = slide.diagram_data.nodes || [];
    return `<div class="process-row">${nodes.map((n) => `<div class="step">${n.label}</div>`).join("")}</div>`;
  }
  if (t === "layered_architecture") {
    const layers = slide.diagram_data.layers || [];
    return `<div>${layers.map((l) => `<div class="layer-row"><div class="layer"><b>${l.label}</b><br/>${(l.items || []).join(" • ")}</div></div>`).join("")}</div>`;
  }
  if (t === "roadmap") {
    const m = slide.diagram_data.milestones || [];
    return `<div class="roadmap-row">${m.map((x) => `<div class="mile"><b>${x.period}</b><br/>${x.label}</div>`).join("")}</div>`;
  }
  return `<ul>${(slide.content_blocks || []).map((b) => `<li>${b.text}</li>`).join("")}</ul>`;
}

function renderSlide() {
  const target = el("slidePreview");
  if (!state.deck) {
    target.innerHTML = "<p>No deck generated yet.</p>";
    return;
  }
  const slide = state.deck.slides[state.selected];
  target.innerHTML = `
    <h3>${slide.title}</h3>
    <div class="meta">${slide.slide_type} • Audience: ${slide.audience}</div>
    <div class="grid">
      <div class="box"><b>Objective</b><p>${slide.objective}</p></div>
      <div class="box"><b>Audience Takeaway</b><p>${slide.audience_takeaway}</p></div>
    </div>
    <div class="box" style="margin-top:10px;"><b>Summary</b><p>${slide.summary}</p></div>
    <div style="margin-top:8px;">${(slide.key_entities || []).map((x) => `<span class="badge">${x}</span>`).join("")}</div>
    ${renderDiagram(slide)}
  `;
}

function bindEditor() {
  if (!state.deck) return;
  const s = state.deck.slides[state.selected];
  el("titleEdit").value = s.title;
  el("objectiveEdit").value = s.objective;
  el("summaryEdit").value = s.summary;
  el("entitiesEdit").value = (s.key_entities || []).join(", ");
  el("relationshipsEdit").value = (s.relationships || []).join("\n");
}

function applyEdits() {
  if (!state.deck) return;
  const s = state.deck.slides[state.selected];
  s.title = el("titleEdit").value;
  s.objective = el("objectiveEdit").value;
  s.summary = el("summaryEdit").value;
  s.key_entities = el("entitiesEdit").value.split(",").map((x) => x.trim()).filter(Boolean);
  s.relationships = el("relationshipsEdit").value.split("\n").map((x) => x.trim()).filter(Boolean);
  renderAll();
}

function renderAll() {
  renderTabs();
  renderSlide();
  bindEditor();
}

el("generateBtn").onclick = async () => {
  try {
    setStatus("Generating deck...");
    const result = await callApi("/api/generate", "POST", getConfig());
    state.deck = result.deck;
    state.selected = 0;
    renderAll();
    setStatus(`Deck generated (${result.mode}).`);
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  }
};

el("regenerateBtn").onclick = async () => {
  if (!state.deck) return setStatus("Generate deck first.");
  try {
    setStatus("Regenerating selected slide...");
    const result = await callApi("/api/regenerate-slide", "POST", {
      prompt: el("promptInput").value,
      deck: state.deck,
      slide_id: state.deck.slides[state.selected].id,
      model: el("modelInput").value,
      temperature: Number(el("tempInput").value),
      max_tokens: 1000,
      use_mock: el("mockInput").checked,
    });
    state.deck.slides[state.selected] = result.slide;
    renderAll();
    setStatus(`Slide regenerated (${result.mode}).`);
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  }
};

el("saveBtn").onclick = async () => {
  if (!state.deck) return setStatus("Nothing to save.");
  const name = prompt("Project name", "otc_deck");
  if (!name) return;
  try {
    const r = await callApi(`/api/save/${name}`, "POST", state.deck);
    setStatus(`Saved to ${r.saved}`);
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  }
};

el("loadBtn").onclick = async () => {
  try {
    const list = await callApi("/api/projects");
    const name = prompt(`Available: ${list.projects.join(", ")}\nProject name to load:`);
    if (!name) return;
    state.deck = await callApi(`/api/load/${name}`);
    state.selected = 0;
    renderAll();
    setStatus(`Loaded ${name}.`);
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  }
};

el("exportBtn").onclick = () => {
  if (!state.deck) return setStatus("Nothing to export.");
  const blob = new Blob([JSON.stringify(state.deck, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "slide_deck.json";
  a.click();
  setStatus("Exported JSON.");
};

el("applyEditBtn").onclick = () => applyEdits();

renderAll();
