"""Tests for the case workflow state machine.

All LLM-touching functions are mocked so no ANTHROPIC_API_KEY is required.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.schemas import Case, CaseStatus
from app.store import InMemoryStore
from app.workflow import make_sample_evidence, run_case_workflow
from tests.conftest import make_analysis_output, make_hypothesis, make_intervention

# ---------------------------------------------------------------------------
# Shared mock return values
# ---------------------------------------------------------------------------

_HYPOTHESIS_1 = make_hypothesis(case_id="case_wf", confidence=0.55)
_HYPOTHESIS_2 = make_hypothesis(
    case_id="case_wf",
    confidence=0.50,
)
# Give h2 a different ID to avoid collision
_HYPOTHESIS_2 = _HYPOTHESIS_2.model_copy(update={"id": "hyp_test_02"})

_INTERVENTION = make_intervention(case_id="case_wf")
_ANALYSIS = make_analysis_output()

LLM_PASS = {"pass": True, "violations": []}


def _mock_patches():
    """Return a list of context managers that mock all LLM-dependent calls."""
    return [
        patch("app.workflow.value_logic_hypothesis", return_value=_HYPOTHESIS_1),
        patch("app.workflow.systems_hypothesis", return_value=_HYPOTHESIS_2),
        patch("app.workflow.intervention_candidates", return_value=[_INTERVENTION]),
        patch("app.workflow.synthesis_output", return_value=_ANALYSIS),
        patch("app.governance._llm_policy_check", return_value=LLM_PASS),
    ]


def _apply_patches(patches):
    for p in patches:
        p.start()
    return patches


def _stop_patches(patches):
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store():
    return InMemoryStore(db_path=":memory:")


@pytest.fixture
def case_with_evidence(store):
    """A case pre-loaded with sample evidence, ready to run the workflow."""
    case = Case(
        id="case_wf",
        title="Workflow test case",
        context_summary="Testing the state machine end-to-end.",
        goals=["validate state transitions"],
    )
    store.save_case(case)
    for ev in make_sample_evidence("case_wf"):
        store.save_evidence(ev)
        case.evidence_ids.append(ev.id)
    case.status = CaseStatus.evidence
    store.save_case(case)
    return store


# ---------------------------------------------------------------------------
# State machine tests
# ---------------------------------------------------------------------------

class TestWorkflowStateMachine:
    def test_workflow_completes_without_error(self, case_with_evidence):
        patches = _apply_patches(_mock_patches())
        try:
            result = run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)
        assert "error" not in result
        assert result["case_id"] == "case_wf"

    def test_final_state_is_active_when_policy_passes(self, case_with_evidence):
        patches = _apply_patches(_mock_patches())
        try:
            result = run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)
        assert result["stage"] == CaseStatus.active
        assert result["review_required"] is False

    def test_synthesis_state_is_set_on_case(self, case_with_evidence):
        """The synthesis CaseStatus must be reachable (was previously skipped)."""
        observed_states = []

        original_save = case_with_evidence.save_case

        def tracking_save(case):
            observed_states.append(case.status)
            original_save(case)

        case_with_evidence.save_case = tracking_save

        patches = _apply_patches(_mock_patches())
        try:
            run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)

        # synthesis must appear in the sequence of states saved
        assert CaseStatus.synthesis in observed_states

    def test_human_validation_required_when_policy_fails(self, case_with_evidence):
        """If governance flags a violation, case must go to human_validation."""
        failing_llm = {
            "pass": False,
            "violations": [
                {
                    "rule": "no_essentialization",
                    "severity": "high",
                    "excerpt": "test",
                    "rationale": "test violation",
                }
            ],
        }
        patches = _apply_patches(_mock_patches()[:-1])  # exclude LLM patch
        patches.append(
            patch("app.governance._llm_policy_check", return_value=failing_llm)
        )
        patches[-1].start()
        try:
            result = run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)

        assert result["review_required"] is True
        assert result["stage"] == CaseStatus.human_validation

    def test_audit_log_is_written(self, case_with_evidence):
        patches = _apply_patches(_mock_patches())
        try:
            result = run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)
        audit_id = result["memory_writeback"]["audit_event"]
        assert audit_id in case_with_evidence.audit_logs

    def test_interventions_are_scored_and_sorted(self, case_with_evidence):
        i_low = make_intervention(case_id="case_wf", risk_profile="high")
        i_low = i_low.model_copy(update={"id": "int_low", "impact": 0.2, "feasibility": 0.2,
                                          "evidence_strength": 0.2, "regenerative_fit": 0.2})
        i_high = make_intervention(case_id="case_wf", risk_profile="low")
        i_high = i_high.model_copy(update={"id": "int_high", "impact": 0.9, "feasibility": 0.9,
                                            "evidence_strength": 0.9, "regenerative_fit": 0.9})

        base_patches = _mock_patches()[:-1]  # without LLM_PASS governance patch
        base_patches[2] = patch(
            "app.workflow.intervention_candidates",
            return_value=[i_low, i_high],
        )
        patches = _apply_patches(base_patches)
        patches.append(patch("app.governance._llm_policy_check", return_value=LLM_PASS))
        patches[-1].start()
        try:
            run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)

        # Verify scores were computed and stored
        stored_high = case_with_evidence.interventions.get("int_high")
        stored_low = case_with_evidence.interventions.get("int_low")
        assert stored_high is not None
        assert stored_low is not None
        assert stored_high.score > stored_low.score


# ---------------------------------------------------------------------------
# Closed-case guard
# ---------------------------------------------------------------------------

class TestClosedCaseGuard:
    def test_closed_case_returns_error(self, store):
        case = Case(
            id="case_closed",
            title="Closed case",
            context_summary="Already done.",
            status=CaseStatus.closed,
        )
        store.save_case(case)
        result = run_case_workflow(store, "case_closed")
        assert result.get("error") == "workflow_refused"
        assert "closed" in result["reason"].lower()

    def test_non_closed_case_runs_normally(self, case_with_evidence):
        patches = _apply_patches(_mock_patches())
        try:
            result = run_case_workflow(case_with_evidence, "case_wf")
        finally:
            _stop_patches(patches)
        assert "error" not in result
