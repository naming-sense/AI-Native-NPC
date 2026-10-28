# Runtime 수집 자료의 ML 가져오기 V1 계약

**상태:** 구현 전 계약. 이 개정은 Schema와 실패 하네스의 입력을 확정한다. Runtime/ML 기능 구현, 실제 수집, Teacher 실행, Human 승인 또는 학습 준비 완료를 뜻하지 않는다. 기존 Dataset v2 레코드·manifest exact-field 집합과 `silver/0.25`, `gold/1.0`, `dagger/1.0` 가중치를 유지한다. 모든 수집 산출물은 `production_eligible=false`다. 범위에는 새 trainer가 없다(`no new trainer`).

## 1. 목적과 현재 코드의 경계

실제 Capture의 입력·Utility label·생산 이력을 보존하는 Snapshot을 만든다. 출처 검증, label 권한 검증, 학습/Production 자격은 별도 판단이다. 현재 `contract_metadata()`는 Runtime build 필드까지 Python generator digest와 비교한다. importer는 원본 build 값을 Python digest로 바꾸어 통과시키지 않는다.

이 문서가 참조하는 현재 구현은 다음과 같다. 아래의 새 authority/context/result는 **구현 목표**이며 기존 함수가 이미 제공하는 보증으로 읽지 않는다.

- 문서 저장소 `tools/validate_anpc_capture_v2.py`: immutable-byte decoder `decode_committed_capture_bytes`, payload 반환부 413–440행, unsigned marker 검증부 449–477행.
- 문서 저장소 `tools/validate_scenario_collection.py`: `load_catalog`, `catalog_digest`, `validate_index`; collection Schema의 기존 exact-field 집합.
- ML root `/mnt/d/Codex-cli/NeuralProject/NeuralGame/ML`의 `anpc_ml/snapshot.py`: required fields, Tensor/handle/input 검증; `contracts.py`: generated binding과 semantic metadata; `canonical.py`: Tensor/JSON/identity encoding.
- 같은 ML root의 `teacher.py`: Profile, request projection, raw attempts와 consensus; `gold.py`: decision/queue/Snapshot join; `dataset.py`: `_base_record`, `_annotation_provenance`, public final validator.
- Runtime project `NeuralGame/Source/NeuralGame/AINativeNPC`: `Dataset/DecisionRecordV2.{h,cpp}`의 wire 순서, `Execution/AINativeNPCGoalHostComponent.cpp`의 producer, `Policy/UtilitySelection.{h,cpp}`의 compiled Utility profile.

기존 Gold의 canonical JSON·hash·join 검사는 Teacher 발행자나 reviewer 신원을 인증하지 않는다. 기존 public Dataset validator가 모든 hash를 다시 쓴 forged Gold를 구조적으로 허용할 수 있다는 재현을 인정한다. 이 사실을 Production 승인 우회로 확대하지 않는다.

<!-- R1:issuance -->
## 2. 완료된 수집 묶음의 발행 권한

### 2.1 외부 completion pin

최소 발행 anchor는 **최종 collection index exact bytes의 외부 고정 digest**인 `expected_collection_index_sha256`다. trusted collector/controller가 실제 수집한 immutable Capture/marker를 읽어 검증하고 session·episode 이력을 닫은 후 최종 index를 배타적으로 발행한다(`publish index last`). 최종 파일의 exact readback까지 성공한 뒤에만 owner-controlled storage에 완료 pin을 예치한다. 실행 중 index, 임시 파일, 미완료 이력에는 pin을 발행하지 않는다.

기존 collection index top-level `format, version, session_id, entries`는 보존한다. **base index has no session/episode descriptors**: index digest 하나가 그 밖의 session/episode 파일까지 직접 hash한다고 주장하지 않는다. 따라서 동일한 owner-controlled 완료 항목에 다음 `completion_closure`를 함께 불변 보관한다. 이 항목은 base collection-index Schema **밖**의 authority다.

- `collection_index={path,size_bytes,sha256}`: 최종 index. `sha256 == expected_collection_index_sha256`.
- `session`: 최종 session descriptor.
- `ordered_episodes`: 실제 실행 순서의 모든 최종 episode descriptor. index에 Capture가 없는 실패·취소 회차도 포함한다.
- `replay_predecessors`: 필요한 이전 session의 완료 pin 식별자와 해당 원본 session/episode descriptor. 외부 predecessor도 그 session의 독립 pin으로 검증한다. forward/cyclic 링크는 거부한다.
- `catalog`: 보관한 catalog descriptor와 별도로 고정한 canonical `catalog_sha256`.
- `collection_execution_profile`: descriptor와 별도로 고정한 `collection_execution_profile_sha256`.
- `runtime_build_evidence`: descriptor와 별도로 고정한 `runtime_build_evidence_sha256`.
- `session_start_evidence`: §3의 실제 시작/loaded-module 검증 기록 descriptor.

각 descriptor는 `{path,size_bytes,sha256}`이며 `path`는 collection root에 대한 POSIX 상대 경로다. build evidence 내부의 다른 path base는 §3에서만 해석한다. 최종 index의 **모든** Capture/marker 및 diagnostic artifact descriptor를 검증한다. closure가 아닌 제출 파일을 보충 출처로 탐색하지 않는다. 완료 storage는 같은 authority namespace의 **same index digest**에 서로 다른 closure를 등록하는 일을 거부한다. 최소 pin과 이 불변 closure를 함께 가져와야 완전한 발행 판단이 가능하다.

real Runtime origin에는 session/episode/entry의 `input_source`가 실제 수집 방식에 맞는 `automated_runtime` 또는 `human_play`여야 한다. `offline_procedural`과 `test_fixture`는 기존 collection 구조 하네스에서 표현할 수 있지만 real Runtime origin 권한을 발행하지 않는다. 격리 fixture namespace의 완료 pin도 실제 authority의 pin으로 교환할 수 없다.

trusted caller는 제출 묶음과 독립적인 owner storage에서 `TrustedCollectionCompletionPin`을 획득한다(`independent_out_of_band`). target factory 입력은 `authorize_runtime_import(root, *, completion_pin, parser_pin, importer_pin)`이다. `completion_pin`은 위 외부 digest/closure와 owner storage 항목 identity를 담은 trusted 호출 입력이며, bundle JSON로 역직렬화하여 권한 객체를 만들지 않는다. catalog/profile/build pins도 이 owner 항목에서 별도로 획득한다. parser/importer pin은 운영자가 허용한 도구 source/version이다.

