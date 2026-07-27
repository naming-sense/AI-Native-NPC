# AI Native NPC — Unreal Engine 5.7 / Manny·Quinn 공간·시야·소리 통합 구현 계획서
## UE 클라이언트·신경망·Goal·Typed Target·Schema 2.0 통합 기준

- 문서 버전: **v0.4**
- 문서 상태: **UE 5.7 Client Implementation Profile / Schema 2.0 Freeze Candidate**
- 개정일: 2026-07-26
- 대체 문서: 기존 `ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan.md` v0.3
- 상위 기준서: `ai_native_npc_requirements_implementation_plan_v0.4.md`
- Tensor 단일 원본: `ai_native_npc_schema_v2_0.yaml`
- 상위 기준서 SHA-256: `f1d11ca1ae85d9b2181830c76ac09f265038cc17d684b24b5cbb00455a403e14`
- Schema YAML SHA-256: `eae78842b23d7fcceb391b147e35714bd6883c03a737ffdd9c46c95032c9f515`
- Phase 0 판정: **GO**
- Schema 2.0 최종 Freeze: **생성 코드와 Unreal–Python Golden Test 통과 후 승인**

> 이 문서는 Unreal Engine 5.7 Third Person 프로젝트에서 Quinn을 플레이어로 유지하고, Manny를 학습 기반 NPC로 적용하기 위한 엔진 구현 기준서다.  
> Tensor·Enum·Padding·Normalization·Hash가 충돌하면 본문보다 `ai_native_npc_schema_v2_0.yaml`이 우선하고, Goal·Target·Commit 책임이 충돌하면 상위 v0.4 요구사항이 우선한다.

---

# 0. 최신 리뷰 반영 판정

최신 리뷰의 지적은 모두 타당하다. 기존 UE 문서에는 다음 구현 블로커가 남아 있었다.

1. `Actor/Entity` 중심 Target 모델로 인해 SoundEvent, LastKnownPosition, CoverSlot, SmartObject, Waypoint, WorldPosition을 일관되게 처리하지 못함
2. Target을 8개 또는 16개로 줄이는 과정이 명시되지 않아 숨은 Behavior Tree가 될 위험
3. 장기 Goal 상태는 언급됐지만 arbitration, preemption, suspend/resume, revision 계약이 없음
4. 32개 Candidate, GRU Hidden State, 단순 score gap confidence가 최신 기준과 충돌
5. 비동기 응답의 stale 검증과 Skill 시작의 원자적 Commit 경계가 불완전
6. Sight Lost 이후에도 Actor Identity를 그대로 Target으로 유지해 숨은 위치가 실행 단계에서 누출될 가능성
7. Unreal과 Python이 동일 Tensor/Hash를 만들 수 있는 고정 Schema가 없음
8. Phase 0과 V1 범위, KPI, Owner, 성능 분모가 혼재

v0.4 UE 구현판은 다음을 고정한다.

- 일반 Target 16개 + 고정 `NoTarget` 1개 = 총 17 Target Slot
- 16 Skill × 17 Slot = 272 Candidate
- Runtime `FTargetHandle`과 모델 입력 `FTargetFeatures` 완전 분리
- V1은 GRU 없이 최근 12개 명시적 Event Buffer 사용
- Goal Manager가 장기 상태를 소유하고 Neural Policy는 현재 Goal 안의 전술 Candidate만 평가
- Candidate raw score와 confidence를 분리하고 OOD·Calibration·Abstain 적용
- NPC당 Commit 가능한 Decision은 최대 1개이며 urgent 요청은 기존 요청을 supersede
- 원자적 범위는 Server Game Thread의 `Validate + Reserve + StartCommit`
- Sight Lost 시 `Entity` Target을 끊고 immutable `LastKnownPosition` Target 생성
- Schema YAML에서 C++·Python·문서·Golden Vector를 생성

---

# 1. 핵심 결론과 전체 실행 구조

## 1.1 책임 경계

| 계층 | Unreal 구현 책임 |
|---|---|
| Authoritative World | 실제 Actor 상태, 물리, 피해, 퀘스트, 서버 권위 |
| AI Perception | Sight/Hearing/Damage 원시 Stimulus |
| Belief Runtime | NPC가 아는 위치·상태, source, observed time, confidence, TTL |
| Goal Manager | Goal 생성, arbitration, phase transition, suspend/resume, revision |
| Typed Target Universe | Entity·Sound·Position·Resource를 공통 Handle/Snapshot으로 변환 |
| Target Slotter | Target Universe에서 일반 Target 16개를 결정론적으로 선정 |
| Candidate Builder | 272개 고정 Candidate와 hard mask 생성 |
| Feature Builder | Schema 2.0 순서와 정규화로 Tensor 생성 |
| Neural Policy | Candidate raw score와 제한된 parameter proposal 출력 |
| Utility Baseline | 동일 Target/Candidate/Mask를 사용하는 비교 및 fallback 정책 |
| Post-process | switch cost, adjusted score, OOD, calibration, abstain |
| Commit Coordinator | stale 검증, 자원 예약, Skill 시작의 짧은 원자 Commit |
| Skill Executor | Tick, Complete, Fail, Cancel, 물리·애니메이션 실행 |

## 1.2 런타임 흐름

```text
Quinn 위치·움직임·발소리
        │
        ▼
Manny AI Sight / Hearing / Damage
        │
        ▼
Belief Runtime
- 현재 보이는 Entity
- immutable SoundEvent
- Sight Lost 시 LastKnownPosition
- source / age / confidence / TTL
        │
        ▼
Goal Manager
- Active Goal 1개
- phase / deadline / target
- preemption / suspended stack
        │
        ▼
Typed Target Universe
        │
        ▼
Target Slotter
- 일반 Target 16
- NoTarget slot 16
        │
        ▼
Candidate Builder
- 16 Skills × 17 Slots
- 272 fixed rows
- hard mask only
        │
        ▼
Schema 2.0 Feature Builder
        │
        ├──────────────► Utility Baseline
        ▼
NNE Neural Policy
        │
        ▼
Raw → Adjusted → OOD → Calibration → Accept/Abstain
        │
        ▼
Validate + Reserve + StartCommit
        │
        ▼
Manny Skill / Movement / Animation / Dialogue
```

## 1.3 V1에서 사용하지 않는 것

- GRU hidden state
- 모델의 authoritative 감정·관계 Delta
- 모델의 퀘스트·Goal 변경
- 모델의 직접 NavMesh 경로 생성
- Actor Stable ID를 신경망 Feature로 전달
- 보이지 않는 Quinn의 현재 Transform을 Target 위치로 갱신

---

# 2. 구현 범위

## 2.1 Phase 0 — MVP Vertical Slice

Phase 0은 실제 착수 가능한 최소 범위다.

| 항목 | 범위 |
|---|---|
| NPC Profile | Guard 1개 |
| Goal | `IdleObserve`, `InvestigateDisturbance` |
| 실행 Skill | `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea` |
| Control Candidate | `ContinueCurrentAction` |
| Target Kind | `Entity`, `SoundEvent`, `LastKnownPosition`, `Waypoint`, `NoTarget` |
| 기억 | 최근 Event 12개 |
| 정책 | Utility Baseline + 단순 Neural Scorer |
| 권위 | Single-player에서도 서버 권위 형태의 GameThread Commit |
| Schema | 17 Target Slot, 272 Candidate layout 그대로 사용 |

Phase 0에서 16개 Skill 전체를 구현하지 않더라도 Registry ID와 272개 Tensor layout은 고정한다. 미구현 Skill row는 hard mask한다. 이렇게 해야 Phase 1에서 Tensor shape를 바꾸지 않는다.

## 2.2 Phase 0 필수 수직 슬라이스

### A. 소리 없는 정면 접근

```text
Quinn이 Manny 정면 시야에 조용히 진입
→ SightCurrent Entity 생성
→ 상대 위치·거리·접근 속도 Feature
→ TurnTo 또는 Continue 후보 평가
→ Manny가 Quinn을 인식
```

### B. 뒤쪽 발소리에서 시야 획득

```text
Quinn이 Manny 뒤에서 발소리 발생
→ immutable SoundEvent Target 생성
→ TurnTo(SoundEvent)
→ Manny 회전
→ Sight가 Quinn Entity를 획득
→ SoundEvent와 Entity를 별도 Target으로 관리
```

### C. 시야 상실과 마지막 목격 위치

```text
Manny가 Quinn을 봄
→ Quinn이 벽 뒤로 이동
→ Entity Target 제거
→ immutable LastKnownPosition 생성
→ Investigate/Approach/SearchArea 후보
→ 숨은 Quinn의 현재 좌표는 사용하지 않음
```

### D. Goal 시퀀스

```text
IdleObserve
→ SoundHeard
→ InvestigateDisturbance 생성 및 arbitration
→ Orient
→ Navigate
→ Search
→ Return
→ IdleObserve resume
```

### E. 긴급 이벤트

```text
일반 Decision inference 중 Manny 피격
→ urgent flag
→ 기존 request cancellation/supersede
→ 새 decision ID
→ 취소된 응답은 Commit 불가
```

## 2.3 Phase 1 — V1

- Role 3개
- Goal 4개 이상
- Skill 16개
- Target Kind 8개
- Calibration/OOD/Abstain
- CoverSlot/SmartObject reservation
- 멀티플레이 서버 권위
- DAgger
- 정식 KPI Gate
- 30~50 NPC 부하 검증

## 2.4 비목표

- 카메라 RGB를 입력으로 하는 Computer Vision
- 신경망이 애니메이션 pose 또는 이동 벡터를 직접 생성
- 완전한 전투 시스템을 Third Person `None` 템플릿에 새로 구현
- LLM이 공격·아이템·퀘스트·관계를 직접 변경
- 신규 Skill의 zero-shot 품질 보장

---

# 3. 저장소와 단일 계약 관리

```text
/AINativeNPC
  /Contracts
    ai_native_npc_schema_v2_0.yaml
    skill_registry_v1.yaml
    goal_registry_v1.yaml
    calibration_manifest.json
    perf_manifest.json

  /Generated
    /Cpp
      AINPCSchema.generated.h
      AINPCEnums.generated.h
      AINPCNormalization.generated.h
      AINPCHash.generated.h
    /Python
      schema_generated.py
      enums_generated.py
      normalization_generated.py
    /Docs
      schema_2_0_generated.md
    /Golden
      discrete_vectors.json
      float_vectors.npz
      model_vectors.npz

  /ML
    /src
      dataset/
      feature_builder/
      target_slotter_reference/
      models/
      calibration/
      export/
      evaluation/
    /tests

  /Unreal
    /AINativeNPCDemo
      /Source
        /AINativeNPCContracts
        /AINativeNPCRuntime
        /AINativeNPCEditor
        /AINativeNPCTests
      /Content
        /AINativeNPC
        /Characters
        /Maps

  /Docs
    ai_native_npc_requirements_implementation_plan_v0.4.md
    ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.md
```

## 3.1 계약 우선순위

1. `ai_native_npc_schema_v2_0.yaml`: Tensor, enum, padding, normalization, hash
2. 상위 v0.4 요구사항: Goal, Target, Candidate, Commit, KPI
3. 본 UE 문서: Unreal 클래스와 실행 방식
4. Data Asset: 튜닝 가능한 센서·Skill 파라미터

## 3.2 Code Generation

```text
schema.yaml
→ validate_schema.py
→ C++ header
→ Python constants
→ generated Markdown
→ Golden Vector
```

수동으로 다음 값을 중복 작성하지 않는다.

- Feature index
- Tensor shape
- Enum ID
- Candidate count
- NoTarget slot
- normalization constant
- hash byte layout

## 3.3 CI Gate

- YAML schema validation
- Generated file clean check
- C++ compile-time static assert
- Python shape test
- discrete/hash byte-identical test
- float feature tolerance test
- ONNX/NNE output tolerance test

---

# 4. Unreal Engine 5.7 프로젝트 구성

## 4.1 프로젝트 생성

1. Unreal Engine 5.7 실행
2. `Games` → `Third Person`
3. C++ 프로젝트
4. Variant `None`
5. 프로젝트명 `AINativeNPCDemo`
6. 첫 Editor/Development/Shipping 빌드 확인

Quinn을 플레이어로 유지하고 Manny를 별도 NPC로 구성한다.

## 4.2 플러그인

프로젝트 설치본에서 실제 플러그인 이름과 Runtime 지원을 확인한 뒤 활성화한다.

- NNE
- 사용할 NNE Runtime backend
- Gameplay Tags
- StateTree 및 Gameplay StateTree — 복합 Skill에만 선택
- Smart Objects — Phase 1에서 선택

`.uproject` 예시:

```json
{
  "Plugins": [
    { "Name": "NNE", "Enabled": true },
    { "Name": "NNERuntimeORT", "Enabled": true },
    { "Name": "StateTree", "Enabled": true },
    { "Name": "GameplayStateTree", "Enabled": true }
  ]
}
```

NNE runtime과 header 경로는 UE 5.7 설치본 및 CI에서 검증한다. 문서에 특정 backend API를 직접 확정하지 않고 `INPCInferenceBackend` 어댑터 뒤로 격리한다.

## 4.3 Runtime Module 의존성

```csharp
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core",
    "CoreUObject",
    "Engine",
    "AIModule",
    "GameplayTasks",
    "NavigationSystem",
    "GameplayTags",
    "NNE",
    "DeveloperSettings",
    "NetCore"
});

PrivateDependencyModuleNames.AddRange(new string[]
{
    "Json",
    "JsonUtilities"
});

// 선택
// "StateTreeModule"
// "GameplayStateTreeModule"
// "SmartObjectsModule"
```

