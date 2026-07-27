# AI Native NPC 의사결정 시스템
## 요구사항·구현 계약·Schema 2.0 명세서

- 문서 버전: **v0.4.4**
- Schema 상태: **2.0.0 RC3 / Semantic Closure Candidate**
- 개정일: 2026-07-26
- 대체 문서: `ai_native_npc_requirements_implementation_plan.md` v0.2 및 별도 v0.3/v0.4 보완 메모
- 문서 성격: 연구 제안서가 아니라 **Unreal 클라이언트·Python 학습 코드·서버 실행기가 함께 따라야 하는 단일 구현 기준서**
- Phase 0 판정: **GO**
- Schema 2.0 판정: **RC3 Semantic Closure PASS / Unreal Runtime Gate 통과 전 최종 Freeze 보류**

---

# 0. v0.4.4 Semantic Closure 판정

최신 리뷰는 타당하다. v0.4.2는 cross-environment release와 Python↔C++ Golden parity를 해결했지만, YAML 필드 변경이 문서 Appendix에 자동 반영되지 않았고, Normalizer의 역전 범위·0 이하 divisor 같은 의미 오류를 충분히 차단하지 못했으며, Hash serializer 일부가 YAML이 아니라 생성기 코드에 하드코딩되어 있었다.

v0.4.4는 기존 v0.4.2 계약에 다음 Semantic Closure를 추가한다.

1. PyYAML `safe_load` 기반 전체 Schema 의미 검증
2. Enum ID·Tensor Shape·Field Index·Target Payload·Output·Normalizer·Hash 계약 검증
3. `skill_registry_v1.yaml`, `goal_registry_v1.yaml`
4. YAML에서 생성한 C++/Python 코드와 생성 Manifest
5. Candidate Set canonical bytes와 정수 Slotter quantization Golden fixture
6. Lock 등록 파일과 실제 ZIP 파일 집합의 역방향 일치 검사
7. 모든 normative Freeze Gate의 상태·증거·도구 버전을 기록하는 통합 Manifest
8. Contract mismatch와 OOD 분리
9. Slotter 정렬용 정수 quantization
10. bounded cosine scorer와 Skill별 Parameter 계약

11. 규범 테스트 리포트에서 Compiler Version·실행시간·stdout/stderr 제거
12. 환경 진단은 `dist/local/`의 비규범 파일로 분리하고 ZIP에서 제외
13. `release` 단일 명령으로 생성→테스트→Manifest→Lock→Strict Validate→Double Pack 실행
14. 생성 C++에 quantization·normalizer·canonical serialization·bit packing·SHA-256·parameter clamp 구현
15. 동일 Golden vector를 Python과 C++ 양쪽에서 실행
16. Harness tree digest와 file count를 Validator가 직접 재계산

17. Schema·Registry에서 Appendix A~D를 자동 생성하고 Requirements/UE 문서의 marker block과 byte 단위 비교
18. 모든 Normalizer에 finite·min≤max·positive divisor·log1p domain·missing/sentinel/valid-range 정합성 강제
19. Candidate/Decision Hash serializer를 YAML의 ordered field contract에서 Python/C++로 생성
20. Candidate Hash magic 변경, field rename, reversed clamp를 검출하는 mutation regression test
21. Decision Contract Hash의 Python↔C++ Golden vector 추가
22. Hash magic literal은 자동 생성 Appendix D.3 밖에서 수기 중복할 수 없도록 strict guard 추가
23. constant normalizer·missing·must_equal·valid range·padding_zero의 교차 정합성 검증 추가
24. Mutation probe는 현재 Schema 값에서 동적으로 다른 값을 생성해 probe 충돌을 방지

판정:

- Phase 0: **GO**
- Schema 코드 생성: **GO**
- 대량 학습 데이터 생성: **HOLD**
- Schema 2.0 최종 Freeze: Float/ONNX parity와 Runtime Gate 통과 전 **NO-GO / Conditional**

현재 단일 원본은 다음 세 파일이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

`archive/`의 JSON Schema와 이전 문서는 구현 입력으로 사용할 수 없다.

---

# 1. 목표와 책임 경계


## 1.1 목표

- 상황별 행동 선호 조건문의 수를 줄인다.
- 장기 Mission/Goal은 명시적으로 유지하면서 현재 Goal 안의 전술 행동 Ranking을 학습한다.
- NPC가 실제로 관측하거나 전달받은 정보만 사용한다.
- Candidate 누락, 모델 Ranking 오류, Calibration 오류, Skill 실행 오류를 각각 분리해 측정한다.
- Utility Baseline보다 안전·성능은 나빠지지 않으면서 사전 정의된 핵심 품질 지표에서 우월함을 증명한다.

## 1.2 비목표

- 퀘스트와 장기 Goal을 신경망이 임의로 생성·완료하는 것
- 숨은 Actor의 실제 위치·체력·행동을 모델이 사용하는 것
- 감정·관계를 모델 출력으로 직접 누적 변경하는 것
- 신규 Role·Skill의 무조건적인 zero-shot 품질 보장
- 매 프레임 이동 벡터·애니메이션을 모델이 직접 출력하는 것
- GRU hidden state만으로 장기 계획을 유지하는 것

## 1.3 계층별 소유권

| 계층 | 소유 책임 |
|---|---|
| Authoritative World | 물리, 피해, 실제 Actor 상태, 퀘스트, 서버 권한 |
| Perception/Belief | NPC가 아는 상태, 출처, 관측시각, confidence, TTL |
| Goal Manager | Goal 생성, arbitration, phase transition, suspend/resume, revision |
| Target Slotter | Target Universe에서 16개 일반 Target을 결정론적으로 선정 |
| Candidate Builder | 16×17 고정 Candidate layout과 hard mask 생성 |
| Neural Policy | raw score와 제한된 표현 파라미터 출력 |
| Post-process | switch cost, adjusted score, OOD, calibration, abstain |
| Commit Coordinator | stale 검증, 자원 예약, Skill 시작의 원자적 Commit |
| Skill Executor | Tick, Complete, Cancel, 물리·애니메이션·전투 실행 |

---

# 2. Typed Target 계약

## 2.1 Runtime Handle과 Model Feature 분리

식별자는 lookup·Commit·Hash를 위한 Runtime 데이터다. 신경망 입력이 아니다.

```cpp
USTRUCT()
struct FTargetHandle
{
    ETargetKind Kind;      // uint8
    uint64 StableId;       // Runtime identity only
    uint32 Generation;     // Reuse/spawn generation
    uint64 Revision;       // Belief/resource/snapshot/goal revision
};
```

```cpp
USTRUCT()
struct FTargetFeatures
{
    float Common[32];      // Local spatial, age, confidence, perception
    float KindPayload[16]; // Kind-specific normalized semantics
};
```

비교 규칙:

- `IdentityKey = (Kind, StableId, Generation)`
- `SnapshotKey = (Kind, StableId, Generation, Revision)`
- Dedupe와 이전 slot 유지에는 `IdentityKey`를 사용하고 같은 identity 중 가장 최신 Revision을 선택한다.
- Candidate Hash와 Commit snapshot 검증에는 `SnapshotKey`를 사용한다.
- Event가 과거 Revision의 같은 대상을 참조할 때 현재 slot 재매핑은 `IdentityKey`로 수행한다.

금지 사항:

- `StableId`, `EventId`, `SlotId`, `WaypointId`, `ReservationId`를 Tensor에 넣지 않는다.
- 절대 월드 좌표, `CreatedTime`, Actor Pointer를 Tensor에 넣지 않는다.
- 시간은 `age`, 위치는 NPC-local 상대 위치로 변환한다.
- `ReservationId`는 Commit 성공 후에만 존재한다.

## 2.2 Target Kind ID

| ID | Name |
| --- | --- |
| 0 | NoTarget |
| 1 | Entity |
| 2 | SoundEvent |
| 3 | LastKnownPosition |
| 4 | CoverSlot |
| 5 | SmartObject |
| 6 | Waypoint |
| 7 | WorldPosition |

## 2.3 Handle 생성 규칙

| Kind | StableId | Generation | Revision |
|---|---|---|---|
| NoTarget | 0 | 0 | 0 |
| Entity | 서버 영속 Entity/Net ID | Actor spawn generation | Belief revision |
| SoundEvent | World epoch 내 단조 증가 event ID | World event epoch | immutable event revision 0 |
| LastKnownPosition | NPC별 단조 증가 snapshot ID | source Entity generation 또는 0 | snapshot 생성 시 Belief revision |
| CoverSlot | authored/runtime resource ID | resource spawn/rebuild generation | availability revision |
| SmartObject | smart-object slot ID | resource spawn/rebuild generation | availability revision |
| Waypoint | authored route+waypoint ID | route load generation | route revision |
| WorldPosition | Goal Manager가 발급한 immutable position ID | authorizing goal instance generation | 생성 시 goal revision |

## 2.4 Runtime Payload


### NoTarget


| Field | Type | Contract |
| --- | --- | --- |
| payload | none | No payload. Handle is all zero. |


### Entity


| Field | Type | Contract |
| --- | --- | --- |
| belief_source | uint8 | SightCurrent/Shared/Scripted; Entity target is not retained after sight loss |
| perceived_world_position | FVector3d | latest permitted perceived position |
| perceived_world_velocity | FVector3f | derived only from permitted observations |
| observed_at | float64 | server world time |
| confidence | float32 | [0,1] |
| belief_revision | uint32 | belief snapshot revision |
| trackable_now | bool | may update aim/move target from current perception |


### SoundEvent


| Field | Type | Contract |
| --- | --- | --- |
| event_world_position | FVector3d | immutable event snapshot |
| created_at | float64 | server world time |
| loudness | float32 | normalized at feature build |
| attribution_confidence | float32 | [0,1] |
| ttl_seconds | float32 | event lifetime |
| sound_class | uint8 | fixed sound-class enum |
| attributed_entity | optional FTargetHandle | lookup only; current transform forbidden unless separately perceived |


