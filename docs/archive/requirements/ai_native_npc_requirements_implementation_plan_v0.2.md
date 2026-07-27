# AI Native NPC 의사결정 시스템
## 구체 요구사항 및 구현 계획서 — 프로덕션 검토 반영판

- 문서 버전: v0.2
- 개정일: 2026-07-26
- 원본 문서: `ai_native_npc_requirements_implementation_plan.md` v0.1
- 문서 목적: 전통적인 대규모 조건문 및 Behavior Tree 없이, NPC가 지각·관계·성격·기억을 바탕으로 전술 행동을 선택하는 학습 기반 시스템의 요구사항과 프로덕션 구현 계획을 정의한다.
- 목표 독자: 게임 디자이너, AI/ML 엔지니어, 게임플레이 프로그래머, 서버/네트워크 프로그래머, 테크니컬 디자이너, QA
- 권장 개발 전략: **장기 Goal과 안전·실행 계약은 코드가 소유하고, 학습 모델은 현재 Goal 안에서 후보 전술 행동을 평가한다.**
- V1 메모리 전략: **최근 3~10초의 명시적 이벤트 버퍼**
- V1 감정·관계 전략: **사건 기반 코드 갱신, 모델은 읽기 전용**
- V1 후보 전략: **선호 기반 사전 가지치기 없이 최대 후보 집합을 평가하고 Candidate Recall을 먼저 검증**

---

# 0. 리뷰 판정과 개정 원칙

제시된 리뷰 항목은 모두 타당하다. 다만 몇 항목은 다음과 같이 범위를 명확히 해 반영한다.

| 리뷰 항목 | 판정 | v0.2 반영 |
|---|---|---|
| Candidate Generator가 숨은 Behavior Tree가 될 위험 | 타당 | Candidate Recall을 최우선 게이트로 추가하고, V1에서는 32개 선호 가지치기를 제거 |
| 장기 목표 계층 부재 | 타당 | 코드 소유의 Mission Goal / Intent Phase 계층 추가 |
| Ground Truth와 NPC Belief 혼재 | 타당 | 모든 타인 정보를 `Perceived/Believed State`로 강제 |
| LLM·절차 데이터의 편향 | 타당 | Silver/Gold/Live 데이터 계층, 시나리오 계열 hold-out, DAgger 추가 |
| 비교 기준선 부재 | 타당 | 동일 Skill·Candidate·Mask를 사용하는 소형 Utility Baseline 필수화 |
| 신규 Role/Skill 무코드 추가 주장 | 타당 | 기존 속성·Skill 조합만 코드 변경이 없을 수 있으며, 데이터·평가·재학습은 별도 요구 |
| GRU 운영 수명주기 부재 | 타당 | V1 GRU 제외, 명시적 이벤트 버퍼 사용. GRU는 Phase 2 선택 기능으로 이동 |
| 확신도 정의 부족 | 타당 | 점수 차이를 confidence로 사용하지 않고 별도 Calibration/OOD/Abstain 계약 추가 |
| 감정·관계 Delta 피드백 루프 | 타당 | V1에서 Delta Head 제거, 사건 기반 상태 전이로 변경 |
| 비동기·멀티플레이 실행 계약 부재 | 타당 | Decision ID, Target Generation, Deadline, Commit 재검증, 서버 권위 추가 |
| 16 Skill × 8 Target과 후보 32개 모순 | 타당 | V1 Target 16개, NoTarget 1개, 패딩 상한 272개로 일치시킴 |
| Entity 8~16개와 Target 8개 모순 | 타당 | V1 Perceived Entity와 Action Target 용량을 모두 16개로 통일 |
| GRU 입력 256차원 모순 | 타당 | Optional GRU 앞에 명시적 `Fusion 416→256` Projection 추가 |
| 3M FP32와 10MB 모델 예산 충돌 | 타당 | FP32 V1 상한을 2M 파라미터로 제한 |
| NPC 수·판단 주기·프레임당 요청 수 불일치 | 타당 | 초당 Decision Request와 p50/p95/p99 기준으로 재정의 |
| Skill 실행 계약 부족 | 타당 | 자원 예약, 실패 원인, 재개 정책, Commit 직전 검증 추가 |

본 개정판은 “신경망 모델”만을 제품으로 보지 않는다. 다음 네 가지가 모두 제품 범위다.

1. Perception/Belief State
2. Goal/Intent와 Candidate Pipeline
3. 학습·Calibration·평가 파이프라인
4. 비동기 Skill 실행 및 서버 권위 계약

---

# 1. 프로젝트 배경

전통적인 NPC AI는 흔히 다음과 같은 상황별 규칙으로 구현된다.

- 플레이어가 특정 영역에 들어오면 감지한다.
- 플레이어가 시야 안에 있으면 바라본다.
- 뒤쪽에서 소리가 나면 뒤를 돌아본다.
- 관계가 적대적이고 무기를 들고 있으면 경고한다.
- 경고 이후에도 접근하면 공격한다.
- 체력이 낮거나 적의 수가 많으면 도망간다.

각 규칙은 단순하지만 거리, 방향, 가시성, 소리, 관계, 성격, 최근 사건, 현재 임무가 조합되면 분기와 예외가 급격히 증가한다.

본 프로젝트는 작업의 단위를 다음처럼 바꾼다.

```text
기존
상황 조합마다 반응 규칙 작성
        ↓
개정 구조
지각·Belief 구성
+ 장기 Goal 수명주기
+ 재사용 가능한 Skill
+ 안전·실행 제약
+ 후보 행동의 적합도를 학습
```

신경망은 모든 게임 로직을 대체하지 않는다. 특히 다음은 신경망이 소유하지 않는다.

- 퀘스트 목표와 장기 임무
- 물리적 가능 여부
- 자원 선점
- 서버 권위
- 감정·관계의 영구 변경
- 대상의 실제 숨은 상태
- Skill의 실행 및 성공 판정

---

# 2. 프로젝트 목표

## 2.1 핵심 목표

1. 상황별 조건문과 거대한 Behavior Tree 분기 작성량을 줄인다.
2. 공용 전술 의사결정 모델을 여러 NPC 성격과 역할에 재사용한다.
3. 코드가 소유한 Goal 안에서 새로운 상황 조합에 일반화된 행동 순위를 제공한다.
4. 디자이너가 역할 속성, 성격, Goal 정책, 선호 데이터로 NPC를 제작할 수 있게 한다.
5. NPC가 실제로 지각하거나 믿는 정보만 사용해 공정한 행동을 하게 한다.
6. Candidate Pipeline의 누락과 모델 Ranking 오류를 분리해 측정한다.
7. 소형 Utility Baseline과 동일 조건에서 모델의 품질 및 제작 효율을 비교한다.
8. 비동기 추론, stale 결과, 자원 경쟁, 서버 권위를 포함한 실행 계약을 제공한다.
9. 모델의 불확실성과 OOD 상황에서 abstain하고 안전 정책으로 복귀할 수 있게 한다.
10. 실제 플레이 데이터와 사람 개입을 통해 배포 후에도 개선 가능한 파이프라인을 만든다.

## 2.2 비목표

초기 버전에서 다음 항목은 목표로 하지 않는다.

- 신경망이 직접 애니메이션 프레임 또는 매 프레임 이동 벡터를 생성하는 것
- 신경망이 NavMesh 경로를 직접 계산하는 것
- 신경망이 퀘스트·Mission Goal을 임의로 생성하거나 완료하는 것
- LLM이 게임 상태를 직접 변경하는 것
- 모델이 감정·관계 값을 직접 누적 변경하는 것
- GRU hidden state만으로 장기 계획을 유지하는 것
- 새로운 Role이나 Skill의 무조건적인 zero-shot 동작
- 학습 없이 모든 NPC 행동이 자동으로 완성되는 것
- Ground Truth를 이용해 보이지 않는 플레이어를 추적하는 것
- 안전·권한·자원 경쟁을 모델 판단에만 맡기는 것

---

# 3. 핵심 설계 원칙

## 3.1 Mission Goal, 전술 판단, Skill 실행의 분리

시스템은 세 계층으로 나뉜다.

### 계층 A — Goal/Intent Authority

코드와 데이터가 소유한다.

- 퀘스트 Mission Goal
- 현재 장기 Goal
- Goal의 단계 또는 Intent Phase
- 단계 진입/종료 조건
- 시간 제한
- 복귀 지점
- 서사상 허용 범위
- Goal 우선순위
- 세이브/로드

예시:

```text
InvestigateDisturbance
  Orient
  → ReachLastKnownPosition
  → SearchArea
  → ReturnToPost

EnforceRestrictedArea
  Observe
  → Warn
  → Escalate
  → Resolve
```

이는 모든 센서 조합을 조건문으로 작성하는 Behavior Tree가 아니다. Goal 계층은 장기 수명주기와 단계만 소유하며, 각 단계에서 어떤 전술 행동을 선택할지는 모델이 결정한다.

