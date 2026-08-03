# 보스 전용 Neural Pattern Selector 요구사항

- 상태: 완료
- 작성일: 2026-08-03
- 범위: 공통 272 Candidate 계약을 유지하는 선택적 보스 전투 확장

## 1. 목적

다크 소울류 보스는 공통 Tactical Policy가 `Attack(Entity)`를 선택한 뒤, 보스 전용 Pattern Selector가 authored 공격 패턴을 고른다. StateTree와 Combat Module은 선택된 패턴의 Telegraph, Active, Recovery, Montage, Hitbox, Damage, Root Motion을 결정론적으로 실행한다.

```text
Perception/Belief
→ Target Slot snapshot
→ 공통 Skill × Target Slot 272 Candidate ranking
→ Attack(Entity) Commit
→ Boss Pattern Candidate Builder
→ Utility Baseline 또는 Neural Pattern Policy ranking
→ Boss Pattern Commit
→ StateTree/Combat Executor
```

## 2. 보존 계약

1. 공통 `16 Skills × 17 Target Slots = 272 Candidates` layout과 index 식을 변경하지 않는다.
2. `QuickSlash`, `DelayedHeavy`, `GapCloser`는 Target Slot도 공통 Skill도 아니다.
3. Boss Pattern Selector는 `Attack(Entity)`가 Commit되고 NPC가 보스 패턴 capability를 가질 때만 활성화한다.
4. 일반 NPC와 공통 Policy는 보스 Pattern Tensor나 Pattern ID를 소비하지 않는다.

## 3. 별도 고정 Pattern Candidate 공간

1. 한 보스 archetype은 최대 32개의 authored Pattern Slot을 가진다.
2. Pattern Slot은 Data Asset의 stable `pattern_id` 오름차순으로 canonical assignment한다.
3. 비어 있는 행과 실행 불가능한 행을 제거하지 않고 `pattern_mask=false`로 유지한다.
4. Pattern Candidate index는 해당 request의 `pattern_slot`이며 공통 Candidate index와 별도 namespace를 사용한다.
5. Pattern Policy I/O는 별도 `boss_pattern_contract_v1`에서 고정한다.
6. Pattern Registry/Data Asset bundle과 request mask는 별도 hash 계약으로 묶는다.
7. 모든 float feature는 generated normalizer에 정확히 한 번 배정하고 거리·속도·시간 divisor, clamp, non-finite reject를 Python/C++에서 공유한다.
8. 비어 있는 Pattern row는 정규화 후 feature 0, `invalid_pattern_id`, `pattern_mask=false`로 고정한다.

## 4. 선택 가능 시점과 실행 잠금

Pattern inference는 다음 Selection Boundary에서만 요청한다.

- `PreAttack`: 공격 시작 전
- `BranchWindow`: authored combo branch window
- `RecoveryEnd`: 현재 패턴 Recovery 종료

실행 상태는 다음과 같다.

```text
ReadyToSelect
→ Pattern Commit + lock
→ PreAttackTurn
→ Startup/Telegraph
→ Active
→ Recovery
→ BranchWindow 또는 Completed
```

- `PreAttackTurn`: Pattern Commit 성공과 함께 잠그고 authored 방향 보정만 수행한다.
- `Startup/Telegraph`: 선택 잠금을 유지한다.
- `Active`: Pattern 변경을 금지한다.
- `Recovery`: 기본적으로 변경을 금지한다.
- `BranchWindow`: Data Asset이 명시한 branch만 새 Pattern 선택을 허용한다.
- `Completed`: 다음 공통 Tactical 판단 또는 다음 Pattern 선택을 허용한다.

센싱과 공통 Tactical 추론이 계속 실행되어도 현재 locked Pattern을 교체하지 않는다.

## 5. Authored Pattern 소유권

각 Pattern Data Asset은 최소한 다음을 소유한다.

- stable `pattern_id`, 이름, pattern family/tag
- 허용 Boss Phase와 combo predecessor/successor
- 거리·방향·고저·LOS 조건
- stamina/resource/cooldown 조건
- Startup/Telegraph, Active, Recovery 시간
- 최소 Telegraph와 최소 Recovery
- Montage, section, Root Motion mode
- Hitbox window와 Damage profile reference
- Startup/Active/Recovery별 tracking yaw·speed 상한
- Branch Window
- interruptibility allowlist와 interrupt-safe cleanup
- arena/nav safety 조건

Neural Policy는 위 authored 값을 수정하거나 animation frame, hitbox, damage, root motion을 출력하지 않는다.

## 6. Hard Mask

Candidate Builder는 ranking 전에 다음을 검사한다.

- Pattern Slot occupied
- Boss Phase 허용
- Attack Target identity/generation 유효
- 거리·각도·고저·LOS 범위
- cooldown 완료
- stamina/resource 확보 가능
- predecessor와 branch 조건
- arena boundary와 nav feasibility
- montage/combat asset load 완료
- 현재 실행 상태가 Selection Boundary
- 동시 실행·reservation 충돌 없음

