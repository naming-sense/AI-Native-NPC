# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# AI Native NPC를 만드는 순서
## 데이터 준비부터 모델 학습·Unreal 검증까지 설명하는 구현 계획

- 문서 버전: **v0.4.15**
- 개정일: 2026-08-12
- 현재 상태: **소리를 듣고 조사 Goal을 시작하는 Phase 3A는 완료됐다. 다음 Phase 3B는 기존 Target·Candidate·Feature·Utility·Commit·Skill Core를 production Goal 경로로 연결한다.**
- 주 독자: **기획자, 사업 책임자, 새로 합류한 개발자, ML·Data·Gameplay AI·Server·Unreal NNE·QA·Release 담당자**
- 설명 범위: **구현 순서, 담당 팀, 모델 구조, 학습 데이터 생성, 학습 설정, Unreal 검증과 최종 승인 절차**
- 제품 요구사항: [AI Native NPC 제품 요구사항](requirements.md)
- 세부 기술 요구사항: [AI Native NPC 세부 기술 요구사항](technical-requirements.md)
- 계약 부록: [AI Native NPC Contract Appendices](contract-appendices.md)

세부 기술 요구사항은 게임 실행 중 동작과 안전 규칙을 정한다. 계약 부록은 정확한 ID·모델 입출력 크기·승인 기준을 정한다. 이 문서는 구현 순서와 담당 팀, 산출물, 검증 방법을 정한다.


<!-- BEGIN GOAL GAMEPLAY SEMANTICS V1 STATUS -->
### Bounded Goal gameplay authority status

- Goal Registry: `1.1.0` / SHA-256 `d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e`
- `GuardPhase0` bounded semantics authority: **PASS**
- Authority scope: 9 executable unique guards, 3 provider-unavailable unique guards, 12 executable transition bindings, 2 staged effects, 5 production executable Skills
- Gameplay Goal FSM: **HOLD** — complete guard catalog, other Goals, full Utility/Commit/Skill-result progression, arbitration/save archive, and product release are not claimed by this bounded authority PASS.
<!-- END GOAL GAMEPLAY SEMANTICS V1 STATUS -->

---

<a id="document-guide"></a>
# 0. 이 문서는 무엇을 설명하는가

## 0.1 한 줄 설명

이 문서는 AI Native NPC를 어떤 순서로 구현하고, 학습 데이터를 만들고, 모델을 학습하고, Unreal에서 검증할지 설명한다.

## 0.2 전체 구현 흐름

```text
게임 상황을 저장하거나 가상 상황을 생성한다
→ 허용 가능한 행동과 선호 순서를 표시한다
→ 학습 데이터를 검사하고 분리한다
→ 모델을 학습한다
→ ONNX로 내보낸다
→ Unreal에서 같은 결과가 나오는지 검사한다
→ 안전·품질·성능 기준을 통과한 모델만 배포한다
```

## 0.3 먼저 알아둘 말

| 이름 | 쉬운 뜻 |
|---|---|
| Phase | 구현 작업을 순서대로 묶은 단계 |
| Goal | NPC가 지금 이루려는 목적 |
| Knowledge | NPC가 관측하거나 전달받아 보관하는 정보. 코드 이름은 `Belief` |
| Target의 종류와 식별 정보 | NPC가 행동을 적용할 대상의 종류와 정확한 대상을 나타내는 정보. 코드 이름은 `Typed Target` |
| Skill | NPC가 실제로 실행할 수 있는 행동 |
| Candidate | 현재 Goal에서 가능한 `Skill + Target` 조합 |
| Utility | 사람이 정한 점수식으로 Candidate 순위를 매기는 기준 로직 |
| Neural 모델 | 학습 데이터로 Candidate 선호 순위를 배우는 모델 |
| Silver | 절차 생성과 Teacher LLM으로 만드는 낮은 가중치의 학습 예시 |
| Gold | 사람이 검토한 높은 신뢰도의 학습·평가 예시 |
| DAgger | 모델 실행 중 디자이너가 수정한 상황을 다시 학습하는 데이터 |
| OOD | 학습 데이터와 다른 낯선 상황을 감지하는 기준 |
| Calibration | 모델 점수를 믿을 수 있는 확률로 바꾸는 과정 |
| ONNX·NNE | 학습한 모델을 저장하는 파일 형식과 Unreal에서 그 모델을 실행하는 기능 |
| Runtime | 게임을 실행하는 동안 실제 판단과 행동을 처리하는 코드 |
| fixture | 사람이 결과를 미리 정해 둔 테스트 입력 |
| Commit | 선택 결과를 최신 게임 상태로 다시 검사하고 실행을 확정하는 서버 작업 |
| Model Bundle | 모델과 실행에 필요한 계약·정규화·신뢰도 기준을 묶은 배포 단위 |

## 0.4 현재 상태 표시

| 상태 | 뜻 |
|---|---|
| PASS | 해당 범위의 구현과 검증이 통과된 상태 |
| RED | 실패하는 테스트가 준비됐고 구현이 필요한 상태 |
| HOLD | 먼저 필요한 기능이나 증거를 기다리는 상태 |
| NO-GO | 최종 제품 승인 조건을 충족하는 작업이 남은 상태 |

## 0.5 목차