### 계층 B — Neural Tactical Policy

학습 모델이 담당한다.

- 현재 Goal/Intent 안에서 후보 Skill의 적합도 평가
- 행동 대상 선택
- 행동 지속 시간·강도·선호 거리 등 제한된 파라미터 제안
- 대화 행위와 표현 톤 제안
- 후보 행동의 Ranking
- Calibration을 거친 선택 수락 또는 abstain

### 계층 C — Skill Executor

게임 코드가 담당한다.

- Commit 직전 실행 가능 여부 재검증
- 자원 예약
- NavMesh 이동
- 회전, LookAt, 애니메이션
- 공격 및 상호작용 판정
- 성공·실패·취소 판정
- 실패 원인 기록
- Suspend/Resume
- 자원 반환
- 네트워크 복제

## 3.2 Ground Truth와 Perceived/Believed State 분리

월드가 알고 있는 사실과 NPC가 알고 있는 사실은 별도 데이터 구조여야 한다.

### Ground Truth 사용 허용

- NPC 자신의 체력과 자원
- 서버 권위 검증
- 물리 및 피해 판정
- 학습 보상과 오프라인 평가
- Editor 전용 디버그
- 치트 방지

### 모델 입력 허용

대상에 대해서는 다음 중 하나로 획득한 값만 사용한다.

- 현재 시야로 관측
- 소리로 추정
- 마지막 관측 기억
- 대화나 퀘스트를 통해 명시적으로 전달
- 다른 NPC가 공유한 정보

모든 Belief 값은 가능하면 다음 메타데이터를 가져야 한다.

```text
value
source
observed_at
age
confidence
valid_until
uncertainty
```

예시:

- 대상 체력 → 정확한 값이 아니라 관측 가능한 추정 구간
- 대상 무기 → 현재 보이거나 명시적 사건으로 확인된 경우만
- 대상 현재 행동 → 애니메이션·소리로 분류된 추정값
- 소리 원인 Actor ID → Attribution Confidence가 충분한 경우만
- 벽 뒤 현재 위치 → 마지막 목격 위치만 사용하고 실제 Actor 위치는 차단

## 3.3 행동 규칙이 아닌 Skill 구현

개발자는 다음과 같은 재사용 가능한 Skill을 구현한다.

- `Idle`
- `ContinueCurrentAction`
- `LookAt`
- `TurnTo`
- `Approach`
- `KeepDistance`
- `RetreatFrom`
- `Follow`
- `Investigate`
- `SearchArea`
- `Greet`
- `Warn`
- `CallForHelp`
- `TakeCover`
- `Flee`
- `Attack`

Skill은 “언제 선택할지”가 아니라 “선택된 행동을 어떻게 실행할지”를 정의한다.

## 3.4 하드 제약과 소프트 판단의 분리

### 하드 제약

- 대상이 존재하고 generation이 일치하는가
- Skill에 필요한 장비가 있는가
- 현재 Goal에서 금지되지 않았는가
- 서버 권한이 있는가
- 자원을 예약할 수 있는가
- 경로 또는 상호작용 슬롯이 유효한가
- 대상이 Commit 시점에도 실행 가능한가

### 소프트 판단

- 지금 공격하는 것이 적절한가
- 소리를 무시할 것인가 조사할 것인가
- 경고할 것인가 후퇴할 것인가
- 어느 대상을 우선할 것인가
- 현재 행동을 계속할 것인가
- 어느 정도 거리를 유지할 것인가

## 3.5 Utility Baseline은 필수 비교군

완성형 Behavior Tree를 교사로 만들 필요는 없지만, 동일한 다음 요소를 사용하는 작은 Utility Baseline은 반드시 구현한다.

- 동일 Observation/Belief
- 동일 Goal/Intent
- 동일 Skill
- 동일 Candidate Set
- 동일 Action Mask
- 동일 Skill Executor

Baseline은 10~20개의 단순한 가중 특성 또는 곡선으로 구성하며 모델의 교사로 사용하지 않는다.

비교 목적:

- 모델이 실제로 더 자연스러운가
- 신규 시나리오에서 더 잘 일반화하는가
- 행동 제작 시간이 줄어드는가
- 안전 위반과 latency가 증가하지 않는가
- fallback으로 사용할 수 있는가

---

# 4. 전체 시스템 아키텍처

```text
Authoritative Game World
  │
  ├─ Ground Truth
  ├─ Quest / Mission
  └─ Server Rules
          │
          ├───────────────┐
          ▼               │
Sensor & Event Layer      │
  ├─ Sight                │
  ├─ Hearing              │
  ├─ Damage               │
  └─ Shared Knowledge     │
          │               │
          ▼               │
Perception / Belief Builder
  ├─ source
  ├─ observed_at
  ├─ confidence
  ├─ TTL
  └─ last known state
          │
          ▼
Goal / Intent Authority
  ├─ Mission Goal
  ├─ Intent Phase
  ├─ phase lifecycle
  └─ allowed tactical scope
          │
          ▼
Observation Builder
  ├─ self state
  ├─ perceived entities
  ├─ relationship/personality
  ├─ explicit event buffer
  └─ goal/intent state
          │
          ▼
Candidate Universe Generator
  ├─ Skill × Target compatibility
  ├─ hard masks only
  ├─ mandatory fallback candidates
  └─ candidate set hash
          │
          ▼
Candidate Coverage Gate
  ├─ Entity Recall
  ├─ Candidate Recall
  └─ miss-reason audit
          │
          ├───────────────┐
          ▼               ▼
Neural Tactical Scorer   Utility Baseline
          │               │
          └──────┬────────┘
                 ▼
Calibration / OOD / Abstain Gate
                 │
                 ▼
Async Decision Commit
  ├─ decision_id
  ├─ deadline
  ├─ target generation
  ├─ goal revision
  ├─ CanExecute 재검증
  └─ atomic resource reservation
                 │
                 ▼
Skill Executor
  ├─ Start/Tick/Suspend/Resume
  ├─ success/failure taxonomy
  └─ resource release
                 │
                 ▼
Result / Event / Training Logger
```

---

# 5. 기능 요구사항

## 5.1 Perception 및 Belief State

### FR-BELIEF-001 정보 출처 강제

타인 또는 외부 세계에 대한 Feature는 다음 출처 중 하나를 가져야 한다.

- `SightCurrent`
- `HearingEvent`
- `LastSeenMemory`
- `SharedKnowledge`
- `ScriptedKnowledge`
- `Inferred`
- `Unknown`

출처가 없는 외부 상태는 모델 입력에 넣지 않는다.

### FR-BELIEF-002 시간과 신뢰도

각 Belief는 다음 값을 포함한다.

- 관측 시간
- 현재 age
- confidence
- TTL
- valid flag
- uncertainty 또는 추정 구간

### FR-BELIEF-003 Ground Truth 누출 방지

- 숨은 Actor의 현재 위치를 Belief 위치로 갱신하지 않는다.
- 대상의 정확한 체력·탄약은 게임 디자인상 공개된 경우가 아니면 전달하지 않는다.
- 원인을 모르는 소리에 Instigator Actor ID를 강제로 붙이지 않는다.
- Ground Truth 로그와 Policy Input Buffer를 물리적으로 분리한다.
- 자동 테스트에서 Ground Truth만 변경했을 때 Policy Tensor가 동일한지 검증한다.

### FR-BELIEF-004 거리·방향

모델이 받는 거리와 방향은 Perceived Position을 기준으로 계산한다.

- 상대 위치 XYZ
- 3D 거리
- 평면 거리
- 로그 거리
- bearing sin/cos
- elevation sin/cos
- 감지 위치 기반 상대 속도
- 접근/이탈 속도

### FR-BELIEF-005 시야

- visible now
- line of sight
- 노출 정도
- 시야 중심 편차
- 연속 가시 시간
- 마지막 목격 후 경과 시간
- 마지막 목격 위치
- sight confidence

### FR-BELIEF-006 소리

- 소리 종류
- 소리 위치
- loudness
- 발생 후 경과 시간
- 반복 횟수
- 추정 위험도
- 원인 attribution confidence
- event TTL

## 5.2 NPC 자기 상태

NPC 자신의 권위 있는 상태는 직접 사용할 수 있다.

- 체력
- 스태미나
- 탄약
- 사용 가능한 아이템
- 이동 가능 여부
- 현재 Skill
- 현재 Skill 지속 시간
- 최근 Skill 결과
- 피격 여부
- 최근 피해량
- 현재 엄폐
- 현재 Goal/Intent
- 현재 구역
- 전투 허용 상태

## 5.3 성격과 역할

### 성격

연속형 속성 벡터를 기본으로 한다.

