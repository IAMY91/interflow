from __future__ import annotations

from typing import List

from .schemas import Hypothesis, Intervention


PROHIBITED_PHRASES = [
    "this team is green",
    "this person is stage",
    "low consciousness",
    "clearly at stage",
]


def check_stereotyping(text: str) -> List[str]:
    lowered = text.lower()
    return [p for p in PROHIBITED_PHRASES if p in lowered]


def enforce_hypothesis_policy(h: Hypothesis) -> dict:
    violations = []
    if not h.evidence_ids:
        violations.append("missing_evidence_links")
    if h.confidence > 0.8 and len(h.evidence_ids) < 3:
        violations.append("high_confidence_thin_data")
    if check_stereotyping(h.statement):
        violations.append("stereotype_or_stage_label_risk")
    if not h.alternatives:
        violations.append("missing_alternatives")
    return {
        "pass": len(violations) == 0,
        "violations": violations,
    }


def enforce_intervention_policy(i: Intervention) -> dict:
    violations = []
    if not i.success_indicators or not i.failure_indicators:
        violations.append("missing_outcome_signals")
    if "covert" in i.title.lower() or "manipulat" in i.intended_outcome.lower():
        violations.append("manipulation_risk")
    if "high" in i.risk_profile.lower() and not i.contraindications:
        violations.append("high_risk_missing_contraindications")
    return {
        "pass": len(violations) == 0,
        "violations": violations,
    }
