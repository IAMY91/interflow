"""Tests for new agent functions: ADKAR, Theory U, Regenerative, Process Guidance."""
from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest

from app.agents import (
    adkar_assessment,
    process_guidance,
    regenerative_governance_assessment,
    theory_u_assessment,
)
from app.schemas import ADKARAssessment, Evidence, Hypothesis, Intervention, TheoryUAssessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(case_id: str) -> list[Evidence]:
    return [
        Evidence(
            id=f"ev_{uuid4().hex[:8]}",
            case_id=case_id,
            source="test",
            source_type="interview",
            raw_excerpt="People feel unclear about ownership.",
            evidence_category="behavioral",
            reliability_estimate=0.7,
            aqal_quadrant_hint="It",
        )
    ]


def _make_hypothesis(case_id: str) -> Hypothesis:
    return Hypothesis(
        id=f"hyp_{uuid4().hex[:8]}",
        case_id=case_id,
        statement="Test hypothesis.",
        model_sources=["VSM"],
        evidence_ids=[],
        confidence=0.55,
        alternatives=["Alternative A"],
        missing_information=["More data needed"],
    )


def _make_intervention(case_id: str) -> Intervention:
    return Intervention(
        id=f"int_{uuid4().hex[:8]}",
        case_id=case_id,
        title="Test intervention",
        intended_outcome="Improve clarity",
        risk_profile="medium",
        success_indicators=["Clarity improves"],
        failure_indicators=["No change"],
        regenerative_impact_notes="Builds trust",
    )


# ---------------------------------------------------------------------------
# ADKAR Assessment Agent
# ---------------------------------------------------------------------------

class TestADKARAssessmentFallback:
    def test_fallback_returns_valid_structure(self):
        """When LLM is unavailable, fallback returns a valid ADKARAssessment."""
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = adkar_assessment(case_id, evidence)

        assert isinstance(result, ADKARAssessment)
        assert result.case_id == case_id
        assert 0.0 <= result.awareness <= 1.0
        assert 0.0 <= result.desire <= 1.0
        assert 0.0 <= result.knowledge <= 1.0
        assert 0.0 <= result.ability <= 1.0
        assert 0.0 <= result.reinforcement <= 1.0
        assert result.confidence <= 0.40  # fallback caps at 0.40
        assert result.bottleneck != ""
        assert result.id.startswith("adkar_")

    def test_fallback_links_evidence(self):
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = adkar_assessment(case_id, evidence)

        assert len(result.evidence_ids) == len(evidence)

    def test_llm_result_parsed_correctly(self):
        """When LLM returns valid JSON, values are used."""
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)
        llm_response = """{
            "awareness": 0.8, "desire": 0.6, "knowledge": 0.7,
            "ability": 0.5, "reinforcement": 0.3,
            "bottleneck": "reinforcement",
            "recommended_focus": "Start with reinforcement mechanisms.",
            "confidence": 0.72
        }"""

        with patch("app.agents.call_agent", return_value=llm_response):
            result = adkar_assessment(case_id, evidence)

        assert result.awareness == pytest.approx(0.8)
        assert result.bottleneck == "reinforcement"
        assert result.confidence == pytest.approx(0.72)


# ---------------------------------------------------------------------------
# Theory U Assessment Agent
# ---------------------------------------------------------------------------

class TestTheoryUAssessmentFallback:
    def test_fallback_returns_valid_structure(self):
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = theory_u_assessment(case_id, evidence)

        assert isinstance(result, TheoryUAssessment)
        assert result.case_id == case_id
        assert result.current_phase in {
            "downloading", "seeing", "sensing", "presencing",
            "crystallizing", "prototyping", "performing",
        }
        assert isinstance(result.blockers, list)
        assert isinstance(result.entry_points, list)
        assert result.confidence <= 0.40
        assert result.id.startswith("theoryu_")

    def test_llm_result_parsed_correctly(self):
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)
        llm_response = """{
            "current_phase": "sensing",
            "blockers": ["Lack of safe space", "Fear of conflict"],
            "entry_points": ["Listening circles", "Futures workshop"],
            "social_field_quality": "Transactional but not hostile.",
            "confidence": 0.65
        }"""

        with patch("app.agents.call_agent", return_value=llm_response):
            result = theory_u_assessment(case_id, evidence)

        assert result.current_phase == "sensing"
        assert "Listening circles" in result.entry_points
        assert result.confidence == pytest.approx(0.65)