- 공격성
- 용기
- 호기심
- 충성심
- 사교성
- 충동성
- 인내심
- 경계심
- 이타성
- 규칙 준수 성향

### 역할

V1은 다음을 함께 사용할 수 있다.

- 역할 속성 벡터
- 이미 학습된 Role ID Embedding

새로운 Role 프리셋이 기존 속성 범위와 기존 Skill만 사용한다면 엔진 코드 변경이 없을 수 있다. 그러나 분포가 달라지면 데이터 추가, 평가, Calibration 또는 재학습이 필요하다.

**새 Role을 추가하는 것과 zero-shot으로 품질을 보장하는 것은 다르다.**

## 5.4 Goal/Intent State

각 NPC는 다음 상태를 가져야 한다.

- `mission_goal_id`
- `goal_instance_id`
- `goal_revision`
- `intent_phase`
- `phase_entered_at`
- `phase_timeout`
- `phase_progress`
- `home_or_return_target`
- `allowed_skill_tags`
- `forbidden_skill_tags`
- `goal_priority`

Goal/Intent 변경은 로그와 세이브 대상이다.

## 5.5 감정과 관계

### V1 원칙

- 감정과 관계는 모델 입력이다.
- 모델은 감정·관계를 직접 변경하지 않는다.
- 갱신은 사건 기반 코드가 담당한다.
- 동일 사건은 idempotent event ID로 한 번만 반영한다.
- 값 범위, 감쇠, 회복 속도, 최대 변화량을 코드와 데이터에서 제한한다.

예시:

```text
PlayerHealedNPC
  trust +0.15
  gratitude +0.25

PlayerThreatenedNPC
  fear +0.20
  affinity -0.10
```

모델은 대화 표현용 tone이나 animation intensity를 제안할 수 있지만 권위 있는 상태에는 쓰지 않는다.

### Phase 2 이후 실험

감정·관계 예측 Head는 오프라인 분석용으로만 추가할 수 있다. 직접 상태 전이에 연결하려면 별도 안정성 검증과 승인 계층이 필요하다.

## 5.6 단기 기억과 이벤트 버퍼

### V1 — 명시적 이벤트 버퍼

GRU 대신 최근 3~10초의 이벤트를 고정 길이 Ring Buffer로 제공한다.

권장:

- 최대 8~16 이벤트
- event type
- target slot
- event age
- strength
- source
- result
- position confidence
- relevant goal phase

예시 이벤트:

- 뒤에서 발소리
- 플레이어 무기 꺼냄
- 경고 Skill 완료
- 플레이어가 경고를 무시함
- target sight lost
- path failure
- 피해 수신

장점:

- save/load 가능
- 디버깅 가능
- 화면 밖 LOD 후 재구성 가능
- 모델 hot swap 시 호환성 관리가 쉬움
- hidden state drift를 줄임

### Phase 2 — 선택적 GRU

GRU는 이벤트 버퍼 대비 품질 향상이 검증될 때만 추가한다.

Hidden State 수명주기:

- Spawn/Respawn: 초기화
- Pawn Possession 변경: 초기화
- 큰 Teleport 또는 Level 이동: 초기화
- 모델·Schema·Skill Registry 변경: 초기화
- 서버 재접속: 이벤트 버퍼로 재구성하거나 초기화
- 화면 밖 LOD: hidden 갱신 중단 후 복귀 시 burn-in 또는 초기화
- Save/Load: 기본은 이벤트 버퍼를 저장하고 hidden을 재구성
- Hot Swap: 모든 hidden 초기화 후 warm-up flag 설정
- hidden을 저장하려면 동일 모델 hash와 런타임 버전을 강제

## 5.7 주변 개체와 Action Target

### V1 용량

- Perceived Entity 최대 16개
- Action Target 최대 16개
- `NoTarget` 별도 1개
- Entity와 Target의 최대 수를 문서 전체에서 동일하게 유지

### Entity 입력

- stable entity ID
- generation
- entity type
- Perceived Position
- 위치 출처
- 관측 age
- confidence
- 상대 거리·방향
- 가시성
- 최근 소리
- 추정 위협
- 추정 무기 상태
- 추정 체력 구간
- 관계
- 현재 관측된 행동
- 상호작용 가능 여부

Entity 슬롯 누락은 Candidate 누락으로 이어지므로 `Entity Target Recall`을 별도 측정한다.

---

# 6. 행동 Skill 요구사항

## 6.1 공통 인터페이스

```cpp
interface INPCSkill
{
    // 후보 생성 단계의 저비용 정적/스냅샷 검증
    bool CanGenerateCandidate(
        const FNPCContextSnapshot& Context,
        const FActionTargetSnapshot& Target) const;

    // 실행 계획 생성. 아직 월드 상태를 변경하지 않는다.
    FSkillExecutionPlan BuildExecutionPlan(
        const FNPCContextSnapshot& Context,
        const FActionTargetSnapshot& Target,
        const FActionParameters& Parameters) const;

    // Commit 직전 최신 월드 상태로 재검증
    FSkillValidationResult ValidateAtCommit(
        const FSkillExecutionPlan& Plan,
        const FNPCCommitContext& CommitContext) const;

    // 엄폐물, 상호작용 슬롯 등 공유 자원을 원자적으로 예약
    FSkillReservationResult TryReserveResources(
        const FSkillExecutionPlan& Plan);

    void Start(const FSkillExecutionPlan& Plan);
    ESkillStatus Tick(float DeltaTime);

    bool CanSuspend() const;
    void Suspend(ESuspendReason Reason);
    FSkillResumeResult Resume();

    void Cancel(ECancelReason Reason);
    void ReleaseResources();

    FSkillResult GetResult() const;
};
```

## 6.2 Skill 공통 속성

- Skill ID와 version
- 의미 메타데이터
- 허용 Target Type
- 대상 필요 여부
- 최소/최대 지속 시간
- cooldown
- 긴급 interrupt 가능 여부
- 이동/대화/무기 요구
- 권한 요구
- Goal/Intent 허용 태그
- 성공/실패 조건
- 실행 직전 재검증 항목
- 예약 자원 종류
- reservation TTL
- resume policy
- 모델이 조정 가능한 파라미터 범위

## 6.3 실패 원인 Taxonomy

최소 분류:

- `TargetInvalid`
- `TargetGenerationChanged`
- `PreconditionChanged`
- `GoalChanged`
- `PathUnavailable`
- `ReservationConflict`
- `Interrupted`
- `TimedOut`
- `AuthorityRejected`
- `ExecutionError`
- `CancelledByNewDecision`

실패 원인은 이벤트 버퍼, 디버그 로그, 학습 데이터에 기록한다.

## 6.4 재개 정책

Skill마다 다음 중 하나를 지정한다.

- `NotResumable`
- `Restartable`
- `SuspendAndResume`

## 6.5 초기 Skill 목록

### 필수 V1

1. `Idle`
2. `ContinueCurrentAction`
3. `LookAt`
4. `TurnTo`
5. `Approach`
6. `KeepDistance`
7. `RetreatFrom`
8. `Follow`
9. `Investigate`
10. `SearchArea`
11. `Greet`
12. `Warn`
13. `CallForHelp`
14. `TakeCover`
15. `Flee`
16. `Attack`

### 신규 Skill 추가 요구사항

새 Skill은 다음 작업이 필요하다.

- 엔진 실행 코드
- Skill Registry와 version 갱신
- Target Type 및 의미 메타데이터
- Candidate compatibility
- 테스트 시나리오
- 학습 데이터
- 모델 평가와 대개 재학습
- Calibration 재검증

Skill 메타데이터를 사용하면 일부 전이 학습이 가능하지만 V1에서 zero-shot 품질을 보장하지 않는다.

---

# 7. Candidate Generator와 Coverage

## 7.1 역할

Candidate Generator는 자연스러움을 판단하지 않는다. 다음만 수행한다.

- Skill과 Target Type의 정적 호환성
- 현재 snapshot에서 명백히 불가능한 하드 조건
- 현재 Goal에서 허용된 Skill 범위
- Target handle 생성
- mandatory fallback 삽입
- candidate set hash 계산

다음과 같은 선호 규칙은 넣지 않는다.

```text
가까우면 Attack 후보 우선
겁이 많으면 Flee 후보 유지
뒤쪽 소리면 TurnTo 후보 우선
```

이런 판단은 Neural Scorer 또는 Utility Baseline이 담당한다.

## 7.2 후보 용량과 모순 해소

V1 상수:

```text
Skill Capacity          16
Action Target Capacity  16
NoTarget Capacity        1
Padded Candidate Max   272
```

최악의 단순 상한:

```text
16 Skills × (16 Targets + NoTarget) = 272
```

실제로는 Skill–Target 호환성 Mask로 유효 후보 수가 줄어든다.

