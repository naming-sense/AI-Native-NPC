from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml"
SKILL = ROOT / "contracts/current/skill_registry_v1.yaml"
GOAL = ROOT / "contracts/current/goal_registry_v1.yaml"
MODEL_DESCRIPTOR = ROOT / "generated/model/resolve_policy_model_descriptor_v1.json"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def transition_rows(goal_registry: dict, goal_name: str, phase_name: str) -> list[dict]:
    goal = next(row for row in goal_registry["goals"] if row["name"] == goal_name)
    return goal["phases"][phase_name]["transitions"]


def guard(contract: dict, name: str) -> dict:
    return next(row for row in contract["guard_authorities"] if row["guard"] == name)


class ProductionResolveV1MachineContractTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.schema = load_yaml(SCHEMA)
        self.skill = load_yaml(SKILL)
        self.goal = load_yaml(GOAL)
        self.execution = self.skill["execution_semantics_v1"]
        self.gameplay = self.goal["goal_gameplay_semantics_v1"]

    def test_rc6_bundle_versions_move_together_without_resizing_fixed_layout(self) -> None:
        self.assertEqual(self.schema["schema"]["contract_revision"], "2.0.0-rc6")
        self.assertEqual(self.schema["schema"]["release_stage"], "rc6")
        self.assertEqual(self.schema["schema"]["bundle_version"], "0.4.7")
        self.assertEqual(self.schema["constants"]["schema_contract_revision"], "2.0.0-rc6")
        self.assertEqual(self.schema["constants"]["skill_registry_version"], "1.1.0")
        self.assertEqual(self.schema["constants"]["goal_registry_version"], "1.2.0")
        self.assertEqual(self.skill["registry"]["version"], "1.1.0")
        self.assertEqual(self.skill["registry"]["contract_revision"], "2.0.0-rc6")
        self.assertEqual(self.execution["version"], "1.1.0")
        self.assertEqual(self.goal["registry"]["version"], "1.2.0")
        self.assertEqual(self.goal["registry"]["contract_revision"], "2.0.0-rc6")
        self.assertEqual(self.gameplay["version"], "1.2.0")
        self.assertEqual(self.schema["constants"]["total_target_slots"], 17)
        self.assertEqual(self.schema["constants"]["candidate_count"], 272)

    def test_greet_is_the_only_new_production_action_and_has_exact_effect_contract(self) -> None:
        self.assertEqual(
            self.gameplay["production_skills"],
            {
                "executable": ["Idle", "TurnTo", "Approach", "Investigate", "SearchArea", "Greet"],
                "control": "ContinueCurrentAction",
                "resolve_action": "Greet",
                "resolve_control_policy": "exact_current_running_greet_only",
                "all_others_policy": "hard_mask_false_even_if_precondition_true",
            },
        )
        self.assertNotIn("Warn", self.gameplay["production_skills"]["executable"])
        self.assertNotIn("CallForHelp", self.gameplay["production_skills"]["executable"])
        self.assertNotIn("Attack", self.gameplay["production_skills"]["executable"])

        greet = self.execution["skills"]["Greet"]
        self.assertEqual(greet["skill_id"], 10)
        self.assertEqual(greet["target_kind"], "Entity")
        self.assertTrue(greet["requires_los"])
        self.assertEqual(greet["active_parameter_slots"], {"duration": 0, "intensity": 3})
        self.assertEqual(greet["inactive_parameter_slots"], [1, 2])
        self.assertEqual(greet["inactive_parameter_value"], 0.0)
        self.assertEqual(greet["duration_seconds"], {"min": 1.0, "max": 5.0, "default": 2.0})
        self.assertEqual(greet["intensity"], {"min": 0.0, "max": 1.0, "default": 0.5})
        self.assertEqual(
            greet["gameplay_effect"],
            {
                "focus_target": "exact_entity_actor",
                "social_signal": "server_authoritative_greet_one_shot",
                "cue": "source_guard_world_space_visible",
                "cue_base_visible_at_zero_intensity": True,
                "presentation_strength": "clamp_intensity_zero_one",
                "target_receiver_component_required": False,
            },
        )
        self.assertEqual(greet["duplicate_policy"]["scope"], "pawn_session")
        self.assertEqual(greet["duplicate_policy"]["decision_rule"], "strictly_greater_than_highest_applied")
        self.assertEqual(greet["duplicate_policy"]["guarantee"], "in_process_session_lifetime_at_most_once")
        self.assertEqual(greet["event_exclusivity"]["target_invalid_producer_event"], "TargetInvalidated")
        self.assertTrue(greet["event_exclusivity"]["same_cause_skill_failed_forbidden"])

    def test_resolve_rollout_budget_fallback_and_retry_are_exact(self) -> None:
        policy = self.gameplay["general_policy_orchestration"]
        self.assertEqual(
            policy["production_neural_rollout_scope"],
            {
                "profile_id": "GuardPhase0",
                "goal": "InvestigateDisturbance",
                "phase": "Resolve",
                "out_of_scope_primary": "GeneratedUtilityProfile",
            },
        )
        self.assertEqual(policy["evaluator_statuses"], ["Selected", "Unavailable", "Failed", "Abstained", "Invalid"])
        self.assertEqual(policy["neural_budget_ms"], 20)
        self.assertEqual(policy["total_decision_deadline_ms"], 40)
        self.assertEqual(policy["fallback_on"], ["Unavailable", "Failed", "Abstained", "Invalid"])
        self.assertEqual(policy["fallback_within_deadline_utility_calls"], 1)
        self.assertEqual(policy["fallback_after_deadline_utility_calls"], 0)
        self.assertEqual(
            policy["single_valid_calibration"],
            {
                "second_adjusted_score": "selected_adjusted_score",
                "adjusted_gap": "positive_zero",
                "normalized_entropy": "zero",
            },
        )
        scheduling = self.gameplay["decision_scheduling"]
        self.assertEqual(scheduling["total_decision_deadline_ms"], 40)
        self.assertEqual(scheduling["stale_result_reuse_policy"], "forbidden")
        self.assertEqual(
            scheduling["fresh_snapshot_retry"],
            {
                "schedule": "next_tick",
                "max_attempts_per_goal_revision": 1,
                "second_stale_policy": "wait_for_authoritative_goal_or_knowledge_change",
                "primary_entity_invalid_policy": "generated_target_invalidated_not_stale_retry",
            },
        )

    def test_resolve_generated_guards_and_transitions_are_fully_executable(self) -> None:
        self.assertEqual(
            self.gameplay["scope"]["claims"],
            {
                "executable_unique_guards": 14,
                "unavailable_unique_guards": 0,
                "executable_transition_bindings": 18,
                "unavailable_transition_bindings": 0,
                "effects": 2,
                "production_executable_skills": 6,
                "full_guard_catalog_pass": True,
            },
        )
        rows = transition_rows(self.goal, "InvestigateDisturbance", "Resolve")
        self.assertEqual(
            rows,
            [
                {
                    "order": 0,
                    "trigger": {"kind": "event", "event_type": "SkillSucceeded"},
                    "guard": "resolution_complete",
                    "to_phase": "Return",
                },
                {
                    "order": 1,
                    "trigger": {"kind": "event", "event_type": "TargetInvalidated"},
                    "guard": "identified_subject_invalid_recoverable",
                    "to_phase": "Search",
                },
                {
                    "order": 2,
                    "trigger": {"kind": "event", "event_type": "TargetInvalidated"},
                    "guard": "identified_subject_invalid_unrecoverable",
                    "terminal": "Failed",
                },
                {
                    "order": 3,
                    "trigger": {"kind": "event", "event_type": "SkillFailed"},
                    "guard": "resolution_failed",
                    "terminal": "Failed",
                },
            ],
        )
        expected = {
            "resolution_complete": (
                "SkillExecutor",
                ["Greet"],
                [],
                [
                    "ExactCurrentGoalToken",
                    "ExactCurrentDecisionId",
                    "ExactTargetIdentityAndRevision",
                    "CurrentIdentifiedSubjectBindingSatisfiesEntityRevisionRule",
                    "CurrentIdentifiedSubjectVisibleSameWorldAndLos",
                    "ExecutionStatusSucceeded",
                ],
            ),
            "identified_subject_invalid_recoverable": (
                "GoalAuthority",
                [],
                [],
                [
                    "ExactCurrentGoalToken",
                    "ExactCurrentPrimaryTarget",
                    "GoalOwnedIdentifiedSubjectResolverCannotResolve",
                    "GoalOwnedDisturbancePositionResolvable",
                ],
            ),
            "identified_subject_invalid_unrecoverable": (
                "GoalAuthority",
                [],
                [],
                [
                    "ExactCurrentGoalToken",
                    "ExactCurrentPrimaryTarget",
                    "GoalOwnedIdentifiedSubjectResolverCannotResolve",
                    "GoalOwnedDisturbancePositionCannotResolve",
                ],
            ),
            "resolution_failed": (
                "SkillExecutor",
                ["Greet"],
                ["TimedOut", "AuthorityLost", "AssemblyInvalidated"],
                [
                    "ExactCurrentGoalToken",
                    "ExactCurrentDecisionId",
                    "ExactTargetIdentityAndRevision",
                    "CurrentIdentifiedSubjectBindingSatisfiesEntityRevisionRule",
                    "CurrentIdentifiedSubjectVisibleSameWorldAndLos",
                    "ExecutionStatusFailed",
                    "ExactFailureReason",
                ],
            ),
        }
        for name, (source, skills, failures, requirements) in expected.items():
            authority = guard(self.gameplay, name)
            self.assertEqual(authority["availability"], "executable")
            self.assertEqual(len(authority["bindings"]), 1)
            binding = authority["bindings"][0]
            self.assertEqual(binding["fact_source"], source)
            self.assertEqual(binding["accepted_skills"], skills)
            self.assertEqual(binding["accepted_target_kinds"], ["Entity"])
            self.assertEqual(binding["target_authorities"], ["IdentifiedSubject"])
            self.assertEqual(binding["accepted_failure_reasons"], failures)
            self.assertEqual(binding["requirements"], requirements)

    def test_schema_has_exact_ten_inputs_three_outputs_and_generated_descriptor(self) -> None:
        self.assertEqual(
            list(self.schema["tensors"]),
            [
                "global_state",
                "target_features",
                "target_kind_ids",
                "target_mask",
                "event_features",
                "event_type_ids",
                "event_target_slots",
                "event_mask",
                "candidate_pair_features",
                "candidate_mask",
            ],
        )
        self.assertEqual(
            list(self.schema["outputs"]),
            ["candidate_raw_scores", "candidate_parameter_proposals", "tactical_context"],
        )
        self.assertEqual(self.schema["outputs"]["tactical_context"], {
            "shape": ["B", 128],
            "dtype": "float32",
            "valid_range": [-1.0, 1.0],
            "meaning": "calibration and OOD context, never an action authority",
        })
        descriptor = json.loads(MODEL_DESCRIPTOR.read_text(encoding="utf-8"))
        self.assertEqual(descriptor["contract_revision"], "2.0.0-rc6")
        self.assertEqual(descriptor["batch_size"], 1)
        self.assertEqual([row["name"] for row in descriptor["inputs"]], list(self.schema["tensors"]))
        self.assertEqual([row["name"] for row in descriptor["outputs"]], list(self.schema["outputs"]))
        canonical = json.dumps(
            {key: value for key, value in descriptor.items() if key != "model_contract_sha256"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(descriptor["model_contract_sha256"], hashlib.sha256(canonical).hexdigest())


if __name__ == "__main__":
    unittest.main()
