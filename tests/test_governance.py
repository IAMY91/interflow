"""Tests for governance policy enforcement.

LLM calls are mocked so no ANTHROPIC_API_KEY is required.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.governance import enforce_hypothesis_policy, enforce_intervention_policy
from tests.conftest import make_hypothesis, make_intervention

# All tests patch _llm_policy_check so that structural rules are tested in
# isolation, and one set of tests verifies the LLM path is actually called.

LLM_PASS = {"pass": True, "violations": []}
LLM_VIOLATION = {
    "pass": False,
    "violations": [
        {
            "rule": "no_essentialization",
            "severity": "high",
            "excerpt": "This team is clearly at stage red",
            "rationale": "Assigns a fixed developmental label to a team.",
        }
    ],
}


# ---------------------------------------------------------------------------
# Hypothesis policy — structural rules
# ---------------------------------------------------------------------------

class TestHypothesisStructuralRules:
    def test_valid_hypothesis_passes(self):
        h = make_hypothesis(confidence=0.55, evidence_ids=["ev_01", "ev_02", "ev_03"])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is True
        assert result["violations"] == []

    def test_missing_evidence_ids_fails(self):
        h = make_hypothesis(evidence_ids=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "missing_evidence_links" in rules

    def test_high_confidence_thin_data_fails(self):
        # confidence > 0.80 with < 3 evidence items
        h = make_hypothesis(confidence=0.85, evidence_ids=["ev_01"])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "high_confidence_thin_data" in rules

    def test_confidence_at_threshold_with_enough_evidence_passes(self):
        # confidence == 0.80 exactly is not > 0.80, so should pass
        h = make_hypothesis(confidence=0.80, evidence_ids=["ev_01", "ev_02"])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is True

    def test_missing_alternatives_fails(self):
        h = make_hypothesis(alternatives=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "missing_alternatives" in rules

    def test_multiple_structural_violations_accumulate(self):
        h = make_hypothesis(evidence_ids=[], alternatives=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "missing_evidence_links" in rules
        assert "missing_alternatives" in rules


# ---------------------------------------------------------------------------
# Hypothesis policy — LLM critic path
# ---------------------------------------------------------------------------

class TestHypothesisLLMCritic:
    def test_llm_violation_causes_policy_failure(self):
        h = make_hypothesis()  # structurally valid
        with patch("app.governance._llm_policy_check", return_value=LLM_VIOLATION):
            result = enforce_hypothesis_policy(h)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "no_essentialization" in rules

    def test_llm_check_is_called(self):
        h = make_hypothesis()
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS) as mock_check:
            enforce_hypothesis_policy(h)
        mock_check.assert_called_once()

    def test_llm_failure_falls_back_gracefully(self):
        """When LLM raises, structural checks still run and result is returned."""
        h = make_hypothesis()
        with patch("app.governance.call_agent", side_effect=RuntimeError("network error")):
            result = enforce_hypothesis_policy(h)
        # Structurally valid, LLM skipped → should pass with llm_check_skipped flag
        assert result["pass"] is True
        assert result.get("llm_check_skipped") is True


# ---------------------------------------------------------------------------
# Intervention policy — structural rules
# ---------------------------------------------------------------------------

class TestInterventionStructuralRules:
    def test_valid_intervention_passes(self):
        i = make_intervention()
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is True
        assert result["violations"] == []

    def test_missing_success_indicators_fails(self):
        i = make_intervention(success_indicators=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "missing_outcome_signals" in rules

    def test_missing_failure_indicators_fails(self):
        i = make_intervention(failure_indicators=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "missing_outcome_signals" in rules

    def test_high_risk_without_contraindications_fails(self):
        i = make_intervention(risk_profile="high", contraindications=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is False
        rules = [v["rule"] for v in result["violations"]]
        assert "high_risk_missing_contraindications" in rules

    def test_high_risk_with_contraindications_passes_structural(self):
        i = make_intervention(
            risk_profile="high",
            contraindications=["Active organisational crisis", "Leader not engaged"],
        )
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is True

    def test_medium_risk_no_contraindications_passes(self):
        i = make_intervention(risk_profile="medium", contraindications=[])
        with patch("app.governance._llm_policy_check", return_value=LLM_PASS):
            result = enforce_intervention_policy(i)
        assert result["pass"] is True

    def test_llm_failure_falls_back_gracefully(self):
        i = make_intervention()
        with patch("app.governance.call_agent", side_effect=RuntimeError("timeout")):
            result = enforce_intervention_policy(i)
        assert result["pass"] is True
        assert result.get("llm_check_skipped") is True