V1에서는 후보를 32개로 사전 축소하지 않는다. 최대 272개를 패딩 Tensor 또는 ragged batch로 평가한다. 성능 프로파일링 후에도 병목이 확인되지 않으면 그대로 유지한다.

## 7.3 Candidate Recall

정답 또는 허용 가능한 후보 집합을 `G(s)`, 생성된 후보를 `C(s)`라고 정의한다.

### Any-Acceptable Candidate Recall

```text
P(C(s) ∩ G(s) ≠ ∅)
```

해당 상태에서 허용 가능한 행동이 하나라도 후보에 들어왔는지 측정한다.

### Full Acceptable Recall

```text
Σ |C(s) ∩ G(s)| / Σ |G(s)|
```

여러 개의 적절한 행동 중 몇 개가 보존됐는지 측정한다.

### Target Recall

사람 또는 Gold Label이 선택한 target이 16개 Target 슬롯에 포함됐는지 측정한다.

### V1 Gate

- 전체 Any-Acceptable Candidate Recall: **99.5% 이상 목표**
- 안전·퀘스트 Critical Scenario: **100%**
- Target Recall: **99.5% 이상 목표**
- Candidate miss는 모델 오류가 아니라 Pipeline 오류로 별도 집계
- 모델 Top-1/Top-3는 Candidate가 존재하는 조건부 지표와 전체 end-to-end 지표를 모두 보고

## 7.4 Candidate Miss 원인

- Perception miss
- Belief TTL 만료
- Entity slot 탈락
- Target Type 호환성 오류
- Goal scope 오류
- 잘못된 hard mask
- candidate capacity 초과
- stale target handle
- registry/schema mismatch

Decision Inspector에서 miss 원인을 표시해야 한다.

## 7.5 향후 Candidate Retriever

272개 평가가 실제 목표 하드웨어에서 병목일 때만 Retriever를 도입한다.

도입 조건:

- 같은 후보 universe를 먼저 생성
- reducer가 제거한 후보를 로그
- Hold-out Candidate Recall 99.5% 이상
- Critical Scenario 100%
- role/goal별 worst-group recall 보고
- Retriever 변경 시 Scorer 성능과 별개로 회귀 테스트

---

# 8. 신경망 아키텍처

## 8.1 권장 모델

모델은 후보 행동의 적합도 점수를 계산한다.

```text
Score = f(
    SelfState,
    GoalIntent,
    PerceivedEntities,
    ExplicitEventBuffer,
    CandidateAction,
    CandidateTarget,
    Personality,
    Relationship
)
```

## 8.2 V1 입력 인코더

### Global Context Encoder

입력:

- NPC 자기 상태
- 성격
- 관계
- 현재 Skill
- 월드 Context

구조:

```text
Input 96~160
Linear → 128
SiLU
LayerNorm
Linear → 128
```

### Entity Encoder

```text
Perceived Entity 40~64
Linear → 64
SiLU
Linear → 64
LayerNorm
```

### Entity Aggregator

```text
Entity Embedding 64
Masked Attention 또는 Set Pooling
Output 128
```

### Explicit Event Encoder

```text
Event 24~40
Event MLP → 48
Temporal Attention / Masked Pooling
Output 96
```

### Goal/Intent Encoder

```text
Goal/Intent metadata
Embedding + MLP
Output 32
```

### Previous Action/Result

```text
Previous Skill Embedding 16
Previous Result Embedding 16
```

### Fusion

정확한 차원:

```text
Global Context      128
Entity Aggregate    128
Event Buffer         96
Goal/Intent          32
Previous Skill       16
Previous Result      16
------------------------
Concat              416
Linear 416 → 256
SiLU
LayerNorm
```

V1에서는 이 256차원 Fusion을 MLP로 128차원 Tactical Context로 변환한다.

```text
Fusion 256 → 128
```

## 8.3 Phase 2 선택적 GRU

GRU를 사용할 경우 입력 차원 모순을 피하기 위해 Fusion Projection 뒤에 배치한다.

```text
Concat 416
→ Fusion Linear 416→256
→ GRU Input 256
→ GRU Hidden 128
```

GRU 채택 조건:

- Event Buffer 모델보다 시퀀스 품질이 유의미하게 개선
- save/load와 LOD 회귀 테스트 통과
- hidden reset 및 warm-up 정책 구현
- 모델 hot swap 정책 구현
- 성능 예산 충족

## 8.4 Action과 Target Encoder

### Action Encoder

- Skill ID
- Skill 의미 메타데이터
- 이동/사회/전투 카테고리
- 위험도
- 현재 Skill과 동일 여부
- 기본 지속 시간
- resource requirement
- resume policy

```text
Skill Embedding 32
Metadata MLP 32
Concat → 64
```

### Target Encoder

대상 Entity Embedding 64를 사용한다.

`NoTarget`은 학습 가능한 별도 Embedding 64를 사용한다.

### Pair Feature

- 거리
- 방향 정렬
- 현재 보임
- 위치 confidence
- path projection
- line of sight
- Skill–Target compatibility
- 현재 target과 동일 여부

```text
Pair Feature → 32
```

## 8.5 Score Head

```text
Tactical Context 128
Action Embedding   64
Target Embedding   64
Pair Feature       32
----------------------
Concat            288
Linear → 128
SiLU
Linear → 64
SiLU
Linear → 1
```

출력 점수는 utility/logit이며 confidence가 아니다.

### V1 출력

- `candidate_scores`
- 제한된 행동 파라미터
- optional dialogue act
- optional expression tone

### V1에서 제외

- authoritative emotion delta
- authoritative relationship delta
- 퀘스트/Goal 변경
- 아이템·경제·게임 상태 변경

## 8.6 Calibration, OOD, Abstain

1위와 2위 점수 차이는 confidence가 아니다. 후보 수와 분포가 변하면 값의 의미도 바뀐다.

### Calibration Set

Train/Validation/Test와 분리된 Calibration Set을 유지한다.

### Acceptability Calibrator

다음 값을 입력으로 선택 행동이 허용 가능한 행동일 확률을 추정한다.

- top-1 score
- top-2 gap
- candidate score entropy
- candidate count
- current role/goal group
- OOD score
- scorer model version
- candidate schema version

출력:

```text
P(selected candidate is acceptable)
```

### OOD 탐지

V1:

- Feature 범위 위반
- unseen Role/Skill/Goal ID
- missing modality 패턴
- 학습 분포와의 embedding distance
- 비정상 candidate count
- schema/version mismatch

### Abstain

role/goal 또는 상황군별 threshold를 사용한다.

abstain 시:

- 현재 안전한 행동 유지
- Utility Baseline 사용
- 최소 안전 정책 사용
- 재판단 요청

관리 지표:

- Calibration Error
- Brier Score
- Risk–Coverage Curve
- OOD detection recall
- abstain rate
- fallback rate
- 잘못 수락한 비율
- 불필요하게 abstain한 비율

Candidate Set이나 모델이 변경되면 Calibration도 다시 수행한다.

## 8.7 모델 크기 예산

V1:

- 파라미터: **0.5M~2.0M**
- FP32 raw weight: 최대 약 8MB
- 패키징 모델 목표: 10MB 이하
- activations, runtime cache, calibration asset는 별도 측정
- 2M을 초과하면 FP16 또는 INT8을 기본 검토

참고:

```text
3M parameters × 4 bytes = 약 12MB
```

따라서 3M FP32 모델은 10MB 예산과 호환되지 않는다.

## 8.8 신규 Role/Skill 일반화

### Role

속성 벡터 기반 Role은 알려진 범위 안에서 일부 보간이 가능하다. 그러나 새로운 역할 분포에 대한 품질은 별도 hold-out 테스트와 Calibration이 필요하다.

### Skill

Skill 의미 메타데이터는 전이 가능성을 높이지만, 실행 코드와 학습 사례가 없는 신규 Skill을 zero-shot으로 신뢰하지 않는다.

V1 성공 기준에 “신규 Skill 무재학습 추가”를 포함하지 않는다.

---

# 9. 장기 행동 일관성과 의사결정 안정화

## 9.1 Goal/Intent가 소유하는 상태

- 장기 목적
- 단계
- 단계 시작 시간
- 단계 완료 조건
- Search budget
- 경고 횟수
- 복귀 목표
- Goal 우선순위
- 중단 및 재개 정책

GRU 또는 최근 이벤트만으로 이를 암묵적으로 유지하지 않는다.

## 9.2 판단 주기

권장 시작값:

- Idle/저우선 NPC: 1Hz
- Alert/사회 반응: 2~3Hz
- Combat: 5Hz
- 피격·폭발·Skill 종료: 이벤트 기반 요청
- Skill 실행·애니메이션: 매 프레임

판단 빈도는 Goal과 상황에 따라 조정하지만 성능 평가는 “프레임당 NPC 수”가 아니라 초당 Decision Request로 측정한다.

## 9.3 행동 전환 비용

