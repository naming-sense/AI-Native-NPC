import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
CURRENT = ROOT / "docs" / "current"
HISTORY = ROOT / "docs" / "history" / "ml-data-pipeline-v1-history-2026-10-28.md"


def test_ml_plan_opens_with_reader_guide_and_scoped_current_status() -> None:
    text = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")
    opening = text.split('<a id="implementation-reference"></a>', 1)[0]
    assert text.startswith("# 학습 데이터 생성·수집 계획\n")
    for heading in (
        "## 1. 목표와 읽는 순서",
        "## 2. 먼저 알아둘 용어",
        "## 3. 완료된 일과 남은 일",
        "## 4. 데이터가 만들어지는 과정",
        "## 5. 학습용 시나리오 실행·수집 도구",
        "## 6. 다음 작업과 완료 조건",
    ):
        assert heading in opening
    assert opening.index("## 2.") < opening.index("## 3.")
    assert "Task 2D" in opening and "저장·읽기와 NPC 실행 연결" in opening
    assert "선택 화면·자동 실행·회차 초기화" in opening
    assert "일반 플레이 수집 활성화는 남아 있다" in opening
    assert "Schema `2.0.0-rc6`" not in opening
    assert "47 passed" not in opening and "167/167" not in opening
    assert "duration = clamp" not in opening
    assert text.count('<a id="scenario-collection-plan"></a>') == 1
    assert text.count("<details>") == text.count("</details>") >= 3


def test_ml_plan_history_preserves_previous_execution_claims() -> None:
    text = HISTORY.read_text(encoding="utf-8")
    assert "현재 구현 기준은" in text
    for phrase in (
        "독립 hostile review에서",
        "7개 Snapshot × 5회 = 35회", "Teacher Silver 6개", "Gold review 1개",
        "`AINativeNPC.Shipping.GeneralNPC` 21/21", "전체 `AINativeNPC` 167/167",
        "committed Phase 3B hearing Capture 세 개", "`ResolveShadow` Capture는 0개",
        "`TargetSlotter`",
        "exact matching Knowledge Candidate를 in-place Goal Primary Target으로 승격",
        "실제 Play를 다시 수집한다",
        "ML Python suite: **47 passed**",
        "Contract repository: **89 passed, 133 subtests passed**",
        "두 `production_candidate` shard를 Production Dataset으로 거부",
    ):
        assert phrase in text
    current = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")
    assert "../history/ml-data-pipeline-v1-history-2026-10-28.md" in current


def test_ml_data_pipeline_plan_bounds_fixture_and_production_scope() -> None:
    text = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")

    assert "Schema `2.0.0-rc6`" in text
    assert "Skill Registry `1.1.0`" in text
    assert "Goal Registry `1.2.0`" in text
    assert "`integration_fixture`" in text
    assert "production 학습·promotion authority가 아니다" in text
    assert "Teacher는 parameter label을 만들지 않는다" in text
    assert "production scenario family" in text.lower()
    assert "Candidate canonical bytes를 구조적으로 decode" in text
    assert "raw provider payload 5개의 path·hash·response를 재검증" in text
    assert "`source_weight`는 `silver=0.25`" in text


def test_main_implementation_plan_delegates_pipeline_contract() -> None:
    text = (CURRENT / "implementation-plan.md").read_text(encoding="utf-8")

    assert "[Procedural Generator와 Teacher Pipeline v1 구현 계획](ml-data-pipeline-v1-implementation-plan.md)" in text
    assert "Greet `production_candidate`는 사용자 승인 권장 기본값과 parameter label 공식을 실행하지만 heuristic Silver에 한정한다." in text
    assert "Production scenario family는 Gold와 Unreal Capture 분포 비교 전까지 열지 않는다." in text
    assert "절차 생성기의 scenario family, 값 추출 범위, heuristic label 계산식과 실행 CLI는 후속 상세 설계 항목이다." not in text
    assert "현재 실제 `ML/` 코드, 학습 Dataset, Teacher Profile과 학습 모델은 없다." not in text
    assert "uv run python -m anpc_ml teacher generate" in text
    assert "uv run python -m anpc_ml dataset validate --input" in text
    assert "현재 `NeuralGame`에는 `ML/` 디렉터리" not in text


