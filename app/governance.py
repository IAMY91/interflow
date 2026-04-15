from __future__ import annotations

import json
import logging
from typing import List

from .llm import call_agent, extract_json
from .schemas import Hypothesis, Intervention

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM-based critic prompt
# ---------------------------------------------------------------------------

_CRITIC_PROMPT = """\
You are a governance critic agent for the Interflow platform.

Your job is to review an AI-generated object and flag any policy violations.

POLICY RULES
1. no_essentialization — Do not assign a fixed developmental stage, color, or identity label to any person, team, or group.
2. high_confidence_unsupported — Confidence > 0.70 requires at least 3 supporting evidence items; flag if the statement asserts high certainty without explicit evidence.
3. missing_alternatives — Every hypothesis must acknowledge at least one alternative interpretation; flag if the output presents only one possible explanation as certain.
4. manipulation_language — Flag any framing that coerces, manipulates, shames, or undermines human agency or dignity.
5. pathologizing_language — Flag clinical, derogatory, or reductive characterizations of people or teams.

OBJECT TO REVIEW
{object_json}

OUTPUT SCHEMA (return ONLY valid JSON — no preamble, no explanation)
{{
  "pass": true,
  "violations": []
}}

OR if violations exist:
{{
  "pass": false,
  "violations": [
    {{
      "rule": "<rule name from list above>",
      "severity": "low" | "medium" | "high",
      "excerpt": "<exact text that triggered this violation>",
      "rationale": "<why this is a violation>"
    }}
  ]
}}
"""


def _llm_policy_check(obj_json: str) -> dict:
    """Run LLM critic policy check. Falls back gracefully on error."""
    try:
        prompt = _CRITIC_PROMPT.format(object_json=obj_json)
        response = call_agent(prompt, max_tokens=1000)
        result = extract_json(response)
        if "pass" not in result:
            result["pass"] = len(result.get("violations", [])) == 0
        return result
    except Exception as exc:
        logger.warning("LLM policy check failed (%s) — structural checks only", exc)
        return {"pass": True, "violations": [], "llm_check_skipped": True}


# ---------------------------------------------------------------------------
# Hypothesis policy
# ---------------------------------------------------------------------------

def enforce_hypothesis_policy(h: Hypothesis) -> dict:
    violations: List[dict] = []

    # Structural checks (deterministic)
    if not h.evidence_ids:
        violations.append({
            "rule": "missing_evidence_links",
            "severity": "high",
            "excerpt": h.statement[:120],
            "rationale": "Hypothesis carries no supporting evidence IDs.",
        })

    if h.confidence > 0.8 and len(h.evidence_ids) < 3:
        violations.append({
            "rule": "high_confidence_thin_data",
            "severity": "high",
            "excerpt": f"confidence={h.confidence}, evidence_count={len(h.evidence_ids)}",
            "rationale": "Confidence > 0.80 requires at least 3 evidence items.",
        })

    if not h.alternatives:
        violations.append({
            "rule": "missing_alternatives",
            "severity": "medium",
            "excerpt": h.statement[:120],
            "rationale": "Every hypothesis must include at least one alternative interpretation.",
        })

    # LLM semantic critic
    obj_json = json.dumps({
        "type": "hypothesis",
        "statement": h.statement,
        "confidence": h.confidence,
        "alternatives": h.alternatives,
        "missing_information": h.missing_information,
        "misuse_risks": h.misuse_risks,
    }, ensure_ascii=False)
    llm_result = _llm_policy_check(obj_json)
    violations.extend(llm_result.get("violations", []))

    result: dict = {"pass": len(violations) == 0, "violations": violations}
    if llm_result.get("llm_check_skipped"):
        result["llm_check_skipped"] = True
    return result


# ---------------------------------------------------------------------------
# Intervention policy
# ---------------------------------------------------------------------------

def enforce_intervention_policy(i: Intervention) -> dict:
    violations: List[dict] = []

    # Structural checks (deterministic)
    if not i.success_indicators or not i.failure_indicators:
        violations.append({
            "rule": "missing_outcome_signals",
            "severity": "medium",
            "excerpt": i.title,
            "rationale": "Intervention must specify both success and failure indicators.",
        })

    if "high" in i.risk_profile.lower() and not i.contraindications:
        violations.append({
            "rule": "high_risk_missing_contraindications",
            "severity": "high",
            "excerpt": f"risk_profile={i.risk_profile}",
            "rationale": "High-risk interventions must list contraindications.",
        })

    # LLM semantic critic
    obj_json = json.dumps({
        "type": "intervention",
        "title": i.title,
        "intended_outcome": i.intended_outcome,
        "risk_profile": i.risk_profile,
        "regenerative_impact_notes": i.regenerative_impact_notes,
        "contraindications": i.contraindications,
        "success_indicators": i.success_indicators,
        "failure_indicators": i.failure_indicators,
    }, ensure_ascii=False)
    llm_result = _llm_policy_check(obj_json)
    violations.extend(llm_result.get("violations", []))

    result: dict = {"pass": len(violations) == 0, "violations": violations}
    if llm_result.get("llm_check_skipped"):
        result["llm_check_skipped"] = True
    return result