- 현재 Skill 취소 비용
- 애니메이션 전환 비용
- target 변경 비용
- 최근 반복 행동 패널티
- 실패 Skill 재시도 패널티
- Goal phase 전환 비용

전환 비용은 모델 원점수와 별도 로그에 기록한다.

## 9.4 최소 지속 시간과 긴급 인터럽트

예시:

- `LookAt`: 0.5초
- `Warn`: 1.5초
- `Investigate`: 3초
- `SearchArea`: 5초
- `Flee`: 2초

긴급 인터럽트:

- 피격
- 폭발
- target 사망
- Goal revision 변경
- path 차단
- 권한 변경
- 중요 대화
- reservation 상실

## 9.5 반복과 루프 방지

- 최근 Skill 시퀀스 Event Buffer
- 동일 Skill 재선택 cooldown
- 동일 실패 원인 반복 제한
- Goal phase progress watchdog
- 최대 Search/Investigate budget
- fallback 후 재진입 backoff

## 9.6 수락 Gate

선택된 행동은 다음 순서로 수락한다.

1. scorer ranking
2. post-processing 전환 비용
3. calibrated acceptability
4. OOD/abstain
5. asynchronous commit validation
6. resource reservation
7. Skill Start

---

# 10. 학습 데이터 생성 전략

## 10.1 데이터 계층

### Silver

- LLM 교사
- 절차적 규칙
- 자동 합성
- 낮은 비용, 높은 양
- 품질 가중치 낮음

### Gold

- 사람 시연
- 사람 선호 비교
- 복수 Annotator 합의
- 분쟁 adjudication
- Calibration과 Test에 우선 사용

### Live/DAgger

- 실제 정책 rollout
- 디자이너 개입
- 플레이어 로그
- 이상 행동 신고
- 모델이 실제로 방문한 상태

LLM과 절차적 생성기는 정답 원천이 아니라 데이터 공급원이다.

## 10.2 절차적 상황 생성

변수:

- 거리와 방향
- 가시성과 가림
- 소리 종류와 크기
- Belief source, age, confidence
- NPC 역할 속성
- 성격
- 관계
- 감정
- Goal/Intent
- 현재 Skill
- 최근 이벤트
- 주변 아군과 적군
- 자원 상태
- 퀘스트 제약
- target generation change
- reservation 경쟁

생성 방식:

- 유효 범위 랜덤
- 현실적 상관관계
- 희귀 상황 오버샘플링
- 경계값 집중
- OOD 상황 별도 생성
- 실제 플레이 분포 재가중
- Candidate miss를 유발한 상황 재생성

## 10.3 데이터 분할

행 단위 무작위 분할만 사용하지 않는다.

다음 단위로 전체 계열을 hold-out한다.

- 맵 또는 레이아웃 family
- 시야/소리 조합 family
- Goal/Intent sequence family
- Role–Personality 조합 family
- target 수와 modality 패턴
- 생성기 version 또는 template
- 특정 사건 sequence
- 신규 Skill 조합

필수 세트:

- Train
- Validation
- Calibration
- Test
- OOD Test
- Critical Safety Test

Calibration Set은 학습과 hyperparameter 선택에 사용하지 않는다.

## 10.4 데이터 Provenance

각 샘플에 기록:

- source type
- generator version
- LLM model/prompt version
- annotator IDs 또는 익명 그룹
- agreement
- scenario family
- map seed
- policy version
- candidate pipeline version
- Belief schema version
- label confidence
- adjudication status

---

# 11. LLM 교사 데이터

## 11.1 역할

LLM은 후보 행동을 평가하는 Silver Label 공급자다.

입력:

- Goal/Intent
- NPC 역할 속성
- 성격
- 관계
- 현재 Belief
- 최근 이벤트
- Candidate Set
- 절대 금지 조건

출력:

- 허용 가능한 후보 집합
- 후보 Ranking
- 모호성
- 안전 위반 후보
- 짧은 이유

## 11.2 품질 관리

- 복수 sampling 합의
- 프롬프트 변형
- 하드 제약 자동 검증
- Role/Goal별 행동 분포 검사
- 사람 Gold 샘플과 정기 비교
- 낮은 합의 샘플 가중치 감소
- LLM Teacher와 Utility Baseline의 불일치 수집
- LLM 단독 label을 Critical Test 정답으로 사용하지 않음

## 11.3 예시 출력

```json
{
  "acceptable_candidates": [2, 4],
  "ranking": [
    {"candidate_id": 4, "score": 0.91},
    {"candidate_id": 2, "score": 0.74}
  ],
  "ambiguous": true,
  "unsafe_candidates": [7],
  "label_confidence": 0.61
}
```

---

# 12. 사람 데이터와 DAgger

## 12.1 행동 시연 도구

- 상황과 Belief 요약
- Ground Truth는 별도 Debug 탭
- Goal/Intent
- Candidate Set
- 후보 target
- 선택 행동
- 복수 acceptable 선택
- 적절한 후보 없음
- 선택 이유
- Candidate miss 신고
- 현재 정책 행동 수정

## 12.2 선호 비교

- A 선호
- B 선호
- 동등
- 둘 다 부적절
- 판단 불가

평가 기준을 분리한다.

- 자연스러움
- 캐릭터 일관성
- 공정성
- 임무 적합성
- 게임플레이 재미

## 12.3 Annotator 합의

Gold Set 일부는 최소 2명 이상이 평가한다.

보고 항목:

- pairwise agreement
- 다중 라벨 overlap
- 역할/Goal별 agreement
- ambiguous rate
- adjudication rate

합의가 낮은 상태는 단일 정답 정확도에서 제외하거나 복수 acceptable label로 다룬다.

## 12.4 DAgger/Intervention Loop

```text
현재 정책으로 시뮬레이션 또는 플레이
→ 실제 방문 상태 수집
→ 디자이너가 잘못된 행동에 개입
→ 올바른 후보 또는 acceptable set 기록
→ 기존 데이터에 합침
→ 재학습 및 회귀 테스트
```

초기 합성 분포와 실제 정책 방문 분포의 차이를 줄이는 핵심 단계다.

## 12.5 Active Learning

우선 검수 대상:

- calibrated confidence가 낮음
- OOD score가 높음
- Candidate miss
- Utility Baseline과 모델이 크게 불일치
- 사람과 LLM이 불일치
- 신규 Role/Goal/Skill
- 반복 실패
- 실제 플레이 이상 행동

단순 top-1/top-2 gap만으로 검수 대상을 정하지 않는다.

---

# 13. 학습 및 비교 계획

## 13.1 Gate 0 — Candidate Pipeline

모델 학습 전에 다음을 통과해야 한다.

- Entity Target Recall
- Candidate Recall
- Mask 정확도
- Critical 후보 100% 보존
- 후보 누락 원인 로깅

이 Gate가 통과되지 않으면 Scorer 개선보다 Candidate Pipeline을 먼저 수정한다.

## 13.2 Gate 1 — Utility Baseline

동일 데이터 계약으로 소형 Utility Baseline을 구현한다.

기록:

- 구현 시간
- 튜닝 시간
- 규칙 수
- 시나리오별 성능
- 신규 Role/Goal 추가 시간
- fallback rate
- latency

## 13.3 Gate 2 — 행동 Ranking

손실:

- Pairwise Ranking Loss
- Listwise Ranking Loss
- multi-label acceptable loss
- candidate score regression
- optional action category auxiliary loss

여러 행동이 적절할 수 있으므로 단일 class accuracy만 최적화하지 않는다.

## 13.4 Gate 3 — 이벤트 시퀀스

V1:

- Event Buffer 8~16개
- 3~10초 window
- Temporal Attention/Pooling
- Skill 결과와 Goal phase transition 포함

Phase 2:

- Optional GRU
- event-buffer-only 모델과 ablation
- hidden lifecycle 회귀 테스트

## 13.5 Gate 4 — Calibration/OOD

Scorer를 고정한 후 Calibration Set에서 Calibrator를 학습한다.

평가:

- ECE
- Brier Score
- risk–coverage
- fallback rate
- OOD set
- role/goal worst group

## 13.6 Gate 5 — DAgger

실제 policy rollout에서 수집한 상태를 학습 데이터에 추가한다.

## 13.7 Gate 6 — 강화학습

PPO 등은 다음 조건 이후에만 검토한다.

- Candidate Recall Gate 통과
- Baseline 대비 기본 품질 확보
- Calibration/OOD 구현
- 안전 정책 유지
- Reward hacking 테스트
- Goal Authority와 Skill Executor 분리 유지

강화학습 적용 대상:

- 탐색 효율
- 거리 조절
- 엄폐 선택
- 협동
- 행동 타이밍
- Mission 성능 미세조정

---

# 14. 런타임 추론 및 실행 계약

## 14.1 Decision Request