## 4.4 테스트 레벨

`L_AINativeNPC_MVP`

필수 배치:

- Player Start
- Manny NPC 1~3명
- NavMeshBoundsVolume
- 시야 차폐용 벽과 기둥
- 발소리 표면 2종
- Guard home Waypoint
- 제한 구역 Trigger
- 디버그 HUD
- Ground Truth와 Belief를 비교하는 Debug Actor

---

# 5. Manny NPC와 Quinn Player

## 5.1 Quinn Player

기존 `BP_ThirdPersonCharacter`를 유지한다.

추가 Component:

- `UAIPerceptionStimuliSourceComponent`
- `UPlayerNoiseEmitterComponent`
- 선택: `UNPCObservableStateComponent`

Quinn의 정확한 상태를 모델에 직접 전달하지 않는다. `UNPCObservableStateComponent`는 NPC가 현재 관측할 수 있는 외형·자세·무기 표현을 Belief Builder가 읽기 위한 인터페이스다.

```cpp
UINTERFACE(BlueprintType)
class UNPCObservableActor : public UInterface
{
    GENERATED_BODY()
};

class INPCObservableActor
{
    GENERATED_BODY()

public:
    virtual FGameplayTagContainer GetObservableTags() const = 0;
    virtual float GetVisibleWeaponConfidence(
        const FVector& ObserverLocation) const = 0;
};
```

## 5.2 Manny NPC

```text
BP_AINativeNPC_Manny
Parent: AAINativeNPCCharacter
Skeletal Mesh: SKM_Manny
Anim Class: ABP_Manny
AI Controller: AAINativeNPCController
Auto Possess AI: Placed in World or Spawned
NPC Profile: DA_NPCProfile_Guard_Cautious
Policy: DA_NPCPolicy_Schema2
Goal Profile: DA_NPCGoalProfile_Guard
Sensor Config: DA_NPCSensor_Guard
```

권장 이동 설정:

- `Use Controller Rotation Yaw`: false
- `Orient Rotation to Movement`: true
- TurnTo/LookAt Skill 동안 rotation mode override
- locomotion은 기존 `ABP_Manny` 재사용

## 5.3 서버 권위 형태

Single-player Phase 0에서도 다음 코드는 권위 실행 경로 하나만 사용한다.

```text
Perception/Goal/Decision/Commit: Authority
Animation/UI: Local presentation
```

Phase 1 멀티플레이로 전환할 때 정책 소유권을 다시 옮기지 않도록 처음부터 `HasAuthority()` 경계를 둔다.

---

# 6. Unreal 모듈과 핵심 클래스

## 6.1 모듈

| Module | 책임 |
|---|---|
| `AINativeNPCContracts` | 생성된 Enum, Tensor shape, hash, POD snapshot |
| `AINativeNPCRuntime` | Perception, Belief, Goal, Slotter, NNE, Commit, Skill |
| `AINativeNPCEditor` | Inspector, Replay, Labeling, Schema 검사 |
| `AINativeNPCTests` | Automation, Golden, Scenario, Performance |

## 6.2 런타임 클래스

| 클래스 | 책임 |
|---|---|
| `AAINativeNPCCharacter` | Manny Pawn과 Component 소유 |
| `AAINativeNPCController` | AI Perception, Navigation, Possession |
| `UNPCBeliefComponent` | 현재 지각·추정 상태와 Typed Target 원본 |
| `UNPCSocialStateComponent` | 사건 기반 감정·관계 권위 상태; Policy에는 read-only |
| `UNPCEventBufferComponent` | 최근 12개 명시적 Event |
| `UNPCGoalManagerComponent` | Goal arbitration, FSM, revision |
| `UNPCTargetUniverseComponent` | Entity·Event·Resource·Goal Target 통합 |
| `UNPCTargetSlotterComponent` | 16 regular + NoTarget slot 결정 |
| `UNPCCandidateBuilderComponent` | 272 Candidate와 hard mask |
| `UNPCFeatureBuilderComponent` | Schema 2.0 Tensor 생성 |
| `UNPCUtilityBaselineComponent` | 동일 후보 기준 Utility raw score |
| `UNPCDecisionComponent` | trigger, dirty/urgent, request lifecycle |
| `UNPCPostProcessComponent` | switch cost, OOD, calibration, abstain |
| `UNPCCommitCoordinatorComponent` | Validate/Reserve/StartCommit |
| `UNPCSkillExecutorComponent` | Active Skill Tick/Complete/Cancel |
| `UNPCInferenceWorldSubsystem` | NNE 모델 공유, queue, batch, worker |
| `UNPCResourceReservationSubsystem` | Cover/SmartObject lease와 rollback |
| `UNPCSchemaRegistrySubsystem` | schema/model/registry/hash 검증 |
| `UNPCDebugComponent` | Inspector, DrawDebug, Replay capture |
| `UPlayerNoiseEmitterComponent` | Quinn의 발소리와 충돌 소음 |
| `UAnimNotify_ReportAINoise` | 발 접촉 시 Hearing Event |

## 6.3 Data Asset

| Asset | 책임 |
|---|---|
| `UNPCProfileDataAsset` | 성격, 역할 속성, 초기 감정·관계 |
| `UNPCPolicyDataAsset` | NNE ModelData, model hash, contract hash |
| `UNPCSkillRegistryDataAsset` | Skill ID, 허용 Target Kind, resource, LOS, 파라미터 |
| `UNPCGoalDefinitionDataAsset` | Goal priority, source, phase table, preemption |
| `UNPCSensorConfigDataAsset` | Sight/Hearing/TTL |
| `UNPCCalibrationDataAsset` | logistic weights, group threshold, OOD asset |
| `UNPCUtilityBaselineDataAsset` | baseline version, feature curves, weights |
| `UNPCPerformanceProfileDataAsset` | 판단 빈도와 deadline |

---

# 7. 핵심 C++ 계약

## 7.1 Enum

Enum ID는 생성 Header에서 가져온다. 수동 순서 변경을 금지한다.

```cpp
enum class ETargetKind : uint8
{
    NoTarget = 0,
    Entity = 1,
    SoundEvent = 2,
    LastKnownPosition = 3,
    CoverSlot = 4,
    SmartObject = 5,
    Waypoint = 6,
    WorldPosition = 7
};
```

Skill ID:

```text
0 Idle
1 ContinueCurrentAction
2 LookAt
3 TurnTo
4 Approach
5 KeepDistance
6 RetreatFrom
7 Follow
8 Investigate
9 SearchArea
10 Greet
11 Warn
12 CallForHelp
13 TakeCover
14 Flee
15 Attack
```

## 7.2 Runtime Handle

```cpp
struct FTargetHandle
{
    ETargetKind Kind = ETargetKind::NoTarget;
    uint64 StableId = 0;
    uint32 Generation = 0;
    uint64 Revision = 0;

    bool SameIdentity(const FTargetHandle& Other) const
    {
        return Kind == Other.Kind
            && StableId == Other.StableId
            && Generation == Other.Generation;
    }

    bool SameSnapshot(const FTargetHandle& Other) const
    {
        return SameIdentity(Other) && Revision == Other.Revision;
    }
};
```

- `IdentityKey`: dedupe, 이전 slot 유지, 과거 Event remap
- `SnapshotKey`: Candidate Hash, Commit validation
- StableId/Generation/Revision은 모델 Feature에 들어가지 않는다.

## 7.3 Runtime Payload

GameThread의 Typed Target은 Kind별 payload를 가진다.

```cpp
using FTargetPayloadVariant = TVariant<
    FNoTargetPayload,
    FEntityTargetPayload,
    FSoundEventTargetPayload,
    FLastKnownPositionPayload,
    FCoverSlotTargetPayload,
    FSmartObjectTargetPayload,
    FWaypointTargetPayload,
    FWorldPositionTargetPayload>;

struct FTargetRuntimeSnapshot
{
    FTargetHandle Handle;
    FTargetPayloadVariant Payload;
};
```

`TWeakObjectPtr<AActor>` 같은 UObject reference는 `FEntityTargetPayload`의 GameThread 조회용으로만 허용한다. Worker용 `FNPCInferenceRequest`에는 복사하지 않는다.

## 7.4 Model Feature

```cpp
struct FTargetFeatures
{
    TStaticArray<float, 48> Values{};
};
```

다음 값은 금지한다.

- StableId/EventId/WaypointId
- Actor pointer
- ReservationId
- 절대 월드 좌표
- CreatedTime
- 숨은 Actor의 현재 속도

위치와 시간은 다음으로 변환한다.

- NPC-local 상대 위치
- 거리와 bearing/elevation
- `now - observed_at`
- confidence
- perception source

## 7.5 Handle 생성과 Runtime Payload 필수 필드

| Kind | StableId | Generation | Revision | 필수 Runtime Payload |
|---|---|---|---|---|
| NoTarget | 0 | 0 | 0 | 없음 |
| Entity | 서버 영속 Entity/Net ID | Actor spawn generation | Belief revision | current permitted perceived position, belief source, observed_at, confidence, trackable_now |
| SoundEvent | World epoch 내 단조 event ID | World event epoch | 0 | immutable position, created_at, loudness, attribution confidence, TTL, sound class |
| LastKnownPosition | NPC별 snapshot ID | source Entity generation 또는 0 | 생성 시 Belief revision | immutable position, source, observed_at, creation confidence, TTL, optional subject identity |
| CoverSlot | resource ID | resource spawn/rebuild generation | availability revision | entry/peek position, resource generation, availability revision |
| SmartObject | Smart Object slot ID | resource generation | availability revision | entry position, use type, capacity/availability |
| Waypoint | route+waypoint ID | route load generation | route revision | authored position, sequence index, semantic flags |
| WorldPosition | Goal별 immutable position ID | authorizing Goal generation | 생성 시 Goal revision | immutable position, source, TTL, authorizing Goal ID/revision |

`ReservationId`는 CoverSlot/SmartObject 후보 생성 시 존재하지 않는다. Commit의 예약 성공 후 별도 Receipt에만 저장한다.

Runtime Snapshot의 `created_at`과 월드 좌표는 Feature Builder에서 `age`와 NPC-local 상대 좌표로 변환한 뒤 버린다.

## 7.6 Event Record

```cpp
struct FNPCRecentEvent
{
    ENPCEventType Type;
    uint64 EventId;
    double OccurredAt;
    float Strength;
    float Confidence;
    FVector3d SnapshotWorldPosition;
    FTargetHandle StableTarget;
    uint64 GoalRevisionAtEvent;
    bool bUrgent;
};
```

Event는 Target Slot을 저장하지 않는다. Tensor 생성 시 `IdentityKey`로 현재 17개 slot에 remap한다.

## 7.7 Goal Instance

```cpp
struct FNPCGoalInstance
{
    uint64 GoalInstanceId;
    uint64 GoalRevisionAtActivation;
    ENPCGoalType GoalType;
    ENPCGoalState State;
    ENPCGoalPhase Phase;
    uint8 Priority;
    ENPCGoalSourcePriority SourcePriority;
    double CreatedAt;
    TOptional<double> Deadline;
    ENPCGoalInterruptibility Interruptibility;
    ENPCGoalResumePolicy ResumePolicy;
    FTargetHandle PrimaryTarget;
    TArray<FTargetHandle, TInlineAllocator<2>> SecondaryTargets;
    uint16 AllowedSkillMask;
    uint16 ForbiddenSkillMask;
};
```

## 7.8 Candidate Record

```cpp
struct FNPCCandidateRecord
{
    uint16 CandidateIndex;  // 0..271
    uint8 SkillId;          // 0..15
    uint8 TargetSlot;       // 0..16
    FTargetHandle TargetSnapshot;
    bool bValid;
    ENPCCandidateMaskReason MaskReason;
};
```

## 7.9 SHA-256 Digest

Unreal의 SHA-1 계열 타입과 혼동하지 않도록 계약 전용 32-byte 타입을 사용한다.

```cpp
struct FAINPCSha256Digest
{
    TStaticArray<uint8, 32> Bytes{};
};
```

## 7.10 Inference Request

```cpp
struct FNPCInferenceRequest
{
    uint64 NPCStableId;
    uint32 NPCGeneration;
    uint64 DecisionId;
    uint64 GoalRevision;
    uint64 BeliefRevision;
    double SnapshotWorldTime;
    double DeadlineWorldTime;

    FAINPCSha256Digest CandidateSetHash;   // exactly 32 bytes
    FAINPCSha256Digest DecisionContractHash; // exactly 32 bytes
    uint32 PostProcessVersion;
    uint32 CalibrationVersion;

    TStaticArray<float, 128> GlobalState;
    TStaticArray<float, 17 * 48> TargetFeatures;
    TStaticArray<int64, 17> TargetKindIds;
    TStaticArray<uint8, 17> TargetMask;

    TStaticArray<float, 12 * 24> EventFeatures;
    TStaticArray<int64, 12> EventTypeIds;
    TStaticArray<int64, 12> EventTargetSlots;
    TStaticArray<uint8, 12> EventMask;

    TStaticArray<float, 272 * 16> CandidatePairFeatures;
    TStaticArray<uint8, 272> CandidateMask;

    TStaticArray<FTargetHandle, 17> TargetHandleSnapshot;
};
```

`uint8` Mask buffer는 ONNX BOOL Tensor에 바인딩하는 adapter에서 0/1을 보장한다. Schema dtype 자체를 float로 임의 변경하지 않는다.

`BeliefRevision`은 로그와 최신 snapshot 비교용이다. 모든 Belief 변화가 Commit을 무효화하지는 않는다. Commit Gate는 선택된 Target의 SnapshotKey와 Skill에 필요한 Belief 조건만 검증해 불필요한 stale 폐기를 방지한다.

