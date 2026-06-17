"""The methodology's phase map, encoded as data.

Source of truth: skills/using-methodology/SKILL.md phase table. Phase progress is
derived purely from file existence; this module holds no logic, only the schema.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    skill: str
    output: str            # relative path whose existence means the phase is done
    predecessor: str | None  # relative path that must exist for the phase to be available


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    output: str            # relative path whose existence means the gate has run


PHASES: list[Phase] = [
    Phase("1", "Scope", "ai-process-assessment:scoping-engagement", "scope.md", None),
    Phase("2", "Context", "ai-process-assessment:mapping-context", "context.md", "scope.md"),
    Phase("3", "Tech & Data", "ai-process-assessment:inventorying-tech-data", "tech-inventory.md", "context.md"),
    Phase("4", "Discovery", "ai-process-assessment:discovering-processes", "processes/_index.md", "tech-inventory.md"),
    Phase("5", "Opportunities", "ai-process-assessment:identifying-opportunities", "opportunities/_index.md", "processes/_index.md"),
    Phase("6", "Scoring", "ai-process-assessment:scoring-opportunities", "scores/_index.md", "opportunities/_index.md"),
    Phase("7", "Roadmap", "ai-process-assessment:prioritizing-roadmap", "roadmap.md", "scores/_index.md"),
    Phase("8", "Use-Case Briefs", "ai-process-assessment:packaging-usecases", "usecase-briefs/_index.md", "roadmap.md"),
    Phase("8.5", "Cost Actuals", "ai-process-assessment:collecting-cost-actuals", "cost-actuals.md", "usecase-briefs/_index.md"),
    Phase("9", "Business Case", "ai-process-assessment:building-business-case", "business-case.md", "cost-actuals.md"),
    Phase("10", "Executive Summary", "ai-process-assessment:building-executive-summary", "executive-summary.md", "business-case.md"),
    Phase("11", "Deliverable", "ai-process-assessment:building-deliverable", "deliverable.html", "executive-summary.md"),
]

GATES: list[Gate] = [
    Gate("grc", "Governance & Risk (Gate A)", "grc/_index.md"),
    Gate("deliverable", "Deliverable Gate (Gate B)", "evidence-log.md"),
]

# Maps a model/*.json input stem to the human key surfaced in the snapshot.
MODEL_INPUTS: dict[str, str] = {
    "baselines": "baselines",
    "value": "value",
    "scores": "scores",
    "initiatives": "initiatives",
    "costs": "costs",
}