```json
{
  "npc_id": "guard_013",
  "npc_generation": 4,
  "decision_id": 1821,
  "snapshot_world_time": 102.41,
  "deadline_world_time": 102.46,
  "goal_instance_id": "goal_91",
  "goal_revision": 12,
  "belief_revision": 370,
  "candidate_set_hash": "sha256:...",
  "model_version": "npc_policy_0.4.0",
  "schema_version": "2.0.0",
  "calibration_version": "0.2.0",
  "observation": {},
  "candidates": []
}
```

## 14.2 Target Handle

각 target은 다음을 포함한다.

- stable ID 또는 NetGUID
- generation
- target type
- snapshot position
- belief revision
- source
- confidence

Actor pointer만 저장하지 않는다.

## 14.3 Decision Response

```json
{
  "npc_id": "guard_013",
  "npc_generation": 4,
  "decision_id": 1821,
  "candidate_set_hash": "sha256:...",
  "selected_candidate_id": 47,
  "raw_score": 1.84,
  "calibrated_acceptability": 0.87,
  "ood_score": 0.08,
  "abstained": false,
  "parameters": {
    "duration": 2.0,
    "speed": 0.6
  }
}
```

## 14.4 결과 수락 순서

응답 도착 시:

1. NPC generation 일치
2. 최신 유효 decision ID인지 확인
3. deadline 미초과
4. model/schema/calibration version 일치
5. candidate set hash 일치
6. Goal instance와 revision 일치
7. target stable ID와 generation 일치
8. 최신 월드 상태로 `ValidateAtCommit`
9. 자원 원자적 예약
10. Skill Start

하나라도 실패하면 결과를 버리고, 이유를 로그하며 재판단 또는 fallback한다.

## 14.5 Stale 응답 정책

- 이전 decision보다 최신 요청이 이미 Commit됐다면 폐기
- Goal revision이 변경됐으면 폐기
- target generation이 변경됐으면 폐기
- deadline이 지났으면 폐기
- 현재 Skill이 긴급 상태로 바뀌었으면 폐기
- 폐기율을 runtime KPI로 추적

## 14.6 배치 추론

- 짧은 요청 수집 창
- NPC 우선순위 큐
- 동일 모델·Tensor shape 배치
- combat/critical deadline 우선
- 화면 밖 NPC 낮은 판단 빈도
- candidate count별 bucket batch
- preprocessing, queue, inference, commit 시간을 분리 측정

## 14.7 성능 Profile

성능 승인에는 다음 기준 하드웨어 정보를 반드시 기록한다.

- CPU/GPU
- 메모리
- Development/Shipping Build
- 추론 backend
- FP32/FP16/INT8
- batch size
- candidate count
- 활성 NPC 수
- 초당 Decision Request

### 초기 PC 프로토타입 예산

Reference PC는 프로젝트 시작 시 별도 명시한다.

부하 모델:

```text
30 Idle NPC × 1Hz
15 Alert NPC × 3Hz
 5 Combat NPC × 5Hz
-------------------
Typical 100 decisions/sec
Burst   250 decisions/sec for 1 second
```

잠정 목표:

- Batch inference p50 ≤ 2ms
- Batch inference p95 ≤ 6ms
- Batch inference p99 ≤ 12ms
- Request-to-Commit p50 ≤ 8ms
- Request-to-Commit p95 ≤ 20ms
- Request-to-Commit p99 ≤ 40ms
- Typical deadline miss < 0.1%
- Burst deadline miss < 1.0%

수치는 Reference Hardware가 확정된 뒤 조정한다. “프레임당 5~20 NPC”는 성능 계약으로 사용하지 않는다.

## 14.8 멀티플레이 권위

권장:

- 서버가 Perception, Belief, Goal, 추론, Commit을 소유
- 클라이언트는 선택된 Skill, target NetGUID, 파라미터, server start time, 결과를 복제받음
- 클라이언트 추론은 디버그 또는 cosmetic prediction만 허용
- 피해, 이동 권한, 아이템, 관계, Goal은 서버만 변경
- 서버와 클라이언트가 각각 독립적으로 정책 결정을 내려 경쟁하지 않음

## 14.9 모델 배포

- 모델 hash
- schema version
- Skill Registry version
- Goal schema version
- calibration asset
- normalization asset
- fallback baseline version
- supported precision/backend

패키지 시작 시 호환성을 검증한다.

---

# 15. LLM 런타임 통합

## 15.1 권장 책임

Tactical Policy 출력:

- 대화 행위
- target
- 표현용 tone
- 강도
- allowed facts

LLM 출력:

- 실제 대사
- 말투 변형
- 대화 문맥 연결

모델 또는 LLM이 표현용 감정을 제안해도 권위 있는 감정·관계 상태는 변경하지 않는다.

## 15.2 금지 사항

- 공격 실행
- 아이템 지급
- 퀘스트 완료
- 관계 직접 변경
- 감정 상태 누적 변경
- 문 잠금 해제
- 게임 경제 변경
- 영구 기억 직접 생성
- 서버 권한 변경

모든 LLM 출력은 구조와 허용 사실 검증을 통과해야 한다.

---

# 16. 디버깅 및 관찰 가능성

## 16.1 NPC Decision Inspector

- Ground Truth와 Belief를 별도 표시
- Goal/Intent와 revision
- Event Buffer
- Perceived Entity 16개
- target source/age/confidence
- raw Candidate Universe
- Mask 후보와 이유
- Candidate Recall miss 원인
- Utility Baseline 점수
- Neural raw score
- 전환 비용
- calibrated acceptability
- OOD score
- abstain/fallback 이유
- decision ID
- deadline
- stale discard 여부
- target generation
- reservation 결과
- Skill failure taxonomy
- model/schema/calibration version
- optional GRU lifecycle state

## 16.2 결정 로그

```json
{
  "timestamp": 102.41,
  "npc_id": "guard_013",
  "decision_id": 1821,
  "goal_revision": 12,
  "candidate_set_hash": "sha256:...",
  "candidate_count": 84,
  "selected_candidate": 47,
  "raw_score": 1.84,
  "calibrated_acceptability": 0.87,
  "ood_score": 0.08,
  "fallback": null,
  "commit_validation": "passed",
  "reservation": "cover_slot_7",
  "result": "started"
}
```

## 16.3 이상 행동 신고

- 최근 10~30초 Event Buffer
- Belief Snapshot
- Ground Truth Debug Snapshot
- Goal/Intent
- Candidate Set
- 모델 및 Baseline 결과
- 사람 기대 행동
- Candidate miss 여부
- decision/target generation
- stale 응답 기록
- Replay Seed
- 영상 또는 스크린샷

---

# 17. 테스트 요구사항

## 17.1 Candidate Pipeline

- Entity Target Recall
- Candidate Recall
- Critical 후보 100% 보존
- NoTarget 후보
- Goal scope
- Skill–Target compatibility
- 잘못된 hard mask
- 272개 패딩/Mask
- candidate hash 안정성

## 17.2 Belief와 정보 누출

- 벽 뒤 target Ground Truth 이동 시 Policy Tensor 불변
- 마지막 목격 위치 TTL
- 잘못된 sound attribution 차단
- 체력/무기 추정 confidence
- source/age/confidence
- Shared Knowledge 전파
- Ground Truth Buffer와 Policy Buffer 분리

## 17.3 Goal/Intent

- Investigate → Search → Return
- Warn → Escalate → Resolve
- Goal timeout
- Goal interrupt
- Save/Load
- Goal revision 중 stale response 폐기
- 복귀 target 소실

## 17.4 Skill Executor

- Commit 직전 target 사망
- target generation 변경
- 경로 차단
- 엄폐 슬롯 경쟁
- reservation timeout
- Suspend/Resume
- failure taxonomy
- resource release
- 모든 후보 무효
- Skill Start 직전 권한 변경

## 17.5 Memory Lifecycle

### V1 Event Buffer

- save/load
- LOD off/on
- teleport
- event TTL
- ordering
- duplicate event ID
- buffer overflow

### Optional GRU

- Spawn reset
- model hot swap reset
- schema 변경 reset
- save/load rebuild
- reconnect
- burn-in
- hidden hash compatibility

## 17.6 Calibration/OOD

- candidate count 변화
- unseen Role/Skill ID
- feature range 위반
- OOD scenario
- threshold별 fallback
- role/goal worst group
- calibrator version mismatch

## 17.7 비동기 및 멀티플레이

- out-of-order response
- deadline 초과
- 이전 decision response
- target generation mismatch
- candidate hash mismatch
- 서버 권위
- client prediction 불일치
- replication late join
- server reconnect

## 17.8 시나리오

