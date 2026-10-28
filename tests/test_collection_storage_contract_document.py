"""Task2D 문서 일관성 + in-memory hostile mutation 검사.

C++/Win32 동작, 외부 acceptance, 실제 수집 authority를 실행 검증하지 않는다.
ANPC_STORAGE_DOCUMENT_MODE=before-plan은 부모의 문서 RED 전용 입력이다.
기존 문서로 규범 assertion을 실패시키며 missing-file/import 오류를 RED로 세지 않는다.
"""
from __future__ import annotations

import os
from pathlib import Path
import re

import pytest

from test_collection_host_bridge_contract_document import table

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "docs/current"
STORAGE = "scenario-collection-storage-v1-implementation-plan.md"
BRIDGE = "scenario-host-capture-v1-contract.md"
PLAN = "scenario-collection-v1-implementation-plan.md"
SCOPES = (
    "status", "baseline", "lower-files", "host-files", "context-files",
    "paths", "ownership", "reservations", "io", "receipt", "host-flow",
    "matrix", "steps", "verification", "boundaries",
)
FILES = {
    "lower-files": {
        "Collection/AINativeNPCCollectionFileStore.h",
        "Collection/AINativeNPCCollectionFileStore.cpp",
        "Dataset/DecisionRecordV2.h",
        "Dataset/DecisionRecordV2.cpp",
        "Tests/DecisionRecordV2Tests.cpp",
    },
    "host-files": {
        "Execution/AINativeNPCGoalHostComponent.h",
        "Execution/AINativeNPCGoalHostComponent.cpp",
        "Tests/AINativeNPCCollectionHostTests.cpp",
    },
    "context-files": {
        "Collection/AINativeNPCCollectionContext.h",
        "Collection/AINativeNPCCollectionContext.cpp",
    },
}
# 규범은 exact active line으로 검사한다. 다른 절/예제/과거 기록의 token은
# 현재 의무를 대신할 수 없다. 문장 의미 전체를 판정하는 하네스는 아니다.
RULES = {
    "status": {
        "D00": "이 문서는 활성 Task2D 세부 계획이다. 문서 하네스 통과는 C++ 행동 검증을 대체하지 않는다.",
        "D01": "Task2D 전체 완료는 lower test만으로 주장 금지다. lower, Host integration, Task2E oracle을 분리한다.",
        "D02": "production collection closed; Approved=false; ResolvePolicyReady=false; production_eligible=false를 유지한다.",
    },
    "baseline": {
        "D03": "Task2C 독립 SPEC→QUALITY 승인은 고정된 copy context/lease 부분 범위다. 원본 승격·실제 저장·reset·authority·ML 완료로 확대하지 않는다.",
        "D04": "읽기 기준은 task2d-x0xm6hwr/before-source/Source이며 현재 live copy의 최종 bytes·실행 성공은 이 문서가 인증하지 않는다.",
    },
    "lower-files": {
        "D05": "lower 범위는 FileStore/Dataset/기존 DecisionRecordV2Tests뿐이다. legacy Writer/Reader signature·호출자·serialization 의미를 보존한다.",
    },
    "host-files": {
        "D06": "Host wiring은 lower 이후 별도 단계다. 기존 CollectionHostTests에서 actual Coordinator와 private Skill start를 실행한다.",
    },
    "context-files": {
        "D07": "Context 변경은 필요한 read-only observation accessor만 별도 delta로 허용한다. public authority mint·새 issuer·mutable setter는 금지한다.",
    },
    "paths": {
        "D08": "process-wide checked uint64는 0을 발급하지 않는다. MAX_uint64는 마지막 유효 번호이며 이후 영구 실패한다. 실패 번호 재사용·World/Host/reset에 의한 초기화는 금지한다.",
        "D09": "native root는 canonical local Windows absolute directory이고 artifact는 canonical POSIX relative path다. 두 입력 검사를 구분하며 trim/lowercase로 수선하지 않는다.",
        "D10": "artifact의 absolute·drive·UNC·backslash·빈 component·dot/parent traversal·ADS·device name·alias를 거부한다.",
    },
    "ownership": {
        "D11": "실 filesystem root directory handle 독점과 cooperating process mutex를 함께 보유한다. 추가 persistent lock artifact는 만들지 않는다.",
        "D12": "root 위 ancestor부터 destination parent까지 component별 directory handle을 no delete sharing으로 유지한다. reparse/alias/query failure는 reject한다.",
        "D13": "보장은 protected cooperating root에 한정한다. arbitrary malicious writer 방어·crash recovery·gameplay rollback은 범위 밖이며 unsupported는 fail closed다.",
    },
    "reservations": {
        "D14": "여섯 예약 이름의 file·directory·reparse 충돌을 거부한다. final.tmp도 검사하며 stage별 exact owned identity만 허용한다.",
    },
    "io": {
        "D15": "각 stage에서 lease/reservations를 검사한다. CREATE_NEW → full write/flush/close → nonreplace MoveFileW 순서를 지킨다.",
        "D16": "cleanup은 exact owned handle identity에 결속한다. foreign identity·충돌 sentinel·committed pair를 삭제하거나 truncate/replace하지 않는다.",
        "D17": "post-start I/O failure는 과거 Commit/start counter rollback 금지다. raw final을 보존하고 receipt/verified를 새로 발행하지 않는다.",
    },
    "receipt": {
        "D18": "Dataset의 같은 cpp private BuildCaptureEnvelopeBytes/BuildCommittedMarkerBytes를 재사용한다. 새 parser·wire format·공개 serializer를 만들지 않는다.",
        "D19": "committed-readback은 Capture 1회 + marker 1회다. 같은 immutable images로 exact expected bytes·marker·size/hash를 계산하며 legacy chain read와 hash용 재개방을 금지한다.",
        "D20": "receipt는 Reader-only immutable result다. 실패 미발행·strong context lease pin·publication 직전 current lease 재검사를 요구한다. public path+bool/digest mint는 금지한다.",
        "D21": "pending readback과 marker 생성 I/O는 별도 집계한다. invalid-first·mixed images·감지된 rebind는 재시도 읽기 없이 실패한다.",
    },
    "host-flow": {
        "D22": "collection intent 실패에는 legacy fallback 금지다. actual Coordinator의 final promotion/private start 뒤 marker→receipt→verified 순서를 유지한다.",
        "D23": "producer verified와 collection accepted를 구분한다. metadata/group/context join·sidecar·diagnostic은 Task2E다.",
    },
    "matrix": {
        "D24": "각 hostile case에 정상 native control과 stage 도달 증거가 필요하다. mock 성공·0-discovery·compile/link 오류·timeout은 행동 RED가 아니다.",
        "D25": "기존 sentinel의 bytes/size/hash/type/membership을 보존한다. race로 삽입한 sentinel은 삽입 직후 inventory와 비교한다.",
    },
    "steps": {
        "D26": "문서/하네스 확정 → 부모 실제 RED→GREEN → focused/broad → 고정 subject 독립 SPEC→QUALITY 순서다. commit/push는 수행하지 않는다.",
    },
    "verification": {
        "D27": "단일 build owner가 원본 프로젝트에서 개발·빌드한다. 테스트 Saved만 전용 경로로 격리하고 기존 수집 파일·과거 evidence를 보존한다.",
        "D28": "exact test-name multiset·owning TU compile·source→binary·exit·StopTestSession/report·원본 보존을 대조한다. 문서 검사 수와 Unreal 행동 검사 수는 별도다.",
    },
    "boundaries": {
        "D29": "Adapter/Observation tests/Builder/Coordinator/Knowledge/Schema/generated/assets/ML은 동결한다. Dataset cpp 안의 Builder 구현도 동결한다.",
        "D30": "Task3 실제 owner/reset/UI와 Task4 authority/import는 후속이다. fixture drain·reset 값은 실제 측정으로 승격하지 않는다.",
    },
}
STATUS = [
    ["Task2C", "고정 부분 범위 승인", "copy context/lease만; acceptance 기록 참조"],
    ["문서/하네스", "작성·실행 대기", "contract consistency와 hostile mutations"],
    ["2D-lower", "구현·행동 검증 후속", "Store/Dataset bytes·경로 안전"],
    ["2D-Host", "lower 이후 후속", "실제 phase/World/Coordinator/start 통합"],
    ["2E", "후속", "metadata/group/context join·sidecar·diagnostic"],
    ["Task3/4", "후속", "실제 owner/reset/UI·authority/import"],
]
RESERVATIONS = [
    ["allocated", "none", "final,final.tmp,final.pending,final.pending.tmp,final.committed,final.committed.tmp"],
    ["pending-temp", "final.pending.tmp", "final,final.tmp,final.pending,final.committed,final.committed.tmp"],
    ["pending", "final.pending", "final,final.tmp,final.pending.tmp,final.committed,final.committed.tmp"],
    ["raw-final", "final", "final.tmp,final.pending,final.pending.tmp,final.committed,final.committed.tmp"],
    ["marker-temp", "final,final.committed.tmp", "final.tmp,final.pending,final.pending.tmp,final.committed"],
    ["committed", "final,final.committed", "final.tmp,final.pending,final.pending.tmp,final.committed.tmp"],
]
FLOW = [
    ["Request", "Host", "same Snapshot/token/identity"],
    ["pending+exact readback", "additive Dataset/Store", "precommit failure: Commit/start delta 0"],
    ["actual Coordinator(final promotion/private start)", "Coordinator/Host", "stale/promotion/start reject: verified delta 0"],
    ["marker", "additive Dataset/Store", "post-start failure: start 사실·raw final 보존"],
    ["receipt", "additive Reader", "same-image+current lease; failure unpublished"],
    ["verified", "Host", "SlotHistory/VerifiedCaptureDecisionIds; accepted는 2E"],
]
# 행별 입력·lower·Host·2E의 관찰 대상을 따로 고정한다.
MATRIX = {
    "P01": (("Orient/Navigate/Search/Resolve/Return", "Observe"), ("roundtrip",), ("실제 phase", "fake Capture 0"), ("metadata",)),
    "P02": (("same DecisionId=1", "실패"), ("sequence", "재사용 0"), ("raw episode/sample/path",), ("join",)),
    "P03": (("World A", "World B", "MAX_uint64"), ("영구 실패", "동시"), ("World", "A bytes"), ("Task3",)),
    "P04": (("여섯", "file", "directory", "reparse"), ("final.tmp", "membership"), ("fallback 0",), ("sidecar/diagnostic",)),
    "P05": (("CREATE_NEW 직전", "MoveFileW 직전", "두 cooperating writer"), ("실제 Windows", "경쟁 sentinel"), ("verified delta 0",), ("accepted",)),
    "P06": (("escape", "alias", "ancestor rename", "query failure"), ("root 밖 write/delete 0", "no delete sharing"), ("lease",), ("owner",)),
    "P07": (("open", "partial/zero write", "flush", "close", "promote", "foreign identity"), ("exact owned", "residual"), ("Commit/start delta 0",), ("diagnostic",)),
    "P08": (("short", "trailing", "tamper", "valid B Record"), ("expected bytes",), ("Commit/start delta 0",), ("metadata",)),
    "P09": (("stale Request/Goal/target",), ("owned pending",), ("actual Coordinator", "marker/verified delta 0"), ("accepted",)),
    "P10": (("promotion collision", "private start reject", "cleanup 실패"), ("residual raw final", "markerless reject"), ("actual private start", "verified delta 0"), ("accepted",)),
    "P11": (("actual start 이후", "marker fault"), ("raw final 보존",), ("start fact", "counter rollback 금지", "session blocked"), ("accepted",)),
    "P12": (("A/B ABA", "mixed", "invalid-first", "rebind"), ("Capture=1/marker=1", "동일 image",), ("stale lease", "미발행"), ("join",)),
    "P13": (("rehash", "metadata/build/group mismatch", "context join"), ("expected 전체 bytes", "rewrite 0"), ("lease",), ("group derivation", "sidecar/accepted 0")),
}


