# Unreal에서 NPC 판단을 연결하는 구현 계획
## AI Native NPC · Unreal Engine 5.7 · NeuralGame

- 문서 버전: **v0.4.16**
- 개정일: **2026-08-12**
- 현재 상태: **NPC가 소리를 듣고 조사를 시작하는 연결은 완료됐다. 다음 작업은 행동 선택부터 실행 결과까지 실제 게임 흐름으로 잇는 것이다.**
- 실제 Unreal 프로젝트: `D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject`
- Unreal 모듈: `Source/NeuralGame/AINativeNPC`

이 문서의 역할은 **Unreal에서 일반 NPC 판단 흐름을 연결하는 순서, 담당 파일, 실패 시 보존할 상태, 완료 조건을 정하는 것**이다.

처음 읽는 사람은 다음 여섯 곳을 먼저 읽는다.

- [꼭 알아야 할 말](#glossary)
- [현재 상태](#current-status)
- [전체 흐름](#runtime-flow)
- [Phase 3A](#phase-3a)
- [Phase 3B](#phase-3b)
- [검증 순서](#verification-order)

이 문서는 Unreal 연결 방법을 설명한다.

정확한 자료형, ID, 배열 크기와 계산식은 [세부 기술 요구사항](technical-requirements.md)과 [계약 부록](contract-appendices.md)이 소유한다.

---

<a id="overview"></a>
# 0. 한눈에 보기

<a id="glossary"></a>
## 0.1 꼭 알아야 할 말

| 용어 | 쉬운 뜻 | 코드에서 자주 보이는 이름 |
|---|---|---|
| Pawn | 게임 세계에 실제로 놓이는 NPC 몸체 | `AAINativeNPCGuardPawn` |
| Controller | NPC의 감지와 제어를 담당하는 객체 | `AAINativeNPCGuardController` |
| Component | Pawn이나 Controller에 붙어 한 가지 책임을 맡는 부품 | Goal Host, Knowledge, Skill Executor |
| Goal | 여러 행동에 걸쳐 유지되는 목적 | `Goal`, `GoalFsmRuntime` |
| Knowledge | NPC가 직접 얻어 보관하는 정보 | `Knowledge`, 기존 계약의 `Belief` |
| Target | 행동이 향하는 사람, 사물 또는 위치 | `TypedTarget`, `FTargetHandleWire` |
| Skill | 회전, 이동, 조사처럼 실행기가 수행하는 한 행동 | `SkillExecutor`, `StateTree` |
| Candidate | Skill과 Target을 합친 행동 후보 | `FCandidateRow` |
| Feature | 현재 상황을 선택기가 읽을 수 있는 숫자로 표현한 값 | `FDecisionFeatureBuilder` |
| Snapshot | 한 번의 판단에 사용하도록 고정한 상태 | `FFinalizedDecisionSnapshot` |
| Utility | 규칙과 가중치로 Candidate 점수를 계산하는 선택기 | `FUtilitySelection` |
| Commit | 최신 상태를 다시 확인하고 실행을 확정하는 짧은 서버 작업 | `FDecisionCommitCoordinator` |
| Host | 실제 Pawn 안에서 여러 Runtime과 Component를 연결하는 소유자 | `UAINativeNPCGoalHostComponent` |
| Core | Unreal 객체 수명과 분리해 같은 입력에 같은 결과를 내는 로직 | `FTargetSlotter`, `FCandidateBuilder` |
| Runtime | 게임 실행 중 Goal, Timer와 행동 상태를 관리하는 코드 | Goal Runtime, Gameplay Runtime |
| Neural Policy | 학습된 모델로 실행 가능한 Candidate의 선호 순위를 매기는 선택기 | ONNX 모델, NNE Adapter |
| revision | 같은 상태가 바뀔 때 증가하는 번호 | Goal revision, Knowledge revision |
| generation | Target이나 단계가 새 수명으로 교체될 때 증가하는 번호 | Target generation, phase generation |
| epoch | Component가 다시 등록될 때 바뀌는 등록 세대 번호 | registration epoch |
| lease | 현재 등록 세대에서 사건을 받을 수 있는 권한 | event sink lease |
| callback | 실행 결과를 소유자에게 돌려주는 완료 통지 함수 | Skill result callback |
| RED | 필요한 실제 게임 연결이 비어 있어 새 검사가 예상대로 실패하는 상태 | Phase 3B 전용 RED |
| GREEN | 최소 구현 뒤 같은 검사가 통과하는 상태 | Phase 3B 전용 GREEN |

<a id="current-status"></a>
## 0.2 현재 상태

| 기능 | 상태 | 지금 할 수 있는 일 | 다음 작업 |
|---|---|---|---|
| 계약과 생성 코드 | 완료 | Python과 C++이 같은 Goal·Skill 규칙을 사용한다. | 계약이 바뀔 때 생성 결과와 사용처를 함께 갱신한다. |
| Goal과 Timer Core | 완료 | Goal 상태와 단계 시간을 결정론적으로 처리한다. | Phase 3B의 Skill 결과를 이 Runtime에 연결한다. |
| Phase 3A | 완료 | 유효한 소리를 들으면 조사 Goal의 `Orient` 단계를 시작한다. | 완료 상태를 유지한다. |
| 5개 Skill 실행 | 완료 | `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea`를 실행한다. | Goal이 고른 Candidate에서 실행 권한을 발행하도록 연결한다. |
| Phase 3B | 다음 작업 | 개별 Target·Candidate·Feature·Utility·Commit Core를 사용할 수 있다. | 실제 Goal Host 안에서 전체 흐름을 연결한다. |
| 일반 NPC 전체 Goal Runtime | 진행 중 | Phase 3A 범위의 실제 Pawn 흐름을 검증할 수 있다. | 다른 Goal, 전체 중단 경쟁, 저장과 복제를 추가한다. |
| 보스 공격 패턴 | 제한된 실행 기반 완료 | 고정된 테스트 자산으로 Commit부터 StateTree 시작까지 확인한다. | 실제 전투 선택 정보와 공격 효과를 연결한다. |
| Neural Policy | 후속 작업 | 생성된 입력 계약과 Utility 경로를 사용할 수 있다. | ONNX, NNE Adapter, Calibration과 OOD를 구현한다. |

<a id="runtime-flow"></a>
## 0.3 전체 판단 흐름

```text
Goal
→ Knowledge
→ Goal이 소유한 Target
→ Candidate
→ Feature
→ Utility 또는 Neural 선택
→ Commit
→ Skill 실행
→ Skill 결과
→ 다음 Goal 단계
```

각 단계의 역할은 다음과 같다.

| 단계 | 역할 | 결과 |
|---|---|---|
| Goal | NPC가 지금 이루려는 목적과 현재 단계를 정한다. | 현재 Goal, 단계, Target 정책 |
| Knowledge | NPC가 직접 얻은 정보를 보관한다. | 현재 보이는 대상, 들은 소리, 마지막으로 확인한 위치 |
| Target | 이번 행동이 향할 대상을 정한다. | 종류, 식별 정보, 위치 또는 대상 참조 |
| Candidate | Skill과 Target을 조합한다. | 실행 가능한 행동 후보 목록 |
| Feature | 현재 상황을 고정된 숫자 묶음으로 만든다. | Candidate와 결속된 판단 Snapshot |
| 선택 | 실행 가능한 Candidate의 선호 순위를 매긴다. | 선택된 Candidate와 파라미터 제안 |
| Commit | 서버가 최신 Goal·Target·조건을 다시 확인한다. | 한 번만 사용할 수 있는 실행 권한 |
| Skill | 이동, 회전, 조사 같은 행동을 수행한다. | 성공, 실패 또는 중단 |
| Goal 진행 | Skill 결과를 현재 Goal에 적용한다. | 다음 단계, 재계획 또는 종료 |

## 0.4 단계 이름의 관계

이 프로젝트에는 두 종류의 단계 이름이 있다.

| 이름 | 뜻 | 현재 상태 |
|---|---|---|
| 제품 Phase 0 | 일반 NPC가 플레이어를 보고 듣고 판단하고 행동하는 최소 게임 흐름 | 구현 중 |
| 제품 Phase 1 | 전체 Skill, Neural, 멀티플레이와 품질 검증을 포함한 확장 범위 | 후속 작업 |
| Runtime Phase 3A | 소리를 Knowledge에 저장하고 조사 Goal을 시작하는 연결 작업 | 완료 |
| Runtime Phase 3B | Goal이 행동을 고르고 Skill 결과로 다음 단계에 진행하는 연결 작업 | 다음 작업 |

Runtime Phase 3A와 3B는 제품 Phase 0 안의 세부 작업이다.

## 0.5 목차

0. [한눈에 보기](#overview)
1. [소리를 듣고 행동하기까지](#example-flow)
2. [이번 구현의 범위](#scope)
3. [실제 프로젝트와 계약 원본](#project-roots)
4. [문서부터 구현까지의 작업 순서](#work-order)
5. [소리를 듣고 조사 Goal을 시작한다](#phase-3a)
6. [Goal에 맞는 행동을 고르고 다음 단계로 진행한다](#phase-3b)
7. [Unreal 구성요소의 역할](#components)
8. [Neural Policy와 학습 모델](#neural)
9. [보스 공격 패턴](#boss-pattern)
10. [서버, 저장과 성능](#server-save-performance)
11. [파일별 작업 위치](#file-map)
12. [검증 순서와 완료 조건](#verification-order)
13. [주요 위험과 대응](#risks)
14. [권한 문서와 자동 생성 참고](#references)

---

<a id="example-flow"></a>
# 1. 소리를 듣고 행동하기까지

이 장은 전체 판단 흐름을 발소리 조사 예시로 설명한다.

## 1.1 소리를 들으면 Knowledge가 생긴다

1. Unreal Perception이 소리 자극을 받는다.
2. Knowledge가 소리 식별 정보, 위치, 세기와 발생 시점을 저장한다.
3. 저장이 끝나면 Knowledge revision이 증가한다.
4. Goal Host는 저장이 끝난 사건만 받는다.

## 1.2 Goal이 조사 목적과 위치를 소유한다

1. Goal Host는 현재 소리 식별 정보와 revision을 다시 확인한다.
2. Host는 소리 위치를 조사 Goal이 소유하는 `WorldPosition` Target으로 캡처한다.
3. Host는 `InvestigateDisturbance/Orient`를 준비한다.
4. 새 Goal과 Timer 준비가 모두 끝나면 현재 Goal을 한 번 교체한다.

## 1.3 Phase 3B가 행동을 고른다

1. 현재 Goal과 단계가 사용할 Target을 결정한다.
2. Target Slotter가 최대 16개 Target과 `NoTarget` 한 자리를 만든다.
3. Candidate Builder가 16개 Skill과 17개 Target 자리를 조합한다.
4. 실행 조건을 통과한 Candidate만 선택 대상으로 남는다.
5. Feature Builder가 Candidate와 입력값을 하나의 Snapshot으로 확정한다.
6. Utility가 실행 가능한 Candidate 하나를 고른다.
7. Commit Coordinator가 최신 상태를 다시 확인한다.
8. Commit 성공 시 Skill을 시작한다.

## 1.4 Skill 결과가 Goal을 진행한다

```text
Orient
→ Navigate
→ Search
→ Return
→ IdleObserve
```

각 Skill 결과는 Goal, 단계, Decision, Skill과 Target 식별 정보에 묶인다.

Goal Runtime은 현재 상태와 정확히 일치하는 결과를 한 번만 적용한다.

---

<a id="scope"></a>
# 2. 이번 구현의 범위

이 장은 제품 Phase 0과 Phase 1의 경계를 정한다.

## 2.1 제품 Phase 0

제품 Phase 0의 목표는 **일반 NPC가 플레이어를 보고 듣고, 조사 목적을 세우고, 허용된 행동을 골라 실행하는 최소 게임 흐름**이다.

| 항목 | Phase 0 범위 |
|---|---|
| NPC Profile | Guard 1개 |
| Goal | `IdleObserve`, `InvestigateDisturbance` |
| 실행 Skill | `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea` |
| 제어 Candidate | `ContinueCurrentAction` |
| 주요 Target | `Entity`, `SoundEvent`, `LastKnownPosition`, `Waypoint`, `WorldPosition`, `NoTarget` |
| 정책 | 결정론적 Utility |
| 실행 권한 | 서버 GameThread의 짧은 Commit |
| 배열 구조 | 17개 Target 자리와 272개 Candidate |

Phase 0에서 구현하는 5개 Skill만 실행 가능 상태로 둔다.

나머지 Skill 행은 mask로 제외하며, 272개 배열 크기는 Phase 1에서도 유지한다.

## 2.2 Phase 0에서 확인할 게임 흐름

| 상황 | 기대 결과 |
|---|---|
| 정면에서 조용히 접근 | Sight Knowledge가 Entity Target을 만든다. |
| 뒤에서 발소리 발생 | SoundEvent를 저장하고 조사 Goal을 시작한다. |
| 시야에서 사라짐 | 마지막으로 확인한 위치를 별도 Target으로 보관한다. |
| 조사 완료 | `Orient → Navigate → Search → Return` 뒤 Idle로 돌아간다. |
| 판단 중 피격 | 이전 판단을 종료하고 긴급 판단을 시작한다. |
| 경로 계산 실패 | Skill 실패 이유를 Goal에 전달해 정해진 회복 경로를 사용한다. |

## 2.3 제품 Phase 1

제품 Phase 1은 다음 기능을 추가한다.

- 전체 Skill과 Target 종류
- Cover와 SmartObject 예약
- 여러 Goal의 우선순위와 중단 경쟁
- Neural Policy, Calibration, OOD와 Utility fallback
- 멀티플레이 서버 권한과 복제
- 저장과 불러오기
- 30~50 NPC 성능 검증
- 학습 데이터 수집과 품질 승인

## 2.4 허용 범위

| 구분 | 허용 범위 |
|---|---|
| 모델 | 게임 규칙이 허용한 Candidate의 선호 순위를 매긴다. |
| Goal | Gameplay Runtime이 생성하고 진행한다. |
| 감정과 관계 | Gameplay Runtime이 사건을 적용한다. |
| 이동 | Unreal Navigation과 Skill이 수행한다. |
| 숨은 대상 위치 | NPC가 마지막으로 확인한 Snapshot만 사용한다. |
| 전투 효과 | Combat Runtime과 Data Asset이 소유한다. |

---

<a id="project-roots"></a>
# 3. 실제 프로젝트와 계약 원본

이 장은 현재 작업하는 저장소와 파일의 책임을 구분한다.

## 3.1 현재 작업 위치

| 용도 | Windows 경로 | WSL 경로 |
|---|---|---|
| 계약과 문서 | 해당 Git 작업 트리 | `/home/namingsense/AI-Native-NPC` |
| Unreal 프로젝트 | `D:\Codex-cli\NeuralProject\NeuralGame` | `/mnt/d/Codex-cli/NeuralProject/NeuralGame` |
| Unreal C++ | `Source\NeuralGame\AINativeNPC` | `/mnt/d/Codex-cli/NeuralProject/NeuralGame/Source/NeuralGame/AINativeNPC` |
| Unreal Asset | `Content\AINativeNPC` | `/mnt/d/Codex-cli/NeuralProject/NeuralGame/Content/AINativeNPC` |

Unreal 프로젝트는 Engine 5.7을 사용한다.

이 기능과 직접 관련된 플러그인은 `StateTree`와 `GameplayStateTree`다.

## 3.2 계약의 원본

| 정보 | 원본 |
|---|---|
| Tensor, Enum, Candidate 배열 | `contracts/current/ai_native_npc_schema_v2_0.yaml` |
| Skill 의미와 실행값 | `contracts/current/skill_registry_v1.yaml` |
| Goal, 단계와 전환 | `contracts/current/goal_registry_v1.yaml` |
| 품질 평가 상황 | `contracts/current/test_taxonomy_v1.yaml` |
| 보스 공격 패턴 | `contracts/current/boss_pattern_contract_v1.yaml` |

## 3.3 문서의 책임

| 문서 | 답하는 질문 |
|---|---|
| [제품 요구사항](requirements.md) | 무엇을 만들고 왜 만드는가? |
| [세부 기술 요구사항](technical-requirements.md) | Runtime은 정확히 어떻게 동작하는가? |
| [공통 구현 계획](implementation-plan.md) | 데이터, 모델과 Runtime을 어떤 순서로 만드는가? |
| 이 문서 | Unreal에서 어떤 파일을 어떤 순서로 연결하는가? |
| [계약 부록](contract-appendices.md) | 정확한 ID, 크기, 수치와 승인 기준은 무엇인가? |

값이 다르면 기계 판독 계약, 세부 기술 요구사항, 제품 요구사항, 이 문서 순서로 판단한다.

## 3.4 생성 코드

계약 저장소는 다음 산출물을 만든다.

```text
generated/cpp/AINativeNPCContracts.generated.h
generated/cpp/AINativeNPCGoalGameplaySemantics.generated.h
generated/cpp/AINativeNPCSkillExecutionSemantics.generated.h
generated/python/ai_native_npc_contracts_generated.py
generated/python/ai_native_npc_goal_gameplay_semantics_generated.py
generated/python/ai_native_npc_skill_execution_semantics_generated.py
```

Unreal 프로젝트는 같은 이름의 C++ 산출물을 `Source/NeuralGame/AINativeNPC/Generated`에서 사용한다.

계약을 바꾼 작업은 두 위치의 byte 일치를 확인한다.

---

<a id="work-order"></a>
# 4. 문서부터 구현까지의 작업 순서

모든 기능은 문서, 하네스, 구현, 검증 순서로 진행한다.

## 4.1 기본 순서

1. 사람이 읽는 문서에 목표와 범위를 적는다.
2. 입력, 결과와 처리 순서를 적는다.
3. 실패 시 보존할 상태를 적는다.
4. 완료 조건을 적는다.
5. 새 설계를 사용자에게 설명하고 확인받는다.
6. Registry, 생성 코드와 테스트 하네스를 갱신한다.
7. 새 테스트가 실패하는 RED 상태를 확인한다.
8. 승인된 범위의 최소 구현으로 GREEN을 만든다.
9. 계약, Build, 변경 기능 검사, 관련 기능 검사와 Asset 검사 순서로 검증한다.

구현 중 새 판단이 필요하면 문서와 하네스를 먼저 갱신한다.

사용자 확인이 다음 실제 게임 연결 구현의 시작 조건이다.

## 4.2 현재 `main`에서 실행할 계약 검사

```bash
python3 tools/generate_goal_gameplay_semantics_v1.py --check
python3 tools/generate_skill_execution_semantics_v1.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/validate_anpc_capture_v2.py tests/fixtures/phase0_golden.anpcv2
```

현재 `main`에서는 위 네 명령을 사용한다.

전체 문서 하네스와 release 묶음은 `archive/full-harness-v0.4.6` 보관 branch가 소유한다.

## 4.3 계약 변경 확인 목록

- Registry와 생성 결과가 일치한다.
- Python과 C++의 Enum, 배열 크기와 Hash가 일치한다.
- Unreal의 Generated 사본이 계약 저장소와 일치한다.
- 기존 Golden fixture가 다시 통과한다.
- 새 계약에 필요한 RED 테스트가 먼저 실패한다.
- 문서의 링크와 자동 생성 영역이 최신이다.

---

<a id="phase-3a"></a>
# 5. 소리를 듣고 조사 Goal을 시작한다 (Phase 3A, 완료)

Phase 3A의 역할은 **유효한 소리를 Knowledge에 저장하고, 그 위치를 조사 Goal이 소유하는 Target으로 캡처해 `InvestigateDisturbance/Orient`를 시작하는 것**이다.

## 5.1 입력과 결과

Host는 다음 구성에서만 준비 상태가 된다.

| 소유자 | 필요한 구성 |
|---|---|
| Guard Pawn | Goal Host, Goal Timer, Skill Executor, Skill Handoff가 각각 한 개 |
| Guard Controller | Perception, Knowledge, StateTree가 각각 한 개 |
| 공통 조건 | 서버 권한, 정확한 Pawn·Controller 연결, 등록된 Component, 준비된 StateTree |

Host의 준비 조건은 위 표의 구성과 정확히 일치하는 것이다.

| 구분 | 내용 |
|---|---|
| 입력 | 서버가 받은 유효한 Hearing 자극 |
| Knowledge 결과 | 소리 식별 정보, 위치, 세기, 시점과 새 revision |
| Goal 결과 | `InvestigateDisturbance/Orient` Active Goal |
| Target 결과 | Goal 수명 동안 유지되는 `WorldPosition` Snapshot |
| Timer 결과 | 현재 Goal과 단계에 묶인 한 번의 Timer |

## 5.2 처리 순서

1. Controller가 Hearing 자극을 Knowledge에 저장한다.
2. Knowledge가 새 revision과 사건을 Goal Host에 전달한다.
3. Host가 현재 Knowledge registration과 event sink lease를 확인한다.
4. Host가 현재 revision, 소리 식별 정보와 X·Y·Z 위치의 정확한 일치를 다시 확인한다.
5. Host가 조사 Goal의 위치 Target을 준비한다.
6. Host가 새 Goal Runtime 상태를 준비한다.
7. Host가 새 단계 Timer를 현재 새 Goal token에 묶어 건다.
8. 실행 중인 이전 Idle 또는 TurnTo를 중단한다.
9. 이전 Goal의 pending Decision을 종료한다.
10. 준비한 새 Goal Runtime을 현재 Goal로 한 번 교체한다.

## 5.3 실패 시 보존할 상태

| 실패 시점 | 보존 상태 | 처리 |
|---|---|---|
| Knowledge 재확인 실패 | 기존 Goal, Timer와 실행 중 Skill | 준비 중인 전환을 폐기한다. |
| Target 준비 실패 | 기존 Goal, Timer와 실행 중 Skill | 준비 중인 위치 Target을 폐기한다. |
| Goal 준비 실패 | 기존 Goal, Timer와 실행 중 Skill | 준비 중인 Goal을 폐기한다. |
| Timer 준비 실패 | 기존 Goal, Timer와 실행 중 Skill | 준비 중인 Goal과 Timer를 폐기한다. |
| 이전 Skill 중단 실패 | 기존 Goal과 실행 중 Skill | 새 Timer를 취소하고 재계획을 요청한다. |
| pending Decision 종료 실패 | 기존 Goal | 새 Timer를 취소하고 중단된 이전 Skill 없이 재계획한다. |
| 전환 게시 뒤 Skill 시작 실패 | 새 Goal | 현재 단계에서 재계획하거나 Timer를 기다린다. |

## 5.4 Goal과 Timer Core의 역할

| 기능 | 현재 구현 |
|---|---|
| 생성 계약 조회 | Goal Registry의 생성된 행과 순서를 사용한다. |
| Goal 상태 | 한 세션 안에서 `Active`, `Suspended`, `Terminal`을 관리한다. |
| 단계 시작 | 단계의 전체 시간을 Timer에 설정한다. |
| 같은 단계 재개 | 저장한 남은 시간을 다시 사용한다. |
| 단계 재시작 | 해당 단계의 전체 시간을 다시 설정한다. |
| Timer 만료 | 현재 token에 묶인 사건을 한 번 queue한다. |
| 오래된 Timer | 현재 Goal과 다른 token을 폐기한다. |
| 저장 Snapshot | 버전과 현재 token을 함께 검사한다. |
| 종료 Snapshot | Runtime 수명과 분리된 값으로 보관한다. |
| guard와 effect | 현재 Host가 필요한 사실과 적용 권한을 제공할 때만 전환한다. |
| 중첩 호출 | Pump 실행 중 들어온 Queue, Pump와 수명 변경 요청을 거부한다. |
| Unreal 시간 | 같은 World의 `GetTimeSeconds()`와 `FTimerManager`를 사용한다. |

Pause와 time dilation은 Unreal World 시간 규칙을 따른다.

Goal 전환 전용 Skill 중단의 결과 전달 횟수는 0회다.

## 5.5 수명과 재등록

- event sink는 사건을 전달하는 동안 지역 shared reference로 Knowledge 객체의 수명을 유지한다.
- Host는 readiness를 확인할 때마다 Knowledge registration epoch와 sink lease를 다시 비교한다.
- epoch와 lease ID가 최댓값에 도달하면 해당 수명에서는 새 ID 발급을 중단한다.
- 새 lease 발급이 실패하면 현재 유효한 lease를 유지한다.
- Host와 Timer 중 하나가 등록 해제되면 예약된 wakeup, pending expiry, Timer Runtime과 Goal Runtime을 폐기한다.
- Knowledge가 등록 해제되면 먼저 sink lease를 끊고 연결된 Host를 teardown한다.
- 재등록은 새 assembly 설치 절차를 다시 통과해야 한다.

## 5.6 구현 파일

| 역할 | 파일 |
|---|---|
| 실제 Pawn | `Execution/AINativeNPCGuardPawn.h/.cpp` |
| 실제 Controller와 Perception | `Knowledge/AINativeNPCGuardController.h/.cpp` |
| Knowledge 저장 | `Knowledge/TypedTargetKnowledgeComponent.h/.cpp` |
| Goal 소유자 | `Execution/AINativeNPCGoalHostComponent.h/.cpp` |
| Goal 상태 | `Goal/GoalFsmRuntime.h/.cpp` |
| Timer | `Goal/GoalTimerComponent.h/.cpp`, `Goal/GoalTimerRuntime.h/.cpp` |
| Skill 실행 | `Execution/AINativeNPCSkillExecutorComponent.h/.cpp` |
| StateTree 전달 | `Execution/AINativeNPCSkillHandoffComponent.h/.cpp` |
| 생성 계약 | `Generated/AINativeNPCGoalGameplaySemantics.generated.h` |

## 5.7 허용 범위

| 포함 | 후속 작업 |
|---|---|
| 생성 계약의 초기 Goal과 Hearing 전환 | 전체 Goal catalog와 중단 경쟁 |
| 한 NPC 세션의 Goal 상태 | 여러 비활성 Goal collection과 전체 archive |
| 단계 Timer와 오래된 callback 차단 | 전체 save/load |
| Goal이 소유하는 조사 위치 | 일반 Waypoint, CoverSlot과 SmartObject producer |
| Phase 3A의 guard와 effect | 다른 gameplay guard와 effect 제공자 |
| 5개 Skill 실행 기반 | PatternSet, selector trigger와 전체 combat effect |

## 5.8 완료 조건과 증거

Phase 3A는 다음 검증을 순서대로 통과했다.

| 순서 | 결과 |
|---:|---|
| Contract | 39/39 |
| Editor build | 성공 |
| Shipping 일반 NPC | 10/10 |
| Goal FSM | 23/23 |
| Knowledge | 6/6 |
| 전체 AINativeNPC Automation | 134/134 |
| Data Validation | 291 assets, error 0, warning 0 |
| 독립 재검토 | 문제 0 |

이 수치는 Phase 3A 범위의 완료 증거다.

전체 일반 NPC Goal Runtime과 제품 Release는 별도 완료 조건을 사용한다.

---

<a id="phase-3b"></a>
# 6. Goal에 맞는 행동을 고르고 다음 단계로 진행한다 (Phase 3B, 다음 작업)

Phase 3B의 역할은 **현재 Goal이 사용할 Target과 Skill을 고르고, Commit된 Skill 결과로 조사 Goal의 다음 단계에 진행하는 것**이다.

## 6.1 목표

```text
Goal
→ Knowledge
→ Goal-owned Target
→ Candidate
→ Feature
→ Utility
→ Commit
→ Skill
→ Skill result
→ Goal phase progression
```

완료 후 `InvestigateDisturbance`는 `Orient → Navigate → Search → Return`을 진행하고 `IdleObserve`로 돌아간다.

## 6.2 기존 Core와 남은 연결

| 단계 | 기존 Core | Phase 3B 작업 |
|---|---|---|
| 전체 연결 | `FAINativeNPCGameplayCommitAuthority` | 한 NPC 세션의 판단, Commit과 결과 전달을 소유한다. |
| Goal | `FGoalFsmRuntime` | 현재 Goal과 단계의 판단 요청을 시작한다. |
| Knowledge | `UAINativeNPCKnowledgeComponent` | 같은 revision의 immutable 판단 입력을 제공한다. |
| Target | `FTargetSlotter` | Goal이 소유한 행동 Target과 Candidate에 사용할 수 있는 현재 Knowledge Target을 한 목록으로 조립한다. |
| Candidate | `FCandidateBuilder` | 현재 Goal과 단계의 Skill 허용 범위를 제공한다. |
| Feature | `FDecisionFeatureBuilder` | Target과 Candidate에 결속된 Snapshot을 확정한다. |
| 선택 | `FUtilitySelection` | `GuardPhase0UtilityV1` Profile로 한 Candidate를 고른다. |
| Commit | `FDecisionCommitCoordinator` | 실제 Gameplay 권한 제공자를 연결한다. |
| 실행 | `UAINativeNPCSkillExecutorComponent` | Commit된 one-shot 실행 권한을 소비한다. |
| Goal 진행 | `FGoalFsmRuntime` | Skill 결과를 현재 Goal token과 전환 규칙에 적용한다. |

## 6.3 처리 순서

1. Goal Host가 현재 Goal token과 Knowledge revision을 캡처한다.
2. Goal-owned Target resolver가 현재 단계의 주 Target을 만든다.
3. Target Slotter가 17개 Target 자리를 확정한다.
4. Candidate Builder가 272개 행과 실행 가능 표를 만든다.
5. Feature Builder가 Candidate와 입력값을 하나의 Snapshot으로 묶는다.
6. Utility가 실행 가능한 Candidate 하나를 선택한다.
7. Host가 새 Decision ID와 deadline을 발행한다.
8. Commit Coordinator가 현재 Goal, Target, Knowledge와 Skill 조건을 다시 확인한다.
9. Commit 성공 시 one-shot 실행 권한을 만든다.
10. Skill Executor가 권한을 소비하고 Skill을 시작한다.
11. Skill Executor가 성공, 실패 또는 중단 결과를 발행한다.
12. Goal Host가 결과의 Goal, 단계, Decision, Skill과 Target 식별 정보를 확인한다.
13. Goal Runtime이 결과를 한 번 적용해 다음 단계 또는 회복 경로를 선택한다.

각 단계의 주 Target은 다음과 같다.

| Goal 단계 | 주 Target | Target을 만든 시점 |
|---|---|---|
| `Orient` | 조사 위치 | 유효한 소리로 조사 Goal을 시작할 때 |
| `Navigate` | 같은 조사 위치 | `Orient`에서 받은 Goal Target을 유지한다. |
| `Search` | 같은 조사 위치 | `Navigate`에서 받은 Goal Target을 유지한다. |
| `Return` | 집으로 돌아갈 위치 | NPC 세션을 시작할 때 Pawn 위치를 캡처한다. |

소리 식별 정보의 역할은 조사 위치의 출처 확인이다.

Candidate에는 Goal이 소유한 조사 위치를 Target으로 사용한다.

Candidate가 모두 실행 불가면 현재 Goal을 유지한다.

이 경우 현재 판단은 Candidate 단계에서 끝난다.

## 6.4 실패 시 보존할 상태

| 실패 | 보존 상태 | 결과 |
|---|---|---|
| Target 조립 실패 | 현재 Goal과 실행 중 Skill | 이번 판단을 종료한다. |
| Candidate가 모두 실행 불가 | 현재 Goal과 실행 중 Skill | 현재 단계에서 재계획하거나 Timer를 기다린다. |
| Feature 확정 실패 | 현재 Goal과 실행 중 Skill | 준비 중인 판단을 폐기한다. |
| Utility 실패 | 현재 Goal과 실행 중 Skill | 선택 실패를 기록하고 재계획한다. |
| Commit 재검사 실패 | 현재 Goal과 실행 상태 | 이번 시도가 얻은 자원만 되돌리고 선택 결과를 폐기한다. |
| Skill 시작 실패 | 현재 Goal | 전용 실패 결과를 Goal에 한 번 전달한다. |
| 오래된 Skill callback | 현재 Goal과 새 Skill | callback을 폐기한다. |
| component 재등록 뒤 이전 결과 | 새 assembly 상태 | 이전 epoch의 결과를 폐기한다. |

## 6.5 안전 기준

| 검증 조건 | 기대 결과 |
|---|---|
| Candidate와 Feature의 Target 목록 | 같은 Snapshot을 공유한다. |
| 선택된 Candidate | Candidate mask에서 실행 가능 상태다. |
| Decision ID | 현재 Commit 가능 ID와 같다. |
| Goal token | 현재 Goal instance, revision, phase와 phase generation이 같다. |
| Target | 종류, stable ID, generation과 revision이 같다. |
| Knowledge | Skill이 요구하는 현재 정보와 일치한다. |
| Commit | 한 Decision을 세션 수명 동안 한 번 terminal 처리한다. |
| Skill 결과 | 현재 Goal과 정확히 일치할 때 한 번 적용한다. |
| 결과 종류 | 성공, 실패와 중단을 생성 계약의 서로 다른 사건으로 처리한다. |
| Timer와 Skill 결과 경쟁 | 먼저 유효하게 적용된 한 사건만 현재 단계를 바꾼다. |
| 외부 callback | 호출 전에 판단 식별 정보를 게시하고, 호출 뒤 현재 상태를 다시 확인한다. |
| callback 재진입 | 같은 public 작업 안의 중첩 호출을 거부한다. |
| ID 최댓값 | 새 ID 발급을 중단하고 현재 상태를 보존한다. |

## 6.6 하네스와 RED 테스트

구현 전에 다음 실패를 자동검사로 고정한다.

1. Goal-owned Target resolver 호출 시 명시적 실패
2. 현재와 다른 이전 Goal token
3. 현재와 다른 이전 Knowledge revision
4. Target generation 변경
5. Candidate Hash와 Feature Hash 불일치
6. 실행 가능한 Candidate 0개
7. 같은 Decision 중복 Commit
8. Commit callback 재진입
9. Skill callback 중복 전달
10. Skill 결과의 Target 불일치
11. Host teardown 뒤 callback
12. component 재등록 뒤 이전 epoch 결과
13. ID 최댓값 경계
14. Skill 시작 실패 뒤 Goal 보존
15. Timer와 Skill 결과가 같은 단계에서 경쟁하는 상황

Phase 3B의 실제 Guard Pawn 연결은 아직 구현 전이다.

새 실패 검사는 이 빈 연결을 확인하며 먼저 실패해야 한다.

기존 Core 단위 테스트 결과는 별도 증거로 유지한다.

## 6.7 구현 순서

1. 문서에 Goal이 소유한 Target을 만드는 기능의 입력과 결과를 확정한다.
2. Host가 한 번의 판단에 사용할 고정 Snapshot을 확정한다.
3. 실제 Commit 권한 제공자인 `IDecisionCommitAuthority` 구현의 책임을 확정한다.
4. Skill 결과를 Goal Runtime에 전달할 계약상 사건을 확정한다.
5. 위 계약을 사용자에게 설명하고 확인받는다.
6. Registry, 생성 코드와 고의 실패 검사를 갱신한다.
7. Phase 3B 전용 실패 검사가 예상대로 실패하는지 확인한다.
8. Target → Candidate → Feature → Utility 연결을 구현한다.
9. Commit → Skill 시작 연결을 구현한다.
10. Skill 결과 → Goal 단계 진행을 구현한다.
11. 최소 구현 뒤 같은 검사가 통과하는지 확인한다.
12. 전체 검증 순서를 실행한다.

## 6.8 허용 범위

| 이번 Phase 3B에 포함 | 후속 작업 |
|---|---|
| `IdleObserve`와 `InvestigateDisturbance`의 선택 흐름 | 다른 Goal 전체 |
| `Orient`, `Navigate`, `Search`, `Return` | `Resolve` 단계의 실제 권한 제공자 |
| 결정론적 Utility | Neural Policy |
| 현재 구현된 5개 Skill | 나머지 Skill |
| Goal-owned 위치와 Home Waypoint | Cover와 SmartObject 예약 |
| 같은 서버 세션의 중복 차단 | crash 이후에도 유지되는 중복 차단 |
| 한 NPC의 Goal 진행 | 전체 arbitration과 save/load |

## 6.9 완료 조건

Phase 3B는 다음 조건을 모두 만족하면 완료다.

- 실제 Guard Pawn에서 전체 흐름이 실행된다.
- `Orient → Navigate → Search → Return → IdleObserve`가 자동으로 진행된다.
- 각 단계는 Registry가 허용한 Skill만 실행한다.
- 오래된 판단과 callback의 Skill 시작은 0건이다.
- 같은 Decision과 Skill 결과의 중복 적용은 0건이다.
- Commit 실패가 현재 Goal과 실행 상태를 보존한다.
- teardown과 재등록 뒤 이전 epoch 결과의 적용 건수는 0이다.
- Timer와 Skill 결과가 경쟁해도 Goal 단계는 한 번만 바뀐다.
- 계약 검사, Editor build, 변경 기능 검사, 관련 기능 검사와 Asset 검사가 모두 통과한다.
- 실제 Guard Pawn을 Editor나 실행 게임에서 한 번 끝까지 동작시키는 확인이 통과한다.
- 최신 source에 결속된 독립 재검토에서 blocker가 0개다.

---

<a id="components"></a>
# 7. Unreal 구성요소의 역할

이 장은 각 구성요소가 소유하는 일과 전달하는 결과를 정한다.

## 7.1 Perception과 Knowledge

Knowledge의 역할은 **NPC가 직접 얻은 사실을 현재 상태와 사건 기록으로 보관하는 것**이다.

- Sight는 현재 보이는 Entity를 갱신한다.
- Hearing은 변경되지 않는 SoundEvent를 추가한다.
- Sight Lost는 마지막으로 확인한 위치를 만든다.
- 각 사실은 source, age, confidence와 TTL을 가진다.
- Knowledge는 정보 저장이 끝난 뒤 event sink를 호출한다.
- Knowledge 입력의 허용 범위는 현재 관측과 마지막으로 확인한 Snapshot이다.

## 7.2 Goal Runtime

Goal Runtime의 역할은 **현재 목적, 단계, 수명과 전환을 관리하는 것**이다.

- Active Goal은 한 개다.
- Suspended Goal은 남은 Timer와 함께 보존할 수 있다.
- Terminal Goal의 수명은 종료 상태로 고정된다.
- 단계 전환은 생성된 guard 순서를 따른다.
- effect는 먼저 intent를 만들고 Host가 안전하게 적용한다.

## 7.3 Target Slotter

Target Slotter의 역할은 **Knowledge와 Goal의 Target을 고정된 17개 자리에 배치하는 것**이다.

- 일반 Target은 최대 16개다.
- 마지막 자리는 `NoTarget`이다.
- 현재 Skill Target과 Goal 주 Target 같은 필수 항목을 먼저 배치한다.
- 같은 Target은 한 번만 배치한다.
- 정렬 결과는 같은 입력에서 항상 같다.
- 필수 Target이 범위를 넘으면 선택을 보류한다.

정확한 정렬과 quota는 [세부 기술 요구사항의 Target 장](technical-requirements.md#3-target-universe와-slotter)이 소유한다.

## 7.4 Candidate Builder

Candidate Builder의 역할은 **16개 Skill과 17개 Target 자리를 조합해 272개 행동 후보를 만드는 것**이다.

- 각 Candidate는 Skill ID와 Target 자리로 결정된다.
- 게임 규칙은 실행 가능한 Candidate만 표시한다.
- 현재 Goal과 단계가 Skill 허용 범위를 제공한다.
- Target 종류, 시야, 자원과 실행 조건을 확인한다.
- 실행 중인 행동의 Continue 조건을 별도로 확인한다.
- 결과는 Candidate Hash와 함께 고정된다.

## 7.5 Feature Builder

Feature Builder의 역할은 **Candidate를 고를 때 사용할 숫자와 mask를 하나의 변경 불가능한 Snapshot으로 확정하는 것**이다.

- Target 결과와 Candidate 결과를 함께 받는다.
- 생성 계약의 정규화 규칙을 사용한다.
- 모든 실수 입력의 유한성을 확인한다.
- Canonical bytes와 입력 Hash를 만든다.
- Candidate Hash와 입력 Hash를 결속한다.

## 7.6 Utility 선택

Utility의 역할은 **실행 가능한 Candidate의 점수를 계산하고 하나를 선택하는 것**이다.

- Skill별 기본 점수와 Candidate Feature 가중치를 사용한다.
- 실행 중인 행동을 바꾸는 비용을 적용한다.
- Candidate mask를 통과한 행만 평가한다.
- 같은 입력은 같은 결과를 만든다.
- 동점 규칙은 계약이 정한 순서를 따른다.

Phase 3B는 Utility를 실제 게임 경로의 선택기로 사용한다.

## 7.7 Commit Coordinator

Commit Coordinator의 역할은 **선택 시점과 실행 시점 사이에 바뀐 상태를 찾아 안전한 Skill 시작을 확정하는 것**이다.

Commit은 다음 값을 다시 확인한다.

- Decision ID와 deadline
- Candidate Hash와 입력 Hash
- Goal instance, revision, phase와 generation
- Target stable ID, generation과 Knowledge 유효성
- Skill precondition과 현재 시야 조건
- 필요한 자원 예약
- 서버 권한

모든 검사를 통과하면 Commit은 Skill 시작 제안을 한 번 실행한다.

## 7.8 Skill Executor와 StateTree

Skill Executor의 역할은 **Commit된 Skill을 실행하고 정확한 결과를 한 번 반환하는 것**이다.

| Skill | 역할 |
|---|---|
| `Idle` | 현재 위치에서 관찰 상태를 유지한다. |
| `TurnTo` | Target 방향을 바라본다. |
| `Approach` | Target Snapshot까지 이동한다. |
| `Investigate` | 위치와 방향을 확인한다. |
| `SearchArea` | 정해진 검색 지점을 순서대로 방문한다. |

실행 시작 때 Target 위치를 다시 캡처한 뒤 해당 Skill 수명 동안 고정한다.

새 Perception은 다음 판단에 사용한다.

---

<a id="neural"></a>
# 8. Neural Policy와 학습 모델

Neural Policy의 역할은 **게임 규칙이 허용한 Candidate 안에서 더 자연스러운 행동의 순위를 매기는 것**이다.

## 8.1 현재 상태

제품 Phase 0의 실제 연결은 Utility를 사용한다.

ONNX ModelData와 NNE Adapter는 제품 Phase 1의 구현 대상이다.

## 8.2 구현할 순서

1. Dataset Record와 split 규칙을 고정한다.
2. Python과 Unreal이 같은 Feature 값을 만드는지 확인한다.
3. 작은 fixture 모델을 학습하고 ONNX로 내보낸다.
4. Unreal NNE가 입력과 출력 descriptor를 확인한다.
5. `B=1,2,4,8` batch의 ORT와 NNE 결과를 비교한다.
6. 모델 실패 시 같은 Snapshot의 Utility 결과를 사용한다.
7. Calibration과 OOD asset을 추가한다.
8. 패키징한 Development와 Shipping 게임에서 최소 실제 경로를 끝까지 실행한다.

## 8.3 Unreal 연결 조건

| 조건 | 검증 |
|---|---|
| NNE runtime | 프로젝트 설정의 허용 목록과 정확히 일치한다. |
| ModelData | cook 결과에 포함된다. |
| 입력·출력 | 이름, 자료형, 차원과 크기가 Manifest와 같다. |
| Model Instance | 각 worker가 전용 Instance를 사용한다. |
| 숫자 결과 | 모든 값이 유한하다. |
| 실패 | Utility fallback 또는 안전한 대기 상태를 사용한다. |
| 플랫폼 | 지원 대상마다 build와 최소 실제 경로 실행을 따로 통과한다. |

Unreal은 Model Bundle의 Manifest에서 다음 계약 식별 정보를 확인한다.

```json
{
  "schema_version": "2.0.0",
  "schema_sha256": "a7791004de0534f29198ebf5eaaff7cd764185b59b05446d419f5d0a3303f886",
  "skill_registry_version": "1.0.0",
  "skill_registry_sha256": "ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d",
  "goal_registry_version": "1.1.0",
  "goal_registry_sha256": "d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e"
}
```

Manifest의 전체 필드와 정확한 Tensor 크기, 허용 오차는 [세부 기술 요구사항](technical-requirements.md)과 [계약 부록](contract-appendices.md)이 소유한다.

---

<a id="boss-pattern"></a>
# 9. 보스 공격 패턴

보스 공격 패턴의 역할은 **공통 `Attack(Entity)` Candidate가 선택된 뒤 실제 공격 절차 하나를 고르는 것**이다.

## 9.1 공통 판단과의 관계

```text
공통 판단
→ Attack(Entity) Commit
→ Boss Pattern 선택
→ Pattern Commit
→ StateTree 실행
→ Telegraph
→ Active
→ Recovery
```

Pattern 선택은 기존 공통 Target 자리와 Candidate 수를 그대로 사용한다.

## 9.2 현재 구현

- Pattern 정의와 Set Data Asset
- 32개 Pattern 자리와 mask
- Utility 선택과 Neural 출력 정리 Core
- Commit, one-shot handoff와 실행 Session
- StateTree `PreAttackTurn` 시작 경로
- 고정 테스트 자산을 사용한 Pawn과 Controller assembly

## 9.3 후속 작업

| 필요한 기능 | 완료 조건 |
|---|---|
| 실제 PatternSet과 selector trigger | 전투 상태가 현재 Snapshot을 제공한다. |
| 실제 공격 효과 | Montage, Hitbox, Damage와 Root Motion이 Data Asset 규칙을 따른다. |
| 중단 처리 | 허용된 interrupt 지점과 cleanup 순서를 지킨다. |
| 복제 | Pattern ID, 시작 시각, 단계와 cue를 클라이언트에 보낸다. |
| 저장 | 세션, executor와 현재 단계가 같은 Snapshot으로 복원된다. |

보스 패턴의 정확한 수치와 mask는 [보스 계약](../../contracts/current/boss_pattern_contract_v1.yaml)과 [계약 부록](contract-appendices.md)이 소유한다.

---

<a id="server-save-performance"></a>
# 10. 서버, 저장과 성능

이 장은 제품 Phase 1에서 연결할 권한, 저장과 부하 기준을 요약한다.

## 10.1 서버와 클라이언트

서버는 판단과 실행을 소유한다.

클라이언트는 확정된 결과를 화면에 표시한다.

| 서버 상태 | 클라이언트 표시 상태 |
|---|---|
| Perception과 Knowledge | 현재 Skill |
| Goal과 Target 선택 | 필요한 Target 표시 정보 |
| Candidate와 Policy | 서버 시작 시각 |
| Commit과 자원 예약 | 애니메이션 상태 |
| Skill 결과 | 종료 결과와 cue |

## 10.2 저장과 불러오기

저장 대상은 Goal instance와 revision, Knowledge source와 age, active Skill Snapshot이다.

불러온 뒤 만료된 Knowledge를 정리하고 자원 예약을 다시 얻는다.

판단 중인 Neural 요청은 새 상태로 다시 요청한다.

## 10.3 성능 검증

성능 검증은 다음 조건을 고정한다.

- 같은 프레임에서 판단하는 NPC 수
- 초당 판단 요청 수
- batch 크기
- CPU, GPU와 build 설정
- Runtime과 precision
- 요청부터 Commit까지의 지연 시간

정확한 목표값은 [계약 부록의 품질·안전·성능 기준](contract-appendices.md#appendix-e-품질안전성능-승인-기준)이 소유한다.

---

<a id="file-map"></a>
# 11. 파일별 작업 위치

이 장은 실제 `NeuralGame` 파일과 Phase 3B에서 수정할 위치를 보여 준다.

## 11.1 실제 일반 NPC Runtime

```text
Source/NeuralGame/AINativeNPC/
  Generated/
  Knowledge/
  Goal/
  Target/
  Candidate/
  Feature/
  Policy/
  Execution/
  Dataset/
  Tests/
```

## 11.2 Phase 3B의 중심 파일

| 역할 | 파일 |
|---|---|
| 실제 게임 경로의 소유자 | `Execution/AINativeNPCGoalHostComponent.h/.cpp` |
| Goal 상태와 사건 | `Goal/GoalFsmRuntime.h/.cpp` |
| Knowledge 입력 | `Knowledge/TypedTargetKnowledgeComponent.h/.cpp` |
| Target 자리 | `Target/TargetSlotter.h/.cpp` |
| Candidate | `Candidate/CandidateBuilder.h/.cpp` |
| Feature Snapshot | `Feature/DecisionFeatureBuilder.h/.cpp` |
| Utility | `Policy/UtilitySelection.h/.cpp` |
| Commit | `Policy/DecisionCommitCoordinator.h/.cpp` |
| Skill 시작 | `Execution/AINativeNPCSkillExecutorComponent.h/.cpp` |
| StateTree 전달 | `Execution/AINativeNPCSkillHandoffComponent.h/.cpp` |
| 테스트 | `Tests/*.cpp` |

새 클래스를 추가하기 전에 기존 Host와 Core의 책임으로 구현할 수 있는지 확인한다.

새 책임이 필요하면 문서와 하네스에 먼저 추가한다.

## 11.3 Unreal Asset

| 역할 | 현재 Asset |
|---|---|
| 일반 NPC Skill handoff | `Content/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff.uasset` |
| 보스 실행 StateTree | `Content/AINativeNPC/BossPattern/StateTree/ST_BossPatternExecution.uasset` |
| 보스 Pawn | `Content/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterPawn.uasset` |
| 보스 Controller | `Content/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterAIController.uasset` |

Asset 변경은 Editor와 GameDevMCP를 사용하고 재시작 뒤 다시 읽어 영속성을 확인한다.

---

<a id="verification-order"></a>
# 12. 검증 순서와 완료 조건

검증은 계약에서 실제 게임 흐름으로 범위를 넓힌다.

## 12.1 실행 순서

각 검사의 대상과 통과 의미는 다음과 같다.

| 검사 | 확인하는 내용 |
|---|---|
| 계약과 생성 결과 일치 | Registry와 생성된 Python·C++이 같은 규칙과 값을 가진다. |
| Editor build | 현재 C++와 Unreal 설정으로 Editor 실행 파일을 만들 수 있다. |
| 변경 기능 Automation | 이번에 바꾼 기능의 좁은 자동검사가 통과한다. |
| 관련 기능 묶음 Automation | 변경과 연결된 기능을 함께 실행해 기존 동작을 유지한다. |
| 전체 `AINativeNPC` Automation | AI Native NPC 자동검사 전체가 통과한다. |
| Data Validation | Unreal 프로젝트 Asset의 설정과 참조가 유효하다. |
| 실제 게임 흐름 확인 | Editor 또는 실행 게임에서 최소 실제 경로가 끝까지 동작한다. |
| 독립 재검토 | 최신 source에 고정된 별도 검토 결과가 문제 0개다. |

검증은 다음 순서로 진행한다.

1. 계약과 생성 결과 일치
2. Unreal Editor build
3. 변경 기능 Automation
4. 관련 기능 묶음 Automation
5. 전체 `AINativeNPC` Automation
6. Data Validation
7. 실제 게임 흐름 확인
8. 최신 source에 결속된 독립 재검토

각 단계는 앞 단계가 통과한 뒤 시작한다.

## 12.2 현재 Unreal 명령 인터페이스

| 목적 | 명령 또는 필터 |
|---|---|
| Editor build | `Build.bat NeuralGameEditor Win64 Development -Project="D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject" -WaitMutex -NoHotReloadFromIDE` |
| 일반 NPC shipping focused | `Automation RunTests AINativeNPC.Shipping.GeneralNPC` |
| Goal FSM | `Automation RunTests AINativeNPC.GoalFsm` |
| 전체 | `Automation RunTests AINativeNPC` |
| Data Validation | `-run=DataValidation -AllAssets -ProjectOnly` |

Windows 실행기는 Unreal Engine 5.7의 `UnrealEditor-Cmd.exe`를 사용한다.

자동화는 `-unattended -nop4 -nosplash -NullRHI -NoSound` 조건으로 실행한다.

`Intermediate/Hermes/Run*.bat`와 `RunNeuralGameTests.ps1`은 현재 검증 환경의 실행 도우미다.

계약 원본은 각 Automation filter와 검증 순서다.

## 12.3 기능별 검사

| 기능 | 핵심 검사 |
|---|---|
| Knowledge | 숨은 정보 사용, revision, TTL과 event sink 수명 |
| Goal | 전환 순서, Timer, suspend/resume와 이전 token |
| Target | 필수 Target, 중복 제거, 정렬과 overflow |
| Candidate | 272개 행, mask, Continue와 Hash |
| Feature | 정규화, 유한값, canonical bytes와 Candidate 결속 |
| Utility | mask 준수, switch cost와 동점 |
| Commit | 최신 상태, 중복 차단, rollback과 재진입 |
| Skill | one-shot 시작, Target Snapshot과 typed result |
| Phase 3B | 전체 단계 진행, teardown과 재등록 |
| Neural | Python·ONNX·NNE 결과 일치, cook와 fallback |

## 12.4 완료 판정

| 판정 | 뜻 |
|---|---|
| 계약 완료 | Registry와 생성 결과가 일치한다. |
| Core 완료 | 순수 C++ 단위 테스트가 통과한다. |
| 연결 단계 완료 | 실제 Pawn과 Host 경로의 변경 기능·관련 기능 검사가 통과한다. |
| 제품 완료 | 전체 기능, 품질, 성능, 저장, 복제와 Release 승인이 끝난다. |

각 완료 판정은 표에 적힌 범위에만 적용한다.

---

<a id="risks"></a>
# 13. 주요 위험과 대응

| 위험 | 영향 | 대응과 검증 |
|---|---|---|
| Target Slotter가 선호까지 결정함 | Utility와 Neural의 선택 범위가 줄어든다. | Slotter는 필수 배치와 정렬만 담당하고 Target Recall을 측정한다. |
| Python과 Unreal Feature가 다름 | 학습과 게임 결과가 달라진다. | 생성 코드, Golden fixture와 허용 오차 검사를 사용한다. |
| 숨은 정보를 사용함 | NPC가 관측하지 않은 위치를 알고 행동한다. | Entity와 LastKnownPosition을 분리하고 Hidden Leakage를 검사한다. |
| 오래된 판단이 도착함 | 이전 행동이 최신 행동을 덮어쓴다. | Decision ID, Goal token, Target generation과 deadline을 Commit에서 확인한다. |
| callback이 중복됨 | Goal 단계나 Skill이 두 번 진행된다. | 세션 수명의 terminal ledger와 one-shot 결과를 사용한다. |
| component가 재등록됨 | 이전 assembly 결과가 새 상태에 적용된다. | registration epoch와 lease를 모든 entry에서 확인한다. |
| Candidate 수가 많음 | NPC 수가 늘 때 지연 시간이 증가한다. | 고정 batch를 먼저 측정하고 Recall 기준을 지키며 최적화한다. |
| Animation 문제가 판단 문제처럼 보임 | 원인 분석이 어려워진다. | Skill 결과와 화면 표현 문제를 별도 태그로 기록한다. |
| 문서와 실제 파일이 다름 | 잘못된 위치와 명령으로 구현한다. | 실제 project root, ref와 파일 존재를 작업 시작 때 확인한다. |

---

<a id="references"></a>
# 14. 권한 문서와 자동 생성 참고

## 14.1 독자가 찾을 문서

| 궁금한 내용 | 문서 |
|---|---|
| 제품 목적과 쉬운 설명 | [제품 요구사항](requirements.md) |
| Goal, Target, Candidate와 Commit의 정확한 동작 | [세부 기술 요구사항](technical-requirements.md) |
| 데이터, 학습과 전체 구현 순서 | [공통 구현 계획](implementation-plan.md) |
| 정확한 ID, 수치와 품질 기준 | [계약 부록](contract-appendices.md) |
| 과거 Unreal 상태와 검증 기록 | [Unreal 구현 이력 v0.4.15](../history/unreal-implementation-history-v0.4.15.md) |
| 전체 문서 이력 | [문서 이력](../history/README.md) |

## 14.2 현재 계약 식별 정보

이 표는 생성 도구와 사용처의 일치를 확인하는 개발자용 정보다.

| 계약 | 버전 또는 SHA-256 |
|---|---|
| Requirements SHA-256 | `2bb7f2b8b11554125b12739f473b1c3619913607125a38aa533df997160bc1a2` |
| Technical Requirements SHA-256 | `7a581bbeb1b7a7b91e16006a908463a032fa28e734faa7d5c7305ba8d21121ae` |
| Schema YAML SHA-256 | `a7791004de0534f29198ebf5eaaff7cd764185b59b05446d419f5d0a3303f886` |
| Boss Pattern Contract SHA-256 | `e4f828c114fcc5db1cb04b5d0a6e2b3d29dada7e45c60a3dd18c674baa78c789` |
| Skill Registry SHA-256 | `ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d` |
| Goal Registry `1.1.0` SHA-256 | `d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e` |
| Test Taxonomy SHA-256 | `2c4f911c23c8502231351fd2a1ffc606a04c29c4c3e39ea384099462811dad79` |

## 14.3 자동 생성된 Goal 상태

아래 영역은 생성기가 관리한다.

본문의 쉬운 상태 설명은 [0.1 현재 상태](#current-status)에 있다.

<details>
<summary>개발자용 생성 상태 펼치기</summary>

<!-- BEGIN GOAL GAMEPLAY SEMANTICS V1 STATUS -->
### Bounded Goal gameplay authority status

- Goal Registry: `1.1.0` / SHA-256 `d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e`
- `GuardPhase0` bounded semantics authority: **PASS**
- Authority scope: 9 executable unique guards, 3 provider-unavailable unique guards, 12 executable transition bindings, 2 staged effects, 5 production executable Skills
- Gameplay Goal FSM: **HOLD** — complete guard catalog, other Goals, full Utility/Commit/Skill-result progression, arbitration/save archive, and product release are not claimed by this bounded authority PASS.
<!-- END GOAL GAMEPLAY SEMANTICS V1 STATUS -->

</details>

## 14.4 자동 생성된 품질 기준

아래 영역은 Test Taxonomy 생성물이 관리한다.

제품 승인에서는 [계약 부록의 품질·안전·성능 기준](contract-appendices.md#appendix-e-품질안전성능-승인-기준)과 함께 사용한다.

<details>
<summary>개발자용 품질 기준 펼치기</summary>

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

</details>
