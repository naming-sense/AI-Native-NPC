#!/usr/bin/env python3
"""Strict scenario-collection V1 contracts; no Runtime execution or Dataset import.

Paths are read-only. Callers own exclusive publication and a stable trusted root.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator, validators

from tools import validate_anpc_capture_v2 as capture_v2

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts/current/scenario_collection_v1.schema.json"
CATALOG_PATH = ROOT / "contracts/current/scenario_catalog_v1.json"
FAMILY_KEYS = ("scenario_family_id", "template_family", "layout_family", "event_sequence_family")
OBSERVATION_MAPPING_VERSION = "observed_geometry_goal_v1"
PROVENANCE_KEYS = ("input_source", "execution_mode", "controller", "observation_mapping_version")
REPLAY_KEYS = ("scenario_id", "scenario_version", "variant_id", "map", "conditions", "seeds", "family")
SUPPORTED = {
    "hearing_only": ("move_for_hearing",),
    "hearing_appearance": ("move_for_hearing", "appear"),
    "hearing_appearance_loss": ("move_for_hearing", "appear", "lose_target"),
}
UNSUPPORTED = {"relationship_friendly", "relationship_hostile", "low_identity", "unreachable_greet"}
TERMINAL = {"completed", "cancelled", "timed_out", "failed"}
# Preserve the legacy summary API even when the decoder exposes additional payload fields.
_CAPTURE_SUMMARY_KEYS = (
    "path", "bytes", "record_version", "sample_id", "input_content_hash", "label_block_hash",
    "candidate_set_hash", "feature_contract_hash", "episode_id", "decision_id",
    "selected_candidate_index", "source_type", "map_seed", "simulation_seed", "scenario_family_id",
    "group_dimensions", "generator_version", "prompt_version", "annotator_set_hash", "tensor_lengths",
    "valid_candidate_count", "acceptable_candidate_count", "canonical_cbor_parity", "committed_marker",
)


class ValidationError(ValueError):
    """Invalid structure, binding, artifact, provenance or lifecycle operation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValidationError(f"nonfinite JSON constant: {value}")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object_pairs,
                          parse_constant=_invalid_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load JSON {path}: {exc}") from exc


_SCHEMA_BYTES = SCHEMA_PATH.read_bytes()
_SCHEMA = json.loads(_SCHEMA_BYTES, object_pairs_hook=_object_pairs, parse_constant=_invalid_constant)
_SCHEMA_SHA256 = hashlib.sha256(_SCHEMA_BYTES).hexdigest()
_type_checker = Draft202012Validator.TYPE_CHECKER.redefine_many({
    "integer": lambda checker, value: type(value) is int,
    "number": lambda checker, value: type(value) is int or (type(value) is float and math.isfinite(value)),
})
_Validator = validators.extend(Draft202012Validator, type_checker=_type_checker)


def _json_types(value: Any) -> None:
    # Refuse Python-only values and nonfinite numbers before schema evaluation.
    if type(value) in (str, int, bool, type(None)):
        return
    if type(value) is float:
        _require(math.isfinite(value), "nonfinite number")
        return
    if type(value) is list:
        for item in value:
            _json_types(item)
        return
    _require(type(value) is dict, "value is not a JSON type")
    for key, item in value.items():
        _require(type(key) is str, "object keys must be strings")
        _json_types(item)


def validate_structure(kind: str, value: Any) -> None:
    """Validate a named schema definition; semantic/catalog checks are separate."""
    _require(kind in _SCHEMA["$defs"], f"unknown schema kind: {kind}")
    _json_types(value)
    validator = _Validator({"$ref": f"#/$defs/{kind}", "$defs": _SCHEMA["$defs"]})
    error = next(validator.iter_errors(value), None)
    if error:
        location = "/".join(str(part) for part in error.absolute_path)
        raise ValidationError(f"{kind}/{location}: {error.message}")


def catalog_digest(catalog: dict) -> str:
    validate_catalog(catalog)
    raw = json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def contract_hashes() -> dict[str, str]:
    return {
        "collection_schema_sha256": _SCHEMA_SHA256,
        "capture_schema_sha256": capture_v2.SCHEMA_SHA256,
        "skill_registry_sha256": capture_v2.SKILL_REGISTRY_SHA256,
        "goal_registry_sha256": capture_v2.GOAL_REGISTRY_SHA256,
    }


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    result = _load_json(path)
    validate_catalog(result)
    return result


