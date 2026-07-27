# AI Native NPC 의사결정 시스템
## 요구사항·구현 계약·Schema 2.0 통합 기준서

- 문서 버전: **v0.3.0**
- 상태: **Phase 0 구현 승인 / Schema 2.0 동결 후보**
- 개정일: 2026-07-26
- 대체 관계: 본 문서는 `ai_native_npc_requirements_implementation_plan_v0.2_reviewed.md`와 `v0.3_schema_freeze` 보완 메모를 **전체 대체**한다.
- 권위 규칙: 구현자는 이전 문서와 병합 해석하지 않고 본 문서와 동봉된 `ai_native_npc_schema_2_0.json`만 사용한다.
- V1 정책: Event Buffer 사용, GRU 미사용, 감정·관계 read-only, padded Tensor 고정, 서버 권위, 모델 출력은 Candidate raw score만 제공

---

# 0. 리뷰 타당성 및 최종 판정

제시된 리뷰는 모두 타당하다. 특히 “방향을 정의했다”와 “실제로 코딩 가능한 계약을 고정했다”는 서로 다른 단계라는 지적이 정확하다. 본 개정은 선언 수준이던 항목을 field, enum, 상태전이, 공식, byte serialization, 통계 Gate로 내린다.

| 리뷰 항목 | 판정 | v0.3 조치 |
|---|---|---|
| Typed Target payload 부재 | 타당 | Kind별 runtime payload, stable ID/generation, encoder payload 8차원, Skill 호환표 고정 |
| Target 16개 선정 규칙 부재 | 타당 | Target Universe→Slotter→Candidate Universe, mandatory·quota·fixed-point retention·hysteresis 고정 |
| Goal 관리자 계약 부재 | 타당 | 단일 Active Goal, arbitration, preemption, phase transition, revision 규칙 고정 |
| Calibration/OOD 순서 충돌 | 타당 | Raw→Adjusted→Select→OOD→Calibration→Accept/Abstain으로 확정 |
| Atomic Commit 예외 부재 | 타당 | 서버 game thread transaction, rollback, reservation lease, dirty/urgent/cancellation 계약 고정 |
| Hidden Information Commit 누출 | 타당 | Target Kind별 Commit 정보 허용표와 LastKnown immutable 규칙 추가 |
| Tensor/Hash 미동결 | 타당 | Schema 2.0 실제 shape·dtype·index·enum·padding·hash byte sequence 고정 |
| KPI 통계 계약 부재 | 타당 | Baseline hash, margin, 95% CI, group 최소 표본, Critical Suite 분모 고정 |
| v0.2와 보완판 분리 | 타당 | 본 문서를 v0.2 전체를 대체하는 유일한 권위 문서로 지정 |
| 기간·의존성·Owner 부재 | 타당 | 단계별 RACI, 의존성, person-week 계획 가정 추가 |

## 0.1 승인 상태

- **Phase 0 MVP Vertical Slice:** GO
- **Schema 2.0 코드 생성:** 본 문서의 Golden Vector 통과 후 GO
- **본 학습 데이터 대량 생성:** Schema source hash와 Skill/Post-process hash가 Freeze Registry에 등록된 뒤 GO
- **Phase 1 V1:** Phase 0 Exit Gate 이후 GO

---

# 1. 목표와 책임 경계

## 1.1 목표

상황별 선호 분기를 코드로 모두 작성하지 않고, NPC가 실제로 지각한 상태와 코드가 소유한 Goal 안에서 신경망이 전술 Candidate를 Ranking하도록 한다.

## 1.2 책임 분리

```text
Authoritative World / Quest / Server
        ↓
Perception → Belief State
        ↓
Goal Manager & Arbitration
        ↓
Typed Target Universe
        ↓
Deterministic Target Slotter
        ↓
Canonical Candidate Universe
        ↓
Neural Raw Score + Utility Baseline
        ↓
Switch Cost / OOD / Calibration / Abstain
        ↓
Atomic Validate-Reserve-Start
        ↓
Skill Executor / Result / Event Buffer
```

### 코드가 소유

- Ground Truth와 서버 권위
- Belief 수명주기
- Goal 생성·선점·중단·재개·완료
- Typed Target snapshot
- Target slotting과 hard mask
- Skill 실행과 자원 예약
- 감정·관계 상태 전이
- Commit transaction

### 모델이 소유

- 현재 Active Goal 안에서 Candidate raw utility score
- Target 선택은 Candidate Ranking의 결과로만 수행
- V1에서는 권위 상태나 Skill parameter를 직접 변경하지 않음

---

# 2. Ground Truth와 Belief 계약

## 2.1 외부 상태의 필수 메타데이터

```text
value / source / observed_at / age / confidence / valid_until / uncertainty
```

모델의 모든 외부 대상 Feature는 Belief에서 생성한다. 숨은 Actor의 실제 Transform, 정확한 체력·탄약, 미확인 sound instigator는 입력하지 않는다.

## 2.2 Believed Position 원칙

- `SightCurrent`: 현재 센서가 성공한 동안에만 Actor Transform을 감지 위치로 갱신
- `HearingEvent`: immutable sound location
- `LastSeenMemory`: Sight Lost 순간의 immutable snapshot
- `SharedKnowledge`와 `ScriptedKnowledge`: 전달 시각·confidence·TTL 필수
- `Inferred`: 추론 출처와 uncertainty 필수

Path, LOS, 거리, Pair Feature는 **Ground Truth가 아닌 Believed Position**으로 계산한다.

## 2.3 실행 경계 누출 방지

| Target Kind | Commit 시 허용되는 최신 정보 | 금지되는 정보 | 대표 실패 코드 |
|---|---|---|---|
| `None` | NPC 자기 상태, Goal/권한 | 외부 target 조회 | `PreconditionChanged` |
| `Entity` | 존재·generation·alive 권위 상태, **현재 센서가 허용한** perceived position/visibility/LOS, authorized tracking | 시야가 없는 Actor의 실제 Transform·Velocity·거리 | `TargetGenerationChanged`, `PerceptionRequirementChanged` |
| `SoundEvent` | immutable event location, TTL, 정적 world/nav | instigator 현재 Transform, 숨은 Actor LOS | `TargetInvalid`, `PathUnavailable` |
| `LastKnownPosition` | immutable snapshot, TTL, 정적 world/nav | origin Actor 현재 위치·이동·사망을 이유로 위치 변경/취소 | `TargetInvalid`, `PathUnavailable` |
| `CoverSlot` | slot generation, reservation epoch, occupancy, 접근 경로; 적 위치는 Belief만 사용 | 숨은 적 Ground Truth를 이용한 exposure | `ReservationConflict`, `PathUnavailable` |
| `SmartObject` | definition generation, availability, reservation, 접근 경로 | 관련 Actor의 비지각 상태 | `ReservationConflict`, `TargetGenerationChanged` |
| `Waypoint` | graph revision, position, nav | 관련 숨은 Actor 상태 | `TargetGenerationChanged`, `PathUnavailable` |
| `WorldPosition` | immutable position, owner Goal revision, nav | owner Actor의 숨은 현재 위치 | `GoalChanged`, `PathUnavailable` |

---

# 3. Goal Manager와 장기 행동 계약

## 3.1 Goal lifecycle

`Inactive`, `Active`, `Suspended`, `Succeeded`, `Failed`, `Aborted`를 사용하며, 한 NPC는 동시에 **Active Goal 하나**만 가진다. Suspended Goal은 최대 8개를 보유한다.

## 3.2 Goal proposal과 Arbitration

Goal priority는 `0..1000` 정수이며 높은 값이 우선이다. Arbitration은 Goal proposal 또는 권위 이벤트가 변할 때 수행한다.

정렬 순서:

1. eligible=true
2. priority 내림차순
3. Goal class: `Emergency(0)`, `QuestCritical(1)`, `Combat(2)`, `Social(3)`, `Ambient(4)`
4. created_sequence 오름차순
5. Goal UUID lexicographic 오름차순

Preemption 조건:

- `force_preempt=true`
- 새 Goal class가 Emergency이고 Active Goal이 Emergency가 아님
- `new.priority >= active.priority + 50`
- Active Goal이 더 이상 진행 불가 또는 terminal timeout

동점 Goal은 Active Goal을 선점하지 않는다. Active Goal이 종료된 뒤 동일 정렬 규칙으로 다음 Goal을 선택한다.

## 3.3 상태 전이

| Current | Trigger | Guard | Next | 처리 |
|---|---|---|---|---|
| Inactive | ArbitrationSelected | eligible=true | Active | OnActivated phase row 실행, revision +1 |
| Active | HigherPriorityGoal | force 또는 priority gap≥50 | Suspended 또는 Aborted | resumable이면 Suspended, 아니면 Aborted |
| Active | PhaseTransition | transition row guard=true | Active/new phase | phase와 target/mask를 한 transaction으로 변경, revision +1 |
| Active | GoalSucceeded | terminal guard=true | Succeeded | resource release, revision +1 |
| Active | GoalFailed/Timeout | failure guard=true | Failed | failure reason 기록, revision +1 |
| Suspended | ArbitrationSelected | still eligible & resumable | Active | Resume hook, revision +1 |
| Suspended | Invalid/Expired | true | Aborted | resource release, revision +1 |
| Succeeded/Failed/Aborted | Archive | retention elapsed | Inactive/removed | active revision에 영향 없음 |

Goal Definition은 다음 순서의 transition row를 가진다.

```text
row_priority desc → row_id asc → first guard true row만 실행
```

Trigger는 `OnActivated`, `OnEvent`, `OnSkillResult`, `OnTimeout`, `OnTargetInvalid`, `OnCommand` 중 하나다. 한 이벤트당 최대 한 row만 전이한다.

### 3.3.1 Transition row schema

