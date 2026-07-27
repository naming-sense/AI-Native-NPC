# AI Native NPC — Unreal Engine 5.7 / Manny·Quinn 공간·시야·소리 통합 구현 계획서
## 신경망 학습 시스템과 Unreal 클라이언트 분리 설계

- 문서 버전: v0.3
- 기준 엔진: Unreal Engine 5.7
- 기준 프로젝트: Games → Third Person → C++ → Variant `None`
- 기준 캐릭터: 플레이어 `Quinn`, NPC `Manny`
- 기준 추론 방식: 로컬 CPU 추론, Unreal Neural Network Engine(NNE) + `NNERuntimeORT`
- 상위 문서: `ai_native_npc_requirements_implementation_plan.md`
- 문서 목적: 기존 요구사항을 실제 제작 가능한 **오프라인 신경망 학습 시스템**, **모델–클라이언트 계약**, **Unreal Engine 런타임 클라이언트**로 분리하고, 소리뿐 아니라 **NPC와 플레이어의 상대 위치·거리·방향·이동 상태·현재 시야·가림·마지막 목격 위치**를 일급 입력으로 반영하는 구현 계획을 정의한다.
- v0.3 변경 범위: 기존 소리 중심 수직 슬라이스를 **시야 단독 반응**, **위치·이동 기반 반응**, **소리→회전→시야 획득**, **시야 상실 후 마지막 목격 위치 조사**까지 확장한다.
- 계약 변경: `entities`와 `candidates` Tensor가 확장되므로 v0.2 모델과 호환되지 않는 **Schema 2.0**으로 관리한다.

> 사용자가 언급한 “Mannaquin”은 본 문서에서 Unreal Engine의 공식 명칭인 **Mannequin**으로 표기한다. UE5 Third Person 템플릿의 기본 여성형 Mannequin은 `Quinn`, 남성형 Mannequin은 `Manny`다.

---

# 1. 문서의 핵심 결론

본 프로젝트는 하나의 코드베이스가 아니라 다음 세 영역으로 분리해야 한다.

1. **오프라인 신경망 프로젝트**
   - 데이터 생성, LLM/사람 라벨링, 학습, 평가, ONNX Export를 담당한다.
   - Unreal Engine 없이도 반복적으로 학습과 검증이 가능해야 한다.

2. **모델–클라이언트 계약 프로젝트**
   - 입력 Feature 순서, 정규화, Skill ID, Tensor Shape, 모델 버전을 정의한다.
   - Python과 Unreal이 동일한 계약 파일을 사용해야 한다.

3. **Unreal Engine 5.7 클라이언트**
   - 시야·소리 수집, 감지 위치와 마지막 목격 위치 관리, 후보 행동 생성, NNE 추론 요청, 행동 안정화, Manny 애니메이션 및 이동 실행을 담당한다.
   - 상황별 선호 규칙은 작성하지 않고, 물리적 가능 여부와 게임 안전 제약만 코드로 보장한다.

전체 구조는 다음과 같다.

```text
┌──────────────────────────────────────────────────────────────┐
│ A. 오프라인 신경망 프로젝트                                 │
│                                                              │
│ 상황 데이터 → 교사/선호 라벨 → PyTorch 학습 → 평가 → ONNX  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ ONNX + Manifest + Normalization
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ B. 모델–클라이언트 계약                                     │
│                                                              │
│ Feature Schema / Skill Registry / Tensor Shapes / Version    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ C. Unreal Engine 5.7 클라이언트                              │
│                                                              │
│ AI Sight/Hearing → Spatial Memory → Observation → Candidate → NNE → Skill 실행  │
│                     Manny NPC / Quinn Player                  │
└──────────────────────────────────────────────────────────────┘
```

핵심 책임 분리는 다음과 같다.

| 영역 | 담당 | 담당하지 않는 것 |
|---|---|---|
| 신경망 프로젝트 | 상황의 의미와 행동 선호 학습 | NavMesh 이동, 애니메이션, 충돌, 실제 공격 판정 |
| 모델 계약 | Python과 Unreal의 입력·출력 호환성 | NPC의 실제 행동 결정 |
| Unreal 클라이언트 | 센서, 후보, 추론, 실행, 로그 | 대규모 상황별 행동 선호 조건문 |
| Skill 실행기 | `TurnTo`, `MoveTo`, `Warn` 등의 실제 수행 | 언제 해당 Skill을 선택할지 판단 |
| 안전 제약 | 불가능·금지 행동 차단 | 자연스러운 행동 선호도 결정 |

---

# 2. 구현 범위와 전제

## 2.1 MVP 범위

MVP에서는 소리만 처리하는 데모가 아니라, 다음 세 가지 감각 수직 슬라이스를 모두 완성한다.

### 수직 슬라이스 A — 시야만으로 플레이어 반응

```text
Quinn이 Manny의 정면 시야 안으로 조용히 진입
→ Manny의 AI Sight가 Quinn을 감지
→ Quinn의 감지된 상대 위치·거리·방향·이동 속도를 Observation에 기록
→ Candidate Generator가 LookAt / TurnTo / Greet / Warn / KeepDistance 후보 생성
→ 신경망이 역할·성격·관계·거리·시야 상태를 함께 평가
→ Manny가 Quinn을 바라보거나 적절한 후속 행동을 실행
```

이 흐름은 발소리가 없어도 동작해야 한다. 즉, **현재 시야와 위치가 독립적인 입력 채널**이어야 한다.

### 수직 슬라이스 B — 소리에서 시야로 전환

```text
Quinn이 Manny의 뒤쪽으로 이동
→ Quinn 발소리가 Hearing Stimulus로 보고됨
→ Manny는 Quinn의 실제 현재 좌표가 아니라 소리 발생 위치만 인식
→ 신경망이 TurnTo(SoundLocation) 또는 Investigate(SoundLocation)를 평가
→ Manny가 소리 방향을 돌아봄
→ AI Sight가 Quinn을 새로 감지
→ 위치 정보의 출처가 Hearing에서 Sight로 전환
→ 관계와 성격에 따라 Greet / Warn / KeepDistance / Attack 후보 재평가
```

### 수직 슬라이스 C — 시야 상실과 마지막 목격 위치

```text
Manny가 Quinn을 보고 있음
→ Quinn이 벽 뒤로 이동
→ AI Sight가 Sight Lost 이벤트를 보고
→ 모델 입력에서 visible_now는 0으로 변경
→ 현재 Quinn의 실제 숨은 좌표는 전달하지 않음
→ 마지막 목격 위치, 목격 후 경과 시간, 위치 신뢰도만 유지
→ Investigate(LastSeenLocation) / SearchArea / ContinueCurrentAction 후보 평가
→ 기억 시간이 만료되면 해당 위치 정보도 제거
```

이 구현에서 다음과 같은 상황별 선호 규칙은 넣지 않는다.

```cpp
// 구현하지 않을 코드
if (PlayerIsBehind && HeardFootstep)
{
    TurnToPlayer();
}

if (PlayerIsVisible && DistanceToPlayer < 300.0f)
{
    WarnPlayer();
}

if (!PlayerIsVisible && HasLastSeenLocation)
{
    InvestigateLastSeenLocation();
}
```

대신 다음 공통 기능만 구현한다.

- Sight와 Hearing Stimulus를 수집한다.
- 감지된 위치를 NPC 로컬 좌표계의 Feature로 변환한다.
- 현재 보이는 위치, 소리 발생 위치, 마지막 목격 위치를 구분한다.
- 현재 감각 상태에 맞는 행동·대상 후보를 생성한다.
- `LookAt`, `TurnTo`, `Approach`, `KeepDistance`, `Investigate` 등의 Skill은 전달된 대상에 대해 일반적으로 동작한다.
- 모델이 감각 상태와 후보 행동을 평가한다.

가장 중요한 제한은 다음과 같다.

> Unreal 월드는 Quinn의 실제 좌표를 항상 알고 있지만, NPC 모델은 **현재 감각으로 획득했거나 기억하고 있는 위치만** 입력받아야 한다. 보이지도 들리지도 않는 Quinn의 실시간 좌표를 전달하면 학습 모델이 전지적 AI처럼 행동하므로 금지한다.

## 2.2 MVP 플랫폼 전제

- 우선 플랫폼: Windows Desktop
- 플레이 모드: Single Player
- 추론 위치: 로컬 클라이언트 CPU
- NPC 수 목표: 활성 NPC 30명, 추론 요청은 스케줄링하여 분산
- 모델 입력: 구조화된 float Tensor
- 모델 출력: 후보 행동별 점수와 선택적 행동 파라미터
- 런타임 LLM: MVP 범위에서 제외
- Behavior Tree: 정책 판단 용도로 사용하지 않음
- StateTree: 선택 사항이며, 사용할 경우 Skill 내부의 실행 순서만 담당

## 2.3 프로덕션 전 확인 사항

Unreal NNE는 UE 5.7 공식 문서에서 Beta 기능으로 표시된다. 따라서 다음을 출시 승인 조건으로 둔다.

- Editor가 아닌 Development/Shipping 패키지에서 모델 로딩 테스트
- 지원 대상 CPU와 플랫폼별 성능 측정
- NNE 및 `NNERuntimeORT` 플러그인 Cooking 확인
- 모델 import 실패와 runtime 미탐색에 대한 fallback
- 엔진 5.7 패치 버전 변경 시 NNE API 및 모델 재검증

---

## 2.4 감각 및 공간 정보 구현 범위

| 정보 | Unreal 내부 원본 | 모델에 전달되는 값 | 전달 조건 |
|---|---|---|---|
| Manny 자기 위치·회전 | Pawn Transform | 속도, 가속도, 정면 벡터, 구역 정보 | 항상 |
| Quinn 현재 위치 | Actor Transform | NPC 로컬 기준 상대 위치 | **현재 Sight 성공일 때만** |
| Quinn 마지막 목격 위치 | Perception Memory | NPC 로컬 기준 마지막 목격 위치, age, confidence | Sight 상실 후 TTL 동안 |
| 소리 발생 위치 | Hearing Stimulus Location | NPC 로컬 기준 소리 위치, loudness, age | Hearing Event가 유효할 때 |
| Quinn 현재 숨은 위치 | Actor Transform | 전달 금지 | 보이지 않고 다른 합법적 센서도 없을 때 |
| 이동 방향·접근 속도 | 연속된 감지 위치 | 감지 위치 기반 추정 속도와 closing speed | 충분한 유효 샘플이 있을 때 |
| 시야 상태 | AI Sight | visible, sight strength, visible duration, time since seen | Sight Cache가 유효할 때 |
| 가림 정보 | AI Sight + 선택적 Trace | line-of-sight, 선택적 exposure ratio | 시야 검사 시 |
| 절대 월드 좌표 | World Transform | 원칙적으로 전달하지 않음 | 구역 ID나 특별한 월드 목표만 예외 |
| Ground Truth | Actor Transform | 학습 평가·디버그 로그 전용 | 모델 입력과 물리적으로 분리 |

## 2.5 위치 정보의 의미

모델이 받는 `target_position`은 항상 **지각된 위치(perceived position)**다.

위치 출처 우선순위:

```text
1. 현재 Sight 성공 위치
2. 최근 Hearing Event 위치
3. TTL이 남은 마지막 목격 위치
4. 명시적으로 알려진 World Target 위치
5. 그 외에는 invalid / entity_mask = 0
```

동일 Actor가 Sight와 Hearing에 동시에 잡힌 경우 Actor Entity에 감각 상태를 합칠 수 있다. 다만 발소리의 원인을 확정할 수 없거나 Actor 없이 발생한 소리는 별도의 Sound Event Entity로 유지한다.

## 2.6 MVP에서 다루지 않는 시각 입력

초기 버전의 “시야”는 카메라 RGB 이미지를 신경망에 직접 넣는 Computer Vision이 아니다. 다음과 같은 **구조화된 시각 센서**를 사용한다.

- 보이는가
- 어느 방향에 있는가
- 얼마나 먼가
- 얼마나 오래 보였는가
- 언제 마지막으로 보였는가
- 가려졌는가
- 접근 중인가
- 무기를 들고 있는가

이미지 기반 인식, 물체 검출, 포즈 추정은 V2 이후 별도 모듈로 확장한다.

---

# 3. 전체 저장소와 프로젝트 구조

한 저장소 안에 Unreal과 ML을 함께 두되, 빌드와 의존성은 분리한다.

```text
AI-Native-NPC/
├─ README.md
├─ contracts/
│  ├─ observation_schema.json
│  ├─ entity_schema.json
│  ├─ candidate_schema.json
│  ├─ skill_registry.json
│  ├─ normalization.json
│  ├─ model_manifest.schema.json
│  └─ golden_samples/
│     ├─ observation_0001.json
│     ├─ expected_tensors_0001.npz
│     └─ ...
│
├─ ml/
│  ├─ pyproject.toml
│  ├─ configs/
│  │  ├─ model_mvp.yaml
│  │  ├─ train_imitation.yaml
│  │  └─ export_onnx.yaml
│  ├─ src/ai_native_npc/
│  │  ├─ contract/
│  │  ├─ data/
│  │  ├─ models/
│  │  ├─ losses/
│  │  ├─ evaluation/
│  │  └─ export/
│  ├─ tools/
│  │  ├─ generate_scenarios.py
│  │  ├─ request_teacher_labels.py
│  │  ├─ convert_ue_logs.py
│  │  ├─ train.py
│  │  ├─ export_onnx.py
│  │  └─ validate_onnx.py
│  └─ tests/
│
├─ unreal/
│  └─ AINativeNPCDemo/
│     ├─ AINativeNPCDemo.uproject
│     ├─ Config/
│     ├─ Content/
│     │  ├─ ThirdPerson/
│     │  └─ AINativeNPC/
│     │     ├─ Blueprints/
│     │     ├─ Characters/
│     │     ├─ Data/
│     │     ├─ Models/
│     │     ├─ UI/
│     │     ├─ Maps/
│     │     ├─ Animations/
│     │     └─ Tests/
│     ├─ Plugins/
│     │  └─ AINativeNPC/
│     │     ├─ AINativeNPC.uplugin
│     │     └─ Source/
│     │        ├─ AINativeNPCRuntime/
│     │        ├─ AINativeNPCEditor/
│     │        └─ AINativeNPCTests/
│     └─ Source/AINativeNPCDemo/
│
└─ artifacts/
   ├─ models/
   │  ├─ npc_policy_mvp.onnx
   │  ├─ model_manifest.json
   │  └─ model_card.md
   └─ reports/
```