### LastKnownPosition


| Field | Type | Contract |
| --- | --- | --- |
| snapshot_world_position | FVector3d | immutable after creation |
| source | uint8 | SightLost/Shared/Scripted |
| observed_at | float64 | time of source observation |
| confidence_at_creation | float32 | [0,1] |
| ttl_seconds | float32 | snapshot lifetime |
| subject_handle | optional FTargetHandle | identity only; no hidden transform reads |


### CoverSlot


| Field | Type | Contract |
| --- | --- | --- |
| resource_id | uint64 | authored/runtime stable slot ID |
| entry_world_position | FVector3d | known world resource position |
| peek_left_world_position | FVector3d | optional |
| peek_right_world_position | FVector3d | optional |
| resource_generation | uint32 | spawn/rebuild generation |
| availability_revision | uint32 | changes when availability changes |
| reservation_id | not present pre-commit | returned only by reservation transaction |


### SmartObject


| Field | Type | Contract |
| --- | --- | --- |
| resource_id | uint64 | smart-object slot ID |
| entry_world_position | FVector3d | known resource position |
| resource_generation | uint32 | spawn/rebuild generation |
| availability_revision | uint32 | changes when occupancy/capacity changes |
| use_type | uint8 | fixed semantic enum |
| reservation_id | not present pre-commit | returned only by reservation transaction |


### Waypoint


| Field | Type | Contract |
| --- | --- | --- |
| waypoint_id | uint64 | authored stable ID |
| world_position | FVector3d | authored or route-generated position |
| route_generation | uint32 | route asset generation |
| route_revision | uint32 | authoritative route edit/replan revision |
| sequence_index | uint16 | route-local index |
| semantic_flags | uint32 | patrol/return/search/etc. |


### WorldPosition


| Field | Type | Contract |
| --- | --- | --- |
| position_id | uint64 | per-goal monotonic immutable target ID |
| world_position | FVector3d | immutable snapshot |
| source | uint8 | Goal/Script/Shared/PlayerPing |
| created_at | float64 | server world time |
| ttl_seconds | float32 | 0 means goal-lifetime |
| authorizing_goal_instance_id | uint64 | prevents cross-goal reuse |
| authorizing_goal_revision | uint64 | revision at creation |

## 2.5 Event Buffer의 Target 참조

Event Buffer는 Target Slot 번호를 영구 저장하지 않는다.

```text
Event Runtime Record
  └─ FTargetHandle stable_target

Tensor Build
  └─ stable_target을 현재 17개 Slot에 재매핑
      ├─ 발견: event_target_slots = current slot
      └─ 미발견: slot 16(NoTarget), target_present=0
```

따라서 이전 tick의 slot 3이 다음 tick에 다른 Actor를 가리켜도 과거 Event가 잘못 연결되지 않는다.

---

# 3. Target Universe와 Target Slotter

## 3.1 고정 용량

```text
Regular Target Slots = 16
NoTarget Slot        = 16번 고정 1개
Total Target Slots   = 17
Skill Count          = 16
Candidate Max        = 16 × 17 = 272
```

## 3.2 Quota와 Kind 대응

| Quota Category | 수 | 포함 Kind |
|---|---:|---|
| Entity | 8 | Entity |
| Sound | 2 | SoundEvent |
| Cover | 2 | CoverSlot |
| SmartObject | 1 | SmartObject |
| PositionLike | 3 | LastKnownPosition, Waypoint, WorldPosition |
| NoTarget | 1 고정 | NoTarget |

일반 quota 합은 16이고 `NoTarget`은 quota 밖의 고정 slot 16이다.

## 3.3 Pipeline

```text
Perceived/Goal/Resource Universe
→ Typed Target Universe
→ Dedupe
→ Mandatory Preserve
→ Quota Selection
→ Overflow Round-Robin Backfill
→ Stable Slot Assignment
→ Candidate Universe 272
```

## 3.4 Dedupe

- 동일 `IdentityKey`는 하나로 합치고 가장 최신 `Revision`의 snapshot을 사용한다.
- `Entity`와 그 Actor가 만든 `SoundEvent`는 의미가 다르므로 별도 Target이다.
- Sight Lost 순간 기존 `Entity`는 정책 Target Universe에서 제거하고 immutable `LastKnownPosition`을 생성한다.
- 같은 Subject의 `Entity`와 `LastKnownPosition`은 동시에 유지하지 않는다.

## 3.5 Mandatory Preserve 순서

중복 제거 후 다음 순서를 사용한다.

1. 현재 실행 중 Skill Target — 최대 1
2. Active Goal Primary Target — 최대 1
3. Active Dialogue Target — 최대 1
4. 현재 NPC가 보유한 Reservation Resource — 최대 2
5. 최근 피해를 준 Attacker — 최대 2, 피해시각 내림차순
6. Active Goal Secondary Target — 최대 2

Mandatory는 category quota를 초과할 수 있지만 일반 slot 16개를 초과할 수 없다.

- Mandatory unique target이 16개를 넘으면 `MandatoryOverflow`를 기록한다.
- 이 경우 조용히 Target을 버리지 않고 Neural Policy를 abstain하며 Goal별 fallback을 사용한다.
- `MandatoryOverflow`는 Critical Suite 실패다.

## 3.6 Quota 소비와 정수 Quantized 선정 Key

- Mandatory Target은 먼저 16개 일반 slot을 소비한다.
- category별 남은 quota는 `max(0, configured quota - mandatory count)`다.
- quota fill 후 남은 slot은 고정 category 순서로 round-robin backfill한다.
- Platform별 float 마지막 비트가 Target 선정 순서를 바꾸지 않도록 정렬 입력을 먼저 정수화한다.

정수화는 `half_away_from_zero`로 고정한다.

```text
confidence_q = clamp(round(confidence × 1000), 0, 1000)
age_q        = clamp(round(age_seconds × 100), 0, 1000)        # 10 ms 단위
distance_q   = clamp(round(distance_cm / 10), 0, 500)          # 10 cm 단위
loudness_q   = clamp(round(loudness × 1000), 0, 1000)
```

정렬에는 raw float를 사용하지 않는다.

| Category | Canonical 정렬 Key |
|---|---|
| Entity | visible desc → confidence_q desc → age_q asc → distance_q asc → canonical handle bytes asc |
| Sound | event_priority desc → confidence_q desc → age_q asc → loudness_q desc → canonical handle bytes asc |
| Cover | availability desc → generation_valid desc → path_reachable desc → distance_q asc → canonical handle bytes asc |
| SmartObject | availability desc → generation_valid desc → distance_q asc → canonical handle bytes asc |
| PositionLike | goal_owned desc → confidence_q desc → age_q asc → distance_q asc → kind ID asc → canonical handle bytes asc |

Quota 미달 backfill 순서:

```text
Entity → Sound → Cover → SmartObject → PositionLike → 반복
```

정수화 공식, scale, clamp, rounding은 Schema YAML의 구조화된 `target_slots.quantization`이 단일 원본이다.

## 3.7 Slot Hysteresis와 Canonical Assignment

1. 선정된 Target이 이전 tick에도 있었으면 기존 slot을 유지한다.
2. 해제된 slot은 비운다.
3. 새 Target은 `Mandatory rank → category order → category sort key` 순으로 정렬한다.
4. 새 Target을 가장 낮은 빈 slot에 배치한다.
5. 동일 입력·이전 slot map이면 Python과 Unreal이 동일한 slot map을 만들어야 한다.

Hysteresis는 **선정 여부**를 바꾸지 않고 선정된 Target의 slot 위치만 유지한다.

## 3.8 Target Recall Gate

- General Target Recall point estimate ≥ 99.5%
- 95% Wilson lower bound ≥ 99.0%
- Critical Suite Target Recall = 100%
- miss reason: `PerceptionMiss`, `ExpiredBelief`, `MandatoryOverflow`, `QuotaDrop`, `DedupeError`, `SlotterMismatch`, `UnsupportedKind`

---

# 4. Candidate Universe

## 4.1 고정 Layout

```text
candidate_index = skill_id * 17 + target_slot
skill_id        = floor(candidate_index / 17)
target_slot     = candidate_index % 17
```

모든 요청은 272개 row를 갖는다. Ragged batch는 V1에서 금지한다.

## 4.2 ContinueCurrentAction 중복 제거

`ContinueCurrentAction`은 실행 가능한 Skill이 아니라 현재 실행을 유지하는 control candidate다.

- 실행 중 Skill이 있을 때 정확히 하나만 valid다.
- 현재 Target이 slot에 있으면 그 slot을 사용하고, 없으면 `NoTarget` 16을 사용한다.
- 동일 Skill/동일 Target을 다시 `Start`하는 일반 Candidate는 mask한다.
- Skill이 종료된 상태에서는 Continue를 mask한다.
- Commit 전에 반드시 `RunningSkill.CanContinue(LatestBelief, LatestGoalRevision)`를 호출한다.
- 최신 Belief에서 Target이 더 이상 유효하지 않거나 Goal 계약이 바뀌면 Continue는 거부한다.
- `ContinueCurrentAction`은 실제 실행 Skill이 아니므로 `global_state[17]`은 항상 0인 reserved field다.

따라서 “현재 실행 유지”와 “같은 Skill을 새로 시작”하는 의미가 중복되지 않는다.

## 4.3 Skill ID

| ID | Name |
| --- | --- |
| 0 | Idle |
| 1 | ContinueCurrentAction |
| 2 | LookAt |
| 3 | TurnTo |
| 4 | Approach |
| 5 | KeepDistance |
| 6 | RetreatFrom |
| 7 | Follow |
| 8 | Investigate |
| 9 | SearchArea |
| 10 | Greet |
| 11 | Warn |
| 12 | CallForHelp |
| 13 | TakeCover |
| 14 | Flee |
| 15 | Attack |



