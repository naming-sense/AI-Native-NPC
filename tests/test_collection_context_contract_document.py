"""Task 2C document consistency only; no C++/owner/reset/collection execution.

Missing-plan fallback deliberately fails normative assertions, not file imports.
The external S01 acceptance is historical evidence, not a portable test input.
"""
from __future__ import annotations

import re

import pytest

from test_collection_host_bridge_contract_document import (
    BRIDGE, CURRENT, PLAN, read, require, section, table,
)

CONTEXT = "scenario-collection-context-v1-implementation-plan.md"
SOURCE_PATHS = {
    "Execution/AINativeNPCGoalHostComponent.h",
    "Execution/AINativeNPCGoalHostComponent.cpp",
    "Collection/AINativeNPCCollectionContext.h",
    "Collection/AINativeNPCCollectionContext.cpp",
    "Tests/AINativeNPCCollectionHostTests.cpp",
}
CLAUSES = {
    "scope": (
        "immutable context", "lease", "Task 2C", "문서·하네스", "C++ 미수정",
        "Unreal build/run 미실행", "production collection closed", "Task 2D", "Task 2E",
        "Task 3", "Task 4", "Approved=false", "ResolvePolicyReady=false", "production_eligible=false",
    ),
    "baseline": (
        "PrepareDecisionFeatures", "KnowledgeBeforePromotion", "Populate", "Host 9", "Observation 37",
        "2026-10-25", "fresh-host-02", "fresh-observation-01", "S01", "whole_task2b_closed=false",
        "acceptance/acceptance.json", "packet/SCOPE.md", "H10", "broad", "old438", "INCOMPLETE",
        "/mnt/d/Codex-cli/NeuralProject/collection-next-uq63w5dx/NeuralGame",
        "부모 제공 baseline", "Task 2C 성공으로 집계하지 않는다", "원본 승격"
    ),
    "inputs": (
        "validated 값 복사", "caller mutation", "immutable", "session_id", "collection_episode_id",
        "catalog_sha256", "profile_sha256", "runtime_build_evidence_sha256", "observed_geometry_goal_v1",
        "family", "seeds", "limits", "root", "running", "source/controller/mode", "strict lowercase UUIDv4",
        "invalid source/build", "legacy fallback 금지", "public bool/digest setter", "외부 evidence",
        "test_fixture", "human_play", "automated_runtime", "offline_procedural",
    ),
    "lease": (
        "exact World/Host/episode", "epoch", "wrap/reuse 금지", "collection intent", "authorization",
        "context 부재", "preparing", "terminal", "stale", "wrong World/Host", "direct decision",
        "retry 예약", "이미 예약된 callback", "receipt", "teardown", "OnUnregister", "EndPlay",
        "same DecisionId", "intent 없는 legacy", "failed episode reopen 금지",
    ),
    "terminal": (
        "terminal latch", "revoke", "callback·파일 I/O 전에", "authoritative monotonic",
        "deadline 전", "at/after deadline", "timed_out", "observation_mapping_failed",
        "직접 검사한 precondition", "normal sensor absence", "위치 전용", "missing sentinel",
        "session blocked", "lifecycle 검증 예외", "nonfinite", "backwards", "reset precondition",
    ),
    "callbacks": (
        "local strong pin", "authority/context", "callback 뒤", "lease 재검사", "committed-start stack",
        "동기 reset/reattach 금지", "stack unwound/drained", "Task 3", "old callback",
        "현재 B 불변", "teardown", "실패 반환", "counter rollback 금지",
    ),
    "owner": (
        "verified-reset receipt", "terminal-evidence receipt", "fixture-only", "WITH_DEV_AUTOMATION_TESTS",
        "exact 이전 episode/World lease", "persist/readback", "새 collection_episode_id",
        "Task 3", "Task 4", "production collection closed", "실제 reset 미구현",
        "실제 authority 검증 미구현", "bool 성공 선언", "completion pin", "failed/unverified",
    ),
    "steps": (
        "RED", "GREEN", "PrepareDecisionFeatures", "TryStartCurrentDecision", "ScheduleDecisionForAuthority",
        "TeardownAssembly", "FAINativeNPCCollectionHostTestAccess", "WITH_DEV_AUTOMATION_TESTS",
        "강한 소유권", "재진입", "원본", "새 제품 판단", "중단",
    ),
    "verification": (
        "tests/test_collection_context_contract_document.py", "tests/test_collection_host_bridge_contract_document.py",
        "-B", "no:cacheprovider", "--basetemp", "--junitxml", "command/exit/stdout", "원본 bytes", "delta",
        "예상 Runtime RED", "0-discovery", "compile/link", "exact test-name multiset",
        "AINativeNPC.Collection.Host", "AINativeNPC.Collection.Observation", "단일 build owner", "H10",
    ),
}

