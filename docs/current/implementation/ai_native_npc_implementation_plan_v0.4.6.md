# AI Native NPC 구현 계획
## Reference Model·학습·릴리스·Phase 실행 계획

- 문서 버전: **v0.4.6**
- 개정일: 2026-08-02
- 주 독자: **ML, Data, Gameplay AI, Server, Unreal NNE, QA, Release 승인자**
- 범위: **Reference Model 구조, ML pipeline, Training Config, Checkpoint·Report, 구현 명령, release pipeline, Phase·Owner·일정, 최종 승인 절차**
- 상위 요구사항: [AI Native NPC 의사결정 시스템 요구사항](../requirements/ai_native_npc_requirements_v0.4.6.md)
- 계약 부록: [AI Native NPC Contract Appendices](../reference/ai_native_npc_contract_appendices_v0.4.6.md)

이 문서는 요구사항을 중복 소유하지 않는다. Runtime 동작·권한·입출력·안전·데이터·평가 규칙은 상위 요구사항을, 생성된 정확한 계약값과 승인 Gate는 계약 부록을 참조한다.

---

# 1. 독자와 실행 범위

이 계획의 작업자는 상위 요구사항과 계약 부록의 버전·Hash를 잠근 뒤 아래 순서와 산출물을 구현한다. 요구사항 또는 생성 계약값을 변경해야 하면 이 문서에서 우회하지 않고 해당 규범 원본과 생성 산출물을 먼저 갱신한다.

# 2. `policy_arch_v1.0.0` Reference Model

## 2.1 V1 모델

V1은 GRU를 사용하지 않고 최근 12개 명시적 Event Buffer를 사용한다.

### Context Encoder

```text
global_state [128] → MLP → global embedding 128
targets [17×48] + kind embedding → shared encoder → target embeddings 17×64
masked target pooling → target context 128
events [12×24] + event type embedding + referenced target embedding
→ shared encoder + temporal attention → event context 96
concat 128+128+96 = 352
→ fusion 352→256→128 = tactical context h
```

### `policy_arch_v1.0.0` 정확한 Layer 계약

아래 Layer와 상수는 V1 Reference Model의 규범 계약이다. 실험 모델은 별도 이름으로 만들 수 있지만, V1 승격 후보는 이 구조를 그대로 사용하거나 architecture version을 올리고 모든 parity·Calibration·성능 Gate를 다시 통과해야 한다.

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
  slot 16 NoTarget은 항상 valid이므로 all-masked Target 입력은 허용하지 않음

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

Scorer와 Parameter Head:

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

### Bounded Factorized Candidate Scorer

고정 Switch Cost가 학습 중 커지는 raw logit에 묻히지 않도록 Query와 Key를 정규화하고 점수 범위를 제한한다.

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


---

# 3. ML Pipeline

## 3.1 ML Training Contract 개요

규범 프로필 ID는 `policy_train_v1.0.0`이다. 학습 코드는 별도 Unreal 구현 저장소의 `ML/`에 두고, 이 저장소의 YAML과 `generated/python/ai_native_npc_contracts_generated.py`를 고정 커밋으로 가져와 사용한다.

학습 파이프라인은 다음 순서를 지킨다.

```text
Unreal Capture / Procedural Generator
→ immutable shard 작성
→ Dataset Contract Validation
→ family 단위 Split 확정 및 hash
→ Silver warm start
→ Gold + DAgger fine-tune
→ checkpoint 동결
→ OOD asset fit
→ Calibrator fit
→ ONNX export
→ PyTorch ↔ ONNX Runtime ↔ UE NNE parity
→ General/OOD/Critical/Performance Gate
→ Model Bundle 승격
```

Test, OOD, Critical split은 checkpoint와 Calibration asset이 동결되기 전 학습 코드에서 열 수 없다. Test 결과를 보고 architecture, seed, epoch, threshold를 고르면 새 실험으로 간주하고 Test split을 새 버전으로 교체한다.

## 3.2 Teacher LLM Silver Label 생성

