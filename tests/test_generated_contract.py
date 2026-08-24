from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tools.contractlib import default_paths, validate_contracts  # noqa: E402
GEN = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
CONTRACT_LOCK = ROOT / "generated/contract-lock.json"
UNREAL_GENERATED = Path("/mnt/d/Codex-cli/NeuralProject/NeuralGame/Source/NeuralGame/AINativeNPC/Generated")
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

    def test_contract_revision(self) -> None:
        self.assertEqual(self.discrete["contract_revision"], g.CONTRACT_REVISION)
        self.assertEqual(self.discrete["schema_source_sha256"], g.SCHEMA_SOURCE_SHA256)

    def test_contract_lock_binds_current_sources_and_unreal_copies(self) -> None:
        lock = json.loads(CONTRACT_LOCK.read_text(encoding="utf-8"))
        source_paths = {
            "contracts/current/ai_native_npc_schema_v2_0.yaml": ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml",
            "contracts/current/goal_registry_v1.yaml": ROOT / "contracts/current/goal_registry_v1.yaml",
            "contracts/current/skill_registry_v1.yaml": ROOT / "contracts/current/skill_registry_v1.yaml",
            "contracts/current/test_case_catalog_v1.yaml": ROOT / "contracts/current/test_case_catalog_v1.yaml",
            "contracts/current/test_taxonomy_v1.yaml": ROOT / "contracts/current/test_taxonomy_v1.yaml",
        }
        for relative, path in source_paths.items():
            self.assertEqual(lock["source_contracts"][relative]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        for name in (
            "AINativeNPCContracts.generated.h",
            "AINativeNPCGoalGameplaySemantics.generated.h",
            "AINativeNPCSkillExecutionSemantics.generated.h",
        ):
            repository = ROOT / "generated/cpp" / name
            unreal = UNREAL_GENERATED / name
            self.assertEqual(repository.read_bytes(), unreal.read_bytes(), name)
            self.assertEqual(lock["generated_files"][name], hashlib.sha256(repository.read_bytes()).hexdigest())
        self.assertEqual(CONTRACT_LOCK.read_bytes(), (UNREAL_GENERATED / "contract-lock.json").read_bytes())
        promotion_authority = "AINativeNPCResolvePolicyPromotion.generated.h"
        self.assertEqual(
            (ROOT / "generated/cpp" / promotion_authority).read_bytes(),
            (UNREAL_GENERATED / promotion_authority).read_bytes(),
            promotion_authority,
        )

    def test_validator_rejects_extra_or_mistyped_model_interface_entries(self) -> None:
        def extra_input(schema: dict) -> None:
            schema["tensors"]["forged_input"] = deepcopy(schema["tensors"]["candidate_mask"])

        def extra_output(schema: dict) -> None:
            schema["outputs"]["forged_output"] = {"shape": ["B", 1], "dtype": "float32"}

        def raw_score_wrong_dtype(schema: dict) -> None:
            schema["outputs"]["candidate_raw_scores"]["dtype"] = "int64"

        def parameter_wrong_dtype(schema: dict) -> None:
            schema["outputs"]["candidate_parameter_proposals"]["dtype"] = "bool"

        cases = [
            ("extra input", extra_input, "tensor key order/cardinality mismatch"),
            ("extra output", extra_output, "output key order/cardinality mismatch"),
            ("raw-score dtype", raw_score_wrong_dtype, "candidate_raw_scores dtype mismatch"),
            ("parameter dtype", parameter_wrong_dtype, "candidate_parameter_proposals dtype mismatch"),
        ]
        for label, mutate, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                shutil.copytree(ROOT / "contracts/current", root / "contracts/current")
                schema_path = root / "contracts/current/ai_native_npc_schema_v2_0.yaml"
                schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
                mutate(schema)
                schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
                errors = validate_contracts(default_paths(root))
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_catalog_and_taxonomy_are_first_class_cross_validated_sources(self) -> None:
        lock = json.loads(CONTRACT_LOCK.read_text(encoding="utf-8"))
        for relative in (
            "contracts/current/test_case_catalog_v1.yaml",
            "contracts/current/test_taxonomy_v1.yaml",
        ):
            path = ROOT / relative
            self.assertEqual(lock["source_contracts"][relative]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(
            g.TEST_CASE_CATALOG_SHA256,
            hashlib.sha256((ROOT / "contracts/current/test_case_catalog_v1.yaml").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            g.TEST_TAXONOMY_SHA256,
            hashlib.sha256((ROOT / "contracts/current/test_taxonomy_v1.yaml").read_bytes()).hexdigest(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shutil.copytree(ROOT / "contracts/current", root / "contracts/current")
            catalog_path = root / "contracts/current/test_case_catalog_v1.yaml"
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
            catalog["resolve_policy_v1"]["groups"][0]["minimum_cases"] = 63
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")
            errors = validate_contracts(default_paths(root))
            self.assertTrue(any("Resolve policy catalog/taxonomy" in error for error in errors), errors)

    def test_catalog_and_taxonomy_registered_semantics_are_fail_closed(self) -> None:
        def verify(relative: str, mutate, expected: str) -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                shutil.copytree(ROOT / "contracts/current", root / "contracts/current")
                path = root / relative
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                mutate(document)
                path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
                errors = validate_contracts(default_paths(root))
                self.assertTrue(any(expected in error for error in errors), errors)

        verify(
            "contracts/current/test_case_catalog_v1.yaml",
            lambda document: document["resolve_policy_v1"]["groups"][0].pop("expected_status"),
            "Resolve policy catalog semantics fingerprint mismatch",
        )
        verify(
            "contracts/current/test_case_catalog_v1.yaml",
            lambda document: document["resolve_policy_v1"]["groups"][0].update(expected_goal_result="forged"),
            "Resolve policy catalog semantics fingerprint mismatch",
        )
        verify(
            "contracts/current/test_taxonomy_v1.yaml",
            lambda document: document["resolve_policy_v1"].update(label_fields=[]),
            "Resolve policy taxonomy semantics fingerprint mismatch",
        )
        verify(
            "contracts/current/test_case_catalog_v1.yaml",
            lambda document: document.update(split_contract={
                "train": 0.25,
                "calibration": 0.25,
                "general_test": 0.25,
                "ood_test": 0.25,
                "isolation_key": "scenario_seed",
                "overlap_policy": "forbidden",
            }),
            "Resolve policy split semantics fingerprint mismatch",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shutil.copytree(ROOT / "contracts/current", root / "contracts/current")
            taxonomy_path = root / "contracts/current/test_taxonomy_v1.yaml"
            catalog_path = root / "contracts/current/test_case_catalog_v1.yaml"
            taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
            taxonomy["resolve_policy_v1"]["split_isolation_key"] = "arbitrary"
            catalog["split_contract"]["isolation_key"] = "arbitrary"
            taxonomy_path.write_text(yaml.safe_dump(taxonomy, sort_keys=False), encoding="utf-8")
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")
            errors = validate_contracts(default_paths(root))
            self.assertTrue(any("semantics fingerprint mismatch" in error for error in errors), errors)

    def test_current_docs_scope_test_case_catalog_without_future_or_critical_overclaim(self) -> None:
        technical = (ROOT / "docs/current/technical-requirements.md").read_text(encoding="utf-8")
        requirements = (ROOT / "docs/current/requirements.md").read_text(encoding="utf-8")
        self.assertIn("contracts/current/test_case_catalog_v1.yaml", requirements)
        self.assertIn("현재 Catalog의 범위는 Resolve policy case group과 split contract", technical)
        self.assertIn("OOD/Critical fixture allowlist를 소유하지 않는다", technical)
        self.assertNotIn("후속 machine-readable `test_case_catalog_v1.yaml`", technical)
        self.assertNotIn("case catalog를 추가할 때", technical)

    def test_production_resolve_plan_reports_implemented_core_and_dormant_rollout(self) -> None:
        plan = (ROOT / "docs/current/production-resolve-v1-implementation-plan.md").read_text(
            encoding="utf-8")
        self.assertIn("**상태:** 핵심 코드 구현 완료, production rollout 대기", plan)
        self.assertIn("현재 없는 production rollout 요소", plan)
        self.assertIn("generated promotion authority는 `Approved=false`", plan)
        self.assertNotIn("**상태:** 구현 전 확정", plan)
        self.assertNotIn("production evaluator/Greet source, RC6 generated contract와 asset은 아직 변경하지 않는다", plan)

    def test_current_docs_do_not_reintroduce_superseded_rc5_or_missing_core_claims(self) -> None:
        documents = {
            name: (ROOT / "docs/current" / name).read_text(encoding="utf-8")
            for name in (
                "contract-appendices.md",
                "implementation-plan.md",
                "production-resolve-v1-implementation-plan.md",
                "technical-requirements.md",
                "unreal-implementation-plan.md",
            )
        }
        stale_claims = {
            "technical-requirements.md": (
                "`ACTIVE RC5`",
                "`POST-RC5`",
                "현재 RC5 Schema Appendix는 앞의 두 output만 포함한다",
                "| `SCHEMA-OUTPUT-001` | output 2개 |",
                "| `TEST-CATALOG-001` | family taxonomy만 존재 |",
            ),
            "implementation-plan.md": (
                "문서 확정, 구현 대기",
                "Production Neural evaluator와 production-executable Resolve Skill은 아직 없으므로",
                "`tactical_context [B,128]` output을 Schema·ONNX·ORT·NNE descriptor에 연결",
            ),
            "contract-appendices.md": (
                "ONNX/NNE/OOD evaluator와 production-executable Resolve Skill이 없으므로",
                "현재 실제 ModelData·NNE adapter·OOD·Calibration asset은 없다",
            ),
            "production-resolve-v1-implementation-plan.md": (
                "현재 project에는 `NNERuntimeORT` plugin이 활성화돼 있지 않으므로",
            ),
            "unreal-implementation-plan.md": (
                "현재 project는 `NNERuntimeORT` plugin을 enable하지 않았으며",
            ),
        }
        for name, claims in stale_claims.items():
            for claim in claims:
                with self.subTest(document=name, claim=claim):
                    self.assertNotIn(claim, documents[name])

    def test_contract_appendix_generated_block_matches_current_schema_reference(self) -> None:
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
        contract = schema["documentation_contract"]
        begin = contract["marker_begin"]
        end = contract["marker_end"]
        appendix = (ROOT / "docs/current/contract-appendices.md").read_text(encoding="utf-8")
        expected = f"{begin}\n{(ROOT / contract['generated_reference']).read_text(encoding='utf-8').rstrip()}\n{end}"
        start = appendix.index(begin)
        finish = appendix.index(end, start) + len(end)
        self.assertEqual(appendix[start:finish], expected)

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


if __name__ == "__main__":
    unittest.main()
