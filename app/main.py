from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import Role, require_roles
from .model_seeds import seed_default_models
from .schemas import (
    ADKARAssessment,
    AuditLog,
    Case,
    CaseStatus,
    Evidence,
    ModelRegistryEntry,
    OutcomeObservation,
    PatternMemory,
    ProcessPlan,
    Stakeholder,
    TheoryUAssessment,
    ValidationRecord,
)
from .store import InMemoryStore
from .agents import structure_evidence
from .workflow import make_sample_evidence, run_case_workflow

app = FastAPI(title="Interflow", version="0.2.0")
store = InMemoryStore()

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


@app.get("/")
def index() -> FileResponse:
    html = WEB_DIR / "index.html"
    if not html.exists():
        raise HTTPException(status_code=404, detail="frontend not found")
    return FileResponse(html)


@app.get("/health")
def health() -> dict:
    return {
        "name": "interflow",
        "status": "ok",
        "layers": ["execution", "meaning", "governance", "experience"],
        "rbac": ["admin", "practitioner", "reviewer", "auditor"],
    }


@app.post("/cases", response_model=Case)
def create_case(payload: Case, _: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> Case:
    if payload.id in store.cases:
        raise HTTPException(status_code=409, detail="case already exists")
    store.save_case(payload)
    return payload


@app.get("/cases", response_model=List[Case])
def list_cases(_: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor))) -> List[Case]:
    return list(store.cases.values())


@app.get("/cases/{case_id}/bundle")
def get_case_bundle(case_id: str, _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor))) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    return store.get_case_bundle(case_id)


@app.post("/cases/{case_id}/stakeholders", response_model=Stakeholder)
def add_stakeholder(
    case_id: str,
    stakeholder: Stakeholder,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner)),
) -> Stakeholder:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.save_stakeholder(stakeholder)
    case = store.cases[case_id]
    case.stakeholder_ids.append(stakeholder.id)
    store.save_case(case)
    return stakeholder


@app.post("/cases/{case_id}/evidence", response_model=Evidence)
def add_evidence(case_id: str, evidence: Evidence, _: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> Evidence:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.save_evidence(evidence)
    case = store.cases[case_id]
    case.evidence_ids.append(evidence.id)
    case.status = CaseStatus.evidence
    store.save_case(case)
    return evidence


@app.post("/cases/{case_id}/seed-sample-evidence", response_model=List[Evidence])
def seed_sample_evidence(case_id: str, _: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> List[Evidence]:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    seeded = make_sample_evidence(case_id)
    case = store.cases[case_id]
    for ev in seeded:
        store.save_evidence(ev)
        case.evidence_ids.append(ev.id)
    case.status = CaseStatus.evidence
    store.save_case(case)
    return seeded


class IngestTextPayload(BaseModel):
    raw_text: str
    source: str
    source_type: str


@app.post("/cases/{case_id}/ingest-text", response_model=List[Evidence])
def ingest_text(
    case_id: str,
    payload: IngestTextPayload,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner)),
) -> List[Evidence]:
    """Extract structured Evidence objects from raw text using the Evidence Structuring Agent."""
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    items = structure_evidence(case_id, payload.raw_text, payload.source, payload.source_type)
    case = store.cases[case_id]
    for ev in items:
        store.save_evidence(ev)
        case.evidence_ids.append(ev.id)
    case.status = CaseStatus.evidence
    store.save_case(case)
    return items


def _run_job(job_id: str, case_id: str) -> None:
    store.db.set_job(job_id, case_id, "running", {})
    try:
        result = run_case_workflow(store, case_id)
        store.db.set_job(job_id, case_id, "completed", result)
    except Exception as exc:  # noqa: BLE001
        store.db.set_job(job_id, case_id, "failed", {"error": str(exc)})


@app.post("/jobs/workflow/{case_id}")
def start_workflow_job(
    case_id: str,
    background_tasks: BackgroundTasks,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner)),
) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    job_id = f"job_{uuid4().hex[:8]}"
    store.db.set_job(job_id, case_id, "queued", {})
    background_tasks.add_task(_run_job, job_id, case_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor))) -> dict:
    job = store.db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/cases/{case_id}/run-workflow")
def run_workflow_sync(case_id: str, _: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    return run_case_workflow(store, case_id)


@app.post("/models", response_model=ModelRegistryEntry)
def register_model(entry: ModelRegistryEntry, _: Role = Depends(require_roles(Role.admin))) -> ModelRegistryEntry:
    store.save_model(entry)
    return entry


@app.get("/models", response_model=List[ModelRegistryEntry])
def list_models(_: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor))) -> List[ModelRegistryEntry]:
    return list(store.model_registry.values())


@app.post("/validations", response_model=ValidationRecord)
def submit_validation(record: ValidationRecord, _: Role = Depends(require_roles(Role.admin, Role.reviewer))) -> ValidationRecord:
    if record.case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.save_validation(record)
    if record.action in {"approve", "override"}:
        case = store.cases[record.case_id]
        case.status = CaseStatus.active
        store.save_case(case)
    return record


@app.post("/patterns", response_model=PatternMemory)
def add_pattern(pattern: PatternMemory, _: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> PatternMemory:
    store.save_pattern(pattern)
    return pattern


@app.post("/outcomes", response_model=OutcomeObservation)
def add_outcome(outcome: OutcomeObservation, _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer))) -> OutcomeObservation:
    if outcome.case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.save_outcome(outcome)
    return outcome