규범 계약은 [요구사항 §9.1.1](../requirements/ai_native_npc_requirements_v0.4.6.md#911-teacher-llm-silver-label-생성)이 소유한다. 이 절은 그 계약을 중복 정의하지 않고 구현 순서와 실행 지점만 제안한다.

별도 Unreal 구현 저장소에 다음 경로를 둔다.

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

`ML/tests/test_teacher_pipeline.py`는 request/profile hash Golden, Tensor→view parity, hidden-information filtering, strict response schema, abstain invariant, mask 위반, 합의·confidence, source snapshot join과 `candidate_set_canonical_bytes` 재검증, annotation join, parameter positive-zero/mask, `selected_is_acceptable=null`, `source_type=silver`, split Gate를 fixture로 검증한다.

```bash
python -m ML.teacher.generate --profile ML/config/teacher_profile_v1.yaml --input <decision_snapshot_shard> --output <annotation_shard> --review-queue <gold_review_queue>
python -m ML.teacher.validate --profile ML/config/teacher_profile_v1.yaml --input <annotation_shard>
python -m ML.teacher.map --snapshots <decision_snapshot_shard> --annotations <annotation_shard> --output <dataset_record_v2_shard> --manifest <dataset_manifest>
python -m ML.teacher.report --profile ML/config/teacher_profile_v1.yaml --input <annotation_shard> --gold-manifest ML/config/teacher_gold_validation_manifest.json --output <report_dir>
```


---

# 4. Training Config와 Checkpoint·Report

## 4.1 Training Config

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

추가 고정:

- release seed는 `1729` 하나를 사용하고 Python, NumPy, PyTorch, DataLoader worker에 모두 전파한다.
- Role×Goal group은 epoch 안에서 균등 sampler를 사용한다. source 비율은 위 표를 따른다.
- mixed precision, TF32, quantized training은 V1 FP32 Reference에서 끈다.
- PyTorch deterministic algorithms를 켜고 non-deterministic operator 발견 시 실패한다.
- Stage B는 Stage A best checkpoint에서 시작하며 모든 Layer를 학습한다.
- Validation은 매 epoch 수행하며 Test/OOD/Critical split은 loader 등록 자체를 금지한다.
- 정확한 Python/PyTorch/ONNX/ORT/CUDA 버전, OS image digest, GPU/CPU model, driver, code commit은 `train_environment.lock.json`에 고정한다.

서로 다른 hardware/library에서 weight byte가 같다는 보장은 하지 않는다. 동일 release model을 다시 만들 때는 잠긴 환경을 사용한다. 환경이 달라 model hash가 바뀌면 새 Model Bundle로 취급하고 전체 Gate를 다시 실행한다.

## 4.2 Checkpoint 선택과 Training Report

Stage별 best checkpoint는 Validation의 다음 정렬 Key로 자동 선택한다.

```text
1. macro Role×Goal Any-Acceptable Top-1, post-switch-cost — 큰 값
2. worst Role×Goal Any-Acceptable Top-1 — 큰 값
3. annotated active parameter MAE — 작은 값
4. epoch — 작은 값
```

Top-1은 Runtime과 동일한 Adjusted Score 선택 결과로 계산한다. 보고서에는 micro/macro/worst-group, source별, Target Kind별, valid candidate count bucket별 결과와 abstain-only 분모를 모두 기록한다.

Checkpoint 파일은 weights만 담는 `model.safetensors`, architecture/config JSON, optimizer state, epoch, RNG state, Dataset/Code/Environment hash로 구성한다. Release Export는 best weights와 architecture/config만 사용하며 optimizer state는 배포하지 않는다.


---

# 5. 구현 저장소 명령

## 5.1 구현 저장소 명령과 Phase 구분

별도 구현 저장소의 CLI는 다음 단일 흐름을 제공한다.

```bash
python -m anpc_ml.dataset.validate --manifest <dataset_manifest.json>
python -m anpc_ml.train --config <train_config.json>
python -m anpc_ml.fit_calibration --checkpoint <best_checkpoint>
python -m anpc_ml.export_onnx --checkpoint <best_checkpoint>
python -m anpc_ml.parity --bundle <model_bundle_dir>
python -m anpc_ml.evaluate --bundle <model_bundle_dir>
```

Phase 0은 작은 deterministic fixture dataset으로 ONNX→Unreal 경로를 검증한다. Fixture model의 증거 범위는 통합 경로다. V1 Model Bundle은 Appendix E의 데이터·품질·안전·성능 Gate를 적용한다.


---

# 6. Cross-Environment Release Pipeline

## 6.1 Cross-Environment Release Pipeline

규범 증거에는 논리 결과와 입력·도구 Hash만 포함한다. Compiler 경로·버전, 테스트 실행시간, stdout/stderr는 `dist/local/contract_test_diagnostics.json`에만 기록하며 Lock과 ZIP에서 제외한다.

승인 산출물은 다음 단일 명령으로 만든다.

```bash
python tools/doc_harness.py release --output <bundle.zip>
```

실행 순서는 고정한다.

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

`validate --strict`는 규범 리포트의 입력 Hash·Test ID·논리 결과를 검증한다. 환경별 진단문은 byte 비교에서 제외하며, 로컬 C++17 Compiler가 있으면 동일 Golden을 추가 실행한다.


---

# 7. Phase·Owner·일정

## 7.1 Phase와 구현 범위

Phase 0은 Perception→Utility Baseline→Commit 연결과 데이터 Capture를 검증한다. Phase 1은 구조화 계약 patch·Dataset·Neural·OOD·Calibration·승격 Gate를 적용한다. 각 Phase는 Runtime 경로와 검증 증거로 완료한다.

### 7.1.1 Phase 0 = MVP Vertical Slice

범위:

- NPC Profile 1개: Guard
- Goal 2개: IdleObserve, InvestigateDisturbance
- 실행 Skill 5개: Idle, TurnTo, Approach, Investigate, SearchArea
- `ContinueCurrentAction` control candidate
- Target Kind: Entity, SoundEvent, LastKnownPosition, Waypoint, NoTarget
- Event Buffer, Target Slotter, 272 layout, Utility Baseline, 단순 Neural Scorer
- Single-player 서버 권위 형태의 GameThread Commit

### 7.1.2 Phase 1 = V1

- Role 3개
- Goal 4개
- Skill Registry 16개
- Target Kind 8개
- Calibration/OOD/Abstain
- Cover/SmartObject reservation
- 멀티플레이 서버 권위
- DAgger와 정식 KPI Gate

### 7.1.3 일정·Owner·의존성

| Workstream | Owner | Phase 0 예상 | Phase 1 예상 | 선행 의존성 |
|---|---|---:|---:|---|
| Belief/Target Runtime | Gameplay AI | 2주 | 3주 | Target contract |
| Goal Manager/FSM | Gameplay AI + Designer | 2주 | 3주 | Goal Registry Appendix D.2 + typed trigger patch |
| Slotter/Candidate/Hash | Gameplay AI + ML | 2주 | 2주 | Schema Appendix A/C/D |
| Utility Baseline | AI Designer | 1주 | 2주 | Candidate pipeline |
| Feature Builder/Golden Test | ML + Gameplay AI | 2주 | 2주 | schema.yaml generator |
| Neural Model/Export | ML | 2주 | 4주 | Golden Feature parity |
| Async Commit/Reservation | Gameplay/Server | 2주 | 4주 | Skill contract |
| Gold/DAgger Tool | Tech Designer | 1주 | 4주 | Inspector/Replay |
| QA/KPI Automation | QA + ML | 2주 | 지속 | Critical Suite |

Phase 0은 병렬 수행을 전제로 약 6~8주 범위다. Phase 1은 Phase 0 Gate 통과 후 약 12~16주 범위이며 팀 규모와 Unreal 통합 상태에 따라 조정한다.


---

# 8. 최종 승인

## 8.1 최종 승인 체크리스트

Schema 2.0 Freeze는 다음 항목을 모두 요구한다.

- [ ] `ai_native_npc_schema_v2_0.yaml`에서 C++/Python/문서 생성
- [ ] `tactical_context [B,128]` output이 Schema·ONNX·ORT·NNE descriptor에 존재하고 3-output parity 통과
- [ ] Enum·Mask·Padding·Hash Golden Vector byte-identical
- [ ] Float Feature parity tolerance 통과
- [ ] `source_moving_probability` 의미·dtype remediation과 migration 완료
- [ ] Pair Feature same-target comparison이 Schema의 `identity_key`로 구조화되고 Revision-only Golden 통과
- [ ] 17 Target Slot과 272 Candidate layout parity
- [ ] Typed Target Runtime Payload 구현
- [ ] Target Slotter Target Recall Gate 통과
- [ ] Goal Registry typed trigger·phase duration·revision contract 생성/검증
- [ ] Goal Arbitration/FSM Phase 0 테스트와 UE generated Phase 표 parity 통과
- [ ] Dataset Record v2의 Switch Cost·feature/content/sample hash Validator 통과
- [ ] OOD/Critical `test_case_catalog_v1.yaml` allowlist와 split 격리 통과
- [ ] Adjusted Score→OOD→Calibration 순서와 Runtime threshold 0.80 parity
- [ ] Calibration global/group accepted count·coverage·one-sided risk CI Gate 통과
- [ ] Model Bundle manifest self-exclusion과 `model_sha256=SHA256(policy.onnx)` 검증
- [ ] `snapshot_revision` stale response와 `SnapshotSuperseded` Runtime 테스트 통과
- [ ] 40ms request deadline의 39/40/41ms·overflow Runtime 테스트 통과
- [ ] Candidate Hash mismatch가 `CandidateHashMismatch`로 거부되고 Neural 실패→latest Utility→Goal fallback 순서 테스트 통과
- [ ] Atomic Commit rollback·lease·urgent cancellation 테스트 통과
- [ ] Hidden Information Leakage Test 통과
- [ ] Appendix E의 실제 Baseline/CI/표본 Gate 통과
- [ ] 보관 validation report의 pending Runtime/Formal Gate가 실제 evidence로 모두 종료

현재 Runtime 계약은 RC5 YAML의 field index·enum·shape다. §10.6 항목은 새 patch의 YAML·generated artifacts·Golden·Decision Contract Hash 발급 후 활성화한다. 완료 전 상태는 Freeze·OOD Runtime 승격 대상에서 제외한다. 변경 이력은 `docs/current/history/ai_native_npc_requirements_history_v0.4.6.md`에 보관한다.
