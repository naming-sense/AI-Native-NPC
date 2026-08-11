from __future__ import annotations

import hashlib
import importlib.util
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Callable

import yaml


ROOT = Path(__file__).resolve().parents[1]
GOAL_REGISTRY = ROOT / "contracts/current/goal_registry_v1.yaml"
SKILL_REGISTRY = ROOT / "contracts/current/skill_registry_v1.yaml"
SCHEMA = ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml"
GENERATOR = ROOT / "tools/generate_goal_gameplay_semantics_v1.py"
GENERATED_PY = ROOT / "generated/python/ai_native_npc_goal_gameplay_semantics_generated.py"
GENERATED_CPP = ROOT / "generated/cpp/AINativeNPCGoalGameplaySemantics.generated.h"
GENERATED_DOC = ROOT / "generated/docs/goal_gameplay_semantics_v1.md"
MONOLITHIC_PY = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
MONOLITHIC_CPP = ROOT / "generated/cpp/AINativeNPCContracts.generated.h"
CAPTURE_VALIDATOR = ROOT / "tools/validate_anpc_capture_v2.py"
CURRENT_DOCS = (
    ROOT / "docs/current/contract-appendices.md",
    ROOT / "docs/current/implementation-plan.md",
    ROOT / "docs/current/technical-requirements.md",
    ROOT / "docs/current/unreal-implementation-plan.md",
)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def import_path(name: str, path: Path):
    if not path.exists():
        raise AssertionError(f"missing generated/tool artifact: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def find_guard(contract: dict, guard: str) -> dict:
    return next(row for row in contract["guard_authorities"] if row["guard"] == guard)


def find_binding(guard: dict, goal: str, phase: str, order: int) -> dict:
    return next(
        row
        for row in guard["bindings"]
        if (row["goal"], row["phase"], row["order"]) == (goal, phase, order)
    )


def markdown_table_rows(text: str, heading: str) -> list[list[str]]:
    lines = text.splitlines()
    start = lines.index(heading)
    table = lines[start + 4 :]
    rows: list[list[str]] = []
    for line in table:
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(
            [cell[1:-1] if len(cell) >= 2 and cell.startswith("`") and cell.endswith("`") else cell for cell in cells]
        )
    return rows


class GoalGameplayAuthorityTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.goal_registry = load_yaml(GOAL_REGISTRY)
        self.skill_registry = load_yaml(SKILL_REGISTRY)
        self.schema = load_yaml(SCHEMA)

    @property
    def contract(self) -> dict:
        self.assertIn("goal_gameplay_semantics_v1", self.goal_registry)
        return self.goal_registry["goal_gameplay_semantics_v1"]

    def test_registry_adds_versioned_bounded_authority_without_breaking_schema_dependency(self) -> None:
        self.assertEqual(self.goal_registry["registry"]["version"], "1.1.0")
        self.assertEqual(self.contract["version"], "1.0.0")
        self.assertEqual(self.contract["status"], "approved_production_authority")
        self.assertEqual(self.contract["approved_on"], "2026-08-11")
        self.assertEqual(self.contract["scope"]["profile_id"], "GuardPhase0")
        self.assertEqual(
            self.contract["scope"]["supported_goals"],
            ["IdleObserve", "InvestigateDisturbance"],
        )
        self.assertFalse(self.contract["scope"]["claims"]["full_guard_catalog_pass"])
        self.assertEqual(
            self.contract["scope"]["claims"],
            {
                "executable_unique_guards": 9,
                "unavailable_unique_guards": 3,
                "executable_transition_bindings": 12,
                "unavailable_transition_bindings": 4,
                "effects": 2,
                "production_executable_skills": 5,
                "full_guard_catalog_pass": False,
            },
        )

    def test_initial_goal_and_terminal_idle_resume_are_exact(self) -> None:
        self.assertEqual(
            self.contract["initial_profiles"],
            [
                {
                    "profile_id": "GuardPhase0",
                    "initial_goal": "IdleObserve",
                    "initial_phase": "Observe",
                    "goal_instance_id_policy": "session_monotonic_nonzero",
                    "initial_goal_revision": 1,
                    "initial_phase_generation": 1,
                    "lifecycle": "Active",
                    "activation_authority": "server_game_thread_exact_assembly_once",
                    "activation_precondition_target": "HomeWaypoint",
                    "failure_policy": "remain_dormant_fail_closed",
                }
            ],
        )
        self.assertEqual(
            self.contract["terminal_resume"],
            {
                "terminal_states": ["Succeeded", "Failed"],
                "record_outcome": "once_for_exact_goal_token",
                "remove_terminal_goal": True,
                "resume_goal": "IdleObserve",
                "resume_policy": "ResumeSamePhase",
                "required_suspended_goal_count": 1,
                "timer_policy": "reuse_stored_remaining",
                "request_new_decision": True,
                "missing_or_stale_idle_policy": "dormant_fail_closed_no_synthetic_idle",
            },
        )

    def test_target_ownership_and_phase_hard_policies_are_exact(self) -> None:
        targets = {row["id"]: row for row in self.contract["target_authorities"]}
        self.assertEqual(targets["HomeWaypoint"]["target_kind"], "Waypoint")
        self.assertEqual(targets["HomeWaypoint"]["owner"], "GameplayGoalAuthority")
        self.assertEqual(targets["HomeWaypoint"]["lifetime"], "AuthoritySession")
        self.assertEqual(targets["HomeWaypoint"]["capture_source"], "FirstExactAssemblyPawnFiniteWorldPosition")
        self.assertFalse(targets["HomeWaypoint"]["stored_in_knowledge"])
        self.assertFalse(targets["HomeWaypoint"]["mutable"])
        self.assertTrue(targets["HomeWaypoint"]["candidate_usable"])

        self.assertEqual(targets["SourceSoundHandle"]["target_kind"], "SoundEvent")
        self.assertTrue(targets["SourceSoundHandle"]["provenance_only"])
        self.assertFalse(targets["SourceSoundHandle"]["candidate_usable"])
        self.assertEqual(targets["DisturbancePosition"]["target_kind"], "WorldPosition")
        self.assertEqual(targets["DisturbancePosition"]["capture_source"], "ExactSoundEventStimulusLocation")
        self.assertEqual(targets["DisturbancePosition"]["lifetime"], "InvestigateGoalInstance")
        self.assertEqual(targets["DisturbancePosition"]["source_ttl_expiry_policy"], "preserve_immutable_position")
        self.assertFalse(targets["DisturbancePosition"]["actor_transform_lookup"])

        policies = {
            (row["goal"], row["phase"]): row
            for row in self.contract["phase_target_policies"]
        }
        self.assertEqual(policies[("IdleObserve", "Observe")]["policy"], "AnyAllowedTargetOrNoTarget")
        for phase in ("Orient", "Navigate", "Search"):
            row = policies[("InvestigateDisturbance", phase)]
            self.assertEqual(row["policy"], "ActiveGoalPrimaryTargetOnly")
            self.assertEqual(row["target_authority"], "DisturbancePosition")
        self.assertEqual(
            policies[("InvestigateDisturbance", "Return")]["target_authority"],
            "HomeWaypoint",
        )
        self.assertEqual(
            policies[("InvestigateDisturbance", "Resolve")]["policy"],
            "UnavailableInGuardPhase0",
        )

    def test_production_skill_mask_and_guard_utility_are_exact(self) -> None:
        self.assertEqual(
            self.contract["production_skills"],
            {
                "executable": ["Idle", "TurnTo", "Approach", "Investigate", "SearchArea"],
                "control": "ContinueCurrentAction",
                "all_others_policy": "hard_mask_false_even_if_precondition_true",
            },
        )
        utility = self.contract["utility_profile"]
        self.assertEqual(utility["profile_id"], "GuardPhase0UtilityV1")
        self.assertTrue(utility["deterministic"])
        self.assertEqual(utility["score_formula"], "skill_bias_plus_pair_feature_dot_product")
        self.assertEqual(utility["all_other_skill_bias"], -2.5)
        self.assertEqual(
            utility["skill_biases"],
            {
                "SearchArea": 1.5,
                "Investigate": 1.25,
                "TurnTo": 1.0,
                "Approach": 0.75,
                "ContinueCurrentAction": 0.5,
                "Idle": 0.0,
            },
        )
        self.assertEqual(utility["candidate_pair_feature_weights"], [0.0] * 16)
        self.assertEqual(utility["switch_cost_policy"], "existing_postprocess_v1")
        self.assertEqual(utility["parameter_policy"], "skill_registry_defaults_normalized")

    def test_typed_event_field_contract_has_exact_applicability_and_defaults(self) -> None:
        event = self.contract["typed_event_fact"]
        self.assertEqual(event["immutability"], "value_immutable")
        self.assertEqual(event["queue_validation"], "reject_before_enqueue")
        self.assertEqual(event["event_sequence_policy"], "session_monotonic_nonzero_at_most_once")
        fields = {row["name"]: row for row in event["fields"]}
        self.assertEqual(
            tuple(fields),
            (
                "EventSequence",
                "EventType",
                "Source",
                "GoalToken",
                "KnowledgeRevision",
                "DecisionId",
                "Skill",
                "Target",
                "ExecutionStatus",
                "FailureReason",
                "TimerId",
                "TimerRuntimeEpoch",
            ),
        )
        self.assertEqual(fields["EventSequence"]["type"], "uint64")
        self.assertEqual(fields["EventSequence"]["required_for_sources"], ["Knowledge", "SkillExecutor", "GoalTimer", "GoalAuthority"])
        self.assertEqual(fields["EventSequence"]["constraint"], "nonzero")
        self.assertEqual(fields["KnowledgeRevision"]["required_for_sources"], ["Knowledge"])
        self.assertEqual(fields["KnowledgeRevision"]["canonical_default"], 0)
        self.assertEqual(fields["DecisionId"]["required_for_sources"], ["SkillExecutor"])
        self.assertEqual(fields["FailureReason"]["required_when"], "SkillExecutorAndExecutionStatusFailed")
        self.assertEqual(fields["TimerId"]["required_for_sources"], ["GoalTimer"])
        self.assertEqual(fields["TimerRuntimeEpoch"]["required_for_sources"], ["GoalTimer"])
        self.assertEqual(fields["TimerRuntimeEpoch"]["constraint"], "nonzero_when_required")

    def test_guard_authority_counts_and_exact_registry_rows_match(self) -> None:
        contract = self.contract
        authorities = contract["guard_authorities"]
        self.assertEqual(len(authorities), 12)
        self.assertEqual(
            {row["guard"] for row in authorities if row["availability"] == "executable"},
            {
                "valid_disturbance_target",
                "social_subject",
                "orientation_complete",
                "no_valid_snapshot",
                "phase_timeout",
                "arrived_at_snapshot",
                "PathUnavailable",
                "search_budget_exhausted",
                "at_return_target",
            },
        )
        self.assertEqual(
            {row["guard"] for row in authorities if row["availability"] == "provider_unavailable"},
            {"subject_identified", "resolution_complete", "no_valid_belief"},
        )
        bindings = [binding for row in authorities for binding in row["bindings"]]
        self.assertEqual(len(bindings), 16)
        executable = [
            binding
            for row in authorities
            if row["availability"] == "executable"
            for binding in row["bindings"]
        ]
        self.assertEqual(len(executable), 12)

        registry_rows = {}
        for goal in self.goal_registry["goals"]:
            for phase, phase_spec in goal.get("phases", {}).items():
                for transition in phase_spec.get("transitions", []):
                    registry_rows[(goal["name"], phase, transition["order"])] = transition
        for authority in authorities:
            for binding in authority["bindings"]:
                key = (binding["goal"], binding["phase"], binding["order"])
                row = registry_rows[key]
                self.assertEqual(row["guard"], authority["guard"])
                self.assertEqual(row["trigger"], binding["trigger"])

        orientation = find_binding(
            find_guard(contract, "orientation_complete"),
            "InvestigateDisturbance",
            "Orient",
            0,
        )
        self.assertEqual(orientation["fact_source"], "SkillExecutor")
        self.assertEqual(orientation["accepted_skills"], ["TurnTo"])
        self.assertEqual(orientation["target_authorities"], ["DisturbancePosition"])
        self.assertEqual(orientation["accepted_failure_reasons"], [])
        self.assertIn("ExactCurrentDecisionId", orientation["requirements"])

        social = find_binding(
            find_guard(contract, "social_subject"),
            "IdleObserve",
            "Observe",
            1,
        )
        self.assertIn("ExactCurrentKnowledgeRevision", social["requirements"])

        navigate_path = find_binding(
            find_guard(contract, "PathUnavailable"),
            "InvestigateDisturbance",
            "Navigate",
            1,
        )
        self.assertEqual(navigate_path["accepted_skills"], ["Approach", "Investigate"])
        self.assertEqual(navigate_path["accepted_failure_reasons"], ["PathUnavailable"])
        self.assertEqual(navigate_path["target_authorities"], ["DisturbancePosition"])

        return_path = find_binding(
            find_guard(contract, "PathUnavailable"),
            "InvestigateDisturbance",
            "Return",
            1,
        )
        self.assertEqual(return_path["accepted_skills"], ["Approach"])
        self.assertEqual(return_path["target_authorities"], ["HomeWaypoint"])

    def test_staged_effects_preserve_the_approved_failure_boundaries(self) -> None:
        effects = {row["name"]: row for row in self.contract["effects"]}
        request = effects["request_new_goal"]
        self.assertEqual(request["apply_effect_policy"], "stage_intent_only_no_external_mutation")
        self.assertEqual(request["pump_result"], "GoalRequested")
        self.assertEqual(request["transaction_policy"], "owner_bounded_prepare_interrupt_commit")
        self.assertEqual(request["failure_before_interrupt"], "preserve_old_goal_timer_and_running_skill")
        self.assertEqual(request["interrupt_failure"], "keep_old_goal_active_and_replan")
        self.assertEqual(request["failure_after_interrupt"], "keep_old_goal_active_without_running_skill_and_replan")
        self.assertEqual(request["post_commit_skill_start_failure"], "keep_new_goal_and_replan_or_wait_timeout")
        self.assertEqual(request["callback_free_atomic_steps"], ["suspend_old_goal_and_pause_timer", "activate_new_goal_and_install_primary_target", "arm_new_phase_timer", "supersede_pending_old_decision"])

        remain = effects["remain_and_replan"]
        self.assertEqual(remain["apply_effect_policy"], "stage_intent_only_no_external_mutation")
        self.assertEqual(remain["transaction_policy"], "supersede_pending_decision_then_request_new_snapshot")
        self.assertEqual(
            remain["preserve"],
            ["GoalInstance", "Lifecycle", "Phase", "PhaseGeneration", "PhaseDeadline", "TimerRuntimeEpoch"],
        )
        self.assertEqual(remain["revision_without_target_change"], "unchanged")
        self.assertEqual(remain["revision_with_target_change"], "increment_once_authoritative_primary_target_changed")

    def test_validator_rejects_hostile_contract_mutations(self) -> None:
        generator = import_path("goal_gameplay_generator_hostile", GENERATOR)
        good = deepcopy(self.goal_registry)
        self.assertEqual(generator.validate_registry(good, self.skill_registry, self.schema), [])

        cases: list[tuple[str, Callable[[dict], None], str]] = []

        def missing_initial(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["initial_profiles"] = []

        def wrong_semantics_version(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["version"] = "2.0.0"

        def unknown_guard(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["guard_authorities"][0]["guard"] = "forged_guard"

        def unknown_effect(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["effects"][0]["name"] = "forged_effect"

        def duplicate_guard(registry: dict) -> None:
            rows = registry["goal_gameplay_semantics_v1"]["guard_authorities"]
            rows.append(deepcopy(rows[0]))

        def incomplete_skill_payload(registry: dict) -> None:
            guard = find_guard(registry["goal_gameplay_semantics_v1"], "orientation_complete")
            find_binding(guard, "InvestigateDisturbance", "Orient", 0)["accepted_skills"] = []

        def executable_resolve(registry: dict) -> None:
            find_guard(registry["goal_gameplay_semantics_v1"], "resolution_complete")["availability"] = "executable"

        def request_without_rollback(registry: dict) -> None:
            effect = next(row for row in registry["goal_gameplay_semantics_v1"]["effects"] if row["name"] == "request_new_goal")
            effect.pop("failure_after_interrupt")

        def raw_sound_search_target(registry: dict) -> None:
            policies = registry["goal_gameplay_semantics_v1"]["phase_target_policies"]
            row = next(row for row in policies if row["goal"] == "InvestigateDisturbance" and row["phase"] == "Search")
            row["target_authority"] = "SourceSoundHandle"

        def missing_home(registry: dict) -> None:
            targets = registry["goal_gameplay_semantics_v1"]["target_authorities"]
            targets[:] = [row for row in targets if row["id"] != "HomeWaypoint"]

        def wider_production_skills(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["production_skills"]["executable"].append("LookAt")

        def nondeterministic_utility(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["utility_profile"]["deterministic"] = False

        def nonfinite_utility(registry: dict) -> None:
            registry["goal_gameplay_semantics_v1"]["utility_profile"]["candidate_pair_feature_weights"][3] = math.nan

        def mismatched_transition(registry: dict) -> None:
            guard = find_guard(registry["goal_gameplay_semantics_v1"], "orientation_complete")
            find_binding(guard, "InvestigateDisturbance", "Orient", 0)["trigger"]["event_type"] = "SkillFailed"

        cases.extend(
            [
                ("wrong semantics version", wrong_semantics_version, "goal gameplay semantics version"),
                ("missing initial profile", missing_initial, "initial profile"),
                ("unknown guard", unknown_guard, "transition binding"),
                ("unknown effect", unknown_effect, "effect authority"),
                ("duplicate guard authority", duplicate_guard, "duplicate guard authority"),
                ("incomplete Skill event payload", incomplete_skill_payload, "Skill event binding"),
                ("executable Resolve guard", executable_resolve, "unavailable phase"),
                ("request_new_goal rollback missing", request_without_rollback, "request_new_goal effect"),
                ("SoundEvent used directly by SearchArea", raw_sound_search_target, "candidate-usable target authority"),
                ("home Waypoint missing", missing_home, "target authority"),
                ("production skill set wider than five", wider_production_skills, "production executable skill count"),
                ("nondeterministic Utility", nondeterministic_utility, "utility determinism"),
                ("non-finite Utility weight", nonfinite_utility, "utility numeric"),
                ("transition trigger mismatch", mismatched_transition, "transition binding"),
            ]
        )
        for label, mutate, expected in cases:
            with self.subTest(label=label):
                bad = deepcopy(good)
                mutate(bad)
                errors = generator.validate_registry(bad, self.skill_registry, self.schema)
                self.assertTrue(errors, label)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_generator_derives_policy_values_instead_of_copying_approved_names(self) -> None:
        generator = import_path("goal_gameplay_generator_derivation", GENERATOR)
        source = GENERATOR.read_text(encoding="utf-8")
        for forbidden in (
            "valid_disturbance_target",
            "orientation_complete",
            "request_new_goal",
            "GuardPhase0UtilityV1",
            "DisturbancePosition",
            "HomeWaypoint",
        ):
            self.assertNotIn(forbidden, source)

        mutated = deepcopy(self.goal_registry)
        mutated["goal_gameplay_semantics_v1"]["utility_profile"]["skill_biases"]["SearchArea"] = 1.75
        py_text = generator.generate_python(mutated, self.skill_registry, self.schema, "0" * 64)
        cpp_text = generator.generate_cpp(mutated, self.skill_registry, self.schema, "0" * 64)
        doc_text = generator.generate_markdown(mutated, self.skill_registry, self.schema, "0" * 64)
        self.assertIn("1.75", py_text)
        self.assertIn("1.75", cpp_text)
        self.assertIn("1.75", doc_text)

        baseline_cpp = generator.generate_cpp(
            self.goal_registry,
            self.skill_registry,
            self.schema,
            "0" * 64,
        )
        target_mutated = deepcopy(self.goal_registry)
        target_mutated["goal_gameplay_semantics_v1"]["target_authorities"][2]["generation"] = 2
        target_cpp = generator.generate_cpp(
            target_mutated,
            self.skill_registry,
            self.schema,
            "0" * 64,
        )
        self.assertNotEqual(
            baseline_cpp,
            target_cpp,
            "Target ownership/lifetime/generation authority must affect generated C++ bytes",
        )

        effect_mutated = deepcopy(self.goal_registry)
        effect_mutated["goal_gameplay_semantics_v1"]["effects"][0][
            "transaction_policy"
        ] += "_mutation_probe"
        effect_cpp = generator.generate_cpp(
            effect_mutated,
            self.skill_registry,
            self.schema,
            "0" * 64,
        )
        self.assertNotEqual(
            baseline_cpp,
            effect_cpp,
            "Effect transaction authority must affect generated C++ bytes",
        )

        baseline_outputs = (
            generator.generate_python(self.goal_registry, self.skill_registry, self.schema, "0" * 64),
            baseline_cpp,
            generator.generate_markdown(self.goal_registry, self.skill_registry, self.schema, "0" * 64),
        )
        contract = self.goal_registry["goal_gameplay_semantics_v1"]

        def replace_exact_value(node, old_value: str, new_value: str) -> None:
            if isinstance(node, dict):
                for key, item in node.items():
                    if item == old_value:
                        node[key] = new_value
                    else:
                        replace_exact_value(item, old_value, new_value)
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    if item == old_value:
                        node[index] = new_value
                    else:
                        replace_exact_value(item, old_value, new_value)

        for table_name, identity_key in (("target_authorities", "id"), ("effects", "name")):
            rows = contract[table_name]
            for row_index, row in enumerate(rows):
                for field, value in row.items():
                    with self.subTest(table=table_name, row=row[identity_key], field=field):
                        probe = deepcopy(self.goal_registry)
                        probe_rows = probe["goal_gameplay_semantics_v1"][table_name]
                        if isinstance(value, bool):
                            mutated_value = not value
                        elif isinstance(value, int):
                            mutated_value = value + 7
                        elif isinstance(value, list):
                            mutated_value = [*value, "mutation_probe"]
                        elif field == identity_key:
                            mutated_value = f"{value}MutationProbe"
                            replace_exact_value(
                                probe["goal_gameplay_semantics_v1"], value, mutated_value
                            )
                        elif field == "target_kind":
                            mutated_value = rows[(row_index + 1) % len(rows)][field]
                        else:
                            mutated_value = f"{value}_mutation_probe"
                        if field != identity_key:
                            probe_rows[row_index][field] = mutated_value
                        probe_outputs = (
                            generator.generate_python(probe, self.skill_registry, self.schema, "0" * 64),
                            generator.generate_cpp(probe, self.skill_registry, self.schema, "0" * 64),
                            generator.generate_markdown(probe, self.skill_registry, self.schema, "0" * 64),
                        )
                        for artifact, baseline, changed in zip(
                            ("Python", "C++", "Markdown"), baseline_outputs, probe_outputs
                        ):
                            self.assertNotEqual(
                                baseline,
                                changed,
                                f"{table_name}.{field} must affect generated {artifact} bytes",
                            )


class GoalGameplayGeneratedArtifactsTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_yaml(GOAL_REGISTRY)
        cls.contract = cls.registry.get("goal_gameplay_semantics_v1", {})
        cls.generated = import_path("goal_gameplay_generated_contract", GENERATED_PY)
        cls.digest = hashlib.sha256(GOAL_REGISTRY.read_bytes()).hexdigest()
        cls.skill_digest = hashlib.sha256(SKILL_REGISTRY.read_bytes()).hexdigest()

    def test_python_binding_exposes_consumer_helpers_and_equivalent_values(self) -> None:
        generated = self.generated
        self.assertEqual(generated.GOAL_REGISTRY_SHA256, self.digest)
        self.assertEqual(generated.GOAL_REGISTRY_VERSION, "1.1.0")
        self.assertEqual(generated.GAMEPLAY_SEMANTICS_VERSION, "1.0.0")
        profile = generated.find_initial_profile("GuardPhase0")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.goal, generated.GoalType.IdleObserve)
        self.assertEqual(profile.phase, generated.GoalPhase.Observe)
        self.assertEqual(profile.initial_goal_revision, 1)
        self.assertEqual(profile.initial_phase_generation, 1)

        self.assertEqual(len(generated.TRANSITION_BINDINGS), 16)
        self.assertEqual(generated.EXECUTABLE_TRANSITION_BINDING_COUNT, 12)
        binding = generated.find_transition_binding(
            generated.GoalType.InvestigateDisturbance,
            generated.GoalPhase.Navigate,
            1,
        )
        self.assertIsNotNone(binding)
        self.assertEqual(binding.guard, generated.GuardId.PathUnavailable)
        self.assertEqual(binding.fact_source, generated.FactSource.SkillExecutor)
        self.assertTrue(binding.accepted_skill_mask & (1 << generated.SkillId.Investigate))
        self.assertTrue(binding.accepted_failure_mask & (1 << generated.FailureReason.PathUnavailable))
        self.assertTrue(binding.requirement_mask)

        self.assertTrue(generated.is_production_executable_skill(generated.SkillId.Idle))
        self.assertTrue(generated.is_production_executable_skill(generated.SkillId.SearchArea))
        self.assertFalse(generated.is_production_executable_skill(generated.SkillId.LookAt))
        self.assertEqual(generated.CONTROL_SKILL, generated.SkillId.ContinueCurrentAction)
        self.assertEqual(generated.utility_bias(generated.SkillId.SearchArea), 1.5)
        self.assertEqual(generated.utility_bias(generated.SkillId.Attack), -2.5)
        self.assertEqual(generated.CANDIDATE_PAIR_FEATURE_WEIGHTS, (0.0,) * 16)
        self.assertEqual(
            tuple(generated.TARGET_AUTHORITIES),
            tuple(self.contract["target_authorities"]),
        )
        self.assertEqual(
            tuple(generated.EFFECT_AUTHORITIES),
            tuple(self.contract["effects"]),
        )

        search_policy = generated.phase_target_policy(
            generated.GoalType.InvestigateDisturbance,
            generated.GoalPhase.Search,
        )
        self.assertIsNotNone(search_policy)
        self.assertEqual(search_policy.policy, generated.TargetPolicy.ActiveGoalPrimaryTargetOnly)
        self.assertEqual(search_policy.target_authority, generated.TargetAuthorityId.DisturbancePosition)
        resolve_policy = generated.phase_target_policy(
            generated.GoalType.InvestigateDisturbance,
            generated.GoalPhase.Resolve,
        )
        self.assertEqual(resolve_policy.policy, generated.TargetPolicy.UnavailableInGuardPhase0)

    def test_markdown_and_cpp_publish_equivalent_scope_without_full_guard_claim(self) -> None:
        cpp = GENERATED_CPP.read_text(encoding="utf-8")
        doc = GENERATED_DOC.read_text(encoding="utf-8")
        self.assertNotIn("\x00", cpp)
        self.assertIn("*A != '\\0'", cpp)
        for text in (cpp, doc):
            self.assertIn(self.digest, text)
        self.assertIn("TransitionBindings", cpp)
        self.assertIn("RequirementMask", cpp)
        self.assertIn("ERequirementId", cpp)
        self.assertIn("EFailureReason", cpp)
        self.assertIn("HasRequirement", cpp)
        self.assertIn("ProductionSkillMask", cpp)
        self.assertIn("CandidatePairFeatureWeights", cpp)
        self.assertIn("FindInitialProfile", cpp)
        self.assertIn("FindTransitionBinding", cpp)
        self.assertIn("FindPhaseTargetPolicy", cpp)
        self.assertIn("TargetAuthorities", cpp)
        self.assertIn("EffectAuthorities", cpp)
        self.assertIn("FindTargetAuthority", cpp)
        self.assertIn("FindEffectAuthority", cpp)
        self.assertIn("GetUtilityBias", cpp)
        self.assertIn("9 executable unique guards", doc)
        self.assertIn("3 provider-unavailable unique guards", doc)
        self.assertIn("12 executable transition bindings", doc)
        self.assertIn("Gameplay Goal FSM: **HOLD**", doc)
        self.assertNotIn("all 29 guards PASS", doc)
        expected_target_rows = [
            [
                row["id"], row["target_kind"], row["owner"], row["lifetime"],
                row["stable_id_policy"], row["capture_source"], str(row["generation"]),
                str(row["initial_revision"]), str(row["mutable"]).lower(),
                str(row["stored_in_knowledge"]).lower(), str(row["provenance_only"]).lower(),
                str(row["candidate_usable"]).lower(), str(row["actor_transform_lookup"]).lower(),
                row["source_ttl_expiry_policy"],
            ]
            for row in self.contract["target_authorities"]
        ]
        expected_effect_rows = [
            [
                row["name"], row["apply_effect_policy"], row["pump_result"], row["transaction_policy"],
                row["failure_before_interrupt"], row["interrupt_failure"], row["failure_after_interrupt"],
                row["post_commit_skill_start_failure"],
                ", ".join(row["callback_free_atomic_steps"]) or "none",
                ", ".join(row["preserve"]) or "none",
                row["revision_without_target_change"], row["revision_with_target_change"],
            ]
            for row in self.contract["effects"]
        ]
        self.assertEqual(markdown_table_rows(doc, "## Target authorities"), expected_target_rows)
        self.assertEqual(markdown_table_rows(doc, "## Effects"), expected_effect_rows)

        bool_text = lambda value: "true" if value else "false"
        for row in self.contract["target_authorities"]:
            expected = (
                f'FTargetAuthority{{ETargetAuthorityId::{row["id"]}, '
                f'SchemaV2::ETargetKind::{row["target_kind"]}, "{row["owner"]}", "{row["lifetime"]}", '
                f'"{row["stable_id_policy"]}", {bool_text(row["owner"] == "GameplayGoalAuthority")}, '
                f'{bool_text(row["owner"] == "Knowledge")}, {bool_text(row["lifetime"] == "AuthoritySession")}, '
                f'{bool_text(row["lifetime"] == "SourceKnowledgeFact")}, '
                f'{bool_text(row["lifetime"] == "InvestigateGoalInstance")}, '
                f'{bool_text(row["stable_id_policy"] == "session_monotonic_nonzero_goal_target_allocator")}, '
                f'{bool_text(row["stable_id_policy"] == "exact_source_handle")}, '
                f'{row["generation"]}ULL, {row["initial_revision"]}ULL, {bool_text(row["mutable"])}, '
                f'{bool_text(row["stored_in_knowledge"])}, {bool_text(row["provenance_only"])}, '
                f'{bool_text(row["candidate_usable"])}, "{row["capture_source"]}", '
                f'{bool_text(row["capture_source"] == "FirstExactAssemblyPawnFiniteWorldPosition")}, '
                f'{bool_text(row["capture_source"] == "ExactCurrentSoundEventHandleAtRequest")}, '
                f'{bool_text(row["capture_source"] == "ExactSoundEventStimulusLocation")}, '
                f'{bool_text(row["actor_transform_lookup"])}, "{row["source_ttl_expiry_policy"]}"}}'
            )
            self.assertIn(f"    {expected},", cpp)
        for row in self.contract["effects"]:
            steps = "|".join(row["callback_free_atomic_steps"])
            preserve = "|".join(row["preserve"])
            expected = (
                f'FEffectAuthority{{"{row["name"]}", "{row["apply_effect_policy"]}", "{row["pump_result"]}", '
                f'{bool_text(row["apply_effect_policy"] == "stage_intent_only_no_external_mutation")}, '
                f'{bool_text(row["pump_result"] == "GoalRequested")}, '
                f'{bool_text(row["transaction_policy"] == "owner_bounded_prepare_interrupt_commit")}, '
                f'"{row["transaction_policy"]}", "{row["failure_before_interrupt"]}", '
                f'"{row["interrupt_failure"]}", "{row["failure_after_interrupt"]}", '
                f'"{row["post_commit_skill_start_failure"]}", "{steps}", "{preserve}", '
                f'"{row["revision_without_target_change"]}", "{row["revision_with_target_change"]}"}}'
            )
            self.assertIn(f"    {expected},", cpp)

        unreal_plan = (ROOT / "docs/current/unreal-implementation-plan.md").read_text(encoding="utf-8")
        self.assertIn(f'"skill_registry_sha256": "{self.skill_digest}"', unreal_plan)
        self.assertIn(f'"goal_registry_sha256": "{self.digest}"', unreal_plan)
        self.assertNotIn('"skill_registry_sha256": "08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8"', unreal_plan)
        self.assertNotIn('"goal_registry_sha256": "ede7aaba704ecbbd9c6e1cb649c87e03fd24e9dc71ea4166f82baa42fb00ee43"', unreal_plan)

    def test_generator_check_and_goal_digest_consumers_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(ROOT), "--check"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('"status": "pass"', result.stdout)

        version = self.registry["registry"]["version"]
        consumers = (MONOLITHIC_PY, MONOLITHIC_CPP, CAPTURE_VALIDATOR, *CURRENT_DOCS)
        for path in consumers:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn(self.digest, text)
                self.assertIn(version, text)

    def test_generated_cpp17_compiles_and_matches_python_values(self) -> None:
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.fail("C++17 compiler is required")
        source = r'''
#include <cstdint>
#include <iostream>
#include "AINativeNPCGoalGameplaySemantics.generated.h"
using namespace AINativeNPC;
using namespace AINativeNPC::GoalGameplayV1;
static_assert(InitialProfiles.size() == 1U);
static_assert(InitialProfiles[0].Goal == SchemaV2::EGoalType::IdleObserve);
static_assert(InitialProfiles[0].Phase == SchemaV2::EGoalPhase::Observe);
static_assert(ExecutableUniqueGuardCount == 9U);
static_assert(UnavailableUniqueGuardCount == 3U);
static_assert(ExecutableTransitionBindingCount == 12U);
static_assert(TargetAuthorities.size() == 3U);
static_assert(EffectAuthorities.size() == 2U);
static_assert(TargetAuthorities[0].OwnedByGameplayGoalAuthority);
static_assert(TargetAuthorities[0].AuthoritySessionLifetime);
static_assert(TargetAuthorities[0].SessionMonotonicGoalTargetAllocator);
static_assert(TargetAuthorities[0].FirstExactAssemblyPawnCapture);
static_assert(TargetAuthorities[1].OwnedByKnowledge);
static_assert(TargetAuthorities[1].SourceKnowledgeFactLifetime);
static_assert(TargetAuthorities[1].ExactSourceHandleStableId);
static_assert(TargetAuthorities[1].ExactCurrentSoundEventHandleCapture);
static_assert(TargetAuthorities[2].Generation == 1ULL);
static_assert(TargetAuthorities[2].InitialRevision == 1ULL);
static_assert(TargetAuthorities[2].OwnedByGameplayGoalAuthority);
static_assert(TargetAuthorities[2].InvestigateGoalInstanceLifetime);
static_assert(TargetAuthorities[2].SessionMonotonicGoalTargetAllocator);
static_assert(TargetAuthorities[2].ExactSoundEventStimulusLocationCapture);
static_assert(EffectAuthorities[0].StageIntentOnly);
static_assert(EffectAuthorities[0].RequestsGoal);
static_assert(EffectAuthorities[0].OwnerBoundedPrepareInterruptCommit);
static_assert(IsProductionExecutableSkill(SchemaV2::ESkillId::Idle));
static_assert(IsProductionExecutableSkill(SchemaV2::ESkillId::SearchArea));
static_assert(!IsProductionExecutableSkill(SchemaV2::ESkillId::LookAt));
static_assert(GetUtilityBias(SchemaV2::ESkillId::SearchArea) == 1.5);
static_assert(GetUtilityBias(SchemaV2::ESkillId::Attack) == -2.5);
int main() {
    const auto* Binding = FindTransitionBinding(
        SchemaV2::EGoalType::InvestigateDisturbance,
        SchemaV2::EGoalPhase::Navigate,
        1U);
    const auto* Policy = FindPhaseTargetPolicy(
        SchemaV2::EGoalType::InvestigateDisturbance,
        SchemaV2::EGoalPhase::Search);
    const auto* TargetAuthority = FindTargetAuthority(ETargetAuthorityId::DisturbancePosition);
    const auto* EffectAuthority = FindEffectAuthority("request_new_goal");
    if (Binding == nullptr || Policy == nullptr || TargetAuthority == nullptr || EffectAuthority == nullptr) return 2;
    std::cout
        << static_cast<unsigned>(InitialProfiles[0].Goal) << ','
        << TransitionBindings.size() << ','
        << ExecutableTransitionBindingCount << ','
        << ProductionSkillMask << ','
        << Binding->AcceptedSkillMask << ','
        << Binding->AcceptedFailureMask << ','
        << static_cast<unsigned>(Policy->TargetAuthority) << ','
        << GetUtilityBias(SchemaV2::ESkillId::SearchArea) << ','
        << CandidatePairFeatureWeights.size();
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source_path = temp / "goal_gameplay_compile.cpp"
            binary_path = temp / "goal_gameplay_compile"
            source_path.write_text(source, encoding="utf-8")
            compile_result = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-pedantic", "-I", str(GENERATED_CPP.parent), str(source_path), "-o", str(binary_path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout)
            run_result = subprocess.run(
                [str(binary_path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(run_result.returncode, 0, run_result.stdout)

        generated = self.generated
        binding = generated.find_transition_binding(
            generated.GoalType.InvestigateDisturbance,
            generated.GoalPhase.Navigate,
            1,
        )
        policy = generated.phase_target_policy(
            generated.GoalType.InvestigateDisturbance,
            generated.GoalPhase.Search,
        )
        expected = ",".join(
            (
                str(int(generated.GoalType.IdleObserve)),
                str(len(generated.TRANSITION_BINDINGS)),
                str(generated.EXECUTABLE_TRANSITION_BINDING_COUNT),
                str(generated.PRODUCTION_SKILL_MASK),
                str(binding.accepted_skill_mask),
                str(binding.accepted_failure_mask),
                str(int(policy.target_authority)),
                "1.5",
                str(len(generated.CANDIDATE_PAIR_FEATURE_WEIGHTS)),
            )
        )
        self.assertEqual(run_result.stdout, expected)


if __name__ == "__main__":
    unittest.main()
