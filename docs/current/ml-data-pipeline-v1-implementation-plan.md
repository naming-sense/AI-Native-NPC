# Procedural Generator와 Teacher Pipeline v1 구현 계획

- 문서 버전: **v1.0.1**
- 개정일: 2026-08-23
- 현재 상태: **Greet production candidate 생성·Teacher smoke·비production 검증 완료**
- 적용 계약: Schema `2.0.0-rc6`, Skill Registry `1.1.0`, Goal Registry `1.2.0`
- 구현 루트: `NeuralGame/ML`

## 1. 목적

이 계획은 Unreal Resolve Capture가 열리기 전에 초기 Silver Dataset을 만드는 두 Pipeline을 정한다.

1. Procedural Generator는 contract-valid Decision Snapshot shard를 결정적으로 생성한다.
2. Teacher Pipeline은 Snapshot을 model-visible view로 변환하고 복수 응답 합의로 Silver label을 만든다.
3. Dataset Mapper는 Snapshot과 label을 `anpc_decision_record_v2` Parquet shard로 변환한다.

이 Pipeline은 production `ResolvePolicyReady`를 변경하지 않는다. 예제 Profile과 smoke Dataset은 `integration_fixture`와 `production_candidate` 범위이며 production 학습·promotion authority가 아니다.

## 2. 입력과 결과

### 2.1 Procedural Generator 입력

`procedural_profile_v1.yaml`은 다음 값을 소유한다.

- `profile_version`, `scope`, `owner`
- Schema·Skill·Goal source SHA-256
- base seed와 scenario template 목록
- group dimension
- Target·Event·Candidate 구성
- generated enum 이름을 사용하는 raw feature override
- acceptable Candidate, preference와 parameter label

Feature override는 generated normalizer를 통과한다. Tensor index를 숫자로 직접 작성하지 않는다.

### 2.2 Decision Snapshot shard

Snapshot shard는 UTF-8 JSON Lines와 manifest pair다. 각 row는 한 번의 immutable Decision Snapshot이다.

필수 값:

- exact 10 Tensor canonical byte와 dtype·shape
- `candidate_set_canonical_bytes`, `candidate_set_hash`
- `switch_cost_terms`, `captured_switch_cost`
- contract hash와 `input_content_hash`
- episode·decision·group·provenance
- procedural label block

Binary field는 base64로 저장한다. JSON object는 key 오름차순·compact UTF-8로 기록한다. Manifest는 shard byte 크기·row 수·SHA-256·profile hash·source/group 분모를 고정한다.

Snapshot Validator는 Candidate canonical bytes를 구조적으로 decode해 magic·version·Schema hash·17 Target Handle·Target mask·272 Candidate mask를 Tensor와 다시 비교한다. Handle 정수 field는 bool·float coercion을 금지하며, NoTarget·masked Target handle과 masked Tensor row는 canonical zero여야 한다.

### 2.3 Teacher 결과

Teacher request는 Tensor에서 복원한 다음 model-visible view만 포함한다.

- `global`
- `targets`
- `events`
- `candidates`
- `current_action`
- contract·content hash

Runtime handle, Actor 이름, absolute world position, future event와 hidden Ground Truth는 제외한다.

Provider는 Profile로 선택한다.

- `command`: request JSON을 stdin으로 전달하고 response JSON을 stdout으로 받는다.
- `replay_fixture`: 테스트용 고정 response를 읽는다. production scope에서 사용할 수 없다.

각 Snapshot은 정확히 5개 provider call provenance를 수집한다. 최소 3개 valid response, majority consensus, pairwise Jaccard와 `label_confidence`를 적용한다. valid response가 3개 미만이거나 confidence 0.60 미만, hard conflict, preference cycle 또는 합의된 ambiguous이면 training annotation에서 제외하고 Gold review queue로 보낸다.

Request Validator는 generated enum의 global·target·event·candidate feature 이름과 Skill·Target Kind·Event Type을 exact allowlist로 검사한다. Dataset Mapper는 Teacher Profile을 다시 로드하고 Snapshot에서 request를 재생성한 뒤 raw provider payload 5개의 path·hash·response를 재검증하고 consensus 결과가 annotation body와 byte-equivalent한 경우에만 mapping한다.

Teacher는 parameter label을 만들지 않는다. Teacher mapper는 `parameter_target_norm=+0.0`, `parameter_label_mask=false`를 사용한다.

### 2.4 Dataset Record v2

Mapper는 Snapshot과 procedural 또는 Teacher annotation을 결합해 Zstandard Parquet를 작성한다.

- Tensor는 Arrow fixed-size list다.
- 10개 Tensor, mask와 Switch Cost를 다시 검증한다.
- `input_content_hash`, `label_block_hash`, `sample_id`를 다시 계산한다.
- `source_type`, `source_weight`, code/contract provenance를 기록한다.
- Snapshot·annotation join key는 `source_snapshot_shard_sha256 + episode_id + decision_id + input_content_hash`다.
- fixture source가 포함된 manifest는 `scope=integration_fixture`를 유지한다.
- `source_weight`는 `silver=0.25`, `gold=1.0`, `dagger=1.0`과 exact 일치해야 한다.