## 7.11 Inference Response

```cpp
struct FNPCInferenceResponse
{
    uint64 DecisionId;
    FAINPCSha256Digest CandidateSetHash;   // exactly 32 bytes
    FAINPCSha256Digest DecisionContractHash; // exactly 32 bytes
    uint32 PostProcessVersion;
    uint32 CalibrationVersion;
    TStaticArray<float, 272> RawScores;
    TStaticArray<float, 272 * 4> ParameterProposals;
};
```

OOD, Calibration, Switch Cost는 Unreal authoritative post-process에서 계산한다.

---

# 8. AI Perception과 Belief Runtime

## 8.1 Component 배치

`AAINativeNPCController`

- `UAIPerceptionComponent`
- `UAISenseConfig_Sight`
- `UAISenseConfig_Hearing`
- 선택: Damage Sense

Quinn:

- Sight Stimuli Source 등록
- Animation Notify 기반 Hearing Event

AI Perception callback은 Skill을 실행하지 않는다.

```text
Stimulus 수집
→ Belief 갱신
→ Event Buffer 기록
→ Goal Event 전달
→ Decision dirty/urgent 표시
```

## 8.2 Sight 설정 시작값

Data Asset 예시:

```text
Sight Radius                  2000 cm
Lose Sight Radius             2500 cm
Peripheral Vision Half Angle  70 deg
Sight Max Age                 4 sec
LastKnownPosition TTL         6 sec
```

값은 Data Asset에서 조정하고 Schema의 normalization 상수와 혼동하지 않는다.

## 8.3 Sight Acquired

현재 Sight가 성공하면:

- `Entity` Handle/Snapshot 생성 또는 Revision 갱신
- source = Sight
- perceived position 갱신
- 관측 위치로 velocity 추정
- visible duration 갱신
- `SightAcquired` Event 기록
- 동일 Subject의 LastKnownPosition Target 제거

## 8.4 Sight Lost

Sight Lost 순간:

1. 기존 `Entity`는 Target Universe에서 제거
2. 마지막 허용 위치를 복사해 immutable `LastKnownPosition` 생성
3. source, observed_at, confidence_at_creation, TTL 저장
4. 실행 중 Entity 추적 Skill은 마지막 허용 위치에서 freeze
5. urgent 또는 dirty 재판단 요청
6. 이후 Actor Transform/Velocity로 snapshot을 갱신하지 않음

```cpp
void UNPCBeliefComponent::HandleSightLost(
    const FTargetHandle& EntityHandle,
    const FEntityBelief& LastVisibleBelief)
{
    RemoveCurrentEntityTarget(EntityHandle);

    FLastKnownPositionPayload Snapshot;
    Snapshot.WorldPosition = LastVisibleBelief.PerceivedWorldPosition;
    Snapshot.ObservedAt = LastVisibleBelief.ObservedAt;
    Snapshot.ConfidenceAtCreation = LastVisibleBelief.Confidence;
    Snapshot.TTLSeconds = Config.LastKnownPositionTTL;

    AddImmutableLastKnownPosition(EntityHandle, Snapshot);
}
```

## 8.5 Hearing

SoundEvent는 immutable Target이다.

```cpp
struct FSoundEventTargetPayload
{
    FVector3d EventWorldPosition;
    double CreatedAt;
    float Loudness;
    float AttributionConfidence;
    float TTLSeconds;
    uint8 SoundClass;
    TOptional<FTargetHandle> AttributedEntity;
};
```

Attributed Entity가 있어도 현재 Sight가 없으면 그 Actor의 Transform으로 Event 위치를 갱신하지 않는다.

최근 발소리는 공간·시간 근접 기준으로 Event를 병합할 수 있지만 병합 알고리즘과 Revision은 결정론적으로 정의한다.

## 8.6 Quinn 발소리

```text
Walk/Run Animation
→ AN_ReportAINoise
→ UPlayerNoiseEmitterComponent::EmitFootstep
→ UAISense_Hearing::ReportNoiseEvent
```

소리 발생 코드는 반응을 결정하지 않는다.

```cpp
void UPlayerNoiseEmitterComponent::EmitFootstep(
    const FVector& WorldLocation,
    float SpeedNorm,
    FGameplayTag SurfaceTag)
{
    const float Loudness = FootstepCurve->GetFloatValue(SpeedNorm);
    ReportNoise(WorldLocation, Loudness, SurfaceTag);
}
```

## 8.7 Belief 위치 Feature

```cpp
const FTransform NPCTransform = NPC->GetActorTransform();
const FVector LocalPos =
    NPCTransform.InverseTransformPositionNoScale(BelievedWorldPosition);
const FVector LocalVel =
    NPCTransform.InverseTransformVectorNoScale(BeliefDerivedVelocity);

const float Distance3D = LocalPos.Size();
const float DistancePlanar = FVector2D(LocalPos.X, LocalPos.Y).Size();
const float Bearing = FMath::Atan2(LocalPos.Y, LocalPos.X);
const float Elevation =
    FMath::Atan2(LocalPos.Z, FMath::Max(DistancePlanar, 1.0f));
```

Path와 LOS Feature도 이 Believed Position으로 계산한다.

## 8.8 Ground Truth 분리

Editor와 Test는 다음을 별도 채널로 저장할 수 있다.

- Ground Truth Actor 위치
- Believed Position
- LastKnownPosition
- SoundEvent 위치

그러나 Inference Request는 Ground Truth pointer와 transform을 보유하지 않는다.

Development Assertion:

- Sight가 없는데 Entity 위치가 Actor를 따라가면 실패
- LastKnownPosition이 생성 후 바뀌면 실패
- SoundEvent가 Instigator를 따라가면 실패
- 숨은 Actor Ground Truth만 바꿨는데 Tensor가 바뀌면 실패

---

# 9. Event Buffer

## 9.1 V1 고정 계약

- 슬롯 수: 12
- 시간 범위: 최대 10초
- 과거 Target 참조: Stable Typed Handle
- 저장 순서: 발생 시간 오름차순, 동시간이면 Event ID 오름차순
- overflow: 가장 오래된 non-urgent Event 제거
- urgent Event는 동일 Type/Target 중복 병합 가능
- Event ID는 NPC별 uint64 단조 증가

## 9.2 Event Type

```text
0 NoneOrPadding
1 SightAcquired
2 SightLost
3 SoundHeard
4 Damaged
5 SkillSucceeded
6 SkillFailed
7 SkillInterrupted
8 WarningIssued
9 WarningIgnored
10 TargetMovedSignificantly
11 TargetInvalidated
12 GoalChanged
13 ReservationLost
14 SharedKnowledgeReceived
15 Other
```

## 9.3 Slot Remap

```text
Event.StableTarget
→ 현재 Target Slot의 IdentityKey 검색
→ 존재: event_target_slots = 0..15
→ 없음: slot 16 NoTarget
→ event_features[17] target_present = 0
```

동일 Identity의 Revision이 달라도 과거 Event는 현재 slot에 연결할 수 있다. Commit 검증에는 Event Handle이 아니라 Candidate Target의 최신 SnapshotKey를 사용한다.

---

# 10. Goal Manager

## 10.1 상태

```text
Inactive → Active → Succeeded / Failed / Aborted
                 ↘ Suspended → Active / Aborted
```

- Active Goal: 최대 1개
- Suspended stack: 최대 8개
- terminal Goal 재활성화 금지

## 10.2 Arbitration Key

작은 tuple이 우선한다.

```text
(-priority, -source_priority, created_at, goal_instance_id)
```

Source:

```text
Emergency 4 > Quest 3 > Combat 2 > Social 1 > Routine 0
```

## 10.3 Preemption

| Interruptibility | 일반 상위 Goal | Emergency | Server ForceAbort |
|---|---|---|---|
| Always | 즉시 | 즉시 | 즉시 |
| PhaseBoundary | Skill/Phase 경계 | 즉시 | 즉시 |
| EmergencyOnly | 대기 | 즉시 | 즉시 |
| Never | 대기 | 대기 | 즉시 |

Resume Policy:

- `ResumeSamePhase`
- `RestartPhase`
- `AbortOnPreempt`

새 Goal activation 준비가 실패하면 기존 Goal은 계속 Active다.

## 10.4 Goal Revision

다음 변화에서만 증가한다.

- Active Goal instance 변경
- Active/Suspended/terminal 전환
- Phase 변경
- Primary authoritative Target Handle 변경
- allowed/forbidden Skill mask 변경
- authoritative deadline 값 변경
- interruptibility/resume policy 변경

다음은 증가시키지 않는다.

- 매 frame progress
- deadline countdown
- Event Buffer 변화
- Belief Revision 변화
- Candidate score 변화

## 10.5 Phase 0 FSM — IdleObserve

| Phase | Trigger | Guard | Action | Next |
|---|---|---|---|---|
| Observe | OnEnter | 없음 | Idle/관찰 Candidate 허용 | Observe |
| Observe | SoundHeard | confidence ≥0.40, TTL 유효 | InvestigateDisturbance 생성 | arbitration |
| Observe | Timeout | 없음 | 유지 | Observe |
| Observe | ForceAbort | 없음 | 종료 | Aborted |

## 10.6 Phase 0 FSM — InvestigateDisturbance

| Phase | Trigger | Guard | Allowed Skill | Next/Result |
|---|---|---|---|---|
| Orient | OnEnter | target valid | TurnTo, Continue | Orient |
| Orient | TurnTo 성공 | 없음 | — | Navigate |
| Orient | 1.5초 timeout | target valid | — | Navigate |
| Orient | TargetExpired | 없음 | — | Failed |
| Navigate | OnEnter | Believed Position path 가능 | Approach, Investigate, Continue | Navigate |
| Navigate | 도착 ≤150cm | 없음 | — | Search |
| Navigate | PathUnavailable | 없음 | — | Failed |
| Navigate | 8초 timeout | 없음 | — | Failed |
| Search | OnEnter | search budget 5초 | SearchArea, TurnTo, Continue | Search |
| Search | SightAcquired(subject) | attribution ≥0.7 | — | Succeeded |
| Search | budget 만료 | 없음 | — | Return |
| Return | OnEnter | home Waypoint valid | Approach, Continue | Return |
| Return | 도착 ≤100cm | 없음 | — | Succeeded |
| Return | 10초 timeout | 없음 | — | Failed |

## 10.7 Skill Result 연결

Skill Executor는 terminal 결과를 Goal Manager에 전달한다.

```text
SkillSucceeded
SkillFailed(PathUnavailable)
SkillInterrupted
ReservationLost
```

Goal Manager가 Phase를 바꾸면 `goal_revision`을 올리고 현재 inference를 supersede한다.

---

# 11. Typed Target Universe와 Target Slotter

## 11.1 고정 Slot

```text
Regular Target Slot 0..15
NoTarget Slot        16
Total                17
```

Quota:

| Category | 수 | Kind |
|---|---:|---|
| Entity | 8 | Entity |
| Sound | 2 | SoundEvent |
| Cover | 2 | CoverSlot |
| SmartObject | 1 | SmartObject |
| PositionLike | 3 | LastKnownPosition, Waypoint, WorldPosition |
| NoTarget | 고정 1 | NoTarget |

Phase 0에서 미사용 Kind의 quota는 overflow backfill에 사용될 수 있지만 Kind ID와 slot capacity는 바꾸지 않는다.

## 11.2 Target Universe 원천

- Belief Component: Entity, SoundEvent, LastKnownPosition
- Goal Manager: Waypoint, WorldPosition, primary/secondary Target
- Resource Subsystem: CoverSlot, SmartObject
- Skill Executor: 현재 Target, 예약 Resource
- Dialogue: Active Dialogue Target
- Damage: 최근 Attacker

## 11.3 Dedupe

- 같은 `IdentityKey`는 최신 Revision 하나만 유지
- Entity와 SoundEvent는 별개
- Sight Lost 후 같은 Subject의 Entity와 LastKnownPosition 동시 유지 금지
- WorldPosition ID는 Goal 수명주기 안에서 immutable

## 11.4 Mandatory Preserve

순서:

1. 현재 Skill Target — 최대 1
2. Active Goal Primary Target — 최대 1
3. Active Dialogue Target — 최대 1
4. 보유 Reservation Resource — 최대 2
5. 최근 Attacker — 최대 2
6. Active Goal Secondary Target — 최대 2

16개를 넘으면 `MandatoryOverflow`로 abstain하고 Goal fallback을 사용한다. 임의로 잘라내지 않는다.

## 11.5 Non-mandatory 정렬

| Category | 정렬 |
|---|---|
| Entity | visible desc → confidence desc → age asc → distance asc → handle asc |
| Sound | priority desc → confidence desc → age asc → loudness desc → handle asc |
| Cover | availability desc → generation valid desc → path reachable desc → distance asc → handle asc |
| SmartObject | availability desc → generation valid desc → distance asc → handle asc |
| PositionLike | goal owned desc → confidence desc → age asc → distance asc → kind ID asc → handle asc |

빈 Slot은 다음 round-robin으로 backfill한다.

```text
Entity → Sound → Cover → SmartObject → PositionLike → 반복
```

## 11.6 Sound Event Priority v1

Slotter의 `event_priority`는 행동 선호가 아니라 정보 보존 우선순위다. `target_slotter_v1.0.0`에서 다음 고정 값을 사용한다.

```text
Explosion 7
Weapon    6
Voice     5
Impact    4
Vehicle   3
Door      2
Footstep  1
Other     0
```

값을 바꾸면 `target_slotter_version`을 올리고 Target Recall과 Hash Golden Test를 다시 수행한다. 정렬 key, quota, mandatory 순서, sound priority는 모두 동일 version asset의 일부다.

