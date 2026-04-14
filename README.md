# Interflow Platform Spec (Implementation Baseline)

## 1) Objective

Build a **multi-agent sensemaking and intervention platform** for human, team, organizational, and systemic development that:

- applies multiple interpretive models as **bounded lenses**,
- separates evidence from inference,
- keeps humans in control,
- remains auditable and governable,
- and optimizes for long-term regenerative outcomes, not short-term extraction.

---

## 2) Design assumptions

1. **Models are hypothesis engines, not truth engines.**
2. **No single lens is sufficient** for organizational diagnosis.
3. **Evidence quality varies** and must be represented explicitly.
4. **High-impact outputs require human validation** before action.
5. **Architecture is modular** (new lenses and agents can be added without rewrites).
6. **All outputs are inspectable** (traceable to evidence, assumptions, and alternatives).

---

## 3) Core components

## 3.1 System layers

### A) Execution layer

Purpose: run workflows, tools, retrieval, memory writes.

- Case intake API
- Document/conversation ingestion
- Evidence extraction pipeline
- Agent orchestrator
- Memory + retrieval services
- Intervention tracker

### B) Meaning layer

Purpose: run lens adapters and cross-lens synthesis.

- AQAL adapter
- Spiral Dynamics adapter
- ADKAR adapter
- Theory U adapter
- Cynefin adapter
- VSM adapter
- Antifragility adapter
- Regenerative/Biomimicry adapter
- Flow adapter
- Cross-lens convergence/tension engine

### C) Governance layer

Purpose: policy enforcement and risk control.

- Claim policy engine (observation vs interpretation checks)
- Confidence gate engine
- Human-review router
- Safety filter (anti-stereotyping, anti-pathologizing)
- Audit log writer

## 3.2 Required platform primitives

- `Case`
- `Stakeholder`
- `EvidenceObject`
- `Hypothesis`
- `ModelRegistryEntry`
- `AgentRegistryEntry`
- `Intervention`
- `OutcomeObservation`
- `AuditEvent`
- `HumanValidation`

## 3.3 Component interaction map

1. Intake service creates/updates `Case`.
2. Evidence pipeline writes `EvidenceObject` + provenance.
3. Orchestrator dispatches to lens agents.
4. Agents emit `Hypothesis` objects (with alternatives and uncertainty).
5. Governance validates policy compliance.
6. Synthesis agent emits decision-ready report.
7. Human validators approve/reject/correct.
8. Intervention execution writes outcome telemetry.
9. Calibration service updates confidence history and pattern memory.

---

## 4) Agent specifications (bounded multi-agent council)

## 4.1 Agent registry schema

```json
{
  "agent_name": "aqal_mapping_agent",
  "mandate": "Balance evidence across I/We/It/Its",
  "required_inputs": ["case_id", "evidence_ids"],
  "outputs": ["quadrant_map", "coverage_score", "balancing_questions"],
  "allowed_inferences": ["coverage imbalance", "missing-perspective hypotheses"],
  "forbidden_inferences": ["fixed developmental identity claims"],
  "escalation_conditions": ["coverage_below_threshold", "insufficient_evidence"],
  "handoff_to": ["critic_agent", "synthesis_agent"]
}
```

## 4.2 Default agent set + boundaries

### 1. Intake Agent
- Mandate: capture scope, goals, constraints, stakeholders.
- Must not infer hidden motives from minimal context.
- Escalate when goals conflict across sponsors.

### 2. Evidence Structuring Agent
- Mandate: create atomic evidence records with provenance and reliability estimates.
- Must not convert interpretation into evidence.
- Escalate when source authenticity is uncertain.

### 3. AQAL Mapping Agent
- Mandate: map evidence to I/We/It/Its and score balance.
- Must not assign developmental status.
- Escalate when fewer than 3 quadrants have credible evidence.

### 4. Developmental / Value-Logic Agent
- Mandate: generate cautious value-logic hypotheses.
- Must not label people/teams as fixed stages/colors.
- Escalate when evidence is mainly anecdotal self-report.

### 5. Systems Mapping Agent
- Mandate: map incentives, structures, dependencies, feedback loops.
- Must not reduce systemic issues to individual psychology.
- Escalate when structural data is missing.

