# AI Native NPC

AI Native NPC는 게임 속 NPC가 알고 있는 정보와 현재 목적을 보고 다음 행동을 고르는 시스템입니다. 서버는 선택한 행동의 안전성과 유효성을 검사한 뒤 실행합니다.

이 저장소는 공통 요구사항, 구현 계획, Unreal Engine 5.7 계약과 기계 판독 Schema를 제공합니다.

## 현재 상태

일반 NPC가 평소 주변을 살피다가 유효한 소리를 들으면 조사 Goal을 시작하는 흐름을 실제 Unreal 경로에서 검증했습니다. 다음 작업은 현재 Goal에 맞는 행동을 고르고 실행 결과에 따라 다음 Goal 단계로 진행하는 흐름입니다.

### 개발자용 상세 상태

- 기계 계약: **Schema 2.0 RC5 + Goal Registry 1.1.0**, Python↔C++ 생성·Golden 검증 완료
- 소리를 듣고 조사 Goal 시작(Phase 3A): **완료**. `IdleObserve/Observe`에서 유효한 소리를 받으면 `InvestigateDisturbance/Orient`로 안전하게 전환
- 목표에 맞는 행동 선택과 진행(Phase 3B): **다음 작업**. Goal-owned Target 해결 → Candidate·Feature 생성 → Utility 선택 → Commit → Skill 실행 → 결과에 따른 Goal 단계 진행
- 일반 NPC 실행 Skill: `Idle`, `TurnTo`, `Approach`, `Investigate`, `SearchArea` 구현과 자동검사 완료
- 보스 공격 시작: 고정 테스트 입력 기반 검증 통과(PASS). Commit 뒤 StateTree start handoff focused `2/2`, broad `53/53`
- 실제 보스 전투: production PatternSet·selector trigger·authored transition·Montage·Hitbox·Damage·Root Motion·replication·save/load 구현이 필요
- AI 모델과 전체 Release: 학습·ONNX/NNE·OOD·품질·성능 검증이 남은 상태(NO-GO)

상태 표시의 뜻은 [구현 계획의 현재 상태 표시](docs/current/implementation-plan.md#04-현재-상태-표시)에서 확인할 수 있습니다.

## 먼저 읽을 문서

`docs/current` 바로 아래의 다섯 문서가 현재 구현 기준입니다.

1. [AI Native NPC 제품 요구사항](docs/current/requirements.md)
   - 도메인 지식 없이 시스템 목적, 판단 흐름, 책임과 현재 상태를 이해하는 문서입니다.
2. [AI Native NPC 세부 기술 요구사항](docs/current/technical-requirements.md)
   - Goal·Target·Candidate·timer·Commit·데이터·안전의 정확한 구현 계약입니다.
3. [AI Native NPC를 만드는 순서](docs/current/implementation-plan.md)
   - 무엇을 먼저 만들고 데이터를 어떻게 준비해 모델을 학습·검증할지 설명합니다.
4. [AI Native NPC Contract Appendices](docs/current/contract-appendices.md)
   - Schema·Registry의 생성 표와 품질·안전·성능 승인 기준을 제공합니다.
5. [UE5.7 Manny 공간·시야·청각 구현 계획](docs/current/unreal-implementation-plan.md)
   - 요구사항을 Unreal에서 구현하고 시험하는 절차를 정의합니다.

제품 요구사항은 목적과 책임을 설명합니다. 세부 기술 요구사항은 정확한 Runtime 의미를, Implementation Plan과 UE Plan은 실행 절차를, Contract Appendices는 생성된 값과 승인 Gate를 제공합니다.

## 문서 작성 규칙

- 정의와 결론을 첫 문장에 씁니다.
- `A는 C다` 형태의 짧고 긍정적인 문장을 사용합니다.
- 오해나 틀린 정의를 먼저 소개하는 문장은 생략합니다.
- 한 문장에는 하나의 판단을 담습니다.
- 정식 독자용 명칭을 먼저 정의하고 문서 전체에서 같은 이름을 사용합니다.
- 코드·Schema 식별자는 독자용 명칭 뒤에 괄호로 표시합니다.

예시:

> Knowledge는 NPC가 관측하거나 전달받아 보관하는 정보다.
> 현재 코드와 Schema에서는 `Belief`라는 이름을 사용한다.

## 구현 기준 파일

- [Schema 2.0](contracts/current/ai_native_npc_schema_v2_0.yaml)
- [Boss Pattern Policy Contract](contracts/current/boss_pattern_contract_v1.yaml)
- [Skill Registry](contracts/current/skill_registry_v1.yaml)
- [Goal Registry](contracts/current/goal_registry_v1.yaml)
- [Test Taxonomy](contracts/current/test_taxonomy_v1.yaml)
- [생성 Python 계약](generated/python/ai_native_npc_contracts_generated.py)
- [생성 Goal Gameplay 계약](generated/python/ai_native_npc_goal_gameplay_semantics_generated.py)
- [생성 Skill 실행 계약](generated/python/ai_native_npc_skill_execution_semantics_generated.py)
- [생성 Boss Pattern Python 계약](generated/python/ai_native_npc_boss_pattern_contracts_generated.py)
- [생성 C++ 계약 Header](generated/cpp/AINativeNPCContracts.generated.h)
- [생성 Goal Gameplay C++ Header](generated/cpp/AINativeNPCGoalGameplaySemantics.generated.h)
- [생성 Skill 실행 C++ Header](generated/cpp/AINativeNPCSkillExecutionSemantics.generated.h)
- [생성 Boss Pattern C++ 계약 Header](generated/cpp/AINativeNPCBossPatternContracts.generated.h)

YAML 5개가 기계 판독 가능한 기준 계약입니다. Goal과 Skill 생성기는 각 Registry에서 Python·C++·사람이 읽는 표를 만듭니다. 공통 생성 계약은 272 Candidate를, Boss Pattern 생성 계약은 `Attack(Entity)` 하위의 별도 32 Pattern row를 정의합니다. 생성 파일은 수동으로 수정하지 않습니다.

현재 `main`은 현행 문서와 계약 YAML·생성 계약을 유지합니다. 완료된 감사·계획 기록은 [`docs/history`](docs/history/README.md)에 분리합니다.

## 문서 이력

과거 판정, 완료된 검토, 문서 정리 계획은 [문서 이력 안내](docs/history/README.md)에서 확인합니다. 현재 구현 기준은 `docs/current`에서 확인합니다.

## 전체 하네스 보관본

검증 도구, Golden Vector, mutation test, Manifest, 과거 문서·계약을 포함한 전체 하네스는 다음 위치에 보존되어 있습니다.

- [보관 브랜치: archive/full-harness-v0.4.6](https://github.com/naming-sense/AI-Native-NPC/tree/archive/full-harness-v0.4.6)
- [고정 태그: full-harness-v0.4.6-rc5](https://github.com/naming-sense/AI-Native-NPC/tree/full-harness-v0.4.6-rc5)
- 보관 커밋: `62dec4334671cb6dfb455b12f7c0e1b251ebc1d0`

일상적인 Unreal 구현에서는 현재 `main`의 핵심 파일만 보면 됩니다. 전체 하네스는 계약 변경 검증이나 감사가 필요할 때 사용합니다.