## 11.7 Slot Hysteresis

- 이번에 선정된 Target이 이전 tick에도 존재하면 기존 slot 유지
- selection 자체에는 hysteresis bonus를 주지 않음
- 새 Target은 mandatory rank, category, sort key 순으로 낮은 빈 slot에 배치
- `canonical handle asc`는 `(Kind uint8, StableId uint64, Generation uint32, Revision uint64)`의 숫자 tuple 오름차순이다.
- `TMap`/`TSet` 순회 순서에 의존하지 않음

## 11.8 Target Recall

로그:

- `PerceptionMiss`
- `ExpiredBelief`
- `MandatoryOverflow`
- `QuotaDrop`
- `DedupeError`
- `SlotterMismatch`
- `UnsupportedKind`

General Test:

- point ≥99.5%
- Wilson 95% lower bound ≥99.0%

Critical Suite:

- 100%
- MandatoryOverflow 0건

---

# 12. Candidate Builder

## 12.1 고정 Layout

```text
candidate_index = skill_id * 17 + target_slot
skill_id        = candidate_index / 17
target_slot     = candidate_index % 17
```

모든 요청은 272 row다. Ragged Candidate는 V1에서 사용하지 않는다.

## 12.2 ContinueCurrentAction

- 실행 중 Skill이 있을 때 정확히 하나만 valid
- 현재 Target이 slot에 있으면 그 slot 사용
- 없으면 NoTarget slot 16
- 현재 실행 중인 동일 Skill/동일 Target 일반 Candidate는 mask
- Skill이 없으면 Continue mask

## 12.3 Skill–Target Kind Matrix

| Skill | NoTarget | Entity | SoundEvent | LastKnownPosition | CoverSlot | SmartObject | Waypoint | WorldPosition |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
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

## 12.4 Hard Mask

허용:

- Registry의 Skill–Target Kind
- Target slot valid
- Goal allowed/forbidden Skill
- NPC 생존·장비·권한
- 현재 Skill interruptibility
- Continue 특수 규칙

금지:

- 거리가 가까우므로 Attack만 남김
- 성격이 겁이 많으므로 Flee만 남김
- 뒤쪽 소리이므로 TurnTo 우선
- 관계가 낮으므로 Greet 제거

선호는 모델 또는 Utility Baseline이 평가한다.

## 12.5 Candidate Pair Feature

Schema의 16개 Feature를 Candidate마다 생성한다.

- running Skill 동일 여부
- running Target 동일 여부
- target present
- visible
- confidence/age/distance
- believed position의 path
- Skill LOS/resource 요구
- current belief의 LOS/resource 가능
- Goal 허용
- Kind 호환
- default parameter

## 12.6 Candidate Hash

Hash에는 discrete 정보만 들어간다.

```text
magic ANPCCS20
schema major/minor
Skill Registry SHA-256
Target Slotter version
slot count 17
Target Handle 17개
Candidate Mask 272 bit
```

Switch Cost, raw/adjusted score, float Feature는 포함하지 않는다.

- Target Handle은 `kind uint8 + stable_id uint64 LE + generation uint32 LE + revision uint64 LE`
- Candidate Mask는 272 bit = 34 byte, candidate `i`는 byte `i/8`의 bit `i%8`, LSB-first
- NoTarget Handle은 전부 0
- padding slot의 Handle도 전부 0


---

# 13. Schema 2.0 Feature Builder

## 13.1 고정 상수

```text
regular_target_slots       = 16
no_target_slot             = 16
total_target_slots         = 17
skill_count                = 16
candidate_count            = 272
event_slots                = 12
global_feature_count       = 128
target_feature_count       = 48
event_feature_count        = 24
candidate_pair_feature_count = 16
parameter_count            = 4
```

## 13.2 Tensor

| Tensor | Shape | dtype | Semantics |
| --- | --- | --- | --- |
| global_state | ['B', 128] | float32 |  |
| target_features | ['B', 17, 48] | float32 |  |
| target_kind_ids | ['B', 17] | int64 |  |
| target_mask | ['B', 17] | bool | true for occupied regular slot and always true for NoTarget slot 16 |
| event_features | ['B', 12, 24] | float32 |  |
| event_type_ids | ['B', 12] | int64 |  |
| event_target_slots | ['B', 12] | int64 | runtime stable typed handle is remapped to current slot; absent target maps to NoTarget and target_present=0 |
| event_mask | ['B', 12] | bool | true for valid event |
| candidate_pair_features | ['B', 272, 16] | float32 |  |
| candidate_mask | ['B', 272] | bool | hard-valid candidate only |
| candidate_raw_scores | ['B', 272] | float32 | output |
| candidate_parameter_proposals | ['B', 272, 4] | float32 | output |

`NoTarget`:

- slot index 16
- kind ID 0
- target mask true
- target feature 48개 모두 0

Unused regular slot:

- Handle 전부 0
- kind ID 0
- target mask false
- target feature 모두 0

Unused Event:

- Event Type 0
- target slot 16
- mask false
- feature 모두 0

## 13.3 Feature Builder 순서

```text
1. Authority self snapshot
2. Active Goal snapshot
3. Belief snapshot
4. Event Buffer snapshot
5. Target Universe
6. Target Slotter
7. Candidate Builder
8. NPC-local spatial feature
9. normalization
10. NaN/Inf/range validation
11. discrete hash
12. immutable Inference Request
```

## 13.4 좌표·시간 규칙

- 거리 단위: cm
- 시간 기준: server monotonic world seconds
- 절대 좌표는 Feature에 넣지 않음
- `age = now - observed_at`
- sin/cos 입력은 radian
- path query는 Believed Position
- 숨은 Entity velocity는 사용하지 않음

Normalization 상수:

```text
spatial_max_cm          = 5000.0
path_distance_max_cm    = 10000.0
speed_max_cm_s          = 1200.0
acceleration_max_cm_s2  = 4000.0
yaw_rate_max_deg_s      = 720.0
target_age_max_s        = 10.0
event_age_max_s         = 10.0
```

## 13.5 Generated API

```cpp
static_assert(AINPCSchema::GlobalFeatureCount == 128);
static_assert(AINPCSchema::TotalTargetSlots == 17);
static_assert(AINPCSchema::CandidateCount == 272);

AINPCSchema::WriteGlobalFeature(
    Buffer,
    EGlobalFeature::SelfHealthNorm,
    Value);
```

Feature index를 숫자로 직접 쓰는 코드는 금지한다.

`schema.yaml`에서 최소 다음 산출물을 생성한다.

```text
AINPCSchema.generated.h
AINPCEnums.generated.h
AINPCNormalization.generated.h
schema_generated.py
schema_2_0_generated.md
discrete_vectors.json
float_vectors.npz
```


---

# 14. Neural Policy와 오프라인 학습

## 14.1 V1 모델

V1은 Event Buffer를 사용하고 GRU를 사용하지 않는다. 감정·관계 값은 `UNPCSocialStateComponent`가 사건 기반으로 갱신하며 모델은 읽기만 한다.

```text
global_state [128]
→ MLP
→ global embedding 128

target_features [17×48]
+ target_kind_ids
→ shared target encoder
→ target embeddings [17×64]
→ masked pooling 128

event_features [12×24]
+ event_type_ids
+ referenced target embedding
→ temporal attention
→ event context 96

concat 128+128+96 = 352
→ fusion 352→256→128
→ tactical context h
```

## 14.2 Factorized Candidate Scorer

```text
q = Wq(h)                                  # 64
s = SkillEmbedding[skill_id]               # 64
t = Wt(TargetEmbedding[target_slot])       # 64
p = Wp(candidate_pair_features[16])        # 64
k = LayerNorm(s + t + p)
RawScore = dot(q, k) / 8
         + skill_bias
         + target_kind_bias
```

Output:

- `candidate_raw_scores [B,272]`
- `candidate_parameter_proposals [B,272,4]`

Parameter:

- duration
- speed
- preferred distance
- intensity

모델이 자원 예약, 관계 변경, Goal 전환을 출력하지 않는다.

목표:

- 전체 모델 ≤2.0M parameter
- FP32 raw weight ≤8MB
- candidate scoring 부분 약 0.35M MAC/decision
- encoder 포함 목표 ≤1.0M MAC/decision
- 실제 승인은 Export ONNX profiler 값으로 판단

## 14.3 Utility Baseline

동일한 다음 입력을 사용한다.

- 같은 Target Slot
- 같은 Candidate Mask
- 같은 Belief
- 같은 Goal
- 같은 Switch Cost

Baseline은 Candidate별 raw utility를 출력한다. 모델 교사로 강제 사용하지 않으며 비교군과 fallback으로 사용한다.

Baseline A/B 비교에서는 동일 hard mask와 동일 Switch Cost를 적용한다. Neural 전용 Calibration/OOD asset은 Baseline score에 재사용하지 않고, Baseline은 versioned deterministic acceptance/fallback 규칙을 가진다.

Version:

```text
utility_baseline_v1.0.0
```

## 14.4 데이터

### Silver

- 절차 생성
- LLM ranking
- 자동 heuristic
- 대량, 낮은 label weight

### Gold

- 사람 acceptable set
- 사람 시연
- preference 비교
- 복수 annotator agreement

### Live/DAgger

- 실제 policy rollout
- 디자이너 intervention
- Candidate miss
- abstain/OOD
- 이상 행동

분할은 row random이 아니라 시나리오 계열, 맵 family, Role×Goal, sensor modality, sequence family 단위로 한다.

## 14.5 Unreal Capture Record

```text
runtime identifiers / handles     → debug·replay 전용
schema tensors                    → model input
candidate mask                    → contract
raw/adjusted/calibrated scores    → evaluation
selected/accepted/commit result   → label
ground truth                      → 별도 evaluation channel
```

Ground Truth를 Feature Builder에 전달하지 않는다.

## 14.6 ONNX Export

산출물:

- model ONNX
- model hash
- schema version/hash
- normalization version
- Skill Registry hash
- Target Slotter version
- output shape
- profiler MAC/latency
- calibration/OOD asset 별도

Export 전 Python Reference Model과 ONNX Runtime 결과를 비교한다.

Policy Manifest 필수 필드:

```json
{
  "schema_version": "2.0.0",
  "skill_registry_version": "1.0.0",
  "target_slotter_version": "1.0.0",
  "postprocess_version": "1.0.0",
  "normalization_version": "2.0.0",
  "candidate_count": 272,
  "target_slots": 17,
  "event_slots": 12,
  "model_sha256": "...",
  "decision_contract_sha256": "..."
}
```

---

# 15. NNE 추론 Subsystem

## 15.1 구조

`UNPCInferenceWorldSubsystem`

- ModelData 1회 로드
- runtime/backend 탐색
- model instance pool
- request queue
- batch assembly
- worker execution
- GameThread response enqueue
- performance counters

NPC마다 모델을 로드하지 않는다.

## 15.2 초기화

```text
World Begin
→ Policy Data Asset 읽기
→ Schema/Model/Registry/Contract Hash 검증
→ NNE runtime 생성
→ Model Instance 생성
→ Tensor descriptor 검증
→ Golden smoke vector 실행
→ ready
```

검증 실패 시 Neural Policy를 비활성화하고 Utility Baseline을 사용한다.

## 15.3 Tensor Binding

- float32: contiguous `TArray<float>` 또는 static buffer
- int64: 생성 계약과 동일
- bool: ONNX BOOL 의미의 0/1 buffer
- shape를 runtime에서 추론하지 않고 generated constants와 비교
- 출력 길이가 272/272×4와 다르면 모델 로드 실패

## 15.4 Batch

Candidate row는 항상 272이므로 NPC batch만 합친다.

초기 전략:

- 1~8 NPC micro-batch
- 1~3ms request collection window
- deadline 우선 queue
- 같은 model/contract hash만 같은 batch
- stale NPC request는 batch 전 제거

## 15.5 Worker 안전

Worker Request는 immutable POD다.

금지:

- UObject dereference
- Actor Transform 조회
- Nav query
- Goal 변경
- Skill Start
- relationship/emotion update

## 15.6 Output 검증

- NaN/Inf
- output shape
- score finite
- parameter `[0,1]` clamp
- response contract hash
- decision ID

NaN/Inf가 하나라도 있으면 전체 응답을 폐기하고 fallback한다.

---

# 16. Decision Scheduler와 Post-process

## 16.1 요청 상태

NPC별:

```text
next_decision_id
commit_eligible_decision_id
active_cancellation_token
dirty_flag
urgent_flag
latest_snapshot_revision
```

## 16.2 판단 Trigger

- periodic
- Skill terminal
- SightAcquired
- SightLost
- SoundHeard
- Damaged
- GoalChanged
- ReservationLost
- TargetInvalidated
- TargetMovedSignificantly

권장 시작 빈도:

- Idle: 1Hz
- Alert/Social: 2~3Hz
- Combat: 5Hz
- 긴급 Event: 즉시

## 16.3 In-flight

- Commit 가능한 request 최대 1개
- 일반 변화: dirty flag
- urgent: 기존 token cancel/supersede 후 새 ID
- worker가 실제로 계속 돌더라도 취소된 response는 Commit 불가
- 응답 후 dirty가 있으면 최신 snapshot으로 재요청

## 16.4 Switch Cost

```text
SwitchCost = clamp(
    0.45 × skill_changed
  + 0.25 × target_changed
  + 0.20 × before_min_duration
  + 0.10 × releases_or_transfers_reservation,
  0, 1)

AdjustedScore = RawScore - SwitchCost
```

interrupt 불가능한 후보는 비용이 아니라 mask다.

