"""Document consistency only: these tests implement no provenance/security boundary."""
from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/current/runtime-capture-import-v1-contract.md"


@pytest.fixture(scope="module")
def document() -> str:
    return CONTRACT.read_text(encoding="utf-8")


def section(document: str, identifier: str) -> str:
    match = re.search(
        rf"^<!-- {re.escape(identifier)} -->\n(.*?)(?=^<!-- |\Z)",
        document,
        flags=re.MULTILINE | re.DOTALL,
    )
    # The pre-revision document has no section markers: test its actual claims,
    # not just the absence of new navigation comments.
    return match.group(1) if match else document


def require(text: str, *clauses: str) -> None:
    missing = [clause for clause in clauses if clause not in text]
    assert not missing, f"Missing normative clauses: {missing}"


def rows(text: str) -> list[list[str]]:
    return [
        [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.startswith("| ") and "---" not in line
    ]


def test_r1_completion_pin_is_independently_acquired(document: str) -> None:
    require(
        section(document, "R1:issuance"),
        "expected_collection_index_sha256",
        "TrustedCollectionCompletionPin",
        "owner-controlled storage",
        "independent_out_of_band",
        "submitted index, metadata, uploaded bundle, self-declared expected fields",
        "publish index last",
        "readback",
        "unknown root/bundle",
        "rehashed Capture/marker/index",
    )


def test_r1_completion_closure_does_not_invent_base_index_fields(document: str) -> None:
    require(
        section(document, "R1:issuance"),
        "format, version, session_id, entries",
        "base index has no session/episode descriptors",
        "completion_closure",
        "session",
        "ordered_episodes",
        "replay_predecessors",
        "catalog_sha256",
        "collection_execution_profile_sha256",
        "runtime_build_evidence_sha256",
        "session_start_evidence",
        "same index digest",
        "automated_runtime",
        "human_play",
        "offline_procedural",
        "test_fixture",
        "real Runtime origin",
    )


def test_r1_trusted_operator_and_storage_exclusions_are_explicit(document: str) -> None:
    require(
        section(document, "R1:issuance"),
        "trusted collector/controller",
        "trusted local operator",
        "malicious trusted operator/toolchain",
        "unsigned marker",
        "no signing service",
        "custody",
    )


def test_p1_digest_names_and_byte_rules_are_distinct(document: str) -> None:
    text = section(document, "P1:digests-build")
    require(
        text,
        "collection_execution_profile_sha256",
        "utility_profile_source_sha256",
        "teacher_profile_sha256",
        "runtime_build_evidence_sha256",
        "load_catalog",
        "catalog_digest",
        'json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")',
        "exact file bytes",
        "BuildGuardPhase0UtilityProfile",
        "utility-profile-source-v1",
        "sorted_json_bytes",
        "without trailing LF",
    )


def test_p1_build_evidence_has_bounded_source_binary_and_command_closure(document: str) -> None:
    require(
        section(document, "P1:digests-build"),
        "project_root",
        "authority_root",
        "evidence_root",
        "source_inventory_before",
        "source_inventory_after",
        "project_file",
        "target",
        "platform",
        "configuration",
        "build_argv",
        "build_working_directory",
        "exit_code",
        "build_log",
        "build_receipt",
        "module_artifacts",
        "clean_or_forced_project_modules",
        "incremental_success_only",
        "installed engine/toolchain",
        "full reproducible engine attestation",
        "engine_version, engine_executable, compiler, linker, build_tool",
        "installed_path, size_bytes, sha256, version",
    )


def test_p1_cold_start_evidence_and_historical_import_are_separate(document: str) -> None:
    require(
        section(document, "P1:digests-build"),
        "process_id",
        "process_start_identity",
        "launch_argv",
        "loaded_module_inventory",
        "Live Coding",
        "hot-reload",
        "boolean assertion alone",
        "current installed binaries/source",
        "pinned historical closure",
        "offline historical import",
    )


def test_p2_wire_source_enum_mapping_is_explicit(document: str) -> None:
    table = rows(section(document, "P2:source-enum"))
    assert table[1:] == [["0", "Silver", "silver"], ["1", "Gold", "gold"], ["2", "Dagger", "dagger"]]


def test_p2_capture_mapping_covers_snapshot_fields_and_raw_provenance(document: str) -> None:
    text = section(document, "P2:field-mapping")
    mappings = {row[0]: row[1] for row in rows(text)[1:]}
    expected = {
        "episode_id": "episode_id",
        "decision_id": "decision_id",
        "captured_at_server_time": "captured_at_server_time",
        "scenario_family_id": "scenario_family_id",
        "episode.family.template_family": "template_id",
        "generator_version": "generator_template_version",
        "map_seed": "map_seed",
        "simulation_seed": "simulation_seed",
        "candidate_bytes": "candidate_set_canonical_bytes",
        "candidate_set_hash": "candidate_set_hash",
        "input_content_hash": "input_content_hash",
        "feature_contract_hash": "feature_contract_hash",
        "switch_cost_terms": "switch_cost_terms",
        "captured_switch_cost": "captured_switch_cost",
        "target_handles": "target_handles",
        "labels.acceptable_candidate_indices": "acceptable_candidate_indices",
        "labels.preference_pairs": "preference_pairs",
        "labels.parameter_target_norm": "parameter_target_norm",
        "labels.parameter_label_mask": "parameter_label_mask",
        "labels.selected_is_acceptable": "selected_is_acceptable",
        "labels.label_confidence": "label_confidence",
        "labels.reason_tags": "reason_tags",
        "prompt_version": "prompt_or_teacher_version",
        "parent_policy_hash": "parent_policy_sha256",
    }
    assert expected.items() <= mappings.items()
    require(
        text,
        "anpc_decision_snapshot_v1",
        "source_weight=0.0",
        "abstain = (len(acceptable_candidate_indices) == 0)",
        "raw_capture",
        "selected_candidate_index",
        "sample_id",
        "label_block_hash",
        "annotator_set_hash",
        "annotator_agreement",
        'empty string -> None',
        "raw values",
        "template_id",
        "sample_id(input_content_hash, episode_id, decision_id, label_block_hash)",
        "generation_code_sha256",
    )


def test_p2_group_order_matches_capture_wire(document: str) -> None:
    expected = [
        "map_family", "occlusion_layout_family", "goal_sequence_family", "role_id",
        "personality_cluster_id", "perception_modality_family", "target_composition_family",
        "event_sequence_family",
    ]
    table = rows(section(document, "P2:groups"))[1:]
    assert table == [[f"group_dimensions[{index}]", field] for index, field in enumerate(expected)]


def test_p2_tensor_order_dtype_shape_and_bytes_are_explicit(document: str) -> None:
    expected = [
        ["0", "global_state", "float32", "[128]"],
        ["1", "target_features", "float32", "[17, 48]"],
        ["2", "target_kind_ids", "int64", "[17]"],
        ["3", "target_mask", "bool", "[17]"],
        ["4", "event_features", "float32", "[12, 24]"],
        ["5", "event_type_ids", "int64", "[12]"],
        ["6", "event_target_slots", "int64", "[12]"],
        ["7", "event_mask", "bool", "[12]"],
        ["8", "candidate_pair_features", "float32", "[272, 16]"],
        ["9", "candidate_mask", "bool", "[272]"],
    ]
    text = section(document, "P2:tensors")
    assert rows(text)[1:] == expected
    require(text, "tensor_order", "TENSOR_ORDER", "MODEL_INPUT_NAMES", "data_base64", "little-endian", "byte-for-byte")


def test_p2_contract_hash_order_and_absent_wire_semantic_versions(document: str) -> None:
    text = section(document, "P2:contract-metadata")
    table = rows(text)[1:]
    expected = [
        "schema_sha256", "skill_registry_sha256", "goal_registry_sha256", "target_slotter_sha256",
        "normalization_sha256", "postprocess_sha256", "generator_or_runtime_build_sha256",
        "source_decision_contract_hash",
    ]
    assert [row[:2] for row in table] == [[f"contract_hashes[{i}]", field] for i, field in enumerate(expected)]
    require(
        text, "SCHEMA_VERSION", "CONTRACT_REVISION", "GOAL_REGISTRY_VERSION",
        'CONSTANTS["skill_registry_version"]', 'CONSTANTS["target_slotter_version"]',
        'CONSTANTS["normalization_version"]', 'CONSTANTS["postprocess_version"]',
        "absent from wire", "empty string -> None", "raw_capture.contract_hashes",
    )


def test_p3_policy_lineage_preserves_all_four_combinations(document: str) -> None:
    text = section(document, "P3:policy-lineage")
    assert rows(text)[1:] == [
        ["None", "None", "None", "None"],
        ["S", "None", "S", "None"],
        ["None", "P", "None", "P"],
        ["S", "P (S != P)", "S", "P"],
    ]
    require(text, "_annotation_provenance", "no source-decision fallback", "mismatch", "reject")


def test_r2_teacher_authority_reconstructs_attempts_and_routing(document: str) -> None:
    require(
        section(document, "R2:labels"),
        "consistency, not Teacher issuance or reviewer authorization",
        "teacher_run_completion_pin",
        "permitted_teacher_profile_sha256",
        "exact request",
        "all five raw attempts",
        "provider_error",
        "aggregate_responses",
        "review-routing",
        "independent_out_of_band",
        "fresh process",
        "utility_unreviewed",
        "source_weight=0.0",
    )


def test_r2_human_authority_binds_exact_decisions_queue_and_source(document: str) -> None:
    require(
        section(document, "R2:labels"),
        "owner review workflow",
        "decision_set_sha256",
        "review_queue_sha256",
        "snapshot_shard_sha256",
        "snapshot_manifest_sha256",
        "reviewer_authorization",
        "reviewer_id text is insufficient",
        "historical Gold",
        "no new human approval",
        "not cryptographically authenticated",
    )


def test_r2_fixture_provider_cannot_authorize_candidate_training(document: str) -> None:
    require(
        section(document, "R2:fixtures"),
        "replay_fixture",
        "production_candidate",
        "integration_fixture",
        "fixture_only",
        "training_eligible=false",
        "label_authorized=false",
        "Dataset v2 exact fields",
        "silver/0.25",
        "gold/1.0",
        "legacy Gold",
        "reject Runtime candidate label authorization",
    )


def test_p4_keyword_only_context_preserves_existing_positional_label_metadata(document: str) -> None:
    text = section(document, "P4:context-api")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    assert blocks, "Missing concrete compatibility signatures"
    signatures = {}
    for block in blocks:
        for node in ast.parse(block).body:
            if isinstance(node, ast.FunctionDef):
                signatures[node.name] = node.args
    assert {"_base_record", "validate_snapshot_row", "read_snapshot_shard_bytes", "validate_dataset_shard"} <= signatures.keys()
    base = signatures["_base_record"]
    assert [arg.arg for arg in base.args] == ["snapshot", "labels", "provenance"]
    for name, args in signatures.items():
        kw_names = [arg.arg for arg in args.kwonlyargs]
        assert "origin_context" in kw_names, name
        default = args.kw_defaults[kw_names.index("origin_context")]
        assert isinstance(default, ast.Constant) and default.value is None, name
        assert "provenance" not in kw_names, name
    final = signatures["validate_dataset_shard"]
    assert "require_authorization" in [arg.arg for arg in final.kwonlyargs]
    assert "provenance=None" not in document


def test_p4_context_lifecycle_has_no_pre_mapping_dataset_hash_cycle(document: str) -> None:
    require(
        section(document, "P4:context-api"),
        "import-authorized",
        "label-authorized prepublication",
        "final-derived-index",
        "Dataset hash not required before mapping",
        "publish derived index last",
        "immutable",
        "fresh process",
        "validate_dataset_shard",
    )


def test_r3_proofless_validation_is_structure_only_not_authentication(document: str) -> None:
    require(
        section(document, "R3:public-acceptance"),
        "STRUCTURE/CONSISTENCY ONLY",
        "fully rehashed forged Gold",
        "structurally valid",
        "declared/structurally reconstructed",
        "authorization_status",
        "structure_only",
        "origin_authorized=false",
        "label_authorized=false",
        "training_eligible=false",
        "outside record/manifest exact-field sets",
    )


def test_r3_public_final_validator_owns_acceptance_not_only_mapper(document: str) -> None:
    require(
        section(document, "R3:public-acceptance"),
        "validate_dataset_shard",
        "require_authorization=True",
        "DatasetAuthorizationResult",
        "authorized_candidate",
        "training/qualification acceptance",
        "import acceptance requires origin_only",
        "proofless forged row never training-ready",
        "source_counts",
        "group_counts",
        "require_production=True",
        "production_eligible=false",
    )


def test_r3_procedural_regeneration_is_independent_not_universal_proof(document: str) -> None:
    require(
        section(document, "R3:procedural"),
        "map_procedural_dataset",
        "silver/0.25",
        "trusted procedural profile",
        "exact bytes",
        "complete row/manifest",
        "not a universal proof for direct final Dataset validation",
        "registered bundled profile",
        "custom profile",
    )


@pytest.mark.parametrize("case", [
    "R1-substitute-rehashed", "R1-trusted-publication", "R2-forged-queue",
    "R2-forged-reviewer", "R2-fixture-candidate", "R2-authorized-teacher",
    "R2-authorized-human", "R3-public-proofless-forgery", "R3-public-authorized-origins",
    "P1-cold-start-historical", "P2-full-parity", "P3-four-policy-combinations",
    "P4-prepublication-lifecycle",
])
def test_future_security_regressions_are_named_not_claimed_executed(document: str, case: str) -> None:
    require(section(document, "regression-matrix"), case)


def test_stale_authenticity_claims_are_removed_and_scope_stays_document_only(document: str) -> None:
    forbidden = (
        "Gold 입력은 기존 인증된 Teacher review queue 경로를 재사용한다.",
        "기본값은 기존 procedural 경로이며 Runtime 증명 없는 수입 자료는 거부한다.",
        "Runtime Dataset 검증에서 proof 생략은 실패다.",
    )
    assert not [claim for claim in forbidden if claim in document]
    require(document, "document consistency tests", "not executable security fixes", "no new trainer", "구현 전 계약")
