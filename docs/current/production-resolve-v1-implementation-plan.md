# Production Resolve v1 구현 계획

**문서 버전:** 1.0.1
**기준일:** 2026-08-23
**상태:** 핵심 코드 구현 완료, production rollout 대기
**범위:** `InvestigateDisturbance.Resolve`의 production Neural evaluator와 첫 production-executable Resolve Skill

**목표:** `subject_identified`가 설치한 `IdentifiedSubject`를 대상으로 검증된 Neural-first 정책과 실제 `Greet` Skill을 실행하고, 실패 시 generated 계약에 따라 안전하게 fallback 또는 종료한다.

**Architecture:** `FFinalizedDecisionSnapshot`이 Candidate와 Tensor의 유일한 입력 authority다. NNE evaluator는 고정 Candidate의 순위와 parameter proposal만 계산하고, Utility fallback·Commit Coordinator·Skill Executor가 각각 fallback, 최신 상태 재검증, gameplay effect를 소유한다.

**Tech Stack:** Unreal Engine 5.7, NNE, ONNX opset 17, generated YAML Registry, StateTree, Unreal Automation, production PIE

---

## 목차

- [1. 이 문서가 확정하는 결정](#1-이-문서가-확정하는-결정)
- [2. 현재 기준선과 활성화 원칙](#2-현재-기준선과-활성화-원칙)
- [3. Production Neural evaluator 계약](#3-production-neural-evaluator-계약)
- [4. Production-executable Greet 계약](#4-production-executable-greet-계약)
- [5. Commit과 실패 처리](#5-commit과-실패-처리)
- [6. ResolvePolicyReady 조건](#6-resolvepolicyready-조건)
- [7. 구현 순서](#7-구현-순서)
- [8. 검증 계획](#8-검증-계획)
- [9. 완료 정의](#9-완료-정의)

---

<a id="1-이-문서가-확정하는-결정"></a>
## 1. 이 문서가 확정하는 결정

### 1.1 첫 production Resolve 행동

Production Resolve v1의 첫 production-executable Skill은 **`Greet(Entity)` 하나**로 고정한다.

선정 이유:

- `subject_identified`는 현재 visible한 Entity를 식별했다는 뜻이며 적대성 판정이 아니다.
- `InvestigateDisturbance`는 Social source의 Goal이다.
- generated Registry에서 `Greet`는 `Resolve`가 허용하고 `Entity` Target과 호환되는 비적대적 Skill이다.
- `Greet`는 기존 parameter 계약의 `duration`과 `intensity`를 그대로 사용한다.

다음 Skill은 v1 production executable set에 넣지 않는다.

| Skill | v1 결정 | 이유 |
|---|---|---|
| `Warn` | 제외 | 경계 위반 또는 경고 필요성을 증명하는 authoritative policy가 없음 |
| `CallForHelp` | 제외 | 지원 요청을 허용하는 authoritative threat/escalation policy가 없음 |
| `Attack` | 제외 | `subject_identified`는 적대성 또는 공격 권한이 아님 |
| `Flee` | 제외 | Resolve의 `Entity` Primary Target과 Target Kind가 호환되지 않음 |
| `ContinueCurrentAction` | control-only | Resolve 진입 시 이전 조사 Skill은 exact transition interrupt 대상이다. 이후 exact current Greet가 이미 running일 때만 기존 Continue 규칙으로 허용 |

`Warn`, `CallForHelp`, `Attack`을 나중에 추가하려면 별도의 authoritative `ResolveDispositionPolicy`가 먼저 필요하다. Neural score, Personality, Relationship 또는 `subject_identified`만으로 이 Skill을 production mask에 추가하면 안 된다.

### 1.2 Neural과 Utility의 역할

- Neural Policy는 finalized Candidate의 **순위와 parameter proposal만** 계산한다.
- v1 production Neural rollout scope는 `GuardPhase0 + InvestigateDisturbance/Resolve` exact pair 하나다. 다른 Goal·phase는 기존 generated Utility 경로를 유지한다.
- Candidate 유효성, 적대성 권한, Goal 전환, Target 설치와 gameplay effect는 Neural이 소유하지 않는다.
- Neural이 성공하면 Utility는 호출하지 않는다.
- Neural이 unavailable, failed, abstained 또는 invalid이고 total deadline이 남아 있으면 **같은 immutable Snapshot**으로 Utility fallback을 정확히 한 번 호출한다. 이미 total deadline이 지났으면 Utility와 Commit은 모두 0건이다.
- Utility fallback도 선택하지 못하면 Commit과 Skill start를 실행하지 않는다.

### 1.3 적대성 소유권

Production Resolve v1은 적대성 값을 만들거나 변경하지 않는다.

- `subject_identified`는 disturbance 발생자 증명, 적대성 판정, 공격·추격·접근·도주 명령이 아니다.
- v1 `Greet`는 피해, 위협도, Relationship, Goal priority, Knowledge confidence를 변경하지 않는다.
- 향후 적대 행동의 eligibility는 별도 authoritative gameplay policy와 generated hard requirement가 소유한다.
- Neural은 authoritative eligibility가 true인 Candidate 사이에서만 선호를 계산한다.

---

<a id="2-현재-기준선과-활성화-원칙"></a>
## 2. 현재 기준선과 활성화 원칙

현재 구현에는 다음 기반과 Resolve v1 핵심 코드가 있다.

- `FFinalizedDecisionSnapshot`과 272개 fixed Candidate
- Neural-first·same-Snapshot Utility fallback orchestrator
- Commit Coordinator의 Candidate·Target·revision 재검증
- `subject_identified`의 detached transaction과 `IdentifiedSubject` Entity Target 설치
- Timer, running Skill, handoff, Decision, StateTree authority의 exact transition 검증
- `NNERuntimeORTCpu` production evaluator, 10 input·3 output descriptor 검사와 Calibration/OOD fail-closed 처리
- `Greet(Entity)` SocialAction, source-owned duration·terminal permit, world-space cue·focus 실행 코드와 StateTree task
- Resolve의 `SkillSucceeded`, `SkillFailed`, `TargetInvalidated` terminal result와 transactional recovery

현재 없는 production rollout 요소는 다음과 같다.

- 승인된 ONNX Model Bundle과 NNE ModelData
- 승인된 Calibration/OOD asset과 compiled promotion authority
- `WBP_AINativeNPCGreetCueV1`, production StateTree Greet branch와 exact Guard Pawn asset assembly
- actual Resolve Greet PIE, Target-loss PIE, packaged production NNE smoke와 전체 promotion evidence

핵심 코드는 구현됐지만 이 rollout 항목이 모두 준비·검증되기 전에는 `ResolvePolicyReady=false`를 유지한다. 현재 generated promotion authority는 `Approved=false`이며 production Resolve 경로는 dormant다. Test-only override, fault injection, private-state access는 `WITH_DEV_AUTOMATION_TESTS` 밖에 존재하면 안 된다.

---

<a id="3-production-neural-evaluator-계약"></a>
## 3. Production Neural evaluator 계약

### 3.1 입력 authority

Evaluator public seam은 기존 `IAINativeNPCNeuralPolicyEvaluator::Evaluate()`를 유지한다.

Host가 임의 `if (Phase == Resolve)` 분기로 rollout을 결정하면 안 된다. Machine-readable `general_policy_orchestration.production_neural_rollout_scope`가 `GuardPhase0/InvestigateDisturbance/Resolve`만 허용하고, 그 밖의 scope에서는 evaluator attempt를 만들지 않고 generated Utility를 primary로 사용한다. 이 제한은 `phase_skill_override`가 아니라 production policy rollout authority다.

입력은 다음 두 값뿐이다.

1. `TSharedPtr<const FFinalizedDecisionSnapshot>`
2. 같은 Decision의 `FSwitchCostFacts`

Evaluator는 World, Actor, Knowledge Component 또는 Goal Runtime을 직접 읽지 않는다. Snapshot 밖의 현재 상태를 읽어 score를 보정하면 안 된다.

NNE Model 입력은 Schema 2.0의 다음 10개 Tensor를 batch `B=1`로 exact-match한다.

Resolve v1 target contract version은 Schema `2.0.0`, `contract_revision=2.0.0-rc6`, contract bundle `0.4.7`, Goal Registry·`goal_gameplay_semantics_v1` `1.2.0`, Skill Registry·`execution_semantics_v1` `1.1.0`으로 고정한다. Current RC5/Goal 1.1.0/Skill 1.0.0은 Task 1 GREEN 전까지 readiness false인 이전 계약이다.

| 이름 | dtype | shape |
|---|---|---|
| `global_state` | `float32` | `[1,128]` |
| `target_features` | `float32` | `[1,17,48]` |
| `target_kind_ids` | `int64` | `[1,17]` |
| `target_mask` | `bool` | `[1,17]` |
| `event_features` | `float32` | `[1,12,24]` |
| `event_type_ids` | `int64` | `[1,12]` |
| `event_target_slots` | `int64` | `[1,12]` |
| `event_mask` | `bool` | `[1,12]` |
| `candidate_pair_features` | `float32` | `[1,272,16]` |
| `candidate_mask` | `bool` | `[1,272]` |

입력 이름, 순서, dtype, shape, finite 범위와 Tensor canonical digest가 하나라도 다르면 evaluator status는 `Invalid`다.

### 3.2 출력과 action 계약

NNE Model output은 다음 세 개다.

| 이름 | dtype | shape | 의미 |
|---|---|---|---|
| `candidate_raw_scores` | `float32` | `[1,272]` | fixed Candidate의 raw preference |
| `candidate_parameter_proposals` | `float32` | `[1,272,4]` | Registry parameter slot의 normalized proposal |
| `tactical_context` | `float32` | `[1,128]` | Calibration/OOD 입력 |

Evaluator output은 문자열 action, JSON, Skill 이름 또는 임의 command가 아니다. `FNeuralPolicyAttempt` 안의 canonical `FUtilitySelectionResult`만 반환한다.

후처리 규칙:

1. `candidate_mask=false` row의 score, switch cost, adjusted score와 parameter는 canonical positive zero여야 한다.
2. masked row는 선택할 수 없다.
3. valid row의 raw score는 finite이고 `[-2.5,2.5]` 범위여야 한다.
4. inactive parameter slot은 positive zero다.
5. active parameter proposal은 finite `[0,1]`이다.
6. generated Registry의 fixed index `SkillId × 17 + TargetSlot`만 사용한다.
7. adjusted score는 `raw_score - generated switch_cost`다.
8. 동점은 더 작은 Candidate index를 선택한다.
9. `tactical_context`가 Calibration/OOD asset의 계약을 통과해야 `Selected`를 반환한다.

v1은 valid action Candidate가 `Greet(Entity)` 하나뿐일 수 있다. `valid_count=1`이면 Calibration의 second adjusted score는 selected adjusted score와 같고 adjusted gap은 positive zero, normalized entropy는 zero다. `valid_count=0`이면 evaluator와 Calibration을 호출하지 않는다. 둘 이상이면 selected row를 제외한 valid row의 최대 adjusted score를 second로 사용하고 동점은 낮은 Candidate index 순서로 정한다.

272개 밖의 index, masked Candidate, unknown Skill/Target, unknown output, shape drift와 non-finite 값은 모두 `Invalid`다. Runtime이나 evaluator가 Candidate 또는 Skill을 동적으로 추가하면 안 된다.

### 3.3 evaluator status

| 상태 | 조건 | 처리 |
|---|---|---|
| `Selected` | descriptor, output, Calibration/OOD와 canonical selection이 모두 유효 | Neural selection을 Commit에 전달 |
| `Unavailable` | 승인된 ModelData/NNE/Calibration bundle이 설치되지 않음 | deadline이 남아 있으면 같은 Snapshot의 Utility fallback 1회 |
| `Failed` | NNE 실행 오류 또는 Neural budget 초과 | deadline이 남아 있으면 같은 Snapshot의 Utility fallback 1회 |
| `Abstained` | OOD 또는 calibration confidence 기준 미달 | deadline이 남아 있으면 같은 Snapshot의 Utility fallback 1회 |
| `Invalid` | descriptor, dtype, shape, finite, mask, index, parameter 또는 identity 불일치 | deadline이 남아 있으면 같은 Snapshot의 Utility fallback 1회 |

`Invalid`를 `Abstained`나 성공으로 축소하면 안 된다. Unknown output을 default action으로 바꾸면 안 된다.

### 3.4 시간 예산과 stale 정책

- 전체 Decision deadline은 기존 Commit request의 **40ms**를 유지한다.
- Neural evaluator budget은 **20ms**로 고정한다. 이 값은 machine-readable policy contract에서 생성한다.
- NNE 호출을 중간 취소할 수 없으면 반환 직후 monotonic time을 검사한다. 20ms를 넘긴 output은 사용하지 않고 `Failed`로 처리한다.
- Utility fallback은 남은 전체 deadline 안에서 같은 Snapshot으로만 실행한다.
- Neural 반환 시 total deadline이 이미 지났으면 Utility를 호출하지 않고 Decision을 `DeadlineExpired`로 폐기한다.
- 전체 40ms가 지났거나 Commit의 Goal, material Knowledge dependency, Candidate, World 또는 revision 검사가 stale이면 아무 Skill도 시작하지 않는다. Entity의 revision-only drift는 기술 요구사항 §7.1의 `continuous_nonmaterial` 조건과 50ms age bound를 모두 만족할 때만 예외로 허용한다.
- stale Commit은 Neural/Utility 결과를 새 Snapshot에 재사용하지 않는다.
- Host는 같은 GoalToken에서 fresh Snapshot 재평가를 다음 tick에 한 번만 예약한다. 같은 GoalRevision에서 두 번째 stale이면 자동 busy retry를 멈추고 다음 authoritative Goal/Knowledge 변화까지 기다린다.
- Target가 더 이상 current visible Entity가 아니면 fresh retry 대신 generated `TargetInvalidated` 경로를 평가한다.

Primary `IdentifiedSubject` 자체의 material·판정불가 Entity revision, identity·World mismatch, Actor invalidation, visibility 또는 LOS loss는 evaluator stale retry가 아니다. Exact signal/cue를 정리한 뒤 retained Goal-owned `DisturbancePosition`을 resolve할 수 있으면 `identified_subject_invalid_recoverable → Search`를 적용한다. 복구 Target도 resolve할 수 없으면 `identified_subject_invalid_unrecoverable → Failed terminal`을 적용한다. Search에 복구한 disturbance Target에서 새 `SightAcquired`가 다시 증명돼야 current Entity revision으로 Resolve에 재진입할 수 있다.

### 3.5 Model Bundle과 NNE adapter

Production bundle은 기술 요구사항 §9.14의 파일과 hash 계약을 그대로 따른다.

UE 5.7의 v1 production provider는 `NNERuntimeORTCpu`로 고정한다. Project에는 `NNERuntimeORT` plugin과 `NNE` interface dependency가 enable됐고, synchronous `IModelInstanceCPU`의 `B=1` fixture adapter와 10-input·3-output descriptor 검증을 구현했다. `NNERuntimeORTDml`이나 다른 provider로 자동 fallback하지 않는다. Provider를 바꾸려면 별도 ORT↔NNE parity, latency, packaged smoke와 새 Freeze Manifest promotion이 필요하다. 승인된 production ModelData·Calibration/OOD bundle은 아직 없으며 UE 5.7 plugin descriptor의 Beta 표시는 남은 risk다. 이 둘은 packaged smoke·latency·Utility fallback Gate를 생략하는 근거가 아니다.

승격 순서:

1. fixture ONNX로 descriptor, binding, failure path를 RED→GREEN한다.
2. frozen dataset과 split manifest로 실제 model을 학습한다.
3. PyTorch↔ONNX Runtime parity를 통과한다.
4. ModelData로 import하고 NNE model creation을 검증한다.
5. ORT↔NNE golden output을 허용 오차 `abs≤1e-4`, `rel≤1e-4`로 비교한다.
6. Calibration/OOD asset을 frozen model과 exact hash로 결속한다.
7. packaged-runtime NNE provider에서 model creation과 inference smoke를 통과한다.

Fixture model이나 test-only evaluator는 `ResolvePolicyReady`를 열 수 없다.

---

<a id="4-production-executable-greet-계약"></a>
## 4. Production-executable Greet 계약

### 4.1 Target과 parameter

`Greet` v1은 다음 Registry 계약을 사용한다.

| 항목 | 값 |
|---|---|
| Goal/Phase | `InvestigateDisturbance.Resolve` |
| Skill | `Greet` (`SkillId=10`) |
| Target | current `IdentifiedSubject`의 exact `Entity` handle |
| LOS | Candidate 작성, Commit, Skill start에서 필요 |
| `duration` | normalized proposal을 `[1.0,5.0]s`로 decode, default `2.0s` |
| `speed` | inactive, positive zero |
| `preferred_distance` | inactive, positive zero |
| `intensity` | normalized proposal을 `[0.0,1.0]`로 decode, default `0.5` |

Target handle의 Entity revision은 Knowledge revision을 유지한다. GoalRevision으로 대체하면 안 된다.

### 4.2 gameplay effect

`Greet`는 단순한 log, Debug 표시 또는 즉시 성공이 아니다. 다음 production gameplay effect를 모두 실행한다.

1. exact Entity Actor를 focus target으로 설정한다.
2. server-authoritative `Greet` social signal을 exact `DecisionId + GoalToken + Entity Target`에 one-shot으로 시작한다.
3. source Guard가 소유한 configured world-space greeting cue state를 server world time의 `duration` 동안 활성화한다.
4. social signal은 source Guard와 Target Entity handle을 보존하며 Target 쪽 별도 receiver Component를 요구하지 않는다.
5. cue의 base marker는 `intensity=0`에서도 visible하다. `PresentationStrength=clamp(intensity,0,1)`은 cosmetic 강조 채널로 그대로 전달할 뿐 cue를 숨기거나 gameplay 값을 바꾸지 않는다.
6. signal이 시작됐고 authoritative cue state가 끝까지 정상 유지된 뒤에만 `SkillSucceeded`를 발행한다. Client render·ack callback은 success authority가 아니다.

`UAINativeNPCSocialActionComponent`는 current Host `SessionId`별 highest applied `DecisionId`와 그 `(GoalToken, SkillId, TargetHandle)` identity를 보존한다. SessionId 변경은 old authority를 닫은 뒤에만 high-water를 초기화한다. 새 `BeginGreet`는 current exact authority와 `DecisionId > highest applied`를 모두 만족해야 한다. 같은 identity 재호출이나 더 작거나 같은 DecisionId는 signal·cue를 다시 발행하지 않고 duplicate/stale로 거부한다. 보장은 in-process session-lifetime at-most-once이며 crash-durable exactly-once를 주장하지 않는다.

구현 소유권:

- `UAINativeNPCSocialActionComponent`: active social signal, exact identity, one-shot 시작·취소·완료
- `UAINativeNPCSkillExecutorComponent`: Commit된 parameter, Target, controller, lifecycle과 completion fact
- `FStateTreeAINativeNPCGreetTask`: StateTree start/tick/exit 연결
- production greeting cue asset: 실제 게임 경로의 visible effect

Social signal과 cue가 구성되지 않았거나 exact Entity Actor binding과 cue activation을 시작할 수 없으면 `Greet`는 production executable이 아니다.

### 4.3 start, success, cancel

Start 순서:

1. Commit Coordinator가 request deadline, Candidate hash, input hash, GoalToken, Entity Target와 기술 요구사항 §7.1의 Entity revision rule을 재검증한다.
2. Executor가 exact controller, owner Pawn, World, current Primary Target, visible Entity binding과 LOS를 재검증한다.
3. inactive parameter가 zero인지, active parameter가 Registry 범위인지 검사한다.
4. StateTree task와 SocialActionComponent가 exact Decision authority를 수락한다.
5. social signal과 cue를 시작한다.
6. 실제 effect start가 성공한 뒤에만 running Decision과 Skill start를 공개한다.

Success 조건:

- 같은 GoalToken, DecisionId, Skill과 Target authority가 유지된다.
- signal이 one-shot으로 정확히 한 번 시작됐다.
- decoded `duration`이 server world time으로 완료됐다.
- authoritative cue completion이 exact signal identity를 확인했다. Client presentation completion은 기다리지 않는다.
- target가 현재 같은 World의 valid Entity이며 Resolve Target identity가 유지된다.

Cancel/interrupt 조건:

- Goal change, authority loss, Target invalidation, LOS loss, executor quarantine 또는 StateTree exit가 발생하면 cue, focus와 social signal을 exact identity로 취소한다.
- 취소 후 `SkillSucceeded`를 발행하지 않는다.
- stale callback은 새 signal이나 새 Decision을 종료할 수 없다.
- 같은 DecisionId의 signal은 session lifetime에서 at-most-once다.

### 4.4 Resolve transition 결과

Machine-readable Goal contract는 구현 단계에서 다음 authority를 생성해야 한다.

`subject_identified` 성공으로 Primary Target을 `IdentifiedSubject`로 바꿔도 Goal-owned immutable `DisturbancePosition`은 recovery context로 유지한다. 이 handle과 position은 Resolve에서 public Primary Target이 아니며 Goal terminal/resume 전까지 TargetInvalidated recovery에만 사용한다.

| Trigger | accepted Skill/Target | 결과 |
|---|---|---|
| `SkillSucceeded` | exact current `Greet(Entity)` running Decision | `Return`으로 이동하고 `HomeWaypoint` 설치 |
| `TargetInvalidated` | current `IdentifiedSubject` invalid, retained Goal-owned `DisturbancePosition` resolvable | `Search`로 이동하고 조사 위치 Target을 원자적으로 복원 |
| `TargetInvalidated` | current `IdentifiedSubject` invalid, retained disturbance Target도 unresolvable | Goal을 `Failed`로 terminalize; Target 없는 `Search` 금지 |
| `SkillFailed` | exact current `Greet(Entity)`가 `TimedOut`, `AuthorityLost` 또는 `AssemblyInvalidated`로 종료 | Goal을 `Failed`로 terminalize |

외부 Goal 전환으로 인한 `Interrupted`는 stale old-Goal event로 처리하고 새 Goal을 변경하지 않는다.

---

<a id="5-commit과-실패-처리"></a>
## 5. Commit과 실패 처리

### 5.1 Commit 직전 재검증

다음 값은 exact-match해야 한다.

- Goal instance, GoalRevision, phase, PhaseGeneration과 lifecycle
- pending DecisionId, SnapshotRevision, CandidateSetHash와 InputContentHash
- current Knowledge revision의 exact match 또는 §7.1 `continuous_nonmaterial` 예외
- `IdentifiedSubject`의 Entity StableId, Generation, 허용된 Revision과 Actor binding
- current visible, same World, finite position과 LOS
- Resolve Primary Target와 Candidate Target
- generated Skill·Target compatibility와 production execution semantics
- active controller, owner Pawn, StateTree, Timer, handoff와 retry authority
- request deadline

하나라도 다르면 effect를 시작하지 않는다.

### 5.2 irreversible 경계

`Greet`의 첫 irreversible operation은 authoritative social signal publication이다.

- `subject_identified` Commit 전 readiness·assembly 실패는 mutation-free이며 old investigation phase, Target, Timer, Skill과 Decision/retry authority를 보존한다.
- Resolve Commit 뒤 signal publication 전 Greet assembly가 invalid면 SkillExecutor가 exact `SkillFailed(AssemblyInvalidated)`를 one-shot으로 발행한다. Goal은 `Failed` terminalize하고 guessed retry를 만들지 않는다.
- publication 뒤 start 조립이 실패하면 fake rollback이나 guessed retry를 하지 않는다.
- Host assembly, Executor, SocialAction, handoff, Decision/retry authority를 먼저 닫고 callback을 유발할 수 있는 StateTree stop과 presentation stop을 마지막에 수행한다.
- 외부 callback 뒤에는 Goal, Target, Knowledge, World, LOS와 exact execution authority를 다시 검사한다.
- drift가 있으면 success나 `Return`을 공개하지 않는다.

### 5.3 실패별 결과

| 실패 | 결과 |
|---|---|
| Neural unavailable/failed/abstained/invalid, total deadline 남음 | 같은 Snapshot Utility fallback 정확히 한 번 |
| Neural 반환 시 total deadline 만료 | Utility/Commit/Skill start 0건 |
| Utility도 선택 실패 | Commit/Skill start 없음, bounded fresh decision 정책 적용 |
| Commit stale/deadline | 결과 폐기, 새 Snapshot 한 번 재평가 |
| Commit 전 Target invalid | disturbance Target 복구 가능 시 `TargetInvalidated` → `Search`, 불가능 시 Goal `Failed` |
| Resolve Commit 뒤 effect start 전 assembly invalid | signal/cue 0건, exact `SkillFailed(AssemblyInvalidated)` → Goal `Failed`, 자동 retry 0건 |
| Effect start 후 Target/LOS invalid | signal/cue 취소, disturbance Target 복구 가능 시 `TargetInvalidated` → `Search`, 불가능 시 Goal `Failed` |
| Effect start 후 timeout/authority/assembly 실패 | authority quarantine, exact `SkillFailed` → Goal `Failed` |
| Unknown requirement/action/status | fail-closed, success 금지 |

Generated guard binding은 다음으로 고정한다.

| guard | fact source | accepted Skill/Target | requirements |
|---|---|---|---|
| `resolution_complete` | `SkillExecutor` | `Greet` / `Entity` / `IdentifiedSubject` | `ExactCurrentGoalToken`, `ExactCurrentDecisionId`, `ExactTargetIdentityAndRevision`, `CurrentIdentifiedSubjectBindingSatisfiesEntityRevisionRule`, `CurrentIdentifiedSubjectVisibleSameWorldAndLos`, `ExecutionStatusSucceeded` |
| `identified_subject_invalid_recoverable` | `GoalAuthority` | none / `Entity` / `IdentifiedSubject` | `ExactCurrentGoalToken`, `ExactCurrentPrimaryTarget`, `GoalOwnedIdentifiedSubjectResolverCannotResolve`, `GoalOwnedDisturbancePositionResolvable` |
| `identified_subject_invalid_unrecoverable` | `GoalAuthority` | none / `Entity` / `IdentifiedSubject` | `ExactCurrentGoalToken`, `ExactCurrentPrimaryTarget`, `GoalOwnedIdentifiedSubjectResolverCannotResolve`, `GoalOwnedDisturbancePositionCannotResolve` |
| `resolution_failed` | `SkillExecutor` | `Greet` / `Entity` / `IdentifiedSubject` | `ExactCurrentGoalToken`, `ExactCurrentDecisionId`, `ExactTargetIdentityAndRevision`, `CurrentIdentifiedSubjectBindingSatisfiesEntityRevisionRule`, `CurrentIdentifiedSubjectVisibleSameWorldAndLos`, `ExecutionStatusFailed`, `ExactFailureReason`; accepted reason은 `TimedOut|AuthorityLost|AssemblyInvalidated` |

Task 1 이후 `goal_gameplay_semantics_v1.scope.claims`는 executable unique guards `14`, unavailable unique guards `0`, executable transition bindings `18`, unavailable transition bindings `0`, effects `2`, production executable skills `6`, `full_guard_catalog_pass=true`여야 한다.

---

<a id="6-resolvepolicyready-조건"></a>
## 6. ResolvePolicyReady 조건

Runtime `ResolvePolicyReady`는 다음 조건의 AND다.

1. generated Goal/Skill/Schema hash와 Runtime generated header가 exact parity다.
2. Resolve production action mask에는 `Greet(Entity)`만 추가되고, exact current Greet의 `ContinueCurrentAction`만 control Candidate로 허용되며 hostile Resolve Skill은 제외돼 있다.
3. production Greet execution semantics와 Goal transition guard authority가 generated contract에 존재한다.
4. production SocialActionComponent, Greet StateTree task와 visible cue asset이 exact production Pawn에 조립돼 있다.
5. approved Model Bundle, ModelData, Calibration/OOD asset과 manifest hash가 일치한다.
6. NNE model instance가 생성됐고 10 input·3 output descriptor가 exact-match한다.
7. imported `ResolvePolicyFreezeManifest`의 scope, contract/model/calibration/Greet asset hash가 current package와 일치하고 `release_status=approved`다.

Runtime에서 한 번의 NNE inference가 실패하는 것은 evaluator status `Failed`이며 Utility fallback 대상이다. 반면 ModelData, descriptor, Calibration/OOD 또는 Greet assembly가 설치되지 않은 상태는 readiness false다.

Readiness는 구현자가 직접 true로 설정하는 flag가 아니다. Runtime은 테스트 로그를 직접 읽지 않고 위 production asset·contract·assembly와 promoted Freeze Manifest를 검사해 계산한다. Freeze Manifest는 §8.4의 Gate를 모두 통과한 뒤 promotion tool만 생성할 수 있다.

이 v1 Gate는 Resolve의 production inference·parameter·fallback 경로를 승인한다. Candidate action이 하나인 상태이므로 multi-action learned ranking의 자연스러움이나 다른 Goal·phase의 Neural rollout을 승인하지 않는다.

---

<a id="7-구현-순서"></a>
## 7. 구현 순서

이 문서 확정 전에는 아래 production 구현을 시작하지 않는다. 구현은 각 Task에서 RED를 먼저 확인한 뒤 GREEN으로 진행한다.

### Task 1. Machine-readable contract와 harness를 먼저 갱신

**변경 대상**

- `contracts/current/skill_registry_v1.yaml`
- `contracts/current/goal_registry_v1.yaml`
- `contracts/current/ai_native_npc_schema_v2_0.yaml`
- `tests/test_skill_execution_semantics_v1.py`
- `tests/test_goal_gameplay_semantics_v1.py`
- Schema output·decision hash 검사와 두 Registry generated contract generator, generated C++/Python/docs

**RED**

- `Greet` production semantics가 없으면 Resolve production mask가 비어야 한다.
- Resolve `SkillSucceeded`, `SkillFailed`, `TargetInvalidated` authority가 unavailable이면 readiness가 false여야 한다.
- Neural budget, fallback status와 bounded stale retry policy가 machine contract에 없으면 parity test가 실패해야 한다.
- Schema에 `tactical_context float32 [B,128]` output이 없거나 Model/Decision Contract Hash가 갱신되지 않으면 descriptor·parity test가 실패해야 한다.

**GREEN**

- `goal_gameplay_semantics_v1.production_skills.executable`에 `Greet` 하나만 추가한다.
- Schema/Goal/Skill과 두 semantics block의 version을 §3.1의 target version으로 함께 올린다. ID와 fixed 배열 크기 17/272는 바꾸지 않는다.
- `general_policy_orchestration`에 exact `GuardPhase0/InvestigateDisturbance/Resolve` rollout scope, Neural `20ms` budget, five-status same-Snapshot fallback, within-deadline Utility 1회·expired Utility 0회와 single-valid Calibration 정책을 추가하고, `decision_scheduling`에 total `40ms`와 one-fresh-retry 정책을 추가한다.
- Resolve의 `resolution_complete`를 exact current `Greet(Entity)` success authority로 바꾸고, 기존 `no_valid_belief`를 order 1 `identified_subject_invalid_recoverable` authority로 교체한다.
- Resolve order 2에 같은 `TargetInvalidated`를 받는 `identified_subject_invalid_unrecoverable → Failed terminal`, order 3에 exact current Greet의 `TimedOut|AuthorityLost|AssemblyInvalidated`만 받는 `resolution_failed`/`SkillFailed` terminal transition을 추가한다.
- 새 guard requirement `CurrentIdentifiedSubjectBindingSatisfiesEntityRevisionRule`, `CurrentIdentifiedSubjectVisibleSameWorldAndLos`, `GoalOwnedIdentifiedSubjectResolverCannotResolve`, `GoalOwnedDisturbancePositionResolvable`, `GoalOwnedDisturbancePositionCannotResolve`를 generated Runtime support 목록과 evaluator에 추가한다. Target/LOS invalid producer는 `TargetInvalidated`만 발행하고 같은 원인으로 `SkillFailed`를 발행하지 않는다. 두 event가 이미 queue에 함께 있어도 `resolution_failed`는 current visible·World·LOS requirement 때문에 Target invalid 상태에서 false이고, TargetInvalidated 전환 뒤 old SkillFailed는 stale phase result로 폐기된다.
- `skill_registry_v1.execution_semantics_v1`에 §4의 Greet duration·intensity·LOS·social signal·cue·success·cancel 계약을 추가한다.
- Schema output contract에 `tactical_context float32 [B,128]`를 세 번째 output으로 추가하고 feature/model/decision contract hash 산출물과 Golden descriptor를 함께 갱신한다.
- 그 밖에는 §3~§6의 exact 값만 YAML에 추가한다.
- generated output을 재생성하고 source YAML과 C++/Python/docs parity를 통과한다.
- `Warn`, `CallForHelp`, `Attack`은 production execution semantics에 추가하지 않는다.

### Task 2. Greet gameplay effect core를 TDD로 구현

**새 production type**

- `Execution/AINativeNPCSocialActionComponent.h/.cpp`
- `Execution/AINativeNPCGreetStateTreeTask.h/.cpp`

**수정 대상**

- `Execution/AINativeNPCSkillExecutorComponent.h/.cpp`
- exact production Guard Pawn 구성

**RED**

- material·판정불가 Entity revision, wrong World/LOS/DecisionId에서 disturbance Target 복구 가능 여부에 따른 Search/Failed exact 결과
- inactive nonzero parameter
- duplicate signal start
- target invalidation과 stale completion callback
- effect start 후 assembly failure

**GREEN**

- exact one-shot signal, focus, cue, duration, completion·cancel semantics을 구현한다.
- cue나 SocialAction assembly가 없으면 production start가 거부된다.
- intensity `0`과 `1`에서 base cue visibility와 exact `PresentationStrength` 전달을 검사한다.

### Task 3. Fixture NNE adapter를 TDD로 구현

**새 production type**

- `Policy/AINativeNPCPolicyModelData.h/.cpp`
- `Policy/AINativeNPCNNEPolicyEvaluator.h/.cpp`

**수정 대상**

- `NeuralGame.uproject`: `NNERuntimeORT` plugin enable
- `NeuralGame.Build.cs`: `NNE` interface dependency
- `Policy/DecisionPolicyOrchestrator.*`는 필요한 canonicalization만 확장하고 fallback 순서는 변경하지 않음

**RED**

- input/output 이름·순서·dtype·shape mismatch
- masked nonzero output, NaN/Inf, out-of-range score/parameter
- 20ms budget 초과
- Neural 반환이 total 40ms 안과 밖인 두 경계에서 Utility 호출이 각각 1·0건
- OOD, low confidence, wrong model/contract/calibration hash
- out-of-range 또는 masked selected Candidate
- valid count 0·1·2 이상에서 second score, adjusted gap과 entropy canonicalization

**GREEN**

- fixture model로 descriptor, inference, canonicalization, Calibration/OOD와 status mapping을 구현한다.
- fixture는 readiness를 열지 않는다.

### Task 4. Actual Model Bundle을 생성하고 검증

**작업**

1. current Schema/Registry로 Decision Capture dataset을 생성한다.
2. Resolve의 Greet score·duration·intensity label과 hostile/invalid/Target-loss case를 taxonomy와 case catalog에 추가한다.
3. split 누출, 최소 분모, OOD/Critical allowlist를 검증한다.
4. model, Calibration/OOD를 학습하고 freeze한다.
5. ONNX export, ORT parity, manifest hash와 evaluation gate를 통과한다.
6. `tools/promote_resolve_policy.py`와 manifest validator를 RED→GREEN한다. Tool은 §8.4의 required evidence ID와 current artifact hash가 모두 맞을 때만 Freeze Manifest를 쓴다.

실제 model과 calibration이 없는 fixture-only 상태는 production evaluator 완료가 아니다.

### Task 5. Production Host에 evaluator와 Greet를 연결

**수정 대상**

- `Execution/AINativeNPCGoalHostComponent.h/.cpp`
- `Execution/AINativeNPCSkillHandoffComponent.*`
- `Policy/AINativeNPCResolvePolicyFreezeManifest.h/.cpp`
- production StateTree와 ModelData/cue assets

**RED**

- evaluator null/invalid, material·판정불가 stale revision, Target drift, World drift, LOS loss
- Utility fallback exact-one
- same-call stale output reuse 금지
- one-fresh-retry 뒤 busy retry 금지
- Greet 성공·TargetInvalidated·SkillFailed generated transition
- callback 이후 authority 재검증과 quarantine ordering

**GREEN**

- validated production evaluator를 `FDecisionPolicyInput.NeuralEvaluator`에 설치한다.
- computed readiness만 `ResolvePolicyReady`에 사용한다.
- Greet effect start 성공 뒤에만 running Skill을 공개한다.

### Task 6. Asset과 production path를 검증

**필수 asset**

- approved policy ModelData: `/Game/AINativeNPC/Policy/MD_AINativeNPCResolvePolicyV1`
- Calibration/OOD Data Asset: `/Game/AINativeNPC/Policy/DA_AINativeNPCResolveCalibrationV1`
- imported Freeze Manifest Data Asset: `/Game/AINativeNPC/Policy/DA_AINativeNPCResolveFreezeV1`
- existing production StateTree `/Game/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff`의 Greet task branch
- visible cue asset: `/Game/AINativeNPC/UI/WBP_AINativeNPCGreetCueV1`
- exact Guard Pawn component binding

Asset authoring은 idempotent해야 한다. 마지막 Data Validation 뒤에는 asset writer를 실행하지 않는다.

---

<a id="8-검증-계획"></a>
## 8. 검증 계획

### 8.1 Focused Automation

최소 다음 case를 독립적으로 검증한다.

- action은 `Greet(Entity)`만 production-valid이고 exact running Greet의 `ContinueCurrentAction`만 control-valid
- Resolve 밖에서는 production Neural evaluator 호출 0건이고 기존 generated Utility 결과가 유지됨
- Neural `Selected`이면 Utility 호출 0
- unavailable/failed/abstained/invalid이고 deadline이 남으면 same-Snapshot Utility 호출 1
- Neural 반환 시 total deadline이 만료됐으면 Utility·Commit·Skill start 0
- masked/unknown/out-of-range/non-finite output 거부
- descriptor와 bundle hash mismatch 거부
- 20ms Neural budget과 40ms Commit deadline
- packaged production bundle 100 warmup/1,000 sample에서 p99 `<=20ms`, max `<=40ms`
- Primary Target이 여전히 resolvable인 material·판정불가 Knowledge dependency/Goal revision 폐기, `continuous_nonmaterial` 허용과 one fresh retry
- Primary Entity material·판정불가 revision은 fresh retry가 아니라 recoverable `TargetInvalidated → Search` 또는 unrecoverable Goal `Failed`
- second stale에서 busy retry 중단
- Greet exact Target/World/LOS/parameter start
- duplicate signal, stale callback, post-start Target invalidation
- success → `Return`, Target invalid → `Search`, operational failure → Goal `Failed`
- effect callback 이후 stale success publication 금지
- `WITH_DEV_AUTOMATION_TESTS=0`에서 test seams 부재

### 8.2 Broad 검증

순서는 다음과 같다.

1. Contract Python tests와 generated parity
2. Unreal Editor Development build
3. focused evaluator/Resolve/Greet Automation
4. 전체 `AINativeNPC` Automation
5. production PIE: `SightAcquired` → `Resolve` → Neural 또는 Utility → actual Greet cue → `Return`
6. Neural failure를 주입한 production-like PIE: Utility fallback → actual Greet
7. Target loss PIE with retained disturbance: cue 취소 → `Search`와 조사 Target 복원
8. Target loss hostile Automation with unresolvable disturbance: Target 없는 Search 0건, Goal `Failed`
9. Data Validation
10. packaged-runtime NNE model creation·inference smoke
11. Win64 Development non-editor build와 test-seam absence 검사
12. 최신 source·asset manifest의 독립 blocker review

### 8.3 증거 경계

- fixture ONNX 통과는 adapter 증거이며 production model 증거가 아니다.
- Automation 통과는 actual PIE cue와 effect 증거를 대신하지 않는다.
- PIE 통과는 Shipping 증거가 아니다.
- Shipping build/package/startup은 실제 배포 요청이 있을 때만 별도 Release gate로 수행한다.
- timeout, exit code `1`, 축약되어 결과를 확인할 수 없는 출력은 통과로 세지 않는다.

### 8.4 Promotion과 runtime readiness

다음 evidence가 모두 통과한 뒤 `tools/promote_resolve_policy.py`가 외부 `resolve_policy_freeze_manifest.json`을 생성한다.

1. fixture가 아닌 production bundle의 ORT↔NNE parity와 packaged-runtime smoke
2. 같은 packaged NNE provider에서 `B=1` 100회 warmup 뒤 1,000회 inference p99 `<=20ms`, max `<=40ms`; hardware·OS·driver·provider version 기록
3. focused hostile Automation과 전체 `AINativeNPC` Automation
4. production PIE와 Data Validation
5. Win64 Development non-editor build에서 test-only readiness override, evaluator, callback seam과 private-state access가 컴파일되지 않는 증거
6. 최신 source·contract·asset에 결속된 독립 blocker-0 검토

Canonical evidence index의 required ID는 `contract_tests`, `editor_build`, `ort_nne_parity`, `packaged_nne_smoke`, `nne_perf`, `focused_automation`, `broad_automation`, `production_build`, `production_pie`, `data_validation`, `independent_review`다. 각 entry는 `id`, `status=passed`, 결속된 `artifact_set_sha256`, 원본 `report_sha256`, 실행 또는 검토 handle과 시작·종료 시각을 가진다. 실행 evidence는 command와 exit code도 기록한다. Timeout, nonzero exit, missing full report와 artifact hash mismatch는 `passed`가 아니다.

`artifact_set_sha256`은 active Resolve plan·technical requirements, production AINativeNPC source와 project `.uproject`/`Build.cs`, 세 current contract YAML, generator source, generated Python/C++/contract manifest/contract appendices, Policy Manifest·Calibration/OOD, StateTree·Greet cue·exact Pawn assembly의 source artifact hash를 path UTF-8 ascending 순으로 `path NUL size_decimal NUL sha256_raw32` 연결 후 SHA-256한다. `policy_manifest.json`이 열거한 모든 Model Bundle 파일은 policy manifest hash를 통해 간접 결속한다. Evidence index, 아직 생성되지 않은 Freeze Manifest와 그 manifest에서 파생되는 runtime promotion-authority C++ header는 이 artifact set에서 제외해 순환 hash를 막는다.

Freeze Manifest 필드는 다음으로 고정한다.

```text
release_scope_id = GuardPhase0/InvestigateDisturbance/Resolve
release_status = approved
runtime_name = NNERuntimeORTCpu
runtime_plugin_version = 1.0
engine_version = 5.7
schema_contract_revision = 2.0.0-rc6
schema_sha256
goal_registry_sha256
skill_registry_sha256
policy_manifest_sha256
calibration_ood_asset_sha256
greet_asset_set_sha256
artifact_set_sha256
evidence_index_sha256
```

Promotion tool은 evidence 하나가 누락·실패·timeout이거나 hash가 current artifact와 다르면 아무 출력도 생성하지 않는다. 성공한 한 promotion 작업은 외부 `resolve_policy_freeze_manifest.json`과 그 manifest의 exact `artifact_set_sha256`·`evidence_index_sha256`를 담은 runtime promotion-authority C++ header를 함께 생성한다. import된 Data Asset은 문자열 status나 자기 hash 필드를 독립 authority로 믿지 않는다. Runtime은 compiled promotion-authority가 `approved`일 때만 Data Asset의 두 digest를 그 authority와 exact 비교하고, authority가 없거나 mismatch이면 `ResolvePolicyReady=false`를 유지한다.

---

<a id="9-완료-정의"></a>
## 9. 완료 정의

### 9.1 계획과 현재 상태의 일치

- 이 문서가 `docs/current`에 존재한다.
- 공통 구현 계획과 Unreal 구현 계획이 이 문서를 다음 vertical authority로 가리킨다.
- `Greet` v1, Neural/Utility fallback, stale 정책, hostility ownership, readiness와 검증 순서에 미결정 항목이 없다.
- §2는 현재 구현된 핵심 코드와 아직 없는 production rollout 요소를 구분한다.
- §7의 작업 순서는 구현 이력을 보존하고, 현재 완료·검증·잔여 상태는 §10이 관리한다.

### 9.2 구현 단계 완료

- machine-readable contract와 harness가 먼저 RED→GREEN이다.
- production model/NNE/Calibration/OOD와 Greet effect가 모두 실제 path에 있다.
- §8.4 evidence로 Freeze Manifest를 promotion한 뒤 `ResolvePolicyReady` computed gate가 test override 없이 true가 된다.
- actual `SightAcquired`에서 `IdentifiedSubject`를 설치하고 Neural 또는 Utility가 `Greet`를 Commit하며 visible gameplay effect를 실행한다.
- 성공, Target invalidation과 operational failure가 generated transition 결과와 일치한다.
- focused·broad·PIE·Data Validation·packaged NNE smoke와 최신 독립 review가 모두 완료된다.

이 완료 정의 전에는 production Resolve 행동을 준비됐다고 표현하지 않는다.

---

## 10. 현재 구현 상태

2026-08-23 기준 구현 상태는 다음과 같다.

### 10.1 완료된 기반

- RC6 Schema·Goal·Skill 계약, generated Python·C++·문서와 Golden descriptor를 갱신했다.
- `Greet(Entity)`의 SocialAction, world-space cue, focus, one-shot Decision ledger, completion·cancel과 StateTree task를 구현했다. committed start failure, post-start target destruction, cue/focus invalidation과 assembly quarantine은 exact Decision terminal result를 한 번만 publish한다. Apply 중 재진입한 quarantine은 consumed start를 `Failed/AssemblyInvalidated`로 끝내고 Running을 열지 않는다. Source-owned completion permit은 SocialAction만 생성하며 Executor는 읽기만 한다. Session 재등록 뒤 같은 DecisionId를 재사용해도 이전 Session callback은 거부한다.
- `NNERuntimeORTCpu` B=1 adapter, 10 input·3 output descriptor 검사, canonical output, Calibration/OOD status와 20ms budget을 구현했다.
- 전체 40ms deadline 안에서만 same-Snapshot Utility fallback을 한 번 허용한다.
- retained `DisturbancePosition` 기반 recoverable·unrecoverable `TargetInvalidated` transition과 one-fresh-retry 제한을 Host에 연결했다. recoverable 전이는 detached Runtime에서 준비하고 Search timer arm이 성공한 뒤 함께 publish하므로 timer 실패가 Search phase를 노출하지 않는다.
- Freeze Manifest와 production ModelData를 검사하는 computed readiness를 구현했다. Runtime promotion authority가 없거나 Data Asset digest와 compiled authority가 다르면 readiness는 false다.
- Resolve target/`IdentifiedSubject` authority, Greet lifecycle·callback·duplicate high-water 규칙과 Test Taxonomy·Catalog 의미를 등록 버전에 fail-closed로 고정했다. Generated C++은 Greet lifecycle을 publish하고 contract 문자열을 UTF-8 byte-safe literal로 생성한다.
- Promotion validator는 bundle·artifact·manifest symlink escape를 거부하고 Policy Manifest, Evidence Index와 각 report를 한 번 읽은 immutable byte snapshot으로 parse·hash한다. 실행 report도 `passed=true`, 빈 blocking finding, timeout·full-report·command·exit 조건을 동시에 만족해야 한다.
- fixture ONNX Bundle과 fixture ModelData는 adapter 검증 전용 경로에만 두었다. fixture는 production readiness를 열지 않는다.

### 10.2 현재 검증된 범위

- Contract·promotion test: 89개와 subtest 133개 통과
- Resolve/Greet/NNE focused Automation 통과
- 전체 `AINativeNPC` Automation: 166개 통과
- 기존 production vertical PIE 회귀 통과
- Data Validation: 301 assets, error 0, warning 0
- Win64 Development Editor와 non-editor build 통과
- ML candidate: 7개 Snapshot × 5회 Provider 판정, strict-valid 35회, Teacher Silver 6개와 사용자 검토 low-identity Human Gold 1개. 모든 candidate shard는 `--require-production`에서 거부
- low-identity Human Gold 1-row persistence 검증 완료. 이 결과는 candidate 저장 증거이며 production Dataset·Provider 승인 근거가 아니다.

### 10.3 남은 production Gate

- immutable Provider revision 기반 전체 Gold qualification: 12개 Role×Goal group마다 100개 이상, 총 1,200개 이상과 ML 데이터 계획 §11의 품질 기준 충족
- Unreal rollout Capture와 synthetic-real parity, family-aware split·중복·누수 검사
- frozen gameplay Decision Capture dataset 기반 production model과 Calibration/OOD 승격
- approved production ModelData, Calibration/OOD, Freeze Manifest와 `WBP_AINativeNPCGreetCueV1`
- production StateTree의 explicit Greet branch 저장·readback
- actual Resolve Greet PIE, Target-loss PIE와 packaged production NNE smoke
- §8.4 전체 evidence index와 최신 독립 blocker-0 검토

위 항목이 끝나기 전에는 `ResolvePolicyReady=false`이며 actual production Resolve 행동 경로는 dormant다.
