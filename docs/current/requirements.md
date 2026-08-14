# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# AI Native NPC 제품 요구사항
## 처음 보는 사람을 위한 의사결정 시스템 설명

- 문서 버전: **v0.4.14**
- 개정일: 2026-08-12
- 주 독자: **기획자, 사업 책임자, Gameplay Designer, 새로 합류한 개발자**
- 한 줄 상태: **일반 NPC가 유효한 소리를 듣고 조사 Goal을 시작하는 Phase 3A는 완료됐다. 다음 Phase 3B는 Goal에 맞는 행동을 고르고 실행 결과에 따라 다음 단계로 진행하는 흐름을 연결한다.**
- 세부 기술 계약: [AI Native NPC 세부 기술 요구사항](technical-requirements.md)
- 정확한 ID·크기·수치: [Contract Appendices](contract-appendices.md)
- 구현 순서: [Implementation Plan](implementation-plan.md)
- Unreal 작업 기준: [Unreal Implementation Plan](unreal-implementation-plan.md)
- 변경 이력: [Requirements History](../history/README.md)

이 문서는 “무엇을 만들고, 왜 만들며, 누가 무엇을 결정하는가”를 설명한다. 구현에 필요한 정확한 자료형, 계산식, timer, hash, 저장 규칙은 [세부 기술 요구사항](technical-requirements.md)이 소유한다.

정확한 값이 서로 다르면 다음 순서로 판단한다.

1. Schema·Registry 같은 기계 판독 계약
2. 세부 기술 요구사항
3. 이 제품 요구사항

---

<a id="guide"></a>
# 0. 한눈에 보기

<a id="toc"></a>
## 0.1 목차

