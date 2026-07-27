# AI Native NPC — Unreal Engine 5.7 / Manny·Quinn 구현 계획서
## 신경망 학습 시스템과 Unreal 클라이언트 분리 설계

- 문서 버전: v0.2
- 기준 엔진: Unreal Engine 5.7
- 기준 프로젝트: Games → Third Person → C++ → Variant `None`
- 기준 캐릭터: 플레이어 `Quinn`, NPC `Manny`
- 기준 추론 방식: 로컬 CPU 추론, Unreal Neural Network Engine(NNE) + `NNERuntimeORT`
- 상위 문서: `ai_native_npc_requirements_implementation_plan.md`
- 문서 목적: 기존 요구사항을 실제 제작 가능한 두 프로젝트, 즉 **오프라인 신경망 학습 시스템**과 **Unreal Engine 런타임 클라이언트**로 분리하고, 두 시스템 사이의 데이터 계약과 단계별 통합 계획을 정의한다.

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
   - 감각 수집, 후보 행동 생성, NNE 추론 요청, 행동 안정화, Manny 애니메이션 및 이동 실행을 담당한다.
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
│ AI Perception → Observation → Candidate → NNE → Skill 실행  │
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

MVP에서는 다음 수직 슬라이스를 완성한다.

```text
Quinn이 Manny의 뒤쪽으로 이동
→ Quinn 발소리가 Hearing Stimulus로 보고됨
→ Manny가 소리 이벤트를 Observation에 기록
→ Candidate Generator가 가능한 행동 후보 생성
→ 신경망이 TurnTo(SoundLocation)를 높은 점수로 평가
→ Manny가 뒤를 돌아봄
→ AI Sight가 Quinn을 인식
→ 관계와 성격에 따라 Greet / Warn / KeepDistance 중 하나 선택
```

이 흐름에는 다음과 같은 직접적인 상황 규칙을 넣지 않는다.

```cpp
// 구현하지 않을 코드
if (PlayerIsBehind && HeardFootstep)
{
    TurnToPlayer();
}
```

대신 다음 공통 기능만 구현한다.

- 소리 이벤트를 감지한다.
- 소리 위치를 행동 대상 후보로 만든다.
- `TurnTo` Skill은 주어진 위치를 향해 회전할 수 있다.
- 모델이 상황과 후보 행동을 평가한다.

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
| `entities` | `[B, 8, 40]` | float32 | 플레이어, 다른 NPC, 소리 위치 등 주변 개체 |
| `entity_mask` | `[B, 8]` | float32 | 유효 개체는 1, Padding은 0 |
| `candidates` | `[B, 32, 48]` | float32 | Skill, 대상 슬롯, 행동 메타데이터, pair feature |
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

| 그룹 | 차원 | 예시 |
|---|---:|---|
| 자기 상태 | 24 | 체력, 속도, 피격, 무기, 현재 행동 시간, 자원 |
| 성격 | 10 | 공격성, 용기, 호기심, 인내심 등 |
| 감정 | 8 | 공포, 분노, 의심, 긴장 등 |
| 플레이어 관계 | 8 | 호감, 신뢰, 존중, 두려움 등 |
| 역할 one-hot | 8 | Guard, Civilian, Companion 등 |
| 현재 Skill one-hot | 16 | MVP Skill Registry |
| 최근 Skill 결과 | 6 | 성공, 실패, 취소, 진행 중 등 |
| 월드 Context | 8 | 안전 구역, 제한 구역, 아군/적군 수 등 |
| Reserved | 8 | schema 호환용 예약 공간 |
| 합계 | 96 |  |

## 5.4 `entities` 초기 구성

각 Entity는 actor뿐 아니라 sound/location 같은 비Actor 관심점도 표현한다.

| 그룹 | 차원 | 예시 |
|---|---:|---|
| Entity type one-hot | 8 | Player, NPC, Sound, Cover, Exit, Object 등 |
| 상대 공간 정보 | 10 | 거리, log 거리, 상대 XYZ, 방향 sin/cos, 접근 속도 |
| 지각 정보 | 8 | visible, heard, age, strength, confidence, occlusion |
| 위협·상태 | 8 | 무기, 공격 중, 체력 추정, threat, interactable |
| 관계 | 6 | 호감, 신뢰, 공포, 적대, 빚, 의심 |
| 합계 | 40 |  |