## 3.1 모듈 분리 원칙

### `AINativeNPCRuntime`

패키지 빌드에 포함되는 런타임 코드다.

- NPC Character와 AIController
- AI Perception 연결
- Observation 인코딩
- Candidate 생성
- NNE 추론
- Skill 실행
- 런타임 로그
- 안전 fallback

### `AINativeNPCEditor`

에디터에서만 필요한 제작 도구다.

- NPC Decision Inspector
- 상황 생성기
- 데이터 캡처
- 모델 계약 검증
- Model Asset 검사
- Profile 제작 도구

### `AINativeNPCTests`

자동화 테스트와 Functional Test 지원 코드를 둔다.

- Golden Tensor 테스트
- Candidate/Mask 테스트
- NNE parity 테스트
- Skill 실행 테스트
- 패키지 smoke test 지원

---

# PART A. 오프라인 신경망 구현 계획

# 4. 신경망 시스템의 책임

신경망 시스템은 다음 질문에 답한다.

> 현재 NPC 상태와 주변 상황에서, 제시된 후보 행동 중 어떤 행동이 가장 적절한가?

모델이 직접 생성하지 않는 항목:

- 월드 좌표 경로
- 매 프레임 이동 입력
- 애니메이션 Pose
- 충돌 결과
- 공격 성공 판정
- 퀘스트 상태 변경
- 존재하지 않는 임의의 행동 문자열

모델이 출력하는 항목:

- 후보별 적합도 점수
- 선택적 행동 강도
- 선택적 최소 지속 시간 제안
- 선택적 선호 거리
- 다음 GRU Hidden State
- 선택적 감정 변화 제안

---

# 5. 모델–클라이언트 Tensor 계약

## 5.1 권장 고정 크기

MVP는 Padding과 Mask를 사용하는 고정 최대 크기 Tensor로 시작한다.

| Tensor | Shape | Type | 설명 |
|---|---:|---|---|
| `global_state` | `[B, 96]` | float32 | NPC 자기 상태, 성격, 감정, 관계, 현재 Skill |
| `entities` | `[B, 8, 56]` | float32 | 플레이어, 다른 NPC, 소리·마지막 목격 위치 등 지각된 주변 개체 |
| `entity_mask` | `[B, 8]` | float32 | 유효 개체는 1, Padding은 0 |
| `candidates` | `[B, 32, 56]` | float32 | Skill, 대상 슬롯, 공간·시야 pair feature, 행동 메타데이터 |
| `candidate_mask` | `[B, 32]` | float32 | 실행 가능한 후보는 1, 무효/Padding은 0 |
| `hidden_in` | `[B, 128]` | float32 | NPC별 GRU 상태 |
| `candidate_scores` | `[B, 32]` | float32 | 후보별 원시 점수 |
| `action_parameters` | `[B, 32, 4]` | float32 | 후보별 강도·지속 시간·선호 거리·긴급도 |
| `hidden_out` | `[B, 128]` | float32 | 다음 GRU 상태 |

`B`는 batch size다. 첫 통합 단계는 `B=1`로 시작하며, 성능 고도화 단계에서 `B=8` 또는 `B=16` 전용 Model Instance를 추가한다.

## 5.2 float32 중심 계약

초기 버전은 Unreal 측 Tensor Binding 복잡도를 줄이기 위해 모든 입력을 float32로 통일한다.

- Skill ID는 one-hot 또는 registry 기반 float encoding으로 전달한다.
- Target slot은 `8개 entity + NoTarget`의 9차원 one-hot으로 전달한다.
- Mask는 0 또는 1의 float로 전달한다.
- enum 원시 ordinal을 모델 입력으로 직접 사용하지 않는다.

이후 모델이 안정된 뒤 int64 Embedding 입력으로 변경할 수 있으나, 계약 변경은 schema major version 증가로 처리한다.

## 5.3 `global_state` 초기 구성

`global_state`에는 Manny 자신의 상태를 넣는다. 맵 절대 좌표를 그대로 넣기보다, 이동 상태와 구역 문맥을 사용한다.

| 그룹 | 차원 | 예시 |
|---|---:|---|
| 자기 상태·자기 Pose | 32 | 체력, 속도, 로컬 속도 XYZ, 가속도, 정면/오른쪽 벡터, 피격, 무기, 현재 행동 시간 |
| 성격 | 10 | 공격성, 용기, 호기심, 인내심 등 |
| 감정 | 8 | 공포, 분노, 의심, 긴장 등 |
| 플레이어 관계 | 8 | 호감, 신뢰, 존중, 두려움 등 |
| 역할 one-hot | 8 | Guard, Civilian, Companion 등 |
| 현재 Skill one-hot | 16 | MVP Skill Registry |
| 최근 Skill 결과 | 6 | 성공, 실패, 취소, 진행 중 등 |
| 월드 Context | 4 | 안전 구역, 제한 구역, 실내/실외, 전투 허용 |
| Reserved | 4 | schema 호환용 예약 공간 |
| 합계 | 96 |  |

## 5.4 `entities` 초기 구성

각 Entity는 Actor뿐 아니라 SoundLocation, LastSeenLocation, Cover, Exit 같은 비Actor 관심점도 표현한다. 모든 공간 값은 Manny 로컬 좌표계로 변환한다.

| 그룹 | 차원 | 예시 |
|---|---:|---|
| Entity type one-hot | 8 | Player, NPC, Sound, LastSeen, Cover, Exit, Object 등 |
| 상대 위치·Pose·Motion | 16 | 상대 XYZ, 3D/평면/log 거리, bearing sin/cos, elevation sin/cos, 앞뒤·좌우, 감지 기반 상대 속도 XYZ, closing speed |
| Sight 상태 | 12 | visible now, line-of-sight, sight strength, sight confidence, time since seen, visible duration, FOV 중심 편차, sight acquire/lost 정보 |
| Hearing·Memory·출처 | 8 | heard recently, time since heard, loudness, position source one-hot, position age, position confidence |
| 위협·상태 | 6 | 무기, 공격 중, 체력 추정, threat hint, interactable, alive |
| 관계 | 6 | 호감, 신뢰, 공포, 적대, 빚, 의심 |
| 합계 | 56 |  |

### 상대 위치·Pose·Motion 16차원 권장 순서

```text
0  rel_x
1  rel_y
2  rel_z
3  distance_3d
4  distance_planar
5  log_distance
6  bearing_sin
7  bearing_cos
8  elevation_sin
9  elevation_cos
10 forward_component
11 right_component
12 estimated_vel_x
13 estimated_vel_y
14 estimated_vel_z
15 closing_speed
```

`rel_x/y/z`와 속도는 `MannyTransform.InverseTransformPositionNoScale()` 또는 이에 상응하는 로컬 변환 결과를 정규화해 사용한다.

## 5.5 `candidates` 초기 구성

| 그룹 | 차원 | 설명 |
|---|---:|---|
| Skill one-hot | 16 | Skill Registry의 고정 16개 슬롯 |
| Target slot one-hot | 9 | Entity 8개 + NoTarget |
| Target type | 7 | Actor, Sound, LastSeen, WorldLocation, Cover 등 |
| 공간·시야 Pair Feature | 12 | 거리, 방향 정렬, 현재 보임, 최근 들림, 위치 신뢰도, 위치 age, path 가능, 요구 LoS 충족 등 |
| 기본 파라미터·제약 | 12 | 기본 지속 시간, 속도, 위험, cooldown, 최소/최대 거리, interrupt 가능 여부 등 |
| 합계 | 56 |  |

공간·시야 Pair Feature는 행동의 물리적 전제와 현재 대상 상태를 표현한다. “가까우므로 공격이 좋다” 같은 선호 점수를 코드에서 넣어서는 안 된다.

## 5.6 Mask 규칙

- `entity_mask == 0`인 Entity는 attention과 target aggregation에서 제외한다.
- `candidate_mask == 0`인 후보는 최종 점수를 매우 작은 값으로 만든다.
- Unreal 클라이언트도 모델 출력 이후 다시 Mask를 검증한다.
- 모든 후보가 Mask된 경우 모델 결과를 사용하지 않고 `Idle` 또는 `ContinueCurrentAction` fallback을 실행한다.

---

## 5.7 지각 위치 계약

위치 출처는 다음 enum과 동일한 의미로 Python과 Unreal에서 관리한다.

```text
Invalid
SightCurrent
HearingEvent
LastSeenMemory
ScriptedWorldTarget
```

필수 규칙:

1. `SightCurrent`일 때만 현재 Actor Transform에서 target position을 갱신한다.
2. Sight가 끊긴 프레임부터는 Actor의 현재 Transform을 읽어 모델 입력을 갱신하지 않는다.
3. `HearingEvent`는 소리 발생 위치이며, Instigator의 실제 현재 위치와 동일하다고 가정하지 않는다.
4. `LastSeenMemory`는 마지막 목격 순간에 저장된 좌표를 고정하고, 시간에 따라 confidence를 감소시킨다.
5. 위치 출처가 `Invalid`이면 해당 Entity를 제거하거나 position-valid feature를 0으로 만든다.
6. Ground Truth 좌표는 학습 평가와 Editor Debug에만 기록하며 ONNX 입력 배열에는 포함하지 않는다.

## 5.8 로컬 좌표 및 정규화 계약

절대 월드 좌표를 모델에 직접 넣으면 맵마다 분포가 달라지고 위치를 외우기 쉬우므로 금지한다.

```cpp
const FVector LocalPosition =
    NPCTransform.InverseTransformPositionNoScale(PerceivedWorldPosition);

const FVector LocalVelocity =
    NPCTransform.InverseTransformVectorNoScale(EstimatedWorldVelocity);
```

권장 정규화:

```text
rel_x/y/z        = clamp(local / spatial_max_distance, -1, 1)
distance         = clamp(distance / spatial_max_distance, 0, 1)
log_distance     = log1p(distance) / log1p(spatial_max_distance)
position_age     = clamp(age / position_memory_ttl, 0, 1)
position_conf    = clamp(confidence, 0, 1)
bearing/elevation = sin/cos
```

공간 전체를 회전시켜도 동일한 상대 상황이면 동일한 Feature가 만들어져야 한다. 이를 **회전 불변 Golden Test**로 검증한다.

---

# 6. 계약 파일과 코드 생성

Python과 Unreal 양쪽에서 Feature 순서를 수동으로 중복 작성하면 반드시 불일치가 발생한다. 따라서 계약 파일에서 양쪽 코드를 생성한다.

## 6.1 계약 원본

- `contracts/observation_schema.json`
- `contracts/entity_schema.json`
- `contracts/candidate_schema.json`
- `contracts/skill_registry.json`
- `contracts/normalization.json`

## 6.2 생성 결과

`tools/generate_contract.py`는 다음 파일을 생성한다.

```text
ml/src/ai_native_npc/contract/generated_contract.py
unreal/.../Public/Generated/NPCModelContract.generated.h
unreal/.../Content/AINativeNPC/Data/DA_NPCModelContract.uasset용 JSON
```

## 6.3 Skill ID 안정성

C++ enum의 선언 순서에 의존하지 않는다.

```json
{
  "registry_version": "1.0.0",
  "skills": [
    { "id": 0, "name": "Idle" },
    { "id": 1, "name": "ContinueCurrentAction" },
    { "id": 2, "name": "LookAt" },
    { "id": 3, "name": "TurnTo" },
    { "id": 4, "name": "Approach" },
    { "id": 5, "name": "KeepDistance" },
    { "id": 6, "name": "RetreatFrom" },
    { "id": 7, "name": "Investigate" },
    { "id": 8, "name": "SearchArea" },
    { "id": 9, "name": "Greet" },
    { "id": 10, "name": "Warn" },
    { "id": 11, "name": "CallForHelp" },
    { "id": 12, "name": "TakeCover" },
    { "id": 13, "name": "Flee" },
    { "id": 14, "name": "Attack" },
    { "id": 15, "name": "Interact" }
  ]
}
```

Skill을 삭제하지 말고 deprecated 처리한다. ID 재사용은 금지한다.

## 6.4 Model Manifest

ONNX와 함께 다음 manifest를 배포한다.

```json
{
  "model_id": "npc_policy_spatial_mvp",
  "model_version": "0.4.0",
  "schema_version": "2.0.0",
  "skill_registry_version": "1.0.0",
  "normalization_version": "2.0.0",
  "max_entities": 8,
  "max_candidates": 32,
  "hidden_size": 128,
  "inputs": {
    "global_state": [1, 96],
    "entities": [1, 8, 56],
    "entity_mask": [1, 8],
    "candidates": [1, 32, 56],
    "candidate_mask": [1, 32],
    "hidden_in": [1, 128]
  },
  "outputs": {
    "candidate_scores": [1, 32],
    "action_parameters": [1, 32, 4],
    "hidden_out": [1, 128]
  },
  "onnx_sha256": "...",
  "contract_sha256": "...",
  "dataset_version": "ue_spatial_sight_audio_mvp_2026_01"
}
```

