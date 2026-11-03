"""Development Game 대상 보정의 추가 문서 coverage. 행동 RED/Unreal 증거가 아니다."""
from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from test_collection_play_session_index_document import active, check_document, load_document

ROOT = Path(__file__).resolve().parents[1]
HEADING = "### 12.4 별도 Development Game의 최종 수집 통합"
CLAUSES = (
    "- **DG01:** 최종 대상은 기존 Target=NeuralGame, Win64/x64/Development/Game이다. `UnrealEditor.exe -game`과 새 Game target 생성을 채택하지 않는다. 기존 Editor/Host Automation은 lower regression이며 최종 수집통합은 별도 Development Game에서 확인한다.",
    "- **DG02:** PS01–PS25의 Console 3개·기본값·limits·PS13–PS14 drain·native publication·index·World identity 계약을 유지한다. 자동 Game 입력은 automated_runtime/automatic/automated다. human_play/manual/human은 실제 사용자 입력과 피드백으로 별도 확인한다.",
    "- **DG03:** read-only Game planner는 actual receipt·uproject·모든 project-local uplugin descriptor·현재 Target.cs/Build.cs bytes를 고정 입력으로 받는다. 현재 receipt는 stale build여도 계획의 actual input이다. 최신 기능 build 성공은 별도 forced compile/link 증거를 요구한다.",
    "- **DG04:** 현재 지원 범위는 단일 논리 project module NeuralGame이 기본 monolithic EXE에 결합되는 닫힌 source 형태다. module_descriptor{module_name,base,path,size_bytes,sha256}에 실제 EXE를 한 행으로 표현한다. 같은 EXE의 중복 path rows·빈 목록·DLL 위장은 거부한다. descriptor eligibility에서 예상 집합을 먼저 정하며 실제 observed module 누락에 맞춰 줄이지 않는다.",
    "- **DG05:** 현재 GameDevMCPPlugin의 UnrealMCPEditor는 Editor module이므로 Game compile/runtime 대상에서 제외한다. 제외를 결정한 descriptor도 inventory/pin에 포함한다. Editor 전용 MCP를 Game runtime 제어에 사용한다고 가정하지 않는다. 새 runtime RPC/원격 bridge를 추가하지 않는다.",
    "- **DG06:** HotReload와 LiveCoding은 별도 검증이다. WITH_HOT_RELOAD 기본식과 실제 Game build definitions/link를 대조한다. bWithLiveCoding/-NoLiveCoding의 RequiresUniqueBuildEnvironment를 우회하지 않는다. supported session query/disable API와 연속 현재성 관측의 미확인 성공 조건은 pending으로 남긴다.",
    "- **DG07:** GameInstance early-init 이후 bootstrap rendezvous, 상속 native pipe protocol, private automation adapter를 연결한다. 현재 N1은 raw file/pipe IO만이며 전체 bootstrap authority가 아니다. startup만으로 gameplay 성공을 주장하지 않는다.",
    "- **DG08:** 최종 증거는 forced Game compile/link action coverage → 선택 MVP asset dependency cook/staging → 새 Game PID/creation/EXE/loaded inventory → Start→NewEpisode→Stop→terminal/index readback이다. original Content/Saved는 보존하며 source/build/cook/startup/수집/재읽기 결과를 각각 기록한다.",
    '- **DG09:** 사용자 승인으로 NeuralGame.Build.cs에 `if (Target.bWithLiveCoding)` 조건의 `PrivateIncludePathModuleNames.Add("LiveCoding")` 한 항목을 허용한다. planner는 기존 형태와 이 정확한 successor 형태만 허용하며 추가 의존성·macro·Target 변경은 거부한다. public header의 실제 compile로 소비를 확인한다. 이는 설정 보완이며 runtime disabled/currentness나 일반 플레이 수집 성공 증거가 아니다.',
)


def check_game_scope(text: str) -> None:
    check_document(text)  # 동결된 기존 PS/table oracle를 그대로 호출한다.
    visible = active(text)
    assert visible.splitlines().count(HEADING) == 1, "Missing/duplicate Development Game section"
    section = visible.split(HEADING, 1)[1]
    found = tuple(line for line in section.splitlines() if line.startswith("- **DG"))
    assert found == CLAUSES, "Development Game clauses differ"
    assert tuple(line for line in visible.splitlines() if line.startswith("- **DG")) == CLAUSES
    for token in (
        "development-game-path-decision-01.md", "development-game-launch-slice-01.md",
        "development-game-plan-red-handoff-01.md", "runtime-inputs-launcher-design-01.md",
        "supersede", "초기 PASS는 추가 문서 coverage이지 behavioral RED가 아니다",
        "원본 기록은 수정하거나 삭제하지 않는다", "실제 Python RED", "return None",
    ):
        assert token in section, "Missing Game scope detail: " + token
    assert "Engine·Target.cs·Build.cs·plugin·Content·Config 편집 권한을 추가하지 않는다" in visible
    assert "이 한정 예외가 PS04와 위 실행 대상 보정의 Build.cs 보존 범위에 우선한다" in visible
    assert "과거 PIE 증거를 Development Game 수집 통합 증거로 승격하지 않는다" in visible


def test_active_development_game_scope() -> None:
    check_game_scope(load_document())


@pytest.mark.parametrize("clause", CLAUSES, ids=["DG01", "DG02", "DG03", "DG04", "DG05", "DG06", "DG07", "DG08", "DG09"])
@pytest.mark.parametrize("mutation", ["delete", "weaken", "fence", "comment", "duplicate", "relocate"])
def test_game_scope_mutation_requires_positive_control(clause: str, mutation: str) -> None:
    original = load_document()
    check_game_scope(original)
    replacement = {
        "delete": "", "weaken": clause + " 선택 사항이다.",
        "fence": "```text\n" + clause + "\n```", "comment": "<!-- " + clause + " -->",
        "duplicate": clause + "\n" + clause, "relocate": "",
    }[mutation]
    changed = original.replace(clause, replacement, 1)
    if mutation == "relocate":
        changed = changed.replace(HEADING, clause + "\n\n" + HEADING, 1)
    assert changed != original
    with pytest.raises(AssertionError, match="Development Game clauses differ"):
        check_game_scope(changed)


def test_current_module_descriptor_has_no_dll_only_constraint() -> None:
    """Schema 구조 coverage만 수행한다. EXE가 실제 빌드/로드됐다고 판정하지 않는다."""
    defs = json.loads((ROOT / "contracts/current/capture_import_provenance_v1.schema.json").read_bytes())["$defs"]
    descriptor = defs["module_descriptor"]
    assert descriptor["additionalProperties"] is False
    assert set(descriptor["required"]) == set(descriptor["properties"]) == {
        "module_name", "base", "path", "size_bytes", "sha256"}
    assert descriptor["properties"]["base"] == {"const": "project_root"}
    assert descriptor["properties"]["path"] == {"$ref": "#/$defs/relative_path"}
    assert re.fullmatch(defs["relative_path"]["pattern"], "Binaries/Win64/NeuralGame.exe")
    for kind, field in (("runtime_build_evidence", "module_artifacts"),
                        ("session_start_evidence", "loaded_module_inventory")):
        entry = defs[kind]["properties"][field]
        assert entry["minItems"] == 1 and entry["items"] == {"$ref": "#/$defs/module_descriptor"}
        assert defs[kind]["additionalProperties"] is False
