# AI Native NPC — Unreal Engine 5.7 / Manny·Quinn 공간·시야·소리 통합 구현 계획서
## UE 클라이언트·신경망·Goal·Typed Target·Schema 2.0 통합 기준

- 문서 버전: **v0.4.6**
- 문서 상태: **Boss Pattern 선택 안전 Core Handoff까지 PASS / 공통 NPC Runtime·실제 Executor·ML/NNE pending**
- 개정일: 2026-08-06
- 문서 보강: **ML/NNE Implementation Supplement 1 + Requirements Review Remediation Binding Notice**
- 대체 문서: 기존 `ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan.md` v0.3
- 상위 요구사항: `requirements.md`
- 공통 구현 계획: `implementation-plan.md`
- 계약 부록: `contract-appendices.md`
- Tensor 단일 원본: `ai_native_npc_schema_v2_0.yaml`
- Requirements SHA-256: `b8c9e5e3c79d047b55b5a4ad393aae388472baee4aa212ba998e5c0fb6262734`
- Schema YAML SHA-256: `56deff3a5f55ddad30864bcf7df4d100d2f1c5472f86f0a8b9e2599044c37385`
- Boss Pattern Contract SHA-256: `e4f828c114fcc5db1cb04b5d0a6e2b3d29dada7e45c60a3dd18c674baa78c789`
- Skill Registry SHA-256: `08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8`
- Goal Registry SHA-256: `b6ed883e39f8da4f792b2ad4542b4cf7045ff5fe00147a9eba15eac61fa67ac2`
- Test Taxonomy SHA-256: `2c4f911c23c8502231351fd2a1ffc606a04c29c4c3e39ea384099462811dad79`
- ML 구현 프로필: **`policy_arch_v1.0.0` / `policy_train_v1.0.0` / ONNX opset 17**
- Phase 0 판정: **조건부 GO — Utility Baseline/RC5 smoke 한정**
- V1 Neural/OOD 판정: **HOLD — Schema/Goal/Dataset remediation patch 필요**
- Schema 2.0 최종 Freeze: **NO-GO — 생성 계약과 Unreal Runtime Gate 재승격 필요**

> 이 문서는 Unreal Engine 5.7 Third Person 프로젝트에서 Quinn을 플레이어로 유지하고, Manny를 학습 기반 NPC로 적용하기 위한 엔진 구현 기준서다.  
> Tensor·Enum·Padding·Normalization·Hash가 충돌하면 본문보다 `ai_native_npc_schema_v2_0.yaml`이 우선하고, Goal·Target·Commit 책임이 충돌하면 상위 v0.4.6 요구사항이 우선한다.

---

# 0. v0.4.6 Validation Scope & Catalog Closure 반영

최신 리뷰는 타당하다. UE 구현판은 YAML에서 생성된 Appendix·Normalizer·Hash serializer를 직접 소비하며, 문서 표와 런타임 바인딩이 서로 다른 계약을 선택하지 못하도록 변경한다.

RC5에서는 Hash magic 문장·JSON·백틱 수기 복제를 모두 거부하고, Critical Suite 최소 분모를 Taxonomy에서 자동 생성한다.

v0.4.6은 수기 계약 검증 범위를 모든 Lock 대상 active Markdown으로 확장한다.
`docs/history`, `docs/archive`, `generated/docs`는 이 범위에서 제외한다.
Source File Map과 Archive Catalog는 실제 파일 집합에서 생성한다.

v0.4.6까지 누적된 추가 계약:

- PyYAML 전체 Schema validator를 CI에서 실행
- Skill/Goal Registry를 실제 파일로 포함
- generated C++ header를 Unreal Module에서 include
- Slotter의 raw float 정렬 금지, 정수 quantization 사용
- Query/Key LayerNorm + L2 normalize + bounded cosine score
- Skill별 Parameter active mask·unit·min/max/default·Commit clamp
- Contract mismatch는 NNE 실행 전 hard reject
- Continue는 `CanContinue(LatestBelief)`를 반드시 통과
- Entity/immutable/resource Target의 revision 검증 방식 분리
- Candidate Hash에 Target Mask 17 bit 포함
- pending request hash 우선 비교
- Save/Load, hot-swap/rollback, provenance/Active Learning 수명주기 추가

- 규범 테스트 리포트에서 compiler version·duration·stdout/stderr를 제거
- 환경 진단은 `dist/local/`에만 생성하고 패키지에서 제외
- `doc_harness.py release`가 Evidence→Manifest→Lock→Validate→Double Pack을 원자적 순서로 실행
- Generated C++에서 Python과 동일한 quantization, normalizer, bit packing, canonical serialization, SHA-256, parameter clamp 제공
- `tests/generated_cpp_golden_test.cpp`가 Python fixture와 동일한 bytes/hash/float 결과를 검증
- Harness integrity evidence의 tree digest와 file count를 strict validator가 재계산

- 공유 Contract Appendices의 A~D를 YAML·Registry에서 자동 생성하고 strict parity 검사
- Normalizer의 역전 범위, 0 이하 divisor, log1p 정의역, sentinel/valid-range 충돌을 release 전에 hard reject
- Candidate/Decision Hash field order·magic·endianness를 YAML에서 Python/C++ 및 Appendix D.3·D.4로 생성
- Decision Contract Hash Golden parity와 semantic mutation regression test 추가
- 자동 생성 Appendix 밖의 manual hash literal을 strict validation에서 거부
- constant/missing/must_equal/padding_zero 의미 교차검증과 동적 mutation probe 추가

Phase 0은 조건부 GO다.

- 진행 가능: Utility Baseline, Capture, fallback, atomic Commit, 현 RC5 2-output score/parameter smoke
- 보류: 대량 학습 데이터, 최종 Freeze
- 보류 해제 조건: Float Tensor/ONNX parity, Target/Candidate Recall, Atomic Commit, Hidden Leakage Runtime 증거, Requirements Remediation 통과

2026-07-30 보강은 다음 공통 구현 계획을 Unreal 구현 절차로 연결했다.

