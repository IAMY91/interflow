from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    AnalysisOutput,
    Case,
    EvidenceRef,
    Hypothesis,
    HypothesisRef,
    Intervention,
    InterventionRef,
)
from app.store import InMemoryStore


# ---------------------------------------------------------------------------
# Store and client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_store():
    """Isolated in-memory store — no file I/O."""
    return InMemoryStore(db_path=":memory:")


@pytest.fixture
def client(test_store):
    """TestClient with the global store replaced by an isolated one."""
    with patch("app.main.store", test_store):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Auth header shortcuts
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_h():
    return {"X-API-Key": "admin-key"}


@pytest.fixture
def practitioner_h():
    return {"X-API-Key": "practitioner-key"}


@pytest.fixture
def reviewer_h():
    return {"X-API-Key": "reviewer-key"}


@pytest.fixture
def auditor_h():
    return {"X-API-Key": "auditor-key"}


# ---------------------------------------------------------------------------
# Reusable domain object builders
# ---------------------------------------------------------------------------

def make_hypothesis(
    case_id: str = "case_test",
    confidence: float = 0.55,
    evidence_ids: list[str] | None = None,
    alternatives: list[str] | None = None,
) -> Hypothesis:
    return Hypothesis(
        id="hyp_test_01",
        case_id=case_id,
        statement="One possible interpretation is that unclear ownership is driving re-work.",
        model_sources=["VSM"],
        evidence_ids=evidence_ids if evidence_ids is not None else ["ev_01", "ev_02", "ev_03"],
        confidence=confidence,
        alternatives=alternatives if alternatives is not None else ["Interpersonal conflict as primary driver"],
        missing_information=["Direct observation data not available"],
        human_validation_required=True,
        misuse_risks=["Avoid labeling team as dysfunctional"],
    )


def make_intervention(
    case_id: str = "case_test",
    risk_profile: str = "medium",
    success_indicators: list[str] | None = None,
    failure_indicators: list[str] | None = None,
    contraindications: list[str] | None = None,
) -> Intervention:
    return Intervention(
        id="int_test_01",
        case_id=case_id,
        title="Decision rights clarification workshop",
        target_levels=["team", "structure"],
        intended_outcome="Reduce decision churn by 40% within 60 days",
        supporting_models=["VSM", "ADKAR"],
        prerequisites=["Leadership alignment on scope"],
        contraindications=contraindications if contraindications is not None else [],
        risk_profile=risk_profile,
        success_indicators=success_indicators if success_indicators is not None else ["Decision re-work rate drops"],
        failure_indicators=failure_indicators if failure_indicators is not None else ["Continued escalation pattern"],
        regenerative_impact_notes="Increases distributed decision capability",
        impact=0.8,
        feasibility=0.7,
        evidence_strength=0.65,
        regenerative_fit=0.75,
    )


def make_analysis_output() -> AnalysisOutput:
    return AnalysisOutput(
        situation_summary="Test situation summary",
        evidence_observed=[
            EvidenceRef(id="ev_01", excerpt="Excerpt text", reliability=0.7, quadrant="It")
        ],
        interpretations_by_lens=[
            HypothesisRef(
                id="hyp_test_01",
                statement="One possible interpretation…",
                confidence=0.55,
                model_sources=["VSM"],
            )
        ],
        convergence=["Decision rights ambiguity confirmed across lenses"],
        disagreements=[],
        missing_information=["Direct observation data"],
        confidence_and_uncertainty={"overall": "moderate"},
        recommended_interventions=[
            InterventionRef(
                id="int_test_01",
                title="Decision rights clarification workshop",
                risk_profile="medium",
                regenerative_impact_notes="Increases distributed decision capability",
                score=0.55,
            )
        ],
        risks_and_ethical_cautions=["Avoid framing as team failure"],
        regenerative_assessment={"trust": "stable"},
        questions_for_human_validation=["Is leadership alignment feasible within 2 weeks?"],
    )