```cpp
struct FGoalPhaseTransitionRow
{
    uint16 RowId;
    int16 RowPriority;
    EIntentPhase FromPhase;
    EGoalTrigger Trigger;
    FGameplayTag TriggerFilter;
    FName GuardId;
    EIntentPhase NextPhase;
    EGoalTerminalOutcome TerminalOutcome; // None/Succeeded/Failed/Aborted
    uint16 NextAllowedSkillMask;
    uint16 NextForbiddenSkillMask;
    EGoalTargetMutation TargetMutation;
    float NewDeadlineSeconds; // -1이면 유지
};
```

Guard는 등록된 순수 함수이며 Belief Snapshot, Goal state, SkillResult만 읽는다. 월드에 side effect를 만들지 않는다. Transition action은 phase, mask, target, deadline을 하나의 Goal mutation transaction으로 적용한다.

### 3.3.2 Phase 0 Goal 정의

#### `IdlePatrol`

| From | Trigger | Guard | Next/Outcome | Allowed Skill |
|---|---|---|---|---|
| Observe | OnActivated | always | Observe | Idle, Maintain, LookAt, TurnTo |
| Observe | OnEvent(SoundHeard) | confidence≥0.3 | Goal proposal `InvestigateDisturbance` 생성 | 현재 phase 유지 |
| Observe | OnEvent(DamageReceived) | always | Emergency/Combat Goal proposal 생성 | 현재 phase 유지 |
| Observe | OnCommand(StopPatrol) | always | Succeeded | — |

#### `InvestigateDisturbance`

| From | Trigger | Guard | Next/Outcome | Allowed Skill | Deadline |
|---|---|---|---|---|---:|
| Orient | OnActivated | target valid | Orient | Maintain, LookAt, TurnTo, CallForHelp | 1.5s |
| Orient | OnSkillResult | LookAt/TurnTo Succeeded | Approach | Maintain, Approach, Investigate | 10s |
| Orient | OnTimeout | target valid | Approach | Maintain, Approach, Investigate | 10s |
| Approach | OnEvent | distance≤acceptance radius | Search | Maintain, LookAt, TurnTo, SearchArea | 5s |
| Approach | OnSkillResult | PathUnavailable | Failed | — | — |
| Approach | OnTargetInvalid | TTL expired | Failed | — | — |
| Search | OnEvent(SightAcquired) | perceived entity valid | Resolve | Maintain, LookAt, TurnTo, Warn, CallForHelp | 3s |
| Search | OnTimeout | home target valid | Return | Maintain, Approach | 15s |
| Return | OnEvent | home distance≤acceptance radius | Succeeded | — | — |
| Return | OnSkillResult | PathUnavailable | Failed | — | — |

Phase 0에서는 동일 event에 여러 row가 매칭되면 `RowPriority desc → RowId asc` 순서의 첫 row만 실행한다.

## 3.4 Revision 규칙

Goal mutation은 서버 game thread의 단일 transaction으로 처리하며, 한 transaction에서 여러 필드가 바뀌어도 revision은 정확히 한 번 증가한다.

| 변경 | Revision 증가 | 설명 |
|---|:---:|---|
| Active Goal instance 변경 | ✓ | 기존 Goal 종료·preempt·새 Goal 활성화 포함 |
| Lifecycle state 변경 | ✓ | Active↔Suspended, terminal outcome 포함 |
| Intent phase 변경 | ✓ | phase transition transaction당 1회 |
| authoritative Goal target handle 변경 | ✓ | Stable ID 또는 generation 변경 |
| allowed/forbidden Skill bitmask 변경 | ✓ | phase transition과 같은 transaction이면 총 1회만 증가 |
| authoritative deadline 변경 | ✓ | countdown 감소가 아니라 명령·정책에 의한 deadline 값 변경 |
| Goal definition version/hot reload 변경 | ✓ | Shipping에서는 hot reload 금지, 개발 빌드에서만 허용 |
| progress float 변경 | — | 비동기 응답을 매 tick stale로 만들지 않음 |
| elapsed/time remaining 파생값 변경 | — | deadline 자체가 같으면 증가하지 않음 |
| Belief confidence/age 변화 | — | Belief revision이 별도 담당 |
| Debug/UI 필드 변경 | — | 권위 상태가 아님 |

---

# 4. Typed Action Target 계약

## 4.1 Handle

```cpp
enum class EActionTargetKind : uint8
{
    None = 0,
    Entity = 1,
    SoundEvent = 2,
    LastKnownPosition = 3,
    CoverSlot = 4,
    SmartObject = 5,
    Waypoint = 6,
    WorldPosition = 7
};

struct FActionTargetHandle
{
    EActionTargetKind Kind;
    uint64 StableId;
    uint32 Generation;
};
```

Handle 비교는 `(Kind, StableId, Generation)`의 완전 일치다. Event Buffer는 Target slot 번호를 저장하지 않고 이 Handle을 저장한다. Tensor 생성 시 현재 Target slot에 재매핑하며, 없으면 `event_target_index=16`으로 기록한다.

## 4.2 Kind별 Runtime payload

| Kind | Stable ID / Generation | 필수 Runtime Payload | 불변성·만료 규칙 |
|---|---|---|---|
| `None` | ID=0, Generation=0 | payload 없음 | `NoTarget` 전용. Target 슬롯에는 넣지 않고 index 16으로 표현 |
| `Entity` | 서버 NetGUID 또는 PersistentActorID / Spawn Generation | actor handle, belief source, perceived position, observed_at, valid_until, visibility, LOS belief, estimated velocity, alive/weapon/health belief | 숨은 동안 Actor Transform으로 갱신 금지. Sight를 잃으면 Candidate용 EntityTarget을 제거하고 LastKnownPosition snapshot 생성 |
| `SoundEvent` | 서버 단조 증가 64-bit EventID / 0 | immutable location, event type, created_at, loudness, max range, attribution handle optional, attribution confidence, TTL | event location은 instigator를 따라가지 않음. TTL 만료 시 invalid |
| `LastKnownPosition` | Hash(origin handle, sight-memory sequence) / memory revision | immutable position, origin handle optional, source, observed_at, confidence, uncertainty radius, TTL, last observed heading/speed | 생성 후 위치 불변. Actor 현재 위치·이동·LOS 조회 금지 |
| `CoverSlot` | Persistent CoverSlot GUID / slot topology generation | approach position, cover normal, height class, exposure belief, availability snapshot, reservation epoch | topology generation 불일치 시 invalid. Reservation epoch는 Commit에서 재검증 |
| `SmartObject` | SmartObject Slot GUID / definition generation | interaction type, approach transform, availability, reservation epoch, interaction radius | definition generation·availability·reservation 재검증 |
| `Waypoint` | Persistent Waypoint GUID / graph revision | position, acceptance radius, semantic type, graph revision | graph revision 불일치 또는 asset unload 시 invalid |
| `WorldPosition` | 서버 생성 SnapshotID / owner Goal revision | immutable position, acceptance radius, semantic type, created_at, valid_until | Goal revision 변경 또는 TTL 만료 시 invalid |

## 4.3 Tensor payload 8차원

| Kind | `kind_payload_0..7` 의미 |
|---|---|
| `None` | 모두 0 |
| `Entity` | player, npc, ally, enemy, neutral, observed_attacking, observed_fleeing, observed_in_cover |
| `SoundEvent` | footstep, gunshot, explosion, voice, door, impact, machinery, other |
| `LastKnownPosition` | source_sight, source_shared, source_scripted, uncertainty_radius_norm, last_speed_norm, last_heading_sin, last_heading_cos, immutable_flag=1 |
| `CoverSlot` | low_cover, high_cover, cover_normal_sin, cover_normal_cos, exposure_belief, occupancy_belief, peek_available, destructible_belief |
| `SmartObject` | door, seat, console, pickup, heal_station, dialogue_spot, climb, other |
| `Waypoint` | patrol, retreat, rally, exit, search_anchor, escort, home, other |
| `WorldPosition` | generic, investigate, flee, formation, quest, dialogue, hazard_avoidance, other |

## 4.4 Skill–Target Kind 호환

| Skill ID / Skill | None | Entity | SoundEvent | LastKnownPosition | CoverSlot | SmartObject | Waypoint | WorldPosition | Commit rule |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 0 `Idle` | ✓ | — | — | — | — | — | — | — | `SelfOnly` |
| 1 `MaintainCurrentExecution` | ✓ | — | — | — | — | — | — | — | `CurrentExecutionMustRemainValid` |
| 2 `LookAt` | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | `UseKindSpecificPosition` |
| 3 `TurnTo` | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | `UseKindSpecificPosition` |
| 4 `Approach` | — | ✓ | — | ✓ | — | ✓ | ✓ | ✓ | `PathToBelievedPosition` |
| 5 `KeepDistance` | — | ✓ | — | — | — | — | — | — | `CurrentPerceivedEntityRequired` |
| 6 `RetreatFrom` | — | ✓ | — | ✓ | — | — | — | — | `UseBelievedPosition` |
| 7 `Follow` | — | ✓ | — | — | — | — | — | — | `CurrentPerceivedOrAuthorizedTracking` |
| 8 `Investigate` | — | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | `PathToImmutableSnapshot` |
| 9 `SearchArea` | — | — | — | ✓ | — | — | ✓ | ✓ | `PathToImmutableSnapshot` |
| 10 `Greet` | — | ✓ | — | — | — | — | — | — | `CurrentVisibleEntityRequired` |
| 11 `Warn` | — | ✓ | — | — | — | — | — | — | `CurrentVisibleEntityRequired` |
| 12 `CallForHelp` | ✓ | — | — | — | — | — | — | — | `SelfOnly` |
| 13 `TakeCover` | — | — | — | — | ✓ | — | — | — | `ValidateAndReserveCover` |
| 14 `Flee` | — | — | — | — | — | — | ✓ | ✓ | `PathToBelievedPosition` |
| 15 `Attack` | — | ✓ | — | — | — | — | — | — | `CurrentVisibleEntityAndLOSRequired` |

