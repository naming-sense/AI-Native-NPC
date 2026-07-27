# AI Native NPC 실행형 문서·계약 하네스 v0.4.6

v0.4.6은 **Validation Scope & Catalog Closure / Schema 2.0 RC5** 패키지다. v0.4.5의 계약을 유지하면서 문서 의미 검증 범위와 Archive Catalog의 양방향 정합성을 닫는다.

## 이번 릴리스에서 닫은 범위

1. 현재 Requirements와 UE 문서뿐 아니라, Lock 대상인 모든 non-archive 수기 Markdown을 Hash 계약과 Critical Suite 분모 검사 대상으로 포함한다.
2. `docs/archive/`, `contracts/archive/`, `manifests/archive/`, `generated/docs/`는 전역 수기 문서 검사에서 제외한다.
3. 현재 Requirements와 UE 문서에서만 승인된 자동 생성 블록을 제거한 뒤 수기 영역을 검사한다.
4. 대문자·소문자·숫자·밑줄을 포함한 일반 Hash magic 배정문을 차단한다.
5. README를 실제로 변조한 전체 `release` 회귀 테스트를 규범 증거로 포함한다.
6. Catalog의 Archive 항목과 실제 Archive 파일 집합을 양방향 exact-match로 검증한다.
7. Source File Map을 실제 Current/Archive 경로에서 자동 생성한다.
8. Missing/Ghost Archive 회귀 테스트를 포함한다.

## 현재 기준선

| 역할 | 현재 기준 |
|---|---|
| 요구사항·구현 계약 | `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md` |
| UE 5.7 Manny/Quinn 구현 프로필 | `docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md` |
| Tensor·Enum·Normalization 단일 원본 | `contracts/current/ai_native_npc_schema_v2_0.yaml` |
| Skill 계약 | `contracts/current/skill_registry_v1.yaml` |
| Goal 계약 | `contracts/current/goal_registry_v1.yaml` |
| Test Taxonomy | `contracts/current/test_taxonomy_v1.yaml` |

## 판정

- Phase 0: **GO**
- 문서·Schema 하네스: **Freeze-ready / Runtime Gate pending**
- Schema 설계 RC5: **Conditional GO**
- 대량 학습 데이터: **HOLD**
- 최종 Schema Freeze: **NO-GO / Unreal Runtime Gate pending**

## 검증과 릴리스

```bash
python tools/doc_harness.py validate --strict
python tools/doc_harness.py release \
  --output ../ai_native_npc_document_harness_v0.4.6.zip
```

`release`는 계약 생성, 문서 동기화, 전역 Markdown mutation, C++/Python Golden, Manifest, Source File Map, Catalog, Lock, strict validation과 deterministic double-pack을 하나의 절차로 수행한다.

## 폴더 구조

```text
docs/current/       현재 기준 문서
docs/archive/       과거 문서
contracts/current/  코드 생성 단일 원본
contracts/archive/  과거 계약
generated/          YAML 기반 생성 코드와 표
tests/              Golden·semantic·release mutation 회귀 테스트
manifest/           Catalog·Freeze 상태·Lock·Checksum
reports/            Validation 및 Source File Map
tools/              생성·검증·릴리스 도구
```

Archive와 Legacy 계약은 현재 구현 입력으로 사용할 수 없다.
