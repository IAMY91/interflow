# Interflow Platform Specification (Build-Ready v1)

This document is a **development-ready system specification** for building Interflow: a multi-agent, multi-lens platform for organizational and systemic sensemaking, intervention design, and outcome learning.

---

## 1) Platform Overview

Interflow is a human-in-the-loop AI platform that helps practitioners diagnose situations, compare interpretations across multiple lenses, design interventions, and learn from outcomes.

### Primary use cases

- Organizational diagnosis
- Change management copilot
- Stakeholder and team sensemaking
- Workshop/facilitation design support
- Leadership and capability development support
- Intervention sequencing and governance design
- Regenerative transformation planning
- Cross-case pattern learning

### Core platform outcomes

- Better decisions through plural interpretation
- Fewer one-dimensional diagnoses
- Strong evidence-to-recommendation traceability
- Safer, auditable model usage
- Higher long-term trust, resilience, and capability

---

## 2) Design Principles

1. **Evidence before interpretation**: observations and interpretations are separate objects.
2. **Lenses, not truth**: AQAL/Spiral/etc. are hypothesis aids, never absolute reality.
3. **No essentializing**: no fixed identity labeling for people/teams.
4. **Explicit uncertainty**: confidence, alternatives, and missing data are mandatory.
5. **Human agency preserved**: validate, override, annotate, reinterpret.
6. **Regenerative preference**: favor long-term vitality over short-term extraction.
7. **Audit by default**: every claim must be inspectable and reproducible.
8. **Modular architecture**: models, agents, and workflows are extensible.
9. **Bounded automation**: high-impact outputs require human review.
10. **Practicality over ideology**: operational schemas and workflows first.

---

## 3) System Architecture

Interflow uses four layers with explicit boundaries.

## 3.1 Layer map

### A) Execution Layer

**Purpose**: data ingestion, orchestration, storage, retrieval, APIs, integrations.

**Services**
- Case API Service
- Ingestion Service (docs/chats/surveys/metrics)
- Evidence Processing Service
- Agent Orchestrator
- Memory Store + Retrieval Service
- Intervention Tracking Service
- Notification/Task Service

### B) Meaning Layer

**Purpose**: lens application, model policies, synthesis, and confidence logic.

**Services**
- Model Registry Service
- Lens Adapter Runtime (AQAL, Spiral, Theory U, ADKAR, Cynefin, VSM, Antifragility, Biomimicry, Flow)
- Cross-Lens Synthesis Service
- Bias & Blind-Spot Checker
- Confidence Calibration Service

### C) Governance Layer

**Purpose**: policy enforcement, access control, review thresholds, audit.

**Services**
- Policy Engine
- Prohibited Claim Filter
- Human Review Gate Service
- Consent & Access Control Service
- Audit Log Service

### D) Experience Layer

**Purpose**: practitioner-facing product interfaces.

**Modules**
- Case Dashboard
- Evidence Explorer
- Multi-Lens Interpretation Workspace
- Intervention Studio
- Validation Panel
- Governance/Audit Console
- Pattern Retrieval & Comparison View

## 3.2 Service boundaries

- Execution layer **cannot** make normative claims.
- Meaning layer **cannot** bypass governance policy.
- Governance layer **cannot** mutate source evidence.
- Experience layer must expose provenance and alternatives for every recommendation.

## 3.3 Suggested technical stack (reference)

- API: GraphQL/REST gateway
- Orchestration: event-driven workflow engine
- Storage: relational DB + vector index + object store
- Policy: declarative rules engine
- Audit: append-only event store
- UI: React-based modular workspace

---

## 4) Agent Architecture

Interflow is a bounded multi-agent council.

## 4.1 Agent registry entry (canonical)

```json
{
  "agent_id": "aqal_mapping_agent",
  "mission": "Balance evidence across AQAL quadrants and detect blind spots",
  "inputs": ["case_id", "evidence_ids"],
  "outputs": ["quadrant_map", "coverage_report", "balancing_questions"],
  "allowable_inference_scope": ["coverage imbalance", "missing-perspective hypotheses"],
  "prohibited_behaviors": ["fixed identity developmental claims"],
  "escalation_rules": ["quadrant_coverage_below_threshold"],
  "handoff_conditions": ["to_critic_on_low_evidence", "to_synthesis_on_policy_pass"],
  "logging_requirements": ["input_ids", "output_ids", "confidence", "policy_checks"],
  "evaluation_criteria": ["coverage_accuracy", "question_quality", "policy_compliance"]
}
```