def validate_catalog(catalog: dict) -> None:
    validate_structure("catalog", catalog)
    ids = [scenario["id"] for scenario in catalog["scenarios"]]
    _require(len(ids) == len(set(ids)), "duplicate scenario id")
    _require(set(ids) == set(SUPPORTED) | UNSUPPORTED, "catalog scenario inventory mismatch")
    for scenario in catalog["scenarios"]:
        name = scenario["id"]
        _require(scenario["supported"] == (name in SUPPORTED), f"unsupported scenario cannot be enabled: {name}")
        for values in scenario["variations"].values():
            _require(all(type(value) is int for value in values), "variation defaults require integer values")
        events = scenario["events"]
        _require(tuple(event["type"] for event in events) == SUPPORTED.get(name, ()), f"event sequence mismatch: {name}")
        _require([event["order"] for event in events] == list(range(len(events)))
                 and all(type(event["order"]) is int for event in events), "event order mismatch")
        termination = scenario["termination"]
        _require(termination["preparation_timeout_seconds"] <= termination["max_duration_seconds"], "preparation bound exceeds duration")
        _require(sum(event["timeout_seconds"] for event in events) <= termination["max_duration_seconds"], "event deadlines exceed duration")
        for event in events:
            if event["type"] == "move_for_hearing":
                _require(event["movement_seconds"] <= event["timeout_seconds"], "movement exceeds event timeout")


def validate_conditions(catalog: dict, scenario_id: str, conditions: dict) -> dict:
    validate_catalog(catalog)
    validate_structure("conditions", conditions)
    scenario = next((item for item in catalog["scenarios"] if item["id"] == scenario_id), None)
    if scenario is None:
        raise ValidationError(f"unknown scenario: {scenario_id}")
    _require(scenario["supported"], f"unsupported scenario: {scenario_id}: {scenario['unsupported_reason']}")
    for key, value in conditions.items():
        _require(value in scenario["variations"][key], f"condition outside catalog: {key}")
    return copy.deepcopy(scenario)


def _provenance(value: dict) -> None:
    human = value["controller"] == "human"
    _require((value["input_source"] == "human_play") == human, "controller/input_source provenance mismatch")
    if value["execution_mode"] == "manual":
        _require(human, "manual mode requires a human controller")
    if value["execution_mode"] == "automatic":
        _require(not human, "automatic mode cannot claim human input")


def _session_bindings(session: dict, catalog: dict) -> None:
    validate_structure("session", session)
    _provenance(session)
    _require(session["catalog_sha256"] == catalog_digest(catalog), "stale catalog hash")
    _require(session["contract_hashes"] == contract_hashes(), "contract hash mismatch")
    limits = session["limits"]
    _require(limits["preparation_timeout_seconds"] <= limits["episode_timeout_seconds"], "preparation timeout exceeds episode timeout")


def validate_session(session: dict, catalog: dict, *, expected_profile_sha256: str,
                     expected_runtime_build_sha256: str, seen_session_ids: Iterable[str] = ()) -> None:
    _session_bindings(session, catalog)
    validate_structure("hash", expected_profile_sha256)
    validate_structure("hash", expected_runtime_build_sha256)
    _require(session["profile_sha256"] == expected_profile_sha256, "profile hash mismatch")
    _require(session["runtime_build_sha256"] == expected_runtime_build_sha256, "runtime build hash mismatch")
    _require(session["session_id"] not in seen_session_ids, "duplicate session id")