금지된 expected-value 취득원은 **submitted index, metadata, uploaded bundle, self-declared expected fields**다. bundle 내부에 pin을 복사해 두는 것은 진단용일 뿐이다. importer가 방금 읽은 index의 digest를 계산해 그것을 expected pin으로 다시 넣는 경로는 거부한다. `unknown root/bundle`은 이 독립 anchor 없이는 실패한다. 외부 보관 묶음의 복사본은 독립 pin과 전체 closure가 일치할 때만 허용된다. 공개된 build/profile 이름·digest를 복사하고 `rehashed Capture/marker/index`를 제출해도 원래 pin과 맞지 않아 실패한다.

### 2.2 신뢰 전제와 한계

신뢰 주체는 trusted local operator, 지정된 build producer, trusted collector/controller, owner storage 관리자다. producer는 제출 파일을 사후 수집물처럼 등록하지 않고 자신이 관찰한 실행에서만 완료 항목을 발행한다. storage는 작성 권한과 변경 이력을 관리하고 발행 후 immutable custody를 유지한다. private/stable root는 경로 경쟁을 막는 전제이며 그 자체가 파일 발행자의 증명은 아니다.

Capture checksum과 unsigned marker는 bytes의 결속만 확인한다. 이 설계는 `no signing service`인 로컬 신뢰 방식이며 malicious trusted operator/toolchain, 소유자 storage 장악, 신뢰 프로세스 내 임의 코드 실행을 암호학적으로 해결하지 않는다. issuer가 실제 실행과 pin을 정직하게 연결한다는 전제를 문서·결과에 유지한다. 임의의 외부 파일을 인증된 Runtime 발행물로 받아들이는 범용 원격 attestation을 약속하지 않는다.

모든 index/closure 입력은 unknown field·중복 JSON key·비유한 값·유형 coercion을 거부한다. lexical `..`·absolute·drive·backslash·symlink escape를 거부하고 ancestor directory 치환을 막는다. source artifact는 한 번 읽은 immutable bytes로 크기·hash·parse·join·decode를 수행한다. hash 후 재개방, validate 후 rehash, ABA 경로 치환은 허용하지 않는다. 외부 pin이 bytes의 발행을, 이 규칙이 검증 중 같은 bytes의 사용을 각각 보장한다.

<!-- P1:digests-build -->
## 3. Profile 구분과 수집 전용 build 증거

### 3.1 digest 이름과 byte grammar

SHA-256는 lowercase hex다. 아래 catalog 예외 외에는 **exact file bytes**를 hash한다. 새 JSON artifact는 `sorted_json_bytes(value) + b"\n"`(UTF-8, key sort, compact separators, `ensure_ascii=False`, `allow_nan=False`)로 한 번 직렬화하고 그 파일 bytes를 pin한다. 기존 YAML Profile은 파싱 후 재직렬화하지 않는다. 배열의 의미 순서는 보존하며 inventory만 `(base,path)`의 UTF-8 byte 순으로 정렬하고 중복을 거부한다.

| 이름 | 의미와 고정 규칙 |
|---|---|
| `catalog_sha256` | `load_catalog`의 strict parse/validation 뒤 `catalog_digest`와 동일한 canonical object bytes를 hash. 아래 식은 without trailing LF. 저장 catalog descriptor의 raw-file hash와 구분한다. |
| `collection_execution_profile_sha256` | 수집 실행 설정 JSON exact bytes. session의 기존 `profile_sha256` 및 이 importer가 만드는 Snapshot manifest의 `profile_sha256`가 이 값을 가리킨다. ML procedural/Teacher Profile과 혼용하지 않는다. |
| `utility_profile_source_sha256` | compiled Utility의 `utility-profile-source-v1` source descriptor JSON exact bytes. `BuildGuardPhase0UtilityProfile`의 이름이나 ProfileId 문자열 자체의 hash가 아니다. |
| `teacher_profile_sha256` | `load_teacher_profile`이 읽은 원본 YAML exact bytes. 허용 권한은 별도 `permitted_teacher_profile_sha256` pin으로 결정한다. |
| `runtime_build_evidence_sha256` | 아래 post-build evidence JSON exact bytes. session의 기존 `runtime_build_sha256` 및 수집 Capture `GeneratorOrRuntimeBuildSha256`에 같은 값을 결속한다. |

catalog 식은 정확히 다음과 같다.

```text
sha256(json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
```

collection execution profile의 최소 closed object는 `format="anpc_collection_execution_profile_v1"`, `version=1`, `catalog_sha256`, `observation_mapping_version`, `input_source`, `execution_mode`, `controller`, `limits`, `utility_profile_source_sha256`다. mode/source/controller/limits는 기존 session Schema의 동일 type·범위를 따른다. 실제 선택된 scenario/version/conditions/seeds는 pin된 episode와 catalog에서 확정한다. 새 placement 범위나 관측 feature를 이 profile로 발명하지 않는다.

`utility-profile-source-v1` object는 `format`, `profile_id`, `entries`로 닫는다. `profile_id`는 generated `AINativeNPC::GoalGameplayV1::UtilityProfileId`의 exact text다. `entries`는 project root 기준 `Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.cpp`, `UtilitySelection.h`(동일 디렉터리), `Source/NeuralGame/AINativeNPC/Generated/AINativeNPCGoalGameplaySemantics.generated.h`, `AINativeNPCContracts.generated.h`(동일 Generated 디렉터리)의 `{base,path,size_bytes,sha256}` 목록이다. 이 digest는 해당 source 선택을 식별하며 실행 binary와의 대응은 다음 build evidence가 담당한다. 새로운 Utility 직렬화/평가 알고리즘을 정의하지 않는다.

### 3.2 bounded build evidence

기존 일반 플레이의 `ComputeRuntimeBuildHash()`는 보존한다. 그 값은 build-version 문자열의 hash이며 실제 binary 증명으로 승격하지 않는다. 수집 모드만 외부 post-build evidence digest를 사용한다. binary에 자기 digest를 삽입하는 순환은 만들지 않는다.

build producer가 작성할 evidence의 closed top-level 필드는 `format="anpc_collection_build_evidence_v1"`, `version=1`, `project_file`, `target`, `platform`, `configuration`, `source_inventory_before`, `source_inventory_after`, `build_mode`, `build_argv`, `build_working_directory`, `exit_code`, `build_log`, `build_receipt`, `module_artifacts`, `engine_toolchain_identity`, `collection_schema_sha256`, `catalog_sha256`, `collection_execution_profile_sha256`, `utility_profile_source_sha256`, `observation_mapping_version`다. 구체적인 프로젝트 target/platform/configuration 값은 신뢰한 build invocation의 값을 기록한다. 성공하지 않은 명령을 예시 성공으로 채우지 않는다.

