"""Deterministic mock-mode prompts and deck payloads."""

from __future__ import annotations

from copy import deepcopy

from app.models.schemas import Deck, DeckRequest, Slide


CANNED_SAMPLE_PROMPTS: list[dict[str, str]] = [
    {
        "id": "order-to-cash-architecture",
        "label": "Order-to-cash process + architecture",
        "prompt": (
            "Create a transformation deck for the order-to-cash process including end-to-end process "
            "diagnostics and target architecture options."
        ),
    },
    {
        "id": "customer-onboarding-target-design",
        "label": "Customer onboarding target design",
        "prompt": (
            "Design an executive-ready deck for customer onboarding target operating model, "
            "service blueprint, and KPI governance."
        ),
    },
    {
        "id": "claims-transformation-roadmap",
        "label": "Claims transformation roadmap",
        "prompt": (
            "Build a claims transformation roadmap deck with value case, capability maturity, "
            "and phased implementation plan."
        ),
    },
]


DECK_TEMPLATES: dict[str, dict[str, object]] = {
    "order-to-cash-architecture": {
        "title": "Order-to-Cash Transformation Blueprint",
        "theme": "enterprise-blue",
        "slides": [
            {
                "title": "Transformation Objective",
                "bullets": [
                    "Reduce cash conversion cycle by 18 days over 12 months",
                    "Increase straight-through processing to 72%",
                    "Standardize policy controls across regions",
                ],
                "notes": "Sets scope and quantified ambition.",
            },
            {
                "title": "Current Process Friction",
                "bullets": [
                    "Quote-to-order handoff has duplicate validations",
                    "Credit checks run late and trigger rework",
                    "Collections escalation lacks priority logic",
                ],
                "notes": "Summarizes where delay and leakage occur.",
            },
            {
                "title": "Future-State O2C Process",
                "bullets": [
                    "Digital intake with rules-driven completeness checks",
                    "Automated credit and pricing decisioning before fulfillment",
                    "Exception queues routed by risk and value",
                ],
                "notes": "Process design anchor for operating model changes.",
            },
            {
                "title": "Target Architecture",
                "bullets": [
                    "Experience layer: customer portal + sales cockpit",
                    "Orchestration layer: workflow and policy engine",
                    "Core systems: ERP, billing, and collections microservices",
                ],
                "notes": "Layered architecture that supports process determinism.",
            },
            {
                "title": "Integration Design",
                "bullets": [
                    "Event bus connects order, invoicing, and collections events",
                    "Master data service publishes canonical customer profile",
                    "Finance lakehouse receives daily reconciliation feed",
                ],
                "notes": "Shows system boundaries and data contracts.",
            },
            {
                "title": "Execution Roadmap",
                "bullets": [
                    "Wave 1: controls baseline and data remediation",
                    "Wave 2: workflow automation and exception management",
                    "Wave 3: AI-assisted collections optimization",
                ],
                "notes": "Prioritized sequence with value realization checkpoints.",
            },
        ],
    },
    "customer-onboarding-target-design": {
        "title": "Customer Onboarding Target Design",
        "theme": "modern-teal",
        "slides": [
            {
                "title": "Strategic Intent",
                "bullets": [
                    "Cut onboarding cycle time from 14 to 5 days",
                    "Deliver consistent first-90-day customer experience",
                    "Enable tiered journeys by segment and risk profile",
                ],
                "notes": "Defines the target outcomes and guardrails.",
            },
            {
                "title": "Journey Blueprint",
                "bullets": [
                    "Pre-signature readiness checklist with digital capture",
                    "Day 0 activation playbook and role-based ownership",
                    "Day 30 value review with adoption score",
                ],
                "notes": "Core journey states and handoffs.",
            },
            {
                "title": "Operating Model",
                "bullets": [
                    "Central command center for orchestration and SLA governance",
                    "Shared services pod for verification and provisioning",
                    "Account team remains single-threaded owner",
                ],
                "notes": "Defines teams, RACI, and service model.",
            },
            {
                "title": "Capability Architecture",
                "bullets": [
                    "CRM triggers onboarding workflow templates",
                    "Identity, compliance, and billing integrated via APIs",
                    "Telemetry layer captures milestone completion and risk signals",
                ],
                "notes": "Target design for systems and control points.",
            },
            {
                "title": "KPI Governance",
                "bullets": [
                    "Primary KPIs: time-to-value, activation, and CSAT",
                    "Weekly health review with red-amber-green rules",
                    "Quarterly calibration of playbooks by segment",
                ],
                "notes": "Governance rhythm and metric ownership.",
            },
            {
                "title": "Implementation Plan",
                "bullets": [
                    "Phase 1: baseline process and metric instrumentation",
                    "Phase 2: automation + standardized assets",
                    "Phase 3: predictive risk management and optimization",
                ],
                "notes": "Phased target design deployment.",
            },
        ],
    },
    "claims-transformation-roadmap": {
        "title": "Claims Transformation Roadmap",
        "theme": "charcoal-gold",
        "slides": [
            {
                "title": "Why Transform Now",
                "bullets": [
                    "Claims leakage estimated at 6.5% of paid losses",
                    "Average resolution time exceeds peer benchmark by 11 days",
                    "Regulatory scrutiny increasing on fairness and transparency",
                ],
                "notes": "Business case and urgency framing.",
            },
            {
                "title": "Current-State Assessment",
                "bullets": [
                    "Fragmented intake channels create duplicate records",
                    "Manual triage drives inconsistent assignment",
                    "Limited fraud analytics in early decision points",
                ],
                "notes": "Top pain points and root causes.",
            },
            {
                "title": "Target Claims Capability Map",
                "bullets": [
                    "Unified FNOL intake with guided evidence capture",
                    "Rules + ML triage for complexity and fraud propensity",
                    "Digital adjuster workspace with automation copilot",
                ],
                "notes": "North-star capability design.",
            },
            {
                "title": "Technology Enablers",
                "bullets": [
                    "API-first claims core and document intelligence",
                    "Real-time partner integrations for repair and medical networks",
                    "Model governance framework with explainability controls",
                ],
                "notes": "Platform enablers for scaled execution.",
            },
            {
                "title": "Roadmap by Wave",
                "bullets": [
                    "Wave 1 (Q3-Q4): data quality + intake modernization",
                    "Wave 2 (Q1-Q2): triage automation + workforce enablement",
                    "Wave 3 (Q3-Q4): advanced analytics and continuous tuning",
                ],
                "notes": "24-month phased roadmap.",
            },
            {
                "title": "Benefits & Risks",
                "bullets": [
                    "Expected 9-12% indemnity savings with better triage",
                    "Cycle time reduction target: 30% for standard claims",
                    "Key risk: change fatigue mitigated via branch-based pilots",
                ],
                "notes": "Value realization and risk controls.",
            },
        ],
    },
}


