from __future__ import annotations

from typing import List
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .schemas import (
    AuditLog,
    Case,
    CaseStatus,
    Evidence,
    Hypothesis,
    Intervention,
    ModelRegistryEntry,
    PatternMemory,
    Stakeholder,
    ValidationRecord,
)
from .store import InMemoryStore
from .workflow import make_sample_evidence, run_case_workflow

app = FastAPI(title="Interflow", version="0.1.0")
store = InMemoryStore()


@app.get("/")
def health() -> dict:
    return {
        "name": "interflow",
        "status": "ok",
        "layers": ["execution", "meaning", "governance", "experience"],
    }


@app.post("/cases", response_model=Case)
def create_case(payload: Case) -> Case:
    if payload.id in store.cases:
        raise HTTPException(status_code=409, detail="case already exists")
    store.cases[payload.id] = payload
    return payload


@app.get("/cases/{case_id}/bundle")
def get_case_bundle(case_id: str) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    return store.get_case_bundle(case_id)


@app.post("/cases/{case_id}/stakeholders", response_model=Stakeholder)
def add_stakeholder(case_id: str, stakeholder: Stakeholder) -> Stakeholder:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.stakeholders[stakeholder.id] = stakeholder
    store.link(case_id, "stakeholders", stakeholder.id)
    store.cases[case_id].stakeholder_ids.append(stakeholder.id)
    return stakeholder


@app.post("/cases/{case_id}/evidence", response_model=Evidence)
def add_evidence(case_id: str, evidence: Evidence) -> Evidence:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.evidence[evidence.id] = evidence
    store.link(case_id, "evidence", evidence.id)
    store.cases[case_id].evidence_ids.append(evidence.id)
    return evidence


@app.post("/cases/{case_id}/seed-sample-evidence", response_model=List[Evidence])
def seed_sample_evidence(case_id: str) -> List[Evidence]:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    seeded = make_sample_evidence(case_id)
    for ev in seeded:
        store.evidence[ev.id] = ev
        store.link(case_id, "evidence", ev.id)
        store.cases[case_id].evidence_ids.append(ev.id)
    store.cases[case_id].status = CaseStatus.evidence
    return seeded


@app.post("/cases/{case_id}/run-workflow")
def run_workflow(case_id: str) -> dict:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    return run_case_workflow(store, case_id)


@app.post("/models", response_model=ModelRegistryEntry)
def register_model(entry: ModelRegistryEntry) -> ModelRegistryEntry:
    store.model_registry[entry.name] = entry
    return entry


@app.get("/models", response_model=List[ModelRegistryEntry])
def list_models() -> List[ModelRegistryEntry]:
    return list(store.model_registry.values())


@app.post("/validations", response_model=ValidationRecord)
def submit_validation(record: ValidationRecord) -> ValidationRecord:
    if record.case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    store.validations[record.id] = record
    store.link(record.case_id, "validations", record.id)
    if record.action in {"approve", "override"}:
        store.cases[record.case_id].status = CaseStatus.active
    return record


@app.post("/patterns", response_model=PatternMemory)
def add_pattern(pattern: PatternMemory) -> PatternMemory:
    store.pattern_memory[pattern.id] = pattern
    return pattern


@app.get("/audit/{case_id}", response_model=List[AuditLog])
def list_audit(case_id: str) -> List[AuditLog]:
    if case_id not in store.cases:
        raise HTTPException(status_code=404, detail="case not found")
    ids = store.case_index[case_id]["audit"]
    return [store.audit_logs[i] for i in ids if i in store.audit_logs]


@app.post("/bootstrap-case")
def bootstrap_case() -> dict:
    case = Case(
        id=f"case_{uuid4().hex[:8]}",
        title="Cross-functional decision friction",
        context_summary="Decisions are frequently revisited across teams.",
        goals=["reduce decision churn", "improve trust and accountability"],
    )
    store.cases[case.id] = case

    st = Stakeholder(
        id=f"st_{uuid4().hex[:8]}",
        case_id=case.id,
        role="Product Director",
        relationship_context="Coordinates with operations and engineering",
        stated_goals=["clarity", "faster execution"],
    )
    store.stakeholders[st.id] = st
    store.link(case.id, "stakeholders", st.id)
    case.stakeholder_ids.append(st.id)

    return {"case": case, "stakeholder": st}
