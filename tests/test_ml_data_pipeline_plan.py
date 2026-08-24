from pathlib import Path


ROOT = Path(__file__).parents[1]
CURRENT = ROOT / "docs" / "current"


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
    assert "독립 hostile review에서" in text


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
    assert "Teacher Silver로 채택" in implementation
    assert "`--require-production`에서 거부" in implementation
    assert "Production Resolve v1 | Core 완료, rollout HOLD" in requirements
    assert "Procedural·Teacher Dataset | candidate 완료" in requirements
    assert "Schema 2.0.0 RC6" in technical
    assert "`Approved=false`, `ResolvePolicyReady=false`" in technical
    assert "production 경로는 dormant" in unreal
    assert "Contract·promotion test: 89개와 subtest 133개 통과" in production
    assert "ML candidate: 7개 Snapshot × 5회 Provider 판정" in production
    assert "구현은 시작하지 않음" not in requirements
    assert "Schema 2.0.0 RC5" not in technical
    assert "RC5 2-output Neural 연결" not in technical


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
    assert "7개 Snapshot × 5회 = 35회" in text
    assert "Teacher Silver 6개" in text
    assert "Gold review 1개" in text
    assert "low identity confidence" in text
    assert "production Provider 승인 근거가 아니다" in text
    assert "ML Python suite: **33 passed**" in text
    assert "Contract repository: **89 passed, 133 subtests passed**" in text
    assert "두 `production_candidate` shard를 Production Dataset으로 거부" in text
    assert "예제 Profile과 smoke Dataset은 `integration_fixture`와 `production_candidate` 범위" in text
    assert "Repository에는 작은 `integration_fixture` Profile과 별도 `production_candidate` Profile을 둔다." in text
    assert "현재 Generator는 `integration_fixture`만 실행" not in text
    assert "Repository에는 작은 `integration_fixture` Profile만 둔다." not in text