## 4.4 Skill–Target Kind 허용표


| Skill | NoTarget | Entity | SoundEvent | LastKnownPosition | CoverSlot | SmartObject | Waypoint | WorldPosition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Idle | ✓ |  |  |  |  |  |  |  |
| ContinueCurrentAction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LookAt |  | ✓ | ✓ | ✓ |  |  | ✓ | ✓ |
| TurnTo |  | ✓ | ✓ | ✓ |  |  | ✓ | ✓ |
| Approach |  | ✓ |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| KeepDistance |  | ✓ |  |  |  |  |  |  |
| RetreatFrom |  | ✓ |  | ✓ |  |  |  |  |
| Follow |  | ✓ |  |  |  |  |  |  |
| Investigate |  |  | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| SearchArea |  |  |  | ✓ |  |  | ✓ | ✓ |
| Greet |  | ✓ |  |  |  |  |  |  |
| Warn |  | ✓ |  |  |  |  |  |  |
| CallForHelp | ✓ | ✓ |  |  |  |  |  |  |
| TakeCover |  |  |  |  | ✓ |  |  |  |
| Flee | ✓ |  |  |  |  |  | ✓ | ✓ |
| Attack |  | ✓ |  |  |  |  |  |  |

## 4.5 Hard Mask

Mask는 다음만 판단한다.

- Skill–Target Kind Registry 호환성
- Target slot valid 여부
- Goal allowed/forbidden Skill mask
- 장비·권한·생존 같은 명백한 전제
- 현재 Skill의 interruptibility
- `ContinueCurrentAction` 특수 규칙

“가까우므로 공격이 좋다”, “겁이 많으므로 도망 후보를 남긴다” 같은 선호는 Mask에 넣지 않는다.

## 4.6 Candidate Recall

Gold acceptable set을 `G(s)`, valid candidate set을 `C(s)`라고 할 때:

```text
Any-Acceptable Recall = P(C(s) ∩ G(s) ≠ ∅)
Full Acceptable Recall = Σ|C(s)∩G(s)| / Σ|G(s)|
```

Gate는 Appendix E를 따른다.

---

# 5. Goal Manager와 Arbitration

## 5.1 Goal State

```text
Inactive → Active → Succeeded / Failed / Aborted
                 ↘ Suspended → Active / Aborted
```

한 NPC는 동시에 `Active` Goal 하나만 가진다.

## 5.2 식별자

- `goal_instance_id`: NPC별 uint64 단조 증가, 재사용 금지, save/load 보존
- `goal_revision`: NPC별 uint64 단조 증가, 현재 의사결정 계약 변경을 나타냄
- Terminal Goal은 archive되며 다시 Active가 되지 않는다.

## 5.3 Arbitration Key

다음 lexicographic key에서 작은 tuple이 우선한다.

```text
(-priority, -source_priority, created_at, goal_instance_id)
```

- priority: uint8, 높은 값 우선
- source priority: Emergency 4 > Quest 3 > Combat 2 > Social 1 > Routine 0
- created_at: 먼저 생성된 Goal 우선
- goal_instance_id: 낮은 값 우선

## 5.4 Preemption

Active phase는 다음 interruptibility 중 하나를 가진다.

| 값 | 일반 상위 Goal | Emergency | Server ForceAbort |
|---|---|---|---|
| Always | 즉시 preempt | 즉시 | 즉시 |
| PhaseBoundary | phase/skill 경계에서 | 즉시 | 즉시 |
| EmergencyOnly | 대기 | 즉시 | 즉시 |
| Never | 대기 | 대기 | 즉시 |

Preempt 시 Resume Policy:

- `ResumeSamePhase`: snapshot을 Suspended stack에 push
- `RestartPhase`: phase 초기 상태로 재개하도록 push
- `AbortOnPreempt`: 즉시 Aborted

현재 Goal을 preempt할 새 Goal의 activation 준비가 실패하면 기존 Goal은 계속 Active다. 반쪽 preemption은 허용하지 않는다.

## 5.5 Suspended Resume

1. Active Goal이 terminal이 되면 Suspended stack top을 확인한다.
2. top Goal이 아직 valid하고, 그 Goal보다 엄격히 높은 Arbitration Key를 가진 Inactive Goal이 없으면 resume한다.
3. 더 높은 Inactive Goal이 있으면 그 Goal을 activate하고 stack은 유지한다.
4. resume validation 실패 시 해당 Goal을 Failed 또는 Aborted로 terminal 처리하고 다음 후보를 평가한다.

## 5.6 goal_revision 증가 조건

| 변경 | Revision 증가 |
|---|---|
| Active Goal instance 변경 | 예 |
| Active↔Suspended 또는 terminal 전환 | 예 |
| Intent Phase 변경 | 예 |
| Primary authoritative Target Handle 변경 | 예 |
| allowed/forbidden Skill bitset 변경 | 예 |
| authoritative deadline 값 변경 | 예 |
| interruptibility/resume policy 변경 | 예 |
| 매 frame progress 변화 | 아니오 |
| deadline countdown | 아니오 |
| Event Buffer 변화 | 아니오 |
| Belief revision 변화 | 아니오 |
| Candidate score 변화 | 아니오 |

Deadline은 “설정된 절대 deadline”이 바뀔 때만 revision이 증가하며 시간이 흐르는 것만으로 증가하지 않는다.

---

## 5.7 Primary Social Subject 선정 계약

관계 Feature 8개가 참조하는 대상은 다음 결정론적 Key로 하나만 선정한다.

```text
active_dialogue_subject desc
→ active_goal_primary_target desc
→ visible_now desc
→ identity_confidence_q desc
→ belief_age_q asc
→ distance_q asc
→ stable_id asc
→ generation asc
```

- 모든 confidence·age·distance 값은 Schema Slotter 정수 Quantization을 사용한다.
- raw float 정렬을 금지한다.
- Slot 번호가 바뀌어도 Stable Handle Identity가 같으면 동일 Subject로 본다.
- 적격 Entity의 `identity_confidence_q`는 최소 500이어야 한다.

## 5.8 V1 고정 Goal 4종

V1에서 구현·평가하는 Goal은 다음 네 개로 고정한다.

1. `IdleObserve`
2. `InvestigateDisturbance`
3. `EnforceBoundary`
4. `CombatEngage`

`Disengage`와 `Escort`는 Post-V1로 연기하고 `Reserved`는 사용하지 않는다. 실제 Phase Transition은 `goal_registry_v1.yaml`이 단일 원본이다.

# 6. Neural Policy와 Post-process

## 6.1 V1 모델

V1은 GRU를 사용하지 않고 최근 12개 명시적 Event Buffer를 사용한다.

### Context Encoder

```text
global_state [128] → MLP → global embedding 128
targets [17×48] + kind embedding → shared encoder → target embeddings 17×64
masked target pooling → target context 128
events [12×24] + event type embedding + referenced target embedding
→ shared encoder + temporal attention → event context 96
concat 128+128+96 = 352
→ fusion 352→256→128 = tactical context h
```

### Bounded Factorized Candidate Scorer

고정 Switch Cost가 학습 중 커지는 raw logit에 묻히지 않도록 Query와 Key를 정규화하고 점수 범위를 제한한다.

```text
q = L2Normalize(LayerNorm(Wq(h)))
s = SkillEmbedding[skill_id]
t = Wt(TargetEmbedding[slot])
p = Wp(pair_features[16])
k = L2Normalize(LayerNorm(s + t + p))

RawScore = clamp(
    cosine(q, k) / 0.5
  + clamp(skill_bias, -0.25, 0.25)
  + clamp(target_kind_bias, -0.25, 0.25),
  -2.5, 2.5)
```

- Query/Key dimension: 64
- Cosine temperature: 0.5
- Bias와 Raw Score clamp는 모델 계약에 포함한다.
- 해당 값이 바뀌면 model/post-process 계약과 Calibration을 함께 갱신한다.

### Candidate Parameter Proposal

모델은 Candidate별 normalized 4개를 출력하지만 의미와 범위는 Skill Registry가 소유한다.

```text
0 duration
1 speed
2 preferred_distance
3 intensity
```

각 Skill Registry row는 다음을 고정한다.

- active mask
- physical unit
- min/max/default
- normalized decode 공식
- inactive output 처리
- Server Commit clamp

```text
physical = min + clamp(norm,0,1) × (max-min)
```

비활성 slot은 모델 출력을 무시하고 Registry default를 사용한다. Commit Coordinator는 Decode 후 반드시 min/max로 다시 clamp한다.

## 6.2 Switch Cost


Post-process v1.0.0:

```text
SwitchCost = clamp(
    0.45 × skill_changed
  + 0.25 × target_changed
  + 0.20 × before_min_duration
  + 0.10 × releases_or_transfers_reservation,
  0, 1)

AdjustedScore = RawScore - 1.0 × SwitchCost
```

- Continue candidate의 SwitchCost는 0이다.
- interrupt 불가능한 변경은 비용을 주는 대신 hard mask한다.
- 모든 비용은 dimensionless `[0,1]`이다.
- 계수 또는 λ가 바뀌면 `postprocess_version`을 올린다.

## 6.3 Selection, OOD, Calibration 순서

```text
Raw Score
→ Hard Mask
→ Switch Cost
→ Adjusted Score
→ 최종 Candidate 선택
→ OOD 계산
→ Adjusted Score 통계 + OOD로 Calibration
→ Accept 또는 Abstain
```

### Masked Softmax 통계

valid candidate만 사용한다.

```text
p_i = exp((a_i - max(a))/T) / Σ_valid exp((a_j-max(a))/T)
T = 1.0
H = -Σ p_i log(p_i)
H_norm = 0                    if valid_count = 1
H_norm = H / log(valid_count) otherwise
```

### Contract Mismatch와 OOD v1

Schema, Enum, Registry, Model 또는 Decision Contract Hash 불일치는 OOD가 아니다.

