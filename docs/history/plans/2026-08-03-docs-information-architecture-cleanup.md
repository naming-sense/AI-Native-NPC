# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# AI Native NPC 문서 정보 구조 정리 Implementation Plan

> **For Hermes:** 이 계획을 순서대로 실행하고, 경로 계약을 변경한 뒤 보관 Harness에서 생성 산출물과 Manifest를 다시 만든다.

**Goal:** `docs/current`에는 지금 읽고 구현할 현행 문서 네 개만 남기고, 완료된 계획·검토·개정 기록은 `docs/history`에서 찾도록 정리한다.

**Architecture:**

- `docs/current`는 안정적인 짧은 파일명으로 현행 Requirements, Implementation Plan, Contract Appendices, Unreal Plan만 제공한다.
- Contract Appendices는 현재 Schema·Registry에서 생성되는 규범 계약이므로 History로 보내지 않는다.
- `docs/history`는 비규범 변경 기록을 보존한다.
- 보관 Harness의 `docs/archive`는 이전 버전 원본을 보존한다.

**Tech Stack:** Markdown, YAML contract, Python Generator, Git rename detection, SHA-256 binding, Manifest/Golden validation

---

## 적용·집행 경계

| 구조 | 독자 | 역할 | 집행 방식 |
|---|---|---|---|
| `docs/current/` | 구현자·검토자 | 지금 적용할 문서 네 개 | README 읽기 순서, Schema/Taxonomy 경로 계약, Harness strict validation |
| `docs/history/` | 감사자·문서 관리자 | 완료된 계획·검토·개정 기록 | History index와 상대 링크, 현재 계약 집행 범위에서 제외 |
| `docs/archive/` | 이전 버전 감사자 | 과거 릴리스 원본 | 보관 Harness archive catalog와 lock |
| `contracts/current/` | Generator·Runtime·ML | 기계 판독 계약 | Generator, Golden, Python/C++ parity |

## 요구사항

1. `docs/current` 바로 아래에는 다음 네 문서만 둔다.
   - `requirements.md`
   - `implementation-plan.md`
   - `contract-appendices.md`
   - `unreal-implementation-plan.md`
2. Contract Appendices는 현재 규범 계약이므로 `docs/history`로 이동하지 않는다.
3. Requirements History는 `docs/history/requirements-history-v0.4.6.md`로 이동한다.
4. 완료된 검토는 `docs/history/reviews/`로 이동한다.
5. 완료된 작업 계획은 `docs/history/plans/`로 이동한다.
6. `docs/history/README.md`는 History의 비규범 성격과 각 기록의 위치를 안내한다.
7. Root README는 현재 문서 네 개를 먼저 안내하고 History는 별도 섹션으로 분리한다.
8. 현행 문서의 상대 링크와 명시적 파일 경로는 새 안정 경로를 사용한다.
9. 과거 계획의 작업 단계에 기록된 당시 파일 경로는 역사적 증거이므로 보존한다. 현재 후속 문서로 연결되는 Markdown 링크만 새 경로로 갱신한다.
10. Schema `documentation_contract`, Test Taxonomy, Harness path constants, Source File Map, INDEX, Manifest, Lock, Checksum은 새 경로와 일치해야 한다.
11. `docs/history/`는 manual hash literal 등 현재 규범 Markdown 집행 범위에서 제외한다.
12. Requirements 내용 변경 후 SHA-256과 UE binding을 다시 생성한다.
13. Unreal Float/ONNX/Runtime Gate의 pending 상태를 유지한다.

## 목표 구조

```text
docs/
├── current/
│   ├── requirements.md
│   ├── implementation-plan.md
│   ├── contract-appendices.md
│   └── unreal-implementation-plan.md
└── history/
    ├── README.md
    ├── requirements-history-v0.4.6.md
    ├── reviews/
    │   └── requirements-review-v0.4.6.md
    └── plans/
        ├── 2026-08-02-requirements-document-split.md
        ├── 2026-08-02-requirements-reader-first-restructure.md
        ├── 2026-08-02-requirements-review-remediation.md
        ├── 2026-08-03-reader-first-final-cleanup.md
        └── 2026-08-03-docs-information-architecture-cleanup.md
```

---

## Implementation Plan

### Task 1: 현행 문서와 History를 역할별로 이동

**Files:**

- Rename: `docs/current/requirements/ai_native_npc_requirements_v0.4.6.md` → `docs/current/requirements.md`
- Rename: `docs/current/implementation/ai_native_npc_implementation_plan_v0.4.6.md` → `docs/current/implementation-plan.md`
- Rename: `docs/current/reference/ai_native_npc_contract_appendices_v0.4.6.md` → `docs/current/contract-appendices.md`
- Rename: `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md` → `docs/current/unreal-implementation-plan.md`
- Rename: `docs/current/history/ai_native_npc_requirements_history_v0.4.6.md` → `docs/history/requirements-history-v0.4.6.md`
- Rename: `docs/current/reviews/ai_native_npc_requirements_review_v0.4.6.md` → `docs/history/reviews/requirements-review-v0.4.6.md`
- Rename: `docs/plans/*.md` → `docs/history/plans/*.md`
- Create: `docs/history/README.md`

**Verification:** `docs/current`의 Markdown 파일이 네 개이며 하위 디렉터리가 없어야 한다.

### Task 2: 독자 링크와 경로 계약 갱신

**Files:**

- Modify: `README.md`
- Modify: `docs/current/*.md`
- Modify: `docs/history/**/*.md`
- Modify: `contracts/current/ai_native_npc_schema_v2_0.yaml`
- Modify: `contracts/current/test_taxonomy_v1.yaml`
- Modify: 보관 Harness의 `INDEX.md`, `tools/doc_harness.py`

**Verification:** 현재 문서를 설명하는 tracked source에는 이전 `docs/current` 하위 경로와 `docs/plans` 경로가 없어야 한다.

과거 계획 본문의 당시 경로는 예외로 분류한다.

### Task 3: 보관 Harness와 생성 산출물 동기화

**Files:**

- Regenerate: `generated/docs/*`
- Regenerate: `generated/python/*`
- Regenerate: `generated/cpp/*`
- Regenerate: `golden/*`
- Regenerate: `manifest/*`
- Regenerate: `reports/*`
- Regenerate: `tests/reports/*`

**Verification:** `python3 tools/doc_harness.py refresh`, `python3 tools/generate_contracts.py --check`, main/Harness byte parity가 통과해야 한다.

### Task 4: 최종 검증

1. 전체 Python unittest를 실행한다.
2. generated C++ Golden test를 컴파일·실행한다.
3. strict document validation을 실행한다.
4. 모든 Markdown 상대 링크와 fragment를 검사한다.
5. Requirements SHA와 UE binding을 비교한다.
6. `git diff --check`와 두 working tree의 상태를 확인한다.
7. 독립 semantic contract review와 first-reader review에서 잔여 Critical·Important·Minor finding이 없어야 한다.

## 완료 조건

- `docs/current`에는 현행 문서 네 개만 존재한다.
- Root README의 읽기 순서와 실제 파일 구조가 일치한다.
- History와 Archive의 역할이 문서로 구분된다.
- 모든 생성·Hash·Manifest·Golden 검증이 통과한다.
- Unreal Runtime pending 경고는 그대로 유지된다.
- 사용자 요청이 없는 한 커밋하거나 푸시하지 않는다.
