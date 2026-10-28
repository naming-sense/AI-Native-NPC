"""Contract-first tests. All fabricated metadata below is explicitly test_fixture."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "contracts/current/scenario_catalog_v1.json"
SCHEMA = ROOT / "contracts/current/scenario_collection_v1.schema.json"
SID = "11111111-1111-4111-8111-111111111111"
EID = "22222222-2222-4222-8222-222222222222"
EID2 = "33333333-3333-4333-8333-333333333333"
DID = "44444444-4444-4444-8444-444444444444"
SID2 = "55555555-5555-4555-8555-555555555555"
EID3 = "66666666-6666-4666-8666-666666666666"
PROFILE = "a" * 64
BUILD = "b" * 64
MAPPING = "observed_geometry_goal_v1"
PIN = {"expected_profile_sha256": PROFILE, "expected_runtime_build_sha256": BUILD}


@pytest.fixture
def api():
    assert importlib.util.find_spec("tools.validate_scenario_collection") is not None, "scenario collection harness is not implemented"
    return importlib.import_module("tools.validate_scenario_collection")


@pytest.fixture
def catalog(api):
    return api.load_catalog()


def session_for(api, catalog):
    return {
        "format": "scenario_collection_session_v1", "version": 1, "session_id": SID,
        "catalog_sha256": api.catalog_digest(catalog), "profile_sha256": PROFILE,
        "runtime_build_sha256": BUILD, "contract_hashes": api.contract_hashes(),
        "observation_mapping_version": MAPPING,
        "input_source": "test_fixture", "execution_mode": "automatic", "controller": "automated",
        "limits": {"max_episodes": 2, "episode_timeout_seconds": 30,
                   "preparation_timeout_seconds": 10, "storage_limit_bytes": 1000000},
    }


@pytest.fixture
def session(api, catalog):
    return session_for(api, catalog)


def episode_for(catalog, session, index=0):
    scenario = catalog["scenarios"][index]
    return {
        "format": "scenario_collection_episode_v1", "version": 1, "session_id": session["session_id"],
        "collection_episode_id": EID, "scenario_id": scenario["id"], "scenario_version": scenario["version"],
        "variant_id": "d400-a0-s0", "map": scenario["map"],
        "conditions": {"distance_cm": 400, "approach_angle_deg": 0, "seed": 0},
        "seeds": {"map_seed": 0, "simulation_seed": 0},
        "family": {**{key: scenario[key] for key in ("scenario_family_id", "template_family", "layout_family", "event_sequence_family")}, "split": "unassigned"},
        **{key: session[key] for key in ("input_source", "execution_mode", "controller", "observation_mapping_version")},
        "state": "preparing", "reason": None, "reset_result": "not_attempted", "event_observations": [],
    }


@pytest.fixture
def episode(catalog, session):
    return episode_for(catalog, session)


def diagnostic(episode):
    return {
        "kind": "diagnostic", "diagnostic_id": DID,
        **{key: copy.deepcopy(episode[key]) for key in ("collection_episode_id", "input_source", "execution_mode", "controller", "family", "observation_mapping_version")},
        "observed_id": None, "stage": "preparation", "reason": "no observation before timeout",
        "observed_at_seconds": 10, "snapshot_present": False, "snapshot_ref": None,
    }


def index_for(entries):
    return {"format": "scenario_collection_index_v1", "version": 1, "session_id": SID, "entries": entries}


def test_required_artifacts_exist():
    assert SCHEMA.is_file(), "strict JSON schema has not been implemented"
    assert CATALOG.is_file(), "deterministic scenario catalog has not been implemented"


def test_catalog_schema_and_cli(api, catalog):
    from jsonschema import Draft202012Validator
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    api.validate_structure("catalog", catalog)
    assert catalog["scope"] == "production_candidate"
    assert catalog["support_semantics"] == "code_supported_pending_runtime_validation"
    assert [item["id"] for item in catalog["scenarios"] if item["supported"]] == ["hearing_only", "hearing_appearance", "hearing_appearance_loss"]
    unsupported = {item["id"]: item for item in catalog["scenarios"] if not item["supported"]}
    assert set(unsupported) == {"relationship_friendly", "relationship_hostile", "low_identity", "unreachable_greet"}
    assert all(item["unsupported_reason"] and item["events"] == [] for item in unsupported.values())
    assert all(item["variations"] == {"distance_cm": [400, 600], "approach_angle_deg": [0], "seed": [0, 1, 2]} for item in catalog["scenarios"])
    result = subprocess.run([sys.executable, "-m", "tools.validate_scenario_collection"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert api.catalog_digest(catalog) in result.stdout


@pytest.mark.parametrize("mutation", [
    lambda c: c["scenarios"].append(copy.deepcopy(c["scenarios"][0])),
    lambda c: c["scenarios"][0].update(command="quit"),
    lambda c: c["scenarios"][0]["events"][0].update(type="inject_hearing"),
    lambda c: c["scenarios"][0]["events"][0].update(condition={"goal": "Navigate"}),
    lambda c: c["scenarios"][0]["events"][0].update(order=1),
    lambda c: c["scenarios"][0]["events"][0].update(movement_seconds=11),
    lambda c: c["scenarios"][0]["termination"].update(max_duration_seconds=0),
    lambda c: c["scenarios"][0]["termination"].update(max_duration_seconds=5),
    lambda c: c["scenarios"][0]["variations"].update(distance_cm=[400, -1]),
    lambda c: c["scenarios"][0].update(map="/Game/Other"),
    lambda c: c["scenarios"][3].update(supported=True, unsupported_reason=None),
    lambda c: c["scenarios"][3].update(unsupported_reason=""),
    lambda c: c["scenarios"].pop(),
])
def test_catalog_rejects_contract_drift(api, catalog, mutation):
    mutation(catalog)
    with pytest.raises(api.ValidationError):
        api.validate_catalog(catalog)


def test_loader_rejects_duplicate_json_keys_and_nan(api, tmp_path):
    path = tmp_path / "bad.json"
    for text in ('{"version":1,"version":1}', '{"version":NaN}'):
        path.write_text(text)
        with pytest.raises(api.ValidationError):
            api.load_catalog(path)
    result = subprocess.run([sys.executable, "-m", "tools.validate_scenario_collection", "--catalog", str(path)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1


@pytest.mark.parametrize("patch", [{"distance_cm": 500}, {"distance_cm": -1}, {"seed": 3}, {"approach_angle_deg": 90}, {"relationship": "friendly"}, {"seed": True}, {"seed": 0.0}, {"distance_cm": float("nan")}])
def test_conditions_reject_invalid_values(api, catalog, episode, patch):
    episode["conditions"].update(patch)
    with pytest.raises(api.ValidationError):
        api.validate_conditions(catalog, "hearing_only", episode["conditions"])


def test_conditions_reject_unsupported_and_unknown(api, catalog, episode):
    for name in ("relationship_friendly", "relationship_hostile", "low_identity", "unreachable_greet", "unknown"):
        with pytest.raises(api.ValidationError):
            api.validate_conditions(catalog, name, episode["conditions"])


def test_session_and_episode_positive(api, catalog, session, episode):
    api.validate_session(session, catalog, **PIN)
    api.validate_episode(episode, session, catalog)
    assert api.catalog_digest(catalog) == api.catalog_digest(json.loads(json.dumps(catalog, sort_keys=True)))


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(catalog_sha256="c" * 64),
    lambda s: s.update(profile_sha256="c" * 64),
    lambda s: s.update(runtime_build_sha256="c" * 64),
    lambda s: s["contract_hashes"].update(capture_schema_sha256="c" * 64),
    lambda s: s["limits"].update(max_episodes=0),
    lambda s: s["limits"].update(storage_limit_bytes=-1),
    lambda s: s["limits"].update(preparation_timeout_seconds=31),
    lambda s: s["limits"].update(episode_timeout_seconds=float("inf")),
    lambda s: s.update(input_source="human_play"),
    lambda s: s.update(execution_mode="replay", input_source="human_play"),
    lambda s: s.update(input_source="teacher_silver"),
    lambda s: s.update(execution_mode="manual"),
    lambda s: s.update(raw_count=100),
    lambda s: s.update(session_id="not-unique-id"),
])
def test_session_invariants(api, catalog, session, mutation):
    mutation(session)
    with pytest.raises(api.ValidationError):
        api.validate_session(session, catalog, **PIN)


def test_duplicate_session_id(api, catalog, session):
    with pytest.raises(api.ValidationError):
        api.validate_session(session, catalog, seen_session_ids=[SID], **PIN)


@pytest.mark.parametrize("mutation", [
    lambda e: e.update(session_id=EID2),
    lambda e: e.update(variant_id="other"),
    lambda e: e.update(input_source="human_play"),
    lambda e: e["seeds"].update(simulation_seed=1),
    lambda e: e["family"].update(layout_family="different"),
    lambda e: e.update(state="completed", reason=None),
    lambda e: e.update(state="completed", reason="done"),
    lambda e: e.update(reset_result="verified"),
    lambda e: e.update(replay_of=EID2),
    lambda e: e.update(event_observations=[{"order": 0, "observed_at_seconds": -1}]),
])
def test_episode_invariants(api, catalog, session, episode, mutation):
    mutation(episode)
    with pytest.raises(api.ValidationError):
        api.validate_episode(episode, session, catalog)


def test_completed_events_and_budget(api, catalog, session):
    episode = episode_for(catalog, session, 2)
    episode.update(state="completed", reason="events observed", event_observations=[{"order": n, "observed_at_seconds": n + 1} for n in range(3)])
    api.validate_episode(episode, session, catalog)
    episode["event_observations"][2]["observed_at_seconds"] = 1
    with pytest.raises(api.ValidationError):
        api.validate_episode(episode, session, catalog)
    session["limits"]["episode_timeout_seconds"] = 31
    with pytest.raises(api.ValidationError):
        api.validate_episode(episode, session, catalog)


def test_replay_new_identity_same_conditions_explicit_provenance(api, catalog, session, episode):
    original = copy.deepcopy(episode)
    original.update(input_source="human_play", controller="human", execution_mode="manual")
    session.update(execution_mode="replay", input_source="automated_runtime")
    replay = api.replay_episode(original, EID2, session)
    api.validate_episode(replay, session, catalog, replay_original=original)
    assert replay["replay_of"] == EID
    assert replay["collection_episode_id"] != EID
    assert replay["conditions"] == original["conditions"]
    assert replay["input_source"] == "automated_runtime"
    assert replay["event_observations"] == []
    with pytest.raises(api.ValidationError):
        api.replay_episode(original, EID, session)
    replay["conditions"]["seed"] = 1
    replay["seeds"] = {"map_seed": 1, "simulation_seed": 1}
    replay["variant_id"] = "d400-a0-s1"
    with pytest.raises(api.ValidationError):
        api.validate_episode(replay, session, catalog, replay_original=original)


@pytest.mark.parametrize("path", ["../capture", "a/../capture", "/capture", "C:/capture", "C:relative", "a\\b", "./capture", "a//b", ""])
def test_path_confinement_lexical(api, tmp_path, path):
    with pytest.raises(api.ValidationError):
        api.confine_artifact_path(tmp_path, path, must_exist=False)


def test_path_symlink_escape_and_no_overwrite(api, tmp_path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(api.ValidationError):
        api.confine_artifact_path(root, "escape/new", must_exist=False)
    (root / "kept").write_bytes(b"keep")
    with pytest.raises(api.ValidationError):
        api.confine_artifact_path(root, "kept", must_exist=False, must_not_exist=True)
    (root / "dangling").symlink_to(root / "missing")
    with pytest.raises(api.ValidationError):
        api.confine_artifact_path(root, "dangling", must_exist=False, must_not_exist=True)
    assert api.confine_artifact_path(root, "kept").read_bytes() == b"keep"
    assert api.confine_artifact_path(root, "new", must_exist=False, must_not_exist=True) == root / "new"


@pytest.mark.parametrize("group", ["scenario_family_id", "template_family", "layout_family", "event_sequence_family"])
def test_family_split_leakage_even_with_new_seed(api, episode, group):
    first = copy.deepcopy(episode)
    first["family"]["split"] = "train"
    second = copy.deepcopy(episode)
    second["collection_episode_id"] = EID2
    second["conditions"]["seed"] = 1
    second["family"] = {key: "other" for key in first["family"] if key != "split"}
    second["family"].update({"split": "validation", group: first["family"][group]})
    with pytest.raises(api.ValidationError):
        api.validate_family_splits([first, second])
    second["family"]["split"] = "unassigned"
    api.validate_family_splits([first, second])


@pytest.fixture
def committed(api, catalog, session, episode, tmp_path):
    # Reuse the existing golden Capture fixture/parser helpers; altered metadata is TEST ONLY.
    from test_validate_anpc_capture_v2 import FIXTURE, _parse_capture, _rebuild_capture
    from tools.validate_anpc_capture_v2 import COMMIT_MAGIC, validate_committed_capture
    parts = _parse_capture(FIXTURE.read_bytes())
    parts[1][7] = episode["family"]["scenario_family_id"]
    parts[6] = parts[7] = 0
    data = _rebuild_capture(parts)
    capture = tmp_path / "capture.anpccap2"
    capture.write_bytes(data)
    marker = Path(str(capture) + ".committed")
    prefix = COMMIT_MAGIC + struct.pack("<IQ", 1, len(data)) + hashlib.sha256(data).digest()
    marker.write_bytes(prefix + hashlib.sha256(prefix).digest())
    result = validate_committed_capture(capture)
    def artifact(path):
        raw = path.read_bytes()
        return {"path": path.name, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    entry = {
        "kind": "committed", **{key: copy.deepcopy(episode[key]) for key in ("collection_episode_id", "input_source", "execution_mode", "controller", "family", "observation_mapping_version")},
        "capture_identity": {key: result[key] for key in ("episode_id", "decision_id", "input_content_hash", "sample_id")},
        "capture": artifact(capture), "committed": artifact(marker),
    }
    return entry, capture, marker


def test_committed_bytes_and_counts(api, catalog, session, episode, committed, tmp_path):
    entry, _, _ = committed
    result = api.validate_committed_entry(entry, tmp_path)
    assert result["sample_id"] == entry["capture_identity"]["sample_id"]
    assert result["source_type"] == 0  # Existing label enum is unchanged.
    report = api.validate_index(index_for([entry, diagnostic(episode)]), tmp_path, session, [episode], catalog, **PIN)
    assert report == {"collection_episode_count": 1, "committed_capture_count": 1, "diagnostic_count": 1, "validated_row_count": 0, "production_eligible": False}


@pytest.mark.parametrize("mutation", [
    lambda e: e["capture_identity"].update(episode_id="forged"),
    lambda e: e["capture_identity"].update(decision_id=2),
    lambda e: e["capture_identity"].update(input_content_hash="c" * 64),
    lambda e: e["capture_identity"].update(sample_id="c" * 64),
    lambda e: e["capture"].update(sha256="c" * 64),
    lambda e: e["capture"].update(size_bytes=1),
    lambda e: e["committed"].update(path="wrong.committed"),
    lambda e: e.update(kind="diagnostic"),
])
def test_committed_identity_rejection(api, committed, tmp_path, mutation):
    entry, _, _ = committed
    mutation(entry)
    with pytest.raises(api.ValidationError):
        api.validate_committed_entry(entry, tmp_path)


@pytest.mark.parametrize("case", ["missing", "tampered", "escape", "bad_capture"])
def test_marker_validation(api, committed, tmp_path, case):
    entry, capture, marker = committed
    if case == "missing":
        marker.unlink()
    elif case == "escape":
        outside = tmp_path.parent / f"{tmp_path.name}-marker"
        outside.write_bytes(marker.read_bytes())
        marker.unlink()
        marker.symlink_to(outside)
    else:
        path = marker if case == "tampered" else capture
        path.write_bytes(b"invalid")
        key = "committed" if case == "tampered" else "capture"
        entry[key].update(size_bytes=7, sha256=hashlib.sha256(b"invalid").hexdigest())
    with pytest.raises(api.ValidationError):
        api.validate_committed_entry(entry, tmp_path)


@pytest.mark.parametrize("case", ["duplicate_entry", "duplicate_episode", "provenance", "family", "storage", "row_count", "capture_seed"])
def test_index_structural_invariants(api, catalog, session, episode, committed, tmp_path, case):
    entry, _, _ = committed
    index = index_for([entry])
    episodes = [episode]
    if case == "duplicate_entry":
        index["entries"].append(copy.deepcopy(entry))
    elif case == "duplicate_episode":
        episodes.append(copy.deepcopy(episode))
    elif case == "provenance":
        entry["input_source"] = "human_play"
    elif case == "family":
        entry["family"]["scenario_family_id"] = "different"
    elif case == "storage":
        session["limits"]["storage_limit_bytes"] = 1
    elif case == "row_count":
        index["validated_row_count"] = 100
    else:
        episode["conditions"]["seed"] = 1
        episode["seeds"] = {"map_seed": 1, "simulation_seed": 1}
        episode["variant_id"] = "d400-a0-s1"
    with pytest.raises(api.ValidationError):
        api.validate_index(index, tmp_path, session, episodes, catalog, **PIN)


def test_diagnostic_never_promoted(api, catalog, session, episode, tmp_path):
    entry = diagnostic(episode)
    report = api.validate_index(index_for([entry]), tmp_path, session, [episode], catalog, **PIN)
    assert report["committed_capture_count"] == report["validated_row_count"] == 0
    entry["capture_identity"] = {"episode_id": "invented"}
    with pytest.raises(api.ValidationError):
        api.validate_structure("diagnostic", entry)
    del entry["capture_identity"]
    entry["snapshot_ref"] = {"path": "fake", "size_bytes": 1, "sha256": "a" * 64}
    with pytest.raises(api.ValidationError):
        api.validate_structure("diagnostic", entry)
    entry.update(snapshot_present=True, snapshot_ref=None)
    with pytest.raises(api.ValidationError):
        api.validate_structure("diagnostic", entry)


def test_lifecycle_one_active_reset_and_reasons(api, session):
    state = api.new_lifecycle(session)
    started = api.transition(state, "start", at_seconds=0, collection_episode_id=EID)
    assert state.state == "idle"  # Pure immutable transitions.
    with pytest.raises(api.ValidationError):
        api.transition(started, "start", at_seconds=1, collection_episode_id=EID2)
    running = api.transition(started, "ready", at_seconds=1)
    done = api.transition(running, "completed", at_seconds=2, reason="observed events")
    assert done.last_outcome == "completed" and done.last_reason == "observed events"
    with pytest.raises(api.ValidationError):
        api.transition(done, "start", at_seconds=3, collection_episode_id=EID2)
    idle = api.transition(done, "reset_verified", at_seconds=3)
    assert idle.last_reason == "observed events"
    with pytest.raises(api.ValidationError):
        api.transition(idle, "start", at_seconds=4, collection_episode_id=EID)
    again = api.transition(idle, "start", at_seconds=4, collection_episode_id=EID2)
    cancelled = api.transition(again, "cancelled", at_seconds=5, reason="user requested stop")
    idle = api.transition(cancelled, "reset_verified", at_seconds=6)
    assert idle.last_outcome == "cancelled" and idle.last_reason == "user requested stop"
    with pytest.raises(api.ValidationError):
        api.transition(idle, "start", at_seconds=7, collection_episode_id=DID)


@pytest.mark.parametrize("reset", ["reset_failed", "reset_unverified"])
def test_reset_failure_blocks_all_restarts(api, session, reset):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    state = api.transition(state, "failed", at_seconds=1, reason="capture write failed")
    state = api.transition(state, reset, at_seconds=2)
    assert state.state == "blocked" and state.last_reason == "capture write failed"
    for event in ("start", "reset_verified"):
        with pytest.raises(api.ValidationError):
            api.transition(state, event, at_seconds=3, collection_episode_id=EID2)


def test_schema_path_rejects_parent_segments_without_filesystem(api):
    for path in ("a/../b", "a/./b", "a//b"):
        with pytest.raises(api.ValidationError):
            api.validate_structure("artifact", {"path": path, "size_bytes": 1, "sha256": PROFILE})


def test_new_path_reservation_default(api, tmp_path):
    assert api.confine_artifact_path(tmp_path, "new", must_not_exist=True) == tmp_path / "new"


def test_huge_integer_is_contract_error_not_overflow(api, session, catalog):
    session["limits"]["episode_timeout_seconds"] = 10 ** 1000
    with pytest.raises(api.ValidationError):
        api.validate_session(session, catalog, **PIN)


@pytest.mark.parametrize("state,reset", [("preparing", "not_attempted"), ("completed", "failed"), ("completed", "unverified"), ("completed", "not_attempted")])
def test_index_enforces_ordered_single_episode_reset_history(api, session, catalog, episode, tmp_path, state, reset):
    first = copy.deepcopy(episode)
    if state == "completed":
        first.update(state=state, reason="events observed", reset_result=reset,
                     event_observations=[{"order": 0, "observed_at_seconds": 1}])
    second = copy.deepcopy(episode)
    second["collection_episode_id"] = EID2
    with pytest.raises(api.ValidationError):
        api.validate_index(index_for([]), tmp_path, session, [first, second], catalog, **PIN)


def test_replay_index_with_separate_predecessor_inventory(api, session, catalog, episode, tmp_path):
    original = copy.deepcopy(episode)
    original.update(input_source="human_play", controller="human", execution_mode="manual", session_id=DID)
    session.update(execution_mode="replay", input_source="automated_runtime")
    replay = api.replay_episode(original, EID2, session)
    report = api.validate_index(index_for([diagnostic(replay)]), tmp_path, session, [replay], catalog,
                                replay_originals=[original], **PIN)
    assert report["collection_episode_count"] == 1
    assert report["diagnostic_count"] == 1
    with pytest.raises(api.ValidationError):
        api.validate_index(index_for([]), tmp_path, session, [replay], catalog,
                           replay_originals=[original, original], **PIN)


def test_lifecycle_rejects_stale_episode_callback(api, session):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    state = api.transition(state, "ready", at_seconds=1)
    with pytest.raises(api.ValidationError):
        api.transition(state, "failed", at_seconds=2, collection_episode_id=EID2, reason="stale callback")


def test_diagnostic_snapshot_bytes_and_duplicate_ids(api, session, catalog, episode, tmp_path):
    entry = diagnostic(episode)
    raw = b"test-only observed artifact; not a Snapshot importer fixture"
    path = tmp_path / "observation.bin"
    path.write_bytes(raw)
    entry.update(snapshot_present=True, snapshot_ref={"path": path.name, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    report = api.validate_index(index_for([entry]), tmp_path, session, [episode], catalog, **PIN)
    assert report["diagnostic_count"] == 1 and report["validated_row_count"] == 0
    with pytest.raises(api.ValidationError):
        api.validate_index(index_for([entry, copy.deepcopy(entry)]), tmp_path, session, [episode], catalog, **PIN)
    path.write_bytes(b"modified")
    with pytest.raises(api.ValidationError):
        api.validate_index(index_for([entry]), tmp_path, session, [episode], catalog, **PIN)


@pytest.mark.parametrize("kind,value", [("hash", PROFILE + "\n"), ("uuid", SID + "\n"), ("id", "case\n"), ("text", "reason\n"), ("captureId", "capture\n"), ("path", "artifact\n")])
def test_schema_rejects_trailing_control_characters(api, kind, value):
    with pytest.raises(api.ValidationError):
        api.validate_structure(kind, value)


def test_contract_hash_matches_loaded_schema_not_replacement(api, tmp_path, monkeypatch):
    expected = api.contract_hashes()
    replacement = tmp_path / "replacement.json"
    replacement.write_text('{"type":"null"}')
    monkeypatch.setattr(api, "SCHEMA_PATH", replacement)
    assert api.contract_hashes() == expected


@pytest.mark.parametrize("case", ["duplicate_decision", "decision_budget"])
def test_index_rejects_conflicting_decision_or_scenario_budget(api, catalog, session, episode, committed, tmp_path, case):
    from test_validate_anpc_capture_v2 import _parse_capture, _rebuild_capture, _refresh_identity
    from tools.validate_anpc_capture_v2 import COMMIT_MAGIC, CborReader, validate_committed_capture
    first, capture, _ = committed
    parts = _parse_capture(capture.read_bytes())
    if case == "decision_budget":
        parts[2] = 2
        catalog["scenarios"][0]["termination"]["max_decisions"] = 1
        session["catalog_sha256"] = api.catalog_digest(catalog)
    label = CborReader(parts[13][1]).complete()
    label[6] = ["different_test_annotation"]
    _refresh_identity(parts, label_obj=label)
    raw = _rebuild_capture(parts)
    second_capture = tmp_path / "second.anpccap2"
    second_capture.write_bytes(raw)
    second_marker = Path(str(second_capture) + ".committed")
    prefix = COMMIT_MAGIC + struct.pack("<IQ", 1, len(raw)) + hashlib.sha256(raw).digest()
    second_marker.write_bytes(prefix + hashlib.sha256(prefix).digest())
    summary = validate_committed_capture(second_capture)
    second = copy.deepcopy(first)
    second["capture_identity"] = {name: summary[name] for name in second["capture_identity"]}
    for key, path in (("capture", second_capture), ("committed", second_marker)):
        data = path.read_bytes()
        second[key] = {"path": path.name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    with pytest.raises(api.ValidationError):
        api.validate_index(index_for([first, second]), tmp_path, session, [episode], catalog, **PIN)


def test_observation_mapping_version_bound_on_all_sidecars(api, catalog, session, episode, committed, tmp_path):
    entry, _, _ = committed
    assert session["observation_mapping_version"] == episode["observation_mapping_version"] == entry["observation_mapping_version"] == MAPPING
    api.validate_session(session, catalog, **PIN)
    api.validate_episode(episode, session, catalog)
    report = api.validate_index(index_for([entry, diagnostic(episode)]), tmp_path, session, [episode], catalog, **PIN)
    assert report["committed_capture_count"] == 1
    assert api.OBSERVATION_MAPPING_VERSION == MAPPING


@pytest.mark.parametrize("kind", ["session", "episode", "committedEntry", "diagnostic"])
@pytest.mark.parametrize("bad", [None, "all_features_v1", "observed_geometry_goal_v2"])
def test_observation_mapping_missing_or_unsupported(api, session, episode, committed, kind, bad):
    entry, _, _ = committed
    value = {"session": session, "episode": episode, "committedEntry": entry, "diagnostic": diagnostic(episode)}[kind]
    if bad is None:
        value.pop("observation_mapping_version")
    else:
        value["observation_mapping_version"] = bad
    with pytest.raises(api.ValidationError):
        api.validate_structure(kind, value)


def test_lifecycle_timeout_and_invalid_events(api, session):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    assert api.transition(state, "check_timeout", at_seconds=9).state == "preparing"
    timeout = api.transition(state, "ready", at_seconds=10)
    assert timeout.last_outcome == "timed_out" and timeout.last_reason == "preparation_timeout"
    running = api.transition(state, "ready", at_seconds=1)
    timeout = api.transition(running, "completed", at_seconds=30, reason="late completion")
    assert timeout.last_outcome == "timed_out" and timeout.last_reason == "episode_timeout"
    for event, timestamp, reason in (("unknown", 2, None), ("completed", 2, None), ("check_timeout", -1, None), ("check_timeout", float("nan"), None)):
        with pytest.raises(api.ValidationError):
            api.transition(running, event, at_seconds=timestamp, reason=reason)


def test_committed_image_single_read_and_legacy_summary(api, committed, tmp_path, monkeypatch):
    entry, capture, marker = committed
    expected = api.capture_v2.validate_committed_capture(capture)
    read_bytes = Path.read_bytes
    decode = api.capture_v2.decode_committed_capture_bytes
    images = {}
    decoded = []

    def read_once(path):
        assert path in (capture, marker), "unexpected artifact read"
        assert path not in images, "artifact image was reopened"
        images[path] = read_bytes(path)
        return images[path]

    def decode_same_bytes(capture_bytes, marker_bytes, *, path):
        assert path == capture
        assert capture_bytes is images[capture]
        assert marker_bytes is images[marker]
        decoded.append(path)
        return decode(capture_bytes, marker_bytes, path=path)

    monkeypatch.setattr(Path, "read_bytes", read_once)
    monkeypatch.setattr(api.capture_v2, "decode_committed_capture_bytes", decode_same_bytes)
    result = api.validate_committed_entry(entry, tmp_path)
    assert result == expected  # No decoded payload keys may leak into the public summary.
    assert set(images) == {capture, marker}
    assert decoded == [capture]
    assert json.loads(json.dumps(result)) == expected


def invalid_committed_images(api, capture_bytes, marker_bytes, defect):
    # Deliberately invalid test_fixture bytes, with independently pinned sidecar hashes.
    if defect == "marker":
        return capture_bytes, marker_bytes + b"\0"
    body = capture_bytes + b"\0"
    prefix = api.capture_v2.COMMIT_MAGIC + struct.pack("<IQ", 1, len(body)) + hashlib.sha256(body).digest()
    return body, prefix + hashlib.sha256(prefix).digest()


@pytest.mark.parametrize("pinned_valid", [False, True], ids=["invalid-pinned", "valid-pinned"])
@pytest.mark.parametrize("defect", ["capture", "marker"])
def test_committed_image_transient_aba(api, committed, tmp_path, monkeypatch, pinned_valid, defect):
    entry, capture, marker = committed
    expected = api.capture_v2.validate_committed_capture(capture)
    valid = (capture.read_bytes(), marker.read_bytes())
    invalid = invalid_committed_images(api, *valid, defect)
    with pytest.raises(api.capture_v2.ValidationError):
        api.capture_v2.decode_committed_capture_bytes(*invalid, path=capture)
    pinned, transient = (valid, invalid) if pinned_valid else (invalid, valid)
    images = {}
    reads = {capture: 0, marker: 0}
    for key, path, initial, replacement in zip(("capture", "committed"), (capture, marker), pinned, transient):
        path.write_bytes(initial)
        entry[key].update(size_bytes=len(initial), sha256=hashlib.sha256(initial).hexdigest())
        images[path] = (initial, replacement)
    read_bytes = Path.read_bytes

    def aba_read(path):
        if path not in images:
            return read_bytes(path)
        reads[path] += 1
        initial, replacement = images[path]
        return replacement if reads[path] == 2 else initial

    monkeypatch.setattr(Path, "read_bytes", aba_read)
    if pinned_valid:
        assert api.validate_committed_entry(entry, tmp_path) == expected
    else:
        with pytest.raises(api.ValidationError, match="committed Capture invalid"):
            api.validate_committed_entry(entry, tmp_path)
    assert reads == {capture: 1, marker: 1}


def test_committed_image_retained_after_path_replacement(api, committed, tmp_path, monkeypatch):
    entry, capture, marker = committed
    expected = api.capture_v2.validate_committed_capture(capture)
    invalid = invalid_committed_images(api, capture.read_bytes(), marker.read_bytes(), "capture")
    read_bytes = Path.read_bytes
    reads = {capture: 0, marker: 0}

    def replace_after_read(path):
        raw = read_bytes(path)
        reads[path] += 1
        if path == marker and reads[path] == 1:
            capture.write_bytes(invalid[0])
            marker.write_bytes(invalid[1])
        return raw

    monkeypatch.setattr(Path, "read_bytes", replace_after_read)
    assert api.validate_committed_entry(entry, tmp_path) == expected
    assert reads == {capture: 1, marker: 1}
    assert (read_bytes(capture), read_bytes(marker)) == invalid


def test_committed_image_resolved_marker_alias_still_required(api, committed, tmp_path):
    entry, capture, marker = committed
    target = tmp_path / "target.anpccap2"
    capture.rename(target)
    capture.symlink_to(target)
    with pytest.raises(api.ValidationError, match="alias mismatch"):
        api.validate_committed_entry(entry, tmp_path)
    target_marker = Path(str(target) + ".committed")
    marker.rename(target_marker)
    marker.symlink_to(target_marker)
    assert api.validate_committed_entry(entry, tmp_path) == api.capture_v2.validate_committed_capture(target)


@pytest.mark.parametrize("phase,deadline", [("preparing", 10), ("running", 30)])
@pytest.mark.parametrize("offset", [-0.001, 0, 1], ids=["before", "at", "after"])
@pytest.mark.parametrize("event", ["reset_verified", "reset_failed", "reset_unverified"])
def test_reset_order_checked_before_timeout(api, session, phase, deadline, offset, event):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    if phase == "running":
        state = api.transition(state, "ready", at_seconds=1)
    # No returned timeout state may silently discard a reset callback and permit a restart.
    with pytest.raises(api.ValidationError, match="reset requires terminal episode"):
        api.transition(state, event, at_seconds=deadline + offset, collection_episode_id=EID)
    assert state.state == phase and state.reset_result == "not_attempted"


@pytest.mark.parametrize("outcome", ["completed", "cancelled", "failed", "preparation_timeout", "episode_timeout"])
@pytest.mark.parametrize("event", ["reset_verified", "reset_failed", "reset_unverified"])
def test_reset_after_terminal_preserves_result_and_restart_policy(api, session, outcome, event):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    if outcome != "preparation_timeout":
        state = api.transition(state, "ready", at_seconds=1)
    if outcome.endswith("timeout"):
        deadline = 10 if outcome == "preparation_timeout" else 30
        terminal = api.transition(state, "check_timeout", at_seconds=deadline)
        expected_outcome, expected_reason = "timed_out", outcome
    else:
        terminal = api.transition(state, outcome, at_seconds=2, reason="test_fixture terminal")
        expected_outcome, expected_reason = outcome, "test_fixture terminal"
    assert terminal.state == "awaiting_reset"
    reset = api.transition(terminal, event, at_seconds=31, collection_episode_id=EID)
    assert reset.reset_result == event.removeprefix("reset_")
    assert reset.last_outcome == expected_outcome and reset.last_reason == expected_reason
    assert reset.active_episode_id is None and reset.started_at_seconds is None
    if event == "reset_verified":
        assert reset.state == "idle"
        restarted = api.transition(reset, "start", at_seconds=32, collection_episode_id=EID2)
        assert restarted.state == "preparing" and restarted.active_episode_id == EID2
    else:
        assert reset.state == "blocked"
        for action in ("start", "ready", "completed", "cancelled", "failed", "check_timeout",
                       "reset_verified", "reset_failed", "reset_unverified"):
            with pytest.raises(api.ValidationError, match="session is blocked"):
                api.transition(reset, action, at_seconds=32, collection_episode_id=EID2 if action == "start" else None)


@pytest.fixture
def replay_history(api, catalog, session, episode):
    original_session = copy.deepcopy(session)
    original_session["session_id"] = SID2
    original = copy.deepcopy(episode)
    original.update(session_id=SID2, state="completed", reason="test_fixture events observed",
                    reset_result="verified", event_observations=[{"order": 0, "observed_at_seconds": 1}])
    api.validate_session(original_session, catalog, **PIN)
    api.validate_episode(original, original_session, catalog)
    session["execution_mode"] = "replay"
    first = api.replay_episode(original, EID2, session)
    first.update(state="completed", reason="test_fixture replay observed", reset_result="verified",
                 event_observations=[{"order": 0, "observed_at_seconds": 1}])
    second = api.replay_episode(first, EID3, session)
    return original, first, second


@pytest.mark.parametrize("link", ["forward", "cycle", "self"])
def test_replay_ancestry_rejects_nonpreceding_current_episode(api, catalog, session, replay_history, tmp_path, link):
    original, first, second = replay_history
    first["replay_of"] = first["collection_episode_id"] if link == "self" else second["collection_episode_id"]
    if link == "forward":
        second["replay_of"] = original["collection_episode_id"]
    with pytest.raises(api.ValidationError, match="replay"):
        api.validate_index(index_for([]), tmp_path, session, [first, second], catalog, replay_originals=[original], **PIN)


@pytest.mark.parametrize("count", [1, 2], ids=["external-replay", "ordered-chain"])
def test_replay_ancestry_accepts_validated_external_and_ordered_prefix(api, catalog, session, replay_history, tmp_path, count):
    original, first, second = replay_history
    episodes = [first, second][:count]
    report = api.validate_index(index_for([]), tmp_path, session, iter(episodes), catalog,
                                replay_originals=iter([original]), **PIN)
    assert report["collection_episode_count"] == count
    assert report["committed_capture_count"] == report["validated_row_count"] == 0
    assert not report["production_eligible"]
    assert all(item["conditions"] == original["conditions"] and item["input_source"] == "test_fixture" for item in episodes)


@pytest.mark.parametrize("case", ["same-session", "current-id-alias", "duplicate-external-id"])
def test_replay_ancestry_external_inventory_is_separate(api, catalog, session, replay_history, tmp_path, case):
    original, first, second = replay_history
    originals = [original]
    if case == "same-session":
        original["session_id"] = session["session_id"]
    elif case == "current-id-alias":
        original["collection_episode_id"] = second["collection_episode_id"]
        first["replay_of"] = original["collection_episode_id"]
    else:
        originals.append(copy.deepcopy(original))
    with pytest.raises(api.ValidationError, match="replay"):
        api.validate_index(index_for([]), tmp_path, session, [first, second], catalog, replay_originals=originals, **PIN)


@pytest.mark.parametrize("scenario", [0, 1, 2])
@pytest.mark.parametrize("at_seconds", [29.999, 30, 30.001], ids=["before", "at", "after"])
@pytest.mark.parametrize("validator", ["episode", "index"])
def test_completed_deadline_agrees_with_lifecycle(api, catalog, session, tmp_path, scenario, at_seconds, validator):
    episode = episode_for(catalog, session, scenario)
    count = len(catalog["scenarios"][scenario]["events"])
    observations = [{"order": n, "observed_at_seconds": n + 1} for n in range(count)]
    observations[-1]["observed_at_seconds"] = at_seconds
    episode.update(state="completed", reason="test_fixture events observed", event_observations=observations)
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    state = api.transition(state, "ready", at_seconds=1)
    result = api.transition(state, "completed", at_seconds=at_seconds, reason=episode["reason"])

    def validate():
        if validator == "episode":
            api.validate_episode(episode, session, catalog)
        else:
            api.validate_index(index_for([]), tmp_path, session, [episode], catalog, **PIN)

    if at_seconds < session["limits"]["episode_timeout_seconds"]:
        assert result.last_outcome == "completed"
        validate()
    else:
        assert result.last_outcome == "timed_out" and result.last_reason == "episode_timeout"
        with pytest.raises(api.ValidationError, match="observation"):
            validate()


def test_completed_deadline_keeps_timeout_observations_and_diagnostics(api, catalog, session, episode, tmp_path):
    state = api.transition(api.new_lifecycle(session), "start", at_seconds=0, collection_episode_id=EID)
    state = api.transition(state, "ready", at_seconds=1)
    timeout = api.transition(state, "check_timeout", at_seconds=30)
    episode.update(state=timeout.last_outcome, reason=timeout.last_reason,
                   event_observations=[{"order": 0, "observed_at_seconds": 30}])
    entry = diagnostic(episode)
    entry.update(stage="execution", observed_at_seconds=30, reason=timeout.last_reason)
    api.validate_episode(episode, session, catalog)
    report = api.validate_index(index_for([entry]), tmp_path, session, [episode], catalog, **PIN)
    assert report["diagnostic_count"] == 1
    assert report["committed_capture_count"] == report["validated_row_count"] == 0
