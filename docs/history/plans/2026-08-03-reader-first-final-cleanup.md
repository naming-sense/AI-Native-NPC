# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# AI Native NPC 독자 중심 최종 정리 Implementation Plan

> **For Hermes:** 이 계획을 순서대로 실행하고 generated marker 내부는 보관 Generator 결과로만 갱신한다.

**Goal:** Implementation Plan의 실행 순서를 먼저 제시하고, Requirements의 생성 ID 중복과 긴 복합 문장을 줄이며, generated Appendix D 번호를 연속적으로 만든다.

**Architecture:**

- Requirements는 의미·행동·권한을 소유한다.
- Contract Appendices는 정확한 ID를 단독 소유한다.
- Implementation Plan은 Phase·Owner·완료 조건을 모델 Layer보다 먼저 제공한다.
- Appendix D는 `archive/full-harness-v0.4.6`의 Generator에서 재생성한다. Marker는 직접 편집하지 않는다.

**Tech Stack:** Markdown, YAML 계약, Python Generator, Git worktree, SHA-256, Python/C++ Golden parity

---

## 적용·집행 경계

| 산출물 | 독자 | 적용 위치 | 집행 방식 |
|---|---|---|---|
| Requirements | Gameplay AI, ML, Server, QA | 설계·구현·검토 | 의미·권한 규칙과 Appendix 링크 |
| Implementation Plan | 구현 Owner, 승인자 | Phase 계획·실행 | Phase→Workstream→세부 구현 순서 |
| Contract Appendices | Runtime·ML 구현자 | 정확한 ID·Hash 참조 | Generator 출력과 marker parity |
| 보관 Generator | 계약 관리자 | 문서·코드 재생성 | `generate_contracts.py --check`, Golden parity |

## 요구사항

1. Implementation Plan은 Phase·Owner·작업 범위를 모델 Layer보다 먼저 보여야 한다.
2. 장 번호는 문서 순서대로 연속이어야 하며 모든 교차 참조와 heading fragment를 갱신해야 한다.
3. Requirements는 Target Kind와 Skill의 의미를 설명하되 숫자 ID를 복제하지 않아야 한다.
4. 정확한 ID는 Contract Appendices의 generated 표가 단독 소유해야 한다.
5. 180자 이상인 비표·비코드 문장은 한 문장 한 규칙 원칙으로 검토한다.
6. 안전 금지, stale reject, hard mask, hash byte 계약 등 규범적 제한은 유지한다.
7. Appendix D의 Hash subsection은 `D.3`, `D.4`로 연속 번호를 사용하고 Normalizer는 `D.5`를 사용해야 한다.
8. generated marker는 수정된 보관 Generator의 출력과 byte-identical이어야 한다.
9. 마지막 Requirements 편집 후 SHA-256을 계산하고 UE binding을 갱신해야 한다.
10. 최종 검증은 마지막 metadata 편집 이후 실행해야 한다.

---

### Task 1: Implementation Plan 실행 순서 재배치

**Objective:** Phase·Owner·작업 범위를 모델 세부보다 먼저 제시한다.

**Files:**
- Modify: `docs/current/implementation/ai_native_npc_implementation_plan_v0.4.6.md`
- Modify: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md`
- Modify: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md`

**Steps:**
1. 기존 §7을 §2로 이동한다.
2. 기존 §2~§6을 §3~§7로 renumber한다.
3. 문서 내부와 companion 문서의 `§N` 참조·fragment를 갱신한다.
4. heading 순서와 link fragment를 검사한다.

### Task 2: Requirements generated ID 중복 제거

**Objective:** 의미 설명은 Requirements에, 숫자 ID는 Appendices에 한 번만 둔다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md`

**Steps:**
1. Target Kind ID 표를 의미 중심 Target Kind 표로 바꾸고 Appendix A 직접 링크를 추가한다.
2. Skill ID 숫자 표를 제거하고 Skill Registry generated 표 링크를 추가한다.
3. Candidate 허용표와 행동 의미는 유지한다.
4. Requirements에 생성 ID 숫자 표가 남지 않았는지 검사한다.

### Task 3: 긴 복합 문장 정리

**Objective:** 규범 의미를 유지하면서 한 문장에 섞인 조건·동작·실패 결과를 분리한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md`

**Steps:**
1. 비표·비코드 180자 이상 문장을 추출한다.
2. 설명 문장은 직접형 단문으로 나눈다.
3. 여러 조건을 가진 규칙은 bullet 또는 `조건 / 동작 / 실패 결과` 표로 바꾼다.
4. 안전·hidden information·stale·hash 제한을 재검토한다.

### Task 4: Appendix D 번호 Generator 수정

**Objective:** generated Appendix D heading을 `D.3`, `D.4`, `D.5`로 연속 생성한다.

**Files:**
- Modify in worktree `archive/full-harness-v0.4.6`: `tools/generate_contracts.py`
- Modify in worktree `archive/full-harness-v0.4.6`: Generator/contract tests as needed
- Regenerate: `generated/docs/schema_reference.md`
- Regenerate: `docs/current/reference/ai_native_npc_contract_appendices_v0.4.6.md`

**Steps:**
1. `schema["hash_contract"]` 순회에 `start=3` enumerate를 적용한다.
2. 각 Hash heading에 순회 번호를 사용한다.
3. Normalizer heading을 Hash 개수 다음 번호로 계산한다.
4. 생성 결과에 duplicate subsection이 없고 번호가 연속인지 검증한다.
5. main Appendix marker를 Generator 결과로 동기화한다.

### Task 5: 최종 binding·계약 검증

**Objective:** 마지막 편집 상태를 기준으로 문서·Generator·계약 정합성을 증명한다.

**Files:**
- Modify: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md`

**Steps:**
1. 최종 Requirements SHA-256을 계산해 UE binding을 갱신한다.
2. Markdown file link·heading fragment·fence를 검사한다.
3. generated marker와 Generator 출력을 byte 비교한다.
4. Schema semantic validation과 Generator reproducibility를 실행한다.
5. Golden fixture, Python parity, C++17 parity, unit test를 실행한다.
6. 독립 first-reader review와 semantic contract review를 실행한다.
7. `git diff --check`와 `git status`를 확인한다.

## 완료 기준

- Implementation Plan은 Phase→작업 범위→모델·학습 세부 순서다.
- Requirements에 Target Kind/Skill 숫자 ID 표가 없다.
- 검토 대상 긴 복합 문장은 단문·목록·표로 분리됐다.
- Appendix D heading은 `D.1`부터 `D.5`까지 중복 없이 연속이다.
- 모든 링크·fragment·marker·hash·Generator·Golden 검증이 통과한다.
- Unreal Runtime Gate pending 상태를 release-green으로 표현하지 않는다.
- 사용자의 별도 요청 전에는 commit·push하지 않는다.
