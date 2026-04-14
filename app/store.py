from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

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
)


class InMemoryStore:
    def __init__(self) -> None:
        self.cases: Dict[str, Case] = {}
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.evidence: Dict[str, Evidence] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.interventions: Dict[str, Intervention] = {}
        self.validations: Dict[str, ValidationRecord] = {}
        self.audit_logs: Dict[str, AuditLog] = {}
        self.pattern_memory: Dict[str, PatternMemory] = {}
        self.model_registry: Dict[str, ModelRegistryEntry] = {}
        self.case_index = defaultdict(lambda: {
            "stakeholders": [], "evidence": [], "hypotheses": [], "interventions": [], "validations": [], "audit": []
        })

    def link(self, case_id: str, collection: str, object_id: str) -> None:
        self.case_index[case_id][collection].append(object_id)

    def get_case_bundle(self, case_id: str) -> Dict[str, List[dict]]:
        idx = self.case_index[case_id]
        return {
            "case": self.cases.get(case_id).model_dump() if case_id in self.cases else None,
            "stakeholders": [self.stakeholders[s].model_dump() for s in idx["stakeholders"] if s in self.stakeholders],
            "evidence": [self.evidence[e].model_dump() for e in idx["evidence"] if e in self.evidence],
            "hypotheses": [self.hypotheses[h].model_dump() for h in idx["hypotheses"] if h in self.hypotheses],
            "interventions": [self.interventions[i].model_dump() for i in idx["interventions"] if i in self.interventions],
            "validations": [self.validations[v].model_dump() for v in idx["validations"] if v in self.validations],
            "audit_logs": [self.audit_logs[a].model_dump() for a in idx["audit"] if a in self.audit_logs],
        }
