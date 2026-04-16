from __future__ import annotations

import logging
from uuid import uuid4

from .agents import (
    adkar_assessment,
    aqal_mapping,
    intervention_candidates,
    process_guidance,
    regenerative_governance_assessment,
    synthesis_output,
    systems_hypothesis,
    theory_u_assessment,
    value_logic_hypothesis,
)
from .governance import enforce_hypothesis_policy, enforce_intervention_policy
from .schemas import AuditLog, CaseStatus, Evidence
from .store import InMemoryStore

logger = logging.getLogger(__name__)

# Models consumed by each workflow phase
_INTERPRETATION_MODELS = ["AQAL", "Spiral Dynamics", "VSM", "Cynefin"]
_INTERVENTION_MODELS   = ["ADKAR", "Antifragility", "Flow"]


def _check_model_requirements(store: InMemoryStore, model_names: list[str], evidence_count: int) -> list[str]:
    """Return a list of policy warning strings for unregistered models or unmet evidence minimums."""
    warnings: list[str] = []
    for name in model_names:
        entry = store.model_registry.get(name)
        if entry is None:
            warnings.append(f"model_not_registered:{name}")
            logger.warning("Model %r not in registry — proceeding without registry constraints", name)
            continue
        min_total = entry.min_evidence_requirements.get("total", 0)
        if evidence_count < min_total:
            warnings.append(
                f"evidence_below_minimum_for:{name} (requires {min_total}, have {evidence_count})"
            )
    return warnings


def run_case_workflow(store: InMemoryStore, case_id: str) -> dict:
    case = store.cases[case_id]

    # Guard: refuse to re-run a closed case
    if case.status == CaseStatus.closed:
        return {
            "case_id": case_id,
            "error": "workflow_refused",
            "reason": "Case is closed. Re-open or create a new case to run the workflow again.",
        }

    evidence = [store.evidence[eid] for eid in store.case_index[case_id]["evidence"] if eid in store.evidence]

    # ── Model registry pre-flight ────────────────────────────────────────────
    registry_warnings = (
        _check_model_requirements(store, _INTERPRETATION_MODELS, len(evidence))
        + _check_model_requirements(store, _INTERVENTION_MODELS, len(evidence))
    )

    # ── Interpretation phase ────────────────────────────────────────────────
    case.status = CaseStatus.interpretation
    aqal = aqal_mapping(evidence)

    h1 = value_logic_hypothesis(case_id, evidence)
    h2 = systems_hypothesis(case_id, evidence)
    hypothesis_checks = {
        h1.id: enforce_hypothesis_policy(h1),
        h2.id: enforce_hypothesis_policy(h2),
    }

    for h in [h1, h2]:
        store.save_hypothesis(h)
        case.hypothesis_ids.append(h.id)

    # ── Synthesis phase (state machine checkpoint) ──────────────────────────
    case.status = CaseStatus.synthesis
    store.save_case(case)  # persist the synthesis checkpoint for auditability

    # ── Intervention phase ──────────────────────────────────────────────────
    case.status = CaseStatus.intervention
    ints = intervention_candidates(case_id, hypotheses=[h1, h2])

    # Compute ranking scores and sort highest first
    for i in ints:
        i.score = i.compute_score()
    ints.sort(key=lambda x: x.score, reverse=True)

    intervention_checks: dict = {}
    for i in ints:
        intervention_checks[i.id] = enforce_intervention_policy(i)
        store.save_intervention(i)
        case.intervention_ids.append(i.id)

    # ── Extended OD assessments (ADKAR, Theory U, Regenerative, Process Plan) ─
    adkar = adkar_assessment(case_id, evidence)
    store.save_adkar(adkar)

    theory_u = theory_u_assessment(case_id, evidence)
    store.save_theory_u(theory_u)

    regen = regenerative_governance_assessment(case_id, [h1, h2], ints)
    store.save_regen_assessment(case_id, regen)

    plan = process_guidance(case_id, [h1, h2], ints, adkar, theory_u)
    store.save_process_plan(plan)

    # ── Governance review ───────────────────────────────────────────────────
    case.status = CaseStatus.governance_review
    review_required = any(not v["pass"] for v in hypothesis_checks.values()) or any(
        not v["pass"] for v in intervention_checks.values()
    )

    case.status = CaseStatus.human_validation if review_required else CaseStatus.active
    store.save_case(case)

    synthesis = synthesis_output(case.title, evidence, [h1, h2], ints)

    # Build structured policy_results for audit log
    policy_violations: dict = {}
    for hid, check in hypothesis_checks.items():
        if not check["pass"]:
            policy_violations[f"hypothesis:{hid}"] = [v["rule"] for v in check["violations"]]
    for iid, check in intervention_checks.items():
        if not check["pass"]:
            policy_violations[f"intervention:{iid}"] = [v["rule"] for v in check["violations"]]

    audit = AuditLog(
        id=f"aud_{uuid4().hex[:8]}",
        case_id=case_id,
        actor_type="workflow_engine",
        actor_id="run_case_workflow",
        action="workflow_run",
        models_used=[
            "AQAL", "Spiral Dynamics", "VSM", "Cynefin",
            "ADKAR", "Antifragility", "Biomimicry", "Flow", "Theory U",
        ],
        evidence_ids=[e.id for e in evidence],
        assumptions=["Hypotheses are provisional and context-dependent."],
        alternatives_considered=["Interpersonal-only explanation", "structure-only explanation"],
        policy_results={
            "hypothesis_policy": "pass" if all(v["pass"] for v in hypothesis_checks.values()) else "needs_review",
            "intervention_policy": "pass" if all(v["pass"] for v in intervention_checks.values()) else "needs_review",
            "violations_count": str(len(policy_violations)),
            "violated_items": str(list(policy_violations.keys())),
            "registry_warnings": str(registry_warnings) if registry_warnings else "none",
        },
    )
    store.save_audit(audit)

    return {
        "case_id": case_id,
        "stage": case.status,
        "aqal": aqal,
        "registry_warnings": registry_warnings,
        "hypothesis_checks": hypothesis_checks,
        "intervention_checks": intervention_checks,
        "analysis": synthesis.model_dump(),
        "adkar": adkar.model_dump(),
        "theory_u": theory_u.model_dump(),
        "regenerative": regen,
        "process_plan": plan.model_dump(),
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