Unreal 클라이언트는 다음 중 하나라도 다르면 모델을 실행하지 않는다.

- schema version
- Skill Registry version
- Tensor 개수와 shape
- 정규화 version/hash
- 지원 모델 major version

---

# 7. 권장 신경망 아키텍처

## 7.1 전체 구조

Entity Encoder는 위치·이동, 감각 상태, 의미·관계를 서로 다른 Branch로 먼저 인코딩한 뒤 결합한다.

```text
global_state [B,96]
        │
        ▼
State MLP 96→128→128
        │
        └───────────────────────────────┐
                                        │
entities [B,8,56]                       │
        │                               │
        ├─ Spatial Branch 16→32         │
        ├─ Perception Branch 20→32      │
        └─ Semantic Branch 20→32        │
                    │                   │
                    ▼                   │
             Concat 96→64               │
                    │                   │
       Masked Entity Attention →128     │
                    │                   │
                    └──────────┬────────┘
                               ▼
                         Context 256
                               │
hidden_in [B,128] ───────► GRU Cell 128
                               │
                               ▼
                          Memory 128
                               │
                               ├───────────────────────────────┐
                               │                               │
candidates [B,32,56]           │                               │
        │                      │                               │
Candidate MLP 56→64            │                               │
                               │                               │
Target slot                    │                               │
        │                      │                               │
Entity Embedding 선택 →64     │                               │
                               │                               │
Memory 128 + Candidate 64 + Target 64 = 256                   │
                               │
                               ▼
                    Score MLP 256→128→64→1
                               │
                               ▼
                   candidate_scores [B,32]
```

Branch 입력 분할:

- Spatial 16: 상대 위치, 거리, 방위각, 고도각, 감지 기반 속도, closing speed
- Perception 20: Sight 12 + Hearing/Memory/Position Source 8
- Semantic 20: Entity Type 8 + 위협·상태 6 + 관계 6

이 구조를 사용하면 같은 상대 위치라도 `SightCurrent`, `HearingEvent`, `LastSeenMemory` 상태를 서로 다르게 표현할 수 있다.

## 7.2 권장 Layer

- Activation: SiLU
- 정규화: LayerNorm
- Entity Attention Head: 2~4
- GRU hidden: 128
- Dropout: 학습에서만 0.05~0.15
- 총 파라미터 목표: 약 0.5M~3M
- Candidate Scoring은 32개 후보에 대해 vectorized 실행

## 7.3 출력 파라미터

`action_parameters[..., 4]`는 다음으로 시작한다.

1. `intensity`: `[0,1]`
2. `duration_scale`: `[0,1]`을 Skill별 실제 범위로 변환
3. `preferred_distance`: `[0,1]`을 Skill별 거리 범위로 변환
4. `urgency`: `[0,1]`

모델 값은 제안값이며 Unreal Skill Definition의 허용 범위로 clamp한다.

---

# 8. 학습 데이터 파이프라인

## 8.1 데이터 출처

데이터는 다음 네 경로를 결합한다.

1. Python 절차적 상황 생성
2. Unreal PIE 시나리오 생성 및 실제 Observation 캡처
3. LLM 교사의 후보 행동 Ranking
4. 사람의 행동 시연·선호 비교·QA 수정

## 8.2 Unreal 캡처 데이터 우선 원칙

최종 학습 데이터의 핵심은 Unreal이 실제로 만든 Observation이어야 한다.

이유:

- Unreal AI Perception의 거리, stimulus age, sight 결과와 동일한 분포 사용
- NavMesh와 Skill `CanExecute` 결과 반영
- Python에서 가정한 값과 런타임 Feature 차이 방지
- 실제 Candidate Generator의 후보 분포 학습

권장 흐름:

```text
UE Editor Scenario Runner
→ Observation + Candidates + Mask를 JSONL로 기록
→ Python converter가 Parquet/NPZ로 변환
→ LLM 또는 사람이 후보 Ranking 부여
→ 학습 Dataset 생성
```

## 8.3 한 샘플의 필수 데이터

```json
{
  "episode_id": "ep_000103",
  "step": 18,
  "npc_profile_id": "guard_cautious",
  "observation": {},
  "entities": [],
  "candidates": [],
  "candidate_mask": [],
  "teacher_ranking": [3, 7, 0],
  "teacher_scores": {
    "3": 0.91,
    "7": 0.63,
    "0": 0.20
  },
  "selected_action": null,
  "skill_result": null,
  "model_version": null
}
```

## 8.4 학습 단계

### 단계 A — 단일 프레임 Ranking

- GRU 없이 State/Entity/Candidate Scorer부터 학습
- 후보 행동 순위가 안정적으로 학습되는지 확인
- UE에서 NNE 통합을 먼저 검증

권장 Loss:

```text
L = 1.0 * ListwiseRankingLoss
  + 0.5 * PairwiseRankingLoss
  + 0.2 * CandidateScoreRegression
  + 0.1 * ActionParameterHuber
```

### 단계 B — 시퀀스 모방학습

- GRU 추가
- 연속된 16~64 decision step으로 학습
- 이전 행동 결과와 사건 순서를 반영
- hidden state burn-in 4~16 step

### 단계 C — 실제 플레이 보정

- 모델 확신도가 낮은 샘플 수집
- QA가 기대 행동 또는 선호 비교 입력
- 이상 행동을 재현 데이터셋에 추가
- 기존 데이터와 혼합하여 재학습

### 단계 D — 선택적 강화학습

PPO 등은 다음 목적에만 사용한다.

- 조사 효율
- 전투 거리 유지
- 엄폐와 후퇴 타이밍
- 협동
- 장기 임무 성공률

자연스러움을 처음부터 PPO 보상만으로 학습시키지 않는다.

---

## 8.5 위치·시야 학습 데이터 요구사항

절차적 데이터 생성기는 다음 변수를 독립적으로 조합해야 한다.

- Quinn의 Manny 기준 극좌표: 거리, 방위각, 높이
- Quinn 이동 방향과 속도
- Manny의 회전 방향
- Sight Radius 안/밖
- Peripheral Vision 경계 안/밖
- 벽, 기둥, 문에 의한 가림
- 현재 보임, 방금 시야 상실, 오래전에 시야 상실
- 소리 있음/없음
- 보이지만 조용함
- 들리지만 보이지 않음
- 동일 위치에서 시야 조건만 다른 counterfactual pair
- 동일 시야에서 관계와 성격만 다른 pair

### 위치 누출 방지 데이터 검사

각 샘플은 다음 두 위치를 별도 필드로 저장할 수 있다.

```text
perceived_target_location  → 모델 입력용
ground_truth_location      → 평가 전용
```

데이터 로더는 `ground_truth_location`을 모델 Feature 생성 함수에 전달하지 않아야 한다. 테스트에서는 숨은 플레이어의 ground truth를 이동시켰을 때, perceived input이 동일하면 모델 입력 Tensor도 완전히 동일한지 검사한다.

### 권장 Augmentation

- 월드 전체 Yaw 회전
- 거리와 위치에 작은 센서 노이즈 추가
- Sight/Hearing modality dropout
- position age와 confidence jitter
- 일부 Entity 순서 shuffle
- occlusion on/off counterfactual
- 시야 상실 후 last-seen TTL 다양화

---

# 9. ONNX Export와 검증

## 9.1 Export 요구사항

- 입력과 출력 이름을 manifest와 동일하게 고정
- batch 축만 동적으로 허용하거나, 고정 batch 모델을 별도 export
- Custom ONNX Operator 사용 금지
- NNE/NNERuntimeORT가 지원하는 표준 연산으로 구성
- `eval()` 상태에서 export
- Dropout 제거 확인
- 모델 내부의 Mask 처리 검증

## 9.2 Export 산출물

```text
npc_policy_mvp.onnx
model_manifest.json
normalization.json
skill_registry.json
model_card.md
onnx_validation_report.json
```

## 9.3 Python 검증

- PyTorch와 ONNX Runtime 출력 오차 비교
- 1,000개 이상 random valid input 비교
- 모든 후보 mask, entity 없음, 최대 entity 등 경계값 테스트
- NaN/Inf 검출
- 출력 shape 검사
- 동일 hidden input에 대한 재현성 검사

## 9.4 Unreal parity 검증

Golden Sample을 이용해 다음을 비교한다.

```text
Python Feature Encoder 결과
       ==
Unreal Feature Encoder 결과

Python ONNX Runtime 결과
       ≈
Unreal NNE 결과
```

허용 오차는 모델 정밀도별로 정의한다.

- FP32 초기 목표: `absolute error <= 1e-4`
- FP16/INT8은 별도 tolerance 정의

---

# PART B. Unreal Engine 5.7 클라이언트 구현 계획

# 10. UE 5.7 프로젝트 생성

## 10.1 프로젝트 생성 절차

1. Unreal Engine 5.7 실행
2. `Games` 선택
3. `Third Person` 템플릿 선택
4. Project Type을 `C++`로 선택
5. Variant는 `None` 선택
6. Starter Content는 선택 사항
7. 프로젝트명: `AINativeNPCDemo`
8. 첫 빌드 성공 확인

Third Person 표준 템플릿은 기본 플레이어로 Quinn을 사용한다. 본 계획에서는 Quinn을 플레이어로 유지하고 Manny를 NPC로 별도 생성한다.

## 10.2 필수 플러그인

Editor → Plugins에서 다음을 활성화한다.

- Neural Network Engine (`NNE`)
- Neural Network Engine Runtime ORT (`NNERuntimeORT`)
- StateTree — 선택
- Gameplay StateTree — 선택
- Gameplay Tags — 프로젝트에서 사용

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

StateTree를 사용하지 않는 MVP에서는 마지막 두 플러그인은 제외할 수 있다.

## 10.3 Runtime Module 의존성

`AINativeNPCRuntime.Build.cs`의 권장 시작점:

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
    "DeveloperSettings"
});

PrivateDependencyModuleNames.AddRange(new string[]
{
    "Json",
    "JsonUtilities"
});

// StateTree 기반 Skill 실행기를 사용할 때만 추가
// "StateTreeModule"
// "GameplayStateTreeModule"
```

`NNERuntimeORT`는 runtime plugin으로 활성화하고, C++ 코드는 NNE의 CPU interface를 통해 runtime을 검색한다. 엔진 패치에 따라 모듈 노출 방식이 바뀔 수 있으므로 실제 UE 5.7 설치본의 `.uplugin`과 header를 CI에서 검증한다.

---

# 11. Manny NPC와 Quinn Player 구성

## 11.1 Quinn Player

기존 `BP_ThirdPersonCharacter`를 유지한다.

추가 Component:

- `AIPerceptionStimuliSourceComponent`
- `PlayerNoiseEmitterComponent`

설정:

- Sight에 대한 Stimuli Source 등록
- 발소리·점프 착지·충돌 소음을 Hearing Event로 보고
- 플레이어 상태를 NPC가 조회할 수 있는 가벼운 인터페이스 제공

권장 인터페이스:

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
    virtual float GetNPCThreatLevel() const = 0;
    virtual bool IsWeaponDrawnForNPC() const = 0;
    virtual FGameplayTagContainer GetNPCObservableTags() const = 0;
};
```

## 11.2 Manny NPC Blueprint

새 Blueprint:

```text
BP_AINativeNPC_Manny
Parent Class: AAINativeNPCCharacter
```

설정:

- Skeletal Mesh: `SKM_Manny`
- Animation Mode: `Use Animation Blueprint`
- Anim Class: `ABP_Manny`
- AI Controller Class: `AAINativeNPCController` 또는 `BP_AINativeNPCController`
- Auto Possess AI: `Placed in World or Spawned`
- Player Input Component 없음
- Camera Component 없음
- NPC Profile: `DA_NPCProfile_Guard_Cautious`
- Policy Asset: `DA_NPCPolicy_MVP`

Mesh transform과 Capsule/Movement 값은 `BP_ThirdPersonCharacter`의 Manny 적용 설정을 기준으로 복사한다. 숫자를 코드에 중복 고정하기보다 Blueprint Default에서 조정한다.

## 11.3 이동 설정

기본 locomotion:

- `Use Controller Rotation Yaw`: false
- `Orient Rotation to Movement`: true
- Skill이 명시적인 회전을 수행할 때만 rotation mode override
- 이동 중에는 `ABP_Manny`의 기존 locomotion을 유지

`TurnTo`/`LookAt` 중에는 다음 중 하나를 사용한다.

- V1: Actor Yaw를 보간
- V1.5: Aim Offset 또는 Control Rig로 상체/머리 시선 분리

## 11.4 테스트 레벨

새 레벨:

```text
L_AINativeNPC_MVP
```

필수 배치:

- Player Start
- Manny NPC 1~3명
- `NavMeshBoundsVolume`
- 시야 차폐용 벽
- 소리 테스트 구역
- 제한 구역 Trigger
- Debug UI Actor 또는 HUD

Navigation 표시를 켜서 Manny가 이동 가능한 영역을 확인한다.

---

# 12. Unreal 런타임 클래스 설계

## 12.1 핵심 클래스

