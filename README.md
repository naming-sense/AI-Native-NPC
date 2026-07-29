# AI Native NPC

AI Native NPC의 요구사항과 Unreal Engine 5.7 구현 계약을 담은 최소 구성 저장소입니다.

- 문서·Schema 계약: **v0.4.6 / Schema 2.0 RC5**
- 기반 문서·Schema 하네스 검증: **보관 태그 기준 Freeze-ready**
- 현재 ML/NNE 구현 보강: **문서 반영 완료 / Runtime 증거 대기**
- 실제 Unreal Runtime Gate: **구현 및 검증 대기**

## 먼저 읽을 문서

1. [AI Native NPC 요구사항·구현 계획](docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md)
   - 무엇을 만들고 어떤 계약과 안전 조건을 지켜야 하는지 정의합니다.
   - §6.1과 §9.8–§9.16에 정확한 모델 Layer, Dataset, Loss, 학습 설정, Calibration/OOD, Model Bundle 계약이 있습니다.
2. [UE5.7 Manny 공간·시야·청각 구현 계획](docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md)
   - 요구사항을 Unreal에서 어떻게 구현하고 시험할지 정의합니다.
   - §14–§15에 ONNX Export, UE5.7 NNE/ORT Import, binding, batch, cook, parity, fallback 절차가 있습니다.

두 문서는 역할이 다르지만, 공통 Schema·Registry·Tensor·Hash·Goal·Skill 계약은 v0.4.6 기준으로 동기화되어 있습니다.

## 구현 기준 파일

- [Schema 2.0](contracts/current/ai_native_npc_schema_v2_0.yaml)
- [Skill Registry](contracts/current/skill_registry_v1.yaml)
- [Goal Registry](contracts/current/goal_registry_v1.yaml)
- [Test Taxonomy](contracts/current/test_taxonomy_v1.yaml)
- [생성 Python 계약](generated/python/ai_native_npc_contracts_generated.py)
- [생성 C++ 계약 Header](generated/cpp/AINativeNPCContracts.generated.h)

YAML 4개가 기계 판독 가능한 기준 계약입니다. 생성 Python 계약은 Dataset Builder·학습·ONNX Export에서, 생성 C++ Header는 Unreal Runtime에서 사용합니다. 두 생성 파일은 수동 수정하지 않습니다.

현재 `main`은 문서 2개, 계약 YAML 4개, 생성 계약 2개, README를 합친 **핵심 9개 파일**만 유지합니다.

## 전체 하네스 보관본

검증 도구, Golden Vector, mutation test, Manifest, 과거 문서·계약을 포함한 90개 파일 전체는 다음 위치에 보존되어 있습니다.

- [보관 브랜치: archive/full-harness-v0.4.6](https://github.com/naming-sense/AI-Native-NPC/tree/archive/full-harness-v0.4.6)
- [고정 태그: full-harness-v0.4.6-rc5](https://github.com/naming-sense/AI-Native-NPC/tree/full-harness-v0.4.6-rc5)
- 보관 커밋: `62dec4334671cb6dfb455b12f7c0e1b251ebc1d0`

일상적인 Unreal 구현에서는 현재 `main`의 핵심 파일만 보면 됩니다. 전체 하네스는 계약 변경 검증이나 감사가 필요할 때 사용합니다.