### 6. Process Guidance Agent
- Mandate: sequence change process via ADKAR/Theory U/Cynefin context.
- Must not impose single-process dogma.
- Escalate when context classification confidence is low.

### 7. Intervention Design Agent
- Mandate: generate options across person/relationship/team/workflow/structure/governance.
- Must not recommend manipulative interventions.
- Escalate when high-impact interventions lack safeguards.

### 8. Governance / Ethics Agent
- Mandate: enforce policy, dignity, consent, and regenerative constraints.
- Must not allow high-confidence claims from thin data.
- Escalate when stakeholder harm risk is medium/high.

### 9. Critic / Red-Team Agent
- Mandate: challenge weak evidence, overreach, hidden assumptions, and model misuse.
- Must not suppress viable alternatives.
- Escalate when unresolved contradictions remain.

### 10. Synthesis Agent
- Mandate: produce final report with convergence, disagreement, uncertainty, and next actions.
- Must not collapse uncertainty into false consensus.
- Escalate when human validation is mandatory.

---

## 5) Workflow (stateful, auditable)

## 5.1 Case lifecycle states

`draft -> intake_validated -> evidence_structured -> lens_hypothesized -> governance_checked -> human_review -> intervention_active -> outcome_observed -> closed_or_iterating`

## 5.2 Orchestration steps

1. **Intake checkpoint**
   - Required: case context, goals, stakeholder map.
   - Write: `Case`, `Stakeholder`.

2. **Evidence checkpoint**
   - Required: source metadata and provenance completeness.
   - Write: `EvidenceObject`.

3. **Lens hypothesis checkpoint**
   - Required: each hypothesis links evidence IDs and alternatives.
   - Write: `Hypothesis`.

4. **Cross-lens synthesis checkpoint**
   - Required: convergence + disagreement + missing-data report.

5. **Governance checkpoint**
   - Required: policy pass + confidence thresholds + risk gate.
   - Write: `AuditEvent`.

6. **Human validation checkpoint (mandatory for high-impact)**
   - Actions: approve, reject, annotate, request more data.
   - Write: `HumanValidation`.

7. **Intervention and outcome checkpoint**
   - Write: `Intervention`, `OutcomeObservation`.

8. **Learning checkpoint**
   - Recalibrate confidence and update analogous-case retrieval indexes.

---

## 6) Schemas (evidence/inference separation by design)

## 6.1 EvidenceObject

```json
{
  "id": "ev_001",
  "case_id": "case_001",
  "source": "interview_transcript_07",
  "source_type": "interview",
  "timestamp": "2026-04-14T00:00:00Z",
  "raw_excerpt": "We keep revisiting decisions after meetings.",
  "summary": "Recurring decision reversals reported",
  "evidence_category": "behavioral_observation",
  "stakeholder_reference": ["st_3"],
  "provenance": {
    "collector": "evidence_structuring_agent",
    "location_ref": "transcript_07:112-120"
  },
  "reliability_estimate": 0.72,
  "tags": ["decision-making", "rework"],
  "is_interpretation": false
}
```

## 6.2 Hypothesis

```json
{
  "id": "hyp_014",
  "case_id": "case_001",
  "hypothesis_statement": "Evidence may indicate a structural decision-rights ambiguity, not only interpersonal misalignment.",
  "model_source": ["VSM", "AQAL", "Cynefin"],
  "evidence_ids": ["ev_001", "ev_015", "ev_044"],
  "confidence": 0.63,
  "alternative_explanations": [
    "Temporary resource bottleneck",
    "Unclear meeting facilitation norms"
  ],
  "missing_information": ["formal decision policy", "RACI clarity by function"],
  "human_validation_status": "required",
  "risk_notes": ["overgeneralization_risk_medium"]
}
```

## 6.3 ModelRegistryEntry