## 5.5 `candidates` 초기 구성

| 그룹 | 차원 | 설명 |
|---|---:|---|
| Skill one-hot | 16 | Skill Registry의 고정 16개 슬롯 |
| Target slot one-hot | 9 | Entity 8개 + NoTarget |
| Target type | 7 | Actor, Sound, Location, Cover 등 |
| Pair feature | 8 | 현재 Skill과 동일, 이동 거리, 예상 비용 등 |
| 기본 파라미터·제약 | 8 | 기본 지속 시간, 기본 속도, 위험, cooldown 등 |
| 합계 | 48 |  |

## 5.6 Mask 규칙

- `entity_mask == 0`인 Entity는 attention과 target aggregation에서 제외한다.
- `candidate_mask == 0`인 후보는 최종 점수를 매우 작은 값으로 만든다.
- Unreal 클라이언트도 모델 출력 이후 다시 Mask를 검증한다.
- 모든 후보가 Mask된 경우 모델 결과를 사용하지 않고 `Idle` 또는 `ContinueCurrentAction` fallback을 실행한다.

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
  "model_id": "npc_policy_mvp",
  "model_version": "0.3.0",
  "schema_version": "1.0.0",
  "skill_registry_version": "1.0.0",
  "normalization_version": "1.0.0",
  "max_entities": 8,
  "max_candidates": 32,
  "hidden_size": 128,
  "inputs": {
    "global_state": [1, 96],
    "entities": [1, 8, 40],
    "entity_mask": [1, 8],
    "candidates": [1, 32, 48],
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
  "dataset_version": "ue_mvp_2026_01"
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

```text
global_state [B,96]
        │
        ▼
State MLP 96→128→128
        │
        ├──────────────────────────────┐
        │                              │
entities [B,8,40]                      │
        │                              │
Entity MLP 40→64→64                    │
        │                              │
Masked Attention Pool → 128            │
        │                              │
        └──────────────┬───────────────┘
                       ▼
                 Context 256
                       │
hidden_in [B,128] → GRU Cell 128
                       │
                       ▼
                 Memory 128
                       │
                       ├──────────────────────────────────────┐
                       │                                      │
candidates [B,32,48] → Candidate MLP 48→64                  │
Target slot one-hot × Entity Embeddings → Target Embedding 64│
                       │                                      │
                       └──────────── Candidate-wise concat ───┘
                                           │
                                    Score MLP 256→128→64→1
                                           │
                                  candidate_scores [B,32]
```

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
| `UNPCPerceptionMemoryComponent` | Controller/Pawn | Sight/Hearing stimulus를 구조화된 캐시로 변환 |
| `UNPCObservationComponent` | Pawn | 센서·상태·관계로 Observation 구성 |
| `UNPCRelationshipComponent` | Pawn | 대상별 관계 상태 저장 |
| `UNPCExplicitMemoryComponent` | Pawn | 구조화된 사건 기억 저장 |
| `UNPCCandidateGeneratorComponent` | Pawn | Skill×Target 후보와 Action Mask 생성 |
| `UNPCDecisionComponent` | Pawn | 판단 요청, hidden state, stale result 관리 |
| `UNPCSkillExecutorComponent` | Pawn | 선택된 Skill 시작·Tick·취소 |
| `UNPCInferenceWorldSubsystem` | WorldSubsystem | 모델 로드, NNE Instance Pool, 비동기 추론 큐 |
| `UNPCDebugComponent` | Pawn | 현재 Observation, 후보 점수, 결정 로그 제공 |
| `UPlayerNoiseEmitterComponent` | Player | 발소리 등 Hearing stimulus 발생 |
| `UAnimNotify_ReportAINoise` | Animation | 발 접촉 시점에 소리 보고 |

## 12.2 Data Asset

| Asset Class | 예시 Asset | 책임 |
|---|---|---|
| `UNPCProfileDataAsset` | `DA_NPCProfile_Guard_Cautious` | 역할, 성격, 기본 관계, 감정 감쇠 |
| `UNPCPolicyDataAsset` | `DA_NPCPolicy_MVP` | `UNNEModelData`, manifest, runtime, tensor shape |
| `UNPCSkillRegistryDataAsset` | `DA_NPCSkillRegistry_V1` | Skill ID와 실행 클래스 매핑 |
| `UNPCSkillDefinitionDataAsset` | `DA_Skill_Investigate` | 지속 시간, target type, 파라미터 범위 |
| `UNPCSensorConfigDataAsset` | `DA_NPCSensor_Guard` | Sight/Hearing 설정 |

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
    SightChanged,
    ImportantSound,
    Damaged,
    RelationshipChanged,
    Emergency
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
    UPROPERTY() FVector LastKnownLocation = FVector::ZeroVector;
    UPROPERTY() float Distance = 0.0f;
    UPROPERTY() float LastSensedWorldTime = 0.0f;
    UPROPERTY() float StimulusStrength = 0.0f;
    UPROPERTY() float Confidence = 0.0f;
    UPROPERTY() bool bVisible = false;
    UPROPERTY() bool bHeard = false;
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

# 14. AI Perception 구현

## 14.1 Component 배치

`AAINativeNPCController`에 다음을 둔다.

- `UAIPerceptionComponent`
- `UAISenseConfig_Sight`
- `UAISenseConfig_Hearing`
- 선택: `UAISenseConfig_Damage`

AI Perception callback은 행동을 직접 실행하지 않는다. 오직 `UNPCPerceptionMemoryComponent`에 stimulus를 기록하고 판단 요청을 발생시킨다.

```cpp
void AAINativeNPCController::HandleTargetPerceptionUpdated(
    AActor* Actor,
    FAIStimulus Stimulus)
{
    PerceptionMemory->RecordStimulus(Actor, Stimulus);

    if (PerceptionMemory->IsDecisionRelevant(Stimulus))
    {
        DecisionComponent->RequestDecision(
            ENPCDecisionTrigger::SightChanged);
    }
}
```

`IsDecisionRelevant`는 행동 선호를 판단하지 않는다. 다음과 같은 scheduling 기준만 판정한다.

- 새로운 대상인가
- 성공 감지 상태가 변경되었는가
- 긴급도가 높은 감각 종류인가
- 직전 판단 이후 충분한 시간이 지났는가

## 14.2 Sight Feature

각 Actor에 대해 저장한다.

- 현재 감지 성공 여부
- 마지막 감지 위치
- stimulus age
- stimulus strength
- 마지막으로 보인 시간
- 보인 누적 시간
- 최근 시야 진입/이탈 횟수
- 상대 위치와 방향

## 14.3 Hearing Feature

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

## 14.4 Quinn 발소리

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
    const float Loudness = FootstepCurve->GetFloatValue(SpeedNormalized);

    UAISense_Hearing::ReportNoiseEvent(
        GetWorld(),
        Location,
        Loudness,
        GetOwner(),
        MaxFootstepRange,
        TEXT("Noise.Footstep"));
}
```

발소리의 크기는 움직임 속도, crouch, 착지, 표면 재질로 조정하되, “NPC가 어떤 반응을 해야 하는가”는 소음 발생 코드에 포함하지 않는다.

---

# 15. Observation Builder

## 15.1 실행 시점

Observation은 매 프레임 만들지 않는다.

- 정기 판단 tick
- 중요 stimulus 수신
- 현재 Skill 종료/실패
- 피해 발생
- 관계·퀘스트 상태 변경

## 15.2 처리 순서

```text
1. NPC 자기 상태 Snapshot
2. Profile에서 성격/역할 읽기
3. 감정/관계 읽기
4. Perception Cache에서 관심 Entity 선정
5. Explicit Memory에서 관련 기억 Top-K 선정
6. 현재 Skill 및 결과 기록
7. Feature Schema 순서로 float Tensor 생성
8. Normalization 적용
9. NaN/Inf 및 범위 검증
```

## 15.3 Entity 슬롯 선정

MVP 최대 8개 슬롯:

- Player 우선 1개
- 가장 최근/강한 Sight Actor 최대 3개
- 최근 Sound Event 최대 3개
- 중요 World Target 1개

동일 대상을 중복 슬롯에 넣지 않는다.

선정 기준은 모델 대신 런타임 성능을 위한 정보 보존 기준이다. “적대적이면 우선” 같은 행동 선호 규칙은 넣지 않고, 최신성·감각 강도·거리·명시적 중요 태그만 사용한다.

## 15.4 정규화

모든 feature는 계약의 `normalization.json`을 사용한다.

- 거리: max sensing range 기반 clamp 또는 log transform
- 시간: 최대 기억 시간으로 clamp
- 각도: sin/cos
- boolean: 0/1
- 성격·감정·관계: 계약 범위로 clamp

Unreal과 Python이 각각 임의의 상수를 사용하지 않는다.

---

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
| LookAt | Actor, SoundLocation, WorldLocation | target 유효 |
| TurnTo | Actor, SoundLocation, WorldLocation | 회전 가능 |
| Approach | Actor | Nav path 존재 가능성, 이동 가능 |
| KeepDistance | Actor | 이동 가능 |
| RetreatFrom | Actor | 이동 가능 |
| Investigate | SoundLocation, WorldLocation | Nav projection 성공 |
| Greet | Actor | 대화 가능, 대상 생존 |
| Warn | Actor | 대화 가능, mute 상태 아님 |
| CallForHelp | None/Actor | 호출 기능 사용 가능 |
| TakeCover | Cover | 유효 cover point 존재 |
| Flee | Exit/WorldLocation | 유효 flee point 존재 |
| Attack | Actor | 공격 능력 보유, 퀘스트 허용 |
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

## 22.1 시나리오: Quinn이 Manny 뒤에서 걸어옴

### 1단계 — 플레이어 소리 발생

- Quinn의 walk animation에 발소리 notify 발생
- `ReportNoiseEvent` 호출
- 위치, loudness, instigator, tag가 Hearing 시스템에 전달됨

### 2단계 — Manny의 AI Perception

- `AAINativeNPCController`의 Hearing sense가 stimulus 수신
- `UNPCPerceptionMemoryComponent`가 Sound Event 생성
- 행동을 직접 실행하지 않고 `RequestDecision(ImportantSound)` 호출

### 3단계 — Observation 생성

```text
Player visible = 0
Sound direction sin/cos = Manny 뒤쪽
Sound loudness = 0.55
Sound age = 0.1
Current skill = Idle
Personality curiosity = 0.7
Relationship trust = 0.1
```

### 4단계 — Candidate 생성

```text
0: ContinueCurrentAction(None)
1: LookAt(SoundEvent_0)
2: TurnTo(SoundEvent_0)
3: Investigate(SoundEvent_0)
4: CallForHelp(None)
5: Idle(None)
```

후보 생성기는 “뒤쪽 소리”라는 이유로 TurnTo를 우선하지 않는다. 후보만 만든다.

### 5단계 — NNE 추론

예시 출력:

```text
ContinueCurrentAction  0.12
LookAtSound            0.71
TurnToSound            0.91
InvestigateSound       0.63
CallForHelp            0.05
Idle                   0.08
```

### 6단계 — Skill 실행

- Stabilizer가 `TurnToSound` 선택
- `UNPCSkillExecutorComponent`가 sound location 방향으로 Manny를 회전
- 목표 각도 도달 시 Skill 성공

### 7단계 — Quinn 시야 인식

- 회전 후 AI Sight가 Quinn 감지
- 새 Observation과 후보 생성
- 신중한 Guard라면 `Warn`, 우호적인 Civilian이면 `Greet`, 겁이 많은 NPC라면 `KeepDistance` 또는 `CallForHelp`가 선택될 수 있음

이 전체 흐름에서 “뒤에서 발소리면 돌아본다”는 직접 조건문은 존재하지 않는다.

---

# 23. Debug UI와 로그

## 23.1 화면 Debug

`WBP_NPCDecisionInspector`에 다음을 표시한다.

- 선택된 NPC 이름/Profile
- 모델 ID와 버전
- 현재 Skill과 Target
- 현재 감정과 관계
- 최근 Sight/Hearing Event
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

- Sight target: 선과 색상 표시
- Sound Event: 위치 sphere와 TTL
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
  "model_version": "0.3.0",
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

1. Quinn이 Manny 정면에 정지
2. Quinn이 Manny 뒤에서 걷기
3. Quinn이 Manny 뒤에서 달리기
4. Quinn이 벽 뒤에서 발소리 발생
5. 소리만 있고 Actor 없음
6. 우호 관계에서 접근
7. 적대 관계에서 접근
8. 겁이 많은 Manny Profile
9. 용감한 Manny Profile
10. 현재 Investigate 중 새 폭발 발생
11. target이 이동 불가능한 위치에 있음
12. NavMesh가 없는 위치
13. 모델 파일 누락
14. 잘못된 manifest
15. 모든 후보 mask
16. 30 NPC 동시 판단

## 26.7 회귀 지표

- 금지 행동 선택률
- 행동 진동 횟수/분
- 평균 반응 시간
- top-1/top-3 교사 일치율
- 소리 조사 완료율
- target switch 빈도
- fallback 비율
- inference p50/p95/p99
- Game Thread frame time 영향

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
- Quinn 발소리 notify 연결

### 산출물

- `L_AINativeNPC_MVP`
- `BP_AINativeNPC_Manny`
- `DA_NPCProfile_Guard_Cautious`
- Perception debug UI

### 완료 조건

- Manny가 Quinn과 발소리를 Perception Cache에 기록
- 아직 판단 로직은 없음
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
- entity 8×40
- candidate 32×48
- MLP + Entity Encoder + Candidate Scorer
- 단일 프레임 LLM/사람 Ranking 데이터
- 계약 코드 생성

### 완료 조건

- 기본 20개 시나리오에서 적절한 top-3 행동
- 뒤쪽 발소리 → TurnTo/LookAt/Investigate 계열 일반화
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

다음 순서대로 구현하면 ML과 클라이언트 문제를 한꺼번에 디버깅하는 상황을 피할 수 있다.

1. Third Person C++ 프로젝트 생성
2. Quinn 기본 플레이 확인
3. Manny 기반 `AAINativeNPCCharacter` 생성
4. AIController possession 확인
5. NavMesh와 `MoveToLocation` 테스트
6. `TurnTo` Skill 단독 테스트
7. AI Sight로 Quinn 감지
8. Quinn 발소리 `ReportNoiseEvent` 연결
9. Hearing Event를 화면에 표시
10. Observation Snapshot 구조 생성
11. Candidate Generator 생성
12. Editor에서 Candidate 수동 선택
13. Skill Executor로 TurnTo/Investigate 실행
14. Tiny ONNX 모델 생성
15. NNE CPU inference 연결
16. Python/Unreal parity test
17. 실제 Candidate Scorer V0 학습
18. 뒤쪽 발소리 시나리오 실행
19. 관계/Profile 변경 시 행동 변화 확인
20. GRU 추가

가장 중요한 Gate는 13번이다. **모델 없이도 Observation→Candidate→Skill 실행 파이프라인이 동작해야 한다.** 그 다음 NNE를 연결해야 문제의 원인이 클라이언트인지 모델인지 구분할 수 있다.

---

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

- 뒤쪽 소리를 듣고 확인
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

# 33. 공식 참고 문서

- [Third Person Template — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/third-person-template-in-unreal-engine?application_version=5.7)
- [Neural Network Engine — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-in-unreal-engine?application_version=5.7)
- [Neural Network Engine Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/neural-network-engine-overview-in-unreal-engine?application_version=5.7)
- [AI Perception in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine?application_version=5.7)
- [StateTree in Unreal Engine — Unreal Engine 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/state-tree-in-unreal-engine?application_version=5.7)
- [Navigation System in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/navigation-system-in-unreal-engine?application_version=5.7)
- [Animation Blueprints in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprints-in-unreal-engine?application_version=5.7)

---

# 34. 최종 권장 구조

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
Quinn 발소리/행동
→ Manny AI Perception
→ Observation Builder
→ Candidate Generator
→ NNE Async Inference
→ Decision Stabilizer
→ Skill Executor
→ Manny Movement/Animation
→ Decision Log
```

본 설계에서 신경망 프로젝트와 Unreal 클라이언트는 명확히 분리되지만, **모델 계약과 Golden Test**를 통해 하나의 제품으로 연결된다. Unreal 클라이언트는 감각과 실행 능력을 제공하고, 신경망은 상황별 행동 선호를 담당한다. 이 경계를 유지하는 것이 전통적인 대규모 조건문/Behavior Tree로 되돌아가지 않으면서도, 실제 게임에서 안정적으로 동작하는 AI Native NPC를 만드는 핵심이다.
