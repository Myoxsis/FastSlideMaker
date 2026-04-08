import { getSelectedSlide, state } from "./editor_state.js";
import { createShape } from "./shape_factory.js";

const STEP = 8;

export function attachToolbarHandlers(toolbarEl, onChange) {
  toolbarEl.addEventListener("click", (event) => {
    const action = event.target.dataset.action;
    if (!action) return;

    const slide = getSelectedSlide();
    if (!slide) return;

    if (action.startsWith("insert-shape:")) {
      const type = action.split(":")[1];
      slide.visual_elements.push(createShape(type, slide.visual_elements.length + 1));
      slide.user_modified = true;
      onChange();
      return;
    }

    if (!state.selectedElementKey) return;
    const selected = resolveSelected(slide);
    if (!selected) return;

    switch (action) {
      case "delete-element":
        deleteSelected(slide, selected);
        break;
      case "duplicate-element":
        duplicateSelected(slide, selected);
        break;
      case "nudge-up":
        nudge(selected.ref, 0, -STEP);
        break;
      case "nudge-down":
        nudge(selected.ref, 0, STEP);
        break;
      case "nudge-left":
        nudge(selected.ref, -STEP, 0);
        break;
      case "nudge-right":
        nudge(selected.ref, STEP, 0);
        break;
      case "bring-forward":
        selected.ref.z_index = (selected.ref.z_index || 1) + 1;
        break;
      case "send-backward":
        selected.ref.z_index = Math.max(1, (selected.ref.z_index || 1) - 1);
        break;
      default:
        break;
    }

    slide.user_modified = true;
    onChange();
  });
}

function resolveSelected(slide) {
  const [kind, id] = (state.selectedElementKey || "").split(":");
  if (kind === "shape") return { kind, ref: slide.visual_elements.find((item) => item.id === id) };
  if (kind === "text") return { kind, ref: slide.text_blocks.find((item) => item.id === id) };
  return null;
}

function nudge(ref, dx, dy) {
  ref.x = (ref.x || 0) + dx;
  ref.y = (ref.y || 0) + dy;
}

function deleteSelected(slide, selected) {
  if (selected.kind === "shape") slide.visual_elements = slide.visual_elements.filter((item) => item.id !== selected.ref.id);
  if (selected.kind === "text") slide.text_blocks = slide.text_blocks.filter((item) => item.id !== selected.ref.id);
}

function duplicateSelected(slide, selected) {
  const clone = structuredClone(selected.ref);
  clone.id = `${clone.id}-copy-${Date.now()}`;
  clone.x = (clone.x || 0) + 12;
  clone.y = (clone.y || 0) + 12;
  clone.user_modified = true;
  clone.is_user_modified = true;
  if (selected.kind === "shape") slide.visual_elements.push(clone);
  if (selected.kind === "text") slide.text_blocks.push(clone);
}
