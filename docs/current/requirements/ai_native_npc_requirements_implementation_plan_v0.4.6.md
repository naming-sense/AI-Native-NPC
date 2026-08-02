# AI Native NPC 의사결정 시스템
## 요구사항·구현 계약·Schema 2.0 명세서

- 문서 버전: **v0.4.6**
- Schema 상태: **2.0.0 RC5 Harness PASS / Requirements Remediation pending / Not Freeze-ready**
- 개정일: 2026-08-02
- 문서 보강: **ML/NNE Implementation Supplement 1 + Requirements Review Remediation 1**
- 검토 근거: `docs/current/reviews/ai_native_npc_requirements_review_v0.4.6.md`
- 대체 문서: `ai_native_npc_requirements_implementation_plan.md` v0.2 및 별도 v0.3/v0.4 보완 메모
- 문서 성격: 연구 제안서가 아니라 **Unreal 클라이언트·Python 학습 코드·서버 실행기가 함께 따라야 하는 단일 구현 기준서**
- ML 구현 프로필: **`policy_arch_v1.0.0` / `policy_train_v1.0.0` / ONNX opset 17**
- Phase 0 판정: **조건부 GO — Utility Baseline 중심 수직 슬라이스 착수 가능**
- V1 ML/NNE 판정: **HOLD — OOD output·Dataset Switch Cost·Goal Registry remediation 필요**
- Schema 2.0 판정: **RC5 Harness PASS / 새 remediation 미반영 / Unreal Runtime Gate 통과 전 최종 Freeze 보류**

---

# 0. v0.4.6 Validation Scope & Catalog Closure 판정

최신 리뷰는 타당하다. v0.4.2는 cross-environment release와 Python↔C++ Golden parity를 해결했지만, YAML 필드 변경이 문서 Appendix에 자동 반영되지 않았고, Normalizer의 역전 범위·0 이하 divisor 같은 의미 오류를 충분히 차단하지 못했으며, Hash serializer 일부가 YAML이 아니라 생성기 코드에 하드코딩되어 있었다.

v0.4.6는 기존 v0.4.2 계약에 다음 Semantic Closure를 추가한다.

이번 RC5는 수기 Hash magic 전면 차단, Critical Suite 최소 분모의 Taxonomy 자동 파생·문서 동기화, RC5 릴리스 승격을 최종 고정 범위로 추가한다.

v0.4.6은 의미 검증을 모든 Lock 대상 non-archive 수기 Markdown으로 확장하고, Catalog Archive 목록과 실제 Archive 파일 집합을 양방향 exact-match로 고정한다. README 기반 전체 release mutation과 Missing/Ghost Archive 회귀 테스트를 규범 증거로 포함한다.

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

2026-07-30 RC5 보관 Harness 시점의 역사적 판정:

- Phase 0: **GO**
- Schema 코드 생성: **GO**
- 대량 학습 데이터 생성: **HOLD**
- Schema 2.0 최종 Freeze: Float/ONNX parity와 Runtime Gate 통과 전 **NO-GO / Conditional**

위 GO는 2026-08-02 Requirements Review Remediation 이전 RC5 artifact에 대한 기록이다. 현재 작업 판정은 문서 상단과 §0.1의 조건부 GO/HOLD/NO-GO가 대체한다.

2026-07-30 ML/NNE 구현 보강은 Schema·Enum·Registry·Tensor Shape·Hash 값을 바꾸지 않는다. 대신 기존에 방향만 있던 신경망을 실제 코드로 옮길 수 있도록 모델 Layer, Dataset Record, Loss, 학습 설정, Calibration/OOD, ONNX Export와 Unreal NNE 적용 절차를 고정한다. Phase 0의 작은 fixture 모델과 end-to-end smoke test는 진행해도 되지만, Feature Capture parity와 split validator가 통과하기 전 V1 대량 데이터 생성은 계속 HOLD다.

고정 태그 `full-harness-v0.4.6-rc5`의 Freeze-ready 증거는 이 보강 전 Schema·기반 문서를 검증한다. 이번 Supplement는 그 Schema 값을 변경하지 않지만 기존 90파일 Lock bundle에는 포함되지 않는다. 최종 Freeze 또는 계약 값 변경 시에는 Supplement를 포함한 새 문서 버전으로 전체 Harness를 다시 baseline해야 한다.

## 0.1 Requirements Review Remediation 1 판정

2026-08-02 검토는 RC5 Harness PASS와 Runtime/ML 계약 승인을 분리한다. 기존 YAML·생성 코드의 byte parity와 문서 하네스는 유효하지만, 새 ML/NNE 구현 계약은 다음 네 항목이 닫히기 전 V1 구현·대량 학습·최종 Freeze의 규범 입력으로 승격할 수 없다.

1. Unreal Runtime OOD 계산을 위한 `tactical_context [B,128]` ONNX output
2. 학습·평가에서 Runtime Switch Cost를 재현하는 Candidate별 component record
3. Goal arbitration의 `preemption_margin`, 생성시간 quantization, suspended resume, revision 단일 계약
4. Event/Timer/Lifecycle을 분리한 Typed Goal Trigger와 phase timeout Registry

판정은 다음과 같다.

| 범위 | 판정 | 허용 범위 |
|---|---|---|
| 기존 RC5 Schema/Generated Harness | PASS | 현 RC5 계약의 생성·Golden·문서 parity 증거로 사용 |
| Phase 0 Utility Baseline 수직 슬라이스 | 조건부 GO | OOD/Calibration 품질 승격 주장을 하지 않고 fallback·capture·commit 경로 검증 |
| Phase 0 fixture Neural smoke | 조건부 GO | 현 2-output model은 score/parameter smoke에만 사용하며 OOD Runtime Gate 증거로 사용 금지 |
| V1 Neural Training/Calibration | HOLD | Dataset Switch Cost와 output/Goal 계약 patch 후 재개 |
| 대량 학습 데이터 생성 | HOLD | feature/content hash와 split case catalog validator 통과 후 재개 |
| Schema 2.0 최종 Freeze | NO-GO | 새 Schema/Registry 생성·Golden·Runtime Gate·Formal Approval 필요 |

이번 Remediation은 Requirements의 목표 계약을 고정하지만 현재 RC5 YAML·Generated output을 수동 수정하지 않는다. Tensor shape, output, Registry 값 변경은 후속 patch release에서 Generator로 재생성하고 새 Decision Contract Hash를 발급해야 한다.

## 0.2 독자·Runtime·집행 경계

| 규칙군 | 주 독자 | 적용 Runtime/단계 | 집행 위치 |
|---|---|---|---|
| Tensor/ONNX/OOD | ML·Unreal NNE | Export, Import, NNE binding, Post-process | Schema output, Bundle Validator, UE descriptor validation, parity test |
| Dataset/Switch Cost | Data·ML | Capture, Dataset Validation, Train/Evaluate | Dataset schema, Validator, loss/evaluation code |
| Goal arbitration/trigger | Gameplay AI·Server | Goal Manager, Save/Load, async invalidation | Goal Registry, generated FSM, Runtime tests |
| Snapshot/Commit | Gameplay AI·Server | inference envelope, GameThread Commit | Commit Coordinator, stale/rollback tests |
| KPI/승격 | QA·ML·승인자 | General/OOD/Critical/Performance evaluation | Taxonomy, case catalog, release report, formal approval |

이 Markdown의 문장만으로 Runtime enforcement가 생기지 않는다. 각 규칙은 표의 집행 위치에 구현되고 해당 evidence가 Freeze Manifest에 잠긴 뒤에만 완료로 판정한다.

현재 Runtime/학습 Tensor 계약의 단일 원본은 다음 세 파일이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

평가 family와 KPI 분모의 단일 원본은 별도 `contracts/current/test_taxonomy_v1.yaml`이다.

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
- Switch Cost의 `target_changed`, `same_as_current_target`, `same_as_current_skill_target`, Continue slot 재매핑은 `IdentityKey` 비교를 사용한다.
- `Revision`만 바뀐 동일 identity는 Target switch가 아니라 snapshot update다. 이 변경은 `SnapshotKey` stale 검증에는 반영하지만 switch penalty를 만들지 않는다.
- Canonical serialization의 `FTargetHandle` 전체 byte 비교를 의미상 same-target 비교로 재사용하지 않는다.

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
5. 최근 피해를 준 Attacker — 최대 2
6. Active Goal Secondary Target — 최대 2