```json
{
  "model_name": "Spiral Dynamics",
  "model_type": "value_logic_lens",
  "purpose": "Hypothesize contextual motivational patterns for communication/intervention matching",
  "valid_use_cases": ["stakeholder translation", "resistance interpretation"],
  "invalid_use_cases": ["fixed color labels", "status ranking"],
  "minimum_evidence_requirements": {
    "min_evidence_objects": 6,
    "required_source_diversity": 2
  },
  "known_failure_modes": ["stereotyping", "thin-data stage inference"],
  "ethical_risks": ["identity essentialization"],
  "output_template": [
    "possible_dominant_logic",
    "possible_secondary_logic",
    "confidence",
    "alternatives",
    "missing_data"
  ],
  "review_requirements": ["human_review_if_stakeholder_sensitive"]
}
```

## 6.4 Intervention

```json
{
  "id": "int_021",
  "title": "Decision-rights clarity workshop",
  "target_level": ["team", "workflow", "governance"],
  "intended_outcome": "Reduce decision churn and escalation lag",
  "supporting_models": ["VSM", "ADKAR", "AQAL"],
  "prerequisites": ["cross-functional participation", "sponsor backing"],
  "risks": ["defensiveness", "surface compliance"],
  "contraindications": ["active trust breakdown without facilitation support"],
  "success_signals": ["fewer reopened decisions", "faster decision cycle time"],
  "failure_signals": ["meeting inflation", "informal shadow decisions"],
  "regenerative_assessment": {
    "trust": 0.76,
    "capability_growth": 0.82,
    "resilience": 0.69,
    "extractive_risk": 0.19
  }
}
```

## 6.5 Case

```json
{
  "id": "case_001",
  "title": "Cross-functional execution friction",
  "context_summary": "Product and operations teams report recurring decision reversals",
  "goals": ["stabilize decision flow", "increase accountability clarity"],
  "stakeholders": ["st_1", "st_2", "st_3"],
  "active_tensions": ["speed_vs_alignment", "autonomy_vs_standardization"],
  "evidence_ids": ["ev_001", "ev_015"],
  "hypothesis_ids": ["hyp_014"],
  "interventions_applied": ["int_021"],
  "outcomes": ["out_002"],
  "unresolved_questions": ["policy authority boundary"],
  "status": "intervention_active"
}
```

---

## 7) Model integration guardrails (good use vs misuse)

| Model | Good for | Bad for | Minimum evidence | Human review trigger |
|---|---|---|---|---|
| AQAL | Evidence balancing, blind-spot detection | Spiritual/developmental ranking | 3+ quadrants represented | Any identity-adjacent interpretation |
| Spiral Dynamics | Value-logic hypotheses, communication adaptation | Fixed color labels, superiority claims | Multi-source behavior + language data | Stakeholder-sensitive framing |
| Theory U | Process design for sensing/emergence | Mystical certainty claims | Process observations across phases | Strategic intervention recommendation |
| ADKAR | Adoption sequence diagnosis | Reducing all change to individual gaps | Role-based adoption evidence | Performance-impacting interventions |
| Cynefin | Context classification for intervention style | Hard certainty in ambiguous contexts | Context signals + uncertainty score | Low-confidence classification |
| VSM | Structural viability mapping | Non-actionable abstraction | Org design + feedback loop evidence | Governance redesign outputs |
| Antifragility | Safe-to-fail experiment design | Unbounded stress exposure | Risk envelope + reversibility | High downside experiments |
| Biomimicry/Regenerative | Long-term vitality checks | Vague nature rhetoric | Vitality indicators over time | Tradeoff against short-term KPIs |
| Flow | Challenge-skill and energy design | Manipulative optimization | Workload + capability + recovery data | Anything affecting wellbeing risk |

---

## 8) Governance rules (enforced)

## 8.1 Required output sections

Every synthesis/report must include:
1. Situation summary
2. Evidence observed
3. Interpretations by lens
4. Convergence across lenses
5. Tensions/disagreements across lenses
6. Missing information
7. Confidence and uncertainty
8. Recommended interventions
9. Risks and ethical cautions
10. Regenerative assessment
11. Questions for human validation

## 8.2 Prohibited claims

- Fixed stage/color labeling of persons or teams.
- Claims of human superiority/inferiority from developmental models.
- Clinical/psychiatric claims outside explicit governed scope.
- High-certainty recommendations with insufficient evidence.

## 8.3 Audit log minimum fields

