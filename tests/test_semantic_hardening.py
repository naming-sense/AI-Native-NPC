from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from contractlib import (  # noqa: E402
    collect_hash_magic_tokens,
    critical_suite_metrics,
    default_paths,
    load_contracts,
    sha256_file,
    validate_contracts,
    validate_generated_block,
    validate_manual_hash_literal_policy,
)
from generate_contracts import generate_cpp, generate_markdown, generate_python, generate_requirements_kpi, generate_unreal_kpi  # noqa: E402
from doc_harness import build_archive_catalog, source_file_map_text, validate_catalog_data  # noqa: E402


def different_identifier(current: str, existing: set[str] | None = None) -> str:
    existing = existing or set()
    base = f"{current}__semantic_probe"
    candidate = base
    suffix = 1
    while candidate == current or candidate in existing:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def different_ascii_same_length(current: str) -> str:
    if not current:
        raise ValueError("current magic must be non-empty")
    chars = list(current)
    replacement = "B" if chars[0] != "B" else "C"
    chars[0] = replacement
    candidate = "".join(chars)
    if candidate == current:
        raise AssertionError("mutation probe did not change magic")
    return candidate


class SemanticHardeningTests(unittest.TestCase):
    def test_boss_pattern_contract_path_is_required(self) -> None:
        paths = default_paths(ROOT)
        self.assertTrue(hasattr(paths, "boss_pattern_contract"))
        self.assertEqual(paths.boss_pattern_contract.name, "boss_pattern_contract_v1.yaml")
        self.assertTrue(paths.boss_pattern_contract.is_file())

    def _mutated_root(self, mutate) -> Path:
        temp = Path(tempfile.mkdtemp(prefix="ainpc-semantic-"))
        self.addCleanup(lambda: shutil.rmtree(temp, ignore_errors=True))
        target = temp / "contracts/current"
        target.mkdir(parents=True)
        for source in (ROOT / "contracts/current").glob("*.yaml"):
            shutil.copy2(source, target / source.name)
        schema_path = target / "ai_native_npc_schema_v2_0.yaml"
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        mutate(schema)
        schema_path.write_text(yaml.safe_dump(schema, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return temp

    def _mutated_boss_root(self, mutate) -> Path:
        temp = Path(tempfile.mkdtemp(prefix="ainpc-boss-pattern-semantic-"))
        self.addCleanup(lambda: shutil.rmtree(temp, ignore_errors=True))
        target = temp / "contracts/current"
        target.mkdir(parents=True)
        for source in (ROOT / "contracts/current").glob("*.yaml"):
            shutil.copy2(source, target / source.name)
        contract_path = target / "boss_pattern_contract_v1.yaml"
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        mutate(contract)
        contract_path.write_text(yaml.safe_dump(contract, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return temp

    def test_boss_pattern_common_candidate_layout_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["activation_contract"]["common_candidate_layout_unchanged"]["candidate_count"] = 273

        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("common candidate layout" in error for error in errors), errors)

    def test_boss_pattern_zero_minimum_occupied_slots_is_rejected(self) -> None:
        def mutate(contract):
            contract["slot_assignment_contract"]["minimum_occupied_slots"] = 0
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("at least one occupied row" in error for error in errors), errors)

    def test_boss_pattern_tensor_shape_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["tensors"]["pattern_features"]["shape"] = ["B", 33, 24]

        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("boss pattern tensor pattern_features shape" in error for error in errors), errors)

    def test_boss_pattern_active_reselection_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["selection_lock_contract"]["phase_rules"]["Active"] = "selection_allowed"

        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("Active" in error for error in errors), errors)

    def test_boss_pattern_late_branch_response_policy_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["selection_lock_contract"]["late_branch_response"] = "commit_after_window"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("late BranchWindow" in error for error in errors), errors)

    def test_boss_pattern_lock_acquisition_point_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["selection_lock_contract"]["lock_acquired_at"] = "startup_telegraph_entry"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("lock acquisition point" in error for error in errors), errors)

    def test_boss_pattern_fallback_tie_break_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["fallback_contract"]["utility_tie_break"] = "array_order"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("Utility tie-break" in error for error in errors), errors)

    def test_boss_pattern_unknown_interrupt_mutation_is_rejected(self) -> None:
        def mutate(contract):
            contract["interrupt_contract"]["forced"].append("UnknownInterrupt")

        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("unknown forced interrupt" in error for error in errors), errors)

    def test_boss_pattern_hash_field_order_mutation_is_rejected(self) -> None:
        def mutate(contract):
            fields = contract["hash_contract"]["pattern_candidate_set_hash"]["fields"]
            fields[2], fields[3] = fields[3], fields[2]

        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("pattern_candidate_set_hash field order mismatch" in error for error in errors), errors)

    def test_boss_pattern_timing_invariant_weakening_is_rejected(self) -> None:
        def mutate(data):
            data["pattern_asset_contract"]["invariants"]["startup_telegraph_seconds"] = "finite"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("telegraph" in error for error in errors), errors)

    def test_boss_pattern_parameter_authority_widening_is_rejected(self) -> None:
        def mutate(data):
            data["outputs"]["pattern_parameter_proposals"]["forbidden_outputs"].remove("damage")
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("forbidden output" in error for error in errors), errors)

    def test_boss_pattern_semantic_feature_rename_is_rejected(self) -> None:
        def mutate(data):
            data["tensors"]["pattern_context"]["fields"][0]["name"] = "ground_truth_player_health"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("semantic field order" in error for error in errors), errors)

    def test_boss_pattern_normalizer_assignment_gap_is_rejected(self) -> None:
        def mutate(data):
            data["normalization_contract"]["assignments"]["pattern_context"]["ratio_01"].remove("boss_health_ratio")
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("assignment closure" in error for error in errors), errors)

    def test_boss_pattern_ground_truth_feature_source_is_rejected(self) -> None:
        def mutate(data):
            data["tensors"]["pattern_context"]["fields"][4]["source"] = "ground_truth_player_transform"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("source not allowed" in error or "forbidden source" in error for error in errors), errors)

    def test_boss_pattern_executor_transform_feedback_is_rejected(self) -> None:
        def mutate(data):
            data["hidden_information_contract"]["post_lock_executor_transform_fed_back_to_model"] = True
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("fed_back_to_model" in error for error in errors), errors)

    def test_boss_pattern_client_gameplay_authority_is_rejected(self) -> None:
        def mutate(data):
            data["authority_contract"]["client_inference_gameplay_authority"] = True
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("authority contract" in error for error in errors), errors)

    def test_boss_pattern_asset_digest_canonical_leaf_bytes_are_accepted(self) -> None:
        def mutate(data):
            digest = data["pattern_asset_bundle_digest_contract"]
            digest["pattern_set_id_digest"] = {
                "algorithm": "SHA-256",
                "source_type": "string",
                "text_encoding": "UTF-8",
                "unicode_normalization": "NFC",
                "case_policy": "case_sensitive",
                "whitespace_policy": "preserve",
                "input_bytes": "normalized_utf8_without_bom",
                "empty_allowed": False,
            }
            digest["pattern_definition_digest"]["asset_reference_substitution"] = {
                "jcs_value_type": "string",
                "jcs_string_format": "lowercase_hex_64_no_prefix",
                "source_digest_algorithm": "SHA-256",
                "source_digest_bytes": 32,
                "object_path_in_digest": False,
            }
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertFalse(any("asset bundle digest contract mismatch" in error for error in errors), errors)

    def test_boss_pattern_asset_digest_unicode_policy_mutation_is_rejected(self) -> None:
        def mutate(data):
            data["pattern_asset_bundle_digest_contract"]["pattern_set_id_digest"]["unicode_normalization"] = "none"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("asset bundle digest contract mismatch" in error for error in errors), errors)

    def test_boss_pattern_asset_reference_digest_format_mutation_is_rejected(self) -> None:
        def mutate(data):
            substitution = data["pattern_asset_bundle_digest_contract"]["pattern_definition_digest"]["asset_reference_substitution"]
            substitution["jcs_string_format"] = "uppercase_hex_64_no_prefix"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("asset bundle digest contract mismatch" in error for error in errors), errors)

    def test_boss_pattern_document_marker_mutation_is_rejected(self) -> None:
        def mutate(data):
            data["documentation_contract"]["marker_begin"] = "<!-- FAKE BOSS BLOCK -->"
        errors = validate_contracts(default_paths(self._mutated_boss_root(mutate)))
        self.assertTrue(any("documentation marker" in error for error in errors), errors)


    def test_reversed_clamp_is_rejected(self) -> None:
        def mutate(schema):
            field = schema["tensors"]["global_state"]["fields"][0]
            field["normalizer"] = {"type": "clamp", "min": 1.0, "max": 0.0}

        errors = validate_contracts(default_paths(self._mutated_root(mutate)))
        self.assertTrue(any("reversed" in error or "min" in error for error in errors), errors)

    def test_invalid_log1p_and_nonpositive_divisor_are_rejected(self) -> None:
        def mutate(schema):
            fields = schema["tensors"]["target_features"]["common_fields"]
            log_field = next(row for row in fields if row["normalizer"]["type"] == "log1p_ratio")
            log_field["normalizer"]["input_min"] = -1.0
            div_field = next(row for row in fields if row["normalizer"]["type"] == "divide_clamp")
            div_field["normalizer"].pop("divisor_ref", None)
            div_field["normalizer"]["divisor"] = 0.0

        errors = validate_contracts(default_paths(self._mutated_root(mutate)))
        self.assertTrue(any("input_min must be > -1" in error for error in errors), errors)
        self.assertTrue(any("divisor must be > 0" in error for error in errors), errors)

    def test_constant_missing_and_must_equal_must_be_consistent(self) -> None:
        def mutate(schema):
            field = schema["tensors"]["global_state"]["fields"][17]
            field["valid_range"] = [0.0, 1.0]
            field["missing"] = {"policy": "constant", "value": 1.0}

        errors = validate_contracts(default_paths(self._mutated_root(mutate)))
        self.assertTrue(any("constant normalizer value must equal missing" in error for error in errors), errors)
        self.assertTrue(any("singleton valid_range" in error for error in errors), errors)
        self.assertTrue(any("missing constant != constraints.must_equal" in error for error in errors), errors)

    def test_padding_zero_must_fit_valid_range(self) -> None:
        def mutate(schema):
            field = schema["target_payload_features"]["WorldPosition"][12]
            field["normalizer"] = {"type": "constant", "value": 1.0}
            field["valid_range"] = [1.0, 1.0]
            field["missing"] = {"policy": "padding_zero", "value": 0.0, "occupied_required_value": 1.0}
            field["constraints"] = {"occupied_required_value": 1.0}

        errors = validate_contracts(default_paths(self._mutated_root(mutate)))
        self.assertTrue(any("padding_zero value outside valid_range" in error for error in errors), errors)

    def test_hash_magic_is_generated_from_yaml_with_dynamic_probe(self) -> None:
        paths = default_paths(ROOT)
        schema, skills, goals = load_contracts(paths)
        hashes = {
            "schema": sha256_file(paths.schema),
            "skill_registry": sha256_file(paths.skill_registry),
            "goal_registry": sha256_file(paths.goal_registry),
            "test_taxonomy": sha256_file(paths.test_taxonomy),
        }
        original_py = generate_python(schema, skills, goals, hashes)
        original_cpp = generate_cpp(schema, skills, goals, hashes)
        mutated = copy.deepcopy(schema)
        original_magic = mutated["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"]
        mutated_magic = different_ascii_same_length(original_magic)
        mutated["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"] = mutated_magic
        mutated_py = generate_python(mutated, skills, goals, hashes)
        mutated_cpp = generate_cpp(mutated, skills, goals, hashes)
        self.assertNotEqual(original_py, mutated_py)
        self.assertNotEqual(original_cpp, mutated_cpp)
        self.assertIn(mutated_magic, mutated_py)
        expected_cpp_bytes = ", ".join(str(value) for value in mutated_magic.encode("ascii"))
        self.assertIn(expected_cpp_bytes, mutated_cpp)

    def test_field_rename_changes_generated_appendix_with_dynamic_probe(self) -> None:
        paths = default_paths(ROOT)
        schema, skills, goals = load_contracts(paths)
        hashes = {
            "schema": sha256_file(paths.schema),
            "skill_registry": sha256_file(paths.skill_registry),
            "goal_registry": sha256_file(paths.goal_registry),
            "test_taxonomy": sha256_file(paths.test_taxonomy),
        }
        fields = schema["tensors"]["global_state"]["fields"]
        original_name = fields[0]["name"]
        existing = {row["name"] for row in fields}
        mutated_name = different_identifier(original_name, existing)
        mutated = copy.deepcopy(schema)
        mutated["tensors"]["global_state"]["fields"][0]["name"] = mutated_name
        markdown = generate_markdown(mutated, skills, goals, hashes)
        self.assertIn(mutated_name, markdown)
        self.assertNotIn(f"`{original_name}`", markdown)

    def test_manual_hash_magic_contexts_are_rejected(self) -> None:
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
        contract = schema["documentation_contract"]
        token = schema["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"]
        forms = [
            f"magic {token}",
            f"Candidate magic is {token}.",
            f'{{"magic": "{token}"}}',
            f"`magic` = `{token}`",
            "Candidate magic is abcdefgh.",
        ]
        known = collect_hash_magic_tokens(ROOT)
        for form in forms:
            with self.subTest(form=form):
                text = f"# Manual section\n\n{form}\n\n{contract['marker_begin']}\nGenerated only\n{contract['marker_end']}\n"
                errors = validate_manual_hash_literal_policy(schema, text, "probe.md", known)
                self.assertTrue(any("hash magic" in error for error in errors), errors)

    def test_stale_old_magic_is_rejected_after_yaml_magic_change(self) -> None:
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
        old_magic = schema["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"]
        mutated = copy.deepcopy(schema)
        new_magic = different_ascii_same_length(old_magic)
        mutated["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"] = new_magic
        known = collect_hash_magic_tokens(ROOT) | {old_magic, new_magic}
        errors = validate_manual_hash_literal_policy(mutated, f"Candidate magic is {old_magic}.\n", "stale.md", known)
        self.assertTrue(any(old_magic in error for error in errors), errors)

    def test_taxonomy_changes_regenerate_kpi_and_stale_blocks_fail(self) -> None:
        taxonomy = yaml.safe_load((ROOT / "contracts/current/test_taxonomy_v1.yaml").read_text(encoding="utf-8"))
        baseline_metrics = critical_suite_metrics(taxonomy)
        baseline_req = generate_requirements_kpi(taxonomy)
        baseline_ue = generate_unreal_kpi(taxonomy)
        baseline_total = baseline_metrics["critical_minimum_sequence_count"]
        baseline_family_count = baseline_metrics["required_family_count"]
        baseline_cases = baseline_metrics["minimum_cases_per_family"]
        self.assertEqual(baseline_total, baseline_family_count * baseline_cases)
        self.assertIn(f"{baseline_total} sequences", baseline_req)
        self.assertIn(f"{baseline_total} sequences", baseline_ue)

        cases_mutated = copy.deepcopy(taxonomy)
        cases_mutated["critical_suite"]["minimum_cases_per_family"] += 1
        cases_metrics = critical_suite_metrics(cases_mutated)
        expected_cases_total = baseline_family_count * (baseline_cases + 1)
        self.assertEqual(cases_metrics["critical_minimum_sequence_count"], expected_cases_total)
        self.assertIn(f"{expected_cases_total} sequences", generate_requirements_kpi(cases_mutated))

        family_mutated = copy.deepcopy(taxonomy)
        family_mutated["critical_suite"]["required_family_count"] += 1
        next_id = max(item["id"] for item in family_mutated["critical_suite"]["families"]) + 1
        family_mutated["critical_suite"]["families"].append({"id": next_id, "name": "semantic_probe_family"})
        family_metrics = critical_suite_metrics(family_mutated)
        expected_family_total = (baseline_family_count + 1) * baseline_cases
        self.assertEqual(family_metrics["critical_minimum_sequence_count"], expected_family_total)
        changed_req = generate_requirements_kpi(family_mutated)
        self.assertIn(f"{expected_family_total} sequences", changed_req)

        spec = taxonomy["documentation_contract"]["requirements"]
        stale_text = f"{spec['marker_begin']}\n\n{baseline_req}\n\n{spec['marker_end']}"
        expected_changed = f"{spec['marker_begin']}\n\n{changed_req.rstrip()}\n\n{spec['marker_end']}"
        errors = validate_generated_block(stale_text, spec["marker_begin"], spec["marker_end"], expected_changed, "requirements.md")
        self.assertTrue(errors)

    def test_current_documents_have_no_manual_hash_literal(self) -> None:
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
        taxonomy = yaml.safe_load((ROOT / "contracts/current/test_taxonomy_v1.yaml").read_text(encoding="utf-8"))
        boss_pattern = yaml.safe_load((ROOT / "contracts/current/boss_pattern_contract_v1.yaml").read_text(encoding="utf-8"))
        known = collect_hash_magic_tokens(ROOT)
        blocks = [(boss_pattern["documentation_contract"]["marker_begin"], boss_pattern["documentation_contract"]["marker_end"])]
        blocks.extend((spec["marker_begin"], spec["marker_end"]) for spec in taxonomy["documentation_contract"].values() if isinstance(spec, dict) and "marker_begin" in spec)
        for declared in schema["documentation_contract"]["required_documents"]:
            text = (ROOT / declared).read_text(encoding="utf-8")
            self.assertEqual(validate_manual_hash_literal_policy(schema, text, declared, known, blocks), [])


    def test_noncurrent_markdown_cannot_hide_magic_in_fake_generated_markers(self) -> None:
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
        token = schema["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"]
        contract = schema["documentation_contract"]
        text = f"{contract['marker_begin']}\nCandidate magic is {token}.\n{contract['marker_end']}\n"
        errors = validate_manual_hash_literal_policy(
            schema, text, "README.md", collect_hash_magic_tokens(ROOT), allow_schema_generated_block=False
        )
        self.assertTrue(errors)

    def test_catalog_missing_archive_is_rejected(self) -> None:
        catalog = json.loads((ROOT / "manifest/catalog.json").read_text(encoding="utf-8"))
        expected = build_archive_catalog(ROOT)
        self.assertTrue(expected)
        catalog["archives"] = expected[1:]
        errors = validate_catalog_data(ROOT, catalog)
        self.assertTrue(any("missing archive entry" in error for error in errors), errors)

    def test_catalog_requires_boss_pattern_canonical_role(self) -> None:
        catalog = json.loads((ROOT / "manifest/catalog.json").read_text(encoding="utf-8"))
        catalog["canonical"].pop("boss_pattern_contract", None)
        errors = validate_catalog_data(ROOT, catalog)
        self.assertTrue(any("canonical role set mismatch" in error for error in errors), errors)

    def test_catalog_ghost_archive_is_rejected(self) -> None:
        catalog = json.loads((ROOT / "manifest/catalog.json").read_text(encoding="utf-8"))
        catalog["archives"] = build_archive_catalog(ROOT) + [{
            "path": "docs/archive/requirements/ghost_v9.9.md",
            "type": "requirements",
            "version": "9.9",
            "status": "superseded",
            "sha256": "0" * 64,
        }]
        errors = validate_catalog_data(ROOT, catalog)
        self.assertTrue(any("ghost archive entry" in error for error in errors), errors)

    def test_current_document_directory_is_flat_and_exact(self) -> None:
        current = ROOT / "docs/current"
        expected = {
            "contract-appendices.md",
            "implementation-plan.md",
            "requirements.md",
            "unreal-implementation-plan.md",
        }
        actual = {path.name for path in current.iterdir() if path.is_file()}
        subdirectories = [path.name for path in current.iterdir() if path.is_dir()]
        self.assertEqual(actual, expected)
        self.assertEqual(subdirectories, [])

    def test_source_file_map_is_exact(self) -> None:
        actual = (ROOT / "reports/SOURCE_FILE_MAP.md").read_text(encoding="utf-8")
        self.assertEqual(actual, source_file_map_text())


if __name__ == "__main__":
    unittest.main()