## 16.5 선택·OOD·Calibration

```text
Raw
→ Mask
→ Switch Cost
→ Adjusted
→ argmax
→ OOD
→ Calibrator
→ Accept / Abstain
```

Masked softmax entropy는 valid Candidate만 사용한다.

OOD:

- unknown schema/enum/version → 1
- Tactical Context Mahalanobis distance 사용
- OOD ≥0.80 → abstain

Calibrator 입력:

- selected adjusted score
- second adjusted score
- adjusted gap
- normalized entropy
- valid count
- OOD
- Goal Type one-hot
- selected Target Kind one-hot

기본 accept threshold 0.75. Role/Goal override는 Calibration Asset에서 제공한다.

## 16.6 Fallback

1. 현재 Skill이 안전하고 유효하면 Continue
2. Utility Baseline
3. Goal phase fallback
4. 최소 안전 정책
5. Idle

Fallback 원인을 로그한다.

- OOD
- low calibration
- timeout
- model load failure
- stale
- contract mismatch
- all masked
- MandatoryOverflow

---

# 17. Atomic Commit과 Resource Reservation

## 17.1 원자 경계

Skill 전체 실행을 transaction으로 묶지 않는다.

```text
Worker
  BuildExecutionPlan

Server Game Thread
  Validate request/goal/target
  → Validate Skill
  → Reserve/transfer resources
  → StartCommit pending Skill
  → active Skill swap
```

`Tick`, `Complete`, `Fail`, `Cancel`은 transaction 밖이다.

## 17.2 Commit 검증

1. decision ID가 commit eligible인가
2. deadline 유효
3. Candidate Set Hash 일치
4. Decision Contract Hash 일치
5. NPC generation 일치
6. Goal Revision 일치
7. Target SnapshotKey 일치
8. Skill precondition
9. Target Kind별 정보 경계
10. Resource availability
11. StartCommit 가능

## 17.3 Reservation

- Resource Handle canonical order 정렬
- 전부 예약되거나 전부 실패
- 부분 성공 rollback
- 기본 lease 2.0초
- active Skill 0.5초마다 renew
- Start 실패 시 역순 rollback
- 후보 생성 단계에는 ReservationId 없음
- Generation과 Availability Revision만 사용

## 17.4 실패 코드

```text
DecisionSuperseded
DeadlineExpired
ContractMismatch
GoalRevisionChanged
TargetGenerationChanged
TargetBeliefInvalid
PreconditionChanged
ReservationConflict
PartialReservationRolledBack
StartCommitFailed
AuthorityRejected
```

## 17.5 Skill Start

`StartCommit`은 1ms 안에 다음만 수행한다.

- 실행 상태 생성
- 필요한 callback 등록
- 예약 소유권 연결
- Active Skill pending 상태 설정

blocking path search, asset load, network wait를 하지 않는다.

---

# 18. Target Kind별 실행 경계

| Kind | Commit/실행에서 허용 | 금지 |
|---|---|---|
| NoTarget | NPC, Goal, Skill 자체 상태 | Target Actor 조회 |
| Entity | 존재/generation/권한, 현재 허용 Perception, Skill이 요구하는 현재 LOS, authoritative collision/damage | Sight Lost 후 숨은 Transform으로 이동·조준 갱신 |
| SoundEvent | immutable event position, TTL, class | attributed Actor의 현재 Transform |
| LastKnownPosition | immutable snapshot, age, confidence, authorizing Goal | subject Actor 현재 위치·이동·생존을 이유로 취소 |
| CoverSlot | resource generation, availability, entry/peek 위치, reservation | 숨은 적 위치로 cover 품질 재계산 |
| SmartObject | resource generation, availability, capacity, object transform | 관계없는 hidden Actor 상태 |
| Waypoint | route generation/revision, authored position, Nav availability | 숨은 Actor를 따라 waypoint 이동 |
| WorldPosition | immutable position, Goal authority, TTL, bounds | 연결된 hidden Actor Transform으로 갱신 |

## 18.1 Entity 추적 단절

- Entity는 현재 지각되고 trackable한 동안만 aim/move target 갱신
- Sight Lost 즉시 Entity Candidate mask
- 실행 중 Skill은 마지막 허용 위치에서 freeze
- 재판단 후 LastKnownPosition 기반 Skill로 전환
- Physics hit test는 authoritative지만 숨은 위치를 알아내는 sensor로 사용하지 않음

## 18.2 Path/LOS

Candidate Feature와 Commit validation의 path/LOS는 다음 좌표를 사용한다.

- Entity: 현재 허용된 Perceived Position
- SoundEvent: immutable event position
- LastKnownPosition: immutable snapshot
- Resource/Waypoint/WorldPosition: 해당 권위 snapshot

Actor pointer가 있다는 이유로 현재 Transform을 대신 사용하지 않는다.

---

# 19. Skill 실행 시스템

## 19.1 인터페이스

```cpp
class INPCSkill
{
public:
    virtual bool CanGenerateCandidate(
        const FNPCDecisionSnapshot& Snapshot,
        const FTargetRuntimeSnapshot& Target) const = 0;

    virtual FSkillExecutionPlan BuildExecutionPlan(
        const FNPCDecisionSnapshot& Snapshot,
        const FNPCCandidateRecord& Candidate,
        const FNPCActionParameters& Parameters) const = 0;

    virtual FSkillValidationResult ValidateAtCommit(
        const FSkillExecutionPlan& Plan,
        const FNPCCommitContext& Context) const = 0;

    virtual FSkillReservationRequest GetReservationRequest(
        const FSkillExecutionPlan& Plan) const = 0;

    virtual bool StartCommit(
        const FSkillExecutionPlan& Plan,
        const FSkillReservationReceipt& Receipt) = 0;

    virtual ENPCSkillStatus Tick(float DeltaSeconds) = 0;
    virtual bool CanSuspend() const = 0;
    virtual void Suspend(ENPCSkillSuspendReason Reason) = 0;
    virtual FSkillResumeResult Resume() = 0;
    virtual void Cancel(ENPCSkillCancelReason Reason) = 0;
};
```

## 19.2 Failure Taxonomy

- TargetInvalid
- TargetGenerationChanged
- PreconditionChanged
- GoalChanged
- PathUnavailable
- ReservationConflict
- Interrupted
- TimedOut
- AuthorityRejected
- ExecutionError
- CancelledByNewDecision

## 19.3 Phase 0 Skill

### Idle

- NoTarget
- 현재 위치 유지
- look-around presentation은 deterministic animation layer에서 처리 가능

### ContinueCurrentAction

- 새 Skill을 Start하지 않음
- active execution 유지
- 원래 Target이 slot에서 빠졌더라도 Executor의 안전 규칙을 검증

### TurnTo

- Entity/Sound/LastKnown/Waypoint/WorldPosition
- snapshot 위치를 향해 Yaw 보간
- Entity는 현재 지각되는 동안만 갱신
- 각도 tolerance 도달 시 성공

### Approach

- Entity/LastKnown/Cover/SmartObject/Waypoint/WorldPosition
- Believed Snapshot의 Nav projection
- preferred distance를 acceptance radius로 변환
- path failure taxonomy 기록

### Investigate

```text
snapshot 위치 검증
→ Nav projection
→ MoveTo
→ 도착 시 방향 확인
→ Goal phase event
```

### SearchArea

- LastKnown/Waypoint/WorldPosition
- Goal이 제공한 search radius와 budget 사용
- 무작위 점은 seed와 canonical order로 재현 가능하게 생성

## 19.4 Phase 1 Skill

- LookAt
- KeepDistance
- RetreatFrom
- Follow
- Greet
- Warn
- CallForHelp
- TakeCover
- Flee
- Attack

Attack은 현재 허용된 Entity Perception과 Combat Module의 authoritative 판정을 요구한다.

## 19.5 StateTree

복합 Skill 내부 절차에만 사용한다.

```text
Neural Policy: Investigate 선택
StateTree: Move → Turn → Wait/Search → Complete
```

StateTree에서 관계·거리·성격 조합으로 상위 Skill을 선택하지 않는다.

---

# 20. Manny Animation

## 20.1 Locomotion

- `SKM_Manny`
- `ABP_Manny`
- CharacterMovement 기반 기존 locomotion 유지
- NPC 전용 AnimGraph 전체 복제 금지

## 20.2 추가 Montage

Phase 1:

- Greet
- Warn
- CallForHelp
- Attack placeholder
- Hit reaction

## 20.3 Turn/Look 단계

### Phase 0

- Actor/Capsule Yaw 보간
- root motion 없이 검증

### V1

- Turn-in-place
- Aim Offset
- Head/Spine LookAt
- 몸과 머리 속도 분리

모델은 pose를 출력하지 않고 Skill/강도 파라미터만 제공한다.

---

# 21. 실제 시나리오

## 21.1 정면 시야

```text
SightAcquired(Quinn)
→ Entity Target Universe
→ Entity slot 선정
→ 272 Candidate 생성
→ TurnTo(Entity) raw score
→ adjusted/calibrated accept
→ Commit
→ Manny 회전
```

소리가 없어도 위치·시야 Feature로 반응한다.

## 21.2 뒤쪽 발소리

```text
SoundHeard
→ SoundEvent Handle/immutable 위치
→ Target Slotter Sound quota
→ TurnTo(SoundEvent)
→ 회전 후 SightAcquired
→ Entity Target 추가
```

SoundEvent의 attributed Quinn Actor Transform은 사용하지 않는다.

## 21.3 벽 뒤 이동

```text
SightLost
→ Entity 제거
→ LastKnownPosition snapshot
→ 현재 Entity Attack/Follow candidate mask
→ Goal InvestigateDisturbance
→ Approach/Investigate/SearchArea
```

Quinn이 벽 뒤에서 이동해도 snapshot은 변하지 않는다.

## 21.4 Goal 복귀

```text
Search budget 만료
→ Return phase
→ home Waypoint mandatory target
→ Approach(Waypoint)
→ 도착
→ Investigate Succeeded
→ Suspended IdleObserve resume
```

## 21.5 긴급 피격

```text
Decision 42 inference 중
→ Damaged urgent
→ epoch/decision ID 43
→ token 42 cancel
→ 43 dispatch
→ response 42 도착: DecisionSuperseded
→ 43만 Commit 가능
```

## 21.6 Phase 1 Cover

```text
CoverSlot Target
→ candidate raw score
→ Commit transaction에서 availability revision 검증
→ lease 예약
→ TakeCover StartCommit
→ Tick 중 lease renew
```

---

# 22. Debug, 로그, 데이터 캡처

## 22.1 Decision Inspector

표시:

- Ground Truth와 Belief 별도
- Active Goal/Phase/Revision
- Event Buffer 12개
- Target Universe
- mandatory/quota/drop reason
- Target Slot 0..16
- Target Handle와 Kind
- 272 Candidate mask
- Neural raw score
- Utility Baseline score
- Switch Cost
- Adjusted score
- selected candidate
- OOD
- calibrated acceptability
- abstain/fallback
- decision ID/deadline
- stale discard reason
- reservation lease
- Skill failure taxonomy
- model/schema/registry/hash

## 22.2 DrawDebug

- Sight cone
- currently perceived Entity: 실선
- LastKnownPosition: 점선/age/confidence
- SoundEvent: sphere/TTL
- Goal target
- Target slot 번호
- Nav path to Believed Position
- Editor 전용 Ground Truth marker

## 22.3 Decision Log

```json
{
  "npc_id": "guard_013",
  "decision_id": 1821,
  "goal_revision": 12,
  "candidate_set_hash": "sha256:...",
  "decision_contract_hash": "sha256:...",
  "target_count": 7,
  "candidate_valid_count": 24,
  "selected_candidate": 47,
  "raw_score": 1.84,
  "switch_cost": 0.25,
  "adjusted_score": 1.59,
  "ood": 0.08,
  "p_acceptable": 0.87,
  "commit": "Started"
}
```

## 22.4 이상 행동 캡처

- 이전 10~30초 Event
- Goal stack
- Belief Snapshot
- Target Universe/Slot Map
- Candidate/Hash
- 모델/Baseline 결과
- Commit 결과
- Ground Truth debug
- Replay seed
- 사람 acceptable candidate
- Candidate/Target miss 여부

---

# 23. 멀티플레이

## 23.1 서버

서버가 소유한다.

- Perception
- Belief
- Goal
- Target Slotter
- inference request
- post-process
- Commit
- Skill authority
- 관계·감정 사건 갱신

## 23.2 복제

클라이언트에 복제:

- active Skill ID
- typed target의 필요한 public reference 또는 immutable snapshot
- parameter
- server start time
- animation state
- Skill terminal result

신경망 raw score와 모든 Belief는 일반 플레이 클라이언트에 복제할 필요가 없다.

## 23.3 Late Join

- active Goal 요약
- active Skill
- target presentation snapshot
- server time offset
- animation sync

클라이언트가 독립적으로 정책을 다시 결정하지 않는다.

---

# 24. 성능과 부하

## 24.1 부하 모델

```text
30 Idle NPC × 1Hz
15 Alert NPC × 3Hz
 5 Combat NPC × 5Hz
-------------------
Typical 100 decisions/sec

Burst 250 decisions/sec, 1초
Candidate 272 fixed
```

## 24.2 Gate

| Metric | Budget |
|---|---:|
| Neural batch inference p95 | ≤6ms |
| Neural batch inference p99 | ≤12ms |
| Request-to-Commit p95 | ≤20ms |
| Request-to-Commit p99 | ≤40ms |
| Typical deadline miss | <0.1% |
| Burst deadline miss | <1.0% |

