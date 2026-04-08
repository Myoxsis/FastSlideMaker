import { state, updateSelection } from "./editor_state.js";

export function attachSelectionHandlers(container, onChange) {
  container.addEventListener("click", (event) => {
    const target = event.target.closest("[data-element-key]");
    if (!target) return;
    const multi = event.shiftKey;
    updateSelection(target.dataset.elementKey, multi);
    onChange();
  });
}

export function applySelectionClass(container) {
  container.querySelectorAll("[data-element-key]").forEach((element) => {
    const key = element.dataset.elementKey;
    const selected = state.selectedElementKeys.includes(key);
    element.classList.toggle("is-selected", selected);
    if (element.classList.contains("shape-element")) syncResizeHandles(element, selected);
  });
}

function syncResizeHandles(element, selected) {
  element.querySelectorAll(".resize-handle").forEach((handle) => handle.remove());
  if (!selected) return;
  ["nw", "ne", "sw", "se"].forEach((direction) => {
    const handle = document.createElement("button");
    handle.type = "button";
    handle.className = `resize-handle handle-${direction}`;
    handle.dataset.resizeHandle = direction;
    handle.setAttribute("aria-label", `Resize ${direction}`);
    element.appendChild(handle);
  });
}
