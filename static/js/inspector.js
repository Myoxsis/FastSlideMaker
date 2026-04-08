import { getSelectedSlide, state } from "./editor_state.js";

function byKey(slide, key) {
  if (!slide || !key) return null;
  const [kind, id] = key.split(":");
  if (kind === "title") return { kind, ref: slide };
  if (kind === "objective") return { kind, ref: slide };
  if (kind === "text") return { kind, ref: slide.text_blocks.find((block) => block.id === id) };
  if (kind === "shape") return { kind, ref: slide.visual_elements.find((shape) => shape.id === id) };
  return null;
}

export function updateInspectorFromSelection(inspectorEl) {
  const slide = getSelectedSlide();
  const selected = byKey(slide, state.selectedElementKey);

  if (!selected?.ref) {
    inspectorEl.innerHTML = '<p class="muted">Select an element to edit its properties.</p>';
    return;
  }

  const style = selected.ref.style || {};
  inspectorEl.innerHTML = `
    <h3>Inspector</h3>
    <p class="muted">${selected.kind} · ${selected.ref.id || selected.kind}</p>
    <label>Font size <input data-inspector-field="font_size" type="number" min="8" max="72" value="${style.font_size || 16}" /></label>
    <label>Font weight
      <select data-inspector-field="font_weight">
        <option value="regular" ${style.font_weight === "regular" ? "selected" : ""}>regular</option>
        <option value="bold" ${style.font_weight === "bold" ? "selected" : ""}>bold</option>
      </select>
    </label>
    <label>Italic <input data-inspector-field="italic" type="checkbox" ${style.italic ? "checked" : ""} /></label>
    <label>Text color <input data-inspector-field="text_color" type="color" value="${style.text_color || "#111827"}" /></label>
    <label>Fill color <input data-inspector-field="fill_color" type="color" value="${style.fill_color || "#ffffff"}" /></label>
    <label>Border color <input data-inspector-field="border_color" type="color" value="${style.border_color || "#94a3b8"}" /></label>
    <label>Border width <input data-inspector-field="border_width" type="number" min="0" max="16" step="0.5" value="${style.border_width ?? 1}" /></label>
    <label>Opacity <input data-inspector-field="opacity" type="number" min="0.1" max="1" step="0.1" value="${style.opacity ?? 1}" /></label>
    <label>Padding <input data-inspector-field="padding" type="number" min="0" max="40" value="${style.padding ?? 8}" /></label>
    <label>Align
      <select data-inspector-field="text_align">
        <option value="left" ${style.text_align === "left" ? "selected" : ""}>left</option>
        <option value="center" ${style.text_align === "center" ? "selected" : ""}>center</option>
        <option value="right" ${style.text_align === "right" ? "selected" : ""}>right</option>
      </select>
    </label>
    <label>Line spacing <input data-inspector-field="line_spacing" type="number" min="1" max="2" step="0.1" value="${style.line_spacing ?? 1.2}" /></label>
    <label>Bullet style
      <select data-inspector-field="bullet_style">
        <option value="disc" ${style.bullet_style === "disc" ? "selected" : ""}>disc</option>
        <option value="dash" ${style.bullet_style === "dash" ? "selected" : ""}>dash</option>
        <option value="number" ${style.bullet_style === "number" ? "selected" : ""}>number</option>
      </select>
    </label>
    <label>Uppercase <input data-inspector-field="text_case" type="checkbox" ${style.text_case === "uppercase" ? "checked" : ""} /></label>
    <label>User locked <input data-inspector-field="user_locked" type="checkbox" ${selected.ref.user_locked ? "checked" : ""} /></label>
  `;
}

export function attachInspectorHandlers(inspectorEl, onChange) {
  inspectorEl.addEventListener("input", (event) => {
    const field = event.target.dataset.inspectorField;
    if (!field) return;
    const slide = getSelectedSlide();
    const selected = byKey(slide, state.selectedElementKey);
    if (!selected?.ref) return;
    selected.ref.style ||= {};

    let value;
    if (event.target.type === "checkbox") value = event.target.checked;
    else if (event.target.type === "number") value = Number(event.target.value);
    else value = event.target.value;

    if (field === "text_case") value = value ? "uppercase" : "sentence";
    if (field === "user_locked") selected.ref.user_locked = value;
    else selected.ref.style[field] = value;

    selected.ref.user_modified = true;
    selected.ref.is_user_modified = true;
    slide.user_modified = true;
    onChange();
  });
}