- `project_root`는 `NeuralGame.uproject`가 있는 실제 project 디렉터리, `authority_root`는 `AI-Native-NPC` 문서/계약 저장소, `evidence_root`는 collector가 만든 이번 evidence 디렉터리다. 이 세 base의 실제 절대 위치는 trusted caller가 설정한다. bundle이 경로 base를 바꾸지 못한다.
- source inventory entry는 `{base,path,size_bytes,sha256}`다. 최소 closure는 project의 `NeuralGame.uproject`, `Source/` 전체(모든 project module·Target.cs·Build.cs·generated header 포함), `Config/` 전체, 활성 project-local plugin의 descriptor/source/config, 실제 선택 map 및 그 project content dependency closure, authority의 collection/Capture Schema·Skill/Goal Registry·catalog·관측 mapping 계약·generated lock이다. 활성 plugin과 content dependency 목록은 build receipt/선택 map dependency 기록으로 완전성을 검사한다. 불명확하거나 누락된 dependency는 실패한다. engine 전체 source를 inventory에 넣는 약속은 하지 않는다.
- `source_inventory_before`와 `source_inventory_after`는 같은 목록·크기·digest여야 한다. 새 파일·삭제·누락도 차이로 센다. project-local 생성 header가 빌드 중 바뀌었다면 안정화된 source로 다시 build evidence를 만든다. UHT가 Intermediate에 생성한 결과는 build receipt/log의 산출물로 식별한다.
- `build_mode="clean_or_forced_project_modules"`만 허용한다. `build_argv`는 shell string이 아닌 실행 인수 배열, `build_working_directory`는 `{base,path}`이며 `exit_code=0`이어야 한다. `build_log`와 `build_receipt`는 evidence-root descriptors다. clean 또는 forced rebuild가 closure에 속한 project module의 모든 translation unit을 실제 다시 compile/link했음을 log/receipt로 확인한다. `incremental_success_only`는 실패한다. 단순 build 성공과 별도 source/DLL hash의 나열만으로 source-to-binary 대응을 주장하지 않는다.
- `module_artifacts`는 receipt가 선택한 모든 로드 대상 project module의 `{module_name,base,path,size_bytes,sha256}` 목록이다. base는 project_root이며 실제 loader/receipt 경로를 사용한다. wildcard로 가장 최근 DLL을 고르거나 stale/hot-reload 대체 DLL을 받아들이지 않는다. launch executable이 engine 제공이면 그 exact 설치 경로·크기·digest는 `engine_toolchain_identity`에 기록한다.
- `engine_toolchain_identity`는 `engine_version, engine_executable, compiler, linker, build_tool`의 closed object다. `engine_version`은 설치 engine의 exact build/version text다. `engine_executable`은 descriptor 하나이고 `compiler`, `linker`, `build_tool`은 각각 실제 호출한 실행 파일들의 비어 있지 않은 descriptor 배열이다. 각 descriptor는 `installed_path, size_bytes, sha256, version`을 가진다. installed_path는 trusted operator가 관찰한 실제 설치 경로이며 bundle artifact resolver 경로로 사용하지 않는다. **installed engine/toolchain**은 신뢰 전제다. 이것을 **full reproducible engine attestation**으로 해석하지 않는다.

### 3.3 시작 시 검사와 과거 import

session 시작 시 **current installed binaries/source**가 외부 build pin/evidence와 일치하는지 검사한다. trusted launcher는 기존 Editor 재사용을 금지하고 새 process를 시작한다. 별도 `session_start_evidence`는 `format`, `version`, `session_id`, `runtime_build_evidence_sha256`, `process_id`, `process_start_identity`, `launch_argv`, `executable`, `loaded_module_inventory`, `source_inventory`, `loader_log`, `live_coding_state`, `hot_reload_state`를 가진다. executable/module descriptors의 실제 로드 경로·크기·digest를 build receipt와 비교한다. `process_start_identity`는 OS가 제공한 프로세스 시작 식별값이며 PID 재사용과 구분한다.

Live Coding 비활성 launch/config와 실제 patch-module 부재, hot-reload module 부재를 loaded-module inventory/loader log에서 검사한다. 시작 뒤 module 변경·patch load를 관찰하면 session을 실패시키고 완료 pin 발행을 막는다. 설정 bool이나 `cold_start=true` 같은 **boolean assertion alone**은 증거가 아니다. launcher/collector가 실제 이 기록을 만들고 비교하는 Runtime 하네스가 아직 필요하다.

**offline historical import**는 보관된 source·binary·receipt·시작 증거와 외부 완료 pin의 **pinned historical closure**를 검증한다. 현재 설치된 다른 binary로 과거 결과를 재해석하거나 현재 source hash를 과거 값에 덮어쓰지 않는다. historical artifact가 없거나 decoder/semantic binding이 그 계약을 지원하지 않으면 실패한다. 실제 세션 시작 당시 설치/로드 확인은 trusted collector 증거로 검증하고, 현재 설치 검사는 새로운 수집 session을 열 때 수행한다.

<!-- P2:source-enum -->
## 4. Capture에서 Snapshot으로의 정확한 변환

`decode_committed_capture_bytes`가 검증한 동일 bytes의 payload만 입력으로 쓴다. 두 번째 parser를 만들지 않는다. `EDecisionRecordSourceType`의 숫자 의미는 다음과 같다. 이는 원본 표기 보존이며 label 권한이 아니다. 수집 모드는 raw `2/Dagger`를 요구한다.

| wire source_type | Runtime enum | Snapshot source_type |
|---|---|---|
| `0` | `Silver` | `silver` |
| `1` | `Gold` | `gold` |
| `2` | `Dagger` | `dagger` |

<!-- P2:field-mapping -->
### 4.1 identity·label·부가 metadata

Snapshot의 `snapshot_version="anpc_decision_snapshot_v1"`, `scope="production_candidate"`는 importer 정책이다. wire에 없는 weight는 `source_weight=0.0`으로 두고 `abstain = (len(acceptable_candidate_indices) == 0)`으로만 계산한다. acceptable set을 지워 가짜 abstain을 만들지 않는다. manifest는 기존 `anpc_snapshot_manifest_v1` 형태를 사용하며 `production_eligible=false`, `profile_sha256=collection_execution_profile_sha256`, exact shard bytes/row/source/family counts를 결속한다. 이 source count는 raw enum의 집계이며 Gold 정답 수가 아니다.

