from __future__ import annotations

import hashlib
import importlib.util
import math
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "contracts/current/skill_registry_v1.yaml"
GENERATOR = ROOT / "tools/generate_skill_execution_semantics_v1.py"
GENERATED_PY = ROOT / "generated/python/ai_native_npc_skill_execution_semantics_generated.py"
GENERATED_CPP = ROOT / "generated/cpp/AINativeNPCSkillExecutionSemantics.generated.h"
GENERATED_DOC = ROOT / "generated/docs/skill_execution_semantics_v1.md"
MONOLITHIC_PY = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
MONOLITHIC_CPP = ROOT / "generated/cpp/AINativeNPCContracts.generated.h"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ApprovedExecutionSemanticsContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_yaml(REGISTRY)

    def test_common_contract_is_exact(self) -> None:
        common = self.registry["execution_semantics_v1"]["common"]
        self.assertEqual(common["authority"], "server_game_thread")
        self.assertEqual(common["target_position_policy"], "recapture_at_execution_start_then_freeze")
        self.assertEqual(common["evaluation_interval_seconds"], 0.05)
        self.assertEqual(
            common["intensity_speed_multiplier"],
            {
                "formula": "base_plus_scale_times_intensity",
                "base": 0.5,
                "scale": 0.5,
                "input_min": 0.0,
                "input_max": 1.0,
                "output_min": 0.5,
                "output_max": 1.0,
            },
        )
        self.assertEqual(common["same_time_resolution"], "success_before_timeout")
        self.assertEqual(common["new_perception_policy"], "knowledge_only_until_next_selection")
        self.assertEqual(common["decision_record_v2_layout"], "unchanged")
        self.assertEqual(common["tensor_contract"], "unchanged")
        self.assertEqual(
            common["navigation"],
            {
                "path_mode": "complete_path_only",
                "allow_partial_path": False,
                "projection_horizontal_cm": 100.0,
                "projection_vertical_cm": 200.0,
                "include_agent_radius_in_acceptance": False,
                "include_goal_radius_in_acceptance": False,
            },
        )

    def test_local_failure_reasons_are_exact(self) -> None:
        self.assertEqual(
            self.registry["execution_semantics_v1"]["local_failure_reasons"],
            [
                "TargetInvalid",
                "TargetUnsupported",
                "PathUnavailable",
                "TimedOut",
                "MovementModeUnsupported",
                "AuthorityLost",
                "AssemblyInvalidated",
                "Interrupted",
            ],
        )

    def test_turn_to_contract_is_exact(self) -> None:
        skill = self.registry["execution_semantics_v1"]["skills"]["TurnTo"]
        self.assertEqual(skill["skill_id"], 3)
        self.assertEqual(skill["target_position_policy"], "frozen_execution_start_position")
        self.assertEqual(skill["planar_coincident_distance_cm"], 1.0)
        self.assertEqual(skill["facing_tolerance_degrees"], 5.0)
        self.assertEqual(skill["success_stable_seconds"], 0.10)
        self.assertEqual(skill["rotation_axis"], "yaw_only")
        self.assertEqual(skill["root_motion_policy"], "fail_movement_mode_unsupported")
        self.assertEqual(skill["timeout_result"], "TimedOut")

    def test_approach_contract_is_exact(self) -> None:
        skill = self.registry["execution_semantics_v1"]["skills"]["Approach"]
        self.assertEqual(skill["skill_id"], 4)
        self.assertEqual(skill["target_position_policy"], "frozen_execution_start_position")
        self.assertEqual(skill["success_distance"], "planar_center_to_frozen_target_lte_preferred_distance")
        self.assertEqual(skill["already_inside_policy"], "succeed_without_move")
        self.assertEqual(skill["completion_recheck"], "recompute_planar_distance")
        self.assertEqual(skill["path_failure_result"], "PathUnavailable")
        self.assertEqual(skill["timeout_result"], "TimedOut")

    def test_investigate_contract_is_exact(self) -> None:
        skill = self.registry["execution_semantics_v1"]["skills"]["Investigate"]
        self.assertEqual(skill["skill_id"], 8)
        self.assertEqual(skill["target_position_policy"], "frozen_execution_start_position")
        self.assertEqual(skill["distance_condition"], "planar_distance_lte_preferred_distance")
        self.assertEqual(skill["facing_tolerance_degrees"], 15.0)
        self.assertEqual(skill["success_stable_seconds"], 0.50)
        self.assertEqual(skill["condition_loss_policy"], "reset_stable_time_to_zero")
        self.assertEqual(skill["base_turn_speed_degrees_per_second"], 360.0)
        self.assertEqual(skill["success_meaning"], "arrived_faced_and_observed_not_evidence_found")
        self.assertEqual(skill["path_failure_result"], "PathUnavailable")
        self.assertEqual(skill["timeout_result"], "TimedOut")

    def test_search_area_contract_is_exact(self) -> None:
        skill = self.registry["execution_semantics_v1"]["skills"]["SearchArea"]
        self.assertEqual(skill["skill_id"], 9)
        self.assertEqual(skill["target_position_policy"], "frozen_execution_start_center")
        self.assertEqual(skill["basis"], "world_positive_x_positive_y")
        self.assertEqual(skill["point_acceptance_radius_cm"], 100.0)
        self.assertEqual(skill["revisit_policy"], "no_revisit_per_execution")
        self.assertEqual(skill["invalid_point_policy"], "skip")
        self.assertEqual(skill["all_points_invalid_result"], "PathUnavailable")
        self.assertEqual(skill["deadline_without_visited_point_result"], "TimedOut")
        self.assertEqual(skill["success_meaning"], "allocated_area_checked_not_evidence_found")
        offsets = skill["normalized_offsets"]
        self.assertEqual(len(offsets), 9)
        expected = [
            [0.0, 0.0],
            [0.5, 0.0],
            [0.0, 0.5],
            [-0.5, 0.0],
            [0.0, -0.5],
            [math.sqrt(0.5), math.sqrt(0.5)],
            [-math.sqrt(0.5), math.sqrt(0.5)],
            [-math.sqrt(0.5), -math.sqrt(0.5)],
            [math.sqrt(0.5), -math.sqrt(0.5)],
        ]
        for actual, wanted in zip(offsets, expected, strict=True):
            self.assertTrue(math.isclose(actual[0], wanted[0], abs_tol=1e-12))
            self.assertTrue(math.isclose(actual[1], wanted[1], abs_tol=1e-12))
        for x, y in offsets[5:]:
            self.assertTrue(math.isclose(math.hypot(x, y), 1.0, abs_tol=1e-12))

    def test_skill_ids_and_parameter_ranges_stay_bound_to_registry_rows(self) -> None:
        by_name = {row["name"]: row for row in self.registry["skills"]}
        expected_ids = {"TurnTo": 3, "Approach": 4, "Investigate": 8, "SearchArea": 9}
        expected_ranges = {
            "TurnTo": [(0.25, 2.0, 0.75), (90.0, 720.0, 360.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.5)],
            "Approach": [(0.5, 10.0, 3.0), (150.0, 600.0, 350.0), (100.0, 500.0, 200.0), (0.0, 1.0, 0.5)],
            "Investigate": [(1.0, 12.0, 5.0), (100.0, 500.0, 280.0), (100.0, 1200.0, 400.0), (0.0, 1.0, 0.6)],
            "SearchArea": [(3.0, 20.0, 8.0), (80.0, 400.0, 220.0), (200.0, 2000.0, 700.0), (0.0, 1.0, 0.6)],
        }
        for name, skill_id in expected_ids.items():
            self.assertEqual(by_name[name]["id"], skill_id)
            actual = [(p["min"], p["max"], p["default"]) for p in by_name[name]["parameters"]]
            self.assertEqual(actual, expected_ranges[name])

    def test_generator_validator_rejects_hostile_mutations(self) -> None:
        generator = import_path("skill_execution_semantics_generator_test", GENERATOR)
        good = deepcopy(self.registry)
        self.assertEqual(generator.validate_registry(good), [])

        bad = deepcopy(good)
        bad["execution_semantics_v1"]["common"]["intensity_speed_multiplier"]["base"] = 0.6
        self.assertIn("intensity multiplier contract mismatch", generator.validate_registry(bad))

        bad = deepcopy(good)
        bad["execution_semantics_v1"]["skills"]["SearchArea"]["normalized_offsets"][8] = [1.0, 1.0]
        self.assertIn("SearchArea normalized_offsets mismatch", generator.validate_registry(bad))

        bad = deepcopy(good)
        bad["execution_semantics_v1"]["skills"]["Approach"]["skill_id"] = 8
        self.assertIn("Approach skill_id mismatch", generator.validate_registry(bad))

    def test_generator_derives_runtime_target_policy_from_registry(self) -> None:
        generator = import_path("skill_execution_semantics_generator_target_policy_test", GENERATOR)
        mutated = deepcopy(self.registry)
        turn_row = next(row for row in mutated["skills"] if row["name"] == "TurnTo")
        turn_row["allowed_target_kinds"].append("CoverSlot")
        cpp = generator.generate_cpp(mutated, "0" * 64)
        turn_case = cpp.split("case SchemaV2::ESkillId::TurnTo:", 1)[1].split("case SchemaV2::ESkillId::Approach:", 1)[0]
        self.assertIn("SchemaV2::ETargetKind::CoverSlot", turn_case)
        self.assertNotIn("EXPECTED_COMMON", GENERATOR.read_text(encoding="utf-8"))
        self.assertNotIn("EXPECTED_SKILLS", GENERATOR.read_text(encoding="utf-8"))

    def test_generated_artifacts_match_registry_digest_and_checked_in_outputs(self) -> None:
        digest = hashlib.sha256(REGISTRY.read_bytes()).hexdigest()
        generated = import_path("skill_execution_semantics_generated_test", GENERATED_PY)
        self.assertEqual(generated.SKILL_REGISTRY_SHA256, digest)
        self.assertEqual(generated.EVALUATION_INTERVAL_SECONDS, 0.05)
        self.assertEqual(generated.effective_speed(360.0, 0.5), 270.0)
        self.assertEqual(generated.SKILL_EXECUTION_SEMANTICS[3]["facing_tolerance_degrees"], 5.0)
        self.assertEqual(len(generated.SKILL_EXECUTION_SEMANTICS[9]["normalized_offsets"]), 9)

        cpp = GENERATED_CPP.read_text(encoding="utf-8")
        doc = GENERATED_DOC.read_text(encoding="utf-8")
        self.assertIn(digest, cpp)
        self.assertIn(digest, doc)
        self.assertIn("TurnFacingToleranceDegrees = 5", cpp)
        self.assertIn("InvestigateSuccessStableSeconds = 0.5", cpp)
        self.assertIn("SearchPointCount = 9", cpp)
        self.assertIn("PRODUCTION AUTHORITY", doc)

        self.assertIn(digest, MONOLITHIC_CPP.read_text(encoding="utf-8"))
        self.assertIn(digest, MONOLITHIC_PY.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
