# AI Native NPC

AI Native NPC는 NPC가 알고 있는 정보와 현재 Goal을 바탕으로 실행 가능한 행동 후보의 순위를 정하고, 서버 검증 후 Skill을 실행하는 의사결정 시스템입니다.

이 저장소는 공통 요구사항, 구현 계획, Unreal Engine 5.7 계약과 기계 판독 Schema를 제공합니다.

## 현재 상태

쉽게 말하면 **보스 전투는 Commit 뒤 production StateTree를 시작하는 안전한 handoff까지 구현됐고, 공통 Goal FSM은 기계 계약 동기화 후 RED 테스트 단계**다. 실제 Belief/Target 기반 Goal 판단과 전투 효과는 아직 없다.

- 정적 계약: **Schema 2.0 RC5 + Goal Registry 1.1.0**, Python↔C++ 생성·Golden 검증 완료
- Goal 계약 배포: **41 transition = 35 event + 6 timer**, authority commit `2770b4a5...`로 consumer lock/sync 완료
- 제한된 Goal Core: **`GoalFsmRuntimeTests.cpp` RED 테스트 존재; Runtime `.h/.cpp`와 server timer component는 아직 없음**
- Gameplay Goal FSM: **production Belief·Goal·Typed Target producer, 29 guard·2 effect provider, 전체 arbitration/save archive가 없어 HOLD**
- Boss Pattern 실행 기반: **fixture-backed Session/EventSource/Host exact-one, Commit 뒤 StateTree start handoff phase PASS; focused `2/2`, broad `53/53`**
- Boss Pattern 남은 실행: **production PatternSet/selector trigger, authored transition, Montage·Hitbox·Damage·Root Motion·replication/save-load 대기**
- AI 모델과 전체 Release: **학습·ONNX/NNE·OOD·품질·성능 Gate가 남아 있어 NO-GO**

## 먼저 읽을 문서

`docs/current` 바로 아래의 다섯 문서가 현재 구현 기준입니다.

1. [AI Native NPC 제품 요구사항](docs/current/requirements.md)
   - 도메인 지식 없이 시스템 목적, 판단 흐름, 책임과 현재 상태를 이해하는 문서입니다.
2. [AI Native NPC 세부 기술 요구사항](docs/current/technical-requirements.md)
   - Goal·Target·Candidate·timer·Commit·데이터·안전의 정확한 구현 계약입니다.
3. [AI Native NPC 구현 계획](docs/current/implementation-plan.md)
   - Phase·Owner·완료 조건, Reference Model, Teacher LLM, 학습·릴리스 Pipeline을 정의합니다.
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
- [생성 Boss Pattern Python 계약](generated/python/ai_native_npc_boss_pattern_contracts_generated.py)
- [생성 C++ 계약 Header](generated/cpp/AINativeNPCContracts.generated.h)
- [생성 Boss Pattern C++ 계약 Header](generated/cpp/AINativeNPCBossPatternContracts.generated.h)

YAML 5개가 기계 판독 가능한 기준 계약입니다. 공통 생성 계약은 272 Candidate를, Boss Pattern 생성 계약은 `Attack(Entity)` 하위의 별도 32 Pattern row를 정의합니다. 생성 Python 계약은 Dataset Builder·학습·ONNX Export에서, 생성 C++ Header는 Unreal Runtime에서 사용하며 수동 수정하지 않습니다.

현재 `main`은 현행 문서와 계약 YAML·생성 계약을 유지합니다. 완료된 감사·계획 기록은 [`docs/history`](docs/history/README.md)에 분리합니다.

## 문서 이력

과거 판정, 완료된 검토, 문서 정리 계획은 [문서 이력 안내](docs/history/README.md)에서 확인합니다. 현재 구현 기준은 `docs/current`에서 확인합니다.

## 전체 하네스 보관본

검증 도구, Golden Vector, mutation test, Manifest, 과거 문서·계약을 포함한 전체 하네스는 다음 위치에 보존되어 있습니다.

- [보관 브랜치: archive/full-harness-v0.4.6](https://github.com/naming-sense/AI-Native-NPC/tree/archive/full-harness-v0.4.6)
- [고정 태그: full-harness-v0.4.6-rc5](https://github.com/naming-sense/AI-Native-NPC/tree/full-harness-v0.4.6-rc5)
- 보관 커밋: `62dec4334671cb6dfb455b12f7c0e1b251ebc1d0`

일상적인 Unreal 구현에서는 현재 `main`의 핵심 파일만 보면 됩니다. 전체 하네스는 계약 변경 검증이나 감사가 필요할 때 사용합니다.