| 클래스 | 위치 | 책임 |
|---|---|---|
| `AAINativeNPCCharacter` | Pawn | Manny Mesh, CharacterMovement, NPC Component 소유 |
| `AAINativeNPCController` | AIController | AI Perception, MoveTo, possession lifecycle |
| `UNPCPerceptionMemoryComponent` | Controller/Pawn | Sight/Hearing 원시 Stimulus와 감지 성공·상실 상태 저장 |
| `UNPCSpatialMemoryComponent` | Pawn | 현재 감지 위치, 마지막 목격 위치, 마지막 소리 위치, 위치 출처·age·confidence 관리 |
| `UNPCObservationComponent` | Pawn | 자기 Pose·감지 위치·시야·소리·상태·관계로 Observation 구성 |
| `UNPCVisibilityProbeComponent` | Pawn | 선택 기능: 머리/가슴/골반 Trace로 partial exposure 계산 |
| `UNPCRelationshipComponent` | Pawn | 대상별 관계 상태 저장 |
| `UNPCExplicitMemoryComponent` | Pawn | 구조화된 사건 기억 저장 |
| `UNPCCandidateGeneratorComponent` | Pawn | Skill×Target 후보와 Action Mask 생성 |
| `UNPCDecisionComponent` | Pawn | 판단 요청, hidden state, stale result 관리 |
| `UNPCSkillExecutorComponent` | Pawn | 선택된 Skill 시작·Tick·취소 |
| `UNPCInferenceWorldSubsystem` | WorldSubsystem | 모델 로드, NNE Instance Pool, 비동기 추론 큐 |
| `UNPCDebugComponent` | Pawn | 현재 Observation, 후보 점수, 결정 로그 제공 |
| `UAIPerceptionStimuliSourceComponent` | Player | Quinn을 Sight Stimuli Source로 등록 |
| `UPlayerNoiseEmitterComponent` | Player | 발소리 등 Hearing stimulus 발생 |
| `UAnimNotify_ReportAINoise` | Animation | 발 접촉 시점에 소리 보고 |

## 12.2 Data Asset

| Asset Class | 예시 Asset | 책임 |
|---|---|---|
| `UNPCProfileDataAsset` | `DA_NPCProfile_Guard_Cautious` | 역할, 성격, 기본 관계, 감정 감쇠 |
| `UNPCPolicyDataAsset` | `DA_NPCPolicy_MVP` | `UNNEModelData`, manifest, runtime, tensor shape |
| `UNPCSkillRegistryDataAsset` | `DA_NPCSkillRegistry_V1` | Skill ID와 실행 클래스 매핑 |
| `UNPCSkillDefinitionDataAsset` | `DA_Skill_Investigate` | 지속 시간, target type, 파라미터 범위 |
| `UNPCSensorConfigDataAsset` | `DA_NPCSensor_Guard` | Sight/Hearing 범위, FOV, MaxAge, 위치 기억 TTL, confidence 감쇠 |

## 12.3 모델 공유와 NPC별 상태

공유할 것:

- ONNX/NNE Model Data
- CPU Model
- Model Instance Pool
- Feature Schema
- Normalization
- Skill Registry

NPC별로 유지할 것:

- GRU Hidden State
- 현재 Skill
- 최근 결정 ID
- 관계와 감정
- Perception Cache
- Spatial Memory와 마지막 목격/소리 위치
- 명시적 기억
- 현재 in-flight request 여부

모델 자체를 NPC마다 중복 로드하지 않는다.

---

# 13. 주요 C++ 데이터 구조

```cpp
UENUM(BlueprintType)
enum class ENPCSkillId : uint8
{
    Idle,
    ContinueCurrentAction,
    LookAt,
    TurnTo,
    Approach,
    KeepDistance,
    RetreatFrom,
    Investigate,
    SearchArea,
    Greet,
    Warn,
    CallForHelp,
    TakeCover,
    Flee,
    Attack,
    Interact
};

UENUM(BlueprintType)
enum class ENPCTargetType : uint8
{
    None,
    Actor,
    SoundLocation,
    WorldLocation,
    Cover,
    Exit,
    Interactable
};

UENUM(BlueprintType)
enum class ENPCDecisionTrigger : uint8
{
    Periodic,
    SkillCompleted,
    SkillFailed,
    SightAcquired,
    SightLost,
    TargetMovedSignificantly,
    ImportantSound,
    Damaged,
    RelationshipChanged,
    Emergency
};

UENUM(BlueprintType)
enum class ENPCPositionSource : uint8
{
    Invalid,
    SightCurrent,
    HearingEvent,
    LastSeenMemory,
    ScriptedWorldTarget
};
```

권장 구조체:

```cpp
USTRUCT(BlueprintType)
struct FNPCPerceivedEntity
{
    GENERATED_BODY()

    UPROPERTY() FGuid StableId;
    UPROPERTY() TWeakObjectPtr<AActor> Actor;
    UPROPERTY() ENPCTargetType TargetType = ENPCTargetType::None;
    UPROPERTY() ENPCPositionSource PositionSource = ENPCPositionSource::Invalid;

    // 모델 입력에 사용할 지각 위치. 현재 보이지 않으면 Actor의 실시간 위치로 갱신하지 않는다.
    UPROPERTY() FVector PerceivedWorldLocation = FVector::ZeroVector;
    UPROPERTY() FVector LastSeenWorldLocation = FVector::ZeroVector;
    UPROPERTY() FVector LastHeardWorldLocation = FVector::ZeroVector;
    UPROPERTY() FVector EstimatedWorldVelocity = FVector::ZeroVector;

    UPROPERTY() float LastSeenWorldTime = -1.0f;
    UPROPERTY() float LastHeardWorldTime = -1.0f;
    UPROPERTY() float PositionAge = 0.0f;
    UPROPERTY() float PositionConfidence = 0.0f;
    UPROPERTY() float SightStrength = 0.0f;
    UPROPERTY() float HearingStrength = 0.0f;
    UPROPERTY() float ContinuousVisibleTime = 0.0f;

    UPROPERTY() bool bVisibleNow = false;
    UPROPERTY() bool bHasLineOfSight = false;
    UPROPERTY() bool bHeardRecently = false;
    UPROPERTY() bool bHasLastSeenMemory = false;
};

USTRUCT()
struct FNPCCandidateAction
{
    GENERATED_BODY()

    UPROPERTY() int32 CandidateIndex = INDEX_NONE;
    UPROPERTY() ENPCSkillId SkillId = ENPCSkillId::Idle;
    UPROPERTY() ENPCTargetType TargetType = ENPCTargetType::None;
    UPROPERTY() int32 EntitySlot = INDEX_NONE;
    UPROPERTY() FGuid TargetStableId;
    UPROPERTY() bool bExecutable = false;
    UPROPERTY() FGameplayTag FailureReason;
    UPROPERTY() float BaseDuration = 0.0f;
    UPROPERTY() float BaseCost = 0.0f;
};
```

추론 요청에는 UObject pointer를 직접 넣지 않는다. Worker Thread로 전달되는 snapshot은 POD에 가까운 값과 고유 ID만 포함한다.

```cpp
struct FNPCInferenceRequest
{
    uint64 RequestId = 0;
    FGuid NPCId;
    uint32 DecisionEpoch = 0;
    double RequestedWorldTime = 0.0;

    TArray<float> GlobalState;
    TArray<float> Entities;
    TArray<float> EntityMask;
    TArray<float> Candidates;
    TArray<float> CandidateMask;
    TArray<float> HiddenIn;

    TArray<FNPCCandidateAction> CandidateSnapshot;
};
```

---

# 14. AI Perception·위치·시야 구현

## 14.1 Component 배치

`AAINativeNPCController`에 다음을 둔다.

- `UAIPerceptionComponent`
- `UAISenseConfig_Sight`
- `UAISenseConfig_Hearing`
- 선택: `UAISenseConfig_Damage`

Quinn Player에는 `UAIPerceptionStimuliSourceComponent`를 추가하고 Sight Sense에 등록한다. 발소리는 별도의 `UPlayerNoiseEmitterComponent`에서 Hearing Event로 보고한다.

AI Perception callback은 행동을 직접 실행하지 않는다. 다음 두 작업만 한다.

1. 원시 Stimulus를 `UNPCPerceptionMemoryComponent`에 기록
2. 감지 상태가 의미 있게 변한 경우 `UNPCDecisionComponent`에 재판단 요청

```cpp
void AAINativeNPCController::HandleTargetPerceptionUpdated(
    AActor* Actor,
    FAIStimulus Stimulus)
{
    const ENPCPerceptionChange Change =
        PerceptionMemory->RecordStimulus(Actor, Stimulus);

    SpatialMemory->ApplyPerceptionChange(Actor, Stimulus, Change);

    switch (Change)
    {
        case ENPCPerceptionChange::SightAcquired:
            DecisionComponent->RequestDecision(
                ENPCDecisionTrigger::SightAcquired);
            break;

        case ENPCPerceptionChange::SightLost:
            DecisionComponent->RequestDecision(
                ENPCDecisionTrigger::SightLost);
            break;

        case ENPCPerceptionChange::ImportantSound:
            DecisionComponent->RequestDecision(
                ENPCDecisionTrigger::ImportantSound);
            break;

        default:
            break;
    }
}
```

## 14.2 Sight 설정

`DA_NPCSensor_Guard`에서 다음 항목을 조정한다.

- Sight Radius
- Lose Sight Radius
- Peripheral Vision Half Angle Degrees
- Auto Success Range from Last Seen Location
- Point of View Backward Offset
- Near Clipping Radius
- Detection by Affiliation
- Max Age
- Starts Enabled

프로토타입 시작값 예시:

```text
Sight Radius                  2000 cm
Lose Sight Radius             2500 cm
Peripheral Vision Half Angle  70 deg
Sight Max Age                 4 sec
Last Seen Position TTL        6 sec
```

값은 게임 스케일과 플레이테스트에 따라 Data Asset에서 조정한다. 코드 상수로 박지 않는다.

## 14.3 시야 획득과 상실 처리

`FAIStimulus.WasSuccessfullySensed()`가 true인 Sight Stimulus:

- `bVisibleNow = true`
- `bHasLineOfSight = true`
- `PositionSource = SightCurrent`
- `PerceivedWorldLocation`을 현재 감지 위치로 갱신
- `LastSeenWorldLocation`과 `LastSeenWorldTime` 갱신
- 이전 감지 위치와 시간으로 `EstimatedWorldVelocity` 계산
- `ContinuousVisibleTime` 누적

false로 바뀐 Sight Stimulus:

- `bVisibleNow = false`
- `bHasLineOfSight = false`
- `PositionSource = LastSeenMemory`
- `PerceivedWorldLocation = LastSeenWorldLocation`
- 이후 Actor의 `GetActorLocation()`으로 숨은 위치를 갱신하지 않음
- `PositionAge` 증가
- `PositionConfidence` 감소
- TTL 만료 시 memory 제거

## 14.4 위치 출처 상태 머신

```text
Sight Acquired
  → SightCurrent
  → position confidence = 1.0

Sight Lost
  → LastSeenMemory
  → last seen position 고정
  → age 증가 / confidence 감소

Hearing Event
  → HearingEvent
  → sound event location 사용
  → actor current location으로 보정하지 않음

Memory TTL Expired
  → Invalid
  → entity 제거 또는 mask 0
```

시야와 소리가 동시에 들어온 경우:

- 현재 Sight가 성공이면 Actor Entity의 위치 출처는 `SightCurrent`
- Hearing 정보는 heard/loudness/age Feature로 병합
- Actor를 확인할 수 없는 소리는 별도의 Sound Event Entity 유지

## 14.5 상대 위치와 이동 Feature 계산

Manny 기준 로컬 좌표를 사용한다.

```cpp
const FTransform NPCTransform = NPC->GetActorTransform();

const FVector LocalPosition =
    NPCTransform.InverseTransformPositionNoScale(
        Entity.PerceivedWorldLocation);

const FVector LocalVelocity =
    NPCTransform.InverseTransformVectorNoScale(
        Entity.EstimatedWorldVelocity);

const float Distance3D = LocalPosition.Size();
const float DistancePlanar =
    FVector2D(LocalPosition.X, LocalPosition.Y).Size();

const float Bearing =
    FMath::Atan2(LocalPosition.Y, LocalPosition.X);

const float Elevation =
    FMath::Atan2(LocalPosition.Z, FMath::Max(DistancePlanar, 1.0f));
```

추가 Feature:

- target이 접근 중인지 이탈 중인지 나타내는 closing speed
- Manny 정면과 target 방향의 dot product
- target이 개인 공간 안에 있는지
- 현재 Skill target과 동일한지
- target position age와 confidence

`EstimatedWorldVelocity`는 감지된 위치 샘플로 계산한다. 시야 밖 Actor의 실제 `Velocity`를 직접 읽지 않는다.

## 14.6 Sight Feature

각 Actor에 대해 다음 값을 저장한다.

- 현재 감지 성공 여부
- 현재 line-of-sight 여부
- 감지 위치
- 마지막 목격 위치
- stimulus age
- stimulus strength
- 마지막으로 보인 시간
- 연속으로 보인 시간
- 최근 시야 진입/이탈 횟수
- Peripheral Vision 중심으로부터의 각도
- 위치 신뢰도
- Sight 위치와 Manny의 상대 위치·방향

기본 AI Sight는 이진적인 보임/안 보임으로 시작한다.

### 선택적 V1.5 — 부분 노출 비율

필요한 경우 Manny 눈 위치에서 Quinn의 다음 지점으로 Line Trace를 수행한다.

- 머리
- 가슴
- 골반