## 4.2 Required agents

### 1) Intake Agent
- Mission: structure case objective, scope, stakeholders, constraints.
- Inputs: intake form, sponsor brief.
- Outputs: draft `Case`, `Stakeholder` map, scope statement.
- Allowed inferences: objective ambiguity detection.
- Prohibited: psychologizing stakeholders.
- Escalation: conflicting goals or missing decision owner.
- Handoff: Evidence Structuring Agent.
- Logging: assumptions and unresolved questions.
- Evaluation: intake completeness and clarity.

### 2) Evidence Structuring Agent
- Mission: convert raw sources into atomic evidence with provenance.
- Inputs: transcripts, notes, docs, metrics.
- Outputs: `EvidenceObject[]` with reliability estimates.
- Allowed inferences: evidence category suggestion only.
- Prohibited: recommendations or stakeholder labeling.
- Escalation: low source reliability / missing provenance.
- Handoff: AQAL + Systems + Value-Logic agents.
- Logging: extraction method and confidence.
- Evaluation: precision/recall on evidence extraction.

### 3) AQAL Mapping Agent
- Mission: map evidence to I/We/It/Its; detect imbalance.
- Inputs: evidence objects.
- Outputs: quadrant coverage map + balancing questions.
- Allowed inferences: perspective blind-spot hypotheses.
- Prohibited: metaphysical/spiritual status inference.
- Escalation: <3 quadrants represented.
- Handoff: Critic Agent + Synthesis Agent.
- Logging: mapping rationale and uncertain mappings.
- Evaluation: mapping consistency and usefulness.

### 4) Developmental / Value-Logic Agent
- Mission: generate context-dependent value-logic hypotheses.
- Inputs: stakeholder statements + behavior evidence.
- Outputs: value-tension hypotheses + communication adaptation notes.
- Allowed inferences: likely contextual motivational patterns.
- Prohibited: fixed color/stage assignment.
- Escalation: sparse/mono-source evidence.
- Handoff: Process Guidance + Intervention Design.
- Logging: alternatives and stereotype-risk flags.
- Evaluation: communication fit and overreach rate.

### 5) Systems Mapping Agent
- Mission: map structure, incentives, dependencies, loops.
- Inputs: org artifacts, process metrics, governance docs.
- Outputs: system map + bottlenecks + leverage points.
- Allowed inferences: structural tension hypotheses.
- Prohibited: reducing all causes to individuals.
- Escalation: missing org structure data.
- Handoff: Process Guidance + Intervention Design.
- Logging: source links for each structural claim.
- Evaluation: actionability and accuracy of map.

### 6) Process Guidance Agent
- Mission: sequence change steps (ADKAR/Theory U/Cynefin).
- Inputs: hypotheses + system map + case goals.
- Outputs: staged process plan + checkpoints.
- Allowed inferences: process-stage fit hypotheses.
- Prohibited: one-model absolutism.
- Escalation: low context classification confidence.
- Handoff: Intervention Design Agent.
- Logging: model choice rationale.
- Evaluation: adoption flow quality.

### 7) Intervention Design Agent
- Mission: generate intervention options across levels.
- Inputs: synthesis bundle + process plan.
- Outputs: `Intervention[]` with risks/contraindications.
- Allowed inferences: intervention-mechanism hypotheses.
- Prohibited: covert manipulation tactics.
- Escalation: high-risk interventions lacking mitigation.
- Handoff: Regenerative Governance Agent.
- Logging: evidence basis per intervention.
- Evaluation: intervention relevance and feasibility.

### 8) Regenerative Governance Agent
- Mission: evaluate long-term vitality, trust, resilience, agency impacts.
- Inputs: intervention candidates + risk data.
- Outputs: regenerative score + constraints + review requirement.
- Allowed inferences: long-horizon risk/benefit hypotheses.
- Prohibited: optimizing only short-term KPI gains.
- Escalation: high extractive risk.
- Handoff: Critic Agent + Human Validation.
- Logging: tradeoff rationale.
- Evaluation: post-implementation vitality outcomes.

