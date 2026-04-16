"""Default ModelRegistryEntry seeds for all 9 Interflow meta-models."""
from __future__ import annotations

from .schemas import ModelRegistryEntry
from .store import InMemoryStore


def seed_default_models(store: InMemoryStore) -> list[ModelRegistryEntry]:
    models = [
        ModelRegistryEntry(
            name="AQAL",
            version="1.0",
            description="Integral quadrant mapping (I/We/It/Its). Checks evidence coverage across subjective, intersubjective, behavioural, and structural dimensions.",
            allowed_uses=["evidence_balance_check", "gap_identification", "quadrant_coverage"],
            disallowed_uses=["personality_typing", "stage_labeling", "ranking_individuals"],
            min_evidence_requirements={"total": 2, "quadrants": 1},
            confidence_rules={"max_without_review": 0.75, "min_evidence_for_0.8": 6},
            ethical_risks=["reductionism", "false_completeness"],
        ),
        ModelRegistryEntry(
            name="Spiral Dynamics",
            version="1.0",
            description="Value-logic analysis of organisational culture themes. Identifies value systems present in evidence WITHOUT assigning stages to individuals or groups.",
            allowed_uses=["value_theme_identification", "tension_mapping", "culture_hypothesis"],
            disallowed_uses=["stage_labeling_people", "ranking_teams", "color_assignment", "developmental_hierarchy"],
            min_evidence_requirements={"total": 4},
            confidence_rules={"max_without_review": 0.60, "requires_alternatives": True},
            ethical_risks=["essentialism", "developmental_hierarchy", "contested_empirics"],
        ),
        ModelRegistryEntry(
            name="Theory U",
            version="1.0",
            description="Maps the collective change journey from downloading patterns to co-creating new futures. Identifies current phase and movement blockers.",
            allowed_uses=["change_journey_mapping", "blocker_identification", "practice_recommendation"],
            disallowed_uses=["prescriptive_staging", "individual_assessment_without_consent"],
            min_evidence_requirements={"total": 3},
            confidence_rules={"max_without_review": 0.70},
            ethical_risks=["spiritual_overlay", "facilitation_dependency"],
        ),
        ModelRegistryEntry(
            name="ADKAR",
            version="1.0",
            description="Change readiness assessment across Awareness, Desire, Knowledge, Ability, Reinforcement dimensions. Identifies the weakest link in adoption.",
            allowed_uses=["change_readiness", "bottleneck_identification", "intervention_sequencing"],
            disallowed_uses=["individual_performance_review", "permanent_labeling"],
            min_evidence_requirements={"total": 3},
            confidence_rules={"max_without_review": 0.80},
            ethical_risks=["mechanistic_view_of_change", "ignoring_systemic_factors"],
        ),
        ModelRegistryEntry(
            name="Cynefin",
            version="1.0",
            description="Complexity framing framework. Classifies the situation domain (simple/complicated/complex/chaotic/disorder) to inform appropriate response strategies.",
            allowed_uses=["domain_classification", "response_strategy", "sense_making"],
            disallowed_uses=["permanent_domain_assignment", "ignoring_domain_shifts"],
            min_evidence_requirements={"total": 2},
            confidence_rules={"max_without_review": 0.75, "requires_alternatives": True},
            ethical_risks=["false_certainty_about_domain", "oversimplification"],
        ),
        ModelRegistryEntry(
            name="VSM",
            version="1.0",
            description="Viable System Model. Analyses organisational viability through 5 systems: operations, coordination, control, intelligence, policy.",
            allowed_uses=["structural_analysis", "viability_assessment", "autonomy_mapping"],
            disallowed_uses=["prescriptive_restructuring_without_context"],
            min_evidence_requirements={"total": 3},
            confidence_rules={"max_without_review": 0.70},
            ethical_risks=["mechanistic_reductionism", "ignoring_informal_systems"],
        ),
        ModelRegistryEntry(
            name="Antifragility",
            version="1.0",
            description="Assesses whether proposed interventions build fragility, resilience, or antifragility. Prefers designs that gain from disorder.",
            allowed_uses=["intervention_stress_testing", "resilience_assessment", "optionality_design"],
            disallowed_uses=["justifying_harmful_volatility", "ignoring_human_cost_of_stress"],
            min_evidence_requirements={"total": 2},
            confidence_rules={"max_without_review": 0.65},
            ethical_risks=["valorising_stress_without_consent", "ignoring_power_dynamics"],
        ),
        ModelRegistryEntry(
            name="Biomimicry",
            version="1.0",
            description="Draws on nature-inspired principles (feedback loops, diversity, redundancy, edge effects) to enrich intervention design.",
            allowed_uses=["design_principle_enrichment", "systemic_metaphor", "regenerative_assessment"],
            disallowed_uses=["literal_biological_mapping", "ignoring_social_complexity"],
            min_evidence_requirements={"total": 2},
            confidence_rules={"max_without_review": 0.60},
            ethical_risks=["metaphor_overreach", "obscuring_power_with_nature_language"],
        ),
        ModelRegistryEntry(
            name="Flow",
            version="1.0",
            description="Analyses conditions for optimal engagement and performance: clear goals, immediate feedback, challenge-skill balance, reduced friction.",
            allowed_uses=["engagement_assessment", "friction_identification", "environment_design"],
            disallowed_uses=["individual_flow_scoring_without_consent", "productivity_surveillance"],
            min_evidence_requirements={"total": 2},
            confidence_rules={"max_without_review": 0.70},
            ethical_risks=["commodifying_human_experience", "ignoring_systemic_causes_of_disengagement"],
        ),
    ]

    for m in models:
        store.save_model(m)

    return models
