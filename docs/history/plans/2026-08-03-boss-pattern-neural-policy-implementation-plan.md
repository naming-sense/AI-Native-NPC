# 보스 전용 Neural Pattern Selector 구현 계획

- 상태: 정적 계약 구현 완료
- 작성일: 2026-08-03
- 요구사항: `../requirements/2026-08-03-boss-pattern-neural-policy-requirements.md`
- 작업 저장소: `/tmp/ai-native-npc-harness`
- 동기화 대상: `/home/namingsense/AI-Native-NPC`
- 커밋·푸시: 사용자 요청 전까지 금지

## 1. 구현 원칙

1. Harness에서 구조화 원본·Generator·테스트를 먼저 변경한다.
2. 새 동작은 failing test를 먼저 작성하고 RED를 확인한다.
3. generated 파일은 수동 편집하지 않는다.
4. Harness refresh 이후 공유 파일을 main에 동기화한다.
5. 최종 검증은 마지막 문서·metadata 편집 이후 다시 시작한다.

## 2. Task 1 — 별도 Boss Pattern 구조화 계약

### 파일

- 생성: `contracts/current/boss_pattern_contract_v1.yaml`
- 수정: `tools/contractlib.py`
- 수정: `tests/test_semantic_hardening.py`

### 구현

- 최대 Pattern Slot 32개와 별도 Tensor/Output shape를 선언한다.
- Selection Boundary, Execution Phase, Interrupt Kind, Mask Reason enum을 선언한다.
- authored Pattern Data Asset 필수 field와 timing/range/interrupt/tracking 불변식을 선언한다.
- Pattern candidate-set hash와 boss pattern decision-contract hash의 canonical field order를 선언한다.
- validator가 count, contiguous enum, field uniqueness, normalizer closure, source allowlist, range, timing, branch, interrupt, hash field order를 검사한다.
- mutation test로 공통 272 변경, 32-row shape 변경, normalizer assignment gap, Ground Truth source, Active 중 reselect, 늦은 BranchWindow Commit, unknown interrupt, stale hash field order를 거부하는지 확인한다.

### RED/GREEN

1. 새 mutation/contract tests를 작성한다.
2. 기존 loader에서 새 계약이 없어 실패하는 것을 확인한다.
3. loader와 validator를 최소 구현한다.
4. 특정 테스트와 전체 unittest를 통과시킨다.

## 3. Task 2 — Boss Pattern codegen과 Golden

### 파일

- 수정: `tools/generate_contracts.py`
- 수정: `tools/generate_golden.py`
- 생성: `generated/python/ai_native_npc_boss_pattern_contracts_generated.py`
- 생성: `generated/cpp/AINativeNPCBossPatternContracts.generated.h`
- 생성: `generated/docs/boss_pattern_reference.md`
- 생성: boss pattern Golden JSON 또는 기존 Golden의 별도 section
- 수정: `tests/test_generated_contract.py`
- 수정: `tests/generated_cpp_golden_test.cpp`

### 구현

- Pattern 상수, enum, shape, mask, slot-layout validator, normalizer table/function, request hash, decision hash를 Python/C++로 생성한다.
- 공통 `CandidateCount=272`와 `CandidateIndex(15,16)=271`를 유지한다.
- Python↔C++ canonical bytes와 SHA-256 결과를 Golden으로 비교한다.
- 별도 generated Markdown에 Pattern Data Asset contract, mask/lock/interrupt/hash 표를 생성한다.

## 4. Task 3 — 현행 문서 반영

### 파일

- 수정: `docs/current/requirements.md`
- 수정: `docs/current/implementation-plan.md`
- 수정: `docs/current/unreal-implementation-plan.md`
- generated 삽입: `docs/current/contract-appendices.md`
- 수정: `README.md`

### 구현