def test_current_docs_report_candidate_progress_and_keep_production_dormant() -> None:
    implementation = (CURRENT / "implementation-plan.md").read_text(encoding="utf-8")
    requirements = (CURRENT / "requirements.md").read_text(encoding="utf-8")
    technical = (CURRENT / "technical-requirements.md").read_text(encoding="utf-8")
    unreal = (CURRENT / "unreal-implementation-plan.md").read_text(encoding="utf-8")
    production = (CURRENT / "production-resolve-v1-implementation-plan.md").read_text(encoding="utf-8")

    assert "## 2026-08-23 진행 요약" in implementation
    assert "총 35회 호출" in implementation
    assert "Teacher Silver로 유지" in implementation
    assert "Human Gold로 확정" in implementation
    assert "`--require-production`에서 거부" in implementation
    assert "Production Resolve v1 | Core 완료, rollout HOLD" in requirements
    assert "Procedural·Teacher·Human Gold Dataset | candidate 완료" in requirements
    assert "Schema 2.0.0 RC6" in technical
    assert "`Approved=false`, `ResolvePolicyReady=false`" in technical
    assert "production 경로는 dormant" in unreal
    assert "Contract·promotion test: 89개와 subtest 133개 통과" in production
    assert "ML candidate: 7개 Snapshot × 5회 Provider 판정" in production
    assert "구현은 시작하지 않음" not in requirements
    assert "Schema 2.0.0 RC5" not in technical
    assert "RC5 2-output Neural 연결" not in technical


def test_production_plan_separates_completed_gold_persistence_from_qualification() -> None:
    text = (CURRENT / "production-resolve-v1-implementation-plan.md").read_text(encoding="utf-8")
    completed = text.split("### 10.2 현재 검증된 범위", 1)[1].split("### 10.3 남은 production Gate", 1)[0]
    remaining = text.split("### 10.3 남은 production Gate", 1)[1]

    assert "Human Gold 1-row persistence 검증 완료" in completed
    assert "candidate 저장 증거" in completed
    assert "production Dataset·Provider 승인 근거가 아니다" in completed
    assert "low-identity Human Gold 1-row persistence 검증과" not in remaining
    assert "immutable Provider revision 기반 전체 Gold qualification" in remaining
    assert "12개 Role×Goal group마다 100개 이상, 총 1,200개 이상" in remaining
    assert "ResolvePolicyReady=false" in remaining


def test_ml_plan_defines_greet_production_candidate_and_provider_qualification() -> None:
    text = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")

    assert "GuardPhase0/InvestigateDisturbance/Resolve" in text
    assert "Greet(Entity)" in text
    assert "production_candidate" in text
    assert "production 학습 authority가 아니다" in text
    assert "exact model identifier와 revision" in text
    assert "12개 Role×Goal group마다 Gold sample 100개 이상" in text
    assert "strict response valid rate ≥95%" in text
    assert "Any-Acceptable Recall ≥95%" in text
    assert "acceptable-set Jaccard ≥0.80" in text
    assert "hard-invalid candidate 선택 0건" in text
    assert "replay_fixture" in text
    assert "command" in text
    assert "hostility ≤ 0.35" in text
    assert "identity_confidence ≥ 0.80" in text
    assert "duration = clamp(1.0, 5.0, 1.0 + 0.60 × affinity + 0.40 × sociability - 0.30 × hostility)" in text
    assert "intensity = clamp(0.0, 1.0, 0.20 + 0.35 × sociability + 0.30 × affinity + 0.15 × trust - 0.40 × hostility)" in text
    assert "7개 anchor" in text
    assert "low identity confidence" in text
    assert "신원 확신이 낮으면 인사하지 않음" in text
    assert "source_type=gold" in text
    assert "source_weight=1.0" in text
    assert "같은 immutable byte image를 hash·parse·join" in text
    assert "한 번 읽은 Parquet bytes" in text
    assert "anpc_ml gold promote" in text
    assert "anpc_ml gold map" in text
    assert "audit_production_readiness.py" in text
    assert "manifest directory 아래의 상대 경로만 허용" in text
    assert "`sha256:<64 lowercase hex>`" in text
    assert "실제 Parquet에서 다시 계산한 denominator" in text
    assert "ML/teacher/candidates/production_resolve_v1_candidate/" in text
    assert "-AINativeNPCResolveCaptureOnly" in text
    assert "Neural evaluator를 반드시 `nullptr`" in text
    assert "`Dagger` weak label" in text
    assert "ResolveShadow/<session-id>" in text
    assert "process-wide monotonic sequence" in text
    assert "기존 committed Capture를 지우지 않고" in text
    assert "production Provider 승인 근거가 아니다" in text
    assert "예제 Profile과 smoke Dataset은 `integration_fixture`와 `production_candidate` 범위" in text
    assert "Repository에는 작은 `integration_fixture` Profile과 별도 `production_candidate` Profile을 둔다." in text
    assert "현재 Generator는 `integration_fixture`만 실행" not in text
    assert "Repository에는 작은 `integration_fixture` Profile만 둔다." not in text


def _collection_plan() -> str:
    text = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")
    anchor = '<a id="scenario-collection-plan"></a>'
    assert anchor in text, "학습용 시나리오 실행·수집 계획이 필요하다"
    return text.split(anchor, 1)[1].split('<a id="implementation-reference"></a>', 1)[0]


def _runtime_collection_reference() -> str:
    text = (CURRENT / "ml-data-pipeline-v1-implementation-plan.md").read_text(encoding="utf-8")
    return text.split('<a id="runtime-collection-contract"></a>', 1)[1].split(
        '<a id="implementation-files-and-checks"></a>', 1
    )[0]