def validate_episode(episode: dict, session: dict, catalog: dict, *, replay_original: dict | None = None) -> None:
    _session_bindings(session, catalog)
    validate_structure("episode", episode)
    _provenance(episode)
    _require(episode["session_id"] == session["session_id"], "episode session mismatch")
    _require(all(episode[key] == session[key] for key in PROVENANCE_KEYS), "episode provenance mismatch")
    scenario = validate_conditions(catalog, episode["scenario_id"], episode["conditions"])
    _require(episode["scenario_version"] == scenario["version"] and episode["map"] == scenario["map"], "scenario version/map mismatch")
    _require(all(episode["family"][key] == scenario[key] for key in FAMILY_KEYS), "episode family mismatch")
    conditions = episode["conditions"]
    variant = f"d{conditions['distance_cm']}-a{conditions['approach_angle_deg']}-s{conditions['seed']}"
    _require(episode["variant_id"] == variant, "variant id mismatch")
    _require(all(seed == conditions["seed"] for seed in episode["seeds"].values()), "resolved seed mismatch")
    limits = session["limits"]
    _require(limits["episode_timeout_seconds"] <= scenario["termination"]["max_duration_seconds"], "episode budget exceeds scenario bound")
    _require(limits["preparation_timeout_seconds"] <= scenario["termination"]["preparation_timeout_seconds"], "preparation budget exceeds scenario bound")
    active = episode["state"] not in TERMINAL
    _require((episode["reason"] is None) == active, "terminal outcome requires reason; active outcome forbids reason")
    _require(not active or episode["reset_result"] == "not_attempted", "active episode cannot have reset result")
    observations = episode["event_observations"]
    _require([item["order"] for item in observations] == list(range(len(observations))), "observations must be an ordered prefix")
    times = [item["observed_at_seconds"] for item in observations]
    _require(times == sorted(times) and all(time <= limits["episode_timeout_seconds"] for time in times), "event observation time invalid")
    _require(len(observations) <= len(scenario["events"]), "too many event observations")
    _require(episode["state"] != "preparing" or not observations, "preparing episode has observations")
    _require(episode["state"] != "completed" or len(observations) == len(scenario["events"]), "completion requires all event observations")
    _require(episode["state"] != "completed" or all(time < limits["episode_timeout_seconds"] for time in times),
             "completion requires observations before episode timeout")
    if episode["execution_mode"] != "replay":
        _require("replay_of" not in episode, "non-replay episode has replay link")
        return
    if "replay_of" not in episode or replay_original is None:
        raise ValidationError("replay requires its original episode")
    validate_structure("episode", replay_original)
    _provenance(replay_original)
    _require(episode["replay_of"] == replay_original["collection_episode_id"], "replay predecessor mismatch")
    _require(episode["collection_episode_id"] != episode["replay_of"], "replay must use a new id")
    _require(all(episode[key] == replay_original[key] for key in REPLAY_KEYS), "replay conditions/family changed")


def replay_episode(original: dict, new_id: str, session: dict) -> dict:
    validate_structure("episode", original)
    validate_structure("session", session)
    validate_structure("uuid", new_id)
    _provenance(session)
    _require(session["execution_mode"] == "replay", "replay requires explicit session mode")
    _require(new_id != original["collection_episode_id"], "replay must use a new id")
    result = copy.deepcopy(original)
    result.update(session_id=session["session_id"], collection_episode_id=new_id,
                  replay_of=original["collection_episode_id"], state="preparing", reason=None,
                  reset_result="not_attempted", event_observations=[])
    result.update({key: session[key] for key in PROVENANCE_KEYS})
    return result


def confine_artifact_path(root: Path, relative_path: str, *, must_exist: bool = True,
                          must_not_exist: bool = False) -> Path:
    validate_structure("path", relative_path)
    if must_not_exist:
        must_exist = False
    posix = PurePosixPath(relative_path)
    windows = PureWindowsPath(relative_path)
    _require(not posix.is_absolute() and not windows.drive and not windows.root and "\\" not in relative_path, "absolute/drive path forbidden")
    _require(all(part not in ("", ".", "..") for part in relative_path.split("/")), "noncanonical/traversal path forbidden")
    try:
        trusted_root = Path(root).resolve(strict=True)
        _require(trusted_root.is_dir(), "root is not a directory")
        candidate = trusted_root / relative_path
        _require(not must_not_exist or not (candidate.exists() or candidate.is_symlink()), "artifact already exists; overwrite forbidden")
        resolved = candidate.resolve(strict=must_exist)
        _require(resolved.is_relative_to(trusted_root), "symlink escapes collection root")
        _require(not must_exist or resolved.is_file(), "artifact is not a file")
        return resolved
    except (OSError, RuntimeError) as exc:
        raise ValidationError(f"invalid artifact path {relative_path}: {exc}") from exc


def _artifact(root: Path, descriptor: dict) -> tuple[Path, bytes]:
    validate_structure("artifact", descriptor)
    path = confine_artifact_path(root, descriptor["path"])
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValidationError(f"cannot read artifact {path}: {exc}") from exc
    _require(len(data) == descriptor["size_bytes"], "artifact size mismatch")
    _require(hashlib.sha256(data).hexdigest() == descriptor["sha256"], "artifact hash mismatch")
    return path, data