source 내부에서 최대 개수보다 많은 Target이 있으면 다음 canonical key를 사용한다.

| Source | 내부 선정 Key |
|---|---|
| Reservation Resource | `resource_kind asc → canonical handle bytes asc` |
| Recent Attacker | `damage_time_quantized_ms desc → canonical handle bytes asc` |
| Goal Secondary | `secondary_rank:uint16 asc → canonical handle bytes asc` |

`damage_time_quantized_ms`는 server monotonic time을 millisecond 단위로 `floor`한 값이다. `secondary_rank`는 Goal Manager가 Goal contract 생성 시 발급하고 Goal revision 없이 재정렬할 수 없다.

Mandatory는 category quota를 초과할 수 있지만 일반 slot 16개를 초과할 수 없다. 현재 V1 source별 최대 합은 `1+1+1+2+2+2=9`이므로 정상 Schema 계약에서는 `MandatoryOverflow`에 도달할 수 없다.

- `MandatoryOverflow`는 미래 Schema cap 변경 또는 잘못된 source cap 구현을 방어하는 Runtime invariant다.
- Schema `target_slots.mandatory_preserve_order`의 source cap 합이 16을 초과하는 변경은 Schema semantic validation에서 release 전에 거부한다.
- Runtime에서 16개 초과가 관측되면 source cap 위반으로 기록하고 Neural Policy를 abstain하며 Goal별 fallback을 사용한다.
- 해당 관측은 Critical Suite 실패이며, 현재 V1 품질을 증명하는 비자명 KPI로 계산하지 않는다.

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

한 Decision state `s`의 Gold relevant Target 집합을 `R(s)`라고 한다. Relevant Target은 해당 Goal phase에서 하나 이상의 safe acceptable Skill을 실행하거나 Critical invariant를 만족하는 데 필요한 unique `IdentityKey`이며, Ground Truth label channel에서만 작성한다.

```text
Target Recall numerator   = Σ_s |SlottedIdentity(s) ∩ R(s)|
Target Recall denominator = Σ_s |R(s)|
```

- `R(s)=∅` state는 Target Recall에서 제외하고 분모를 별도 보고한다.
- 만료·파괴 등 label 시점에 유효하지 않은 Target은 `R(s)`에 넣지 않는다. 사후 임의 제외를 금지한다.
- General Target Recall point estimate ≥99.5%, relevant-target trial Wilson 95% lower bound ≥99.0%다.
- Critical Suite는 512 sequence의 모든 decision·relevant-target trial을 보고하고 miss 0건이어야 한다.
- 보고서는 target-trial micro, decision-state micro, Role×Goal macro, sequence별 miss를 모두 포함한다.
- episode-cluster bootstrap 10,000회 CI를 민감도 분석으로 함께 보고하며 Wilson만으로 상관 구조를 숨기지 않는다.
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
Any-Acceptable Recall numerator   = Σ_s 1[C(s) ∩ G(s) ≠ ∅]
Any-Acceptable Recall denominator = count{s | |G(s)| > 0}

Full Acceptable Recall numerator   = Σ_s |C(s) ∩ G(s)|
Full Acceptable Recall denominator = Σ_s |G(s)|
```

- 한 trial은 immutable Decision state 한 개다. `G(s)`는 annotation freeze 이후 변경하지 않는다.
- `abstain-only`, 즉 `G(s)=∅`인 state는 두 Recall에서 제외하고 별도 분모·fallback 성공률로 보고한다.
- 동일 Candidate index의 duplicate label은 Dataset Validator 실패다.
- General Any-Acceptable Recall은 Appendix E의 point/Wilson Gate를 따른다.
- Full Acceptable Recall은 승격 절대 Gate는 아니지만 전체, Role×Goal, Target Kind, valid-count bucket별 필수 보고 metric이다.
- Critical Suite는 sequence·decision·acceptable-candidate 분모를 모두 보고하며 Any-Acceptable miss 0건이어야 한다.
- episode-cluster bootstrap 10,000회 CI를 함께 보고한다.

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
(-priority, -source_priority, created_time_quantized_ms, goal_instance_id)
```

- `priority`: uint8, 높은 값 우선
- `source_priority`: Emergency 4 > Quest 3 > Combat 2 > Social 1 > Routine 0
- `created_time_quantized_ms`: `floor(max(server_monotonic_world_seconds,0) × 1000)`을 uint64로 저장하며 먼저 생성된 Goal 우선
- `goal_instance_id`: 낮은 값 우선
- quantized 생성시간은 Goal 생성 시 한 번 고정하고 save/load에서 보존한다. raw float `created_at`을 arbitration 비교에 사용하지 않는다.

## 5.4 Preemption

Active phase는 다음 interruptibility 중 하나를 가진다.

| 값 | 일반 상위 Goal | Emergency | Server ForceAbort |
|---|---|---|---|
| Always | 즉시 preempt | 즉시 | 즉시 |
| PhaseBoundary | phase/skill 경계에서 | 즉시 | 즉시 |
| EmergencyOnly | 대기 | 즉시 | 즉시 |
| Never | 대기 | 대기 | 즉시 |

일반 preemption은 다음을 모두 만족해야 한다.

1. 새 Goal의 Arbitration Key가 현재 Active Goal보다 lexicographic하게 작다.
2. `new.priority ≥ active.priority + preemption_margin`이다.
3. V1 `preemption_margin`은 Goal Registry의 `50`이다. uint8 계산 전 넓은 정수형으로 승격해 overflow를 금지한다.
4. 현재 interruptibility가 허용하는 시점이다.

Emergency source는 `preemption_margin`과 일반 priority key 우위를 우회하고 위 표의 Emergency 열을 따른다. 둘 이상의 Emergency 후보끼리는 같은 Arbitration Key로 정렬한다. `Server ForceAbort`는 replacement Goal preemption이 아니라 현재 Active Goal을 즉시 `Aborted`로 만드는 authoritative terminal command이며, margin·key·interruptibility를 모두 우회한다.

Preempt 시 Resume Policy:

- `ResumeSamePhase`: snapshot을 Suspended collection에 저장
- `RestartPhase`: phase 초기 상태로 재개하도록 저장
- `AbortOnPreempt`: 즉시 Aborted

현재 Goal을 preempt할 새 Goal의 activation 준비가 실패하면 기존 Goal은 계속 Active다. 반쪽 preemption은 허용하지 않는다.

Suspended 최대 8개가 이미 찬 상태에서 새 suspension이 필요하면 일반 preemption은 거부한다. Emergency Goal은 replacement activation 준비를 먼저 완료한 뒤 Suspended 중 Arbitration Key가 가장 나쁜 Goal을 `Aborted` 처리하고 현재 Goal을 저장할 수 있으며, 이 eviction을 audit event로 기록한다. activation 준비 실패 시 eviction과 현재 Goal 변경을 모두 금지한다. `Server ForceAbort`는 현재 Goal을 저장하거나 기존 Suspended Goal을 evict하지 않는다. `AbortOnPreempt`는 slot을 소비하지 않는다.

## 5.5 Suspended Resume

Suspended 저장 구조가 stack이어도 재개 선택은 LIFO가 아니라 Goal Registry의 `same_selection_key`를 따른다.

1. Active Goal이 terminal이 되면 valid한 Suspended Goal과 Inactive Goal을 함께 Arbitration Key로 정렬한다.
2. 가장 작은 Key의 후보를 activate/resume한다.
3. Suspended 후보는 Resume Policy에 따라 같은 phase 또는 phase 초기 상태로 validation한다.
4. resume validation 실패 시 해당 Goal을 Failed 또는 Aborted로 terminal 처리하고 다음 후보를 평가한다.
5. 동일 Key tie는 `goal_instance_id`까지 포함한 전체 Key로 해소한다.

## 5.6 goal_revision 증가 조건