1. [이 계획이 정하는 것](#implementation-scope)
2. [무엇을 어떤 순서로 만들 것인가](#phase-owner)
3. [NPC가 행동을 고르는 모델을 어떻게 만들 것인가](#reference-model)
4. [학습 데이터를 만들고 모델을 준비하는 순서](#ml-pipeline)
5. [어떤 데이터로 몇 번 학습할 것인가](#training-config)
6. [구현 명령을 어떤 순서로 실행하는가](#implementation-cli)
7. [검증된 모델 묶음을 어떻게 만드는가](#release-pipeline)
8. [언제 구현 완료로 승인하는가](#final-approval)

---

<a id="implementation-scope"></a>
# 1. 이 계획이 정하는 것

구현 팀은 이 계획의 순서에 따라 Runtime, 데이터, 모델과 검증 도구를 만든다. 각 작업은 담당 팀, 산출물과 완료 증거를 가진다.

기계 계약과 세부 기술 요구사항이 정확한 동작을 정한다. 구현은 잠긴 계약 버전과 Hash를 사용한다. 계약 변경은 YAML 원본과 생성 산출물 갱신부터 시작한다.

---

<a id="phase-owner"></a>
# 2. 무엇을 어떤 순서로 만들 것인가

## 2.1 두 단계로 구현한다

1단계(Phase 0)는 NPC가 상황을 인식하고 규칙 기반 Utility로 행동을 고른 뒤 Commit하는 작은 흐름을 연결한다. 이 단계에서 학습에 사용할 게임 상황도 저장한다.

2단계(Phase 1)는 전체 Dataset, Neural 모델, OOD, Calibration과 배포 승인 기준을 적용한다. 각 단계는 실제 Runtime 경로와 테스트 증거로 완료한다.

현재 구현은 보스 공격 패턴의 안전 Core와 deterministic Phase 0 Core를 완성했다. 일반 NPC는 소리를 듣고 조사 Goal을 시작하는 Phase 3A와 5개 Skill 실행기를 구현했다. Target Slotter, Candidate Builder, Feature Builder, Utility Selection과 Commit Coordinator의 순수 Core도 구현돼 있다. Phase 3B는 이 Core를 실제 Goal Host에 연결한다.

| 기능 | 현재 상태 |
|---|---|
| 일반 NPC의 전체 판단 흐름 | Phase 3A 완료. Phase 3B인 Goal-owned Target→Candidate→Utility→Commit→Skill-result 연결은 다음 작업 |
| Goal 규칙 데이터와 Unreal 전달 | 완료(PASS). Goal Registry `1.1.0`과 consumer sync 검증 |
| Goal 전환과 Timer 실행 코드 | pure Contract Dispatcher·Timer Core·Unreal Timer Core, exact Pawn/Controller Goal host, generated initial `IdleObserve/Observe`, production Hearing→`InvestigateDisturbance/Orient`와 one-shot timer 구현. 나머지 guard/effect provider와 전체 progression은 HOLD |
| 일반 NPC Knowledge와 Target Actor binding | production Perception Knowledge, exact Handle/Revision/Actor binding, exact-one identity와 sight-loss invalidation 구현. Knowledge `6/6` PASS |
| 일반 NPC StateTree 시작 경계 | private one-shot committed capability, authored handoff StateTree와 task-entry exact-once consume 구현. exact-one Executor는 5개 V1 Skill을 실행한다. 행동별 focused PASS, broad `134/134`, Data Validation `291/0/0`. Goal-owned Skill Commit authority와 완료→Goal event는 HOLD |
| 보스 패턴 검사·규칙 기반 선택·Commit | C++ 안전 Core 구현. 테스트 `31/31` PASS |
| 보스 StateTree·Pawn·AIController 연결 | 구현과 저장 에셋 검증 PASS |
| Commit 뒤 보스 StateTree 시작 | fixture 기반 `2/2`, 관련 보스 테스트 `53/53` PASS |
| 실제 보스 패턴 목록·선택 시작 조건·전투 효과 | 구현 전 |
| 학습 Dataset·AI 모델·ONNX·OOD·Calibration | Decision Record v2 capture/replay와 C++↔Python Golden validator는 Core PASS. 실제 대량 Dataset·Teacher·학습 모델·ONNX·OOD·Calibration은 구현 전 |

### 2.1.1 1단계: 작은 NPC 판단 흐름을 연결한다 (`Phase 0`)

이 단계는 경비 NPC 하나가 상황을 인식하고 규칙 기반 행동을 선택해 실행하는 흐름을 만든다.

범위:

- NPC Profile 1개: Guard
- Goal 2개: IdleObserve, InvestigateDisturbance
- 실행 Skill 5개: Idle, TurnTo, Approach, Investigate, SearchArea
- `ContinueCurrentAction` control candidate
- Target Kind: Entity, SoundEvent, LastKnownPosition, Waypoint, NoTarget
- Event Buffer, Target Slotter, 272 layout, Utility Baseline, 단순 Neural Scorer
- Single-player 서버 권위 형태의 GameThread Commit

완료 조건:

- Perception→Utility Baseline→Commit/Fallback 경로가 재현 가능한 Runtime 테스트를 통과한다.
- Capture record, 272 feature layout, score·parameter output이 Schema·Golden parity를 통과한다.
- Phase 0 증거와 남은 Runtime Gate를 [최종 승인 체크리스트](#final-approval)에 기록한다.

<a id="phase-3a"></a>
#### 2.1.1.1 소리를 듣고 조사 Goal을 시작한다 (Phase 3A — 완료)

Phase 3A는 `IdleObserve/Observe`에서 유효한 소리를 받아 `InvestigateDisturbance/Orient`를 한 번 활성화한다.

```text
Perception Hearing
→ Knowledge 저장
→ 현재 revision·Sound handle·X/Y/Z 위치 재확인
→ 새 Goal·Timer 준비
→ 기존 Idle/TurnTo와 대기 중인 Decision 정리
→ InvestigateDisturbance/Orient 공개
```

현재 구현은 다음 경계를 닫는다.

- exact Pawn·Controller·Knowledge·GoalTimer·SkillHandoff·SkillExecutor assembly
- generated `GuardPhase0` initial Goal
- 오래된 소리, 위치 변경, 잘못된 대상, 중복 event와 Pump 재진입 거부
- 새 Goal 준비 실패 시 기존 Goal·Skill·Decision 보존
- Host·Timer·Knowledge 제거와 재등록 시 이전 Timer·Runtime·callback 폐기
- ID 최댓값 뒤 재사용 금지와 새 lease 발급 실패 시 기존 lease 보존
- `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea` production 실행

최종 증거는 Contract `39/39`, GoalFsm `23/23`, Knowledge `6/6`, shipping `10/10`, broad `134/134`, Data Validation `291 assets / 0 errors / 0 warnings`다. Round 6 manifest는 관련 파일 `116/116`을 고정했고 좁은 독립 재검토는 문제 `0`으로 통과했다.

Skill Registry `execution_semantics_v1`은 5개 Skill의 실행 의미를 소유한다. `TurnTo`는 5°를 0.10초 유지한다. `Approach`는 preferred distance 안에 들어간다. `Investigate`는 preferred distance와 15°를 0.50초 유지한다. `SearchArea`는 world-axis 고정 9점을 순회한다. 이동 행동은 완전한 Nav path만 허용한다. server Timer는 0.05초 간격으로 상태를 평가한다.

<a id="phase-3b"></a>
#### 2.1.1.2 목표에 맞는 행동을 고르고 다음 단계로 진행한다 (Phase 3B — 다음 작업)

Phase 3B는 현재 Goal이 Target과 Skill을 고르고 실행 결과를 다음 Goal 단계로 연결한다.

```text
Goal
→ Knowledge
→ Goal-owned Target resolver
→ Target Slotter
→ Candidate Builder
→ Decision Feature Builder
→ Utility Selection
→ Decision Commit Coordinator
→ StateTree handoff와 Skill Executor
→ typed Skill result
→ Goal Runtime
```

기존 Core와 연결 상태:

| 부품 | 현재 상태 | Phase 3B 작업 |
|---|---|---|
| Goal-owned home·disturbance Target | Host 내부 capture 구현 | 현재 Goal·phase용 resolver로 공개하고 Target Slotter 입력에 연결 |
| `FTargetSlotter` | 순수 Core 구현 | 현재 Knowledge와 Goal-owned Target을 production 입력으로 제공 |
| `FCandidateBuilder` | 272행 Hard Mask Core 구현 | generated phase별 허용 Skill과 현재 실행 조건을 production fact로 제공 |
| `FDecisionFeatureBuilder` | Candidate와 Feature 동시 확정 Core 구현 | 실제 Goal·Knowledge·Event Feature를 채워 immutable Snapshot 생성 |
| `FUtilitySelection` | 결정론적 선택 Core 구현 | generated `GuardPhase0UtilityV1` profile로 호출 |
| `FDecisionCommitCoordinator` | 재검사·중복 방지 Core 구현 | Goal Host의 concrete `IDecisionCommitAuthority`에 연결 |
| StateTree handoff와 5-Skill Executor | 실행 구현 | Commit 성공 때만 한 번 사용할 수 있는 실행 권한 발행 |
| Skill result sink | Executor 내부 발행 구현 | Goal Host에 exact sink 설치 후 typed Goal event로 변환 |

Phase 3B는 다음 순서로 구현한다.

1. **Goal-owned Target 해결:** `AINativeNPCGoalHostComponent`의 private authority가 현재 Goal token에 맞는 disturbance position과 home Waypoint를 반환한다.
2. **판단 Snapshot 구성:** Host가 `FTargetSlotter`, `FCandidateBuilder`, `FDecisionFeatureBuilder`를 순서대로 호출한다. 세 Core는 같은 Target·Candidate identity를 공유한다.
3. **Utility 선택:** Host가 generated Utility profile로 `FUtilitySelection`을 호출한다. 실행 가능한 Candidate가 0개면 Skill을 시작하지 않는다.
4. **Commit 연결:** `FAINativeNPCGameplayCommitAuthority`가 `IDecisionCommitAuthority`를 구현한다. Commit 직전에 Goal·Knowledge·Target·Candidate·Skill 조건을 다시 읽는다.
5. **Skill 시작:** Commit 성공은 `FAINativeNPCCommittedSkillStart`를 한 번 발행한다. 기존 private StateTree handoff가 이를 소비한다.
6. **결과 연결:** Goal Host가 Executor result sink를 설치한다. exact Goal token·DecisionId·Skill·Target과 일치하는 결과만 Goal Runtime event로 변환한다.
7. **단계 진행:** `Orient → Navigate → Search → Return`을 진행한다. Return은 session 시작 위치로 만든 home Waypoint를 사용한다. 완료 뒤 `IdleObserve`를 재개한다.

각 순서는 실패하는 Automation을 먼저 추가한다. 수정 뒤 focused test, 전체 `AINativeNPC`, Data Validation과 실제 production Pawn smoke를 실행한다.

Phase 3B의 완료 조건:

- 실제 Hearing 한 번이 `Orient → Navigate → Search → Return → IdleObserve`를 끝까지 진행한다.
- 각 단계의 Skill은 generated phase 규칙과 같은 Target만 사용한다.
- 오래된 Goal·Knowledge·Target·Decision·Skill result는 상태를 바꾸지 않는다.
- Commit 실패와 실행 가능 Candidate 0개는 기존 Goal·Skill을 손상시키지 않는다.
- 같은 Decision과 Skill result는 한 번만 적용된다.
- Host·Timer·Knowledge·Executor 제거와 재등록 뒤 이전 판단·Timer·callback은 부활하지 않는다.
- Contract → Editor build → focused → broad → Data Validation 순서의 최종 증거가 모두 통과한다.

이번 범위는 `InvestigateDisturbance/Resolve`, 다른 V1 Goal, Cover·SmartObject production 예약, Neural 모델, 전체 arbitration, save/load와 replication을 구현하지 않는다.

### 2.1.2 2단계: 학습 모델과 전체 기능을 붙인다 (`Phase 1`)

이 단계는 역할과 Goal을 늘리고, 학습 모델과 멀티플레이 안전 규칙을 적용한다.

- Role 3개
- Goal 4개
- Skill Registry 16개
- Target Kind 8개
- Calibration/OOD/Abstain
- Cover/SmartObject reservation
- 멀티플레이 서버 권위
- DAgger와 정식 KPI Gate
- 선택적 Boss Pattern Policy: 공통 `Attack(Entity)` 하위 32 Pattern row, 별도 Model Bundle과 Utility fallback

완료 조건:

- Phase 1 Schema patch와 생성 계약·Dataset·Model Bundle의 Hash binding이 일치한다.
- Neural·OOD·Calibration·Unreal Runtime Gate가 실제 증거로 통과한다.
- [최종 승인 체크리스트](#final-approval)에 pending Gate가 없어야 한다.

### 2.1.3 담당 팀과 예상 기간

| 작업 | 담당 팀 | 1단계 예상 | 2단계 예상 | 먼저 필요한 것 |
|---|---|---:|---:|---|
| Knowledge와 Target을 저장·갱신하는 Runtime | Gameplay AI | 2주 | 3주 | Target 계약 |
| Goal 선택과 전환 | Gameplay AI + Designer | 2주 | 3주 | Goal Registry의 생명주기·우선순위·전환 규칙 |
| Target 17개와 Candidate 272개 구성 | Gameplay AI + ML | 2주 | 2주 | Schema Appendix A/C/D |
| 규칙 기반 행동 선택(Utility Baseline) | AI Designer | 1주 | 2주 | Candidate 생성 흐름 |
| 모델 입력 생성과 Python·Unreal 결과 비교 | ML + Gameplay AI | 2주 | 2주 | Schema Generator |
| Neural 모델 학습과 ONNX 출력 | ML | 2주 | 4주 | 모델 입력 비교 통과 |
| 보스 공격 패턴 모델·Utility·실행기 | ML + Combat AI + Animation + QA | - | 4주 | 공통 Attack Commit과 Boss Pattern 계약 |
| 비동기 응답 Commit과 자원 예약 | Gameplay + Server | 2주 | 4주 | Skill 계약 |
| Gold·DAgger 제작 도구 | Tech Designer | 1주 | 4주 | Inspector와 Replay |
| 품질 기준 자동 검사 | QA + ML | 2주 | 지속 | Critical Suite |

Phase 0은 병렬 수행을 전제로 약 6~8주 범위다. Phase 1은 Phase 0 Gate 통과 후 약 12~16주 범위이며 팀 규모와 Unreal 통합 상태에 따라 조정한다.

---

<a id="reference-model"></a>
# 3. NPC가 행동을 고르는 모델을 어떻게 만들 것인가

모델은 NPC가 아는 현재 상황과 실행 가능한 Candidate를 읽고 각 Candidate에 점수만 매긴다.

Runtime Post-process는 Hard Mask → Switch Cost → Candidate 선택 → OOD·Calibration → Accept·Abstain 순서로 판단한다.

Accept 결과는 Commit Coordinator로 전달한다. Commit Coordinator는 최신 게임 상태를 검사하고 실행을 확정한다.

Abstain 결과는 같은 immutable Snapshot·Candidate·Mask를 사용하는 Goal Utility 기준 로직으로 전달한다.

일반 NPC 모델의 기술명은 `policy_arch_v1.0.0`이다. 보스 공격 패턴 모델은 `Attack(Entity)` Commit, `BossPatternPolicy` capability와 `ReadyToSelect` 진입이 모두 확인된 뒤 사용하는 하위 모델이다.

## 3.1 일반 NPC의 행동 선택 모델 (`policy_arch_v1.0.0`)

일반 NPC 모델은 현재 상태, Target, 최근 Event와 Candidate를 함께 읽는다. V1의 시계열 입력은 최근 12개 Event Buffer로 고정한다.

### 3.1.1 상황 정보를 하나의 판단 정보로 묶는다

Context Encoder는 서로 다른 입력을 128개 숫자로 된 전술 판단 정보(`tactical context`)로 묶는다.

```text
global_state [128] → MLP → global embedding 128
targets [17×48] + kind embedding → shared encoder → target embeddings 17×64
masked target pooling → target context 128
events [12×24] + event type embedding + referenced target embedding
→ shared encoder + temporal attention → event context 96
concat 128+128+96 = 352
→ fusion 352→256→128 = tactical context h
```

### 3.1.2 개발자가 그대로 구현할 Layer 구조

아래 숫자와 수식은 ML 개발자가 같은 모델을 만들기 위한 정확한 값이다. 처음 읽는 독자는 [보스 공격 패턴 모델](#32-보스-공격-패턴을-고르는-하위-모델-boss_pattern_arch_v100)로 이동할 수 있다.

V1 승격 후보는 아래 Layer와 상수를 그대로 사용한다. 다른 구조를 사용하는 실험 모델은 새 architecture version을 받고 parity·Calibration·성능 검증을 다시 수행한다.

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
  slot 16 NoTarget은 항상 valid이며 최소 1개의 Target row를 보장

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

### 3.1.3 각 Candidate에 점수와 실행 값을 제안한다

Scorer는 272개 Candidate의 순위를 계산한다. Parameter Head는 이동 거리나 회전량처럼 Skill이 허용한 실행 값을 제안한다.

정확한 구조:

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

### 3.1.4 점수 범위를 고정한다

Query와 Key 정규화는 모델 점수를 일정 범위로 유지한다. 이 범위는 행동 전환 비용(`Switch Cost`)이 선택 결과에 안정적으로 반영되게 한다.

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

## 3.2 보스 공격 패턴을 고르는 하위 모델 (`boss_pattern_arch_v1.0.0`)

공통 행동 선택 Runtime이 `Attack(Entity)`를 고르면 Commit Coordinator가 실행을 확정한다. `BossPatternPolicy` capability와 `ReadyToSelect` 진입 조건이 함께 충족되면 보스 공격 패턴 모델이 최대 32개 공격 패턴에 점수를 매긴다.

```text
Pattern Context
  pattern_context [B,32]
  → Linear(32,64) → LayerNorm → ReLU
  → Linear(64,64) → LayerNorm → ReLU
  = context [B,64]

Pattern Row
  pattern_features [B,32,24]
  → shared Linear(24,64) → LayerNorm → ReLU
  = pattern [B,32,64]

Context×Pattern
  pattern_pair_features [B,32,16]
  → shared Linear(16,32) → LayerNorm → ReLU
  concat(context broadcast 64, pattern 64, pair 32) = 160
  → shared Linear(160,64) → LayerNorm → ReLU

Heads
  score: Linear(64,1) → pattern_raw_scores [B,32]
  parameter: Linear(64,4) → Sigmoid → pattern_parameter_proposals [B,32,4]
```

- Python과 Unreal Feature Builder는 generated Boss Pattern normalizer table을 사용한다. 거리·속도·시간 divisor, clamp, non-finite reject, zero padding이 일치하지 않으면 Float parity Gate를 실패시킨다.
- `target_health_ratio_estimate`는 confidence를 동반하며 confidence 0의 추정값을 확정 정보로 해석하지 않는다.
- post-lock 현재 Target transform은 결정론적 Combat Executor의 bounded tracking에만 쓰며 Pattern Model 입력이나 재선택 조건으로 되먹이지 않는다.
- 학습과 순위 계산은 `pattern_mask=true`인 row만 사용한다. 빈 row와 실행 불가능한 row는 `pattern_mask=false`이며 Loss와 parameter decode에 참여하지 않는다.
- 요청 Snapshot이 안정적인 `pattern_id`를 제공한다. 모델은 각 row의 점수만 출력한다.
- Parameter 0은 authored tracking 상한을 줄이는 비율이다.
- Parameter 1·2는 Telegraph·Recovery의 authored extension 상한 안에서 시간을 늘리는 비율이다.
- Parameter 3은 reserved zero다.
- Data Asset과 Combat Executor가 Damage·Hitbox·Active window·Root Motion·interruptibility·Phase transition을 소유한다. 모델 출력은 점수와 허용된 Parameter 4개로 제한한다.
- abstain 또는 계약·OOD·Calibration 실패는 같은 immutable request와 같은 `pattern_mask`를 사용하는 Boss Pattern Utility Baseline으로 이어진다.
- Utility 동점은 adjusted score 내림차순 후 `pattern_id` 오름차순으로 해소한다.
- Utility 결과가 없으면 현재 valid 조건을 만족하는 Authored safe default를 사용한다.
- fallback 결과가 없으면 Runtime은 `PatternUnavailable`을 Attack Skill에 반환하고 Parent Tactical Policy가 다음 행동을 고른다.
- valid row가 0개이면 Neural·Utility 호출 수는 0이다. Runtime은 즉시 `PatternUnavailable`을 반환한다(`ReturnPatternUnavailableToAttackSkillWithoutInferenceOrUtility`).

### 3.2.1 보스 전용 학습 데이터와 배포 묶음

Boss Pattern Dataset은 공통 272 Candidate Dataset과 별도 record type으로 저장한다.

각 record는 Pattern candidate-set hash, Pattern asset-bundle hash, Attack Target Knowledge snapshot과 Boss/Combat revision을 기록한다. 선택 결과는 valid mask, acceptable Pattern set, 선택 boundary와 실행 결과로 기록한다.

`boss_pattern_model_bundle_v1`은 다음 digest를 묶는다.

- Boss Pattern Contract
- Pattern model
- Pattern normalization contract
- Pattern post-process contract
- Pattern Calibration/OOD asset
- 결정론적 Pattern Executor contract

보스별 Pattern Asset bundle은 공통 Tactical Model Bundle과 독립적으로 교체할 수 있다. Pattern Asset 교체는 `pattern_candidate_set_hash`를 바꾸며 pending 응답을 stale로 만든다.

### 3.2.2 재미와 공정성을 함께 평가한다

- Pattern recall과 mask 위반을 Boss Phase×거리×이전 Pattern×selection boundary별로 보고한다.
- Telegraph 시작 후 Pattern 변경, Active 중 재선택, 허용되지 않은 interrupt는 Critical miss다.
- 공격별 Telegraph 최소 시간, Recovery 최소 시간, post-lock tracking 상한을 Runtime trace로 검증한다.
- 짧은 Pattern 반복, 같은 family 연속 사용, 특정 거리에서의 단일 Pattern collapse를 별도 분포 metric으로 보고한다.
- 승격 기준은 Player hit rate, 공격 가독성, 반격 가능 시간, 반복도, Pattern 다양성과 hard-constraint 위반 0건을 함께 사용한다.
- 품질 결과는 Boss Pattern Utility Baseline과 같거나 더 좋아야 한다(`utility_baseline_noninferiority_or_improvement`).


---

<a id="ml-pipeline"></a>
# 4. 학습 데이터를 만들고 모델을 준비하는 순서

이 장은 앞으로 만들 학습 Pipeline의 파일과 실행 순서를 정한다. 현재 실제 `ML/` 코드, 학습 Dataset, Teacher Profile과 학습 모델은 없다.

학습 코드는 Unreal 프로젝트 `NeuralGame`의 루트에 만든다. 현재 기준 작업 공간은 `/mnt/d/Codex-cli/NeuralProject/NeuralGame`이다.

이 문서의 `ML/...` 경로와 `python -m anpc_ml...` 명령은 `NeuralGame` 루트를 기준으로 한다. 기계 계약 입력은 source SHA로 고정한 generated contract와 consumer provenance lock을 사용한다. Registry, generator, generated 산출물과 회귀 검사는 같은 `main` 변경으로 게시한다.

## 4.1 게임 상황을 학습 Record로 만든다

Unreal Capture는 실제 플레이 상황을 저장한다. Procedural Generator는 계약에 맞는 가상 상황을 만든다. 두 경로는 한 번의 NPC 판단 상황을 변경 불가능한 Dataset shard로 저장한다.

절차 생성기의 scenario family, 값 추출 범위, heuristic label 계산식과 실행 CLI는 후속 상세 설계 항목이다.

학습 설정의 기술명은 `policy_train_v1.0.0`이다. 학습 코드는 별도 Unreal 구현 저장소의 `ML/`에 둔다. 학습 코드는 이 저장소의 YAML과 `generated/python/ai_native_npc_contracts_generated.py`를 고정 commit으로 가져와 사용한다.

학습 파이프라인은 다음 순서를 지킨다.

```text
실제 플레이 저장 / 가상 상황 생성
→ 변경 불가능한 Dataset shard 작성
→ Dataset 계약 검사
→ `scenario_family_id` family 단위로 Train·Validation·Calibration·Test·OOD·Critical 분리
→ `split_assignment.csv`와 immutable Dataset shard의 SHA-256 고정
→ Silver 데이터로 기본 행동 학습
→ Gold·DAgger 데이터로 품질 조정
→ 가장 좋은 학습 결과 고정
→ 낯선 상황 감지 기준 생성
→ 모델 신뢰도 기준 생성
→ Unreal용 ONNX 모델 출력
→ PyTorch·ONNX Runtime·Unreal NNE 결과 비교
→ 일반·낯선 상황·안전·성능 기준 검사
→ 배포할 Model Bundle 승인
```

학습 코드는 checkpoint와 Calibration asset을 먼저 고정한다. Test·OOD·Critical 데이터는 그다음 평가 단계에서 연다. Test 결과를 사용해 구조나 학습 설정을 바꾸면 새 실험과 새 Test 버전을 만든다.

## 4.2 Teacher LLM이 Silver Label을 만든다

Teacher LLM은 저장된 게임 상황과 Candidate 목록을 읽고 적절한 행동 후보와 선호 순서를 제안한다. 같은 상황에 대한 여러 응답은 합의 과정을 거친다. 애매한 상황은 사람이 확인하는 Gold review queue로 보낸다.

Teacher LLM은 개발 중 Silver 학습 데이터를 만드는 도구다. 정확한 입력·출력·합의 규칙은 [세부 기술 요구사항 §9.1.1](technical-requirements.md#911-teacher-llm-silver-label-생성)이 정한다. 이 절은 구현 순서와 실행 위치를 정한다.

별도 Unreal 구현 저장소의 `ML/` 디렉터리에 다음 파일을 만든다.

```text
ML/config/teacher_profile_v1.yaml
ML/config/teacher_gold_validation_manifest.json
ML/teacher/schemas/teacher_request_v1.schema.json
ML/teacher/schemas/teacher_response_v1.schema.json
ML/teacher/
ML/tests/test_teacher_pipeline.py
```

`ML/teacher/` 파이프라인은 다음 순서로 구현한다.

```text
Profile·Schema hash 검증
→ hidden-information filter와 request builder
→ provider adapter와 raw payload 저장
→ strict parser와 consensus aggregator
→ annotation shard·Gold review queue 작성
→ Dataset Record v2 mapper·manifest 작성
→ Role×Goal Gold comparison report
```

`ML/tests/test_teacher_pipeline.py`는 다음 계약을 fixture로 검증한다.

- Request·Profile: hash Golden, Tensor→view parity, hidden-information filtering
- Response·Consensus: strict Schema, abstain invariant, mask 위반, 합의·confidence
- Provenance·Join: source Snapshot join, `candidate_set_canonical_bytes` 재검증, annotation join
- Dataset mapping·Split: parameter positive-zero/mask, `selected_is_acceptable=null`, `source_type=silver`, split Gate

```bash
python -m ML.teacher.generate --profile ML/config/teacher_profile_v1.yaml --input <decision_snapshot_shard> --output <annotation_shard> --review-queue <gold_review_queue>
python -m ML.teacher.validate --profile ML/config/teacher_profile_v1.yaml --input <annotation_shard>
python -m ML.teacher.map --snapshots <decision_snapshot_shard> --annotations <annotation_shard> --output <dataset_record_v2_shard> --manifest <dataset_manifest>
python -m ML.teacher.report --profile ML/config/teacher_profile_v1.yaml --input <annotation_shard> --gold-manifest ML/config/teacher_gold_validation_manifest.json --output <report_dir>
```


---

<a id="training-config"></a>
# 5. 어떤 데이터로 몇 번 학습할 것인가

Silver는 모델이 다양한 상황을 넓게 익히는 데 사용한다. Gold와 DAgger는 사람이 확인한 판단으로 모델의 품질을 높이는 데 사용한다.

## 5.1 두 단계로 학습한다

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

재현 조건:

- release seed는 `1729` 하나를 사용하고 Python, NumPy, PyTorch, DataLoader worker에 모두 전파한다.
- Role×Goal group은 epoch 안에서 균등 sampler를 사용한다. source 비율은 위 표를 따른다.
- V1 기준 학습은 FP32를 사용한다. mixed precision, TF32와 quantized training은 비활성화한다.
- PyTorch deterministic algorithms를 켜고 non-deterministic operator 발견 시 실패한다.
- Stage B는 Stage A best checkpoint에서 시작하며 모든 Layer를 학습한다.
- Validation은 매 epoch 수행한다. Test·OOD·Critical split은 최종 평가 단계에서만 loader에 등록한다.
- 정확한 Python/PyTorch/ONNX/ORT/CUDA 버전, OS image digest, GPU/CPU model, driver, code commit은 `train_environment.lock.json`에 고정한다.

동일한 Release 모델은 잠긴 환경에서 다시 만든다. 환경 변경으로 model hash가 바뀌면 새 Model Bundle을 만들고 전체 검증을 다시 실행한다.

## 5.2 가장 좋은 학습 결과를 고르고 기록한다

Checkpoint는 학습 중 저장한 모델 상태다. 각 Stage의 best checkpoint는 Validation 결과를 다음 순서로 비교해 자동 선택한다.

```text
1. macro Role×Goal Any-Acceptable Top-1, post-switch-cost — 큰 값
2. worst Role×Goal Any-Acceptable Top-1 — 큰 값
3. annotated active parameter MAE — 작은 값
4. epoch — 작은 값
```

Top-1은 Runtime과 동일한 Adjusted Score 선택 결과로 계산한다. 보고서에는 micro/macro/worst-group, source별, Target Kind별, valid candidate count bucket별 결과와 abstain-only 분모를 모두 기록한다.

Checkpoint는 다음 파일과 상태를 포함한다.

- weights 전용 `model.safetensors`
- architecture/config JSON
- optimizer state, epoch, RNG state
- Dataset/Code/Environment hash

Release Export는 best weights와 architecture/config만 포함한다. Optimizer state는 학습 재개용 Checkpoint에 보관한다.


---

<a id="implementation-cli"></a>
# 6. 구현 명령을 어떤 순서로 실행하는가

아래 명령은 `NeuralGame/ML` 코드를 구현한 뒤 제공할 실행 인터페이스다. 현재 `NeuralGame`에는 `ML/` 디렉터리와 이 명령을 실행할 학습 코드가 없다.

구현 CLI는 `NeuralGame` 프로젝트 루트에서 Dataset 검사부터 모델 평가까지 한 방향으로 실행한다.

```bash
python -m anpc_ml.dataset.validate --manifest <dataset_manifest.json>
python -m anpc_ml.train --config <train_config.json>
python -m anpc_ml.fit_calibration --checkpoint <best_checkpoint>
python -m anpc_ml.export_onnx --checkpoint <best_checkpoint>
python -m anpc_ml.parity --bundle <model_bundle_dir>
python -m anpc_ml.evaluate --bundle <model_bundle_dir>
```

1단계는 사람이 준비한 작은 고정 Dataset으로 ONNX→Unreal 연결을 검증한다. 이 증거는 모델을 불러오고 결과를 전달하는 통합 경로를 보장한다.

V1 Model Bundle은 실제 학습 데이터와 모델을 사용한다. V1 승격에는 Appendix E의 데이터·품질·안전·성능 기준을 적용한다.


---

<a id="release-pipeline"></a>
# 7. 검증된 모델 묶음을 어떻게 만드는가

이 장은 학습 모델이 생긴 뒤 구현할 Release Pipeline을 정한다.

Release Pipeline은 같은 계약과 모델이 Python, C++와 Unreal에서 같은 결과를 내는지 검사한다. 모든 검사를 통과하면 재현 가능한 배포 ZIP을 만든다.

Lock과 ZIP의 구성원은 논리 결과와 입력·도구 Hash로 고정한다. Compiler 경로·버전, 테스트 실행시간과 stdout/stderr는 로컬 전용 파일 `dist/local/contract_test_diagnostics.json`에 기록한다. 이 로컬 파일은 Lock과 ZIP의 구성원 집합 밖에 둔다.

다음 명령은 현재 Release Pipeline의 목표 인터페이스다. 현재 `main`에는 `tools/doc_harness.py`가 없다.

과거 하네스 구현은 보관 브랜치 `archive/full-harness-v0.4.6`과 태그 `full-harness-v0.4.6-rc5`에 있다. 이 보관본은 v0.4.6 감사 자료다. 현재 계약용 Release 도구를 활성 구현으로 옮기고 도구 Hash를 고정한 뒤 아래 명령을 실행한다.

```bash
python tools/doc_harness.py release --output <bundle.zip>
```

배포 묶음은 다음 순서로 만든다.

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

`validate --strict`는 규범 리포트의 입력 Hash·Test ID·논리 결과를 검증한다. byte 비교는 환경마다 달라지는 진단문을 로컬 기록으로 분리한다. 로컬 C++17 Compiler가 있으면 동일 Golden을 추가 실행한다.


---

<a id="final-approval"></a>
# 8. 언제 구현 완료로 승인하는가

승인은 `계약 Freeze → Phase 0 완료 → V1 제품 Release` 순서로 진행한다. 개발 작업은 병렬로 진행할 수 있다. 승인 결정은 앞 Gate의 증거를 이어받는다.

| Gate | 승인 목적 | 승인 책임자 | 필수 증거 | 현재 결정 |
|---|---|---|---|---|
| 1. 계약 Freeze | 기계 계약과 생성 결과를 한 버전으로 고정 | Contract Owner, Data/ML Lead, Unreal Integration, QA | YAML, generated binding, Golden, Hash, split assignment | **NO-GO** |
| 2. Phase 0 완료 | 규칙 기반 NPC 판단과 안전한 실행 흐름을 검증 | Gameplay AI, Server/Runtime, Unreal QA | Runtime·Timer·Commit·Target Recall·lifecycle 테스트 | **HOLD** |
| 3. V1 제품 Release | 실제 데이터와 학습 모델을 게임에 배포 | ML/Data, Gameplay AI, Unreal NNE, QA/Release, Product Design | Model Bundle, Calibration/OOD, parity, 성능·품질·플레이테스트, Release ZIP | **NO-GO** |

상태 표시는 다음 의미를 가진다.

- **현재 완료:** 현재 범위의 구현과 증거가 승인됐다.
- **현재 완료·최종 재실행:** 현재 증거가 있으며 Gate 결정 때 고정된 최종 byte로 다시 실행한다.
- **부분 완료:** 제한된 fixture 또는 계약 증거가 있다.
- **미완료:** 구현 또는 필수 증거가 남아 있다.

## 8.1 Gate 1: 기계 계약을 고정한다

**결론:** Goal·Boss 정적 계약은 현재 완료다. 전체 Schema Freeze는 활성 generator/harness 복원, remediation과 최종 Golden 재실행을 기다린다.

### 현재 완료 또는 최종 재실행

- **현재 완료·최종 재실행:** Goal Registry typed trigger·phase duration·revision contract 생성/검증
- **현재 완료·최종 재실행:** Goal definition·14 phase/skill-mask·lifecycle/arbitration metadata generated C++ binding과 consumer provenance sync
- **현재 완료·최종 재실행:** `boss_pattern_contract_v1.yaml` validator와 별도 Python/C++/Markdown·Candidate/Decision hash Golden 생성
- **부분 완료:** `ai_native_npc_schema_v2_0.yaml`의 generated Python/C++ binding은 현재 존재한다. generated docs와 최종 Golden은 활성 Release 도구에서 다시 만든다.
- **부분 완료:** Enum·Mask·Padding·Hash Golden Vector와 17 Target Slot·272 Candidate layout은 보관 하네스 증거가 있다. 현재 Gate는 최종 byte 재실행 증거를 요구한다.

### 남은 Freeze 조건

- **미완료:** `source_moving_probability` 의미·dtype remediation과 migration
- **미완료:** Pair Feature same-target comparison을 Schema의 `identity_key`로 구조화하고 Revision-only Golden 통과
- **미완료:** Dataset Record v2의 Switch Cost·feature/content/sample hash Validator 통과
- **미완료:** `split_assignment.csv` 고정과 여섯 split의 `input_content_hash`·`scenario_family_id` 교집합 0
- **미완료:** OOD/Critical `test_case_catalog_v1.yaml` allowlist와 split 격리 통과

**Gate 1 승인 산출물:** Freeze Manifest, generated artifacts, Golden report, `split_assignment.csv`, 입력·도구 Hash와 parity report.

## 8.2 Gate 2: 규칙 기반 NPC 판단과 안전한 실행을 완료한다

**결론:** 보스 공격 전달 fixture, Goal Dispatcher·Timer Core, bounded 일반 NPC 5-Skill 실행, generated initial Goal과 production Hearing→`InvestigateDisturbance/Orient` 전환은 PASS다. 전체 Goal-owned Utility→Commit→Skill-result progression과 전체 production integration은 HOLD다.

### 현재 증거

- **부분 완료:** Float Feature parity는 기존 계약·fixture 범위에서 증거가 있다. production Feature Builder 전체 parity가 남아 있다.
- **부분 완료:** Telegraph/Active/Recovery lock·interrupt cleanup·stale Commit은 보스 fixture 범위에서 PASS다. shipping combat effect와 production PatternSet 통합이 남아 있다.

### 남은 Phase 0 조건

- **부분 완료:** Entity·SoundEvent·LastKnownPosition production Knowledge와 exact Entity Actor binding은 구현됐다. bounded `HomeWaypoint`와 Hearing에서 고정한 `DisturbancePosition`은 Goal authority가 생성한다. CoverSlot·SmartObject와 일반 Waypoint·WorldPosition producer는 남아 있다.
- **미완료:** Target Slotter Target Recall Gate 통과
- **완료:** Goal Contract Dispatcher Core의 41-row 소비·guard/effect fail-closed·destination/revision hostile test. `AINativeNPC.GoalFsm` `23/23` PASS
- **완료:** Goal Timer Runtime Core의 `2/15/8/4/6/5초`, lifecycle·snapshot·expected-token CAS·pause/time-dilation hostile test
- **부분 완료:** exact general-NPC Pawn/Controller assembly, live typed Actor binding, authoritative generated initial Goal, production Hearing 전환과 committed capability→StateTree handoff foundation
- **완료:** production `Idle(NoTarget)`은 Registry duration 동안 이동을 멈추고 one-shot Timer 완료 시 정확히 한 번 Succeeded가 된다. 최종 19-file SHA 독립 재리뷰 `3/3`은 모두 `19/19`, PASS, blocker `0`이다.
- **구현됨:** pending proposal은 Executor effect 전에 이동·비우고 acquisition guard를 먼저 세운다. 이동 정지 callback 전에는 Running·재진입 guard를 설치하고 callback 뒤 authority·owner·Controller·exact assembly를 다시 검사한다. 재진입 중 assembly가 바뀌면 Running 또는 Succeeded를 publish하지 않고 Failed로 닫는다.
- **완료:** Skill Registry `execution_semantics_v1`에서 생성한 immutable C++ 표로 `TurnTo`·`Approach`·`Investigate`·`SearchArea`를 committed capability 뒤에서 실행한다. Target 위치는 실행 시작 시 다시 확인해 고정한다. 행동별 hostile RED→GREEN, 최신 encompassing broad `134/134`, Data Validation `291/0/0` PASS다.
- **부분 완료:** generated bounded authority는 9 executable guard·3 provider-unavailable guard·2 staged effect다. production은 initial `IdleObserve/Observe`, `valid_disturbance_target`, staged `request_new_goal`, suspended old Goal, active `InvestigateDisturbance/Orient`와 generated timer까지 연결했다. 나머지 guard/effect provider, Goal Arbitration, Utility→actual Commit authority, Skill 완료→Goal event와 전체 save/archive는 남아 있다.
- **완료:** `snapshot_revision` stale response, 40ms deadline 경계, Candidate Hash mismatch와 Atomic Commit rollback·replay hostile tests. Policy `14/14` PASS
- **미완료:** Hidden Information Leakage Test

**Gate 2 승인 산출물:** Unreal Automation report, Target Recall report, Goal lifecycle·Timer report, Commit/fallback hostile test report와 production integration smoke.

## 8.3 Gate 3: 실제 학습 모델을 제품에 배포한다

**결론:** 실제 학습 Dataset과 모델이 없다. V1 제품 Release는 NO-GO다.

### 남은 V1 Release 조건

- **미완료:** `tactical_context [B,128]` output을 Schema·ONNX·ORT·NNE descriptor에 연결하고 3-output parity 통과
- **미완료:** Adjusted Score→OOD→Calibration 순서와 Runtime threshold 0.80 parity
- **미완료:** Calibration global/group accepted count·coverage·one-sided risk CI Gate
- **미완료:** Model Bundle manifest self-exclusion과 `model_sha256=SHA256(policy.onnx)` 검증
- **미완료:** Pattern Asset Bundle canonical digest Python↔Unreal Build Commandlet parity
- **미완료:** Boss Pattern Float Tensor Python↔Unreal parity
- **미완료:** Boss Pattern ONNX Runtime↔Unreal NNE output parity
- **미완료:** Boss Pattern readability·punish-window·반복도·다양성·성능 Gate
- **미완료:** Utility Baseline 대비 비열등 또는 개선 Gate
- **미완료:** Appendix E의 실제 Baseline·CI·표본 Gate
- **미완료:** 보관 validation report의 pending Runtime/Formal Gate 종료

**Gate 3 승인 산출물:** versioned Dataset manifest, Model Bundle, Calibration/OOD asset, ORT↔NNE parity report, 성능·품질·플레이테스트 report, Lock·Checksum과 deterministic Release ZIP.

현재 Runtime 계약은 RC5 YAML의 field index·enum·shape다.

[세부 기술 요구사항 §10.6](technical-requirements.md#106-rc5-구조화-계약-remediation-상태)의 항목은 새 patch 발급 후 활성화한다.

새 patch는 YAML·generated artifacts·Golden·Decision Contract Hash를 포함한다.

완료된 Gate 증거만 Freeze·OOD Runtime 승격 대상으로 사용한다. 변경 이력은 [`docs/history`](../history/README.md)에 보관한다.

## 8.4 현재 확인한 Unreal·Goal 구현 증거



### 보스 공격을 StateTree로 전달하는 흐름

- exact focused `2/2`, broad `AINativeNPC.BossPattern` `53/53`, warning/failure `0/0`
- `NeuralGameEditor Win64 Development` clean+cold UBT/UHT: PASS
- Data Validation: `290 assets`, error/warning `0/0`
- generated contract lock sync와 MCP restart Host/Session/EventSource `1/1/1`: PASS
- StateTree ready/hash/clean, map dirty/unsaved `false/false`, active/interrupted ChangeSet `0/0`
- authority/security·lifecycle/terminal·asset/test 독립 review: `Critical 0 / Important 0 — GO`

### Goal 계약과 남은 Runtime 구현

- Goal Registry `1.1.0`: transition `41 = 35 event + 6 timer`, production timeout `2/15/8/4/6/5초`
- focused Goal contract `23/23`, full Python harness `67/67`, generator/schema/golden, C++17 parity: PASS
- Goal Registry SHA `d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e`; consumer byte parity·lock sync와 `--check`: PASS. Registry·generator·generated 산출물·회귀 검사는 같은 `main` 변경으로 게시
- `GoalFsmRuntime.h/.cpp`와 server Timer Runtime Component: 구현, `AINativeNPC.GoalFsm` `23/23` PASS
- exact Pawn/Controller·Perception Knowledge·execution Target snapshot·committed capability→StateTree handoff·5개 bounded Skill: 구현
- generated initial Goal과 production Hearing→`InvestigateDisturbance/Orient` 전환: 구현
- 나머지 gameplay guard/effect provider·실제 Goal-owned Utility→Commit authority·Skill 완료→Goal event·전체 arbitration/save: 미구현

현재 판정은 **Goal binding/provenance PASS, Contract Dispatcher·Timer Core PASS, bounded initial/Hearing Goal integration PASS, bounded 5-Skill execution PASS, 전체 Goal-owned Commit/Skill-result progression HOLD, Gameplay Goal FSM HOLD**다.

보스 공격 전달 흐름과 Goal 정적 계약은 제한된 범위에서 PASS다. Schema Freeze와 전체 제품 Release는 **NO-GO**다.