```text
0/3 visible → exposure 0.0
1/3 visible → exposure 0.33
2/3 visible → exposure 0.67
3/3 visible → exposure 1.0
```

이 값은 추가 Sight Feature로 사용할 수 있다. Trace 예산을 제한하고 모든 NPC에 매 프레임 실행하지 않는다.

## 14.7 Hearing Feature

소리는 Actor와 별개인 Event Entity로 관리한다.

```cpp
USTRUCT()
struct FNPCSoundEvent
{
    GENERATED_BODY()

    FGuid EventId;
    FVector Location;
    FGameplayTag NoiseTag;
    float Loudness;
    float MaxRange;
    float CreatedWorldTime;
    TWeakObjectPtr<AActor> Instigator;
};
```

최근 소리 이벤트는 TTL과 중요도를 기준으로 최대 4개 유지한다.

- 총성·폭발: 긴 TTL
- 발소리: 짧은 TTL
- 반복 발소리: 동일 Instigator/위치 근처 이벤트 병합
- Instigator가 있어도 보이지 않으면 Instigator의 현재 좌표를 사용하지 않음

## 14.8 Quinn 발소리

권장 구현은 Animation Notify다.

```text
ABP_Quinn이 사용하는 Walk/Run Animation
→ 발이 지면에 닿는 Frame에 AN_ReportAINoise 배치
→ UPlayerNoiseEmitterComponent::EmitFootstep 호출
→ UAISense_Hearing::ReportNoiseEvent
```

개념 코드:

```cpp
void UPlayerNoiseEmitterComponent::EmitFootstep(
    FVector Location,
    float SpeedNormalized,
    FGameplayTag SurfaceTag)
{
    const float Loudness =
        FootstepCurve->GetFloatValue(SpeedNormalized);

    UAISense_Hearing::ReportNoiseEvent(
        GetWorld(),
        Location,
        Loudness,
        GetOwner(),
        MaxFootstepRange,
        TEXT("Noise.Footstep"));
}
```

발소리 크기는 움직임 속도, crouch, 착지, 표면 재질로 조정하되, “NPC가 어떤 반응을 해야 하는가”는 소음 발생 코드에 포함하지 않는다.

## 14.9 감각 정보와 Ground Truth 분리

Editor와 자동 테스트에서는 다음을 모두 그릴 수 있다.

- Ground Truth Quinn 위치
- Manny가 현재 지각하는 위치
- 마지막 목격 위치
- 마지막 소리 위치

하지만 Runtime Inference Request에는 **지각 위치만** 복사한다. `FNPCInferenceRequest`에는 Actor Pointer나 Ground Truth Transform을 넣지 않는다.

# 15. Observation Builder

## 15.1 실행 시점

Observation은 매 프레임 만들지 않는다.

- 정기 판단 tick
- Sight 획득
- Sight 상실
- 감지된 target이 임계 거리 또는 임계 각도만큼 이동
- 중요 Hearing Stimulus 수신
- 현재 Skill 종료/실패
- 피해 발생
- 관계·퀘스트 상태 변경

보이는 target의 이동으로 매 프레임 추론하지 않도록 `TargetMovedSignificantly` 기준을 둔다.

예시:

```text
위치 변화 100 cm 이상
방위각 변화 10 deg 이상
거리 구간 변화
개인 공간 진입/이탈
```

이 기준은 추론 스케줄링 최적화이며 행동 선호 규칙이 아니다.

## 15.2 처리 순서

```text
1. Manny 자기 상태와 자기 Pose Snapshot
2. Profile에서 성격/역할 읽기
3. 감정/관계 읽기
4. Perception Cache와 Spatial Memory에서 지각 Entity 선정
5. 각 Entity의 위치 출처와 유효성 확인
6. 지각 위치를 Manny 로컬 좌표로 변환
7. Sight/Hearing/Memory Feature 작성
8. Explicit Memory에서 관련 기억 Top-K 선정
9. 현재 Skill 및 결과 기록
10. Candidate 생성
11. Feature Schema 순서로 float Tensor 생성
12. Normalization 적용
13. NaN/Inf, 범위, 위치 누출 검증
```

## 15.3 Entity 슬롯 선정

MVP 최대 8개 슬롯:

- 현재 Sight로 보이는 Player/Actor 최대 3개
- 최근 Sight를 잃었지만 TTL이 남은 LastSeen Actor 최대 2개
- 최근 Sound Event 최대 2개
- 중요 World Target 1개

동일 Actor가 현재 보이고 동시에 소리를 냈다면 Actor Entity 하나에 Sight와 Hearing Feature를 합친다. Actor를 식별하지 못한 소리는 별도 Sound Entity로 둔다.

Player라는 이유만으로 무조건 슬롯에 넣지 않는다. 다음 중 하나가 있어야 한다.

- 현재 보임
- 최근 들림
- 유효한 마지막 목격 기억
- 퀘스트 또는 대화가 명시적으로 위치를 알려줌

선정 기준은 모델 대신 런타임 성능을 위한 정보 보존 기준이다. 최신성, 감각 강도, 거리, 위치 confidence, 명시적 중요 태그는 사용할 수 있다. “적대적이면 우선” 같은 행동 선호 규칙은 넣지 않는다.

## 15.4 지각 위치 선택 의사 코드

```cpp
bool UNPCObservationComponent::ResolvePerceivedLocation(
    const FNPCPerceivedEntity& Entity,
    FVector& OutWorldLocation,
    ENPCPositionSource& OutSource) const
{
    if (Entity.bVisibleNow)
    {
        OutWorldLocation = Entity.PerceivedWorldLocation;
        OutSource = ENPCPositionSource::SightCurrent;
        return true;
    }

    if (Entity.bHeardRecently &&
        Entity.PositionSource == ENPCPositionSource::HearingEvent)
    {
        OutWorldLocation = Entity.LastHeardWorldLocation;
        OutSource = ENPCPositionSource::HearingEvent;
        return true;
    }

    if (Entity.bHasLastSeenMemory &&
        Entity.PositionConfidence > MinPositionConfidence)
    {
        OutWorldLocation = Entity.LastSeenWorldLocation;
        OutSource = ENPCPositionSource::LastSeenMemory;
        return true;
    }

    return false;
}
```

이 함수는 target Actor가 유효하다는 이유만으로 `Actor->GetActorLocation()`을 호출해서는 안 된다.

## 15.5 정규화

모든 Feature는 계약의 `normalization.json`을 사용한다.

- 상대 위치: 최대 공간 거리로 clamp
- 거리: 선형 거리와 log distance 병행
- 시간: 최대 기억 시간으로 clamp
- 각도: sin/cos
- boolean: 0/1
- confidence: `[0,1]`
- 성격·감정·관계: 계약 범위로 clamp
- 감지 기반 속도: 최대 예상 속도로 clamp

Unreal과 Python이 각각 임의의 상수를 사용하지 않는다.

## 15.6 위치 누출 Runtime Assertion

Development/Editor 빌드에서 다음 검사를 수행한다.

- `SightCurrent`인데 `bVisibleNow == false`면 오류
- `LastSeenMemory` 위치가 Sight Lost 이후 계속 바뀌면 오류
- `HearingEvent` 위치가 Instigator Transform을 따라 이동하면 오류
- Invalid Entity인데 position feature가 non-zero면 오류
- Ground Truth Buffer가 Inference Tensor Builder에 전달되면 오류

## 15.7 Ground Truth 로그

학습 평가와 QA를 위해 Ground Truth를 별도 로그 채널에 저장할 수 있다.

```json
{
  "perceived": {
    "source": "LastSeenMemory",
    "location": [120.0, -80.0, 0.0],
    "age": 1.4,
    "confidence": 0.72
  },
  "ground_truth_debug_only": {
    "location": [480.0, 210.0, 0.0]
  }
}
```

`ground_truth_debug_only` 필드는 모델 학습 Feature 생성에서 제외한다.

# 16. Candidate Generator

## 16.1 Candidate Generator가 해야 하는 것

- Skill과 Target의 의미적 호환성 확인
- 물리적 실행 가능 여부 확인
- 게임 규칙상 금지 여부 확인
- 최대 32개 후보 구성
- Candidate Tensor 작성

## 16.2 해서는 안 되는 것

- “뒤에서 소리가 나면 TurnTo 점수 증가”
- “관계가 낮으면 Warn 우선”
- “체력이 낮으면 Flee 우선”
- “플레이어가 가까우면 Attack 우선”

이런 선호는 모델이 학습한다.

## 16.3 허용되는 Affordance 규칙

| Skill | 허용 Target | 하드 실행 조건 예시 |
|---|---|---|
| Idle | None | 항상 가능 |
| ContinueCurrentAction | None | 현재 Skill이 계속 가능 |
| LookAt | Actor, SoundLocation, LastSeenLocation, WorldLocation | 유효한 지각 위치 존재 |
| TurnTo | Actor, SoundLocation, LastSeenLocation, WorldLocation | 유효한 지각 위치, 회전 가능 |
| Approach | Actor, LastSeenLocation | 위치 confidence 충족, Nav path 존재 가능성, 이동 가능 |
| KeepDistance | Actor | 현재 Sight 또는 충분히 신뢰 가능한 위치, 이동 가능 |
| RetreatFrom | Actor, LastSeenLocation | 유효한 위치, 이동 가능 |
| Investigate | SoundLocation, LastSeenLocation, WorldLocation | 위치 TTL 유효, Nav projection 성공 |
| Greet | Actor | 현재 Sight, 대화 가능, 대상 생존 |
| Warn | Actor | 현재 Sight 또는 게임 규칙상 확정된 Actor, 대화 가능 |
| CallForHelp | None/Actor | 호출 기능 사용 가능 |
| TakeCover | Cover | 유효 cover point 존재 |
| Flee | Exit/WorldLocation | 유효 flee point 존재 |
| Attack | Actor | 현재 Sight/공격 시스템이 요구하는 LoS, 공격 능력 보유, 퀘스트 허용 |
| Interact | Interactable | 상호작용 인터페이스 지원 |

## 16.4 Candidate 생성 의사 코드

```cpp
Candidates.Add(MakeNoTargetCandidate(Idle));

if (SkillExecutor->CanContinueCurrentSkill())
{
    Candidates.Add(MakeNoTargetCandidate(ContinueCurrentAction));
}

for (int32 EntitySlot = 0; EntitySlot < Entities.Num(); ++EntitySlot)
{
    for (const FSkillDefinition& Skill : SkillRegistry)
    {
        if (!Skill.SupportsTarget(Entities[EntitySlot].TargetType))
        {
            continue;
        }

        FNPCCandidateAction Candidate =
            BuildCandidate(Skill, Entities[EntitySlot], EntitySlot);

        Candidate.bExecutable = SkillExecutor->CanExecute(Candidate);
        Candidates.Add(Candidate);
    }
}

PadAndMaskToFixedSize(Candidates, 32);
```

`CanExecute`는 행동이 좋은지 나쁜지가 아니라 실행 가능한지만 반환한다.

---

## 16.5 공간·시야 Candidate Pair Feature

각 Candidate에는 다음과 같은 generic 실행 문맥을 포함한다.

- target distance
- target bearing
- facing alignment
- target visible now
- target heard recently
- target position source
- target position age
- target position confidence
- path projection success
- estimated path length
- Skill이 LoS를 요구하는가
- 현재 LoS 조건이 충족되는가

이 값은 모델이 행동 적합도를 판단하도록 돕지만, Candidate Generator가 후보 점수를 직접 조정하지는 않는다.

---

# 17. NNE 추론 Subsystem

## 17.1 역할

`UNPCInferenceWorldSubsystem`은 World당 하나 존재한다.

- Policy Asset 로드
- `UNNEModelData` 로드
- NNE CPU Runtime 탐색
- CPU Model 생성
- Model Instance Pool 생성
- 입력/출력 buffer 관리
- 비동기 추론 job queue
- 결과를 Game Thread로 반환
- 모델 및 계약 상태 모니터링

## 17.2 Runtime 선택

기본 runtime 이름:

```text
NNERuntimeORTCpu
```

하드코딩만 하지 말고 다음 순서로 선택한다.

1. Policy Asset의 선호 runtime 조회
2. NNE가 제공하는 CPU runtime 목록 확인
3. `NNERuntimeORTCpu` 사용 가능 여부 확인
4. 사용 불가 시 허용 목록에서 대체 runtime 탐색
5. 전부 실패하면 모델 비활성화와 fallback 정책 사용

## 17.3 모델 초기화 흐름

아래 코드는 API 흐름을 보여주는 skeleton이다. NNE는 Beta이므로 실제 UE 5.7 설치본 header의 반환 타입과 status enum을 최종 기준으로 한다.

```cpp
bool UNPCInferenceWorldSubsystem::InitializePolicy(
    UNPCPolicyDataAsset* Policy)
{
    UNNEModelData* ModelData = Policy->ModelData.LoadSynchronous();
    if (!ModelData)
    {
        return false;
    }

    const FString RuntimeName = Policy->PreferredRuntimeName;

    auto Runtime = UE::NNE::GetRuntime<UE::NNE::INNERuntimeCPU>(
        RuntimeName);
    if (!Runtime.IsValid())
    {
        return false;
    }

    auto Model = Runtime->CreateModelCPU(ModelData);
    if (!Model.IsValid())
    {
        return false;
    }

    auto Instance = Model->CreateModelInstanceCPU();
    if (!Instance.IsValid())
    {
        return false;
    }

    // Input shape는 instance 생성 후, RunSync 전에 한 번 설정한다.
    // 고정 shape instance는 runtime 중 반복 설정하지 않는다.
    ConfigureTensorShapes(*Instance, Policy->Manifest);

    ModelInstances.Add(MoveTemp(Instance));
    SharedModel = MoveTemp(Model);
    return true;
}
```