| decoder/verified closure field | Snapshot field | 변환 규칙 |
|---|---|---|
| `episode_id` | `episode_id` | exact text; collection episode UUID와 구분 |
| `decision_id` | `decision_id` | exact uint64 |
| `captured_at_server_time` | `captured_at_server_time` | raw finite float64; wall-clock으로 바꾸지 않음 |
| `scenario_family_id` | `scenario_family_id` | exact raw text; episode/catalog와 대조 |
| `episode.family.template_family` | `template_id` | pin된 catalog와 같은 exact text; wire에는 없음을 기록 |
| `generator_version` | `generator_template_version` | exact raw text |
| `map_seed` | `map_seed` | exact uint64; 확정 episode와 대조 |
| `simulation_seed` | `simulation_seed` | exact uint64; 확정 episode와 대조 |
| `candidate_bytes` | `candidate_set_canonical_bytes` | 동일 bytes를 standard base64 ASCII로 인코딩 |
| `candidate_set_hash` | `candidate_set_hash` | raw digest와 재계산 값 일치 |
| `input_content_hash` | `input_content_hash` | raw digest와 재계산 값 일치 |
| `feature_contract_hash` | `feature_contract_hash` | raw digest와 generated semantic 계약 일치 |
| `switch_cost_terms` | `switch_cost_terms` | 272×4 exact bool; 항목 순서 보존 |
| `captured_switch_cost` | `captured_switch_cost` | 272개 float32 decoded value; 다시 pack한 bytes 일치 |
| `target_handles` | `target_handles` | 17개 `{kind,stable_id,generation,revision}`의 exact unsigned integers; slot 순서 보존 |
| `labels.acceptable_candidate_indices` | `acceptable_candidate_indices` | 정렬된 exact indices 보존 |
| `labels.preference_pairs` | `preference_pairs` | 원본 ordered pair 배열 보존 |
| `labels.parameter_target_norm` | `parameter_target_norm` | 272×4 flattened float32 values 보존 |
| `labels.parameter_label_mask` | `parameter_label_mask` | 272×4 flattened bool 보존 |
| `labels.selected_is_acceptable` | `selected_is_acceptable` | raw bool/null 보존; 선택을 추측하지 않음 |
| `labels.label_confidence` | `label_confidence` | raw float32 value 보존 |
| `labels.reason_tags` | `reason_tags` | 원본 canonical 순서와 text 보존 |
| `prompt_version` | `prompt_or_teacher_version` | exact raw text; 빈 문자열도 유지 |
| `parent_policy_hash` | `parent_policy_sha256` | optional hash의 empty string -> None; 나머지 exact digest |

`parent_policy_sha256`는 Snapshot의 추가 provenance metadata로 명시적으로 허용하고 Dataset의 기존 같은 필드로 전달한다. 원본 `sample_id`, `label_block_hash`, `selected_candidate_index`, `record_version`, `annotator_set_hash`, `annotator_agreement` 및 input/label CBOR는 import index의 `raw_capture`에 결속한다. 특히 annotator hash의 빈 text는 원본 그대로 유지하며 가짜 annotator digest로 채우지 않는다. Snapshot 소비자가 필요로 하지 않는 필드를 새 Dataset column으로 만들지 않는다.

`raw_capture`는 raw values와 정규화 전 optional hash 문자열·raw source enum·group 배열·generator/prompt text를 보존한다. binary blob은 standard base64 ASCII로 저장하고 descriptor의 원본 bytes와 대조한다. import index는 Capture/sample identity → Snapshot shard digest와 row ordinal/identity를 기록한다. metadata의 출처가 wire인지 closure인지 importer 정책인지 구분한다. row에 없는 selected index를 새 정답으로 추정하거나 label/source/weight를 바꿔 input parity라고 보고하지 않는다.

label 승인 뒤에는 기존 `sample_id(input_content_hash, episode_id, decision_id, label_block_hash)` 규칙으로 새 Dataset sample identity를 재계산한다. derived index는 원본 sample과 새 label을 가진 sample을 각각 연결하며 원본 sample ID를 덮어쓰지 않는다. Dataset manifest의 `generation_code_sha256`는 변환에 사용한 ML 코드 identity이고 row의 Runtime build digest는 원본 producer identity다. 서로 대신 넣지 않는다.

<!-- P2:groups -->
### 4.2 여덟 group의 wire 순서

scenario family는 별도 필드다. 아래 값은 raw 순서로 복사한다. catalog의 family 이름을 임의로 여덟 위치에 재배치하지 않는다. 필수 생산 metadata가 비었거나 실제 phase/Role 등과 충돌하면 수집/import 검증이 실패하며 기본값으로 수선하지 않는다.

| decoder field | Snapshot field |
|---|---|
| `group_dimensions[0]` | `map_family` |
| `group_dimensions[1]` | `occlusion_layout_family` |
| `group_dimensions[2]` | `goal_sequence_family` |
| `group_dimensions[3]` | `role_id` |
| `group_dimensions[4]` | `personality_cluster_id` |
| `group_dimensions[5]` | `perception_modality_family` |
| `group_dimensions[6]` | `target_composition_family` |
| `group_dimensions[7]` | `event_sequence_family` |

<!-- P2:tensors -->
### 4.3 Tensor blocks

`tensor_blocks[i]`는 아래 `TENSOR_ORDER`/generated `MODEL_INPUT_NAMES` 순서다. Snapshot `tensor_order`도 같은 이름 배열이다. `tensors[name]={dtype,shape,data_base64}`는 원본 block bytes를 그대로 인코딩한다. 최상위 같은 이름의 값 배열은 little-endian float32/int64 또는 0/1 bool로 decode한 row-major flattened 값이다. shape에서 batch 축만 뺀다. `decode_tensor`/`encode_tensor` round-trip과 `tensor_block_bytes`의 **byte-for-byte** 일치를 요구한다. 재정규화나 float smoothing은 하지 않는다.

| i | name | dtype | shape (without B) |
|---|---|---|---|
| `0` | `global_state` | `float32` | `[128]` |
| `1` | `target_features` | `float32` | `[17, 48]` |
| `2` | `target_kind_ids` | `int64` | `[17]` |
| `3` | `target_mask` | `bool` | `[17]` |
| `4` | `event_features` | `float32` | `[12, 24]` |
| `5` | `event_type_ids` | `int64` | `[12]` |
| `6` | `event_target_slots` | `int64` | `[12]` |
| `7` | `event_mask` | `bool` | `[12]` |
| `8` | `candidate_pair_features` | `float32` | `[272, 16]` |
| `9` | `candidate_mask` | `bool` | `[272]` |

<!-- P2:contract-metadata -->
### 4.4 contract hashes와 semantic versions

| decoder field | Snapshot field | 검증 |
|---|---|---|
| `contract_hashes[0]` | `schema_sha256` | pinned generated semantic 계약 |
| `contract_hashes[1]` | `skill_registry_sha256` | pinned generated semantic 계약 |
| `contract_hashes[2]` | `goal_registry_sha256` | pinned generated semantic 계약 |
| `contract_hashes[3]` | `target_slotter_sha256` | 현재 지원 계약은 schema digest에 결속 |
| `contract_hashes[4]` | `normalization_sha256` | 현재 지원 계약은 schema digest에 결속 |
| `contract_hashes[5]` | `postprocess_sha256` | 현재 지원 계약은 schema digest에 결속 |
| `contract_hashes[6]` | `generator_or_runtime_build_sha256` | 외부 runtime_build_evidence_sha256와 일치 |
| `contract_hashes[7]` | `source_decision_contract_hash` | empty string -> None; 값은 exact raw digest |

