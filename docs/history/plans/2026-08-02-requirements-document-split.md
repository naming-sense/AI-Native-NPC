# AI Native NPC 문서 분리와 Teacher LLM 계약 구현 계획

> **For Hermes:** 이 계획을 순서대로 실행하고 각 단계 후 경로·링크·계약 정합성을 검증한다.

**Goal:** 결합된 v0.4.6 문서를 Requirements, Implementation Plan, Contract Appendices로 분리하고 Teacher LLM Silver Label 생성 계약을 복원한다.

**Architecture:** Requirements는 시스템 동작·권한·입출력·안전·데이터 요구사항만 소유한다. Implementation Plan은 모델 구조·학습·코드 생성·Phase·일정·완료 절차를 소유한다. Contract Appendices는 Schema/Registry/Test Taxonomy의 생성 표와 승인 기준을 한 곳에서 제공한다.

**Tech Stack:** Markdown, YAML contract, archived Python Generator, SHA-256 binding, Git diff verification

---

## Task 1. 문서 경계와 경로 확정

**Objective:** 세 문서의 독자·내용·집행 위치를 명확히 고정한다.

**Files:**

- Create: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md`
- Create: `docs/current/implementation/ai_native_npc_implementation_plan_v0.4.6.md`
- Create: `docs/current/reference/ai_native_npc_contract_appendices_v0.4.6.md`
- Remove: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`

**Steps:**

1. Requirements에 목적, Runtime 구조, Typed Target, Slotter, Candidate, Goal, Policy, Commit, Hidden Information, 데이터·평가 요구사항을 둔다.
2. Implementation Plan에 `policy_arch_v1.0.0`, 학습 파이프라인, Training Config, Checkpoint, Export, Schema Generator, Release Pipeline, Phase·Owner·일정·완료 체크리스트를 둔다.
3. Appendices에 생성된 Appendix A–D, Requirements KPI, UE 승인 체크리스트를 둔다.
4. 세 문서 상단에 서로의 상대 링크와 독자·집행 범위를 명시한다.

**Verification:** 세 문서가 동일 규칙을 중복 소유하지 않고, 이동한 모든 절을 링크로 찾을 수 있어야 한다.

---

## Task 2. Teacher LLM Silver Label 계약 추가

**Objective:** Teacher LLM 입력·출력·합의·검증·provenance·Gold 승격 경계를 재현 가능하게 정의한다.

**Files:**

- Modify: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md`
- Modify: `docs/current/implementation/ai_native_npc_implementation_plan_v0.4.6.md`

**Requirements 내용:**

1. Teacher LLM은 개발 단계의 Silver Label 공급자다.
2. 입력은 contract-valid Decision Snapshot, Belief/Event, Role·Personality·Relationship, Goal/Phase, Candidate Mask와 valid Candidate 설명으로 제한한다.
3. 출력은 strict structured schema의 acceptable candidates, preference/ranking, ambiguity, reason tags다.
4. LLM은 hard mask를 해제할 수 없고 hidden/future/absolute-world 정보를 받지 않는다.
5. 복수 sampling, prompt 변형, 합의, 사람 Gold 비교, Utility 불일치 수집, Critical/OOD/Test 정답 사용 제한을 정의한다.
6. Dataset Record v2의 `label_confidence`, `prompt_or_teacher_version`, `annotator_set_hash`, `annotator_agreement` 계산·저장 책임과 연결한다.

**Implementation Plan 내용:**

1. Teacher request builder
2. provider/model/prompt/sampling profile lock
3. strict response parser
4. consensus aggregator
5. Dataset Validator와 Gold review queue
6. 품질 report와 재실행 명령

**Verification:** 모든 Teacher output이 Dataset Record 필드로 매핑되고, 재현에 필요한 version/hash와 reject 조건이 존재해야 한다.

---

## Task 3. Appendix 분리와 Generator 대상 변경

**Objective:** 생성 Appendix를 공유 reference 문서 한 곳으로 이동하고 기계 판독 source가 새 경로를 소유하게 한다.

**Files:**

- Create: `docs/current/reference/ai_native_npc_contract_appendices_v0.4.6.md`
- Modify: `contracts/current/ai_native_npc_schema_v2_0.yaml`
- Modify: `contracts/current/test_taxonomy_v1.yaml`
- Modify: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md`
- Regenerate: `generated/python/ai_native_npc_contracts_generated.py`
- Regenerate: `generated/cpp/AINativeNPCContracts.generated.h`

**Steps:**

1. Schema `documentation_contract.required_documents`를 shared appendices 문서로 변경한다.
2. Test Taxonomy의 Requirements·Unreal marker target을 shared appendices 문서로 변경한다.
3. 보관 harness Generator의 경로 상수를 임시 작업공간에서 새 구조에 맞춘다.
4. A–D Schema block, Requirements KPI block, Unreal KPI block을 생성한다.
5. Requirements와 UE 문서의 Appendix는 링크로 교체한다.
6. generated Python/C++의 source hash를 새 YAML hash로 갱신한다.

**Verification:** shared appendices의 marker content가 Generator output과 byte-identical이고 Requirements·UE 본문에는 generated Appendix 복사본이 없어야 한다.

---

## Task 4. 교차 문서 링크와 감사 기록 갱신

**Objective:** 삭제된 결합 문서를 가리키는 active reference를 제거하면서 과거 리뷰의 감사 대상을 보존한다.

**Files:**

- Modify: `README.md`
- Modify: `docs/current/history/ai_native_npc_requirements_history_v0.4.6.md`
- Modify: `docs/current/reviews/ai_native_npc_requirements_review_v0.4.6.md`
- Modify: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md`
- Modify: `docs/plans/2026-08-02-requirements-review-remediation.md`
- Modify: `docs/plans/2026-08-02-requirements-reader-first-restructure.md`

**Steps:**

1. README의 읽기 순서를 Requirements → Implementation Plan → Appendices → UE Plan으로 변경한다.
2. History에 결합 문서 분리와 Teacher LLM 계약 복원 이력을 추가한다.
3. Review는 기존 검토 경로·commit을 유지하고 현행 후속 문서 링크를 추가한다.
4. UE 상위 Requirements 파일명과 SHA-256 binding을 최종 Requirements hash로 갱신한다.
5. 과거 plan에는 결합 문서가 대체됐다는 후속 경로를 추가한다.

**Verification:** active 문서·YAML에서 삭제된 파일 경로 검색 결과가 0이어야 한다. 과거 리뷰·계획의 감사 문맥에는 superseded 설명과 함께 남을 수 있다.

---

## Task 5. 최종 검증

**Objective:** 문서 분리가 계약·생성·감사 정합성을 유지했음을 증명한다.

**Checks:**

1. Markdown heading·code fence·relative link 검사
2. `git diff --check`
3. 새 Requirements SHA와 UE binding 일치
4. Schema·Skill·Goal·Taxonomy SHA와 generated header/module 일치
5. shared appendices marker parity
6. 삭제 경로 active reference 0
7. Teacher input/output/provenance/consensus/Gold/Critical 경계 검사
8. Requirements와 Implementation Plan의 동일 규칙 중복 소유 검사
9. 독립 first-reader review
10. 독립 semantic contract review

**Stage boundary:** 보관 harness는 새 문서 구조에 맞춘 임시 작업공간에서 실행한다. Runtime/NNE Gate는 문서 구조 변경 범위가 아니므로 기존 pending 상태를 유지한다.
