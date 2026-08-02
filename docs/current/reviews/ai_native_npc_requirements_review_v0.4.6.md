# AI Native NPC v0.4.6 요구사항·구현 계약 검토 보고서

- 검토 대상: `docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md`
- 대상 `main` commit: `f068bc16ba84e0149bfae91b429164e9c252b29f`
- 대상 문서 SHA-256: `da69e31934d7549ab5cb5bce209bfb4e233731d88ddd3fc96318fabed3aa5ac4`
- 검토일: 2026-08-02
- 판정: **Changes Requested**
- 범위: Requirements, Schema/Registry, generated contracts, UE 구현 계획, 보관 Harness 증거의 정적·교차 계약 검토

---

## 1. 요약 판정

| 범위 | 판정 | 근거 |
|---|---|---|
| Phase 0 구현 착수 | 조건부 GO | Utility Baseline 중심 수직 슬라이스는 가능하나 아래 P0 계약을 임의 해석하지 않아야 함 |
| 기존 RC5 Schema/Generated Harness | PASS | 보관 태그 clean archive에서 `validate --strict` 실행 성공 |
| ML/NNE Supplement | 변경 필요 | OOD Runtime 입력과 학습 Switch Cost record가 닫히지 않음 |
| V1 대량 데이터 생성 | HOLD | Dataset identity/split/catalog 계약 보강 필요 |
| Schema 2.0 최종 Freeze | NO-GO | Runtime/ONNX/Goal/Commit Gate와 새 계약 재생성 필요 |
| 전체 Release | Release-green 아님 | 보관 validation report의 Runtime·승인 Gate 14개 pending |

현재 문서는 Typed Target, Hidden Information, 생성 계약 및 Atomic Commit의 큰 방향은 우수하다. 그러나 ML/NNE Supplement와 Goal Runtime 계약에는 구현자가 서로 다르게 해석할 수 있는 차단 결함이 있다. 따라서 Phase 0의 제한된 착수와 V1/Freeze 승인을 분리해야 한다.

---

## 2. 실제 검증 결과

### 2.1 실행한 확인

```bash
# 현재 main
HEAD=f068bc16ba84e0149bfae91b429164e9c252b29f

# 보관 태그 clean archive
python3 tools/doc_harness.py validate --strict
# PASS

# 현재 generated Python
python3 -m py_compile generated/python/ai_native_npc_contracts_generated.py
# PASS
```

추가 확인:

- 현재 YAML 4개와 generated Python/C++ 2개는 `full-harness-v0.4.6-rc5` 태그의 파일과 byte-identical이다.
- UE 문서에 기록된 Requirements/Schema/Registry/Test Taxonomy SHA는 검토 시점 파일과 일치했다.
- 현재 ML/NNE Supplement는 보관 태그 이후 Requirements에 397줄 추가·3줄 삭제된 변경이다.
- Requirements 자체가 밝히듯 이 Supplement는 기존 90파일 Lock bundle에 포함되지 않는다.

### 2.2 PASS의 정확한 의미

보관 Harness PASS는 다음을 증명한다.

- Schema/Registry semantic validation
- generated Python/C++ 재현성
- canonical serialization 및 discrete/hash Golden
- generated Appendix parity
- Lock/Catalog/Archive 문서 하네스 정합성

다음을 증명하지 않는다.

- Python↔Unreal Float Tensor parity
- ONNX↔Unreal NNE output parity
- Target/Candidate Recall
- Goal FSM Runtime
- Atomic Commit Runtime
- Hidden Information Leakage
- Safety Fuzz
- Calibration/OOD
- Performance
- Save/Load/Hot-swap
- Decision Contract Runtime binding
- Formal Freeze approval

따라서 이 보고서에서는 `Harness PASS`, `Runtime pending`, `Release-green`을 서로 다른 상태로 취급한다.

---

## 3. 규칙 적용·집행 매트릭스