def test_collection_definition_keeps_family_goal_and_phase_required() -> None:
    definition = _collection_plan().split("### 5.2", 1)[1].split("### 5.3", 1)[0]
    for field in ("scenario family", "`Goal`", "`phase`"):
        assert field in definition


def test_collection_approved_limits_are_pinned_in_execution_profile() -> None:
    coverage = _collection_plan().split("### 5.5", 1)[1].split("## 6.", 1)[0]
    assert "허용 조합·비율·수집 예산과 중단 기준" in coverage
    assert "수집 설정(`Profile`)에 고정한다" in coverage


def test_collection_terminology_distinguishes_state_scenario_and_episode() -> None:
    text = (CURRENT / "technical-requirements.md").read_text(encoding="utf-8")
    assert '<a id="collection-terminology"></a>' in text
    for term in ("상황", "시나리오", "변형 사례", "실행 회차", "scenario_family_id"):
        assert term in text
    assert "한 번 판단하는 시점의 상태" in text
    assert "초기 조건과 사건의 진행 순서" in text
    assert "시나리오 한 회차에서 여러 판단 상황" in text


def test_collection_plan_assigns_bulk_work_to_automation_and_bounds_human_play() -> None:
    text = _collection_plan()
    for phrase in (
        "AI 개발 에이전트", "Gameplay/Data owner", "생성·실행 도구",
        "대표 사례", "정답 검토",
        "구현 전", "수집 출처", "라벨 출처",
    ):
        assert phrase in text
    assert "자동 실행을 사람 플레이 분포로 집계하지 않는다" in text
    reference = _runtime_collection_reference()
    assert "Play 7회" in reference and "학습량 기준" in reference


def test_collection_plan_defines_shared_modes_and_runtime_boundary() -> None:
    text = _collection_plan()
    for phrase in (
        "시나리오 선택", "직접 플레이", "자동 수집", "같은 조건 재실행",
        "같은 시나리오 정의",
        "최대 회차", "회차 시간 제한", "중단", "초기화",
        "process-wide monotonic sequence", "byte-identical", "미지원",
    ):
        assert phrase in text
    reference = _runtime_collection_reference()
    for phrase in ("Perception", "Knowledge", "Commit", "Tensor나 Knowledge 결과를 직접 주입"):
        assert phrase in reference


def test_collection_plan_preserves_failed_and_uncommitted_observations_separately() -> None:
    text = _collection_plan()
    for phrase in (
        "인사하지 않음", "대상 상실", "판단 실패", "진단 기록",
        ".anpccap2", ".committed", "유효 학습 항목", "수집 출처와 라벨 출처",
    ):
        assert phrase in text
    assert "실패·미확정 기록은 실행 확정 기록으로 취급하지 않는다" in text
    assert "source_type" in text and "Schema" in text
    reference = _runtime_collection_reference()
    for phrase in (
        "유효 학습 row", "Utility 선택을 정답으로 복사하지 않는다", "Dagger", "Gold",
        "실패·미확정 기록을 committed Capture로 위장하지 않는다",
    ):
        assert phrase in reference


def test_collection_plan_requires_coverage_split_and_closed_readiness() -> None:
    text = _collection_plan()
    for phrase in (
        "고유 입력", "근접 중복", "조건별", "scenario_family_id",
        "Train", "Validation", "Calibration", "Test", "OOD", "Critical",
        "문서·하네스", "검증",
    ):
        assert phrase in text
    reference = _runtime_collection_reference()
    for phrase in ("Approved=false", "ResolvePolicyReady=false", "production_eligible=false", "Snapshot"):
        assert phrase in reference


def test_collection_plan_is_discoverable_from_active_reader_entrypoints() -> None:
    link = "ml-data-pipeline-v1-implementation-plan.md#scenario-collection-plan"
    for name in (
        "requirements.md", "technical-requirements.md", "implementation-plan.md",
        "unreal-implementation-plan.md",
    ):
        text = (CURRENT / name).read_text(encoding="utf-8")
        assert link in text, name
        assert "시나리오" in text, name
    assert "docs/current/" + link in (ROOT / "README.md").read_text(encoding="utf-8")


def test_unreal_plan_pins_current_reader_and_technical_requirements() -> None:
    text = (CURRENT / "unreal-implementation-plan.md").read_text(encoding="utf-8")
    for label, name in (
        ("Requirements", "requirements.md"),
        ("Technical Requirements", "technical-requirements.md"),
    ):
        pattern = rf"^\| {re.escape(label)} SHA-256 \| `([0-9a-f]{{64}})` \|$"
        match = re.search(pattern, text, re.MULTILINE)
        assert match is not None, label
        assert match.group(1) == hashlib.sha256((CURRENT / name).read_bytes()).hexdigest(), name
