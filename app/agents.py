from __future__ import annotations

from collections import Counter
from uuid import uuid4

from .schemas import AnalysisOutput, Evidence, Hypothesis, Intervention


AQAL_QUADRANTS = {"I", "We", "It", "Its"}


def aqal_mapping(evidence: list[Evidence]) -> dict:
    counts = Counter([e.aqal_quadrant_hint for e in evidence if e.aqal_quadrant_hint in AQAL_QUADRANTS])
    missing = [q for q in AQAL_QUADRANTS if q not in counts]
    balancing_questions = [f"What additional evidence do we need in quadrant {q}?" for q in missing]
    return {
        "coverage": dict(counts),
        "missing_quadrants": missing,
        "balancing_questions": balancing_questions,
    }


def value_logic_hypothesis(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    statement = (
        "Current evidence may suggest tension between order/predictability and autonomy/performance in this context."
    )
    return Hypothesis(
        id=f"hyp_{uuid4().hex[:8]}",
        case_id=case_id,
        statement=statement,
        model_sources=["Spiral Dynamics", "AQAL"],
        evidence_ids=[e.id for e in evidence[:5]],
        confidence=0.58,
        alternatives=[
            "This may reflect temporary role ambiguity.",
            "A competing interpretation is that process debt is driving conflict.",
        ],
        missing_information=["decision-rights policy", "cross-team dependency map"],
        misuse_risks=["essentialization_risk_if_presented_as_identity"],
    )


def systems_hypothesis(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    return Hypothesis(
        id=f"hyp_{uuid4().hex[:8]}",
        case_id=case_id,
        statement="Evidence suggests a possible structural bottleneck in decision flow and escalation pathways.",
        model_sources=["VSM", "Cynefin"],
        evidence_ids=[e.id for e in evidence[:5]],
        confidence=0.61,
        alternatives=["This may be a facilitation-quality issue rather than structure."],
        missing_information=["formal governance map"],
        misuse_risks=["overfitting_from_limited_metrics"],
    )


def intervention_candidates(case_id: str) -> list[Intervention]:
    return [
        Intervention(
            id=f"int_{uuid4().hex[:8]}",
            case_id=case_id,
            title="Decision-rights clarity workshop",
            target_levels=["team", "workflow", "governance"],
            intended_outcome="Increase accountability clarity without overcontrol.",
            supporting_models=["VSM", "ADKAR", "AQAL"],
            prerequisites=["cross-functional sponsor", "facilitator"],
            contraindications=["acute trust crisis without mediation"],
            risk_profile="medium",
            success_indicators=["fewer reopened decisions", "faster cycle time"],
            failure_indicators=["shadow governance", "meeting load increase"],
            regenerative_impact_notes="Builds distributed capability and lowers coordination fragility.",
        ),
        Intervention(
            id=f"int_{uuid4().hex[:8]}",
            case_id=case_id,
            title="Safe-to-fail communication framing experiment",
            target_levels=["relationship", "team"],
            intended_outcome="Adapt message framing to reduce resistance while preserving agency.",
            supporting_models=["Spiral Dynamics", "Antifragility", "Flow"],
            prerequisites=["stakeholder mapping"],
            contraindications=["coercive mandate environment"],
            risk_profile="low",
            success_indicators=["improved participation", "reduced defensive responses"],
            failure_indicators=["message confusion", "trust drop"],
            regenerative_impact_notes="Improves trust and learning without rigid scripts.",
        ),
    ]


def synthesis_output(case_title: str, evidence: list[Evidence], hypotheses: list[Hypothesis], interventions: list[Intervention]) -> AnalysisOutput:
    return AnalysisOutput(
        situation_summary=f"Case '{case_title}' indicates multi-level coordination and meaning-making tension.",
        evidence_observed=[e.raw_excerpt for e in evidence[:5]],
        interpretations_by_lens=[h.statement for h in hypotheses],
        convergence=["Both value-logic and systems lenses indicate coordination strain."],
        disagreements=["Relative contribution of structural vs interpersonal factors remains uncertain."],
        missing_information=["full dependency network", "baseline trust measure"],
        confidence_and_uncertainty={
            "overall_confidence": "moderate",
            "uncertainty": "evidence diversity is limited",
        },
        recommended_interventions=[i.title for i in interventions],
        risks_and_ethical_cautions=["Avoid framing stakeholders as fixed stages or colors."],
        regenerative_assessment={
            "trust": "expected positive",
            "resilience": "moderate positive",
            "agency": "positive if voluntary participation maintained",
        },
        questions_for_human_validation=[
            "Do these hypotheses match lived reality across teams?",
            "Which intervention has acceptable risk under current constraints?",
        ],
    )