`MaintainCurrentExecution`은 현재 Executor를 유지하는 special control Candidate다. 현재 실행 중인 Skill과 동일한 `(Skill, Target Handle)` Candidate는 별도로 생성하지 않고 `HardMaskReason=CurrentExecutionDuplicate`로 mask한다.

---

# 5. Target Universe와 Target Slotter

## 5.1 Pipeline

```text
Belief / Goal / Resource Snapshot
→ Target Universe
→ Dedupe
→ Mandatory Preserve
→ Type Quota
→ Shared Overflow
→ Slot Hysteresis
→ 16 Target Slots
→ Candidate Universe
```

## 5.2 Dedupe

기본 key는 `(Kind, StableId, Generation)`이다. 동일 key가 여러 역할을 가지면 Target 하나에 mandatory flag를 OR하고 가장 높은 mandatory rank를 보존한다. Sight Lost 시 EntityTarget을 유지한 채 LastKnown을 중복 생성하지 않고, Entity Candidate를 제거한 뒤 새 LastKnown snapshot으로 교체한다.

## 5.3 Mandatory Preserve

우선순위가 낮은 숫자일수록 먼저 보존한다.

| Rank | Mandatory target |
|---:|---|
| 0 | Active Goal authoritative target |
| 1 | Current executing Skill target |
| 2 | 최근 3초 내 Current Attacker |
| 3 | Active Dialogue/Interaction target |
| 4 | 현재 NPC가 소유한 Reserved Resource |

Mandatory가 16개를 넘으면 다음 순서로 16개를 보존한다.

```text
mandatory rank asc
→ confidence desc
→ observed_at desc
→ kind id asc
→ stable id asc
→ generation asc
```

이 경우 `TargetMandatoryOverflow`를 기록하고 Neural Policy는 abstain하며 Goal별 안전 fallback을 사용한다. Critical Suite에서는 overflow 0건이 요구된다.

## 5.4 Type quota

| Kind | Base quota | Retention 후보 예시 |
|---|---:|---|
| Entity | 6 | 현재 보이는 Actor, authorized tracking Entity |
| SoundEvent | 2 | 최근 유효 Sound Event |
| LastKnownPosition | 2 | TTL이 남은 immutable snapshot |
| CoverSlot | 2 | Belief 기반 접근 가능한 Cover |
| SmartObject | 1 | 현재 Goal에서 사용 가능한 slot |
| Waypoint | 1 | Goal/Navigation waypoint |
| WorldPosition | 1 | Goal 또는 event가 만든 immutable position |
| Shared overflow | 1 | quota 충족 후 전체 잔여 중 최고 retention |
| 합계 | 16 | `NoTarget`은 슬롯 밖 index 16 |

Mandatory target은 quota를 초과할 수 있다. quota는 최대치가 아니라 비Mandatory target을 위한 최소 보존 시도다.

### 5.4.1 정확한 선정 알고리즘

```text
Input: deduped valid Target Universe U, previous_slot_map
Output: selected handles S (max 16), slot_map[16]

1. M = mandatory targets sorted by mandatory comparator
2. if |M| > 16:
     keep first 16, set MandatoryOverflow, Neural abstain, go to slot assignment
3. S = M
4. for kind in [Entity, SoundEvent, LastKnownPosition, CoverSlot, SmartObject, Waypoint, WorldPosition]:
     need = max(0, base_quota[kind] - count_kind(S, kind))
     add first `need` targets from (U-S) of that kind sorted by retention comparator
     stop immediately when |S| == 16
5. if |S| < 16:
     add targets from all (U-S), sorted by retention comparator, until |S| == 16 or U exhausted
6. selected target가 16개 미만이면 나머지 slot은 padding
7. 이전 slot에 존재하는 selected handle을 같은 slot에 먼저 배치
8. 나머지 selected handle은 선정 순서대로 가장 낮은 free slot에 배치
```

각 단계는 동일한 fixed-point score와 tie-break를 사용한다. 플랫폼별 associative container 순회 순서는 절대 선정 순서로 사용하지 않는다.

## 5.5 Retention score

Role, Personality, Relationship, 행동 선호는 사용하지 않는다. 정보 보존용 신호만 사용한다.

각 입력을 `q(x)=floor(clamp(x,0,1)*1000+0.5)`로 정수 양자화한다.

```text
R = 30*q(confidence)
  + 25*q(recency)
  + 20*q(source_reliability)
  + 15*q(proximity)
  + 10*q(previously_slotted)
```

- `recency = clamp(1-age/TTL,0,1)`
- `proximity = 1-clamp(distance/3000cm,0,1)`; 비공간 target은 0.5
- source reliability: Sight/Scripted=1.0, Shared=0.8, Hearing=0.7, LastSeen=0.6, Inferred=0.4, Unknown=0
- `previously_slotted=1`이면 1, 아니면 0

동점 정렬:

```text
R desc → kind id asc → stable id asc → generation asc
```

## 5.6 Slot hysteresis와 canonical slot

1. 최종 선택 Handle 집합을 먼저 결정한다.
2. 이전 판단에서 같은 Handle이 같은 slot에 있었고 slot이 비어 있으면 그 slot을 유지한다.
3. 나머지는 선정 순서대로 가장 낮은 빈 slot에 배치한다.
4. 이전 slot map이 없으면 모두 선정 순서대로 배치한다.

탈락 사유는 `Invalid`, `Expired`, `Deduplicated`, `QuotaNotReached`, `LowerRetentionScore`, `MandatoryOverflow`, `CapacityOverflow` 중 하나로 기록한다.

## 5.7 Target Recall

- 전체 Target Recall 목표: 99.5% 이상
- Critical Suite: 100%
- 분모는 Gold/DAgger가 지정한 acceptable target handle 수
- Target miss는 모델 오류가 아니라 Slotter 오류로 보고한다.

---

# 6. Canonical Candidate Universe

## 6.1 용량과 순서

```text
Skill Count       16
Target Slot       16
NoTarget Index    16
Target Ref Count  17
Candidate Count   16 × 17 = 272
```

Candidate index는 고정식으로 계산한다.

```text
candidate_index = skill_id * 17 + target_ref_index
```

- `target_ref_index 0..15`: Target slot
- `target_ref_index 16`: NoTarget
- 모든 272 entry가 항상 존재하며 invalid entry는 `candidate_mask=0`
- padded Tensor만 사용하며 ragged batch는 Schema 2.0에서 금지

## 6.2 Hard Mask

Candidate Generator는 Skill–Kind 호환, Goal mask, capability, cooldown, target validity, perception requirement, authority, resource requirement 같은 하드 조건만 판단한다. 자연스러운지 여부는 판단하지 않는다.

`HardMaskReason` enum은 Schema Appendix와 JSON source를 따른다.

## 6.3 Candidate Recall

- Any-Acceptable Candidate Recall ≥99.5%
- Full Acceptable Recall을 별도 보고
- Critical Suite N≥500 version-fixed scenario에서 100%
- Candidate miss 이유는 Perception, Target Slotter, compatibility, Goal scope, mask, registry mismatch로 분해한다.

---

# 7. Skill Executor 계약

## 7.1 Interface

```cpp
interface INPCSkill
{
    bool CanGenerateCandidate(const FNPCContextSnapshot&, const FActionTargetSnapshot&) const;
    FSkillExecutionPlan BuildExecutionPlan(const FNPCContextSnapshot&, const FActionTargetSnapshot&) const;
    FSkillValidationResult ValidateAtCommit(const FSkillExecutionPlan&, const FNPCCommitContext&) const;
    FSkillReservationResult TryReserveResources(const FSkillExecutionPlan&);
    FSkillStartResult Start(const FSkillExecutionPlan&);
    ESkillStatus Tick(float DeltaTime);
    bool CanSuspend() const;
    void Suspend(ESuspendReason);
    FSkillResumeResult Resume();
    void Cancel(ECancelReason);
    void ReleaseResources();
    FSkillResult GetResult() const;
};
```

## 7.2 실행 규칙

- `BuildExecutionPlan`은 side effect가 없다.
- `ValidateAtCommit`은 Target Kind별 허용 정보만 사용한다.
- Reservation은 canonical resource handle 순서로 획득한다.
- `Start` 실패 시 transaction이 모든 예약과 executor state를 rollback한다.
- 실패 reason은 Schema enum으로 기록한다.

---

# 8. V1 Neural Policy

## 8.1 입력 Tensor

| Name | Shape | dtype | 비고 |
|---|---|---|---|
| `global_state` | `[B,160]` | float32 | self/profile/goal/current execution |
| `target_features` | `[B,16,64]` | float32 | typed target common + kind payload |
| `target_mask` | `[B,16]` | float32 | 0/1 |
| `event_features` | `[B,16,32]` | float32 | 최근 10초, 최대 16 event |
| `event_target_index` | `[B,16]` | int64 | 0..15, unresolved/none=16 |
| `event_mask` | `[B,16]` | float32 | 0/1 |
| `candidate_features` | `[B,272,48]` | float32 | canonical candidate metadata/pair features |
| `candidate_target_index` | `[B,272]` | int64 | `candidate_index % 17` |
| `candidate_mask` | `[B,272]` | float32 | 0/1 |

## 8.2 출력 Tensor

| Name | Shape | dtype | 계약 |
|---|---|---|---|
| `candidate_raw_scores` | `[B,272]` | float32 | `4*tanh(logit)`, 범위 `[-4,4]` |

V1.0은 score-only다. duration, speed, emotion, relationship delta Head는 포함하지 않는다. Skill parameter는 Data Asset 기본값을 사용한다.

## 8.3 Encoder

