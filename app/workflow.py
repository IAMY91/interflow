from __future__ import annotations

from uuid import uuid4

from .agents import aqal_mapping, intervention_candidates, synthesis_output, systems_hypothesis, value_logic_hypothesis
from .governance import enforce_hypothesis_policy, enforce_intervention_policy
from .schemas import AuditLog, CaseStatus, Evidence
from .store import InMemoryStore


def run_case_workflow(store: InMemoryStore, case_id: str) -> dict:
    case = store.cases[case_id]
    evidence = [store.evidence[eid] for eid in store.case_index[case_id]["evidence"] if eid in store.evidence]

    case.status = CaseStatus.interpretation
    aqal = aqal_mapping(evidence)

    h1 = value_logic_hypothesis(case_id, evidence)
    h2 = systems_hypothesis(case_id, evidence)
    hypothesis_checks = {
        h1.id: enforce_hypothesis_policy(h1),
        h2.id: enforce_hypothesis_policy(h2),
    }

    for h in [h1, h2]:
        store.hypotheses[h.id] = h
        store.link(case_id, "hypotheses", h.id)
        case.hypothesis_ids.append(h.id)

    case.status = CaseStatus.intervention
    ints = intervention_candidates(case_id)
    intervention_checks = {}
    for i in ints:
        intervention_checks[i.id] = enforce_intervention_policy(i)
        store.interventions[i.id] = i
        store.link(case_id, "interventions", i.id)
        case.intervention_ids.append(i.id)

    case.status = CaseStatus.governance_review
    review_required = any(not v["pass"] for v in hypothesis_checks.values()) or any(
        not v["pass"] for v in intervention_checks.values()
    )

    case.status = CaseStatus.human_validation if review_required else CaseStatus.active

    synthesis = synthesis_output(case.title, evidence, [h1, h2], ints)

    audit = AuditLog(
        id=f"aud_{uuid4().hex[:8]}",
        case_id=case_id,
        actor_type="workflow_engine",
        actor_id="run_case_workflow",
        action="workflow_run",
        models_used=["AQAL", "Spiral Dynamics", "VSM", "Cynefin", "ADKAR", "Antifragility", "Flow"],
        evidence_ids=[e.id for e in evidence],
        assumptions=["Hypotheses are provisional and context-dependent."],
        alternatives_considered=["Interpersonal-only explanation", "structure-only explanation"],
        policy_results={
            "hypothesis_policy": "pass" if all(v["pass"] for v in hypothesis_checks.values()) else "needs_review",
            "intervention_policy": "pass" if all(v["pass"] for v in intervention_checks.values()) else "needs_review",
        },
    )
    store.audit_logs[audit.id] = audit
    store.link(case_id, "audit", audit.id)

    return {
        "case_id": case_id,
        "stage": case.status,
        "aqal": aqal,
        "hypothesis_checks": hypothesis_checks,
        "intervention_checks": intervention_checks,
        "analysis": synthesis.model_dump(),
        "review_required": review_required,
        "memory_writeback": {
            "case_updated": True,
            "hypotheses_added": len([h1, h2]),
            "interventions_added": len(ints),
            "audit_event": audit.id,
        },
        "outcome_learning": "Pending: submit post-intervention outcome observations via /outcomes endpoint.",
    }


def make_sample_evidence(case_id: str) -> list[Evidence]:
    return [
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source="interview_01",
            source_type="interview",
            raw_excerpt="We revisit decisions because ownership is not clear.",
            evidence_category="behavioral",
            reliability_estimate=0.72,
            provenance={"collector": "evidence_agent", "loc": "t1:20-24"},
            aqal_quadrant_hint="It",
        ),
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source="retro_notes",
            source_type="artifact",
            raw_excerpt="People feel unheard between product and ops teams.",
            evidence_category="relational",
            reliability_estimate=0.68,
            provenance={"collector": "facilitator", "loc": "retro-mar"},
            aqal_quadrant_hint="We",
        ),
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source="org_chart",
            source_type="artifact",
            raw_excerpt="Decision authority is split across two functions.",
            evidence_category="structural",
            reliability_estimate=0.81,
            provenance={"collector": "systems_agent", "loc": "org_v4"},
            aqal_quadrant_hint="Its",
        ),
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source="pulse_survey",
            source_type="survey",
            raw_excerpt="I am unsure how my work contributes to shared goals.",
            evidence_category="subjective",
            reliability_estimate=0.64,
            provenance={"collector": "hr_ops", "loc": "q2_pulse"},
            aqal_quadrant_hint="I",
        ),
    ]