### 9) Critic / Red-Team Agent
- Mission: challenge overreach, thin-data certainty, hidden assumptions.
- Inputs: all hypotheses and interventions.
- Outputs: critique report + failure-mode flags.
- Allowed inferences: logical inconsistency detection.
- Prohibited: replacing synthesis with a single preferred worldview.
- Escalation: unresolved high-impact contradictions.
- Handoff: Synthesis Agent.
- Logging: rejected and retained alternatives.
- Evaluation: reduction in bad decisions.

### 10) Synthesis Agent
- Mission: produce integrated recommendation package.
- Inputs: validated outputs from all prior agents.
- Outputs: final report with convergence/disagreement/uncertainty.
- Allowed inferences: best-current interpretation with alternatives visible.
- Prohibited: false consensus or certainty inflation.
- Escalation: mandatory human review trigger.
- Handoff: Practitioner UI + memory write-back.
- Logging: final claim-to-evidence map.
- Evaluation: practitioner usefulness and trust.

---

## 5) Model Registry Design

## 5.1 Registry schema

```json
{
  "name": "AQAL",
  "category": "evidence_balancing_lens",
  "purpose": "Detect quadrant blind spots and improve diagnostic completeness",
  "allowed_uses": ["evidence bucketing", "question generation", "coverage scoring"],
  "disallowed_uses": ["spiritual ranking", "identity labeling"],
  "minimum_evidence_requirements": {
    "min_items": 6,
    "min_sources": 2
  },
  "typical_inputs": ["evidence_objects", "stakeholder_notes"],
  "output_schema": ["quadrant_map", "coverage", "missing_quadrants", "balancing_questions"],
  "confidence_rules": ["cap_confidence_if_lt_3_quadrants"],
  "known_failure_modes": ["subjective_overweight"],
  "ethical_risks": ["developmental_reification"],
  "human_review_requirements": ["required_if_used_for_people_decisions"],
  "compatible_companion_models": ["VSM", "Cynefin"],
  "risky_combinations": ["AQAL_plus_fixed_stage_classifier"]
}
```

## 5.2 Required model entries (operational roles)

### AQAL / Integral
- Role: evidence balancing, blind-spot detection.
- Allowed: I/We/It/Its evidence completeness checks.
- Disallowed: metaphysical/developmental status claims.

### Spiral Dynamics
- Role: value-logic hypothesis + communication adaptation.
- Allowed: contextual motivational pattern hypotheses.
- Disallowed: fixed color labeling, ranking worth.

### Theory U
- Role: sensing/emergence process guidance.
- Allowed: process-stage intervention design.
- Disallowed: unverifiable certainty claims.

### ADKAR
- Role: adoption sequencing lens.
- Allowed: identify missing adoption elements.
- Disallowed: reducing all change complexity to ADKAR alone.

### Cynefin
- Role: context classification for decision style.
- Allowed: classify with uncertainty bands.
- Disallowed: overconfident category assignment from sparse evidence.

### Viable System Model (VSM)
- Role: viability and coordination diagnostics.
- Allowed: map control/intelligence/policy functions.
- Disallowed: theory-only outputs without actionable mappings.

### Antifragility
- Role: fragility/resilience and safe-to-fail design.
- Allowed: reversible experiment portfolio design.
- Disallowed: unmanaged stress exposure.

### Biomimicry / Regenerative
- Role: vitality and reciprocity assessment.
- Allowed: long-term ecological/systemic impact checks.
- Disallowed: non-operational rhetoric.

### Flow models
- Role: challenge-skill-energy-recovery design.
- Allowed: workload and attention balance interventions.
- Disallowed: manipulative state optimization.

---

## 6) Core Schemas

All schemas include provenance, confidence, and review fields where applicable.

## 6.1 Case

**Purpose**: anchor object for all analysis and interventions.

**Core fields**
- `id`, `title`, `context_summary`, `goals`, `status`
- `stakeholder_ids[]`, `evidence_ids[]`, `hypothesis_ids[]`, `intervention_ids[]`

**Optional fields**
- `constraints[]`, `timeline`, `sponsor`, `domain`, `sensitivity_level`

**Relationships**
- one-to-many with Evidence/Hypothesis/Intervention/Validation/Audit

**Confidence handling**
- `case_confidence_overview` derived from hypothesis confidence distribution

**Review fields**
- `requires_human_review`, `review_reason`

## 6.2 Stakeholder