```text
global_state 160 → MLP → 128

target common 0..55 → Common MLP → 64
kind payload 56..63 → Kind별 8→16 encoder 8개를 one-hot weighted sum
common 64 + payload 16 → Fusion → target embedding 64
16 targets → masked attention → 128

event 32 → MLP 48
stable event handle → current target slot gather; unresolved는 learned embedding
events → temporal attention → 96

goal/context from global → 32
previous execution from global → 32

concat 128+128+96+32+32 = 416
→ Fusion 416→256→128 Tactical Context

candidate 48→64
candidate target gather 64; NoTarget learned embedding 64
context 128 + candidate 64 + target 64 = 256
→ Score MLP 256→128→64→1
→ 4*tanh
```

Target kind payload encoder는 8개 MLP를 모두 계산한 뒤 TargetKind one-hot으로 weighted sum하여 ONNX에서 결정적 분기를 유지한다.

## 8.4 모델 크기

- 0.5M~2.0M parameter
- FP32 raw weight 최대 약 8MB
- package 목표 10MB 이하
- 2M 초과 시 FP16/INT8 검토

## 8.5 연산량과 Reference Profile

272개 Candidate를 모두 평가하는 V1 Score Head는 구조에 따라 판단 1회당 약 **12~13M MAC**을 사용한다. Typical 100 decisions/sec이면 약 **1.2~1.3G MAC/sec**이므로 배치와 backend 최적화를 전제로 한다.

Schema Freeze용 잠정 Reference Profile:

```text
ID: REF-PC-CPU-01
CPU: AMD Ryzen 7 5800X
Memory: 32GB DDR4-3200
OS: Windows 11 64-bit
Build: Unreal Shipping
Backend: NNE/ONNX Runtime CPU, AVX2
Precision: FP32
Inference worker: 4 threads
Batch buckets: 1, 8, 16
Candidate tensor: fixed 272
```

제품 대상 하드웨어가 다르면 별도 Reference ID를 추가하며 기존 결과를 덮어쓰지 않는다. Release report는 다음을 함께 기록한다.

- 실제 valid Candidate 분포 p50/p95/p99
- batch 크기 분포
- preprocessing/queue/inference/commit 각각의 p50/p95/p99
- decisions/sec typical 및 1초 burst
- CPU utilization과 game-thread stall

Reference Profile 실측 전 p99 수치는 승인 목표이지 보장값으로 간주하지 않는다.

---

# 9. Switch Cost, OOD, Calibration, Abstain

## 9.1 Adjusted score 공식

모든 cost component는 `[0,1]`이다. 모델 raw score는 `[-4,4]`다.

```text
switch_cost_i =
    0.30 * cancel_current_i
  + 0.20 * target_change_i
  + 0.15 * animation_transition_i
  + 0.20 * recent_failure_i
  + 0.10 * repetition_i
  + 0.05 * resource_contention_i

adjusted_score_i = raw_score_i - 1.0 * switch_cost_i
```

Mask된 Candidate의 adjusted score는 `-∞`다. 동점은 candidate index가 낮은 항목을 선택한다. 이 공식과 weight는 `postprocess 1.0.0`의 일부다.

`MaintainCurrentExecution`의 cost는 0이다. 현재 `(Skill, Target)`을 재시작하는 중복 Candidate는 mask하므로 의미가 겹치지 않는다.

## 9.2 정확한 처리 순서

```text
Raw Score
→ Hard Mask
→ Switch Cost
→ Adjusted Score
→ Selected Candidate
→ OOD 계산
→ Adjusted 통계 + OOD를 Acceptability Calibrator에 입력
→ Threshold Gate
→ Accept 또는 Abstain
```

## 9.3 Entropy

Valid Candidate에 대해 `T=1.0` softmax를 사용한다.

```text
H = -Σ p_i log(p_i) / log(N_valid)
```

`N_valid=1`이면 H=0이다. Mask Candidate는 분모와 합에서 제외한다.

## 9.4 OOD

- unseen enum/version, NaN/Inf, feature 범위 허용오차 초과는 `hard_ood=1`
- Tactical Context embedding의 Goal group별 Mahalanobis distance를 계산한다.
- Calibration Set의 q95와 q99.9로 `embedding_ood`를 `[0,1]`로 선형 변환한다.
- `ood_score=max(hard_ood, embedding_ood)`

## 9.5 Calibrator

V1 Calibrator는 8입력 logistic regression이다.

```text
[selected_adjusted,
 second_adjusted,
 gap,
 normalized_masked_entropy,
 valid_candidate_count/272,
 selected_switch_cost,
 ood_score,
 selected_raw_score]
```

출력은 `P(selected candidate acceptable)`이다. 기본 threshold는 accept 0.80, OOD 0.80이며 Role×Goal group별 값은 Calibration asset에서 override할 수 있다.

- group 표본이 500 미만이거나 positive/negative 각각 100 미만이면 global threshold 사용
- `hard_ood=1`이면 확률과 무관하게 abstain
- model, postprocess, candidate schema가 바뀌면 재Calibration

## 9.6 Version/Hash

- Schema source SHA-256: `34b57127ccc42d4c14337e78a079715e964da2430059f164bb37c30861503f8d`
- Enum registry SHA-256: `536bdc8dcb5a83afda31aed354e95e5c638f2e54da745ffcd0e1d01d03504234`
- Skill registry SHA-256: `159a779b2f85296c8fa74a3e55f648387b5617e83719af498cb54c14f5f8f581`
- Post-process SHA-256: `eea1bcc20a851da8fb72247d84037687152813aefc44b43a33b020808e903389`

Decision Request는 schema, skill registry, postprocess, calibrator version/hash를 모두 포함한다.

---

# 10. 비동기 추론과 Atomic Commit

## 10.1 In-flight 정책

NPC당 동시에 **commit-eligible request는 최대 1개**다.

- 일반 trigger가 InFlight 중 발생: `dirty=true`; 현재 응답 처리 후 즉시 새 request
- 긴급 trigger(피격, 폭발, force Goal): `urgent=true`, decision epoch 증가, cancellation token set, 기존 request는 `Superseded`
- backend cancellation이 불가능하면 기존 계산이 물리적으로 계속될 수 있으나 commit 자격은 즉시 상실한다.
- scheduler가 허용하는 가장 빠른 시점에 urgent request를 dispatch한다.
- trigger coalescing window는 16ms다.

## 10.2 Decision identity

- npc stable id/generation
- decision id/epoch
- snapshot world time
- deadline
- goal instance/revision
- belief revision
- target slot map revision
- candidate set hash
- model/schema/skill/postprocess/calibration hash

## 10.3 Atomic server transaction

서버 game thread에서 다음을 한 transaction으로 처리한다.

```text
Validate response identity/deadline
→ Resolve selected canonical candidate
→ Target Kind별 ValidateAtCommit
→ 필요한 Resource Handle을 canonical order로 lock
→ TryReserve all resources
→ final cheap validation
→ Start Skill
→ Commit executor state
```

- 획득 전 reservation lease: 250ms
- active Skill heartbeat: 100ms
- heartbeat 미수신 만료: 300ms
- `Start` 실패 시 reservation과 executor mutation을 즉시 rollback하고 `StartFailedRollback` 기록
- 일부 resource만 예약된 상태로 외부에 노출하지 않는다.

## 10.4 Response 폐기

- decision epoch가 최신이 아님
- deadline 초과
- Goal instance/revision 불일치
- selected target generation 불일치
- candidate set hash 불일치
- 필요한 perception requirement 변경
- authority 변경

Belief revision이 단순 위치 confidence 변화로 증가했다는 이유만으로 일괄 폐기하지 않고, 선택 Skill과 Target Kind가 의존하는 commit invariant를 검증한다.

## 10.5 멀티플레이

- 서버가 Belief, Goal, Policy, Commit, Skill Result를 소유
- 클라이언트는 Skill ID, target handle/NetGUID, start time, cosmetic parameter를 복제받음
- 클라이언트 policy는 Debug 또는 cosmetic prediction 전용

---

# 11. Candidate/Observation Canonical Hash

## 11.1 Candidate set hash 목적

모델 output index가 어떤 Skill/Target 조합을 의미했는지 검증한다. float Feature 전체를 hash하지 않고, index mapping에 필요한 discrete metadata를 hash한다.

## 11.2 Byte sequence

SHA-256 입력은 다음 순서의 little-endian byte sequence다.

```text
8 bytes  magic ASCII "ANPCCS20"
2 bytes  schema major uint16 = 2
2 bytes  schema minor uint16 = 0
32 bytes schema source SHA-256 raw bytes
32 bytes skill registry SHA-256 raw bytes
32 bytes postprocess SHA-256 raw bytes
4 bytes  goal revision uint32
4 bytes  target slot map revision uint32

16 × target slot record:
  1 byte kind uint8
  3 bytes zero padding
  8 bytes stable_id uint64
  4 bytes generation uint32

272 × candidate record:
  1 byte skill_id uint8
  1 byte target_ref_index uint8
  1 byte candidate_mask uint8
  1 byte hard_mask_reason uint8
```

UUID 문자열, JSON object order, locale-dependent float 문자열은 hash에 사용하지 않는다.

## 11.3 Tensor canonicalization

- IEEE-754 float32
- little-endian
- NaN/Inf 금지
- `-0.0`을 `+0.0`으로 변환
- mask는 float32 0.0/1.0
- one-hot unknown은 enum의 Unknown slot을 사용; padding은 전체 0 + mask 0
- Python–UE Feature parity는 abs tolerance `1e-5`, relative tolerance `1e-5`
- Candidate hash는 discrete mapping이므로 byte exact 일치

---

# 12. Schema 2.0 Single Source와 Code Generation

## 12.1 Single source

동봉된 `ai_native_npc_schema_2_0.json`을 유일한 source로 사용한다. JSON은 YAML 1.2 호환이며 key order와 무관한 subdocument hash를 위해 canonical JSON hash를 병행한다.

## 12.2 생성 산출물

`tools/generate_npc_schema.py`가 다음을 생성한다.

- `NPCSchema2.generated.h/.cpp`
- `npc_schema2_generated.py`
- `npc_schema_2_0.generated.json`
- Tensor index Markdown appendix
- enum/registry unit test
- normalization constants

