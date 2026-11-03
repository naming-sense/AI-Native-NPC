"""일반 플레이 세션/index 구현 기준의 문서 하네스.

이 파일은 Runtime 구현·사람 플레이·학습 승인을 증명하지 않는다.
작성자는 실행하지 않는다. 부모가 단일 실행 소유자로 실행 결과를 남긴다.
before-plan 모드는 기존 문서를 읽어 missing-contract assertion으로 RED를 만든다.
변조 검사는 메모리 문자열만 변경한다. 기존 문서·Schema·catalog를 쓰지 않는다.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "docs/current"
PLAN = CURRENT / "scenario-collection-play-session-index-v1-implementation-plan.md"
SCOPES = (
    "scope", "files", "entry", "inputs", "lifecycle", "drain", "persist",
    "index", "budget", "provenance", "matrix", "execution",
)
RULES = {
    "scope": {
        "PS01": "이번 범위는 일반 플레이의 수동 수집 start/stop/new episode, 실제 GameInstance 소유 수명, 최종 index 저장이다. 독립 검토는 사용자 요청으로 생략한다.",
        "PS02": "Approved=false; ResolvePolicyReady=false; production_eligible=false를 유지한다. 일반 플레이 수집 활성화 허용은 학습·Resolve policy·ML import 승인이 아니다.",
        "PS03": "문서 작성자는 신규 문서·신규 문서 하네스·지정 design-handoff만 작성한다. 기존 문서·tests·C++는 읽기 전용이며 Unreal/build/terminal/execute_code/commit/push/skill 변경은 수행하지 않는다.",
    },
    "files": {
        "PS04": "부모 구현은 아래 exact allowlist만 사용한다. Config·Content·PlayerController·Build.cs·Schema·catalog·generated·Builder·serializer·ObservationAdapter·Coordinator·ML과 기존 tests는 보존한다.",
    },
    "entry": {
        "PS05": "UAINativeNPCCollectionSessionSubsystem은 새 UGameInstanceSubsystem owner다. 실제 nondev console WithWorld 진입이 typed closed parameters로 owner를 호출하며 dev wrapper를 production 진입으로 사용하지 않는다.",
        "PS06": "기본 수집은 꺼져 있다. start는 MVP Game/PIE World·authority·exact native Guard/Host·단일 local Player.Main·실제 controller provenance·owned runtime inputs를 모두 검사한다. 잘못된 map은 거부하며 기본 ThirdPerson Config를 바꾸지 않는다.",
        "PS07": "collection intent의 preparing/missing context/stale lease는 legacy fallback을 금지한다. intent 없는 일반 플레이의 입력·Goal·Capture·ResolveShadow 동작은 보존한다.",
    },
    "inputs": {
        "PS08": "context/lease/session 생성과 Host attach는 owner-private runtime 경로다. public bool/digest/fixtureResetReceipt와 TryAttachOwnedCollectionForTest 또는 TryBindCollectionStorageForTest 호출로 실제 허가를 만들지 않는다.",
        "PS09": "catalog/profile/schema/build는 실제 파일 bytes와 독립 launcher 관측을 검증해 owned 값으로 고정한다. FApp::GetBuildVersion 문자열 hash·임의 hex·caller expected 값은 실제 runtime build identity를 대체하지 않는다.",
    },
    "lifecycle": {
        "PS10": "session_id와 collection_episode_id는 재사용 없는 lowercase UUIDv4다. Capture episode_id와 process-wide nonzero sequence는 별개이며 World reset·session 종료로 재설정하지 않는다.",
        "PS11": "첫 회차는 현재 World/Host/Player의 pristine 준비 관측을 요구한다. 다음 회차는 이전 terminal persist/readback·실제 drain·이전 World cleanup·다른 World identity·새 assembly 준비·reset 결과 persist/readback 뒤에만 fresh ID로 attach한다.",
        "PS12": "동시 회차는 하나다. preparation 포함 monotonic deadline을 사용하며 at/after deadline은 timed_out 우선이다. completed는 실제 사건 전체 prefix가 deadline 전에 관측됐을 때만 허용한다.",
    },
    "drain": {
        "PS13": "stop/cancel/error는 callback·I/O 전에 terminal latch·retry epoch·lease를 닫는다. committed-start/receipt stack 안에서는 World·authority를 파괴하거나 새 회차를 붙이지 않는다.",
        "PS14": "owner는 입력·emitter·예약 사건·retry·GoalTimer·Executor timer/move·StateTree를 실제 정지하고 attempt depth와 Executor result/external-effect dispatch가 0인 관측을 확인한다. fixture drain bool이나 EndPlay 플래그 초기화는 증거가 아니다.",
    },
    "persist": {
        "PS15": "session descriptor·episode terminal·reset 결과·session terminal journal은 immutable 별도 파일로 exclusive publish와 exact readback을 수행한다. session/episode Schema에 terminal-history 필드를 끼워 넣지 않는다.",
        "PS16": "storage/sidecar/diagnostic/terminal/index 저장 실패와 reset failed/unverified는 sticky session block이다. 원본 Capture/marker·수락 ledger·잔여 bytes를 보존하며 같은 세션 재개와 성공 index를 차단한다.",
    },
    "index": {
        "PS17": "최종 index의 필드는 format/version/session_id/entries뿐이다. entries는 readback된 accepted/diagnostic canonical entry 본문이며 descriptor 목록·counts·approval·session/episode 객체를 추가하지 않는다.",
        "PS18": "정지·drain·terminal 저장 뒤 ledger를 동결한다. accepted entries 다음 diagnostic entries의 기존 순서를 보존하고 각 마지막 LF만 제거해 합친 canonical UTF-8 index를 session당 한 번 nonreplace publish/readback한다.",
        "PS19": "index 발행은 lease revoke 뒤에도 유효한 owner-private one-shot purpose 권한을 사용한다. sidecar current-lease 검사를 풀거나 public arbitrary-path writer를 만들지 않으며 중복 stop은 기존 결과만 반환한다.",
    },
    "budget": {
        "PS20": "누적 budget은 Capture/marker/entry/diagnostic/index/session/episode/reset/journal/metadata와 in-flight overhead를 포함한다. checked arithmetic·쓰기 전 예약·실제 정산을 사용하며 World 교체·root/limit 변경으로 소비량을 지우지 않는다.",
        "PS21": "mIndexBytes의 기존 예약은 최종 본문으로 한 번 전환한다. 빈 ledger도 wrapper를 예약하고 최종 bytes와 일치시킨다. 실패 final/residual 예약은 남기며 보존 자료 삭제로 예산을 확보하지 않는다.",
    },
    "provenance": {
        "PS22": "자동검사는 automated_runtime/automatic/automated 또는 격리 test_fixture로 기록한다. public manual start의 자동 호출은 human 허가를 만들지 않는다. 사람 플레이 확인은 사용자 실제 입력과 피드백으로만 완료한다.",
        "PS23": "index readback 성공은 구조·저장 완료다. completion pin/ML importer/Teacher/Human label/Resolve readiness/Shipping/UI/자동 시나리오 연출/commit/push는 이번 범위 밖이다.",
    },
    "matrix": {
        "PS24": "각 실패 검사는 정상 control과 실제 경계 도달을 함께 기록한다. 컴파일 실패·0 discovery·timeout·문서 mutation은 Unreal 행동 RED나 사람 플레이 증거가 아니다.",
    },
    "execution": {
        "PS25": "실행은 부모 한 명이 직렬 소유한다. 문서 하네스·C++·build·Automation·실파일 검증을 구분하며 독립 검토·재검토를 추가하지 않는다. 현재 문서 작성 상태는 source_editing_complete=true, actual_execution=false다.",
    },
}
SOURCE_FILES = [
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionSessionSubsystem.h", "신규", "GameInstance owner·typed 공개 요청"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionSessionSubsystem.cpp", "신규", "nondev console·수명·reset·최종 저장"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionRuntimeInputs.h", "신규", "owned validated inputs·private issuer"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionRuntimeInputs.cpp", "신규", "strict metadata·실제 build/start binding"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionContext.h", "수정", "runtime-private 생성·session ledger 재사용"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionContext.cpp", "수정", "공통 검증·runtime namespace·lease 발급"),
    ("Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGoalHostComponent.h", "수정", "owner-only attach/stop/관측 경계"),
    ("Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGoalHostComponent.cpp", "수정", "실제 assembly rendezvous·stop·ledger 연결"),
    ("Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSkillExecutorComponent.h", "수정", "collection-only stop/drain 관측"),
    ("Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSkillExecutorComponent.cpp", "수정", "실제 timer/move/dispatch 정지 확인"),
    ("Source/NeuralGame/AINativeNPC/Player/PlayerNoiseEmitterComponent.cpp", "수정", "collection preparing/stop 때 발소리 발행 차단"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionCaptureBridge.h", "수정", "typed session/episode/index encoding"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionCaptureBridge.cpp", "수정", "canonical JSON·ledger index·budget 경계"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionFileStore.h", "수정", "owner-private purpose publication 요청"),
    ("Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionFileStore.cpp", "수정", "닫힌 path grammar·nonreplace/readback"),
    ("Source/NeuralGame/AINativeNPC/Tests/AINativeNPCCollectionPlaySessionTests.cpp", "신규", "AINativeNPC.Collection.Host.PlaySession.*"),
]
COMMANDS = [
    ("anpc.Collection.Start", "인수 없음 또는 scenario distance angle seed", "닫힌 값 파싱 후 RequestStartManual"),
    ("anpc.Collection.NewEpisode", "인수 없음", "현재 조건 유지·새 ID·실제 fresh World barrier"),
    ("anpc.Collection.Stop", "인수 없음", "cancel 또는 기존 terminal 유지·drain·최종 index"),
]
DEFAULTS = [
    ("enabled", "false"), ("scenario_id", "hearing_only"),
    ("distance_cm", "400"), ("approach_angle_deg", "0"), ("seed", "0"),
    ("max_episodes", "2"), ("episode_timeout_seconds", "30"),
    ("preparation_timeout_seconds", "10"), ("max_decisions", "100"),
    ("storage_limit_bytes", "67108864"), ("split", "unassigned"),
]
PATHS = [
    ("Session", "sessions/<session UUID>/session.json", "scenario_collection_session_v1"),
    ("EpisodePreparing", "episodes/<session UUID>/<episode UUID>/preparing.json", "scenario_collection_episode_v1"),
    ("EpisodeTerminal", "episodes/<session UUID>/<episode UUID>/terminal.json", "scenario_collection_episode_v1"),
    ("EpisodeReset", "episodes/<session UUID>/<episode UUID>/reset.json", "scenario_collection_episode_v1"),
    ("SessionTerminal", "sessions/<session UUID>/terminal.json", "anpc_collection_session_terminal_v1"),
    ("Index", "indexes/<session UUID>/index.json", "scenario_collection_index_v1"),
    ("Metadata", "metadata/<session UUID>/<closed name>.json", "검증한 원본 metadata bytes"),
]
MATRIX = [
    ("S01", "start", "정상 MVP/단일 local/assembly", "nondev owner·첫 lease·session readback"),
    ("S02", "start", "ThirdPerson/wrong World/no authority/복수 player", "attach와 Capture 0·일반 플레이 보존"),
    ("S03", "inputs", "malformed catalog/profile/build·동일 forged digest", "실제 검증 실패·fixture 승격 0"),
    ("S04", "provenance", "자동 runner의 manual start", "human 오분류 0·automation 출처 유지"),
    ("S05", "id", "중복 session/episode·sequence/epoch overflow", "재사용 0·기존 bytes 보존"),
    ("S06", "lifecycle", "동시 start/new·기한 경계·관측 prefix 부족", "단일 회차·timeout 우선·completed 거부"),
    ("S07", "stop", "committed-start/result callback 중 stop", "revoke 선행·stack 내 teardown 0"),
    ("S08", "drain", "입력 held·emitter·timer·move·dispatch 진행", "실제 정지/0 관측 전 reset 금지"),
    ("S09", "reset", "old cleanup 누락·동일 World·재사용 Host·late callback", "fresh barrier 거부·새 회차 불변"),
    ("S10", "persist", "terminal/reset/session write/readback 실패", "sticky block·원본 보존·index 성공 0"),
    ("S11", "index", "accepted+diagnostic·빈 ledger", "strict fields·canonical bytes·실파일 재검증"),
    ("S12", "index", "final/temp 충돌·alias·race·readback 변조", "nonreplace·실패 bytes 보존·재발행 0"),
    ("S13", "budget", "wrapper/metadata/terminal/residual·overflow", "누적 선예약·이중 청구 0·초과 write 0"),
    ("S14", "cancel", "중복 stop·cancel 뒤 new·GameInstance 종료", "일회 index·drain·오류 상태 보존"),
    ("S15", "normalgame", "수집 off·Resolve capture-only", "legacy 동작·세 승인 false 유지"),
    ("S16", "nondev", "macro-off compile/preprocess와 실제 entry", "prod 경로 존재·test helper 의존 0"),
    ("S17", "realfile", "session/episodes/index·Capture/marker 재읽기", "validate_index·validated_row_count=0·production_eligible=false"),
]
TABLES = (
    ("files", ("파일", "작업", "허용 변경"), SOURCE_FILES),
    ("entry", ("명령", "인수", "효과"), COMMANDS),
    ("entry", ("항목", "고정 기본값"), DEFAULTS),
    ("persist", ("purpose", "상대 경로", "payload"), PATHS),
    ("matrix", ("ID", "경계", "입력·실패", "필수 oracle"), MATRIX),
)


def active(text: str) -> str:
    """Offset를 보존하면서 fence와 일반 comment를 지운다."""
    result = []
    fence = None
    for line in text.splitlines(keepends=True):
        boundary = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence is None and boundary:
            fence = boundary.group(1)
            result.append(re.sub(r"[^\r\n]", " ", line))
        elif fence is not None:
            if boundary and boundary.group(1)[0] == fence[0] and len(boundary.group(1)) >= len(fence) and not boundary.group(2).strip():
                fence = None
            result.append(re.sub(r"[^\r\n]", " ", line))
        else:
            result.append(line)
    assert fence is None, "Unclosed plan fence"
    return re.sub(
        r"<!--(?! PS:[a-z-]+ -->).*?-->",
        lambda match: re.sub(r"[^\r\n]", " ", match.group()),
        "".join(result), flags=re.DOTALL,
    )


def sections(text: str) -> dict[str, str]:
    visible = active(text)
    markers = list(re.finditer(r"^<!-- PS:([a-z-]+) -->$", visible, re.MULTILINE))
    assert tuple(match.group(1) for match in markers) == SCOPES, "Missing/duplicate/out-of-order active play-session clauses"
    return {
        match.group(1): visible[match.end():markers[index + 1].start() if index + 1 < len(markers) else len(visible)]
        for index, match in enumerate(markers)
    }


def table(text: str, header: tuple[str, ...]) -> list[tuple[str, ...]]:
    lines = text.splitlines()
    header_line = "| " + " | ".join(header) + " |"
    assert lines.count(header_line) == 1, f"Missing/duplicate table: {header}"
    start = lines.index(header_line)
    assert start + 1 < len(lines) and re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", lines[start + 1]), "Invalid table separator"
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        assert line.endswith("|"), "Unclosed table row"
        row = tuple(value.strip() for value in line[1:-1].split("|"))
        assert len(row) == len(header), "Table column count differs"
        rows.append(row)
    return rows


def check_document(text: str) -> None:
    parts = sections(text)
    for scope, rules in RULES.items():
        found = [line for line in parts[scope].splitlines() if re.match(r"^- \*\*PS\d+\*\*:", line)]
        assert found == [f"- **{key}**: {value}" for key, value in rules.items()], f"Normative clause differs: {scope}"
    for scope, header, expected in TABLES:
        assert table(parts[scope], header) == expected, f"Exact table differs: {scope}/{header}"
    required = {
        "scope": ("publication-runtime-implementation-01/implementation-result-01.md", "역사적", "문서 하네스 미실행"),
        "files": ("design-handoff-01.md", "design-handoff-01.json", "읽기 전용", "실행 소유자"),
        "entry": ("FAutoConsoleCommandWithWorldAndArgs", "RequestStartManual", "RequestNewEpisode", "RequestStop", "새로 제안", "hearing_appearance_loss", "relationship_friendly"),
        "inputs": ("Saved/AINativeNPC/CollectionRuntime", "catalog package availability", "runtime-build-evidence.json", "session-start-evidence.json", "clean_or_forced_project_modules", "loaded_module_inventory", "source_inventory_before", "source_inventory_after", "independent_out_of_band", "host_transient_fixture_v1"),
        "lifecycle": ("HasBegunPlay", "OnPostWorldCleanup", "UGameplayStatics::OpenLevel", "mUsedEpisodeIds", "pristine", "placement", "replay_of"),
        "drain": ("bResultDispatchInProgress", "bExternalEffectInProgress", "mCommittedGreetStartInProgress", "FlushPressedKeys", "StopMovementImmediately", "OnWorldTickEnd", "UninstallResultSinkForAuthority", "mAttemptDepth"),
        "persist": ("session_terminal", "ordered_episodes", "reset_result", "not_attempted", "PublishJsonExact", "IsCanonicalJsonRelativePath", "CREATE_NEW", "MoveFileW"),
        "index": ("mAcceptedEntries", "mDiagnosticEntries", "mIndexEntryCount", "sorted_json_bytes", "validate_index", "actual exact readback", "frozen", "one-shot"),
        "budget": ("mBudgetBytes", "mIndexBytes", "checked", "reservation", "empty index", "owner thread"),
        "provenance": ("사용자 피드백", "GIsAutomationTesting", "test_fixture", "검증 범위"),
        "execution": ("ANPC_PLAY_SESSION_DOCUMENT_MODE=before-plan", "PYTHONDONTWRITEBYTECODE=1", "-B -m pytest", "no:cacheprovider", "--basetemp", "--junitxml", "RunNeuralGameTests.ps1", "AINativeNPC.Collection.Host.PlaySession", "macro-off", "source_editing_complete=true", "actual_execution=false"),
    }
    for scope, values in required.items():
        for value in values:
            assert value in parts[scope], f"Missing scoped detail: {scope}/{value}"


def load_document(mode: str = "active") -> str:
    assert mode in {"active", "before-plan"}, "Unknown play-session document mode"
    if mode == "before-plan" or not PLAN.is_file():
        return (CURRENT / "scenario-collection-v1-implementation-plan.md").read_text(encoding="utf-8")
    return PLAN.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def document() -> str:
    return load_document(os.environ.get("ANPC_PLAY_SESSION_DOCUMENT_MODE", "active"))


def test_active_play_session_index_document(document: str) -> None:
    check_document(document)


def test_before_plan_is_contract_assertion_not_missing_file() -> None:
    with pytest.raises(AssertionError, match="active play-session clauses"):
        check_document(load_document("before-plan"))


def test_schema_index_and_lifecycle_fields_stay_closed() -> None:
    defs = json.loads((ROOT / "contracts/current/scenario_collection_v1.schema.json").read_text(encoding="utf-8"))["$defs"]
    for kind in ("session", "episode", "index", "committedEntry", "diagnostic"):
        assert defs[kind]["additionalProperties"] is False
    assert set(defs["index"]["required"]) == set(defs["index"]["properties"]) == {"format", "version", "session_id", "entries"}
    assert defs["index"]["properties"]["entries"]["items"] == {"$ref": "#/$defs/entry"}
    assert "state" not in defs["session"]["properties"]
    assert set(defs["episode"]["properties"]["reset_result"]["enum"]) == {"not_attempted", "verified", "failed", "unverified"}
    for kind in ("session", "episode", "index", "committedEntry", "diagnostic"):
        assert not ({"Approved", "ResolvePolicyReady", "production_eligible", "counts"} & set(defs[kind]["properties"]))


def test_defaults_and_scenario_selection_match_actual_catalog() -> None:
    catalog = json.loads((ROOT / "contracts/current/scenario_catalog_v1.json").read_text(encoding="utf-8"))
    scenarios = {item["id"]: item for item in catalog["scenarios"]}
    assert {key for key, value in scenarios.items() if value["supported"]} == {"hearing_only", "hearing_appearance", "hearing_appearance_loss"}
    assert {key for key, value in scenarios.items() if not value["supported"]} == {"relationship_friendly", "relationship_hostile", "low_identity", "unreachable_greet"}
    defaults = dict(DEFAULTS)
    selected = scenarios[defaults["scenario_id"]]
    for key in ("distance_cm", "approach_angle_deg", "seed"):
        assert int(defaults[key]) in selected["variations"][key]
    assert int(defaults["episode_timeout_seconds"]) == selected["termination"]["max_duration_seconds"]
    assert int(defaults["preparation_timeout_seconds"]) == selected["termination"]["preparation_timeout_seconds"]
    assert int(defaults["max_decisions"]) == selected["termination"]["max_decisions"]
    assert defaults["enabled"] == "false" and defaults["split"] == "unassigned"
    assert catalog["support_semantics"] == "code_supported_pending_runtime_validation"
    assert all(item["map"] == "/Game/AINativeNPC/Maps/L_AINativeNPC_MVP" for item in scenarios.values())


RULE_CASES = [(scope, key, value) for scope, rules in RULES.items() for key, value in rules.items()]


@pytest.mark.parametrize("scope,key,value", RULE_CASES, ids=[case[1] for case in RULE_CASES])
@pytest.mark.parametrize("mutation", ["delete", "weaken", "fence", "comment", "relocate"])
def test_hostile_rule_mutation(document: str, scope: str, key: str, value: str, mutation: str) -> None:
    check_document(document)
    line = f"- **{key}**: {value}"
    assert document.splitlines().count(line) == 1
    replacement = {"delete": "", "weaken": line + " 선택 사항이다.", "fence": f"```text\n{line}\n```", "comment": f"<!-- {line} -->", "relocate": ""}[mutation]
    changed = document.replace(line, replacement, 1)
    if mutation == "relocate":
        target = "files" if scope != "files" else "entry"
        marker = f"<!-- PS:{target} -->"
        changed = changed.replace(marker, marker + "\n" + line, 1)
    assert changed != document
    with pytest.raises(AssertionError, match="Normative clause differs"):
        check_document(changed)


@pytest.mark.parametrize("old,new", [
    ("Approved=false; ResolvePolicyReady=false; production_eligible=false", "Approved=true; ResolvePolicyReady=true; production_eligible=true"),
    ("독립 검토는 사용자 요청으로 생략한다.", "독립 검토를 필수로 추가한다."),
    ("실행은 부모 한 명이 직렬 소유한다.", "작업자가 병렬로 build를 실행한다."),
    ("source_editing_complete=true, actual_execution=false", "source_editing_complete=true, actual_execution=true"),
    ("public manual start의 자동 호출은 human 허가를 만들지 않는다.", "public manual start의 자동 호출은 human 허가를 만든다."),
    ("format/version/session_id/entries뿐이다.", "format/version/session_id/entries/counts/approval이다."),
    ("nonreplace publish/readback한다.", "replace publish만 수행한다."),
])
def test_specific_false_approval_and_scope_regressions(document: str, old: str, new: str) -> None:
    check_document(document)
    assert old in document
    changed = document.replace(old, new, 1)
    with pytest.raises(AssertionError, match="Normative clause differs"):
        check_document(changed)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("mutation", ["delete", "duplicate", "fence", "rename"])
def test_hostile_scope_mutation(document: str, scope: str, mutation: str) -> None:
    check_document(document)
    marker = f"<!-- PS:{scope} -->"
    changed = document.replace(marker, {"delete": "", "duplicate": marker + "\n" + marker, "fence": "~~~text\n" + marker + "\n~~~", "rename": "<!-- PS:unknown -->"}[mutation], 1)
    with pytest.raises(AssertionError, match="active play-session clauses"):
        check_document(changed)


@pytest.mark.parametrize("scope,header,rows", TABLES, ids=["files", "commands", "defaults", "paths", "matrix"])
@pytest.mark.parametrize("mutation", ["delete-row", "duplicate-row", "swap", "weaken", "fence", "comment"])
def test_hostile_table_mutation(document: str, scope: str, header: tuple[str, ...], rows: list[tuple[str, ...]], mutation: str) -> None:
    check_document(document)
    header_line = "| " + " | ".join(header) + " |"
    lines = document.splitlines()
    start = lines.index(header_line)
    end = start + 2 + len(rows)
    original = "\n".join(lines[start:end])
    altered = list(lines[start:end])
    if mutation == "delete-row":
        altered.pop()
    elif mutation == "duplicate-row":
        altered.append(altered[-1])
    elif mutation == "swap":
        altered[-1], altered[-2] = altered[-2], altered[-1]
    elif mutation == "weaken":
        cells = altered[-1].split("|")
        cells[-2] = " REMOVED "
        altered[-1] = "|".join(cells)
    replacement = "\n".join(altered)
    if mutation == "fence":
        replacement = "```text\n" + original + "\n```"
    elif mutation == "comment":
        replacement = "<!--\n" + original + "\n-->"
    changed = document.replace(original, replacement, 1)
    assert changed != document
    with pytest.raises(AssertionError):
        check_document(changed)


@pytest.mark.parametrize("case", MATRIX, ids=[row[0] for row in MATRIX])
def test_every_behavior_oracle_is_required(document: str, case: tuple[str, ...]) -> None:
    check_document(document)
    line = "| " + " | ".join(case) + " |"
    cells = line.split("|")
    cells[-2] = " NO_ORACLE "
    changed = document.replace(line, "|".join(cells), 1)
    assert changed != document
    with pytest.raises(AssertionError, match="Exact table differs"):
        check_document(changed)
