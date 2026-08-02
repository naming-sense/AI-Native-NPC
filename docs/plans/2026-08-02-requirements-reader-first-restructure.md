# AI Native NPC 요구사항 문서 독자 중심 재구성 계획

> **For Hermes:** 이 계획을 순서대로 실행하되 Auto-generated marker 내부는 수정하지 않는다.

**Goal:** 처음 읽는 사람이 AI Native NPC의 목적, 전체 동작 흐름, 각 계층의 책임, Typed Target을 비롯한 핵심 개념의 존재 이유를 먼저 이해한 뒤 세부 구현 계약을 읽을 수 있도록 요구사항 문서를 재구성한다.

**Architecture:** 현재 본문 앞의 검증·판정 이력은 별도 history 문서로 옮긴다. Requirements 본문에는 현재 상태만 짧게 남기고, 시스템이 해결하려는 문제와 런타임 흐름을 먼저 설명한다. 기존 규범 값과 Auto-generated Appendix는 유지하며 각 기술 장 앞에 `왜 필요한가`와 `어떻게 동작하는가`를 2~4문장으로 추가한다.

**Tech Stack:** Markdown, Schema/Registry-generated marker block, SHA-256 companion binding

---

### Task 1: 검증·판정 이력 분리

**Objective:** 현재 구현을 이해하는 데 필요하지 않은 RC5 검증 변천사를 본문에서 제거한다.

**Files:**
- Create: `docs/current/history/ai_native_npc_requirements_history_v0.4.6.md`
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. 기존 §0의 Validation Scope, RC5 판정, Remediation 판정 내용을 history 문서로 이동한다.
2. Requirements 상단에는 현재 가능한 작업, 아직 금지된 주장, 다음 차단 작업만 표 하나로 남긴다.
3. 검토 보고서와 history 문서 링크를 상단 metadata에 추가한다.

**Verification:** Requirements 첫 화면에 과거 버전 설명이 없어야 하며, history 문서가 기존 판정과 검증 범위를 보존해야 한다.

---

### Task 2: 문서 목적과 시스템 전체 그림 작성

**Objective:** 세부 계약 전에 제품 목적과 전체 데이터 흐름을 이해할 수 있게 한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. 한 문장 정의, 해결하려는 문제, 설계 선택, 성공 조건을 작성한다.
2. Runtime 의사결정 흐름과 학습·배포 흐름을 각각 짧은 도식으로 추가한다.
3. 문서가 정하는 것과 정하지 않는 것을 분리한다.
4. 기획자·Gameplay AI·ML·Unreal·QA별 읽기 순서를 제공한다.

**Verification:** 처음 읽는 독자가 "무엇을 만들며 모델이 어디까지 책임지는가"를 첫 두 장에서 설명할 수 있어야 한다.

---

### Task 3: 계층별 책임과 핵심 용어 재작성

**Objective:** 아키텍처 구성요소의 입력, 출력, 책임 경계를 한눈에 보이게 한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. 계층별 소유권 표를 `역할 / 받는 정보 / 내보내는 결과 / 금지 책임` 중심으로 바꾼다.
2. Goal, Skill, Target, Candidate, Belief, Commit, OOD, Contract를 짧은 용어 표로 정의한다.
3. Neural Policy는 후보를 평가할 뿐 Goal 생성, 안전 판정, 월드 변경을 소유하지 않는다는 경계를 명시한다.

**Verification:** 각 규칙의 독자, Runtime, 집행 위치가 사라지지 않아야 한다.

---

### Task 4: 주요 장에 존재 이유와 동작 요약 추가

**Objective:** 독자가 세부 표와 수식에 들어가기 전에 각 장의 맥락을 이해하게 한다.

**Files:**
- Modify: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**
1. §2 Typed Target에 다양한 대상 형식을 하나로 묶는 이유와 Handle/Feature 분리 이유를 설명한다.
2. §3~§10 제목을 쉬운 한국어 설명과 기술 용어가 함께 보이도록 바꾼다.
3. 각 장 첫머리에 `왜 필요한가`, `어떻게 동작하는가`를 2~4문장으로 추가한다.
4. 기존 규범 수치, 식별자, 표, 수식, 내부 절 참조는 유지한다.

**Verification:** 장 제목과 첫 문단만 읽어도 전체 Pipeline을 순서대로 따라갈 수 있어야 한다.

---

### Task 5: companion binding과 최종 검증

**Objective:** 가독성 수정이 계약·생성 문서 정합성을 깨뜨리지 않았음을 확인한다.

**Files:**
- Modify: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md`
- Verify: repository diff

**Steps:**
1. 모든 Requirements 편집이 끝난 뒤 SHA-256을 계산한다.
2. UE 문서의 상위 Requirements SHA만 새 값으로 갱신한다.
3. Requirements와 UE의 모든 Auto-generated marker block이 HEAD와 byte-identical인지 검사한다.
4. Markdown code fence, 파일 mode, 잘못된 내부 참조, `git diff --check`를 검사한다.
5. YAML/Registry/generated 파일이 수정되지 않았는지 확인한다.

**Verification:** Local 문서 검증이 모두 통과해야 한다. Runtime/NNE 테스트를 실행하지 않았다면 문서 검증과 Runtime 검증을 구분해 보고한다.

---

## 적용·집행 경계

- 처음 읽는 사람은 Requirements §0~§1과 각 장의 첫 안내 문단을 읽는다.
- Gameplay AI, ML, Unreal 구현자는 이후 세부 계약과 Appendix를 구현 입력으로 사용한다.
- Auto-generated Appendix의 값은 Schema/Registry와 Generator가 소유하며 이 작업에서 수동 수정하지 않는다.
- History 문서는 감사 기록이며 현재 Runtime 구현 입력이 아니다.
- 이번 작업은 문서 재구성이다. Schema, Runtime, ML 구현 상태를 PASS로 바꾸지 않는다.