| 변경 | Revision 증가 |
|---|---|
| Active Goal instance 변경 | 예 |
| Active↔Suspended 또는 terminal 전환 | 예 |
| Intent Phase 변경 | 예 |
| Primary authoritative Target Handle 변경 | 예 |
| allowed/forbidden Skill bitset 변경 | 예 |
| authoritative deadline 값 변경 | 예 |
| interruptibility 변경 | 예 |
| resume policy 변경 | 예 |
| 매 frame progress 변화 | 아니오 |
| deadline countdown | 아니오 |
| Event Buffer 변화 | 아니오 |
| Belief revision 변화 | 아니오 |
| Candidate score 변화 | 아니오 |

Goal Registry `revision_contract.increase_on`은 `interruptibility_changed`, `resume_policy_changed`를 포함해야 한다. 해당 Registry patch 전에는 Goal Runtime Gate와 최종 Freeze를 통과할 수 없다.

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

## 5.9 Typed Goal Trigger와 Phase Timeout

Goal transition의 `trigger`는 다음 네 namespace 중 하나다.

| `trigger.kind` | 값의 단일 원본 | Event Buffer 저장 |
|---|---|---|
| `event` | Schema `event_type` enum | 예 |
| `timer` | Goal Registry의 `timer_id`, `after_seconds` | 아니오; 발생 결과만 audit 가능 |
| `lifecycle` | `OnEnter`, `OnResume`, `OnPhaseBoundary` | 아니오 |
| `server_control` | `ForceAbort` 등 authoritative command | 아니오 |

`Timeout`을 Schema `event_type`의 암묵적 확장으로 취급하지 않는다. Timer transition은 다음처럼 구조화한다.

```yaml
trigger:
  kind: timer
  timer_id: phase_timeout
  after_seconds: 1.5
```

규칙:

- `after_seconds`는 finite positive float이며 phase entry/resume 시점의 server monotonic deadline으로 변환한다.
- Timer countdown 자체는 `goal_revision`을 올리지 않지만 deadline 계약 값 변경은 revision을 올린다.
- `ResumeSamePhase` suspension은 phase timer를 pause하고 `remaining_ms = max(0, deadline_ms - suspended_at_ms)`를 uint64로 저장한다. resume 시 full duration으로 초기화하지 않고 이 remaining time으로 재무장한다.
- `RestartPhase` suspension은 이전 phase timer remaining을 폐기한다. resume 시 phase `OnEnter`를 다시 실행하고 Registry의 full `after_seconds`로 재무장한다.
- Suspended 동안 phase timer는 진행하지 않지만 Goal의 별도 authoritative absolute deadline은 계속 진행한다. resume validation 시 이미 지난 absolute deadline은 Goal을 terminal 처리한다.
- Save/Load는 timer ID, timer contract duration, `remaining_ms`, Resume Policy를 보존한다. Load 후 server monotonic epoch가 달라도 stored remaining으로 재무장하며 wall-clock을 사용하지 않는다.
- 동일 tick에 여러 trigger가 발생하면 Registry의 contiguous `order`가 우선하고, 같은 order는 validation 실패다.
- `goal_registry_v1.yaml`의 현재 문자열 `event: Timeout`과 누락된 duration은 후속 Registry patch에서 typed trigger로 변환한다.
- Registry patch 전에는 Goal FSM Runtime Gate를 PASS로 표시할 수 없다.
- Companion UE 문서의 Phase 0 표가 Registry와 다르면 Registry transition을 우선하며, UE 표는 Registry에서 재생성한 뒤 parity를 검사한다.

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

### `policy_arch_v1.0.0` 정확한 Layer 계약

아래 Layer와 상수는 V1 Reference Model의 규범 계약이다. 실험 모델은 별도 이름으로 만들 수 있지만, V1 승격 후보는 이 구조를 그대로 사용하거나 architecture version을 올리고 모든 parity·Calibration·성능 Gate를 다시 통과해야 한다.

공통 설정:

| 항목 | 고정값 |
|---|---|
| 내부 dtype | FP32 |
| Linear 초기화 | Xavier uniform, bias 0 |
| Embedding 초기화 | Normal mean 0, std 0.02 |
| LayerNorm epsilon | `1e-5` |
| L2Normalize epsilon | `1e-12` |
| Activation | ReLU |
| Training Dropout | `0.10`; `eval()`과 ONNX에서는 비활성 |
| Candidate index | `skill_id = index // 17`, `target_slot = index % 17` |

Encoder:

```text
Global
  [B,128]
  → Linear(128,256) → LayerNorm(256) → ReLU → Dropout(0.10)
  → Linear(256,128) → LayerNorm(128) → ReLU
  = global_embedding [B,128]

Target
  target_kind_embedding: Embedding(8,8)
  concat(target_features 48, kind_embedding 8) = 56
  → Linear(56,128) → LayerNorm(128) → ReLU
  → Linear(128,64) → LayerNorm(64) → ReLU
  = target_embedding [B,17,64]

  mean = sum(embedding×mask) / clamp_min(sum(mask),1)
  max = max(Where(mask,embedding,-1e9))
  concat(mean,max) = target_context [B,128]
  slot 16 NoTarget은 항상 valid이므로 all-masked Target 입력은 허용하지 않음

Event
  event_type_embedding: Embedding(16,8)
  event_target_slots로 target_embedding 64 gather
  concat(event_features 24, type_embedding 8, referenced_target 64) = 96
  → Linear(96,128) → LayerNorm(128) → ReLU
  → Linear(128,96) → LayerNorm(96) → ReLU
  = encoded_events [B,12,96]

  attention logits:
    Linear(96,64) → Tanh → Linear(64,1)
  event_mask=false logit은 -1e9로 바꾼 뒤 max를 빼고 exp(logit)×mask를 계산
  denominator는 clamp_min(1), event가 0개이면 context를 정확히 0으로 고정
  = event_context [B,96]

Fusion
  concat(global 128,target 128,event 96) = 352
  → Linear(352,256) → LayerNorm(256) → ReLU → Dropout(0.10)
  → Linear(256,128) → LayerNorm(128) → ReLU
  = tactical_context h [B,128]
```

Scorer와 Parameter Head:

```text
Query
  h → Linear(128,64) → LayerNorm(64) → L2Normalize

Candidate Key
  SkillEmbedding(16,64)[skill_id]
  + Linear(64,64)(target_embedding[target_slot])
  + Linear(16,64)(candidate_pair_features)
  → LayerNorm(64) → L2Normalize

Bias
  skill_bias: learnable [16], forward에서 [-0.25,0.25] clamp
  target_kind_bias: learnable [8], forward에서 [-0.25,0.25] clamp

Parameter Head, 모든 Candidate에 weight 공유
  concat(h 128, skill_embedding 64, target_embedding 64, pair_features 16) = 272
  → Linear(272,128) → ReLU → Linear(128,4) → Sigmoid
```

V1 OOD Runtime을 포함하는 목표 ONNX output 계약은 다음 세 개다.

```text
candidate_raw_scores             float32 [B,272]
candidate_parameter_proposals    float32 [B,272,4]
tactical_context                 float32 [B,128]
```

`tactical_context`는 Fusion의 `h`와 동일한 FP32 Tensor이며 별도 projection이나 post-export 변환을 적용하지 않는다. OOD asset fit, PyTorch 평가, ONNX Runtime, Unreal NNE가 이 동일 output을 사용한다.

현재 RC5 Schema Appendix는 앞의 두 output만 포함하므로 현 Schema로는 OOD Runtime Gate를 통과할 수 없다. 후속 Schema patch는 세 번째 output을 구조화된 원본에 추가하고 generated Python/C++/docs, UE descriptor, Golden output, Decision Contract Hash를 함께 갱신해야 한다.

`target_mask`, `event_mask`, `candidate_mask`는 attention·pooling·loss에 사용하지만 모델이 hard constraint를 새로 판단하는 수단은 아니다. Candidate Hard Mask의 소유자는 계속 Candidate Builder다. Candidate가 invalid여도 ONNX 출력 Tensor 크기는 고정 272이며, invalid row 출력은 loss·선택·parameter decode에서 전부 무시한다.