Generated file은 수동 편집하지 않는다.

## 12.3 Golden Vector

최소 32개 vector를 고정한다.

- visible Entity
- SoundEvent
- LastKnownPosition
- Cover reservation
- missing/padding
- slot hysteresis
- event handle unresolved/remapped
- Goal revision
- duplicate current execution
- all candidate mask

각 vector는 raw domain snapshot, 이전 slot map, 예상 target handles, tensor `.npz`, candidate hash, selected key index를 포함한다.

승인 Gate:

- Python과 Unreal tensor: abs/rel `1e-5`
- enum, mask, index, candidate hash: byte exact
- 32/32 통과 전 Schema Freeze 승인 금지

---

# 13. Exact Schema 2.0

## 13.1 Missing/Padding

- Target padding: feature 전부 0, `target_mask=0`
- Event padding: feature 전부 0, `event_mask=0`, `event_target_index=16`
- Candidate 272개는 모두 canonical index에 존재; invalid는 `candidate_mask=0`
- Continuous missing은 0이지만 valid/confidence/mask로 구분
- Target slot에는 None을 넣지 않음; NoTarget은 index 16

## 13.2 Enum IDs

### TargetKind

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `Entity` |
| 2 | `SoundEvent` |
| 3 | `LastKnownPosition` |
| 4 | `CoverSlot` |
| 5 | `SmartObject` |
| 6 | `Waypoint` |
| 7 | `WorldPosition` |

### BeliefSource

| ID | 이름 |
|---:|---|
| 0 | `Unknown` |
| 1 | `SightCurrent` |
| 2 | `HearingEvent` |
| 3 | `LastSeenMemory` |
| 4 | `SharedKnowledge` |
| 5 | `ScriptedKnowledge` |
| 6 | `Inferred` |

### SkillId

| ID | 이름 |
|---:|---|
| 0 | `Idle` |
| 1 | `MaintainCurrentExecution` |
| 2 | `LookAt` |
| 3 | `TurnTo` |
| 4 | `Approach` |
| 5 | `KeepDistance` |
| 6 | `RetreatFrom` |
| 7 | `Follow` |
| 8 | `Investigate` |
| 9 | `SearchArea` |
| 10 | `Greet` |
| 11 | `Warn` |
| 12 | `CallForHelp` |
| 13 | `TakeCover` |
| 14 | `Flee` |
| 15 | `Attack` |

### RoleId

| ID | 이름 |
|---:|---|
| 0 | `Unknown` |
| 1 | `Guard` |
| 2 | `Civilian` |
| 3 | `Companion` |
| 4 | `HostileSoldier` |
| 5 | `Merchant` |
| 6 | `Animal` |
| 7 | `Reserved` |

### GoalTypeId

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `IdlePatrol` |
| 2 | `InvestigateDisturbance` |
| 3 | `EnforceBoundary` |
| 4 | `CombatEngage` |
| 5 | `Disengage` |
| 6 | `Dialogue` |
| 7 | `Reserved` |

### IntentPhaseId

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `Observe` |
| 2 | `Orient` |
| 3 | `Approach` |
| 4 | `Interact` |
| 5 | `Search` |
| 6 | `Resolve` |
| 7 | `Return` |

### GoalLifecycleId

| ID | 이름 |
|---:|---|
| 0 | `Inactive` |
| 1 | `Active` |
| 2 | `Suspended` |
| 3 | `Succeeded` |
| 4 | `Failed` |
| 5 | `Aborted` |

### PreviousResultId

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `Running` |
| 2 | `Succeeded` |
| 3 | `Failed` |
| 4 | `Aborted` |
| 5 | `Superseded` |

### EventTypeId

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `SightAcquired` |
| 2 | `SightLost` |
| 3 | `SoundHeard` |
| 4 | `DamageReceived` |
| 5 | `WeaponObserved` |
| 6 | `WarningIssued` |
| 7 | `WarningIgnored` |
| 8 | `SkillSucceeded` |
| 9 | `SkillFailed` |
| 10 | `TargetLost` |
| 11 | `GoalChanged` |
| 12 | `AllyDown` |
| 13 | `HelpRequested` |
| 14 | `ReservationLost` |
| 15 | `Other` |

### HardMaskReason

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `InvalidTargetSlot` |
| 2 | `SkillTargetKindIncompatible` |
| 3 | `GoalForbidden` |
| 4 | `MissingCapability` |
| 5 | `CooldownActive` |
| 6 | `PerceptionRequirementMissing` |
| 7 | `PathRequirementMissing` |
| 8 | `ReservationRequirementMissing` |
| 9 | `TargetExpired` |
| 10 | `CurrentExecutionDuplicate` |
| 11 | `AuthorityForbidden` |
| 12 | `QuestForbidden` |
| 13 | `ResourceUnavailable` |
| 14 | `SchemaMismatch` |
| 15 | `Reserved` |

### SkillFailureReason

| ID | 이름 |
|---:|---|
| 0 | `None` |
| 1 | `TargetInvalid` |
| 2 | `TargetGenerationChanged` |
| 3 | `PreconditionChanged` |
| 4 | `GoalChanged` |
| 5 | `PathUnavailable` |
| 6 | `ReservationConflict` |
| 7 | `Interrupted` |
| 8 | `TimedOut` |
| 9 | `AuthorityRejected` |
| 10 | `ExecutionError` |
| 11 | `CancelledByNewDecision` |
| 12 | `DeadlineExpired` |
| 13 | `DecisionSuperseded` |
| 14 | `PerceptionRequirementChanged` |
| 15 | `StartFailedRollback` |

## 13.3 Tensor field index

### A. `global_state` — `[B,160] float32`

