from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CaseStatus(str, Enum):
    intake = "intake"
    evidence = "evidence"
    interpretation = "interpretation"
    synthesis = "synthesis"
    intervention = "intervention"
    governance_review = "governance_review"
    human_validation = "human_validation"
    active = "active"
    closed = "closed"


class ValidationAction(str, Enum):
    approve = "approve"
    reject = "reject"
    annotate = "annotate"
    request_more_data = "request_more_data"
    override = "override"


class Case(BaseModel):
    id: str
    title: str
    context_summary: str
    goals: List[str] = Field(default_factory=list)
    status: CaseStatus = CaseStatus.intake
    stakeholder_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    hypothesis_ids: List[str] = Field(default_factory=list)
    intervention_ids: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Stakeholder(BaseModel):
    id: str
    case_id: str
    role: str
    relationship_context: str
    stated_goals: List[str] = Field(default_factory=list)
    consent_flags: Dict[str, bool] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str
    case_id: str
    source: str
    source_type: str
    raw_excerpt: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence_category: str
    reliability_estimate: float = Field(ge=0, le=1)
    provenance: Dict[str, str] = Field(default_factory=dict)
    aqal_quadrant_hint: Optional[str] = None


class Hypothesis(BaseModel):
    id: str
    case_id: str
    statement: str
    model_sources: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    alternatives: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    human_validation_required: bool = True
    misuse_risks: List[str] = Field(default_factory=list)


class ModelRegistryEntry(BaseModel):
    name: str
    category: str
    purpose: str
    allowed_uses: List[str] = Field(default_factory=list)
    disallowed_uses: List[str] = Field(default_factory=list)
    min_evidence_requirements: Dict[str, int] = Field(default_factory=dict)
    confidence_rules: List[str] = Field(default_factory=list)
    known_failure_modes: List[str] = Field(default_factory=list)
    ethical_risks: List[str] = Field(default_factory=list)


class Intervention(BaseModel):
    id: str
    case_id: str
    title: str
    target_levels: List[str] = Field(default_factory=list)
    intended_outcome: str
    supporting_models: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)
    risk_profile: str
    success_indicators: List[str] = Field(default_factory=list)
    failure_indicators: List[str] = Field(default_factory=list)
    regenerative_impact_notes: str


class ValidationRecord(BaseModel):
    id: str
    case_id: str
    target_type: str
    target_id: str
    reviewer: str
    action: ValidationAction
    rationale: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    id: str
    case_id: str
    actor_type: str
    actor_id: str
    action: str
    models_used: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    alternatives_considered: List[str] = Field(default_factory=list)
    policy_results: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatternMemory(BaseModel):
    id: str
    pattern_type: str
    pattern_signature: str
    supporting_case_ids: List[str] = Field(default_factory=list)
    associated_lenses: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    outcome_summary: str


class OutcomeObservation(BaseModel):
    id: str
    case_id: str
    intervention_id: str
    observed_effects: List[str] = Field(default_factory=list)
    regenerative_signals: Dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisOutput(BaseModel):
    situation_summary: str
    evidence_observed: List[str]
    interpretations_by_lens: List[str]
    convergence: List[str]
    disagreements: List[str]
    missing_information: List[str]
    confidence_and_uncertainty: Dict[str, str]
    recommended_interventions: List[str]
    risks_and_ethical_cautions: List[str]
    regenerative_assessment: Dict[str, str]
    questions_for_human_validation: List[str]