| 규칙군 | 주 독자 | 적용 Runtime/단계 | 최종 집행 위치 |
|---|---|---|---|
| ONNX output/OOD | ML, Unreal NNE | ONNX Export, NNE binding, post-process | Schema output, Bundle Validator, UE descriptor validation, parity test |
| Switch Cost Dataset | ML, Data | Capture, Dataset Validator, training/evaluation | Dataset schema, Validator, loss/evaluation code |
| Goal arbitration/trigger | Gameplay AI, Server | Goal Manager, Save/Load | Goal Registry, generated tables, Runtime FSM tests |
| Snapshot staleness | Server, Gameplay AI | async response Commit | inference envelope, Commit Coordinator, stale tests |
| Target equality | Gameplay AI, ML | Slotter, Candidate Builder, post-process, Commit | Schema/Registry helper API와 Golden |
| Calibration/OOD Gate | ML, QA | Calibration fit, Runtime accept/abstain, evaluation | Calibration fitter, asset validator, QA Gate |
| Model Bundle hash | ML, Build/Release | Export/import/cook/startup | Bundle builder, manifest validator, Unreal commandlet |
| Recall/KPI | QA, ML, 승인자 | General/Critical evaluation | metric implementation, taxonomy/case catalog, release report |

이 Markdown 보고서는 감사 입력이지 Runtime enforcement가 아니다. 규범 변경은 Requirements에 반영하고, 실제 강제는 차기 Schema/Registry 및 구현 저장소의 도구·Runtime Gate가 담당해야 한다.

---

# 4. P0 — 구현 차단 결함

## P0-1. OOD가 요구하는 `tactical_context h`를 Unreal Runtime이 받을 수 없음

### 근거

- Requirements §6.3: OOD는 Tactical Context 128의 Mahalanobis distance `d`를 사용한다.
- Requirements §9.14: OOD asset은 `h[128]`을 기준으로 fit한다.
- Requirements §9.15: ONNX 출력은 `candidate_raw_scores`, `candidate_parameter_proposals` 두 개뿐이다.
- Schema `outputs`와 UE NNE descriptor도 동일한 두 출력만 허용하며 추가 Tensor를 load failure로 처리한다.

### 영향

ONNX/NNE 실행 뒤 Unreal post-process는 내부 encoder Tensor `h`를 얻지 못하므로 규범 OOD 계산을 수행할 수 없다. Python encoder 중복 구현이나 비공식 intermediate extraction은 현재 exact descriptor와 parity 계약에 포함되지 않는다.

### 요구 변경

- ONNX/Schema 세 번째 출력으로 `tactical_context [B,128] float32`를 추가한다.
- PyTorch↔ORT↔NNE에서 해당 출력 parity를 검증한다.
- Unreal descriptor, Model Bundle manifest, OOD asset binding, `decision_contract_hash`를 함께 갱신한다.
- 이는 “Schema 값 변경 없음” 보강이 아니라 Schema output 계약 변경으로 처리한다.

---

## P0-2. Dataset Record만으로 Runtime Switch Cost를 재현할 수 없음

### 근거

Requirements §9.11은 학습에서도 Runtime과 같은 Switch Cost를 적용한다. 그러나 Dataset Record의 10개 모델 Tensor와 `candidate_pair_features`에는 `releases_or_transfers_reservation`을 재현할 현재 Reservation 상태가 없다.

### 영향

다음 결과가 Runtime과 달라질 수 있다.

- `L_set`, `L_pair`
- adjusted top-1
- best checkpoint 선택
- Calibrator label 재계산
- Unreal Capture↔Python evaluation parity

### 요구 변경

Dataset의 non-model metadata에 다음을 추가한다.

```text
switch_cost_terms bool [272,4]
  0 skill_changed
  1 target_changed
  2 before_min_duration
  3 releases_or_transfers_reservation
```

Validator는 `postprocess_version`의 고정 계수로 `switch_cost [272]`를 재계산하고 Capture 값과 대조한다. `target_changed`는 `IdentityKey` 기준으로 고정한다.

---

## P0-3. Goal Arbitration 본문과 `goal_registry_v1.yaml`이 충돌함

### 근거

1. Registry의 `preemption_margin: 50`이 Requirements/UE 본문에 실행 의미 없이 존재한다.
2. Requirements는 `created_at`을 사용하지만 Registry는 `created_time_quantized_ms:uint64`를 사용한다.
3. Requirements는 Suspended `stack top`을 재개하지만 Registry는 `same_selection_key`를 지정한다.
4. Requirements는 interruptibility/resume policy 변경 시 `goal_revision` 증가를 요구하지만 Registry `increase_on`에는 없다.

### 영향

Python simulation, Unreal Goal Manager, Save/Load 및 Golden이 서로 다른 Goal을 선택하거나 stale response를 다르게 판정할 수 있다.

### 요구 변경

