const SHAPE_DEFAULTS = {
  rectangle: { fill_color: "#dbeafe", border_color: "#2563eb", border_width: 1, corner_radius: 0, opacity: 1 },
  rounded_rectangle: { fill_color: "#ede9fe", border_color: "#7c3aed", border_width: 1, corner_radius: 8, opacity: 1 },
  circle: { fill_color: "#dcfce7", border_color: "#059669", border_width: 1, corner_radius: 999, opacity: 1 },
  line: { fill_color: "transparent", border_color: "#111827", border_width: 2, corner_radius: 0, opacity: 1 },
  arrow: { fill_color: "transparent", border_color: "#1d4ed8", border_width: 2, corner_radius: 0, opacity: 1 },
  connector: { fill_color: "transparent", border_color: "#475569", border_width: 2, corner_radius: 0, opacity: 1 },
  callout: { fill_color: "#fff7ed", border_color: "#ea580c", border_width: 1, corner_radius: 8, opacity: 1 },
  divider: { fill_color: "transparent", border_color: "#cbd5e1", border_width: 1, corner_radius: 0, opacity: 1 },
  legend: { fill_color: "#f8fafc", border_color: "#94a3b8", border_width: 1, corner_radius: 6, opacity: 1 },
  section_header: { fill_color: "#e2e8f0", border_color: "#64748b", border_width: 1, corner_radius: 4, opacity: 1 },
  icon: { fill_color: "#eef2ff", border_color: "#4f46e5", border_width: 1, corner_radius: 6, opacity: 1 },
};

export function createShape(type, index) {
  return {
    id: `shape-${Date.now()}-${index}`,
    type,
    label: type.replaceAll("_", " "),
    x: 40 + (index % 6) * 20,
    y: 40 + (index % 6) * 20,
    w: type === "line" || type === "divider" ? 220 : 140,
    h: type === "line" || type === "divider" ? 8 : 70,
    z_index: index + 1,
    element_role: "shape",
    is_user_modified: true,
    user_locked: false,
    user_modified: true,
    style: SHAPE_DEFAULTS[type] || SHAPE_DEFAULTS.rectangle,
  };
}