ONNX가 `candidate_mask` 입력을 제거하지 않도록 마지막에 score는 `Where(candidate_mask, score, 0)`, parameter는 `Where(candidate_mask.unsqueeze(-1), parameter, 0)`를 적용한다. Invalid row의 score와 parameter는 정확히 0이지만 의미는 없으며, valid row만 Runtime에서 사용한다.

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
- `skill_changed`는 실행 Skill ID 비교, `target_changed`는 `IdentityKey` 비교다. Target `Revision`만 바뀐 경우 `target_changed=0`이다.
- `before_min_duration`은 현재 실행 Skill의 authoritative minimum hold deadline과 request snapshot time으로 계산한다.
- `releases_or_transfers_reservation`은 현재 보유 Reservation 집합과 Candidate Execution Plan의 요구 Resource 집합이 다를 때 1이다.
- interrupt 불가능한 변경은 비용을 주는 대신 hard mask한다.
- 모든 비용은 dimensionless `[0,1]`이다.
- 계수 또는 λ가 바뀌면 `postprocess_version`을 올린다.
- Capture/Dataset은 네 boolean component를 Candidate별로 저장하고 Validator가 위 공식으로 재계산해야 한다.

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
- ONNX output `tactical_context h[128]`에 대해 squared Mahalanobis distance를 사용한다.

```text
delta_i = float64(h_i) - mean_i
tmp_i = Σ(j=0..127, ascending) precision[i,j] × delta_j
d2 = max(0, Σ(i=0..127, ascending) delta_i × tmp_i)
ood_continuous = clamp((d2 - q95_train) / (q99_9_train - q95_train), 0, 1)
ood_q = clamp(floor(ood_continuous × 1_000_000 + 0.5), 0, 1_000_000)
OOD = ood_q / 1_000_000
```

`q95_train`, `q99_9_train`도 동일한 `d2`의 empirical quantile이다. Runtime은 square root를 취하지 않는다.

수치 계약:

- ONNX `h`는 FP32이며 OOD 계산 직전에 각 element를 binary64로 승격한다.
- Python fit은 covariance/precision을 binary64로 계산하고 `precision = (precision + precision^T) / 2`로 한 번 대칭화한 값을 asset에 저장한다.
- mean `[128]`과 precision `[128,128]`은 JSON number→IEEE-754 binary64, precision은 C row-major로 해석한다.
- Python release reference와 Unreal은 위 `j` 내부, `i` 외부 scalar accumulation order를 사용한다. BLAS별 reduction order에 OOD Runtime을 맡기지 않는다.
- Calibrator의 OOD 입력과 Runtime threshold는 quantized `OOD`를 사용한다. `ood_q ≥ 800000`이면 abstain한다.
- Golden Gate는 `h abs/rel≤1e-4`, `d2 abs/rel≤1e-6`, `ood_q` byte-identical을 모두 요구한다. `ood_q`가 다르면 tolerance 안의 `d2`라도 Bundle을 승격하지 않는다.

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
| `feature_contract_hash` | schema + skill/goal registry + normalization + slotter + postprocess contract; model/calibration 제외 |
| `model_sha256` | `policy.onnx` raw bytes SHA-256 |
| `decision_contract_hash` | feature contract + model + calibration/OOD asset hash |

`postprocess_version`은 `candidate_set_hash`에 포함하지 않는다. Dataset Capture source의 Decision Contract와 새 Model을 학습하는 Feature Contract를 같은 값으로 취급하지 않는다.

후속 patch의 canonical hash는 hex 문자열이 아니라 decoded raw 32-byte digest를 이어 붙인다.

```text
feature_contract_hash = SHA256(
    ASCII("ANPCFEAT1")                         # 9 byte
  || schema_sha256_raw32
  || skill_registry_sha256_raw32
  || goal_registry_sha256_raw32
  || target_slotter_contract_sha256_raw32
  || normalization_contract_sha256_raw32
  || postprocess_contract_sha256_raw32
)

model_sha256 = SHA256(policy.onnx raw bytes)
calibration_ood_asset_sha256 = SHA256(calibration_ood_asset.json raw bytes)

decision_contract_hash = SHA256(
    ASCII("ANPCDEC3")                          # 8 byte
  || feature_contract_hash_raw32
  || model_sha256_raw32
  || calibration_ood_asset_sha256_raw32
)
```

- 각 입력 digest는 정확히 32 byte여야 하며 hex text, filename, path, JSON rendering을 대신 넣지 않는다.
- field order는 위 순서로 고정하고 length prefix는 사용하지 않는다. magic/version 변경 없이 field를 추가하지 않는다.
- 현재 RC5 generated serializer의 `ANPCDEC2`는 현 active contract의 증거로 유지한다. 위 `ANPCDEC3`는 Schema/Generator/Python/C++/Golden을 함께 올린 뒤에만 active다.
- Python/C++은 `ANPCFEAT1`과 `ANPCDEC3` input bytes 및 digest를 byte-identical Golden으로 검증한다.

---

# 7. 비동기 추론과 Atomic Commit

## 7.1 Request 상태

NPC별 상태:

- `next_decision_id`: uint64 단조 증가
- `commit_eligible_decision_id`: 최대 1개
- `active_cancellation_token`
- `dirty_flag`
- `urgent_flag`
- `latest_snapshot_revision`: Commit-relevant material state가 바뀔 때만 증가하는 uint64

각 inference request/response envelope는 `snapshot_revision:uint64`과 `snapshot_captured_at_monotonic_ms:uint64`를 저장한다. 이것은 연속적인 raw float 변화마다 증가시키는 frame counter가 아니다.

Material change:

- Active Goal instance/revision 변경
- Candidate Set/Mask 또는 Target `SnapshotKey` 변경
- 현재 Perception/LOS 상실 등 Commit 가능성을 바꾸는 변경
- Skill precondition, interruptibility, authoritative deadline 변경
- Resource generation/availability 변경
- 피격·폭발·강제 Goal 같은 urgent event

Non-material change:

- 로그·telemetry counter와 model input이 아닌 presentation state
- Schema에서 `staleness_class: continuous_nonmaterial`로 구조화된 float feature drift만 허용
- 해당 drift 중에도 모든 ID/enum/mask/bool/sentinel, Target `SnapshotKey`, Goal revision, Candidate Hash, Event ID/order, path reachable/LOS, Skill precondition, Resource generation/availability가 같아야 함

V1 `max_nonmaterial_stale_ms`는 `50`이다. 이 값과 Schema staleness allowlist는 Decision Runtime Contract에 포함하며 변경 시 Decision Contract Hash를 갱신한다. 현재 RC5 Schema에 staleness class가 없으므로 후속 patch 전 구현은 수기 field 추정을 금지하고 non-material stale Commit을 승격 증거로 사용할 수 없다.

## 7.2 In-flight 정책

- NPC당 **Commit 가능한 요청은 항상 1개 이하**다.
- material 일반 변경은 `latest_snapshot_revision`을 증가시키고 `dirty_flag`를 설정한다. 기존 worker가 끝날 수는 있지만 response의 revision이 다르면 `SnapshotSuperseded`로 폐기한다.
- non-material 일반 변경은 `dirty_flag`만 설정하고 기존 요청 완료/Commit 검증 후 최신 snapshot으로 재요청한다.
- 피격·폭발 같은 긴급 이벤트는 새 decision ID를 발급하고 기존 token을 cancel/supersede한다.
- Backend가 물리적으로 이전 worker를 즉시 중단하지 못해 잠시 두 작업이 돌 수는 있다.
- 취소된 decision ID 또는 stale `snapshot_revision`은 영구적으로 Commit 불가하며 응답 도착 즉시 폐기한다.
- 정책은 `latest-commit-relevant-snapshot-only`다.
- continuous drift 허용 응답도 request deadline과 Kind별 최신 Commit 검증을 모두 통과해야 한다.
- Commit 시 `current_server_monotonic_ms - snapshot_captured_at_monotonic_ms ≤ max_nonmaterial_stale_ms`를 checked uint64 subtraction으로 검증한다. clock 역행/overflow 또는 50ms 초과는 `SnapshotSuperseded`다.
- Commit 성공 직후 `dirty_flag`가 있으면 새 요청을 발급한다.

## 7.3 원자적 Commit 경계

원자 범위는 Server Game Thread의 `Validate + Reserve + StartCommit`이다. 수초간 수행되는 Tick/Complete는 트랜잭션 밖이다.

