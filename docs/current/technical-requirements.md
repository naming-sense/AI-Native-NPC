# AI Native NPC 세부 기술 요구사항
## Runtime·데이터·안전의 정확한 구현 계약

- 문서 버전: **v0.4.13**
- 개정일: 2026-08-10
- 적용 범위: **Unreal 클라이언트, 서버 Gameplay AI, Python 학습·평가 코드**
- 현재 요약: **Knowledge는 NPC가 관측하거나 전달받아 보관하는 정보이며 현재 코드 이름은 `Belief`다. Boss Pattern Commit→StateTree start handoff phase는 PASS. Goal Registry `1.1.0`과 consumer provenance sync는 PASS지만 Contract Dispatcher·Timer Core는 RED 테스트 단계이고, production Knowledge·Goal·Target의 종류와 식별 정보·guard/effect provider·전체 gameplay FSM·ML/NNE·최종 Freeze는 보류**
- 기계 판독 계약: **Schema 2.0.0 RC5 + Goal Registry 1.1.0**
- 쉬운 요구사항: [초보자용 제품 요구사항](requirements.md)
- 구현 계획: [AI Native NPC 구현 계획](implementation-plan.md)
- 계약 부록: [AI Native NPC Contract Appendices](contract-appendices.md)
- Unreal 구현 계획: [UE 5.7 Manny·Quinn 구현 계획](unreal-implementation-plan.md)
- 검증·개정 이력: [Requirements History](../history/README.md)
- 상세 검토: [Requirements Review](../history/reviews/requirements-review-v0.4.6.md)

이 문서는 구현자가 따라야 하는 세부 동작, 권한 경계, Runtime 입출력, 안전, 데이터·평가 규칙을 보존한다. 처음 읽는 사람은 `requirements.md`부터 읽는다. 정확한 ID·크기·transition은 기계 판독 계약이, 세부 Runtime 의미는 이 문서가, 제품 수준의 목적과 책임은 쉬운 요구사항이 소유한다.

독자용 이름은 **`Knowledge`**와 **“Target의 종류와 식별 정보”**다. 코드·Schema·API에서는 각각 기존 식별자 `Belief`와 `Typed Target`을 그대로 사용한다.

---

# 0. 문서 안내

## 0.1 시스템 정의

AI Native NPC는 **NPC가 현재 알고 있는 정보만으로 장기 목표 안에서 다음 행동과 대상을 고르고, 서버가 그 선택을 다시 검증한 뒤 실행하는 의사결정 시스템**이다.

신경망은 실행 가능한 행동 후보의 순위를 매긴다.

## 0.2 현재 상태

| 항목 | 현재 상태 | 지금 할 수 있는 일 |
|---|---|---|
| Schema·Registry·Generated contract | Schema 2.0 RC5와 Goal Registry `1.1.0`; transition `41 = 35 event + 6 timer`, Python↔C++ Golden·consumer sync PASS | generated binding을 고정 입력으로 사용 |
| Goal Contract Dispatcher·Timer Core | `GoalFsmRuntimeTests.cpp` RED 테스트만 존재; Runtime `.h/.cpp`와 server timer component 없음 | generated row 소비·timer lifecycle TDD만 진행 가능 |
| Gameplay Goal FSM·공통 NPC Runtime | Knowledge·Goal producer·17 Target Slot·272 Candidate·Skill Executor·29 guard·2 effect provider 미구현 | production integration과 전체 arbitration/save archive는 HOLD |
| Boss Pattern 선택 안전 Core | C++ Core는 one-shot Handoff까지 구현, Automation 31/31; Definition JCS/cooked parity pending | 모델 없이 Utility 경로와 Commit/Handoff Core 검증 |
| Boss Pattern 실제 실행 | C++ Phase Executor·event/Session/Host adapter·production StateTree asset·encounter Blueprint physical assembly·fixture-backed Commit/start handoff PASS; concrete gameplay authority provider·전투 효과 미구현 | production Pawn 자동 possession, Session ready, Commit 뒤 `PreAttackTurn` Task 진입과 start-failure fail-closed terminalization 검증 |
| RC5 2-output Neural 연결 | NNE/ONNX asset·adapter 없음 | generated I/O 계약과 raw-output canonicalization만 사용 가능 |
| V1 Neural·OOD·Calibration | 구현 계약 보강 중 | 후속 Schema/Registry/Generator patch 전 품질 승격 금지 |
| 대량 학습 데이터와 최종 Freeze | 준비되지 않음 | Runtime Gate와 Dataset Validator가 닫힐 때까지 보류 |

Goal 계약의 정적 PASS는 Runtime PASS가 아니다. `GoalFsmRuntimeTests.cpp`는 구현이 없어 compile RED를 의도한 테스트이며, 제한 Core도 아직 PASS가 아니다. Boss Pattern의 `31/31`은 선택 안전 Core, `2/2`·`53/53`은 fixture-backed encounter Host/start handoff phase 증거다. 어느 숫자도 공통 NPC Runtime, 실제 공격 효과, NNE/ONNX parity, 품질·성능 완료를 뜻하지 않는다.

## 0.3 문서 범위

이 문서는 Unreal, 서버 Gameplay AI, Python 학습 코드의 공통 계약을 정한다.

- NPC가 사용할 수 있는 정보
- Goal·Skill·Target의 소유권
- Target과 Candidate 표현
- 신경망 입출력
- stale·invalid 응답 처리
- Python↔Unreal parity
- 데이터·학습·평가·승격 기준

Unreal class 구성과 작업 순서:

`docs/current/unreal-implementation-plan.md`

## 0.4 읽는 순서

### 실제 장 번호 목차