semantic version 필드는 **absent from wire**다. pin된 generated binding에서 다음 이름으로 가져오고 wire digest가 그 binding과 같은지 먼저 검사한다: `schema_version=SCHEMA_VERSION`, `schema_revision=CONTRACT_REVISION`, `skill_registry_version=CONSTANTS["skill_registry_version"]`, `goal_registry_version=GOAL_REGISTRY_VERSION`, `target_slotter_version=CONSTANTS["target_slotter_version"]`, `normalization_version=CONSTANTS["normalization_version"]`, `postprocess_version=CONSTANTS["postprocess_version"]`.

`contract_metadata()`의 현재 값 전체를 덮어쓰지 않는다. 기존 semantic 검사는 유지하고 build와 optional source-decision만 검증된 context의 원본 값으로 판단한다. `raw_capture.contract_hashes`는 빈 문자열까지 그대로 남긴다. `feature_contract_hash`는 기존 `ANPCFEAT1`/여섯 raw digest 규칙을 재검산한다. 지원되지 않는 semantic binding은 원본을 고쳐 맞추지 않고 거부한다.

수집 전용 producer는 모든 phase에 다음 규칙을 적용한다. Capture `episode_id`는 `scenario_capture_<session UUID>_<collection episode UUID>_<process sequence>`이며 sequence는 0이 아닌 20자리 unsigned decimal이다. `generator_template_version`은 `neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1`이다. reason tag에 `scenario_collection_utility_unreviewed`를 포함한다. raw build·namespace·tag·family·seed·실제 group/phase를 closure와 대조한다. 이는 기존 일반 플레이·fixture namespace를 소급 변경하지 않으며, tag 자체를 발행 권한으로 취급하지 않는다.

<!-- P3:policy-lineage -->
### 4.5 독립적인 정책 lineage

`source_decision_contract_hash`는 원본 decision 계약이고 `parent_policy_sha256`는 별도 원본 policy provenance다. 정규화 후 네 조합은 Snapshot → annotation mapping → final Dataset에서 다음과 같이 보존한다.

| 원본 source-decision | 원본 parent-policy | Dataset source_decision_contract_hash | Dataset parent_policy_sha256 |
|---|---|---|---|
| `None` | `None` | `None` | `None` |
| `S` | `None` | `S` | `None` |
| `None` | `P` | `None` | `P` |
| `S` | `P (S != P)` | `S` | `P` |

Runtime 전용 `_annotation_provenance` 규칙은 **no source-decision fallback**이다. annotation에 parent field가 없으면 context가 증명한 원본 parent 값을 사용한다. field가 명시되어 있으면 `None`도 값으로 비교하고 원본과 mismatch인 경우 reject한다. Teacher/Human label 부여가 rollout policy lineage를 바꾸지 않는다. 우연히 두 digest가 같아도 각 필드의 출처를 따로 검사한다.

<!-- R2:labels -->
## 5. Teacher와 Human label 발행 권한

### 5.1 기존 경로와 새 Runtime-only 권한

현재 `gold.py`의 queue parser/decision join은 **consistency, not Teacher issuance or reviewer authorization**을 확인한다. version marker와 정확한 Snapshot hash가 있는 손작성 queue도 이 조건을 만족할 수 있다. reviewer ID의 nonempty/NFC/sorted 검사는 신원 권한 검사와 구분한다. 기존 Teacher mapper의 request/raw consensus 재구성은 활용하되 그것만으로 provider 실행 사실을 인증했다고 말하지 않는다.

새 Runtime label factory는 다음 증거를 같은 immutable bytes로 재구성한다.

1. import-authorized Snapshot과 독립적으로 허용된 `permitted_teacher_profile_sha256`. Profile의 exact YAML, prompt, request/response Schema, provider type/model identifier/revision/decoding 설정을 결속한다. 허용 목록은 owner가 운영하는 Teacher workflow에서 얻는다. 공개 Profile 이름이나 `provider.type=command`만으로 실제 provider 권한이 생기지 않는다.
2. `build_teacher_request`의 기존 model-visible projection으로 만든 **exact request**. collection 설명·future events·기대 행동·Utility label·sidecar 전체는 모델에 전달하지 않는다.
3. **all five raw attempts**의 실제 bytes, 순서/call index, hash/path, provider 호출 결과와 `provider_error`. 실패한 호출도 버리지 않는다. 현재 generator가 error call을 consensus에 빈 response로 전달하는 규칙까지 동일하게 재구성하고, error call의 원본 stdout bytes는 별도로 그대로 보존한다.
4. 같은 `aggregate_responses`로 strict response validation, consensus, confidence와 **review-routing**을 재실행한다. training annotation과 review queue 양쪽을 exact 비교하며, low-confidence/충돌/불충분 응답 등을 임의 training row로 바꾸지 않는다. 새 consensus 알고리즘을 추가하지 않는다.
5. trusted Teacher runner가 요청·모든 attempts·annotation·queue·source Snapshot shard/manifest·import index·permitted Profile을 완료 artifact closure로 발행하고 readback한 뒤 예치한 `teacher_run_completion_pin`. 이 pin은 owner storage에서 **independent_out_of_band**로 얻는다. 최소 receipt는 각 artifact descriptor와 provider/profile identity, 호출 outcome을 묶고 그 exact receipt digest를 외부 고정한다. 제출된 raw payload·queue를 모두 다시 hash해도 원래 run pin을 대체하지 못한다. bundle 내부의 `expected`나 `approved` 값은 허용하지 않는다.

재구성과 실제 실행의 발행 증명을 둘 다 통과해야 Teacher label 권한을 부여한다. 허용된 실제 provider가 없거나 그 실행 pin이 없으면 실제 Runtime row는 `label_status=utility_unreviewed`, `source_weight=0.0`, `training_eligible=false`로 남는다. 성공한 Teacher consensus만 새 `silver/0.25` Dataset row로 변환한다. Utility의 raw `Dagger`와 선택 결과만으로 전문가 correction 또는 `dagger/1.0`을 만들지 않는다.

### 5.2 Human Gold의 추가 권한

V1 Human 경로는 위 Teacher run의 **재구성된 review queue**를 입력으로 한다. 직접 Capture→Human queue 경로는 추가하지 않는다. 기존 decision/label/parameter 검증은 유지한다. 별도의 owner review workflow가 실제 허용 reviewer의 결정을 확인하고 다음 exact 값과 권한을 owner storage에 발행해야 한다.

