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
    element.classList.toggle("is-selected", state.selectedElementKeys.includes(key));
  });
}