def read(name: str) -> str:
    return (CURRENT / name).read_text(encoding="utf-8")


def inert_mask(text: str) -> str:
    """길이/행을 보존하며 fenced 예제와 일반 HTML comment를 비활성화한다."""
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
    assert fence is None, "Contract has an unclosed fence"
    return re.sub(
        r"<!--(?! D:[a-z-]+ -->).*?-->",
        lambda match: re.sub(r"[^\r\n]", " ", match.group()),
        "".join(output), flags=re.DOTALL,
    )


def scopes(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^<!-- D:([a-z-]+) -->$", inert_mask(text), re.MULTILINE))
    assert tuple(match.group(1) for match in matches) == SCOPES, "Active storage scopes differ"
    return {
        match.group(1): text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        for index, match in enumerate(matches)
    }


def rule_line(identifier: str, body: str) -> str:
    return f"- **{identifier}**: {body}"


def check_rules(parts: dict[str, str]) -> None:
    for scope, rules in RULES.items():
        lines = inert_mask(parts[scope]).splitlines()
        found = [line for line in lines if re.match(r"^- \*\*D\d+\*\*:", line)]
        expected = [rule_line(identifier, body) for identifier, body in rules.items()]
        assert found == expected, f"Normative rules differ: {scope}"


def check_files(parts: dict[str, str]) -> None:
    for scope, expected in FILES.items():
        blocks = re.findall(r"^```text\n(.*?)^```$", parts[scope], re.MULTILINE | re.DOTALL)
        assert len(blocks) == 1, f"Required one exact allowlist: {scope}"
        paths = blocks[0].splitlines()
        assert len(paths) == len(set(paths)) and set(paths) == expected, f"Source allowlist differs: {scope}"


def check_matrix(parts: dict[str, str]) -> None:
    rows = table(parts["matrix"], ["ID", "입력·주입 시점", "2D lower oracle", "2D Host oracle", "후속 2E/3 경계"])
    assert [row[0] for row in rows] == list(MATRIX), "P01–P13 matrix identity/order differs"
    for row in rows:
        for column, clauses in enumerate(MATRIX[row[0]], start=1):
            assert all(clause in row[column] for clause in clauses), f"Matrix obligation differs: {row[0]} column {column}"


def check_document(text: str) -> None:
    parts = scopes(text)
    check_rules(parts)
    check_files(parts)
    assert table(parts["status"], ["단계", "현재 상태", "허용 주장"]) == STATUS, "Stage boundaries differ"
    assert table(parts["reservations"], ["stage", "허용 owned 이름", "반드시 부재할 이름"]) == RESERVATIONS, "Reservation state differs"
    assert table(parts["host-flow"], ["순서", "책임", "실패·성공 oracle"]) == FLOW, "Host order differs"
    check_matrix(parts)
    for literal in (
        "captures/<session UUID>/<episode UUID>/<20digit>.anpccap2",
        "scenario_capture_<session>_<episode>_<20digit>",
        "20자리 unsigned decimal",
    ):
        assert literal in inert_mask(parts["paths"]), f"Path/namespace differs: {literal}"
    for literal in (
        "ANPC_STORAGE_DOCUMENT_MODE=before-plan", "-B -m pytest", "no:cacheprovider",
        "--basetemp", "--junitxml", "AINativeNPC.Dataset.RecordV2",
        "AINativeNPC.Collection.Host", "AINativeNPC.Collection.Observation",
        "Saved/AINativeNPC/Capture/Phase3B", "900초", "null exit",
        "clean_or_forced_project_modules", "원본 preserved-source inventory",
    ):
        assert literal in parts["verification"], f"Execution handoff missing: {literal}"


def load_document(mode: str = "active") -> str:
    assert mode in {"active", "before-plan"}, "Unknown document test mode"
    path = CURRENT / STORAGE
    if mode == "before-plan" or not path.is_file():
        return read(BRIDGE) + "\n" + read(PLAN)
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def document() -> str:
    return load_document(os.environ.get("ANPC_STORAGE_DOCUMENT_MODE", "active"))


def test_active_storage_contract(document: str) -> None:
    check_document(document)


def test_missing_plan_is_normative_assertion_red() -> None:
    fallback = load_document("before-plan")
    assert fallback == read(BRIDGE) + "\n" + read(PLAN)
    with pytest.raises(AssertionError, match="Active storage scopes differ"):
        check_document(fallback)


@pytest.mark.parametrize("name", [BRIDGE, PLAN])
def test_entrypoints_link_active_storage_plan_and_bounded_approval(name: str) -> None:
    text = read(name)
    assert f"]({STORAGE})" in text
    assert "<!-- T2D:active -->" in text
    assert "Task2D 전체 완료는 lower test만으로 주장 금지" in text
    assert "독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만" in text
    assert "production collection closed" in text
    assert "독립 승인 대기로 구분한다" not in text
    assert "최신 bytes 재검증과 독립 SPEC→QUALITY는 아직 남아 있다" not in text


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("mutation", ["missing", "duplicate", "fenced", "tilde-fenced"])
def test_active_scopes_cannot_be_removed_or_supplied_by_example(document: str, scope: str, mutation: str) -> None:
    check_document(document)
    marker = f"<!-- D:{scope} -->"
    if mutation == "missing":
        changed = document.replace(marker, "", 1)
    elif mutation == "duplicate":
        changed = document + "\n" + marker + "\n"
    else:
        fence = "```" if mutation == "fenced" else "~~~"
        changed = document.replace(marker, f"{fence}text\n{marker}\n{fence}", 1)
    assert changed != document
    with pytest.raises(AssertionError, match="Active storage scopes differ"):
        check_document(changed)


RULE_CASES = [(scope, identifier, body) for scope, rules in RULES.items() for identifier, body in rules.items()]


@pytest.mark.parametrize("scope,identifier,body", RULE_CASES, ids=[case[1] for case in RULE_CASES])
@pytest.mark.parametrize("mutation", ["delete", "negate", "archive", "comment", "duplicate"])
def test_each_normative_rule_rejects_weakening(document: str, scope: str, identifier: str, body: str, mutation: str) -> None:
    check_document(document)
    line = rule_line(identifier, body)
    assert document.splitlines().count(line) == 1
    if mutation == "delete":
        replacement = ""
    elif mutation == "negate":
        replacement = line + " 이 규칙은 적용하지 않는다."
    elif mutation == "archive":
        replacement = "```text\n" + line + "\n```"
    elif mutation == "comment":
        replacement = "<!-- " + line + " -->"
    else:
        replacement = line + "\n" + line
    changed = document.replace(line, replacement, 1)
    assert changed != document
    with pytest.raises(AssertionError, match=f"Normative rules differ: {scope}"):
        check_document(changed)


@pytest.mark.parametrize("scope", FILES)
@pytest.mark.parametrize("mutation", ["extra", "missing", "duplicate"])
def test_exact_slice_allowlists_reject_scope_expansion(document: str, scope: str, mutation: str) -> None:
    check_document(document)
    part = scopes(document)[scope]
    path = sorted(FILES[scope])[0]
    replacement = path + "\nPolicy/DecisionCommitCoordinator.cpp" if mutation == "extra" else (
        "" if mutation == "missing" else path + "\n" + path
    )
    changed_part = part.replace(path, replacement, 1)
    changed = document.replace(part, changed_part, 1)
    assert changed != document
    with pytest.raises(AssertionError, match="Source allowlist differs"):
        check_document(changed)


@pytest.mark.parametrize("case", MATRIX)
def test_matrix_keeps_every_layer_obligation(document: str, case: str) -> None:
    check_document(document)
    part = scopes(document)["matrix"]
    line = next(line for line in part.splitlines() if line.startswith(f"| {case} |"))
    for column, clauses in enumerate(MATRIX[case], start=1):
        cells = line.split("|")
        cells[column + 1] = cells[column + 1].replace(clauses[0], "REMOVED")
        changed = document.replace(line, "|".join(cells), 1)
        assert changed != document
        with pytest.raises(AssertionError, match="Matrix obligation differs"):
            check_document(changed)


@pytest.mark.parametrize("key", ["status", "reservations", "host-flow", "matrix"])
@pytest.mark.parametrize("mutation", ["fenced", "missing-header", "split", "missing-row", "duplicate-row", "extra-column"])
def test_tables_require_active_complete_structure(document: str, key: str, mutation: str) -> None:
    check_document(document)
    part = scopes(document)[key]
    lines = part.splitlines(keepends=True)
    indices = [index for index, line in enumerate(lines) if line.startswith("|")]
    start, stop = indices[0], indices[-1] + 1
    block = lines[start:stop]
    if mutation == "fenced":
        changed_block = ["```text\n", *block, "```\n"]
    elif mutation == "missing-header":
        changed_block = block[1:]
    elif mutation == "split":
        changed_block = [*block[:2], "\n", *block[2:]]
    elif mutation == "missing-row":
        changed_block = block[:-1]
    elif mutation == "duplicate-row":
        changed_block = [*block, block[-1]]
    else:
        changed_block = [*block[:-1], block[-1].rstrip("\n") + " extra |\n"]
    changed_part = "".join([*lines[:start], *changed_block, *lines[stop:]])
    changed = document.replace(part, changed_part, 1)
    assert changed != document
    with pytest.raises(AssertionError):
        check_document(changed)


@pytest.mark.parametrize("old,new", [
    ("final,final.tmp,final.pending,final.pending.tmp,final.committed,final.committed.tmp", "final,final.pending,final.committed"),
    ("lower 이후 후속", "lower PASS로 전체 완료"),
    ("actual Coordinator(final promotion/private start)", "mock authority success"),
    ("captures/<session UUID>/<episode UUID>/<20digit>.anpccap2", "captures/<DecisionId>.anpccap2"),
    ("scenario_capture_<session>_<episode>_<20digit>", "scenario_capture_<DecisionId>"),
])
def test_named_shortcuts_are_rejected(document: str, old: str, new: str) -> None:
    check_document(document)
    assert old in document
    changed = document.replace(old, new)
    with pytest.raises(AssertionError):
        check_document(changed)


def test_host_order_rejects_marker_before_actual_start(document: str) -> None:
    check_document(document)
    part = scopes(document)["host-flow"]
    lines = part.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("| actual Coordinator("))
    marker = next(index for index, line in enumerate(lines) if line.startswith("| marker |"))
    lines[start], lines[marker] = lines[marker], lines[start]
    changed = document.replace(part, "\n".join(lines) + "\n", 1)
    with pytest.raises(AssertionError, match="Host order differs"):
        check_document(changed)
