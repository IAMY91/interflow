"""Tests for FastAPI routes — RBAC, case lifecycle, and validation endpoints."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.schemas import Case, CaseStatus, ValidationAction
from tests.conftest import make_analysis_output, make_hypothesis, make_intervention

LLM_PASS = {"pass": True, "violations": []}


# ---------------------------------------------------------------------------
# Health check (no auth)
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "rbac" in data


# ---------------------------------------------------------------------------
# RBAC enforcement
# ---------------------------------------------------------------------------

class TestRBAC:
    def test_missing_api_key_returns_401(self, client):
        resp = client.post("/cases", json={"id": "x", "title": "t", "context_summary": "s"})
        assert resp.status_code == 401

    def test_invalid_api_key_returns_401(self, client):
        resp = client.get("/health", headers={"X-API-Key": "bad-key"})
        # health has no auth, so it passes; use a protected endpoint
        resp = client.get("/models", headers={"X-API-Key": "bad-key"})
        assert resp.status_code == 401

    def test_auditor_cannot_create_case(self, client, auditor_h):
        payload = {"id": "case_rbac", "title": "T", "context_summary": "C"}
        resp = client.post("/cases", json=payload, headers=auditor_h)
        assert resp.status_code == 403

    def test_reviewer_cannot_create_case(self, client, reviewer_h):
        payload = {"id": "case_rbac", "title": "T", "context_summary": "C"}
        resp = client.post("/cases", json=payload, headers=reviewer_h)
        assert resp.status_code == 403

    def test_practitioner_can_create_case(self, client, practitioner_h):
        payload = {"id": "case_rbac_p", "title": "T", "context_summary": "C"}
        resp = client.post("/cases", json=payload, headers=practitioner_h)
        assert resp.status_code == 200

    def test_admin_can_create_case(self, client, admin_h):
        payload = {"id": "case_rbac_a", "title": "T", "context_summary": "C"}
        resp = client.post("/cases", json=payload, headers=admin_h)
        assert resp.status_code == 200

    def test_practitioner_cannot_register_model(self, client, practitioner_h):
        payload = {"name": "TestModel", "category": "diagnostic", "purpose": "test"}
        resp = client.post("/models", json=payload, headers=practitioner_h)
        assert resp.status_code == 403

    def test_admin_can_register_model(self, client, admin_h):
        payload = {"name": "TestModel", "category": "diagnostic", "purpose": "test"}
        resp = client.post("/models", json=payload, headers=admin_h)
        assert resp.status_code == 200

    def test_auditor_can_read_audit_log(self, client, admin_h, auditor_h):
        # Create a case first
        client.post("/cases", json={"id": "case_audit_test", "title": "T", "context_summary": "C"}, headers=admin_h)
        resp = client.get("/audit/case_audit_test", headers=auditor_h)
        assert resp.status_code == 200

    def test_practitioner_cannot_read_audit_log(self, client, admin_h, practitioner_h):
        client.post("/cases", json={"id": "case_audit_p", "title": "T", "context_summary": "C"}, headers=admin_h)
        resp = client.get("/audit/case_audit_p", headers=practitioner_h)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Case lifecycle
# ---------------------------------------------------------------------------

class TestCaseLifecycle:
    def test_create_and_retrieve_case(self, client, admin_h):
        payload = {
            "id": "case_lifecycle",
            "title": "Decision friction",
            "context_summary": "Teams revisit decisions frequently.",
            "goals": ["reduce churn"],
        }
        resp = client.post("/cases", json=payload, headers=admin_h)
        assert resp.status_code == 200
        assert resp.json()["id"] == "case_lifecycle"

    def test_duplicate_case_returns_409(self, client, admin_h):
        payload = {"id": "case_dup", "title": "T", "context_summary": "C"}
        client.post("/cases", json=payload, headers=admin_h)
        resp = client.post("/cases", json=payload, headers=admin_h)
        assert resp.status_code == 409

    def test_add_evidence_to_case(self, client, admin_h):
        client.post("/cases", json={"id": "case_ev", "title": "T", "context_summary": "C"}, headers=admin_h)
        ev_payload = {
            "id": "ev_001",
            "case_id": "case_ev",
            "source": "interview_01",
            "source_type": "interview",
            "raw_excerpt": "People feel unheard.",
            "evidence_category": "relational",
            "reliability_estimate": 0.7,
        }
        resp = client.post("/cases/case_ev/evidence", json=ev_payload, headers=admin_h)
        assert resp.status_code == 200
        assert resp.json()["id"] == "ev_001"

    def test_evidence_moves_case_to_evidence_status(self, client, admin_h):
        client.post("/cases", json={"id": "case_ev2", "title": "T", "context_summary": "C"}, headers=admin_h)
        ev_payload = {
            "id": "ev_002",
            "case_id": "case_ev2",
            "source": "s",
            "source_type": "t",
            "raw_excerpt": "excerpt",
            "evidence_category": "relational",
            "reliability_estimate": 0.6,
        }
        client.post("/cases/case_ev2/evidence", json=ev_payload, headers=admin_h)
        bundle = client.get("/cases/case_ev2/bundle", headers=admin_h).json()
        assert bundle["case"]["status"] == CaseStatus.evidence

    def test_add_evidence_to_nonexistent_case_returns_404(self, client, admin_h):
        ev_payload = {
            "id": "ev_x",
            "case_id": "nonexistent",
            "source": "s",
            "source_type": "t",
            "raw_excerpt": "x",
            "evidence_category": "behavioral",
            "reliability_estimate": 0.5,
        }
        resp = client.post("/cases/nonexistent/evidence", json=ev_payload, headers=admin_h)
        assert resp.status_code == 404

    def test_seed_sample_evidence(self, client, admin_h):
        client.post("/cases", json={"id": "case_seed", "title": "T", "context_summary": "C"}, headers=admin_h)
        resp = client.post("/cases/case_seed/seed-sample-evidence", headers=admin_h)
        assert resp.status_code == 200
        assert len(resp.json()) == 4  # make_sample_evidence returns 4 items

    def test_bundle_contains_all_collections(self, client, admin_h):
        client.post("/cases", json={"id": "case_bundle", "title": "T", "context_summary": "C"}, headers=admin_h)
        bundle = client.get("/cases/case_bundle/bundle", headers=admin_h).json()
        for key in ("case", "stakeholders", "evidence", "hypotheses", "interventions", "validations", "audit_logs"):
            assert key in bundle


# ---------------------------------------------------------------------------
# Validation submission
# ---------------------------------------------------------------------------

class TestValidation:
    def test_reviewer_can_submit_validation(self, client, admin_h, reviewer_h):
        client.post("/cases", json={"id": "case_val", "title": "T", "context_summary": "C"}, headers=admin_h)
        val = {
            "id": "val_001",
            "case_id": "case_val",
            "target_type": "hypothesis",
            "target_id": "hyp_001",
            "reviewer": "reviewer@org",
            "action": ValidationAction.approve,
            "rationale": "Hypothesis is well-supported.",
        }
        resp = client.post("/validations", json=val, headers=reviewer_h)
        assert resp.status_code == 200

    def test_approve_moves_case_to_active(self, client, admin_h, reviewer_h):
        client.post("/cases", json={"id": "case_val2", "title": "T", "context_summary": "C"}, headers=admin_h)
        val = {
            "id": "val_002",
            "case_id": "case_val2",
            "target_type": "hypothesis",
            "target_id": "hyp_x",
            "reviewer": "r@r",
            "action": ValidationAction.approve,
            "rationale": "OK",
        }
        client.post("/validations", json=val, headers=reviewer_h)
        bundle = client.get("/cases/case_val2/bundle", headers=admin_h).json()
        assert bundle["case"]["status"] == CaseStatus.active

    def test_practitioner_cannot_submit_validation(self, client, admin_h, practitioner_h):
        client.post("/cases", json={"id": "case_val3", "title": "T", "context_summary": "C"}, headers=admin_h)
        val = {
            "id": "val_003",
            "case_id": "case_val3",
            "target_type": "hypothesis",
            "target_id": "hyp_y",
            "reviewer": "p@p",
            "action": ValidationAction.approve,
            "rationale": "OK",
        }
        resp = client.post("/validations", json=val, headers=practitioner_h)
        assert resp.status_code == 403

    def test_validation_on_missing_case_returns_404(self, client, reviewer_h):
        val = {
            "id": "val_404",
            "case_id": "no_such_case",
            "target_type": "hypothesis",
            "target_id": "hyp_z",
            "reviewer": "r@r",
            "action": ValidationAction.annotate,
            "rationale": "Note",
        }
        resp = client.post("/validations", json=val, headers=reviewer_h)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Bootstrap helper
# ---------------------------------------------------------------------------

class TestBootstrap:
    def test_bootstrap_creates_case_and_stakeholder(self, client, admin_h):
        resp = client.post("/bootstrap-case", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert "case" in data
        assert "stakeholder" in data
        assert data["case"]["title"] == "Cross-functional decision friction"


# ---------------------------------------------------------------------------
# New OD dashboard endpoint tests
# ---------------------------------------------------------------------------

class TestSeedDefaults:
    def test_seed_defaults_populates_registry(self, client, admin_h):
        resp = client.post("/seed-defaults", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 9
        assert "AQAL" in data["seeded"]
        assert "ADKAR" in data["seeded"]
        # Verify they appear in /models
        models_resp = client.get("/models", headers=admin_h)
        assert models_resp.status_code == 200
        names = [m["name"] for m in models_resp.json()]
        for expected in ["AQAL", "Spiral Dynamics", "Theory U", "ADKAR", "Cynefin", "VSM", "Antifragility", "Biomimicry", "Flow"]:
            assert expected in names

    def test_seed_defaults_requires_admin(self, client, practitioner_h):
        resp = client.post("/seed-defaults", headers=practitioner_h)
        assert resp.status_code == 403


class TestGetPatterns:
    def test_get_patterns_returns_empty_list(self, client, admin_h):
        resp = client.get("/patterns", headers=admin_h)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_patterns_returns_saved_pattern(self, client, admin_h):
        pattern = {
            "id": "pat_001",
            "pattern_type": "recurring_tension",
            "pattern_signature": "clarity_ownership_gap",
            "supporting_case_ids": [],
            "associated_lenses": ["AQAL"],
            "confidence": 0.7,
            "outcome_summary": "Observed in 3 similar cases.",
        }
        resp = client.post("/patterns", json=pattern, headers=admin_h)
        assert resp.status_code == 200
        resp2 = client.get("/patterns", headers=admin_h)
        assert len(resp2.json()) == 1
        assert resp2.json()[0]["id"] == "pat_001"


class TestPutCase:
    def test_put_case_updates_domain(self, client, admin_h):
        resp = client.post(
            "/cases",
            json={"id": "case_put1", "title": "T", "context_summary": "C"},
            headers=admin_h,
        )
        assert resp.status_code == 200
        update_resp = client.put(
            "/cases/case_put1",
            json={"domain": "culture", "timeline_weeks": 12},
            headers=admin_h,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["domain"] == "culture"
        assert data["timeline_weeks"] == 12
        # Verify persisted
        get_resp = client.get("/cases", headers=admin_h)
        cases = {c["id"]: c for c in get_resp.json()}
        assert cases["case_put1"]["domain"] == "culture"

    def test_put_case_404_on_missing(self, client, admin_h):
        resp = client.put("/cases/no_such", json={"domain": "x"}, headers=admin_h)
        assert resp.status_code == 404


class TestPerCaseMetrics:
    def test_per_case_metrics_returns_expected_keys(self, client, admin_h):
        client.post(
            "/cases",
            json={"id": "case_metrics1", "title": "M", "context_summary": "MC"},
            headers=admin_h,
        )
        resp = client.get("/cases/case_metrics1/metrics", headers=admin_h)
        assert resp.status_code == 200
        data = resp.json()
        for key in ["case_id", "status", "evidence_count", "hypothesis_count",
                    "intervention_count", "workflow_runs", "policy_violations"]:
            assert key in data

    def test_per_case_metrics_404_on_missing(self, client, admin_h):
        resp = client.get("/cases/no_case_here/metrics", headers=admin_h)
        assert resp.status_code == 404