## 17.4 Tensor Binding

NNE CPU Tensor Binding에 전달하는 메모리는 호출자가 소유한다. 따라서 input/output 배열은 `RunSync`가 끝날 때까지 유효해야 한다.

권장 job 구조:

```cpp
struct FNPCInferenceJob
{
    FNPCInferenceRequest Request;

    TArray<float> CandidateScores;
    TArray<float> ActionParameters;
    TArray<float> HiddenOut;

    TArray<UE::NNE::FTensorBindingCPU> InputBindings;
    TArray<UE::NNE::FTensorBindingCPU> OutputBindings;
};
```

Buffer는 Job 객체 또는 Instance Worker가 소유한다. Game Thread의 임시 `TArray` pointer를 worker에 그대로 넘기지 않는다.

## 17.5 비동기 실행

NNE CPU의 synchronous run을 Game Thread에서 직접 호출하지 않는다.

```text
Game Thread
  → 요청 Snapshot 생성
  → Inference Queue에 enqueue

Worker Thread
  → 전용 Model Instance 획득
  → Tensor Binding 설정
  → RunSync
  → 결과 Queue에 enqueue

Game Thread
  → NPC 생존/Request ID/Epoch 검증
  → 결과 적용
```

규칙:

- 동일 Model Instance를 두 thread가 동시에 사용하지 않는다.
- Instance Pool의 각 instance는 한 번에 한 job만 처리한다.
- Actor/UObject 접근은 Game Thread에서만 수행한다.
- Worker에는 값 복사본과 stable ID만 전달한다.
- World 종료 시 신규 job 수신을 중지하고 in-flight job의 callback을 무효화한다.

## 17.6 Batch 전략

### Phase 1

- Batch 1
- Model Instance 1~2개
- 통합 정확성과 thread safety 우선

### Phase 2

- Batch 8 또는 16
- 고정 batch shape별 Instance Pool
- 부족한 row는 mask로 padding
- NPC별 hidden과 candidate snapshot mapping 유지

`SetInputTensorShapes`는 instance 초기화 시 고정 shape로 한 번 호출하고, 매 판단마다 반복하지 않는다.

---

# 18. Decision Component와 Scheduler

## 18.1 판단 요청 상태

`UNPCDecisionComponent`는 다음을 보유한다.

```text
NPC Stable ID
Current Request ID
Decision Epoch
In-flight 여부
Last Decision Time
Next Periodic Decision Time
Hidden State[128]
Current Skill ID
Current Target ID
Current Skill Start Time
```

## 18.2 Request coalescing

한 NPC에 여러 stimulus가 짧은 시간에 발생할 수 있다.

- 이미 inference 중이면 신규 요청 사유를 pending trigger에 병합
- 긴급 요청은 epoch를 증가시키고 이전 결과를 stale 처리
- 일반 Hearing Event 반복은 debounce
- Skill 완료 요청은 우선순위 높음

## 18.3 권장 판단 빈도

| NPC 상태 | 빈도 |
|---|---:|
| 화면 밖·비전투 | 1~2 Hz |
| 일반 상호작용 | 2~5 Hz |
| 전투 | 5~10 Hz |
| 피격·폭발·대상 사망 | 이벤트 기반 즉시 |

이동과 애니메이션은 매 프레임 실행하지만, 모델 판단은 위 빈도로 제한한다.

## 18.4 결과 적용 검증

NNE 결과를 적용하기 전에 확인한다.

- NPC가 아직 유효한가
- 동일 World인가
- Request ID가 최신인가
- Decision Epoch가 동일한가
- Candidate snapshot이 아직 유효한가
- Target actor 또는 location이 유효한가
- 후보가 현재도 `CanExecute` 가능한가
- 출력에 NaN/Inf가 없는가

유효하지 않은 결과는 폐기하며 hidden state도 반영하지 않는다.

---

# 19. Decision Stabilizer

모델의 raw score만으로 바로 행동을 바꾸면 행동 진동이 발생한다.

최종 점수:

```text
FinalScore
= ModelScore
- SkillSwitchCost
- TargetSwitchCost
- RecentRepeatPenalty
- RecentFailurePenalty
+ ContinueCurrentSkillBonus
```

이 보정은 상황별 행동 선호 규칙이 아니라 시간적 안정성과 실행 비용을 반영하는 공통 정책이다.

## 19.1 Skill 최소 지속 시간

| Skill | 초기 최소 지속 시간 |
|---|---:|
| LookAt | 0.5초 |
| TurnTo | 목표 각도 도달 또는 1.5초 |
| Greet | Montage/대사 종료 |
| Warn | 1.5초 |
| Investigate | 3초 |
| SearchArea | 5초 |
| Flee | 2초 |

## 19.2 긴급 인터럽트

- 피해 발생
- 폭발
- target 사망
- Nav path 실패
- 퀘스트 금지 상태 전환
- NPC incapacitated
- 플레이어의 즉각적인 공격

## 19.3 확신도 처리

모델 top-1과 top-2의 점수 차이가 임계값보다 작으면 다음 중 하나를 적용한다.

- 현재 Skill 유지
- 안전한 idle 행동
- stochastic sampling을 허용한 NPC Profile이면 제한적 sampling
- 디버그 로그에 low-confidence 플래그 기록

MVP 기본값은 현재 Skill 유지다.

---

# 20. Skill 실행 시스템

## 20.1 공통 인터페이스

```cpp
class INPCSkill
{
public:
    virtual bool CanExecute(
        const FNPCExecutionContext& Context,
        const FNPCCandidateAction& Candidate) const = 0;

    virtual void Start(
        const FNPCExecutionContext& Context,
        const FNPCCandidateAction& Candidate,
        const FNPCActionParameters& Parameters) = 0;

    virtual ENPCSkillStatus Tick(float DeltaSeconds) = 0;
    virtual void Cancel(ENPCSkillCancelReason Reason) = 0;
};
```

## 20.2 Skill 실행 방식

### `TurnTo`

- Actor 또는 location 방향 계산
- Yaw 차이를 shortest path로 계산
- 설정된 angular speed로 회전 보간
- 허용 각도 안에 들어오면 성공

### `LookAt`

- V1: `TurnTo`와 유사하게 몸 전체 회전
- V1.5: Head/Spine Aim Offset 또는 Control Rig 적용
- target 소실 시 마지막 위치를 잠시 유지

### `Approach`

- `AAIController::MoveToActor` 또는 `MoveToLocation`
- 모델의 preferred distance를 acceptance radius로 변환
- path failure를 Skill 실패로 기록

### `KeepDistance`

- target과 현재 거리 비교
- Skill 내부의 generic controller가 거리 오차를 줄이는 이동 target 계산
- “언제 KeepDistance를 선택할지”는 모델이 결정

### `Investigate`

권장 실행 순서:

```text
Target 위치 NavMesh projection
→ MoveToLocation
→ 도착 후 해당 방향 LookAt
→ 짧은 Search wait
→ Success
```

### `Greet` / `Warn`

- target 방향으로 회전
- Animation Montage 재생
- Dialogue Act Event 발생
- MVP에서는 사전 제작 대사 또는 subtitle 사용
- 런타임 LLM 연결은 후속 단계

### `Flee`

- target 반대 방향으로 NavMesh 후보점 생성
- 장애물과 도달 가능성 검사
- 적절한 후보점으로 MoveTo
- Flee 선택 자체는 모델이 결정

### `Attack`

표준 Third Person Variant `None`에는 완성된 전투 시스템이 없으므로 MVP에서는 다음 중 하나로 제한한다.

- 공격 Montage + Gameplay Event만 발생
- target이 사정거리 안에 들어왔는지 검증
- 실제 Damage 적용은 별도 Combat Module 통합 후 활성화

## 20.3 StateTree 사용 여부

StateTree를 사용할 경우 다음 원칙을 지킨다.

```text
신경망: 어떤 Skill을 실행할지 선택
StateTree: 선택된 Skill의 내부 단계 실행
```

예:

```text
Investigate StateTree
  ├─ MoveTo Target Location
  ├─ TurnTo Location
  ├─ Wait/Search
  └─ Complete
```

StateTree 안에서 “소리가 뒤에 있고 관계가 낮으면 Warn” 같은 상황별 선택 로직을 작성하지 않는다.

StateTree 없이 C++ Skill FSM으로 시작해도 된다. MVP에는 C++ Skill Executor가 더 단순하며, 복합 Skill이 늘어날 때 StateTree로 전환하는 것을 권장한다.

---

# 21. Manny Animation 통합

## 21.1 기존 locomotion 유지

Manny NPC는 `SKM_Manny`와 `ABP_Manny`를 사용한다.

- 걷기·달리기·정지 locomotion은 기존 Animation Blueprint 사용
- CharacterMovement 속도에 따라 기존 BlendSpace가 동작
- 기존 Foot IK 동작을 유지
- NPC AI 때문에 locomotion AnimGraph 전체를 복제하지 않는다.

## 21.2 행동 Animation 추가

다음 Montage를 별도 Slot으로 재생한다.

- Greet
- Warn
- CallForHelp
- Attack placeholder
- Hit reaction

필요한 경우 `ABP_Manny_AINative`를 만들되, `ABP_Manny`를 부모 또는 linked layer 방식으로 재사용하고 변경 범위를 최소화한다.

## 21.3 Turn/Look 개선 단계

### V1

- Capsule/Actor Yaw 회전
- locomotion이 회전을 따라감

### V1.5

- Turn-in-place Animation
- Aim Offset
- Head/Spine LookAt
- 몸과 머리 회전 속도 분리

### V2

- 감정 기반 pose additive
- 경계 자세, 공포 자세, 공격 자세
- 모델이 직접 pose를 출력하지 않고 감정/stance parameter만 전달

---

# 22. 모델 선택에서 행동 실행까지의 실제 흐름

## 22.1 시나리오 A: Quinn이 소리 없이 Manny 정면으로 접근

### 1단계 — Sight 획득

- Quinn은 Sight Stimuli Source로 등록되어 있음
- Quinn이 Sight Radius와 Peripheral Vision 안으로 진입
- AI Sight가 `Successfully Sensed = true`인 Stimulus 보고
- Spatial Memory가 `PositionSource = SightCurrent`로 설정

### 2단계 — 위치·시야 Observation

```text
Player visible_now = 1
Player position_source = SightCurrent
Player relative_x = 0.42
Player relative_y = 0.08
Player distance = 0.43
Player closing_speed = 0.35
Player time_since_seen = 0
Player visible_duration = 0.2
Sound heard = 0
Current skill = Idle
Relationship trust = 0.6
```

### 3단계 — 후보와 추론

```text
LookAt(Player)
TurnTo(Player)
Greet(Player)
Warn(Player)
KeepDistance(Player)
ContinueCurrentAction(None)
```

발소리가 없어도 위치와 Sight Feature만으로 적절한 반응이 선택되어야 한다.

---

## 22.2 시나리오 B: Quinn이 Manny 뒤에서 걸어옴

### 1단계 — 플레이어 소리 발생

- Quinn의 walk animation에 발소리 Notify 발생
- `ReportNoiseEvent` 호출
- 소리 위치, loudness, Instigator, tag가 Hearing 시스템에 전달됨

### 2단계 — Hearing 위치 기록

- Manny는 소리 발생 위치를 받음
- Quinn이 보이지 않으므로 Quinn의 실시간 Actor 위치는 모델에 전달하지 않음
- 위치 출처는 `HearingEvent`

### 3단계 — Observation 생성

```text
Player visible_now = 0
Sound position_source = HearingEvent
Sound bearing = Manny 뒤쪽
Sound loudness = 0.55
Sound age = 0.1
Sound position_confidence = 0.75
Current skill = Idle
Personality curiosity = 0.7
```

### 4단계 — Candidate 생성

```text
ContinueCurrentAction(None)
LookAt(SoundEvent_0)
TurnTo(SoundEvent_0)
Investigate(SoundEvent_0)
CallForHelp(None)
Idle(None)
```

후보 생성기는 “뒤쪽 소리”라는 이유로 `TurnTo` 점수를 올리지 않는다.

### 5단계 — NNE 추론과 Skill 실행

예시:

```text
ContinueCurrentAction  0.12
LookAtSound            0.71
TurnToSound            0.91
InvestigateSound       0.63
CallForHelp            0.05
Idle                   0.08
```

Manny가 회전한 뒤 Quinn이 Sight에 들어오면 Actor Entity가 `SightCurrent`로 갱신되고 후속 결정을 수행한다.

---

## 22.3 시나리오 C: Quinn이 벽 뒤로 숨음

### 1단계 — Sight Lost

- Quinn이 벽 뒤로 이동
- AI Sight가 감지 실패 상태 변경을 보고
- 마지막 목격 위치를 저장
- `PositionSource = LastSeenMemory`

### 2단계 — 숨은 위치 차단

```text
visible_now = 0
last_seen_age = 0.3
position_confidence = 0.92
perceived_position = last_seen_location
ground_truth_hidden_position = 모델 입력에 없음
```

Quinn이 벽 뒤에서 계속 이동하더라도 `perceived_position`은 자동으로 따라가지 않는다.

### 3단계 — 후보

```text
LookAt(LastSeenLocation)
TurnTo(LastSeenLocation)
Approach(LastSeenLocation)
Investigate(LastSeenLocation)
SearchArea(LastSeenLocation)
ContinueCurrentAction(None)
```