Reference CPU/GPU, build, backend, precision, batch를 `perf_manifest.json`에 고정한다.

## 24.3 최적화 순서

1. Snapshot/Feature Builder profile
2. batch와 queue
3. factorized scorer
4. FP16/INT8
5. 판단 빈도 LOD
6. 필요할 때만 Candidate Retriever

Candidate Retriever를 도입할 경우 Target/Candidate Recall Gate를 별도로 통과해야 한다.

## 24.4 메모리

NPC별 주요 상태:

- Belief/Target Universe
- Event 12
- Goal stack
- Target slot 17
- Candidate mask 272 bit
- Decision request lifecycle
- active Skill
- no GRU hidden

모델과 NNE instance는 World 단위로 공유한다.

---

# 25. 테스트

## 25.1 Schema/Parity

- generated enum/static assert
- Tensor shape
- padding/mask
- Candidate index
- canonical hash bytes
- NoTarget slot
- Target payload
- Python–Unreal float tolerance
- ONNX–NNE output tolerance

Tolerance:

```text
Discrete/hash input: byte-identical
Float feature: abs ≤1e-6 or rel ≤1e-5
FP32 model output: abs ≤1e-4 or rel ≤1e-4
```

## 25.2 Belief/Hidden Information

- 숨은 Quinn Ground Truth 이동 시 Tensor 불변
- LastKnownPosition immutable
- SoundEvent immutable
- hidden Actor velocity 미사용
- LastKnown Commit에서 Actor 이동을 이유로 취소하지 않음
- Entity Attack은 현재 Perception/LOS 요구
- path/LOS는 Believed Position

## 25.3 Goal

- arbitration key
- 동점
- preemption
- suspended resume
- activation 실패 rollback
- revision 증가/비증가
- Idle→Investigate→Return
- Goal 변경 중 stale inference

## 25.4 Target Slotter

- dedupe
- mandatory order
- quota
- round-robin
- hysteresis
- canonical sort
- MandatoryOverflow
- Python reference parity
- Target Recall

## 25.5 Candidate

- 272 고정
- Skill×Target matrix
- Continue 중복 제거
- Goal mask
- Candidate Hash
- acceptable candidate recall

## 25.6 Async/Commit

- out-of-order response
- dirty request
- urgent supersede
- deadline
- target generation
- Goal revision
- contract mismatch
- partial reservation rollback
- StartCommit failure
- lease expiry
- authority rejection

## 25.7 Gameplay

1. 소리 없는 정면 접근
2. 뒤쪽 작은 발소리
3. 뒤쪽 큰 소리
4. Sight Lost
5. LastKnown TTL
6. 숨은 Quinn 이동
7. SoundEvent attribution 불확실
8. Search 후 Return
9. path failure
10. 피격 urgent
11. all masked
12. model missing
13. schema mismatch
14. 30 NPC
15. Typical/Burst

## 25.8 KPI

고정 평가 버전:

```text
utility_baseline_v1.0.0
schema 2.0.0
target_slotter 1.0.0
postprocess 1.0.0
critical_suite_v1
```

Gate:

- General Target Recall 20,000 states: point ≥99.5%, Wilson lower ≥99.0%
- Candidate Recall 동일
- Critical Suite 256 sequences: 100%
- Safety Fuzz 100,000 decisions: hard-constraint Commit 0
- Hidden Leakage 10,000 pair: 0
- ECE ≤0.05
- Brier ≤0.18
- OOD recall ≥0.90 at FPR ≤0.10
- Naturalness A/B: 600 sequence×3명, point ≥55%, CI lower >52%
- Goal completion 비열등: lower bound ≥ -2.0pp
- 불필요한 switch 비열등: upper ≤ +0.2 switch/10s
- stable scenario p95 ≤3 switch/10s

---

# 26. 단계별 구현 계획

## Phase 0 — MVP Vertical Slice, 6~8주 병렬 기준

### Stream A — Contracts, ML+Gameplay

- schema generator
- C++/Python constants
- Target Handle/Feature
- 17 Slot/272 Candidate
- Golden vectors

### Stream B — Manny/Perception, Gameplay

- Quinn stimuli/noise
- Manny Controller
- Sight/Hearing
- Belief
- LastKnownPosition

### Stream C — Goal/Skill, Gameplay+Designer

- Goal Manager
- IdleObserve/Investigate FSM
- 5 Skill
- Continue
- failure taxonomy

### Stream D — Slotter/Baseline, Gameplay+ML+Designer

- Target Universe
- mandatory/quota/hysteresis
- Candidate Builder
- Utility Baseline
- Recall Inspector

### Stream E — Inference/Commit, Engine/Gameplay

- NNE adapter
- World subsystem
- in-flight lifecycle
- Validate/StartCommit
- Phase 0에서는 Resource Kind가 mask되어 있어 예약 경로는 mock transaction으로 검증

### Phase 0 Exit

- Critical Target/Candidate Recall 100%
- Hidden Leakage 0
- Goal FSM 성공
- stale response Commit 0
- Utility fallback
- Manny 수직 슬라이스 5개 재현

## Phase 1 — V1, Phase 0 후 12~16주

- 16 Skill
- 모든 Target Kind
- Cover/SmartObject reservation
- Calibration/OOD
- 3 Role×4 Goal
- multiplayer
- Gold/DAgger
- KPI/성능 Gate

## Owner·기간·의존성

| Workstream | Owner | Phase 0 예상 | Phase 1 예상 | 선행 의존성 |
|---|---|---:|---:|---|
| Belief/Target Runtime | Gameplay AI | 2주 | 3주 | Typed Target 계약 |
| Goal Manager/FSM | Gameplay AI + AI Designer | 2주 | 3주 | Goal FSM |
| Slotter/Candidate/Hash | Gameplay AI + ML | 2주 | 2주 | Schema/Registry |
| Utility Baseline | AI Designer | 1주 | 2주 | Candidate Pipeline |
| Feature/Golden | ML + Gameplay AI | 2주 | 2주 | Schema Generator |
| Neural Model/Export | ML | 2주 | 4주 | Feature Parity |
| NNE/Commit/Reservation | Gameplay + Server | 2주 | 4주 | Skill/Target 계약 |
| Label/DAgger Tool | Tech Designer | 1주 | 4주 | Inspector/Replay |
| QA/KPI | QA + ML | 2주 | 지속 | Critical Suite |

---

# 27. 파일 단위 구현 목록

## Contracts

```text
Source/AINativeNPCContracts/Public/Generated/AINPCSchema.generated.h
Source/AINativeNPCContracts/Public/Generated/AINPCEnums.generated.h
Source/AINativeNPCContracts/Public/Generated/AINPCNormalization.generated.h
Source/AINativeNPCContracts/Public/Generated/AINPCHash.generated.h
```

## Runtime Public

```text
Characters/AINativeNPCCharacter.h
AI/AINativeNPCController.h
Perception/NPCBeliefComponent.h
Social/NPCSocialStateComponent.h
Memory/NPCEventBufferComponent.h
Goals/NPCGoalManagerComponent.h
Targets/NPCTargetTypes.h
Targets/NPCTargetUniverseComponent.h
Targets/NPCTargetSlotterComponent.h
Decision/NPCCandidateBuilderComponent.h
Decision/NPCFeatureBuilderComponent.h
Decision/NPCDecisionComponent.h
Decision/NPCPostProcessComponent.h
Decision/NPCUtilityBaselineComponent.h
Inference/NPCInferenceWorldSubsystem.h
Execution/NPCCommitCoordinatorComponent.h
Execution/NPCSkillExecutorComponent.h
Execution/NPCResourceReservationSubsystem.h
Skills/NPCSkill.h
Debug/NPCDebugComponent.h
```

## Runtime Private

```text
Perception/NPCBeliefComponent.cpp
Social/NPCSocialStateComponent.cpp
Goals/NPCGoalManagerComponent.cpp
Targets/NPCTargetUniverseComponent.cpp
Targets/NPCTargetSlotterComponent.cpp
Decision/NPCCandidateBuilderComponent.cpp
Decision/NPCFeatureBuilderComponent.cpp
Decision/NPCPostProcessComponent.cpp
Inference/NPCInferenceNNEBackend.cpp
Execution/NPCCommitCoordinatorComponent.cpp
Execution/NPCSkillExecutorComponent.cpp
Skills/NPCSkill_Idle.cpp
Skills/NPCSkill_TurnTo.cpp
Skills/NPCSkill_Approach.cpp
Skills/NPCSkill_Investigate.cpp
Skills/NPCSkill_SearchArea.cpp
```

## Editor

```text
Inspector/SNPCDecisionInspector.cpp
Replay/NPCDecisionReplayAsset.cpp
Labeling/SNPCPreferenceTool.cpp
Schema/NPCSchemaValidationCommandlet.cpp
```

## Tests

```text
Schema/NPCSchemaGoldenTest.cpp
Feature/NPCFeatureParityTest.cpp
Targets/NPCTargetSlotterTest.cpp
Decision/NPCCandidateHashTest.cpp
Goals/NPCGoalFSMTest.cpp
Execution/NPCAtomicCommitTest.cpp
Security/NPCHiddenInformationTest.cpp
Performance/NPCInferenceBenchmark.cpp
Scenarios/NPCMannyQuinnScenarioTest.cpp
```

---

# 28. Definition of Done

## 28.1 Phase 0 클라이언트

- Quinn Sight/Hearing stimulus
- Manny Sight/Hearing Belief
- Sight Lost → LastKnownPosition
- Goal Manager 2개 Goal
- Target Slot 17
- Candidate 272
- 5 Skill + Continue
- Utility Baseline
- NNE raw scorer
- dirty/urgent lifecycle
- short atomic Commit
- Inspector와 Replay
- packaged build model load

## 28.2 계약

- schema YAML에서 C++/Python/문서 생성
- discrete/hash byte-identical
- float parity tolerance
- NoTarget/padding
- Target payload
- Decision Contract Hash
- Skill Registry Hash

## 28.3 안전

- Ground Truth 누출 0
- hard-constraint Commit 0
- stale Commit 0
- reservation rollback
- server authority 우회 0

## 28.4 AI Native 목표

- “뒤에서 소리가 나면 돌아본다” 조건문 없음
- “보이면 인사한다” 조건문 없음
- Goal과 Skill 실행은 명시적
- 후보가 존재하는 상황에서 모델/Baseline이 선호를 결정
- Candidate miss와 model error를 분리해 측정

---

# 29. 주요 위험

## 위험 1 — Slotter가 숨은 BT가 됨

- 선호 점수 금지
- mandatory/quota/canonical rule만 사용
- Target Recall Gate

## 위험 2 — Python과 Unreal Feature 차이

- YAML codegen
- Golden vector
- tolerance
- generated index API

## 위험 3 — Hidden Information

- Entity/LastKnown 분리
- worker request에 Actor pointer 없음
- Commit Kind별 boundary
- leakage pair test

## 위험 4 — Goal Revision 과다 증가

- 증가 조건 표
- countdown/progress는 revision 불변
- stale rate dashboard

## 위험 5 — 비동기 race

- latest-request-only
- urgent cancellation
- decision ID
- GameThread atomic Commit

## 위험 6 — Candidate 272 성능

- factorized scorer
- fixed padded batch
- profiler
- Retriever는 Gate 후에만

## 위험 7 — Calibration drift

- calibration version
- group threshold
- OOD
- fallback rate

## 위험 8 — Animation이 판단 품질을 가림

- Skill 결과와 presentation 분리
- 기존 locomotion 재사용
- A/B에서 행동과 animation 문제 태그 분리

---

# Appendix A. Schema 상수와 Enum

## A.1 Constants

| Name | Value |
| --- | --- |
| schema_version | 2.0.0 |
| skill_registry_version | 1.0.0 |
| target_slotter_version | 1.0.0 |
| postprocess_version | 1.0.0 |
| normalization_version | 2.0.0 |
| regular_target_slots | 16 |
| no_target_slot | 16 |
| total_target_slots | 17 |
| skill_count | 16 |
| candidate_count | 272 |
| event_slots | 12 |
| global_feature_count | 128 |
| target_feature_count | 48 |
| event_feature_count | 24 |
| candidate_pair_feature_count | 16 |
| parameter_count | 4 |
| spatial_max_cm | 5000.0 |
| path_distance_max_cm | 10000.0 |
| speed_max_cm_s | 1200.0 |
| acceleration_max_cm_s2 | 4000.0 |
| yaw_rate_max_deg_s | 720.0 |
| target_age_max_s | 10.0 |
| event_age_max_s | 10.0 |
| visible_duration_max_s | 10.0 |
| skill_time_max_s | 10.0 |
| goal_phase_time_max_s | 30.0 |
| goal_deadline_max_s | 120.0 |
| count_max | 8.0 |

## A.2 Target Kind

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

## A.3 Skill

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

## A.4 Goal Type

| ID | Name |
| --- | --- |
| 0 | None |
| 1 | IdleObserve |
| 2 | InvestigateDisturbance |
| 3 | EnforceBoundary |
| 4 | CombatEngage |
| 5 | Disengage |
| 6 | Escort |
| 7 | Reserved |

## A.5 Goal Phase

| ID | Name |
| --- | --- |
| 0 | None |
| 1 | Observe |
| 2 | Orient |
| 3 | Navigate |
| 4 | Interact |
| 5 | Search |
| 6 | Resolve |
| 7 | Return |

## A.6 Event Type

