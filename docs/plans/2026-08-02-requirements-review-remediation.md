# AI Native NPC 요구사항 검토 반영 Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** v0.4.6 요구사항 검토 결과를 저장소의 감사 가능한 문서로 남기고, 발견된 P0/P1/P2 계약 결함을 요구사항 기준서에 반영한다.

**Architecture:** 검토 기록과 규범 요구사항을 분리한다. 검토 문서는 발견 근거·영향·판정·수정 상태를 보존하고, 요구사항 기준서는 해결된 규칙만 규범 문장과 machine-readable 계약 변경 요구로 반영한다. 현재 `main`의 YAML·생성 코드는 RC5 고정 산출물이므로 이번 작업에서 수동 수정하지 않고, Schema/Registry 변경이 필요한 항목은 다음 계약 재생성 릴리스의 명시적 작업과 Freeze Gate로 기록한다.

**Tech Stack:** Markdown, YAML 계약 참조, Git diff, Python 기반 정적 교차검증

---

## 적용·집행 경계

| 산출물 | 독자 | 적용 Runtime | 집행 방식 |
|---|---|---|---|
| 검토 문서 | Gameplay AI, ML, Server, QA, Technical Designer, 승인자 | 직접 Runtime 적용 없음 | 변경 리뷰와 Freeze 승인 시 수동 감사 입력 |
| 요구사항 기준서 | Unreal Runtime, Python 학습/평가, Model Bundle 빌더 | Server Game Thread, ML pipeline, ONNX/NNE | 차기 Schema/Registry Generator·Validator·Golden·Runtime Gate에서 구현 |
| 현재 YAML/Generated | Runtime/학습 코드 | 기존 RC5 계약 | 이번 작업에서는 불변; 후속 계약 버전에서 재생성 |

이 Markdown 수정 자체는 Runtime enforcement가 아니다. 규칙을 실제로 강제하려면 Schema/Registry 변경, 생성 코드 재생성, Dataset Validator, Model Bundle Validator, Unreal descriptor validation, Runtime Commit Gate 및 CI가 후속 릴리스에서 구현되어야 한다.

---

### Task 1: 검토 결과 문서화

**Objective:** 이전 검토의 증거, 심각도, 수정 권고와 검증 범위를 독립 Markdown 문서로 보존한다.

**Files:**
- Create: `docs/current/reviews/ai_native_npc_requirements_review_v0.4.6.md`

**Steps:**
1. 검토 대상 commit/SHA와 실행한 검증 명령을 기록한다.
2. P0/P1/P2 finding을 `근거 → 영향 → 요구 변경` 구조로 기록한다.
3. 기존 Harness PASS와 Runtime pending을 분리한다.
4. 각 규칙의 reader/runtime/enforcement를 표로 기록한다.

**Verification:**
```bash
git diff --check -- docs/current/reviews/ai_native_npc_requirements_review_v0.4.6.md
```
Expected: 출력 없음, exit 0.

---

### Task 2: 요구사항 상태와 변경 범위 명확화

**Objective:** 기존 RC5 Harness와 새 ML/NNE Supplement의 검증 상태를 구분하고 이번 보강의 변경 필요성을 선언한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. 문서 상태에 Review Remediation Supplement를 추가한다.
2. Phase 0 착수 가능, V1 학습/Freeze 차단 항목을 분리한다.
3. 새 규범 항목이 기존 90파일 Lock 증거에 포함되지 않는다는 사실을 유지한다.

**Verification:** 문서 상단 판정과 최종 체크리스트가 같은 상태를 표현해야 한다.

---

### Task 3: Runtime·Goal 계약 수정

**Objective:** OOD Tensor, Goal arbitration/trigger, snapshot staleness, target equality, mandatory selection 규칙을 구현 가능한 수준으로 고정한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. ONNX 세 번째 출력 `tactical_context [B,128]` 요구와 Schema patch 필요성을 추가한다.
2. `preemption_margin`, quantized creation time, suspended resume, revision 조건을 명시한다.
3. Goal trigger를 Event/Timer/Lifecycle로 구분하고 timeout duration Registry 요구를 추가한다.
4. `latest_snapshot_revision`의 Commit invalidation 정책과 실패 코드를 추가한다.
5. `target_changed` 및 Continue equality를 `IdentityKey`로 고정한다.
6. Mandatory source 내부 canonical key와 현재 overflow 불변식을 명시한다.

**Verification:** 본문에서 `preemption_margin`, `created_time_quantized_ms`, `tactical_context`, `SnapshotSuperseded`, typed trigger 규칙을 검색해 모두 존재해야 한다.

---

### Task 4: ML·Dataset·Calibration 계약 수정

**Objective:** 학습과 Runtime post-process의 재현성, Dataset identity, split catalog, Calibration/OOD 통계 계약을 닫는다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. Dataset Record에 Switch Cost component를 추가한다.
2. `feature_contract_hash`, `source_decision_contract_hash`, `input_content_hash`, `sample_id` 역할을 분리한다.
3. Tensor/label canonical serialization을 명시한다.
4. OOD/Critical 실제 case allowlist catalog를 요구한다.
5. Calibration threshold의 최소 accepted count, coverage, one-sided risk CI를 정의한다.
6. OOD KPI를 Runtime threshold 0.80에 결속한다.
7. Model Bundle manifest self-hash를 금지하고 `model_sha256 = SHA256(policy.onnx)`로 고정한다.

**Verification:** Dataset 필드와 Loss Contract가 같은 Switch Cost 입력을 사용하고, manifest가 자기 자신을 hash하지 않아야 한다.

---

### Task 5: KPI·프로젝트·문서 품질 수정

**Objective:** 자명한 Gate, 모호한 Recall 분모, 잘못된 Appendix 참조를 정리하고 generated 번호 결함은 원본·Generator remediation으로 추적한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. `MandatoryOverflow`를 현재 V1 unreachable Runtime invariant와 malformed-cap negative mutation test로 분리한다.
2. Target/Candidate Recall의 trial·분모·aggregation·CI 단위를 정의한다.
3. `source_moving_probability` 타입 변경 요구를 기록한다.
4. 프로젝트 의존성 참조는 수정하되 Auto-generated Appendix D 번호는 수동 편집하지 않고 `DOC-GENERATOR-001` backlog로 기록한다.
5. 최종 승인 체크리스트에 새 차단 Gate를 추가한다.

**Verification:** `Goal Appendix B` 참조가 없어야 한다. Generated marker block은 HEAD와 byte-identical해야 하며, 중복 `D.3`은 `DOC-GENERATOR-001`로 추적되어야 한다.

---

### Task 6: 교차검증과 최종 diff 검토

**Objective:** 문서 편집 오류와 기존 고정 산출물의 우발적 변경을 차단한다.

**Files:**
- Verify only: repository diff

**Steps:**
1. `git status --short`로 작업 소유 파일을 확인한다.
2. `git diff --check`를 실행한다.
3. Markdown heading, code fence, marker block 쌍을 검사한다.
4. YAML 4개와 generated 2개가 수정되지 않았는지 확인한다.
5. 기존 Requirements/UE/Schema/Registry SHA 관계를 보고한다. Requirements 변경으로 UE 문서의 상위 기준서 SHA가 stale해지는 경우 이를 차단 이슈로 처리하고 해당 SHA를 갱신한다.
6. commit/push는 수행하지 않는다.

**Verification:**
```bash
git diff --check
git status --short
```
Expected: whitespace error 없음; 변경 파일은 계획, 검토 문서, Requirements 및 필요한 UE SHA metadata로 제한된다.
