const promptEl = document.getElementById('prompt');
const modelEl = document.getElementById('model');
const generateBtn = document.getElementById('generateBtn');
const exportBtn = document.getElementById('exportBtn');
const statusEl = document.getElementById('status');
const slidesEl = document.getElementById('slides');
const jsonOutputEl = document.getElementById('jsonOutput');

let currentProjectId = null;

function renderSlide(slide) {
  const wrapper = document.createElement('article');
  wrapper.className = 'slide';

  wrapper.innerHTML = `<h3>${slide.title}</h3><p>${slide.subtitle || ''}</p>`;

  if (slide.slide_type === 'process_flow') {
    const container = document.createElement('div');
    container.className = 'process-flow';
    (slide.flow_steps || []).forEach((step) => {
      const div = document.createElement('div');
      div.className = 'step';
      div.innerHTML = `<strong>${step.title}</strong><br>${step.detail || ''}`;
      container.appendChild(div);
    });
    wrapper.appendChild(container);
  } else if (slide.slide_type === 'layered_architecture') {
    (slide.layers || []).forEach((layer) => {
      const div = document.createElement('div');
      div.className = 'layer';
      div.innerHTML = `<strong>${layer.name}</strong>: ${layer.components.join(', ')}`;
      wrapper.appendChild(div);
    });
  } else if (slide.slide_type === 'roadmap') {
    const roadmap = document.createElement('div');
    roadmap.className = 'roadmap';
    (slide.roadmap_phases || []).forEach((phase) => {
      const div = document.createElement('div');
      div.className = 'phase';
      div.innerHTML = `<strong>${phase.name}</strong> (${phase.timeframe})<ul>${(phase.outcomes || []).map((o) => `<li>${o}</li>`).join('')}</ul>`;
      roadmap.appendChild(div);
    });
    wrapper.appendChild(roadmap);
  } else {
    const ul = document.createElement('ul');
    (slide.narrative || []).forEach((line) => {
      const li = document.createElement('li');
      li.textContent = line;
      ul.appendChild(li);
    });
    wrapper.appendChild(ul);
  }

  return wrapper;
}

async function generateDeck() {
  statusEl.textContent = 'Generating deck...';
  slidesEl.innerHTML = '';
  exportBtn.disabled = true;

  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: promptEl.value, model: modelEl.value })
  });

  if (!response.ok) {
    statusEl.textContent = `Error: ${response.status}`;
    return;
  }

  const payload = await response.json();
  currentProjectId = payload.project_id;
  jsonOutputEl.textContent = JSON.stringify(payload.deck, null, 2);
  payload.deck.slides.forEach((slide) => slidesEl.appendChild(renderSlide(slide)));
  statusEl.textContent = `Generated project: ${currentProjectId}`;
  exportBtn.disabled = false;
}

function exportPptx() {
  if (!currentProjectId) return;
  window.open(`/api/projects/${currentProjectId}/export`, '_blank');
}

generateBtn.addEventListener('click', generateDeck);
exportBtn.addEventListener('click', exportPptx);
