# Unreal에서 NPC 판단을 연결하는 구현 계획
## AI Native NPC · Unreal Engine 5.7 · NeuralGame

- 문서 버전: **v0.4.17**
- 개정일: **2026-08-12**
- 현재 상태: **소리를 Knowledge에 저장하고 조사 Goal을 시작하는 bounded C++·Automation slice는 완료됐다. Quinn identity hardening, 전용 Test Level과 Manny·Quinn 제품 Play 경로는 아직 구현 전이다.**
- 실제 Unreal 프로젝트: `D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject`
- Unreal 모듈: `Source/NeuralGame/AINativeNPC`

이 문서의 역할은 **Unreal에서 일반 NPC 판단 흐름과 Test Level, Manny·Quinn, Blueprint·Asset을 만드는 순서, 담당 파일, 실패 시 보존할 상태, 완료 조건을 정하는 것**이다.

처음 읽는 사람은 다음 일곱 곳을 먼저 읽는다.

- [꼭 알아야 할 말](#glossary)
- [현재 상태](#current-status)
- [전체 흐름](#runtime-flow)
- [Phase 3A](#phase-3a)
- [Phase 3B](#phase-3b)
- [Test Level과 Manny·Quinn 제작](#unreal-build-guide)
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
| Phase 3A C++ 연결 | 완료 | native shipping Pawn을 사용하는 Automation fixture에서 유효한 소리를 저장하고 조사 Goal의 `Orient`를 시작한다. | 완료 상태를 유지한다. |
| 5개 Skill 실행 | 완료 | `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea`를 실행한다. | Goal이 고른 Candidate에서 실행 권한을 발행하도록 연결한다. |
| Phase 3B | 다음 작업 | 개별 Target·Candidate·Feature·Utility·Commit Core를 사용할 수 있다. | 실제 Goal Host 안에서 전체 흐름을 연결한다. |
| Unreal 실게임 수직 구성 | 제작 전 | Quinn 기본 Player Asset과 Manny 기본 Mesh·Animation을 재사용할 수 있다. | 전용 Test Level, 보이는 Manny Guard, Quinn 소음 입력과 디버그 표시를 만든다. |
| 일반 NPC 전체 Goal Runtime | 진행 중 | Phase 3A의 native Pawn Automation 경로를 검증할 수 있다. | Quinn·Test Level Play 경로, 다른 Goal, 전체 중단 경쟁, 저장과 복제를 추가한다. |
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
| Runtime Phase 3A C++ slice | fixture의 소리를 Knowledge에 저장하고 조사 Goal을 시작하는 연결 작업 | 완료 |
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
7. [Test Level과 Manny·Quinn을 직접 만든다](#unreal-build-guide)
8. [Unreal 구성요소의 역할](#components)
9. [Neural Policy와 학습 모델](#neural)
10. [보스 공격 패턴](#boss-pattern)
11. [서버, 저장과 성능](#server-save-performance)
12. [파일별 작업 위치](#file-map)
13. [검증 순서와 완료 조건](#verification-order)
14. [주요 위험과 대응](#risks)
15. [권한 문서와 자동 생성 참고](#references)

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
# 5. 소리를 듣고 조사 Goal을 시작한다 (Phase 3A bounded C++ slice, 완료)

Phase 3A bounded C++ slice의 역할은 **Automation fixture의 유효한 소리를 Knowledge에 저장하고, 그 위치를 조사 Goal이 소유하는 Target으로 캡처해 `InvestigateDisturbance/Orient`를 시작하는 것**이다.

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

Phase 3A bounded C++ slice는 다음 검증을 순서대로 통과했다.

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

이 수치는 Phase 3A bounded C++·Automation 범위의 완료 증거다.

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

<a id="unreal-build-guide"></a>
# 7. Test Level과 Manny·Quinn을 직접 만든다

이 장의 역할은 **현재 NeuralGame에서 플레이어와 NPC를 눈으로 확인할 수 있는 최소 Unreal 장면을 만드는 것**이다.

이 장만 따라가면 어떤 Asset이 이미 있고, 무엇을 새로 만들며, 현재 Play에서 어디까지 보여야 하는지 알 수 있다.

## 7.1 먼저 알아야 할 현재 상태

현재 C++ Runtime과 Unreal Asset의 완료 범위는 서로 다르다.

| 항목 | 현재 상태 | 구현자가 할 일 |
|---|---|---|
| Quinn Player | 기본 조작 Asset 있음·AI identity 없음 | 기존 Third Person Player를 재사용하고 AI 입력용 identity ingress를 추가한다. |
| Manny Mesh와 이동 Animation | 기본 Asset 있음 | native Guard Pawn이 읽는 Manny Visual Profile에 지정한다. |
| 일반 NPC native Pawn과 Controller | C++ 구현 있음 | C++ Class를 Test Level에 직접 배치한다. |
| 일반 NPC Skill StateTree | Asset 있음 | 자동 연결 경로와 Asset 유효성을 확인한다. |
| 전용 Test Level | 제작 전 | `L_AINativeNPC_MVP`를 만든다. |
| Manny Visual Profile | 제작 전 | exact native Pawn을 유지하고 Mesh·Animation Profile을 만든다. |
| Quinn 발소리 발생 Component와 Notify | 제작 전 | Hearing 수직 흐름 작업에서 만든다. |
| Goal·Knowledge 디버그 화면 | 제작 전 | 수동 Play 검증 전에 읽기 전용 표시 기능을 만든다. |
| Phase 3B 전체 행동 연결 | 구현 전 | Target부터 Skill 결과까지 연결한다. |

Phase 3A bounded slice는 소리를 저장하고 조사 Goal을 시작하는 C++ 연결과 native Pawn Automation fixture를 소유한다.

Phase 3A의 Quinn·Test Level Play 경로는 identity, 소음 Emitter와 디버그 Asset 제작 뒤 열린다.

Phase 3B는 Manny가 실제로 회전하고 이동하고 검색하고 복귀하는 연결을 소유한다.

현재 Test Level에서 Hearing을 발생시켜도 Phase 3B가 끝나기 전에는 전체 이동 시나리오가 완성되지 않는다.

## 7.2 현재 재사용할 Asset

다음 Asset은 실제 NeuralGame에 있다.

| 역할 | Content Browser 경로 | 사용 방법 |
|---|---|---|
| 기본 Third Person Level | `/Game/ThirdPerson/Lvl_ThirdPerson` | 전용 Test Level의 시작본으로 복제한다. |
| Quinn Player Blueprint | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter` | 플레이어 Pawn으로 유지한다. |
| 기본 GameMode | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode` | Test Level의 GameMode Override로 사용한다. |
| 기본 Player Controller | `/Game/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController` | Quinn 입력을 연결한다. |
| Quinn Mesh | `/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple` | 기존 Player Blueprint가 사용한다. |
| Manny Mesh | `/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple` | Guard Pawn의 `Mesh`에 지정한다. |
| 공용 무장 해제 Animation Blueprint | `/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed` | Quinn과 Manny의 기본 이동 표현에 사용한다. |
| 기본 입력 | `/Game/Input/IMC_Default` | Player Controller가 로드한다. |
| 이동 입력 | `/Game/Input/Actions/IA_Move` | Quinn 이동에 사용한다. |
| 시점 입력 | `/Game/Input/Actions/IA_Look` | Quinn 카메라에 사용한다. |
| 점프 입력 | `/Game/Input/Actions/IA_Jump` | Quinn 점프에 사용한다. |
| 일반 NPC Skill StateTree | `/Game/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff` | Commit된 Skill을 C++ Executor에 한 번 전달한다. |

기본 `BP_ThirdPersonCharacter`는 `SKM_Quinn_Simple`, `ABP_Unarmed`, 이동·시점·점프 Input Action을 이미 참조한다.

## 7.3 Editor를 준비하고 Content Browser 폴더를 만든다

### 7.3.1 최신 C++를 Editor에 연다

1. 실행 중인 `NeuralGame` Editor가 있으면 현재 작업을 저장하고 종료한다.
2. `NeuralGameEditor Win64 Development`를 현재 source로 build한다.
3. build가 성공한 `D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject`를 연다.
4. 이전 Editor process와 Live Coding 잔여 process가 없는지 확인한다.
5. Output Log에 module load error와 Blueprint compile error가 없는지 확인한다.
6. Content Browser Settings에서 `Show C++ Classes`를 켠다.
7. `C++ Classes/NeuralGame/AINativeNPC`에서 Guard Pawn과 Controller가 보이는지 확인한다.
8. `/Game/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff`가 열리는지 확인한다.
9. 사용자가 실행한 Editor의 GameDevMCP 연결이 현재 project와 process를 가리키는지 확인한다.

C++ class가 보이지 않으면 Asset 제작을 시작하지 않는다.

먼저 Editor build, module load와 project 경로를 바로잡는다.

실행 중 Editor가 없으면 Asset 내부 설정을 파일명만 보고 단정하지 않는다.

### 7.3.2 Content Browser 폴더 구성

전용 Asset은 `/Game/AINativeNPC` 아래에 둔다.

```text
Content/AINativeNPC/
  Maps/
    L_AINativeNPC_MVP.umap
  Characters/
    DA_AINativeNPCVisual_Manny.uasset
  Player/
    # Quinn identity ingress와 소음 발생 Asset은 Perception 수직 흐름에서 추가한다.
  Perception/
    DA_AINativeNPCSensor_Guard.uasset
  StateTree/
    ST_AINativeNPCSkillHandoff.uasset
  Debug/
    DA_AINativeNPCDebug_Default.uasset
    BP_AINativeNPCDebugDisplay.uasset
    WBP_AINativeNPCDecisionInspector.uasset
  Tests/
    # 소음 Emitter와 자동화용 fixture Asset을 추가한다.
```

`Characters/Mannequins`와 `Input`의 Epic 기본 Asset은 현재 위치에서 참조한다.

프로젝트 기본 Asset을 `/Game/AINativeNPC`로 복제하는 작업은 NPC 전용 변경이 필요할 때 시작한다.

## 7.4 전용 Test Level을 만든다

전용 Test Level의 이름은 `L_AINativeNPC_MVP`다.

### 7.4.1 Level 생성

1. Content Browser에서 `/Game/ThirdPerson/Lvl_ThirdPerson`을 선택한다.
2. `Duplicate` 또는 `Save Current Level As`를 사용한다.
3. 새 경로를 `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`로 지정한다.
4. World Settings의 `GameMode Override`를 `BP_ThirdPersonGameMode`로 지정한다.
5. `Player Start`를 한 개 유지한다.
6. 기본 조명, 하늘과 바닥을 유지한다.
7. NPC 시나리오와 무관한 장애물은 정리한다.
8. Level을 저장하고 Editor를 다시 열어 Asset이 유지되는지 확인한다.

프로젝트의 기본 시작 Level은 현재 `/Game/ThirdPerson/Lvl_ThirdPerson`이다.

전용 Level 검증이 끝날 때까지 Project Settings의 기본 시작 Level은 유지한다.

### 7.4.2 공간을 역할별로 나눈다

첫 Test Level은 약 `3000 cm × 2000 cm`의 평평한 이동 공간으로 시작한다.

| 구역 | 배치 | 확인 목적 |
|---|---|---|
| Guard Home | Manny 시작 위치와 바닥 표시 | 세션 시작 위치 캡처와 Return 확인 |
| Direct Sight Lane | Manny 정면 `1000~1500 cm` 안쪽의 Quinn 시작 지점 | Sight 입력 확인 |
| Rear Hearing Lane | Manny 뒤쪽 `1000~1500 cm` 안쪽의 소리 지점 | 시야 밖 Hearing 확인 |
| Occlusion Lane | 높이 약 `300 cm`의 벽과 기둥 | Sight Lost와 마지막 확인 위치 확인 |
| Investigation Area | 소리 지점 주변의 빈 이동 공간 | Navigate와 SearchArea 확인 |
| Return Route | 조사 구역에서 Guard Home까지 이어지는 NavMesh | Return 확인 |
| Surface A·B | 서로 구분되는 두 바닥 구역 | 발소리 표면별 loudness 확장 준비 |

모든 시험 지점은 현재 Sight와 Hearing 범위 `3000 cm` 안에서 시작한다.

벽은 Quinn의 몸 전체를 가리는 높이로 만든다.

바닥과 벽은 `/Game/LevelPrototyping`의 Cube와 Grid Material을 재사용할 수 있다.

### 7.4.3 필수 Actor를 배치한다

| Actor | 수량 | 현재 역할 |
|---|---:|---|
| `Player Start` | 1 | Quinn 시작 위치 |
| `AAINativeNPCGuardPawn` | 1 | Manny 외형을 사용할 실제 일반 NPC |
| `NavMeshBoundsVolume` | 1 | Guard Home, 조사 구역과 Return Route를 모두 덮는 이동 영역 |
| 벽 또는 기둥 | 2개 이상 | Sight 획득과 상실을 재현하는 차폐물 |
| 소리 발생 지점 표시 | 2개 | 정면과 후면 Hearing 위치 |
| Home 표시용 `TargetPoint` | 1 | 사람이 Guard 시작 위치를 알아보는 표식 |
| Debug 표시 Actor | 1 | Goal·Knowledge 표시 기능이 구현된 뒤 배치 |
| 제한 구역 Trigger | 1 | Phase 1의 forbidden area·접근 제한 시나리오를 위한 표시 영역 |
| Cover·Smart Object 시험 구역 | 1 | Phase 1의 resource Target을 추가할 여유 공간 |

제한 구역 Trigger와 Cover·Smart Object 시험 구역은 Phase 0 판단 입력에 연결하지 않는다.

현재 Home Target의 실제 값은 assembly가 처음 준비될 때 Guard Pawn의 위치에서 캡처된다.

Home 표시용 `TargetPoint`는 현재 Runtime 입력이 아닌 Level 표식이다.

Manny NPC는 첫 수직 검증에서 한 명을 사용한다.

두 번째 검증에서 Manny를 세 명까지 늘려 서로 독립된 Goal과 Knowledge를 확인한다.

### 7.4.4 Navigation을 확인한다

1. `NavMeshBoundsVolume`을 이동 구역 전체에 맞춘다.
2. Editor에서 `P` 키를 눌러 초록색 NavMesh를 표시한다.
3. Guard Home부터 조사 위치까지 초록색 영역이 이어지는지 확인한다.
4. 벽의 Collision이 NavMesh와 시야 차폐에 반영되는지 확인한다.
5. `Build Paths` 또는 전체 Build로 Navigation을 갱신한다.
6. 벽 뒤 조사 지점까지 유효한 경로가 있는지 확인한다.
7. 별도 막힌 지점을 하나 만들어 `PathUnavailable` 검증에 사용한다.

## 7.5 Quinn Player를 구성한다

Quinn은 플레이어가 직접 움직이며 Manny에게 Sight와 Hearing 입력을 제공하는 역할이다.

### 7.5.1 현재 재사용할 조작 구성

| 항목 | 값 |
|---|---|
| Pawn Blueprint | `BP_ThirdPersonCharacter` |
| Skeletal Mesh | `SKM_Quinn_Simple` |
| Animation Class | `ABP_Unarmed` |
| GameMode | `BP_ThirdPersonGameMode` |
| Player Controller | `BP_ThirdPersonPlayerController` |
| Input Mapping Context | `IMC_Default` |

Play를 시작하면 `Player Start`에서 Quinn이 생성돼야 한다.

이동, 시점 조작과 점프가 먼저 정상 동작해야 한다.

이 구성만으로는 Quinn이 AI Knowledge의 유효한 Entity가 되지 않는다.

### 7.5.2 AI Target identity를 준비한다

제품 요구는 Sight와 Hearing이 감지된 Actor의 유효한 `UAINativeNPCTargetIdentityComponent`가 정확히 한 개일 때만 Knowledge를 만드는 것이다.

현재 `BP_ThirdPersonCharacter`에는 이 Component가 없다.

현재 source에는 Quinn 연결 전에 막아야 할 identity 검증 틈도 있다.

- `bInitialized`가 `EditInstanceOnly`라서 Editor에서 bool만 바꿀 수 있다.
- `FindIdentity()`는 exact-one과 `bInitialized`만 확인한다.
- Sight는 `Entity` 종류를 다시 확인한다.
- Hearing은 현재 종류, nonzero stable ID와 nonzero generation을 모두 다시 확인하지 않는다.

따라서 현재 source의 Hearing을 아직 hostile identity 상태에 안전하다고 판정하지 않는다.

이 Component는 Blueprint에서 추가할 수 있지만 runtime identity 초기화 함수는 Blueprint에 공개돼 있지 않다.

이 문서는 identity 발급자로 서버 전용 `UAINativeNPCEntityIdentitySubsystem`을 선택한다.

파일은 `Source/NeuralGame/AINativeNPC/Knowledge/AINativeNPCEntityIdentitySubsystem.h/.cpp`다.

Phase 0의 Quinn persistent key는 `Player.Main`이다.

Blueprint는 이 key와 숫자 ID를 편집하지 않는다.

제품 identity 순서는 다음과 같다.

1. `ANeuralGameCharacter` 생성자는 `UAINativeNPCTargetIdentityComponent`를 기본 Subobject로 정확히 한 개 만든다.
2. `BP_ThirdPersonCharacter`는 상속된 Component를 사용한다.
3. 같은 Component를 Blueprint에서 다시 추가하면 assembly를 거부한다.
4. 서버 BeginPlay는 `Player.Main`과 Quinn Actor를 Identity Subsystem에 등록한다.
5. Subsystem은 persistent key에 대응하는 nonzero stable ID를 발급한다.
6. Subsystem은 같은 stable ID의 Actor 수명이 새로 시작될 때 nonzero spawn generation을 증가시킨다.
7. stable ID와 generation은 `MAX`에서 wrap하거나 재사용하지 않는다.
8. Subsystem의 private ingress만 Component를 정확히 한 번 초기화한다.
9. Component의 `InitializeRuntimeIdentity()`는 public C++ API에서 제거한다.
10. `bInitialized`, stable ID와 generation은 runtime 전용 private 상태로 둔다.
11. client, Blueprint와 다른 authority caller는 첫 identity를 만들 수 없다.
12. teardown은 Actor binding을 해제하되 stable ID와 generation high-water mark를 되돌리지 않는다.

Phase 0의 Test Level은 한 서버 세션에서 `Player.Main` 한 개를 사용한다.

제품 Save/Load는 다음 identity archive를 저장한다.

- persistent key와 stable ID의 대응
- stable ID별 마지막 spawn generation
- stable ID 발급 high-water mark
- archive version과 checksum

Load는 archive를 먼저 복원한 뒤 Actor를 등록한다.

Save/Load가 구현되기 전에는 세션 종료 뒤 같은 stable ID를 보장한다고 주장하지 않는다.

멀티플레이에서는 `Player.Main`을 그대로 재사용하지 않는다.

Phase 1의 서버 Player identity provider가 영속 Player·Net key를 공급한다.

첫 RED 검사는 다음 사실을 고정한다.

- identity 없는 Quinn의 Sight와 Hearing은 Knowledge를 만들지 않는다.
- Editor에서 `bInitialized=true`만 지정하는 경로가 존재하지 않는다.
- Hearing은 `Entity`, nonzero stable ID와 nonzero generation을 모두 다시 확인한다.
- 초기화된 identity가 정확히 한 개면 Sight와 Hearing이 같은 subject stable ID를 사용한다.
- identity가 두 개면 Actor binding을 거부한다.
- 같은 Component를 두 번 초기화해도 첫 identity가 유지된다.
- 서버가 아닌 호출은 identity를 만들지 않는다.
- 권한은 있지만 Identity Subsystem이 아닌 caller는 첫 identity를 만들지 못한다.
- stable ID와 generation counter가 wrap하거나 재사용되지 않는다.
- teardown 뒤 이전 binding은 새 Actor를 가리키지 않는다.

구현할 최소 수정은 다음과 같다.

1. `BlueprintSpawnableComponent`와 `bInitialized`의 `EditInstanceOnly`를 제거한다.
2. Identity Subsystem과 private one-shot ingress를 추가한다.
3. `FindIdentity()`가 종류, stable ID와 generation까지 검증한다.
4. Sight와 Hearing이 같은 validator를 사용한다.
5. hostile Editor 상태, forged first-call과 counter exhaustion 검사를 GREEN으로 만든다.

Blueprint에는 C++에서 상속된 identity Component의 읽기 전용 상태만 보인다.

### 7.5.3 Sight 입력

현재 AI Controller는 Sight를 주 감각으로 사용한다.

현재 `DefaultEngine.ini`에는 Pawn의 Sight 자동 등록을 바꾸는 명시적 설정이 없다.

따라서 현재 Editor 시험은 Unreal Engine 5.7의 기본 Pawn 자동 등록 동작에 의존할 수 있다.

기본 동작이 Quinn을 Sight 자극의 원천으로 등록하더라도 AI Native NPC Knowledge의 Entity 조건은 완료되지 않는다.

Quinn은 7.5.2의 identity 초기화를 먼저 통과해야 한다.

명시적인 제품 구성을 만들 때는 Quinn에 `UAIPerceptionStimuliSourceComponent`를 추가하고 Sight를 등록한다.

명시적 Source 전환은 Pawn 자동 등록 설정과 패키징 결과를 함께 검증한다.

### 7.5.4 Hearing 입력

현재 Quinn Blueprint에는 AI 발소리를 보고하는 Component와 Animation Notify가 없다.

Hearing 구현은 다음 흐름을 만든다.

```text
Quinn 발이 바닥에 닿음
→ Animation Notify
→ Player Noise Emitter
→ UAISense_Hearing::ReportNoiseEvent
→ Manny Perception
→ Knowledge의 SoundEvent
→ 조사 Goal 시작
```

목표 Asset과 코드는 다음과 같다.

| 역할 | 목표 이름 | 책임 |
|---|---|---|
| 소음 발생 Component | `UPlayerNoiseEmitterComponent` | 속도와 표면에 따른 위치·loudness·tag를 만든다. |
| 발 접촉 Notify | `UAnimNotify_ReportAINoise` | 실제 발 접촉 프레임에 Component를 호출한다. |
| Quinn 설정 | `BP_ThirdPersonCharacter`의 Component | Sight와 Hearing source를 소유한다. |
| 표면 설정 | `DA_AINativeNPCSensor_Guard`의 Curve | Surface A·B의 loudness를 정한다. |

`ABP_Unarmed`는 `/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run`을 사용한다.

이 BlendSpace는 Walk 8개와 Jog 8개 Animation Sequence를 참조한다.

Notify는 BlendSpace가 아니라 실제 16개 Walk·Jog Sequence의 발 접촉 프레임에 넣는다.

각 Sequence에는 왼발과 오른발 Notify가 정확히 한 번씩 있어야 한다.

같은 발 접촉 프레임의 중복 Notify는 한 Noise Event로 dedupe한다.

`Config/DefaultEngine.ini`에 다음 표면을 추가한다.

```ini
[/Script/Engine.PhysicsSettings]
+PhysicalSurfaces=(Type=SurfaceType1,Name="AINPC_SurfaceA")
+PhysicalSurfaces=(Type=SurfaceType2,Name="AINPC_SurfaceB")
```

Surface A·B의 바닥 Material은 해당 Physical Material을 사용한다.

Noise Emitter는 발 아래 line trace로 Surface Type을 읽는다.

line trace가 실패하면 `Default` surface를 사용한다.

Sensor Config의 첫 loudness 값은 다음과 같다.

| 이동 | Default | Surface A | Surface B |
|---|---:|---:|---:|
| Walk | `0.35` | `0.30` | `0.55` |
| Jog | `0.70` | `0.60` | `1.00` |

최종 loudness는 `0..1`로 clamp한다.

같은 값은 AI 판단 의미가 아니라 Hearing 자극의 시작 튜닝값이다.

소리 발생 코드는 Perception 입력만 만든다.

Goal과 행동 선택은 Manny의 권한 Runtime이 담당한다.

### 7.5.5 Hearing의 첫 수동 시험 도구

Quinn 발소리 Notify 구현 전에는 전용 시험용 소음 발생 Actor를 사용할 수 있다.

권장 이름은 `/Game/AINativeNPC/Tests/BP_AINoiseTestEmitter`다.

이 Blueprint의 부모는 새 C++ class `AAINativeNPCNoiseTestEmitter`다.

C++ 부모는 다음 책임만 가진다.

- `UAINativeNPCTargetIdentityComponent`를 기본 Subobject로 정확히 한 개 만든다.
- Editor·Development 시험 world의 승인된 test-only ID 발급자에게 identity를 받는다.
- 서버에서 `EmitOnce()`를 한 번만 허용한다.
- `UAISense_Hearing::ReportNoiseEvent`에 자기 자신을 instigator로 전달한다.
- 발생 위치와 유효 범위를 Development 화면에 표시한다.
- teardown 뒤 callback과 test-only identity 등록을 정리한다.

Blueprint 자식은 loudness, max range, delay와 debug color만 조정한다.

Blueprint가 stable ID, generation, Event ID와 Goal을 직접 지정하면 안 된다.

시험용 ID 발급자는 제품 ID 발급자와 이름, 저장 범위와 검증을 분리한다.

`bEmitOnBeginPlay`는 기본 `false`다.

첫 수동 시험은 Level의 명시적 Trigger 또는 Debug 명령이 `EmitOnce()`를 호출한다.

제품 수직 흐름 완료 판정은 Quinn의 실제 발 접촉 Notify 경로를 사용한다.

## 7.6 Manny NPC를 구성한다

Manny는 `AAINativeNPCGuardPawn`의 실제 몸과 `AAINativeNPCGuardController`의 감지·제어를 사용하는 일반 NPC다.

### 7.6.1 exact native Pawn과 Manny Visual Profile을 사용한다

현재 shipping assembly는 정확한 native Pawn과 Controller class를 요구한다.

현재 Pawn 선언은 `final`, `NotBlueprintable`이다.

이 문서는 **exact native Pawn + Visual Profile**을 선택한다.

Phase 0에서는 `BP_AINativeNPC_Manny`를 만들지 않는다.

Manny 외형 Asset은 `/Game/AINativeNPC/Characters/DA_AINativeNPCVisual_Manny`다.

C++ class는 `UAINativeNPCVisualProfile`이며 `UPrimaryDataAsset`을 상속한다.

Visual Profile은 다음 값만 소유한다.

- Skeletal Mesh: `SKM_Manny_Simple`
- Animation Class: `ABP_Unarmed`
- Mesh relative location
- Mesh relative rotation
- Mesh relative scale

Mesh transform은 Editor에서 `BP_ThirdPersonCharacter`의 Quinn Mesh 값을 읽어 그대로 복사한 뒤 Manny의 발이 Capsule 바닥에 맞는지 확인한다.

Goal, Knowledge, Skill, Sensor, 속도와 회전 의미는 Visual Profile에 넣지 않는다.

`AAINativeNPCGuardPawn`은 다음 시작 구성을 C++에서 소유한다.

- Capsule radius `42`, half height `96`
- `Use Controller Rotation Yaw=false`
- `Orient Rotation to Movement=true`
- Yaw Rotation Rate `500`
- AI Controller Class `AAINativeNPCGuardController`
- Auto Possess AI `Placed in World or Spawned`

Skill 속도, 회전과 도착 조건은 생성 Skill 실행 계약이 우선한다.

Guard Pawn은 C++ 기본 soft path로 Manny Visual Profile을 가리킨다.

`PostInitializeComponents()`는 BeginPlay 전에 Profile을 읽어 inherited Mesh에 적용한다.

Profile load가 실패하면 권한 Runtime을 임의 설정으로 계속 꾸미지 않고 `visual_ready=false`를 기록한다.

AI authority assembly와 visual readiness는 별도 상태다.

Test Level 완료 판정은 둘 다 true일 때만 통과한다.

Profile Asset이 cook에 포함되는지 Development·Shipping package에서 검사한다.

Test Level 배치 순서는 다음과 같다.

1. Visual Profile class와 hostile Data Validation RED 검사를 추가한다.
2. `DA_AINativeNPCVisual_Manny`를 만든다.
3. `AAINativeNPCGuardPawn`의 profile load와 적용을 구현한다.
4. `Place Actors`에서 C++ Class `AAINativeNPCGuardPawn`을 찾는다.
5. Level의 Guard Home 위치에 배치한다.
6. Actor 이름을 `AINPC_Guard_01`로 지정한다.
7. Profile 적용 뒤 Mesh가 `SKM_Manny_Simple`인지 확인한다.
8. Animation Mode가 `Use Animation Blueprint`인지 확인한다.
9. Anim Class가 `ABP_Unarmed`인지 확인한다.
10. Manny의 발이 Capsule 바닥에 맞는지 확인한다.
11. AI Controller와 Auto Possess AI 값을 확인한다.
12. Level을 저장하고 Editor를 다시 연다.
13. Profile reference와 Mesh·Animation 적용 결과를 다시 읽는다.

Profile이 없거나 잘못됐을 때 Level 인스턴스에 임의 Mesh Component를 추가하지 않는다.

Manny와 Quinn은 같은 Mannequin Skeleton 계열과 `ABP_Unarmed`를 재사용한다.

Quinn C++의 현재 시작값도 Capsule `42/96`, Yaw Rotation Rate `500`, Max Walk Speed `500`이다.

Quinn 값은 Mesh 정렬을 확인하는 비교 기준이다.

Phase 0의 TurnTo는 Pawn Yaw를 직접 보간한다.

Phase 0의 이동 Skill은 Character Movement와 Unreal Navigation을 사용한다.

### 7.6.2 native Pawn이 이미 소유하는 Component

`AAINativeNPCGuardPawn`은 다음 Component를 C++ 생성자에서 만든다.

| Pawn Component | 역할 |
|---|---|
| `AINativeNPCGoalHost` | Goal, 판단과 실행 권한을 연결한다. |
| `AINativeNPCSkillHandoff` | Commit된 Skill을 StateTree로 전달한다. |
| `AINativeNPCSkillExecutor` | 실제 회전, 이동, 조사와 검색을 수행한다. |
| `AINativeNPCGoalTimer` | 현재 Goal 단계의 시간을 관리한다. |

`AAINativeNPCGuardController`는 다음 Component를 C++ 생성자에서 만든다.

| Controller Component | 역할 |
|---|---|
| `AINativeNPCPerception` | Sight와 Hearing 자극을 받는다. |
| `AINativeNPCKnowledge` | Entity, LastKnownPosition과 SoundEvent를 저장한다. |
| `AINativeNPCStateTree` | Commit된 Skill handoff Asset을 실행한다. |

Level 인스턴스에 같은 역할의 Component를 추가하지 않는다.

assembly는 각 역할이 정확히 한 개일 때 준비된다.

### 7.6.3 현재 Perception 시작값

현재 값은 `AAINativeNPCGuardController.cpp`가 소유한다.

| 설정 | 현재 값 |
|---|---:|
| Sight Radius | `3000 cm` |
| Lose Sight Radius | `3500 cm` |
| Peripheral Vision Half Angle | `90°` |
| Hearing Range | `3000 cm` |
| Dominant Sense | Sight |
| 감지 소속 | Enemy, Neutral, Friendly 모두 |

과거 계획의 `2000/2500/70` 예시는 현재 코드 값이 아니다.

Sensor Data Asset 전환 전에는 위 C++ 값을 기준으로 Level 크기를 정한다.

### 7.6.4 Perception이 Knowledge와 Goal로 가는 순서

Knowledge Component는 BeginPlay에서 Controller의 Perception Component를 찾는다.

유효한 Perception Component가 정확히 한 개일 때만 `OnTargetPerceptionUpdated` callback을 연결한다.

Component가 끝나거나 등록 해제되면 callback과 Goal event sink를 해제한다.

현재 source의 순서는 다음과 같다.

```text
Perception 자극
→ Knowledge가 Sight 또는 Hearing을 구분
→ 서버 권한 확인
→ exact-one이고 bInitialized인 identity Component 확인
→ Sight는 Entity 종류를 추가 확인
→ Hearing은 종류·stable ID·generation 재확인이 아직 없음
→ 통과한 사실을 Knowledge에 저장
→ Knowledge revision 증가
→ 필요한 사건만 Goal Host에 전달
```

identity hardening 뒤의 목표 순서는 다음과 같다.

```text
Perception 자극
→ 서버 권한 확인
→ 공통 validator가 exact-one·Entity·nonzero stable ID·nonzero generation 확인
→ Sight 또는 Hearing 사실을 Knowledge에 저장
→ Knowledge revision 증가
→ 필요한 사건만 Goal Host에 전달
```

Sight 성공은 현재 보이는 `Entity`를 만들거나 갱신한다.

Sight 상실은 현재 `Entity`를 제거하고 마지막으로 허용된 위치를 `LastKnownPosition`으로 복사한다.

현재 `LastKnownPosition` TTL은 `10초`다.

Hearing 성공은 위치가 바뀌지 않는 `SoundEvent`를 만든다.

현재 `SoundEvent` TTL은 `3초`다.

Hearing은 저장 성공 뒤에 `SoundHeard`, Knowledge revision, SoundEvent Handle과 위치를 Goal Host에 전달한다.

Perception callback은 Skill을 직접 시작하지 않는다.

다음 항목은 현재 완료로 보지 않는다.

- 같은 Quinn을 다시 봤을 때 이전 `LastKnownPosition`을 자동 제거하는 제품 경로
- Sensor 시작값과 TTL을 Data Asset에서 읽는 경로
- Quinn의 production identity ingress와 hostile identity hardening
- Quinn의 발 접촉에서 시작하는 Hearing 경로

위 항목은 hostile RED 검사를 먼저 추가한 뒤 구현한다.

### 7.6.5 `BP_AINativeNPC_Manny`를 만들지 않는 이유

과거 계획은 Manny Blueprint 자식을 목표로 했다.

현재 exact assembly는 `AAINativeNPCGuardPawn`의 정확한 class를 검사한다.

Blueprint 자식을 허용하면 hostile subclass, Component 중복과 권한 우회 범위를 다시 열어야 한다.

Phase 0은 그 경계를 넓히지 않는다.

디자이너가 바꿀 Mesh·Animation·transform은 `DA_AINativeNPCVisual_Manny`에 둔다.

Goal Host, Knowledge, Commit과 Skill 권한은 exact native Pawn과 Controller가 계속 소유한다.

Blueprint 자식 허용은 제품 요구가 생길 때 별도 계약·RED 검사·승인을 거쳐 다시 검토한다.

## 7.7 StateTree Asset을 확인한다

일반 NPC는 `/Game/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff`를 사용한다.

Controller는 이 경로를 `PostInitializeComponents()`에서 로드한다.

StateTree Component는 자동 시작을 끈 상태로 준비된다.

Goal Host는 Commit 성공 뒤에만 StateTree를 시작한다.

StateTree의 `CommittedSkillHandoff` 상태는 `FAINativeNPCStateTreeAINativeNPCSkillHandoffTask`를 통해 C++ Executor에 전달한다.

StateTree는 상위 Goal이나 Skill을 선택하는 장소가 아니다.

StateTree 확인 절차는 다음과 같다.

1. Asset을 열어 compile error가 없는지 확인한다.
2. Schema가 AI Component용인지 확인한다.
3. handoff Task가 유효한지 확인한다.
4. Asset을 저장한다.
5. Data Validation을 실행한다.
6. Editor를 다시 연 뒤 Controller가 같은 Asset을 읽는지 확인한다.

## 7.8 Phase 0 Data Asset을 만든다

Phase 0은 Visual, Sensor와 Debug Profile 세 개만 만든다.

Goal과 Utility 값은 generated Registry가 소유한다.

같은 값을 편집하는 Goal Profile과 Utility Profile Data Asset은 만들지 않는다.

### 7.8.1 만들 Asset과 class

| Asset | C++ class | 경로 | 적용자 |
|---|---|---|---|
| Manny Visual | `UAINativeNPCVisualProfile` | `/Game/AINativeNPC/Characters/DA_AINativeNPCVisual_Manny` | `AAINativeNPCGuardPawn` |
| Guard Sensor | `UAINativeNPCSensorConfig` | `/Game/AINativeNPC/Perception/DA_AINativeNPCSensor_Guard` | `AAINativeNPCGuardController` |
| Debug 표시 | `UAINativeNPCDebugProfile` | `/Game/AINativeNPC/Debug/DA_AINativeNPCDebug_Default` | `UAINativeNPCDebugComponent` |

세 class는 `UPrimaryDataAsset`을 상속한다.

세 Asset은 soft object path로 C++ 기본값에 연결한다.

Profile 참조는 Blueprint와 Level 인스턴스에서 다른 Asset로 바꾸지 않는다.

프로필 선택 기능이 필요해지면 Guard role authority를 먼저 계약한다.

### 7.8.2 Visual Profile 필드

Visual Profile은 다음 필드만 가진다.

- `TSoftObjectPtr<USkeletalMesh> SkeletalMesh`
- `TSoftClassPtr<UAnimInstance> AnimClass`
- `FTransform MeshRelativeTransform`

Validation은 Mesh·Anim Class 누락, Skeleton 불일치, non-finite transform과 0 scale을 거부한다.

Goal, Skill, Sensor와 이동 의미는 Visual Profile에 넣지 않는다.

### 7.8.3 Sensor Config 필드

Sensor Config는 다음 필드를 가진다.

- Sight Radius
- Lose Sight Radius
- Peripheral Vision Half Angle
- Sight Max Age
- Hearing Range
- Hearing Max Age
- LastKnownPosition TTL
- SoundEvent TTL
- 감지할 affiliation
- surface별 footstep loudness Curve

첫 Asset은 현재 C++ 값 `3000 / 3500 / 90 / 3000`, LastKnown `10초`, SoundEvent `3초`에서 시작한다.

과거 `2000 / 2500 / 70`, LastKnown `6초`는 현재 시작값으로 복사하지 않는다.

Validation은 non-finite 값, 0 이하 거리·수명, `Lose Sight < Sight`, 잘못된 angle과 누락 Curve를 거부한다.

Guard Controller는 모든 값을 검증한 뒤 Perception에 한 번 적용한다.

적용 실패는 C++ 기본값으로 조용히 섞지 않고 `sensor_ready=false`로 assembly를 막는다.

Sensor 값은 월드 단위의 감지와 수명 설정이다.

Schema normalization 상수는 모델 입력 계약이므로 Sensor Asset에서 바꾸지 않는다.

### 7.8.4 Debug Profile 필드

Debug Profile은 다음 bool과 색만 가진다.

- Sight cone
- 현재 Entity
- LastKnownPosition
- SoundEvent와 남은 TTL
- Goal Target
- Target slot 번호
- Nav path
- Editor 전용 Ground Truth
- Decision·Commit·Skill 실패 이유
- 각 표시의 색과 최대 거리

Ground Truth 표시는 Editor·Test에서만 허용한다.

Shipping build는 Debug Profile을 읽어도 내부 사실과 score를 그리지 않는다.

### 7.8.5 Phase 1 Asset

다음 Asset은 Phase 0에서 만들지 않는다.

| Phase 1 Asset | 이유 |
|---|---|
| Neural Policy | NNE ModelData, descriptor, hashes, calibration과 OOD 연결이 필요하다. |
| Performance Profile | 여러 NPC 판단 빈도와 deadline 조정이 필요하다. |
| Guard role Profile | 역할별 Visual·Sensor·Policy 선택 권한이 필요하다. |

Neural Policy는 model SHA-256, schema·Registry SHA-256, decision contract hash, 허용 Runtime, descriptor manifest와 Utility fallback ID를 가진다.

Goal·Skill ID, transition, phase Timer와 Utility 가중치는 generated Registry가 계속 소유한다.

모든 Data Asset class는 `IsDataValid()`에서 잘못된 ID, non-finite 값, 범위 역전과 누락 참조를 거부한다.

## 7.9 Manny와 Quinn Animation을 구성한다

### 7.9.1 공용 locomotion

Phase 0은 기존 Mannequin locomotion을 재사용한다.

| 기능 | Phase 0 구성 | 후속 표현 |
|---|---|---|
| Idle | `ABP_Unarmed` 기본 Idle | 주변을 보는 additive 표현 |
| 이동 | Character Movement 속도 기반 Walk·Jog | 상황별 stride와 속도 보정 |
| TurnTo | Actor와 Capsule Yaw 보간 | Turn-in-place, Aim Offset, Head·Spine LookAt |
| Investigate | 이동·회전의 조합 | 조사 전용 Montage |
| SearchArea | 여러 지점 이동 | 고개·상체 탐색 표현 |
| 피격·전투 | 현재 범위 밖 | Hit reaction과 Attack Montage |

Animation은 Skill 결과를 보기 쉽게 표현한다.

Goal과 Candidate의 의미는 Runtime과 Registry가 소유한다.

### 7.9.2 Quinn 발 접촉 Notify 검증

1. `BS_Idle_Walk_Run`이 참조하는 Walk·Jog Sequence 16개 목록을 고정한다.
2. 각 Sequence의 왼발·오른발 접촉 프레임을 확인한다.
3. `UAnimNotify_ReportAINoise`를 각 접촉 프레임에 배치한다.
4. Notify의 foot side를 `Left` 또는 `Right`로 지정한다.
5. Sequence별 예상 Notify 수를 Automation으로 검사한다.
6. BlendSpace의 8방향 Walk·Jog를 모두 재생해 중복·누락을 확인한다.
7. Surface A·B에서 화면의 SoundEvent 위치와 loudness를 비교한다.

Epic 기본 Animation을 직접 수정해야 하므로 변경 Asset 16개를 manifest에 고정한다.

프로젝트 기본 Asset 갱신으로 덮어써지지 않는지 upgrade 때 검사한다.

## 7.10 디버그 화면과 Replay를 만든다

수동 Play 검증은 Manny의 내부 상태를 눈으로 읽을 수 있어야 한다.

### 7.10.1 첫 화면

첫 화면은 다음 값을 항상 표시한다.

| 화면 항목 | 이유 |
|---|---|
| Pawn·Controller class | exact assembly 확인 |
| assembly ready | Component 구성 성공 확인 |
| 현재 Goal·phase·revision | Phase 3A 전환과 Phase 3B 진행 확인 |
| Home 위치 | Return Target 확인 |
| 최근 SoundEvent 위치와 TTL | Hearing 입력 확인 |
| 현재 Entity와 LastKnownPosition | Sight 획득·상실 확인 |
| 선택된 Skill과 Target | Candidate와 Commit 결과 확인 |
| Skill 상태와 실패 이유 | 이동 실패와 중단 원인 확인 |
| Nav path | Knowledge 위치를 향한 이동 확인 |

첫 Asset은 `/Game/AINativeNPC/Debug/WBP_AINativeNPCDecisionInspector`다.

`/Game/AINativeNPC/Debug/BP_AINativeNPCDebugDisplay`는 Test Level에서 Widget과 월드 표시를 켜는 Actor다.

화면은 선택한 Manny 한 명의 읽기 전용 `FAINativeNPCDebugSnapshot`만 표시한다.

`UAINativeNPCDebugComponent`는 Guard Pawn에 C++ 기본 Subobject로 정확히 한 개 존재한다.

public Blueprint API는 두 개뿐이다.

```cpp
UFUNCTION(BlueprintPure)
bool GetLatestDebugSnapshot(FAINativeNPCDebugSnapshot& OutSnapshot) const;

UFUNCTION(BlueprintCallable)
bool RequestManualCapture(FName ReasonTag);
```

`GetLatestDebugSnapshot()`은 GameThread에서 마지막으로 확정된 immutable 복사본만 반환한다.

Widget은 Host, Knowledge, Candidate와 Executor 객체를 직접 참조하지 않는다.

`RequestManualCapture()`는 Development·Editor authority와 GameThread에서만 동작한다.

이 함수는 마지막으로 확정된 Debug Snapshot과 현재 Decision Capture 공급자를 한 번 읽어 owned `FAINativeNPCDecisionCaptureRecord`를 만든다.

그 뒤 `UAINativeNPCDecisionCaptureSubsystem::WriteCapture()`를 호출한다.

성공한 Capture handle은 다음 Debug Snapshot의 `LastCapture`에 기록한다.

실패하면 기존 Snapshot과 Runtime 상태를 유지하고 `CaptureFailure`만 기록한다.

화면 버튼이 Goal, Knowledge, Candidate, Commit 또는 Skill 상태를 바꾸면 안 된다.

### 7.10.2 Decision Inspector의 펼침 영역

Phase 3B 검증 전에 다음 영역을 추가한다.

| 영역 | 표시 값 |
|---|---|
| Goal | Active Goal, phase, revision, generation, Timer와 Goal Target |
| Event | 최근 Event 12개와 source·age·strength·urgent |
| Knowledge | Entity, SoundEvent, LastKnownPosition, source·confidence·TTL |
| Target | Target Universe, mandatory·quota·drop reason과 slot `0..16` |
| Candidate | 272개 mask, mask reason과 Candidate Hash |
| Utility | raw score, switch cost, adjusted score와 선택 행 |
| Neural | raw score, OOD, calibrated acceptability와 fallback 이유 |
| Commit | Decision ID, deadline, stale discard, validation과 reservation 결과 |
| Skill | 실행 ID, 고정 Target Snapshot, 상태와 typed failure reason |
| Contract | model·schema·Skill Registry·Goal Registry version과 hash |

Neural과 reservation 값은 해당 기능이 구현되기 전에는 `Not connected`로 표시한다.

빈 값을 `0`이나 `PASS`로 꾸미지 않는다.

보스 Pattern 상세는 일반 NPC 화면과 별도 탭으로 둔다.

### 7.10.3 월드 Debug 표시

`BP_AINativeNPCDebugDisplay`는 Development·Editor에서 다음 모양을 그린다.

- Sight cone
- 현재 보이는 Entity는 실선
- LastKnownPosition은 점선, age와 confidence
- SoundEvent는 구와 남은 TTL
- Goal Target
- Target slot 번호
- Knowledge 위치까지의 Nav path
- Editor 전용 Ground Truth marker

Ground Truth 위치는 Editor 전용 색으로 표시한다.

Knowledge 위치는 다른 색으로 표시한다.

Ground Truth 표시 데이터는 Candidate와 Feature 입력에 들어가지 않는다.

Shipping build에서는 Ground Truth와 내부 score 표시를 제외한다.

### 7.10.4 Decision Log와 이상 행동 Capture

각 판단은 최소 다음 값을 구조화된 log로 남긴다.

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
  "utility_score": 1.59,
  "commit": "Started"
}
```

Neural 연결 뒤에는 raw score, switch cost, adjusted score, OOD와 calibrated acceptability를 추가한다.

이상 행동 Capture는 다음 자료를 한 묶음으로 저장한다.

- 이전 `10~30초` Event
- Goal stack과 Timer
- Knowledge Snapshot
- Target Universe와 slot map
- Candidate mask와 Hash
- Utility 또는 Neural 결과
- Commit과 Skill 결과
- Editor 전용 Ground Truth
- Replay seed와 map seed
- Candidate miss와 Target miss 구분
- schema·registry·model·policy hash

Capture는 `Saved/AINativeNPC/Captures/<session>/<capture-id>.json`과 별도 binary tensor 파일에 저장한다.

JSON은 archive version, endianness, schema·Registry hashes, map package, map seed, NPC stable ID와 binary SHA-256을 가진다.

binary 파일은 canonical tensor bytes와 mask를 가진다.

부분 기록, hash 불일치, unknown archive version과 non-finite 값은 Replay에서 거부한다.

`UAINativeNPCDecisionCaptureSubsystem`은 Capture 저장을 소유한다.

public C++ API는 다음과 같다.

```cpp
bool WriteCapture(
    FAINativeNPCDecisionCaptureRecord&& Record,
    FAINativeNPCCaptureHandle& OutHandle,
    EAINativeNPCCaptureFailure& OutFailure);
```

`FAINativeNPCCaptureHandle`은 session ID, capture ID, JSON path와 binary SHA-256을 가진 immutable 값이다.

`WriteCapture()`는 임시 파일 두 개를 먼저 쓴다.

두 파일의 flush와 SHA-256 계산이 성공한 뒤 최종 경로로 원자적으로 교체한다.

한 단계라도 실패하면 임시 파일을 지우고 유효한 handle을 반환하지 않는다.

`UAINativeNPCDecisionReplaySubsystem`은 같은 Capture를 읽어 Target, Candidate, score와 Commit 직전 검증을 재현한다.

public C++ API는 다음과 같다.

```cpp
bool LoadCapture(
    const FAINativeNPCCaptureHandle& Handle,
    FAINativeNPCReplayInput& OutInput,
    EAINativeNPCReplayFailure& OutFailure) const;

bool RunReplay(
    const FAINativeNPCReplayInput& Input,
    FAINativeNPCReplayResult& OutResult,
    EAINativeNPCReplayFailure& OutFailure) const;
```

`LoadCapture()`는 archive version, 경로 범위, JSON·binary SHA-256, schema·Registry hashes와 모든 유한값을 확인한다.

`FAINativeNPCReplayResult`는 Target slot, Candidate mask·hash, Utility score, 선택 Candidate, Commit 직전 validation 결과와 원본 대비 일치 여부를 가진다.

Decision Inspector와 Automation은 `FAINativeNPCReplayResult`의 소비자다.

Replay는 별도 preview world 또는 pure Core에서 실행한다.

Replay는 실제 서버 권한 Skill을 자동 실행하지 않는다.

사람의 후보 평가를 저장할 때는 acceptable Candidate와 annotator provenance를 함께 기록한다.

현재 `GetGoalSnapshot()`은 C++ 내부 조회 함수다.

Debug Component는 필요한 현재 상태를 한 번 복사해 `FAINativeNPCDebugSnapshot`으로 만들고 내부 pointer를 버린다.

수동 Play 완료 판정은 디버그 화면이 최신 Goal과 Skill 상태를 보여 줄 때 시작한다.

## 7.11 Editor에서 따라 하는 제작 순서

Unreal 수직 구성은 다음 순서로 만든다.

1. 현재 문서와 선택한 class·Asset 이름을 사용자에게 확인받는다.
2. Identity Subsystem·Component hardening·Quinn composition의 RED 검사를 추가한다.
3. identity 경로를 최소 C++로 구현한다.
4. Visual·Sensor·Debug Profile class와 Data Validation RED 검사를 추가한다.
5. 세 Profile class를 최소 C++로 구현한다.
6. Guard Pawn의 Visual 적용과 Guard Controller의 Sensor 적용 RED 검사를 추가한다.
7. exact native Pawn·Controller의 Profile 적용을 구현한다.
8. 읽기 전용 Debug Snapshot·Capture·Replay RED 검사를 추가한다.
9. Debug Component와 두 Subsystem을 최소 C++로 구현한다.
10. test-only identity와 one-shot Hearing Emitter의 RED 검사를 추가한다.
11. `AAINativeNPCNoiseTestEmitter`를 최소 C++로 구현한다.
12. Quinn Noise Emitter·Animation Notify·surface loudness RED 검사를 추가한다.
13. Quinn의 발소리 C++ 경로를 최소 구현한다.
14. Editor target을 build하고 최신 `NeuralGame.uproject`를 연다.
15. C++ Classes, StateTree와 GameDevMCP 연결을 확인한다.
16. Visual·Sensor·Debug Profile Asset을 만든다.
17. 시험용 Emitter와 Debug Blueprint·Widget을 만든다.
18. Walk·Jog Sequence 16개에 발 접촉 Notify를 넣는다.
19. Surface A·B Physical Material과 바닥 Material을 만든다.
20. `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`를 만든다.
21. Quinn의 기존 GameMode, Controller, Mesh, Animation과 입력을 확인한다.
22. native `AAINativeNPCGuardPawn` 한 개를 배치한다.
23. Visual Profile이 Manny Mesh와 `ABP_Unarmed`를 적용했는지 확인한다.
24. NavMesh, 정면 시야 구역, 후면 소리 구역과 차폐 벽을 만든다.
25. Quinn의 Sight Knowledge를 확인한다.
26. 시험용 Emitter로 Hearing 입력을 분리 검증한다.
27. Phase 3A의 Goal 전환을 Play에서 확인한다.
28. Quinn 실제 발소리로 같은 Hearing 흐름을 확인한다.
29. Phase 3B를 RED에서 GREEN으로 구현한다.
30. Manny의 `Orient → Navigate → Search → Return`을 Play에서 확인한다.
31. Manny를 세 명까지 늘려 독립 상태를 확인한다.
32. Save All, Data Validation, Editor 재시작과 Asset 재읽기를 수행한다.

## 7.12 Play에서 직접 확인하는 시나리오

각 시나리오는 입력, 화면에서 볼 결과와 현재 구현 경계를 함께 기록한다.

### 7.12.1 Quinn 기본 조작

1. `L_AINativeNPC_MVP`를 연다.
2. Play In Editor를 시작한다.
3. Quinn을 이동하고 카메라를 돌린다.
4. Quinn Mesh와 Animation이 자연스럽게 재생되는지 확인한다.
5. Manny Mesh가 Capsule 바닥에 맞고 Idle Animation을 재생하는지 확인한다.

### 7.12.2 정면 Sight

1. Quinn을 Manny 정면 `3000 cm` 안으로 이동한다.
2. 디버그 화면에서 현재 Entity Knowledge가 생기는지 확인한다.
3. Quinn을 벽 뒤로 이동한다.
4. Entity가 LastKnownPosition으로 교체되는지 확인한다.
5. LastKnownPosition이 벽 뒤 Quinn의 현재 위치를 따라가지 않는지 확인한다.

현재 Goal gameplay의 Sight 기반 전체 반응은 후속 Goal 연결 범위다.

### 7.12.3 뒤쪽 Hearing과 Phase 3A

1. Quinn 또는 시험용 Emitter를 Manny 뒤쪽 `3000 cm` 안에 둔다.
2. Sight가 벽으로 가려진 상태를 만든다.
3. 서버에서 한 번 Noise Event를 발생시킨다.
4. 디버그 화면에서 SoundEvent 위치와 새 Knowledge revision을 확인한다.
5. 현재 Goal이 `InvestigateDisturbance/Orient`로 바뀌는지 확인한다.
6. Goal Target 위치가 소리 발생 위치와 같은지 확인한다.

이 Play smoke의 통과 범위는 Phase 3A Goal 전환까지다.

이 smoke는 identity hardening·Quinn 발소리·Debug Asset 구현 뒤에 실행하며 기존 bounded C++ 완료와 별도로 기록한다.

### 7.12.4 Phase 3B 전체 조사

1. 뒤쪽 Hearing 시나리오를 시작한다.
2. Manny가 소리 위치를 향해 회전하는지 확인한다.
3. Manny가 NavMesh 경로로 조사 위치까지 이동하는지 확인한다.
4. Manny가 정해진 검색 지점을 방문하는지 확인한다.
5. Manny가 처음 배치된 Home 위치로 돌아오는지 확인한다.
6. 현재 Goal이 `IdleObserve`로 돌아오는지 확인한다.

이 시나리오는 Phase 3B 구현 뒤에 통과해야 한다.

### 7.12.5 경로 실패

1. Noise Event를 NavMesh 밖의 막힌 위치에 발생시킨다.
2. 이동 요청이 `PathUnavailable`로 끝나는지 확인한다.
3. Goal이 현재 단계의 회복 경로를 한 번 적용하는지 확인한다.
4. Manny가 오래된 위치를 향해 계속 이동하지 않는지 확인한다.

### 7.12.6 여러 Manny

1. Manny Guard를 세 명 배치한다.
2. 각 Pawn을 서로 다른 시작 위치에 둔다.
3. 한 Noise Event를 발생시킨다.
4. 각 Pawn의 Home, Knowledge revision, Goal instance와 Skill 상태가 독립적인지 확인한다.
5. 한 Pawn의 teardown과 재등록이 다른 Pawn 상태를 바꾸지 않는지 확인한다.

### 7.12.7 제품 Phase 1 확장 시나리오

다음 장면은 같은 Test Level의 제한 구역과 Cover 구역에서 후속 구현한다.

#### 판단 중 피격

```text
이전 판단 요청 진행 중
→ 서버 Damage 사건
→ 이전 판단 supersede
→ 새 긴급 판단만 Commit 가능
```

피격 Actor와 Damage source는 Authority가 발행한 사실만 사용한다.

이전 응답이 늦게 도착해도 Skill을 시작하면 안 된다.

#### Cover 예약

```text
CoverSlot Candidate 선택
→ Commit에서 availability revision 재검증
→ lease 예약
→ TakeCover 시작
→ 실행 중 lease 갱신
→ 종료·실패·중단에서 해제
```

Cover Actor와 Smart Object는 Phase 0 Level 표식만으로 판단 입력에 넣지 않는다.

Resource Target, 예약 Subsystem과 rollback 검사가 준비된 뒤 연결한다.

## 7.13 Editor 설정과 Asset 검증

현재 프로젝트는 Unreal Engine `5.7`을 사용한다.

과거 문서의 새 프로젝트 이름 `AINativeNPCDemo`는 현재 작업 대상이 아니다.

현재 작업 대상은 이미 존재하는 `NeuralGame.uproject`다.

| 설정 | 현재 상태 | 지금 할 일 |
|---|---|---|
| `StateTree` plugin | 활성화 | 유지하고 Asset compile·Data Validation을 확인한다. |
| `GameplayStateTree` plugin | 활성화 | 유지한다. |
| `GameplayTags` module | Build 의존성 있음 | 생성 Registry와 Asset tag 사용에 유지한다. |
| `AIModule` | Build 의존성 있음 | Perception과 AI Controller에 사용한다. |
| `NavigationSystem` | Build 의존성 있음 | 이동 Skill과 NavMesh에 사용한다. |
| NNE와 NNE Runtime | plugin 미활성화·Build 의존성 없음 | 제품 Phase 1 설치본과 cook 지원 확인 뒤 추가한다. |
| Smart Objects | 미활성화 | Cover·resource Target 작업 전 확인한다. |

현재 일반 NPC 모듈은 `Core`, `CoreUObject`, `Engine`, `InputCore`, `EnhancedInput`, `AIModule`, `NavigationSystem`, `StateTreeModule`, `GameplayStateTreeModule`, `GameplayTags`, `Json`, `UMG`, `Slate`를 공개 의존성으로 가진다.

NNE Runtime 이름과 header 경로는 문서 예시로 추측하지 않는다.

실제 Unreal Engine 5.7 설치본, Development·Shipping build와 cook 결과로 확인한 이름만 `.uproject`와 `Build.cs`에 추가한다.

Asset 작업 후 다음 순서를 수행한다.

1. 모든 수정 Asset을 저장한다.
2. Level과 Asset에 compile error가 없는지 확인한다.
3. `Validate Assets in Folder`로 `/Game/AINativeNPC`를 검사한다.
4. 전체 Data Validation을 실행한다.
5. Editor를 종료하고 다시 연다.
6. Level, Manny 인스턴스, StateTree 참조와 GameMode를 다시 읽는다.
7. GameDevMCP로 Asset 경로와 주요 설정을 다시 조회한다.
8. Play 시나리오를 다시 실행한다.

## 7.14 Unreal 수직 구성 완료 조건

전용 Unreal 수직 구성은 다음 조건을 모두 만족하면 완료다.

- `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`가 저장돼 있다.
- Quinn이 기존 Third Person 입력으로 움직인다.
- Quinn은 서버가 한 번 초기화한 유효한 Entity identity를 정확히 한 개 가진다.
- Manny Guard가 native shipping Pawn과 Controller assembly를 사용한다.
- Manny는 `SKM_Manny_Simple`과 `ABP_Unarmed`로 보인다.
- NavMesh가 Guard Home, 조사 구역과 Return Route를 연결한다.
- 벽을 이용해 Sight 획득과 상실을 재현할 수 있다.
- Quinn 실제 발 접촉이 Hearing Event를 만든다.
- 디버그 화면이 Goal, Knowledge, Target과 Skill 상태를 표시한다.
- Phase 3A Goal 전환을 Play에서 확인한다.
- Phase 3B 전체 조사 흐름을 Play에서 확인한다.
- Data Validation의 error와 warning이 0개다.
- Editor 재시작 뒤 Asset과 설정이 그대로 유지된다.
- 자동검사 성공과 별도로 최신 source에 결속된 독립 재검토가 통과한다.

---

<a id="components"></a>
# 8. Unreal 구성요소의 역할

이 장은 각 구성요소가 소유하는 일과 전달하는 결과를 정한다.

## 8.1 Perception과 Knowledge

Knowledge의 역할은 **NPC가 직접 얻은 사실을 현재 상태와 사건 기록으로 보관하는 것**이다.

- Sight는 현재 보이는 Entity를 갱신한다.
- Hearing은 변경되지 않는 SoundEvent를 추가한다.
- Sight Lost는 마지막으로 확인한 위치를 만든다.
- 각 사실은 source, age, confidence와 TTL을 가진다.
- Knowledge는 정보 저장이 끝난 뒤 event sink를 호출한다.
- Knowledge 입력의 허용 범위는 현재 관측과 마지막으로 확인한 Snapshot이다.

## 8.2 Goal Runtime

Goal Runtime의 역할은 **현재 목적, 단계, 수명과 전환을 관리하는 것**이다.

- Active Goal은 한 개다.
- Suspended Goal은 남은 Timer와 함께 보존할 수 있다.
- Terminal Goal의 수명은 종료 상태로 고정된다.
- 단계 전환은 생성된 guard 순서를 따른다.
- effect는 먼저 intent를 만들고 Host가 안전하게 적용한다.

## 8.3 Target Slotter

Target Slotter의 역할은 **Knowledge와 Goal의 Target을 고정된 17개 자리에 배치하는 것**이다.

- 일반 Target은 최대 16개다.
- 마지막 자리는 `NoTarget`이다.
- 현재 Skill Target과 Goal 주 Target 같은 필수 항목을 먼저 배치한다.
- 같은 Target은 한 번만 배치한다.
- 정렬 결과는 같은 입력에서 항상 같다.
- 필수 Target이 범위를 넘으면 선택을 보류한다.

정확한 정렬과 quota는 [세부 기술 요구사항의 Target 장](technical-requirements.md#3-target-universe와-slotter)이 소유한다.

## 8.4 Candidate Builder

Candidate Builder의 역할은 **16개 Skill과 17개 Target 자리를 조합해 272개 행동 후보를 만드는 것**이다.

- 각 Candidate는 Skill ID와 Target 자리로 결정된다.
- 게임 규칙은 실행 가능한 Candidate만 표시한다.
- 현재 Goal과 단계가 Skill 허용 범위를 제공한다.
- Target 종류, 시야, 자원과 실행 조건을 확인한다.
- 실행 중인 행동의 Continue 조건을 별도로 확인한다.
- 결과는 Candidate Hash와 함께 고정된다.

## 8.5 Feature Builder

Feature Builder의 역할은 **Candidate를 고를 때 사용할 숫자와 mask를 하나의 변경 불가능한 Snapshot으로 확정하는 것**이다.

- Target 결과와 Candidate 결과를 함께 받는다.
- 생성 계약의 정규화 규칙을 사용한다.
- 모든 실수 입력의 유한성을 확인한다.
- Canonical bytes와 입력 Hash를 만든다.
- Candidate Hash와 입력 Hash를 결속한다.

## 8.6 Utility 선택

Utility의 역할은 **실행 가능한 Candidate의 점수를 계산하고 하나를 선택하는 것**이다.

- Skill별 기본 점수와 Candidate Feature 가중치를 사용한다.
- 실행 중인 행동을 바꾸는 비용을 적용한다.
- Candidate mask를 통과한 행만 평가한다.
- 같은 입력은 같은 결과를 만든다.
- 동점 규칙은 계약이 정한 순서를 따른다.

Phase 3B는 Utility를 실제 게임 경로의 선택기로 사용한다.

## 8.7 Commit Coordinator

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

## 8.8 Skill Executor와 StateTree

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
# 9. Neural Policy와 학습 모델

Neural Policy의 역할은 **게임 규칙이 허용한 Candidate 안에서 더 자연스러운 행동의 순위를 매기는 것**이다.

## 9.1 현재 상태

제품 Phase 0의 실제 연결은 Utility를 사용한다.

ONNX ModelData와 NNE Adapter는 제품 Phase 1의 구현 대상이다.

## 9.2 구현할 순서

1. Dataset Record와 split 규칙을 고정한다.
2. Python과 Unreal이 같은 Feature 값을 만드는지 확인한다.
3. 작은 fixture 모델을 학습하고 ONNX로 내보낸다.
4. Unreal NNE가 입력과 출력 descriptor를 확인한다.
5. `B=1,2,4,8` batch의 ORT와 NNE 결과를 비교한다.
6. 모델 실패 시 같은 Snapshot의 Utility 결과를 사용한다.
7. Calibration과 OOD asset을 추가한다.
8. 패키징한 Development와 Shipping 게임에서 최소 실제 경로를 끝까지 실행한다.

## 9.3 Unreal 연결 조건

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
# 10. 보스 공격 패턴

보스 공격 패턴의 역할은 **공통 `Attack(Entity)` Candidate가 선택된 뒤 실제 공격 절차 하나를 고르는 것**이다.

## 10.1 공통 판단과의 관계

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

## 10.2 현재 구현

- Pattern 정의와 Set Data Asset
- 32개 Pattern 자리와 mask
- Utility 선택과 Neural 출력 정리 Core
- Commit, one-shot handoff와 실행 Session
- StateTree `PreAttackTurn` 시작 경로
- 고정 테스트 자산을 사용한 Pawn과 Controller assembly

## 10.3 후속 작업

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
# 11. 서버, 저장과 성능

이 장은 제품 Phase 1에서 연결할 권한, 저장과 부하 기준을 요약한다.

## 11.1 서버와 클라이언트

서버는 판단과 실행을 소유한다.

클라이언트는 확정된 결과를 화면에 표시한다.

| 서버 상태 | 클라이언트 표시 상태 |
|---|---|
| Perception과 Knowledge | 현재 Skill |
| Goal과 Target 선택 | 필요한 Target 표시 정보 |
| Candidate와 Policy | 서버 시작 시각 |
| Commit과 자원 예약 | 애니메이션 상태 |
| Skill 결과 | 종료 결과와 cue |

## 11.2 저장과 불러오기

저장 대상은 Goal instance와 revision, Knowledge source와 age, active Skill Snapshot이다.

불러온 뒤 만료된 Knowledge를 정리하고 자원 예약을 다시 얻는다.

판단 중인 Neural 요청은 새 상태로 다시 요청한다.

## 11.3 성능 검증

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
# 12. 파일별 작업 위치

이 장은 실제 `NeuralGame` 파일과 Phase 3B에서 수정할 위치를 보여 준다.

## 12.1 실제 일반 NPC Runtime

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

## 12.2 Phase 3B의 중심 파일

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

## 12.3 현재 Unreal Asset

| 역할 | 현재 Asset |
|---|---|
| 기본 Level | `Content/ThirdPerson/Lvl_ThirdPerson.umap` |
| Quinn Player | `Content/ThirdPerson/Blueprints/BP_ThirdPersonCharacter.uasset` |
| 기본 GameMode | `Content/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.uasset` |
| 기본 Player Controller | `Content/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController.uasset` |
| Quinn Mesh | `Content/Characters/Mannequins/Meshes/SKM_Quinn_Simple.uasset` |
| Manny Mesh | `Content/Characters/Mannequins/Meshes/SKM_Manny_Simple.uasset` |
| 공용 이동 Animation | `Content/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.uasset` |
| 기본 입력 | `Content/Input/IMC_Default.uasset` |
| 일반 NPC Skill handoff | `Content/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff.uasset` |
| 보스 실행 StateTree | `Content/AINativeNPC/BossPattern/StateTree/ST_BossPatternExecution.uasset` |
| 보스 Pawn | `Content/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterPawn.uasset` |
| 보스 Controller | `Content/AINativeNPC/BossPattern/Encounter/BP_BossPatternEncounterAIController.uasset` |

## 12.4 Unreal 수직 구성에서 수정할 C++ 파일

| 파일 | 수정 목적 | 현재 상태 |
|---|---|---|
| `Source/NeuralGame/NeuralGameCharacter.h/.cpp` | Quinn에 exact-one identity Component를 C++ 기본 Subobject로 둔다. | RED 검사 전 |
| `Knowledge/AINativeNPCEntityIdentitySubsystem.h/.cpp` | persistent key, stable ID, spawn generation과 private ingress를 소유한다. | 새 파일 목표 |
| `Knowledge/AINativeNPCTargetIdentityComponent.h/.cpp` | Editor 수정 경로와 public initializer를 제거한다. | Core 있음·hardening 없음 |
| `Knowledge/TypedTargetKnowledgeComponent.h/.cpp` | Sight·Hearing 공통 exact identity validator와 Sight 재획득 정리를 추가한다. | 저장 경로 있음·Hearing hardening 없음 |
| `Knowledge/AINativeNPCGuardController.h/.cpp` | `UAINativeNPCSensorConfig`을 검증하고 한 번 적용한다. | 현재 C++ 시작값 사용 |
| `Execution/AINativeNPCGuardPawn.h/.cpp` | exact native class를 유지하고 `UAINativeNPCVisualProfile`을 적용한다. | visual 적용 없음 |
| `Execution/AINativeNPCGoalHostComponent.h/.cpp` | Phase 3B 판단과 Skill 결과 기반 Goal 진행을 연결한다. | Phase 3A 있음 |
| `Profiles/AINativeNPCVisualProfile.h/.cpp` | Manny Mesh·Anim Class·relative transform을 제공한다. | 새 파일 목표 |
| `Profiles/AINativeNPCSensorConfig.h/.cpp` | Sight·Hearing·TTL과 surface loudness를 제공한다. | 새 파일 목표 |
| `Profiles/AINativeNPCDebugProfile.h/.cpp` | Editor·Development 표시 bool·색·거리를 제공한다. | 새 파일 목표 |
| `Player/PlayerNoiseEmitterComponent.h/.cpp` | Quinn의 속도·surface별 Hearing Event를 서버에서 만든다. | 새 파일 목표 |
| `Player/AnimNotify_ReportAINoise.h/.cpp` | 발 접촉 프레임을 Noise Emitter에 전달한다. | 새 파일 목표 |
| `Tests/AINativeNPCNoiseTestEmitter.h/.cpp` | test-only identity가 있는 Hearing 자극을 한 번 만든다. | 새 파일 목표 |
| `Debug/AINativeNPCDebugComponent.h/.cpp` | immutable `FAINativeNPCDebugSnapshot`을 만든다. | 새 파일 목표 |
| `Debug/AINativeNPCDecisionLog.h/.cpp` | 구조화된 Decision Log를 기록한다. | 새 파일 목표 |
| `Debug/AINativeNPCDecisionCaptureSubsystem.h/.cpp` | JSON·binary Capture와 SHA-256을 저장한다. | 새 파일 목표 |
| `Debug/AINativeNPCDecisionReplaySubsystem.h/.cpp` | Capture를 pure Core 또는 preview world에서 재생한다. | 새 파일 목표 |
| `Tests/*.cpp` | identity, Visual·Sensor validation, Perception, 발소리, Debug, Level smoke와 Phase 3B RED를 소유한다. | 기존 검사 확장 |

표의 상대 경로는 `Source/NeuralGame/AINativeNPC/` 아래다.

새 class 이름과 책임은 사용자 확인 뒤 하네스에서 먼저 고정한다.

## 12.5 Unreal 수직 구성에서 만들 Asset

| 순서 | Asset | 제작 기준 |
|---:|---|---|
| 1 | `Content/AINativeNPC/Characters/DA_AINativeNPCVisual_Manny.uasset` | Manny Mesh·Animation·relative transform을 제공한다. |
| 2 | `Content/AINativeNPC/Perception/DA_AINativeNPCSensor_Guard.uasset` | 현재 C++ Sensor·TTL 값과 surface loudness에서 시작한다. |
| 3 | `Content/AINativeNPC/Debug/DA_AINativeNPCDebug_Default.uasset` | 표시 bool·색·거리를 제공한다. |
| 4 | `Content/AINativeNPC/Tests/BP_AINoiseTestEmitter.uasset` | `AAINativeNPCNoiseTestEmitter`의 Blueprint 자식이다. |
| 5 | `Content/AINativeNPC/Debug/BP_AINativeNPCDebugDisplay.uasset` | Test Level의 Widget과 월드 표시를 켠다. |
| 6 | `Content/AINativeNPC/Debug/WBP_AINativeNPCDecisionInspector.uasset` | immutable Debug Snapshot과 Replay Result를 표시한다. |
| 7 | Walk Animation Sequence 8개 | 왼발·오른발 `UAnimNotify_ReportAINoise`를 배치한다. |
| 8 | Jog Animation Sequence 8개 | 왼발·오른발 `UAnimNotify_ReportAINoise`를 배치한다. |
| 9 | Surface A·B Physical Material과 바닥 Material | `AINPC_SurfaceA/B`와 Sensor loudness를 연결한다. |
| 10 | `Content/AINativeNPC/Maps/L_AINativeNPC_MVP.umap` | 위 Asset을 사용해 Manny, Quinn, NavMesh, 차폐물과 시험 구역을 배치한다. |
| 11 | Neural Policy와 ModelData | 제품 Phase 1 NNE 검증 뒤 만든다. |

Phase 0에서는 `BP_AINativeNPC_Manny`, Goal Profile, Utility Profile과 Guard role Profile을 만들지 않는다.

Asset 변경은 사용자가 실행한 Editor와 GameDevMCP를 사용한다.

Asset은 저장 뒤 Editor를 재시작하고 GameDevMCP로 다시 읽어 영속성을 확인한다.

---

<a id="verification-order"></a>
# 13. 검증 순서와 완료 조건

검증은 계약에서 실제 게임 흐름으로 범위를 넓힌다.

## 13.1 실행 순서

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

## 13.2 현재 Unreal 명령 인터페이스

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

## 13.3 기능별 검사

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

## 13.4 완료 판정

| 판정 | 뜻 |
|---|---|
| 계약 완료 | Registry와 생성 결과가 일치한다. |
| Core 완료 | 순수 C++ 단위 테스트가 통과한다. |
| 연결 단계 완료 | 실제 Pawn과 Host 경로의 변경 기능·관련 기능 검사가 통과한다. |
| 제품 완료 | 전체 기능, 품질, 성능, 저장, 복제와 Release 승인이 끝난다. |

각 완료 판정은 표에 적힌 범위에만 적용한다.

---

<a id="risks"></a>
# 14. 주요 위험과 대응

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
# 15. 권한 문서와 자동 생성 참고

## 15.1 독자가 찾을 문서

| 궁금한 내용 | 문서 |
|---|---|
| 제품 목적과 쉬운 설명 | [제품 요구사항](requirements.md) |
| Goal, Target, Candidate와 Commit의 정확한 동작 | [세부 기술 요구사항](technical-requirements.md) |
| 데이터, 학습과 전체 구현 순서 | [공통 구현 계획](implementation-plan.md) |
| 정확한 ID, 수치와 품질 기준 | [계약 부록](contract-appendices.md) |
| 과거 Unreal 상태와 검증 기록 | [Unreal 구현 이력 v0.4.15](../history/unreal-implementation-history-v0.4.15.md) |
| 전체 문서 이력 | [문서 이력](../history/README.md) |

## 15.2 현재 계약 식별 정보

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

## 15.3 자동 생성된 Goal 상태

아래 영역은 생성기가 관리한다.

본문의 쉬운 상태 설명은 [0.2 현재 상태](#current-status)에 있다.

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

## 15.4 자동 생성된 품질 기준

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
