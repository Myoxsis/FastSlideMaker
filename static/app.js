let state = {
  deck: null,
  selected: 0,
  logs: [],
};

const el = (id) => document.getElementById(id);

function setStatus(text) {
  el("status").textContent = text;
  addLog("app", text);
}

function addLog(source, message) {
  state.logs.push({ source, message, at: new Date().toISOString() });
  renderLogs();
}

function getConfig() {
  return {
    prompt: el("promptInput").value.trim(),
    slide_count: Number(el("slideCountInput").value || 6),
    base_url: el("baseUrlInput").value.trim() || "http://localhost:11434",
    endpoint: el("endpointInput").value.trim() || "/api/chat",
    model: el("modelInput").value.trim() || "llama3",
    temperature: Number(el("tempInput").value || 0.2),
    max_tokens: Number(el("maxTokensInput").value || 1800),
    use_mock: el("mockInput").checked,
  };
}

function configOnly() {
  const cfg = getConfig();
  delete cfg.prompt;
  delete cfg.slide_count;
  return cfg;
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

function setActiveTab(tabName) {
  document.querySelectorAll(".side-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
}

function renderTabs() {
  const tabs = el("slideTabs");
  tabs.innerHTML = "";
  if (!state.deck) {
    tabs.innerHTML = "<p class='hint'>Generate a deck to see slides.</p>";
    return;
  }
  state.deck.slides.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = `slide-thumb ${i === state.selected ? "active" : ""}`;
    b.innerHTML = `<span class='slide-index'>${i + 1}</span><span>${s.title}</span>`;
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
  addLog("app", `Slide ${state.selected + 1} updated manually.`);
  renderAll();
}

function renderChat() {
  const container = el("chatMessages");
  const chatItems = state.logs.filter((l) => l.source === "user" || l.source === "llm");
  container.innerHTML = chatItems.length
    ? chatItems.map((l) => `<div class="msg ${l.source}"><b>${l.source.toUpperCase()}:</b> ${l.message}</div>`).join("")
    : "<p class='hint'>No chat yet. Start with a question.</p>";
  container.scrollTop = container.scrollHeight;
}

function renderLogs() {
  const container = el("logContainer");
  container.innerHTML = state.logs.length
    ? state.logs
        .slice()
        .reverse()
        .map((l) => `<div class="log-item"><span>[${new Date(l.at).toLocaleTimeString()}]</span> <b>${l.source}</b>: ${l.message}</div>`)
        .join("")
    : "<p class='hint'>No activity logs yet.</p>";
  renderChat();
}

function renderAll() {
  renderTabs();
  renderSlide();
  bindEditor();
  renderLogs();
}

async function loadSettings() {
  try {
    const settings = await callApi("/api/settings");
    el("baseUrlInput").value = settings.base_url;
    el("endpointInput").value = settings.endpoint;
    el("modelInput").value = settings.model;
    el("tempInput").value = settings.temperature;
    el("maxTokensInput").value = settings.max_tokens;
    el("mockInput").checked = settings.use_mock;
  } catch (e) {
    addLog("app", `Could not load settings: ${e.message}`);
  }
}

el("generateBtn").onclick = async () => {
  try {
    setStatus("Generating deck...");
    const config = getConfig();
    const result = await callApi("/api/generate", "POST", config);
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
    const config = getConfig();
    const result = await callApi("/api/regenerate-slide", "POST", {
      ...config,
      deck: state.deck,
      slide_id: state.deck.slides[state.selected].id,
      max_tokens: 1000,
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

el("sendChatBtn").onclick = async () => {
  const msg = el("chatInput").value.trim();
  if (!msg) return;
  el("chatInput").value = "";
  addLog("user", msg);
  try {
    const result = await callApi("/api/chat", "POST", { ...configOnly(), message: msg });
    addLog("llm", `${result.reply} (${result.mode})`);
  } catch (e) {
    addLog("app", `Chat error: ${e.message}`);
  }
};

el("saveSettingsBtn").onclick = async () => {
  try {
    await callApi("/api/settings", "POST", configOnly());
    setStatus("Settings saved.");
  } catch (e) {
    setStatus(`Error: ${e.message}`);
  }
};

document.querySelectorAll(".side-tab").forEach((btn) => {
  btn.onclick = () => setActiveTab(btn.dataset.tab);
});

loadSettings();
renderAll();