| Index | Field | Source | Unit | Normalization | Clamp | Missing |
|---:|---|---|---|---|---|---|
| 0 | `self_health_ratio` | authoritative self | ratio | `health/max_health` | `[0,1]` | `0.0` |
| 1 | `self_stamina_ratio` | authoritative self | ratio | `stamina/max_stamina` | `[0,1]` | `0.0` |
| 2 | `self_ammo_ratio` | authoritative self | ratio | `ammo/max_ammo; no weapon=0` | `[0,1]` | `0.0` |
| 3 | `self_speed_ratio` | authoritative self | cm/s | `speed/velocity_max` | `[0,1]` | `0.0` |
| 4 | `self_acceleration_ratio` | authoritative self | cm/s^2 | `accel/acceleration_max` | `[0,1]` | `0.0` |
| 5 | `self_local_velocity_x` | authoritative self | cm/s | `local_vx/velocity_max` | `[-1,1]` | `0.0` |
| 6 | `self_local_velocity_y` | authoritative self | cm/s | `local_vy/velocity_max` | `[-1,1]` | `0.0` |
| 7 | `self_local_velocity_z` | authoritative self | cm/s | `local_vz/velocity_max` | `[-1,1]` | `0.0` |
| 8 | `self_recently_damaged` | authoritative event | bool | `identity` | `[0,1]` | `0.0` |
| 9 | `self_recent_damage_ratio` | authoritative event | ratio | `damage/max_health` | `[0,1]` | `0.0` |
| 10 | `self_in_cover` | authoritative self | bool | `identity` | `[0,1]` | `0.0` |
| 11 | `self_movement_enabled` | authoritative self | bool | `identity` | `[0,1]` | `0.0` |
| 12 | `self_weapon_available` | authoritative self | bool | `identity` | `[0,1]` | `0.0` |
| 13 | `self_combat_allowed` | authoritative rules | bool | `identity` | `[0,1]` | `0.0` |
| 14 | `current_skill_elapsed_ratio` | executor | sec | `elapsed/skill_time_max` | `[0,1]` | `0.0` |
| 15 | `current_skill_progress` | executor | ratio | `identity` | `[0,1]` | `0.0` |
| 16 | `personality_aggression` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 17 | `personality_courage` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 18 | `personality_curiosity` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 19 | `personality_loyalty` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 20 | `personality_sociability` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 21 | `personality_impulsivity` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 22 | `personality_patience` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 23 | `personality_vigilance` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 24 | `personality_altruism` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 25 | `personality_rule_adherence` | profile | ratio | `identity` | `[-1,1]` | `0.0` |
| 26 | `emotion_fear` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 27 | `emotion_anger` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 28 | `emotion_suspicion` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 29 | `emotion_curiosity` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 30 | `emotion_tension` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 31 | `emotion_affinity` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 32 | `emotion_confusion` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 33 | `emotion_confidence` | event-driven state | ratio | `identity` | `[0,1]` | `0.0` |
| 34 | `relationship_affinity` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 35 | `relationship_trust` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 36 | `relationship_respect` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 37 | `relationship_fear` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 38 | `relationship_debt` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 39 | `relationship_suspicion` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 40 | `relationship_loyalty` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 41 | `relationship_hostility` | event-driven state | ratio | `identity` | `[-1,1]` | `0.0` |
| 42 | `role_attribute_authority` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 43 | `role_attribute_civilian` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 44 | `role_attribute_combatant` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 45 | `role_attribute_support` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 46 | `role_attribute_trader` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 47 | `role_attribute_wildlife` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 48 | `role_attribute_lawfulness` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 49 | `role_attribute_team_affinity` | profile | ratio | `identity` | `[0,1]` | `0.0` |
| 50 | `role_onehot_Unknown` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 51 | `role_onehot_Guard` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 52 | `role_onehot_Civilian` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 53 | `role_onehot_Companion` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 54 | `role_onehot_HostileSoldier` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 55 | `role_onehot_Merchant` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 56 | `role_onehot_Animal` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 57 | `role_onehot_Reserved` | profile role id | onehot | `1 if role id matches` | `[0,1]` | `0.0` |
| 58 | `current_skill_onehot_Idle` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 59 | `current_skill_onehot_MaintainCurrentExecution` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 60 | `current_skill_onehot_LookAt` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 61 | `current_skill_onehot_TurnTo` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 62 | `current_skill_onehot_Approach` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 63 | `current_skill_onehot_KeepDistance` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 64 | `current_skill_onehot_RetreatFrom` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 65 | `current_skill_onehot_Follow` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 66 | `current_skill_onehot_Investigate` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 67 | `current_skill_onehot_SearchArea` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 68 | `current_skill_onehot_Greet` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 69 | `current_skill_onehot_Warn` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 70 | `current_skill_onehot_CallForHelp` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 71 | `current_skill_onehot_TakeCover` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 72 | `current_skill_onehot_Flee` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 73 | `current_skill_onehot_Attack` | executor skill id | onehot | `1 if current skill id matches` | `[0,1]` | `0.0` |
| 74 | `previous_result_onehot_None` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 75 | `previous_result_onehot_Running` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 76 | `previous_result_onehot_Succeeded` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 77 | `previous_result_onehot_Failed` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 78 | `previous_result_onehot_Aborted` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 79 | `previous_result_onehot_Superseded` | executor result | onehot | `1 if result id matches` | `[0,1]` | `0.0` |
| 80 | `goal_type_onehot_None` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 81 | `goal_type_onehot_IdlePatrol` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 82 | `goal_type_onehot_InvestigateDisturbance` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 83 | `goal_type_onehot_EnforceBoundary` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 84 | `goal_type_onehot_CombatEngage` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 85 | `goal_type_onehot_Disengage` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 86 | `goal_type_onehot_Dialogue` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 87 | `goal_type_onehot_Reserved` | goal manager | onehot | `1 if goal type id matches` | `[0,1]` | `0.0` |
| 88 | `intent_phase_onehot_None` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 89 | `intent_phase_onehot_Observe` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 90 | `intent_phase_onehot_Orient` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 91 | `intent_phase_onehot_Approach` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 92 | `intent_phase_onehot_Interact` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 93 | `intent_phase_onehot_Search` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 94 | `intent_phase_onehot_Resolve` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 95 | `intent_phase_onehot_Return` | goal manager | onehot | `1 if phase id matches` | `[0,1]` | `0.0` |
| 96 | `goal_lifecycle_onehot_Inactive` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 97 | `goal_lifecycle_onehot_Active` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 98 | `goal_lifecycle_onehot_Suspended` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 99 | `goal_lifecycle_onehot_Succeeded` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 100 | `goal_lifecycle_onehot_Failed` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 101 | `goal_lifecycle_onehot_Aborted` | goal manager | onehot | `1 if lifecycle id matches` | `[0,1]` | `0.0` |
| 102 | `goal_priority_ratio` | goal manager | priority | `priority/1000` | `[0,1]` | `0.0` |
| 103 | `goal_progress` | goal manager | ratio | `identity` | `[0,1]` | `0.0` |
| 104 | `goal_time_remaining_ratio` | goal manager | sec | `remaining/goal_time_max` | `[0,1]` | `0.0` |
| 105 | `goal_preemptible` | goal manager | bool | `identity` | `[0,1]` | `0.0` |
| 106 | `goal_resumable` | goal manager | bool | `identity` | `[0,1]` | `0.0` |
| 107 | `goal_target_present` | goal manager | bool | `identity` | `[0,1]` | `0.0` |
| 108 | `world_safe_zone` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 109 | `world_restricted_zone` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 110 | `world_indoor` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 111 | `world_outdoor` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 112 | `world_combat_zone` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 113 | `world_crowd_present` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 114 | `world_nav_available` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 115 | `world_dialogue_allowed` | world context | bool | `identity` | `[0,1]` | `0.0` |
| 116 | `sensor_visible_target_count_ratio` | belief set | count | `count/16` | `[0,1]` | `0.0` |
| 117 | `sensor_heard_event_count_ratio` | belief set | count | `count/16` | `[0,1]` | `0.0` |
| 118 | `sensor_last_known_count_ratio` | belief set | count | `count/16` | `[0,1]` | `0.0` |
| 119 | `sensor_cover_target_count_ratio` | target universe | count | `count/16` | `[0,1]` | `0.0` |
| 120 | `sensor_nearest_visible_distance_ratio` | belief set | cm | `distance/spatial_max` | `[0,1]` | `0.0` |
| 121 | `sensor_nearest_sound_age_ratio` | belief set | sec | `age/event_age_max` | `[0,1]` | `0.0` |
| 122 | `sensor_max_threat_belief` | belief set | ratio | `identity` | `[0,1]` | `0.0` |
| 123 | `sensor_max_target_confidence` | belief set | ratio | `identity` | `[0,1]` | `0.0` |
| 124 | `resource_cover_reserved` | reservation manager | bool | `identity` | `[0,1]` | `0.0` |
| 125 | `resource_smart_object_reserved` | reservation manager | bool | `identity` | `[0,1]` | `0.0` |
| 126 | `resource_interaction_slot_reserved` | reservation manager | bool | `identity` | `[0,1]` | `0.0` |
| 127 | `resource_weapon_cooldown_ratio` | executor | sec | `remaining/skill_time_max` | `[0,1]` | `0.0` |
| 128 | `resource_movement_lock` | executor | bool | `identity` | `[0,1]` | `0.0` |
| 129 | `resource_dialogue_lock` | executor | bool | `identity` | `[0,1]` | `0.0` |
| 130 | `resource_contention_ratio` | reservation manager | ratio | `identity` | `[0,1]` | `0.0` |
| 131 | `resource_active_reservation_ttl_ratio` | reservation manager | sec | `remaining/reservation_ttl_max` | `[0,1]` | `0.0` |
| 132 | `current_target_kind_onehot_None` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 133 | `current_target_kind_onehot_Entity` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 134 | `current_target_kind_onehot_SoundEvent` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 135 | `current_target_kind_onehot_LastKnownPosition` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 136 | `current_target_kind_onehot_CoverSlot` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 137 | `current_target_kind_onehot_SmartObject` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 138 | `current_target_kind_onehot_Waypoint` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 139 | `current_target_kind_onehot_WorldPosition` | current execution target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 140 | `time_since_last_decision_ratio` | decision scheduler | sec | `age/decision_time_max` | `[0,1]` | `0.0` |
| 141 | `time_since_skill_change_ratio` | executor | sec | `age/skill_time_max` | `[0,1]` | `0.0` |
| 142 | `time_since_goal_change_ratio` | goal manager | sec | `age/goal_time_max` | `[0,1]` | `0.0` |
| 143 | `time_since_target_change_ratio` | executor | sec | `age/skill_time_max` | `[0,1]` | `0.0` |
| 144 | `decision_deadline_remaining_ratio` | decision scheduler | sec | `remaining/decision_time_max` | `[0,1]` | `0.0` |
| 145 | `decision_dirty_flag` | decision scheduler | bool | `identity` | `[0,1]` | `0.0` |
| 146 | `decision_urgent_flag` | decision scheduler | bool | `identity` | `[0,1]` | `0.0` |
| 147 | `policy_warmup_flag` | policy runtime | bool | `identity` | `[0,1]` | `0.0` |
| 148 | `reserved_00` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 149 | `reserved_01` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 150 | `reserved_02` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 151 | `reserved_03` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 152 | `reserved_04` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 153 | `reserved_05` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 154 | `reserved_06` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 155 | `reserved_07` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 156 | `reserved_08` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 157 | `reserved_09` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 158 | `reserved_10` | reserved | none | `must be zero` | `[0,0]` | `0.0` |
| 159 | `reserved_11` | reserved | none | `must be zero` | `[0,0]` | `0.0` |

### B. `target_features` — `[B,16,64] float32`