- [§3 Reference Model](implementation-plan.md#3-policy_arch_v100-reference-model)
- [§4 ML Pipeline](implementation-plan.md#4-ml-pipeline)
- [§5 Training Config·Checkpoint·Report](implementation-plan.md#5-training-config와-checkpointreport)
- [§6 구현 명령과 Phase](implementation-plan.md#6-구현-저장소-명령과-phase-구분)

현 RC5 Schema·Registry 값은 유지한다. Phase 0은 fixture model로 ONNX Import→NNE→score/parameter Post-process→Commit/Fallback 경로를 먼저 증명한다.

## 0.1 Requirements Review Remediation Binding Notice

2026-08-02 상위 기준서는 다음 목표 계약을 추가했으나 현재 RC5 YAML/Generated/UE Appendix에는 아직 반영되지 않았다.

- 세 번째 ONNX output `tactical_context [B,128]`과 binary64/quantized OOD parity
- Dataset Record v2 Switch Cost component와 feature/content/sample hash
- Goal typed trigger·phase timer·revision/arbitration 계약
- `IdentityKey` same-target 비교와 non-material stale 50ms contract
- 실제 OOD/Critical case catalog와 non-vacuous Calibration group Gate

따라서 이 문서의 기존 2-output descriptor, Goal Phase 표, latest-request-only 표현은 **RC5 active 구현 참고**일 뿐 새 목표 계약의 완료 증거가 아니다. 구조화된 Schema/Registry와 Generator를 patch하기 전 수기로 descriptor를 바꾸지 않는다. Requirements §10.6 backlog를 닫고 새 Decision Contract Hash가 발급되면 UE Runtime 절차와 공유 Contract Appendices를 함께 재생성·검증한다.

## 0.2 현재 Unreal 구현 상태

2026-08-06 기준 `D:\Codex-cli\NeuralProject\NeuralGame`은 Boss Pattern 선택 안전 Core를 먼저 구현했다.

```text
완료: Pattern Data Asset→Hard Mask→Tensor→Utility/Commit→one-shot Handoff
대기: 공통 Belief→Goal→17 Target Slot→272 Candidate→Skill Executor
대기: Pattern Phase Executor→Montage/Hitbox/Damage/Root Motion→terminal unlock
대기: Dataset→학습→ONNX/NNE→ranking/tie/OOD/Calibration
```

최종 증거는 Boss Pattern Automation `31/31`, Data Validation `285/0/0`, BossPatternValidation `pass`, generated sync PASS다. 이 결과는 실제 전투 실행과 전체 AI Native NPC Runtime 완료를 뜻하지 않는다.

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
| Boss Pattern Builder/Selector | `Attack(Entity)` 내부에서 별도 32 Pattern row를 mask·rank |
| Boss Pattern Commit/Executor | Pattern hash·revision·resource 검증, Telegraph/Active/Recovery 잠금과 결정론적 전투 실행 |

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
AI-Native-NPC                         # 계약 저장소, 현재 main 핵심 9개
  contracts/current/*.yaml
  generated/python/ai_native_npc_contracts_generated.py
  generated/cpp/AINativeNPCContracts.generated.h
  docs/current/requirements.md
  docs/current/unreal-implementation-plan.md

AI-Native-NPC-Unreal                  # 실제 구현 저장소
  External/AI-Native-NPC/             # 위 계약 저장소의 고정 commit snapshot/submodule
  Config/AINativeNPCContract.lock     # repo URL, commit, YAML/Generated SHA-256

  ML/
    pyproject.toml
    requirements.lock
    configs/
      model_v1.json
      train_v1.json
      phase0_fixture.json
    src/anpc_ml/
      dataset/
      models/
      calibration/
      export/
      evaluation/
    tests/

  Unreal/AINativeNPCDemo/
    AINativeNPCDemo.uproject
    Source/
      AINativeNPCContracts/
      AINativeNPCRuntime/
      AINativeNPCEditor/
      AINativeNPCTests/
    Content/
      AINativeNPC/Models/
      AINativeNPC/Policy/
      Characters/
      Maps/

  Artifacts/ModelBundles/             # Git LFS 또는 artifact registry; manifest는 Git 추적
```

Unreal 구현 저장소는 임의의 최신 계약을 따라가지 않는다. `AINativeNPCContract.lock`이 가리키는 정확한 commit과 SHA만 사용하며, 계약 update는 별도 PR에서 Python/C++ parity와 model re-export 여부를 검토한다.

## 3.1 계약 우선순위

1. `ai_native_npc_schema_v2_0.yaml`: Tensor, enum, padding, normalization, hash
2. 상위 v0.4.6 요구사항: Goal, Target, Candidate, Commit, KPI
3. 본 UE 문서: Unreal 클래스와 실행 방식
4. Data Asset: 튜닝 가능한 센서·Skill 파라미터

## 3.2 Code Generation

Runtime/학습 Tensor 단일 원본:

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
```

평가 family와 KPI 분모는 `contracts/current/test_taxonomy_v1.yaml`이 소유한다.

생성 명령:

```bash
python tools/validate_schema.py
python tools/generate_contracts.py
python tools/generate_golden.py
```

Unreal이 직접 사용하는 산출물:

```text
generated/cpp/AINativeNPCContracts.generated.h
```

Python 학습·Dataset Builder가 사용하는 산출물:

```text
generated/python/ai_native_npc_contracts_generated.py
```

수동 Enum/Index/Parameter 범위 복제를 금지한다. `--check`가 생성 파일의 byte-identical 재현성을 검증한다.

최소 계약 저장소 `main`에서는 위 Python/C++ 생성 파일 두 개를 모두 유지한다. 학습 코드가 YAML을 직접 임의 해석하지 않고 생성 Python의 Enum·Normalizer·Quantization·Candidate Hash·Parameter Decode를 호출해야 Unreal과 같은 값을 만들 수 있다.

## 3.3 CI Gate

- YAML schema validation
- Generated file clean check
- C++ compile-time static assert
- Python shape test
- discrete/hash byte-identical test
- float feature tolerance test
- ONNX/NNE output tolerance test

---

## 3.4 Release 명령

개별 명령을 수동으로 이어 붙이지 않는다.

```bash
python tools/doc_harness.py release --output dist/ai_native_npc_document_harness_v0.4.6.zip
```

이 명령과 Generator는 최소 `main`이 아니라 `archive/full-harness-v0.4.6` 보관본에 있다. 계약 자체를 바꿀 때만 보관본에서 생성 코드와 Golden 갱신, Python/C++17 테스트, Evidence SHA와 Freeze Manifest 갱신, Lock 갱신, strict validation, byte-identical double-pack을 실행한다. Compiler 정보와 시간은 `dist/local` 진단에만 남고 규범 JSON에는 들어가지 않는다.

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

## 10.8 Primary Social Subject

`UNPCGoalManagerComponent`는 관계 Feature가 참조할 Social Subject를 한 명만 선택한다. 선택 Key는 생성 `goal_registry_v1.yaml`의 다음 순서다.

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

정렬에는 `FTargetFeatures` raw float가 아니라 Generated Quantization API를 사용한다.

## 10.9 V1 Goal 고정 범위

V1 구현 대상은 `IdleObserve`, `InvestigateDisturbance`, `EnforceBoundary`, `CombatEngage` 네 개다. `Disengage`, `Escort`는 Post-V1이다. Phase 표와 Allowed Skill은 `goal_registry_v1.yaml`에서 생성하거나 검증한다.

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

## 11.5 정수 Quantized Non-mandatory 정렬

Slotter는 raw float를 직접 비교하지 않는다.

```text
confidence_q = round_half_away(confidence × 1000)
age_q        = round_half_away(age_seconds × 100)
distance_q   = round_half_away(distance_cm / 10)
loudness_q   = round_half_away(loudness × 1000)
```

각 값은 Schema clamp 범위로 제한한다. 정렬 Key는 YAML의 `target_slots.category_sort_keys` 순서를 그대로 사용하며 마지막 tie-breaker는 canonical Target Handle bytes다.

TMap/TSet 순회 순서, Pointer 주소, raw Actor 배열 순서를 정렬 근거로 사용할 수 없다.

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

- 실행 가능한 Skill이 아닌 control candidate다.
- 실행 중 Skill이 있을 때 정확히 하나만 valid다.
- 동일 Skill/동일 Target을 새로 Start하는 Candidate는 mask한다.
- Commit 직전에 `ActiveSkill->CanContinue(LatestBelief, LatestGoalRevision)`를 호출한다.
- Latest Belief/Goal에서 유효하지 않으면 Continue를 거부하고 재판단한다.
- `global_state[17]`은 `current_skill_ContinueCurrentAction_reserved_zero`이며 항상 0이다.
- Executor의 CurrentSkillId에 1을 기록해서는 안 된다.

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

Candidate Set Hash의 magic, field 순서, byte type, endianness와 bit packing은 본문에서 수기로 복제하지 않는다.

규범 계약은 YAML에서 자동 생성되는 **Appendix D.3 `candidate_set_hash`**와 `AINativeNPCContracts.generated.h`만 사용한다. 런타임은 다음 책임만 준수한다.

- Response 수신 시 hash를 pending request에 저장된 CandidateSetHash와 먼저 비교한다.
- 첫 비교를 위해 현재 월드 상태에서 Candidate Hash를 재계산하지 않는다.
- Hash 일치 후 최신 Goal/Belief/Resource 상태를 Target Kind별 Commit 규칙으로 검증한다.
- raw float, score, Switch Cost와 parameter proposal은 Candidate Set Hash에 포함하지 않는다.

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
using namespace AINativeNPC::SchemaV2;
static_assert(GlobalFeatureCount == 128);
static_assert(TotalTargetSlots == 17);
static_assert(CandidateCount == 272);

const std::size_t Index =
    static_cast<std::size_t>(EGlobalFeature::self_health_norm);
Buffer[Index] = static_cast<float>(NormalizeGlobal(Index, Value));
```

Feature index를 숫자로 직접 쓰는 코드는 금지한다.

현재 최소 `main`에서 직접 소비하는 생성 산출물:

```text
generated/cpp/AINativeNPCContracts.generated.h
generated/python/ai_native_npc_contracts_generated.py
```

자동 생성 문서와 Golden vector는 전체 하네스 보관본에서 계약 변경 시 함께 재생성한다.

---

## 13.6 Generated C++ Runtime Contract

Generated Header는 상수와 Enum만 제공하지 않고 다음 실행 함수를 포함한다.

- `QuantizeConfidence`, `QuantizeAgeSeconds`, `QuantizeDistanceCm`, `QuantizeLoudness`
- 모든 Tensor Field의 `Normalize*`
- `PackBitsLSBFirst`
- `CandidateSetCanonicalBytes`
- portable SHA-256와 `CandidateSetHashHex`
- `DecodeParameter`와 Skill별 Commit Clamp

Phase 0 CI는 동일 fixture를 Python unittest와 C++17 executable 양쪽에서 실행한다.

이 결과는 Unreal Runtime parity의 선행 증거다. 실제 UE `FMath`/NNE parity Gate는 별도로 pending 상태를 유지한다.

# 14. Neural Policy와 오프라인 학습

## 14.1 V1 모델

V1 Reference Model은 `policy_arch_v1.0.0`이다. Event Buffer를 사용하고 GRU를 사용하지 않는다.

`UNPCSocialStateComponent`는 감정·관계 값을 사건 기반으로 갱신한다. 모델은 해당 값을 읽는다.

- Layer·초기화: [공통 구현 계획 §3](implementation-plan.md#reference-model)
- Optimizer: [공통 구현 계획 §5](implementation-plan.md#training-config)
- Loss: [Requirements §9.11](requirements.md#911-loss-contract)

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

## 14.2 Bounded Factorized Candidate Scorer와 Parameter

```text
q = L2Normalize(LayerNorm(Wq(h)))
s = SkillEmbedding[skill_id]
t = Wt(TargetEmbedding[target_slot])
p = Wp(candidate_pair_features[16])
k = L2Normalize(LayerNorm(s + t + p))

RawScore = clamp(
    cosine(q,k) / 0.5
  + clamp(skill_bias,-0.25,0.25)
  + clamp(target_kind_bias,-0.25,0.25),
  -2.5,2.5)
```

Output:

- `candidate_raw_scores [B,272]`
- `candidate_parameter_proposals [B,272,4]`

Parameter 출력은 `[0,1]` sigmoid이며 Skill Registry가 physical unit, active mask, min/max/default를 소유한다.

```cpp
Physical = Min + FMath::Clamp(Norm, 0.0f, 1.0f) * (Max - Min);
Physical = FMath::Clamp(Physical, Min, Max); // Commit 시 재검증
```

비활성 parameter는 출력값을 무시하고 Registry default를 사용한다. 모델이 자원 예약, Goal 전환, 관계 변경을 출력하지 않는다.

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

고정 Export 설정:

- FP32, `model.eval()`
- ONNX opset 17
- batch 축 `B`만 dynamic, 나머지 축 고정
- 입력 이름과 dtype은 Schema의 10개 Tensor exact-match
- 출력 이름은 `candidate_raw_scores`, `candidate_parameter_proposals`
- `B=1,2,4,8` PyTorch↔ONNX Runtime parity
- ONNX checker, shape inference, operator allowlist 검사

Policy Manifest 필수 필드:

```json
{
  "schema_version": "2.0.0",
  "schema_sha256": "424898ba9e80ff8ac7ad4d48a806f8606d2c595ec892d2753becbdaa3e47b6cc",
  "skill_registry_version": "1.0.0",
  "skill_registry_sha256": "08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8",
  "goal_registry_version": "1.0.1",
  "goal_registry_sha256": "b6ed883e39f8da4f792b2ad4542b4cf7045ff5fe00147a9eba15eac61fa67ac2",
  "target_slotter_version": "1.0.0",
  "slotter_contract_sha256": "...",
  "postprocess_version": "1.0.0",
  "postprocess_contract_sha256": "...",
  "normalization_version": "2.0.0",
  "normalization_contract_sha256": "...",
  "architecture_version": "policy_arch_v1.0.0",
  "training_profile": "policy_train_v1.0.0",
  "onnx_opset": 17,
  "dynamic_axes": ["B"],
  "tested_batch_sizes": [1, 2, 4, 8],
  "candidate_count": 272,
  "target_slots": 17,
  "event_slots": 12,
  "model_sha256": "...",
  "calibration_ood_asset_sha256": "...",
  "input_signature_sha256": "...",
  "onnx_operator_set_sha256": "...",
  "decision_contract_sha256": "..."
}
```

## 14.7 학습 구현 Handoff

Unreal Capture와 ML 파이프라인의 책임은 다음처럼 분리한다.

```text
Unreal
  Belief/Goal/Target/Candidate snapshot
  → Schema Feature Builder
  → candidate hash와 contract hash
  → immutable Capture Record

ML
  Capture Record 검증
  → family split 검증
  → policy_arch_v1.0.0 학습
  → Calibration/OOD fit
  → ONNX/Manifest/Golden 생성

Unreal
  Model Bundle import
  → descriptor/hash/parity/cook 검증
  → NNE inference 또는 Utility fallback
```

Phase 0:

- deterministic fixture dataset으로 train/export CLI smoke
- 작은 fixture model의 ONNX와 Golden vector 생성
- Editor와 packaged Development build에서 NNE parity
- fixture model은 gameplay 품질 판정에 사용하지 않음

Phase 1:

- [Contract Appendices E.6](contract-appendices.md#e6-dataset-최소량)의 최소 Silver/Gold/DAgger 데이터 충족
- `policy_train_v1.0.0` 전체 학습
- Calibration/OOD asset 동결
- General/OOD/Critical/Performance Gate 후 V1 bundle 승격

Capture Record는 상위 요구사항 §9.9의 10개 input tensor, label, provenance를 그대로 사용한다. Unreal debug/replay shard의 Actor pointer·이름·absolute transform은 학습 input shard로 복사하지 않는다.

---

# 15. NNE 추론 Subsystem

Epic의 [UE 5.7 NNE Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-overview-in-unreal-engine?application_version=5.7)를 API 기준으로 사용한다. NNE는 UE 5.7에서도 Beta이므로 특정 runtime 성공을 전제하지 않고 모든 target platform에서 Utility Baseline을 항상 함께 cook한다.

## 15.1 Backend 선택

V1 기본:

```text
Interface: UE::NNE::INNERuntimeCPU
Runtime name: NNERuntimeORTCpu
Model format: ONNX opset 17, FP32
Execution: worker thread의 RunSync
```

이 모델은 작은 CPU Tensor를 읽고 결과를 Game Thread 의사결정에 사용하므로 `INNERuntimeRDG`는 사용하지 않는다. `INNERuntimeGPU`도 CPU↔GPU 동기화 비용과 render contention을 별도 측정하기 전에는 사용하지 않는다.

Runtime 선택은 임의 탐색 후 첫 항목을 쓰지 않는다. Policy Manifest의 allowlist와 프로젝트 설정에 있는 정확한 runtime name만 허용한다. backend를 바꾸면 output parity, latency, cook, platform Gate를 다시 통과하고 `perf_manifest.json`을 새로 만든다.

## 15.2 프로젝트 설정

`.uproject`에서 [UE 5.7 NNERuntimeORT plugin](https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/NNERuntimeORT?application_version=5.7)을 활성화한다. `NNE` 자체는 아래 `Build.cs`의 Engine module dependency로 연결한다.

```json
{
  "Plugins": [
    {
      "Name": "NNERuntimeORT",
      "Enabled": true
    }
  ]
}
```

`AINativeNPCRuntime.Build.cs`:

```csharp
PrivateDependencyModuleNames.AddRange(new string[]
{
    "NNE"
});
```

주요 include:

```cpp
#include "NNE.h"
#include "NNERuntimeCPU.h"
#include "NNEModelData.h"
```

Runtime module에 ORT 구현 타입을 직접 link하지 않는다. NNE interface와 runtime name으로 찾으며, plugin이 없거나 target platform에서 등록되지 않으면 정상적인 fallback 상태로 처리한다.

## 15.3 Model Asset Import와 Cook

1. 승인된 Model Bundle의 `policy.onnx` SHA-256을 Manifest와 비교한다.
2. Content Browser로 import해 `UNNEModelData` asset을 만든다.
3. `DA_AINPCPolicy_<version>` Data Asset에 다음을 저장한다.
   - `TSoftObjectPtr<UNNEModelData>`
   - runtime allowlist
   - Model/Schema/Registry/Post-process/Calibration hash
   - input/output descriptor snapshot
   - Golden smoke vector asset
   - Calibration/OOD JSON에서 검증·변환한 scaler, logistic weights/threshold, OOD mean/precision/quantile
4. Model Data asset에서 사용하지 않는 runtime 최적화 결과를 끈다.
5. Policy Data Asset을 Primary Asset 또는 hard-referenced startup asset으로 등록해 cook 누락을 막는다.
6. `NPCPolicyValidationCommandlet`가 source ONNX, Manifest, Data Asset metadata의 hash를 빌드 전에 대조한다.

Cooked `.uasset`에서 원본 ONNX byte hash를 런타임에 추측하지 않는다. 원본 hash 검증은 import/build commandlet가 소유하고, Runtime은 cook된 Policy Data Asset의 manifest snapshot과 generated contract를 검증한다.

Runtime은 매 판단마다 JSON을 parse하지 않는다. `calibration_ood_asset.json`은 build commandlet가 typed Data Asset 값으로 변환하고 원본 JSON SHA-256을 함께 저장한다.

Editor 성공만으로 완료하지 않는다. 지원 target마다 packaged Development와 Shipping-equivalent configuration에서 runtime 등록, model creation, Golden smoke inference를 실행한다.

## 15.4 World Subsystem과 초기화

`UNPCInferenceWorldSubsystem` 책임:

- Policy Data Asset 1회 로드
- runtime/backend 확인
- read-only Model 공유
- Model Instance pool
- deadline queue와 batch assembly
- worker 실행
- Game Thread response queue
- latency/failure/fallback counter

NPC마다 Model/ModelData를 만들지 않는다.

초기화 순서:

```text
World Initialize
→ Policy Data Asset async load
→ generated Schema/Registry/Decision Contract 대조
→ GetAllRuntimeNames<INNERuntimeCPU>() 진단 기록
→ GetRuntime<INNERuntimeCPU>("NNERuntimeORTCpu")
→ weak runtime pointer validity 확인
→ CanCreateModelCPU(ModelData) 성공 확인
→ CreateModelCPU(ModelData) + shared pointer 확인
→ CreateModelInstanceCPU() pool 생성
→ input/output descriptor exact validation
→ batch bucket별 SetInputTensorShapes
→ Golden smoke vector RunSync
→ Ready
```

Epic API 대응:

| 단계 | UE 5.7 NNE API |
|---|---|
| runtime 목록 | `UE::NNE::GetAllRuntimeNames<INNERuntimeCPU>()` |
| runtime 획득 | `UE::NNE::GetRuntime<INNERuntimeCPU>(Name)` |
| 호환성 사전검사 | `CanCreateModelCPU(ModelData)` |
| immutable model | `CreateModelCPU(ModelData)` |
| session/instance | `CreateModelInstanceCPU()` |
| dynamic batch shape | `SetInputTensorShapes(...)` |
| CPU inference | `RunSync(InputBindings, OutputBindings)` |

각 반환 status와 pointer를 확인한다. 초기화 중 어느 단계든 실패하면 subsystem 상태를 `FallbackOnly`로 바꾸고 Utility Baseline을 사용한다.

## 15.5 Descriptor와 Tensor Binding

입력 descriptor는 이름, dtype, rank, 고정 dimension을 전부 비교한다.

| 이름 | dtype | shape |
|---|---|---|
| `global_state` | float32 | `[B,128]` |
| `target_features` | float32 | `[B,17,48]` |
| `target_kind_ids` | int64 | `[B,17]` |
| `target_mask` | bool | `[B,17]` |
| `event_features` | float32 | `[B,12,24]` |
| `event_type_ids` | int64 | `[B,12]` |
| `event_target_slots` | int64 | `[B,12]` |
| `event_mask` | bool | `[B,12]` |
| `candidate_pair_features` | float32 | `[B,272,16]` |
| `candidate_mask` | bool | `[B,272]` |

출력:

| 이름 | dtype | shape |
|---|---|---|
| `candidate_raw_scores` | float32 | `[B,272]` |
| `candidate_parameter_proposals` | float32 | `[B,272,4]` |

ONNX descriptor 배열 순서를 하드코딩하지 않는다. 이름으로 descriptor index map을 한 번 만들고, 중복·누락·추가 Tensor가 있으면 load를 실패시킨다.

Buffer:

- float32: contiguous owned `TArray<float>`/aligned buffer
- int64: contiguous signed 64-bit buffer
- bool: NNE descriptor가 요구하는 ONNX BOOL 0/1 byte buffer
- Input/Output memory는 `RunSync`가 끝날 때까지 worker job이 독점 소유
- byte size는 `element_count × dtype_size`로 계산하고 binding 전 exact-check

Runtime에서 shape를 추측하거나 자동 broadcast에 의존하지 않는다.

## 15.6 Model Instance Pool과 Micro-batch

read-only Model은 World에서 공유하지만 하나의 Model Instance를 동시에 두 worker가 호출하지 않는다. `[1,2,4,8]` batch bucket마다 instance pool과 고정 input/output buffer를 준비하고 초기화 때 `SetInputTensorShapes`를 한 번 호출한다.

실제 요청 수가 bucket보다 작으면 남은 lane을 canonical padding snapshot으로 채우고 `lane_valid=false`로 표시한다. Padding lane은:

- Target slot 16 NoTarget만 valid
- Event 전부 padding
- Candidate mask 전부 false
- 출력은 검증 후 버림

Queue:

- 기본 collection window 1ms, 설정 가능한 상한 3ms
- deadline이 빠른 요청 우선
- 같은 model hash와 decision contract hash만 같은 batch
- superseded/deadline-expired 요청은 batch 구성 전에 제거
- batch 최대 8 NPC

Instance 수와 bucket 메모리는 target hardware에서 profile해 `perf_manifest.json`에 기록한다. 동시성이 더 필요하면 instance를 늘리되 공유 instance에 lock을 걸어 직렬 병목을 숨기지 않는다.

## 15.7 Worker 실행

Game Thread가 immutable `FInferenceRequestPOD`를 만든다.

```text
decision_id
candidate_set_hash
decision_contract_hash
deadline
10 input tensor owned buffers
lane metadata
```

Worker:

```text
instance lease
→ binding byte-size 검사
→ RunSync
→ output validation
→ immutable response 작성
→ Game Thread queue에 enqueue
→ instance 반환
```

`RunSync`는 worker를 block해도 되지만 Game Thread에서 호출하지 않는다. Worker에서는 다음을 금지한다.

- UObject/Actor dereference
- Transform/Perception/Goal 조회
- Nav query
- Post-process mutation
- Skill Start/Cancel
- 관계·감정 update

NNE API가 caller-owned memory의 lifetime과 thread safety를 호출자에게 맡기므로 job buffer를 stack temporary나 재사용 중인 NPC component memory에 bind하지 않는다.

## 15.8 Output과 Response 검증

Worker 단계:

1. `RunSync` status 성공
2. output descriptor/element count exact-match
3. 모든 값 finite
4. raw score가 tolerance 포함 `[-2.5001,2.5001]`
5. parameter가 tolerance 포함 `[-1e-5,1.00001]`
6. 유효 범위 안의 parameter만 최종 `[0,1]` clamp

Game Thread 단계:

1. response decision ID가 아직 commit-eligible
2. response decision contract hash exact-match
3. response candidate hash를 pending request hash와 먼저 비교
4. latest Goal/Target/authority/TTL 재검증
5. Switch Cost→선택→OOD→Calibration
6. Accept면 Atomic Commit, 아니면 Utility/Goal fallback

score 하나라도 NaN/Inf이거나 범위를 크게 벗어나면 batch 전체를 폐기한다. 한 lane의 metadata/hash/stale 문제는 다른 lane의 수치 output을 오염시키지 않았으면 해당 lane만 폐기한다.

## 15.9 Fallback과 Health State

다음은 crash가 아니라 명시적인 fallback 원인이다.

- NNE/ORT plugin 또는 runtime 미등록
- target platform에서 model creation 불가
- Model/Schema/Registry/Decision Contract mismatch
- descriptor, dtype, shape, byte-size mismatch
- `SetInputTensorShapes` 또는 `RunSync` 실패
- Golden smoke parity 실패
- NaN/Inf/range violation
- queue deadline 초과
- stale/superseded response

상태:

```text
Loading → Ready
Loading → FallbackOnly
Ready → Degraded → Ready
Ready/Degraded → FallbackOnly
```

연속 NNE 실패 3회 또는 60초 sliding window 실패율 1% 초과 시 `Degraded`, 5% 초과 시 `FallbackOnly`로 전환한다. 여기에는 init/run/descriptor/numeric failure만 포함하고 stale discard나 정상 deadline cancellation은 포함하지 않는다. 자동 재시도는 30초 cooldown 뒤 Golden smoke 1회만 수행한다. Shipping에서 무한 reload loop를 만들지 않는다.

Metric:

- runtime/model name과 hash
- queue/batch 크기
- inference p50/p95/p99
- deadline miss
- init/run/descriptor/numeric failure
- stale discard
- Neural accept/abstain
- Utility fallback reason

## 15.10 Parity와 Packaging Gate

Golden set은 최소 다음을 포함한다.

- batch `1,2,4,8`
- no-event
- Target slot 16만 존재
- 각 Target Kind 최소 1개
- sparse/dense candidate mask
- 모든 normalizer boundary
- Event Target remap 성공/실패
- Continue candidate

비교:

```text
generated Python input ↔ Unreal Feature Builder
  float: abs≤1e-6 또는 rel≤1e-5
  discrete/mask/hash bytes: byte-identical

PyTorch ↔ ONNX Runtime ↔ UE Editor NNE ↔ packaged NNE
  FP32 output: abs≤1e-4 또는 rel≤1e-4
```

지원 platform별 Gate:

1. runtime 이름 등록
2. `CanCreateModelCPU`/model/instance 생성
3. Golden smoke
4. packaged Development 자동화 테스트
5. Shipping-equivalent cook asset 포함 검사
6. §24 Typical/Burst latency

NNE가 Beta라는 이유로 Gate를 생략하지 않는다. 반대로 특정 platform에서 NNE가 불가능해도 Utility Baseline만으로 기능적으로 안전하게 실행할 수 있으면 그 platform의 Neural 기능을 명시적으로 비활성화할 수 있다.

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

- Schema/Enum/Registry/Decision Contract mismatch → NNE 실행 전 `ContractMismatch` hard reject
- OOD는 유효한 동일 계약 내부의 Tactical Context Mahalanobis distance에만 사용
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

1. response candidate hash를 pending request hash와 비교
2. Decision Contract Hash와 model/schema/registry version 확인
3. decision ID가 commit eligible인지 확인
4. deadline, NPC generation, Goal Revision 확인
5. Kind별 Target 검증
   - Entity: identity/generation 일치, 최신 유효 Belief revision 허용, tracking Skill은 현재 Perception/LOS 필요
   - Sound/LastKnown/WorldPosition: immutable snapshot exact revision + TTL
   - Cover/SmartObject: resource generation + availability revision CAS
   - Waypoint: authored definition revision exact
6. Skill precondition과 `CanContinue(LatestBelief)` 검증
7. Resource lock/order 확인
8. Final Validation
9. StartCommit

최신 월드 상태로 Candidate Hash를 재계산해 response와 먼저 비교하지 않는다.

## 17.3 Reservation

- `Validate + Reserve + StartCommit`만 Game Thread 원자 경계다.
- Resource Handle을 canonical order로 잠근다.
- ResourceGeneration/AvailabilityRevision을 CAS한다.
- 전부 성공한 경우에만 ReservationId를 생성한다.
- 부분 성공과 StartCommit 실패는 역순 rollback한다.
- 기본 lease 2.0초, active Skill renew 0.5초
- Tick/Complete는 transaction 밖이다.
- urgent cancel은 worker 종료를 보장하지 않지만 superseded decision ID는 Commit 불가다.

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

| Kind | Revision/Commit 정책 | Hidden Information 제한 |
|---|---|---|
| NoTarget | 검증 없음 | Target 조회 금지 |
| Entity | Identity/Generation 일치 후 최신 유효 Belief Revision 허용 | Sight Lost 이후 Transform/Velocity로 전술 목표 갱신 금지 |
| SoundEvent | immutable exact revision + TTL | Instigator 현재 Transform 금지 |
| LastKnownPosition | immutable exact revision + TTL | Origin Actor 현재 상태 조회로 취소/갱신 금지 |
| CoverSlot | ResourceGeneration + AvailabilityRevision CAS | 숨은 적 위치로 utility 재계산 금지 |
| SmartObject | ResourceGeneration + AvailabilityRevision CAS | unrelated hidden Actor 상태 금지 |
| Waypoint | authored revision exact | hidden Actor 추종 금지 |
| WorldPosition | immutable exact revision | 연결 Actor Transform 갱신 금지 |

물리·충돌·피해 실행은 서버 Ground Truth를 사용할 수 있다. 제한은 숨은 정보를 전술 선택, 이동·조준 목표, 추적 지속 판단으로 되돌려 넣는 행위에 적용한다.

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
- `CanContinue(LatestBelief, LatestGoalRevision)` 통과 시에만 active execution 유지
- 원래 Target이 slot에서 빠졌으면 Kind별 Commit 정책으로 최신 유효성을 판정
- Executor CurrentSkillId는 실제 실행 Skill을 유지하며 Continue ID 1로 바꾸지 않음

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

## 19.5 보스 전용 Neural Pattern 실행

보스는 공통 `Attack(Entity)` Candidate를 그대로 사용한다. `QuickSlash`, `DelayedHeavy`, `GapCloser` 같은 공격 절차는 Target Slot이나 273번째 Candidate가 아니라 Attack Skill 내부의 `UBossPatternDataAsset`이다.

### 19.5.1 Unreal 소유 객체

| 타입 | 책임 |
|---|---|
| `UBossPatternSetDataAsset` | 보스 archetype의 stable `pattern_id` 목록, `SafeDefaultPatternId`, Utility profile, optional Model Bundle, bundle hash |
| `UBossPatternDataAsset` | 거리·Phase·선후행·Montage·timing·tracking·Hitbox·Damage·Interrupt 규칙 |
| `FBossPatternDecisionSnapshot` | 32 Pattern ID·mask, Belief 기반 Attack Target, boundary, Boss/Combat revision, hash |
| `UBossPatternCandidateBuilderComponent` | stable ID 정렬, `[B,32,*]` Tensor, hard mask 생성 |
| `UBossPatternPolicyComponent` | Utility Baseline 또는 별도 NNE Model Bundle 실행, OOD/Calibration/fallback |
| `UBossPatternCommitCoordinator` | latest request·contract·candidate-set·revision·resource CAS 검증 |
| `UBossPatternExecutorComponent` | 선택 잠금, Montage/Root Motion, Hitbox, Damage, tracking, interrupt cleanup |

공통 `UDecisionSubsystem`과 Boss Pattern Policy는 request ID, model bundle, pending response queue를 공유하지 않는다. Boss Pattern에는 별도 `pattern_decision_id`와 `boss_pattern_decision_contract_hash`를 사용한다.

`UBossPatternCandidateBuilderComponent`는 `AINativeNPCBossPatternContracts.generated.h`의 normalizer table을 직접 사용한다. 거리·속도·시간 divisor와 clamp를 수동 복제하지 않는다. non-finite feature는 request 전체를 거부하고, 비어 있는 Pattern row는 feature 0·`invalid_pattern_id`·`pattern_mask=false`로 채운다. Target 관련 field는 parent Attack의 허용된 Belief snapshot만 읽으며 `target_health_ratio_estimate`와 confidence를 함께 기록한다.

### 19.5.2 Attack 시작 흐름

```text
공통 CommitCoordinator가 Attack(Entity)를 Commit
→ Attack Skill State = ReadyToSelect
→ BossPatternCandidateBuilder가 immutable Pattern snapshot 생성
→ valid row 0개면 PatternUnavailable
→ Pattern Utility 또는 NNE dispatch
→ GameThread에서 BossPatternCommitCoordinator 재검증
→ 선택 Pattern과 제한 parameter를 executor에 잠금
→ StateTree/C++ Combat Executor 시작
```

NNE timeout, NaN, contract mismatch, OOD/Calibration abstain은 valid row가 하나 이상일 때만 같은 snapshot의 Utility Baseline으로 fallback한다. Utility 동점은 adjusted score 내림차순 후 `pattern_id` 오름차순으로 해소한다. Utility 자체가 실패하면 `UBossPatternSetDataAsset.SafeDefaultPatternId` row가 현재 valid일 때만 사용한다. valid row가 0개면 NNE와 Utility를 모두 건너뛰고 Attack Skill을 `Failed(PatternUnavailable)`로 종료해 최신 공통 Tactical decision을 요청한다. `BranchWindow` 응답이 window 종료 뒤 도착하면 `PatternBoundaryClosed`로 거부하고 현재 Pattern의 authored 종료 경로를 계속한다.

### 19.5.3 Pattern Data Asset

각 `UBossPatternDataAsset`은 Contract Appendices BP의 필수 필드를 가진다. 최소 실행 필드는 다음과 같다.

```cpp
UCLASS(BlueprintType)
class UBossPatternDataAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly) uint16 PatternId;
    UPROPERTY(EditDefaultsOnly) FGameplayTagContainer FamilyTags;
    UPROPERTY(EditDefaultsOnly) TArray<int32> AllowedBossPhases;
    UPROPERTY(EditDefaultsOnly) TArray<uint16> AllowedPredecessors;
    UPROPERTY(EditDefaultsOnly) TArray<uint16> AllowedSuccessors;
    UPROPERTY(EditDefaultsOnly) FVector2D PreferredDistanceCm;
    UPROPERTY(EditDefaultsOnly) float StartupTelegraphSeconds;
    UPROPERTY(EditDefaultsOnly) float ActiveSeconds;
    UPROPERTY(EditDefaultsOnly) float RecoverySeconds;
    UPROPERTY(EditDefaultsOnly) float TelegraphExtensionMaxSeconds;
    UPROPERTY(EditDefaultsOnly) float RecoveryExtensionMaxSeconds;
    UPROPERTY(EditDefaultsOnly) FPatternTrackingLimits TrackingByPhase;
    UPROPERTY(EditDefaultsOnly) TObjectPtr<UAnimMontage> Montage;
    UPROPERTY(EditDefaultsOnly) FName MontageSection;
    UPROPERTY(EditDefaultsOnly) FHitboxWindowProfile HitboxWindows;
    UPROPERTY(EditDefaultsOnly) TObjectPtr<UDamageProfile> DamageProfile;
    UPROPERTY(EditDefaultsOnly) TArray<FPatternBranchWindow> BranchWindows;
    UPROPERTY(EditDefaultsOnly) FPatternInterruptPolicy InterruptPolicy;
};
```

Editor validation과 Cook validation은 ID 중복, 32개 초과, 음수·NaN timing, 최소 Telegraph 0 이하, invalid 선후행 참조, load 불가능한 Montage/Hitbox/Damage, Contract tracking 상한 초과를 hard error로 처리한다.

### 19.5.4 제한 Parameter decode

NNE의 4개 proposal은 Commit 시 Data Asset 범위 안에서 decode한다.

```text
tracking = authored_tracking_limit × clamp01(output[0])
telegraph = startup_telegraph_seconds
          + telegraph_extension_max_seconds × clamp01(output[1])
recovery = recovery_seconds
         + recovery_extension_max_seconds × clamp01(output[2])
output[3] = 0
```

모델은 최소 Telegraph와 Recovery를 줄일 수 없다. Active duration, Hitbox, Damage, Root Motion, Interruptibility, Phase transition은 Data Asset과 Combat Module만 소유한다.

### 19.5.5 StateTree 잠금

`ST_BossAttack`은 선택이 Commit된 뒤 다음 deterministic task만 실행한다.

```text
ReadyToSelect
→ BossPatternCommit    # Pattern 잠금과 PreAttackTurn 진입을 원자적으로 수행
→ PreAttackTurn       # 잠금 유지, authored tracking 상한
→ StartupTelegraph    # 잠금 유지, Montage와 cue 시작
→ Active              # Hitbox window와 Damage Profile 적용
→ Recovery            # punish window 유지
→ authored BranchWindow이면 successor 선택 요청
→ 아니면 Completed 후 RecoveryEnd 선택 또는 공통 Tactical 재판단
```

- Pattern Commit 성공과 `PreAttackTurn` 진입은 같은 transaction이다.
- `PreAttackTurn`, `StartupTelegraph`, `Active`에서는 Pattern 재선택을 금지한다.
- 일반 플레이어 이동과 새 Neural score는 interrupt 사유가 아니다.
- 플레이어 추적은 Data Asset의 Phase별 yaw/pitch/speed 상한 안에서만 수행한다.
- 추적용 현재 transform은 서버 Combat Targeting 정책이 Executor에만 제공한다. Pattern Model request로 되먹이지 않고 재선택에도 사용하지 않는다.
- 강제 중단은 Death, Actor destruction, authority loss다.
- Stun, Posture Break, scripted Phase transition, Arena reset은 현재 Pattern의 allowlist와 interrupt point를 만족해야 한다.
- 중단 cleanup 순서는 Hitbox off → Montage 정책 적용 → Root Motion 해제 → reservation 해제 → Event 발행 → Executor state 전환이다.

서버가 Pattern Commit, 실행 Phase, Hitbox, Damage, interrupt 결과를 권위 있게 소유한다. 클라이언트는 committed Pattern ID·start time·phase와 authored cue를 복제받으며 Pattern inference를 Gameplay 권위로 사용하지 않는다.

## 19.6 StateTree

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

## 21.7 Boss Pattern 선택과 잠금

```text
공통 Candidate: Attack(Quinn Entity) Commit
→ Pattern Slot 0 QuickSlash: valid
→ Pattern Slot 1 DelayedHeavy: valid
→ Pattern Slot 2 GapCloser: distance mask=false
→ Neural/Utility가 DelayedHeavy 선택
→ BossPatternCommit에서 Target/Phase/Combat revision과 hash 일치
→ Pattern 잠금과 `PreAttackTurn` 진입을 원자적으로 수행
→ StartupTelegraph에서 잠금 유지, Montage와 cue 시작
→ Quinn이 측면 이동: authored tracking 상한 안에서만 회전
→ Active: Pattern 변경 없이 Hitbox/Damage Profile 실행
→ Recovery: punish window 유지
→ RecoveryEnd에서 다음 Pattern request 생성
```

Telegraph 중 새 추론에서 QuickSlash 점수가 높아져도 현재 DelayedHeavy를 바꾸지 않는다. Stun이 발생하면 Data Asset의 interrupt allowlist와 현재 interrupt point를 확인한 뒤에만 cleanup 순서로 중단한다.

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
- Boss Pattern ID/slot/mask reason/raw·adjusted score
- Pattern selection boundary·executor phase·lock state
- Pattern candidate-set/decision-contract/asset-bundle hash
- authored Telegraph/Active/Recovery와 실제 phase timestamp
- tracking clamp·interrupt allow/deny·cleanup 결과

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

## 23.4 Save/Load

- 서버는 Goal Instance/Revision, Event Buffer, Belief source·age·TTL, Active Skill snapshot을 저장한다.
- Load 시 만료된 Belief/Event를 제거하고 Resource Reservation은 재획득한다.
- Pending NNE request와 cancellation token은 저장하지 않고 재요청한다.

## 23.5 Model Hot-swap과 Rollback

- Model, Calibration, Schema, Skill/Goal Registry를 하나의 Decision Contract bundle로 배포한다.
- 새 bundle은 dry-run inference와 Contract Hash 검증 후 원자적으로 활성화한다.
- 활성화 시 pending request를 supersede한다.
- 실패율·Fallback·Calibration drift가 threshold를 넘으면 이전 bundle 전체로 rollback한다.

## 23.6 데이터 Provenance와 Active Learning

Capture Record에 schema/registry/model/policy hash, scenario family, source type, map seed, annotator/LLM provenance를 포함한다. Active Learning은 OOD, calibrated uncertainty, Candidate/Target miss, 반복 실패, Baseline 불일치 상태를 우선 수집한다.

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
- 선택적 보스: Pattern snapshot 32 row, pending Pattern request, locked Pattern executor state
- no GRU hidden

모델과 NNE instance는 World 단위로 공유한다.

---

# 25. 테스트

## 25.1 Schema/Parity

- generated enum/static assert
- generated Python import와 YAML/Registry SHA exact-match
- Tensor shape
- padding/mask
- Candidate index
- canonical hash bytes
- NoTarget slot
- Target payload
- Python–Unreal float tolerance
- ONNX–NNE output tolerance
- NNE descriptor name/dtype/rank/dimension exact-match
- `B=1,2,4,8` model instance shape/binding
- Editor와 packaged build Golden smoke
- target platform cook에 ModelData/ORT runtime 포함

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

### 25.7.1 Boss Pattern

- 32 Pattern slot 정렬·padding·mask와 Python/C++ hash Golden
- generated normalizer field closure, distance·speed·time clamp, non-finite reject, Python↔C++ smoke parity
- Pattern Asset normalized manifest→definition digest→bundle digest Python↔Build Commandlet parity
- Ground Truth source 주입 거부와 Target estimate confidence 처리
- Float Tensor Python↔Unreal parity와 ORT↔NNE output parity
- Phase·거리·각도·LOS·cooldown·resource·predecessor·Branch Window mask
- latest request, candidate-set hash, Boss/Combat revision stale rejection
- Telegraph 시작 뒤 재선택 0건, Active 중 Pattern 변경 0건
- 최소 Telegraph/Recovery 단축 0건, tracking authored 상한 위반 0건
- Hitbox·Damage·Root Motion·interruptibility Neural 출력 경로 0건
- 강제/allowlist interrupt와 cleanup 순서
- Utility fallback과 all-masked `PatternUnavailable`
- 서버 권위 Commit·복제·save/load/hot-swap
- Phase×거리×이전 Pattern×boundary별 recall, 반복도, 다양성, readability, punish-window, latency

<!-- BEGIN AUTO-GENERATED TEST TAXONOMY KPI: UNREAL -->

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
- Critical Suite 576 sequences: 100%
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

## 25.9 고정 Critical/OOD Family

Critical 9 family와 OOD 9 family 이름은 `test_taxonomy_v1.yaml`을 단일 원본으로 사용한다. Critical은 family당 최소 64 case, 총 최소 576 sequences다.

Critical family:

- `perception_belief_visibility`
- `typed_target_slotting`
- `goal_arbitration_transition`
- `candidate_mask_and_hash`
- `async_latest_only_and_atomic_commit`
- `hidden_information_boundary`
- `skill_parameter_and_resource_cas`
- `save_load_hot_swap_recovery`
- `boss_pattern_mask_lock_interrupt_fairness`

OOD family:

- `feature_range_shift`
- `missing_modality_pattern`
- `unseen_role_attribute_combination`
- `candidate_count_pattern`
- `belief_age_confidence_shift`
- `environment_layout_density_shift`
- `event_sequence_shift`
- `sensor_noise_shift`
- `boss_pattern_phase_composition_shift`

<!-- END AUTO-GENERATED TEST TAXONOMY KPI: UNREAL -->

# 26. 단계별 구현 계획

## Phase 0 — MVP Vertical Slice, 6~8주 병렬 기준

### Stream A — Contracts, ML+Gameplay

- schema generator
- C++/Python constants
- Target Handle/Feature
- 17 Slot/272 Candidate
- Golden vectors
- Dataset Record/Validator 골격
- `phase0_fixture.json` 학습·Export smoke

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
- ONNX import와 Policy Data Asset
- ORT CPU descriptor/binding/instance pool
- Editor + packaged `B=1,2,4,8` parity
- in-flight lifecycle
- Validate/StartCommit
- Phase 0에서는 Resource Kind가 mask되어 있어 예약 경로는 mock transaction으로 검증

### Phase 0 Exit

- Critical Target/Candidate Recall 100%
- Hidden Leakage 0
- Goal FSM 성공
- stale response Commit 0
- Utility fallback
- fixture model PyTorch↔ORT↔UE NNE parity
- NNE 누락/실패 packaged build에서 Utility fallback
- Manny 수직 슬라이스 5개 재현

## Phase 1 — V1, Phase 0 후 12~16주

- 16 Skill
- 모든 Target Kind
- Cover/SmartObject reservation
- Calibration/OOD
- 3 Role×4 Goal
- multiplayer
- Gold/DAgger
- `policy_train_v1.0.0` 학습과 frozen Model Bundle
- Calibration/OOD asset과 General/OOD/Critical 평가
- 선택적 Boss Pattern Utility/NNE/Commit/StateTree/Combat Executor 수직 슬라이스
- Boss Pattern Float/ONNX/Runtime/Fairness/Performance Gate
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
| Boss Pattern Policy/Executor | Combat AI + ML + Animation + QA | - | 4주 | 공통 Attack Commit + Boss Pattern Contract |
| NNE/Commit/Reservation | Gameplay + Server | 2주 | 4주 | Skill/Target 계약 |
| Label/DAgger Tool | Tech Designer | 1주 | 4주 | Inspector/Replay |
| QA/KPI | QA + ML | 2주 | 지속 | Critical Suite |

---

# 27. 파일 단위 구현 목록

## ML

```text
ML/pyproject.toml
ML/requirements.lock
ML/configs/model_v1.json
ML/configs/train_v1.json
ML/configs/phase0_fixture.json
ML/src/anpc_ml/dataset/record_v1.py
ML/src/anpc_ml/dataset/validate.py
ML/src/anpc_ml/models/policy_v1.py
ML/src/anpc_ml/models/boss_pattern_policy_v1.py
ML/src/anpc_ml/dataset/boss_pattern_record_v1.py
ML/src/anpc_ml/losses.py
ML/src/anpc_ml/train.py
ML/src/anpc_ml/calibration.py
ML/src/anpc_ml/export_onnx.py
ML/src/anpc_ml/parity.py
ML/tests/
```

## Contracts

```text
External/AI-Native-NPC/generated/cpp/AINativeNPCContracts.generated.h
External/AI-Native-NPC/generated/cpp/AINativeNPCBossPatternContracts.generated.h
Source/AINativeNPCContracts/Public/AINPCContracts.h
Source/AINativeNPCContracts/Public/AINPCBossPatternContracts.h
```

`AINPCContracts.h`는 Unreal type adapter와 static assert만 소유하고 Enum·Index·Normalizer·Hash 상수를 복제하지 않는다.

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
Inference/NPCPolicyDataAsset.h
Inference/NPCInferenceTypes.h
Execution/NPCCommitCoordinatorComponent.h
Execution/NPCSkillExecutorComponent.h
Execution/NPCResourceReservationSubsystem.h
Boss/BossPatternDataAsset.h
Boss/BossPatternSetDataAsset.h
Boss/BossPatternTypes.h
Boss/BossPatternCandidateBuilderComponent.h
Boss/BossPatternPolicyComponent.h
Boss/BossPatternCommitCoordinator.h
Boss/BossPatternExecutorComponent.h
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
Inference/NPCInferenceWorldSubsystem.cpp
Inference/NPCPolicyDataAsset.cpp
Execution/NPCCommitCoordinatorComponent.cpp
Execution/NPCSkillExecutorComponent.cpp
Boss/BossPatternDataAsset.cpp
Boss/BossPatternCandidateBuilderComponent.cpp
Boss/BossPatternPolicyComponent.cpp
Boss/BossPatternCommitCoordinator.cpp
Boss/BossPatternExecutorComponent.cpp
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
Inference/NPCPolicyValidationCommandlet.cpp
```

## Tests

```text
Schema/NPCSchemaGoldenTest.cpp
Feature/NPCFeatureParityTest.cpp
Inference/NPCNNEGoldenParityTest.cpp
Inference/NPCNNEPackagingSmokeTest.cpp
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
- fixture model train/export 재현
- ORT CPU descriptor·binding·`B=1,2,4,8` Golden parity
- dirty/urgent lifecycle
- short atomic Commit
- Inspector와 Replay
- packaged build model load
- packaged build NNE 실패 시 Utility fallback

## 28.2 계약

- schema YAML에서 C++/Python/문서 생성
- discrete/hash byte-identical
- float parity tolerance
- NoTarget/padding
- Target payload
- Decision Contract Hash
- Skill Registry Hash
- generated Python 계약 import와 Schema/Registry SHA 일치
- Dataset Validator와 split family 교집합 0
- ONNX input/output descriptor와 opset 17

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

## 공유 계약 부록

- [Schema·Registry Appendix A–D](contract-appendices.md#appendix-ad-auto-generated-schemaregistry-계약)
- [UE 구현 승인 체크리스트](contract-appendices.md#ue-구현-승인-체크리스트)