```text
Contract mismatch
→ Feature Build/Inference 전 hard reject
→ Utility/Goal fallback
→ ContractMismatch 로그
```

OOD는 **유효한 동일 계약 안에서 학습 분포를 벗어난 입력**에만 적용한다.

- unknown enum/schema/version을 `OOD=1`로 바꾸어 추론을 계속하지 않는다.
- 유효한 Tactical Context 128의 Mahalanobis distance `d`를 사용한다.

```text
OOD = clamp((d - q95_train) / (q99_9_train - q95_train), 0, 1)
```

### Calibrator v1


Post-process 이후 선택된 candidate로 학습한 logistic calibrator를 사용한다.

입력 22개:

1. selected adjusted score
2. second adjusted score
3. adjusted gap
4. normalized adjusted entropy
5. `log1p(valid_count)/log1p(272)`
6. OOD score
7~14. Goal Type one-hot 8
15~22. selected Target Kind one-hot 8

```text
P_acceptable = sigmoid(w·x + b)
```

Gate:

- `OOD ≥ 0.80`이면 즉시 abstain
- 그렇지 않고 group threshold보다 `P_acceptable`이 낮으면 abstain
- 기본 threshold 0.75, Role/Goal group override는 Calibration asset에 저장

Calibrator는 Raw top-1이 아니라 **Adjusted Score로 최종 선택된 행동**을 기준으로 학습한다.

## 6.4 Version과 Hash 책임 분리

| 값 | 포함 내용 |
|---|---|
| `candidate_set_hash` | Target Handle/order, target_mask 17 bit, candidate_mask 272 bit |
| `postprocess_version` | Switch Cost 공식·계수·softmax 통계 규칙 |
| `calibration_version` | Calibrator weights, thresholds, OOD asset |
| `decision_contract_hash` | schema/model/normalization/registry/slotter/postprocess/calibration asset hash |

`postprocess_version`은 `candidate_set_hash`에 포함하지 않는다.

---

# 7. 비동기 추론과 Atomic Commit

## 7.1 Request 상태

NPC별 상태:

- `next_decision_id`: uint64 단조 증가
- `commit_eligible_decision_id`: 최대 1개
- `active_cancellation_token`
- `dirty_flag`
- `urgent_flag`
- `latest_snapshot_revision`

## 7.2 In-flight 정책

- NPC당 **Commit 가능한 요청은 항상 1개 이하**다.
- 일반 변경이 발생하면 `dirty_flag`만 설정하고 기존 요청 완료 후 최신 snapshot으로 재요청한다.
- 피격·폭발 같은 긴급 이벤트는 새 decision ID를 발급하고 기존 token을 cancel/supersede한다.
- Backend가 물리적으로 이전 worker를 즉시 중단하지 못해 잠시 두 작업이 돌 수는 있다.
- 하지만 취소된 decision ID는 영구적으로 Commit 불가하며 응답 도착 즉시 폐기한다.
- 정책은 `latest-request-only`다.

## 7.3 원자적 Commit 경계

원자 범위는 Server Game Thread의 `Validate + Reserve + StartCommit`이다. 수초간 수행되는 Tick/Complete는 트랜잭션 밖이다.

```text
Worker/Read-only
  BuildExecutionPlan

Server Game Thread, short transaction
  pending request hash 검증
  → Goal/NPC/Target 검증
  → Skill precondition 검증
  → Resource CAS 및 전체 예약
  → Final validation
  → StartCommit
  → success: active Skill swap
  → failure: 신규 mutation/예약 rollback, 기존 Skill 유지

Transaction 밖
  Tick / Complete / Fail / Cancel
```

Kind별 revision 규칙:

| Target Kind | Commit revision 규칙 |
|---|---|
| Entity | Identity/Generation 일치 후 **최신 유효 Belief Revision** 허용. 추적이 필요한 Skill은 현재 Perception/LOS 재검증 |
| SoundEvent | 요청 당시 immutable snapshot revision exact match + TTL |
| LastKnownPosition | immutable snapshot revision exact match. Origin Actor 현재 위치 조회 금지 |
| CoverSlot/SmartObject | Resource Generation + Availability Revision을 CAS하고 성공 시 ReservationId 생성 |
| Waypoint | authored definition/revision exact match |
| WorldPosition | immutable snapshot revision exact match |
| NoTarget | Target 검증 없음 |

응답의 Candidate Hash는 먼저 **pending request에 저장된 hash**와 비교한다. 최신 월드로 Candidate Hash를 재계산해 최초 비교에 사용하지 않는다.

Reservation:

- 기본 lease 2.0초
- active Skill은 0.5초마다 renew
- 부분 예약과 `StartCommit` 실패는 전부 rollback
- 후보 생성 전에는 ReservationId가 없으며 ResourceGeneration과 AvailabilityRevision만 존재

## 7.4 Commit 실패 코드


- `DecisionSuperseded`
- `DeadlineExpired`
- `ContractMismatch`
- `GoalRevisionChanged`
- `TargetGenerationChanged`
- `TargetBeliefInvalid`
- `PreconditionChanged`
- `ReservationConflict`
- `PartialReservationRolledBack`
- `StartCommitFailed`
- `AuthorityRejected`

## 7.5 멀티플레이

- 서버가 Perception, Belief, Goal, Inference 요청, Post-process, Commit을 소유한다.
- 클라이언트는 선택 Skill, typed target Net reference 또는 snapshot, parameter, server start time을 복제받는다.
- 피해·이동 권한·아이템·관계·Goal은 서버만 변경한다.

---

# 8. Hidden Information 실행 경계

## 8.1 원칙

Ground Truth 사용 금지는 Skill Executor 전체에 대한 절대 금지가 아니다.

- 물리, 충돌, 피해 판정, Actor 생존 여부의 서버 권위 검증에는 Ground Truth를 사용할 수 있다.
- 하지만 숨은 Actor의 현재 위치·이동을 전술 판단, 경로 목표 갱신, 추적 지속 여부에 사용할 수 없다.

## 8.2 Target Kind별 Commit 정보

| Kind | 허용 정보 | 전술 판단/목표 갱신에 금지되는 정보 |
|---|---|---|
| Entity | identity/generation, 최신 유효 Belief, 현재 허용 Perception/LOS, 물리·피해 권위 판정 | Sight Lost 이후 숨은 Transform/Velocity |
| SoundEvent | immutable 위치·class·TTL | attributed Actor 현재 Transform |
| LastKnownPosition | immutable snapshot·age·confidence·Goal authority | Origin Actor 현재 위치·이동·생존을 이유로 취소 |
| CoverSlot | ResourceGeneration·AvailabilityRevision·entry/peek snapshot·CAS 결과 | 숨은 적 위치로 cover utility 재계산 |
| SmartObject | ResourceGeneration·AvailabilityRevision·capacity·object transform·CAS 결과 | 관계없는 hidden Actor 상태 |
| Waypoint | authored route generation/revision·position | hidden Actor를 따라 위치 갱신 |
| WorldPosition | immutable position·authority·TTL | 연결 Actor의 숨은 Transform |
| NoTarget | NPC/Goal/Skill 자체 상태 | Target Actor 조회 |

Authoritative 물리·충돌·피해 판정은 Ground Truth를 사용할 수 있다. 금지 대상은 **전술 선택, 이동/조준 목표 갱신, 추적 지속 판단**에 숨은 정보를 재주입하는 행위다.

## 8.3 Entity 추적 단절

- `Entity`는 현재 지각되고 Skill 정책상 trackable한 동안만 이동·조준 target을 갱신한다.
- Sight Lost event가 발생하면 Commit 가능한 Entity candidate를 mask한다.
- 다음 판단에서 immutable `LastKnownPosition`을 생성한다.
- 이미 실행 중인 Entity 추적 Skill은 마지막 허용 위치를 freeze하고 즉시 재판단을 요청한다.
- 공격의 실제 collision/damage는 authoritative physics를 사용하지만 숨은 위치를 알아내는 수단으로 역이용하지 않는다.

## 8.4 Path/LOS Pair Feature

- `path_distance`, `path_reachable`, `LOS`는 Target Runtime Snapshot의 **Believed Position**으로 계산한다.
- LastKnownPosition과 SoundEvent는 Actor pointer 없이 snapshot 좌표로 계산한다.
- Python 합성 데이터도 동일 규칙으로 Feature를 만든다.

---

# 9. 데이터·학습·Baseline

## 9.1 데이터 계층

- Silver: 절차 생성, LLM 교사, 자동 라벨
- Gold: 사람 시연·복수 acceptable label·선호 비교
- Live: 실제 rollout, 이상 행동 신고, DAgger intervention

LLM과 생성기는 정답 자체가 아니라 Silver 공급자다.

## 9.2 분할

행 단위 random split을 금지하고 다음 family 전체를 hold-out한다.

- 맵/가림 layout
- Goal sequence
- Role–Personality 조합
- Perception modality 조합
- Target 수와 Target Kind 조합
- Generator template/version
- 사건 sequence

Train, Validation, Calibration, Test, OOD, Critical Safety Set은 서로 분리한다.

## 9.3 Utility Baseline

Baseline ID: `utility_baseline_v1.0.0`

동일한 다음 계약을 사용한다.

- Belief Snapshot
- Goal Manager
- 17 Target Slot
- 272 Candidate와 Mask
- Post-process 이전 candidate utility
- Skill Executor와 Commit

Baseline은 Neural teacher로 사용하지 않고 비교군과 fallback으로 사용한다.

## 9.4 DAgger

```text
현재 정책 rollout
→ 방문 상태 저장
→ 디자이너 개입 또는 acceptable set 표시
→ Candidate/Target miss 분리
→ 데이터 병합
→ 재학습·Calibration·회귀
```

## 9.5 감정·관계

V1에서 모델은 읽기만 한다. 변경은 idempotent event ID를 가진 코드 기반 상태 전이로 처리한다.