**Purpose**: represent stakeholder context without essentialized identity claims.

**Core fields**
- `id`, `case_id`, `role`, `relationship_context`, `stated_goals[]`

**Optional fields**
- `communication_preferences`, `constraints`, `consent_flags`

**Relationships**
- links to Evidence and Hypothesis references

**Provenance handling**
- every stakeholder claim links back to evidence IDs

**Review fields**
- `sensitivity_tag`, `human_review_required`

## 6.3 EvidenceObject

**Purpose**: atomic observation unit.

**Core fields**
- `id`, `case_id`, `source`, `source_type`, `timestamp`, `raw_excerpt`
- `evidence_category`, `provenance`, `reliability_estimate`

**Optional fields**
- `summary`, `tags[]`, `aqal_quadrant_hint`

**Relationships**
- referenced by Hypothesis, Validation, Audit

**Confidence handling**
- `reliability_estimate` and `source_quality_notes`

**Review fields**
- `is_contested`, `contested_by`

## 6.4 HypothesisObject

**Purpose**: model-generated interpretation with alternatives.

**Core fields**
- `id`, `case_id`, `hypothesis_statement`, `model_sources[]`, `evidence_ids[]`
- `confidence`, `alternative_explanations[]`, `missing_information[]`

**Optional fields**
- `misuse_risks[]`, `bias_notes[]`, `recommended_questions[]`

**Relationships**
- parented to Case; sourced from Evidence; informs Intervention

**Review fields**
- `human_validation_status`, `review_required_reason`

## 6.5 ModelRegistryEntry

**Purpose**: govern model usage boundaries.

**Core fields**
- `name`, `category`, `purpose`, `allowed_uses[]`, `disallowed_uses[]`
- `min_evidence_requirements`, `output_schema`, `confidence_rules[]`

**Optional fields**
- `failure_modes[]`, `ethical_risks[]`, `companion_models[]`, `risky_combinations[]`

**Review fields**
- `review_thresholds`, `approval_roles[]`

## 6.6 AgentRegistryEntry

**Purpose**: define agent contract and behavior limits.

**Core fields**
- `agent_id`, `mission`, `inputs[]`, `outputs[]`
- `allowable_inference_scope[]`, `prohibited_behaviors[]`
- `escalation_rules[]`, `handoff_conditions[]`

**Optional fields**
- `model_dependencies[]`, `runtime_constraints[]`

**Logging fields**
- `required_log_fields[]`

## 6.7 InterventionObject

**Purpose**: actionable option with safeguards.

**Core fields**
- `id`, `title`, `target_level[]`, `intended_outcome`
- `supporting_models[]`, `prerequisites[]`, `contraindications[]`
- `risk_profile`, `evidence_threshold`, `success_indicators[]`, `failure_indicators[]`

**Optional fields**
- `owner_role`, `effort_estimate`, `time_horizon`

**Regenerative fields**
- `regenerative_impact_notes`, `trust_impact`, `resilience_impact`, `capability_distribution_impact`

**Review fields**
- `requires_human_approval`, `approval_status`

## 6.8 ValidationRecord

**Purpose**: capture human review actions.

**Core fields**
- `id`, `case_id`, `reviewer_id`, `target_object_type`, `target_object_id`
- `action` (`approve|reject|annotate|request_more_data|override`)
- `rationale`, `timestamp`

**Optional fields**
- `conditions_for_approval[]`, `follow_up_tasks[]`

## 6.9 AuditLogEvent

**Purpose**: immutable governance trace.

**Core fields**
- `id`, `case_id`, `actor_type`, `actor_id`, `action`, `timestamp`
- `models_used[]`, `evidence_ids[]`, `assumptions[]`, `alternatives_considered[]`

**Optional fields**
- `policy_results`, `risk_flags`, `human_review_refs[]`

## 6.10 PatternMemoryRecord

**Purpose**: cross-case learning object.

**Core fields**
- `id`, `pattern_type`, `pattern_signature`, `supporting_case_ids[]`
- `associated_lenses[]`, `confidence`, `outcome_summary`

**Optional fields**
- `context_constraints[]`, `known_counterexamples[]`

**Governance fields**
- `applicability_warnings[]`, `last_revalidated_at`

---

## 7) Workflow Design (End-to-End)

## 7.1 Stage table