COVERAGE = [
    ["C01", "context copy 불변", "2E", "Record metadata 고정·pending Record 불변"],
    ["C02", "현재 source/controller/mode 검증", "2E/3", "모든 phase raw metadata·실제 입력 provenance"],
    ["C03", "fixture attach·invalid source/build 거부", "3/4", "실제 owner/build authority"],
    ["C04", "intent/lease fail-closed", "2E", "diagnostic 실제 저장"],
    ["C05", "old callback·reset receipt 장벽 fixture", "3", "실제 입력 정지·World reset"],
    ["C06", "readiness false 유지", "2D/2E/4", "committed receipt·bridge·최종 승인 검증"],
    ["C07", "resolved metadata·limits 입력 검증", "2D/2E", "group derivation·join·storage budget 집행"],
]
POLICY = [
    ["intent_absent", "legacy", "기존 retry 보존"],
    ["context_missing_preparing_terminal_stale", "reject", "legacy fallback 0"],
    ["wrong_world_host_episode_epoch", "reject", "현재 다른 lease 변경 0"],
    ["invalid_source_build", "reject", "기본값 수선 0"],
    ["hard_failure_before_deadline", "failed", "latch/revoke 뒤 callback"],
    ["hard_failure_at_or_after_deadline", "timed_out", "관측 실패 diagnostic 별도"],
    ["queued_old_callback", "reject", "현재 B 변경 0"],
    ["reset_without_terminal_evidence", "reject", "새 attach 0"],
    ["reset_failed_unverified", "session_blocked", "새 attach 0"],
    ["verified_reset_and_terminal_evidence", "new_episode_only", "fixture-only receipt·새 lease"],
]


@pytest.fixture(scope="module")
def document() -> str:
    path = CURRENT / CONTEXT
    return path.read_text(encoding="utf-8") if path.is_file() else read(BRIDGE) + "\n" + read(PLAN)


def scoped(text: str, key: str) -> str:
    return section(text, key, "C")


def check_coverage(text: str) -> None:
    assert table(scoped(text, "coverage"), ["ID", "2C 검사 범위", "남은 단계", "2C 완료로 주장할 수 없는 항목"]) == COVERAGE


def check_policy(text: str) -> None:
    assert table(scoped(text, "policy"), ["조건", "결과", "필수 oracle"]) == POLICY


def check_allowlist(text: str) -> None:
    blocks = re.findall(r"```text\n(.*?)```", scoped(text, "files"), re.DOTALL)
    paths = [line.strip() for block in blocks for line in block.splitlines() if line.strip()]
    assert len(paths) == len(set(paths)) and set(paths) == SOURCE_PATHS, "Task 2C source allowlist differs"


@pytest.mark.parametrize("key", CLAUSES)
def test_context_scoped_contract(document: str, key: str) -> None:
    require(scoped(document, key), *CLAUSES[key])


def test_context_exact_source_allowlist(document: str) -> None:
    check_allowlist(document)


def test_context_c01_c07_are_bounded_not_full_acceptance(document: str) -> None:
    check_coverage(document)


def test_context_lifecycle_precedence_and_owner_boundary(document: str) -> None:
    check_policy(document)


def test_dev_map_binding_and_stop_only_callbacks_are_explicit(document: str) -> None:
    require(scoped(document, "inputs"), "transient fixture World", "fixture namespace", "실제 map 검증 증거 0")
    require(scoped(document, "callbacks"), "stop-only callback", "arbitrary synchronous UnregisterComponent/DestroyWorld 지원으로 확대하지 않는다")