---

## 9.6 데이터 Provenance와 Active Learning

모든 샘플에 source type, generator/prompt version, annotator agreement, scenario family, map seed, policy/model/schema/registry hash, label confidence를 기록한다.

Active Learning 우선순위는 calibrated confidence, OOD, Candidate/Target miss, Baseline 불일치, 반복 실패, 신규 Role/Goal 조합으로 정한다. 단순 raw top-1 gap만 사용하지 않는다.

## 9.7 Save/Load와 Model Hot-swap

- V1은 Event Buffer, Goal Instance, Belief TTL 기준 시각, Skill 실행 상태를 서버 Save에 저장한다.
- Load 시 만료된 Belief/Event는 제거하고 Reservation은 재획득한다.
- Model/Calibration/Registry hot-swap은 새 Decision Contract Hash 활성화 전에 dry-run validation과 rollback asset을 요구한다.
- Pending inference는 supersede하고 새 계약으로 재요청한다.
- rollback 시 해당 버전의 Model, Calibration, Schema/Registry 생성 코드 세트를 함께 복구한다.

# 10. Schema Generator와 Parity

## 10.1 Single Source와 실행 산출물

단일 원본은 다음 세 YAML이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

Schema YAML은 Normalizer, Range, Missing, Padding, Hash byte order, Target Slotter quantization을 구조화된 값으로 가진다. 생성기가 자연어 수식을 해석하거나 별도 상수를 하드코딩해서는 안 된다.

실행 도구와 산출물:

```text
tools/validate_schema.py
tools/generate_contracts.py
tools/generate_golden.py
generated/python/ai_native_npc_contracts_generated.py
generated/cpp/AINativeNPCContracts.generated.h
generated/contract_manifest.json
tests/golden/discrete_hash_vectors.json
```

수동으로 C++/Python Enum, Shape, Index, Parameter 범위를 편집하지 않는다.

## 10.2 Golden Test 구분

| 대상 | 기준 |
|---|---|
| Enum ID, mask, padding, candidate index, canonical serialization | byte-identical |
| Candidate/Decision hash input bytes | byte-identical |
| Float Feature Tensor | abs ≤ 1e-6 또는 rel ≤ 1e-5 |
| FP32 model output | abs ≤ 1e-4 또는 rel ≤ 1e-4 |
| FP16/INT8 output | backend별 별도 승인 tolerance |

Python/NumPy와 Unreal/FMath의 마지막 bit 차이를 허용한다.

## 10.3 Hash에 Float 금지

`candidate_set_hash`에는 플랫폼에서 계산한 raw Float를 넣지 않는다. Hash는 typed handle, slot order, candidate mask 같은 discrete contract만 포함한다.

## 10.4 Canonical Serialization과 Hash

- little-endian fixed-width integer
- Target Handle: `kind:uint8 + stable_id:uint64 + generation:uint32 + revision:uint64`
- Target Mask: **17 bit, LSB-first, 3 byte**, 사용하지 않는 상위 7 bit는 0
- Candidate Mask: **272 bit, LSB-first, 34 byte**
- raw float는 Candidate Hash에서 제외
- Response Hash는 pending request hash와 먼저 비교
- Enum/Mask/Padding/Canonical bytes는 byte-identical
- Float Tensor는 tolerance 비교

Hash field/order/type/endianness는 YAML의 구조화된 배열이 단일 원본이다.

## 10.5 Cross-Environment Release Pipeline

규범 증거에는 논리 결과와 입력·도구 Hash만 포함한다. Compiler 경로·버전, 테스트 실행시간, stdout/stderr는 `dist/local/contract_test_diagnostics.json`에만 기록하며 Lock과 ZIP에서 제외한다.

승인 산출물은 다음 단일 명령으로 만든다.

```bash
python tools/doc_harness.py release --output <bundle.zip>
```

실행 순서는 고정한다.

```text
Schema semantic validation
→ generated Python/C++/docs 갱신
→ discrete/hash/normalizer Golden 갱신
→ Python + C++17 동일 Golden 실행
→ Evidence Manifest SHA 갱신
→ Validation Report 갱신
→ Harness tree digest 재계산
→ Freeze Manifest 갱신
→ Lock/Checksum 갱신
→ strict validation
→ deterministic double-pack
```

`validate --strict`는 환경별 진단문을 byte 비교하지 않는다. 대신 규범 리포트의 입력 Hash·Test ID·논리 결과를 검증하고, 로컬 C++17 Compiler가 있으면 동일 Golden을 추가 실행한다.

# 11. Phase와 프로젝트 계획


## 11.1 Phase 0 = MVP Vertical Slice

범위:

- NPC Profile 1개: Guard
- Goal 2개: IdleObserve, InvestigateDisturbance
- 실행 Skill 5개: Idle, TurnTo, Approach, Investigate, SearchArea
- `ContinueCurrentAction` control candidate
- Target Kind: Entity, SoundEvent, LastKnownPosition, Waypoint, NoTarget
- Event Buffer, Target Slotter, 272 layout, Utility Baseline, 단순 Neural Scorer
- Single-player 서버 권위 형태의 GameThread Commit

## 11.2 Phase 1 = V1

- Role 3개
- Goal 4개
- Skill Registry 16개
- Target Kind 8개
- Calibration/OOD/Abstain
- Cover/SmartObject reservation
- 멀티플레이 서버 권위
- DAgger와 정식 KPI Gate

## 11.3 일정·Owner·의존성

| Workstream | Owner | Phase 0 예상 | Phase 1 예상 | 선행 의존성 |
|---|---|---:|---:|---|
| Belief/Target Runtime | Gameplay AI | 2주 | 3주 | Target contract |
| Goal Manager/FSM | Gameplay AI + Designer | 2주 | 3주 | Goal Appendix B |
| Slotter/Candidate/Hash | Gameplay AI + ML | 2주 | 2주 | Schema Appendix A/C/D |
| Utility Baseline | AI Designer | 1주 | 2주 | Candidate pipeline |
| Feature Builder/Golden Test | ML + Gameplay AI | 2주 | 2주 | schema.yaml generator |
| Neural Model/Export | ML | 2주 | 4주 | Golden Feature parity |
| Async Commit/Reservation | Gameplay/Server | 2주 | 4주 | Skill contract |
| Gold/DAgger Tool | Tech Designer | 1주 | 4주 | Inspector/Replay |
| QA/KPI Automation | QA + ML | 2주 | 지속 | Critical Suite |

Phase 0은 병렬 수행을 전제로 약 6~8주 범위다. Phase 1은 Phase 0 Gate 통과 후 약 12~16주 범위이며 팀 규모와 Unreal 통합 상태에 따라 조정한다.

---

<!-- BEGIN AUTO-GENERATED SCHEMA CONTRACT -->

# Appendix A–D. AUTO-GENERATED Schema·Registry 계약

> 이 구간은 `contracts/current/*.yaml`에서 자동 생성된다. 수동 편집하지 않는다.

- Generator: `0.4.4`
- Contract revision: `2.0.0-rc3`
- Schema SHA-256: `a122a02df2c5ce9e3f7403667106e9d14bc287b9a5cf8e23e56281ee54222302`
- Skill Registry SHA-256: `bbbc2a72231ab71744d69c3fffb81e7c3dd2b0375b07cf4683a411a9003c65dc`
- Goal Registry SHA-256: `7299c1907d75be487c96761204ab6241f3bda421b3cdb98a2084c1416f83661b`

## A. Constants와 Enum

### A.1 Constants

| Name | Value |
|---|---:|
| `schema_version` | `2.0.0` |
| `skill_registry_version` | `1.0.0` |
| `target_slotter_version` | `1.0.0` |
| `postprocess_version` | `1.0.0` |
| `normalization_version` | `2.0.0` |
| `regular_target_slots` | `16` |
| `no_target_slot` | `16` |
| `total_target_slots` | `17` |
| `skill_count` | `16` |
| `candidate_count` | `272` |
| `event_slots` | `12` |
| `global_feature_count` | `128` |
| `target_feature_count` | `48` |
| `event_feature_count` | `24` |
| `candidate_pair_feature_count` | `16` |
| `parameter_count` | `4` |
| `spatial_max_cm` | `5000.0` |
| `path_distance_max_cm` | `10000.0` |
| `speed_max_cm_s` | `1200.0` |
| `acceleration_max_cm_s2` | `4000.0` |
| `yaw_rate_max_deg_s` | `720.0` |
| `target_age_max_s` | `10.0` |
| `event_age_max_s` | `10.0` |
| `visible_duration_max_s` | `10.0` |
| `skill_time_max_s` | `10.0` |
| `goal_phase_time_max_s` | `30.0` |
| `goal_deadline_max_s` | `120.0` |
| `count_max` | `8.0` |
| `schema_contract_revision` | `2.0.0-rc3` |
| `goal_registry_version` | `1.0.1` |
| `goal_priority_max` | `255.0` |
| `long_duration_max_s` | `30.0` |
| `slotter_confidence_scale` | `1000` |
| `slotter_age_centisecond_scale` | `100` |
| `slotter_distance_bin_cm` | `10` |
| `slotter_loudness_scale` | `1000` |

### A.target_kind

| ID | Name |
|---:|---|
| 0 | `NoTarget` |
| 1 | `Entity` |
| 2 | `SoundEvent` |
| 3 | `LastKnownPosition` |
| 4 | `CoverSlot` |
| 5 | `SmartObject` |
| 6 | `Waypoint` |
| 7 | `WorldPosition` |

### A.skill

| ID | Name |
|---:|---|
| 0 | `Idle` |
| 1 | `ContinueCurrentAction` |
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

### A.goal_type

| ID | Name |
|---:|---|
| 0 | `None` |
| 1 | `IdleObserve` |
| 2 | `InvestigateDisturbance` |
| 3 | `EnforceBoundary` |
| 4 | `CombatEngage` |
| 5 | `Disengage` |
| 6 | `Escort` |
| 7 | `Reserved` |