| Stage | Objective | Inputs | Outputs | Agent | Validation checkpoint | Typical failure modes |
|---|---|---|---|---|---|---|
| Intake | Define case scope and goals | Intake brief, sponsor notes | Case draft, stakeholder map | Intake | Scope completeness check | Goal ambiguity, missing stakeholders |
| Evidence ingestion | Gather raw sources | Docs/chats/surveys/metrics | Raw corpus | Execution services | Source integrity check | Missing/biased sources |
| Evidence structuring | Atomic evidence with provenance | Raw corpus | Evidence objects | Evidence Structuring | Provenance + reliability check | Interpretation leakage |
| Lens selection | Choose relevant lenses | Case goals + evidence profile | Lens plan | Orchestrator + Meaning layer | Policy compatibility check | Lens monoculture |
| Multi-lens interpretation | Generate bounded hypotheses | Evidence objects | Hypothesis set | AQAL/Value/Systems/Process agents | Confidence + alternatives check | Overclaiming |
| Cross-lens synthesis | Convergence and tensions | Hypothesis set | Synthesis draft | Synthesis Agent | Disagreement visibility check | False consensus |
| Intervention generation | Produce options | Synthesis draft | Intervention set | Intervention Agent | Contraindications check | Intervention theatre |
| Governance review | Policy and safety enforcement | Interventions + hypotheses | Approved/rejected set | Governance + Red-team | High-impact human-review gate | Unreviewed risky action |
| Human validation | Human judgment decisions | Approved set | Validation records | Human reviewers | Required approval states | Rubber-stamping |
| Final output | Deliver actionable package | Validated artifacts | Final recommendation | Synthesis Agent | Completeness check (11 sections) | Missing uncertainty |
| Memory write-back | Learn from run | Final artifacts | Memory records | Execution services | Traceability check | Incomplete audit links |
| Outcome tracking | Measure intervention effects | Intervention telemetry | Outcome observations | Tracking service + analysts | Outcome quality check | No longitudinal follow-up |

## 7.2 Required final output sections (enforced)

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

---

## 8) Intervention Engine Design

## 8.1 Intervention library taxonomy

- Self / individual
- Relationship
- Team
- Workflow
- Structural
- Governance
- Cultural
- Ecosystem

## 8.2 Intervention entry template

```json
{
  "title": "Decision-rights clarity workshop",
  "intended_outcome": "Reduce decision churn and escalation lag",
  "target_level": ["team", "workflow", "governance"],
  "supported_by_models": ["VSM", "ADKAR", "AQAL"],
  "prerequisites": ["cross-functional participation", "sponsor support"],
  "contraindications": ["active trust collapse without facilitation support"],
  "risk_profile": "medium",
  "evidence_threshold": {
    "min_evidence_objects": 8,
    "min_source_diversity": 2
  },
  "success_indicators": ["fewer reopened decisions", "faster decision cycle"],
  "failure_indicators": ["shadow decisions", "meeting inflation"],
  "regenerative_impact_notes": "Expected increase in distributed clarity and accountability"
}
```

## 8.3 Ranking logic (multi-objective)

Interventions are ranked by weighted score:

`score = (impact * 0.30) + (feasibility * 0.20) + (evidence_strength * 0.20) + (regenerative_fit * 0.20) - (risk * 0.10)`

Hard gates:
- block if contraindication is true
- block if human approval required and missing
- block if confidence below policy threshold for target level

---

## 9) Memory and Retrieval Design

## 9.1 Memory layers

1. **Session memory**: current interaction context
2. **Case memory**: all objects for one case
3. **Organizational memory**: aggregate trends and baseline patterns
4. **Pattern memory**: reusable cross-case signatures
5. **Intervention-outcome memory**: effectiveness and side effects over time
6. **Governance/audit memory**: immutable policy and decision history

## 9.2 Retrieval indices

- By similar case profile
- By lens signature (AQAL imbalance pattern, value-tension type)
- By stakeholder pattern hypotheses
- By structural tension (e.g., unclear decision rights)
- By confidence band
- By regenerative risk profile
- By intervention success/failure pattern

## 9.3 Retrieval query contract (example)

```json
{
  "query_type": "analogous_cases",
  "filters": {
    "lenses": ["VSM", "AQAL"],
    "tensions": ["autonomy_vs_alignment"],
    "confidence_min": 0.55,
    "regenerative_risk_max": 0.35
  },
  "limit": 10
}
```

