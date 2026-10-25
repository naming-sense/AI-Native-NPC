# Procedural Generator와 Teacher Pipeline v1 구현 계획

- 문서 버전: **v1.1.0**
- 개정일: 2026-10-25
- 현재 상태: **Greet production candidate 생성·Teacher smoke·비production 검증 완료. 학습용 시나리오 실행·수집 도구는 설계 범위를 문서화했으며 구현 전이다.**
- 적용 계약: Schema `2.0.0-rc6`, Skill Registry `1.1.0`, Goal Registry `1.2.0`
- 구현 루트: `NeuralGame/ML`

## 1. 목적

이 계획은 초기 Silver Dataset을 만드는 경로와 학습용 시나리오 실행·수집 도구의 후속 설계를 정한다.
학습 단위는 NPC가 한 번 판단할 때의 상황과 그 상황에 대한 행동 label이다.

1. Procedural Generator는 contract-valid Decision Snapshot shard를 결정적으로 생성한다.
2. Teacher Pipeline은 Snapshot을 model-visible view로 변환하고 복수 응답 합의로 Silver label을 만든다.
3. Dataset Mapper는 Snapshot과 label을 `anpc_decision_record_v2` Parquet shard로 변환한다.

이 Pipeline은 production `ResolvePolicyReady`를 변경하지 않는다. 예제 Profile과 smoke Dataset은 `integration_fixture`와 `production_candidate` 범위이며 production 학습·promotion authority가 아니다.