### A.goal_phase

| ID | Name |
|---:|---|
| 0 | `None` |
| 1 | `Observe` |
| 2 | `Orient` |
| 3 | `Navigate` |
| 4 | `Interact` |
| 5 | `Search` |
| 6 | `Resolve` |
| 7 | `Return` |

### A.event_type

| ID | Name |
|---:|---|
| 0 | `NoneOrPadding` |
| 1 | `SightAcquired` |
| 2 | `SightLost` |
| 3 | `SoundHeard` |
| 4 | `Damaged` |
| 5 | `SkillSucceeded` |
| 6 | `SkillFailed` |
| 7 | `SkillInterrupted` |
| 8 | `WarningIssued` |
| 9 | `WarningIgnored` |
| 10 | `TargetMovedSignificantly` |
| 11 | `TargetInvalidated` |
| 12 | `GoalChanged` |
| 13 | `ReservationLost` |
| 14 | `SharedKnowledgeReceived` |
| 15 | `Other` |

### A.goal_source_priority

| ID | Name |
|---:|---|
| 0 | `Routine` |
| 1 | `Social` |
| 2 | `Combat` |
| 3 | `Quest` |
| 4 | `Emergency` |

## B. Tensor 계약

### B.1 Tensor Summary

| Name | Shape | dtype |
|---|---|---|
| `global_state` | `["B",128]` | `float32` |
| `target_features` | `["B",17,48]` | `float32` |
| `target_kind_ids` | `["B",17]` | `int64` |
| `target_mask` | `["B",17]` | `bool` |
| `event_features` | `["B",12,24]` | `float32` |
| `event_type_ids` | `["B",12]` | `int64` |
| `event_target_slots` | `["B",12]` | `int64` |
| `event_mask` | `["B",12]` | `bool` |
| `candidate_pair_features` | `["B",272,16]` | `float32` |
| `candidate_mask` | `["B",272]` | `bool` |
| `candidate_raw_scores` | `["B",272]` | `float32` |
| `candidate_parameter_proposals` | `["B",272,4]` | `float32` |