1. 뒤쪽 작은 발소리
2. 뒤쪽 큰 총성
3. 시야 안에서 무기 꺼냄
4. 우호 플레이어 제한 구역 진입
5. 적대 플레이어 원거리 관찰
6. 혼자 다수 적 발견
7. 겁이 많은 NPC와 용감한 NPC
8. 반복 경고 무시
9. NPC 치료 후 접근
10. target sight lost
11. 여러 소리
12. 조사 중 path 차단
13. 공격 중 Goal 변경
14. OOD Role 속성
15. 모델 timeout
16. 후보 누락
17. 엄폐물 동시 선점
18. 모델 hot swap
19. Save/Load
20. 50 NPC Typical/Burst

---

# 18. 평가 지표

## 18.1 Candidate Pipeline

- Entity Target Recall
- Any-Acceptable Candidate Recall
- Full Acceptable Recall
- Critical Candidate Recall
- Candidate miss 원인 비율
- 평균/최대 candidate count
- Candidate Generator latency

## 18.2 모델 Ranking

Candidate가 존재하는 조건부 지표와 전체 end-to-end 지표를 분리한다.

- Top-1 acceptable rate
- Top-3 acceptable inclusion
- Pairwise Ranking accuracy
- NDCG
- 행동별 Precision/Recall
- 역할/Goal별 worst-group
- 행동 다양성
- Utility Baseline 대비 승률

## 18.3 Calibration/OOD

- ECE
- Brier Score
- risk–coverage
- OOD recall/precision
- abstain rate
- fallback rate
- false accept
- unnecessary abstain

## 18.4 시퀀스와 Goal

- 행동 전환 빈도
- 평균 Skill 지속 시간
- Goal 완료율
- Goal 단계 정체율
- 조사→수색→복귀 완료율
- 경고→후속 행동 일관성
- 반복 실패율
- target switch
- 실패 후 회복률

## 18.5 런타임

- decisions/sec
- preprocessing p50/p95/p99
- queue wait p50/p95/p99
- inference p50/p95/p99
- request-to-commit p50/p95/p99
- deadline miss
- stale discard
- reservation conflict
- fallback latency
- 모델 메모리와 activation

## 18.6 플레이테스트와 제작 효율

- 블라인드 자연스러움 선호
- 캐릭터 일관성
- 공정성
- 재미
- 이해 불가능 행동
- 반복 체감
- Baseline 대비 제작 시간
- 신규 Role 데이터 제작 시간
- 신규 Skill 구현·재학습 시간
- 시나리오 추가 시 코드 변경량

---

# 19. 데이터 스키마

## 19.1 Observation

```json
{
  "schema_version": "2.0",
  "npc_self_state": {},
  "personality_attributes": {},
  "role": {
    "role_id": "guard",
    "attributes": {}
  },
  "goal_intent": {
    "goal_instance_id": "goal_91",
    "goal_revision": 12,
    "intent_phase": "orient"
  },
  "emotion_read_only": {},
  "relationship_read_only": {},
  "perceived_entities": [
    {
      "stable_id": "player_1",
      "generation": 4,
      "source": "LastSeenMemory",
      "observed_at": 101.2,
      "age": 1.21,
      "confidence": 0.72,
      "belief": {}
    }
  ],
  "recent_events": [],
  "current_skill": {},
  "constraints": {},
  "world_context": {}
}
```

Ground Truth Debug 데이터는 이 구조 밖에 저장한다.

## 19.2 Candidate

```json
{
  "candidate_id": 47,
  "skill_id": "investigate",
  "skill_version": 2,
  "target_handle": {
    "stable_id": "sound_21",
    "generation": 1,
    "target_type": "sound_event"
  },
  "compatibility": {
    "goal_allowed": true,
    "target_type_allowed": true
  },
  "hard_mask": false,
  "mask_reason": null,
  "base_parameters": {
    "duration": 4.0,
    "speed": 0.6
  }
}
```

## 19.3 Decision Request/Result

Request는 다음을 포함한다.

- NPC ID/generation
- decision ID
- snapshot/deadline time
- Goal instance/revision
- Belief revision
- candidate set hash
- model/schema/calibration version
- Observation
- Candidate Set

Result는 다음을 포함한다.

- 동일 식별자
- selected candidate
- raw score
- calibrated acceptability
- OOD
- abstain
- 제한된 파라미터

감정·관계 Delta는 포함하지 않는다.

## 19.4 Skill Result

```json
{
  "decision_id": 1821,
  "skill_id": "investigate",
  "status": "failed",
  "failure_reason": "PathUnavailable",
  "started_at": 102.42,
  "ended_at": 104.11,
  "target_generation": 1,
  "reservation_id": null,
  "resumability": "Restartable"
}
```

---

# 20. 모델·데이터·Runtime 버전 관리

필수 식별자:

- model version/hash
- Observation Schema
- Candidate Schema
- Belief Schema
- Event Schema
- Goal/Intent Schema
- Skill Registry
- normalization
- calibration
- Utility Baseline
- dataset
- scenario generator
- LLM prompt/model
- training code commit
- inference runtime/backend
- precision
- server build

호환성 규칙:

- Schema 불일치 시 모델 로드 거부
- Skill Registry 변경 시 Candidate 및 Calibration 재검증
- Goal Schema 변경 시 데이터 회귀 테스트
- 모델 hot swap 시 Optional GRU hidden 초기화
- Calibration asset 누락 시 Neural Policy를 authoritative하게 사용하지 않음
- Baseline version을 모델 배포와 함께 기록

---

# 21. 실패 대응 및 Fallback

## 21.1 Fallback 우선순위

1. 현재 Skill이 안전하고 유효하면 유지
2. Utility Baseline
3. Goal별 안전 기본 Skill
4. 최소 안전 정책
5. Idle

## 21.2 Fallback 원인

- low calibrated confidence
- OOD
- model timeout
- model load failure
- stale response
- target invalid
- Goal changed
- reservation conflict
- all candidates masked
- schema mismatch
- calibration missing

## 21.3 최소 안전 정책

- 치명적 위험에서 긴급 회피
- 공격 불가 시 엄폐 또는 이탈
- 경로 없음이면 이동 취소
- target 없음이면 안전한 현재 행동 유지
- 권한 없음이면 상태 변경 행동 금지

최소 안전 정책은 자연스러운 NPC 전체를 구현하는 Behavior Tree가 아니라 시스템 보호 장치다.

## 21.4 Fallback KPI

- 원인별 발동률
- 역할/Goal별 발동률
- 모델 버전별 변화
- 플레이어 체감 영향
- fallback 후 정상 정책 복귀 시간

---

# 22. 구현 마일스톤

## Phase 0 — 기술 검증

### 범위

- NPC 1종
- Player 1명
- Goal 2종
- Skill 5개
- Target 최대 4개
- Perception/Belief 분리
- Event Buffer
- Candidate Universe와 Recall
- Utility Baseline
- 단순 MLP Scorer
- Mock 비동기 요청/Commit 재검증
- 모델은 감정·관계를 읽기만 함
- GRU 없음

### 완료 조건

- Candidate Recall 100% on Phase 0 Critical Set
- Ground Truth 누출 테스트 통과
- Goal lifecycle 동작
- Baseline과 Neural 동일 Skill/후보 사용
- stale target 결과 폐기
- Skill Commit 재검증
- 후보별 점수와 miss 원인 표시
- 모델 실패 시 Baseline fallback

## Phase 1 — V1 프로토타입

### 범위

- Skill 16개
- Entity/Target 16개
- Candidate padded max 272
- Entity Encoder
- Event Encoder
- Goal/Intent Encoder
- Calibration/OOD
- 자원 예약
- failure taxonomy
- 서버 권위 기본 계약
- 절차적·LLM Silver
- Human Gold
- Decision Inspector

### 완료 조건

- 전체 Candidate Recall 99.5% 이상
- Critical Candidate Recall 100%
- 금지 행동 Commit 0건
- 숨은 정보 누출 0건
- 행동 진동 기준 이하
- Calibration 목표 충족
- 30 NPC 기능 테스트
- Utility Baseline 대비 블라인드 평가 또는 제작 효율 이점 확인

## Phase 2 — 데이터 및 품질

### 범위

- DAgger/Intervention
- 실제 플레이 로그
- Scenario-family hold-out
- 사람 합의 측정
- 장기 기억 검색
- Optional GRU ablation
- Role/Goal worst-group
- Candidate Retriever는 필요할 때만
- 멀티플레이 회귀 테스트

### 완료 조건

- 실제 방문 상태에서 품질 향상
- OOD fallback 안정
- 신규 Role 속성 조합 평가
- Optional GRU가 Event Buffer 대비 명확한 이득이 있을 때만 채택
- 자동 회귀 파이프라인

## Phase 3 — 강화학습 및 협동

### 범위

- PPO 또는 대안
- 다수 NPC 협동
- 역할 분담
- 엄폐 경쟁
- 지원 요청
- Goal 성능 미세조정

### 완료 조건