@app.get("/audit/{case_id}", response_model=List[AuditLog])
def list_audit(case_id: str, _: Role = Depends(require_roles(Role.admin, Role.auditor, Role.reviewer))) -> List[AuditLog]:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    ids = store.case_index[case_id]["audit"]
    return [store.audit_logs[i] for i in ids if i in store.audit_logs]


@app.get("/metrics")
def get_metrics(_: Role = Depends(require_roles(Role.admin, Role.auditor))) -> dict:
    """Operational observability: case counts by status, policy violation rate, audit event count."""
    from collections import Counter
    status_counts = Counter(c.status for c in store.cases.values())
    total_audits = len(store.audit_logs)

    # Policy violation rate: proportion of audit logs where any policy is "needs_review"
    violation_count = sum(
        1 for a in store.audit_logs.values()
        if "needs_review" in a.policy_results.values()
    )
    violation_rate = round(violation_count / total_audits, 3) if total_audits else 0.0

    return {
        "cases_total": len(store.cases),
        "cases_by_status": {k.value: v for k, v in status_counts.items()},
        "evidence_total": len(store.evidence),
        "hypotheses_total": len(store.hypotheses),
        "interventions_total": len(store.interventions),
        "audit_events_total": total_audits,
        "policy_violation_rate": violation_rate,
        "pattern_memory_total": len(store.pattern_memory),
    }


@app.post("/bootstrap-case")
def bootstrap_case(_: Role = Depends(require_roles(Role.admin, Role.practitioner))) -> dict:
    case = Case(
        id=f"case_{uuid4().hex[:8]}",
        title="Cross-functional decision friction",
        context_summary="Decisions are frequently revisited across teams.",
        goals=["reduce decision churn", "improve trust and accountability"],
    )
    store.save_case(case)

    st = Stakeholder(
        id=f"st_{uuid4().hex[:8]}",
        case_id=case.id,
        role="Product Director",
        relationship_context="Coordinates with operations and engineering",
        stated_goals=["clarity", "faster execution"],
    )
    store.save_stakeholder(st)
    case.stakeholder_ids.append(st.id)
    store.save_case(case)

    return {"case": case, "stakeholder": st}


# ---------------------------------------------------------------------------
# New OD dashboard endpoints
# ---------------------------------------------------------------------------

@app.post("/seed-defaults")
def seed_defaults(_: Role = Depends(require_roles(Role.admin))) -> dict:
    """Seed the model registry with default entries for all 9 meta-models."""
    models = seed_default_models(store)
    return {"seeded": [m.name for m in models], "count": len(models)}


@app.get("/patterns", response_model=List[PatternMemory])
def list_patterns(
    _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor)),
) -> List[PatternMemory]:
    return list(store.pattern_memory.values())


@app.get("/cases/{case_id}/metrics")
def get_case_metrics(
    case_id: str,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor)),
) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    idx = store.case_index[case_id]
    case = store.cases[case_id]
    audit_ids = idx.get("audit", [])
    violation_count = sum(
        1 for aid in audit_ids
        if aid in store.audit_logs and "needs_review" in store.audit_logs[aid].policy_results.values()
    )
    return {
        "case_id": case_id,
        "status": case.status,
        "evidence_count": len(idx.get("evidence", [])),
        "hypothesis_count": len(idx.get("hypotheses", [])),
        "intervention_count": len(idx.get("interventions", [])),
        "workflow_runs": len(audit_ids),
        "policy_violations": violation_count,
        "validation_count": len(idx.get("validations", [])),
        "outcome_count": len(idx.get("outcomes", [])),
    }


@app.get("/cases/{case_id}/adkar", response_model=ADKARAssessment)
def get_adkar(
    case_id: str,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor)),
) -> ADKARAssessment:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    result = store.adkar_assessments.get(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="ADKAR assessment not yet run — run the workflow first")
    return result


@app.get("/cases/{case_id}/theory-u", response_model=TheoryUAssessment)
def get_theory_u(
    case_id: str,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor)),
) -> TheoryUAssessment:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    result = store.theory_u_assessments.get(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Theory U assessment not yet run — run the workflow first")
    return result


@app.get("/cases/{case_id}/process-plan", response_model=ProcessPlan)
def get_process_plan(
    case_id: str,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner, Role.reviewer, Role.auditor)),
) -> ProcessPlan:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    result = store.process_plans.get(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Process plan not yet generated — run the workflow first")
    return result


class CaseUpdatePayload(BaseModel):
    title: str | None = None
    context_summary: str | None = None
    goals: List[str] | None = None
    domain: str | None = None
    sponsor: str | None = None
    sensitivity_level: str | None = None
    constraints: List[str] | None = None
    timeline_weeks: int | None = None


@app.put("/cases/{case_id}", response_model=Case)
def update_case(
    case_id: str,
    payload: CaseUpdatePayload,
    _: Role = Depends(require_roles(Role.admin, Role.practitioner)),
) -> Case:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    case = store.cases[case_id]
    if payload.title is not None:
        case.title = payload.title
    if payload.context_summary is not None:
        case.context_summary = payload.context_summary
    if payload.goals is not None:
        case.goals = payload.goals
    if payload.domain is not None:
        case.domain = payload.domain
    if payload.sponsor is not None:
        case.sponsor = payload.sponsor
    if payload.sensitivity_level is not None:
        case.sensitivity_level = payload.sensitivity_level
    if payload.constraints is not None:
        case.constraints = payload.constraints
    if payload.timeline_weeks is not None:
        case.timeline_weeks = payload.timeline_weeks
    store.save_case(case)
    return case
