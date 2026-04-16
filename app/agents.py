"""Interflow agent implementations.

Each agent function corresponds to one agent in the council spec (README §4.2).
Every function has a deterministic fallback used when:
  - ANTHROPIC_API_KEY is not set
  - The LLM call fails for any reason (network, quota, parsing)

Fallbacks produce intentionally low-confidence outputs (<=0.40) so governance
rules will flag them for human review rather than pass silently.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from uuid import uuid4

from .llm import AGENT_PROMPT_TEMPLATE, call_agent, extract_json
from .schemas import (
    ADKARAssessment,
    AnalysisOutput,
    Evidence,
    EvidenceRef,
    Hypothesis,
    HypothesisRef,
    Intervention,
    InterventionRef,
    ProcessPlan,
    TheoryUAssessment,
)

logger = logging.getLogger(__name__)

AQAL_QUADRANTS = {"I", "We", "It", "Its"}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _fmt_evidence(evidence: list[Evidence], limit: int = 12) -> str:
    """Format evidence objects for inclusion in an agent prompt."""
    lines = []
    for e in evidence[:limit]:
        lines.append(
            f"[{e.id}] quadrant={e.aqal_quadrant_hint or '?'} "
            f"category={e.evidence_category} reliability={e.reliability_estimate:.2f}: "
            f"{e.raw_excerpt}"
        )
    return "\n".join(lines)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# AQAL Mapping Agent — deterministic (counting is genuinely correct here)
# ---------------------------------------------------------------------------

def aqal_mapping(evidence: list[Evidence]) -> dict:
    """Map evidence to AQAL quadrants and detect coverage gaps.

    This agent is intentionally deterministic — we are counting observable
    quadrant hints, not making inferential leaps.
    """
    counts = Counter(
        e.aqal_quadrant_hint for e in evidence if e.aqal_quadrant_hint in AQAL_QUADRANTS
    )
    missing = [q for q in AQAL_QUADRANTS if q not in counts]
    balancing_questions = [
        f"What additional evidence do we need in quadrant {q}?" for q in missing
    ]
    return {
        "coverage": dict(counts),
        "missing_quadrants": missing,
        "balancing_questions": balancing_questions,
    }


# ---------------------------------------------------------------------------
# Value-Logic Agent (Spiral Dynamics + AQAL)
# ---------------------------------------------------------------------------

def value_logic_hypothesis(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    """Generate a value-logic hypothesis from evidence using Spiral Dynamics as lens."""
    evidence_text = _fmt_evidence(evidence)
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Value-Logic Agent",
        mission=(
            "Generate a context-dependent hypothesis about motivational tensions visible "
            "in the evidence. Apply Spiral Dynamics as an interpretive lens only — "
            "never as a fixed label system. Focus on value-logic tensions that may explain "
            "the observed patterns. Do not essentialize any individual or team."
        ),
        inputs=f"Evidence objects:\n{evidence_text}",
        output_schema=json.dumps(
            {
                "statement": "1-3 sentence hypothesis about value-logic tension",
                "confidence": "float 0.0-1.0 (cap at 0.75 unless evidence is very diverse)",
                "alternatives": ["2+ alternative explanations for the same patterns"],
                "missing_information": ["Data that would improve or refute this hypothesis"],
                "misuse_risks": ["Ways this hypothesis could be misapplied"],
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt)
        data = extract_json(text)
        return Hypothesis(
            id=f"hyp_{uuid4().hex[:8]}",
            case_id=case_id,
            statement=data["statement"],
            model_sources=["Spiral Dynamics", "AQAL"],
            evidence_ids=[e.id for e in evidence[:5]],
            confidence=_clamp(float(data.get("confidence", 0.55))),
            alternatives=data.get("alternatives", []),
            missing_information=data.get("missing_information", []),
            misuse_risks=data.get("misuse_risks", []),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("value_logic_hypothesis LLM call failed (%s) — using fallback", exc)
        return _fallback_value_logic(case_id, evidence)


def _fallback_value_logic(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    return Hypothesis(
        id=f"hyp_{uuid4().hex[:8]}",
        case_id=case_id,
        statement=(
            "Evidence may suggest tension between order/predictability and "
            "autonomy/performance. (LLM unavailable — confidence capped at 0.40)"
        ),
        model_sources=["Spiral Dynamics", "AQAL"],
        evidence_ids=[e.id for e in evidence[:5]],
        confidence=0.40,
        alternatives=[
            "This may reflect temporary role ambiguity.",
            "Process debt may be driving apparent value conflicts.",
        ],
        missing_information=["decision-rights policy", "cross-team dependency map"],
        misuse_risks=["essentialization_risk_if_presented_as_identity"],
    )


# ---------------------------------------------------------------------------
# Systems Mapping Agent (VSM + Cynefin)
# ---------------------------------------------------------------------------

def systems_hypothesis(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    """Generate a structural bottleneck hypothesis using VSM and Cynefin as lenses."""
    evidence_text = _fmt_evidence(evidence)
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Systems Mapping Agent",
        mission=(
            "Map structural bottlenecks, coordination failures, and leverage points. "
            "Apply VSM (Viable System Model) and Cynefin as diagnostic lenses. "
            "Focus on structural patterns — not individual fault. "
            "Explicitly flag if the evidence is insufficient for confident structural claims."
        ),
        inputs=f"Evidence objects:\n{evidence_text}",
        output_schema=json.dumps(
            {
                "statement": "1-3 sentence structural hypothesis",
                "confidence": "float 0.0-1.0",
                "alternatives": ["Alternative structural explanations"],
                "missing_information": ["Missing structural data (org chart, process maps, etc.)"],
                "misuse_risks": ["Ways this structural claim could be misused"],
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt)
        data = extract_json(text)
        return Hypothesis(
            id=f"hyp_{uuid4().hex[:8]}",
            case_id=case_id,
            statement=data["statement"],
            model_sources=["VSM", "Cynefin"],
            evidence_ids=[e.id for e in evidence[:5]],
            confidence=_clamp(float(data.get("confidence", 0.60))),
            alternatives=data.get("alternatives", []),
            missing_information=data.get("missing_information", []),
            misuse_risks=data.get("misuse_risks", []),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("systems_hypothesis LLM call failed (%s) — using fallback", exc)
        return _fallback_systems(case_id, evidence)


def _fallback_systems(case_id: str, evidence: list[Evidence]) -> Hypothesis:
    return Hypothesis(
        id=f"hyp_{uuid4().hex[:8]}",
        case_id=case_id,
        statement=(
            "Evidence suggests a possible structural bottleneck in decision flow "
            "and escalation pathways. (LLM unavailable — confidence capped at 0.40)"
        ),
        model_sources=["VSM", "Cynefin"],
        evidence_ids=[e.id for e in evidence[:5]],
        confidence=0.40,
        alternatives=["This may be a facilitation-quality issue rather than structure."],
        missing_information=["formal governance map", "decision-authority documentation"],
        misuse_risks=["overfitting_from_limited_metrics"],
    )


# ---------------------------------------------------------------------------
# Intervention Design Agent
# ---------------------------------------------------------------------------

def intervention_candidates(
    case_id: str,
    hypotheses: list[Hypothesis] | None = None,
) -> list[Intervention]:
    """Generate ranked intervention options grounded in the active hypotheses."""
    hyp_text = ""
    if hypotheses:
        hyp_text = "\n".join(
            f"- [{h.id}] (confidence={h.confidence:.2f}, lenses={h.model_sources}): {h.statement}"
            for h in hypotheses
        )

    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Intervention Design Agent",
        mission=(
            "Generate 2-3 concrete intervention options grounded in the hypotheses. "
            "Each intervention must: specify target levels, prerequisites, contraindications, "
            "success indicators, failure indicators, and a regenerative impact assessment. "
            "Assign impact (0-1), feasibility (0-1), evidence_strength (0-1), and "
            "regenerative_fit (0-1) for each option."
        ),
        inputs=(
            f"Active hypotheses:\n{hyp_text}"
            if hyp_text
            else "No hypotheses available — design general diagnostic interventions."
        ),
        output_schema=json.dumps(
            {
                "interventions": [
                    {
                        "title": "Intervention name",
                        "target_levels": ["team", "workflow", "governance"],
                        "intended_outcome": "What this intervention achieves",
                        "supporting_models": ["VSM", "ADKAR"],
                        "prerequisites": ["Required conditions for success"],
                        "contraindications": ["When NOT to use this intervention"],
                        "risk_profile": "low|medium|high",
                        "success_indicators": ["Observable signs it is working"],
                        "failure_indicators": ["Observable signs it is not working"],
                        "regenerative_impact_notes": "Long-term trust/resilience/agency assessment",
                        "impact": 0.7,
                        "feasibility": 0.8,
                        "evidence_strength": 0.6,
                        "regenerative_fit": 0.75,
                    }
                ]
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt, max_tokens=3000)
        data = extract_json(text)
        interventions = []
        for item in data.get("interventions", []):
            interventions.append(
                Intervention(
                    id=f"int_{uuid4().hex[:8]}",
                    case_id=case_id,
                    title=item["title"],
                    target_levels=item.get("target_levels", ["team"]),
                    intended_outcome=item.get("intended_outcome", ""),
                    supporting_models=item.get("supporting_models", []),
                    prerequisites=item.get("prerequisites", []),
                    contraindications=item.get("contraindications", []),
                    risk_profile=item.get("risk_profile", "medium"),
                    success_indicators=item.get("success_indicators", []),
                    failure_indicators=item.get("failure_indicators", []),
                    regenerative_impact_notes=item.get("regenerative_impact_notes", ""),
                    impact=_clamp(float(item.get("impact", 0.5))),
                    feasibility=_clamp(float(item.get("feasibility", 0.5))),
                    evidence_strength=_clamp(float(item.get("evidence_strength", 0.5))),
                    regenerative_fit=_clamp(float(item.get("regenerative_fit", 0.5))),
                )
            )
        return interventions if interventions else _fallback_interventions(case_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("intervention_candidates LLM call failed (%s) — using fallback", exc)
        return _fallback_interventions(case_id)


def _fallback_interventions(case_id: str) -> list[Intervention]:
    return [
        Intervention(
            id=f"int_{uuid4().hex[:8]}",
            case_id=case_id,
            title="Decision-rights clarity workshop (fallback)",
            target_levels=["team", "workflow", "governance"],
            intended_outcome="Increase accountability clarity without overcontrol.",
            supporting_models=["VSM", "ADKAR", "AQAL"],
            prerequisites=["cross-functional sponsor", "facilitator"],
            contraindications=["acute trust crisis without mediation"],
            risk_profile="medium",
            success_indicators=["fewer reopened decisions", "faster cycle time"],
            failure_indicators=["shadow governance", "meeting load increase"],
            regenerative_impact_notes="Builds distributed capability and lowers coordination fragility.",
            impact=0.7,
            feasibility=0.6,
            evidence_strength=0.4,  # lower since this is a fallback
            regenerative_fit=0.7,
        ),
        Intervention(
            id=f"int_{uuid4().hex[:8]}",
            case_id=case_id,
            title="Safe-to-fail communication framing experiment (fallback)",
            target_levels=["relationship", "team"],
            intended_outcome="Adapt message framing to reduce resistance while preserving agency.",
            supporting_models=["Spiral Dynamics", "Antifragility", "Flow"],
            prerequisites=["stakeholder mapping"],
            contraindications=["coercive mandate environment"],
            risk_profile="low",
            success_indicators=["improved participation", "reduced defensive responses"],
            failure_indicators=["message confusion", "trust drop"],
            regenerative_impact_notes="Improves trust and learning without rigid scripts.",
            impact=0.5,
            feasibility=0.8,
            evidence_strength=0.4,
            regenerative_fit=0.8,
        ),
    ]


# ---------------------------------------------------------------------------
# Synthesis Agent
# ---------------------------------------------------------------------------

def synthesis_output(
    case_title: str,
    evidence: list[Evidence],
    hypotheses: list[Hypothesis],
    interventions: list[Intervention],
) -> AnalysisOutput:
    """Produce an integrated 11-section analysis from all prior agent outputs."""
    evidence_text = _fmt_evidence(evidence)
    hyp_text = "\n".join(
        f"[{h.id}] (confidence={h.confidence:.2f}, lenses={h.model_sources}): {h.statement}"
        for h in hypotheses
    )
    int_text = "\n".join(
        f"[{i.id}] score={i.score:.2f} risk={i.risk_profile}: {i.title} — {i.intended_outcome}"
        for i in interventions
    )

    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Synthesis Agent",
        mission=(
            "Produce an integrated analysis. Explicitly surface convergence across lenses, "
            "name disagreements, and flag unknowns. Do NOT create false consensus. "
            "Prefer uncertainty over false precision. "
            "Flag all key questions requiring human validation."
        ),
        inputs=(
            f"Case: {case_title}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            f"Hypotheses:\n{hyp_text}\n\n"
            f"Ranked interventions:\n{int_text}"
        ),
        output_schema=json.dumps(
            {
                "situation_summary": "2-3 sentence summary of the situation",
                "convergence": ["Points where multiple lenses agree"],
                "disagreements": ["Points of genuine tension between lenses or hypotheses"],
                "missing_information": ["Key unknowns affecting confidence"],
                "confidence_and_uncertainty": {
                    "overall_confidence": "low|moderate|high",
                    "uncertainty_notes": "Explanation of key uncertainties",
                },
                "risks_and_ethical_cautions": ["Ethical and practical risks"],
                "regenerative_assessment": {
                    "trust": "Expected trust impact",
                    "resilience": "Expected resilience impact",
                    "agency": "Expected agency impact",
                    "capability": "Expected capability distribution impact",
                },
                "questions_for_human_validation": [
                    "Key questions requiring human judgment before action"
                ],
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt, max_tokens=3000)
        data = extract_json(text)
        return AnalysisOutput(
            situation_summary=data.get(
                "situation_summary",
                f"Analysis of case: {case_title} (partial LLM output)",
            ),
            evidence_observed=[
                EvidenceRef(
                    id=e.id,
                    excerpt=e.raw_excerpt,
                    reliability=e.reliability_estimate,
                    quadrant=e.aqal_quadrant_hint,
                )
                for e in evidence[:5]
            ],
            interpretations_by_lens=[
                HypothesisRef(
                    id=h.id,
                    statement=h.statement,
                    confidence=h.confidence,
                    model_sources=h.model_sources,
                )
                for h in hypotheses
            ],
            convergence=data.get("convergence", []),
            disagreements=data.get("disagreements", []),
            missing_information=data.get("missing_information", []),
            confidence_and_uncertainty=data.get(
                "confidence_and_uncertainty",
                {"overall_confidence": "low", "uncertainty_notes": "Partial synthesis"},
            ),
            recommended_interventions=[
                InterventionRef(
                    id=i.id,
                    title=i.title,
                    risk_profile=i.risk_profile,
                    regenerative_impact_notes=i.regenerative_impact_notes,
                    score=i.score,
                )
                for i in interventions
            ],
            risks_and_ethical_cautions=data.get("risks_and_ethical_cautions", []),
            regenerative_assessment=data.get("regenerative_assessment", {}),
            questions_for_human_validation=data.get("questions_for_human_validation", []),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("synthesis_output LLM call failed (%s) — using fallback", exc)
        return _fallback_synthesis(case_title, evidence, hypotheses, interventions)


# ---------------------------------------------------------------------------
# Evidence Structuring Agent (Priority 9)
# ---------------------------------------------------------------------------

def structure_evidence(
    case_id: str,
    raw_text: str,
    source: str,
    source_type: str,
) -> list[Evidence]:
    """Extract structured Evidence objects from raw practitioner text.

    Accepts transcripts, interview notes, survey responses, or any unstructured
    text and returns a list of evidence items with quadrant hints, categories,
    and reliability estimates.
    """
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Evidence Structuring Agent",
        mission=(
            "Extract discrete, structured evidence items from raw practitioner text. "
            "Each item should be a concrete, self-contained observation — not a paraphrase "
            "or interpretation. Assign each item to an AQAL quadrant based on its nature:\n"
            "  I  = subjective/first-person (emotions, motivations, self-reports)\n"
            "  We = intersubjective/cultural (norms, trust, shared meaning, relational patterns)\n"
            "  It = behavioural/technical (actions, outputs, workflows, artefacts, metrics)\n"
            "  Its = systemic/structural (org design, incentives, governance, policies)\n"
            "Assign a reliability estimate (0.0–1.0) based on source type and specificity.\n"
            "Assign an evidence_category from: subjective, relational, behavioral, structural.\n"
            "Extract 1-8 items. Do not invent detail not present in the text."
        ),
        inputs=f"Source: {source} (type: {source_type})\n\nRaw text:\n{raw_text}",
        output_schema=json.dumps(
            {
                "evidence_items": [
                    {
                        "raw_excerpt": "Verbatim or lightly edited excerpt from the text",
                        "evidence_category": "subjective|relational|behavioral|structural",
                        "aqal_quadrant_hint": "I|We|It|Its",
                        "reliability_estimate": 0.70,
                        "rationale": "One sentence explaining why this excerpt qualifies",
                    }
                ]
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt, max_tokens=2500)
        data = extract_json(text)
        items = []
        for item in data.get("evidence_items", []):
            items.append(
                Evidence(
                    id=f"ev_{uuid4().hex[:8]}",
                    case_id=case_id,
                    source=source,
                    source_type=source_type,
                    raw_excerpt=item["raw_excerpt"],
                    evidence_category=item.get("evidence_category", "behavioral"),
                    aqal_quadrant_hint=item.get("aqal_quadrant_hint"),
                    reliability_estimate=_clamp(float(item.get("reliability_estimate", 0.5))),
                    provenance={
                        "collector": "evidence_structuring_agent",
                        "rationale": item.get("rationale", ""),
                    },
                )
            )
        return items if items else _fallback_evidence(case_id, raw_text, source, source_type)
    except Exception as exc:  # noqa: BLE001
        logger.warning("structure_evidence LLM call failed (%s) — using fallback", exc)
        return _fallback_evidence(case_id, raw_text, source, source_type)


def _fallback_evidence(
    case_id: str,
    raw_text: str,
    source: str,
    source_type: str,
) -> list[Evidence]:
    """Return one catch-all evidence item when LLM is unavailable."""
    return [
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source=source,
            source_type=source_type,
            raw_excerpt=raw_text[:500],
            evidence_category="behavioral",
            reliability_estimate=0.40,
            provenance={
                "collector": "evidence_structuring_agent_fallback",
                "rationale": "LLM unavailable — excerpt stored raw for human review",
            },
        )
    ]


# ---------------------------------------------------------------------------
# ADKAR Assessment Agent
# ---------------------------------------------------------------------------

def adkar_assessment(case_id: str, evidence: list[Evidence]) -> ADKARAssessment:
    """Score the 5 ADKAR dimensions from evidence and identify the adoption bottleneck."""
    evidence_text = _fmt_evidence(evidence)
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="ADKAR Assessment Agent",
        mission=(
            "Assess change readiness across 5 ADKAR dimensions using evidence. "
            "Score each dimension 0.0–1.0 representing current observed level. "
            "Identify the bottleneck (lowest score). Recommend where to focus first."
        ),
        inputs=f"Evidence:\n{evidence_text}",
        output_schema=json.dumps(
            {
                "awareness": 0.6,
                "desire": 0.4,
                "knowledge": 0.5,
                "ability": 0.45,
                "reinforcement": 0.3,
                "bottleneck": "reinforcement",
                "recommended_focus": "Narrative explanation of where to invest first",
                "confidence": 0.65,
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt)
        data = extract_json(text)
        return ADKARAssessment(
            id=f"adkar_{uuid4().hex[:8]}",
            case_id=case_id,
            awareness=_clamp(float(data.get("awareness", 0.5))),
            desire=_clamp(float(data.get("desire", 0.5))),
            knowledge=_clamp(float(data.get("knowledge", 0.5))),
            ability=_clamp(float(data.get("ability", 0.5))),
            reinforcement=_clamp(float(data.get("reinforcement", 0.5))),
            bottleneck=data.get("bottleneck", "unknown"),
            recommended_focus=data.get("recommended_focus", ""),
            evidence_ids=[e.id for e in evidence],
            confidence=_clamp(float(data.get("confidence", 0.55))),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("adkar_assessment LLM call failed (%s) — using fallback", exc)
        return _fallback_adkar(case_id, evidence)


def _fallback_adkar(case_id: str, evidence: list[Evidence]) -> ADKARAssessment:
    return ADKARAssessment(
        id=f"adkar_{uuid4().hex[:8]}",
        case_id=case_id,
        awareness=0.5,
        desire=0.4,
        knowledge=0.4,
        ability=0.35,
        reinforcement=0.3,
        bottleneck="reinforcement",
        recommended_focus="LLM unavailable — review reinforcement mechanisms with stakeholders.",
        evidence_ids=[e.id for e in evidence],
        confidence=0.40,
    )


# ---------------------------------------------------------------------------
# Theory U Assessment Agent
# ---------------------------------------------------------------------------

def theory_u_assessment(case_id: str, evidence: list[Evidence]) -> TheoryUAssessment:
    """Map the change journey to the Theory U phases and identify movement blockers."""
    evidence_text = _fmt_evidence(evidence)
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Theory U Assessment Agent",
        mission=(
            "Map evidence to the Theory U journey (downloading → seeing → sensing → "
            "presencing → crystallizing → prototyping → performing). "
            "Identify the current phase the organisation is in. "
            "List blockers preventing deeper movement into the U. "
            "Suggest specific practices to unblock movement. "
            "Assess the overall social field quality."
        ),
        inputs=f"Evidence:\n{evidence_text}",
        output_schema=json.dumps(
            {
                "current_phase": "downloading|seeing|sensing|presencing|crystallizing|prototyping|performing",
                "blockers": ["List of blockers preventing movement"],
                "entry_points": ["Specific practices to try"],
                "social_field_quality": "Observation on collective intelligence health",
                "confidence": 0.60,
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt)
        data = extract_json(text)
        return TheoryUAssessment(
            id=f"theoryu_{uuid4().hex[:8]}",
            case_id=case_id,
            current_phase=data.get("current_phase", "downloading"),
            blockers=data.get("blockers", []),
            entry_points=data.get("entry_points", []),
            social_field_quality=data.get("social_field_quality", ""),
            evidence_ids=[e.id for e in evidence],
            confidence=_clamp(float(data.get("confidence", 0.55))),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("theory_u_assessment LLM call failed (%s) — using fallback", exc)
        return _fallback_theory_u(case_id, evidence)


def _fallback_theory_u(case_id: str, evidence: list[Evidence]) -> TheoryUAssessment:
    return TheoryUAssessment(
        id=f"theoryu_{uuid4().hex[:8]}",
        case_id=case_id,
        current_phase="downloading",
        blockers=["LLM unavailable — blockers require human assessment"],
        entry_points=["Conduct listening circles", "Run future-back visioning session"],
        social_field_quality="Unable to assess without LLM — review evidence manually.",
        evidence_ids=[e.id for e in evidence],
        confidence=0.40,
    )


# ---------------------------------------------------------------------------
# Regenerative Governance Assessment Agent
# ---------------------------------------------------------------------------

def regenerative_governance_assessment(
    case_id: str,
    hypotheses: list[Hypothesis],
    interventions: list[Intervention],
) -> dict:
    """Assess interventions against Antifragility, Biomimicry, and Flow principles."""
    hyp_text = "\n".join(f"[{h.id}]: {h.statement}" for h in hypotheses)
    int_text = "\n".join(
        f"[{i.id}] {i.title}: {i.intended_outcome}" for i in interventions
    )
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Regenerative Governance Agent",
        mission=(
            "Assess proposed interventions against three regenerative lenses:\n"
            "1. Antifragility: Do they build capability from disorder? "
            "Are they brittle under stress?\n"
            "2. Biomimicry: Do they use feedback loops, diversity, redundancy? "
            "Are they extractive or regenerative in design?\n"
            "3. Flow: Do they create conditions for optimal engagement? "
            "Do they reduce friction or create new friction?\n"
            "Score each lens 0.0–1.0. Provide key insights and risks."
        ),
        inputs=f"Hypotheses:\n{hyp_text}\n\nInterventions:\n{int_text}",
        output_schema=json.dumps(
            {
                "antifragility_score": 0.65,
                "biomimicry_score": 0.55,
                "flow_score": 0.70,
                "overall_regenerative_score": 0.63,
                "insights": ["Key regenerative strengths"],
                "risks": ["Regenerative risks or extractive tendencies"],
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt)
        data = extract_json(text)
        return {
            "antifragility_score": _clamp(float(data.get("antifragility_score", 0.5))),
            "biomimicry_score": _clamp(float(data.get("biomimicry_score", 0.5))),
            "flow_score": _clamp(float(data.get("flow_score", 0.5))),
            "overall_regenerative_score": _clamp(float(data.get("overall_regenerative_score", 0.5))),
            "insights": data.get("insights", []),
            "risks": data.get("risks", []),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("regenerative_governance_assessment failed (%s) — using fallback", exc)
        return {
            "antifragility_score": 0.40,
            "biomimicry_score": 0.40,
            "flow_score": 0.40,
            "overall_regenerative_score": 0.40,
            "insights": ["LLM unavailable — regenerative assessment requires human review"],
            "risks": ["Cannot assess without LLM output"],
        }


# ---------------------------------------------------------------------------
# Process Guidance Agent
# ---------------------------------------------------------------------------

def process_guidance(
    case_id: str,
    hypotheses: list[Hypothesis],
    interventions: list[Intervention],
    adkar: ADKARAssessment,
    theory_u: TheoryUAssessment,
) -> ProcessPlan:
    """Synthesise all assessments into a phased, sequenced process plan."""
    hyp_text = "\n".join(f"[{h.id}]: {h.statement}" for h in hypotheses)
    int_text = "\n".join(
        f"[{i.id}] stage={i.adkar_stage or '?'} score={i.score:.2f}: {i.title}"
        for i in interventions
    )
    prompt = AGENT_PROMPT_TEMPLATE.format(
        agent_name="Process Guidance Agent",
        mission=(
            "Synthesise all diagnostic outputs into a phased process plan. "
            "Sequence interventions using ADKAR logic (address the bottleneck first) "
            "and Theory U phase. Output 3-5 concrete phases, each with: "
            "phase name, objective, key activities, duration in weeks, success indicators."
        ),
        inputs=(
            f"Hypotheses:\n{hyp_text}\n\n"
            f"Interventions (ranked):\n{int_text}\n\n"
            f"ADKAR bottleneck: {adkar.bottleneck} (confidence={adkar.confidence:.2f})\n"
            f"Theory U phase: {theory_u.current_phase} (confidence={theory_u.confidence:.2f})\n"
            f"Theory U blockers: {theory_u.blockers}"
        ),
        output_schema=json.dumps(
            {
                "phases": [
                    {
                        "phase": "Phase name",
                        "objective": "What this phase achieves",
                        "activities": ["Key activities"],
                        "duration_weeks": 4,
                        "success_indicators": ["Observable signs of completion"],
                    }
                ],
                "total_duration_weeks": 12,
                "key_risks": ["Critical risks to the plan"],
            },
            indent=2,
        ),
    )
    try:
        text = call_agent(prompt, max_tokens=3000)
        data = extract_json(text)
        return ProcessPlan(
            id=f"plan_{uuid4().hex[:8]}",
            case_id=case_id,
            phases=data.get("phases", []),
            total_duration_weeks=int(data.get("total_duration_weeks", 0)),
            key_risks=data.get("key_risks", []),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("process_guidance LLM call failed (%s) — using fallback", exc)
        return ProcessPlan(
            id=f"plan_{uuid4().hex[:8]}",
            case_id=case_id,
            phases=[
                {
                    "phase": "Stabilise",
                    "objective": "Address immediate friction and build psychological safety",
                    "activities": ["Stakeholder listening sessions", "Decision-rights mapping"],
                    "duration_weeks": 4,
                    "success_indicators": ["Reduced escalation rate"],
                },
                {
                    "phase": "Redesign",
                    "objective": "Co-design structural and process changes",
                    "activities": ["Cross-functional design sprint", "Pilot experiment"],
                    "duration_weeks": 6,
                    "success_indicators": ["Prototype tested", "Stakeholder buy-in confirmed"],
                },
                {
                    "phase": "Embed",
                    "objective": "Institutionalise changes and build capability",
                    "activities": ["Training", "Practice circles", "Metrics review"],
                    "duration_weeks": 8,
                    "success_indicators": ["Behaviour change observable at 60 days"],
                },
            ],
            total_duration_weeks=18,
            key_risks=["LLM unavailable — process plan is a generic template, requires customisation"],
        )


def _fallback_synthesis(
    case_title: str,
    evidence: list[Evidence],
    hypotheses: list[Hypothesis],
    interventions: list[Intervention],
) -> AnalysisOutput:
    return AnalysisOutput(
        situation_summary=(
            f"Case '{case_title}' indicates multi-level coordination tension. "
            "(LLM synthesis unavailable — human review required)"
        ),
        evidence_observed=[
            EvidenceRef(
                id=e.id,
                excerpt=e.raw_excerpt,
                reliability=e.reliability_estimate,
                quadrant=e.aqal_quadrant_hint,
            )
            for e in evidence[:5]
        ],
        interpretations_by_lens=[
            HypothesisRef(
                id=h.id,
                statement=h.statement,
                confidence=h.confidence,
                model_sources=h.model_sources,
            )
            for h in hypotheses
        ],
        convergence=["Both lenses indicate coordination strain (fallback)."],
        disagreements=[
            "Relative contribution of structural vs interpersonal factors is uncertain."
        ],
        missing_information=["full dependency network", "baseline trust measure"],
        confidence_and_uncertainty={
            "overall_confidence": "low",
            "uncertainty_notes": "LLM unavailable — outputs are fallback only",
        },
        recommended_interventions=[
            InterventionRef(
                id=i.id,
                title=i.title,
                risk_profile=i.risk_profile,
                regenerative_impact_notes=i.regenerative_impact_notes,
                score=i.score,
            )
            for i in interventions
        ],
        risks_and_ethical_cautions=["Avoid framing stakeholders as fixed stages or colors."],
        regenerative_assessment={
            "trust": "unknown — LLM unavailable",
            "resilience": "unknown",
            "agency": "unknown",
            "capability": "unknown",
        },
        questions_for_human_validation=[
            "Do these hypotheses match the lived reality across teams?",
            "Which intervention has acceptable risk under current constraints?",
        ],
    )