## 3. Procedural Resolve integration Profile

Repository에는 작은 `integration_fixture` Profile과 별도 `production_candidate` Profile을 둔다. 이 절은 integration fixture의 고정 범위를 설명한다.

- Goal: `InvestigateDisturbance`
- Phase: `Resolve`
- Role: `Guard`
- Target slot 0: `Entity`
- NoTarget slot 16: 항상 valid
- valid Candidate: `Greet(Entity)` index `170` 또는 target-loss case의 빈 mask
- scenario family: friendly-visible, hostile-visible, invalid-target
- parameter label: friendly-visible procedural row에서만 Greet active slot인 duration·intensity

이 값은 Pipeline 검증 fixture다. production 범위, 분포, 비율과 label 공식을 승인하지 않는다.

## 4. 실패 처리

다음 구조 오류에서는 shard나 annotation을 publish하지 않는다.

- contract hash·version 불일치
- unknown feature·enum·Profile field
- non-finite·negative-zero·범위 밖 Tensor
- invalid NoTarget slot 또는 Candidate layout
- masked acceptable/preference index
- request/response content hash 불일치
- manifest에 없는 shard 또는 byte hash 불일치
- production scope에서 `replay_fixture` 사용

출력은 temporary file에 작성하고 validation을 통과한 뒤 atomic replace한다.
valid Teacher response가 3개 미만인 개별 sample은 training annotation에서 제외하고 Gold review queue로 보낸다.

## 5. 구현 파일

```text
NeuralGame/ML/
  pyproject.toml
  uv.lock
  contracts/
    ai_native_npc_contracts_generated.py
    consumer-provenance-lock.json
  config/
    procedural_resolve_integration_v1.yaml
    teacher_profile_integration_v1.yaml
  teacher/schemas/
    teacher_request_v1.schema.json
    teacher_response_v1.schema.json
  anpc_ml/
    canonical.py
    contracts.py
    snapshot.py
    procedural.py
    dataset.py
    teacher.py
    cli.py
    __main__.py
  tests/
    test_canonical.py
    test_contract_provenance.py
    test_procedural.py
    test_teacher.py
    test_dataset.py
    test_cli_smoke.py
```

## 6. 구현 순서

1. Profile·request·response Schema와 hostile fixture test를 먼저 작성한다.
2. 테스트가 missing implementation으로 실패하는지 확인한다.
3. contract loader와 canonical encoding을 구현한다.
4. Procedural Generator를 구현하고 deterministic double-run을 검증한다.
5. Teacher request·strict parse·consensus·Gold queue를 구현한다.
6. Dataset mapper와 Zstandard Parquet writer를 구현한다.
7. 실제 CLI로 fixture Snapshot→Teacher annotation→Parquet를 생성한다.
8. focused test, 전체 Contract test와 `git diff --check`를 실행한다.

## 7. 완료 조건

- 같은 Profile·seed의 Snapshot shard가 두 번 실행해 byte-identical하다.
- Greet candidate index, 10 Tensor shape·dtype·canonical byte와 candidate hash가 generated contract와 일치한다.
- hidden field, masked index, stale hash, low consensus와 preference cycle hostile test가 실패한다.
- 5개 응답 consensus와 Gold review queue가 문서 규칙과 일치한다.
- Mapper 출력은 Parquet Zstandard이고 Arrow fixed-size Tensor schema를 사용한다.
- Parquet row를 다시 읽어 Snapshot hash·label hash·sample identity를 검증한다.
- integration fixture manifest는 production으로 승격할 수 없다.
- 실제 CLI smoke 산출물이 생성되고 validator가 통과한다.

## 8. 현재 검증 상태

- ML Python suite: **33 passed**
- Contract repository: **89 passed, 133 subtests passed**
- generated contract·Goal·Skill check: **PASS**
- 실제 CLI smoke:
  - Procedural Snapshot 4개 생성
  - Teacher 4개 처리, training 4개, review 0개
  - Teacher/Procedural Parquet 각각 4 rows 작성 및 재검증
  - `--require-production`이 integration fixture를 정확히 거부
  - Procedural 7 rows와 Teacher Silver 6 rows의 두 `production_candidate` shard를 Production Dataset으로 거부

2026-08-23 독립 hostile review에서 Candidate canonical/Tensor 분리, Handle·padding coercion, Teacher annotation raw provenance 재검증, exact 5-call, request allowlist와 source-weight binding finding이 재현됐다. 해당 finding은 hostile test로 고정한 뒤 회수했으며, 최신 source 독립 재검토에서 추가 차단 문제가 없음을 확인했다.

## 9. 남는 production 작업

- Gameplay/Data owner가 production scenario family, 값 범위, 분포와 procedural parameter label 공식을 승인한다.
- production Teacher provider·model revision·prompt를 고정한다.
- Gold validation manifest로 Teacher Profile을 승인한다.
- Unreal Resolve capture-only/shadow 계약 또는 첫 모델 이후 rollout Capture를 추가한다.
- Train·Calibration·General Test·OOD·Critical 최소 분모를 채운다.