### B.2 global_state

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `self_health_norm` | self authoritative health ratio | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `self_stamina_norm` | self authoritative stamina ratio | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `self_speed_norm` | self speed | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `self_local_velocity_x` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `self_local_velocity_y` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `self_local_velocity_z` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `self_local_acceleration_x` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `self_local_acceleration_y` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `self_local_acceleration_z` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `self_yaw_rate_norm` | self yaw angular speed | `deg/s` | `{"divisor_ref":"yaw_rate_max_deg_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `self_grounded` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `self_crouched` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `self_sprinting` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `self_in_combat` | authoritative self combat state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `self_damaged_recently` | damage event within 3 seconds | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `self_recent_damage_norm` | damage received in 3-second window / max health | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `current_skill_Idle` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `current_skill_ContinueCurrentAction_reserved_zero` | control candidate is never an executing skill | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 18 | `current_skill_LookAt` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `current_skill_TurnTo` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `current_skill_Approach` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `current_skill_KeepDistance` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `current_skill_RetreatFrom` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `current_skill_Follow` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 24 | `current_skill_Investigate` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 25 | `current_skill_SearchArea` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 26 | `current_skill_Greet` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 27 | `current_skill_Warn` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 28 | `current_skill_CallForHelp` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 29 | `current_skill_TakeCover` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 30 | `current_skill_Flee` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 31 | `current_skill_Attack` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 32 | `skill_elapsed_norm` | elapsed time in current skill | `s` | `{"divisor_ref":"skill_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 33 | `skill_progress_norm` | skill-defined progress | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 34 | `skill_min_duration_remaining_norm` | remaining minimum hold time | `s` | `{"divisor_ref":"skill_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 35 | `skill_interruptible_now` | current skill may be interrupted | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 36 | `skill_has_target` | current skill has typed target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 37 | `skill_target_still_believed_valid` | current target remains valid in Belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 38 | `last_skill_result_success` | last terminal result | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 39 | `last_skill_result_failure` | last terminal result | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 40 | `personality_aggression` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 41 | `personality_courage` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 42 | `personality_curiosity` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 43 | `personality_loyalty` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 44 | `personality_sociability` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 45 | `personality_impulsivity` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 46 | `personality_patience` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 47 | `personality_vigilance` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 48 | `personality_altruism` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 49 | `personality_rule_adherence` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 50 | `emotion_fear` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 51 | `emotion_anger` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 52 | `emotion_suspicion` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 53 | `emotion_curiosity` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 54 | `emotion_tension` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 55 | `emotion_affection` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 56 | `emotion_confusion` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 57 | `emotion_confidence` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 58 | `relationship_affinity` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 59 | `relationship_trust` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 60 | `relationship_respect` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 61 | `relationship_fear` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 62 | `relationship_debt` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 63 | `relationship_suspicion` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 64 | `relationship_loyalty` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 65 | `relationship_hostility` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 66 | `role_combatant` | role attribute, not unseen Role ID | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 67 | `role_guard` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 68 | `role_civilian` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 69 | `role_companion` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 70 | `role_support` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 71 | `role_authority_level` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 72 | `role_social_authority` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 73 | `role_territory_ownership` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 74 | `role_mission_importance` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 75 | `role_risk_tolerance` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 76 | `goal_type_None` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 77 | `goal_type_IdleObserve` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 78 | `goal_type_InvestigateDisturbance` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 79 | `goal_type_EnforceBoundary` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 80 | `goal_type_CombatEngage` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 81 | `goal_type_Disengage` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 82 | `goal_type_Escort` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 83 | `goal_type_Reserved` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 84 | `goal_phase_None` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 85 | `goal_phase_Observe` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 86 | `goal_phase_Orient` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 87 | `goal_phase_Navigate` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 88 | `goal_phase_Interact` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 89 | `goal_phase_Search` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 90 | `goal_phase_Resolve` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 91 | `goal_phase_Return` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 92 | `goal_priority_norm` | active goal priority uint8 / 255 | `ratio` | `{"divisor_ref":"goal_priority_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 93 | `goal_time_in_phase_norm` | time since phase entry | `s` | `{"divisor_ref":"goal_phase_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 94 | `goal_deadline_remaining_norm` | remaining authoritative deadline; 1 when no deadline | `s` | `{"divisor_ref":"goal_deadline_max_s","max":1.0,"min":0.0,"sentinel":"no_deadline","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"no_deadline"}` | `{}` |
| 95 | `goal_progress_norm` | goal-defined non-revision progress | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 96 | `goal_interruptible` | active phase interruptibility permits ordinary preemption | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 97 | `goal_has_primary_target` | active goal owns a typed target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 98 | `allowed_skill_fraction` | allowed skill count / 16 | `ratio` | `{"divisor_ref":"skill_count","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 99 | `forbidden_skill_fraction` | forbidden skill count / 16 | `ratio` | `{"divisor_ref":"skill_count","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 100 | `world_safe_zone` | authoritative zone flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 101 | `world_restricted_zone` | authoritative zone flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 102 | `world_indoors` | environment flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 103 | `world_combat_allowed` | authoritative rule flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 104 | `world_perceived_ally_count_norm` | count from Belief | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 105 | `world_perceived_hostile_count_norm` | count from Belief | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 106 | `world_light_level_norm` | environment sample available to NPC | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 107 | `world_crowd_density_norm` | perceived local density | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 108 | `recent_sound_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 109 | `recent_sight_change_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 110 | `recent_damage_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 111 | `recent_skill_failure_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 112 | `recent_target_switch_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 113 | `recent_warning_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 114 | `recent_reservation_conflict_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 115 | `event_buffer_fill_ratio` | valid event slots / 12 | `ratio` | `{"divisor_ref":"event_slots","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 116 | `reserved_116` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 117 | `reserved_117` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 118 | `reserved_118` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 119 | `reserved_119` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 120 | `reserved_120` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 121 | `reserved_121` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 122 | `reserved_122` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 123 | `reserved_123` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 124 | `reserved_124` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 125 | `reserved_125` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 126 | `reserved_126` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 127 | `reserved_127` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### B.3 target_features common

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `relative_position_x` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `relative_position_y` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `relative_position_z` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `distance_3d_norm` | distance to perceived position | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `distance_planar_norm` | planar distance to perceived position | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `log_distance_norm` | log distance | `cm` | `{"denominator_ref":"spatial_max_cm","input_max_ref":"spatial_max_cm","input_min":0.0,"type":"log1p_ratio"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `bearing_sin` | NPC-local bearing | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `bearing_cos` | NPC-local bearing | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `elevation_sin` | NPC-local elevation | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `elevation_cos` | NPC-local elevation | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `relative_velocity_x` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `relative_velocity_y` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `relative_velocity_z` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `closing_speed_norm` | positive means approaching | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `path_distance_norm` | navigation estimate to believed position | `cm` | `{"divisor_ref":"path_distance_max_cm","max":1.0,"min":0.0,"sentinel":"invalid","sentinel_value":0.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":0.0,"policy":"sentinel","sentinel":"invalid"}` | `{}` |
| 15 | `path_reachable_belief` | path query to believed snapshot position | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `belief_age_norm` | now - observed_at | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `belief_confidence` | position/state confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 18 | `source_sight` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `source_hearing` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `source_last_known` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `source_shared` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `source_scripted` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `position_valid` | perceived/snapshot position is valid | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 24 | `visible_now` | currently perceived by sight | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 25 | `line_of_sight_belief` | LOS query against believed/currently perceived target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 26 | `sight_strength` | sensor strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 27 | `visible_duration_norm` | continuous visibility duration | `s` | `{"divisor_ref":"visible_duration_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 28 | `heard_recently` | valid hearing event associated with target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 29 | `hearing_strength` | normalized loudness/strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 30 | `time_since_seen_norm` | time since last sight; 1 if never | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"sentinel":"never","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"never"}` | `{}` |
| 31 | `time_since_heard_norm` | time since last hearing; 1 if never | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"sentinel":"never","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"never"}` | `{}` |

### B.4 event_features

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `age_norm` | now - event time | `s` | `{"divisor_ref":"event_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `strength` | event strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `confidence` | event confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `relative_position_x` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `relative_position_y` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `relative_position_z` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `distance_norm` | distance to event snapshot | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `bearing_sin` | event bearing | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `bearing_cos` | event bearing | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `source_sight` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `source_hearing` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `source_damage` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `source_scripted` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `result_success` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `result_failure` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `result_interrupted` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `urgent` | event urgency | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `target_present_in_current_slots` | stable handle remapped to current slot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 18 | `same_as_current_skill_target` | handle equality | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `same_goal_revision` | event goal revision equals current | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `magnitude_norm` | event-specific magnitude | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `duration_norm` | event-specific duration | `s` | `{"divisor_ref":"event_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `reserved_22` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `reserved_23` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### B.5 candidate_pair_features

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `same_as_current_skill` | candidate skill equals running skill | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `same_as_current_target` | typed handle equals running target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `target_present` | target slot is valid; NoTarget is valid | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `target_visible_now` | copied from target belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `target_position_confidence` | copied from target belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `target_age_norm` | copied from target belief | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `distance_norm` | copied from target feature | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `path_distance_norm` | computed to believed snapshot | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `path_reachable_belief` | computed to believed snapshot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `skill_requires_los` | Skill Registry metadata | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `los_satisfied_belief` | computed against currently permitted belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `skill_requires_resource` | Skill Registry metadata | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `resource_available_belief` | latest allowed availability snapshot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `skill_allowed_by_goal` | Goal contract | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `target_kind_allowed` | Skill Registry matrix | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `default_parameter_norm` | Skill Registry default primary parameter | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

## C. Target Payload [32:47]

### C.NoTarget

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `zero_0` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 1 | `zero_1` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 2 | `zero_2` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 3 | `zero_3` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 4 | `zero_4` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 5 | `zero_5` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 6 | `zero_6` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 7 | `zero_7` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 8 | `zero_8` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 9 | `zero_9` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 10 | `zero_10` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 11 | `zero_11` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 12 | `zero_12` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 13 | `zero_13` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 14 | `zero_14` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 15 | `zero_15` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.Entity

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `alive_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `armed_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `attacking_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `health_estimate` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `health_uncertainty` | estimate interval width | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `threat_estimate` | perception/classifier estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `interactable` | observed/known affordance | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `same_faction_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `affinity` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `trust` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `fear` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `hostility` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `debt` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `suspicion` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `current_action_confidence` | observed action classifier confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `identity_confidence` | entity attribution confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.SoundEvent

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `loudness` | normalized loudness | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `danger_estimate` | sensor/event semantic estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `attribution_confidence` | confidence in source attribution | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `repetition_norm` | repeat count / 8 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `class_footstep` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `class_weapon` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `class_explosion` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `class_voice` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `class_impact` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `class_door` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `class_vehicle` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `class_other` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `source_moving_probability` | event inference | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `occluded_probability` | hearing propagation estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `ttl_remaining_norm` | remaining TTL / event max TTL | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.LastKnownPosition

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `subject_is_player` | Belief semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `subject_hostile_probability` | snapshot belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `subject_armed_probability` | snapshot belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `subject_alive_probability_at_observation` | snapshot belief; not updated from hidden truth | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `motion_direction_sin` | last observed motion | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `motion_direction_cos` | last observed motion | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `observed_speed_norm` | last observed speed / 1200 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `reason_sight_lost` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `reason_shared` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `reason_scripted` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `goal_primary_target` | owned by active goal | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `search_radius_norm` | search radius / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `confidence_decay_rate_norm` | configured decay rate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `ttl_remaining_norm` | remaining snapshot TTL | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `subject_identity_confidence` | snapshot attribution confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.CoverSlot

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `cover_quality` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `exposure_reduction` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `flank_risk` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `distance_to_peek_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `occupancy_ratio` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `available_belief` | latest known availability | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `reserved_by_self` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `resource_generation_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `low_cover` | one-hot/flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `high_cover` | one-hot/flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `left_peek` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `right_peek` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `destructible_probability` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `lease_required` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `resource_age_norm` | availability revision age / 10s | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.SmartObject

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `availability_belief` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `capacity_norm` | capacity / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `occupancy_ratio` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `interaction_duration_norm` | seconds / 30 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `requires_item` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `use_type_door` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `use_type_console` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `use_type_pickup` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `use_type_heal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `use_type_vehicle` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `use_type_social` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `use_type_traversal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `use_type_other` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `resource_generation_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `resource_age_norm` | availability revision age / 10s | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.Waypoint

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `goal_primary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `goal_secondary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `sequence_progress` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `wait_duration_norm` | seconds / 30 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `desired_facing_sin` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `desired_facing_cos` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `patrol_waypoint` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `return_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `search_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `escape_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `formation_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `scripted_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `path_index_norm` | index / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `loop_flag` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `arrival_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.WorldPosition

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `goal_primary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `goal_secondary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `safe_zone_probability` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `search_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `arrival_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `desired_facing_sin` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `desired_facing_cos` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `source_goal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `source_script` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `source_shared_knowledge` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `source_player_ping` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `immutable_flag` | must be 1 in V1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"occupied_required_value":1.0,"policy":"padding_zero","value":0.0}` | `{"occupied_required_value":1.0}` |
| 13 | `ttl_remaining_norm` | remaining TTL / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `authority_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

## D. Skill·Goal·Hash 계약

### D.1 Skill Parameter

| Skill ID | Skill | Slot | Parameter | Active | Unit | Min | Max | Default |
|---:|---|---:|---|---:|---|---:|---:|---:|
| 0 | `Idle` | 0 | `duration` | 1 | `second` | 0.5 | 5.0 | 1.0 |
| 0 | `Idle` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 0 | `Idle` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 0 | `Idle` | 3 | `intensity` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 0 | `duration` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 3 | `intensity` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 0 | `duration` | 1 | `second` | 0.25 | 3.0 | 1.0 |
| 2 | `LookAt` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 3 | `TurnTo` | 0 | `duration` | 1 | `second` | 0.25 | 2.0 | 0.75 |
| 3 | `TurnTo` | 1 | `speed` | 1 | `degree_per_second` | 90.0 | 720.0 | 360.0 |
| 3 | `TurnTo` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 3 | `TurnTo` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 4 | `Approach` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 4 | `Approach` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 350.0 |
| 4 | `Approach` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 500.0 | 200.0 |
| 4 | `Approach` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 5 | `KeepDistance` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 5 | `KeepDistance` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 300.0 |
| 5 | `KeepDistance` | 2 | `preferred_distance` | 1 | `centimeter` | 200.0 | 1000.0 | 500.0 |
| 5 | `KeepDistance` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 6 | `RetreatFrom` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 6 | `RetreatFrom` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 650.0 | 400.0 |
| 6 | `RetreatFrom` | 2 | `preferred_distance` | 1 | `centimeter` | 300.0 | 1500.0 | 700.0 |
| 6 | `RetreatFrom` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 7 | `Follow` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 4.0 |
| 7 | `Follow` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 350.0 |
| 7 | `Follow` | 2 | `preferred_distance` | 1 | `centimeter` | 150.0 | 700.0 | 350.0 |
| 7 | `Follow` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 8 | `Investigate` | 0 | `duration` | 1 | `second` | 1.0 | 12.0 | 5.0 |
| 8 | `Investigate` | 1 | `speed` | 1 | `centimeter_per_second` | 100.0 | 500.0 | 280.0 |
| 8 | `Investigate` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 1200.0 | 400.0 |
| 8 | `Investigate` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.6 |
| 9 | `SearchArea` | 0 | `duration` | 1 | `second` | 3.0 | 20.0 | 8.0 |
| 9 | `SearchArea` | 1 | `speed` | 1 | `centimeter_per_second` | 80.0 | 400.0 | 220.0 |
| 9 | `SearchArea` | 2 | `preferred_distance` | 1 | `centimeter` | 200.0 | 2000.0 | 700.0 |
| 9 | `SearchArea` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.6 |
| 10 | `Greet` | 0 | `duration` | 1 | `second` | 1.0 | 5.0 | 2.0 |
| 10 | `Greet` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 10 | `Greet` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 10 | `Greet` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 11 | `Warn` | 0 | `duration` | 1 | `second` | 1.0 | 5.0 | 2.0 |
| 11 | `Warn` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 11 | `Warn` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 11 | `Warn` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 12 | `CallForHelp` | 0 | `duration` | 1 | `second` | 1.0 | 4.0 | 2.0 |
| 12 | `CallForHelp` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 12 | `CallForHelp` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 12 | `CallForHelp` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.8 |
| 13 | `TakeCover` | 0 | `duration` | 1 | `second` | 1.0 | 10.0 | 4.0 |
| 13 | `TakeCover` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 650.0 | 400.0 |
| 13 | `TakeCover` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 13 | `TakeCover` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 14 | `Flee` | 0 | `duration` | 1 | `second` | 1.0 | 15.0 | 6.0 |
| 14 | `Flee` | 1 | `speed` | 1 | `centimeter_per_second` | 200.0 | 700.0 | 500.0 |
| 14 | `Flee` | 2 | `preferred_distance` | 1 | `centimeter` | 500.0 | 3000.0 | 1500.0 |
| 14 | `Flee` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.9 |
| 15 | `Attack` | 0 | `duration` | 1 | `second` | 0.2 | 5.0 | 1.0 |
| 15 | `Attack` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 15 | `Attack` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 2000.0 | 600.0 |
| 15 | `Attack` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |

### D.2 Goal Registry

| Goal ID | Goal | Initial phase | Priority | Source | Interruptibility | Resume |
|---:|---|---|---:|---|---|---|
| 1 | `IdleObserve` | `Observe` | 10 | `Routine` | `Always` | `ResumeSamePhase` |
| 2 | `InvestigateDisturbance` | `Orient` | 120 | `Social` | `PhaseBoundary` | `ResumeSamePhase` |
| 3 | `EnforceBoundary` | `Observe` | 160 | `Quest` | `PhaseBoundary` | `ResumeSamePhase` |
| 4 | `CombatEngage` | `Orient` | 220 | `Combat` | `EmergencyOnly` | `RestartPhase` |
| 5 | `Disengage` | `-` | - | `-` | `-` | `-` |
| 6 | `Escort` | `-` | - | `-` | `-` | `-` |
| 7 | `Reserved` | `-` | - | `-` | `-` | `-` |

### D.3 Hash: candidate_set_hash

- Algorithm: `SHA-256`
- Byte order: `little`

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"ANPCSET2"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `schema_source_sha256` | `bytes[32]` | `{}` |
| 3 | `target_slot_count` | `uint8` | `{"value_ref":"total_target_slots"}` |
| 4 | `target_handles` | `target_handle[17]` | `{"field_order":["kind:uint8","stable_id:uint64","generation:uint32","revision:uint64"]}` |
| 5 | `target_mask` | `bitset` | `{"bit_count":17,"bit_order":"LSB-first","byte_count":3,"unused_high_bits":"zero"}` |
| 6 | `candidate_mask` | `bitset` | `{"bit_count":272,"bit_order":"LSB-first","byte_count":34,"unused_high_bits":"none"}` |

### D.3 Hash: decision_contract_hash

- Algorithm: `SHA-256`
- Byte order: `little`

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"ANPCDEC2"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `schema_source_sha256` | `bytes[32]` | `{}` |
| 3 | `skill_registry_sha256` | `bytes[32]` | `{}` |
| 4 | `goal_registry_sha256` | `bytes[32]` | `{}` |
| 5 | `model_sha256` | `bytes[32]` | `{}` |
| 6 | `normalization_contract_sha256` | `bytes[32]` | `{}` |
| 7 | `slotter_contract_sha256` | `bytes[32]` | `{}` |
| 8 | `postprocess_contract_sha256` | `bytes[32]` | `{}` |
| 9 | `calibration_ood_asset_sha256` | `bytes[32]` | `{}` |

### D.4 Normalizer 의미 규칙

```json
{
  "clamp_bounds_order": "min_lte_max",
  "constant_and_sentinel_value_must_fit_valid_range": true,
  "constant_missing_value_must_equal_normalizer_constant": true,
  "constraint_and_missing_occupied_value_must_match": true,
  "divisor_and_referenced_scale_must_be_positive": true,
  "log1p_input_domain": {
    "denominator_must_be_positive": true,
    "exclusive_min": -1.0
  },
  "missing_contract_must_match_normalizer": true,
  "must_equal_requires_constant_normalizer": true,
  "must_equal_requires_matching_missing_value": true,
  "must_equal_requires_singleton_valid_range": true,
  "normalizer_output_must_fit_valid_range": true,
  "numeric_values_must_be_finite": true,
  "padding_zero_value_must_fit_valid_range": true,
  "valid_range_order": "min_lte_max"
}
```

<!-- END AUTO-GENERATED SCHEMA CONTRACT -->

# Appendix E. KPI·Dataset·Performance Gate

## E.1 고정 평가 버전

- Utility Baseline: `utility_baseline_v1.0.0`
- Schema: `2.0.0`
- Target Slotter: `1.0.0`
- Post-process: `1.0.0`
- Critical Suite: `critical_suite_v1`, **512 sequences = 8 family × 64 case**

### E.1.1 Critical 8 Family

1. `perception_belief_visibility`
2. `typed_target_slotting`
3. `goal_arbitration_transition`
4. `candidate_mask_and_hash`
5. `async_latest_only_and_atomic_commit`
6. `hidden_information_boundary`
7. `skill_parameter_and_resource_cas`
8. `save_load_hot_swap_recovery`

### E.1.2 OOD 8 Family

1. `feature_range_shift`
2. `missing_modality_pattern`
3. `unseen_role_attribute_combination`
4. `candidate_count_pattern`
5. `belief_age_confidence_shift`
6. `environment_layout_density_shift`
7. `event_sequence_shift`
8. `sensor_noise_shift`

## E.2 Candidate/Target

| Metric | Dataset | Gate |
|---|---|---|
| Target Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Any-Acceptable Candidate Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Critical Target/Candidate Recall | Critical Suite 256 sequences | 100%, 분모와 miss 모두 보고 |
| MandatoryOverflow | Critical + General | 0건 |

## E.3 Safety

절대 Gate:

- Critical Suite 256 sequences에서 hard-constraint 위반 Commit 0건
- Randomized Safety Fuzz 100,000 decision에서 hard-constraint 위반 Commit 0건
- Hidden Information Leakage Test 10,000 pair에서 Tensor/행동 누출 0건
- Server authority 우회 0건

Safety는 Baseline 비열등만으로 대체할 수 없다.

## E.4 Calibration/OOD

| Metric | Gate |
|---|---|
| ECE | ≤0.05 |
| Brier Score | ≤0.18 |
| Risk at 80% coverage | ≤0.10 |
| OOD recall | ≥0.90 at FPR ≤0.10 |
| 각 Role×Goal Calibration group | 최소 400 Gold states |

## E.5 품질 승격

Primary superiority metric:

- Baseline과의 blind naturalness A/B
- 600 unique sequence, 각 3명 평가, Role×Goal group당 최소 50 sequence
- cluster bootstrap 10,000회
- 모델 point win rate ≥55%
- 95% CI lower bound >52%

동시에 다음 secondary metric은 비열등해야 한다.

| Metric | Non-inferiority Margin |
|---|---:|
| Goal completion rate | Neural - Baseline 95% CI lower bound ≥ -2.0 percentage points |
| Unnecessary skill switch rate | Neural - Baseline 95% CI upper bound ≤ +0.2 switch/10s |
| P95 stable-scenario switch count | 절대 ≤3 switch/10s |
| Player fairness/understandability rating | 95% CI lower bound ≥ -0.10 on 5-point normalized scale |

승격 조건은 다음 AND다.

```text
Safety absolute Gate
AND Candidate/Target Gate
AND Latency Gate
AND Calibration/OOD Gate
AND Primary quality superiority
AND 나머지 core quality non-inferiority
```

## E.6 Dataset 최소량

V1의 3 Role × 4 Goal = 12 group 기준:

| Split | Group당 최소 | 총 최소 |
|---|---:|---:|
| Gold Train | 800 | 9,600 |
| Gold Calibration | 400 | 4,800 |
| Gold Test | 400 | 4,800 |
| DAgger Intervention | 200 | 2,400 |
| OOD Test | 8 family당 200 | 1,600 이상 |
| Critical Suite | 8 family×64 | 512 sequences |

Silver는 25k→50k→100k→200k learning curve를 작성한다. 두 번 연속 doubling에서 전체 primary validation 개선 <0.5pp이고 worst-group 개선 <1.0pp이면 추가 합성의 한계로 판단한다. 최소 100k Silver 이전에는 V1 freeze 결정을 하지 않는다.

## E.7 Latency·성능

Reference Hardware의 정확한 CPU/GPU/Build/backend는 `perf_manifest.json`에 고정하고 변경 시 재승인한다.

부하:

```text
Typical: 100 decisions/sec
Burst:   250 decisions/sec for 1 second
Candidate: 272 fixed rows
```

최소 표본:

- Typical 10,000 decisions
- Burst 2,500 decisions
- warm-up 500 decisions 제외

Gate:

| Metric | Absolute Budget | Baseline Non-inferiority Margin |
|---|---:|---:|
| Neural batch inference p95 | ≤6ms | N/A — absolute budget |
| Neural batch inference p99 | ≤12ms | N/A — absolute budget |
| Request-to-Commit p95 | ≤20ms | `utility_baseline_v1.0.0` +15ms |
| Request-to-Commit p99 | ≤40ms | `utility_baseline_v1.0.0` +30ms |
| Typical deadline miss | <0.1% | +0.05pp |
| Burst deadline miss | <1.0% | +0.5pp |

## E.8 통계 방법

- 비율: Wilson 95% CI
- paired A/B: scenario-cluster bootstrap 10,000회
- Goal completion/oscillation 차이: Role×Goal stratified bootstrap 10,000회
- latency percentile: request bootstrap 10,000회 및 raw percentile 동시 보고
- worst-group는 평균으로 상쇄하지 않고 별도 Gate로 보고

---

# 12. 최종 승인 체크리스트

Schema 2.0 Freeze 승인에는 다음이 모두 필요하다.

- [ ] `ai_native_npc_schema_v2_0.yaml`에서 C++/Python/문서 생성
- [ ] Enum·Mask·Padding·Hash Golden Vector byte-identical
- [ ] Float Feature parity tolerance 통과
- [ ] 17 Target Slot과 272 Candidate layout parity
- [ ] Typed Target Runtime Payload 구현
- [ ] Target Slotter Target Recall Gate 통과
- [ ] Goal Arbitration/FSM Phase 0 테스트 통과
- [ ] Adjusted Score→OOD→Calibration 순서 parity
- [ ] Atomic Commit rollback·lease·urgent cancellation 테스트 통과
- [ ] Hidden Information Leakage Test 통과
- [ ] Appendix E의 실제 Baseline/CI/표본 Gate 통과

이 문서와 YAML이 상충하면 YAML의 field index·enum·shape를 우선하며, 아키텍처 의미와 실행 경계는 본 문서를 우선한다. 충돌 발견 시 두 artifact의 patch version을 함께 올린다.