- Requirements 시스템 흐름과 용어에 `Attack(Entity) → Boss Pattern Selector → StateTree/Combat Executor`를 추가한다.
- 공통 272 Candidate와 Pattern Candidate namespace를 분리한다.
- Selection Boundary, lock, hard mask, fairness, interrupt, async Commit, fallback, data/metrics를 규범화한다.
- 공통 Implementation Plan에 별도 factorized Pattern scorer, Utility-first 학습 순서, export/bundle 상태를 추가한다.
- Unreal Plan에 Data Asset, C++ record/request/response, Candidate Builder, scheduler, StateTree, Combat Module, debug/capture/test/file plan을 추가한다.
- Contract Appendices에는 generated boss pattern reference marker block만 삽입한다.
- Runtime Gate는 pending으로 유지한다.

## 5. Task 4 — Harness·Manifest·Taxonomy

### 파일

- 수정: `tools/doc_harness.py`
- 수정: `contracts/current/test_taxonomy_v1.yaml`
- 필요 시 수정: `manifest/release_config.json`, `manifest/freeze_status.json`
- 자동 갱신: Manifest, Lock, checksums, reports, catalog/source map

### 구현

- 새 계약과 generated 산출물을 package/strict scope에 포함한다.
- 정적 boss pattern contract/codegen/Golden gate는 실제 검증 결과만 PASS로 기록한다.
- Boss Pattern Unreal Float/ONNX/Runtime/Fairness/Performance는 pending으로 분리한다.
- Critical/OOD taxonomy에 boss pattern lock·interrupt·fairness family를 추가하고 KPI를 재생성한다.

## 6. Task 5 — main 동기화와 전체 검증

### 동기화

Harness에서 다음 공유 파일을 main에 복사한다.

- `README.md`
- `contracts/current/*.yaml`
- `docs/current/*.md`
- `generated/python/*.py`
- `generated/cpp/*.h`

Harness-only 도구·테스트·Manifest는 main에 복사하지 않는다.

### 검증

1. `python3 -m unittest discover -s tests -p 'test_*.py'`
2. `python3 tools/validate_schema.py`
3. `python3 tools/generate_contracts.py --check`
4. `python3 tools/generate_golden.py --check`
5. C++17 Golden compile/run
6. `python3 tools/doc_harness.py validate --strict`
7. `git diff --check` 양쪽
8. main custom validator
9. 공유 핵심 파일 byte parity
10. `docs/current`: 정확히 4 Markdown, 하위 폴더 0

## 7. Task 6 — 독립 검토와 기록 이동

- semantic contract review: 권한, mask, lock, interrupt, hidden information, async hash, fallback, gate 상태
- first-reader review: 공통 Candidate와 Pattern Candidate 혼동 여부
- code quality review: loader/generator/test 중복과 오류 처리
- 잔여 Critical/Important/Minor finding을 모두 닫은 뒤 검증을 재실행한다.
- 완료 시 요구사항 기록은 `docs/history/requirements/`, 구현 계획은 `docs/history/plans/`로 이동하고 상태를 완료로 바꾼다.

## 8. 완료 조건

실행 가능한 Harness 산출물과 실제 테스트 출력이 모두 존재하고, main/Harness parity와 clean diff 검사가 통과해야 완료다. Unreal Runtime을 실행하지 않은 상태에서는 정적 계약 완료만 보고한다.

## 9. 완료 증거

- 공통 `16 Skills × 17 Target Slots = 272 Candidate`와 `CandidateIndex(15,16)=271` 유지
- 별도 Boss Pattern 32-row 계약, validator, Python/C++/Markdown codegen, Candidate/Decision hash Golden 완료
- Pattern Slot all-padding·비정렬·padding mask 위반 Python/C++ 거부
- Python unittest **47 tests, OK**
- codegen·Golden reproducibility, Schema validation, strict Harness validation **PASS**
- C++17 Golden과 main Python/C++ smoke **PASS**
- main↔Harness 배포 파일 9개 byte parity **PASS**
- 독립 closure review: **Critical 0 / Important 0 / finding 0**

Pattern Asset Bundle digest parity, Unreal Float/ONNX/NNE, lock·interrupt Runtime, fairness/quality, performance Gate는 실제 Unreal 증거 전까지 `PENDING`이다.