def validate_mock_assets() -> None:
    """Ensure sample prompts and canned outputs stay in sync."""
    prompt_ids = {item.get("id") for item in CANNED_SAMPLE_PROMPTS}
    template_ids = set(DECK_TEMPLATES.keys())

    missing_templates = prompt_ids - template_ids
    missing_prompts = template_ids - prompt_ids
    if missing_templates or missing_prompts:
        raise ValueError(
            "Mock prompts/templates are inconsistent. "
            f"Missing templates for: {sorted(missing_templates)}; "
            f"Missing prompts for: {sorted(missing_prompts)}."
        )


def select_mock_scenario(topic: str) -> str:
    normalized = topic.lower()
    if "order" in normalized and "cash" in normalized:
        return "order-to-cash-architecture"
    if "onboarding" in normalized:
        return "customer-onboarding-target-design"
    if "claim" in normalized:
        return "claims-transformation-roadmap"
    return "order-to-cash-architecture"


def build_mock_deck(payload: DeckRequest, *, ollama_available: bool) -> Deck:
    scenario_id = select_mock_scenario(payload.topic)
    template = deepcopy(DECK_TEMPLATES[scenario_id])
    template_slides: list[dict[str, object]] = template["slides"]  # type: ignore[assignment]
    selected = template_slides[: payload.slide_count]

    while len(selected) < payload.slide_count:
        base_slide = deepcopy(template_slides[len(selected) % len(template_slides)])
        base_slide["title"] = f"{base_slide['title']} (Extended)"
        selected.append(base_slide)

    slides = [Slide.model_validate(item) for item in selected]
    return Deck(
        title=str(template["title"]),
        theme=str(template["theme"]),
        slides=slides,
        metadata={
            "mode": "mock",
            "mock_scenario": scenario_id,
            "ollama_available": ollama_available,
        },
    )