| ID | Name |
| --- | --- |
| 0 | NoneOrPadding |
| 1 | SightAcquired |
| 2 | SightLost |
| 3 | SoundHeard |
| 4 | Damaged |
| 5 | SkillSucceeded |
| 6 | SkillFailed |
| 7 | SkillInterrupted |
| 8 | WarningIssued |
| 9 | WarningIgnored |
| 10 | TargetMovedSignificantly |
| 11 | TargetInvalidated |
| 12 | GoalChanged |
| 13 | ReservationLost |
| 14 | SharedKnowledgeReceived |
| 15 | Other |

## A.7 Goal Source Priority

| ID | Name |
| --- | --- |
| 0 | Routine |
| 1 | Social |
| 2 | Combat |
| 3 | Quest |
| 4 | Emergency |

---

# Appendix B. Tensor Field Snapshot

> 이 Appendix는 `ai_native_npc_schema_v2_0.yaml`에서 생성한 스냅샷이다. 수동 편집하지 않는다.

## B.1 global_state [128]

| Index | Field | Source | Unit | Normalization | Range |
| --- | --- | --- | --- | --- | --- |
| 0 | self_health_norm | self authoritative health ratio | ratio | clamp(x,0,1) | [0,1] |
| 1 | self_stamina_norm | self authoritative stamina ratio | ratio | clamp(x,0,1) | [0,1] |
| 2 | self_speed_norm | self speed | cm/s | clamp(x/1200,0,1) | [0,1] |
| 3 | self_local_velocity_x | self velocity in NPC-local frame | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 4 | self_local_velocity_y | self velocity in NPC-local frame | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 5 | self_local_velocity_z | self velocity in NPC-local frame | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 6 | self_local_acceleration_x | self acceleration in NPC-local frame | cm/s² | clamp(x/4000,-1,1) | [-1,1] |
| 7 | self_local_acceleration_y | self acceleration in NPC-local frame | cm/s² | clamp(x/4000,-1,1) | [-1,1] |
| 8 | self_local_acceleration_z | self acceleration in NPC-local frame | cm/s² | clamp(x/4000,-1,1) | [-1,1] |
| 9 | self_yaw_rate_norm | self yaw angular speed | deg/s | clamp(x/720,-1,1) | [-1,1] |
| 10 | self_grounded | self movement state | bool | 0 or 1 | [0,1] |
| 11 | self_crouched | self movement state | bool | 0 or 1 | [0,1] |
| 12 | self_sprinting | self movement state | bool | 0 or 1 | [0,1] |
| 13 | self_in_combat | authoritative self combat state | bool | 0 or 1 | [0,1] |
| 14 | self_damaged_recently | damage event within 3 seconds | bool | 0 or 1 | [0,1] |
| 15 | self_recent_damage_norm | damage received in 3-second window / max health | ratio | clamp(x,0,1) | [0,1] |
| 16 | current_skill_Idle | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 17 | current_skill_ContinueCurrentAction | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 18 | current_skill_LookAt | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 19 | current_skill_TurnTo | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 20 | current_skill_Approach | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 21 | current_skill_KeepDistance | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 22 | current_skill_RetreatFrom | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 23 | current_skill_Follow | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 24 | current_skill_Investigate | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 25 | current_skill_SearchArea | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 26 | current_skill_Greet | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 27 | current_skill_Warn | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 28 | current_skill_CallForHelp | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 29 | current_skill_TakeCover | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 30 | current_skill_Flee | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 31 | current_skill_Attack | current skill one-hot | one-hot | 0 or 1 | [0,1] |
| 32 | skill_elapsed_norm | elapsed time in current skill | s | clamp(x/10,0,1) | [0,1] |
| 33 | skill_progress_norm | skill-defined progress | ratio | clamp(x,0,1) | [0,1] |
| 34 | skill_min_duration_remaining_norm | remaining minimum hold time | s | clamp(x/10,0,1) | [0,1] |
| 35 | skill_interruptible_now | current skill may be interrupted | bool | 0 or 1 | [0,1] |
| 36 | skill_has_target | current skill has typed target | bool | 0 or 1 | [0,1] |
| 37 | skill_target_still_believed_valid | current target remains valid in Belief | bool | 0 or 1 | [0,1] |
| 38 | last_skill_result_success | last terminal result | bool | 0 or 1 | [0,1] |
| 39 | last_skill_result_failure | last terminal result | bool | 0 or 1 | [0,1] |
| 40 | personality_aggression | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 41 | personality_courage | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 42 | personality_curiosity | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 43 | personality_loyalty | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 44 | personality_sociability | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 45 | personality_impulsivity | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 46 | personality_patience | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 47 | personality_vigilance | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 48 | personality_altruism | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 49 | personality_rule_adherence | NPC profile | ratio | clamp(x,-1,1) | [-1,1] |
| 50 | emotion_fear | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 51 | emotion_anger | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 52 | emotion_suspicion | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 53 | emotion_curiosity | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 54 | emotion_tension | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 55 | emotion_affection | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 56 | emotion_confusion | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 57 | emotion_confidence | authoritative event-driven state, read-only to policy | ratio | clamp(x,0,1) | [0,1] |
| 58 | relationship_affinity | relationship to primary social subject | ratio | clamp(x,-1,1) | [-1,1] |
| 59 | relationship_trust | relationship to primary social subject | ratio | clamp(x,-1,1) | [-1,1] |
| 60 | relationship_respect | relationship to primary social subject | ratio | clamp(x,-1,1) | [-1,1] |
| 61 | relationship_fear | relationship to primary social subject | ratio | clamp(x,0,1) | [0,1] |
| 62 | relationship_debt | relationship to primary social subject | ratio | clamp(x,-1,1) | [-1,1] |
| 63 | relationship_suspicion | relationship to primary social subject | ratio | clamp(x,0,1) | [0,1] |
| 64 | relationship_loyalty | relationship to primary social subject | ratio | clamp(x,-1,1) | [-1,1] |
| 65 | relationship_hostility | relationship to primary social subject | ratio | clamp(x,0,1) | [0,1] |
| 66 | role_combatant | role attribute, not unseen Role ID | ratio | clamp(x,0,1) | [0,1] |
| 67 | role_guard | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 68 | role_civilian | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 69 | role_companion | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 70 | role_support | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 71 | role_authority_level | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 72 | role_social_authority | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 73 | role_territory_ownership | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 74 | role_mission_importance | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 75 | role_risk_tolerance | role attribute | ratio | clamp(x,0,1) | [0,1] |
| 76 | goal_type_None | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 77 | goal_type_IdleObserve | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 78 | goal_type_InvestigateDisturbance | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 79 | goal_type_EnforceBoundary | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 80 | goal_type_CombatEngage | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 81 | goal_type_Disengage | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 82 | goal_type_Escort | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 83 | goal_type_Reserved | active goal type one-hot | one-hot | 0 or 1 | [0,1] |
| 84 | goal_phase_None | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 85 | goal_phase_Observe | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 86 | goal_phase_Orient | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 87 | goal_phase_Navigate | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 88 | goal_phase_Interact | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 89 | goal_phase_Search | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 90 | goal_phase_Resolve | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 91 | goal_phase_Return | active goal phase one-hot | one-hot | 0 or 1 | [0,1] |
| 92 | goal_priority_norm | active goal priority uint8 / 255 | ratio | clamp(x/255,0,1) | [0,1] |
| 93 | goal_time_in_phase_norm | time since phase entry | s | clamp(x/30,0,1) | [0,1] |
| 94 | goal_deadline_remaining_norm | remaining authoritative deadline; 1 when no deadline | s | no deadline=1; else clamp(x/120,0,1) | [0,1] |
| 95 | goal_progress_norm | goal-defined non-revision progress | ratio | clamp(x,0,1) | [0,1] |
| 96 | goal_interruptible | active phase interruptibility permits ordinary preemption | bool | 0 or 1 | [0,1] |
| 97 | goal_has_primary_target | active goal owns a typed target | bool | 0 or 1 | [0,1] |
| 98 | allowed_skill_fraction | allowed skill count / 16 | ratio | clamp(x/16,0,1) | [0,1] |
| 99 | forbidden_skill_fraction | forbidden skill count / 16 | ratio | clamp(x/16,0,1) | [0,1] |
| 100 | world_safe_zone | authoritative zone flag | bool | 0 or 1 | [0,1] |
| 101 | world_restricted_zone | authoritative zone flag | bool | 0 or 1 | [0,1] |
| 102 | world_indoors | environment flag | bool | 0 or 1 | [0,1] |
| 103 | world_combat_allowed | authoritative rule flag | bool | 0 or 1 | [0,1] |
| 104 | world_perceived_ally_count_norm | count from Belief | count | clamp(x/8,0,1) | [0,1] |
| 105 | world_perceived_hostile_count_norm | count from Belief | count | clamp(x/8,0,1) | [0,1] |
| 106 | world_light_level_norm | environment sample available to NPC | ratio | clamp(x,0,1) | [0,1] |
| 107 | world_crowd_density_norm | perceived local density | ratio | clamp(x,0,1) | [0,1] |
| 108 | recent_sound_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 109 | recent_sight_change_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 110 | recent_damage_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 111 | recent_skill_failure_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 112 | recent_target_switch_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 113 | recent_warning_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 114 | recent_reservation_conflict_count_norm | valid events in 10-second buffer | count | clamp(x/8,0,1) | [0,1] |
| 115 | event_buffer_fill_ratio | valid event slots / 12 | ratio | clamp(x/12,0,1) | [0,1] |
| 116 | reserved_116 | reserved; must be zero | none | 0 | {0} |
| 117 | reserved_117 | reserved; must be zero | none | 0 | {0} |
| 118 | reserved_118 | reserved; must be zero | none | 0 | {0} |
| 119 | reserved_119 | reserved; must be zero | none | 0 | {0} |
| 120 | reserved_120 | reserved; must be zero | none | 0 | {0} |
| 121 | reserved_121 | reserved; must be zero | none | 0 | {0} |
| 122 | reserved_122 | reserved; must be zero | none | 0 | {0} |
| 123 | reserved_123 | reserved; must be zero | none | 0 | {0} |
| 124 | reserved_124 | reserved; must be zero | none | 0 | {0} |
| 125 | reserved_125 | reserved; must be zero | none | 0 | {0} |
| 126 | reserved_126 | reserved; must be zero | none | 0 | {0} |
| 127 | reserved_127 | reserved; must be zero | none | 0 | {0} |

## B.2 target_features common [0:31]

| Index | Field | Source | Unit | Normalization | Range |
| --- | --- | --- | --- | --- | --- |
| 0 | relative_position_x | perceived target position in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 1 | relative_position_y | perceived target position in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 2 | relative_position_z | perceived target position in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 3 | distance_3d_norm | distance to perceived position | cm | clamp(x/5000,0,1) | [0,1] |
| 4 | distance_planar_norm | planar distance to perceived position | cm | clamp(x/5000,0,1) | [0,1] |
| 5 | log_distance_norm | log distance | cm | log1p(clamp(x,0,5000))/log1p(5000) | [0,1] |
| 6 | bearing_sin | NPC-local bearing | rad | sin(x) | [-1,1] |
| 7 | bearing_cos | NPC-local bearing | rad | cos(x) | [-1,1] |
| 8 | elevation_sin | NPC-local elevation | rad | sin(x) | [-1,1] |
| 9 | elevation_cos | NPC-local elevation | rad | cos(x) | [-1,1] |
| 10 | relative_velocity_x | belief-derived velocity, never hidden Actor velocity | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 11 | relative_velocity_y | belief-derived velocity, never hidden Actor velocity | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 12 | relative_velocity_z | belief-derived velocity, never hidden Actor velocity | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 13 | closing_speed_norm | positive means approaching | cm/s | clamp(x/1200,-1,1) | [-1,1] |
| 14 | path_distance_norm | navigation estimate to believed position | cm | invalid=0; else clamp(x/10000,0,1) | [0,1] |
| 15 | path_reachable_belief | path query to believed snapshot position | bool | 0 or 1 | [0,1] |
| 16 | belief_age_norm | now - observed_at | s | clamp(x/10,0,1) | [0,1] |
| 17 | belief_confidence | position/state confidence | ratio | clamp(x,0,1) | [0,1] |
| 18 | source_sight | Belief source one-hot | one-hot | 0 or 1 | [0,1] |
| 19 | source_hearing | Belief source one-hot | one-hot | 0 or 1 | [0,1] |
| 20 | source_last_known | Belief source one-hot | one-hot | 0 or 1 | [0,1] |
| 21 | source_shared | Belief source one-hot | one-hot | 0 or 1 | [0,1] |
| 22 | source_scripted | Belief source one-hot | one-hot | 0 or 1 | [0,1] |
| 23 | position_valid | perceived/snapshot position is valid | bool | 0 or 1 | [0,1] |
| 24 | visible_now | currently perceived by sight | bool | 0 or 1 | [0,1] |
| 25 | line_of_sight_belief | LOS query against believed/currently perceived target | bool | 0 or 1 | [0,1] |
| 26 | sight_strength | sensor strength | ratio | clamp(x,0,1) | [0,1] |
| 27 | visible_duration_norm | continuous visibility duration | s | clamp(x/10,0,1) | [0,1] |
| 28 | heard_recently | valid hearing event associated with target | bool | 0 or 1 | [0,1] |
| 29 | hearing_strength | normalized loudness/strength | ratio | clamp(x,0,1) | [0,1] |
| 30 | time_since_seen_norm | time since last sight; 1 if never | s | never=1; else clamp(x/10,0,1) | [0,1] |
| 31 | time_since_heard_norm | time since last hearing; 1 if never | s | never=1; else clamp(x/10,0,1) | [0,1] |

## B.3 event_features [24]