- `decision_set_sha256`: 원본 decision YAML exact bytes.
- `review_queue_sha256`, `snapshot_shard_sha256`, `snapshot_manifest_sha256`: decision source가 가리키는 exact artifact bytes.
- Teacher run completion pin과 Runtime import index/collection completion 항목 identity.
- `reviewer_authorization`: owner workflow에서 허용된 reviewer principal 목록, 이 정확한 decision set과 source에 대한 결정 권한, 해당 workflow 기록 식별자. 이는 decision YAML의 self-declared reviewer 목록과 별도로 획득한다.

이 값들을 묶은 owner review 완료 항목을 `human_review_completion_pin`으로 독립 취득한다. **reviewer_id text is insufficient**: decision 파일에 이름을 적거나 그 이름 배열을 hash한 것만으로 Gold 권한을 만들 수 없다. 실제 승인된 decision set과 reviewer 목록이 exact 일치할 때만 새 `gold/1.0` row를 만든다. 오류·누락·권한 불일치는 실패다.

**fresh process**는 collection/import closure, permitted Teacher profile, Teacher run completion pin과 raw attempts/queue, Human 완료 pin과 decision/source/reviewer authorization을 다시 획득해 재구성한다. 전 프로세스의 bool이나 serialize한 권한 객체를 복원하지 않는다. 이 신뢰는 owner workflow/runner의 정직한 발행을 전제로 하며 외부 암호 서명 서비스의 신원 증명을 주장하지 않는다.

기존 **historical Gold**의 기록 수와 사용자 결정은 유지한다. 이전 기록을 삭제하거나 이 문서만으로 새 권한을 발행하지 않는다(`no new human approval`). 기존 일관성 검증 결과는 **not cryptographically authenticated**이며, 이 Runtime 권한 기준으로 소급 인증된 Gold라고 바꾸어 표시하지 않는다. 과거 데이터에 대한 사용자의 기존 판단과 새 Runtime 데이터의 authorization은 별개다.

<!-- R2:fixtures -->
### 5.3 fixture provider와 테스트 산출물

`load_teacher_profile`은 `replay_fixture`를 `integration_fixture` Profile로 제한하지만 현재 generator는 그 scope와 source Snapshot scope의 동일성을 보장하지 않는다. 따라서 source가 `production_candidate`라는 이유로 fixture 응답에 실제 Teacher/Human 권한을 부여해서는 안 된다. 새 경로는 **reject Runtime candidate label authorization**을 적용한다. 실수로 fixture Profile을 넣어도 원본 Runtime Snapshot은 Utility unreviewed/weight 0을 유지한다.

fixture 실행은 격리된 integration 테스트에서만 허용한다. 결과의 외부 authorization report는 `authorization_status=fixture_only`, `label_authorized=false`, `training_eligible=false`이고 실제 provider/사람이 실행됐다고 보고하지 않는다. immutable 원본 Snapshot의 scope를 덮어쓰지 않는다. fixture를 별도 입력으로 복사할 때도 원본 digest와 fixture 목적을 외부 테스트 기록에 연결한다.

**Dataset v2 exact fields**와 가중치는 테스트에서도 유지한다. Silver fixture Dataset은 `silver/0.25`, Gold shape fixture는 `gold/1.0`을 사용하며 weight 0 Dataset이라는 새 형식을 만들지 않는다. 가능한 경로는 `integration_fixture` scope를 사용한다. **legacy Gold** loader처럼 `production_candidate`만 허용하는 기존 API의 synthetic regression은 그 기존 scope로 실행할 수 있지만 외부 fixture report와 격리된 test root로 명시하고 새 Runtime acceptance에서는 거부한다. scope 문자열이 고정된 테스트 형식과 실제 label 권한을 혼동하지 않는다. fixture 권한이나 test runner가 만든 fake pin을 real authority namespace로 가져오는 경로는 금지한다.

<!-- P4:context-api -->
## 6. Context API와 불변 lifecycle

`RuntimeProvenanceContext`는 §2–5 factory가 만든 immutable 검증 결과다. 임의 JSON의 `allow_runtime`, flag, hash 목록으로 만들지 않는다. caller가 신뢰 프로세스 안에서 임의 코드를 실행해 object를 위조하는 위협은 §2의 제외 범위다. 내부 bytes/row/label 값은 외부 mutable dict와 공유하지 않는다. identity뿐 아니라 Tensor·Candidate·mask·switch facts·모든 group·시각·raw label/provenance에 결속한다.

context 인수 이름은 모든 관련 경로에서 keyword-only **`origin_context=None`**으로 통일한다. `_base_record`의 기존 세 번째 positional `provenance`는 label metadata mapping으로 유지한다. 같은 이름의 새 인수를 추가하지 않는다. 다음은 목표 signature이며 production 구현 stub이 아니다.

```python
def validate_snapshot_row(row, *, origin_context=None): ...
def read_snapshot_shard_bytes(shard_bytes, manifest_bytes=None, *, shard_filename=None, origin_context=None): ...
def read_snapshot_shard(path, manifest_path=None, *, origin_context=None): ...
def _base_record(snapshot, labels, provenance, *, origin_context=None): ...
def _validate_record(record, *, origin_context=None): ...
def validate_dataset_shard(parquet_path, manifest_path, *, require_production=False, origin_context=None, require_authorization=False): ...
```

Teacher의 request/generate/authenticate/mapper, Gold immutable bundle/promote/authenticate/map, Dataset mapping-input/base-record/record/write/final-validation 경로는 기존 positional 및 keyword 인수를 보존하고 이 keyword를 명시적으로 전달한다. `origin_context=None`의 성공 의미는 §7의 구조 검증이다. context가 제공됐는데 불일치하면 proofless 검증으로 낮추어 재시도하지 않는다.

순서는 다음과 같다.

1. **import-authorized**: 완료 pin과 historical closure 검증 → 같은 Capture bytes decode → §4 Snapshot 재구성 → 새 Snapshot/manifest의 readback → import index 발행. import 과정의 임시 context는 원본 bytes/정규화 row만 결속한다. 발행된 import index를 검증한 context는 Snapshot shard/manifest digest까지 결속한다. label 권한은 없다.
2. **label-authorized prepublication**: import context + §5의 독립 Teacher/Human 증거로 exact annotation/row identity·label·weight를 결속한다. **Dataset hash not required before mapping**. 이 단계의 context는 mapping과 아직 발행 전 final readback 검증에만 사용할 수 있다.
3. **final-derived-index**: label-authorized context로 Dataset/manifest를 새 경로에 작성하고 동일 bytes를 public `validate_dataset_shard`에서 검증한다. 완료된 Dataset/manifest와 이전 import index·label 증거의 descriptor를 새 derived index에 넣고 **publish derived index last**. 발행 후 derived index에 결속한 final context/result로만 downstream acceptance를 허용한다.