def validate_committed_entry(entry: dict, root: Path) -> dict:
    validate_structure("committedEntry", entry)
    _provenance(entry)
    capture_name = entry["capture"]["path"]
    _require(capture_name.endswith(".anpccap2"), "capture extension mismatch")
    _require(entry["committed"]["path"] == capture_name + ".committed", "marker path mismatch")
    capture_path, capture_bytes = _artifact(root, entry["capture"])
    marker_path, marker_bytes = _artifact(root, entry["committed"])
    # Preserve the resolved Capture/marker pairing independently of byte decoding.
    _require(Path(str(capture_path) + ".committed").resolve() == marker_path, "resolved capture/marker alias mismatch")
    try:
        result = capture_v2.decode_committed_capture_bytes(capture_bytes, marker_bytes, path=capture_path)
    except (OSError, capture_v2.ValidationError) as exc:
        raise ValidationError(f"committed Capture invalid: {exc}") from exc
    _require(all(result[key] == value for key, value in entry["capture_identity"].items()), "capture identity mismatch")
    _require(result["scenario_family_id"] == entry["family"]["scenario_family_id"], "capture family mismatch")
    return {key: result[key] for key in _CAPTURE_SUMMARY_KEYS}


def validate_family_splits(episodes: Iterable[dict]) -> None:
    assignments: dict[tuple[str, str], str] = {}
    for episode in episodes:
        validate_structure("family", episode["family"])
        family = episode["family"]
        split = family["split"]
        if split == "unassigned":
            continue
        for key in FAMILY_KEYS:
            group = (key, family[key])
            _require(group not in assignments or assignments[group] == split, f"family split leakage: {key}={family[key]}")
            assignments[group] = split


def validate_index(index: dict, root: Path, session: dict, episodes: Iterable[dict], catalog: dict, *,
                   expected_profile_sha256: str, expected_runtime_build_sha256: str,
                   replay_originals: Iterable[dict] = ()) -> dict:
    validate_session(session, catalog, expected_profile_sha256=expected_profile_sha256,
                     expected_runtime_build_sha256=expected_runtime_build_sha256)
    validate_structure("index", index)
    _require(index["session_id"] == session["session_id"], "index session mismatch")
    episodes = list(episodes)
    by_id = {}
    for episode in episodes:
        validate_structure("episode", episode)
        key = episode["collection_episode_id"]
        _require(key not in by_id, "duplicate collection episode id")
        by_id[key] = episode
    _require(len(episodes) <= session["limits"]["max_episodes"], "episode budget exceeded")
    originals = {}
    for original in replay_originals:
        validate_structure("episode", original)
        _provenance(original)
        key = original["collection_episode_id"]
        _require(key not in by_id and key not in originals, "duplicate replay predecessor/episode id")
        _require(original["session_id"] != session["session_id"], "external replay predecessor must belong to a different session")
        originals[key] = original
    for episode in episodes:
        validate_episode(episode, session, catalog, replay_original=originals.get(episode.get("replay_of")))
        originals[episode["collection_episode_id"]] = episode
    for previous in episodes[:-1]:
        _require(previous["state"] in TERMINAL and previous["reset_result"] == "verified",
                 "next episode requires a terminal predecessor with verified reset")
    validate_family_splits(episodes)
    paths: set[Path] = set()
    identities: set[tuple] = set()
    decisions: set[tuple[str, int]] = set()
    sample_ids: set[str] = set()
    diagnostics: set[str] = set()
    episode_counts: dict[str, int] = {}
    decision_limits = {item["id"]: item["termination"]["max_decisions"] for item in catalog["scenarios"]}
    storage_bytes = committed_count = diagnostic_count = 0
    for entry in index["entries"]:
        key = entry["collection_episode_id"]
        _require(key in by_id, "entry references unknown collection episode")
        episode = by_id[key]
        _provenance(entry)
        _require(all(entry[field] == episode[field] for field in (*PROVENANCE_KEYS, "family")), "entry provenance/family mismatch")
        descriptors = []
        if entry["kind"] == "committed":
            result = validate_committed_entry(entry, root)
            _require(all(result[name] == value for name, value in episode["seeds"].items()), "capture seed mismatch")
            identity = tuple(entry["capture_identity"][name] for name in ("episode_id", "decision_id", "input_content_hash", "sample_id"))
            decision = (result["episode_id"], result["decision_id"])
            _require(identity not in identities and result["sample_id"] not in sample_ids and decision not in decisions,
                     "duplicate/conflicting capture identity, sample or decision")
            identities.add(identity)
            decisions.add(decision)
            sample_ids.add(result["sample_id"])
            episode_counts[key] = episode_counts.get(key, 0) + 1
            _require(episode_counts[key] <= decision_limits[episode["scenario_id"]], "scenario decision budget exceeded")
            descriptors = [entry["capture"], entry["committed"]]
            committed_count += 1
        else:
            _require(entry["diagnostic_id"] not in diagnostics, "duplicate diagnostic id")
            diagnostics.add(entry["diagnostic_id"])
            if entry["snapshot_present"]:
                _artifact(root, entry["snapshot_ref"])
                descriptors = [entry["snapshot_ref"]]
            diagnostic_count += 1
        for descriptor in descriptors:
            path = confine_artifact_path(root, descriptor["path"])
            _require(path not in paths, "duplicate artifact path/alias")
            paths.add(path)
            storage_bytes += descriptor["size_bytes"]
    _require(storage_bytes <= session["limits"]["storage_limit_bytes"], "storage byte budget exceeded")
    return {"collection_episode_count": len(episodes), "committed_capture_count": committed_count,
            "diagnostic_count": diagnostic_count, "validated_row_count": 0, "production_eligible": False}