- 보상 해킹 테스트
- Baseline/모방학습 대비 임무 성능 개선
- 캐릭터 일관성 저하 없음
- 안전·Calibration 악화 없음

## Phase 4 — 프로덕션

### 범위

- 플랫폼 최적화
- 배치 추론
- FP16/INT8
- 서버 부하
- 네트워크 복제
- 세이브/로드
- hot swap/rollback
- 운영 대시보드
- 콘텐츠 제작 워크플로

### 완료 조건

- Reference Hardware p50/p95/p99 예산 충족
- 모델·Calibration·Baseline 롤백
- QA 재현
- 기존 Skill과 속성 범위의 Role 프리셋은 엔진 코드 변경 없이 제작 가능
- 신규 Skill은 코드·데이터·재학습 절차가 문서화됨

---

# 23. 권장 팀 역할

## 게임플레이/AI 프로그래머

- Perception/Belief
- Goal/Intent
- Skill Executor
- Candidate Generator
- Utility Baseline
- 자원 예약
- Commit 재검증
- Debug Inspector

## ML 엔지니어

- Scorer
- Event Encoder
- Calibration/OOD
- 데이터 분할
- Candidate Recall 분석
- 학습/평가
- 모델 최적화
- Optional GRU lifecycle

## 서버/네트워크 프로그래머

- 서버 권위
- Decision ID
- target generation
- 복제
- late join/reconnect
- deadline/queue
- authoritative Commit

## AI/게임 디자이너

- Goal/Intent 수명주기
- Role 속성
- Skill 의미
- Gold Label
- 선호 비교
- Baseline 곡선
- 품질 기준

## 테크니컬 디자이너

- Scenario Generator
- DAgger 도구
- Candidate miss 시각화
- Replay
- 자동 테스트
- 데이터 검수

## QA

- Ground Truth 누출
- Goal 일관성
- stale 응답
- reservation 경쟁
- 멀티플레이 권위
- 모델/Calibration 회귀
- 성능 스트레스

---

# 24. 주요 위험과 대응

## 위험 1 — Candidate Generator가 숨은 Behavior Tree가 됨

대응:

- 선호 규칙 금지
- 최대 후보 평가
- Candidate Recall Gate
- candidate miss 원인 로깅
- reducer 도입 전 프로파일링
- Critical Recall 100%

## 위험 2 — 장기 행동이 흔들림

대응:

- Goal/Intent Authority
- 단계 progress와 timeout
- Event Buffer
- 반복 budget
- Goal 단위 회귀 테스트

## 위험 3 — 치팅 AI

대응:

- Belief Schema
- source/age/confidence
- Ground Truth Buffer 분리
- Hidden Information Leakage Test
- sound attribution confidence

## 위험 4 — LLM·생성기 편향 압축

대응:

- Silver/Gold/Live 분리
- scenario-family hold-out
- 사람 합의
- DAgger
- actual play worst-case
- provenance

## 위험 5 — 모델이 Baseline보다 낫지 않음

대응:

- 동일 파이프라인 비교
- 블라인드 평가
- 제작 시간 측정
- Baseline fallback 유지
- 명확한 승격 Gate

## 위험 6 — 신규 Role/Skill 기대 과장

대응:

- 속성 기반 Role
- zero-shot 비목표
- 신규 Skill 절차 명시
- 재학습/Calibration 요구
- worst-group 평가

## 위험 7 — GRU hidden 상태 불일치

대응:

- V1 Event Buffer
- GRU 선택 기능
- reset/rebuild 정책
- model hash
- save/load/hot swap 테스트

## 위험 8 — 잘못된 confidence

대응:

- raw score와 confidence 분리
- Calibration Set
- OOD
- risk–coverage
- 역할/Goal별 threshold
- fallback KPI

## 위험 9 — 감정·관계 피드백 루프

대응:

- V1 모델 read-only
- 사건 기반 idempotent 갱신
- clamp/decay
- authoritative mutation 금지

## 위험 10 — stale 추론과 자원 경쟁

대응:

- decision ID/deadline
- target generation
- Goal revision
- candidate hash
- Commit 재검증
- atomic reservation
- 서버 권위

---

# 25. MVP 권장 범위

## NPC Role

- Guard
- Civilian
- Companion

Role은 속성 벡터와 이미 학습된 ID를 함께 사용할 수 있다.

## Goal

- Idle/Patrol
- Investigate Disturbance
- Enforce Boundary
- Basic Combat/Disengage

## 입력

- NPC 자기 상태
- Goal/Intent
- Perceived 위치·거리·방향
- 시야
- 소리
- source/age/confidence
- 관계·감정 read-only
- 성격
- 최근 Event Buffer
- 현재 Skill/결과

## Skill

- Idle
- ContinueCurrentAction
- LookAt
- TurnTo
- Approach
- KeepDistance
- RetreatFrom
- Investigate
- SearchArea
- Greet
- Warn
- CallForHelp
- TakeCover
- Flee
- Attack
- Follow

## 데이터

- 절차적 Silver 20,000개 이상
- LLM Silver
- Human Gold 1,000~3,000개
- 복수 Annotator Gold Subset
- 실제 rollout/DAgger
- 시나리오 계열 Hold-out
- Calibration Set
- OOD Set
- Critical Set
- 회귀 시나리오 100개 이상

## 성공 기준

- 전체 Candidate Recall 99.5% 이상
- Critical Candidate Recall 100%
- Target Recall 99.5% 이상
- Top-3 acceptable rate 90% 이상 목표
- 하드 제약 위반 Commit 0건
- Ground Truth 누출 0건
- 행동 진동 기준 충족
- Goal sequence 완료율 기준 충족
- Calibration/OOD 목표 충족
- Baseline 대비 자연스러움, 일반화 또는 제작 효율 중 명확한 이점
- 모델 실패 시 안전한 fallback
- Reference Hardware의 p50/p95/p99 예산 충족
- 신규 Role 프리셋은 평가와 필요 시 재학습을 거침
- 신규 Skill은 코드·Registry·데이터·재학습 절차를 거침

---

# 26. 최종 권장 구현 순서

1. Ground Truth와 Belief 데이터 구조 분리
2. source/age/confidence/TTL 계약 정의
3. Goal/Intent Authority 구현
4. Skill Interface와 failure taxonomy 구현
5. 자원 예약과 Commit 재검증 구현
6. Event Buffer 구현
7. Entity/Target 16개 계약 정의
8. Candidate Universe와 272개 Mask 구현
9. Candidate Recall 도구와 miss Inspector 구현
10. Utility Baseline 구현
11. 결정 로그와 Replay 구현
12. Mock 비동기 Decision ID/deadline 처리
13. Phase 0 MLP Scorer 연결
14. Ground Truth 누출 및 stale 결과 테스트
15. 절차적 Silver 데이터 생성
16. LLM Silver 파이프라인
17. Human Gold/선호 도구
18. Scenario-family 분할
19. Entity/Event/Goal Encoder 추가
20. Calibration/OOD/Abstain 추가
21. 서버 권위와 복제
22. DAgger/Intervention
23. 성능 p50/p95/p99 측정
24. 필요할 때만 Candidate Retriever
25. 필요할 때만 Optional GRU
26. 필요할 때만 강화학습
27. 모델·Calibration·Baseline hot swap/rollback
28. 프로덕션 운영 대시보드

---

# 27. 핵심 결론

이 시스템의 성공 여부는 신경망 아키텍처만으로 결정되지 않는다.

프로덕션에서 더 중요한 선행 조건은 다음과 같다.

1. NPC가 실제로 아는 정보만 모델에 전달하는가
2. 적절한 행동과 target이 Candidate Set에 들어오는가
3. 장기 Goal을 코드가 안정적으로 유지하는가
4. 비동기 결과를 Commit 시점에 다시 검증하는가
5. 모델이 불확실할 때 안전하게 abstain하는가
6. Utility Baseline보다 실제 이점이 있는가
7. 실제 플레이 분포를 데이터에 계속 반영하는가

최종 책임 분리는 다음과 같다.

```text
코드와 데이터
- Mission Goal / Intent
- Belief State
- Skill 실행
- 자원 예약
- 안전과 권한
- 감정·관계 상태 전이
- 비동기 Commit
- 서버 권위

학습 모델
- 현재 Goal 안의 전술 후보 Ranking
- target 선택
- 제한된 행동 파라미터
- 대화 행위와 표현 톤

평가·운영
- Candidate Recall
- Baseline 비교
- Calibration/OOD
- DAgger
- p50/p95/p99
- 회귀 및 롤백
```

이 구조는 전통적인 로직을 완전히 제거하는 접근이 아니다. **상황별 선호 분기를 학습 모델로 옮기면서도, 장기 상태·공정성·실행 안정성·멀티플레이 권위는 명시적 시스템으로 유지하는 접근**이다.
