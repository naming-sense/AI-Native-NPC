"""Synthetic shape fixtures only: no build/provider/reviewer execution or issuance.

Fixtures are independently authored from the approved prose and existing generated
contracts. They are never written to owner storage or real Capture directories.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCHEMA = ROOT / "contracts/current/capture_import_provenance_v1.schema.json"
SESSION = "11111111-1111-4111-8111-111111111111"
EPISODE = "22222222-2222-4222-8222-222222222222"
FAILED = "33333333-3333-4333-8333-333333333333"
OTHER_SESSION = "44444444-4444-4444-8444-444444444444"
OTHER_EPISODE = "55555555-5555-4555-8555-555555555555"
GROUPS = ["map_family", "occlusion_layout_family", "goal_sequence_family", "role_id",
          "personality_cluster_id", "perception_modality_family", "target_composition_family",
          "event_sequence_family"]
CONTRACTS = ["schema_sha256", "skill_registry_sha256", "goal_registry_sha256",
             "target_slotter_sha256", "normalization_sha256", "postprocess_sha256",
             "generator_or_runtime_build_sha256", "source_decision_contract_hash"]
TENSORS = [("global_state", "float32", [128], 512),
           ("target_features", "float32", [17, 48], 3264),
           ("target_kind_ids", "int64", [17], 136), ("target_mask", "bool", [17], 17),
           ("event_features", "float32", [12, 24], 1152),
           ("event_type_ids", "int64", [12], 96), ("event_target_slots", "int64", [12], 96),
           ("event_mask", "bool", [12], 12),
           ("candidate_pair_features", "float32", [272, 16], 17408),
           ("candidate_mask", "bool", [272], 272)]
UTILITY_PATHS = ["Source/NeuralGame/AINativeNPC/Generated/AINativeNPCContracts.generated.h",
                 "Source/NeuralGame/AINativeNPC/Generated/AINativeNPCGoalGameplaySemantics.generated.h",
                 "Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.cpp",
                 "Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.h"]
AUTHORITY_PATHS = ["contracts/current/scenario_collection_v1.schema.json",
                   "contracts/current/ai_native_npc_schema_v2_0.yaml",
                   "contracts/current/skill_registry_v1.yaml", "contracts/current/goal_registry_v1.yaml",
                   "contracts/current/scenario_catalog_v1.json",
                   "docs/current/scenario-observation-adapter-v1-contract.md",
                   "generated/contract-lock.json"]
NO_AUTHORITY = {"authorization_status": "structure_only", "origin_authorized": False,
                "label_authorized": False, "training_eligible": False, "production_eligible": False}


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode() + b"\n"


def descriptor(path, *, size=1):
    return {"path": path, "size_bytes": size, "sha256": digest("synthetic:" + path)}


def based(path, base="project_root"):
    return {"base": base, **descriptor(path)}


def item(name="collection"):
    return {"authority_namespace": "synthetic-untrusted", "completion_item_id": name}


def receipt(name):
    return {"completion_item": item(name), "receipt": descriptor(name + ".json")}


def code(name):
    return {"version": "synthetic-v1", "source": descriptor("tools/" + name + ".py")}


def snapshot():
    return {"shard": descriptor("snapshot.jsonl"), "manifest": descriptor("snapshot.manifest.json")}


def closure():
    profile, build = descriptor("profile.json"), descriptor("build.json")
    return {"session_id": SESSION, "collection_index": descriptor("index.json"),
            "session": descriptor("session.json"),
            "ordered_episodes": [
                {"collection_episode_id": EPISODE, "episode": descriptor("episodes/one.json"),
                 "state": "completed", "replay_predecessor": None},
                {"collection_episode_id": FAILED, "episode": descriptor("episodes/failed.json"),
                 "state": "failed", "replay_predecessor": None}],
            "replay_predecessors": [], "catalog": descriptor("catalog.json"),
            "catalog_sha256": digest("synthetic canonical catalog without LF"),
            "collection_execution_profile": profile,
            "collection_execution_profile_sha256": profile["sha256"],
            "runtime_build_evidence": build, "runtime_build_evidence_sha256": build["sha256"],
            "session_start_evidence": descriptor("start.json")}


def profile():
    return {"format": "anpc_collection_execution_profile_v1", "version": 1,
            "catalog_sha256": closure()["catalog_sha256"],
            "observation_mapping_version": "observed_geometry_goal_v1",
            "input_source": "automated_runtime", "execution_mode": "automatic", "controller": "automated",
            "limits": {"max_episodes": 2, "episode_timeout_seconds": 60,
                       "preparation_timeout_seconds": 10, "storage_limit_bytes": 1000000},
            "utility_profile_source_sha256": digest("synthetic utility source")}


def utility():
    return {"format": "utility-profile-source-v1", "profile_id": "GuardPhase0UtilityV1",
            "entries": [based(p) for p in UTILITY_PATHS]}


def inventory():
    entries = [based(p) for p in ["NeuralGame.uproject", "Config/DefaultEngine.ini", *UTILITY_PATHS]]
    entries += [based(p, "authority_root") for p in AUTHORITY_PATHS]
    return sorted(entries, key=lambda e: (e["base"].encode(), e["path"].encode()))


def installed(name):
    return {"installed_path": "/synthetic installed/" + name, "size_bytes": 1,
            "sha256": digest("synthetic installed " + name), "version": "synthetic-v1"}


def modules():
    return [{"module_name": "NeuralGame", **based("Binaries/Win64/UnrealEditor-NeuralGame.dll")}]


def build():
    return {"format": "anpc_collection_build_evidence_v1", "version": 1,
            "project_file": based("NeuralGame.uproject"), "target": "NeuralGameEditor",
            "platform": "Win64", "configuration": "Development", "source_inventory_before": inventory(),
            "source_inventory_after": inventory(), "build_mode": "clean_or_forced_project_modules",
            "build_argv": ["synthetic-build-never-executed", "NeuralGameEditor", "-Rebuild"],
            "build_working_directory": {"base": "project_root", "path": "."}, "exit_code": 0,
            "build_log": based("build.log", "evidence_root"),
            "build_receipt": based("build.target", "evidence_root"), "module_artifacts": modules(),
            "engine_toolchain_identity": {"engine_version": "synthetic-engine",
                "engine_executable": installed("Editor"), "compiler": [installed("compiler")],
                "linker": [installed("linker")], "build_tool": [installed("build-tool")]},
            "collection_schema_sha256": descriptor("contracts/current/scenario_collection_v1.schema.json")["sha256"],
            "catalog_sha256": profile()["catalog_sha256"],
            "collection_execution_profile_sha256": closure()["collection_execution_profile_sha256"],
            "utility_profile_source_sha256": profile()["utility_profile_source_sha256"],
            "observation_mapping_version": "observed_geometry_goal_v1"}


def start():
    return {"format": "anpc_collection_session_start_evidence_v1", "version": 1,
            "session_id": SESSION, "runtime_build_evidence_sha256": closure()["runtime_build_evidence_sha256"],
            "process_id": 1, "process_start_identity": "synthetic-os-start-token",
            "launch_argv": ["synthetic-editor-never-executed", "-NoLiveCoding"],
            "executable": installed("Editor"), "loaded_module_inventory": modules(),
            "source_inventory": inventory(), "loader_log": based("loader.log", "evidence_root"),
            "live_coding_state": "disabled", "hot_reload_state": "disabled"}


def sample(input_hash, episode, decision, label_hash):
    episode_bytes = episode.encode()
    return digest(b"ANPCSAMPLE2" + bytes.fromhex(input_hash) + struct.pack("<I", len(episode_bytes))
                  + episode_bytes + struct.pack("<Q", decision) + bytes.fromhex(label_hash))


def raw():
    # Canonical base64 and dimensional shape; these are not semantic Capture bytes.
    episode = f"scenario_capture_{SESSION}_{EPISODE}_00000000000000000001"
    ih, lh = digest(b"\xa0"), digest(b"\xa1\x00\x00")
    contract_hashes = [digest("synthetic contract " + str(i)) for i in range(6)]
    feature_hash = digest(b"ANPCFEAT1" + b"".join(bytes.fromhex(h) for h in contract_hashes))
    return {"record_version": "anpc_decision_record_v2", "sample_id": sample(ih, episode, 1, lh),
            "episode_id": episode, "decision_id": 1, "input_content_hash": ih, "label_block_hash": lh,
            "candidate_set_hash": digest(b"synthetic candidate"), "feature_contract_hash": feature_hash,
            "captured_at_server_time": 1.0, "selected_candidate_index": 0, "source_type": 2,
            "map_seed": 0, "simulation_seed": 0, "scenario_family_id": "hearing_only",
            "contract_hashes": contract_hashes + [closure()["runtime_build_evidence_sha256"], ""],
            "group_dimensions": ["synthetic-" + key for key in GROUPS],
            "generator_version": "neuralgame_scenario_collection_v1:" + closure()["catalog_sha256"] + ":"
                                 + closure()["collection_execution_profile_sha256"] + ":observed_geometry_goal_v1",
            "prompt_version": "", "annotator_set_hash": "", "annotator_agreement": 0.0,
            "parent_policy_hash": "", "input_cbor_base64": "oA==", "label_cbor_base64": "oQAA",
            "candidate_bytes_base64": base64.b64encode(b"synthetic candidate").decode(),
            "tensor_blocks": [{"name": name, "dtype": dtype, "shape": shape,
                               "data_base64": base64.b64encode(bytes(length)).decode()}
                              for name, dtype, shape, length in TENSORS],
            "target_handles": [{"kind": 0, "stable_id": 0, "generation": 0, "revision": 0} for _ in range(17)],
            "switch_cost_terms": [[False] * 4 for _ in range(272)], "captured_switch_cost": [0.0] * 272,
            "labels": {"acceptable_candidate_indices": [0], "preference_pairs": [],
                       "parameter_target_norm": [0.0] * 1088, "parameter_label_mask": [False] * 1088,
                       "selected_is_acceptable": True, "label_confidence": 1.0,
                       "reason_tags": ["scenario_collection_utility_unreviewed"]}}


def imported():
    r = raw()
    row = {"row_ordinal": 0, "episode_id": r["episode_id"], "decision_id": 1,
           "input_content_hash": r["input_content_hash"], "snapshot_version": "anpc_decision_snapshot_v1",
           "scope": "production_candidate", "source_type": "dagger", "source_weight": 0.0,
           "abstain": False, "template_id": "hearing_only", "parent_policy_sha256": None,
           "source_decision_contract_hash": None, "profile_sha256": closure()["collection_execution_profile_sha256"],
           "groups": dict(zip(GROUPS, r["group_dimensions"], strict=True)),
           "tensor_order": [t[0] for t in TENSORS], "contract_hash_order": CONTRACTS,
           "semantic_binding": {"source": descriptor("generated/semantic_binding.py"),
                                "schema_version": "2.0.0", "schema_revision": "2.0.0-rc6",
                                "skill_registry_version": "1.1.0", "goal_registry_version": "1.2.0",
                                "target_slotter_version": "1.0.0", "normalization_version": "2.0.0",
                                "postprocess_version": "1.0.0"}}
    return {"format": "anpc_runtime_import_provenance_v1", "version": 1, "scope": "production_candidate",
            "production_eligible": False, "training_eligible": False, "label_status": "utility_unreviewed",
            "collection_completion": item(), "completion_closure": closure(), "parser": code("parser"),
            "importer": code("importer"), "snapshot": snapshot(),
            "entries": [{"collection_episode_id": EPISODE, "input_source": "automated_runtime",
                         "capture": descriptor("captures/one.anpccap2"),
                         "committed": descriptor("captures/one.anpccap2.committed"),
                         "raw_capture": r, "snapshot_row": row}]}


def teacher():
    p = descriptor("teacher-profile.yaml")
    return {"format": "anpc_teacher_run_completion_evidence_v1", "version": 1,
            "collection_completion": item(), "import_index": descriptor("import.json"), "snapshot": snapshot(),
            "permitted_teacher_profile": item("permitted-profile"),
            "profile": {"artifact": p, "teacher_profile_sha256": p["sha256"], "scope": "production",
                        "profile_version": "teacher_silver_v1.0.0", "prompt": descriptor("prompt.txt"),
                        "request_schema": descriptor("request.schema.json"),
                        "response_schema": descriptor("response.schema.json"),
                        "provider": {"type": "command", "model_identifier": "synthetic-model",
                                     "revision": "synthetic-revision", "command": ["never-executed"]},
                        "decoding": {"temperature": 0.0, "top_p": 1.0}},
            "requests": [{"snapshot_row_ordinal": 0, "episode_id": raw()["episode_id"], "decision_id": 1,
                          "input_content_hash": raw()["input_content_hash"], "request": descriptor("request.json"),
                          "attempts": [{"call_index": i, "raw_stdout": descriptor(f"attempt-{i}.raw", size=0 if i == 0 else 1),
                                        "outcome": "provider_error" if i == 0 else "returned",
                                        "provider_error": "synthetic timeout; no actual call" if i == 0 else None}
                                       for i in range(5)], "routing": "review"}],
            "annotation": descriptor("annotation.jsonl", size=0), "review_queue": descriptor("review.jsonl")}


def human():
    queue, snap, decisions = descriptor("review.jsonl"), snapshot(), descriptor("decisions.yaml")
    bindings = {"decision_set_sha256": decisions["sha256"], "review_queue_sha256": queue["sha256"],
                "snapshot_shard_sha256": snap["shard"]["sha256"],
                "snapshot_manifest_sha256": snap["manifest"]["sha256"]}
    return {"format": "anpc_human_review_completion_evidence_v1", "version": 1,
            "collection_completion": item(), "import_index": descriptor("import.json"),
            "teacher_run": receipt("teacher-run"), "decision_set": decisions,
            "review_queue": queue, "snapshot": snap, **bindings,
            "decision_reviewers": ["synthetic-reviewer"],
            "reviewer_authorization": {"principals": ["synthetic-reviewer"],
                                       "workflow_record_id": "synthetic-never-approved", **bindings}}


def derived():
    r = raw()
    label = digest("synthetic reviewed label")
    return {"format": "anpc_runtime_derived_provenance_v1", "version": 1,
            "scope": "production_candidate", "production_eligible": False, "training_eligible": False,
            "collection_completion": item(), "import_index": descriptor("import.json"), "snapshot": snapshot(),
            "teacher_run": receipt("teacher-run"), "human_review": receipt("human-review"),
            "dataset": {"shard": descriptor("dataset.parquet"), "manifest": descriptor("dataset.manifest.json")},
            "transformation_code": code("transformation"),
            "generation_code_sha256": digest("synthetic ML aggregate source identity"),
            "runtime_build_evidence_sha256": closure()["runtime_build_evidence_sha256"],
            "rows": [{"original_sample_id": r["sample_id"],
                      "derived_sample_id": sample(r["input_content_hash"], r["episode_id"], 1, label),
                      "episode_id": r["episode_id"], "decision_id": 1, "input_content_hash": r["input_content_hash"],
                      "original_label_block_hash": r["label_block_hash"], "derived_label_block_hash": label,
                      "source_type": "gold", "source_weight": 1.0, "snapshot_row_ordinal": 0,
                      "dataset_row_ordinal": 0, "source_decision_contract_hash": None, "parent_policy_sha256": None}]}


EXAMPLES = {"completion_closure": closure, "collection_execution_profile": profile,
            "utility_profile_source": utility, "runtime_build_evidence": build,
            "session_start_evidence": start, "import_index": imported,
            "teacher_completion_evidence": teacher, "human_completion_evidence": human,
            "derived_index": derived}


@pytest.fixture
def validator():
    return importlib.import_module("tools.validate_capture_import_provenance")


@pytest.mark.parametrize("kind", EXAMPLES)
def test_independent_positive_shapes_grant_no_authority(validator, kind):
    value = EXAMPLES[kind]()
    before = copy.deepcopy(value)
    report = validator.validate_artifact(value, kind=kind)
    assert all(report[k] == v for k, v in NO_AUTHORITY.items())
    assert value == before
    assert validator.validate_bytes(encoded(value), kind=kind) == report
    assert validator.artifact_bytes(value) == encoded(value)


def replace_at(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


R = ("entries", 0, "raw_capture")
S = ("entries", 0, "snapshot_row")
# Each hostile input starts with an independently validated positive fixture.
MUTATIONS = [
    ("import_index", ("version",), 1.0),
    ("import_index", ("version",), True),
    ("import_index", ("version",), 2),
    ("import_index", ("format",), "anpc_runtime_import_provenance_v2"),
    ("import_index", ("scope",), "production"),
    ("import_index", ("training_eligible",), True),
    ("import_index", ("production_eligible",), True),
    ("import_index", ("label_status",), "approved"),
    ("import_index", ("parser", "source", "sha256"), "a" * 63),
    ("import_index", ("parser", "source", "sha256"), "A" * 64),
    ("import_index", ("parser", "source", "sha256"), "a" * 64 + "\n"),
    ("import_index", ("parser", "source", "size_bytes"), True),
    ("import_index", ("parser", "source", "size_bytes"), -1),
    ("import_index", ("collection_completion", "completion_item_id"), ""),
    ("import_index", ("entries", 0, "input_source"), "test_fixture"),
    ("import_index", R + ("decision_id",), 1.0),
    ("import_index", R + ("decision_id",), 0),
    ("import_index", R + ("decision_id",), 18446744073709551616),
    ("import_index", R + ("source_type",), 0),
    ("import_index", R + ("source_type",), 2.0),
    ("import_index", R + ("source_type",), True),
    ("import_index", R + ("parent_policy_hash",), None),
    ("import_index", R + ("annotator_set_hash",), None),
    ("import_index", R + ("contract_hashes", 7), None),
    ("import_index", R + ("contract_hashes", 0), ""),
    ("import_index", R + ("group_dimensions",), ["x"] * 7),
    ("import_index", R + ("group_dimensions", 3), ""),
    ("import_index", R + ("captured_at_server_time",), float("inf")),
    ("import_index", R + ("captured_at_server_time",), -0.0),
    ("import_index", R + ("annotator_agreement",), float("nan")),
    ("import_index", R + ("selected_candidate_index",), 272),
    ("import_index", R + ("labels", "acceptable_candidate_indices"), [1, 0]),
    ("import_index", R + ("labels", "acceptable_candidate_indices"), [0, 0]),
    ("import_index", R + ("labels", "acceptable_candidate_indices"), [1.0]),
    ("import_index", R + ("labels", "parameter_label_mask", 0), 0),
    ("import_index", R + ("labels", "label_confidence"), 0.1),
    ("import_index", R + ("labels", "label_confidence"), 1),
    ("import_index", R + ("labels", "reason_tags"), ["z", "scenario_collection_utility_unreviewed"]),
    ("import_index", R + ("labels", "reason_tags"), []),
    ("import_index", R + ("labels", "preference_pairs"), [[2, 1], [1, 0]]),
    ("import_index", R + ("switch_cost_terms", 0, 0), 1),
    ("import_index", R + ("target_handles", 0, "generation"), 4294967296),
    ("import_index", R + ("target_handles",), []),
    ("import_index", R + ("tensor_blocks", 0, "shape"), [128.0]),
    ("import_index", R + ("tensor_blocks", 0, "dtype"), "float64"),
    ("import_index", R + ("tensor_blocks", 0, "data_base64"), "AA=="),
    ("import_index", R + ("input_cbor_base64",), "oB=="),
    ("import_index", R + ("input_cbor_base64",), "oA==\n"),
    ("import_index", R + ("input_cbor_base64",), "_A=="),
    ("import_index", S + ("source_type",), "gold"),
    ("import_index", S + ("source_weight",), 1.0),
    ("import_index", S + ("source_weight",), False),
    ("import_index", S + ("abstain",), True),
    ("import_index", S + ("groups", "role_id"), "wrong-role"),
    ("import_index", S + ("parent_policy_sha256",), ""),
    ("import_index", S + ("source_decision_contract_hash",), digest("other")),
    ("import_index", S + ("decision_id",), 2),
    ("import_index", S + ("row_ordinal",), 1),
    ("import_index", S + ("tensor_order",), [t[0] for t in reversed(TENSORS)]),
    ("completion_closure", ("ordered_episodes", 1, "state"), "running"),
    ("completion_closure", ("collection_execution_profile_sha256",), digest("mismatch")),
    ("completion_closure", ("runtime_build_evidence_sha256",), digest("mismatch")),
    ("collection_execution_profile", ("limits", "max_episodes"), 10001),
    ("collection_execution_profile", ("limits", "max_episodes"), 2.0),
    ("collection_execution_profile", ("limits", "preparation_timeout_seconds"), 61),
    ("collection_execution_profile", ("controller",), "human"),
    ("collection_execution_profile", ("execution_mode",), "manual"),
    ("collection_execution_profile", ("observation_mapping_version",), "invented"),
    ("utility_profile_source", ("profile_id",), "GuardPhase0UtilityV1 "),
    ("utility_profile_source", ("entries",), []),
    ("runtime_build_evidence", ("build_mode",), "incremental_success_only"),
    ("runtime_build_evidence", ("exit_code",), 1),
    ("runtime_build_evidence", ("exit_code",), 0.0),
    ("runtime_build_evidence", ("build_argv",), "build --all"),
    ("runtime_build_evidence", ("build_argv",), []),
    ("runtime_build_evidence", ("module_artifacts", 0, "base"), "evidence_root"),
    ("runtime_build_evidence", ("engine_toolchain_identity", "compiler"), []),
    ("runtime_build_evidence", ("engine_toolchain_identity", "compiler", 0, "installed_path"), "relative/compiler"),
    ("runtime_build_evidence", ("source_inventory_after", 0, "sha256"), digest("changed")),
    ("session_start_evidence", ("process_id",), 0),
    ("session_start_evidence", ("process_start_identity",), ""),
    ("session_start_evidence", ("live_coding_state",), True),
    ("session_start_evidence", ("hot_reload_state",), "enabled"),
    ("session_start_evidence", ("loaded_module_inventory",), []),
    ("teacher_completion_evidence", ("profile", "provider", "type"), "invented"),
    ("teacher_completion_evidence", ("profile", "teacher_profile_sha256"), digest("mismatch")),
    ("teacher_completion_evidence", ("profile", "decoding", "top_p"), 0),
    ("teacher_completion_evidence", ("profile", "decoding", "temperature"), -0.0),
    ("teacher_completion_evidence", ("requests", 0, "attempts", 0, "call_index"), 1),
    ("teacher_completion_evidence", ("requests", 0, "attempts", 0, "call_index"), 0.0),
    ("teacher_completion_evidence", ("requests", 0, "attempts", 0, "provider_error"), None),
    ("teacher_completion_evidence", ("requests", 0, "attempts", 1, "provider_error"), "hidden error"),
    ("teacher_completion_evidence", ("requests", 0, "attempts"), []),
    ("human_completion_evidence", ("decision_set_sha256",), digest("mismatch")),
    ("human_completion_evidence", ("reviewer_authorization", "review_queue_sha256"), digest("mismatch")),
    ("human_completion_evidence", ("decision_reviewers",), ["self-declared-reviewer"]),
    ("human_completion_evidence", ("reviewer_authorization", "principals"), []),
    ("derived_index", ("rows", 0, "source_type"), "dagger"),
    ("derived_index", ("rows", 0, "source_weight"), 0.0),
    ("derived_index", ("rows", 0, "source_weight"), 0.25),
    ("derived_index", ("rows", 0, "derived_sample_id"), raw()["sample_id"]),
    ("derived_index", ("human_review",), None),
    ("derived_index", ("rows", 0, "dataset_row_ordinal"), 1),
]


@pytest.mark.parametrize("kind,path,replacement", MUTATIONS,
                         ids=[f"{k}:{'/'.join(map(str, p))}:{i}" for i, (k, p, _) in enumerate(MUTATIONS)])
def test_hostile_boundary_rejected(validator, kind, path, replacement):
    value = EXAMPLES[kind]()
    assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
    replace_at(value, path, replacement)
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY


@pytest.mark.parametrize("kind", EXAMPLES)
def test_every_object_is_closed_and_all_authored_fields_required(validator, kind):
    value = EXAMPLES[kind]()
    assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY

    def visit(node, path=()):
        if isinstance(node, dict):
            yield path, node
            for key, val in node.items():
                yield from visit(val, (*path, key))
        elif isinstance(node, list):
            # Same-shaped repeated inventory/tensor rows are covered by boundary tests.
            for index, val in enumerate(node[:1]):
                yield from visit(val, (*path, index))

    for path, node in visit(value):
        forged = copy.deepcopy(value)
        obj = forged
        for key in path:
            obj = obj[key]
        obj["approved"] = True
        with pytest.raises(validator.ValidationError):
            assert validator.validate_artifact(forged, kind=kind) == NO_AUTHORITY
        for key in node:
            absent = copy.deepcopy(value)
            obj = absent
            for part in path:
                obj = obj[part]
            del obj[key]
            with pytest.raises(validator.ValidationError):
                assert validator.validate_artifact(absent, kind=kind) == NO_AUTHORITY


@pytest.mark.parametrize("path", ["../escape", "/abs", "C:/drive", "a\\b", "a/../b", "a/./b", "a//b",
                                   "a/", "./a", "a\x00b", "a\nb"])
def test_lexical_paths_rejected_without_resolving(validator, path):
    value = build()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    value["build_log"]["path"] = path
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


@pytest.mark.parametrize("kind,field", [("utility_profile_source", "entries"),
    ("runtime_build_evidence", "source_inventory_before"),
    ("session_start_evidence", "source_inventory")])
def test_inventory_order_and_duplicates(validator, kind, field):
    value = EXAMPLES[kind]()
    assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
    for replacement in [list(reversed(value[field])), value[field] + value[field][:1]]:
        changed = copy.deepcopy(value)
        changed[field] = replacement
        with pytest.raises(validator.ValidationError):
            assert validator.validate_artifact(changed, kind=kind) == NO_AUTHORITY


def test_duplicate_identities_and_paths(validator):
    for kind, field in [("import_index", "entries"), ("derived_index", "rows"),
                        ("teacher_completion_evidence", "requests"),
                        ("completion_closure", "ordered_episodes"),
                        ("runtime_build_evidence", "module_artifacts")]:
        value = EXAMPLES[kind]()
        assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
        value[field].append(copy.deepcopy(value[field][0]))
        with pytest.raises(validator.ValidationError):
            assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
    value = imported()
    value["snapshot"]["manifest"] = copy.deepcopy(value["snapshot"]["shard"])
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


def test_ordered_replay_graph_and_no_capture_episode(validator):
    value = closure()
    assert validator.validate_artifact(value, kind="completion_closure") == NO_AUTHORITY
    value["ordered_episodes"][1]["replay_predecessor"] = {"session_id": SESSION, "collection_episode_id": EPISODE}
    assert validator.validate_artifact(value, kind="completion_closure") == NO_AUTHORITY
    value["ordered_episodes"][0]["replay_predecessor"] = {"session_id": SESSION, "collection_episode_id": FAILED}
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value, kind="completion_closure") == NO_AUTHORITY
    value = closure()
    value["ordered_episodes"][0]["replay_predecessor"] = {"session_id": OTHER_SESSION, "collection_episode_id": OTHER_EPISODE}
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value, kind="completion_closure") == NO_AUTHORITY
    value["replay_predecessors"] = [{"completion_item": item("previous-session"), "session_id": OTHER_SESSION,
        "session": descriptor("previous/session.json"),
        "episodes": [{"collection_episode_id": OTHER_EPISODE, "episode": descriptor("previous/episode.json")}]}]
    assert validator.validate_artifact(value, kind="completion_closure") == NO_AUTHORITY


@pytest.mark.parametrize("source,parent", [("", ""), (digest("source"), ""), ("", digest("parent")),
                                           (digest("source"), digest("parent"))])
def test_policy_lineages_remain_independent(validator, source, parent):
    value = imported()
    r, s = value["entries"][0]["raw_capture"], value["entries"][0]["snapshot_row"]
    r["contract_hashes"][7], r["parent_policy_hash"] = source, parent
    s["source_decision_contract_hash"], s["parent_policy_sha256"] = source or None, parent or None
    assert validator.validate_artifact(value)["training_eligible"] is False
    s["parent_policy_sha256"] = digest("forged-policy")
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


@pytest.mark.parametrize("transform", [lambda b: b[:-1], lambda b: b + b"\n", lambda b: b" " + b,
    lambda b: b.replace(b'"version":1', b'"version":1,"version":1'),
    lambda b: b.replace(b'"version":1', b'"version":NaN'),
    lambda b: b.replace(b'"version":1', b'"version":1e999'), lambda b: b"\xef\xbb\xbf" + b,
    lambda b: b.replace(b"1", b"\xff", 1)])
def test_strict_json_byte_grammar(validator, transform):
    good = encoded(profile())
    assert validator.validate_bytes(good) == NO_AUTHORITY
    with pytest.raises(validator.ValidationError):
        assert validator.validate_bytes(transform(good)) == NO_AUTHORITY


def test_python_only_inputs_and_unknown_kind(validator):
    for bad in [(), b"{}", {1: "bad"}, {"a": {1, 2}}, {"x": float("inf")}, None]:
        with pytest.raises(validator.ValidationError):
            assert validator.validate_artifact(bad) == NO_AUTHORITY
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(profile(), kind="remote-schema") == NO_AUTHORITY


@pytest.mark.parametrize("exponent", [100, 5000], ids=["ordinary", "over-digit-limit"])
@pytest.mark.parametrize("sign", [1, -1], ids=["above-maximum", "below-minimum"])
def test_parsed_integer_rejection_uses_public_validation_error(validator, exponent, sign):
    digit_limit = sys.get_int_max_str_digits()
    value = profile()
    original = copy.deepcopy(value)
    report = validator.validate_artifact(value)
    assert report == NO_AUTHORITY
    assert all(report[key] is False for key in NO_AUTHORITY if key != "authorization_status")
    assert value == original
    assert sys.get_int_max_str_digits() == digit_limit
    # Build the exact integer inside the test: no serialization or giant pytest ID.
    value["limits"]["max_episodes"] = sign * 10 ** exponent
    before = copy.deepcopy(value)
    try:
        with pytest.raises(validator.ValidationError) as error:
            validator.validate_artifact(value)
        assert type(error.value) is validator.ValidationError
        if exponent == 100:
            comparison = "greater than the maximum of 10000" if sign == 1 else "less than the minimum of 1"
            assert str(error.value) == (
                f"collection_execution_profile/limits/max_episodes: {sign * 10 ** exponent} is {comparison}"
            )
            assert error.value.__cause__ is None
    finally:
        assert value == before
        assert sys.get_int_max_str_digits() == digit_limit


@pytest.mark.parametrize("path,replacement,message", [
    (("limits",), (), "non-JSON type"),
    (("format",), [], "artifact format must be a string"),
    (("format",), "unknown", "unknown artifact format/kind; closure requires explicit kind"),
    (("limits", "max_episodes"), 10001,
     "collection_execution_profile/limits/max_episodes: 10001 is greater than the maximum of 10000"),
    (("controller",), "human", "controller/input_source mismatch"),
], ids=["json-type", "format-type", "unknown-format", "schema-maximum", "consistency"])
def test_parsed_validation_errors_preserve_messages(validator, path, replacement, message):
    digit_limit = sys.get_int_max_str_digits()
    value = profile()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    replace_at(value, path, replacement)
    before = copy.deepcopy(value)
    try:
        with pytest.raises(validator.ValidationError) as error:
            validator.validate_artifact(value)
        assert type(error.value) is validator.ValidationError
        assert str(error.value) == message
        assert error.value.__cause__ is None
    finally:
        assert value == before
        assert sys.get_int_max_str_digits() == digit_limit


def test_schema_is_closed_local_and_reuses_collection_constraints():
    from jsonschema import Draft202012Validator
    schema = json.loads(SCHEMA.read_bytes())
    Draft202012Validator.check_schema(schema)
    collection = json.loads((ROOT / "contracts/current/scenario_collection_v1.schema.json").read_bytes())
    for name in ("id", "uuid", "hash", "text", "path", "artifact", "source", "mode", "controller", "duration", "limits"):
        assert schema["$defs"][name] == collection["$defs"][name]

    def inspect(node):
        if isinstance(node, dict):
            if "$ref" in node:
                assert node["$ref"].startswith("#/$defs/")
            if node.get("type") == "object":
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for val in node.values():
                inspect(val)
        elif isinstance(node, list):
            for val in node:
                inspect(val)
    inspect(schema)
    for kind, factory in EXAMPLES.items():
        Draft202012Validator({"$ref": f"#/$defs/{kind}", "$defs": schema["$defs"]}).validate(factory())


def test_existing_generated_tensor_group_source_contracts():
    from generated.python import ai_native_npc_contracts_generated as binding
    from tools import validate_anpc_capture_v2 as decoder
    assert tuple(t[0] for t in TENSORS) == binding.MODEL_INPUT_NAMES
    assert tuple(t[3] for t in TENSORS) == decoder.TENSOR_LENGTHS
    for name, dtype, shape, _ in TENSORS:
        assert binding.TENSOR_SHAPES[name] == ["B", *shape]
        assert binding.TENSOR_DTYPES[name] == dtype
    authority = (ROOT / "docs/current/runtime-capture-import-v1-contract.md").read_text()
    for index, key in enumerate(GROUPS):
        assert f"| `group_dimensions[{index}]` | `{key}` |" in authority
    assert "| `2` | `Dagger` | `dagger` |" in authority
    source = (ROOT / "tools/validate_anpc_capture_v2.py").read_text()
    assert "source_type <= 2" in source
    assert imported()["entries"][0]["raw_capture"]["source_type"] == 2
    assert derived()["rows"][0]["source_weight"] == 1.0


@pytest.mark.parametrize("bad_format", [[], {}, 1, True, None])
def test_malformed_format_has_validation_error(validator, bad_format):
    value = profile()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    value["format"] = bad_format
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


@pytest.mark.parametrize("kind", EXAMPLES)
def test_cli_valid_and_malformed(validator, tmp_path, kind):
    import subprocess
    artifact = tmp_path / "synthetic-declaration.json"
    value = EXAMPLES[kind]()
    assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
    artifact.write_bytes(encoded(value))
    command = [sys.executable, str(ROOT / "tools/validate_capture_import_provenance.py"),
               str(artifact), "--kind", kind]
    result = subprocess.run(command, capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == NO_AUTHORITY
    assert not result.stderr
    value["approved"] = True
    artifact.write_bytes(encoded(value))
    result = subprocess.run(command, capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 1
    assert "INVALID STRUCTURE:" in result.stderr
    assert not result.stdout
    assert "Traceback" not in result.stderr


def test_cli_usage_and_bad_json(validator, tmp_path):
    import subprocess
    command = [sys.executable, str(ROOT / "tools/validate_capture_import_provenance.py")]
    missing_arg = subprocess.run(command, capture_output=True, text=True, cwd=tmp_path)
    assert missing_arg.returncode == 2
    missing_file = subprocess.run([*command, str(tmp_path / "absent.json")], capture_output=True, text=True)
    assert missing_file.returncode == 1 and "INVALID STRUCTURE:" in missing_file.stderr
    artifact = tmp_path / "synthetic-malformed.json"
    for data in [b'{"format":[]}\n', b'{"x":1,"x":2}\n', b'NaN\n', b'{\n']:
        artifact.write_bytes(data)
        result = subprocess.run([*command, str(artifact)], capture_output=True, text=True, cwd=tmp_path)
        assert result.returncode == 1
        assert "INVALID STRUCTURE:" in result.stderr
        assert "Traceback" not in result.stderr


def test_no_descriptor_reads_or_remote_schema(validator, tmp_path, monkeypatch):
    value = imported()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    with monkeypatch.context() as patcher:
        def no_read(*args, **kwargs):
            pytest.fail("structure validation attempted a descriptor read")
        patcher.setattr(Path, "read_bytes", no_read)
        assert validator.validate_artifact(value) == NO_AUTHORITY
    schema = json.loads(SCHEMA.read_bytes())
    schema["$defs"]["descriptor"]["properties"]["sha256"] = {"$ref": "https://invalid.example/schema.json"}
    path = tmp_path / "synthetic-schema.json"
    path.write_bytes(encoded(schema))
    monkeypatch.setattr(validator, "SCHEMA_PATH", path)
    with pytest.raises(validator.ValidationError, match="nonlocal Schema reference"):
        validator._load_schema()


def test_catalog_digest_remains_separate_no_lf(validator):
    from tools import validate_scenario_collection as collection
    catalog = collection.load_catalog()
    canonical = encoded(catalog)[:-1]
    assert collection.catalog_digest(catalog) == digest(canonical)
    assert collection.catalog_digest(catalog) != digest(validator.artifact_bytes(catalog))


def test_positive_boundary_variants_still_grant_no_authority(validator):
    values = []
    for source, mode, controller in [("human_play", "manual", "human"),
                                      ("human_play", "replay", "human"),
                                      ("test_fixture", "automatic", "automated"),
                                      ("offline_procedural", "automatic", "automated")]:
        value = profile()
        value.update(input_source=source, execution_mode=mode, controller=controller)
        values.append(value)
    value = teacher()
    value["profile"].update(scope="integration_fixture", profile_version="teacher_silver_v1.0.0-integration")
    value["profile"]["provider"] = {"type": "replay_fixture", "model_identifier": "synthetic", "revision": "synthetic"}
    values.append(value)
    value = derived()
    value["human_review"] = None
    value["rows"][0].update(source_type="silver", source_weight=0.25)
    values.append(value)
    value = imported()
    value["entries"][0]["raw_capture"]["labels"]["acceptable_candidate_indices"] = []
    value["entries"][0]["raw_capture"]["labels"]["selected_is_acceptable"] = None
    value["entries"][0]["snapshot_row"]["abstain"] = True
    values.append(value)
    value = imported()
    value["entries"] = []
    values.append(value)
    value = build()
    value["build_argv"].append("")  # Preserve actual empty argv elements.
    values.append(value)
    for value in values:
        assert validator.validate_artifact(value) == NO_AUTHORITY


def test_zero_arg_executable_and_source_inventory_minimum(validator):
    value = build()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    value["build_argv"][0] = ""
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


def test_source_inventory_minimum_is_not_just_project_file(validator):
    value = build()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    value["source_inventory_before"] = [value["project_file"]]
    value["source_inventory_after"] = copy.deepcopy(value["source_inventory_before"])
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


@pytest.mark.parametrize("missing", AUTHORITY_PATHS + UTILITY_PATHS + ["Config/DefaultEngine.ini", "NeuralGame.uproject"])
def test_source_inventory_required_known_closure(validator, missing):
    value = build()
    assert validator.validate_artifact(value) == NO_AUTHORITY
    value["source_inventory_before"] = [e for e in value["source_inventory_before"] if e["path"] != missing]
    value["source_inventory_after"] = copy.deepcopy(value["source_inventory_before"])
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


@pytest.mark.parametrize("kind,path,replacement", [
    ("teacher_completion_evidence", ("profile", "provider", "command"), ["never-executed", ""]),
    ("runtime_build_evidence", ("collection_schema_sha256",), digest("different schema from declared inventory")),
])
def test_additional_cross_field_boundaries(validator, kind, path, replacement):
    value = EXAMPLES[kind]()
    assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY
    replace_at(value, path, replacement)
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value, kind=kind) == NO_AUTHORITY


def test_derived_has_explicit_generation_code_identity(validator):
    value = derived()
    value["generation_code_sha256"] = digest("synthetic ML aggregate source identity")
    assert validator.validate_artifact(value) == NO_AUTHORITY
    del value["generation_code_sha256"]
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY


def test_feature_hash_formula_is_declared_consistency(validator):
    value = imported()
    r = value["entries"][0]["raw_capture"]
    r["feature_contract_hash"] = digest(b"ANPCFEAT1" + b"".join(bytes.fromhex(h) for h in r["contract_hashes"][:6]))
    assert validator.validate_artifact(value) == NO_AUTHORITY
    r["feature_contract_hash"] = digest("self-inconsistent feature hash")
    with pytest.raises(validator.ValidationError):
        assert validator.validate_artifact(value) == NO_AUTHORITY