```text
Worker/Read-only
  BuildExecutionPlan

Server Game Thread, short transaction
  pending request hash 검증
  → decision ID와 request snapshot_revision 검증
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
- `SnapshotSuperseded`
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
- Suspended Goal phase timer는 §5.9의 `remaining_ms`와 Resume Policy를 저장하고, absolute Goal deadline은 저장 시점의 remaining duration과 authority revision으로 복구한다.
- Load 시 만료된 Belief/Event는 제거하고 Reservation은 재획득한다.
- Model/Calibration/Registry hot-swap은 새 Decision Contract Hash 활성화 전에 dry-run validation과 rollback asset을 요구한다.
- Pending inference는 supersede하고 새 계약으로 재요청한다.
- rollback 시 해당 버전의 Model, Calibration, Schema/Registry 생성 코드 세트를 함께 복구한다.

## 9.8 ML Training Contract 개요

규범 프로필 ID는 `policy_train_v1.0.0`이다. 학습 코드는 별도 Unreal 구현 저장소의 `ML/`에 두고, 이 저장소의 YAML과 `generated/python/ai_native_npc_contracts_generated.py`를 고정 커밋으로 가져와 사용한다.

학습 파이프라인은 다음 순서를 지킨다.

```text
Unreal Capture / Procedural Generator
→ immutable shard 작성
→ Dataset Contract Validation
→ family 단위 Split 확정 및 hash
→ Silver warm start
→ Gold + DAgger fine-tune
→ checkpoint 동결
→ OOD asset fit
→ Calibrator fit
→ ONNX export
→ PyTorch ↔ ONNX Runtime ↔ UE NNE parity
→ General/OOD/Critical/Performance Gate
→ Model Bundle 승격
```

Test, OOD, Critical split은 checkpoint와 Calibration asset이 동결되기 전 학습 코드에서 열 수 없다. Test 결과를 보고 architecture, seed, epoch, threshold를 고르면 새 실험으로 간주하고 Test split을 새 버전으로 교체한다.

## 9.9 Dataset Record v2

저장 형식은 Zstandard 압축 Parquet이며 Tensor는 Arrow fixed-size list로 저장한다. 하나의 row는 한 번의 Decision Snapshot이다. 대용량 runtime handle과 debug payload는 별도 replay shard에 저장하고 학습 shard에는 필요한 hash와 model input만 둔다. 기존 `anpc_decision_record_v1`은 아래 Switch Cost와 content identity를 재현하지 못하므로 V1 Neural release 학습 입력으로 승격하지 않는다.

필수 필드:

```text
record_version = "anpc_decision_record_v2"
sample_id: sha256
input_content_hash: sha256
label_block_hash: sha256
episode_id: string
decision_id: uint64
captured_at_server_time: float64

contract:
  schema_version / schema_sha256
  skill_registry_version / skill_registry_sha256
  goal_registry_version / goal_registry_sha256
  target_slotter_version / target_slotter_sha256
  normalization_version / normalization_sha256
  postprocess_version / postprocess_sha256
  feature_contract_hash
  source_decision_contract_hash: sha256 | null
  generator_or_runtime_build_sha256
  candidate_set_canonical_bytes
  candidate_set_hash

group:
  scenario_family_id
  map_family
  occlusion_layout_family
  goal_sequence_family
  role_id
  personality_cluster_id
  perception_modality_family
  target_composition_family
  event_sequence_family

inputs:
  global_state                float32 [128]
  target_features             float32 [17,48]
  target_kind_ids             int64   [17]
  target_mask                 bool    [17]
  event_features              float32 [12,24]
  event_type_ids              int64   [12]
  event_target_slots          int64   [12]
  event_mask                  bool    [12]
  candidate_pair_features     float32 [272,16]
  candidate_mask              bool    [272]

postprocess:
  switch_cost_terms           bool    [272,4]
  captured_switch_cost        float32 [272]

labels:
  acceptable_candidate_mask   272 bit
  preference_pairs            list<(preferred_index,rejected_index)>
  parameter_target_norm       float32 [272,4]
  parameter_label_mask        bool    [272,4]
  selected_is_acceptable      bool | null
  label_confidence            float32 [0,1]
  reason_tags                 list<string>

provenance:
  source_type                 silver | gold | dagger
  generator_template_version
  prompt_or_teacher_version
  annotator_set_hash
  annotator_agreement
  map_seed / simulation_seed
  parent_policy_sha256: sha256 | null