- `preemption_margin`의 비교식과 Emergency 예외를 명시한다.
- 생성시간을 server monotonic milliseconds의 `floor` quantization으로 고정한다.
- Suspended resume는 `same_selection_key` 재평가로 통일한다.
- interruptibility/resume policy 변경을 revision contract에 추가한다.
- 최대 8개 Suspended 초과 정책을 명시한다.

---

## P0-4. Goal `Timeout`이 Typed Trigger가 아니며 문서 간 transition도 충돌함

### 근거

- Goal Registry에는 `event: Timeout`이 6회 존재한다.
- Schema `event_type`에는 `Timeout`이 없다.
- 보관 Validator는 구현 내부에서만 `Timeout`을 별도 허용한다.
- Registry에는 phase timeout duration이 없다.
- UE Phase 0 표와 Registry의 transition 결과가 다르다.
  - `InvestigateDisturbance/Orient` timeout: Registry `Failed`, UE `Navigate`
  - `InvestigateDisturbance/Search`의 `SightAcquired`: Registry `Resolve`, UE `Succeeded`
  - `IdleObserve/Observe` timeout: Registry 없음, UE self transition

### 영향

Runtime이 `Timeout`을 Event Buffer enum으로 처리할지 Goal 내부 timer로 처리할지 알 수 없고, timeout 시간과 결과도 단일 원본에서 결정되지 않는다.

### 요구 변경

Trigger를 다음처럼 type-safe하게 분리한다.

```yaml
trigger:
  kind: timer
  timer_id: phase_timeout
  after_seconds: 1.5
```

```yaml
trigger:
  kind: event
  event_type: SightAcquired
```

`OnEnter`, `ForceAbort`도 lifecycle/server-control trigger로 구분한다. Goal Registry를 고친 뒤 UE Phase 표를 생성·검증한다.

---

# 5. P1 — V1/Freeze 전 필수 보강

## P1-1. Dataset identity와 contract hash 역할이 섞여 있음

`sample_id`에 Model/Calibration까지 포함하는 `decision_contract_hash`를 넣으면 새 Model을 학습하는 Dataset과 순환 관계가 생긴다. 또한 episode/decision ID와 label이 포함된 `sample_id`로는 다른 episode의 동일 입력 중복을 검출할 수 없다.

다음 세 hash를 분리한다.

```text
feature_contract_hash
  = schema + registry + normalization + slotter + postprocess contract

source_decision_contract_hash
  = capture source policy 계약, nullable

input_content_hash
  = canonical model inputs + candidate_set canonical bytes
```

`sample_id`는 immutable record identity로 유지한다. Tensor canonical bytes에는 tensor order, C-contiguous order, bool 1-byte, int64 little-endian, batch 축 제외를 명시하고 label list는 sort/dedupe한다.

---

## P1-2. OOD/Critical 실제 case allowlist가 없음

Requirements는 `test_taxonomy_v1.yaml`의 명시적 allowlist를 요구하지만 현재 Taxonomy는 family name과 최소 분모만 가진다. 실제 `scenario_family_id`, fixture ID, version, expected invariant를 가진 machine-readable case catalog가 필요하다.

---

## P1-3. `latest_snapshot_revision`이 Commit에서 사용되지 않음

일반 변화는 `dirty_flag`만 설정하고 기존 request는 Commit 가능 상태를 유지한다. Candidate Hash는 의도적으로 raw feature를 포함하지 않으므로 stale 판단은 별도 snapshot contract가 맡아야 한다.

- `latest_snapshot_revision`을 inference envelope와 response에 포함한다.
- material decision input 변경 시 이전 response를 `SnapshotSuperseded`로 거부한다.
- telemetry-only 변경은 allowlist로 제한한다.
- 허용 stale age와 Commit 후 즉시 재판단 규칙을 둔다.

---

## P1-4. Calibration threshold가 낮은 coverage로 자명하게 통과할 수 있음

현재 risk ≤0.10만 요구하면 threshold 0.95에서 accept가 거의 없거나 0건인 group이 구현에 따라 통과할 수 있다.

Group threshold 승격 조건에 다음을 추가한다.

- `accepted_count ≥ 100`
- `coverage ≥ 0.80`
- one-sided Wilson 95% risk upper bound `≤ 0.10`
- sparse group의 fallback hierarchy

OOD Gate는 ROC 임의 지점이 아니라 Runtime threshold `0.80`에서 recall/FPR을 평가한다.

---

