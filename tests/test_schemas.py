"""Tests for schema validation and computed fields."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisOutput,
    Case,
    CaseStatus,
    Evidence,
    EvidenceRef,
    Hypothesis,
    HypothesisRef,
    Intervention,
    InterventionRef,
)


# ---------------------------------------------------------------------------
# Intervention.compute_score — ranking formula from README §8.3
# ---------------------------------------------------------------------------

class TestInterventionComputeScore:
    def test_formula_matches_spec(self):
        i = Intervention(
            id="i1",
            case_id="c1",
            title="T",
            intended_outcome="O",
            risk_profile="medium",
            regenerative_impact_notes="R",
            impact=1.0,
            feasibility=1.0,
            evidence_strength=1.0,
            regenerative_fit=1.0,
        )
        # medium risk → 0.5
        # score = 1*0.30 + 1*0.20 + 1*0.20 + 1*0.20 - 0.5*0.10 = 0.85
        assert abs(i.compute_score() - 0.85) < 1e-9

    def test_low_risk_bonus(self):
        i = Intervention(
            id="i2",
            case_id="c1",
            title="T",
            intended_outcome="O",
            risk_profile="low",
            regenerative_impact_notes="R",
            impact=0.5,
            feasibility=0.5,
            evidence_strength=0.5,
            regenerative_fit=0.5,
        )
        # low risk → 0.2
        # score = 0.5*0.30 + 0.5*0.20 + 0.5*0.20 + 0.5*0.20 - 0.2*0.10
        # = 0.15 + 0.10 + 0.10 + 0.10 - 0.02 = 0.43
        assert abs(i.compute_score() - 0.43) < 1e-9

    def test_high_risk_penalty(self):
        i = Intervention(
            id="i3",
            case_id="c1",
            title="T",
            intended_outcome="O",
            risk_profile="high",
            regenerative_impact_notes="R",
            impact=0.5,
            feasibility=0.5,
            evidence_strength=0.5,
            regenerative_fit=0.5,
        )
        # high risk → 0.8
        # score = 0.5*0.30 + 0.5*0.20 + 0.5*0.20 + 0.5*0.20 - 0.8*0.10
        # = 0.15 + 0.10 + 0.10 + 0.10 - 0.08 = 0.37
        assert abs(i.compute_score() - 0.37) < 1e-9

    def test_unknown_risk_defaults_to_medium(self):
        i = Intervention(
            id="i4",
            case_id="c1",
            title="T",
            intended_outcome="O",
            risk_profile="unknown_value",
            regenerative_impact_notes="R",
            impact=0.5,
            feasibility=0.5,
            evidence_strength=0.5,
            regenerative_fit=0.5,
        )
        # unknown → risk_numeric = 0.5 (medium default)
        # 0.5*0.30 + 0.5*0.20 + 0.5*0.20 + 0.5*0.20 - 0.5*0.10
        # = 0.15 + 0.10 + 0.10 + 0.10 - 0.05 = 0.40
        assert abs(i.compute_score() - 0.40) < 1e-9

    def test_score_ranking_order(self):
        def make(impact, risk):
            return Intervention(
                id=f"i_{impact}_{risk}",
                case_id="c1",
                title="T",
                intended_outcome="O",
                risk_profile=risk,
                regenerative_impact_notes="R",
                impact=impact,
                feasibility=0.5,
                evidence_strength=0.5,
                regenerative_fit=0.5,
            )

        high = make(0.9, "low")
        low = make(0.1, "high")
        assert high.compute_score() > low.compute_score()


# ---------------------------------------------------------------------------
# Field constraints
# ---------------------------------------------------------------------------

class TestFieldConstraints:
    def test_evidence_reliability_must_be_0_to_1(self):
        with pytest.raises(ValidationError):
            Evidence(
                id="e1",
                case_id="c1",
                source="s",
                source_type="t",
                raw_excerpt="x",
                evidence_category="behavioral",
                reliability_estimate=1.5,  # invalid
            )

    def test_hypothesis_confidence_must_be_0_to_1(self):
        with pytest.raises(ValidationError):
            Hypothesis(
                id="h1",
                case_id="c1",
                statement="s",
                confidence=-0.1,  # invalid
            )

    def test_intervention_impact_must_be_0_to_1(self):
        with pytest.raises(ValidationError):
            Intervention(
                id="i1",
                case_id="c1",
                title="T",
                intended_outcome="O",
                risk_profile="low",
                regenerative_impact_notes="R",
                impact=1.1,  # invalid
            )

    def test_evidence_ref_reliability_constrained(self):
        with pytest.raises(ValidationError):
            EvidenceRef(id="e1", excerpt="x", reliability=2.0)


# ---------------------------------------------------------------------------
# AnalysisOutput typed reference fields
# ---------------------------------------------------------------------------

class TestAnalysisOutputStructure:
    def test_analysis_output_rejects_plain_strings_in_evidence(self):
        """evidence_observed must be List[EvidenceRef], not List[str]."""
        with pytest.raises(ValidationError):
            AnalysisOutput(
                situation_summary="s",
                evidence_observed=["plain string"],  # wrong type
                interpretations_by_lens=[],
                convergence=[],
                disagreements=[],
                missing_information=[],
                confidence_and_uncertainty={},
                recommended_interventions=[],
                risks_and_ethical_cautions=[],
                regenerative_assessment={},
                questions_for_human_validation=[],
            )

    def test_analysis_output_accepts_typed_refs(self):
        ao = AnalysisOutput(
            situation_summary="s",
            evidence_observed=[EvidenceRef(id="e1", excerpt="x", reliability=0.7)],
            interpretations_by_lens=[
                HypothesisRef(id="h1", statement="s", confidence=0.6, model_sources=["VSM"])
            ],
            convergence=["point A"],
            disagreements=[],
            missing_information=[],
            confidence_and_uncertainty={"overall": "moderate"},
            recommended_interventions=[
                InterventionRef(id="i1", title="T", risk_profile="low",
                                regenerative_impact_notes="R", score=0.55)
            ],
            risks_and_ethical_cautions=[],
            regenerative_assessment={},
            questions_for_human_validation=["Question?"],
        )
        assert ao.evidence_observed[0].id == "e1"
        assert ao.interpretations_by_lens[0].confidence == 0.6
        assert ao.recommended_interventions[0].score == 0.55


# ---------------------------------------------------------------------------
# CaseStatus enum
# ---------------------------------------------------------------------------

class TestCaseStatusEnum:
    def test_all_nine_statuses_exist(self):
        expected = {
            "intake", "evidence", "interpretation", "synthesis",
            "intervention", "governance_review", "human_validation",
            "active", "closed",
        }
        actual = {s.value for s in CaseStatus}
        assert actual == expected

    def test_case_defaults_to_intake(self):
        case = Case(id="c1", title="T", context_summary="C")
        assert case.status == CaseStatus.intake