대량 데이터 생산은 자동 생성·수집을 중심으로 구성한다. 사람은 대표 사례의 플레이 확인과 정답 검토를 맡는다.
현재 Procedural Generator는 설정된 값으로 Snapshot을 만드는 도구이며 Unreal 장면을 자동 배치·플레이하는 도구와 구분한다.
용어는 [세부 기술 요구사항의 상황·시나리오 정의](technical-requirements.md#collection-terminology)를 따른다.
선택 화면, 직접 플레이, 자동 수집과 역할 분담은 [§12 학습용 시나리오 실행·수집 도구](#scenario-collection-plan)에 정리한다.

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

아래는 기존 Dataset·Capture 기반의 검증 기록이다. §12의 선택 화면·시나리오 실행 도구가 구현됐다는 증거로 사용하지 않는다.

- ML Python suite: **47 passed**
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
- Unreal Resolve capture-only/shadow 구현은 완료했다. 사람은 대표 사례의 Play Capture를 확인하고, 반복 수집은 §12의 자동 실행 도구를 구현한 뒤 수행한다.
- Train·Calibration·General Test·OOD·Critical 최소 분모를 채운다.

### Unreal Resolve capture-only/shadow 계약

첫 모델 전 실제 플레이 분포는 Editor 전용 `-AINativeNPCResolveCaptureOnly` 모드로 수집한다.

- 이 모드는 `WITH_EDITOR`에서만 인식하며 Shipping에서는 활성화할 수 없다.
- `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 그대로 유지한다. Capture-only 활성화는 Production 승인이나 모델 준비로 계산하지 않는다.
- Resolve 진입의 exact authority·Target·Timer·Commit 검사는 Production과 동일하게 유지한다.
- Resolve 선택에서는 Neural evaluator를 반드시 `nullptr`로 두고 같은 Snapshot의 Utility 결과만 실행한다.
- Capture label은 Human Gold나 Teacher Silver가 아닌 `Dagger` weak label이며 `resolve_capture_only_utility_selected` reason을 기록한다.
- 각 Editor process는 새 opaque session ID를 만들고 모든 Host가 `Saved/AINativeNPC/Capture/ResolveShadow/<session-id>/`를 공유한다.
- 각 capture는 process-wide monotonic sequence를 받아 Episode ID와 filename에 함께 넣는다. Host별 `DecisionId`가 같거나 Pawn·PIE world가 다시 만들어져도 경로와 sample identity가 충돌하지 않는다.
- 예상 final·pending·marker 경로가 이미 존재하면 기존 committed Capture를 지우지 않고 새 capture를 fail-closed로 거부한다.
- `.anpccap2`는 Commit 성공 뒤 `.committed` marker와 exact readback이 모두 통과해야 유효하다.
- 사람 Play 비교에는 이 유효 Capture만 사용하며, Utility 선택 자체를 Gold 정답으로 승격하지 않는다.

현재 capture-only의 Utility 선택은 행동 정답의 승인을 뜻하지 않는다.
`Dagger` weak label은 수집·비교 증거로 보존하며, 이 label만으로 production 학습 대상에 넣지 않는다.
Teacher 또는 사람의 별도 판정과 해당 Dataset의 scope·품질 검사를 거쳐야 한다. 기존 raw Capture는 덮어쓰지 않는다.

2026-08-31 구현 검증은 Editor build, `ResolveCaptureOnlyGate`, 기존 `SubjectResolveEntryTransaction` 회귀와 `AINativeNPC.Shipping.GeneralNPC` 21/21, 전체 `AINativeNPC` 167/167을 통과했다. 첫 사람 Play는 committed Phase 3B hearing Capture 세 개를 만들었지만 `ResolveShadow` Capture는 0개였다. 실제 Resolve 진입에서 current visible Entity를 Knowledge Candidate와 Goal Primary Target으로 중복 공급해 `TargetSlotter`가 fail-closed한 것이 원인이며, Phase 3B 세 개는 Resolve 분포 분모에 넣지 않는다. exact matching Knowledge Candidate를 in-place Goal Primary Target으로 승격하도록 수정했고, committed Dagger Resolve Capture·exact readback·Greet를 요구하는 hostile 회귀는 RED에서 GREEN으로 전환됐다. 수정 뒤 `AINativeNPC.Shipping.GeneralNPC` 21/21과 전체 `AINativeNPC` 167/167도 다시 통과했다. 이제 실제 Play를 다시 수집한다. 새 유효 Resolve Capture가 생기기 전에는 실제/Procedural Resolve 비교를 시작하지 않는다.

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

이들은 현재 Snapshot 생성기의 고정 사례다. 플레이 가능한 시나리오 목록이나 수동 Play 횟수를 뜻하지 않는다.
같은 사례의 생성 횟수만 늘리는 것으로 학습 상황의 다양성을 확보했다고 판단하지 않는다.

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

2026-08-23 candidate smoke에서는 unpinned OAuth model alias를 실제 `command` adapter로 연결해 7개 Snapshot × 5회 = 35회 응답을 수집했다. 35개 응답은 모두 strict Schema를 통과했다. Consensus 결과는 Teacher Silver 6개와 Gold review 1개였다. Silver 6개는 procedural heuristic과 일치했다. 사용자는 2026-08-31 low identity confidence anchor를 **신원 확신이 낮으면 인사하지 않음**으로 검토해 Human Gold로 확정했다. 이 결과는 transport, review routing과 1-row human persistence의 실행 증거이며 전체 Gold Validation 또는 production Provider 승인 근거가 아니다.
재현용 unpinned Provider candidate Profile·prompt·Schema·command adapter는 `ML/teacher/candidates/production_resolve_v1_candidate/`에 함께 보존한다. Profile hash는 기존 35회 raw 응답 provenance와 같지만 scope와 model revision이 Production 기준을 충족하지 않아 readiness audit에서 계속 차단한다.

Human Gold 결과는 `abstain=true`, acceptable set empty, parameter label mask all-false, `source_type=gold`, `source_weight=1.0`이다. 승격은 원본 review queue·Snapshot shard·Snapshot manifest의 exact hash와 `(episode_id, decision_id, input_content_hash)`를 묶는다. 원본 review queue나 Teacher 결과를 덮어쓰지 않는다. 승인 record가 source queue와 다르거나 중복·누락·masked label·stale hash·비정규 YAML/JSON이면 산출물을 쓰지 않는다.
Gold 승격과 mapping은 decision·review queue·Snapshot·manifest의 각 파일을 한 번 읽고 같은 immutable byte image를 hash·parse·join에 사용한다. Dataset validator도 한 번 읽은 Parquet bytes를 hash와 Arrow parsing에 함께 사용해 검증 중 path 교체를 허용하지 않는다.

```bash
uv run python -m anpc_ml gold promote \
  --decisions config/gold_resolve_v1_decisions.yaml \
  --review-queue out/production-candidate-v1/teacher-review.jsonl \
  --snapshots out/production-candidate-v1/snapshots.jsonl \
  --snapshot-manifest out/production-candidate-v1/snapshot-manifest.json \
  --output out/production-candidate-v1/gold-annotations.jsonl

uv run python -m anpc_ml gold map \
  --decisions config/gold_resolve_v1_decisions.yaml \
  --review-queue out/production-candidate-v1/teacher-review.jsonl \
  --snapshots out/production-candidate-v1/snapshots.jsonl \
  --snapshot-manifest out/production-candidate-v1/snapshot-manifest.json \
  --annotations out/production-candidate-v1/gold-annotations.jsonl \
  --output out/production-candidate-v1/gold-dataset.parquet \
  --manifest out/production-candidate-v1/gold-dataset-manifest.json
```

Gold 1-row shard는 Snapshot의 `production_candidate` scope와 `production_eligible=false`를 상속한다. Procedural·Teacher Silver·Human Gold candidate shard는 모두 `--require-production`에서 거부한다.

### Production readiness audit

`ML/tools/audit_production_readiness.py`는 Dataset·Teacher Provider·Unreal Capture·Calibration·승인 모델의 준비 상태를 한 JSON으로 검사한다.

- Procedural, Teacher Silver, Human Gold manifest는 모두 validator를 통과해야 한다.
- Teacher Provider Profile은 `scope=production`, exact model revision, 고정 prompt·Schema를 가져야 한다. moving alias나 `integration_fixture` Profile은 차단한다.
- Provider 비교 전 Gold Validation Dataset은 12개 Role×Goal group마다 100개 이상, 총 1,200개 이상이어야 한다.
- Unreal Capture는 `.anpccap2`와 같은 이름의 `.committed` marker가 모두 존재하고 `tools/validate_anpc_capture_v2.py`를 통과한 파일만 센다.
- Calibration/OOD asset과 승인 모델 artifact는 파일 hash와 manifest가 모두 있을 때만 준비로 판정한다.
- 승인 artifact의 filename은 manifest directory 아래의 상대 경로만 허용한다. 같은 artifact bytes를 한 번 읽어 크기와 hash를 검사하며 `..`, absolute path와 symlink escape를 거부한다.
- exact model revision은 `sha256:<64 lowercase hex>` 또는 64자리 digest만 허용한다. 날짜가 붙은 `main`, alias, latest와 unpinned 문자열은 승인하지 않는다.
- Gold 최소 분모와 Role×Goal coverage는 manifest 선언이 아니라 Dataset validator가 실제 Parquet에서 다시 계산한 denominator만 사용한다.
- 하나라도 실패하면 `production_ready=false`와 구체적인 blocker를 반환하며 `Approved`, `ResolvePolicyReady`, `production_eligible`을 바꾸지 않는다.

<a id="scenario-collection-plan"></a>
## 12. 학습용 시나리오 실행·수집 도구 — 구현 전

### 12.1 목적과 현재 범위

사용자는 준비된 시나리오를 골라 직접 플레이하고, 같은 정의를 사용하는 자동 실행으로 다양한 판단 상황을 수집한다.
한 시나리오에는 초기 조건과 사건의 진행 순서가 있고, 한 실행 회차에서 여러 판단 상황이 생길 수 있다.
예를 들어 벽 뒤 발소리 → 상대 등장 → 다시 가려짐을 실행하면 소리만 들림 → 상대 확인 → 대상 상실 상황을 관찰할 수 있다.
각 상황이 자동으로 유효 학습 row가 되는 것은 아니며 Snapshot·label·저장·검증 조건을 각각 만족해야 한다.

현재 구현된 것은 Capture 저장, 고정 Profile 기반 Snapshot 생성, Teacher 라벨링과 Human Gold persistence다.
기본 시나리오 묶음, 조건 변형 생성, 선택 화면과 자동 실행은 구현 전이다.
이 절은 후속 구현의 요구와 검증 범위를 정한다. 새 CLI·Asset·Schema가 이미 존재한다는 의미는 아니다.

사람의 한두 번 Play는 대표 사례의 화면·행동·저장 확인에 사용할 수 있다.
실제 사람 플레이 분포의 대표성, 조건별 coverage와 학습 준비도는 별도의 증거가 필요하다.
`Play 7회`는 학습량 기준이나 의무적인 수동 수집 횟수로 정하지 않는다.
§10의 7개 고정 anchor와 Runtime Catalog의 일곱 검사 group도 수집량 기준과 분리한다.

### 12.2 누가 무엇을 만드는가

| 담당 | 역할 | 승인 경계 |
|---|---|---|
| AI 개발 에이전트 | 기존 문서의 NPC 행동 규칙으로 기본 시나리오·변형 규칙·검증 초안을 만들고 도구를 구현 | 새 게임 규칙이나 Gold 정답을 단독 승인하지 않음 |
| 사용자 / Gameplay/Data owner | 원하는 행동, 대표 사례, 허용 범위·분포와 정답 검토 기준을 확정 | 시나리오 설계 승인과 개별 label·production 승인을 구분 |
| 생성·실행 도구 | 승인된 조건 조합을 생성하고 장면 준비·실행·수집·초기화를 반복 | 범위 밖·미지원 조합은 건너뛴 이유를 기록 |
| Teacher / 사람 검토자 | 저장된 판단 상황의 적절한 행동·선호를 판정 | Teacher는 Silver, 검증된 사람 검토만 Gold로 취급 |

사람에게 모든 변형 사례의 수동 플레이를 요구하지 않는다.
사람 검토는 불확실·불일치·실패 사례와 조건별 대표 표본을 함께 다룬다. 쉬운 사례 또는 실패 사례만으로 전체 품질을 판단하지 않는다.

### 12.3 시나리오 정의와 변형 사례

직접 플레이와 자동 실행은 같은 시나리오 정의를 사용한다.
정의에는 이름·버전, scenario family, 초기 배치, 허용된 변형 범위, 사건 순서·종료 조건과 수집 대상 Goal·phase를 포함한다.
변형 사례는 그 정의 안에서 거리·위치·가림·관계 설정·사건 타이밍 등을 고정한 실행 조건이다.

- 공간 조건: NPC·플레이어의 시작 위치, 거리, 접근 방향, 벽·가림, 이동 경로.
- 게임 조건: 지원되는 초기 관계·성격과 신원 확인에 영향을 주는 관측 조건.
- 사건 조건: 발소리, 접근, 등장, 가려짐, 대상 상실과 회복의 순서·시점.
- 재현 정보: 시나리오·생성기 버전, map/layout, seed, 구체적으로 선택된 조건, 실행 모드와 코드·계약 버전.

초기 후보는 §10의 우호·중립·적대·낮은 신원 확신·가림·경로 불가 축을 재사용한다.
벽 뒤 소리 후 등장, 접근 중 대상 상실 같은 시간 순서 사례를 추가 설계한다.
이 목록은 학습용 장면 설계의 출발점이며 production 분포나 모든 Goal의 실행 지원을 승인하지 않는다.
미지원 조합은 지원 여부와 빠진 Runtime 연결을 표시하고 실행 대상에서 제외한다.

자동 모드는 실제 Pawn·Controller의 Perception → Knowledge → Goal → Candidate → Commit 경로를 사용한다.
플레이어 이동·월드 사건과 적법한 초기 설정을 제어하며, NPC의 선택 결과나 정답을 강제하지 않는다.
Tensor나 Knowledge 결과를 직접 주입하는 검사는 fixture로 분리하고 실제 게임 실행 Capture로 집계하지 않는다.
숨은 월드 정답, 미래 사건과 시나리오의 기대 결과는 모델 입력과 Teacher 입력에 넣지 않는다.

### 12.4 선택 화면과 실행 수명

목표 화면은 다음 동작을 제공한다. 현재 사용할 수 있는 화면이나 명령은 아니다.

- **시나리오 선택:** 설명, 초기 조건, 변형 범위, 지원 상태를 표시한다.
- **직접 플레이:** 선택한 조건으로 장면을 준비하고 사용자 입력으로 플레이한다.
- **자동 수집:** 승인된 조건·seed 목록에 따라 이동과 사건 발생을 자동 실행한다.
- **같은 조건 재실행:** 저장된 시나리오 버전·조건·seed로 새 실행 회차를 시작한다.
- **중단·결과 확인:** 현재 상태, 조건별 유효·실패·중복 수와 제외 이유를 보여 준다.

실행 순서는 조건 검증 → 장면 준비 → 감지·이동 준비 확인 → 사건 실행 → 판단·결과 저장 → 검증 → 초기화다.
최대 회차, 회차 시간 제한과 저장 용량 한도를 실행 전에 고정하고, 준비 실패·timeout·사용자 중단은 사유를 보존한다.
초기화는 Pawn·Knowledge·Goal·Timer·관계 변경·예약 등 이전 회차의 영향을 제거한다.
기존 유효 Capture와 process-wide monotonic sequence는 초기화하거나 덮어쓰지 않는다.
초기화 실패 시 다음 회차를 시작하지 않는다. 병렬 실행은 상태·저장 경로 격리를 별도 검증하기 전까지 범위에서 제외한다.

같은 seed는 동일 조건 재구성을 위한 정보다. 사람 입력과 실제 엔진 타이밍까지 byte-identical하다고 보장하지 않는다.
재현 확인에는 실제 입력·사건 시점·판단 결과 기록과 비교 기준이 추가로 필요하다.
§7의 byte-identical 조건은 기존 offline Snapshot 생성기의 검증 범위로 유지한다.

### 12.5 상황 수집과 정답 판정

수집 출처와 라벨 출처를 별도로 추적한다.

- 수집 출처: 사람 플레이, 자동 게임 실행, offline Procedural, test fixture를 구분한다.
- 라벨 출처: 승인된 procedural 규칙, Teacher Silver, Human Gold, 별도 요건을 충족한 DAgger 개입을 구분한다.
- 자동 실행을 사람 플레이 분포로 집계하지 않는다. 시나리오 승인만으로 정답 승인이 생기지 않는다.
- Utility 선택을 정답으로 복사하지 않는다. 현재 `Dagger` weak label은 기존 수집 출처와 reason을 보존한다.
- Teacher·사람은 동일한 판단 Snapshot에 별도 annotation을 연결한다. 기존 Capture와 원본 판정을 덮어쓰지 않는다.
- 수집 정보를 담을 추가 field/sidecar와 mapper는 구현 전에 Schema·문서·하네스로 확정한다. 현재 `source_type` enum을 임의로 확장하지 않는다.

현재 committed Capture는 `.anpccap2`, 대응 `.committed`와 validator 통과가 필요하다.
유효 학습 row는 여기에 대상 정책·label·Dataset 변환·scope 검증까지 필요하다.
Capture 저장 수, 판단 상황 수, 실행 회차 수와 유효 학습 row 수를 각각 집계한다.

성공한 인사뿐 아니라 인사하지 않음, 대상 상실, 판단 실패와 실행되지 않은 상태도 관찰 대상으로 설계한다.
Snapshot이 없는 실패는 원인·단계만 진단 기록에 남긴다. Snapshot이 있는 미실행 상태도 committed 자료와 분리한다.
실패·미확정 기록을 committed Capture로 위장하지 않는다.
이 진단 기록은 현재 readiness audit의 유효 Capture 분모와 학습 Dataset에서 제외한다.
미실행 상태를 학습에 넣는 별도 관측 포맷·label·mapper·validator 계약은 구현 전 확정 항목으로 남긴다.

### 12.6 다양성·분할·수집 완료 기준

반복 횟수보다 조건별 coverage, 고유 입력, 중복·근접 중복과 제외 이유를 관리한다.
같은 입력의 ID·seed만 바뀐 자료를 새로운 학습 상황으로 세지 않는다.
허용 조합·비율·수집 예산과 중단 기준은 Gameplay/Data owner가 승인한 Profile에 고정한다.

`scenario_family_id`와 관련 template/layout/사건 순서 family 단위로 분리한다.
같은 family의 seed·거리 변형을 Train·Validation·Calibration·Test·OOD·Critical에 나눠 넣지 않는다.
숨은 정보 유입, split 간 exact·근접 중복과 source 편향을 검사한다.
자동 실행과 합성 자료는 사람 Play와 분리해 조건·Feature·Candidate 분포를 비교하며, 작은 사람 표본의 한계를 보고한다.
현재 Gold 최소 수량과 Teacher·평가·품질 기준은 유지한다. 작은 수집 smoke가 이 기준을 대신하지 않는다.

### 12.7 구현 순서와 확인할 증거

1. 이 절의 설계를 바탕으로 시나리오 정의·출처 metadata·진단 기록·허용 조합과 승인 기준을 문서·하네스에 확정한다.
2. 잘못된 조건, 미지원 조합, 상태 누수, 저장 충돌, 실패 기록의 부당 승격과 split 누수 검사를 먼저 실패시킨다.
3. 단일 시나리오의 장면 준비·직접 플레이·초기화를 구현하고 대표 사례를 사람이 확인한다.
4. 같은 정의를 사용하는 자동 실행을 구현하고 실제 Runtime 경로·시간 제한·중단·초기화를 검증한다.
5. 기록을 다시 읽어 committed·진단 자료의 구분, Snapshot 결속, annotation 연결과 Dataset 검사를 확인한다.
6. 조건별 coverage·고유 입력·중복·제외 보고서를 만들고 수집 규모를 확장한다.

문서 검사 통과와 실제 수집 도구의 완료를 구분한다.
도구 완료에는 위 검사의 실행 증거, 실제 저장 파일의 재검증, 대표 사람 Play와 독립 검토가 필요하다.
이 작업만으로 모델 학습·배포를 승인하지 않으며 `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다.
