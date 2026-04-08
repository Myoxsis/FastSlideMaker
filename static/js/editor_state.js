export const DEFAULT_THEME = {
  font_family: "Inter",
  palette: ["#1f3a8a", "#2563eb", "#0f766e", "#7c3aed", "#111827", "#dc2626"],
  title_preset: "executive",
  diagram_preset: "enterprise",
};

export const state = {
  deck: null,
  selectedSlideId: null,
  selectedProjectId: null,
  selectedElementKey: null,
  selectedElementKeys: [],
  projects: [],
  snapToGrid: true,
  gridVisible: true,
  safeBoundsVisible: true,
  showGuides: true,
};

export function getSelectedSlide() {
  if (!state.deck || !state.selectedSlideId) return null;
  return state.deck.slides.find((slide) => slide.id === state.selectedSlideId) || null;
}

export function getSlideById(slideId) {
  if (!state.deck) return null;
  return state.deck.slides.find((slide) => slide.id === slideId) || null;
}

export function ensureDeckDefaults(deck) {
  if (!deck.theme) deck.theme = structuredClone(DEFAULT_THEME);
  if (!deck.theme.palette?.length) deck.theme.palette = [...DEFAULT_THEME.palette];
  deck.slides.forEach((slide) => {
    slide.layout_hints = {
      margin_x: 36,
      margin_y: 24,
      spacing_density: "standard",
      template_variant: "default",
      grid_visible: true,
      safe_bounds_visible: true,
      snap_to_grid: true,
      show_guides: true,
      ...(slide.layout_hints || {}),
    };
    slide.user_locked ??= false;
    slide.user_modified ??= false;
    slide.visual_elements ??= [];
    slide.text_blocks = (slide.text_blocks || []).map((block) => ({
      style: {
        font_size: 16,
        font_weight: "regular",
        italic: false,
        text_color: "#111827",
        text_align: "left",
        vertical_align: "top",
        line_spacing: 1.2,
        bullet_style: "disc",
        padding: 8,
        text_case: "sentence",
        font_family: deck.theme.font_family || "Inter",
        ...(block.style || {}),
      },
      user_locked: false,
      user_modified: false,
      ...block,
    }));
  });
  return deck;
}

export function updateSelection(elementKey, multi = false) {
  if (multi) {
    const existing = state.selectedElementKeys.includes(elementKey);
    state.selectedElementKeys = existing
      ? state.selectedElementKeys.filter((key) => key !== elementKey)
      : [...state.selectedElementKeys, elementKey];
  } else {
    state.selectedElementKeys = elementKey ? [elementKey] : [];
  }
  state.selectedElementKey = state.selectedElementKeys[0] || null;
}
