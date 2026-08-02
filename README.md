# AI Native NPC

AI Native NPC는 NPC가 알고 있는 정보와 현재 Goal을 바탕으로 실행 가능한 행동 후보의 순위를 정하고, 서버 검증 후 Skill을 실행하는 의사결정 시스템입니다.

이 저장소는 공통 요구사항, 구현 계획, Unreal Engine 5.7 계약과 기계 판독 Schema를 제공합니다.

## 현재 상태

- 문서·Schema 계약: **v0.4.6 / Schema 2.0 RC5**
- 기반 문서·Schema 하네스 검증: **보관 태그 기준 Freeze-ready**
- 현재 ML/NNE 구현 보강: **문서 반영 완료 / Runtime 증거 대기**
- 실제 Unreal Runtime Gate: **구현 및 검증 대기**

## 먼저 읽을 문서

1. [AI Native NPC 요구사항](docs/current/requirements/ai_native_npc_requirements_v0.4.6.md)
   - 시스템 목적, Runtime 동작, 권한, 입출력, 안전, 데이터·평가 요구사항을 정의합니다.
2. [AI Native NPC 구현 계획](docs/current/implementation/ai_native_npc_implementation_plan_v0.4.6.md)
   - Phase·Owner·완료 조건, Reference Model, Teacher LLM, 학습·릴리스 Pipeline을 정의합니다.
3. [AI Native NPC Contract Appendices](docs/current/reference/ai_native_npc_contract_appendices_v0.4.6.md)
   - Schema·Registry의 생성 표와 품질·안전·성능 승인 기준을 제공합니다.
4. [UE5.7 Manny 공간·시야·청각 구현 계획](docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md)
   - 요구사항을 Unreal에서 구현하고 시험하는 절차를 정의합니다.

Requirements가 공통 규범을 소유합니다. Implementation Plan과 UE Plan은 실행 절차를, Contract Appendices는 생성된 정확한 값과 승인 Gate를 제공합니다.

## 구현 기준 파일

- [Schema 2.0](contracts/current/ai_native_npc_schema_v2_0.yaml)
- [Skill Registry](contracts/current/skill_registry_v1.yaml)
- [Goal Registry](contracts/current/goal_registry_v1.yaml)
- [Test Taxonomy](contracts/current/test_taxonomy_v1.yaml)
- [생성 Python 계약](generated/python/ai_native_npc_contracts_generated.py)
- [생성 C++ 계약 Header](generated/cpp/AINativeNPCContracts.generated.h)

YAML 4개가 기계 판독 가능한 기준 계약입니다. 생성 Python 계약은 Dataset Builder·학습·ONNX Export에서, 생성 C++ Header는 Unreal Runtime에서 사용합니다. 두 생성 파일은 수동 수정하지 않습니다.

현재 `main`은 현행 문서, 계약 YAML, 생성 계약과 감사·계획 문서만 유지합니다.

## 전체 하네스 보관본

검증 도구, Golden Vector, mutation test, Manifest, 과거 문서·계약을 포함한 전체 하네스는 다음 위치에 보존되어 있습니다.

- [보관 브랜치: archive/full-harness-v0.4.6](https://github.com/naming-sense/AI-Native-NPC/tree/archive/full-harness-v0.4.6)
- [고정 태그: full-harness-v0.4.6-rc5](https://github.com/naming-sense/AI-Native-NPC/tree/full-harness-v0.4.6-rc5)
- 보관 커밋: `62dec4334671cb6dfb455b12f7c0e1b251ebc1d0`

일상적인 Unreal 구현에서는 현재 `main`의 핵심 파일만 보면 됩니다. 전체 하네스는 계약 변경 검증이나 감사가 필요할 때 사용합니다.