---

## 10) Governance and Audit Design

## 10.1 Policy rules

- No fixed developmental identity claims.
- No high-certainty claims from thin data.
- No pseudo-clinical diagnosis outside approved scope.
- No hidden model usage (must be declared in output).
- No unreviewed high-impact recommendations.

## 10.2 Review thresholds

Human review is mandatory when:
- stakeholder profiling could affect status/opportunity,
- recommendation affects governance structure,
- confidence < threshold but action impact is high,
- sensitive personal data was used,
- red-team flags unresolved risk.

## 10.3 Red-flag triggers

- stage/color essentialization language
- unsupported confidence > 0.8
- missing alternatives in hypothesis output
- missing provenance for key claims
- intervention with high downside and low reversibility

## 10.4 Model usage restrictions

- AQAL disallowed for ranking personal worth.
- Spiral disallowed for fixed labels.
- Theory U disallowed for unverifiable certainty claims.
- Flow disallowed for manipulative wellbeing tradeoffs.

## 10.5 RBAC and consent considerations

- Roles: practitioner, reviewer, admin, auditor.
- Sensitive stakeholder data visible only to authorized roles.
- Consent flags required for personal data ingestion where applicable.
- Audit export restricted to auditor/admin with immutable references.

## 10.6 Audit event minimum

```json
{
  "event_id": "aud_101",
  "case_id": "case_44",
  "actor_type": "agent",
  "actor_id": "synthesis_agent",
  "models_used": ["AQAL", "VSM", "Cynefin"],
  "evidence_ids": ["ev_12", "ev_19"],
  "assumptions": ["survey response bias possible"],
  "alternatives_considered": ["capacity bottleneck"],
  "policy_results": {
    "claim_policy": "pass",
    "certainty_policy": "pass_with_caveat",
    "review_gate": "human_review_required"
  },
  "timestamp": "2026-04-14T00:00:00Z"
}
```

---

## 11) UX / Product Modules

## 11.1 Case Dashboard
- User goal: understand current state quickly.
- Displays: case status, active tensions, pending reviews.
- Actions: update scope, assign reviewers, launch workflow.
- Traceability: quick links to evidence and audit.

## 11.2 Evidence Explorer
- User goal: inspect source quality and provenance.
- Displays: evidence list, source metadata, reliability.
- Actions: annotate evidence, mark contested items.
- Traceability: source-to-claim links.

## 11.3 AQAL Quadrant Map
- User goal: detect perspective imbalance.
- Displays: I/We/It/Its coverage and gaps.
- Actions: request balancing questions.
- Traceability: each bucket links to evidence IDs.

## 11.4 Stakeholder / Value-Tension Map
- User goal: compare contextual value hypotheses.
- Displays: possible dominant/secondary logics and tensions.
- Actions: test communication framing variants.
- Traceability: hypotheses with alternatives and confidence.

## 11.5 Systems Map View
- User goal: identify leverage points and bottlenecks.
- Displays: loops, dependencies, incentives, governance nodes.
- Actions: annotate structural constraints.
- Traceability: each node tied to evidence.

## 11.6 Intervention Studio
- User goal: design and compare interventions.
- Displays: intervention cards, risk/regenerative scores.
- Actions: select, sequence, assign owners.
- Approvals: send high-impact interventions for review.

## 11.7 Uncertainty / Confidence Panel
- User goal: understand confidence boundaries.
- Displays: confidence by hypothesis, missing data, alternatives.
- Actions: request additional evidence collection.

## 11.8 Governance & Audit Console
- User goal: verify policy compliance.
- Displays: policy results, flags, review history.
- Actions: approve/reject/override with rationale.

## 11.9 Human Validation Panel
- User goal: perform formal review actions.
- Displays: pending validation items with context.
- Actions: approve, reject, annotate, request revisions.

## 11.10 Case Comparison / Pattern Retrieval
- User goal: reuse learning from analogous cases.
- Displays: similar cases, interventions, outcomes.
- Actions: import candidate interventions with warnings.

---

## 12) Evaluation Framework

## 12.1 Offline evaluation

- Evidence extraction quality (precision/recall)
- Claim-evidence linkage completeness
- Overclaim rate under sparse evidence
- Model misuse detection rate
- Red-team catch rate on seeded failure cases