0. [문서 안내](#0-문서-안내)
1. [시스템 구조](#1-시스템-구조)
2. [Target의 종류와 식별 정보 (기술명: Typed Target)](#2-typed-target)
3. [Target Universe와 Slotter](#3-target-universe와-slotter)
4. [Candidate Universe](#4-candidate-universe)
5. [Goal Manager](#5-goal-manager)
6. [Neural Policy와 Post-process](#6-neural-policy와-post-process)
7. [비동기 추론과 Atomic Commit](#7-비동기-추론과-atomic-commit)
8. [Hidden Information 경계](#8-hidden-information-경계)
9. [데이터·학습·Baseline](#9-데이터학습baseline)
10. [Schema Generator와 Parity](#10-schema-generator와-parity)
11. [구현·승인 문서](#11-구현승인-문서)

관련 문서: [생성 계약표와 승인 기준](contract-appendices.md)

| 독자 | 먼저 읽을 곳 | 정확한 값·승인 기준 |
|---|---|---|
| 기획·Gameplay Designer | [시스템 구조](#1-시스템-구조), [Goal Manager](#5-goal-manager) | [Appendix E](contract-appendices.md#appendix-e-품질안전성능-승인-기준) |
| Gameplay AI·Server | [Goal](#5-goal-manager), [Target](#2-typed-target), [Candidate](#4-candidate-universe), [Commit](#7-비동기-추론과-atomic-commit) | [Appendix A–D](contract-appendices.md#appendix-ad-auto-generated-schemaregistry-계약) |
| ML·Data | [Policy](#6-neural-policy와-post-process), [데이터·학습](#9-데이터학습baseline) | [Appendix B](contract-appendices.md#b-tensor-계약)·[Appendix E](contract-appendices.md#appendix-e-품질안전성능-승인-기준) |
| Unreal NNE | [Policy](#6-neural-policy와-post-process), [Commit](#7-비동기-추론과-atomic-commit) | [UE 구현 계획](unreal-implementation-plan.md) |
| QA·승인자 | [현재 상태](#02-현재-상태), [Hidden Information](#8-hidden-information-경계), [Parity](#10-schema-generator와-parity) | [Appendix E](contract-appendices.md#appendix-e-품질안전성능-승인-기준), [최종 승인](implementation-plan.md#8-최종-승인) |

이 문서는 구현 의존성 때문에 Target 형식부터 정의한다. 제품 흐름을 이해하려면 [쉬운 요구사항](requirements.md)의 Goal→Knowledge→Target→Candidate→Commit 순서로 읽는다.

## 0.5 규칙의 소유자와 집행 위치

| 규칙 | 주 독자 | 적용 단계 | 실제 집행 위치 |
|---|---|---|---|
| Tensor·ONNX·OOD | ML·Unreal NNE | Export, Import, NNE 실행 | Schema, Bundle Validator, UE descriptor validation, parity test |
| Dataset·Switch Cost | Data·ML | Capture, Validation, Train/Evaluate | Dataset schema, Validator, loss/evaluation code |
| Goal·Trigger | Gameplay AI·Server | Goal Manager, Save/Load | Goal Registry, generated FSM, Runtime test |
| Snapshot·Commit | Gameplay AI·Server | 비동기 응답 처리, GameThread 실행 | Commit Coordinator, stale/rollback test |
| KPI·승격 | QA·ML·승인자 | General/OOD/Critical 평가 | Taxonomy, case catalog, release report, formal approval |

기계 판독 원본:

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
contracts/current/test_taxonomy_v1.yaml
```

계약 완료 조건은 구조화된 원본, 생성 코드, Runtime 집행, 검증 증거의 동시 갱신이다. `archive/`는 감사 기록이다.

## 0.6 계약 상태 표시

| 표시 | 의미 | 구현 기준 |
|---|---|---|
| `ACTIVE RC5` | 현재 YAML·generated code·Appendix에 존재 | 현재 구현 가능 |
| `POST-RC5` | 다음 Schema/Registry/Generator patch의 목표 | Backlog와 Gate가 닫힐 때까지 구현·승격 보류 |
| `PENDING EVIDENCE` | 계약은 있으나 Runtime·품질 증거가 없음 | PASS·Freeze 주장 금지 |

현재 정확한 ID·Tensor·Hash는 [Contract Appendices](contract-appendices.md)가 제공한다. 본문의 `POST-RC5` 절은 목표 계약과 차단 조건을 함께 표시한다.

---

# 1. 시스템 구조

## 1.1 목표

`목표 × 행동 × 대상 × 상황` 조합에 따른 조건문 증가를 줄인다.

- **게임 로직**은 NPC의 장기 Goal, 실행 가능한 Skill, 안전 조건과 월드 변경 권한을 가진다.
- **Utility Baseline·Neural Policy**는 실행 가능한 후보의 순위를 매긴다.
- **Commit Coordinator**는 선택 결과를 최신 상태로 검증하고 실행한다.

## 1.2 Runtime에서 한 번의 의사결정이 흐르는 순서

```text
Authoritative World
    └─ 실제 Actor, 피해, 퀘스트, 자원 상태
         ↓
Perception → Knowledge Runtime (코드: `Belief`)
    └─ 이 NPC가 실제로 알 수 있는 정보만 보관
         ↓
Goal Manager
    └─ 지금 달성하려는 목표와 현재 phase 결정
         ↓
Target의 종류와 식별 정보 통합 (코드: `Typed Target Universe`) → Target Slotter
    └─ Entity, 소리, 엄폐물, 위치 등을 공통 Target으로 만들고 17 slot에 배치
         ↓
Candidate Builder
    └─ Skill 16개 × Target slot 17개 = 272개 후보와 실행 가능 mask 생성
         ↓
Feature Builder
    └─ 같은 순서와 정규화로 신경망 입력 Tensor 생성
         ↓
Utility Baseline 또는 Neural Policy
    └─ 후보 점수와 제한된 parameter 제안
         ↓
Post-process
    └─ 행동 전환 비용, OOD, Calibration을 적용하고 필요하면 abstain
         ↓
Commit Coordinator
    └─ Goal·Target·자원·기한을 최신 상태로 재검증하고 원자적으로 시작
         ↓
Skill Executor
    └─ 이동, 시선, 대화, 엄폐, 전투를 실제로 실행
         ↓ Attack(Entity) + BossPatternPolicy인 경우만
Boss Pattern Candidate Builder → Utility/Neural Pattern Selector
    └─ Boss Data Asset의 최대 32 Pattern row를 hard mask하고 순위 결정
         ↓
Boss Pattern Commit → StateTree/C++ Combat Executor
    └─ Telegraph·Active·Recovery 잠금, Hitbox·Damage·Interrupt를 결정론적으로 실행
```

예: Hearing이 `SoundEvent`를 만들면 Goal Manager가 `InvestigateDisturbance`를 활성화한다.

Target Slotter와 Candidate Builder는 `Investigate(SoundEvent)`를 구성한다. Commit Coordinator는 TTL·Goal·이동 가능 여부를 검증한 뒤 Skill을 시작한다.

## 1.3 학습한 모델이 Runtime에 들어오는 순서

```text
Runtime Snapshot과 Candidate
→ Dataset Record와 provenance 저장
→ split/누출/Switch Cost 검증
→ Python 학습과 Calibration/OOD fitting
→ ONNX export와 Model Bundle 생성
→ Python↔ONNX Runtime parity
→ Unreal NNE import와 descriptor 검사
→ Unreal Runtime Golden·Safety Gate
```

학습과 Runtime은 같은 Schema, Skill/Goal Registry, Target 순서, Candidate Mask, 정규화와 Post-process 버전을 사용한다. 어느 하나라도 다르면 모델 실행 전에 계약 불일치로 거부한다.

## 1.4 계층별 책임

| 계층 | 역할 | 출력 | 전용 책임 |
|---|---|---|---|
| Authoritative World | Actor·물리·피해·퀘스트·자원 상태 관리 | 최신 World state | 물리·피해·퀘스트 변경 |
| Knowledge(코드: `Perception/Belief`) | 시야·소리·공유 정보 관리 | 출처·시각·confidence·TTL이 있는 Knowledge | NPC 지식 경계 |
| Goal Manager | Goal 우선순위·phase·중단·재개 관리 | Active Goal과 revision | Goal lifecycle |
| Target의 종류와 식별 정보 통합(코드: `Typed Target Universe`)·Slotter | Target 통합·선정·slot 배치 | 일반 Target 16개와 `NoTarget` | Target identity와 순서 |
| Candidate Builder | Skill×Target 조합과 hard mask 생성 | 고정 Candidate 272개 | Candidate 유효성 |
| Utility Baseline·Neural Policy | 전술적 선호 계산 | raw score와 parameter proposal | Candidate ranking |
| Post-process | Switch Cost·OOD·Calibration 적용 | 선택 후보 또는 fallback | Neural 수용 여부 |
| Commit Coordinator | 최신 상태 검증과 자원 예약 | Skill 시작 또는 실패 코드 | 원자적 Skill 시작 |
| Skill Executor | Skill tick·완료·실패·취소 처리 | Gameplay 결과 | 이동·애니메이션·전투 실행 |
| Boss Pattern Candidate Builder | `Attack(Entity)` 내부의 authored Pattern을 최대 32행으로 고정·mask | `pattern_mask`와 Pattern snapshot hash | Pattern 실행 가능성 |
| Boss Pattern Selector | valid Pattern의 전투 맥락별 선호 계산 | Pattern raw score와 제한된 extension proposal | Pattern ranking만 |
| Boss Pattern Commit·Executor | Pattern stale 검증·예약·잠금·전투 실행 | Pattern 시작 또는 실패 코드 | Telegraph·Active·Recovery·Hitbox·Damage·Interrupt |

각 계층은 Target miss, mask 오류, ranking 오류, stale 응답, Skill 실패를 따로 기록한다.

Neural Policy의 권한은 Candidate ranking으로 제한한다. Goal 생성은 Goal Manager, Candidate 유효성은 Candidate Builder, 최종 안전 검증과 자원 예약은 Commit Coordinator가 소유한다.

## 1.5 자주 쓰는 용어

| 용어 | 이 문서에서의 뜻 |
|---|---|
| Knowledge (코드 이름: `Belief`) | NPC가 관측하거나 전달받아 보관하는 정보 |
| Goal | `조사한다`, `전투한다`처럼 여러 행동에 걸쳐 유지되는 목적 |
| Goal Phase | Goal 안의 현재 단계. 예: 소리 방향 보기 → 접근 → 주변 탐색 |
| Skill | `LookAt`, `Approach`, `Attack`처럼 실행기가 수행할 수 있는 한 가지 행동 |
| Target | Skill이 사용하는 Actor·소리·위치·엄폐물 |
| Target의 종류와 식별 정보 (`Typed Target`) | Entity·소리·위치·엄폐물의 종류와 실제 대상을 공통 Handle·Feature로 표현한 것 |
| Target Slot | 이번 의사결정에서 모델에 보여주는 Target의 고정 위치 |
| Candidate | `Skill + Target Slot` 조합. 예: `Investigate + SoundEvent slot 3` |
| Boss Pattern | `Attack(Entity)`가 선택된 뒤 보스가 실행할 authored 공격 절차. Target Slot이나 공통 Candidate가 아님 |
| Pattern Slot | 한 보스의 현재 Pattern Data Asset을 stable `pattern_id` 순으로 배치한 별도 고정 row. 최대 32개 |
| Hard Mask | Candidate의 실행 가능 여부를 고정한 표 |
| Commit | 선택된 Candidate를 최신 상태로 재검증하고 실제 Skill 시작을 확정하는 짧은 트랜잭션 |
| OOD | 학습 분포 밖의 입력에서 Neural 선택을 거부하는 신호 |
| Contract | Python·Unreal·서버가 동일하게 따라야 하는 타입, 순서, 수식, 실패 규칙 |

## 1.6 달성 목표

- 장기 Goal은 명시적으로 유지하고, 현재 Goal 안의 전술 행동 선택만 학습한다.
- NPC가 관측하거나 전달받은 정보만 사용해 플레이어가 납득할 수 있는 행동을 만든다.
- 상황별 행동 선호 조건문의 증가를 줄인다.
- Candidate 누락, Ranking 오류, Calibration 오류, Commit 오류, Skill 실행 오류를 따로 측정한다.
- Utility Baseline 대비 안전·성능 비열등과 자연스러움·목표 수행 품질 개선을 증명한다.
- Python 학습 결과와 Unreal Runtime이 같은 입력에 같은 계약을 적용하도록 만든다.

## 1.7 범위 밖

- 신경망의 퀘스트·장기 Goal 임의 생성 및 완료
- 숨은 Actor의 실제 위치·체력·행동 사용
- 모델 출력만으로 감정·관계 직접 누적
- 신규 Role·Skill의 무조건적 zero-shot 품질 보장
- 프레임별 이동 벡터·애니메이션 출력
- GRU hidden state만으로 장기 계획

---

<a id="2-typed-target"></a>
# 2. Target의 종류와 식별 정보 (기술명: Typed Target)

Target에는 Entity·소리·마지막 위치·엄폐물·Smart Object·Waypoint처럼 여러 종류가 있다. 기술 계약은 이 Target 종류들을 공통 형식으로 표현하며, 이를 `Typed Target`이라고 부른다.

## 2.1 Runtime Handle과 Model Feature 분리

Runtime은 `FTargetHandle`을 lookup·Commit·Hash에 사용한다. Neural input은 `FTargetFeatures`만 사용한다.

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
- Candidate Hash에는 요청 시점의 `SnapshotKey`를 기록한다. Commit의 Revision 일치 방식은 Target Kind별 §7.3 규칙을 따른다.
- Event가 과거 Revision의 같은 대상을 참조할 때 현재 slot 재매핑은 `IdentityKey`로 수행한다.
- Switch Cost의 `target_changed`, `same_as_current_target`, `same_as_current_skill_target`, Continue slot 재매핑은 `IdentityKey` 비교를 사용한다.
- 같은 `IdentityKey`의 Revision-only 변경은 snapshot update로 처리한다.
- immutable/resource Target의 exact Revision 변경은 stale로 처리한다.
- Entity Knowledge 갱신은 §7.1의 제한된 non-material 조건을 만족할 때만 최신 Knowledge 재검증을 허용한다.
- Canonical serialization의 `FTargetHandle` 전체 byte 비교를 의미상 same-target 비교로 재사용하지 않는다.

같은 적을 두 번 관측한 경우를 생각하면 쉽다. `IdentityKey`는 두 관측이 같은 적을 가리키는지 판정한다. `SnapshotKey`는 현재 관측이 요청 시점의 관측과 같은지 판정한다.

새 Entity 관측에서 위치와 같은 연속값만 조금 바뀌면 50ms 한도 안에서 최신 Knowledge로 다시 검증할 수 있다. 시야, 실행 가능 여부, Candidate mask, immutable Target Revision 중 하나라도 바뀌면 이전 응답을 폐기한다.

금지 사항:

- `StableId`, `EventId`, `SlotId`, `WaypointId`, `ReservationId`를 Tensor에 넣지 않는다.
- 절대 월드 좌표, `CreatedTime`, Actor Pointer를 Tensor에 넣지 않는다.
- 시간은 `age`, 위치는 NPC-local 상대 위치로 변환한다.
- `ReservationId`는 Commit 성공 후에만 존재한다.

## 2.2 Target Kind 의미

정확한 숫자 ID는 [Contract Appendices의 `A.target_kind`](contract-appendices.md#atarget_kind)가 소유한다.

| Kind | 역할 |
|---|---|
| `NoTarget` | 대상을 필요로 하지 않는 Skill용 고정 자리 |
| `Entity` | NPC가 현재 추적할 수 있는 Actor |
| `SoundEvent` | 특정 시점에 들린 소리의 변경되지 않는 기록 |
| `LastKnownPosition` | 더 이상 보이지 않는 대상의 마지막 관측 위치 |
| `CoverSlot` | 예약과 점유 상태를 검증해야 하는 엄폐 지점 |
| `SmartObject` | 의자·문·상호작용 지점처럼 예약 가능한 기능 위치 |
| `Waypoint` | 순찰·경로에 작성된 고정 지점 |
| `WorldPosition` | Goal·Script·Player Ping이 만든 임시 위치 |

## 2.3 Handle 생성 규칙

| Kind | StableId | Generation | Revision |
|---|---|---|---|
| NoTarget | 0 | 0 | 0 |
| Entity | 서버 영속 Entity/Net ID | Actor spawn generation | Knowledge revision |
| SoundEvent | World epoch 내 단조 증가 event ID | World event epoch | immutable event revision 0 |
| LastKnownPosition | NPC별 단조 증가 snapshot ID | source Entity generation 또는 0 | snapshot 생성 시 Knowledge revision |
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

# 3. Target Universe와 Slotter

`Target Universe`는 현재 Goal과 Knowledge(`Belief`)에서 Target 종류를 모은다. `Target Slotter`는 필수 대상을 우선 보존하고 나머지를 quota 순서로 선정해 17개 slot에 배치한다.

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
→ Target의 종류와 식별 정보 통합 (코드: `Typed Target Universe`)
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

한 Decision state `s`의 Gold relevant Target 집합을 `R(s)`라고 한다. `R(s)`에는 해당 Goal phase의 safe acceptable Skill 실행이나 Critical invariant 충족에 필요한 unique `IdentityKey`를 포함한다.

`R(s)`는 Ground Truth label channel에서만 작성한다.

```text
Target Recall numerator   = Σ_s |SlottedIdentity(s) ∩ R(s)|
Target Recall denominator = Σ_s |R(s)|
```

- `R(s)=∅` state는 Target Recall에서 제외하고 분모를 별도 보고한다.
- 만료·파괴 등 label 시점에 유효하지 않은 Target은 `R(s)`에 넣지 않는다. 사후 임의 제외를 금지한다.
- General Target Recall point estimate ≥99.5%, relevant-target trial Wilson 95% lower bound ≥99.0%다.
- Critical Suite는 576 sequence의 모든 decision·relevant-target trial을 보고하고 miss 0건이어야 한다.
- 보고서는 target-trial micro, decision-state micro, Role×Goal macro, sequence별 miss를 모두 포함한다.
- episode-cluster bootstrap 10,000회 CI를 민감도 분석으로 함께 보고하며 Wilson만으로 상관 구조를 숨기지 않는다.
- miss reason: `PerceptionMiss`, `ExpiredBelief`, `MandatoryOverflow`, `QuotaDrop`, `DedupeError`, `SlotterMismatch`, `UnsupportedKind`

---

# 4. Candidate Universe

Candidate는 `Skill + Target Slot` 조합이다. Candidate Builder는 16×17=272개 조합을 만들고 hard mask로 실행 가능한 후보를 고정한다. Policy는 valid Candidate의 순위를 매긴다.

## 4.1 고정 Layout

```text
candidate_index = skill_id * 17 + target_slot
skill_id        = floor(candidate_index / 17)
target_slot     = candidate_index % 17
```

모든 요청은 272개 row를 갖는다. Ragged batch는 V1에서 금지한다.

## 4.2 ContinueCurrentAction 중복 제거

`ContinueCurrentAction`은 현재 실행을 유지하는 control candidate다.

- 실행 중 Skill이 있을 때 정확히 하나만 valid다.
- 현재 Target이 slot에 있으면 그 slot을 사용하고, 없으면 `NoTarget` 16을 사용한다.
- 동일 Skill/동일 Target을 다시 `Start`하는 일반 Candidate는 mask한다.
- Skill이 종료된 상태에서는 Continue를 mask한다.
- Commit 전에 반드시 `RunningSkill.CanContinue(LatestBelief, LatestGoalRevision)`를 호출한다.
- 최신 Knowledge에서 Target이 더 이상 유효하지 않거나 Goal 계약이 바뀌면 Continue는 거부한다.
- `ContinueCurrentAction`은 실제 실행 Skill이 아니므로 `global_state[17]`은 항상 0인 reserved field다.

따라서 “현재 실행 유지”와 “같은 Skill을 새로 시작”하는 의미가 중복되지 않는다.

## 4.3 Skill 계약 참조

정확한 Skill 숫자 ID는 [Contract Appendices의 `A.skill`](contract-appendices.md#askill)가 소유한다. 아래 허용표는 각 Skill이 사용할 수 있는 Target Kind를 정의한다.


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

## 4.7 보스 전용 Neural Pattern Selector

보스 패턴은 공통 Candidate Universe를 확장하지 않는다. 공통 Policy가 `Attack(Entity)`를 선택하고 Attack Skill이 `ReadyToSelect`에 진입한 뒤, `BossPatternPolicy` capability가 있는 보스만 별도 Pattern Selector를 실행한다.

```text
공통 Policy: Attack(Player Entity) 선택
→ 공통 Commit: Attack precondition과 Target 검증
→ BossPatternCandidateBuilder: 최대 32 Pattern row + hard mask
→ Pattern Utility Baseline 또는 Neural Pattern Selector
→ BossPatternCommitCoordinator: request/hash/revision/asset/resource 재검증
→ StateTree/C++ Combat Executor: Telegraph → Active → Recovery
```

`QuickSlash`, `DelayedHeavy`, `GapCloser`는 Target Slot이 아니다. 모두 같은 `Attack(Player)` 안에서 선택하는 보스 전용 Pattern Data Asset이다. 일반 NPC와 보스 모두 공통 `candidate_count=272`를 유지하며 Pattern row는 별도 `[B,32,*]` namespace를 사용한다.

### 4.7.1 Pattern Candidate와 hard mask

- 한 보스의 활성 Data Asset을 stable `pattern_id` 오름차순으로 최대 32 slot에 배치한다.
- 빈 row는 `invalid_pattern_id`와 `pattern_mask=false`로 padding한다.
- Phase, Target identity/generation, 거리, 각도, 고도, LOS, cooldown, stamina, predecessor/successor, Branch Window, arena/nav 안전, asset load, executor lock, reservation을 결정론적으로 mask한다.
- 선호도는 mask에 넣지 않는다. 예를 들어 “근거리에서 QuickSlash가 더 좋다”는 Utility/Neural ranking이 판단한다.
- valid row가 0개면 inference와 Utility를 만들지 않고 `PatternUnavailable`로 Attack Skill을 종료해 최신 공통 fallback으로 복귀한다.
- valid row가 있는 inference/response 실패는 같은 immutable snapshot의 Utility를 사용한다. 동점은 adjusted score 내림차순 후 `pattern_id` 오름차순으로 고른다.
- Utility도 실패하면 `PatternSetDataAsset.safe_default_pattern_id`가 현재 valid인 경우에만 사용한다.

### 4.7.2 별도 신경망 I/O

```text
pattern_context             float32 [B,32]
pattern_features            float32 [B,32,24]
pattern_pair_features       float32 [B,32,16]
pattern_ids                 int64   [B,32]
pattern_mask                bool    [B,32]

pattern_raw_scores          float32 [B,32]
pattern_parameter_proposals float32 [B,32,4]
```

Feature divisor·clamp·padding은 `boss_pattern_contract_v1.yaml`에서 생성한다. 모든 field는 정확히 하나의 normalizer에 배정되며 Python Builder와 Unreal Builder가 generated spec을 공유한다. 외부 대상 정보는 허용된 Knowledge 또는 locked Attack Target source만 사용할 수 있고 Ground Truth source는 validator가 거부한다. `target_health_ratio_estimate`는 `target_health_estimate_confidence`와 함께 입력한다. 빈 Pattern row의 feature는 정규화 후 전부 0이며 masked score는 ranking 전에 `-∞`로 바꾼다.

Pattern Policy는 ranking과 다음 제한값만 제안한다.

1. authored tracking 상한을 넘지 않는 `tracking_fraction`
2. Telegraph를 줄이지 않고 authored 상한 안에서만 늘리는 `telegraph_extension_fraction`
3. Recovery를 줄이지 않고 authored 상한 안에서만 늘리는 `recovery_extension_fraction`
4. 항상 0인 reserved parameter

Damage, Hitbox, Active window, Root Motion, interruptibility, Phase transition은 신경망 출력이 아니다.

### 4.7.3 Telegraph 일치와 실행 잠금

- 선택 request는 `PreAttack`, authored `BranchWindow`, `RecoveryEnd`에서만 만든다.
- Pattern Commit 성공 transaction이 Pattern·Target identity·제한 parameter를 원자적으로 잠그고 `PreAttackTurn`에 진입한다.
- `PreAttackTurn`, `Startup/Telegraph`, `Active`에서는 Pattern을 변경하지 않는다.
- `Recovery`는 authored Branch Window에서만 successor 선택을 허용한다.
- 일반 플레이어 이동, 새 Tactical score, 새 Pattern score는 실행 중 Pattern을 중단하지 않는다.
- 잠금 뒤 Target identity와 Pattern은 유지한다. 선택용 Knowledge snapshot은 immutable이다.
- 결정론적 Executor만 Combat Targeting 정책이 허용한 현재 Target transform을 읽어 Data Asset의 Phase별 각도·속도 상한 안에서 추적할 수 있다.
- Executor가 읽은 현재 transform은 Pattern Model 입력으로 되먹이지 않으며 Pattern 변경 사유가 아니다.
- 강제 중단은 `Death`, `ActorDestroyed`, `AuthorityLost`다. `Stun`, `PostureBreak`, scripted Phase transition, Arena reset은 해당 Pattern Data Asset의 allowlist가 허용할 때만 중단한다.
- 중단 시 Hitbox 비활성화 → Montage/Root Motion 정리 → reservation 해제 → 결과 Event 발행 순서를 지킨다.

이 규칙은 플레이어가 본 Telegraph와 실제 공격 결과가 일치하도록 보장한다.

### 4.7.4 정보 경계·Hash·승격

Pattern request는 공통 Attack Target의 허용된 Knowledge snapshot만 사용한다. 보이지 않는 플레이어의 실제 Transform, 미래 입력, ground-truth 상태는 사용할 수 없다.

`pattern_candidate_set_hash`는 Contract hash, Pattern Asset bundle hash, 32개 Pattern ID·mask, Attack Target Handle, selection boundary, Boss Phase revision, Combat State revision을 고정 순서로 묶는다. 응답은 같은 hash와 `boss_pattern_decision_contract_hash`를 반환해야 하며 Commit에서 latest request와 다시 비교한다.

`BranchWindow`가 응답 전에 닫히거나 Phase/Combat revision이 바뀌면 `PatternBoundaryClosed` 또는 stale failure로 거부한다. 현재 Pattern은 재선택 없이 authored 종료 경로를 계속하고 다음 유효 boundary에서 새 request를 만든다.

정확한 Tensor field, enum, Data Asset 필드, hash 직렬화는 [Contract Appendices BP](contract-appendices.md#bp-auto-generated-boss-pattern-selector-계약)가 소유한다. Schema Harness 통과는 구조·생성·Python/C++ Candidate/Decision hash Golden 완료만 뜻한다. Pattern Asset Bundle digest의 Python↔Unreal Build Commandlet parity, Unreal Float parity, ONNX output parity, Unreal Pattern Runtime, fairness/quality, performance Gate는 실제 엔진 증거 전까지 pending이다.

### 4.7.5 현재 Unreal 구현 상태

2026-08-10 기준 구현은 Pattern 선택·Commit/Handoff, Session-owned Phase Executor, production StateTree asset과 encounter Blueprint physical assembly, fixture-backed authoritative Session Host의 Commit→StateTree start handoff까지 닫혔다.

| 단계 | 상태 |
|---|---|
| Pattern Definition/Set Data Asset와 validator | Core 완료; Definition JCS/cooked parity pending |
| 32행 layout·candidate/decision hash·Utility Profile | 완료 |
| Hard Mask·Tensor Normalization | 완료 |
| Utility fallback·Decision Pipeline·Commit | 완료 |
| Neural raw-output finite/mask/parameter canonicalization | 완료 |
| Execution Safety Policy와 Commit-bound Handoff | 완료 |
| NNE/ONNX model adapter와 Neural ranking/tie/OOD | 미구현 |
| Session-owned C++ Phase Executor·terminal barrier/unlock Core | 완료 |
| production StateTree/Turn Task/Combat lifecycle event-source adapter | C++ adapter phase PASS (`7/7`, full `48/48`, independent GO) |
| production StateTree native authoring MCP tool·saved Boss asset | asset phase PASS (`5/5`, focused `8/8`, full `49/49`, independent GO) |
| encounter Pawn/AIController Blueprint physical assembly | phase PASS (`2/2`, full Boss `51/51`, restart persistence PASS, independent GO) |
| fixture-backed authoritative Session Host·Commit 뒤 StateTree start handoff | phase PASS (focused `2/2`, broad `53/53`, independent `Critical 0 / Important 0 — GO`) |
| concrete gameplay authority provider·production PatternSet/selector trigger | 미구현 |
| authored transition/condition·Montage·Hitbox·Damage·Root Motion·cleanup effect | 미구현 |
| Replication·Save/Load·fairness·performance | 미구현 |

`unreal_pattern_runtime`은 concrete gameplay authority provider, production PatternSet/selector trigger, authored transition/condition과 실제 전투 효과가 닫힐 때까지 `pending`이다. fixture-backed Host/start handoff phase PASS를 shipping gameplay Runtime PASS로 확대하지 않는다.

### 4.7.6 Event-driven Phase Executor 권위 계약

Commit-bound Handoff는 서버가 승인한 Pattern·Target·제한 parameter·authored 실행 facts를 변경 불가능한 snapshot으로 봉인해 Session-owned Executor에 최대 한 번 전달한다. Handoff는 실행 자체가 아니며 `at-most-once delivery`만 보장한다. Executor 성공까지 포함한 `exactly-once execution`은 보장하지 않는다.

Phase 변경 write 권한은 `FBossPatternCommitSession`이 소유한 서버 Executor 하나에만 있다. StateTree Task, Turn Task, Montage Notify, Hitbox·Damage·Root Motion component, client는 Phase를 직접 설정하지 않고 다음 사실만 bound server source를 통해 전달한다.

| 전환 | authoritative event source | 승인 조건 |
|---|---|---|
| Commit → `PreAttackTurn` | Commit Session 내부 | authoritative atomic Commit 성공 |
| `PreAttackTurn` → `StartupTelegraph` | 같은 execution에 bound된 server Turn Task | Turn Task가 `Succeeded`를 발행 |
| `StartupTelegraph` → `Active` | Session Executor의 server monotonic deadline | phase-entry time + committed effective Startup duration 도달 |
| `Active` → `Recovery` | Session Executor의 server monotonic deadline | phase-entry time + committed effective Active duration 도달 |
| `Recovery` → `Completed` | Session Executor의 server monotonic deadline | phase-entry time + committed effective Recovery duration 도달 |
| locked phase → `Interrupted` | bound server Combat/Actor lifecycle source | forced interrupt 또는 authored allowlist interrupt 승인 |

Startup·Active·Recovery deadline은 각 Phase의 승인된 진입 시각을 기준으로 계산한다. 늦게 pump되더라도 이전 authoritative deadline을 다음 Phase 진입 시각으로 사용해 같은 서버 시간 입력에서 같은 결과가 나오게 한다. client clock과 Montage Notify는 deadline authority가 아니다.

외부 event는 최소한 `PatternDecisionId`, Session execution/source binding generation, expected current phase, expected phase revision, authoritative source role, source-local sequence, server monotonic event time, event kind를 보존한다. `TurnTask` source는 `PreAttackTurnSucceeded/TimedOut`만, `CombatLifecycle` source는 `InterruptRequested`만 생산할 수 있다. Executor는 다음 규칙을 적용한다.

1. server authority가 아닌 producer는 거부한다.
2. 현재 execution identity·phase·revision과 다른 late/stale event는 거부한다.
3. timed Phase에서 event time이 해당 Phase deadline보다 늦으면, current identity가 일치해 보여도 과거 Phase event로 거부한다.
4. event time이 deadline과 정확히 같으면 validated interrupt/timeout event를 deadline 전환보다 먼저 처리한다.
5. event kind와 authoritative source role 조합이 다르면 거부한다.
6. 각 source-local sequence가 해당 source의 마지막 승인값보다 크지 않은 duplicate/out-of-order event는 거부한다.
7. unknown/future source·event·phase·interrupt 값은 fail-closed한다.
8. finite·non-regressing capture server time은 event 승인 여부와 무관하게 Session clock high-water로 기록한다. 따라서 `10 → rejected 20 → accepted 15` 회귀는 허용하지 않는다.
9. 같은 Session에서 event 처리 또는 terminal callback이 진행 중이면 reentrant 호출을 거부한다.
10. 일반 Target 이동·새 Tactical score·새 Pattern score는 Phase event가 아니다.
11. authored `BranchWindow` timing과 successor 실행은 별도 후속 계약 전까지 이 Core가 발명하지 않는다. 이번 Core는 selected authored row의 `BranchWindows.Num()==0`일 때만 Commit atomic resource callback에 진입하며, branch-capable row는 `PatternExecutorBranchWindowsUnsupported`로 그 전에 거부한다. 따라서 이 Core의 `Recovery → Completed`는 branchless row에만 적용된다.

`PreAttackTurn`의 방향 오차와 최대 대기 시간 수치는 현재 Boss Pattern YAML에 없다. Core는 bound Turn Task의 `Succeeded` 또는 `TimedOut` 사실만 소비한다. production Turn Task adapter를 연결하기 전에 `FacingToleranceDegrees`와 `PreAttackTurnTimeoutSeconds`의 소유 위치와 값을 별도 Turn Task 계약에서 확정해야 하며, 값 미확정 상태에서 임의 상수를 사용하지 않는다. `TimedOut`은 공격을 강제로 시작하지 않고 terminal `Interrupted` 경로로 보낸다.

`AuthorityLost` interrupt는 기존 authority가 cleanup ownership을 아직 가진 상태에서 transition 사실을 발행할 때만 소비한다. `HasServerAuthority()==false`가 먼저 관측되면 Core는 event source를 호출하지 않고 active lock을 유지하며, 새 authority 또는 owner teardown이 이어받아야 한다.

### 4.7.7 Completed·Interrupted terminal unlock 계약

선택 잠금 해제 write 권한은 Session-owned 서버 Executor만 가진다. public `ClearCommittedLock()`, caller-supplied phase setter, caller-supplied unlock callback은 제공하지 않는다. StateTree·Montage·effect component는 unlock을 요청하거나 직접 수행할 수 없다.

`Completed`는 현재 execution이 `Recovery`이고 deadline event가 identity·phase·revision 검증을 통과한 뒤에만 claim한다. `Interrupted`는 `Death`·`ActorDestroyed`·`AuthorityLost` forced interrupt 또는 Pattern snapshot allowlist가 허용한 `Stun`·`PostureBreak`·`ScriptedPhaseTransition`·`ArenaReset`만 claim한다.

Terminal claim 이후 순서는 다음과 같다.

```text
1. Session mutex 안에서 해당 execution의 stable TerminalClaimId를 가진 terminal claim을 단 한 번 설치
2. mutex 밖에서 bound server terminal authority가 detached snapshot proposal로 cleanup·reservation release·result publication을 원자 dispatch
3. `AcceptedPending`이면 같은 claim을 재-dispatch하지 않고 read-only `CaptureTerminalStatus()`로만 Pending/Success를 관찰
4. dispatch/poll의 AuthorityLost·unknown이면 active lock과 terminal claim을 유지하고 fail-closed
5. Success 뒤 Session mutex 안에서 terminal phase/result snapshot을 branch-free publish
6. active execution lock 해제와 다음 selection permission을 같은 Session state 변경으로 publish
7. old pump의 scope가 완전히 끝날 때까지 fresh SetPending/Commit/Pump를 차단
```

`Interrupted` callback은 generated 계약의 canonical cleanup 순서인 Hitbox 비활성화 → authored policy에 따른 Montage 정지/blend → Root Motion 제거 → Pattern reservation 해제 → interrupt result 발행 → Executor state 전환을 모두 완료해야 Success를 반환할 수 있다. `Completed` callback도 남은 effect가 없음을 확인하고 reservation 해제와 completion result publication을 끝내야 한다. 실제 Montage·Hitbox·Damage·Root Motion effect adapter가 없는 Core 단계에서는 이 callback이 terminal barrier만 정의하며 실제 effect 완료를 주장하지 않는다.

Commit과 Terminal authority proposal의 execution snapshot은 callback stack lifetime의 physically-const detached copy이며, 내부 install/active snapshot과 alias하지 않는다. Authority는 proposal·snapshot 주소를 보존하거나 callback 뒤 사용해서는 안 된다. TerminalClaimId, source별 event sequence high-water, server monotonic clock high-water는 execution 교체 시 초기화하지 않는 Session-lifetime ledger다. Fresh Commit의 server time이 clock high-water보다 작으면 atomic Commit callback 전에 거부한다.

Unlock은 실행 기록 삭제가 아니다. Session은 terminal detached snapshot과 `HighestAcceptedPatternDecisionId`를 보존하고, 같은 Decision ID의 재사용·재전달을 거부한다. 다음 선택은 더 큰 Decision ID의 fresh replan만 허용한다. `ActorDestroyed`는 terminal history만 publish하고 `bSelectionUnlocked=false`로 Session을 영구 selection-closed 처리하며, 재사용 가능한 unlock API 없이 owner teardown으로 종료한다.

### 4.7.8 Production Event-source Adapter 계약

production adapter는 trusted `IBossPatternSessionAuthority`와 gameplay producer 사이를 분리한다. `FBossPatternPhaseEvent`·`FBossPatternPhaseEventQuery`는 Session Core와 trusted authority 사이의 transport이며 gameplay ingress가 아니다. production authority의 `CaptureExecutionEvent(Query)`는 bound event-source component의 private destructive capture에 독점 위임하고 authority clock seam도 private friend access로만 사용한다. raw source capture는 component와 dev test-access 외에는 private다. StateTree·Turn Task·Combat component는 complete DTO, Decision ID, execution generation, phase/revision, source role, sequence, timestamp, caller-built Query 또는 generic interrupt enum을 전달할 수 없다.

Commit atomic authority는 opaque `FBossPatternCommitProposal`의 committed `AttackTargetHandle`과 authoritative target actor가 같음을 host transaction 안에서 검증한 뒤 `UBossPatternExecutionEventSourceComponent`에 execution binding을 설치한다. host가 `Success`를 반환했는데 source binding이 없으면 production authority는 host adapter-failure rollback callback을 정확히 한 번 호출하고, rollback 성공 뒤 Commit을 `ResourceConflict`로 거부하며 rollback 실패는 `AuthorityLost`로 fail-closed한다. source bind 뒤 host가 non-Success를 반환하면 authority는 같은 opaque Proposal identity로 source binding을 rollback하고, host는 자신의 gameplay resource 변경을 같은 transaction 안에서 rollback한다. callback 중 authority가 사라져도 exact Proposal identity 확인·cleanup은 authority predicate와 분리하며, 성공 응답이었다면 host rollback callback도 실행한 뒤 Commit을 `AuthorityLost`로 거부한다. binding은 Decision ID·Execution Generation·committed PreAttack tracking limits·target weak lifetime·Turn 설정을 immutable copy로 보존한다. producer는 component가 발급한 opaque Turn/Combat binding만 사용한다. terminal binding retirement도 opaque `FBossPatternTerminalProposal` identity가 현재 binding과 같을 때만 허용한다.

`UBossPatternExecutionSessionComponent`는 하나의 `FBossPatternCommitSession`·Coordinator·trusted authority를 encounter lifetime 동안 소유한다. production 조립은 owner당 Session component와 EventSource component가 각각 정확히 하나여야 하며 ambiguity를 fail-closed한다. EventSource runtime/source는 component constructor에서 eager-create한다. native host는 one-shot 초기화에서 component가 unique ownership으로 받고 Commit/Pump per-call dependency로 다시 받지 않는다. authority가 있는 동안 component Tick이 Session을 pump하고, Combat lifecycle typed ingress는 새 fact의 own pending receipt가 consumed/rejected/terminal 처리될 때까지 최대 두 source fact를 bounded pump한 결과를 caller에게 반환한다. `TerminalPending` owner teardown/authority transfer는 producer binding retirement 뒤 move-only `FBossPatternTerminalDrain`으로 Session·Authority·Host·Coordinator와 strong-pinned host lifetime owner를 encounter/server owner에 이전해 completion까지 poll한다.

`PreAttackTurn` 설정 authority는 authoritative actor의 event-source component CDO/instance다. Commit binding 시 값을 봉인하며 현재 production 기준은 다음과 같다.

| 필드 | 현재 값 | validation |
|---|---:|---|
| `FacingToleranceDegrees` | `5.0`도 | finite, `0 < value <= 180` |
| `PreAttackTurnTimeoutSeconds` | `2.0`초 | finite, `0 < value <= 30` |

invalid config는 binding을 설치하지 않고 fail-closed한다. 실행 중 caller나 StateTree Task가 값을 변경할 수 없다.

StateTree PreAttack Turn Task는 server authority에서만 동작하고, `FStateTreeExecutionContext::GetOwner()`가 bound `AAIController`와 정확히 같으며 그 Controller의 `GetPawn()`과 event-source component owner도 정확히 같을 때만 current `PreAttackTurn` binding을 획득한다. target은 caller input이 아니라 committed binding에서 읽는다. 매 Tick server monotonic elapsed time과 committed `PreAttackTurn.MaxYawDegreesPerSecond`로 yaw step을 clamp하며 translation·Pattern·Target identity·Phase·selection lock은 바꾸지 않는다. 방향 오차가 tolerance 이하면 `Succeeded`, immutable timeout에 먼저 또는 같은 시각에 도달하면 `TimedOut` fact를 각각 한 번만 publish한다. committed target이 invalid이면 새 `TargetLost`나 owner `ActorDestroyed`를 발명하지 않고 회전 없이 timeout 경로만 사용한다. stale binding·authority loss·invalid owner/clock/config는 event를 위조하지 않고 fail-closed한다.

Combat lifecycle ingress는 `Death`, `ActorDestroyed`, `AuthorityWillBeLost`, `Stun`, `PostureBreak`, `ScriptedPhaseTransition`, `ArenaReset`의 typed method만 제공한다. report 결과는 `Queued / SameSourcePending / Rejected`를 구분한다. `Rejected`는 unrelated event를 pump하지 않는다. `Queued`는 자기 opaque binding의 pending receipt가 없어질 때까지 bounded drain한다. `SameSourcePending`은 기존 receipt를 bounded drain한 뒤 새 fact를 정확히 한 번 queue하고 그 새 receipt까지 처리한다. `AuthorityLost`는 authority가 아직 cleanup ownership을 가진 handoff-before-loss 시점에만 publish하고 own receipt가 terminal handoff에 도달하기 전에 authority를 넘기지 않는다. target actor 소멸을 owner `ActorDestroyed`로 바꾸지 않는다. authored interrupt allowlist 최종 승인은 기존 Session Executor가 committed snapshot으로 수행한다.

producer는 typed fact 발생 시 component가 server monotonic event time과 source-local sequence를 부여한다. production authority는 host current-state timestamp를 신뢰하지 않고 같은 event-source component clock으로 교체해 Commit start·event·deadline을 한 clock domain에 둔다. expected Phase/revision은 authority-only `CaptureExecutionEvent(Query)`에서 현재 Session query로 materialize한다. dequeue 순서는 `(EventTime 오름차순, CombatLifecycle 우선, SourceSequence 오름차순)`이다. pending fact가 있으면 capture clock은 선택된 fact의 logical event time으로 한 단계만 전진하고 queue가 빈 뒤에만 actual server now로 catch-up한다. runtime-sampled clock과 Core-visible logical capture clock은 별도 high-water다. 동일 시각 interrupt/timeout의 deadline 우선 규칙을 보존한다. execution당 source별 pending fact는 최대 하나이며 overwrite·silent drop하지 않는다. fresh execution bind는 pending old facts를 버리되 source sequence counter는 Session lifetime 동안 초기화하지 않는다.

component와 StateTree Task는 Game Thread only다. execution binding의 target/owner UObject·Actor는 weak reference로 보존하고, detached drain만 제공된 host lifetime owner를 완료까지 strong-pin한다. raw `this`를 장기 delegate에 capture하지 않는다. owner teardown은 event를 처리할 수 있는 handoff-before-destroy hook에서 `ActorDestroyed`를 report하고 own receipt를 terminal handoff까지 pump한 뒤 실제 destroy한다. `TerminalPending`이면 실제 EndPlay/authority flip 전에 drain ownership을 encounter/server owner에 이전해야 하며, 미이전 EndPlay는 contract violation이다.

2026-08-08 closure evidence는 cold UBT/UHT `226/226`, focused `7/7`, full Boss Pattern `48/48`, Data Validation `285/0/0`, generated sync PASS, SARIF `72/0`, MCP health/typed inspect/touched smoke PASS, independent review `Critical 0 / Important 0 — GO`다. 이 판정은 production event-source/session adapter **C++ phase PASS**다.

이번 adapter 단계는 실제 Montage·Hitbox·Damage·Root Motion·reservation cleanup과 terminal Success 판정, TargetLost semantics, Branch Window, replication/save-load를 구현하지 않는다. 따라서 adapter PASS만으로 `unreal_pattern_runtime`을 release-green으로 승격하지 않는다.

### 4.7.9 Production StateTree Asset·Authoring Tool 계약

StateTree asset 생성은 GameDevMCP의 `statetree.asset.author`만 사용한다. 이 도구는 새 asset만 허용하고 existing destination을 overwrite하지 않는다. request-level dry-run과 실제 write 모두 transient StateTree에서 schema·state hierarchy·native Task·context binding을 완전히 구성해 synchronous compile한다. compile 실패 시 Asset Registry 등록과 package save를 하지 않는다. 실제 write는 compile 성공·`IsReadyToRun()` 확인 뒤에만 asset을 등록하고, `auto_save=true`이면 save 성공까지 operation 성공 조건으로 삼는다. `statetree.asset.inspect`는 schema, state path, Task struct/instance type, binding source/target, editor/compiled hash 일치, package dirty 상태를 read-only로 반환한다.

production asset은 `/Game/AINativeNPC/BossPattern/StateTree/ST_BossPatternExecution`이다.

```text
schema: /Script/GameplayStateTreeModule.StateTreeAIComponentSchema
root: BossPatternExecution
child: BossPatternExecution/PreAttackTurn
task: /Script/NeuralGame.StateTreeBossPatternPreAttackTurnTask
binding: schema AIController -> Task instance AIController
```

Task instance의 `EventSource`는 editor Context property가 아니다. `EnterState()`에서 exact bound Controller의 Pawn에 속한 `UBossPatternExecutionEventSourceComponent`를 찾으며 유효한 component가 정확히 하나일 때만 instance에 고정한다. 0개, 2개 이상, 다른 Pawn의 pre-bound pointer, Context owner/controller 불일치, authority 부재는 fail-closed한다. StateTree asset은 gameplay caller에게 Decision ID·generation·phase/revision·sequence·timestamp 또는 destructive capture 권한을 노출하지 않는다.

2026-08-08 asset-phase evidence는 GameDevMCP clean build PASS, StateTree focused `5/5`, full Runtime `67/67`(`17` succeeded-with-warning, failure `0`), final-build/save rollback fault-injection과 retry no-conflict PASS, NeuralGame clean/cold UBT/UHT `229/229`, reflected incremental UHT/UBT `7/7`, EventSource focused `8/8`, full Boss Pattern `49/49`, Data Validation localization `286`·error/warning `0/0`, generated sync PASS, SARIF `72/0`, MCP dry-run `saved=false/touched=0`, create `saved=true`, restart inspect `ready_to_run=true/hash_matches=true/package_dirty=false`, active/interrupted changeset `0`이다. independent split review는 MCP handler와 Boss runtime/asset 모두 `Critical 0 / Important 0 — GO`로 종료됐다.

이번 asset 단계 자체는 encounter Pawn/AIController Blueprint 배치를 포함하지 않았고, 해당 physical assembly는 §4.7.10에서 별도 phase로 닫았다. transition/condition authoring, Montage·Hitbox·Damage·Root Motion·cleanup effect, replication/save-load는 여전히 구현하지 않았다. 따라서 production StateTree asset PASS만으로 `unreal_pattern_runtime`을 release-green으로 승격하지 않는다.


### 4.7.10 Encounter Blueprint Physical Assembly 계약

production Pawn은 `/Game/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterPawn`, AIController는 `/Game/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterAIController`다. Pawn은 기존 `BP_CombatEnemy_C`, Controller는 `BP_CombatAIController_C`를 parent로 사용한다.

Pawn은 `UBossPatternExecutionSessionComponent`, `UBossPatternExecutionEventSourceComponent`, `UBossPatternEncounterHostComponent`를 각각 정확히 하나 소유한다. Controller는 inherited native `StateTreeAI` 하나만 사용하고 child-local duplicate를 만들지 않는다. Pawn CDO의 `AIControllerClass`는 exact encounter Controller class, `AutoPossessAI`는 `PlacedInWorldOrSpawned`다. Controller의 `StateTreeRef.StateTree`는 production Boss StateTree exact asset이고 `bStartLogicAutomatically=false`, `bStartAILogicOnPossess=false`다.

physical assembly phase 당시에는 authoritative encounter host가 없어 Session이 `IsSessionReady()==false`였다. 현재 상태는 §4.7.11이 supersede하며, BeginPlay 뒤 exact production Pawn에서 Session은 ready가 된다. StateTree는 Commit 전까지 not-running을 유지한다. Blueprint EventGraph는 `InitializeSessionHost`, `StartLogic`, `Resolve`, `BindCommittedExecution`을 호출하지 않는다. 기존 C++ hostile tests의 client role, foreign owner, source 0·복수, Controller/Pawn mismatch fail-closed 계약을 우회하지 않는다.

2026-08-08 closure evidence는 `NeuralGameEditor` cold build PASS, encounter focused `2/2`, full Boss Pattern `51/51`, Data Validation `290` assets·error/warning `0/0`, generated contract lock sync PASS, NeuralGame SARIF `74/0`, 변경된 MCP 파일 SARIF `0`, restart registry/disk exact `1/1`, saved defaults/component/StateTreeRef persistence, begun-play game World의 `AutoPossessAI` automatic Controller spawn/possession(manual fallback 없음)·authority·owner identity·Session not-ready·StateTree stopped PASS, map dirty/unsaved `false/false`, active/interrupted ChangeSet `0`이며, final MCP/encounter independent re-review는 모두 `Critical 0 / Important 0 — GO`다.

같은 canonical path rollback/retry를 위해 GameDevMCP의 native inherited component override와 `asset.delete` package unload 경로를 보완했다. phase 신규 MCP tests `5/5`는 PASS했다. 전체 `UnrealMCP.Runtime` 72개 중 unrelated 기존 UMG 2개가 FAIL이므로 GameDevMCP 저장소 전체 release-green은 아니다.

### 4.7.11 Encounter Session Host / StateTree Start Handoff 계약

`UBossPatternEncounterHostComponent`는 exact production encounter Pawn generated class, server authority, Host/Session/EventSource exact-one을 확인한 뒤 Session host를 BeginPlay에서 한 번만 설치한다. Session의 Host 설치·pending·Commit ingress는 private friend/test-access 경로이며 임의 gameplay C++ Host 선점이나 raw Core 호출을 허용하지 않는다. adapter는 Session-owned `TUniquePtr`이고 Host component는 `TWeakObjectPtr`로 참조한다.

선택 snapshot과 Commit-time current state는 Host가 unique-own하는 private authority provider에서 별도로 capture한다. provider는 typed `(TargetHandle, Actor)` binding을 한 capability로 반환하며 Commit은 exact StableId·Generation·Revision, Actor identity, World, owner, material revisions, mask, resource, boundary, executor lock을 다시 검증한다. 현재 shipping gameplay concrete provider는 아직 없고 dev Automation fixture provider만 존재하므로 이 phase는 production selector 완료를 뜻하지 않는다.

Utility fixture adapter는 non-reentrant Game Thread stack 안에서 finalized request와 opaque Utility authorization을 만들고 pending→Commit을 수행한다. Commit callback은 exact production StateTree preflight를 다시 검사한다. Commit publish 뒤에만 StateTree를 한 번 시작한다. Task 진입 성공은 transient `IsRunning()` 단독이 아니라 same decision/generation의 durable Turn binding acquisition과 `PreAttackTurnSucceeded` queued fact로 판정한다.

Task-entry/start 실패는 Combat lifecycle과 분리된 dedicated `ExecutionHost` one-shot slot·sequence·high-water로 `ExecutionStartFailed`를 보고하고 즉시 Pump한다. 이 terminalization은 binding과 reservation을 한 번 정리하지만 Success가 아니므로 selection을 unlock하지 않는다. terminal poll은 exact durable completed claim이 있을 때만 `Success`다.

2026-08-09 evidence는 exact focused `2/2`, broad Boss Pattern `53/53`, warning/failure `0/0`, hostile client/foreign Pawn/duplicate/replay/stale revision/same-handle foreign Actor/same-Actor stale generation/preflight reject, client pending registration delta `0`, combat collision, failure report·Pump·terminal callback exact `+1`, Task acquisition `0`, Data Validation `290`·error/warning `0/0`, generated lock sync, changed-file SARIF `15/0`, MCP restart Host/Session/EventSource `1/1/1`, StateTree ready/hash/clean, map dirty/unsaved `false/false`, active/interrupted ChangeSet `0/0`이며 authority/security·lifecycle/terminal·asset/test 독립 review는 모두 `Critical 0 / Important 0 — GO`다.

다음 단계는 공통 Knowledge(`Belief`)/Goal/Target의 종류와 식별 정보(`Typed Target`)에서 live state를 공급하는 concrete gameplay authority provider와 production PatternSet/selector trigger다. authored transition/condition과 Montage·Hitbox·Damage·Root Motion·cleanup effect, replication/save-load는 그 이후 별도 단계다.

---

# 5. Goal Manager

Goal은 여러 Skill에 걸쳐 유지되는 목적이다. Goal Manager는 Goal의 우선순위·phase·중단·재개를 관리하고, Policy는 Active Goal 안에서 다음 Candidate를 고른다.

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

- Emergency source는 `preemption_margin`과 일반 priority key 우위 조건을 우회한다.
- Emergency source의 preemption 시점은 위 표의 Emergency 열을 따른다.
- 둘 이상의 Emergency 후보는 같은 Arbitration Key로 정렬한다.
- `Server ForceAbort`는 현재 Active Goal을 즉시 `Aborted`로 만드는 authoritative terminal command다.
- `Server ForceAbort`는 margin·key·interruptibility를 모두 우회한다.

Preempt 시 Resume Policy:

- `ResumeSamePhase`: snapshot을 Suspended collection에 저장
- `RestartPhase`: phase 초기 상태로 재개하도록 저장
- `AbortOnPreempt`: 즉시 Aborted

현재 Goal을 preempt할 새 Goal의 activation 준비가 실패하면 기존 Goal은 계속 Active다. 반쪽 preemption은 허용하지 않는다.

Suspended Goal이 이미 8개인 상태에서 새 suspension이 필요하면 일반 preemption을 거부한다.

이 상태의 Emergency preemption은 다음 순서로 실행한다.

1. replacement activation 준비를 완료한다.
2. Suspended Goal 중 Arbitration Key가 가장 나쁜 Goal을 `Aborted` 처리한다.
3. 현재 Goal을 Suspended collection에 저장한다.
4. eviction을 audit event로 기록한다.

replacement activation 준비가 실패하면 eviction과 현재 Goal 변경을 모두 금지한다. `Server ForceAbort`는 현재 Goal을 저장하지 않으며 기존 Suspended Goal을 evict하지 않는다. `AbortOnPreempt`는 Suspended slot을 소비하지 않는다.

## 5.5 Suspended Resume

Suspended Goal 재개 순서는 Goal Registry의 `same_selection_key`를 따른다.

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
| Knowledge revision 변화 | 아니오 |
| Candidate score 변화 | 아니오 |

Goal Registry `revision_contract.increase_on`은 `interruptibility_changed`, `resume_policy_changed`를 포함한다. 이 authority patch는 완료됐지만, revision을 실제로 발행·검증하는 Goal Runtime과 hostile test가 구현되기 전에는 Goal Runtime Gate와 최종 Freeze를 통과할 수 없다.

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
  after_seconds: 2.0
```

Production 초기 timer authority:

| Goal/Phase | `after_seconds` | Timeout 결과 |
|---|---:|---|
| `InvestigateDisturbance/Orient` | `2.0` | `Failed` |
| `InvestigateDisturbance/Navigate` | `15.0` | `Failed` |
| `InvestigateDisturbance/Search` | `8.0` | `Return` |
| `EnforceBoundary/Observe` | `4.0` | `Failed` |
| `EnforceBoundary/Interact` | `6.0` | `Resolve` |
| `CombatEngage/Search` | `5.0` | `Return` |

정상 event가 먼저 발생하면 현재 token에 결속된 typed event transition을 즉시 평가한다. event 도착만으로 timer를 취소하지 않는다. guard와 effect가 모두 승인되고 phase exit 또는 terminal 상태 변경이 실제 commit된 뒤에만 기존 phase timer를 취소한다. guard false·provider 누락·effect 거부·same-phase 결과에서는 기존 deadline과 timer를 유지한다. 위 값은 `goal_registry_v1.yaml`의 production 초기 authority이며 telemetry·playtest에 따른 조정은 Registry version/hash 변경으로 관리한다.

규칙:

- `after_seconds`는 finite positive float이며 `contract_duration_ms = ceil(after_seconds × 1000)`로 변환한다.
- phase entry에서 `deadline = server_monotonic_world_seconds + contract_duration_ms / 1000.0`로 고정한다. `now < deadline`은 미만료, `now == deadline`과 `now > deadline`은 만료다.
- Unreal adapter는 같은 `UWorld`의 `GetTimeSeconds()`와 `FTimerManager` game-time을 사용한다. World pause 중 timeout도 멈추고 time dilation이 적용된 값을 그대로 따른다. `GetRealTimeSeconds`, OS wall clock, client-local clock을 금지한다.
- Timer countdown 자체는 `goal_revision`을 올리지 않지만 deadline 계약 값 변경은 revision을 올린다.
- `ResumeSamePhase` suspension은 phase timer를 pause하고 `remaining_ms = max(0, deadline_ms - suspended_at_ms)`를 uint64로 저장한다. resume은 stored remaining으로만 재무장하며 full duration을 적용하지 않는다.
- `RestartPhase` suspension은 이전 remaining을 폐기한다. resume은 중단됐던 같은 phase의 `OnEnter` 상태를 다시 만들고 Registry full duration으로 재무장하며 Goal initial phase로 되돌리지 않는다.
- 승인된 transition이 phase exit 또는 terminal을 실제 commit하면 timer를 취소한다. guard false·provider 누락·effect 거부는 state와 timer를 바꾸지 않는다. `remain_and_replan` 같은 승인된 same-phase effect도 phase generation·deadline·timer를 재시작하거나 취소하지 않는다.
- Expiry는 현재 token에 결속된 typed timer trigger를 정확히 한 번 queue한 뒤 Registry order 평가를 요청한다. expiry 자체나 `phase_timeout`이라는 guard 이름만으로 guard를 true로 만들지 않는다. trusted guard provider가 없거나 판정을 제공하지 않으면 fail-closed한다.
- 같은 Game Thread pump batch의 event와 expiry는 도착 순서가 아니라 Registry row `order` 오름차순으로 경쟁한다. 낮은 row guard가 false이거나 provider가 판정을 제공하지 않으면 state와 timer를 유지한 채 다음 eligible row를 평가한다. 첫 승인 row 하나만 적용하며, 그 row가 phase exit 또는 terminal을 commit했을 때만 이전 phase generation의 나머지 trigger를 폐기한다. same-phase 결과는 기존 generation·deadline·timer를 유지한다.
- Suspended 동안 phase timer는 진행하지 않지만 Goal의 별도 authoritative absolute deadline은 계속 진행한다. resume validation 시 이미 지난 absolute deadline은 Goal을 terminal 처리한다.
- Save/Load의 제한 Core 산출물은 full Goal save가 아니라 **versioned timer snapshot**이다. snapshot은 format version, Goal Registry SHA-256, Goal instance/type/lifecycle, phase와 phase generation, Goal revision, timer ID, contract duration, `remaining_ms`, Resume Policy를 보존한다.
- Restore command는 persisted snapshot 외에 호출 시점의 비영속 `expected_current_token` CAS를 요구한다. startup restore는 `expected_unbound`, 실행 중 restore는 current Goal instance·phase generation·Goal revision·runtime epoch exact match여야 한다.
- Load는 format/hash/Goal·phase·timer spec/duration/range/Resume Policy와 expected token을 전부 검증한 뒤에만 원자적으로 교체한다. mismatch는 live state를 바꾸지 않는다. restore가 먼저 성공하면 새 runtime epoch를 발급하고 old handle·queued callback을 무효화한 뒤 active timer 하나만 재무장한다. Suspended snapshot은 resume 전까지 arm하지 않는다.
- Load 전후 server monotonic epoch가 달라도 stored remaining만 사용하며 wall clock이나 offline elapsed time을 추정하지 않는다.
- suspend/load가 pump보다 먼저 token을 바꾸면 이전 callback을 폐기한다. pump가 먼저 state를 바꾸면 stale suspend/load CAS를 거부한다.
- `goal_registry_v1.yaml`은 transition 41개를 typed trigger 35 event + 6 timer로 고정하며 legacy `event` 필드를 금지한다.
- 현 consumer는 authority commit `2770b4a5a3aebd430420e5b330441aa044cc7db5`의 generated C++ binding과 source hash를 lock으로 고정한다. 새 bytes에는 새 provenance commit이 필요하다.
- 현재 `GoalFsmRuntimeTests.cpp`는 RED 테스트만 존재하고 Runtime `.h/.cpp`와 Timer Component는 없다. 따라서 Contract Dispatcher·Timer Core, Unreal Timer Core, Production Integration은 모두 아직 PASS가 아니다.
- 29개 gameplay guard와 2개 effect의 executable provider, 전체 arbitration/save archive, production Knowledge(`Belief`)/Goal/Target의 종류와 식별 정보(`Typed Target`) producer가 닫히기 전에는 `Gameplay Goal FSM Runtime PASS`를 선언하지 않는다.
- Companion UE 문서의 Phase 표가 Registry와 다르면 Registry transition을 우선하며, UE 문서는 수기 stale 표를 구현 근거로 사용하지 않는다.

# 6. Neural Policy와 Post-process

Neural Policy는 Candidate별 `raw score`와 parameter proposal을 출력한다. Post-process는 Switch Cost·OOD·Calibration을 적용하고, abstain 시 Utility Baseline과 Goal fallback을 순서대로 실행한다.

## 6.1 Policy Interface와 Parameter Proposal

> **상태:** score·parameter 2-output은 `ACTIVE RC5`, `tactical_context`를 포함한 OOD interface는 `POST-RC5`다.

Reference Model의 정확한 Layer 구조와 bounded scorer 구현은 [구현 계획의 §3](implementation-plan.md#reference-model)을 따른다.

이 절은 Runtime이 집행하는 출력·mask·parameter interface를 소유한다.

V1 OOD Runtime을 포함하는 목표 ONNX output 계약은 다음 세 개다.

```text
candidate_raw_scores             float32 [B,272]
candidate_parameter_proposals    float32 [B,272,4]
tactical_context                 float32 [B,128]
```

`tactical_context`는 Fusion의 `h`와 동일한 FP32 Tensor이며 별도 projection이나 post-export 변환을 적용하지 않는다. OOD asset fit, PyTorch 평가, ONNX Runtime, Unreal NNE가 이 동일 output을 사용한다.

현재 RC5 Schema Appendix는 앞의 두 output만 포함한다. 따라서 현재 Schema로는 OOD Runtime Gate를 통과할 수 없다.

후속 Schema patch는 `tactical_context` output을 구조화된 원본에 추가한다. generated Python/C++/docs, UE descriptor, Golden output, Decision Contract Hash도 같은 patch에서 갱신한다.

`target_mask`, `event_mask`, `candidate_mask`는 attention·pooling·loss에 사용한다. Candidate Builder는 hard constraint를 소유한다.

ONNX 출력은 272개 row로 고정한다. invalid row는 loss·선택·parameter decode에서 제외한다.

ONNX가 `candidate_mask` 입력을 제거하지 않도록 score의 마지막 연산에 `Where(candidate_mask, score, 0)`를 적용한다. parameter의 마지막 연산에는 `Where(candidate_mask.unsqueeze(-1), parameter, 0)`를 적용한다.

invalid row의 score와 parameter는 정확히 0이어야 한다. Runtime은 valid row만 사용한다.

### Candidate Parameter Proposal

모델은 Candidate별 normalized parameter 4개를 출력한다. 의미와 범위는 Skill Registry가 소유한다.

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
- interrupt 불가능한 변경은 hard mask한다.
- 모든 비용은 dimensionless `[0,1]`이다.
- 계수 또는 λ가 바뀌면 `postprocess_version`을 올린다.
- Capture/Dataset은 네 boolean component를 Candidate별로 저장하고 Validator가 위 공식으로 재계산해야 한다.

## 6.3 Selection, OOD, Calibration 순서

> **상태:** Selection·Switch Cost는 `ACTIVE RC5` 구현 범위다. Runtime OOD·Calibration 승격은 `POST-RC5`다.

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

Schema·Enum·Registry·Model·Decision Contract Hash 불일치는 `ContractMismatch`로 처리한다.

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

Calibrator는 **Adjusted Score로 최종 선택된 행동**을 기준으로 학습한다.

## 6.4 Version과 Hash 책임 분리

> **상태:** [generated decision hash contract](contract-appendices.md#d7-hash-decision_contract_hash)는 `ACTIVE RC5`다.
>
> 아래 `ANPCFEAT1`·`ANPCDEC3` 공식은 `POST-RC5`다.

| 값 | 포함 내용 |
|---|---|
| `candidate_set_hash` | Target Handle/order, target_mask 17 bit, candidate_mask 272 bit |
| `postprocess_version` | Switch Cost 공식·계수·softmax 통계 규칙 |
| `calibration_version` | Calibrator weights, thresholds, OOD asset |
| `feature_contract_hash` | schema + skill/goal registry + normalization + slotter + postprocess contract; model/calibration 제외 |
| `model_sha256` | `policy.onnx` raw bytes SHA-256 |
| `decision_contract_hash` | feature contract + model + calibration/OOD asset hash |

`postprocess_version`은 `candidate_set_hash`에 포함하지 않는다. Dataset Capture source의 Decision Contract와 새 Model을 학습하는 Feature Contract를 같은 값으로 취급하지 않는다.

후속 patch의 canonical hash는 decoded raw 32-byte digest를 이어 붙인다.

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

- 각 입력은 decoded raw 32-byte digest다.
- field order는 위 순서로 고정하고 length prefix는 사용하지 않는다. magic/version 변경 없이 field를 추가하지 않는다.
- 현재 RC5 generated serializer는 active decision hash contract의 증거로 유지한다. 위 `ANPCDEC3`는 Schema/Generator/Python/C++/Golden을 함께 올린 뒤에만 active다.
- Python/C++은 `ANPCFEAT1`과 `ANPCDEC3` input bytes 및 digest를 byte-identical Golden으로 검증한다.

---

# 7. 비동기 추론과 Atomic Commit

Commit Coordinator는 비동기 추론 응답을 최신 상태로 검증하고 Skill을 원자적으로 시작한다.

## 7.1 Request 상태

> **상태:** 아래 stale-bound envelope와 material revision 규칙은 `POST-RC5`다. 현재 RC5 smoke는 Runtime completion 증거로 사용할 수 없다.

NPC별 상태:

- `next_decision_id`: uint64 단조 증가
- `commit_eligible_decision_id`: 최대 1개
- `active_cancellation_token`
- `dirty_flag`
- `urgent_flag`
- `latest_snapshot_revision`: Commit-relevant material state가 바뀔 때만 증가하는 uint64

각 inference request/response envelope는 다음 값을 저장한다.

- `snapshot_revision:uint64`
- `snapshot_captured_at_monotonic_ms:uint64`
- `request_deadline_monotonic_ms:uint64`

`snapshot_revision`은 Commit에 영향을 주는 material state 변경에서만 증가한다.

V1 request deadline:

- Budget: `request_deadline_budget_ms = 40`
- 계산: `checked_add(snapshot_captured_at_monotonic_ms, 40)`
- 범위: Feature Build → queue → inference → Post-process → Commit 시작
- Commit 조건: `current_server_monotonic_ms ≤ request_deadline_monotonic_ms`
- overflow: 요청 미발행, `DeadlineExpired`
- deadline 초과: 응답·Execution Plan 폐기, `DeadlineExpired`

Budget과 계산 방식은 Decision Runtime Contract와 Decision Contract Hash에 포함한다. Appendix E도 같은 capture-to-Commit 시계를 사용한다.

Material change:

- Active Goal instance/revision 변경
- Candidate membership/order/mask 또는 Target `IdentityKey`/Generation 변경
- SoundEvent·LastKnownPosition·Waypoint·WorldPosition처럼 exact match가 필요한 Target Revision 변경
- Entity Knowledge Revision 변경이 현재 Perception/LOS, Target 유효성, Candidate mask, Skill precondition을 바꿈
- Resource generation/availability 변경
- Skill interruptibility 또는 authoritative deadline 변경
- 피격·폭발·강제 Goal 같은 urgent event

Non-material change:

- 로그·telemetry counter와 model input이 아닌 presentation state
- 같은 Entity `IdentityKey`/Generation의 새 Knowledge Revision이면서 현재 허용 Perception이 유지되고 Candidate membership/order/mask와 Commit precondition이 그대로인 경우
- 위 Entity 갱신 중 Schema에서 `staleness_class: continuous_nonmaterial`로 구조화한 float feature만 바뀐 경우

허용된 Entity Revision 갱신은 `latest_snapshot_revision`을 올리지 않는다. 이 갱신은 `dirty_flag`를 설정한다.

응답의 Candidate Hash는 요청 당시 pending hash와 비교한다. Commit은 최신 Entity Knowledge와 50ms age bound를 다시 검증한다.

다른 Target Kind의 Revision 변경은 material이다. boolean·sentinel·eligibility 변화도 material이다.

V1 `max_nonmaterial_stale_ms`는 `50`이다. 이 값과 Schema staleness allowlist는 Decision Runtime Contract에 포함한다. 두 값 중 하나를 변경하면 Decision Contract Hash를 갱신한다.

현재 RC5 Schema에는 staleness class가 없다. 후속 patch 전에는 수기 field 추정을 금지한다. 후속 patch 전의 non-material stale Commit은 승격 증거로 사용할 수 없다.

## 7.2 In-flight 정책

- NPC당 **Commit 가능한 요청은 항상 1개 이하**다.
- material 일반 변경은 `latest_snapshot_revision`을 증가시키고 `dirty_flag`를 설정한다. 기존 worker가 끝날 수는 있지만 response의 revision이 다르면 `SnapshotSuperseded`로 폐기한다.
- non-material 일반 변경은 `dirty_flag`만 설정하고 기존 요청 완료/Commit 검증 후 최신 snapshot으로 재요청한다.
- 피격·폭발 같은 긴급 이벤트는 새 decision ID를 발급하고 기존 token을 cancel/supersede한다.
- Backend가 물리적으로 이전 worker를 즉시 중단하지 못해 잠시 두 작업이 돌 수는 있다.
- 취소된 decision ID 또는 stale `snapshot_revision`은 영구적으로 Commit 불가하며 응답 도착 즉시 폐기한다.
- 정책은 `latest-commit-relevant-snapshot-only`다.
- continuous drift 허용 응답도 request deadline과 Kind별 최신 Commit 검증을 모두 통과해야 한다.
- Commit은 `current_server_monotonic_ms - snapshot_captured_at_monotonic_ms ≤ max_nonmaterial_stale_ms`를 검증한다.
- 시간 차이는 checked uint64 subtraction으로 계산한다.
- clock 역행, subtraction overflow, 50ms 초과는 `SnapshotSuperseded`로 처리한다.
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
| Entity | Identity/Generation 일치 후 **최신 유효 Knowledge Revision**으로 재검증. Revision-only 갱신 허용은 §7.1의 `continuous_nonmaterial` 조건과 50ms age bound를 모두 만족할 때만 가능하며, 추적이 필요한 Skill은 현재 Perception/LOS를 다시 검사 |
| SoundEvent | 요청 당시 immutable snapshot revision exact match + TTL |
| LastKnownPosition | immutable snapshot revision exact match. Origin Actor 현재 위치 조회 금지 |
| CoverSlot/SmartObject | Resource Generation + Availability Revision을 CAS하고 성공 시 ReservationId 생성 |
| Waypoint | authored definition/revision exact match |
| WorldPosition | immutable snapshot revision exact match |
| NoTarget | Target 검증 없음 |

응답의 Candidate Hash는 먼저 **pending request에 저장된 hash**와 비교한다. 다르면 `CandidateHashMismatch`로 폐기한다. 최신 월드로 Candidate Hash를 재계산해 최초 비교에 사용하지 않는다.

Reservation:

- 기본 lease 2.0초
- active Skill은 0.5초마다 renew
- 부분 예약과 `StartCommit` 실패는 전부 rollback
- 후보 생성 전에는 ReservationId가 없으며 ResourceGeneration과 AvailabilityRevision만 존재

## 7.4 모델 거부·실패 후 Fallback

다음 조건은 Neural 결과를 폐기하고 fallback을 시작한다.

- Backend timeout/error 또는 `DeadlineExpired`
- `ContractMismatch`, `DecisionSuperseded`, `SnapshotSuperseded`
- OOD·Calibration abstain
- Candidate가 없거나 Commit 검증 실패

처리 순서는 다음과 같다.

1. 거부된 응답과 그 Execution Plan은 폐기한다.
2. 기존 Skill이 `CanContinue(LatestBelief, LatestGoalRevision)`를 통과하면 새 결정을 준비하는 동안 유지한다.
3. 더 최신인 commit-eligible 요청이 없을 때만 최신 Knowledge·Goal로 새 decision ID와 Candidate를 만든다. 오래된 요청의 Tensor나 Candidate Hash를 재사용하지 않는다.
4. `utility_baseline_v1.0.0`이 같은 Target Slot, Candidate, hard mask와 Switch Cost로 후보를 고른다. Neural OOD·Calibration은 적용하지 않지만 §7.3 Commit 검증은 그대로 통과해야 한다.
5. Utility에도 valid Candidate가 없거나 Commit이 실패하면 Goal Registry의 결정론적 fallback을 사용한다.

긴급 이벤트가 새 요청을 이미 만들었다면 이전 요청의 실패는 telemetry만 남기고 별도 fallback 결정을 만들지 않는다. Fallback reason, 기존 Skill 유지 여부, Utility 결과와 최종 Commit 실패 코드를 모두 기록한다.

## 7.5 Commit 실패 코드


- `DecisionSuperseded`
- `SnapshotSuperseded`
- `DeadlineExpired`
- `ContractMismatch`
- `CandidateHashMismatch`
- `GoalRevisionChanged`
- `TargetGenerationChanged`
- `TargetBeliefInvalid`
- `PreconditionChanged`
- `ReservationConflict`
- `PartialReservationRolledBack`
- `StartCommitFailed`
- `AuthorityRejected`

## 7.6 멀티플레이

- 서버가 Perception, Knowledge, Goal, Inference 요청, Post-process, Commit을 소유한다.
- 클라이언트는 선택 Skill, typed target Net reference 또는 snapshot, parameter, server start time을 복제받는다.
- 피해·이동 권한·아이템·관계·Goal은 서버만 변경한다.

---

# 8. Hidden Information 경계

전술 판단은 NPC의 Perception과 Knowledge를 사용한다.

## 8.1 원칙

- 물리·충돌·피해·Actor 생존 검증은 Ground Truth를 사용한다.
- 전술 선택·경로 목표·추적 판단은 Knowledge를 사용한다.

## 8.2 Target Kind별 Commit 정보

| Kind | 허용 정보 | 전술 판단/목표 갱신에 금지되는 정보 |
|---|---|---|
| Entity | identity/generation, 최신 유효 Knowledge, 현재 허용 Perception/LOS, 물리·피해 권위 판정 | Sight Lost 이후 숨은 Transform/Velocity |
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
- 공격의 collision/damage는 authoritative physics를 사용한다. 전술 위치는 Knowledge에서만 가져온다.

## 8.4 Path/LOS Pair Feature

- `path_distance`, `path_reachable`, `LOS`는 Target Runtime Snapshot의 **Believed Position**으로 계산한다.
- LastKnownPosition과 SoundEvent는 Actor pointer 없이 snapshot 좌표로 계산한다.
- Python 합성 데이터도 동일 규칙으로 Feature를 만든다.

---

# 9. 데이터·학습·Baseline

학습 Record는 Runtime과 같은 Tensor·Candidate Mask·Switch Cost 계약을 사용하고 label·출처를 함께 저장한다. Dataset Validator는 split 누출과 숨은 정보 입력을 차단한다. Utility Baseline은 비교군과 fallback을 담당한다.

## 9.1 데이터 계층

- Silver: 절차 생성, LLM 교사, 자동 라벨
- Gold: 사람 시연·복수 acceptable label·선호 비교
- Live: 실제 rollout, 이상 행동 신고, DAgger intervention

LLM과 생성기는 Silver 데이터를 공급한다.

### 9.1.1 Teacher LLM Silver Label 생성

Teacher LLM은 개발 단계에서 Decision Snapshot의 행동 후보를 판정해 Silver label을 만든다.

#### 역할과 처리 흐름

규범 Profile ID는 `teacher_silver_v1.0.0`이다.

`ML/config/teacher_profile_v1.yaml`은 다음 값을 잠근다.

- provider
- provider가 제공하는 exact model identifier와 revision
- prompt template SHA-256
- response schema version
- decoding config
- prompt variant
- consensus version
- reason-tag allowlist

V1 `sample_count`는 `5`다.

```text
Decision Snapshot → request 생성 → 5개 응답 수집 → strict parse
→ 합의·검증 → Dataset Record 변환 → 학습 또는 Gold review queue
```

Valid response는 최소 3개다. Provider 응답의 비결정성을 감사할 수 있도록 request와 response를 annotation shard에 보존한다.

#### 입력

`ML/teacher/schemas/teacher_request_v1.schema.json`은 요청의 field·type·range와 `additionalProperties=false`를 소유한다. 이 Schema와 Golden parity test가 구현되기 전 Teacher Silver 생성을 시작할 수 없다.

Request builder는 Dataset Record의 10개 입력 Tensor와 generated Schema/Registry를 다음 view로 변환한다.

| View | 내용 |
|---|---|
| `global` | Role·Personality·Relationship, active Goal·Phase를 포함한 model-visible global feature |
| `targets` | slot, kind와 model-visible target feature |
| `events` | event type, target slot과 model-visible event feature |
| `candidates` | index, Skill, Target, `candidate_mask`, switch-cost terms |
| `current_action` | 현재 Candidate index 또는 null |

Request에는 다음 값과 위 view만 둔다.

- `schema_version`
- `request_content_hash`
- `teacher_profile_sha256`
- `input_content_hash`
- `feature_contract_hash`
- `candidate_set_hash`

Feature 이름과 enum 이름은 generated contract에서 가져온다.

Request에는 Runtime Handle stable ID, Actor 이름, absolute world position, future event, hidden Ground Truth를 넣지 않는다. Role·Personality·Relationship은 `global_state`에 포함된 값만 사용한다.

View builder는 원본 Tensor·mask·switch term과 lossless Golden parity를 통과해야 한다. `request_content_hash`는 해당 필드만 제외한 request object를 RFC 8785 JCS로 직렬화한 UTF-8 byte의 SHA-256이다.

#### Strict 구조화 출력

`ML/teacher/schemas/teacher_response_v1.schema.json`은 다음 응답을 강제한다.

```json
{
  "schema_version": "teacher_response_v1",
  "request_content_hash": "<lowercase sha256>",
  "acceptable_candidate_indices": [17, 34],
  "preference_pairs": [[17, 34]],
  "abstain": false,
  "ambiguous": false,
  "reason_tags": ["<allowlisted_tag>"]
}
```

| Field | 규칙 |
|---|---|
| `request_content_hash` | lowercase hex 64자, 현재 request와 일치 |
| Candidate index | `uint16`, `0..271`, valid mask의 부분집합 |
| `acceptable_candidate_indices` | unique, 오름차순 |
| `preference_pairs` | 서로 다른 두 valid index, lexicographic sort, duplicate·reverse pair 금지 |
| `abstain`, `ambiguous` | boolean |
| `reason_tags` | Profile allowlist, unique, NFC UTF-8 byte 오름차순 |

다음 조건 중 하나라도 발생하면 응답 전체를 invalid로 처리한다.

- Unknown field
- hash 불일치
- duplicate
- masked index
- self pair
- reverse pair

`abstain=true`이면 acceptable candidate와 preference pair를 비워야 한다. Teacher self-confidence와 free-text rationale는 training label로 받지 않는다.

Parameter Silver는 procedural/human path가 소유한다. Teacher record는 `parameter_target_norm=+0.0`, `parameter_label_mask=false`를 사용한다.

#### 복수 응답 합의

Valid response 수를 `m`이라 하고 `m >= 3`이어야 한다. 합의 임계값은 `floor(m/2)+1`이다.

- acceptable candidate와 `abstain`은 각각 임계값 이상일 때 채택한다.
- acceptable candidate와 `abstain`이 동시에 채택되면 hard conflict다.
- `ambiguous`가 채택되면 Gold review queue로 보낸다.
- Preference pair는 같은 방향이 임계값 이상이고 반대 방향이 동률·우세하지 않을 때 채택한다.
- `reason_tags`는 임계값 이상인 tag만 채택한다.
- `annotator_agreement`는 acceptable set의 모든 pairwise Jaccard 평균이다. empty–empty는 1, empty–nonempty는 0이다.
- `label_confidence = clamp(valid_response_count / sample_count × annotator_agreement, 0, 1)`이다.

다음 조건 중 하나라도 발생하면 record를 training에서 제외한다.

- `label_confidence < 0.60`
- acceptable candidate와 `abstain`이 모두 합의되지 않음
- preference cycle
- hard conflict

합의된 `abstain`은 acceptable mask가 0인 `abstain-only` record로 보존한다. `sample_count`를 변경하면 새 Teacher Profile version을 발급하고 confidence 계약을 갱신한다.

#### 검증·사용 범위

Teacher는 hard mask와 hard rule을 바꿀 수 없다. Utility Baseline 불일치는 active learning과 Gold review 우선순위에 사용한다.

Teacher Silver는 `train`과 `validation`에만 사용한다. `calibration`, `general_test`, `ood`, `critical`의 정답으로 사용하는 것을 금지한다.

Teacher Profile은 고정된 `teacher_gold_validation_manifest.json`으로 승격한다.

- Gold Validation만 사용하고 다른 split과 family를 격리한다.
- 12개 Role×Goal group마다 100개 이상을 사용한다.
- strict response valid rate ≥95%
- Any-Acceptable Recall ≥95%
- macro Role×Goal acceptable-set Jaccard ≥0.80
- hard-invalid candidate 선택 0건

하나라도 실패하면 해당 Profile을 차단한다. Prompt, model, decoding, consensus를 바꾸면 새 Profile version으로 다시 평가한다.

#### Dataset Record와 annotation provenance

§9.9의 기존 Dataset Record field를 다음 값으로 채운다.

| Field | Teacher Silver 값 |
|---|---|
| `acceptable_candidate_mask` | 합의된 acceptable set, abstain이면 모두 0 |
| `preference_pairs` | 합의된 pair |
| `parameter_target_norm` | FP32 positive zero `[272,4]` |
| `parameter_label_mask` | false `[272,4]` |
| `selected_is_acceptable` | null |
| `reason_tags` | 합의된 allowlisted tag |
| `source_type` | `silver` |
| `prompt_or_teacher_version` | `teacher_silver_v1.0.0:<teacher_profile_sha256>` |
| `annotator_agreement`, `label_confidence` | 위 합의 결과 |
| `generator_template_version` | scenario source template/version |

`teacher_profile_sha256`는 Profile raw byte의 SHA-256이다.

`canonical_response_hash`는 Valid response object를 RFC 8785 JCS로 직렬화한 UTF-8 byte의 SHA-256이다.

`annotator_set_hash`는 canonical response raw32 hash를 오름차순으로 정렬한 뒤 이어 붙인 byte의 SHA-256이다.

Annotation shard는 `annotator_set_hash`를 row key로 사용한다.

각 row는 다음 값을 기록한다.

- `source_snapshot_shard_sha256`
- `episode_id`
- `decision_id`
- `input_content_hash`
- `request_content_hash`
- Profile hash
- canonical response hash
- provider raw payload hash
- provider raw payload 위치

Raw payload hash는 저장한 provider response body exact byte의 SHA-256이다.

Dataset mapper는 source snapshot shard와 annotation shard를 다음 key로 join한다.

`source_snapshot_shard_sha256 + episode_id + decision_id + input_content_hash`

Dataset mapper는 Snapshot의 Tensor, `candidate_set_canonical_bytes`, mask, switch term을 Dataset Record에 복사한다. 복사한 값으로 hash를 다시 계산한다.

Dataset Record의 `annotator_set_hash`는 annotation row를 가리킨다. Teacher Silver의 Loss `source_weight`는 `0.25`다.

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

- Knowledge Snapshot
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

- V1은 Event Buffer, Goal Instance, Knowledge TTL 기준 시각, Skill 실행 상태를 서버 Save에 저장한다.
- Suspended Goal phase timer는 §5.9의 `remaining_ms`와 Resume Policy를 저장하고, absolute Goal deadline은 저장 시점의 remaining duration과 authority revision으로 복구한다.
- Load 시 만료된 Knowledge/Event는 제거하고 Reservation은 재획득한다.
- Model/Calibration/Registry hot-swap은 새 Decision Contract Hash 활성화 전에 dry-run validation과 rollback asset을 요구한다.
- Pending inference는 supersede하고 새 계약으로 재요청한다.
- rollback 시 해당 버전의 Model, Calibration, Schema/Registry 생성 코드 세트를 함께 복구한다.

## 9.8 ML 학습 파이프라인 구현

학습 파이프라인과 split 공개 시점은 [구현 계획의 §4](implementation-plan.md#ml-pipeline)가 소유한다.

## 9.9 Dataset Record v2

저장 형식은 Zstandard 압축 Parquet이다. Tensor는 Arrow fixed-size list로 저장한다. 하나의 row는 한 번의 Decision Snapshot이다.

대용량 runtime handle과 debug payload는 별도 replay shard에 저장한다. 학습 shard에는 필요한 hash와 model input만 저장한다.

기존 `anpc_decision_record_v1`은 아래 Switch Cost와 content identity를 재현하지 못한다. 따라서 기존 record를 V1 Neural release 학습 입력으로 승격하지 않는다.

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

- `candidate_set_canonical_bytes`는 Target Handle·Target Mask·Candidate Mask의 hash 입력을 보관하는 non-model metadata다.
- Dataset Validator는 이 byte에서 `candidate_set_hash`를 다시 계산한다.
- `candidate_set_canonical_bytes`를 모델에 전달하는 것을 금지한다.
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

동일 episode, map seed, generator template의 근접 변형은 split을 넘지 못한다.

`input_content_hash` exact duplicate와 `scenario_family_id` 교집합 검사는 여섯 split의 모든 pair 조합에 적용한다.

의도적 Critical mutation은 원본 `source_fixture_id`와 `mutation_id`를 case catalog에 기록할 수 있다.

Critical mutation은 Train·Validation·Calibration·General·OOD와 동일한 `input_content_hash`를 재사용할 수 없다.

In-distribution family는 사전에 검토한 `split_assignment.csv`로 배치한다. 배치 비율은 Train 70%, Validation 10%, Calibration 10%, General Test 10%다.

`test_taxonomy_v1.yaml`은 OOD/Critical family 이름과 최소 분모를 소유한다. 후속 machine-readable `test_case_catalog_v1.yaml`은 실제 OOD 9 family와 Critical 9 family의 허용 사례를 명시해야 한다.

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

명시적 allowlist 충족 여부는 Taxonomy family와 case catalog fixture entry를 함께 검사한다.

`test_case_catalog_v1.yaml`이 생성·Lock·Validator 대상에 포함되기 전에는 OOD/Critical split을 열 수 없다. Appendix E의 Role×Goal 최소 분모와 family 격리는 split 비율보다 우선한다.

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

## 9.12 Training Config와 Checkpoint·Report

Training Config, checkpoint 선택 및 Training Report 절차는 [구현 계획의 §5](implementation-plan.md#training-config)가 소유한다.

## 9.13 Calibration과 OOD Asset

Checkpoint를 동결한 뒤 순서대로 수행한다.

### OOD

- in-distribution Gold Train의 유효 ONNX output `tactical_context h[128]`만 사용한다.
- `LedoitWolf(assume_centered=false)`로 mean과 shrinkage covariance를 구하고 precision matrix를 저장한다.
- §6.3의 squared Mahalanobis `d2`에 대한 empirical `q95_train`, `q99_9_train`을 저장한다.
- `q99_9_train - q95_train < 1e-6`이면 asset fit 실패다.
- Runtime OOD 공식은 §6.3을 그대로 사용한다.
- OOD 승격 KPI는 Runtime threshold `OOD=0.80`에서 계산한다.

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
- group override 승격 조건을 충족하지 못하면 global threshold를 적용한다.
- 실제 적용 threshold에서 각 필수 Role×Goal group은 `accepted_count ≥100`을 만족해야 한다.
- 각 필수 Role×Goal group은 `coverage ≥0.80`도 만족해야 한다.
- 각 필수 Role×Goal group의 one-sided Wilson 95% risk upper bound는 `≤0.10`이어야 한다.
- global threshold 또는 실제 적용 threshold의 필수 group Gate 하나라도 실패하면 Release Gate를 실패시킨다. 0-coverage/0-accepted group을 fallback 성공으로 간주하지 않는다.
- accepted count가 0이면 risk를 0으로 두지 않고 해당 threshold를 부적격 처리한다.

risk는 threshold 이상으로 accept된 상태 중 선택 candidate가 acceptable set 밖인 비율이다.

Capture 당시 source policy의 `selected_is_acceptable` 값은 분석에만 사용한다.

최종 Calibrator label은 frozen checkpoint로 candidate를 다시 선택해 계산한다. 선택 결과의 acceptable 여부는 `acceptable_candidate_mask`에서 다시 계산한다.

Calibration/OOD asset은 다음 값을 포함한다.

- scaler
- weights
- bias
- group thresholds
- mean
- precision
- `q95`
- `q99.9`
- fit dataset hash
- checkpoint hash
- library version

General Test와 OOD Test는 asset 동결 후 ECE, Brier, risk/coverage, OOD recall, OOD FPR만 평가한다.

## 9.14 Export와 Model Bundle

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

목표 output은 다음 세 개다.

- `candidate_raw_scores float32 [B,272]`
- `candidate_parameter_proposals float32 [B,272,4]`
- `tactical_context float32 [B,128]`

Batch 축만 dynamic으로 허용한다. 나머지 축은 고정한다. OOD Runtime 승격은 세 번째 output을 등록한 Schema patch부터 적용한다.

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

## 9.15 구현 저장소 명령과 Phase 구분

구현 저장소 CLI와 Phase별 적용 범위는 [구현 계획의 §6](implementation-plan.md#implementation-cli)가 소유한다.

# 10. Schema Generator와 Parity

YAML Schema와 Registry에서 Python 코드·C++ header·Appendix를 생성한다. Parity test는 같은 fixture의 byte와 float 결과를 Python↔Unreal에서 비교한다.

## 10.1 Single Source와 실행 산출물

Runtime/학습 Tensor의 단일 원본은 다음 세 YAML이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

평가 family와 Critical/OOD 분모는 `contracts/current/test_taxonomy_v1.yaml`이 소유한다.

실제 OOD/Critical fixture allowlist는 후속 `contracts/current/test_case_catalog_v1.yaml`이 소유한다. case catalog를 추가할 때 Generator·Catalog·Lock·Archive·Validator 대상에도 즉시 포함한다.

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

정리된 `main`에서는 YAML 4개와 생성 Python/C++ 계약만 유지한다. Generator·Golden·Harness는 `archive/full-harness-v0.4.6`에 보존한다.

계약을 변경할 때는 보관본의 Generator로 전체 산출물과 검증 증거를 재생성한다. 재생성한 산출물과 증거는 새 버전으로 승격한다. `main`의 생성 파일을 수동으로 고치는 것을 금지한다.

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

Cross-Environment Release Pipeline과 단일 release 명령은 [구현 계획의 §7](implementation-plan.md#release-pipeline)이 소유한다.

## 10.6 RC5 구조화 계약 Remediation 상태

각 항목의 현재 authority 상태와 남은 후속 작업을 구분한다.

| ID | 현재 상태 | 목표·완료 내용 | Freeze 집행 |
|---|---|---|---|
| `SCHEMA-OUTPUT-001` | output 2개 | `tactical_context float32 [B,128]` 추가 | Schema semantic validation + PyTorch/ORT/NNE 3-output parity |
| `GOAL-TRIGGER-001` | 완료 — Registry `1.1.0` | 35 event + 6 finite timer typed trigger, legacy `event` 0 | Registry validator + 41-row C++17 full-field Golden parity |
| `GOAL-REVISION-001` | 완료 — Registry `1.1.0` | `interruptibility_changed`, `resume_policy_changed` 포함 | Python/C++ generated policy + C++17 Golden parity |
| `IDENTITY-EQUALITY-001` | Pair Feature source가 `handle equality`/`typed handle equals`로 모호 | `same_as_current_target`와 `same_as_current_skill_target`에 `comparison_key: identity_key` 구조화 | generated helper + Revision-only mutation Golden |
| `ASYNC-STALE-001` | continuous float drift allowlist와 age bound가 구조화되지 않음 | Entity Revision-only `staleness_class`, `max_nonmaterial_stale_ms=50`, exact-match Target Kind를 Decision Runtime Contract에 추가 | stale boundary·Kind별 Revision Runtime/Golden test |
| `ASYNC-DEADLINE-001` | request deadline field와 40ms 계산이 구조화되지 않음 | `request_deadline_budget_ms=40`, checked absolute deadline, capture-to-Commit clock을 Decision Runtime Contract에 추가 | 39/40/41ms boundary·overflow·deadline miss Runtime test |
| `FALLBACK-001` | timeout·abstain·supersede의 fallback 규칙과 failure code가 여러 절에 분산 | `CandidateHashMismatch`를 포함한 failure enum과 reason→기존 Skill 유지→latest snapshot Utility→Goal fallback 순서를 Decision Runtime Contract에 구조화 | hash mismatch·timeout·OOD·stale·urgent race Runtime test |
| `EVENT-MOVING-001` | `source_moving_probability`가 bool | 확률이면 ratio `[0,1]`; boolean 의미를 유지하려면 `source_is_moving`으로 rename | Schema migration + Float Feature parity |
| `TEST-CATALOG-001` | family taxonomy만 존재 | 실제 case allowlist YAML 추가 | Catalog/Lock/Archive validation |

Auto-generated marker 내부를 수동 편집해 위 문제를 숨기지 않는다. 구조화된 원본과 Generator를 먼저 고치고 Appendix·Python·C++·Golden·Manifest를 함께 재생성한다.


---

# 11. 구현·승인 문서

- Phase·Owner·일정과 최종 승인 체크리스트: [AI Native NPC 구현 계획](implementation-plan.md)
- 생성 Schema·Registry 계약과 품질·안전·성능 승인 기준: [AI Native NPC Contract Appendices](contract-appendices.md)