| Index | Field | Source | Unit | Normalization | Clamp | Missing |
|---:|---|---|---|---|---|---|
| 0 | `kind_onehot_None` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 1 | `kind_onehot_Entity` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 2 | `kind_onehot_SoundEvent` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 3 | `kind_onehot_LastKnownPosition` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 4 | `kind_onehot_CoverSlot` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 5 | `kind_onehot_SmartObject` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 6 | `kind_onehot_Waypoint` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 7 | `kind_onehot_WorldPosition` | typed target kind | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 8 | `valid` | target snapshot | bool | `identity` | `[0,1]` | `0.0` |
| 9 | `confidence` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 10 | `age_ratio` | belief | sec | `age/belief_age_max` | `[0,1]` | `0.0` |
| 11 | `ttl_remaining_ratio` | belief | sec | `remaining/belief_age_max` | `[0,1]` | `0.0` |
| 12 | `relative_position_x` | believed position | cm | `local_x/spatial_max` | `[-1,1]` | `0.0` |
| 13 | `relative_position_y` | believed position | cm | `local_y/spatial_max` | `[-1,1]` | `0.0` |
| 14 | `relative_position_z` | believed position | cm | `local_z/spatial_max` | `[-1,1]` | `0.0` |
| 15 | `distance_3d_ratio` | believed position | cm | `distance/spatial_max` | `[0,1]` | `0.0` |
| 16 | `distance_planar_ratio` | believed position | cm | `distance/spatial_max` | `[0,1]` | `0.0` |
| 17 | `log_distance_ratio` | believed position | cm | `log1p(distance)/log1p(spatial_max)` | `[0,1]` | `0.0` |
| 18 | `bearing_sin` | believed position | radian | `sin(bearing)` | `[-1,1]` | `0.0` |
| 19 | `bearing_cos` | believed position | radian | `cos(bearing)` | `[-1,1]` | `0.0` |
| 20 | `elevation_sin` | believed position | radian | `sin(elevation)` | `[-1,1]` | `0.0` |
| 21 | `elevation_cos` | believed position | radian | `cos(elevation)` | `[-1,1]` | `0.0` |
| 22 | `perceived_velocity_x` | belief history | cm/s | `local_vx/velocity_max` | `[-1,1]` | `0.0` |
| 23 | `perceived_velocity_y` | belief history | cm/s | `local_vy/velocity_max` | `[-1,1]` | `0.0` |
| 24 | `perceived_velocity_z` | belief history | cm/s | `local_vz/velocity_max` | `[-1,1]` | `0.0` |
| 25 | `closing_speed_ratio` | belief history | cm/s | `closing/velocity_max` | `[-1,1]` | `0.0` |
| 26 | `visible_now` | belief | bool | `identity` | `[0,1]` | `0.0` |
| 27 | `line_of_sight_belief` | belief | bool | `identity` | `[0,1]` | `0.0` |
| 28 | `sight_strength` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 29 | `visible_duration_ratio` | belief | sec | `duration/belief_age_max` | `[0,1]` | `0.0` |
| 30 | `heard_recently` | belief | bool | `identity` | `[0,1]` | `0.0` |
| 31 | `loudness_ratio` | sound belief | ratio | `identity` | `[0,1]` | `0.0` |
| 32 | `attribution_confidence` | sound belief | ratio | `identity` | `[0,1]` | `0.0` |
| 33 | `is_goal_target` | goal manager | bool | `identity` | `[0,1]` | `0.0` |
| 34 | `is_current_skill_target` | executor | bool | `identity` | `[0,1]` | `0.0` |
| 35 | `is_current_attacker` | damage belief | bool | `identity` | `[0,1]` | `0.0` |
| 36 | `is_reserved_resource` | reservation manager | bool | `identity` | `[0,1]` | `0.0` |
| 37 | `is_dialogue_target` | dialogue system | bool | `identity` | `[0,1]` | `0.0` |
| 38 | `alive_belief` | belief | ratio | `0 unknown, 1 alive; confidence separate` | `[0,1]` | `0.0` |
| 39 | `interactable_belief` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 40 | `hostile_belief` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 41 | `threat_belief` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 42 | `weapon_visible_belief` | belief | ratio | `identity` | `[0,1]` | `0.0` |
| 43 | `health_estimate_mid` | belief | ratio | `estimated midpoint` | `[0,1]` | `0.0` |
| 44 | `health_estimate_width` | belief | ratio | `estimated interval width` | `[0,1]` | `0.0` |
| 45 | `path_known` | path query on believed position | bool | `identity` | `[0,1]` | `0.0` |
| 46 | `path_reachable_belief` | path query on believed position | ratio | `identity` | `[0,1]` | `0.0` |
| 47 | `path_length_ratio` | path query on believed position | cm | `length/path_length_max` | `[0,1]` | `0.0` |
| 48 | `reservation_available_belief` | reservation snapshot | ratio | `identity` | `[0,1]` | `0.0` |
| 49 | `source_onehot_Unknown` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 50 | `source_onehot_SightCurrent` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 51 | `source_onehot_HearingEvent` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 52 | `source_onehot_LastSeenMemory` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 53 | `source_onehot_SharedKnowledge` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 54 | `source_onehot_ScriptedKnowledge` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 55 | `source_onehot_Inferred` | belief source | onehot | `1 if source id matches` | `[0,1]` | `0.0` |
| 56 | `kind_payload_0` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 57 | `kind_payload_1` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 58 | `kind_payload_2` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 59 | `kind_payload_3` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 60 | `kind_payload_4` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 61 | `kind_payload_5` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 62 | `kind_payload_6` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |
| 63 | `kind_payload_7` | typed target payload | kind-specific | `see payload layout table` | `[-1,1]` | `0.0` |

### C. `event_features` — `[B,16,32] float32`

| Index | Field | Source | Unit | Normalization | Clamp | Missing |
|---:|---|---|---|---|---|---|
| 0 | `event_type_onehot_None` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 1 | `event_type_onehot_SightAcquired` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 2 | `event_type_onehot_SightLost` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 3 | `event_type_onehot_SoundHeard` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 4 | `event_type_onehot_DamageReceived` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 5 | `event_type_onehot_WeaponObserved` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 6 | `event_type_onehot_WarningIssued` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 7 | `event_type_onehot_WarningIgnored` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 8 | `event_type_onehot_SkillSucceeded` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 9 | `event_type_onehot_SkillFailed` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 10 | `event_type_onehot_TargetLost` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 11 | `event_type_onehot_GoalChanged` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 12 | `event_type_onehot_AllyDown` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 13 | `event_type_onehot_HelpRequested` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 14 | `event_type_onehot_ReservationLost` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 15 | `event_type_onehot_Other` | event buffer | onehot | `1 if event type matches` | `[0,1]` | `0.0` |
| 16 | `target_kind_onehot_None` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 17 | `target_kind_onehot_Entity` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 18 | `target_kind_onehot_SoundEvent` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 19 | `target_kind_onehot_LastKnownPosition` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 20 | `target_kind_onehot_CoverSlot` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 21 | `target_kind_onehot_SmartObject` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 22 | `target_kind_onehot_Waypoint` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 23 | `target_kind_onehot_WorldPosition` | stable event target handle | onehot | `1 if target kind matches` | `[0,1]` | `0.0` |
| 24 | `event_age_ratio` | event buffer | sec | `age/event_age_max` | `[0,1]` | `0.0` |
| 25 | `event_strength` | event buffer | ratio | `identity` | `[0,1]` | `0.0` |
| 26 | `event_confidence` | event buffer | ratio | `identity` | `[0,1]` | `0.0` |
| 27 | `source_sight` | event source | bool | `identity` | `[0,1]` | `0.0` |
| 28 | `source_hearing` | event source | bool | `identity` | `[0,1]` | `0.0` |
| 29 | `source_damage` | event source | bool | `identity` | `[0,1]` | `0.0` |
| 30 | `source_shared_or_scripted` | event source | bool | `identity` | `[0,1]` | `0.0` |
| 31 | `event_polarity` | event semantics | signed ratio | `-1 negative, 0 neutral, 1 positive` | `[-1,1]` | `0.0` |

### D. `candidate_features` — `[B,272,48] float32`

| Index | Field | Source | Unit | Normalization | Clamp | Missing |
|---:|---|---|---|---|---|---|
| 0 | `skill_onehot_Idle` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 1 | `skill_onehot_MaintainCurrentExecution` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 2 | `skill_onehot_LookAt` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 3 | `skill_onehot_TurnTo` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 4 | `skill_onehot_Approach` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 5 | `skill_onehot_KeepDistance` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 6 | `skill_onehot_RetreatFrom` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 7 | `skill_onehot_Follow` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 8 | `skill_onehot_Investigate` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 9 | `skill_onehot_SearchArea` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 10 | `skill_onehot_Greet` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 11 | `skill_onehot_Warn` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 12 | `skill_onehot_CallForHelp` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 13 | `skill_onehot_TakeCover` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 14 | `skill_onehot_Flee` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 15 | `skill_onehot_Attack` | canonical candidate skill | onehot | `1 if skill id matches` | `[0,1]` | `0.0` |
| 16 | `target_kind_onehot_None` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 17 | `target_kind_onehot_Entity` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 18 | `target_kind_onehot_SoundEvent` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 19 | `target_kind_onehot_LastKnownPosition` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 20 | `target_kind_onehot_CoverSlot` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 21 | `target_kind_onehot_SmartObject` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 22 | `target_kind_onehot_Waypoint` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 23 | `target_kind_onehot_WorldPosition` | canonical candidate target | onehot | `1 if kind id matches` | `[0,1]` | `0.0` |
| 24 | `is_maintain_current` | candidate metadata | bool | `identity` | `[0,1]` | `0.0` |
| 25 | `requires_los` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 26 | `requires_path` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 27 | `requires_reservation` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 28 | `requires_weapon` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 29 | `category_social` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 30 | `category_combat` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 31 | `category_movement` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 32 | `same_category_as_current` | executor and registry | bool | `identity` | `[0,1]` | `0.0` |
| 33 | `target_same_as_current` | stable typed handle comparison | bool | `identity` | `[0,1]` | `0.0` |
| 34 | `goal_allowed` | goal allowed/forbidden masks | bool | `identity` | `[0,1]` | `0.0` |
| 35 | `is_emergency_capable` | skill registry | bool | `identity` | `[0,1]` | `0.0` |
| 36 | `base_duration_ratio` | skill registry | sec | `duration/skill_time_max` | `[0,1]` | `0.0` |
| 37 | `base_speed_ratio` | skill registry | ratio | `identity` | `[0,1]` | `0.0` |
| 38 | `min_distance_ratio` | skill registry | cm | `min_distance/spatial_max` | `[0,1]` | `0.0` |
| 39 | `max_distance_ratio` | skill registry | cm | `max_distance/spatial_max` | `[0,1]` | `0.0` |
| 40 | `risk_ratio` | skill registry | ratio | `identity` | `[0,1]` | `0.0` |
| 41 | `cooldown_remaining_ratio` | executor | sec | `remaining/skill_time_max` | `[0,1]` | `0.0` |
| 42 | `pair_distance_ratio` | target feature | ratio | `target distance ratio` | `[0,1]` | `0.0` |
| 43 | `pair_facing_alignment` | target feature | cosine | `forward dot target direction` | `[-1,1]` | `0.0` |
| 44 | `pair_visible` | target belief | bool | `identity` | `[0,1]` | `0.0` |
| 45 | `pair_confidence` | target belief | ratio | `identity` | `[0,1]` | `0.0` |
| 46 | `pair_path_reachable_belief` | path query on believed position | ratio | `identity` | `[0,1]` | `0.0` |
| 47 | `pair_reservation_available_belief` | reservation snapshot | ratio | `identity` | `[0,1]` | `0.0` |

## 13.4 Kind payload