```json
{
  "audit_id": "aud_009",
  "case_id": "case_001",
  "timestamp": "2026-04-14T00:00:00Z",
  "models_used": ["AQAL", "VSM", "Cynefin"],
  "model_selection_rationale": "Need evidence balancing + structural diagnosis + complexity framing",
  "evidence_ids_considered": ["ev_001", "ev_015", "ev_044"],
  "assumptions": ["self-reports may understate structural constraints"],
  "alternatives_considered": ["norm conflict", "capacity bottleneck"],
  "human_validations_requested": ["hv_002"],
  "governance_checks": {
    "claim_policy": "pass",
    "confidence_gate": "pass_with_caveat",
    "safety_filter": "pass"
  }
}
```

---

## 9) Failure modes and mitigations

1. **Lens monoculture**
   - Risk: one model dominates interpretation.
   - Mitigation: enforce minimum 2-lens synthesis + critic check.

2. **Thin-data overreach**
   - Risk: strong claims from sparse evidence.
   - Mitigation: confidence caps and mandatory missing-data section.

3. **Stereotyping/essentializing**
   - Risk: identity-level developmental labels.
   - Mitigation: prohibited phrase filter + governance block + human review.

4. **Intervention theatre**
   - Risk: ritual activity without systemic shift.
   - Mitigation: require measurable success/failure signals per intervention.

5. **Short-term optimization harm**
   - Risk: output gains while trust/resilience degrade.
   - Mitigation: regenerative scorecard and delayed-effect monitoring.

6. **Audit opacity**
   - Risk: cannot reconstruct rationale.
   - Mitigation: immutable audit events linked to evidence and hypotheses.

---

## 10) Evaluation criteria

## 10.1 Product/system metrics

- Evidence/inference separation accuracy
- Traceability completeness (claim -> evidence -> model -> decision)
- Multi-lens utility (did additional lenses change decision quality?)
- Governance compliance rate
- Human-override quality and frequency
- Intervention relevance score
- Regenerative outcome index (trust, capability, resilience)

## 10.2 Safety metrics

- Unsupported high-confidence claim rate
- Stereotyping incident rate
- High-impact action without human review rate
- Policy-block bypass attempts

## 10.3 User value metrics

- Practitioner-rated usefulness
- Time-to-actionable-insight
- Intervention adoption and completion quality

---

## 11) Recommended next build step (2-week sprint)

### Sprint goal
Deliver a minimal, governed multi-agent pipeline that can process one real case end-to-end.

### Scope
1. Implement core objects (`Case`, `EvidenceObject`, `Hypothesis`, `Intervention`, `AuditEvent`).
2. Implement 5 agents first: Intake, Evidence Structuring, AQAL, Critic, Synthesis.
3. Add governance gates: claim policy + confidence gate + mandatory human review for high-impact outputs.
4. Implement report renderer with required 11 output sections.
5. Capture one intervention and one outcome observation.

### Done criteria
- End-to-end run succeeds on a sample case.
- Every recommendation is traceable to evidence IDs.
- Governance gate blocks at least one intentionally unsafe test case.
- Human validation actions are recorded and auditable.

---

## Appendix A: Agent prompt contract (template)

```text
You are {agent_name} in the Interflow platform.

ROLE
- {mandate}

INPUTS
- {required_inputs}

OPERATING RULES
1) Separate raw evidence from interpretation.
2) Treat model outputs as hypotheses, not facts.
3) Include confidence, alternatives, missing information, and risk notes.
4) Never produce fixed developmental/stage/color identity labels.
5) Escalate if evidence is below threshold or harm risk is elevated.

OUTPUT
- Return JSON matching {output_schema}.
- Include `evidence_ids` for every claim.
```

## Appendix B: Synthesis output contract (JSON skeleton)

```json
{
  "situation_summary": "",
  "evidence_observed": [],
  "interpretations_by_lens": [],
  "convergence": [],
  "disagreements": [],
  "missing_information": [],
  "confidence_and_uncertainty": {
    "overall_confidence": 0.0,
    "uncertainty_notes": []
  },
  "recommended_interventions": [],
  "risks_and_ethical_cautions": [],
  "regenerative_assessment": {},
  "questions_for_human_validation": []
}
```
