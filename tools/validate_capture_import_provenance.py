#!/usr/bin/env python3
"""Validate untrusted Runtime import artifact structure; never grant authority.

Reads only the selected JSON artifact and the bundled local Schema. Descriptor
paths are lexical declarations, never filesystem access or issuance evidence.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import struct
import sys
import unicodedata
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import ValidationError as SchemaError
from referencing import Registry
from referencing.exceptions import NoSuchResource

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "contracts/current/capture_import_provenance_v1.schema.json"
KINDS = (
    "completion_closure", "collection_execution_profile", "utility_profile_source", "runtime_build_evidence",
    "session_start_evidence", "import_index", "teacher_completion_evidence", "human_completion_evidence",
    "derived_index",
)
GROUP_ORDER = (
    "map_family", "occlusion_layout_family", "goal_sequence_family", "role_id", "personality_cluster_id",
    "perception_modality_family", "target_composition_family", "event_sequence_family",
)
UTILITY_PATHS = (
    "Source/NeuralGame/AINativeNPC/Generated/AINativeNPCContracts.generated.h",
    "Source/NeuralGame/AINativeNPC/Generated/AINativeNPCGoalGameplaySemantics.generated.h",
    "Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.cpp",
    "Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.h",
)


AUTHORITY_SOURCE_PATHS = (
    "contracts/current/scenario_collection_v1.schema.json",
    "contracts/current/ai_native_npc_schema_v2_0.yaml",
    "contracts/current/skill_registry_v1.yaml",
    "contracts/current/goal_registry_v1.yaml",
    "contracts/current/scenario_catalog_v1.json",
    "docs/current/scenario-observation-adapter-v1-contract.md",
    "generated/contract-lock.json",
)


class ValidationError(ValueError):
    """Invalid structure/declared consistency; no authorization decision is made."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _json_types(value: Any) -> None:
    if type(value) is str:
        value.encode("utf-8", errors="strict")
        return
    if type(value) in (int, bool, type(None)):
        return
    if type(value) is float:
        _require(math.isfinite(value), "nonfinite number")
        _require(value != 0.0 or math.copysign(1.0, value) > 0, "negative zero")
        return
    if type(value) is list:
        for item in value:
            _json_types(item)
        return
    _require(type(value) is dict, "non-JSON type")
    for key, item in value.items():
        _require(type(key) is str, "JSON object keys must be strings")
        _json_types(key)
        _json_types(item)


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValidationError(f"nonfinite JSON constant: {value}")


