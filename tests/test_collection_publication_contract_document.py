"""Task2E 한국어 구현 계약 검사. C++ 실행·수집 권한을 증명하지 않는다.

문서가 없거나 ANPC_PUBLICATION_DOCUMENT_MODE=before-plan이면 기존 계약을
읽는다. 최초 RED는 missing-clause assertion이며 FileNotFound/import 실패가 아니다.
모든 hostile mutation은 메모리에서 수행하고 원본 문서를 보존한다.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

import pytest

from test_collection_host_bridge_contract_document import GROUPS, table

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "docs/current"
PLAN = "scenario-collection-publication-v1-implementation-plan.md"
HOST = "scenario-host-capture-v1-contract.md"
SCOPES = (
    "purpose", "terms", "scope", "order", "failures", "done", "files",
    "metadata", "groups", "join", "json", "diagnostics", "budget",
    "steps", "matrix", "commands",
)
RULES = {
    "purpose": {
        "E01": "출처·결과 연결은 회차의 고정 출처와 실제 저장된 판단 기록을 대조하고 연결 파일까지 재검증한 뒤 수락하는 기능이다.",
    },
    "scope": {
        "E02": "Task2D는 native FileStore·same-image Dataset·Reader-owned receipt·실제 Host 저장 연결의 지정 범위에서 승인됐다. 이 계획은 Task2E 구현·실행 승인을 주장하지 않는다.",
        "E03": "production collection closed; Approved=false; ResolvePolicyReady=false; production_eligible=false를 유지한다.",
        "E04": "Task3 GameInstance·issuer·실제 reset·UI와 Task4 ML·authority/import는 제외한다. fixture reset/drain은 실제 측정으로 승격하지 않는다.",
    },
    "order": {
        "E05": "Record Build 전에 immutable context에서 metadata를 고정한다. Build 뒤 원본 Record의 family·seed·build·source·identity를 수선하지 않는다.",
        "E06": "Skill start는 marker보다 앞이다. pending write 성공·producer verified·collection accepted를 별도로 유지하며 sidecar 실패로 과거 counter를 rollback하지 않는다.",
    },
    "failures": {
        "E07": "실패는 callback·I/O 전에 terminal latch와 epoch/lease를 닫는다. deadline 전 failed, at/after deadline timed_out을 유지하며 진단 실패도 memory terminal과 실패 반환을 보존한다.",
        "E08": "context join·sidecar·diagnostic 저장 실패는 session sticky block이다. 같은 회차 retry·다음 회차·completion pin을 차단하고 기존 Capture/marker와 이미 발생한 Commit/start/verified 사실을 보존한다.",
        "E09": "collection intent에 context 부재·stale lease가 있으면 legacy fallback 금지다. intent 없는 legacy general/ResolveShadow 동작은 보존한다.",
    },
    "done": {
        "E10": "문서 pytest는 계약 일관성만 검사한다. Task2E 완료는 실제 Host 경로의 metadata→receipt→bridge→disk readback과 C01–C07/P14–P18 행동 증거 및 고정 subject 독립 SPEC→QUALITY 검토를 요구한다.",
    },
    "files": {
        "E11": "Builder·serializer·Adapter·Observation tests·Coordinator·Knowledge·Schema·catalog·generated·Content·ML은 동결한다. Dataset은 필요한 additive read-only accessor만 허용한다.",
        "E12": "CollectionContext는 필요한 read-only getter 또는 좁은 lifecycle 경계만 허용한다. public authority mint·mutable setter·production issuer는 금지한다.",
    },
    "metadata": {
        "E13": "모든 생산 phase는 raw source_type=2/Dagger와 scenario_collection_utility_unreviewed를 사용한다. 기존 phase reason tags와 Resolve capture-only 0.25·다른 phase 1.0 및 Utility label 의미를 보존한다.",
        "E14": "source/controller/mode는 현재 context의 실제 조합이다. automatic·automated replay는 automated_runtime이며 family 문자열로 human_play를 추론하지 않는다.",
        "E15": "승격 전 KnowledgeBeforePromotion은 같은 preparation의 owned 값으로 보존한다. Finalize 뒤 같은 immutable Snapshot의 handles/mask/Tensor와 대조해 Record Build 전에 group을 만든다.",
    },
    "groups": {
        "E16": "group 문자열은 canonical ASCII이며 trim/lowercase 수선 금지다. TargetCompositionFamily는 regular target_mask=true에서 NoTarget을 제외하고 중복 제거·generated enum 숫자 오름차순으로 + 연결한다. empty set -> reject다.",
        "E17": "Entity/SoundEvent는 exact KnowledgeBeforePromotion entry와 대조한다. LastKnownPosition은 modality_unknown이며 visible_now=false·age>0도 kind evidence를 지우지 않는다.",
        "E18": "GoalSequenceFamily는 현재 GoalToken과 G76–83/G84–91 one-hot를 대조한다. EventSequenceFamily는 catalog taxonomy이며 관측 prefix·미래 사건 완료·Teacher 입력으로 사용하지 않는다.",
    },
    "join": {
        "E19": "receipt는 FDecisionRecordV2Reader만 생성한다. GetRecord/GetContext/GetLease/GetEpoch/GetAuthority와 descriptor를 사용하고 public path+bool/digest mint·Capture/marker 재개방·새 parser를 금지한다.",
        "E20": "bridge는 exact context/World/Host/episode/lease/epoch·namespace/build/family/seeds/source/tag·여덟 group을 대조한다. 같은 receipt/identity/sample/path 및 episode/decision pair 재발행은 reject한다.",
        "E21": "accepted entry와 count는 sidecar exclusive publish + actual exact readback 및 마지막 current lease 검사 뒤 한 번만 발행한다. 불일치나 재진입은 미발행과 session block을 유지한다.",
    },
    "json": {
        "E22": 'sidecar와 diagnostic은 sorted_json_bytes(value) + b"\\n"의 exact UTF-8 bytes다. key sort·compact separators·ensure_ascii=False·allow_nan=False와 정확한 정수·JSON escaping을 지킨다.',
        "E23": "FileStore의 실제 CREATE_NEW → full write/flush/close → nonreplace MoveFileW → bounded held-image readback을 사용한다. final/temp 충돌·race·ancestor 교체를 거부하고 exact owned temp만 cleanup한다.",
    },
    "diagnostics": {
        "E24": "observed_id는 실제 발급·관찰한 ID 또는 null이다. Request 전 실패에 DecisionId를 만들지 않으며 memory-only Snapshot/Draft는 snapshot_present=false, snapshot_ref=null이다.",
        "E25": "snapshot_present=true는 실제 immutable artifact의 size/hash 검증 뒤에만 허용한다. fake Snapshot/hash와 diagnostic의 capture_identity/committed 필드 추가를 금지하며 committed/Dataset 분모에서 제외한다.",
        "E26": "terminalization 뒤 진단 저장은 exact 실패 episode에 결속된 제한 경로로 수행한다. revoked lease를 일반 publication에 다시 허용하지 않으며 diagnostic persistence 실패도 성공·새 회차·completion pin을 만들지 않는다.",
    },
    "budget": {
        "E27": "storage_limit_bytes는 Capture·marker·sidecar·diagnostic·index 및 in-flight overhead를 모두 포함한다. checked arithmetic과 쓰기 전 예약을 사용하며 World/reset으로 누적 소비량을 초기화하지 않는다.",
        "E28": "실패해도 보존된 final/residual bytes는 소비량에 남긴다. 진단/index 예약 부족도 fail closed이며 원본 삭제로 공간 확보·예산 초과 write·accepted 선증가를 금지한다.",
    },
    "steps": {
        "E29": "metadata slice → lower JSON publication → bridge/diagnostics → Host wiring 순서로 나눈다. 각 작은 단계는 행동 RED → 최소 구현 → focused GREEN이며 writer와 단일 build owner를 분리한다.",
    },
    "matrix": {
        "E30": "hostile case마다 정상 control과 실제 stage 도달을 증명한다. compile/link 오류·0-discovery·timeout·mock 성공은 행동 RED가 아니며 문서 mutation 수를 Unreal 검사 수에 합산하지 않는다.",
    },
    "commands": {
        "E31": "문서 작업자는 C++ 구현·Unreal/build 실행·commit/push를 수행하지 않는다. 부모 실행은 전용 Saved·고유 evidence·원본 preserved-source inventory와 단일 build owner를 전제로 한다.",
    },
}
FILES = [
    ["Execution/AINativeNPCGoalHostComponent.h", "수정", "metadata 전달·bridge 호출·terminal 연결"],
    ["Execution/AINativeNPCGoalHostComponent.cpp", "수정", "metadata 전달·bridge 호출·terminal 연결"],
    ["Collection/AINativeNPCCollectionCaptureBridge.h", "신규", "receipt/context join·entry/diagnostic"],
    ["Collection/AINativeNPCCollectionCaptureBridge.cpp", "신규", "receipt/context join·entry/diagnostic"],
    ["Collection/AINativeNPCCollectionFileStore.h", "수정", "bounded JSON publication·readback"],
    ["Collection/AINativeNPCCollectionFileStore.cpp", "수정", "bounded JSON publication·readback"],
    ["Collection/AINativeNPCCollectionContext.h", "조건부", "read-only getter·좁은 lifecycle 경계"],
    ["Collection/AINativeNPCCollectionContext.cpp", "조건부", "read-only getter·좁은 lifecycle 경계"],
    ["Dataset/DecisionRecordV2.h", "조건부", "필요한 additive read-only accessor만"],
    ["Dataset/DecisionRecordV2.cpp", "조건부", "필요한 additive read-only accessor만"],
    ["Tests/AINativeNPCCollectionHostTests.cpp", "수정", "실제 Host C01–C07/P14–P18"],
    ["Tests/AINativeNPCCollectionCaptureBridgeTests.cpp", "신규", "join·JSON·진단·budget hostile"],
    ["Tests/DecisionRecordV2Tests.cpp", "조건부", "Reader-only·legacy 회귀"],
]
FLOW = [
    ["1", "Finalize", "Host", "승격 전 관측과 같은 Snapshot"],
    ["2", "policy selection", "기존 orchestrator", "기존 Utility 의미 보존"],
    ["3", "Request", "Host", "같은 token/identity"],
    ["4", "metadata + Record Build", "Host", "immutable context·여덟 group 고정"],
    ["5", "pending write + exact readback", "Dataset/FileStore", "실패: Commit/start 0"],
    ["6", "Commit + final promote + private Skill start", "Coordinator/Host", "실제 start 사실 보존"],
    ["7", "marker publish", "Dataset/FileStore", "실패: verified/accepted 0"],
    ["8", "same-image committed readback", "Reader", "Capture 1회 + marker 1회"],
    ["9", "producer verified", "Host", "SlotHistory·VerifiedCaptureDecisionIds"],
    ["10", "bridge context join", "CaptureBridge", "불일치: session block"],
    ["11", "sidecar exclusive publish + actual exact readback", "CaptureBridge/FileStore", "실패: accepted 0"],
    ["12", "collection accepted", "CaptureBridge", "entry/count 한 번 발행"],
]
METADATA = [
    ["EpisodeId", "scenario_capture_<session UUID>_<collection episode UUID>_<process sequence>"],
    ["sequence", "0이 아닌 20자리 unsigned decimal; process-wide checked allocator"],
    ["GeneratorTemplateVersion", "neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1"],
    ["GeneratorOrRuntimeBuildSha256", "runtime_build_evidence_sha256 = session.runtime_build_sha256"],
    ["ScenarioFamilyId", "episode.family.scenario_family_id = catalog.scenario_family_id"],
    ["MapSeed,SimulationSeed", "episode.seeds.map_seed = episode.seeds.simulation_seed = conditions.seed"],
    ["SourceType", "2/Dagger"],
    ["ReasonTags", "scenario_collection_utility_unreviewed + 기존 phase reason tags"],
]
MATRIX = {
    "C01": ("caller family/seed/build 변경", "Build 전", "원본 Record 불변"),
    "C02": ("automatic·automated replay", "모든 생산 phase", "human 오분류 0"),
    "C03": ("forged source/controller/build", "fixture-only", "real authority 0"),
    "C04": ("intent + missing/stale/preparing/terminal", "Request 전", "fallback 0"),
    "C05": ("A revoke 뒤 B·old receipt", "current lease", "B 불변"),
    "C06": ("Utility label·receipt 승인 오인", "readiness", "false 유지"),
    "C07": ("여덟 group·seed·budget", "enum/mask/one-hot", "수선 0"),
    "P14": ("real commit 뒤 sidecar open/write/flush/close/move/readback", "producer verified", "Capture/marker 보존"),
    "P15": ("receipt/identity/sample/path/episode-decision 중복", "ledger", "accepted 증가 0"),
    "P16": ("preparation/timeout/mapping/reset·memory-only", "실제 observed_id/null", "false/null·분모 제외"),
    "P17": ("sidecar 실패 뒤 diagnostic I/O 실패", "terminal 선행", "실패 반환·session block"),
    "P18": ("intent 없는 general/ResolveShadow", "legacy", "namespace/metadata/cleanup 보존"),
    "J01": ("JSON final/temp file·directory·race·alias", "native syscall", "기존 bytes/type/membership 보존"),
    "J02": ("MAX_uint64 DecisionId·escape·Unicode·finite time", "Python canonical bytes", "double 반올림 0"),
    "J03": ("join/publish/readback callback의 revoke·replacement", "같은 strong pin", "old accepted 0·B 불변"),
    "J04": ("누적·overflow·진단/index/in-flight 한도", "쓰기 전 예약", "budget 초과 0"),
}


def active(text: str) -> str:
    """Fence/comment 안의 규범은 비활성화하되 E scope marker 위치는 보존한다."""
    output = []
    fence = None
    for line in text.splitlines(keepends=True):
        boundary = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence is None and boundary:
            fence = boundary.group(1)
            output.append(re.sub(r"[^\r\n]", " ", line))
        elif fence is not None:
            if boundary and boundary.group(1)[0] == fence[0] and len(boundary.group(1)) >= len(fence) and not boundary.group(2).strip():
                fence = None
            output.append(re.sub(r"[^\r\n]", " ", line))
        else:
            output.append(line)
    assert fence is None, "Unclosed publication fence"
    return re.sub(r"<!--(?! E:[a-z-]+ -->).*?-->", lambda m: re.sub(r"[^\r\n]", " ", m.group()), "".join(output), flags=re.DOTALL)


def sections(text: str) -> dict[str, str]:
    markers = list(re.finditer(r"^<!-- E:([a-z-]+) -->$", active(text), re.MULTILINE))
    assert tuple(m.group(1) for m in markers) == SCOPES, "Missing/duplicate/out-of-order active publication clauses"
    return {m.group(1): text[m.end():markers[i + 1].start() if i + 1 < len(markers) else len(text)] for i, m in enumerate(markers)}


def check_document(text: str) -> None:
    parts = sections(text)
    for scope, rules in RULES.items():
        lines = active(parts[scope]).splitlines()
        found = [line for line in lines if re.match(r"^- \*\*E\d+\*\*:", line)]
        assert found == [f"- **{key}**: {value}" for key, value in rules.items()], f"Normative clause differs: {scope}"
    for scope, header, expected in (
        ("files", ["파일", "작업", "허용 변경"], FILES),
        ("order", ["순서", "작업", "책임", "관찰 기준"], FLOW),
        ("metadata", ["필드", "고정 값 또는 대조"], METADATA),
        ("groups", ["wire index", "producer field", "exact 값 또는 닫힌 derivation", "원천/대조 oracle"], GROUPS),
    ):
        assert table(active(parts[scope]), header) == expected, f"Exact table differs: {scope}"
    rows = table(active(parts["matrix"]), ["ID", "입력·실패 주입", "실제 경계", "필수 oracle", "담당 검사"])
    assert [row[0] for row in rows] == list(MATRIX), "Matrix coverage/order differs"
    for row in rows:
        for index, clause in enumerate(MATRIX[row[0]], 1):
            assert clause in row[index], f"Matrix clause differs: {row[0]} column {index}"
        assert row[4] in {"Host", "Bridge", "Host+Bridge", "Host+Dataset"}, "Matrix test owner missing"
    for scope, required in {
        "terms": ("고정 출처(context)", "검증 영수증(receipt)", "연결 파일(sidecar)", "producer verified", "collection accepted"),
        "scope": ("task2d-final-acceptance-01.json", "before-source/Source", "역사적", "문서-only"),
        "groups": ("Orient,Navigate,Search,Resolve,Return", "Entity,SoundEvent,LastKnownPosition,CoverSlot,SmartObject,Waypoint,WorldPosition", "sight,hearing,modality_unknown", "kind_evidence:position_only", "kind_evidence:sight+hearing+modality_unknown"),
        "join": ("ReadCollectionCommittedReceipt", "descriptor-only", "reentrant", "Snapshot"),
        "json": ("entries/<session UUID>/<collection episode UUID>/<process sequence>.json", "diagnostics/<session UUID>/<collection episode UUID>/<diagnostic UUID>.json", ".tmp", "18446744073709551615", "Python", "committedEntry", "diagnostic"),
        "diagnostics": ("preparation", "execution", "capture", "storage", "reset", "observation_mapping_failed", "observed_at_seconds"),
        "budget": ("max_decisions", "checked", "reservation", "World"),
        "steps": ("### 8.1", "### 8.2", "### 8.3", "### 8.4", "C01.BuildMetadataFromImmutableContext", "CaptureCollectionDecision", "CompleteCollectionStorage", "KnowledgeBeforePromotion", "RED", "GREEN"),
        "commands": ("ANPC_PUBLICATION_DOCUMENT_MODE=before-plan", "-B -m pytest", "no:cacheprovider", "PYTHONDONTWRITEBYTECODE=1", "--basetemp", "--junitxml", "NeuralGameEditor Win64 Development", "RunNeuralGameTests.ps1", "AINativeNPC.Collection.CaptureBridge", "AINativeNPC.Collection.Host", "AINativeNPC.Dataset.RecordV2", "AINativeNPC.Collection.Observation", "900초", "null exit", "StopTestSession", "exact test-name multiset", "clean_or_forced_project_modules", "-UserDir=", "tools.validate_anpc_capture_v2", "validate_structure", "validate_committed_entry", "validate_index", "catalog-only"),
    }.items():
        for clause in required:
            assert clause in parts[scope], f"Missing scoped implementation clause: {scope}: {clause}"


def load_document(mode: str = "active") -> str:
    assert mode in {"active", "before-plan"}, "Unknown publication document mode"
    path = CURRENT / PLAN
    if mode == "before-plan" or not path.is_file():
        return (CURRENT / HOST).read_text(encoding="utf-8")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def document() -> str:
    return load_document(os.environ.get("ANPC_PUBLICATION_DOCUMENT_MODE", "active"))


def test_active_publication_contract(document: str) -> None:
    check_document(document)


def test_before_plan_is_missing_clause_not_missing_file() -> None:
    with pytest.raises(AssertionError, match="active publication clauses"):
        check_document(load_document("before-plan"))


@pytest.mark.parametrize("path", ["README.md", "docs/current/scenario-collection-v1-implementation-plan.md", "docs/current/ml-data-pipeline-v1-implementation-plan.md"])
def test_active_entrypoints_link_publication_and_bound_approval(path: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    assert PLAN in text
    assert "<!-- T2E:current -->" in text
    current = text.split("<!-- T2E:current -->", 1)[1].split("<!-- T2E:end -->", 1)[0]
    for clause in ("Task2D", "지정 범위", "Task2E", "production collection closed"):
        assert clause in current, f"Current status missing: {path}: {clause}"
    assert "Task2E 구현 완료" not in current


def test_machine_authorities_and_exact_sidecar_keys_remain_frozen() -> None:
    expected = {
        "scenario_collection_v1.schema.json": "d17f3c153735e2876531eed6f627d0cc7b86e3c7d58bc7ca044b1505a2c00a5f",
        "scenario_catalog_v1.json": "71731db30de5663c040ba31c06b589049f3b575cfd630dae3b8c0a2140aa85e0",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / "contracts/current" / name).read_bytes()).hexdigest() == digest
    defs = json.loads((ROOT / "contracts/current/scenario_collection_v1.schema.json").read_text())["$defs"]
    common = {"kind", "collection_episode_id", "input_source", "execution_mode", "controller", "observation_mapping_version", "family"}
    for kind, additional in (
        ("committedEntry", {"capture_identity", "capture", "committed"}),
        ("diagnostic", {"diagnostic_id", "observed_id", "stage", "reason", "observed_at_seconds", "snapshot_present", "snapshot_ref"}),
    ):
        assert set(defs[kind]["properties"]) == set(defs[kind]["required"]) == common | additional
        assert defs[kind]["additionalProperties"] is False


RULE_CASES = [(scope, key, value) for scope, rules in RULES.items() for key, value in rules.items()]


@pytest.mark.parametrize("scope,key,value", RULE_CASES, ids=[row[1] for row in RULE_CASES])
@pytest.mark.parametrize("mutation", ["delete", "negate", "fence", "comment", "relocate"])
def test_hostile_rule_weakening_is_rejected(document: str, scope: str, key: str, value: str, mutation: str) -> None:
    check_document(document)
    line = f"- **{key}**: {value}"
    assert document.splitlines().count(line) == 1
    replacement = {"delete": "", "negate": line + " 이 규칙은 선택 사항이다.", "fence": f"~~~text\n{line}\n~~~", "comment": f"<!-- {line} -->", "relocate": ""}[mutation]
    changed = document.replace(line, replacement, 1)
    if mutation == "relocate":
        changed += "\n" + line + "\n" if scope != "commands" else ""
    assert changed != document
    with pytest.raises(AssertionError, match="Normative clause differs"):
        check_document(changed)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "fence"])
def test_hostile_scope_markers_cannot_supply_contract(document: str, scope: str, mutation: str) -> None:
    check_document(document)
    marker = f"<!-- E:{scope} -->"
    changed = document.replace(marker, {"missing": "", "duplicate": marker + "\n" + marker, "fence": "```text\n" + marker + "\n```"}[mutation], 1)
    assert changed != document
    with pytest.raises(AssertionError, match="active publication clauses"):
        check_document(changed)


@pytest.mark.parametrize("scope", ["files", "order", "metadata", "groups", "matrix"])
@pytest.mark.parametrize("mutation", ["delete-row", "duplicate-row", "swap", "weaken-cell", "fence", "comment"])
def test_hostile_tables_preserve_exact_coverage(document: str, scope: str, mutation: str) -> None:
    check_document(document)
    part = sections(document)[scope]
    rows = [line for line in part.splitlines() if line.startswith("|")]
    block = "\n".join(rows)
    changed_rows = list(rows)
    if mutation == "delete-row":
        changed_rows.pop()
    elif mutation == "duplicate-row":
        changed_rows.append(rows[-1])
    elif mutation == "swap":
        changed_rows[-1], changed_rows[-2] = changed_rows[-2], changed_rows[-1]
    elif mutation == "weaken-cell":
        cells = changed_rows[-1].split("|")
        cells[2] = " REMOVED "
        changed_rows[-1] = "|".join(cells)
    changed_block = "\n".join(changed_rows)
    if mutation == "fence":
        changed_block = "```text\n" + block + "\n```"
    elif mutation == "comment":
        changed_block = "<!--\n" + block + "\n-->"
    changed = document.replace(block, changed_block, 1)
    assert changed != document
    with pytest.raises(AssertionError):
        check_document(changed)


@pytest.mark.parametrize("case", MATRIX)
def test_hostile_each_matrix_oracle_is_enforced(document: str, case: str) -> None:
    check_document(document)
    part = sections(document)["matrix"]
    row = next(line for line in part.splitlines() if line.startswith(f"| {case} |"))
    for index, clause in enumerate(MATRIX[case], 1):
        cells = row.split("|")
        cells[index + 1] = cells[index + 1].replace(clause, "REMOVED")
        changed = document.replace(row, "|".join(cells), 1)
        assert changed != document
        with pytest.raises(AssertionError, match="Matrix clause differs"):
            check_document(changed)
