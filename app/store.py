from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .db import SQLiteStore
from .schemas import (
    AuditLog,
    Case,
    Evidence,
    Hypothesis,
    Intervention,
    ModelRegistryEntry,
    PatternMemory,
    Stakeholder,
    ValidationRecord,
    OutcomeObservation,
)


class InMemoryStore:
    def __init__(self, db_path: str = "interflow.db") -> None:
        self.db = SQLiteStore(db_path)
        self.cases: Dict[str, Case] = {}
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.evidence: Dict[str, Evidence] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.interventions: Dict[str, Intervention] = {}
        self.validations: Dict[str, ValidationRecord] = {}
        self.audit_logs: Dict[str, AuditLog] = {}
        self.pattern_memory: Dict[str, PatternMemory] = {}
        self.outcomes: Dict[str, OutcomeObservation] = {}
        self.model_registry: Dict[str, ModelRegistryEntry] = {}
        self.case_index = defaultdict(lambda: {
            "stakeholders": [], "evidence": [], "hypotheses": [], "interventions": [], "validations": [], "audit": [], "outcomes": []
        })
        self._load_from_db()

    def _load_from_db(self) -> None:
        for raw in self.db.list_namespace("cases"):
            case = Case(**raw)
            self.cases[case.id] = case
        for raw in self.db.list_namespace("stakeholders"):
            st = Stakeholder(**raw)
            self.stakeholders[st.id] = st
            self.link(st.case_id, "stakeholders", st.id)
        for raw in self.db.list_namespace("evidence"):
            ev = Evidence(**raw)
            self.evidence[ev.id] = ev
            self.link(ev.case_id, "evidence", ev.id)
        for raw in self.db.list_namespace("hypotheses"):
            hyp = Hypothesis(**raw)
            self.hypotheses[hyp.id] = hyp
            self.link(hyp.case_id, "hypotheses", hyp.id)
        for raw in self.db.list_namespace("interventions"):
            inter = Intervention(**raw)
            self.interventions[inter.id] = inter
            self.link(inter.case_id, "interventions", inter.id)
        for raw in self.db.list_namespace("validations"):
            val = ValidationRecord(**raw)
            self.validations[val.id] = val
            self.link(val.case_id, "validations", val.id)
        for raw in self.db.list_namespace("audit"):
            aud = AuditLog(**raw)
            self.audit_logs[aud.id] = aud
            self.link(aud.case_id, "audit", aud.id)
        for raw in self.db.list_namespace("patterns"):
            pm = PatternMemory(**raw)
            self.pattern_memory[pm.id] = pm
        for raw in self.db.list_namespace("models"):
            m = ModelRegistryEntry(**raw)
            self.model_registry[m.name] = m
        for raw in self.db.list_namespace("outcomes"):
            o = OutcomeObservation(**raw)
            self.outcomes[o.id] = o
            self.link(o.case_id, "outcomes", o.id)

    def link(self, case_id: str, collection: str, object_id: str) -> None:
        if object_id not in self.case_index[case_id][collection]:
            self.case_index[case_id][collection].append(object_id)

    def save_case(self, case: Case) -> None:
        self.cases[case.id] = case
        self.db.upsert("cases", case.id, case.model_dump(mode="json"), case.id)

    def save_stakeholder(self, stakeholder: Stakeholder) -> None:
        self.stakeholders[stakeholder.id] = stakeholder
        self.link(stakeholder.case_id, "stakeholders", stakeholder.id)
        self.db.upsert("stakeholders", stakeholder.id, stakeholder.model_dump(mode="json"), stakeholder.case_id)

    def save_evidence(self, evidence: Evidence) -> None:
        self.evidence[evidence.id] = evidence
        self.link(evidence.case_id, "evidence", evidence.id)
        self.db.upsert("evidence", evidence.id, evidence.model_dump(mode="json"), evidence.case_id)

    def save_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.hypotheses[hypothesis.id] = hypothesis
        self.link(hypothesis.case_id, "hypotheses", hypothesis.id)
        self.db.upsert("hypotheses", hypothesis.id, hypothesis.model_dump(mode="json"), hypothesis.case_id)

    def save_intervention(self, intervention: Intervention) -> None:
        self.interventions[intervention.id] = intervention
        self.link(intervention.case_id, "interventions", intervention.id)
        self.db.upsert("interventions", intervention.id, intervention.model_dump(mode="json"), intervention.case_id)

    def save_validation(self, record: ValidationRecord) -> None:
        self.validations[record.id] = record
        self.link(record.case_id, "validations", record.id)
        self.db.upsert("validations", record.id, record.model_dump(mode="json"), record.case_id)

    def save_audit(self, audit: AuditLog) -> None:
        self.audit_logs[audit.id] = audit
        self.link(audit.case_id, "audit", audit.id)
        self.db.upsert("audit", audit.id, audit.model_dump(mode="json"), audit.case_id)

    def save_pattern(self, pattern: PatternMemory) -> None:
        self.pattern_memory[pattern.id] = pattern
        self.db.upsert("patterns", pattern.id, pattern.model_dump(mode="json"))

    def save_model(self, model: ModelRegistryEntry) -> None:
        self.model_registry[model.name] = model
        self.db.upsert("models", model.name, model.model_dump(mode="json"))

    def save_outcome(self, outcome: OutcomeObservation) -> None:
        self.outcomes[outcome.id] = outcome
        self.link(outcome.case_id, "outcomes", outcome.id)
        self.db.upsert("outcomes", outcome.id, outcome.model_dump(mode="json"), outcome.case_id)

    def get_case_bundle(self, case_id: str) -> Dict[str, List[dict]]:
        idx = self.case_index[case_id]
        return {
            "case": self.cases.get(case_id).model_dump(mode="json") if case_id in self.cases else None,
            "stakeholders": [self.stakeholders[s].model_dump(mode="json") for s in idx["stakeholders"] if s in self.stakeholders],
            "evidence": [self.evidence[e].model_dump(mode="json") for e in idx["evidence"] if e in self.evidence],
            "hypotheses": [self.hypotheses[h].model_dump(mode="json") for h in idx["hypotheses"] if h in self.hypotheses],
            "interventions": [self.interventions[i].model_dump(mode="json") for i in idx["interventions"] if i in self.interventions],
            "validations": [self.validations[v].model_dump(mode="json") for v in idx["validations"] if v in self.validations],
            "audit_logs": [self.audit_logs[a].model_dump(mode="json") for a in idx["audit"] if a in self.audit_logs],
            "outcomes": [self.outcomes[o].model_dump(mode="json") for o in idx["outcomes"] if o in self.outcomes],
        }
