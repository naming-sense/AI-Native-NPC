"""Active document checks only; no C++ execution, Runtime authority or reset proof.

When the new bridge document is absent, inspect the existing contracts instead.
Thus the initial RED is missing/conflicting policy assertions, never missing-file
or import errors. Mutations below exercise this document oracle in memory.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "docs/current"
BRIDGE = "scenario-host-capture-v1-contract.md"
ADAPTER = "scenario-observation-adapter-v1-contract.md"
DATA = "scenario-collection-v1-data-contract.md"
PLAN = "scenario-collection-v1-implementation-plan.md"
IMPORT = "runtime-capture-import-v1-contract.md"

RUNTIME_PATHS = {
    "Execution/AINativeNPCGoalHostComponent.h",
    "Execution/AINativeNPCGoalHostComponent.cpp",
    "Dataset/DecisionRecordV2.h",
    "Dataset/DecisionRecordV2.cpp",
    "Collection/AINativeNPCCollectionContext.h",
    "Collection/AINativeNPCCollectionContext.cpp",
    "Collection/AINativeNPCCollectionCaptureBridge.h",
    "Collection/AINativeNPCCollectionCaptureBridge.cpp",
    "Collection/AINativeNPCCollectionFileStore.h",
    "Collection/AINativeNPCCollectionFileStore.cpp",
    "Tests/AINativeNPCCollectionHostTests.cpp",
    "Tests/AINativeNPCCollectionCaptureBridgeTests.cpp",
    "Tests/DecisionRecordV2Tests.cpp",
}

# Deliberately scoped clauses: a disclaimer in an unrelated section cannot
# satisfy a failure, authority, publication, or pending-work obligation.
CLAUSES = {
    "status": (
        "활성 구현 계약", "문서 일관성 검사", "Task 2B", "Task 2C",
        "Host 9", "Observation 37", "S01", "whole_task2b_closed=false",
        "Task 3", "Task 4", "Approved=false", "ResolvePolicyReady=false",
        "production_eligible=false", "37", "204", "보조 검사",
    ),
    "observation": (
        "CaptureTargetUniverse", "성공 직후", "KnowledgeBeforePromotion",
        "승격 전", "같은 Goal token", "현재 Pawn pose", "FinalUniverse",
        "exact PrimaryTarget", "Finalize 직전", "stored WorldPosition",
        "DistanceCm", "숨은 actor transform", "Populate=false",
        "Finalize·policy·Request·Capture·Commit", "이전 성공 Snapshot",
        "전체 Draft", "CandidatePair", "reserved/padding/NoTarget",
        "T14", "T30/T31", "G94", "T15/T25", "위치 전용",
    ),
    "failure": (
        "observation_mapping_failed", "bool", "직접 검사한 precondition",
        "deadline", "timed_out", "diagnostic", "terminal evidence",
        "persist", "epoch", "lease", "retry", "verified reset",
        "새 collection_episode_id", "같은 실패 회차", "Task 3",
        "reentrant committed-start", "stack", "입력·예약 사건", "legacy retry",
    ),
    "context": (
        "immutable", "running", "World/Host", "session_id",
        "collection_episode_id", "catalog_sha256", "profile_sha256",
        "runtime_build_evidence_sha256", "observed_geometry_goal_v1",
        "input_source", "controller", "execution_mode", "family", "seeds",
        "Record Build 전", "collection intent", "legacy fallback 금지",
        "trusted issuer/owner", "public bool/digest setter", "Task 3",
        "실제 authority 검증은 미구현", "caller mutation",
    ),
    "metadata": (
        "scenario_capture_<session UUID>_<collection episode UUID>_<process sequence>",
        "20자리", "0이 아닌", "neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1",
        "scenario_collection_utility_unreviewed", "2/Dagger", "모든 생산 phase",
        "runtime_build_evidence_sha256", "ScenarioFamilyId", "MapSeed", "SimulationSeed",
        "0.25", "1.0", "Utility", "resolve_greet_user_play_v1", "human_play",
    ),
    "groups": (
        "LastKnownPosition", "modality_unknown", "현재 typed evidence 분류",
        "관측 prefix", "taxonomy/provenance", "event_observations",
        "captured_at_server_time", "서로 다른 clock", "Teacher", "미래 사건",
        "새 wire field", "현재 validator", "후속 importer", "G76–83", "G84–91",
        "NoTarget", "target_mask", "중복 제거", "enum 숫자 오름차순",
        "빈 값", "기본값 수선 금지", "KnowledgeBeforePromotion",
    ),
    "storage": (
        "exclusive temp creation", "non-replacing publication", "stable-root ancestors",
        "directory", "symlink", "junction", "race", "소유한",
        "final.tmp", "final.pending.tmp", "final.committed.tmp",
        "FILEWRITE_NoReplaceExisting", "CREATE_ALWAYS", "CREATE_NEW",
        "MoveFileW", "지원하지 않는 플랫폼", "실패 번호도 재사용 금지",
        "World 재생성", "MAX_uint64", "Host precheck만으로",
        "multi-file/gameplay atomic rollback", "legacy",
    ),
    "publication": (
        "Capture 1회 + marker 1회", "same immutable images", "expected Record equality",
        "size/SHA-256", "BuildCaptureEnvelopeBytes", "BuildCommittedMarkerBytes",
        "새 parser 금지", "ReadCommittedAndValidateExact", "재개방 금지",
        "producer verified", "collection accepted", "sidecar exact readback",
        "Skill start는 marker보다 앞", "counter rollback 금지", "중복 receipt",
        "completion pin", "publish index last", "Task 3", "Task 4",
    ),
    "diagnostics": (
        "snapshot_present=false", "snapshot_ref=null", "observed_id",
        "메모리 Snapshot", "실제 저장 artifact", "fake Snapshot/hash 금지",
        "Capture/marker 보존", "diagnostic persistence 실패", "session blocked",
        "committed/Dataset 분모", "completion pin 발행 금지",
    ),
    "boundary": (
        "FAINativeNPCCollectionHostTestAccess", "WITH_DEV_AUTOMATION_TESTS",
        "FAINativeNPCGoalHostComponentTestAccess", "ODR", "ShippingGuardTests",
        "동결", "Task 3 GameInstance/runner/UMG", "Task 4 ML", "단일 build owner",
    ),
    "acceptance": (
        "nonzero populated Draft", "late-row failure", "실제 Host callsite",
        "same DecisionId", "World 재생성", "Capture 1회 + marker 1회",
        "sidecar failure after real commit", "counter rollback 금지",
        "예상 Runtime RED", "실행하지 않았다", "Task 3 실제 reset",
        "fake Snapshot/hash 금지", "exact test-name multiset",
    ),
    "commands": (
        "PYTHONPATH", "PYTHONDONTWRITEBYTECODE=1", "no:cacheprovider",
        "--basetemp", "--junitxml", "NeuralGameEditor Win64 Development",
        "-WaitMutex -NoHotReloadFromIDE", "RunNeuralGameTests.ps1",
        "AINativeNPC.Collection.Host", "AINativeNPC.Collection.CaptureBridge",
        "AINativeNPC.Dataset.RecordV2", "Saved/AINativeNPC/Capture/Phase3B",
        "preserved-source inventory", "격리", "고유 log 이름만으로",
        "900", "null exit", "StopTestSession", "clean_or_forced_project_modules",
        "이번 문서 단계에서 실행 금지",
    ),
}


def read(name: str) -> str:
    return (CURRENT / name).read_text(encoding="utf-8")


def section(text: str, key: str, namespace: str = "H") -> str:
    prefix = re.escape(namespace)
    matches = list(re.finditer(
        rf"^<!-- {prefix}:{re.escape(key)} -->(?:\n|\Z)(.*?)(?=^<!-- {prefix}:|\Z)",
        text, re.MULTILINE | re.DOTALL,
    ))
    assert len(matches) == 1, f"Required scope {namespace}:{key}: expected one marker, got {len(matches)}"
    return matches[0].group(1)


def require(text: str, *clauses: str) -> None:
    missing = [clause for clause in clauses if clause not in text]
    assert not missing, f"Missing normative clauses: {missing}"


def table(text: str, header: list[str]) -> list[list[str]]:
    # Strict repository Markdown form: one active, contiguous table. Fenced
    # examples cannot provide its header, delimiter, or any detached body rows.
    active = []
    fence = None
    for index, line in enumerate(text.splitlines()):
        boundary = re.match(r"^(`{3,}|~{3,})", line)
        if boundary:
            if fence is None:
                fence = boundary.group(1)
            elif line.strip() == fence:
                fence = None
            continue
        if fence is None and line.startswith("|"):
            active.append((index, line))
    assert len(active) >= 3, "Required active table header, delimiter and body"
    indices = [index for index, _ in active]
    assert indices == list(range(indices[0], indices[0] + len(active))), "Required one contiguous active table"
    rows = []
    for _, line in active:
        assert line.endswith("|"), "Table row must end with a pipe"
        cells = [cell.strip().replace("`", "") for cell in line[1:-1].split("|")]
        assert len(cells) == len(header), f"Table column count differs: {cells}"
        rows.append(cells)
    assert rows[0] == header, f"Table header differs: expected {header}, got {rows[0]}"
    assert all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]), "Required table delimiter"
    return rows[2:]


@pytest.fixture(scope="module")
def document() -> str:
    path = CURRENT / BRIDGE
    return path.read_text(encoding="utf-8") if path.is_file() else "\n".join(
        read(name) for name in (ADAPTER, DATA, PLAN)
    )


@pytest.mark.parametrize("key", CLAUSES)
def test_scoped_enforcement_clauses(document: str, key: str) -> None:
    require(section(document, key), *CLAUSES[key])


POLICY = [
    ["hard_observation_failure", "failed_before_deadline_else_timed_out", "suppressed", "persist_then_verified_reset", "new_episode_only"],
    ["normal_sensor_absence", "wait_or_timeout", "existing_wait", "existing_lifecycle", "no_hard_failure"],
    ["position_only_or_missing_sentinel", "valid_mapping", "existing_policy", "existing_lifecycle", "no_hard_failure"],
    ["storage_sidecar_diagnostic_failure", "failed_before_deadline_else_timed_out", "suppressed", "session_blocked", "never_in_session"],
    ["reset_failed_or_unverified", "preserve_terminal_outcome", "suppressed", "session_blocked", "never_in_session"],
]


def check_policy(text: str) -> None:
    rows = table(section(text, "policy-table"), ["조건", "terminal outcome", "Decision retry", "다음 회차 장벽", "재개 범위"])
    assert rows == POLICY, "Episode policy/precedence/retry/reset matrix differs"


def test_episode_policy_table(document: str) -> None:
    check_policy(document)


FLOW = [
    "Finalize", "policy selection", "Request", "Record Build",
    "pending write + exact readback", "Commit + final promote + private Skill start",
    "marker publish", "same-image committed readback", "producer verified",
    "bridge context join", "sidecar exclusive publish + exact readback", "collection accepted",
]


def check_order(text: str) -> None:
    rows = table(section(text, "order"), ["순서", "작업", "책임 caller", "실패 경계"])
    assert [row[1] for row in rows] == FLOW, "Producer/Commit/marker/sidecar order differs"
    assert [row[0] for row in rows] == [str(i) for i in range(1, len(FLOW) + 1)]
    assert all(len(row) == 4 and row[2] and row[3] for row in rows), "Owner and failure boundary required"


def test_producer_publication_order(document: str) -> None:
    check_order(document)


GROUPS = [
    ["0", "MapFamily", "l_ai_native_npc_mvp", "episode.map + catalog.map"],
    ["1", "OcclusionLayoutFamily", "mvp_unvalidated_layout_v1", "episode.family.layout_family + catalog.layout_family"],
    ["2", "GoalSequenceFamily", "InvestigateDisturbance:<Phase>", "GoalToken + global_state"],
    ["3", "RoleId", "manny_guard", "exact native Guard + pinned source/build"],
    ["4", "PersonalityClusterId", "default_guard", "compiled default profile + pinned source/build"],
    ["5", "PerceptionModalityFamily", "kind_evidence:<Modalities>", "finalized target_handles + target_mask + KnowledgeBeforePromotion"],
    ["6", "TargetCompositionFamily", "<Kinds>", "finalized target_handles + target_mask"],
    ["7", "EventSequenceFamily", "catalog.event_sequence_family", "episode.family.event_sequence_family + catalog.event_sequence_family"],
]


def check_groups(text: str) -> None:
    rows = table(section(text, "group-table"), ["wire index", "producer field", "exact 값 또는 닫힌 derivation", "원천/대조 oracle"])
    assert rows == GROUPS, "Eight wire groups/source vocabulary differs"


def test_group_wire_positions_and_sources(document: str) -> None:
    check_groups(document)
    imported = section_import_groups(read(IMPORT))
    assert [row[0] for row in imported] == [f"group_dimensions[{i}]" for i in range(8)]


def section_import_groups(text: str) -> list[list[str]]:
    return table(section(text, "groups", "P2"), ["decoder field", "Snapshot field"])


def test_group_closed_derivation_has_reconstructable_oracle(document: str) -> None:
    text = section(document, "group-grammar")
    require(text, "Orient,Navigate,Search,Resolve,Return", "sight,hearing,modality_unknown",
            "Entity,SoundEvent,LastKnownPosition,CoverSlot,SmartObject,Waypoint,WorldPosition",
            "kind_evidence:position_only", "kind_evidence:sight+hearing+modality_unknown",
            "SoundEvent+LastKnownPosition+Waypoint", "canonical ASCII", "empty set -> reject")
    catalog = json.loads((ROOT / "contracts/current/scenario_catalog_v1.json").read_text())
    supported = [row for row in catalog["scenarios"] if row["supported"]]
    for item in supported:
        require(section(document, "groups"), item["event_sequence_family"])
    assert {item["layout_family"] for item in supported} == {"mvp_unvalidated_layout_v1"}
    assert {item["map"] for item in supported} == {"/Game/AINativeNPC/Maps/L_AINativeNPC_MVP"}


def test_future_runtime_allowlist_is_exact_in_contract_and_task2(document: str) -> None:
    for text in (section(document, "runtime-files"), read(PLAN).split("### Task 2:", 1)[1].split("### Task 3:", 1)[0]):
        blocks = re.findall(r"```text\n(.*?)```", text, re.DOTALL)
        paths = {line.strip() for block in blocks for line in block.splitlines() if line.endswith((".h", ".cpp"))}
        assert paths == RUNTIME_PATHS, f"Runtime allowlist delta: {paths ^ RUNTIME_PATHS}"


def test_entrypoints_link_active_contract_and_separate_runtime_substeps() -> None:
    for path in (ROOT / "README.md", CURRENT / ADAPTER, CURRENT / DATA, CURRENT / PLAN):
        require(path.read_text(encoding="utf-8"), BRIDGE)
    require(read(ADAPTER), "순수 adapter 구현·검증 완료")
    # Adapter/data/README status prose is outside this update allowlist.
    # Its old Host-pending text is not a current-state oracle.
    assert "**상태:** Runtime 구현 전 계약." not in read(ADAPTER)
    task = read(PLAN).split("### Task 2:", 1)[1].split("### Task 3:", 1)[0]
    require(task, "활성 계약·문서 하네스", "Host 9", "Observation 37",
            "whole_task2b_closed=false", "scenario-collection-context-v1-implementation-plan.md",
            "2A", "2B", "2C", "2D", "2E", "RED", "GREEN")
    assert "**Runtime 구현 전**" not in task
    require(read(DATA), "Runtime enforcement", "deadline", "verified reset", "session blocked")


def test_schema_catalog_and_importer_contract_remain_frozen() -> None:
    expected = {
        "contracts/current/scenario_collection_v1.schema.json": "d17f3c153735e2876531eed6f627d0cc7b86e3c7d58bc7ca044b1505a2c00a5f",
        "contracts/current/scenario_catalog_v1.json": "71731db30de5663c040ba31c06b589049f3b575cfd630dae3b8c0a2140aa85e0",
        "contracts/current/capture_import_provenance_v1.schema.json": "3a64fa1c6688d83ff2f8d07c436c41f02a1de47c96e1af0cff5d7d6e274ad05c",
    }
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    require(read(IMPORT), "raw `2/Dagger`", "20자리 unsigned decimal")
    schema = json.loads((ROOT / "contracts/current/scenario_collection_v1.schema.json").read_text())
    # Existing closed fields stay owned by the Schema, never by this document.
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_preserved_adapter_sections_and_other_plan_phases() -> None:
    core = read(ADAPTER).split("## 1. 목적과 입력", 1)[1].split("## 7. Host", 1)[0].rstrip() + "\n"
    assert hashlib.sha256(core.encode()).hexdigest() == "f718d2c497a83ed33ec20b04838bb04118d32f3990478b41ffbc73da16c1a020"
    plan = read(PLAN)
    # Status surfaces outside Task 2 may change; unrelated task contracts stay frozen.
    task1 = plan.split("### Task 1:", 1)[1].split("### Task 2:", 1)[0]
    later_tasks = plan.split("### Task 3:", 1)[1].split("## 6.", 1)[0]
    assert hashlib.sha256(task1.encode()).hexdigest() == "f708fbbb62f19c2ad161353c2171dfd6b293fe434977f05b17a9084fa61d7b0e"
    assert hashlib.sha256(later_tasks.encode()).hexdigest() == "71783289de1ac575545f27533d1d6e7de7f0911d7d5b00ee3ccf8a04c67987dc"
    data = read(DATA)
    original = re.sub(r"## Runtime enforcement .*?(?=## Executable boundary)", "", data, flags=re.DOTALL)
    assert hashlib.sha256(original.encode()).hexdigest() == "b206b6ad9c190e8aa39e7b21cf58f765ee99d03a7aec620f392316b6d6e1f42f"


def test_import_group_and_namespace_rules_are_byte_preserved() -> None:
    text = read(IMPORT)
    groups = text.split("<!-- P2:groups -->", 1)[1].split("<!-- P2:tensors -->", 1)[0]
    metadata = text.split("<!-- P2:contract-metadata -->", 1)[1].split("<!-- P3:policy-lineage -->", 1)[0]
    assert hashlib.sha256((groups + metadata).encode()).hexdigest() == "00afcdd76fb77be768a5d3ab19ad6946b5541ceb7ff57f2beeadcf8520da2aa7"


def test_group_kinds_and_phases_are_generated_identifiers(document: str) -> None:
    tree = ast.parse((ROOT / "generated/python/ai_native_npc_contracts_generated.py").read_text())
    enums = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in {"TargetKind", "GoalPhase"}:
            enums[node.name] = {
                assignment.targets[0].id: ast.literal_eval(assignment.value)
                for assignment in node.body
                if isinstance(assignment, ast.Assign) and isinstance(assignment.targets[0], ast.Name)
            }
    ordered_kinds = sorted(enums["TargetKind"], key=enums["TargetKind"].get)
    assert ordered_kinds.pop(0) == "NoTarget"
    require(section(document, "group-grammar"), ",".join(ordered_kinds))
    for phase in ("Orient", "Navigate", "Search", "Resolve", "Return"):
        assert phase in enums["GoalPhase"]
    # Static vocabulary consistency, not a replacement producer/importer.
    assert enums["GoalPhase"]["Resolve"] == 6


def check_current_host_primary_sources(text: str) -> None:
    registry = yaml.safe_load((ROOT / "contracts/current/goal_registry_v1.yaml").read_text(encoding="utf-8"))
    semantics = registry["goal_gameplay_semantics_v1"]
    authorities = {row["id"]: row for row in semantics["target_authorities"]}
    policies = [row for row in semantics["phase_target_policies"] if row["goal"] == "InvestigateDisturbance"]
    assert policies and len({row["phase"] for row in policies}) == len(policies)
    phases_by_authority = {}
    for policy in policies:
        authority = authorities[policy["target_authority"]]
        assert policy["policy"] == "ActiveGoalPrimaryTargetOnly"
        assert policy["required_target_kind"] == authority["target_kind"]
        assert authority["candidate_usable"] is True and authority["provenance_only"] is False
        phases_by_authority.setdefault(authority["id"], []).append(policy["phase"])

    # Resolve's authority is Goal-owned too: Knowledge storage, not ownership
    # alone, distinguishes its primary from the current synthetic producers.
    synthetic = [authorities[key] for key in phases_by_authority
                 if authorities[key]["owner"] == "GameplayGoalAuthority"
                 and authorities[key]["stored_in_knowledge"] is False]
    knowledge = [authorities[key] for key in phases_by_authority
                 if authorities[key]["stored_in_knowledge"] is True]
    assert synthetic and knowledge
    assert len(synthetic) + len(knowledge) == len(phases_by_authority)
    expected_kinds = {row["target_kind"] for row in synthetic}
    groups = section(text, "groups")
    claims = re.findall(r"현재 Host가 synthetic으로 만드는 primary는 ([A-Za-z]+(?:/[A-Za-z]+)*)이며", groups)
    assert len(claims) == 1, "Expected one current Host synthetic-primary source claim"
    declared = claims[0].split("/")
    assert len(declared) == len(set(declared)) and set(declared) == expected_kinds, (
        f"Current Host synthetic primary kinds: document={declared}, Registry={sorted(expected_kinds)}"
    )

    def phase_claim(authority: dict) -> str:
        phases = "/".join(phases_by_authority[authority["id"]])
        return f"`{phases} → {authority['id']}({authority['target_kind']})`"

    owners = {row["owner"] for row in synthetic}
    assert len(owners) == 1
    require(groups, ", ".join(phase_claim(row) for row in synthetic)
            + f"는 `{next(iter(owners))}` 소유이며 `stored_in_knowledge=false`다.")
    for authority in knowledge:
        require(groups, phase_claim(authority)
                + f"는 `{authority['owner']}` 소유이며 `stored_in_knowledge=true`인 Knowledge-backed primary다.")
    require(groups, "순수 adapter가 허용하는 일반 입력으로는 Goal-owned LastKnownPosition도 가능하다",
            "현재 Host 생산 목록과 구분한다", "**modality_unknown**")
    require(section(text, "group-grammar"), "LastKnownPosition이 있으면 `modality_unknown`")


def test_current_host_primary_sources_match_registry(document: str) -> None:
    check_current_host_primary_sources(document)


@pytest.mark.parametrize("wrong_kind", ["LastKnownPosition", "Entity", "SoundEvent"])
def test_current_host_primary_sources_reject_wrong_kind(document: str, wrong_kind: str) -> None:
    check_current_host_primary_sources(document)
    mutated, count = re.subn(
        r"(현재 Host가 synthetic으로 만드는 primary는 )[A-Za-z]+(/)",
        rf"\g<1>{wrong_kind}\g<2>", document,
    )
    assert count == 1 and mutated != document
    with pytest.raises(AssertionError, match="document=.*Registry="):
        check_current_host_primary_sources(mutated)


@pytest.mark.parametrize("old,new", [
    ("Orient/Navigate/Search →", "Orient/Navigate →"),
    ("`GameplayGoalAuthority` 소유이며", "`Knowledge` 소유이며"),
    ("`stored_in_knowledge=false`다.", "`stored_in_knowledge=true`다."),
    ("순수 adapter가 허용하는 일반 입력", "현재 Host가 생산하는 입력"),
    ("LastKnownPosition이 있으면 `modality_unknown`", "LastKnownPosition이 있으면 `hearing`"),
])
def test_current_host_primary_sources_reject_attribution_regression(document: str, old: str, new: str) -> None:
    check_current_host_primary_sources(document)
    mutated = document.replace(old, new)
    assert mutated != document
    with pytest.raises(AssertionError, match="Missing normative clauses"):
        check_current_host_primary_sources(mutated)


@pytest.mark.parametrize("case", [
    "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10",
    "C01", "C02", "C03", "C04", "C05", "C06", "C07",
    "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09",
    "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18",
    "R01", "R02", "R03",
])
def test_expected_runtime_red_matrix_names_concrete_oracles(document: str, case: str) -> None:
    rows = table(section(document, "matrix"), ["ID", "입력·hostile 조건", "반드시 볼 oracle", "현 상태·소유자"])
    matching = [row for row in rows if row[0] == case]
    assert len(matching) == 1, f"Missing/duplicated future Runtime case {case}"
    assert len(matching[0]) == 4 and all(len(cell) > 12 for cell in matching[0][1:]), case


@pytest.mark.parametrize("key", CLAUSES)
def test_negative_mutation_removes_scoped_obligation(document: str, key: str) -> None:
    text = section(document, key)
    require(text, *CLAUSES[key])  # genuine positive control before mutation
    missing = CLAUSES[key][-1]
    mutated = text.replace(missing, "REMOVED_OBLIGATION")
    assert mutated != text
    with pytest.raises(AssertionError, match="Missing normative clauses"):
        require(mutated, *CLAUSES[key])


@pytest.mark.parametrize("old,new", [
    ("persist_then_verified_reset", "retry_same_episode"),
    ("failed_before_deadline_else_timed_out", "always_failed"),
    ("session_blocked", "next_episode_allowed"),
    ("suppressed", "retry_enabled"),
])
def test_negative_mutation_rejects_policy_regression(document: str, old: str, new: str) -> None:
    check_policy(document)
    with pytest.raises(AssertionError, match="policy"):
        check_policy(document.replace(old, new))


def test_negative_mutation_rejects_publication_reordering(document: str) -> None:
    check_order(document)
    text = document.replace("Commit + final promote + private Skill start", "SWAP_STEP")
    text = text.replace("marker publish", "Commit + final promote + private Skill start")
    text = text.replace("SWAP_STEP", "marker publish")
    with pytest.raises(AssertionError, match="order"):
        check_order(text)


@pytest.mark.parametrize("old,new", [
    ("l_ai_native_npc_mvp", "l_ai_native_npc_mvp_user_play_v1"),
    ("mvp_unvalidated_layout_v1", "surface_fixture_open_v1"),
    ("InvestigateDisturbance:<Phase>", "orient_navigate_search_return"),
    ("catalog.event_sequence_family", "invented_observed_prefix"),
])
def test_negative_mutation_rejects_group_fabrication(document: str, old: str, new: str) -> None:
    check_groups(document)
    with pytest.raises(AssertionError, match="groups"):
        check_groups(document.replace(old, new))


# Structural controls exercise the complete document, before section/table
# extraction, so unrelated history and examples cannot supply active rules.
@pytest.mark.parametrize("key", [*CLAUSES, "policy-table", "order", "group-table",
                                 "group-grammar", "runtime-files", "matrix"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_required_scope_marker_is_unique(document: str, key: str, mutation: str) -> None:
    marker = f"<!-- H:{key} -->"
    assert document.count(marker) == 1
    assert section(document, key).strip()  # exact-current positive control
    mutated = document.replace(marker + "\n", "", 1) if mutation == "missing" else (
        document + "\n" + marker + "\nContradictory replacement rules.\n"
    )
    assert mutated != document
    with pytest.raises(AssertionError):
        section(mutated, key)


@pytest.mark.parametrize("keep_marker", [False, True], ids=["relocated-section", "intact-marker-token"])
def test_failure_history_cannot_supply_active_obligation(document: str, keep_marker: bool) -> None:
    active = section(document, "failure")
    require(active, *CLAUSES["failure"])
    if keep_marker:
        assert "legacy retry" in active
        replacement = active.replace("legacy retry", "legacy scheduling")
        mutated = document.replace(active, replacement, 1)
    else:
        block = "<!-- H:failure -->\n" + active
        assert document.count(block) == 1
        mutated = document.replace(block, "", 1)
    mutated += "\n<!-- H:historical-example -->\n## Archived example — not active requirements\n" + active
    assert mutated != document
    with pytest.raises(AssertionError):
        require(section(mutated, "failure"), *CLAUSES["failure"])


def test_pre_document_fixture_fallback_remains_assertion_red(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(globals(), "BRIDGE", "missing-host-contract-red-fixture.md")
    assert not (CURRENT / BRIDGE).exists()
    fallback = document.__wrapped__()
    assert fallback == "\n".join(read(name) for name in (ADAPTER, DATA, PLAN))
    with pytest.raises(AssertionError):
        require(section(fallback, "failure"), *CLAUSES["failure"])


@pytest.mark.parametrize("name,header,check", [
    ("policy", "| 조건 | terminal outcome | Decision retry | 다음 회차 장벽 | 재개 범위 |", check_policy),
    ("order", "| 순서 | 작업 | 책임 caller | 실패 경계 |", check_order),
    ("groups", "| wire index | producer field | exact 값 또는 닫힌 derivation | 원천/대조 oracle |", check_groups),
    ("matrix", "| ID | 입력·hostile 조건 | 반드시 볼 oracle | 현 상태·소유자 |",
     lambda text: test_expected_runtime_red_matrix_names_concrete_oracles(text, "H01")),
    ("import", "| decoder field | Snapshot field |", section_import_groups),
], ids=["policy", "order", "groups", "matrix", "import"])
@pytest.mark.parametrize("mutation", [
    "header-swapped", "no-separator", "split-before-body", "split-body",
    "fenced-only", "tilde-fenced-only", "short-row", "extra-column", "detached-body",
])
def test_named_table_structure_is_required(document: str, name: str, header: str, check, mutation: str) -> None:
    text = read(IMPORT) if name == "import" else document
    check(text)  # every hostile input starts from a passing current consumer
    lines = text.splitlines(keepends=True)
    assert lines.count(header + "\n") == 1
    start = next(i for i, line in enumerate(lines) if line.rstrip("\n") == header)
    stop = start
    while stop < len(lines) and lines[stop].startswith("|"):
        stop += 1
    block = lines[start:stop]
    assert len(block) >= 4 and set(block[1].strip()) <= set("|-: ")
    changed = block.copy()
    if mutation == "header-swapped":
        cells = header.split("|")
        cells[1], cells[2] = cells[2], cells[1]
        changed[0] = "|".join(cells) + "\n"
    elif mutation == "no-separator":
        del changed[1]
    elif mutation == "split-before-body":
        changed.insert(2, "\n")
    elif mutation == "split-body":
        changed.insert(3, "\nInterrupted normative table.\n\n")
    elif mutation in {"fenced-only", "tilde-fenced-only"}:
        fence = "```" if mutation == "fenced-only" else "~~~"
        changed = [fence + "text\n", *changed, fence + "\n"]
    elif mutation == "short-row":
        # The import consumer used to validate only wire positions; drop the
        # final body cell without triggering an unrelated row-index exception.
        changed[-1] = "|".join(changed[-1].rstrip("\n").split("|")[:-2]) + "|\n"
    elif mutation == "extra-column":
        changed[-1] = changed[-1].rstrip("\n") + " extra |\n"
    else:
        assert mutation == "detached-body"
        changed = ["```text\n", *changed[:2], "```\n", *changed[2:]]
    mutated = "".join([*lines[:start], *changed, *lines[stop:]])
    assert mutated != text
    with pytest.raises(AssertionError):
        check(mutated)