파생 index가 자신의 hash를 담거나 prepublication context가 미래 Dataset hash를 요구하는 순환은 금지한다. 원본 import index와 후속 derived index는 append-only다. 기존 Dataset manifest `snapshot_manifest_sha256`를 source 연결점으로 쓴다. 새 final context는 검증된 source/label 증거로 출력 bytes를 다시 재구성·대조하므로 단순히 제출된 derived index를 다시 hash해 발행 권한을 얻을 수 없다.

**fresh process**는 root·외부 completion/label pins·import/derived index의 exact bytes로 각 단계를 재구성한다. 다른 row의 identity만 복사한 context, 같은 identity의 label 변경, 최종 파일 치환과 stale result 재사용은 실패한다. procedural origin은 §7의 재생성 factory로 같은 명시적 authorization 인터페이스를 제공하며 Runtime context로 위장하지 않는다.

<!-- R3:public-acceptance -->
## 7. Public final validator의 acceptance 경계

### 7.1 proofless 호출의 의미

기존 call syntax와 구조/semantic 검사를 보존한다. `origin_context=None` 기본 호출의 의미는 **STRUCTURE/CONSISTENCY ONLY**다. 기존 code가 성공시키던 procedural/Teacher/Gold 호출을 자동으로 origin 인증으로 격상하지 않는다. Runtime 표식·episode·build·label·manifest를 전부 다시 쓴 **fully rehashed forged Gold**는 **structurally valid**일 수 있다. 기본 validator가 모든 지워진 출처를 감별한다고 약속하지 않는다.

기존 summary `row_count`, `source_counts`, `group_counts`, source/weight/label 주장은 **declared/structurally reconstructed**로 분류한다. bytes에서 다시 셌다는 사실은 authenticated Gold 또는 training readiness를 뜻하지 않는다. structural source count는 별도 인증된 row count와 같은 이름으로 표시하지 않는다.

새 `DatasetAuthorizationResult`는 public `validate_dataset_shard`가 exact final artifact bytes와 context를 검사해 만든 immutable capability/result다. 기존 summary return에 별도의 `authorization` 항목으로 제공한다. 직렬화 report는 읽기용이고 재사용 가능한 권한이 아니다. 모든 status/flag는 **outside record/manifest exact-field sets**에 둔다.

- proofless 결과: `authorization_status=structure_only`, `origin_authorized=false`, `label_authorized=false`, `training_eligible=false`.
- import만 확인된 Snapshot 상태: `authorization_status=origin_only`, origin true/label false/training false. raw Utility를 Dataset으로 만들 권한은 없다.
- fixture 검증 결과: `authorization_status=fixture_only`, 실제 origin/label 권한 false, training false.
- 실제 원본과 허용된 label을 검증한 최종 결과: `authorization_status=authorized_candidate`, origin/label true. exact shard/manifest/import/derived-index digests와 authority 항목 identities를 결속한다. 이는 provenance/label acceptance이며 자동 학습 준비 완료는 아니다.

`training_eligible`은 위 origin/label 권한과 기존 owner-permitted data qualification, scope/Profile/분할·coverage 등 필요한 학습 조건이 모두 충족될 때만 true다. 해당 qualification 증거가 없으면 authorized candidate도 false다. 이 계약은 qualification 정책·훈련기를 새로 구현하지 않는다. 여기서 새로 수집할 자료는 실제 permitted label authority와 qualification이 확보되기 전까지 false다. 모든 경우 collection의 `production_eligible=false`는 그대로 유지한다.

### 7.2 강한 acceptance를 요청하는 호출

Runtime의 **import acceptance requires origin_only**: import-authorized context가 증명한 unreviewed Snapshot을 검토 입력으로 만드는 단계까지 허용하며 미래의 Teacher/Human label을 요구하지 않는다. Runtime Dataset mapping/final acceptance와 **training/qualification acceptance**에는 원본과 label 양쪽 권한이 필요하다. 최종 Dataset 경계는 `validate_dataset_shard(..., origin_context=context, require_authorization=True)`다. source origin 또는 label authority 중 하나라도 유효하지 않으면 오류로 끝낸다. caller는 `require_authorization=False` 결과의 truthiness나 row count를 readiness로 받아들이지 않는다. qualification 입력 채택은 authorized candidate result를 요구하며 실제 training 채택은 별도 qualification까지 만족해야 한다. **proofless forged row never training-ready**가 회귀 조건이다.

public final validator는 mapper를 거치지 않은 직접 호출에서도 모든 row의 origin·label·source/weight·source Snapshot/manifest·derived index 연결을 검사한다. prepublication 검증은 label-authorized context에 결속한 정확한 변환 결과를 검사하고 downstream 사용 가능한 capability는 final-derived-index를 결속한 뒤 발행한다. forged context/status dict 또는 이전 파일에 대한 결과는 권한 입력이 될 수 없다. `require_production=True`는 이 authorization 검사를 포함하고 기존 Production 조건도 모두 유지한다. candidate/fixture는 여전히 Production에서 거부한다.

새 권한의 실제 승인 주체가 없으면 긍정 사례를 실행한 척하지 않는다. 단위 하네스는 격리된 synthetic authority로 재구성 경로를 검증할 수 있지만 결과는 fixture-only이며 실제 Teacher/Human/학습 증거로 집계하지 않는다. real authorized positive case는 허용된 실제 실행/검토 증거가 있을 때에만 real acceptance 증거다.

<!-- R3:procedural -->
### 7.3 procedural mapper의 독립적인 보강

`map_procedural_dataset`은 Runtime context를 허용하지 않고 정확히 `silver/0.25`와 실제 procedural 생성 결과만 허용한다. **trusted procedural profile**의 **exact bytes**·digest와 허용된 generator source로 **complete row/manifest**를 재생성해 입력과 대조한다. 기존 호출은 digest로 등록된 **registered bundled profile**을 찾는다. **custom profile**에는 명시적으로 pin된 경로/digest가 필요하다. 임의 디렉터리 탐색이나 제출 Snapshot의 profile 선언 자체를 anchor로 사용하지 않는다.

이는 mapper의 source laundering 방어이며 **not a universal proof for direct final Dataset validation**이다. public final acceptance의 procedural origin context는 같은 재생성을 다시 증명하고 그 결정적 label/source/weight 정책을 검사해야 한다. procedural Snapshot에 Teacher/Human label이 붙은 경우 origin 재생성과 §5의 label issuance 증거를 각각 요구한다. legacy proofless Teacher/Gold 성공은 계속 구조 검증으로만 분류한다. 이 V1은 새로운 DAgger label 발행/승인 경로를 추가하지 않는다.