하나라도 실패하면 `pattern_mask=false`다. 유효 Pattern이 0개면 모델과 Utility를 호출하지 않고 `PatternUnavailable`로 공통 Skill에 반환한다.

## 7. 공정성·Hidden Information

1. Pattern request는 해당 Selection Boundary에서 관측 가능한 Belief와 Attack Target snapshot만 사용한다.
2. feature source allowlist는 Ground Truth·omniscient·hidden Actor source를 거부한다.
3. `target_health_ratio_estimate`는 confidence를 동반하며 confidence 0의 값을 확정 체력으로 사용하지 않는다.
4. Startup 이후 새 플레이어 입력이나 실제 hidden 위치를 Pattern 재선택에 사용하지 않는다.
5. Pattern 선택용 Belief snapshot은 immutable로 유지하고 Target identity를 lock한다.
6. 결정론적 Executor만 Combat Targeting 정책의 현재 transform을 phase별 yaw/speed 한도 안에서 추적한다.
7. Executor transform은 모델 입력이나 Pattern 재선택 조건으로 되먹이지 않는다.
8. 같은 Telegraph는 authored timing과 결과 범위를 유지한다.
9. 최소 Telegraph와 Recovery를 모델 출력으로 줄일 수 없다.
10. 플레이어의 일반 이동은 현재 Pattern interrupt 사유가 아니다.

## 8. Interrupt

현재 Pattern은 authored interruptibility와 결정론적 강제 규칙이 허용할 때만 중단한다.

- 강제 중단: 사망, actor destruction, authority loss
- 조건부 중단: stun/posture break, scripted phase transition, arena reset
- 중단 금지 기본값: 일반 target movement, 새 tactical score, 새 Pattern score

중단 시 Combat Module은 hitbox 비활성화, montage/Root Motion cleanup, reservation 해제, 상태 전이를 원자적으로 수행한다.

## 9. 비동기 요청과 Commit

Boss Pattern request/response는 다음을 포함한다.

- `pattern_decision_id`
- `selection_boundary`
- `attack_target_handle`
- `boss_phase_revision`
- `combat_state_revision`
- `pattern_candidate_set_hash`
- `boss_pattern_decision_contract_hash`

Commit Coordinator는 latest pending request, hash, target identity/generation, phase/combat revision, Selection Boundary, mask, resources를 재검증한다. 실패한 응답은 현재 Pattern을 변경하지 않는다. `BranchWindow`가 응답 전에 닫히면 stale로 거부하고 현재 Pattern의 authored 종료 경로를 계속한다.

## 10. Fallback

순서는 다음과 같다.

1. valid row가 있는 inference/response 실패는 같은 immutable snapshot의 Utility Baseline으로 선택
2. Utility 동점은 adjusted score 내림차순 후 `pattern_id` 오름차순
3. Utility 자체가 실패한 경우 authored safe default Pattern이 현재 valid하면 선택
4. Attack 시작을 취소하고 `PatternUnavailable` 반환
5. 공통 Policy가 `KeepDistance`, `Approach`, `RetreatFrom`, `Idle` 등 다른 Candidate를 다시 선택

locked Pattern 실행 중 inference 실패는 현재 Pattern을 계속 실행한다. interrupt rule이 발생한 경우에만 중단한다.

## 11. ML·데이터·평가

- Utility Baseline을 먼저 구현하고 Neural Pattern Policy와 동일한 mask/interface를 사용한다.
- 학습 record는 request tensors, mask, selected pattern, teacher/utility scores, pattern outcome, interrupt reason, phase, target snapshot provenance를 저장한다.
- split은 boss archetype, arena, encounter phase, animation family 누출을 차단한다.
- 필수 평가: invalid commit 0, Telegraph 위반 0, hidden-information leakage 0, 반복률, pattern diversity, dodgeability, damage fairness, phase별 completion, Utility 대비 비열등 또는 개선.
- Calibration/OOD는 valid Pattern row만 대상으로 하며 zero accepted sample은 실패다.

## 12. 상태 표시

이번 변경은 Schema/Generator/Harness의 정적 계약과 구현 계획을 추가한다. Pattern Asset Bundle digest parity, Unreal Float, ONNX, Runtime, 공정성, 성능 Gate는 실제 Unreal 구현과 증거가 생길 때까지 `pending`이다.

## 13. 수락 기준

- 공통 Candidate count와 index Golden이 272로 유지된다.
- 별도 boss pattern 계약이 Schema validator와 mutation test로 검증된다.
- generated Python/C++ boss pattern binding, slot-layout validator, normalizer table·function, Candidate/Decision hash Golden, Markdown reference가 재현된다.
- Requirements, 공통 Implementation Plan, Unreal Plan, Contract Appendices가 같은 계층·용어·상태를 사용한다.
- main과 archive Harness의 공유 파일 parity가 유지된다.
- 전체 Python, strict validation, generator reproducibility, C++17 Golden이 통과한다.
- `docs/current`에는 기존 현행 Markdown 4개만 있고 하위 폴더가 없다.
- Runtime pending Gate를 release-green으로 표현하지 않는다.
