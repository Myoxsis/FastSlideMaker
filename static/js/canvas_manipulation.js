import { getSelectedSlide, state, updateSelection } from "./editor_state.js";

const GRID_SIZE = 20;
const MIN_SIZE = 24;
const OVERLAP_GAP = 8;

function getCanvas(container) {
  return container.querySelector(".canvas");
}

function getBounds(slide, canvas) {
  const marginX = slide.layout_hints?.safe_bounds_visible ? Math.max(0, Number(slide.layout_hints?.margin_x ?? 20)) : 0;
  const marginY = slide.layout_hints?.safe_bounds_visible ? Math.max(0, Number(slide.layout_hints?.margin_y ?? 20)) : 0;
  return {
    left: marginX,
    top: marginY,
    right: canvas.clientWidth - marginX,
    bottom: canvas.clientHeight - marginY,
  };
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function overlap(a, b) {
  return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
}

function quantize(value, enabled) {
  if (!enabled) return value;
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
}

function avoidOverlap(candidate, selectedId, shapes, bounds) {
  const ordered = [...shapes].filter((item) => item.id !== selectedId).sort((a, b) => a.id.localeCompare(b.id));
  const adjusted = { ...candidate };

  for (const other of ordered) {
    const otherBox = { x: other.x || 0, y: other.y || 0, w: other.w || 0, h: other.h || 0 };
    if (!overlap(adjusted, otherBox)) continue;
    const shiftRight = otherBox.x + otherBox.w + OVERLAP_GAP;
    if (shiftRight + adjusted.w <= bounds.right) {
      adjusted.x = shiftRight;
      continue;
    }
    const shiftDown = otherBox.y + otherBox.h + OVERLAP_GAP;
    if (shiftDown + adjusted.h <= bounds.bottom) adjusted.y = shiftDown;
  }

  adjusted.x = clamp(adjusted.x, bounds.left, bounds.right - adjusted.w);
  adjusted.y = clamp(adjusted.y, bounds.top, bounds.bottom - adjusted.h);
  return adjusted;
}

function findShapeByKey(slide, key) {
  const [kind, id] = (key || "").split(":");
  if (kind !== "shape") return null;
  return slide.visual_elements.find((shape) => shape.id === id) || null;
}

function ensureGuides(canvas) {
  let xGuide = canvas.querySelector('[data-guide="x"]');
  let yGuide = canvas.querySelector('[data-guide="y"]');
  if (!xGuide) {
    xGuide = document.createElement("div");
    xGuide.className = "canvas-guide x-guide";
    xGuide.dataset.guide = "x";
    canvas.appendChild(xGuide);
  }
  if (!yGuide) {
    yGuide = document.createElement("div");
    yGuide.className = "canvas-guide y-guide";
    yGuide.dataset.guide = "y";
    canvas.appendChild(yGuide);
  }
  return { xGuide, yGuide };
}

function toggleGuides(canvas, visible, x = 0, y = 0) {
  const { xGuide, yGuide } = ensureGuides(canvas);
  xGuide.style.display = visible ? "block" : "none";
  yGuide.style.display = visible ? "block" : "none";
  if (!visible) return;
  xGuide.style.left = `${x}px`;
  yGuide.style.top = `${y}px`;
}

export function attachCanvasManipulationHandlers(container, onSelectionChange, onCommitChange) {
  container.addEventListener("pointerdown", (event) => {
    const shapeEl = event.target.closest(".shape-element[data-element-key]");
    if (!shapeEl) return;

    const slide = getSelectedSlide();
    const canvas = getCanvas(container);
    if (!slide || !canvas) return;

    const key = shapeEl.dataset.elementKey;
    const shape = findShapeByKey(slide, key);
    if (!shape || shape.user_locked) return;

    if (state.selectedElementKey !== key) {
      updateSelection(key, false);
      onSelectionChange();
    }

    const resizeHandle = event.target.closest("[data-resize-handle]")?.dataset.resizeHandle || null;
    const bounds = getBounds(slide, canvas);
    const snap = slide.layout_hints?.snap_to_grid ?? state.snapToGrid;
    const showGuides = slide.layout_hints?.show_guides ?? state.showGuides;
    const start = { x: event.clientX, y: event.clientY, sx: shape.x || 0, sy: shape.y || 0, sw: shape.w || 120, sh: shape.h || 60 };

    shapeEl.setPointerCapture(event.pointerId);
    shapeEl.classList.add("is-dragging");

    const onMove = (moveEvent) => {
      const dx = moveEvent.clientX - start.x;
      const dy = moveEvent.clientY - start.y;
      const next = { x: start.sx, y: start.sy, w: start.sw, h: start.sh };

      if (!resizeHandle) {
        next.x = start.sx + dx;
        next.y = start.sy + dy;
      } else {
        if (resizeHandle.includes("e")) next.w = Math.max(MIN_SIZE, start.sw + dx);
        if (resizeHandle.includes("s")) next.h = Math.max(MIN_SIZE, start.sh + dy);
        if (resizeHandle.includes("w")) {
          const proposedX = start.sx + dx;
          const maxLeft = start.sx + start.sw - MIN_SIZE;
          next.x = Math.min(proposedX, maxLeft);
          next.w = start.sw + (start.sx - next.x);
        }
        if (resizeHandle.includes("n")) {
          const proposedY = start.sy + dy;
          const maxTop = start.sy + start.sh - MIN_SIZE;
          next.y = Math.min(proposedY, maxTop);
          next.h = start.sh + (start.sy - next.y);
        }
      }

      next.w = clamp(next.w, MIN_SIZE, bounds.right - bounds.left);
      next.h = clamp(next.h, MIN_SIZE, bounds.bottom - bounds.top);
      next.x = clamp(next.x, bounds.left, bounds.right - next.w);
      next.y = clamp(next.y, bounds.top, bounds.bottom - next.h);
      next.x = quantize(next.x, snap);
      next.y = quantize(next.y, snap);
      next.w = Math.max(MIN_SIZE, quantize(next.w, snap));
      next.h = Math.max(MIN_SIZE, quantize(next.h, snap));
      next.x = clamp(next.x, bounds.left, bounds.right - next.w);
      next.y = clamp(next.y, bounds.top, bounds.bottom - next.h);

      const collisionSafe = avoidOverlap(next, shape.id, slide.visual_elements, bounds);
      shapeEl.style.left = `${collisionSafe.x}px`;
      shapeEl.style.top = `${collisionSafe.y}px`;
      shapeEl.style.width = `${collisionSafe.w}px`;
      shapeEl.style.height = `${collisionSafe.h}px`;
      toggleGuides(canvas, Boolean(showGuides), collisionSafe.x, collisionSafe.y);
    };

    const onEnd = () => {
      shapeEl.classList.remove("is-dragging");
      toggleGuides(canvas, false);

      const committed = {
        x: parseFloat(shapeEl.style.left || "0"),
        y: parseFloat(shapeEl.style.top || "0"),
        w: parseFloat(shapeEl.style.width || "120"),
        h: parseFloat(shapeEl.style.height || "60"),
      };

      shape.x = committed.x;
      shape.y = committed.y;
      shape.w = committed.w;
      shape.h = committed.h;
      shape.user_modified = true;
      shape.is_user_modified = true;

      slide.layout_hints ||= {};
      slide.layout_hints.element_positions ||= {};
      slide.layout_hints.element_positions[shape.id] = { x: committed.x, y: committed.y, w: committed.w, h: committed.h };
      slide.layout_hints.snap_to_grid = Boolean(snap);
      slide.layout_hints.show_guides = Boolean(showGuides);
      slide.user_modified = true;
      onCommitChange();
      shapeEl.removeEventListener("pointermove", onMove);
      shapeEl.removeEventListener("pointerup", onEnd);
      shapeEl.removeEventListener("pointercancel", onEnd);
    };

    shapeEl.addEventListener("pointermove", onMove);
    shapeEl.addEventListener("pointerup", onEnd);
    shapeEl.addEventListener("pointercancel", onEnd);
  });
}