## 10. Greet Production Profile 후보

첫 Production Profile 후보의 Release 범위는 current Test Taxonomy와 Case Catalog가 고정한 `GuardPhase0/InvestigateDisturbance/Resolve`, production action은 `Greet(Entity)`다.

Profile 승인 전 검토 산출물의 scope는 `production_candidate`로 표시한다. `production_candidate`는 값 범위·분포·parameter label 공식을 검토하기 위한 후보이며 production 학습 authority가 아니다. Generator와 Dataset validator는 이 scope를 실행하되 `production_eligible=false`로 유지하고 `--require-production`에서 거부한다.

Case Catalog의 일곱 group은 Runtime 검증의 최소 축이다.

- `greet_selected`
- `masked_or_nonfinite_output`
- `wrong_descriptor_or_artifact_identity`
- `neural_failure_or_deadline`
- `target_loss_recoverable`
- `target_loss_unrecoverable`
- `duplicate_or_stale_effect`

이 group을 학습 분포로 그대로 복사하지 않는다. Production Profile은 Gameplay/Data owner가 다음 값을 별도로 승인한 뒤 새 version으로 고정한다.

- friendly·neutral·hostile 관계 구간과 비율
- Target visible·occluded·lost·invalid 구간과 비율
- 거리, belief age·confidence, LOS와 path 상태 범위
- Personality·Relationship 조합과 hold-out family
- 현재 Skill 유지·Greet 전환의 Switch Cost 구성
- `Greet` duration·intensity의 procedural/human label 공식

사용자가 권장 기본값으로 계속 진행하도록 승인했으므로 v1 후보는 다음 규칙을 사용한다. 이 규칙의 label은 heuristic Silver이며 Gold 또는 production authority가 아니다.

- Greet 허용: Entity Target과 Greet Candidate가 valid이고, `visible_now = 1`, `line_of_sight_belief ≥ 0.80`, `identity_confidence ≥ 0.80`, `path_reachable_belief ≥ 0.50`, `hostility ≤ 0.35`를 모두 만족한다.
- 그 밖의 anchor는 abstain으로 남기며, Target·Candidate가 무효이면 Candidate mask를 비운다.
- duration = clamp(1.0, 5.0, 1.0 + 0.60 × affinity + 0.40 × sociability - 0.30 × hostility)
- intensity = clamp(0.0, 1.0, 0.20 + 0.35 × sociability + 0.30 × affinity + 0.15 × trust - 0.40 × hostility)

실행 가능한 `production_candidate` Profile은 7개 anchor를 고정한다.

1. friendly close visible
2. friendly far visible
3. neutral trusted visible
4. friendly low identity confidence
5. hostile visible
6. friendly recently occluded
7. friendly visible but path unreachable

Target-invalid는 integration hostile fixture와 Runtime test case로 계속 검증한다. Candidate Profile에서는 model-visible 관계·거리·인지·경로 경계의 비교에 집중한다.

Production Profile로 만든 Snapshot은 첫 Unreal Capture 분모와 feature 구간·Candidate mask·abstain 비율을 비교한다. 비교 전 합성 Dataset만으로 production 범위를 열지 않는다.

## 11. Teacher Provider 선정과 Profile 승인

Production Teacher Profile ID는 `teacher_silver_v1.0.0`이며 provider type은 `command`를 사용한다. `replay_fixture`는 integration 전용이다.

각 Provider 후보는 같은 고정 Gold Validation Dataset으로 비교한다. Profile은 provider의 exact model identifier와 revision, prompt·Schema, decoding, prompt variant, consensus version과 reason-tag allowlist를 함께 고정한다. moving alias나 revision을 증명할 수 없는 연결은 smoke 후보로만 기록하고 production Profile로 승인하지 않는다.

승인 기준은 다음과 같다.

- 12개 Role×Goal group마다 Gold sample 100개 이상
- strict response valid rate ≥95%
- Any-Acceptable Recall ≥95%
- macro Role×Goal acceptable-set Jaccard ≥0.80
- hard-invalid candidate 선택 0건

한 기준이라도 실패하면 해당 Provider/Profile 조합을 차단한다. 둘 이상이 모두 통과하면 worst Role×Goal 성능, 응답 형식 안정성, 처리 시간과 비용 순으로 선택한다. Prompt, model revision, decoding 또는 consensus를 바꾸면 새 Profile version으로 전체 Gold Validation을 다시 실행한다.

2026-08-23 candidate smoke에서는 unpinned OAuth model alias를 실제 `command` adapter로 연결해 7개 Snapshot × 5회 = 35회 응답을 수집했다. 35개 응답은 모두 strict Schema를 통과했다. Consensus 결과는 Teacher Silver 6개와 Gold review 1개였다. Silver 6개는 procedural heuristic과 일치했고, low identity confidence anchor는 응답 간 합의가 약해 review로 분리됐다. 이 결과는 transport와 review routing의 실행 증거이며 Gold Validation 또는 production Provider 승인 근거가 아니다.