# ---------------------------------------------------------------------------
# Regenerative Governance Assessment Agent
# ---------------------------------------------------------------------------

class TestRegenAssessmentFallback:
    def test_fallback_returns_dict_with_all_keys(self):
        case_id = f"case_{uuid4().hex[:8]}"
        hypotheses = [_make_hypothesis(case_id)]
        interventions = [_make_intervention(case_id)]

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = regenerative_governance_assessment(case_id, hypotheses, interventions)

        assert isinstance(result, dict)
        assert "antifragility_score" in result
        assert "biomimicry_score" in result
        assert "flow_score" in result
        assert "overall_regenerative_score" in result
        assert "insights" in result
        assert "risks" in result
        assert all(result[k] <= 0.40 for k in ["antifragility_score", "biomimicry_score", "flow_score"])

    def test_llm_result_parsed_correctly(self):
        case_id = f"case_{uuid4().hex[:8]}"
        hypotheses = [_make_hypothesis(case_id)]
        interventions = [_make_intervention(case_id)]
        llm_response = """{
            "antifragility_score": 0.7,
            "biomimicry_score": 0.65,
            "flow_score": 0.8,
            "overall_regenerative_score": 0.72,
            "insights": ["Good use of feedback loops"],
            "risks": ["May increase short-term stress"]
        }"""

        with patch("app.agents.call_agent", return_value=llm_response):
            result = regenerative_governance_assessment(case_id, hypotheses, interventions)

        assert result["antifragility_score"] == pytest.approx(0.7)
        assert "Good use of feedback loops" in result["insights"]


# ---------------------------------------------------------------------------
# Process Guidance Agent
# ---------------------------------------------------------------------------

class TestProcessGuidanceFallback:
    def test_fallback_returns_valid_process_plan(self):
        from app.schemas import ProcessPlan
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)
        hypotheses = [_make_hypothesis(case_id)]
        interventions = [_make_intervention(case_id)]

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            adkar = adkar_assessment.__wrapped__(case_id, evidence) if hasattr(adkar_assessment, "__wrapped__") else None
            if adkar is None:
                with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
                    adkar_obj = adkar_assessment(case_id, evidence)
                with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
                    theory_u_obj = theory_u_assessment(case_id, evidence)

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = process_guidance(case_id, hypotheses, interventions, adkar_obj, theory_u_obj)

        assert isinstance(result, ProcessPlan)
        assert result.case_id == case_id
        assert len(result.phases) >= 1
        assert result.total_duration_weeks > 0
        assert isinstance(result.key_risks, list)
        assert result.id.startswith("plan_")

    def test_fallback_phases_have_required_keys(self):
        case_id = f"case_{uuid4().hex[:8]}"
        evidence = _make_evidence(case_id)
        hypotheses = [_make_hypothesis(case_id)]
        interventions = [_make_intervention(case_id)]

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            adkar_obj = adkar_assessment(case_id, evidence)
            theory_u_obj = theory_u_assessment(case_id, evidence)

        with patch("app.agents.call_agent", side_effect=RuntimeError("no api key")):
            result = process_guidance(case_id, hypotheses, interventions, adkar_obj, theory_u_obj)

        for phase in result.phases:
            assert "phase" in phase
            assert "objective" in phase
            assert "activities" in phase
            assert "duration_weeks" in phase