| Index | Field | Source | Unit | Normalization | Range |
| --- | --- | --- | --- | --- | --- |
| 0 | age_norm | now - event time | s | clamp(x/10,0,1) | [0,1] |
| 1 | strength | event strength | ratio | clamp(x,0,1) | [0,1] |
| 2 | confidence | event confidence | ratio | clamp(x,0,1) | [0,1] |
| 3 | relative_position_x | event snapshot in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 4 | relative_position_y | event snapshot in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 5 | relative_position_z | event snapshot in NPC-local frame | cm | clamp(x/5000,-1,1) | [-1,1] |
| 6 | distance_norm | distance to event snapshot | cm | clamp(x/5000,0,1) | [0,1] |
| 7 | bearing_sin | event bearing | rad | sin(x) | [-1,1] |
| 8 | bearing_cos | event bearing | rad | cos(x) | [-1,1] |
| 9 | source_sight | event source one-hot | one-hot | 0 or 1 | [0,1] |
| 10 | source_hearing | event source one-hot | one-hot | 0 or 1 | [0,1] |
| 11 | source_damage | event source one-hot | one-hot | 0 or 1 | [0,1] |
| 12 | source_scripted | event source one-hot | one-hot | 0 or 1 | [0,1] |
| 13 | result_success | skill result one-hot | one-hot | 0 or 1 | [0,1] |
| 14 | result_failure | skill result one-hot | one-hot | 0 or 1 | [0,1] |
| 15 | result_interrupted | skill result one-hot | one-hot | 0 or 1 | [0,1] |
| 16 | urgent | event urgency | bool | 0 or 1 | [0,1] |
| 17 | target_present_in_current_slots | stable handle remapped to current slot | bool | 0 or 1 | [0,1] |
| 18 | same_as_current_skill_target | handle equality | bool | 0 or 1 | [0,1] |
| 19 | same_goal_revision | event goal revision equals current | bool | 0 or 1 | [0,1] |
| 20 | magnitude_norm | event-specific magnitude | ratio | clamp(x,0,1) | [0,1] |
| 21 | duration_norm | event-specific duration | s | clamp(x/10,0,1) | [0,1] |
| 22 | reserved_22 | must be zero | none | 0 | {0} |
| 23 | reserved_23 | must be zero | none | 0 | {0} |

## B.4 candidate_pair_features [16]

| Index | Field | Source | Unit | Normalization | Range |
| --- | --- | --- | --- | --- | --- |
| 0 | same_as_current_skill | candidate skill equals running skill | bool | 0 or 1 | [0,1] |
| 1 | same_as_current_target | typed handle equals running target | bool | 0 or 1 | [0,1] |
| 2 | target_present | target slot is valid; NoTarget is valid | bool | 0 or 1 | [0,1] |
| 3 | target_visible_now | copied from target belief | bool | 0 or 1 | [0,1] |
| 4 | target_position_confidence | copied from target belief | ratio | clamp(x,0,1) | [0,1] |
| 5 | target_age_norm | copied from target belief | s | clamp(x/10,0,1) | [0,1] |
| 6 | distance_norm | copied from target feature | ratio | clamp(x,0,1) | [0,1] |
| 7 | path_distance_norm | computed to believed snapshot | ratio | clamp(x,0,1) | [0,1] |
| 8 | path_reachable_belief | computed to believed snapshot | bool | 0 or 1 | [0,1] |
| 9 | skill_requires_los | Skill Registry metadata | bool | 0 or 1 | [0,1] |
| 10 | los_satisfied_belief | computed against currently permitted belief | bool | 0 or 1 | [0,1] |
| 11 | skill_requires_resource | Skill Registry metadata | bool | 0 or 1 | [0,1] |
| 12 | resource_available_belief | latest allowed availability snapshot | bool | 0 or 1 | [0,1] |
| 13 | skill_allowed_by_goal | Goal contract | bool | 0 or 1 | [0,1] |
| 14 | target_kind_allowed | Skill Registry matrix | bool | 0 or 1 | [0,1] |
| 15 | default_parameter_norm | Skill Registry default primary parameter | ratio | clamp(x,0,1) | [0,1] |

---

# Appendix C. Target Kind Payload [32:47]

> Stable ID와 Runtime Handle은 포함되지 않는다.

## C.1 NoTarget

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | zero_0 | must be zero |
| 33 | 1 | zero_1 | must be zero |
| 34 | 2 | zero_2 | must be zero |
| 35 | 3 | zero_3 | must be zero |
| 36 | 4 | zero_4 | must be zero |
| 37 | 5 | zero_5 | must be zero |
| 38 | 6 | zero_6 | must be zero |
| 39 | 7 | zero_7 | must be zero |
| 40 | 8 | zero_8 | must be zero |
| 41 | 9 | zero_9 | must be zero |
| 42 | 10 | zero_10 | must be zero |
| 43 | 11 | zero_11 | must be zero |
| 44 | 12 | zero_12 | must be zero |
| 45 | 13 | zero_13 | must be zero |
| 46 | 14 | zero_14 | must be zero |
| 47 | 15 | zero_15 | must be zero |

## C.2 Entity

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | alive_probability | Belief estimate |
| 33 | 1 | armed_probability | Belief estimate |
| 34 | 2 | attacking_probability | Belief estimate |
| 35 | 3 | health_estimate | Belief estimate |
| 36 | 4 | health_uncertainty | estimate interval width |
| 37 | 5 | threat_estimate | perception/classifier estimate |
| 38 | 6 | interactable | observed/known affordance |
| 39 | 7 | same_faction_probability | Belief estimate |
| 40 | 8 | affinity | relationship [-1,1] |
| 41 | 9 | trust | relationship [-1,1] |
| 42 | 10 | fear | relationship [0,1] |
| 43 | 11 | hostility | relationship [0,1] |
| 44 | 12 | debt | relationship [-1,1] |
| 45 | 13 | suspicion | relationship [0,1] |
| 46 | 14 | current_action_confidence | observed action classifier confidence |
| 47 | 15 | identity_confidence | entity attribution confidence |

## C.3 SoundEvent

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | loudness | normalized loudness |
| 33 | 1 | danger_estimate | sensor/event semantic estimate |
| 34 | 2 | attribution_confidence | confidence in source attribution |
| 35 | 3 | repetition_norm | repeat count / 8 |
| 36 | 4 | class_footstep | sound class one-hot |
| 37 | 5 | class_weapon | sound class one-hot |
| 38 | 6 | class_explosion | sound class one-hot |
| 39 | 7 | class_voice | sound class one-hot |
| 40 | 8 | class_impact | sound class one-hot |
| 41 | 9 | class_door | sound class one-hot |
| 42 | 10 | class_vehicle | sound class one-hot |
| 43 | 11 | class_other | sound class one-hot |
| 44 | 12 | source_moving_probability | event inference |
| 45 | 13 | occluded_probability | hearing propagation estimate |
| 46 | 14 | ttl_remaining_norm | remaining TTL / event max TTL |
| 47 | 15 | reserved | must be zero |

## C.4 LastKnownPosition

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | subject_is_player | Belief semantic flag |
| 33 | 1 | subject_hostile_probability | snapshot belief |
| 34 | 2 | subject_armed_probability | snapshot belief |
| 35 | 3 | subject_alive_probability_at_observation | snapshot belief; not updated from hidden truth |
| 36 | 4 | motion_direction_sin | last observed motion |
| 37 | 5 | motion_direction_cos | last observed motion |
| 38 | 6 | observed_speed_norm | last observed speed / 1200 |
| 39 | 7 | reason_sight_lost | snapshot reason one-hot |
| 40 | 8 | reason_shared | snapshot reason one-hot |
| 41 | 9 | reason_scripted | snapshot reason one-hot |
| 42 | 10 | goal_primary_target | owned by active goal |
| 43 | 11 | search_radius_norm | search radius / 5000 |
| 44 | 12 | confidence_decay_rate_norm | configured decay rate |
| 45 | 13 | ttl_remaining_norm | remaining snapshot TTL |
| 46 | 14 | subject_identity_confidence | snapshot attribution confidence |
| 47 | 15 | reserved | must be zero |

## C.5 CoverSlot

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | cover_quality | [0,1] |
| 33 | 1 | exposure_reduction | [0,1] |
| 34 | 2 | flank_risk | [0,1] |
| 35 | 3 | distance_to_peek_norm | cm / 5000 |
| 36 | 4 | occupancy_ratio | [0,1] |
| 37 | 5 | available_belief | latest known availability |
| 38 | 6 | reserved_by_self | 0 or 1 |
| 39 | 7 | resource_generation_valid | 0 or 1 |
| 40 | 8 | low_cover | one-hot/flag |
| 41 | 9 | high_cover | one-hot/flag |
| 42 | 10 | left_peek | 0 or 1 |
| 43 | 11 | right_peek | 0 or 1 |
| 44 | 12 | destructible_probability | [0,1] |
| 45 | 13 | hazard_norm | [0,1] |
| 46 | 14 | lease_required | 0 or 1 |
| 47 | 15 | resource_age_norm | availability revision age / 10s |

## C.6 SmartObject

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | availability_belief | [0,1] |
| 33 | 1 | capacity_norm | capacity / configured max |
| 34 | 2 | occupancy_ratio | [0,1] |
| 35 | 3 | interaction_duration_norm | seconds / 30 |
| 36 | 4 | requires_item | 0 or 1 |
| 37 | 5 | hazard_norm | [0,1] |
| 38 | 6 | use_type_door | one-hot |
| 39 | 7 | use_type_console | one-hot |
| 40 | 8 | use_type_pickup | one-hot |
| 41 | 9 | use_type_heal | one-hot |
| 42 | 10 | use_type_vehicle | one-hot |
| 43 | 11 | use_type_social | one-hot |
| 44 | 12 | use_type_traversal | one-hot |
| 45 | 13 | use_type_other | one-hot |
| 46 | 14 | resource_generation_valid | 0 or 1 |
| 47 | 15 | resource_age_norm | availability revision age / 10s |

## C.7 Waypoint

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | goal_primary | 0 or 1 |
| 33 | 1 | goal_secondary | 0 or 1 |
| 34 | 2 | sequence_progress | [0,1] |
| 35 | 3 | wait_duration_norm | seconds / 30 |
| 36 | 4 | desired_facing_sin | [-1,1] |
| 37 | 5 | desired_facing_cos | [-1,1] |
| 38 | 6 | patrol_waypoint | semantic flag |
| 39 | 7 | return_point | semantic flag |
| 40 | 8 | search_point | semantic flag |
| 41 | 9 | escape_point | semantic flag |
| 42 | 10 | formation_point | semantic flag |
| 43 | 11 | scripted_point | semantic flag |
| 44 | 12 | path_index_norm | index / configured max |
| 45 | 13 | loop_flag | 0 or 1 |
| 46 | 14 | arrival_radius_norm | cm / 5000 |
| 47 | 15 | reserved | must be zero |

## C.8 WorldPosition

| Tensor Index | Payload Index | Field | Meaning |
| --- | --- | --- | --- |
| 32 | 0 | goal_primary | 0 or 1 |
| 33 | 1 | goal_secondary | 0 or 1 |
| 34 | 2 | safe_zone_probability | [0,1] |
| 35 | 3 | hazard_norm | [0,1] |
| 36 | 4 | search_radius_norm | cm / 5000 |
| 37 | 5 | arrival_radius_norm | cm / 5000 |
| 38 | 6 | desired_facing_sin | [-1,1] |
| 39 | 7 | desired_facing_cos | [-1,1] |
| 40 | 8 | source_goal | one-hot |
| 41 | 9 | source_script | one-hot |
| 42 | 10 | source_shared_knowledge | one-hot |
| 43 | 11 | source_player_ping | one-hot |
| 44 | 12 | immutable_flag | must be 1 in V1 |
| 45 | 13 | ttl_remaining_norm | remaining TTL / configured max |
| 46 | 14 | authority_valid | 0 or 1 |
| 47 | 15 | reserved | must be zero |

---

# Appendix D. Hash와 Parity

## D.1 Candidate Set Hash

- SHA-256
- float 제외
- Target Handle 17개
- Candidate Mask 272 bit, LSB-first
- little-endian

Target Handle bytes:

```text
kind uint8
stable_id uint64 LE
generation uint32 LE
revision uint64 LE
```

## D.2 Decision Contract Hash

```text
schema hash
model hash
normalization hash
skill registry hash
target slotter version
postprocess hash
calibration/OOD hash
```

## D.3 Parity

```text
Enum/Mask/Padding/Hash input: byte-identical
Float Feature: abs 1e-6 또는 rel 1e-5
FP32 Model output: abs 1e-4 또는 rel 1e-4
```

Raw float는 Candidate Hash에 넣지 않는다.

---

# Appendix E. 승인 체크리스트

## Schema Freeze

- [ ] YAML validation
- [ ] C++/Python generated code
- [ ] Enum/Mask/Padding byte parity
- [ ] 17 Slot/272 Candidate parity
- [ ] Float Feature parity
- [ ] NNE output parity
- [ ] Candidate Set Hash parity
- [ ] Decision Contract Hash
- [ ] Target Kind payload 구현
- [ ] Skill Registry matrix 구현

## Phase 0

- [ ] Manny/Quinn 수직 슬라이스
- [ ] Belief/Ground Truth 분리
- [ ] Goal FSM
- [ ] Target Recall Critical 100%
- [ ] Candidate Recall Critical 100%
- [ ] stale Commit 0
- [ ] Hidden Leakage 0
- [ ] Utility fallback
- [ ] packaged build

## Phase 1

- [ ] all Target Kind
- [ ] 16 Skill
- [ ] Reservation
- [ ] Calibration/OOD
- [ ] multiplayer
- [ ] Gold/DAgger
- [ ] Safety/KPI/Latency Gate