## 12.2 Human expert review

- Interpretive humility score
- Multi-lens usefulness rating
- Intervention practicality score
- Governance adequacy score
- Clarity/traceability score

## 12.3 Live product metrics

- Time to actionable synthesis
- Human override rate (and reason taxonomy)
- Review SLA for high-impact outputs
- Policy violation rate
- Practitioner satisfaction and trust

## 12.4 Post-intervention learning loops

- Outcome delta by intervention type
- Leading/lagging regenerative indicators
- Confidence calibration drift
- Pattern reuse success rate
- Counterexample accumulation rate

---

## 13) Suggested Implementation Roadmap

## Phase 0 (2 weeks): Governance-first foundation
- Implement core schemas and audit store.
- Build policy engine with prohibited-claim checks.
- Add human validation workflow primitives.
- Deliver minimal case + evidence + hypothesis APIs.

## Phase 1 (4 weeks): Core council MVP
- Agents: Intake, Evidence Structuring, AQAL, Systems, Critic, Synthesis.
- UI: Case Dashboard, Evidence Explorer, Validation Panel.
- Output contract with required 11 sections.
- End-to-end run on pilot case.

## Phase 2 (4 weeks): Lens expansion + intervention engine
- Add Spiral, ADKAR, Theory U, Cynefin, VSM adapters.
- Intervention Studio with ranking and guardrails.
- Add retrieval for analogous cases.

## Phase 3 (4 weeks): Regenerative and learning intelligence
- Add Antifragility, Biomimicry, Flow modules.
- Build intervention-outcome learning loop.
- Deploy pattern memory and cross-case analytics.

## Phase 4 (ongoing): Trust, scale, and governance hardening
- RBAC maturity, consent governance, compliance reporting.
- Continuous evaluation and red-team simulation.
- Practitioner enablement and feedback-driven refinements.

## Release gates
- No release if policy bypass exists for high-impact outputs.
- No release if audit completeness < threshold.
- No release if essentialization detector false negatives exceed threshold.

---

## 14) Biggest Risks and Tradeoffs

1. **Risk: pseudo-precision from complex models**
   - Tradeoff: richer interpretation vs potential overconfidence.
   - Mitigation: confidence caps + alternatives required.

2. **Risk: lens overload for practitioners**
   - Tradeoff: pluralism vs cognitive burden.
   - Mitigation: progressive disclosure in UI.

3. **Risk: governance friction slows operations**
   - Tradeoff: safety/auditability vs speed.
   - Mitigation: tiered review thresholds by impact.

4. **Risk: sparse data in early cases**
   - Tradeoff: act now vs evidence sufficiency.
   - Mitigation: explicitly low-confidence recommendations + data collection tasks.

5. **Risk: intervention standardization suppresses context**
   - Tradeoff: reuse vs fit.
   - Mitigation: contraindications + context constraints required per intervention.

6. **Risk: organizational misuse of stakeholder hypotheses**
   - Tradeoff: actionable insight vs profiling harm.
   - Mitigation: strict usage policy, consent controls, and review gates.

7. **Risk: hidden ideology through lens selection**
   - Tradeoff: curated defaults vs worldview lock-in.
   - Mitigation: lens selection transparency + critic review.

---

## Appendix A: Prompt Contract (Agent Template)

```text
You are {agent_name} in the Interflow platform.

MISSION
{mission}

INPUTS
{inputs}

RULES
1) Separate observation from interpretation.
2) Treat lens outputs as hypotheses, not facts.
3) Include: evidence_ids, confidence, alternatives, missing_information, misuse_risks.
4) Never output fixed developmental/stage/color identity labels.
5) Escalate when evidence is insufficient or harm risk is elevated.

OUTPUT
Return JSON matching {output_schema}.
```

## Appendix B: Synthesis Output Contract

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
  "regenerative_assessment": {
    "trust_impact": null,
    "resilience_impact": null,
    "capability_distribution_impact": null,
    "ecological_or_systemic_notes": []
  },
  "questions_for_human_validation": []
}
```

## Appendix C: Non-Automation Boundaries

The following must remain human-accountable decisions:
- Final decisions affecting role/status/opportunity of people.
- Acceptance of stakeholder-sensitive interpretations.
- Approval of high-impact governance redesign interventions.
- Tradeoffs where short-term gains conflict with long-term trust/resilience.