## P1-5. `policy_manifest.json` 자기 hash 문제와 `model_sha256` 모호성

Bundle 목록에 `policy_manifest.json`이 포함된 상태에서 “모든 파일 hash를 policy manifest에 기록”하면 manifest가 자기 SHA-256을 포함해야 한다.

- `policy_manifest.json.files`는 manifest 자신을 제외한다.
- `model_sha256`은 `SHA256(policy.onnx raw bytes)`로 고정한다.
- manifest 자체는 외부 release index 또는 별도 bundle manifest hash로 검증한다.

---

## P1-6. Target equality가 `IdentityKey`인지 `SnapshotKey`인지 불명확함

`target_changed`, `same_as_current_target`, Continue remap, Event same-target 판정이 단순 “handle equality”로 표현된다. 전체 `FTargetHandle` 비교 시 Belief Revision이 증가할 때마다 같은 Actor가 새 Target으로 처리된다.

다음으로 고정한다.

```text
target_changed                  = IdentityKey changed
same_as_current_target          = IdentityKey equal
slot retain / Continue remap    = IdentityKey
snapshot stale / candidate hash = SnapshotKey
```

---

## P1-7. 현재 V1에서 `MandatoryOverflow`가 도달 불가능함

현재 source별 최대 합은 `1+1+1+2+2+2=9`이고 overflow threshold는 16 초과다. 따라서 현재 Schema `target_slots.mandatory_preserve_order`를 지키는 한 Appendix E의 `MandatoryOverflow = 0건`은 자명한 Gate다.

- 현재 V1에서는 unreachable Runtime invariant로 문서화한다.
- Schema semantic validation은 source cap 합 16 초과를 거부한다.
- Runtime 방어는 malformed-cap negative mutation test로 검증하고 품질 우수성 KPI로 사용하지 않는다.
- Reservation, secondary target, 동일 timestamp attacker의 내부 canonical key를 추가한다.

---

## P1-8. Recall metric의 분모·aggregation unit이 불명확함

다음을 machine-readable metric contract로 고정해야 한다.

- Target Recall trial: relevant target 단위
- Any-Acceptable Candidate Recall trial: decision state 단위
- Critical: sequence, decision, target 분모를 모두 보고
- episode 내 상관은 episode-cluster bootstrap CI 사용
- `Full Acceptable Recall`은 승격 Gate는 아니어도 필수 보고

---

# 6. P2 — 문서·Schema 품질 결함

1. `source_moving_probability`는 이름은 probability지만 dtype/normalizer가 bool이다. `ratio [0,1]`로 바꾸거나 `source_is_moving`으로 rename해야 한다.
2. Appendix에 `D.3` heading이 두 번 존재한다. Candidate Hash는 D.3, Decision Hash는 D.4, Normalizer는 D.5로 정리해야 한다.
3. 프로젝트 계획의 `Goal Appendix B` 의존성은 실제 Goal Registry Appendix `D.2`로 고쳐야 한다.

---

# 7. 유지할 설계 강점

1. Authoritative World / Belief / Goal / Policy / Commit의 책임 분리
2. `IdentityKey`와 `SnapshotKey` 분리
3. 숨은 Actor Transform의 전술 재주입 금지
4. Candidate Hash에서 raw float 제외
5. pending request hash 우선 비교
6. Resource CAS와 짧은 GameThread atomic boundary
7. Candidate/Target miss와 Ranking/OOD/Calibration 오류 분리
8. Test/OOD/Critical split을 Calibration 동결 전 차단
9. YAML→Python/C++→Appendix 생성·parity 체계
10. Runtime Gate pending과 대량 데이터 HOLD를 명시한 점

---

# 8. 반영 판정

이 보고서의 요구 변경은 같은 작업의 Requirements remediation에 사용한다. 다만 현재 RC5 YAML과 generated 파일은 수동 수정하지 않는다.

- Requirements: 규범 의미·필수 필드·Gate·차기 계약 변경을 반영
- UE 문서: Requirements SHA metadata 갱신과 후속 Registry-generated FSM 동기화 필요
- Schema/Registry/Generated: 후속 patch release에서 Generator로 재생성
- Runtime/ML 구현: 별도 구현 저장소에서 실제 enforcement와 evidence 생성

최종 승인 전에는 Requirements의 새 체크리스트와 보관 validation report의 pending Runtime Gate를 모두 실제 산출물로 닫아야 한다.