def _loads(data: bytes) -> Any:
    _require(type(data) is bytes, "immutable bytes required")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        _json_types(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def artifact_bytes(value: Any) -> bytes:
    """Serialize JSON with the new-artifact grammar; not a validation or pin API."""
    try:
        _json_types(value)
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("utf-8") + b"\n"
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValidationError(f"cannot encode artifact: {exc}") from exc


def _exact_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is list:
        return len(left) == len(right) and all(_exact_equal(a, b) for a, b in zip(left, right, strict=True))
    if type(left) is dict:
        return left.keys() == right.keys() and all(_exact_equal(left[k], right[k]) for k in left)
    return left == right


def _const(validator, expected, value, schema):
    if not _exact_equal(expected, value):
        yield SchemaError(f"exact constant required: {expected!r}")


def _float_width(validator, width, value, schema):
    if type(value) is not float or not math.isfinite(value):
        yield SchemaError(f"exact finite float{width} required")
        return
    if width == 32:
        try:
            exact = struct.unpack("<f", struct.pack("<f", value))[0] == value
        except (OverflowError, struct.error):
            exact = False
        if not exact:
            yield SchemaError("value is not an exact decoded float32")


def _base64_bytes(value: str) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValidationError("invalid standard base64") from exc
    _require(base64.b64encode(raw).decode("ascii") == value, "noncanonical base64")
    return raw


def _canonical_base64(validator, enabled, value, schema):
    if type(value) is not str:
        return
    try:
        _base64_bytes(value)
    except ValidationError as exc:
        yield SchemaError(str(exc))


def _decoded_size(validator, size, value, schema):
    if type(value) is not str:
        return
    try:
        raw = _base64_bytes(value)
    except ValidationError as exc:
        yield SchemaError(str(exc))
        return
    if len(raw) != size:
        yield SchemaError(f"decoded block must have {size} bytes")


def _no_remote(uri: str):
    raise NoSuchResource(ref=uri)


def _load_schema() -> dict:
    schema = _loads(SCHEMA_PATH.read_bytes())

    def local_refs(node):
        if type(node) is dict:
            if "$ref" in node:
                _require(node["$ref"].startswith("#/$defs/"), "nonlocal Schema reference forbidden")
            for child in node.values():
                local_refs(child)
        elif type(node) is list:
            for child in node:
                local_refs(child)

    local_refs(schema)
    Draft202012Validator.check_schema(schema)
    return schema


_SCHEMA = _load_schema()
_FORMATS = {definition["properties"]["format"]["const"]: kind for kind in KINDS
            if "format" in (definition := _SCHEMA["$defs"][kind])["properties"]}
_type_checker = Draft202012Validator.TYPE_CHECKER.redefine_many({
    "integer": lambda checker, value: type(value) is int,
    "number": lambda checker, value: type(value) is int or (type(value) is float and math.isfinite(value)),
})
_Validator = validators.extend(Draft202012Validator, type_checker=_type_checker, validators={
    "const": _const, "x-float-width": _float_width, "x-canonical-base64": _canonical_base64,
    "x-decoded-size": _decoded_size,
})
_VALIDATORS = {kind: _Validator({"$ref": f"#/$defs/{kind}", "$defs": _SCHEMA["$defs"]},
                               registry=Registry(retrieve=_no_remote)) for kind in KINDS}


def _unique(values, name: str) -> None:
    values = list(values)
    _require(len(values) == len(set(values)), f"duplicate {name}")


def _ordered_unique(values: list, name: str) -> None:
    _unique(values, name)
    _require(values == sorted(values), f"noncanonical {name} order")


def _inventory(entries: list[dict]) -> None:
    keys = [(entry["base"].encode("utf-8"), entry["path"].encode("utf-8")) for entry in entries]
    _ordered_unique(keys, "inventory (base,path)")


def _modules(entries: list[dict]) -> None:
    _inventory(entries)
    _unique((entry["module_name"] for entry in entries), "module name")


def _distinct_paths(descriptors: list[dict]) -> None:
    _unique(((d.get("base", "collection_root"), d["path"]) for d in descriptors), "artifact path")


def _descriptor_consistency(value: Any) -> None:
    """Same lexical path/base cannot declare conflicting bytes; no target is opened."""
    seen = {}

    def visit(node):
        if type(node) is list:
            for child in node:
                visit(child)
            return
        if type(node) is not dict:
            return
        if {"path", "size_bytes", "sha256"} <= node.keys():
            key = (node.get("base", "collection_root"), node["path"])
            identity = (node["size_bytes"], node["sha256"])
            _require(key not in seen or seen[key] == identity, "conflicting descriptors for one path")
            seen[key] = identity
        for child in node.values():
            visit(child)

    visit(value)


def _closure(value: dict) -> None:
    for name in ("collection_execution_profile", "runtime_build_evidence"):
        _require(value[name]["sha256"] == value[name + "_sha256"], f"{name} digest mismatch")
    descriptors = [value[key] for key in ("collection_index", "session", "catalog", "collection_execution_profile",
                                         "runtime_build_evidence", "session_start_evidence")]
    episodes = value["ordered_episodes"]
    _unique((ep["collection_episode_id"] for ep in episodes), "episode identity")
    external = set()
    predecessors = value["replay_predecessors"]
    _unique((p["session_id"] for p in predecessors), "external predecessor session")
    _unique(((p["completion_item"]["authority_namespace"], p["completion_item"]["completion_item_id"])
             for p in predecessors), "predecessor completion item")
    for previous in predecessors:
        _require(previous["session_id"] != value["session_id"], "external predecessor uses current session")
        descriptors.append(previous["session"])
        _unique((ep["collection_episode_id"] for ep in previous["episodes"]), "predecessor episode")
        for ep in previous["episodes"]:
            external.add((previous["session_id"], ep["collection_episode_id"]))
            descriptors.append(ep["episode"])
    seen = set(external)
    used_external = set()
    for ep in episodes:
        identity = (value["session_id"], ep["collection_episode_id"])
        predecessor = ep["replay_predecessor"]
        if predecessor is not None:
            key = (predecessor["session_id"], predecessor["collection_episode_id"])
            _require(key in seen, "replay predecessor missing, forward or cyclic")
            if key in external:
                used_external.add(key)
        seen.add(identity)
        descriptors.append(ep["episode"])
    _require(used_external == external, "unreferenced external replay predecessor")
    _distinct_paths(descriptors)


def _profile(value: dict) -> None:
    human = value["controller"] == "human"
    _require((value["input_source"] == "human_play") == human, "controller/input_source mismatch")
    _require(value["execution_mode"] != "manual" or human, "manual requires human controller")
    _require(value["execution_mode"] != "automatic" or not human, "automatic forbids human controller")
    limits = value["limits"]
    _require(limits["preparation_timeout_seconds"] <= limits["episode_timeout_seconds"], "preparation exceeds episode timeout")


def _build(value: dict) -> None:
    before, after = value["source_inventory_before"], value["source_inventory_after"]
    _inventory(before)
    _inventory(after)
    _require(before == after, "source inventories changed across declared build")
    _require(value["project_file"] in before, "project file missing from source inventory")
    paths = {(e["base"], e["path"]) for e in before}
    required = {("authority_root", path) for path in AUTHORITY_SOURCE_PATHS}
    required.update(("project_root", path) for path in (*UTILITY_PATHS, "NeuralGame.uproject"))
    _require(required <= paths, "known minimum source closure is missing")
    _require(any(base == "project_root" and path.startswith("Config/") for base, path in paths),
             "project Config inventory is missing")
    # This is only a necessary lexical minimum, not discovery of whole Source/,
    # plugins or selected-map dependencies. Receipt/runtime checks remain required.
    schema_entry = next(e for e in before if e["base"] == "authority_root"
                        and e["path"] == "contracts/current/scenario_collection_v1.schema.json")
    _require(schema_entry["sha256"] == value["collection_schema_sha256"], "collection Schema inventory digest mismatch")
    _modules(value["module_artifacts"])
    _distinct_paths([value["build_log"], value["build_receipt"]])
    for name in ("compiler", "linker", "build_tool"):
        _unique((tool["installed_path"] for tool in value["engine_toolchain_identity"][name]), f"{name} executable")


def _start(value: dict) -> None:
    _inventory(value["source_inventory"])
    _modules(value["loaded_module_inventory"])


def _sample(input_hash: str, episode: str, decision: int, label_hash: str) -> str:
    raw = episode.encode("utf-8")
    material = (b"ANPCSAMPLE2" + bytes.fromhex(input_hash) + struct.pack("<I", len(raw)) + raw
                + struct.pack("<Q", decision) + bytes.fromhex(label_hash))
    return hashlib.sha256(material).hexdigest()


def _raw(value: dict) -> None:
    feature = hashlib.sha256(b"ANPCFEAT1" + b"".join(bytes.fromhex(h) for h in value["contract_hashes"][:6])).hexdigest()
    _require(value["feature_contract_hash"] == feature, "feature hash formula mismatch")
    labels = value["labels"]
    _ordered_unique(labels["acceptable_candidate_indices"], "acceptable indices")
    _ordered_unique([tuple(pair) for pair in labels["preference_pairs"]], "preference pairs")
    _ordered_unique(labels["reason_tags"], "reason tags")
    _require("scenario_collection_utility_unreviewed" in labels["reason_tags"], "missing Utility-unreviewed reason tag")
    for blob, digest in (("input_cbor_base64", "input_content_hash"), ("label_cbor_base64", "label_block_hash"),
                         ("candidate_bytes_base64", "candidate_set_hash")):
        _require(hashlib.sha256(_base64_bytes(value[blob])).hexdigest() == value[digest], f"declared {blob} digest mismatch")
    expected = _sample(value["input_content_hash"], value["episode_id"], value["decision_id"], value["label_block_hash"])
    _require(value["sample_id"] == expected, "raw sample identity mismatch")


def _import(value: dict) -> None:
    closure = value["completion_closure"]
    _closure(closure)
    episodes = {ep["collection_episode_id"] for ep in closure["ordered_episodes"]}
    entries = value["entries"]
    _unique((e["raw_capture"]["sample_id"] for e in entries), "raw sample")
    _unique(((e["raw_capture"]["episode_id"], e["raw_capture"]["decision_id"]) for e in entries), "Capture decision")
    _require([e["snapshot_row"]["row_ordinal"] for e in entries] == list(range(len(entries))), "Snapshot row ordinals must be contiguous and ordered")
    descriptors = [value["snapshot"]["shard"], value["snapshot"]["manifest"]]
    for entry in entries:
        _require(entry["collection_episode_id"] in episodes, "Capture references unknown collection episode")
        capture = entry["capture"]["path"]
        _require(capture.endswith(".anpccap2"), "Capture extension mismatch")
        _require(entry["committed"]["path"] == capture + ".committed", "Capture/marker path pairing mismatch")
        descriptors.extend([entry["capture"], entry["committed"]])
        raw, row = entry["raw_capture"], entry["snapshot_row"]
        _raw(raw)
        prefix = f"scenario_capture_{closure['session_id']}_{entry['collection_episode_id']}_"
        sequence = raw["episode_id"].removeprefix(prefix)
        _require(raw["episode_id"].startswith(prefix) and len(sequence) == 20 and sequence.isascii()
                 and sequence.isdecimal() and 0 < int(sequence) <= 18446744073709551615,
                 "collection Capture episode namespace/sequence mismatch")
        generator = (f"neuralgame_scenario_collection_v1:{closure['catalog_sha256']}:"
                     f"{closure['collection_execution_profile_sha256']}:observed_geometry_goal_v1")
        _require(raw["generator_version"] == generator, "collection generator version mismatch")
        _require(raw["contract_hashes"][6] == closure["runtime_build_evidence_sha256"], "raw Runtime build mismatch")
        _require(all(row[k] == raw[k] for k in ("episode_id", "decision_id", "input_content_hash")), "Snapshot identity mismatch")
        _require(row["groups"] == dict(zip(GROUP_ORDER, raw["group_dimensions"], strict=True)), "group mapping mismatch")
        _require(row["abstain"] == (not raw["labels"]["acceptable_candidate_indices"]), "abstain mismatch")
        _require(row["parent_policy_sha256"] == (raw["parent_policy_hash"] or None), "parent policy mapping mismatch")
        _require(row["source_decision_contract_hash"] == (raw["contract_hashes"][7] or None), "source decision mapping mismatch")
        _require(row["profile_sha256"] == closure["collection_execution_profile_sha256"], "Snapshot profile mismatch")
    _distinct_paths(descriptors)


def _teacher(value: dict) -> None:
    profile = value["profile"]
    _require(profile["teacher_profile_sha256"] == profile["artifact"]["sha256"], "Teacher Profile digest mismatch")
    fixture = profile["scope"] == "integration_fixture"
    expected = "teacher_silver_v1.0.0" + ("-integration" if fixture else "")
    _require(profile["profile_version"] == expected, "Teacher Profile scope/version mismatch")
    _require(profile["provider"]["type"] != "replay_fixture" or fixture, "replay provider requires fixture Profile")
    if profile["provider"]["type"] == "command":
        _require(all(profile["provider"]["command"]), "Teacher command arguments must be nonempty")
    requests = value["requests"]
    _unique((r["snapshot_row_ordinal"] for r in requests), "Teacher Snapshot row")
    _unique(((r["episode_id"], r["decision_id"]) for r in requests), "Teacher decision")
    descriptors = [value["annotation"], value["review_queue"], value["snapshot"]["shard"], value["snapshot"]["manifest"],
                   value["import_index"], profile["artifact"], profile["prompt"], profile["request_schema"], profile["response_schema"]]
    for request in requests:
        descriptors.append(request["request"])
        _require([a["call_index"] for a in request["attempts"]] == list(range(5)), "five attempts require ordered call indices 0..4")
        for attempt in request["attempts"]:
            failed = attempt["outcome"] == "provider_error"
            _require(failed == (attempt["provider_error"] is not None), "provider outcome/error mismatch")
            descriptors.append(attempt["raw_stdout"])
    _distinct_paths(descriptors)


def _human(value: dict) -> None:
    auth = value["reviewer_authorization"]
    sources = {"decision_set_sha256": value["decision_set"], "review_queue_sha256": value["review_queue"],
               "snapshot_shard_sha256": value["snapshot"]["shard"], "snapshot_manifest_sha256": value["snapshot"]["manifest"]}
    for key, descriptor in sources.items():
        _require(value[key] == descriptor["sha256"] == auth[key], f"Human decision/source binding mismatch: {key}")
    for name, principals in (("reviewer principals", auth["principals"]), ("decision reviewers", value["decision_reviewers"])):
        _ordered_unique([p.encode("utf-8") for p in principals], name)
        _require(all(unicodedata.normalize("NFC", p) == p for p in principals), "reviewer principal must be NFC")
    _require(auth["principals"] == value["decision_reviewers"], "reviewer declaration/authorization list mismatch")
    _distinct_paths([*sources.values(), value["teacher_run"]["receipt"], value["import_index"]])


def _derived(value: dict) -> None:
    rows = value["rows"]
    _require([r["dataset_row_ordinal"] for r in rows] == list(range(len(rows))), "Dataset row ordinals must be contiguous and ordered")
    for key in ("original_sample_id", "derived_sample_id", "snapshot_row_ordinal"):
        _unique((row[key] for row in rows), key)
    for row in rows:
        weight = 0.25 if row["source_type"] == "silver" else 1.0
        _require(row["source_weight"] == weight, "Dataset source/weight mismatch")
        _require(row["source_type"] != "gold" or value["human_review"] is not None, "Gold requires Human completion reference")
        for prefix in ("original", "derived"):
            expected = _sample(row["input_content_hash"], row["episode_id"], row["decision_id"], row[prefix + "_label_block_hash"])
            _require(row[prefix + "_sample_id"] == expected, f"{prefix} sample identity mismatch")
    descriptors = [value["import_index"], value["teacher_run"]["receipt"], *value["snapshot"].values(), *value["dataset"].values()]
    if value["human_review"] is not None:
        descriptors.append(value["human_review"]["receipt"])
    _distinct_paths(descriptors)


def _consistency(kind: str, value: dict) -> None:
    _descriptor_consistency(value)
    if kind == "utility_profile_source":
        _inventory(value["entries"])
        _require(tuple(e["path"] for e in value["entries"]) == UTILITY_PATHS, "Utility source inventory mismatch")
        return
    checks = {"completion_closure": _closure, "collection_execution_profile": _profile,
              "runtime_build_evidence": _build, "session_start_evidence": _start, "import_index": _import,
              "teacher_completion_evidence": _teacher, "human_completion_evidence": _human, "derived_index": _derived}
    checks[kind](value)


def validate_artifact(value: Any, *, kind: str | None = None) -> dict:
    """Validate one declaration; the returned report is never a capability."""
    try:
        _json_types(value)
        _require(type(value) is dict, "artifact must be an object")
        if kind is None:
            _require(type(value.get("format")) is str, "artifact format must be a string")
            kind = _FORMATS.get(value["format"])
        if type(kind) is not str or kind not in KINDS:
            raise ValidationError("unknown artifact format/kind; closure requires explicit kind")
        error = next(_VALIDATORS[kind].iter_errors(value), None)
        if error is not None:
            path = "/".join(map(str, error.absolute_path))
            raise ValidationError(f"{kind}/{path}: {error.message}")
        _consistency(kind, value)
    except ValidationError:
        raise
    except (UnicodeError, RecursionError, struct.error, ValueError) as exc:
        raise ValidationError(f"invalid artifact: {exc}") from exc
    return {"authorization_status": "structure_only", "origin_authorized": False,
            "label_authorized": False, "training_eligible": False, "production_eligible": False}


def validate_bytes(data: bytes, *, kind: str | None = None) -> dict:
    """Parse and validate the exact submitted JSON byte image without reopening it."""
    value = _loads(data)
    _require(data == artifact_bytes(value), "artifact bytes must be sorted compact UTF-8 JSON plus one LF")
    return validate_artifact(value, kind=kind)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="JSON declaration to check; descriptor targets are never read")
    parser.add_argument("--kind", choices=KINDS, help="required for a standalone completion_closure")
    args = parser.parse_args(argv)
    try:
        report = validate_bytes(args.artifact.read_bytes(), kind=args.kind)
    except (OSError, ValidationError) as exc:
        print(f"INVALID STRUCTURE: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