```

Hash 역할:

- `feature_contract_hash`는 §6.4의 `ANPCFEAT1` ordered-byte 공식으로 계산한다. Model과 Calibration asset hash를 포함하지 않는다.
- `source_decision_contract_hash`는 Capture를 만든 source policy의 전체 Decision Contract다. 절차 Silver처럼 source policy가 없으면 null이다.
- `input_content_hash`는 아래 canonical input object의 SHA-256이다. episode/decision ID와 label을 포함하지 않으므로 모든 split 간 동일 입력 중복 검출에 사용한다.
- `sample_id`는 immutable row identity이며 다음 ordered bytes로 계산한다.

```text
sample_id = SHA256(
    ASCII("ANPCSAMPLE2")
  || input_content_hash_raw32
  || episode_id_utf8_byte_length_uint32_le
  || NFC_episode_id_utf8_bytes
  || decision_id_uint64_le
  || label_block_hash_raw32
)
```

Episode ID가 uint32 byte length를 넘거나 valid NFC UTF-8이 아니면 validation 실패다.

Canonical input object는 RFC 8949 deterministic CBOR의 integer-key map이다. integer key 외의 alias를 허용하지 않는다.

```text
0: "anpc_decision_record_v2"                         text
1: feature_contract_hash                              bstr(32)
2: [10개 Tensor canonical bstr]                       array(10), Schema 입력 순서
3: candidate_set_canonical_bytes                      bstr
4: switch_cost_terms                                  bstr, [272,4] row-major 0/1
```

Tensor canonical byte 규칙:

- Dataset row에는 batch 축을 포함하지 않는다.
- 배열 순서는 C-contiguous row-major다.
- float32는 IEEE-754 little-endian이며 NaN, Infinity, negative zero를 금지한다.
- int64는 signed little-endian이다.
- bool은 element마다 `0x00` 또는 `0x01` 한 byte다.
- Arrow 내부 buffer representation을 직접 hash하지 않고 Validator가 위 canonical byte로 다시 encode한다.

Label block은 다음 integer-key deterministic CBOR map이다.

```text
0: acceptable_candidate_mask                         bstr(34), LSB-first
1: preference_pairs                                  array<[uint16,uint16]>
2: parameter_target_norm                             bstr, float32 LE [272,4]
3: parameter_label_mask                              bstr, 0/1 [272,4]
4: selected_is_acceptable                            null | false | true
5: label_confidence                                  bstr(4), float32 LE
6: reason_tags                                       array<text>
```

Label block 규칙:

- `preference_pairs`는 `(preferred_index,rejected_index)` 오름차순 sort 후 duplicate를 거부한다.
- `reason_tags`는 NFC-normalized UTF-8 byte 오름차순 sort 후 duplicate를 거부한다.
- float와 bool은 Tensor canonical byte 규칙을 따른다.
- `label_block_hash = SHA256(deterministic_cbor_label_map_bytes)`다.

추가 규칙:

- `candidate_set_canonical_bytes`는 Target Handle·Target Mask·Candidate Mask의 hash 입력을 보관하는 non-model metadata다. Dataset Validator는 여기서 `candidate_set_hash`를 다시 계산하되 이 byte를 모델에 전달하지 않는다.
- `switch_cost_terms[...,0..3]`은 각각 `skill_changed`, `target_changed`, `before_min_duration`, `releases_or_transfers_reservation`이다.
- Validator는 §6.2의 계수로 `switch_cost`를 재계산하고 `captured_switch_cost`와 FP32 exact 또는 명시된 Golden tolerance로 대조한다. Continue candidate의 네 component와 cost는 모두 0이어야 한다.
- `acceptable_candidate_mask`와 preference pair의 모든 index는 `candidate_mask=true`의 부분집합이어야 한다.
- valid acceptable candidate가 0개인 row는 `abstain-only`로 표시하고 Ranking Loss에서는 제외하되 Calibrator negative 사례로 유지한다.
- Parameter label은 acceptable candidate의 Registry active slot에만 존재할 수 있다.
- runtime handle, Actor 이름, absolute world position, future event, hidden ground truth를 model input에 넣지 않는다.
- Ground Truth는 평가·라벨링용 별도 channel에서만 join하며 Dataset Validator가 input column과의 중복·파생 누출을 검사한다.

각 shard는 `dataset_manifest.json`에 파일명, row 수, byte 크기, SHA-256, source/group별 분모, 생성 코드 커밋을 기록한다. Manifest에 없는 shard 또는 hash가 다른 shard는 학습에서 거부한다.

## 9.10 Split과 Dataset Validation

`scenario_family_id` 전체를 다음 여섯 split 중 하나에만 배치한다.

```text
train | validation | calibration | general_test | ood | critical
```

동일 episode, map seed, generator template의 근접 변형도 split을 넘지 못한다. `input_content_hash` exact duplicate와 `scenario_family_id` 교집합 검사는 여섯 split의 모든 pair 조합에 적용한다. 의도적 Critical mutation은 원본 `source_fixture_id`와 `mutation_id`를 case catalog에 기록할 수 있지만, Train/Validation/Calibration/General/OOD와 동일한 `input_content_hash`를 재사용할 수 없다.

In-distribution family는 사전에 검토한 `split_assignment.csv`로 Train 70%, Validation 10%, Calibration 10%, General Test 10%에 배치한다. `test_taxonomy_v1.yaml`은 OOD/Critical family 이름과 최소 분모를 소유한다. 실제 OOD 8 family와 Critical 8 family의 허용 사례는 후속 machine-readable `test_case_catalog_v1.yaml`에 다음을 명시해야 한다.

```text
case_id
scenario_family_id
fixture_id / fixture_version
source_fixture_id / mutation_id: optional, Critical mutation provenance
map_seed 또는 seed_set_hash
split = ood | critical
expected_invariants
owner
```

Taxonomy family name만으로 “명시적 allowlist”를 충족했다고 보지 않는다. `test_case_catalog_v1.yaml`이 생성·Lock·Validator 대상에 포함되기 전 OOD/Critical split을 열 수 없다. 비율보다 Appendix E의 Role×Goal 최소 분모와 family 격리가 우선한다.

Dataset Validator는 학습 전에 다음을 모두 검사한다.

1. Tensor 이름·dtype·shape·finite·valid range
2. padding, NoTarget slot 16, Event Target remap
3. Candidate layout `16×17`, mask, candidate hash 재계산
4. Switch Cost component/captured cost/postprocess hash 재계산
5. label index·parameter active mask·confidence 범위와 canonical list 규칙
6. `sample_id`, `input_content_hash`, `label_block_hash` 재계산
7. row identity 중복과 여섯 split 모든 pair의 `input_content_hash`·`scenario_family_id` 교집합 0
8. feature contract/schema/registry/generator hash 단일성; source decision hash는 provenance 분포로 별도 보고
9. hidden/future/absolute-world 정보의 input column 누출 0
10. group/source/label 분모와 결측률 보고
11. OOD/Critical case가 Taxonomy family와 case catalog allowlist에 모두 존재

하나라도 실패하면 학습을 시작하지 않는다. Split manifest나 case catalog가 바뀌면 Dataset version을 올리고 이전 결과와 직접 비교하지 않는다.

## 9.11 Loss Contract

학습에서도 Runtime과 같은 hard mask와 Switch Cost를 적용한다. `switch_cost_i`는 Dataset의 `captured_switch_cost`를 맹목적으로 신뢰하지 않고 `switch_cost_terms[i,0..3]`와 잠긴 `postprocess_version`에서 재계산한다.

```text
a_i = clamp(raw_score_i,-2.5,2.5) - switch_cost_i
P(AcceptableSet) = Σ(i∈A) exp(a_i) / Σ(j∈Valid) exp(a_j)
L_set = -log(max(P(AcceptableSet), 1e-8))
```

Preference pair `(p,n)`:

```text
L_pair = softplus(-(a_p-a_n)/0.5)
```

Parameter:

```text
L_param = SmoothL1(
  predicted_norm,
  target_norm,
  beta=0.05
)
```

`L_param`은 `parameter_label_mask=true`인 Registry active slot에만 적용한다. 최종 loss:

```text
L = sample_weight × (
      1.00 × L_set
    + 0.25 × mean(L_pair)
    + 0.10 × mean(L_param)
)
```

- `sample_weight = label_confidence × source_weight`
- source weight: Silver `0.25`, Gold `1.00`, DAgger `1.00`
- 해당 label이 없는 loss term은 0이며 다른 term의 분모에 포함하지 않는다.
- valid candidate가 없거나 acceptable label이 mask 밖이면 조용히 보정하지 않고 Dataset Validation 실패로 처리한다.
- Safety constraint 위반을 loss로 완화하지 않는다. Hard constraint는 Candidate Mask와 Commit 검증이 소유한다.

## 9.12 Training Config

고정 기본값:

| 항목 | Stage A — Silver warm start | Stage B — Gold/DAgger fine-tune |
|---|---:|---:|
| 입력 | Silver Train 75% + Gold Train 25% | Gold Train 75% + DAgger Train 25% |
| 최대 epoch | 40 | 60 |
| Optimizer | AdamW | AdamW |
| 시작 learning rate | `3e-4` | `1e-4` |
| 최소 learning rate | `3e-5` | `1e-5` |
| warm-up | 전체 update의 5% | 전체 update의 5% |
| schedule | cosine decay | cosine decay |
| effective batch | 256 states | 256 states |
| weight decay | `1e-4` | `1e-4` |
| betas / epsilon | `0.9, 0.999 / 1e-8` | 동일 |
| global grad clip | `1.0` | `1.0` |
| early-stop patience | 8 epoch | 10 epoch |

추가 고정:

- release seed는 `1729` 하나를 사용하고 Python, NumPy, PyTorch, DataLoader worker에 모두 전파한다.
- Role×Goal group은 epoch 안에서 균등 sampler를 사용한다. source 비율은 위 표를 따른다.
- mixed precision, TF32, quantized training은 V1 FP32 Reference에서 끈다.
- PyTorch deterministic algorithms를 켜고 non-deterministic operator 발견 시 실패한다.
- Stage B는 Stage A best checkpoint에서 시작하며 모든 Layer를 학습한다.
- Validation은 매 epoch 수행하며 Test/OOD/Critical split은 loader 등록 자체를 금지한다.
- 정확한 Python/PyTorch/ONNX/ORT/CUDA 버전, OS image digest, GPU/CPU model, driver, code commit은 `train_environment.lock.json`에 고정한다.

서로 다른 hardware/library에서 weight byte가 같다는 보장은 하지 않는다. 동일 release model을 다시 만들 때는 잠긴 환경을 사용한다. 환경이 달라 model hash가 바뀌면 새 Model Bundle로 취급하고 전체 Gate를 다시 실행한다.

## 9.13 Checkpoint 선택과 Training Report

Stage별 best checkpoint는 Validation의 다음 정렬 Key로 자동 선택한다.

```text
1. macro Role×Goal Any-Acceptable Top-1, post-switch-cost — 큰 값
2. worst Role×Goal Any-Acceptable Top-1 — 큰 값
3. annotated active parameter MAE — 작은 값
4. epoch — 작은 값
```

Top-1은 raw score가 아니라 Runtime과 동일한 Adjusted Score 선택 결과로 계산한다. 보고서에는 micro/macro/worst-group, source별, Target Kind별, valid candidate count bucket별 결과와 abstain-only 분모를 모두 기록한다.

Checkpoint 파일은 weights만 담는 `model.safetensors`, architecture/config JSON, optimizer state, epoch, RNG state, Dataset/Code/Environment hash로 구성한다. Release Export는 best weights와 architecture/config만 사용하며 optimizer state는 배포하지 않는다.

## 9.14 Calibration과 OOD Asset

Checkpoint를 동결한 뒤 순서대로 수행한다.

### OOD

- in-distribution Gold Train의 유효 ONNX output `tactical_context h[128]`만 사용한다.
- `LedoitWolf(assume_centered=false)`로 mean과 shrinkage covariance를 구하고 precision matrix를 저장한다.
- §6.3의 squared Mahalanobis `d2`에 대한 empirical `q95_train`, `q99_9_train`을 저장한다.
- `q99_9_train - q95_train < 1e-6`이면 asset fit 실패다.
- Runtime OOD 공식은 §6.3을 그대로 사용한다.
- OOD 승격 KPI는 ROC상의 임의 operating point가 아니라 Runtime threshold `OOD=0.80`에서 계산한다.

### Calibrator

- Gold Calibration split만 사용한다.
- Runtime post-process가 선택한 candidate가 acceptable set 안에 있는지를 binary label로 사용한다.
- valid candidate가 1개면 second score는 selected score와 같게 두고 gap과 normalized entropy는 0으로 둔다. valid candidate가 0개면 Calibrator를 호출하지 않고 즉시 fallback한다.
- 22개 입력 중 연속형 6개는 Calibration split mean/std로 표준화하고 std는 최소 `1e-6`으로 clamp한다. one-hot 16개는 그대로 둔다.
- Logistic Regression: L2, `C=1.0`, solver `lbfgs`, `max_iter=2000`, `tol=1e-8`, class weight 없음.
- threshold 후보는 `0.75, 0.76, …, 0.95`다.
- coverage 분모는 contract-valid이고 `valid_candidate_count>0`인 Calibration state 전체다. `OOD≥0.80` 선행 abstain도 미수락으로 분모에 포함한다.
- 전체 global threshold는 `accepted_count ≥400`, `coverage ≥0.80`, one-sided Wilson 95% risk upper bound `≤0.10`을 모두 만족하는 가장 낮은 threshold다.
- Role×Goal override는 해당 group의 Calibration source state가 400개 이상이고, 후보 threshold에서 `accepted_count ≥100`, `coverage ≥0.80`, one-sided Wilson 95% risk upper bound `≤0.10`일 때만 만든다.
- group override 승격 조건을 만족하지 못하면 global threshold를 적용하지만, 실제 적용 threshold에서도 각 필수 Role×Goal group은 `accepted_count ≥100`, `coverage ≥0.80`, one-sided Wilson 95% risk upper bound `≤0.10`을 별도로 만족해야 한다.
- global threshold 또는 실제 적용 threshold의 필수 group Gate 하나라도 실패하면 Release Gate를 실패시킨다. 0-coverage/0-accepted group을 fallback 성공으로 간주하지 않는다.
- accepted count가 0이면 risk를 0으로 두지 않고 해당 threshold를 부적격 처리한다.

여기서 risk는 threshold 이상으로 accept된 상태 중 선택 candidate가 acceptable set 밖인 비율이다. Capture 당시 source policy의 `selected_is_acceptable` 값은 분석용이며, 최종 Calibrator label은 frozen checkpoint로 다시 선택한 결과와 `acceptable_candidate_mask`에서 재계산한다.

Calibration/OOD asset은 scaler, weights, bias, group thresholds, mean, precision, q95/q99.9, fit dataset hash, checkpoint hash, library version을 포함한다. General Test와 OOD Test는 asset 동결 후 ECE, Brier, risk/coverage, OOD recall/FPR만 평가한다.

## 9.15 Export와 Model Bundle

ONNX 입력 이름·순서·dtype은 Schema 2.0의 다음 10개와 exact-match해야 한다.

```text
global_state                float32 [B,128]
target_features             float32 [B,17,48]
target_kind_ids             int64   [B,17]
target_mask                 bool    [B,17]
event_features              float32 [B,12,24]
event_type_ids              int64   [B,12]
event_target_slots          int64   [B,12]
event_mask                  bool    [B,12]
candidate_pair_features     float32 [B,272,16]
candidate_mask              bool    [B,272]
```

목표 output은 `candidate_raw_scores [B,272]`, `candidate_parameter_proposals [B,272,4]`, `tactical_context [B,128]` 세 개다. Batch 축만 dynamic이며 나머지 축은 고정한다. 현 RC5 Schema는 두 output만 등록되어 있으므로 세 번째 output을 포함한 Schema patch 이전 model은 OOD Runtime 승격 대상이 아니다.

Export 계약:

- `model.eval()`, FP32, ONNX opset 17
- constant folding 사용
- ONNX checker와 shape inference 통과
- batch `B=1,2,4,8`에서 세 output 모두 PyTorch↔ONNX Runtime tolerance `abs≤1e-4`, `rel≤1e-4`
- NaN/Inf 0
- 사용하는 ONNX operator allowlist를 manifest에 기록하고 UE target runtime의 model creation smoke test 통과

Model Bundle:

```text
policy.onnx
policy_manifest.json
calibration_ood_asset.json
golden_inputs.npz
golden_outputs_fp32.npz
model.safetensors
model_config.json
train_config.json
dataset_manifest.json
split_assignment.csv
train_environment.lock.json
train_report.json
evaluation_report.json
perf_manifest.json
```

`policy_manifest.json.files`에는 `policy_manifest.json` 자신을 제외한 Bundle 파일의 이름, byte 크기, SHA-256을 기록한다. Manifest가 자기 자신의 hash를 포함하도록 요구하지 않는다.

- `model_sha256 = SHA256(policy.onnx raw bytes)`로 고정한다.
- `checkpoint_sha256 = SHA256(model.safetensors raw bytes)`는 학습 provenance이며 Runtime `model_sha256`과 구분한다.
- Model, Schema, Registry, Normalization, Slotter, Post-process, Calibration/OOD hash로 `decision_contract_hash`를 계산한다.
- `policy_manifest.json` 자체는 외부 release index 또는 Freeze Manifest가 기록한 `policy_manifest_sha256`으로 검증한다.
- 파일 하나라도 바뀌면 기존 Decision Contract Hash와 Bundle 승인 hash를 재사용하지 않는다.

## 9.16 구현 저장소 명령과 Phase 구분

별도 구현 저장소의 CLI는 다음 단일 흐름을 제공한다.

```bash
python -m anpc_ml.dataset.validate --manifest <dataset_manifest.json>
python -m anpc_ml.train --config <train_config.json>
python -m anpc_ml.fit_calibration --checkpoint <best_checkpoint>
python -m anpc_ml.export_onnx --checkpoint <best_checkpoint>
python -m anpc_ml.parity --bundle <model_bundle_dir>
python -m anpc_ml.evaluate --bundle <model_bundle_dir>
```

Phase 0에서는 작은 deterministic fixture dataset으로 위 명령과 ONNX→Unreal 경로를 끝까지 검증한다. Fixture model은 품질 승격 대상이 아니며 Utility Baseline보다 우수하다고 주장하지 않는다. V1은 Appendix E 최소 데이터와 모든 품질·안전·성능 Gate를 충족한 별도 Model Bundle이다.

# 10. Schema Generator와 Parity

## 10.1 Single Source와 실행 산출물

Runtime/학습 Tensor의 단일 원본은 다음 세 YAML이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

평가 family·Critical/OOD 분모는 네 번째 YAML인 `contracts/current/test_taxonomy_v1.yaml`이 소유한다. 실제 OOD/Critical fixture allowlist는 후속 `contracts/current/test_case_catalog_v1.yaml`이 소유하며, 추가 즉시 Generator·Catalog·Lock·Archive·Validator 대상에 포함한다.

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

정리된 `main`에서는 YAML 4개와 생성 Python/C++ 계약만 유지한다. Generator·Golden·Harness는 `archive/full-harness-v0.4.6`에 보존되어 있다. 계약 변경이 필요하면 보관본의 Generator로 전체 산출물과 증거를 재생성한 뒤 새 버전으로 승격해야 하며, `main`의 생성 파일만 손으로 고쳐서는 안 된다.

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

## 10.6 RC5 구조화 계약 Remediation Backlog

다음은 Requirements 문장만 고쳐 완료할 수 없으며 보관 Generator를 사용한 patch release가 필요하다.

| ID | 현재 RC5 상태 | 목표 변경 | Freeze 집행 |
|---|---|---|---|
| `SCHEMA-OUTPUT-001` | output 2개 | `tactical_context float32 [B,128]` 추가 | Schema semantic validation + PyTorch/ORT/NNE 3-output parity |
| `GOAL-TRIGGER-001` | `Timeout` 문자열 allowlist, duration 없음 | typed Event/Timer/Lifecycle/ServerControl trigger와 phase duration | Goal Registry validator + generated FSM runtime test |
| `GOAL-REVISION-001` | Registry revision 목록 누락 | interruptibility/resume policy change 추가 | generated Registry parity |
| `IDENTITY-EQUALITY-001` | Pair Feature source가 `handle equality`/`typed handle equals`로 모호 | `same_as_current_target`와 `same_as_current_skill_target`에 `comparison_key: identity_key` 구조화 | generated helper + Revision-only mutation Golden |
| `ASYNC-STALE-001` | continuous float drift allowlist와 age bound가 구조화되지 않음 | `staleness_class`와 `max_nonmaterial_stale_ms=50`을 Decision Runtime Contract에 추가 | stale boundary Runtime/Golden test |
| `EVENT-MOVING-001` | `source_moving_probability`가 bool | 확률이면 ratio `[0,1]`; boolean 의미를 유지하려면 `source_is_moving`으로 rename | Schema migration + Float Feature parity |
| `DOC-GENERATOR-001` | generated Appendix `D.3` 중복 | Candidate Hash D.3, Decision Hash D.4, Normalizer D.5 | generated docs parity |
| `TEST-CATALOG-001` | family taxonomy만 존재 | 실제 case allowlist YAML 추가 | Catalog/Lock/Archive validation |

Auto-generated marker 내부를 수동 편집해 위 문제를 숨기지 않는다. 구조화된 원본과 Generator를 먼저 고치고 Appendix·Python·C++·Golden·Manifest를 함께 재생성한다.

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
| Goal Manager/FSM | Gameplay AI + Designer | 2주 | 3주 | Goal Registry Appendix D.2 + typed trigger patch |
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

- Generator: `0.4.6`
- Contract revision: `2.0.0-rc5`
- Schema SHA-256: `424898ba9e80ff8ac7ad4d48a806f8606d2c595ec892d2753becbdaa3e47b6cc`
- Skill Registry SHA-256: `08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8`
- Goal Registry SHA-256: `b6ed883e39f8da4f792b2ad4542b4cf7045ff5fe00147a9eba15eac61fa67ac2`
- Test Taxonomy SHA-256: `7e300d01d148129e0741f8e0c468eeb433d80fe9ef414c7be453c47960927155`

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
| `schema_contract_revision` | `2.0.0-rc5` |
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

<!-- BEGIN AUTO-GENERATED TEST TAXONOMY KPI: REQUIREMENTS -->

## E.1 고정 평가 버전

- Utility Baseline: `utility_baseline_v1.0.0`
- Schema: `2.0.0`
- Target Slotter: `1.0.0`
- Post-process: `1.0.0`
- Critical Suite: `critical_suite_v1`, **512 sequences = 8 family × 64 case**

### E.1.1 Critical Family

1. `perception_belief_visibility`
2. `typed_target_slotting`
3. `goal_arbitration_transition`
4. `candidate_mask_and_hash`
5. `async_latest_only_and_atomic_commit`
6. `hidden_information_boundary`
7. `skill_parameter_and_resource_cas`
8. `save_load_hot_swap_recovery`

### E.1.2 OOD Family

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
| Critical Target/Candidate Recall | Critical Suite 512 sequences | 100%, 분모와 miss 모두 보고 |
| MandatoryOverflow | Critical + General | 0건 |

## E.3 Safety

절대 Gate:

- Critical Suite 512 sequences에서 hard-constraint 위반 Commit 0건
- Randomized Safety Fuzz 100,000 decision에서 hard-constraint 위반 Commit 0건
- Hidden Information Leakage Test 10,000 pair에서 Tensor/행동 누출 0건
- Server authority 우회 0건

Safety는 Baseline 비열등만으로 대체할 수 없다.

<!-- END AUTO-GENERATED TEST TAXONOMY KPI: REQUIREMENTS -->

### E.3.1 Remediation 해석

- E.2의 Target Recall과 Any-Acceptable Candidate Recall은 각각 §3.8과 §4.6의 numerator/denominator를 사용한다.
- Critical `100%`는 512 sequence aggregate에서 miss 0건을 뜻하며 sequence·decision·target/candidate 분모를 모두 보고한다.
- 현재 V1 Mandatory source cap 합은 9이고 Schema semantic validation이 cap 합 16 초과를 거부하므로 `MandatoryOverflow 0건`은 품질 우수성 KPI가 아니다. Runtime 방어 invariant와 malformed-cap negative mutation test로만 유지한다.
- Auto-generated E.2 표는 다음 Test Taxonomy patch에서 이 해석을 구조화된 metric contract로 흡수해야 한다.

## E.4 Calibration/OOD

| Metric | Gate |
|---|---|
| ECE | ≤0.05 |
| Brier Score | ≤0.18 |
| Global risk/coverage | accepted ≥400, coverage ≥80%, one-sided Wilson 95% risk upper bound ≤0.10 |
| Role×Goal actual threshold | 각 필수 group accepted ≥100, coverage ≥80%, one-sided Wilson 95% risk upper bound ≤0.10; global fallback에도 동일 적용 |
| OOD Runtime operating point | threshold `0.80`에서 recall ≥0.90, FPR ≤0.10 |
| 각 Role×Goal Calibration group | 최소 400 Gold states; 0 accepted/coverage는 Release 실패 |

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
| Critical Suite | `test_taxonomy_v1.yaml`에서 파생 | Appendix E.1–E.3의 자동 생성 계약 참조 |

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

- 비율: 지정된 trial 단위의 Wilson 95% CI
- Target/Candidate Recall: point/Wilson과 episode-cluster bootstrap 10,000회 CI 동시 보고
- paired A/B: scenario-cluster bootstrap 10,000회
- Goal completion/oscillation 차이: Role×Goal stratified bootstrap 10,000회
- latency percentile: request bootstrap 10,000회 및 raw percentile 동시 보고
- worst-group는 평균으로 상쇄하지 않고 별도 Gate로 보고

---

# 12. 최종 승인 체크리스트

Schema 2.0 Freeze 승인에는 다음이 모두 필요하다.

- [ ] `ai_native_npc_schema_v2_0.yaml`에서 C++/Python/문서 생성
- [ ] `tactical_context [B,128]` output이 Schema·ONNX·ORT·NNE descriptor에 존재하고 3-output parity 통과
- [ ] Enum·Mask·Padding·Hash Golden Vector byte-identical
- [ ] Float Feature parity tolerance 통과
- [ ] `source_moving_probability` 의미·dtype remediation과 migration 완료
- [ ] Pair Feature same-target comparison이 Schema의 `identity_key`로 구조화되고 Revision-only Golden 통과
- [ ] 17 Target Slot과 272 Candidate layout parity
- [ ] Typed Target Runtime Payload 구현
- [ ] Target Slotter Target Recall Gate 통과
- [ ] Goal Registry typed trigger·phase duration·revision contract 생성/검증
- [ ] Goal Arbitration/FSM Phase 0 테스트와 UE generated Phase 표 parity 통과
- [ ] Dataset Record v2의 Switch Cost·feature/content/sample hash Validator 통과
- [ ] OOD/Critical `test_case_catalog_v1.yaml` allowlist와 split 격리 통과
- [ ] Adjusted Score→OOD→Calibration 순서와 Runtime threshold 0.80 parity
- [ ] Calibration global/group accepted count·coverage·one-sided risk CI Gate 통과
- [ ] Model Bundle manifest self-exclusion과 `model_sha256=SHA256(policy.onnx)` 검증
- [ ] `snapshot_revision` stale response와 `SnapshotSuperseded` Runtime 테스트 통과
- [ ] Atomic Commit rollback·lease·urgent cancellation 테스트 통과
- [ ] Hidden Information Leakage Test 통과
- [ ] Appendix E의 실제 Baseline/CI/표본 Gate 통과
- [ ] 보관 validation report의 pending Runtime/Formal Gate가 실제 evidence로 모두 종료

이 문서와 현재 RC5 YAML이 상충하는 output·Registry 항목은 §0.1과 §10.6에 기록된 의도된 remediation 대상이다. 해당 항목은 YAML의 현재 field index·enum·shape를 Runtime active contract로 우선하되 **최종 Freeze와 OOD Runtime 승격은 금지**한다. 구조화된 원본과 Generator를 고쳐 새 patch version의 YAML·generated artifacts·Golden·Decision Contract Hash를 함께 발급한 뒤에만 본문의 목표 계약이 active가 된다.
