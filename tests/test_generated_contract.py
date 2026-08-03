from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
spec = importlib.util.spec_from_file_location("ai_native_npc_contracts_generated_test", GEN)
assert spec and spec.loader
g = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = g
spec.loader.exec_module(g)


class ContractGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.discrete = json.loads((ROOT / "tests/golden/discrete_hash_vectors.json").read_text(encoding="utf-8"))
        cls.normalizers = json.loads((ROOT / "tests/golden/normalizer_vectors.json").read_text(encoding="utf-8"))

    def test_boss_pattern_generated_bindings_exist(self) -> None:
        self.assertTrue((ROOT / "generated/python/ai_native_npc_boss_pattern_contracts_generated.py").is_file())
        self.assertTrue((ROOT / "generated/cpp/AINativeNPCBossPatternContracts.generated.h").is_file())
        self.assertTrue((ROOT / "generated/docs/boss_pattern_reference.md").is_file())

    def test_boss_pattern_hash_vectors(self) -> None:
        boss_gen = ROOT / "generated/python/ai_native_npc_boss_pattern_contracts_generated.py"
        boss_spec = importlib.util.spec_from_file_location("ai_native_npc_boss_pattern_contracts_generated_test", boss_gen)
        assert boss_spec and boss_spec.loader
        boss = importlib.util.module_from_spec(boss_spec)
        sys.modules[boss_spec.name] = boss
        boss_spec.loader.exec_module(boss)
        fixture = json.loads((ROOT / "tests/golden/boss_pattern_hash_vectors.json").read_text(encoding="utf-8"))
        self.assertEqual(boss.CONSTANTS["max_pattern_slots"], 32)
        self.assertEqual(boss.PatternParameter.reserved_zero, 3)
        self.assertEqual(boss.ExecutionPhase.PreAttackTurn, 1)
        self.assertEqual(boss.PATTERN_PARAMETERS[0]["name"], "tracking_fraction")
        self.assertEqual(boss.PATTERN_PARAMETERS[3]["authority"], "none")
        self.assertEqual(boss.TENSOR_SHAPES["pattern_mask"], ["B", 32])
        self.assertAlmostEqual(boss.normalize_feature("pattern_context", boss.PatternContextFeature.target_distance_planar, 5000.0), 0.5)
        self.assertAlmostEqual(boss.normalize_feature("pattern_context", boss.PatternContextFeature.target_relative_speed, -1000.0), -0.5)
        self.assertAlmostEqual(boss.normalize_feature("pattern_features", boss.PatternFeature.telegraph_duration, 15.0), 0.5)
        self.assertEqual(boss.normalize_feature("pattern_pair_features", boss.PatternPairFeature.distance_fit, 1.5), 1.0)
        self.assertEqual(boss.normalize_feature("pattern_features", boss.PatternFeature.reserved_zero, 999.0), 0.0)
        with self.assertRaises(ValueError):
            boss.normalize_feature("pattern_context", 0, math.nan)
        vector = fixture["candidate_set"]
        handle = boss.TargetHandle(**vector["attack_target_handle"])
        raw = boss.pattern_candidate_set_canonical_bytes(
            vector["pattern_asset_bundle_sha256"],
            vector["pattern_ids"],
            vector["pattern_mask"],
            handle,
            vector["selection_boundary"],
            vector["boss_phase_revision"],
            vector["combat_state_revision"],
        )
        self.assertEqual(raw.hex(), vector["canonical_bytes_hex"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), vector["sha256"])
        unsorted_ids = list(vector["pattern_ids"])
        unsorted_ids[0], unsorted_ids[1] = unsorted_ids[1], unsorted_ids[0]
        with self.assertRaises(ValueError):
            boss.validate_pattern_slot_layout(unsorted_ids, list(vector["pattern_mask"]))
        padding_mask = list(vector["pattern_mask"])
        padding_mask[-1] = True
        with self.assertRaises(ValueError):
            boss.validate_pattern_slot_layout(list(vector["pattern_ids"]), padding_mask)
        non_bool_mask = list(vector["pattern_mask"])
        non_bool_mask[0] = 1
        with self.assertRaises(ValueError):
            boss.validate_pattern_slot_layout(list(vector["pattern_ids"]), non_bool_mask)
        all_padding_ids = [boss.CONSTANTS["invalid_pattern_id"]] * boss.CONSTANTS["max_pattern_slots"]
        all_padding_mask = [False] * boss.CONSTANTS["max_pattern_slots"]
        with self.assertRaises(ValueError):
            boss.validate_pattern_slot_layout(all_padding_ids, all_padding_mask)
        with self.assertRaises(ValueError):
            boss.pattern_candidate_set_canonical_bytes(
                vector["pattern_asset_bundle_sha256"], all_padding_ids, all_padding_mask, handle,
                vector["selection_boundary"], vector["boss_phase_revision"], vector["combat_state_revision"],
            )
        decision = fixture["decision_contract"]
        decision_raw = boss.boss_pattern_decision_contract_canonical_bytes(decision["digests"])
        self.assertEqual(decision_raw.hex(), decision["canonical_bytes_hex"])
        self.assertEqual(hashlib.sha256(decision_raw).hexdigest(), decision["sha256"])

    def test_contract_revision(self) -> None:
        self.assertEqual(self.discrete["contract_revision"], g.CONTRACT_REVISION)
        self.assertEqual(self.discrete["schema_source_sha256"], g.SCHEMA_SOURCE_SHA256)

    def test_candidate_formula(self) -> None:
        self.assertEqual(g.candidate_index(15, 16), 271)
        with self.assertRaises(ValueError):
            g.candidate_index(16, 0)

    def test_discrete_hash_vectors(self) -> None:
        for vector in self.discrete["vectors"]:
            handles = [g.TargetHandle(**h) for h in vector["handles"]]
            target_mask = vector["target_mask"]
            candidate_mask = [False] * 272
            for index in vector["candidate_mask_true_indices"]:
                candidate_mask[index] = True
            self.assertEqual(g.pack_bits_lsb_first(target_mask, 17).hex(), vector["target_mask_bytes_hex"], vector["name"])
            self.assertEqual(g.pack_bits_lsb_first(candidate_mask, 272).hex(), vector["candidate_mask_bytes_hex"], vector["name"])
            raw = g.candidate_set_canonical_bytes(handles, target_mask, candidate_mask)
            self.assertEqual(raw.hex(), vector["canonical_bytes_hex"], vector["name"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), vector["sha256"], vector["name"])

    def test_decision_contract_hash(self) -> None:
        vector = self.discrete["decision_contract"]
        raw = g.decision_contract_canonical_bytes(vector["digests"])
        self.assertEqual(raw.hex(), vector["canonical_bytes_hex"])
        self.assertEqual(g.decision_contract_hash(vector["digests"]), vector["sha256"])

    def test_quantization(self) -> None:
        functions = {
            "confidence": g.quantize_confidence,
            "age_seconds": g.quantize_age_seconds,
            "distance_cm": g.quantize_distance_cm,
            "loudness": g.quantize_loudness,
        }
        for name, rows in self.discrete["slotter_quantization"].items():
            for row in rows:
                self.assertEqual(functions[name](row["input"]), row["expected"], (name, row))

    def test_parameter_decode_and_clamp(self) -> None:
        for row in self.discrete["parameter_decode"]:
            self.assertAlmostEqual(
                g.decode_parameter(row["skill_id"], row["slot"], row["normalized"]),
                row["expected"],
                places=12,
            )

    def test_normalizer_vectors(self) -> None:
        abs_tol = self.normalizers["abs_tolerance"]
        rel_tol = self.normalizers["rel_tolerance"]
        table_functions = {
            "global": g.normalize_global,
            "target_common": g.normalize_target_common,
            "event": g.normalize_event,
            "candidate_pair": g.normalize_candidate_pair,
        }
        for row in self.normalizers["vectors"]:
            if row["table"] == "target_payload":
                actual = g.normalize_target_payload(row["kind"], row["index"], row["value"], row["sentinel_matched"])
            else:
                actual = table_functions[row["table"]](row["index"], row["value"], row["sentinel_matched"])
            self.assertTrue(
                math.isclose(actual, row["expected"], abs_tol=abs_tol, rel_tol=rel_tol),
                (row, actual),
            )

    def test_schema_reference_d_headings_are_unique_and_contiguous(self) -> None:
        reference = (ROOT / "generated/docs/schema_reference.md").read_text(encoding="utf-8")
        section_numbers = re.findall(r"^### D\.(\d+) ", reference, flags=re.MULTILINE)
        self.assertEqual(section_numbers, [str(value) for value in range(1, len(section_numbers) + 1)])
        self.assertEqual(len(section_numbers), len(set(section_numbers)))
        self.assertIn("### D.3 Hash: candidate_set_hash", reference)
        self.assertIn("### D.4 Hash: decision_contract_hash", reference)
        self.assertIn("### D.5 Normalizer 의미 규칙", reference)


if __name__ == "__main__":
    unittest.main()