1. [제품 목표](#product-goal)
2. [Goal: 지금 무엇을 이루려는가](#goal)
3. [Knowledge: NPC는 무엇을 알고 있는가](#belief)
4. [Target: 누구·무엇·어디를 대상으로 하는가](#target)
5. [Skill과 Candidate: 무엇을 할 수 있는가](#candidate)
6. [행동 선택: 무엇이 가능하고 무엇이 더 좋은가](#selection)
7. [Commit과 실행: 서버가 마지막으로 확인한다](#commit)
8. [보스 공격은 한 단계 더 선택한다](#boss-pattern)
9. [학습과 평가는 같은 계약을 쓴다](#learning)
10. [현재 구현 상태와 완료 조건](#status)
11. [정확한 기술 자료를 찾는 곳](#references)

이 목차의 번호와 실제 장 번호는 같다. 링크를 누르면 같은 번호의 장으로 이동한다.

<a id="one-sentence"></a>
## 0.2 한 문장 설명

AI Native NPC는 **NPC가 알고 있는 정보와 현재 목적을 바탕으로 허용된 행동을 고르고, 서버가 최신 상태를 다시 확인한 뒤 실행하는 시스템**이다.

신경망이 모든 것을 결정하지 않는다. 게임 규칙이 가능한 행동과 안전 경계를 정하고, 신경망은 그 안에서 더 자연스러운 선택의 순위만 매긴다.

<a id="glossary"></a>
## 0.3 꼭 알아야 할 말

| 용어 | 쉬운 뜻 | 예시 |
|---|---|---|
| Goal | 여러 행동에 걸쳐 유지되는 목적 | 소리 조사, 경계선 집행, 전투 |
| Goal Phase | Goal 안의 현재 단계 | 방향 보기 → 접근 → 주변 찾기 |
| Knowledge | NPC가 직접 보거나 듣거나 전달받아 보관하는 정보. 코드 이름은 `Belief` | 마지막으로 본 위치, 들은 발소리 |
| Target | 행동 문장의 목적어 | 적, 소리, 엄폐물, 위치 |
| Target Slot | 이번 판단에서 고려할 Target을 담는 NPC별 자리 | `slot 1 = 방금 들은 발소리` |
| Skill | 실행기가 수행하는 한 가지 행동 | 바라보기, 접근하기, 공격하기 |
| Candidate | Skill과 Target을 합친 행동 후보 | `조사하기 + 발소리` |
| Hard Mask | 실행하면 안 되는 Candidate를 선택 대상에서 제외하는 규칙 | `공격하기 + 발소리` 제외 |
| Policy | 가능한 Candidate의 선호 순위를 매기는 로직 | 규칙 기반 Utility 또는 신경망 기반 Neural |
| Commit | 선택 결과를 최신 상태로 다시 검사하고 실행을 확정하는 짧은 서버 작업 | Target 생존·Goal·자원 재검사 |
| Boss Pattern | `공격하기`가 선택된 뒤 고르는 보스 전용 공격 절차 | 빠른 베기, 강한 내려찍기 |

<a id="example-flow"></a>
## 0.4 예시: NPC가 발소리를 들었을 때

```text
발소리를 들음
→ “발소리가 저쪽에서 났다”는 정보를 Knowledge에 저장
→ “이상한 소리를 조사한다”는 Goal을 활성화
→ 발소리를 Target으로 선택
→ 돌아보기, 접근하기, 조사하기 같은 Candidate를 만듦
→ 불가능하거나 위험한 Candidate를 제거
→ Utility 또는 Neural Policy가 남은 후보의 순위를 매김
→ 서버가 Goal·Target·경로·자원을 다시 확인
→ 통과하면 Skill 실행
```

실제 사건 처리에서는 관측으로 얻은 Knowledge가 Goal을 활성화할 수 있다. 이 문서는 행동 선택의 기준인 Goal을 먼저 설명한 뒤, 그 판단에 쓰는 Knowledge와 Target을 설명한다.

현재 Phase 3A는 위 흐름의 `발소리를 들음 → 조사 Goal 활성화`까지 실제 Unreal 경로에 연결한다. Phase 3B는 `Target 선택 → Candidate 생성 → Utility 선택 → Commit → Skill 결과 처리`를 연결한다.

---

<a id="product-goal"></a>
# 1. 제품 목표

## 1.1 만들려는 것

NPC가 상황마다 긴 조건문으로 움직이는 대신 다음 구조로 판단하게 만든다.

```text
게임 규칙이 목적과 가능한 행동을 정함
→ Utility 또는 AI가 가능한 행동의 순위를 매김
→ 서버가 안전을 확인하고 실행
```

제품에서 기대하는 결과는 다음과 같다.

- NPC는 자신이 실제로 알 수 있는 정보만 사용한다.
- 같은 상황에서는 같은 안전 규칙을 적용한다.
- 행동 선호는 데이터로 개선할 수 있다.
- 잘못된 AI 응답이 와도 게임 규칙과 서버 권한을 우회하지 못한다.
- Python에서 학습한 계약과 Unreal에서 실행하는 계약이 같아야 한다.

## 1.2 이 시스템이 하지 않는 것

- 신경망이 퀘스트나 장기 Goal을 임의로 만들거나 완료하지 않는다.
- 신경망이 숨은 플레이어 위치나 미래 입력을 보지 않는다.
- 신경망이 이동 벡터, 애니메이션, Hitbox, Damage를 직접 실행하지 않는다.
- 모델 출력만으로 서버 자원이나 Gameplay 상태를 바꾸지 않는다.
- 새 Role이나 Skill이 자동으로 좋은 품질을 낸다고 보장하지 않는다.

---

<a id="goal"></a>
# 2. Goal: 지금 무엇을 이루려는가

Goal은 NPC가 지금 이루려는 목적이다. Goal Manager는 어떤 Goal을 활성화할지, 어느 단계에 있는지, 언제 중단하거나 다시 시작할지를 관리한다.

V1은 네 가지 Goal만 사용한다.

1. `IdleObserve`: 주변을 살피며 대기
2. `InvestigateDisturbance`: 이상한 소리나 사건을 조사
3. `EnforceBoundary`: 경계 위반을 확인하고 대응
4. `CombatEngage`: 전투 상황에 대응

한 NPC는 동시에 Active Goal을 하나만 가진다. 더 중요한 Goal이 들어오면 현재 Goal을 중단, 보관 또는 종료할 수 있다. 신경망은 Goal을 만들지 않고 Active Goal 안에서 다음 행동만 고른다.

Goal의 각 단계에는 완료 event와 timeout이 있다. Timeout은 정상 완료 신호가 오지 않았을 때 쓰는 fallback이다.

- event가 도착했다는 이유만으로 timer를 먼저 취소하지 않는다.
- guard와 effect가 승인되고 phase 이동이나 종료가 실제 확정된 뒤에만 기존 timer를 취소한다.
- guard가 실패하거나 필요한 provider가 없으면 현재 상태와 timer를 유지한다.
- 저장과 복원은 현재 Goal·phase·revision이 정확히 맞을 때만 적용한다.

정확한 우선순위, 중단·재개, timer와 저장 규칙은 [세부 기술 요구사항 §5](technical-requirements.md#5-goal-manager)를 따른다. 실제 transition의 단일 원본은 `contracts/current/goal_registry_v1.yaml`이다.

---

<a id="belief"></a>
# 3. Knowledge: NPC는 무엇을 알고 있는가

Knowledge는 NPC가 직접 보거나 듣거나 전달받아 보관하는 정보다. 현재 코드와 Schema에서는 호환성을 위해 `Belief`라는 이름을 사용한다. NPC의 전술 판단은 실제 월드 전체가 아니라 자신의 Knowledge를 사용한다.

예를 들어 플레이어가 시야에서 사라지면 NPC는 플레이어의 현재 위치를 계속 알 수 없다. 마지막으로 본 위치는 기억할 수 있지만, 벽 뒤의 실제 이동을 따라가면 안 된다.

| 정보 | 전술 판단에 사용 가능 | 사용 금지 |
|---|---|---|
| 현재 보이는 Actor | 현재 관측 범위 안의 위치·상태 | 관측이 끊긴 뒤의 숨은 위치 |
| 발소리 | 들린 위치, 종류, 발생 시각 | 발소리 주인의 현재 실제 위치 |
| 마지막으로 본 위치 | 저장된 위치, 나이, 신뢰도 | 원래 Actor의 최신 위치로 몰래 갱신 |
| 엄폐물·Smart Object | 사용 가능 여부와 예약 상태 | 관계없는 숨은 Actor 상태 |

서버는 충돌, 피해, Actor 생존처럼 게임 판정에 필요한 실제 상태를 사용할 수 있다. 하지만 그 실제 상태를 NPC의 전술 선택이나 조준 갱신에 다시 넣어서는 안 된다.

정확한 정보 경계는 [세부 기술 요구사항 §8](technical-requirements.md#8-hidden-information-경계)를 따른다.

---

<a id="target"></a>
# 4. Target: 누구·무엇·어디를 대상으로 하는가

Target은 행동 문장의 목적어다. 적만 뜻하지 않는다.

- 누구: Actor, 플레이어, NPC
- 무슨 사건: 발소리, 경고 event
- 어디: 마지막으로 본 위치, Waypoint, World Position
- 무엇을 사용할지: 엄폐물, Smart Object
- 대상 없음: 대기처럼 목적어가 없는 행동

## 4.1 Target Slot은 NPC 수가 아니다

Target Slot은 **NPC 한 명이 이번 판단에서 고려할 대상을 담는 로컬 자리**다. 전역 Entity 번호가 아니다.

```text
NPC A의 이번 판단
slot 0  = Player Entity
slot 1  = Footstep SoundEvent
slot 2  = CoverSlot
slot 16 = NoTarget
```

다음 판단에서 같은 Target이 같은 slot을 유지할 수는 있지만, `slot 0은 항상 플레이어`라고 가정하지 않는다. 실제 신원은 Target의 종류, ID, 생성 세대와 revision으로 확인한다.

V1은 일반 Target 16개와 `NoTarget` 1개를 합쳐 총 17개 slot을 사용한다.

정확한 Target의 종류와 식별 정보는 [세부 기술 요구사항 §2](technical-requirements.md#2-typed-target)를, 정렬과 slot 유지 규칙은 [§3](technical-requirements.md#3-target-universe와-slotter)을 따른다.

---

<a id="candidate"></a>
# 5. Skill과 Candidate: 무엇을 할 수 있는가

Skill은 실행할 행동이고, Candidate는 `Skill + Target Slot` 조합이다.

```text
Attack      + Player Entity  → 가능할 수 있음
Investigate + Footstep       → 가능할 수 있음
TakeCover   + CoverSlot      → 가능할 수 있음
Idle        + NoTarget       → 가능할 수 있음
Attack      + Footstep       → 불가능
```

V1은 Skill 16개와 Target Slot 17개를 조합해 항상 272개 행을 만든다.

```text
16 Skill × 17 Target Slot = 272 Candidate row
```

272개를 모두 실행할 수 있다는 뜻은 아니다. 고정된 표를 만들어야 Python, ONNX와 Unreal이 같은 순서와 크기를 사용할 수 있다. 불가능한 행은 삭제하지 않고 Hard Mask로 제외한다.

Hard Mask가 판단하는 것은 “가능한가”다.

- 이 Skill이 이 Target 종류를 받을 수 있는가
- 현재 Goal이 이 Skill을 허용하는가
- Target이 아직 유효한가
- 장비, 권한, 생존, 자원 조건을 만족하는가
- 현재 행동을 중단할 수 있는가

“가까우니 공격이 더 좋다” 같은 선호는 Hard Mask가 아니라 Policy가 판단한다.

정확한 Candidate layout과 허용표는 [세부 기술 요구사항 §4](technical-requirements.md#4-candidate-universe)를 따른다.

---

<a id="selection"></a>
# 6. 행동 선택: 무엇이 가능하고 무엇이 더 좋은가

행동 선택은 두 단계다.

1. 게임 규칙이 불가능한 Candidate를 제거한다.
2. Utility 또는 Neural Policy가 남은 Candidate의 순위를 매긴다.

| 담당 | 결정하는 것 | 결정하지 않는 것 |
|---|---|---|
| Goal Manager | 현재 목적과 허용 Skill | Candidate 선호 점수 |
| Candidate Builder | 실행 가능한 Candidate | 어떤 Candidate가 더 자연스러운지 |
| Utility·Neural Policy | valid Candidate의 순위 | Goal 생성, 안전 규칙, 자원 예약 |
| Commit Coordinator | 최신 상태 검증과 실행 확정 | 장기 행동 선호 학습 |

Neural Policy가 timeout, 오류, OOD 또는 낮은 신뢰도로 거부되면 다음 순서로 처리한다.

1. 잘못되거나 늦은 응답을 폐기한다.
2. 현재 Skill을 계속해도 안전하면 새 결정을 준비하는 동안 유지한다.
3. 최신 Knowledge와 Goal로 Candidate를 다시 만든다.
4. 결정론적 Utility Baseline이 valid Candidate를 고른다.
5. Utility도 실패하면 Goal Registry의 fallback을 사용한다.

현재 AI 모델과 Unreal NNE adapter는 아직 없다. 따라서 지금 검증된 것은 generated 입출력 계약과 일부 안전 Core이며, Neural 행동 품질이 아니다.

정확한 score, Switch Cost, OOD와 Calibration 규칙은 [세부 기술 요구사항 §6](technical-requirements.md#6-neural-policy와-post-process)를 따른다.

---

<a id="commit"></a>
# 7. Commit과 실행: 서버가 마지막으로 확인한다

Policy의 선택은 제안일 뿐이다. 서버의 Commit Coordinator가 최신 상태를 확인하고 성공해야 실제 Skill이 시작된다.

Commit은 짧은 작업이다.

```text
선택 결과 수신
→ 최신 Goal 확인
→ Target의 종류와 식별 정보·유효성 확인
→ Skill 조건 확인
→ 필요한 자원 예약
→ 최종 확인
→ Skill 시작
```

확인 중 하나라도 실패하면 새로 만든 예약과 변경만 되돌리고 기존 Skill은 유지한다. 이미 오래 실행된 월드 전체를 되돌리는 작업은 아니다.

서버는 NPC마다 Commit 가능한 요청을 한 개 이하로 유지한다. 더 최신 상태가 생기면 오래된 응답은 실행하지 않는다. 피해, 이동 권한, 아이템, 관계와 Goal도 서버만 변경한다.

Commit 뒤 Skill Executor가 이동, 시선, 대화, 엄폐와 전투를 실제로 수행한다. 신경망은 매 frame 이동이나 애니메이션을 직접 출력하지 않는다.

정확한 deadline, stale 판정, 자원 예약과 실패 코드는 [세부 기술 요구사항 §7](technical-requirements.md#7-비동기-추론과-atomic-commit)을 따른다.

---

<a id="boss-pattern"></a>
# 8. 보스 공격은 한 단계 더 선택한다

일반 Policy가 먼저 `Attack(Target)`을 고른다. Boss Pattern Selector는 그 공격 안에서 어떤 authored 공격 절차를 사용할지 추가로 고른다.

```text
공통 Policy가 Attack(Player)을 선택
→ 보스의 현재 Pattern 중 실행 가능한 것만 남김
→ Utility 또는 Pattern Neural Policy가 순위를 매김
→ 부모 Attack과 Pattern을 함께 다시 검증하고 Commit
→ StateTree/C++가 예고, 공격, 회복을 실행
```

`QuickSlash`나 `DelayedHeavy`는 Target Slot이 아니다. 같은 플레이어를 공격하는 서로 다른 보스 전용 절차다. 일반 Candidate 272개와 보스 Pattern 최대 32개는 별도 공간으로 유지한다.

모델은 valid Pattern의 순위와 제한된 parameter만 제안한다. Damage, Hitbox 시점, 공격 가능 시간, Root Motion과 interrupt 규칙은 Data Asset과 실행기가 소유한다.

플레이어가 공격 예고를 본 뒤에는 Pattern을 마음대로 바꾸지 않는다. 허용된 추적 범위 안에서만 Target을 따라가며, 일반적인 플레이어 이동이나 새 AI 점수는 실행 중 Pattern 변경 사유가 아니다.

현재는 다음 범위만 PASS다.

- Pattern 선택·Commit·Handoff 안전 Core
- production StateTree asset과 producer adapter
- encounter Pawn/AIController physical assembly
- fixture-backed Session Host의 Commit 뒤 StateTree start handoff

다음은 아직 없다.

- Knowledge·Goal·Target을 공급하는 production authority provider
- production PatternSet과 selector trigger
- authored transition과 실제 Montage·Hitbox·Damage·Root Motion
- replication과 save/load

따라서 현재 PASS는 “보스 전투 전체 완성”이 아니라 “안전한 실행 기반 phase 완료”를 뜻한다.

정확한 Boss Pattern 계약은 [세부 기술 요구사항 §4.7](technical-requirements.md#47-보스-전용-neural-pattern-selector)과 [Boss Pattern Appendix](contract-appendices.md#bp-auto-generated-boss-pattern-selector-계약)를 따른다.

---

<a id="learning"></a>
# 9. 학습과 평가는 같은 계약을 쓴다

학습 데이터는 Runtime과 같은 Target 순서, Candidate Mask, 정규화와 Switch Cost를 사용한다. Python과 Unreal이 다른 의미로 데이터를 해석하면 모델을 배포하지 않는다.

데이터는 세 종류로 관리한다.

| 종류 | 용도 |
|---|---|
| Silver | 절차 생성, Teacher LLM과 자동 라벨로 학습량 확보 |
| Gold | 사람이 검토한 정답·선호·평가 기준 |
| Live | 실제 플레이에서 수집한 rollout, 이상 행동과 개입 기록 |

Teacher LLM은 개발용 Silver label만 만든다. Runtime에서 NPC를 조종하지 않으며, Calibration·General Test·OOD·Critical 평가의 유일한 정답이 될 수 없다.

배포 전에는 최소한 다음을 확인한다.

- 숨은 정보가 모델 입력에 들어가지 않았는가
- Train, Calibration, Test가 같은 scenario를 공유하지 않는가
- Mask와 Candidate 순서가 Runtime과 같은가
- Python, ONNX Runtime과 Unreal NNE가 같은 결과를 내는가
- 안전 위반이 0건인가
- Utility Baseline보다 품질과 성능이 나빠지지 않는가

현재 대량 Dataset, 학습 모델, ONNX/NNE adapter, OOD·Calibration과 최종 품질 증거는 준비되지 않았다.

정확한 Dataset, Teacher, loss, export와 평가 규칙은 [세부 기술 요구사항 §9](technical-requirements.md#9-데이터학습baseline)과 [Appendix E](contract-appendices.md#appendix-e-품질안전성능-승인-기준)를 따른다.

---

<a id="status"></a>
# 10. 현재 구현 상태와 완료 조건

<a id="phase-3a"></a>
## 10.1 소리를 듣고 조사 Goal을 시작한다 (Phase 3A — 완료)

Phase 3A는 NPC가 평소 주변을 살피다가 유효한 소리를 들으면 조사 Goal을 시작하는 기능이다.

```text
IdleObserve/Observe
→ 소리 정보를 Knowledge에 저장
→ 현재 정보 번호와 소리 위치를 다시 확인
→ 새 Goal과 Timer를 별도로 준비
→ 준비가 끝나면 InvestigateDisturbance/Orient로 한 번 전환
```

구현된 내용:

- 게임 시작 시 `IdleObserve/Observe`를 활성화한다.
- 소리의 정확한 정보 번호, 대상 식별 정보와 X/Y/Z 위치를 다시 확인한다.
- 오래된 소리, 바뀐 위치, 잘못된 대상과 중복 실행을 거부한다.
- 새 Goal 준비에 실패하면 기존 Goal과 실행 중인 Skill을 유지한다.
- 전환에 성공하면 이전 `Idle`·`TurnTo`와 대기 중인 결정을 정리한다.
- Host·Timer·Knowledge를 제거하거나 다시 등록하면 이전 callback과 Timer를 폐기한다.
- 새 연결 발급에 실패하면 기존의 유효한 연결은 그대로 유지한다.
- `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea` 실행기가 준비돼 있다.

검증 결과:

- Python 계약 검사 `39/39`
- Goal 전환 검사 `23/23`
- Knowledge 검사 `6/6`
- Shipping 집중 검사 `10/10`
- 전체 `AINativeNPC` 검사 `134/134`
- Data Validation `291 assets`, 오류 `0`, 경고 `0`
- 최종 Round 6 독립 확인: 관련 파일 `116/116`, 문제 `0`

<a id="phase-3b"></a>
## 10.2 목표에 맞는 행동을 고르고 다음 단계로 진행한다 (Phase 3B — 다음 작업)

Phase 3B는 활성 Goal이 직접 Target과 행동을 고르고 Skill 결과를 다음 Goal 단계로 연결하는 기능이다.

```text
Goal
→ Knowledge
→ Target
→ Candidate
→ Utility 선택
→ Commit
→ Skill 실행
→ Skill 결과
→ 다음 Goal 단계
```

Phase 3B는 다음 순서로 구현한다.

1. 활성 Goal과 현재 단계가 사용할 Target을 결정한다.
2. Knowledge와 Goal-owned Target으로 17개 Target 자리를 만든다.
3. `Skill × Target` 272개 Candidate와 실행 가능 여부를 만든다.
4. Candidate별 Feature를 하나의 변하지 않는 판단 정보로 확정한다.
5. 결정론적 Utility가 실행 가능한 Candidate 하나를 고른다.
6. Commit Coordinator가 최신 Goal·Target·Knowledge·Skill 조건을 다시 확인한다.
7. Commit 성공 시에만 one-shot 실행 권한을 발행하고 Skill을 시작한다.
8. Skill 결과를 정확한 Goal·단계·결정·Skill·Target에 묶어 Goal Runtime에 전달한다.
9. `Orient → Navigate → Search → Return`을 진행하고 끝나면 `IdleObserve`로 돌아간다.

Phase 3B의 안전 기준:

- 오래된 판단은 실행하지 않는다.
- Candidate와 Feature는 같은 Target 목록과 실행 가능 표를 공유한다.
- 실행 가능한 Candidate가 없으면 Skill을 시작하지 않는다.
- Commit 실패는 기존 Goal과 실행 상태를 손상시키지 않는다.
- 같은 결정이나 Skill 결과는 한 번만 적용한다.
- component 제거·재등록 뒤에는 이전 판단과 callback을 다시 사용하지 않는다.

이번 Phase 3B 범위에는 `InvestigateDisturbance/Resolve`, 다른 Goal 전체, Cover·SmartObject 실제 예약, Neural 모델, 전체 중단 경쟁, 저장·복원과 replication이 포함되지 않는다.

정확한 작업 순서와 파일은 [구현 계획의 Phase 3B](implementation-plan.md#phase-3b)와 [Unreal 구현 계획의 Phase 3B](unreal-implementation-plan.md#phase-3b)를 따른다.

## 10.3 현재 상태

| 영역 | 상태 | 쉬운 해석 |
|---|---|---|
| Schema·Registry·generated binding | PASS | 정확한 타입과 표는 Python/C++에 동기화됨 |
| Goal Dispatcher·Timer Core | PASS | Goal 전환과 Timer Runtime이 구현됨 |
| Phase 3A: 소리 감지→조사 Goal 시작 | 완료 | 실제 Pawn·Controller·Knowledge 경로에서 검증됨 |
| Phase 3B: 행동 선택→실행→Goal 단계 진행 | 다음 작업 | 개별 Core는 있으나 production Goal 경로 연결이 필요함 |
| 일반 NPC Gameplay Goal FSM 전체 | 진행 중 | Phase 3B 뒤에도 다른 Goal·중단 경쟁·저장 기능이 남음 |
| Boss Pattern 안전 Core와 Host/start 기반 | 제한된 phase PASS | fixture-backed 실행 기반은 검증됨 |
| 실제 Boss 전투 효과 | HOLD | production selector, Montage, Hitbox, Damage 등이 없음 |
| Neural Policy·ONNX·NNE | HOLD | 실제 모델과 adapter가 없음 |
| 데이터 품질·성능·최종 Release | NO-GO | Dataset과 품질 증거가 없음 |

## 10.4 전체 일반 NPC Runtime 완료라고 말하려면

일반 NPC Runtime 완료에는 다음이 모두 필요하다.

1. Phase 3B의 Target→Candidate→Utility→Commit→Skill-result 연결
2. 나머지 guard와 effect의 실제 provider
3. 다른 Goal과 전체 중단 경쟁
4. save/load와 replication
5. Unreal Automation, Data Validation과 실제 gameplay smoke

AI 모델 Release에는 여기에 다음이 더 필요하다.

1. 잠긴 Dataset과 split 검증
2. 학습·Calibration·OOD asset
3. Python↔ONNX↔Unreal NNE parity
4. 안전·품질·성능 Gate
5. 최종 승인 기록

정적 계약 PASS, 일부 Automation PASS 또는 fixture-backed phase PASS만으로 전체 제품 완료를 선언하지 않는다.

---

<a id="references"></a>
# 11. 정확한 기술 자료를 찾는 곳

| 궁금한 내용 | 문서 |
|---|---|
| 제품 목적과 전체 판단 흐름 | 이 문서 |
| Goal 우선순위·phase·timer·save/load | [세부 기술 요구사항 §5](technical-requirements.md#5-goal-manager) |
| Target의 종류와 식별 정보 | [세부 기술 요구사항 §2](technical-requirements.md#2-typed-target) |
| Target 정렬·slot 선정 | [세부 기술 요구사항 §3](technical-requirements.md#3-target-universe와-slotter) |
| Candidate 272행·Hard Mask | [세부 기술 요구사항 §4](technical-requirements.md#4-candidate-universe) |
| Neural·Utility·OOD·fallback | [세부 기술 요구사항 §6](technical-requirements.md#6-neural-policy와-post-process) |
| stale·Commit·server authority | [세부 기술 요구사항 §7](technical-requirements.md#7-비동기-추론과-atomic-commit) |
| 숨은 정보 경계 | [세부 기술 요구사항 §8](technical-requirements.md#8-hidden-information-경계) |
| Dataset·Teacher·학습·export | [세부 기술 요구사항 §9](technical-requirements.md#9-데이터학습baseline) |
| 정확한 ID·Tensor·Registry row·KPI | [Contract Appendices](contract-appendices.md) |
| 구현 phase와 작업 순서 | [Implementation Plan](implementation-plan.md) |
| Unreal class·asset·test | [Unreal Implementation Plan](unreal-implementation-plan.md) |

기계 판독 계약의 원본은 다음 파일이다.

```text
contracts/current/ai_native_npc_schema_v2_0.yaml
contracts/current/skill_registry_v1.yaml
contracts/current/goal_registry_v1.yaml
contracts/current/test_taxonomy_v1.yaml
contracts/current/boss_pattern_contract_v1.yaml
```

이 파일에서 생성된 Python/C++ 계약은 수동으로 수정하지 않는다.