관계, 역할, 현재 임무와 기억 age에 따라 모델이 적절한 후보를 고른다.

### 4단계 — 기억 만료

- age 증가
- confidence 감소
- TTL 만료
- Entity 제거 또는 `entity_mask = 0`
- 이후 Quinn이 다시 보이거나 들릴 때까지 NPC가 숨은 현재 위치를 알 수 없음

---

## 22.4 시나리오 D: 보이는 Quinn이 빠르게 접근

- 현재 Sight 성공
- 상대 거리 감소
- closing speed 양수
- 개인 공간 경계 진입
- `KeepDistance`, `Warn`, `RetreatFrom`, `Attack`, `ContinueCurrentAction` 후보 생성
- 어떤 행동이 적절한지는 관계, 성격, 역할, 무기 상태와 함께 모델이 평가

이 전체 흐름에서 위치와 시야는 소리의 보조 정보가 아니라 독립된 입력이며, “현재 보임”, “소리만 들림”, “마지막 위치만 기억함”을 모델이 구분한다.

# 23. Debug UI와 로그

## 23.1 화면 Debug

`WBP_NPCDecisionInspector`에 다음을 표시한다.

- 선택된 NPC 이름/Profile
- 모델 ID와 버전
- 현재 Skill과 Target
- 현재 감정과 관계
- 최근 Sight/Hearing Event
- 현재 위치 출처(Sight/Hearing/LastSeen/Invalid)
- perceived position, last seen position, last heard position
- position age와 confidence
- relative distance, bearing, closing speed
- Entity 8개 슬롯
- Candidate 최대 32개
- raw score
- switch cost
- final score
- mask 여부와 사유
- inference latency
- request ID/epoch
- low-confidence 여부

## 23.2 World Debug Drawing

- Sight cone, Sight Radius, Lose Sight Radius 표시
- 현재 Sight target: 실선
- Last Seen Location: 점선과 age/confidence
- Sound Event: 위치 sphere와 TTL
- Editor 전용 Ground Truth와 Perceived Position을 서로 다른 marker로 표시
- 선택 Target: 강조 표시
- Nav target: marker
- 현재 Skill: 머리 위 text
- Model disabled/fallback 상태 표시

AI Perception 자체 디버깅과 커스텀 Decision Inspector를 함께 사용한다.

## 23.3 결정 로그

JSONL 또는 Unreal Trace event로 저장한다.

```json
{
  "time": 102.41,
  "npc_id": "guard_013",
  "profile_id": "guard_cautious",
  "model_version": "0.4.0",
  "request_id": 8812,
  "trigger": "ImportantSound",
  "selected_skill": "TurnTo",
  "selected_target": "sound_f204",
  "raw_score": 0.91,
  "final_score": 0.81,
  "inference_ms": 0.42,
  "fallback_used": false
}
```

## 23.4 이상 행동 캡처

QA Debug Command:

```text
npc.ReportBadDecision
```

저장 대상:

- 최근 10~30초 Observation
- 후보와 score
- hidden state
- NPC transform
- target transform
- random seed
- 모델/계약 version
- 기대 행동 입력
- screenshot 또는 replay reference

---

# 24. 성능과 안정성 요구사항

## 24.1 초기 성능 목표

| 항목 | MVP 목표 |
|---|---:|
| 모델 크기 | 10MB 이하 권장 |
| 활성 NPC | 30명 |
| 일반 판단 빈도 | 2~5Hz |
| Candidate | 최대 32개 |
| Entity | 최대 8개 |
| 단일 inference 평균 | 목표 2ms 이하 |
| Game Thread inference | 금지 |
| 모델 load 실패 시 crash | 0건 |
| 하드 제약 위반 | 0건 |

목표 수치는 기준이며 실제 하드웨어 profiling 후 조정한다.

## 24.2 메모리

NPC별:

- Hidden State 128 float ≈ 512 bytes
- Perception Cache
- Candidate snapshot
- 최근 결정 로그 ring buffer

공유:

- NNE Model/weights
- Model Instance Pool
- Schema/Normalization
- Skill Definition

## 24.3 모델 비활성화 조건

- manifest mismatch
- Tensor shape mismatch
- runtime 탐색 실패
- Model Data load 실패
- NNE instance 생성 실패
- 반복 inference failure
- output NaN/Inf

비활성화 시 NPC는 최소 안전 정책으로 전환한다.

## 24.4 최소 안전 정책

완성된 Behavior Tree가 아니라 시스템 유지용이다.

```text
현재 Skill이 안전하게 계속 가능 → Continue
그렇지 않음 → Idle
피격 + 이동 가능 + 공격 불가 → 짧은 거리 회피 또는 Flee fallback
모든 후보 무효 → Idle
```

---

# 25. 멀티플레이 확장 계획

MVP는 Single Player지만, 멀티플레이 시 다음 원칙을 사용한다.

- 서버가 Observation, 모델 추론, Skill 선택의 권한을 가짐
- 클라이언트는 선택된 Skill과 movement/animation state를 replication으로 수신
- 각 클라이언트가 동일 모델을 별도 실행하지 않음
- 관계와 명시적 기억은 서버 저장
- 모델 버전은 서버 기준
- 디버그 score는 개발 빌드에서만 선택적으로 replication

---

# 26. 테스트 계획

## 26.1 계약 테스트

- JSON schema validation
- Skill Registry ID uniqueness
- normalization vector length
- manifest와 ONNX input/output name 일치
- Python/C++ generated constant hash 일치

## 26.2 Feature Golden Test

같은 원시 Observation에 대해:

```text
Python Encoder Tensor == Unreal Encoder Tensor
```

최소 100개 Golden Sample을 유지한다.

## 26.3 Candidate Generator 테스트

- Actor target이 없는 경우 Actor Skill 생성 안 됨
- 무기 없는 경우 Attack mask
- 퀘스트 금지 시 Attack mask
- Sound Event에는 Investigate 가능
- Candidate 최대 32개 보장
- Padding 후보 mask 0
- 동일 candidate 중복 제거

## 26.4 NNE 테스트

- Model load
- Runtime lookup
- Input shape 설정
- FP32 output parity
- worker thread 실행
- World 종료 중 job 완료
- Actor 파괴 후 stale result 폐기
- instance pool 동시성
- packaged build model load

## 26.5 Skill 테스트

- TurnTo 목표 각도 도달
- MoveTo path success/failure
- Investigate 복합 단계
- target 소실 처리
- Skill cancel
- 최소 지속 시간
- 긴급 인터럽트

## 26.6 필수 Gameplay 시나리오

### 시야·위치 단독

1. Quinn이 Manny 정면에 정지하고 소리를 내지 않음
2. Quinn이 Manny 정면에서 천천히 접근
3. Quinn이 Manny 정면에서 빠르게 접근
4. Quinn이 Sight Radius 경계 안/밖으로 이동
5. Quinn이 Peripheral Vision 경계를 횡단
6. Quinn이 Manny 뒤에 조용히 서 있으며 Sight/Hearing 모두 없음
7. Quinn이 벽 뒤에 조용히 있으며 이전 감지 이력도 없음
8. Quinn이 기둥 뒤로 숨었다 다시 나타남
9. Quinn의 일부만 보이는 optional exposure 테스트
10. Manny 자체가 회전하여 같은 Quinn을 다시 감지

### 소리와 센서 융합

11. Quinn이 Manny 뒤에서 걷기
12. Quinn이 Manny 뒤에서 달리기
13. Quinn이 벽 뒤에서 발소리 발생
14. 소리만 있고 Actor 없음
15. 소리 위치와 실제 Instigator 위치가 다름
16. Quinn을 보는 동안 발소리도 발생
17. Sight Lost 직후 다른 위치에서 소리 발생

### 위치 기억과 누출 방지

18. Quinn을 본 뒤 벽 뒤로 숨음
19. Quinn이 숨은 상태에서 계속 이동하지만 LastSeen 위치는 고정
20. LastSeen TTL 만료
21. LastSeen confidence 감소
22. 숨은 Quinn Ground Truth만 변경했을 때 입력 Tensor 불변
23. 전체 장면을 Yaw 회전했을 때 로컬 Feature와 정책 결과 동등
24. Entity position source가 Sight→LastSeen→Invalid로 전환
25. Sound Event position이 Instigator를 따라 이동하지 않음

### 행동·시스템

26. 우호 관계에서 접근
27. 적대 관계에서 접근
28. 겁이 많은 Manny Profile
29. 용감한 Manny Profile
30. 현재 Investigate 중 새 폭발 발생
31. target이 이동 불가능한 위치에 있음
32. NavMesh가 없는 위치
33. 모델 파일 누락
34. 잘못된 manifest
35. 모든 후보 mask
36. 30 NPC 동시 판단

## 26.7 회귀 지표

- 금지 행동 선택률
- 행동 진동 횟수/분
- 평균 반응 시간
- top-1/top-3 교사 일치율
- 소리 조사 완료율
- Sight 획득 반응률
- Sight Lost 후 LastSeen 위치 사용률
- 숨은 현재 위치 누출 건수(목표 0)
- 위치 출처 전환 정확도
- 거리·방향 Feature parity
- target switch 빈도
- fallback 비율
- inference p50/p95/p99
- Game Thread frame time 영향

---

## 26.8 공간·시야 전용 자동화 테스트

### Local Coordinate Golden Test

같은 상대 배치를 월드 원점과 먼 좌표에서 각각 생성해도 Tensor가 같아야 한다.

### Rotation Invariance Test

Manny, Quinn, 벽, 소리 위치를 함께 90도 회전했을 때 로컬 Feature가 동일해야 한다.

### Hidden Position Leakage Test

Sight가 끊긴 뒤 Quinn의 Ground Truth 위치만 변경한다. LastSeen TTL 동안 Unreal Encoder 출력이 변하지 않아야 한다.

### Sight/Hearing Source Transition Test

```text
Invalid → HearingEvent → SightCurrent → LastSeenMemory → Invalid
```

각 상태에서 source one-hot, position age, confidence, mask가 계약과 일치해야 한다.

### Python–Unreal Parity

동일한 Perception Snapshot에 대해 다음 값이 tolerance 내 일치해야 한다.

- local relative XYZ
- distance/log distance
- bearing/elevation sin/cos
- estimated velocity
- closing speed
- position source
- position age/confidence
- sight/hearing flags

---

# 27. 단계별 구현 마일스톤

## Phase 0 — UE 프로젝트와 Manny 수직 슬라이스 기반

### 구현

- UE 5.7 Third Person C++ Variant None 생성
- Quinn 플레이 확인
- Manny NPC Character/AIController 생성
- `SKM_Manny`, `ABP_Manny` 적용
- NavMesh와 MoveTo 테스트
- AI Sight/Hearing 연결
- Quinn Sight Stimuli Source 등록
- Quinn 발소리 notify 연결
- Spatial Memory와 위치 출처 상태 머신 구현
- Sight Current / Last Seen / Hearing Location 디버그 표시

### 산출물

- `L_AINativeNPC_MVP`
- `BP_AINativeNPC_Manny`
- `DA_NPCProfile_Guard_Cautious`
- Perception debug UI

### 완료 조건

- Manny가 현재 보이는 Quinn의 위치·거리·방향을 Perception Cache에 기록
- Sight Lost 후 마지막 목격 위치를 고정 저장
- 발소리 위치를 별도 Hearing Event로 기록
- 아직 행동 선호 판단 로직은 없음
- Manny가 명령받은 location으로 이동·회전 가능

---

## Phase 1 — Candidate와 Skill 실행기

### 구현

- Skill Registry
- Candidate Generator
- Action Mask
- Skill Executor
- Decision Inspector
- Mock Scorer

Mock Scorer는 통합 테스트용이며, 최종 행동 정책이 아니다.

가능한 Mock:

- Editor UI에서 candidate 직접 선택
- 후보 index를 고정 반환
- random valid candidate 선택

### 완료 조건

- Inspector에서 후보를 선택하면 Manny가 Skill 실행
- TurnTo, Approach, Investigate, Greet, Warn 동작
- 상황별 조건문 없이 candidate/skill pipeline 완성

---

## Phase 2 — NNE Hello Model 통합

### 구현

- 매우 작은 ONNX Candidate Scorer 생성
- NNE + `NNERuntimeORTCpu` 모델 로드
- fixed shape 설정
- worker thread inference
- Python/UE output parity
- 모델 실패 fallback

### 완료 조건

- Mock Scorer를 ONNX 모델로 교체
- UE에서 1회 inference 결과가 Python과 tolerance 내 일치
- packaged Development build에서도 모델 로드

---

## Phase 3 — 실제 Observation Model V0

### 구현

- global state 96
- entity 8×56
- candidate 32×56
- Spatial/Sight/Hearing 분기 Entity Encoder + Candidate Scorer
- 단일 프레임 LLM/사람 Ranking 데이터
- 계약 코드 생성

### 완료 조건

- 시야·위치·소리 기본 시나리오에서 적절한 top-3 행동
- 소리 없는 정면 접근 → LookAt/Greet/Warn/KeepDistance 계열 일반화
- 뒤쪽 발소리 → TurnTo/LookAt/Investigate 계열 일반화
- Sight Lost → LastSeenLocation 조사 계열 일반화
- 숨은 Quinn의 실시간 좌표 누출 0건
- Profile/관계 변화에 따라 행동 score 변화

---

## Phase 4 — GRU와 시퀀스

### 구현

- hidden 128
- episode/trajectory 로그
- sequence training
- hidden reset/save 정책
- stale inference hidden 처리