<!-- publication -->
## 8. 산출물·명령·발행 순서

새 authority Schema 목표는 `contracts/current/capture_import_provenance_v1.schema.json`이며 `anpc_runtime_import_provenance_v1` import index와 새 derived index를 정의한다. base collection index와 Dataset v2의 exact fields를 늘리지 않는다. import index는 completion closure/pin identity, parser/importer exact source digest와 version, raw Capture/sample/episode/decision/input identity, §4의 raw-to-Snapshot 매핑, Snapshot shard/manifest descriptors, `scope=production_candidate`, `production_eligible=false`, `label_status=utility_unreviewed`, `training_eligible=false`를 결속한다. derived index는 그 원본과 독립 label authority 및 final Dataset/manifest를 연결한다.

다음은 구현 목표 CLI다. ML 작업 디렉터리는 `NeuralGame/ML`이며 실행 entry는 기존 `python -m anpc_ml`에 연결할 예정이다. 아래 명령이 현재 구현됐다고 주장하지 않는다.

- `capture import`: root·final collection index와 owner storage에서 독립 취득한 completion pin/closure·catalog/execution-profile/build pins → Snapshot·manifest·import index.
- `collection validate`: 같은 외부 anchor와 immutable 원본 closure를 재검증. 구조 검증만 요청한 기존 harness 결과와 발행 권한 결과를 구분한다.
- `collection coverage`: source별 시도·진단·committed·고유 model input·중복·관측 적합·raw labels·authorized labels·Dataset rows를 별도 집계.
- Teacher/Gold/Dataset 명령: proof index/root에 더해 independently acquired completion 및 label pins를 trusted caller 경로로 전달. 새 acceptance 명령은 public final validator의 `require_authorization=True`를 강제한다. legacy 기본 validate는 구조 결과라고 표시한다.

ML이 별도 문서 저장소 decoder/harness를 읽는 실제 dependency root와 source digest를 pin한다. import 오류를 가짜 parser로 대체하지 않는다. 산출물은 새 이름으로 배타적으로 만들고 exact readback 후 index를 마지막에 발행한다. 충돌·중간 실패는 기존 파일을 보존하고 완료/derived index를 발행하지 않는다. 저장 flag를 재사용해 부분 결과를 정상 자료로 다루지 않는다.

<!-- regression-matrix -->
## 9. 먼저 실패시킬 회귀와 이 개정의 검증 범위

다음은 **후속 executable security 하네스의 acceptance 목록**이다. 이 문서의 전용 테스트는 **document consistency tests**, **not executable security fixes**다. 문구/table/signature의 실패→통과는 현재 Runtime/ML 공격 차단 구현의 통과가 아니다.

| 사례 | 후속 하네스에서 요구할 결과 |
|---|---|
| `R1-substitute-rehashed` | 공개 build/profile 값을 복사해 Capture/marker/session/episodes/index 전체를 재작성·rehash해도 원래 외부 index pin/closure에서 실패. 내부 expected 선언으로 우회 불가. |
| `R1-trusted-publication` | 지정 producer가 readback하고 마지막에 발행한 index와 owner pin의 동일 closure는 import-authorized까지 통과. index만 맞고 session/episodes가 바뀌면 실패. |
| `R2-forged-queue` | 손작성 queue, 다른 Profile, 누락/재정렬 raw attempt, provider_error 조작, consensus/review-routing 교체, 전체 rehash 뒤에도 독립 Teacher-run pin에서 실패. |
| `R2-forged-reviewer` | reviewer_id text와 decision/source hashes만 맞춘 Gold는 owner review 권한 없으면 실패. decision/queue/source 또는 허용 principal 교체도 실패. |
| `R2-fixture-candidate` | replay_fixture Profile + production_candidate source도 실제 label/training acceptance에서 실패; 격리 fixture 결과는 fixture_only/false. |
| `R2-authorized-teacher` | 실제 허용 Profile·runner 완료 pin·모든 attempts의 재구성과 training consensus가 있으면 Silver mapping부터 public final authorization까지 통과. review-routed row는 제외. |
| `R2-authorized-human` | 위 Teacher review proof + 독립 owner decision/source/reviewer 권한이 있으면 Gold mapping부터 public final authorization까지 통과. fresh process에서도 같은 결과. |
| `R3-public-proofless-forgery` | 직접 public final validator에 fully rehashed origin-erased Gold 제출: legacy 구조 호출은 구조 성공 가능, strong acceptance는 실패, training-ready는 절대 아님. |
| `R3-public-authorized-origins` | 재생성한 procedural Silver, Runtime+permitted Teacher Silver, Runtime+permitted Human Gold 각각의 정상 final context 통과. 다른 row/file context와 label 증명 누락은 실패. 실제 authority 없는 positive simulation은 fixture-only로 보고. |
| `P1-cold-start-historical` | source/receipt/module 경로·bytes 불일치, incremental-only, patch DLL, 재사용 process, 시작 후 module 변경, bool-only 증거는 실패. 보관 closure가 맞는 과거 import는 다른 현재 설치 때문에 재해석하지 않음. |
| `P2-full-parity` | decoder의 모든 Tensor·Candidate·handle·switch·label·group·identity·raw optional 값과 Snapshot 매핑 parity. semantic version의 wire 부재와 template 출처를 확인. acceptable set 보존. |
| `P3-four-policy-combinations` | null/null, value/null, null/value, distinct value/value의 exact 보존. source-decision을 parent로 대신 넣으면 실패. |
| `P4-prepublication-lifecycle` | positional label metadata와 keyword-only origin_context 전달 유지. Dataset digest 없이 prepublication context 생성, final bytes 검증 뒤 derived index 발행. fresh-process 재구성·mutability·stale result 치환 실패. |

추가로 Capture/marker 및 Snapshot/manifest의 single-read/ABA 치환, source/weight/label 전체 rehash와 procedural 재생성 불일치, raw Utility의 procedural/Gold/Dagger 승격 거부, Teacher request의 hidden scenario/Utility-label noninterference, 기존 procedural/Teacher/Gold 구조 회귀, 모든 candidate의 Production 거부를 유지한다.

미완료 경계는 실제 trusted build/launcher/collector와 외부 pin 저장소 연결, provenance Schema와 executable failure harness, Runtime-only context/권한 API, 허용된 실제 Teacher/Human workflow, data qualification이다. 이 계약은 이 작업들을 승인 완료나 데이터 생산 완료로 표시하지 않는다. 독립 closure review 후에 Schema/harness 구현으로 진행한다.
