from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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
    # Extended OD dashboard fields
    domain: str = ""
    sponsor: str = ""
    sensitivity_level: str = "standard"
    constraints: List[str] = Field(default_factory=list)
    timeline_weeks: int = 0


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
    version: str = "1.0"
    description: str = ""
    category: str = ""
    purpose: str = ""
    allowed_uses: List[str] = Field(default_factory=list)
    disallowed_uses: List[str] = Field(default_factory=list)
    min_evidence_requirements: Dict[str, Any] = Field(default_factory=dict)
    confidence_rules: Dict[str, Any] = Field(default_factory=dict)
    known_failure_modes: List[str] = Field(default_factory=list)
    ethical_risks: List[str] = Field(default_factory=list)

    @field_validator("confidence_rules", mode="before")
    @classmethod
    def coerce_confidence_rules(cls, v: Any) -> Dict[str, Any]:
        """Accept legacy List[str] format from old DB rows and convert to dict."""
        if isinstance(v, list):
            return {item: True for item in v}
        return v if isinstance(v, dict) else {}


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
    # Ranking fields (used by the scoring formula in README §8.3)
    impact: float = Field(default=0.5, ge=0, le=1)
    feasibility: float = Field(default=0.5, ge=0, le=1)
    evidence_strength: float = Field(default=0.5, ge=0, le=1)
    regenerative_fit: float = Field(default=0.5, ge=0, le=1)
    score: float = Field(default=0.0)  # computed by workflow
    # ADKAR + sequencing fields
    adkar_stage: str = ""
    sequencing_order: int = 0
    time_to_value_weeks: int = 0

    def compute_score(self) -> float:
        """Ranking formula from README §8.3.

        score = (impact * 0.30) + (feasibility * 0.20) + (evidence_strength * 0.20)
              + (regenerative_fit * 0.20) - (risk_numeric * 0.10)
        """
        risk_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        risk_numeric = risk_map.get(self.risk_profile.lower(), 0.5)
        return (
            self.impact * 0.30
            + self.feasibility * 0.20
            + self.evidence_strength * 0.20
            + self.regenerative_fit * 0.20
            - risk_numeric * 0.10
        )


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


# ---------------------------------------------------------------------------
# Structured reference types for AnalysisOutput
# (replaces List[str] to preserve claim-to-evidence traceability)
# ---------------------------------------------------------------------------

class EvidenceRef(BaseModel):
    """Structured reference to an evidence object in synthesis output."""
    id: str
    excerpt: str
    reliability: float = Field(ge=0, le=1)
    quadrant: Optional[str] = None


class HypothesisRef(BaseModel):
    """Structured reference to a hypothesis in synthesis output."""
    id: str
    statement: str
    confidence: float = Field(ge=0, le=1)
    model_sources: List[str] = Field(default_factory=list)


class InterventionRef(BaseModel):
    """Structured reference to an intervention in synthesis output."""
    id: str
    title: str
    risk_profile: str
    regenerative_impact_notes: str
    score: float = 0.0


class AnalysisOutput(BaseModel):
    situation_summary: str
    # Typed references preserve traceability from synthesis back to source objects
    evidence_observed: List[EvidenceRef]
    interpretations_by_lens: List[HypothesisRef]
    convergence: List[str]
    disagreements: List[str]
    missing_information: List[str]
    confidence_and_uncertainty: Dict[str, str]
    recommended_interventions: List[InterventionRef]
    risks_and_ethical_cautions: List[str]
    regenerative_assessment: Dict[str, str]
    questions_for_human_validation: List[str]


# ---------------------------------------------------------------------------
# Extended OD assessment schemas
# ---------------------------------------------------------------------------

class ADKARAssessment(BaseModel):
    id: str
    case_id: str
    awareness: float = Field(default=0.5, ge=0, le=1)
    desire: float = Field(default=0.5, ge=0, le=1)
    knowledge: float = Field(default=0.5, ge=0, le=1)
    ability: float = Field(default=0.5, ge=0, le=1)
    reinforcement: float = Field(default=0.5, ge=0, le=1)
    bottleneck: str = ""
    recommended_focus: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    created_at: str = ""


class TheoryUAssessment(BaseModel):
    id: str
    case_id: str
    current_phase: str = "downloading"
    blockers: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    social_field_quality: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    created_at: str = ""


class ProcessPlan(BaseModel):
    id: str
    case_id: str
    phases: List[Dict[str, Any]] = Field(default_factory=list)
    total_duration_weeks: int = 0
    key_risks: List[str] = Field(default_factory=list)
    created_at: str = ""