| Kind | `kind_payload_0..7` 의미 |
|---|---|
| `None` | 모두 0 |
| `Entity` | player, npc, ally, enemy, neutral, observed_attacking, observed_fleeing, observed_in_cover |
| `SoundEvent` | footstep, gunshot, explosion, voice, door, impact, machinery, other |
| `LastKnownPosition` | source_sight, source_shared, source_scripted, uncertainty_radius_norm, last_speed_norm, last_heading_sin, last_heading_cos, immutable_flag=1 |
| `CoverSlot` | low_cover, high_cover, cover_normal_sin, cover_normal_cos, exposure_belief, occupancy_belief, peek_available, destructible_belief |
| `SmartObject` | door, seat, console, pickup, heal_station, dialogue_spot, climb, other |
| `Waypoint` | patrol, retreat, rally, exit, search_anchor, escort, home, other |
| `WorldPosition` | generic, investigate, flee, formation, quest, dialogue, hazard_avoidance, other |

---

# 14. 데이터·학습·Baseline

## 14.1 데이터 계층

- Silver: LLM/절차 합성
- Gold: 사람 acceptable set/선호/시연
- Live: DAgger와 실제 플레이 intervention

LLM은 정답 원천이 아니라 Silver 공급자다.

## 14.2 Split

행 단위 random split을 금지하고 다음 family를 통째로 hold-out한다.

- map/layout
- Goal sequence
- Role×Personality
- sensor modality
- Target Kind 조합
- generator/prompt version
- Skill combination

Train, Validation, Calibration, Test, OOD, Critical Safety를 분리한다.

## 14.3 그룹별 최소 표본

Phase 1 기준:

- Train: 각 주요 Role×Goal group 2,000 state 이상
- Gold Test: 각 주요 group 300 state 이상
- Calibration: 각 group 500 state 이상이며 acceptable/unacceptable 각각 100 이상; 미달 시 global calibrator 사용
- Goal episode Test: 각 주요 group 200 episode 이상
- Candidate/Target Recall: 전체 10,000 state 이상
- Critical Suite: version-fixed 500 scenario 이상

샘플 총량은 학습곡선으로 조정한다. 25/50/75/100% curve를 기록하고 데이터 25% 추가 시 핵심 지표 향상이 두 번 연속 0.5 percentage point 미만이면 모델·feature·label 오류를 먼저 조사한다.

## 14.4 Utility Baseline

`utility_baseline_v1.0`과 hash를 Phase 0 Exit 시 동결한다. Neural과 동일한 Belief, Goal, Target Slot, Candidate, Mask, Executor를 사용한다. Baseline은 교사로 사용하지 않고 비교와 fallback에 사용한다.

---

# 15. KPI와 통계 승인 계약

## 15.1 Recall

- Target Recall ≥99.5%; Critical 500+ scenario에서 100%
- Any-Acceptable Candidate Recall ≥99.5%; Critical 100%
- 95% Wilson CI 보고
- Critical 100%는 고정 suite의 정확한 N과 suite hash를 함께 기록

## 15.2 Safety 비열등

Baseline: 동결된 `utility_baseline_v1.0`.

- hard safety/quest violation: Neural=0, Baseline=0, Critical Suite 전체 0건
- Commit invalid execution: Neural upper 95% CI가 Baseline upper CI +0.1 percentage point 이하
- hidden-information violation: 0건

## 15.3 품질 비열등 및 우월

필수 비열등:

- Goal completion rate 차이 `Neural - Baseline`의 95% CI lower bound ≥ -3 percentage points
- acceptable action rate 차이의 lower bound ≥ -3 points

사전 등록된 핵심 지표 중 최소 하나 우월:

1. blind naturalness A/B: Neural win-rate 95% CI lower bound >55%
2. held-out Goal completion: 차이 lower bound >+3 points
3. 콘텐츠 제작 시간: median reduction의 bootstrap 95% CI lower bound >20%

“셋 중 무엇이든 사후 선택”하지 않고 Phase 1 시작 전에 primary superiority metric 하나를 등록한다.

## 15.4 Latency 비열등

Reference Hardware와 Shipping build, backend, precision, batch profile을 release report에 고정한다.

- trigger-to-Skill-Start p95 ≤ Baseline p95 +20ms
- p99 ≤ Baseline p99 +40ms
- deadline miss rate ≤ Baseline +0.1 percentage point
- server game-thread commit p95 추가 비용 ≤0.25ms per decision batch

모델 inference 자체는 Utility보다 느릴 수 있으므로 gameplay response latency와 game-thread cost를 비교한다.

## 15.5 Calibration/OOD

- ECE ≤0.05 overall
- Brier score를 Baseline acceptability heuristic과 비교
- OOD Critical recall ≥95%
- accepted action risk를 coverage 80%, 90%, 95%에서 보고
- fallback/abstain group별 비율 보고

## 15.6 행동·Goal 수치

- 동일 Skill/Target oscillation: 10초 window당 불필요 전환 평균 ≤1.0
- 3회 이상 A↔B 반복 episode 비율 ≤1%
- Investigate→Search→Return 완료율 ≥90% on valid-path suite
- Warn→Resolve/Escalate terminal 도달률 ≥90%
- Skill failure 후 2회 decision 내 회복률 ≥95%

---

# 16. 테스트

필수 자동화:

- Typed payload validity/generation
- Event stable handle→slot remap
- Target dedupe/quota/mandatory overflow/hysteresis
- Candidate index formula 272개
- current execution duplicate mask
- Goal arbitration tie/preemption/suspend/resume/revision
- adjusted formula/entropy/calibrator order
- urgent supersede/cancellation/dirty replay
- atomic reservation rollback
- LastKnown Commit actor lookup 금지
- Python–UE Golden Vector
- hash byte exact
- server authority/late join/reconnect

---

# 17. 단계·Owner·의존성

| 단계 | 이름 | 주 Owner | 필수 선행조건 | 계획 가정(병렬 팀 기준) | Exit Gate |
|---|---|---|---|---|---|
| 0A | Contract & Schema Freeze | AI Tech Lead(A), Gameplay AI·ML(R) | v0.3 승인 | 2~3 person-weeks | Schema/Registry/Postprocess hash 고정, Golden Vector 통과 |
| 0B | MVP Vertical Slice | Gameplay AI(A/R), ML(R), Designer/QA(C) | 0A | 8~12 person-weeks | 1 NPC·2 Goal·5 Skill, Critical Recall 100%, stale/hidden-info 테스트 |
| 1 | V1 | AI Tech Lead(A), 각 기능 Owner(R) | Phase 0 Exit | 24~36 person-weeks | 3 Role·4 Goal·16 Skill, Calibration/OOD, 서버 권위, KPI 통과 |
| 2 | Data & Quality | ML(A/R), Design·QA(R) | V1 telemetry | 지속 반복 | DAgger, worst-group, 실제 플레이 개선 |
| 3 | RL/Cooperation 선택 | ML(A/R), Gameplay AI(C) | V1 안정화 | 별도 승인 | 모방 모델 대비 임무 성능 우월·안전 비열등 |
| 4 | Productionization | Platform/Network(A/R) | V1 품질 승인 | 플랫폼별 산정 | p50/p95/p99, rollback, packaging, 운영 대시보드 |

## 17.1 RACI 요약

- Architecture/Schema: AI Tech Lead A, Gameplay AI·ML R, Network·QA C
- Belief/Goal/Skill/Commit: Gameplay AI A/R, Network C
- Tensor/Model/Calibration: ML A/R, Gameplay AI C
- Server authority: Network A/R
- Label/Goal UX: AI Designer A/R
- Test/Release Gate: QA A/R, 각 Owner C

일정 값은 1 Gameplay AI, 1 ML, 0.5 Designer, 0.5 QA, Network shared라는 가정의 person-week 범위이며 팀 구성 변경 시 재산정한다.

---

# 18. Phase Scope

## Phase 0 — MVP Vertical Slice

- NPC 1종
- Goal 2종
- Skill 5개
- Target Kind: None, Entity, SoundEvent, LastKnownPosition
- Target slot 4개를 사용할 수 있으나 Schema Tensor는 16개 shape 유지
- Utility Baseline
- Event Buffer
- MLP Scorer
- typed target/slotter/goal/atomic commit 전부 구현

Exit:

- Phase 0 Critical Recall 100%
- Golden Vector 32/32
- hidden-info 0
- stale/rollback 테스트
- Baseline fallback

## Phase 1 — V1

- Role 3종
- Goal 4종
- Skill 16개
- Target Kind 8종
- Target 16 / Candidate 272
- Calibration/OOD
- 서버 권위
- KPI와 통계 Gate

이전 문서의 “MVP 3 Role·4 Goal·16 Skill” 표현은 폐기하고 V1 범위로 정정한다.

---

# 19. 최종 Freeze Gate

Schema 2.0은 다음이 모두 충족될 때만 Freeze로 승인한다.

1. 본 문서 승인
2. JSON source hash 등록
3. Generated C++/Python compile
4. Golden Vector 32/32
5. Target slotter deterministic test
6. Candidate hash byte parity
7. Goal revision test
8. Atomic Commit rollback test
9. LastKnown hidden-information test
10. Utility Baseline version/hash 등록
11. Calibration dataset plan 승인
12. Critical Suite N와 hash 등록

Freeze 이후 필드 순서, enum ID, Tensor shape, candidate index formula 변경은 Schema 2.1 또는 3.0으로만 수행한다.

---

# 20. 핵심 결론

이번 리뷰의 판정은 정확하다. 이전 v0.3 메모는 문제를 올바르게 인식했지만 구현자가 그대로 코딩할 수 있는 계약은 아니었다. 본 통합 v0.3은 다음을 실제 값으로 고정한다.

- Kind별 Typed Target payload와 generation
- 16 Target의 deterministic slotting
- Goal arbitration·transition·revision
- adjusted score와 OOD/Calibration 순서
- urgent request와 Atomic Commit
- LastKnown 실행 경계
- Tensor shape·index·enum·padding
- Candidate canonical index와 byte hash
- 통계적 품질·안전·latency Gate

따라서 **Phase 0 구현은 즉시 착수 가능**하다. Schema 2.0의 최종 Freeze 승인은 generated code와 Golden Vector가 실제로 통과한 시점에 수행한다.