@dataclass(frozen=True)
class Lifecycle:
    max_episodes: int
    episode_timeout_seconds: float
    preparation_timeout_seconds: float
    state: str = "idle"
    started_ids: tuple[str, ...] = ()
    active_episode_id: str | None = None
    started_at_seconds: float | None = None
    last_at_seconds: float = 0
    reset_result: str = "not_attempted"
    last_outcome: str | None = None
    last_reason: str | None = None


def new_lifecycle(session: dict) -> Lifecycle:
    validate_structure("session", session)
    _provenance(session)
    limits = session["limits"]
    _require(limits["preparation_timeout_seconds"] <= limits["episode_timeout_seconds"], "preparation timeout exceeds episode timeout")
    return Lifecycle(limits["max_episodes"], limits["episode_timeout_seconds"], limits["preparation_timeout_seconds"])


def transition(lifecycle: Lifecycle, event: str, *, at_seconds: float,
               collection_episode_id: str | None = None, reason: str | None = None) -> Lifecycle:
    validate_structure("seconds", at_seconds)
    _require(at_seconds >= lifecycle.last_at_seconds, "time moved backwards")
    events = {"start", "ready", "completed", "cancelled", "failed", "check_timeout", "reset_verified", "reset_failed", "reset_unverified"}
    _require(event in events, "unknown lifecycle event")
    _require(lifecycle.state != "blocked", "session is blocked after failed/unverified reset")
    if event != "start" and collection_episode_id is not None:
        _require(collection_episode_id == lifecycle.active_episode_id, "stale episode callback")
    if event in ("reset_verified", "reset_failed", "reset_unverified"):
        _require(lifecycle.state == "awaiting_reset", "reset requires terminal episode")
    state = replace(lifecycle, last_at_seconds=at_seconds)
    if state.state in ("preparing", "running"):
        if state.started_at_seconds is None:
            raise ValidationError("active lifecycle is missing its start time")
        elapsed = at_seconds - state.started_at_seconds
        deadline = state.preparation_timeout_seconds if state.state == "preparing" else state.episode_timeout_seconds
        if elapsed >= deadline:
            timeout_reason = "preparation_timeout" if state.state == "preparing" else "episode_timeout"
            return replace(state, state="awaiting_reset", last_outcome="timed_out", last_reason=timeout_reason)
    if event == "check_timeout":
        return state
    if event == "start":
        _require(state.state == "idle", "only one active episode; verified reset required")
        validate_structure("uuid", collection_episode_id)
        _require(collection_episode_id not in state.started_ids, "duplicate collection episode id")
        _require(len(state.started_ids) < state.max_episodes, "episode budget exceeded")
        return replace(state, state="preparing", active_episode_id=collection_episode_id,
                       started_ids=state.started_ids + (collection_episode_id,), started_at_seconds=at_seconds,
                       reset_result="not_attempted")
    if event == "ready":
        _require(state.state == "preparing", "ready requires preparation")
        return replace(state, state="running")
    if event in ("completed", "cancelled", "failed"):
        allowed = ("running",) if event == "completed" else ("preparing", "running")
        _require(state.state in allowed, "terminal event requires active episode")
        validate_structure("text", reason)
        return replace(state, state="awaiting_reset", last_outcome=event, last_reason=reason)
    _require(state.state == "awaiting_reset", "reset requires terminal episode")
    result = event.removeprefix("reset_")
    return replace(state, state="idle" if result == "verified" else "blocked", reset_result=result,
                   active_episode_id=None, started_at_seconds=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        print(json.dumps({"catalog_sha256": catalog_digest(catalog), "scenario_count": len(catalog["scenarios"]),
                          "production_eligible": False}, sort_keys=True))
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