### 완료 조건

- 경고 직후 즉시 평상시로 돌아가지 않음
- 최근 소리와 최근 행동을 몇 step 동안 기억
- 행동 진동 감소

---

## Phase 5 — 데이터 제작 도구와 Active Learning

### 구현

- UE Scenario Runner
- JSONL 캡처
- LLM teacher batch tool
- 사람 선호 비교 UI
- low-confidence sample 수집
- bad decision report

### 완료 조건

- 이상 행동이 자동으로 재학습 큐에 편입
- 전체 샘플이 아니라 경계 사례 중심으로 검수 가능
- 데이터와 모델 version 추적 가능

---

## Phase 6 — 애니메이션·대사·품질

### 구현

- Turn-in-place
- Aim Offset/LookAt
- Greet/Warn Montage
- Dialogue Act 연동
- 감정 stance
- Skill transition polish

### 완료 조건

- 모델의 행동 선택과 Manny 시각 표현이 자연스럽게 연결
- 이동/회전/대사 중 애니메이션 pop 최소화

---

## Phase 7 — 성능·패키징·운영

### 구현

- Batch inference
- instance pool tuning
- NNE runtime thread 설정 profiling
- FP16/INT8 검토
- Shipping cook 검증
- 모델 롤백
- telemetry dashboard

### 완료 조건

- 목표 플랫폼 frame budget 충족
- 30 NPC stress test 통과
- 모델 교체와 롤백 가능
- 계약 mismatch 시 안전하게 실행 거부

---

# 28. 최초 Vertical Slice 작업 순서

1. UE 5.7 Third Person C++ Variant `None` 프로젝트 생성
2. Quinn Player가 기본 이동·점프하는지 확인
3. Manny NPC Character와 AIController 생성
4. `SKM_Manny`, `ABP_Manny` 적용
5. NavMesh와 MoveTo/TurnTo 수동 명령 테스트
6. `UAIPerceptionComponent`에 Sight와 Hearing 설정
7. Quinn에 `UAIPerceptionStimuliSourceComponent`를 추가해 Sight Source 등록
8. Sight Acquired / Sight Lost 로그와 디버그 선 표시
9. `UNPCSpatialMemoryComponent` 구현
10. `SightCurrent`, `LastSeenMemory`, `HearingEvent`, `Invalid` 상태 전환 구현
11. Quinn 발소리 `ReportNoiseEvent` 연결
12. Sound Event를 화면에 표시
13. Manny 로컬 상대 위치·거리·bearing 계산
14. 숨은 Actor의 실시간 위치를 읽지 않는 assertion 작성
15. Observation Snapshot과 Tensor Encoder 구현
16. Python–Unreal Local Coordinate Golden Test 작성
17. Skill Registry와 Candidate Generator 구현
18. Inspector에서 후보를 직접 선택하는 Mock Scorer 구현
19. LookAt / TurnTo / Approach / KeepDistance / Investigate 실행
20. 소리 없는 정면 접근 시나리오 실행
21. 뒤쪽 발소리→회전→Sight 획득 시나리오 실행
22. Sight Lost→LastSeen 위치 조사 시나리오 실행
23. Hidden Position Leakage Test 통과
24. NNE Hello Model 연결
25. Python과 Unreal ONNX 출력 parity 확인
26. 실제 Spatial/Sight/Hearing Action Scorer로 교체

가장 중요한 Gate는 18번 이전이다. **모델 없이도 Perception→Spatial Memory→Observation→Candidate→Skill 실행 파이프라인이 동작해야 한다.** 그 다음 NNE를 연결해야 문제의 원인이 센서·좌표 변환·클라이언트인지 모델인지 구분할 수 있다.

# 29. 파일 단위 구현 목록

## Runtime Public

```text
Public/
├─ AINativeNPCCharacter.h
├─ AINativeNPCController.h
├─ AINativeNPCSettings.h
├─ Data/NPCPolicyDataAsset.h
├─ Data/NPCProfileDataAsset.h
├─ Data/NPCSkillDefinitionDataAsset.h
├─ Decision/NPCDecisionComponent.h
├─ Decision/NPCCandidateGeneratorComponent.h
├─ Inference/NPCInferenceWorldSubsystem.h
├─ Inference/NPCModelContract.h
├─ Perception/NPCPerceptionMemoryComponent.h
├─ Perception/PlayerNoiseEmitterComponent.h
├─ Memory/NPCExplicitMemoryComponent.h
├─ Relationship/NPCRelationshipComponent.h
├─ Skills/NPCSkillExecutorComponent.h
├─ Skills/NPCSkill.h
├─ Debug/NPCDebugComponent.h
└─ Types/NPCDecisionTypes.h
```

## Runtime Private

각 header에 대응하는 `.cpp`와 다음 구현을 둔다.

```text
Private/Inference/NPCNNEModelInstancePool.cpp
Private/Inference/NPCInferenceJob.cpp
Private/Perception/NPCSpatialMemoryComponent.cpp
Private/Perception/NPCVisibilityProbeComponent.cpp
Private/Decision/NPCObservationEncoder.cpp
Private/Decision/NPCDecisionStabilizer.cpp
Private/Skills/NPCSkill_TurnTo.cpp
Private/Skills/NPCSkill_Approach.cpp
Private/Skills/NPCSkill_Investigate.cpp
Private/Skills/NPCSkill_Greet.cpp
Private/Skills/NPCSkill_Warn.cpp
Private/Animation/AnimNotify_ReportAINoise.cpp
```

## Editor

```text
AINativeNPCEditor/
├─ NPCDecisionInspectorTab.cpp
├─ NPCScenarioRunner.cpp
├─ NPCObservationExportCommandlet.cpp
├─ NPCPolicyValidationCommandlet.cpp
└─ NPCProfileAssetActions.cpp
```

---

# 30. 팀별 작업 분리

## ML 엔지니어

- 계약 parser 및 generated Python code
- Dataset converter
- Action Scorer
- Ranking loss
- sequence training
- ONNX export
- parity report
- model card

## Unreal 게임플레이 프로그래머

- Manny Character/AIController
- Perception
- Observation Builder
- Candidate Generator
- Skill Executor
- Navigation
- 안정화

## Unreal 시스템/엔진 프로그래머

- NNE subsystem
- instance pool
- async job
- memory lifetime
- packaging
- performance profiling

## 테크니컬 디자이너

- NPC Profile
- Skill Definition
- Scenario Runner
- 테스트 맵
- Animation Notify
- Debug Inspector

## AI/내러티브 디자이너

- 캐릭터 원칙
- 행동 선호 평가
- LLM teacher prompt
- 사람 선호 데이터
- 관계/감정 설계

## QA

- Golden Scenario
- bad decision capture
- 패키지 테스트
- 행동 진동
- 모델 회귀

---

# 31. Definition of Done

## 31.1 클라이언트 DoD

- Quinn이 Third Person 입력으로 정상 조작됨
- Manny가 AIController에 의해 possession됨
- Sight/Hearing stimulus가 정상 기록됨
- 소리 없이 보이는 Quinn의 위치·거리·방향이 Tensor에 반영됨
- Sight Lost 후 LastSeen 위치가 고정되고 confidence가 감쇠함
- 보이지도 들리지도 않는 Quinn의 실시간 위치가 모델 입력에 포함되지 않음
- Candidate가 최대 32개로 안정적으로 생성됨
- Action Mask가 하드 제약을 100% 차단함
- NNE 추론이 Game Thread를 장시간 block하지 않음
- stale 결과가 적용되지 않음
- Manny가 최소 8개 Skill을 실행 가능
- 모델 실패 시 crash 없이 fallback
- Development 패키지에서 모델 실행

## 31.2 모델 DoD

- manifest와 ONNX 계약 일치
- Python/Unreal Feature Golden Test 통과
- Python ONNX/UE NNE parity 통과
- 기본 시나리오 top-3 품질 기준 통과
- NaN/Inf 0건
- mask 위반 0건
- model card와 dataset version 기록

## 31.3 AI Native 목표 DoD

다음 상황을 전용 조건문 없이 수행해야 한다.

- 소리 없는 정면 접근을 시야로 인식하고 반응
- 뒤쪽 소리를 듣고 확인
- 시야를 잃은 뒤 마지막 목격 위치를 조사
- 플레이어를 본 뒤 관계에 따라 다른 반응
- 경고 직후 맥락 유지
- 성격이 다른 NPC가 같은 상황에서 다른 행동 분포를 보임
- 새 NPC Profile을 코드 수정 없이 추가

---

# 32. 주요 위험과 대응

## 위험 1 — Candidate Generator가 새로운 Behavior Tree가 됨

대응:

- Candidate Generator에는 호환성과 실행 가능성만 둔다.
- 점수, 우선순위, 상황별 threshold 금지
- 코드 리뷰 체크리스트에 “행동 선호 조건인가?” 포함

## 위험 2 — Python과 Unreal Feature가 다름

대응:

- 계약 파일 단일 원본
- code generation
- Golden Sample
- model manifest hash

## 위험 3 — NNE API/성능 변화

대응:

- NNE wrapper를 subsystem 내부에 격리
- 게임 코드는 NNE 타입을 직접 참조하지 않음
- runtime adapter interface 제공
- 패키지별 smoke test
- 필요 시 직접 ONNX Runtime adapter로 교체 가능하게 설계

## 위험 4 — 비동기 메모리 lifetime 오류

대응:

- Job이 input/output buffer 소유
- UObject pointer를 worker에 전달하지 않음
- Instance당 단일 job
- World teardown token
- Thread Sanitizer에 준하는 stress test

## 위험 5 — 행동은 맞지만 시각적으로 어색함

대응:

- 의사결정 품질과 animation 품질 지표 분리
- V1 actor rotation 후 Aim Offset/turn-in-place 단계적 도입
- Skill transition montage와 최소 지속 시간

## 위험 6 — 학습 데이터 비용 증가

대응:

- UE Scenario Runner
- LLM Ranking
- Active Learning
- low-confidence와 실제 이상 행동 중심 검수

---

## 위험 7 — Ground Truth 위치가 모델에 누출됨

증상:

- 벽 뒤 플레이어를 정확히 추적
- 소리가 없는데 뒤쪽 플레이어를 바라봄
- LastSeen 위치가 숨은 Actor를 따라 이동

대응:

- `PerceivedWorldLocation`과 Ground Truth Transform 데이터 구조 분리
- Sight가 false인 Actor에 대한 `GetActorLocation()` 사용 금지
- Hidden Position Leakage Test
- Editor Assertion과 로그
- 데이터셋에서 ground truth 필드를 Feature Builder에 전달하지 않음

## 위험 8 — 시야 이벤트가 너무 자주 추론을 발생시킴

대응:

- 거리·각도 변화 임계값
- Request coalescing
- 보이는 target의 위치 갱신 빈도 제한
- 중요 NPC와 비가시 NPC의 판단 주기 분리
- Skill 실행은 매 프레임, 정책 판단은 저주기로 분리

---

# 33. v0.3 변경 요약

- Hearing-only 인상을 제거하고 Sight와 상대 위치를 MVP 필수 범위로 승격
- 시야 단독, 소리→시야 전환, 시야 상실 후 LastSeen 기억의 세 수직 슬라이스 정의
- Ground Truth 위치와 Perceived Position 분리
- `ENPCPositionSource`와 `UNPCSpatialMemoryComponent` 추가
- Entity Tensor를 40차원에서 56차원으로 확장
- Candidate Tensor를 48차원에서 56차원으로 확장
- 로컬 좌표, 감지 기반 속도, closing speed, position age/confidence 추가
- Hidden Position Leakage Test와 Rotation Invariance Test 추가
- 시야·위치·소리 데이터 생성 및 학습 요구사항 추가

---

# 34. 공식 참고 문서

- [Third Person Template — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/third-person-template-in-unreal-engine?application_version=5.7)
- [Neural Network Engine — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-in-unreal-engine?application_version=5.7)
- [Neural Network Engine Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-overview-in-unreal-engine?application_version=5.7)
- [AI Perception in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine?application_version=5.7)
- [StateTree in Unreal Engine — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/state-tree-in-unreal-engine?application_version=5.7)
- [Navigation System in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/navigation-system-in-unreal-engine?application_version=5.7)
- [Animation Blueprints in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprints-in-unreal-engine?application_version=5.7)

---

# 35. 최종 권장 구조

```text
[Offline ML]
UE/절차적 상황
→ 후보 행동 Ranking 데이터
→ Neural Action Scorer 학습
→ ONNX + Manifest

[Model Contract]
Feature Schema
+ Skill Registry
+ Normalization
+ Tensor Shapes
+ Version Hash

[UE 5.7 Client]
Quinn 위치·움직임·발소리
→ Manny AI Sight/Hearing
→ Spatial Memory(SightCurrent/LastSeen/Hearing)
→ Observation Builder
→ Candidate Generator
→ NNE Async Inference
→ Decision Stabilizer
→ Skill Executor
→ Manny Movement/Animation
→ Decision Log
```

본 설계에서 신경망 프로젝트와 Unreal 클라이언트는 명확히 분리되지만, **모델 계약과 Golden Test**를 통해 하나의 제품으로 연결된다. Unreal 클라이언트는 감각과 실행 능력을 제공하고, 신경망은 상황별 행동 선호를 담당한다. 이 경계를 유지하는 것이 전통적인 대규모 조건문/Behavior Tree로 되돌아가지 않으면서도, 실제 게임에서 안정적으로 동작하는 AI Native NPC를 만드는 핵심이다.