@pytest.mark.parametrize("name", [BRIDGE, PLAN])
def test_status_surfaces_do_not_hide_existing_host_slice(name: str) -> None:
    text = read(name)
    require(text, CONTEXT, "Host 9", "Observation 37", "S01", "whole_task2b_closed=false")
    for stale in (
        "Host/collection bridge의 Runtime 구현 전", "**Runtime 구현 전**",
        "현재 Host는 `FDecisionFeatureBuilderInput`의 Targets·Candidates를 채우지만 관측 scalar 배열은 기본값이다",
        "Host Populate callsite 부재", "pre-promotion 복사 부재", "Host mapping 실패 경로 부재",
        "Host 실제 호출·downstream 차단 미구현", "Host 연결, 실제 Capture 저장·복원과 사람 플레이 확인은 후속이다",
    ):
        assert stale not in text, f"Stale global Host claim: {stale}"


@pytest.mark.parametrize("key", CLAUSES)
def test_every_context_obligation_rejects_deletion(document: str, key: str) -> None:
    positive = scoped(document, key)
    require(positive, *CLAUSES[key])
    for clause in CLAUSES[key]:
        changed = positive.replace(clause, "REMOVED")
        assert changed != positive
        with pytest.raises(AssertionError, match="Missing normative clauses"):
            require(changed, *CLAUSES[key])


@pytest.mark.parametrize("key", [*CLAUSES, "files", "coverage", "policy"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_context_scope_markers_fail_closed(document: str, key: str, mutation: str) -> None:
    assert scoped(document, key).strip()
    marker = f"<!-- C:{key} -->"
    changed = document.replace(marker, "", 1) if mutation == "missing" else document + "\n" + marker + "\nShadow.\n"
    with pytest.raises(AssertionError):
        scoped(changed, key)


@pytest.mark.parametrize("old,new", [
    ("legacy fallback 0", "legacy fallback allowed"),
    ("latch/revoke 뒤 callback", "callback 뒤 latch/revoke"),
    ("timed_out", "failed"),
    ("현재 B 변경 0", "현재 B revoke"),
    ("fixture-only receipt·새 lease", "production authority"),
    ("new_episode_only", "reopen_failed_episode"),
])
def test_context_policy_rejects_weakening(document: str, old: str, new: str) -> None:
    check_policy(document)
    assert old in scoped(document, "policy")
    with pytest.raises(AssertionError):
        check_policy(document.replace(old, new))


@pytest.mark.parametrize("index", range(len(COVERAGE)))
def test_coverage_rejects_promoting_later_acceptance(document: str, index: int) -> None:
    check_coverage(document)
    changed = document.replace(COVERAGE[index][-1], "2C 전체 완료")
    assert changed != document
    with pytest.raises(AssertionError):
        check_coverage(changed)


@pytest.mark.parametrize("extra", ["Dataset/DecisionRecordV2.cpp", "Collection/AINativeNPCCollectionCaptureBridge.cpp", "Collection/AINativeNPCCollectionFileStore.cpp"])
def test_allowlist_rejects_later_storage_publication_work(document: str, extra: str) -> None:
    check_allowlist(document)
    changed = document.replace("Tests/AINativeNPCCollectionHostTests.cpp\n```", "Tests/AINativeNPCCollectionHostTests.cpp\n" + extra + "\n```")
    assert changed != document
    with pytest.raises(AssertionError):
        check_allowlist(changed)


def test_absent_context_document_fails_contract_assertion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(globals(), "CONTEXT", "absent-context-plan-red-fixture.md")
    assert not (CURRENT / CONTEXT).exists()
    fallback = document.__wrapped__()
    assert fallback == read(BRIDGE) + "\n" + read(PLAN)
    with pytest.raises(AssertionError, match="Required scope"):
        scoped(fallback, "inputs")


# 상태 문구만 검사한다. 외부 실행 증거를 재검증하거나 독립 승인을 발급하지 않는다.
# 이 보강분의 실행은 부모 담당이며 문서 작업자는 테스트를 실행하지 않았다.
CHECKPOINT_CLAUSES = {
    "historical": (
        "문서-only checkpoint에 한한 역사적 사실", "C++ 미수정", "Unreal build/run 미실행",
    ),
    "current": (
        "copy 5파일 구현", "last runtime checkpoint", "부모 확인",
        "/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/final-05",
        "c2-final-host-01", "Host 25", "c2-final-observation-01", "Observation 37",
        "c2-final-broad-01", "broad 229", "최종 최신 bytes 실행 검증 완료; 독립 승인 아님",
    ),
    "limits": (
        "독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만", "production collection closed",
        "Approved=false", "ResolvePolicyReady=false", "production_eligible=false",
        "실제 collection 저장 미구현", "실제 reset 미구현",
        "terminal/reset/dispatch-drain receipt는 dev fixture 값",
        "실제 Executor drain 측정 미구현", "GameInstance owner·production issuer·ML import 미구현",
        "원본 승격 없음", "commit/push 없음",
    ),
}


def check_checkpoint_status(text: str) -> None:
    for key, clauses in CHECKPOINT_CLAUSES.items():
        require(section(text, key, "T2C"), *clauses)
    active = section(text, "current", "T2C")
    for historical_only in ("C++ 미수정", "Unreal build/run 미실행", "문서·하네스 및 후속 구현 계획** 단계"):
        assert historical_only not in active, f"Historical checkpoint promoted to current: {historical_only}"


@pytest.mark.parametrize("name", [CONTEXT, PLAN, BRIDGE])
def test_task2c_history_current_copy_and_pending_approval_are_separate(name: str) -> None:
    check_checkpoint_status(read(name))


@pytest.mark.parametrize("key", CHECKPOINT_CLAUSES)
def test_task2c_checkpoint_obligations_cannot_be_supplied_by_history(document: str, key: str) -> None:
    check_checkpoint_status(document)
    active = section(document, key, "T2C")
    for clause in CHECKPOINT_CLAUSES[key]:
        changed = document.replace(active, active.replace(clause, "REMOVED"), 1)
        changed += "\n<!-- T2C:archived-copy -->\n" + active
        with pytest.raises(AssertionError):
            check_checkpoint_status(changed)


@pytest.mark.parametrize("old,new", [
    ("문서-only checkpoint에 한한 역사적 사실", "현재 전체 작업의 사실"),
    ("copy 5파일 구현", "copy 5파일 구현; C++ 미수정; Unreal build/run 미실행"),
    ("최종 최신 bytes 실행 검증 완료; 독립 승인 아님", "최종 전체 승인 완료"),
    ("독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만", "독립 SPEC→QUALITY 승인 완료"),
    ("Approved=false", "Approved=true"),
    ("ResolvePolicyReady=false", "ResolvePolicyReady=true"),
    ("production_eligible=false", "production_eligible=true"),
    ("실제 collection 저장 미구현", "실제 collection 저장 완료"),
    ("실제 reset 미구현", "실제 reset 완료"),
    ("실제 Executor drain 측정 미구현", "실제 Executor drain 측정 완료"),
    ("원본 승격 없음", "원본 승격 완료"),
])
def test_task2c_checkpoint_rejects_status_promotion(document: str, old: str, new: str) -> None:
    check_checkpoint_status(document)
    assert old in document
    with pytest.raises(AssertionError):
        check_checkpoint_status(document.replace(old, new))


def test_task2c_actual_test_links_keep_partial_coverage_and_fixture_limits(document: str) -> None:
    check_coverage(document)
    check_allowlist(document)
    linked = scoped(document, "runtime-tests")
    rows = table(linked, ["ID", "실제 등록 test-name", "이번 연결의 한계"])
    assert [row[0] for row in rows] == [row[0] for row in COVERAGE]
    expected_suffixes = (
        "C01.ImmutableContextCopy", "C02.SourceModeControls", "C03.StrictContextValidation",
        "C04.IntentRejectsMissingOrInactiveContext", "C05.OwnerResetBarrierAcrossWorlds",
        "C05.OwnerResetBarrierAcrossWorlds", "C03.StrictContextValidation",
    )
    for row, suffix in zip(rows, expected_suffixes):
        assert "AINativeNPC.Collection.Host." + suffix in row[1]
        assert row[2]
    require(linked, "C06 전용 등록 test는 없다", "HostCheckNoCollectionWrites", "IsResolvePolicyReady",
            "Approved/production_eligible는 문서 불변식", "group derivation·join·storage budget 집행은 후속",
            "Reentry.StopWaitsForExternalDrain", "Lease.RevokeBeforeDependencyRelease",
            "Reentry.AttemptPinsOutliveHostBinding", "Failure.InvalidClockBlocksSession")
    require(section(read(BRIDGE), "matrix"), "문서-only checkpoint 당시의 gap",
            "C03의 context 경계·C04의 intent 구분을 현재 copy에도 미구현이라고 재해석하지 않는다")
