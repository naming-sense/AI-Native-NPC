# Runtime 수집 자료의 ML 가져오기 V1 계약

Runtime 수집 자료 가져오기는 게임에서 얻은 판단 기록을 원본과 출처를 보존하면서 학습 검토용 자료로 옮기는 절차다.

**이 계약은 원본 출처 확인, 정답 승인, 학습 자격 판정을 각각 수행하도록 정한다.** 원본 출처를 확인한 자료는 정답 검토에 사용할 수 있다. 학습에는 허용된 정답과 별도의 학습 자격이 필요하다.

## 이 문서에서 정하는 것

- 게임의 판단 기록(Capture)을 학습 검토용 판단 자료(Snapshot)로 변환한다.
- 실제 수집에서 나온 자료인지 확인한다.
- Teacher와 사람의 정답 승인 근거를 확인한다.
- 최종 학습 데이터(Dataset)의 원본·정답·파일 연결을 확인한다.
- 기존 Dataset v2 레코드와 manifest의 필드 집합을 유지한다.
- 기존 가중치 `silver/0.25`, `gold/1.0`, `dagger/1.0`을 유지한다.
- 모든 수집 산출물의 `production_eligible=false`를 유지한다.

**문서 상태:** 새 Schema·API·명령과 실패 조건을 정한 구현 계약이다. 아래의 새 기능은 구현 목표로 기술한다. 실제 구현, 수집, Teacher 실행, 사람 승인, 학습 준비 상태는 각각의 작업 결과에서 확인한다. 새 학습기는 이 계약의 범위 밖이다(`no new trainer`).

**읽는 순서:** §1에서 용어와 전체 흐름을 읽는다. §2–3은 수집 자료의 출처를 다룬다. §4는 정확한 변환 규칙이다. §5–7은 정답과 최종 사용 권한을 다룬다. §8–9는 산출물과 실패 조건이다.

## 1. 목적과 현재 코드의 경계

가져오기는 원본 입력, Utility 정답 후보, 자료가 만들어진 이력을 함께 보존한다.

### 1.1 용어

| 독자용 명칭 | 뜻과 코드·Schema 이름 |
|---|---|
| 판단 기록(Capture) | 게임이 기록한 한 번의 판단 입력과 결과다. 원본 파일과 committed marker를 함께 읽는다. |
| 학습 검토용 판단 자료(Snapshot) | 판단 기록을 ML 도구가 읽는 형태로 변환한 자료다. 정답 승인 전 자료도 담는다. |
| 정답(label) | 학습에 사용할 허용 행동, 선호 관계, 파라미터와 관련 정보다. |
| Utility 정답 후보 | 기존 Utility 정책이 남긴 판단이다. 승인 전 상태는 `utility_unreviewed`다. |
| 완료 확인값(completion pin) | 지정된 발행자가 완료한 파일을 가리키도록 외부 저장소에 고정한 digest와 권한 정보다. |
| 완료 묶음(`completion_closure`) | 최종 목록, 세션, 모든 회차와 출처 기록을 함께 묶은 불변 목록이다. |
| 파일 명세(descriptor) | 파일의 경로·크기·SHA-256를 담은 값이다. 기본 필드는 `{path,size_bytes,sha256}`다. |
| 수집 실행 설정(`collection_execution_profile`) | 입력 주체, 실행 방식, 제한과 사용할 계약을 정한 설정이다. |
| 출처 확인 컨텍스트(`RuntimeProvenanceContext`) | 허용된 절차가 원본과 정답의 근거를 확인한 뒤 만드는 불변 객체다. |
| 권한 결과(`DatasetAuthorizationResult`) | 최종 파일과 출처 확인 컨텍스트를 대조한 결과다. 후속 단계가 사용할 수 있는 범위를 나타낸다. |

SHA-256는 bytes를 식별하는 digest다. 파일 내용의 일치와 발행자의 권한은 별도로 확인한다.

### 1.2 전체 흐름

1. **수집 완료:** 수집기가 세션과 회차를 종료하고 최종 목록을 저장한다. 소유자 저장소에 완료 확인값과 완료 묶음을 보관한다.
2. **원본 가져오기:** 가져오기 도구가 외부 완료 확인값과 원본 파일을 대조한다. 같은 bytes에서 Snapshot을 만든다.
3. **정답 승인:** 허용된 Teacher 실행이나 사람 검토의 완료 근거를 확인한다.
4. **Dataset 발행:** 승인된 정답을 기존 Dataset v2 형식으로 변환한다. 원본과 결과를 연결한 파생 목록을 마지막에 저장한다.
5. **학습 자격 판정:** 원본·정답 권한과 기존 데이터 품질 조건을 모두 충족한 자료만 학습 입력으로 채택한다.

원본 가져오기만 끝난 Snapshot은 `source_weight=0.0`인 검토 자료다. Teacher가 승인한 Dataset은 `silver/0.25`, 사람이 승인한 Dataset은 `gold/1.0`이다. Runtime의 Utility 기록만으로 새 `dagger/1.0` 자료를 발행하는 경로는 이 V1에 포함하지 않는다.

### 1.3 재사용하는 기존 코드

| 위치 | 역할 |
|---|---|
| 문서 저장소 `tools/validate_anpc_capture_v2.py` | 원본 bytes를 해석하는 `decode_committed_capture_bytes`, payload 반환, unsigned marker 검사다. |
| 문서 저장소 `tools/validate_scenario_collection.py` | 카탈로그를 읽는 `load_catalog`, digest를 만드는 `catalog_digest`, 목록을 검사하는 `validate_index`다. |
| `NeuralGame/ML/anpc_ml/snapshot.py` | Snapshot 필수 필드, Tensor, 대상 식별값, 입력 검사다. |
| 같은 ML root의 `contracts.py`, `canonical.py` | 생성된 계약 연결과 의미 정보, Tensor·JSON·식별자 인코딩이다. |
| 같은 ML root의 `teacher.py` | Teacher 설정, 요청 구성, 원본 응답, 합의 처리다. |
| 같은 ML root의 `gold.py` | 사람의 결정과 검토 대기열, Snapshot을 연결하는 코드다. |
| 같은 ML root의 `dataset.py` | `_base_record`, `_annotation_provenance`, 공개 최종 검사기다. |
| Runtime의 `Dataset/DecisionRecordV2.h/.cpp` | 판단 기록의 저장 순서를 정의한다. |
| Runtime의 `Execution/AINativeNPCGoalHostComponent.cpp` | 판단 기록을 생산한다. |
| Runtime의 `Policy/UtilitySelection.h/.cpp` | 컴파일된 Utility 설정을 정의한다. |

Runtime 경로의 기준은 `NeuralGame/Source/NeuralGame/AINativeNPC`다.

기존 `contract_metadata()`는 Runtime build 필드도 Python generator digest와 비교한다. 새 가져오기 경로는 원본 build 값을 별도로 확인한다. 원본 build 값을 Python digest로 바꾸어 맞추는 처리는 허용하지 않는다.

기존 Gold 검사의 범위는 canonical JSON, hash와 자료 간 연결의 일관성이다. Teacher 발행자와 검토자 권한은 이 계약의 별도 확인 대상이다. 모든 hash를 다시 만든 위조 Gold가 기존 공개 검사에서 구조적으로 통과할 수 있다는 재현을 전제로 한다. 구조 통과는 Production 승인이 아니다.

<!-- R1:issuance -->
## 2. 완료된 수집 묶음의 발행 권한

완료 확인값은 지정된 수집기가 끝낸 자료와 제출된 파일을 연결하는 외부 기준이다.

### 2.1 외부 completion pin

최소 외부 기준은 최종 수집 목록 파일의 exact bytes에 대한 SHA-256다. 입력 이름은 `expected_collection_index_sha256`다.

지정된 수집기·제어기는 다음 순서로 발행한다.

1. 실제 수집에서 만든 Capture와 committed marker의 불변 bytes를 읽고 확인한다.
2. 세션과 모든 회차 이력을 종료한다.
3. 최종 수집 목록을 배타적으로 저장한다. 목록은 마지막에 발행한다(`publish index last`).
4. 저장한 최종 파일을 다시 읽어 exact bytes를 확인한다.
5. 소유자 관리 저장소에 완료 확인값과 완료 묶음을 예치한다.

실행 중 목록, 임시 파일, 미완료 이력에는 완료 확인값을 발행하지 않는다.

#### 함께 고정할 완료 묶음

기존 수집 목록의 최상위 필드는 `format`, `version`, `session_id`, `entries`다. 이 필드 집합을 유지한다.

기존 목록에는 세션·회차 파일 명세가 없다(`base index has no session/episode descriptors`). 따라서 목록 digest만으로는 별도 세션·회차 파일을 고정할 수 없다. 같은 소유자 완료 항목에 아래 완료 묶음(`completion_closure`)을 함께 불변 보관한다. 이 권한 정보는 기존 collection-index Schema 밖에 둔다.

| 완료 묶음의 항목 | 고정할 내용 |
|---|---|
| 최종 목록(`collection_index`) | `{path,size_bytes,sha256}`. `sha256`는 외부 `expected_collection_index_sha256`와 같아야 한다. |
| 세션(`session`) | 최종 세션 파일 명세다. |
| 순서 있는 회차 목록(`ordered_episodes`) | 실제 실행 순서의 모든 최종 회차 파일 명세다. Capture가 없는 실패·취소 회차도 포함한다. |
| 이전 재실행 자료(`replay_predecessors`) | 필요한 이전 세션의 완료 확인값 식별자와 원본 세션·회차 명세다. 외부 이전 자료도 해당 세션의 독립 확인값으로 확인한다. 미래 참조와 순환 참조는 거부한다. |
| 카탈로그(`catalog`) | 보관한 파일 명세와 별도로 고정한 canonical `catalog_sha256`다. |
| 수집 실행 설정(`collection_execution_profile`) | 파일 명세와 별도로 고정한 `collection_execution_profile_sha256`다. |
| 빌드 기록(`runtime_build_evidence`) | 파일 명세와 별도로 고정한 `runtime_build_evidence_sha256`다. |
| 시작 기록(`session_start_evidence`) | §3의 실제 프로세스 시작과 로드된 모듈 확인 기록이다. |

각 파일 명세의 `path`는 collection root 기준 POSIX 상대 경로다. 빌드 기록 안의 다른 경로 기준은 §3에서 정한다.

최종 목록이 가리키는 모든 Capture, marker와 diagnostic 파일 명세를 확인한다. 완료 묶음 밖의 제출 파일을 보충 출처로 탐색하지 않는다.

소유자 저장소는 같은 권한 구역에서 같은 목록 digest에 서로 다른 완료 묶음을 등록하는 일을 거부한다. 완전한 발행 판단에는 외부 확인값과 완료 묶음이 모두 필요하다.

#### 실제 Runtime 출처와 테스트 출처

실제 Runtime 자료의 세션·회차·entry는 수집 방식에 맞는 입력 출처(`input_source`)를 가진다.

- 자동 Runtime 수집은 `automated_runtime`이다.
- 사람 플레이 수집은 `human_play`다.
- `offline_procedural`과 `test_fixture`는 기존 구조 검사에서 표현할 수 있다. 실제 Runtime 출처 권한의 발행 대상에는 포함하지 않는다.
- 격리된 테스트용 완료 확인값은 실제 수집의 확인값으로 교환하지 않는다.

#### 가져오기 권한의 입력

신뢰한 호출자는 제출 묶음과 독립적인 소유자 저장소에서 완료 확인값 객체(`TrustedCollectionCompletionPin`)를 얻는다. 취득 방식은 `independent_out_of_band`다.

목표 factory는 다음과 같다.

```python
authorize_runtime_import(root, *, completion_pin, parser_pin, importer_pin)
```

- `completion_pin`은 외부 digest, 완료 묶음과 소유자 저장 항목의 식별자를 담는다.
- 카탈로그·설정·빌드 확인값도 같은 소유자 항목에서 별도로 얻는다.
- `parser_pin`과 `importer_pin`은 운영자가 허용한 도구의 source와 version이다.

제출한 JSON을 역직렬화해 완료 확인값 객체를 만들지 않는다. 예상값의 취득원으로 submitted index, metadata, uploaded bundle, self-declared expected fields를 사용하지 않는다.

묶음 안에 복사한 확인값은 진단용이다. 방금 읽은 목록의 digest를 계산해 그 값을 예상값으로 다시 넣는 경로는 거부한다. 출처를 모르는 root나 bundle은 독립적인 외부 기준이 없으면 실패한다.

외부 보관 묶음의 복사본은 독립 확인값과 완료 묶음 전체가 일치할 때 허용한다. 공개된 build/profile 이름과 digest를 복사한 뒤 Capture·marker·index를 다시 작성하고 hash한 제출물은 원래 완료 확인값과 불일치하므로 거부한다.

### 2.2 신뢰 전제와 한계

이 계약의 신뢰 주체는 지정된 로컬 운영자, 빌드 생산자, 수집기·제어기, 소유자 저장소 관리자다.

- 생산자는 자신이 관찰한 실행에서만 완료 항목을 발행한다.
- 제출된 파일을 사후에 실제 수집물로 등록하지 않는다.
- 저장소는 작성 권한과 변경 이력을 관리한다.
- 발행된 항목은 이후에도 불변으로 보관한다.
- 비공개이고 안정적인 root는 경로 치환을 막는 전제다. 파일 발행자 확인은 별도로 수행한다.

Capture checksum과 서명 없는 marker는 bytes 사이의 연결을 확인한다. 이 계약은 별도 서명 서비스가 없는 로컬 신뢰 방식이다(`no signing service`). 다음 위협은 해결 범위 밖이다.

- 신뢰한 운영자나 toolchain 자체의 악의적 동작.
- 소유자 저장소 장악.
- 신뢰한 프로세스 안에서 임의 코드 실행.

발행자가 실제 실행과 완료 확인값을 정직하게 연결한다는 전제를 문서와 결과에 유지한다. 임의의 외부 파일을 인증하는 범용 원격 증명은 제공하지 않는다.

#### 같은 파일 내용을 끝까지 사용하는 규칙

입력 검사는 같은 불변 bytes를 사용한다.

1. 알려지지 않은 필드, 중복 JSON key, 비유한 수와 자동 유형 변환을 거부한다.
2. 경로의 `..`, 절대 경로, drive, backslash와 symlink escape를 거부한다.
3. 상위 디렉터리가 바뀌지 않도록 보호한다.
4. 원본 파일을 한 번 읽은 bytes에서 크기·hash·parse·join·decode를 수행한다.

hash 후 파일을 다시 열거나, 검사 후 다시 hash해 다른 내용을 채택하지 않는다. 파일을 바꿨다가 원래 경로로 되돌리는 ABA 치환도 허용하지 않는다. 외부 확인값은 발행된 내용을 식별한다. 같은 bytes 사용 규칙은 확인 도중의 내용 변경을 막는다.

<!-- P1:digests-build -->
## 3. Profile 구분과 수집 전용 build 증거

수집 출처는 실행 설정, 빌드 기록, 실제 시작 기록을 함께 확인해 결정한다.

### 3.1 digest 이름과 byte grammar

SHA-256는 소문자 hex로 표현한다. 아래 카탈로그 예외를 제외하면 저장된 파일의 exact bytes를 hash한다.

새 JSON 산출물은 다음 형식으로 한 번 직렬화한다.

```text
sorted_json_bytes(value) + b"\n"
```

- UTF-8을 사용한다.
- key를 정렬한다.
- compact separators를 사용한다.
- `ensure_ascii=False`, `allow_nan=False`를 적용한다.
- 마지막에 LF 하나를 붙인다.
- 이 파일 bytes를 완료 확인값에 연결한다.

기존 YAML Profile은 원본 bytes를 사용한다. 파싱 후 재직렬화하지 않는다. 배열의 의미 있는 순서는 유지한다. inventory만 `(base,path)`의 UTF-8 byte 순서로 정렬하고 중복을 거부한다.

| 독자용 명칭과 식별자 | 식별하는 내용 |
|---|---|
| 카탈로그 digest(`catalog_sha256`) | `load_catalog`로 strict parse·validation한 뒤 `catalog_digest`와 같은 canonical object bytes를 hash한다. 마지막 LF를 붙이지 않는다. 저장된 카탈로그 파일 명세의 raw-file hash와 구분한다. |
| 수집 실행 설정 digest(`collection_execution_profile_sha256`) | 수집 실행 설정 JSON의 exact bytes다. 세션과 Snapshot manifest의 기존 `profile_sha256`가 이 값을 사용한다. ML procedural 설정이나 Teacher 설정과 구분한다. |
| Utility source digest(`utility_profile_source_sha256`) | `utility-profile-source-v1` source 명세 JSON의 exact bytes다. `BuildGuardPhase0UtilityProfile` 이름이나 ProfileId 문자열의 hash와 구분한다. |
| Teacher 설정 digest(`teacher_profile_sha256`) | `load_teacher_profile`이 읽은 YAML 원본 bytes다. 사용 권한은 별도 허용값(`permitted_teacher_profile_sha256`)으로 정한다. |
| Runtime 빌드 기록 digest(`runtime_build_evidence_sha256`) | 빌드 뒤 작성한 기록 JSON의 exact bytes다. 세션의 `runtime_build_sha256`와 수집 Capture의 `GeneratorOrRuntimeBuildSha256`에 같은 값을 연결한다. |

카탈로그의 hash 식은 다음과 같다.

```text
sha256(json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
```

#### 수집 실행 설정의 필드

수집 실행 설정은 아래 필드만 가진다.

- 형식과 버전: `format="anpc_collection_execution_profile_v1"`, `version=1`.
- 카탈로그와 관측 계약: `catalog_sha256`, `observation_mapping_version`.
- 입력과 실행 주체: `input_source`, `execution_mode`, `controller`.
- 실행 제한: `limits`.
- Utility source 연결: `utility_profile_source_sha256`.

입력·실행 주체와 제한의 유형·범위는 기존 session Schema를 따른다. 실제 시나리오, 버전, 조건과 seed는 고정된 episode와 catalog에서 확인한다. 이 설정으로 새 배치 범위나 관측 Feature를 추가하지 않는다.

#### Utility source 명세의 필드

Utility source 명세는 `format`, `profile_id`, `entries`만 가진다.

- `format`은 `utility-profile-source-v1`이다.
- `profile_id`는 생성된 `AINativeNPC::GoalGameplayV1::UtilityProfileId`의 exact text다.
- `entries`는 아래 source의 `{base,path,size_bytes,sha256}` 목록이다.
- 경로 기준은 project root다.

```text
Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.cpp
Source/NeuralGame/AINativeNPC/Policy/UtilitySelection.h
Source/NeuralGame/AINativeNPC/Generated/AINativeNPCGoalGameplaySemantics.generated.h
Source/NeuralGame/AINativeNPC/Generated/AINativeNPCContracts.generated.h
```

이 digest는 선택한 source를 식별한다. 실행 binary와의 대응은 다음 빌드 기록에서 확인한다. Utility 직렬화나 평가 알고리즘은 기존 것을 유지한다.

### 3.2 bounded build evidence

수집 모드는 실제 빌드 뒤 작성한 외부 기록의 digest를 사용한다.

기존 일반 플레이의 `ComputeRuntimeBuildHash()`는 유지한다. 이 함수의 build-version 문자열 hash는 실제 binary 확인용으로 사용하지 않는다. binary 안에 자기 digest를 넣는 순환도 만들지 않는다.

#### 빌드 기록의 필드

빌드 기록은 아래 최상위 필드만 가진다.

| 구분 | 필드 |
|---|---|
| 형식 | `format="anpc_collection_build_evidence_v1"`, `version=1` |
| 빌드 대상 | `project_file`, `target`, `platform`, `configuration` |
| source 목록 | `source_inventory_before`, `source_inventory_after` |
| 실행 내용 | `build_mode`, `build_argv`, `build_working_directory`, `exit_code` |
| 실행 결과 파일 | `build_log`, `build_receipt`, `module_artifacts` |
| 설치 도구 | `engine_toolchain_identity` |
| 수집 계약 | `collection_schema_sha256`, `catalog_sha256`, `collection_execution_profile_sha256`, `utility_profile_source_sha256`, `observation_mapping_version` |

target, platform과 configuration은 신뢰한 실제 빌드 호출의 값을 기록한다. 성공하지 않은 명령의 결과를 성공값으로 채우지 않는다.

#### 경로 기준

경로 기준은 신뢰한 호출자가 지정한다. 제출 묶음은 이 기준을 바꿀 수 없다.

- 프로젝트 기준(`project_root`): 실제 `NeuralGame.uproject`가 있는 디렉터리다.
- 계약 기준(`authority_root`): `AI-Native-NPC` 문서·계약 저장소다.
- 기록 기준(`evidence_root`): 수집기가 이번 실행에 만든 기록 디렉터리다.

#### source 목록과 전후 일치

source 목록의 항목은 `{base,path,size_bytes,sha256}`다. 최소 포함 범위는 다음과 같다.

- 프로젝트의 `NeuralGame.uproject`.
- 프로젝트의 `Source/` 전체. 모든 project module, Target.cs, Build.cs와 생성 header를 포함한다.
- 프로젝트의 `Config/` 전체.
- 활성 project-local plugin의 descriptor, source와 config.
- 실제 선택 map과 그 map이 의존하는 project Content 전체.
- 계약 저장소의 collection/Capture Schema, Skill/Goal Registry, catalog, 관측 mapping 계약과 generated lock.

활성 plugin과 Content 의존성의 완전성은 build receipt와 선택 map의 의존성 기록으로 확인한다. 불명확하거나 누락된 의존성은 거부한다. engine source 전체를 이 목록에 넣지는 않는다.

빌드 전후 목록(`source_inventory_before`, `source_inventory_after`)은 항목·크기·digest가 모두 같아야 한다. 새 파일, 삭제와 누락도 차이로 취급한다. project-local 생성 header가 빌드 중 바뀌면 안정화한 source로 새 빌드 기록을 만든다. UHT가 Intermediate에 만든 결과는 build receipt와 log의 산출물로 식별한다.

이 목록은 준비한 빌드의 입력을 보관하는 기록이다. 수집에는 별도 작업 위치의 고정 입력을 사용한다. 원본 개발 폴더·설치 Engine·원본 Saved 전체를 세션 내내 잠그거나 재귀 감시할 필요는 없다. 매 tick·Capture 발행 때 이 목록의 모든 파일을 다시 읽는 조건도 두지 않는다. 고정 입력과 수집 출력의 실제 읽기·쓰기 실패는 계속 처리한다.

#### 실제 빌드와 모듈 확인

허용하는 빌드 방식은 `build_mode="clean_or_forced_project_modules"`다. 이 값은 준비한 빌드의 생성 방식을 뜻한다. 같은 빌드로 다음 회차나 새로운 수집 세션을 진행할 때마다 재빌드할 필요는 없다.

기존 빌드로 다시 수집할 때는 원래 준비한 실행물과 빌드 기록을 함께 사용한다. 준비 완료 기록은 실제 빌드와 게임 자료 준비가 끝난 뒤 발행한다. 재사용은 그 기록과 실제 파일의 대응을 확인한 뒤 수행한다. 재사용 사실을 새로운 빌드 성공으로 기록하지 않는다.

- `build_argv`는 실행 인수 배열이다. shell string 하나로 저장하지 않는다.
- `build_working_directory`는 `{base,path}`다.
- `exit_code`는 `0`이어야 한다.
- `build_log`와 `build_receipt`는 evidence root 기준 파일 명세다.
- clean 또는 forced rebuild가 대상 project module의 모든 translation unit을 실제 compile/link했는지 log와 receipt로 확인한다.
- `incremental_success_only`는 거부한다.

Unreal 빌드 도구는 C++ 컴파일과 Windows 실행 파일의 리소스 컴파일을 모두 `Compile`로 기록할 수 있다. 실제 호출 도구와 입력·출력으로 두 작업을 구분한다. 리소스 컴파일은 `rc.exe`, 설치 엔진의 `Default.rc2`, 생성된 `.res`와 최종 링크의 연결을 기록한다. C++ 입력이 없는 리소스 작업에 가상의 C++ 파일을 요구하지 않는다.

Unreal이 생성한 C++ 코드는 여러 파일을 묶은 컴파일 입력을 사용할 수 있다. 빌드 기록에서는 생성 코드 폴더의 직접 입력과 `Intermediate/Build/` 아래의 `Module.NeuralGame.gen.*.cpp` 입력을 함께 지원한다. 두 경우 모두 실제 컴파일 명령·입력 파일·산출물·링크 기록을 사용한다.

빌드 성공 여부와 별도로 나열한 source/DLL hash만으로 source와 binary의 대응을 인정하지 않는다.

모듈 산출물(`module_artifacts`)은 receipt가 선택한 모든 로드 대상 project module의 목록이다. 항목은 `{module_name,base,path,size_bytes,sha256}`이며 `base=project_root`다. 실제 loader와 receipt의 경로를 사용한다. 가장 최근 DLL을 wildcard로 고르거나 stale/hot-reload 대체 DLL을 채택하지 않는다.

실행 파일이 engine 제공 파일이면 exact 설치 경로·크기·digest를 설치 도구 기록(`engine_toolchain_identity`)에 넣는다.

#### 설치 engine과 toolchain

설치 도구 기록은 `engine_version`, `engine_executable`, `compiler`, `linker`, `build_tool`만 가진다.

- `engine_version`은 설치 engine의 exact build/version text다.
- `engine_executable`은 파일 명세 하나다.
- `compiler`, `linker`, `build_tool`은 실제 호출한 파일들의 비어 있지 않은 명세 배열이다.
- 각 명세는 `installed_path`, `size_bytes`, `sha256`, `version`을 가진다.
- `installed_path`는 운영자가 관찰한 실제 설치 경로다. 제출 묶음의 파일 경로를 해석하는 기준으로 사용하지 않는다.

설치된 engine과 toolchain은 신뢰 전제다. 이 기록의 범위는 수집에 사용한 설치 도구의 식별이다. engine 전체의 재현 가능한 빌드를 증명하는 범위까지 확대하지 않는다.

### 3.3 시작 시 검사와 과거 import

**수집 실행은 준비한 고정 빌드를 사용하는 운영 규칙으로 관리한다.** 신뢰한 로컬 운영자는 수집 프로세스에 Live Coding·hot reload를 적용하지 않는다. 코드를 변경해 적용하려면 수집을 종료하고 새 빌드로 새 세션을 시작한다.

이 규칙은 관리된 로컬 수집을 전제로 한다. 관리자나 같은 프로세스의 임의 코드가 실행을 변조하는 경우까지 인증하는 계약은 아니다. 엔진 내부 모든 순간의 상태 관측을 시작 조건으로 두지 않는다. 기존의 연속 상태 감시 요구는 이 절로 교체한다.

#### 새 수집을 시작할 때

1. 준비한 binary와 source snapshot을 외부 빌드 확인값·기록과 연결한다.
2. 신뢰한 실행기가 별도 Development Game 프로세스를 시작한다. 기존 Editor 프로세스를 재사용하지 않는다.
3. 실제 EXE와 필요한 project module의 경로·크기·digest를 build receipt와 비교한다.
4. OS의 프로세스 시작 식별값을 기록한다. 같은 PID의 재사용과 구별한다.
5. 실제 실행 인수·설정에서 Live Coding 비활성 실행을 확인한다. 이미 로드된 상태 API가 있으면 알려진 활성화·컴파일 상태를 확인한다. 조회를 위해 모듈을 새로 로드하지 않는다.
6. 실제 patch나 hot-reload 실행이 확인되면 시작을 거부한다. 운영 규칙과 모순되는 관측은 성공 기록으로 남기지 않는다.

같은 빌드를 재사용해도 실행 번호와 세션 번호는 새로 만든다. 실제 새 프로세스의 시작 정보를 기록한다. 원래 빌드 준비 기록의 `run_id`는 빌드를 만든 실행을 가리킨다. 현재 통신의 `run_id`는 이번 수집 실행을 가리킨다. 두 번호의 동일성 대신 원래 빌드 기록의 식별과 이번 프로세스·세션의 연결을 각각 확인한다.

새 시작 기록과 실행 로그는 이전 파일과 다른 위치에 저장한다. 이전 세션의 시작·종료 기록을 복사해 새 실행의 관측으로 사용하지 않는다. 원래 빌드 기록과 그 digest는 유지한다.

게임이 실행 중 만드는 설정·로그는 고정 빌드 입력과 구분한다. 현재 cook 배치에서는 준비 프로젝트의 `Saved/Cooked/Windows/NeuralGame/Saved/`를 cook 입력 목록에서 제외한다. 준비 도구, 재사용 실행기와 게임은 같은 범위를 제외한다. 다른 cook 자료와 전체 stage 목록의 경로·내용 대조는 유지한다.

전체 cook 목록의 자료 이름은 문법과 원본·cook·stage 경로의 대응으로 확인한다. 현재 Game에 해당 자료의 경로가 등록되어 있는지는 전체 목록의 형식 조건으로 사용하지 않는다. 선택한 맵의 의존 자료와 실제 로드한 자료의 cook 대응 확인은 유지한다. 사용하지 않는 플러그인을 이 검사 때문에 활성화하지 않는다.

실행기는 새 프로세스의 초기 파일 확인 완료를 최대 60초 기다린다. 이 대기는 회차 시작 전의 실행 준비에 해당한다. 회차 준비 제한 10초와 기존 40ms 제한은 유지한다. 기존 메시지·파일 형식과 세션 연결 조건은 바꾸지 않는다.

자동 실행의 세션 예약 응답과 시작 기록 전송 뒤의 준비 완료 응답은 각각 최대 10초 기다린다. 응답이 없으면 오류를 반환한다. 사람의 시작 명령을 기다리는 시간에는 이 제한을 적용하지 않는다. 새 세션·회차 번호는 기존 UUIDv4 규칙에 맞게 생성한다. 외부 입력과 이미 저장한 번호를 자동으로 보정하지 않는다.

실행기·수집기는 실제 프로세스와 빌드 기록의 대응을 확인한다. 제출된 `cold_start=true`나 임의 digest만으로 이를 대신하지 않는다. 다만 Live Coding 모듈·조회 API 부재, `Starting` 미구별, 틱 사이 모든 변화의 미관측은 시작 거부 사유가 아니다. helper 프로세스의 시작 자체도 patch 적용 사실로 취급하지 않는다.

일반 DLL·asset load/unload와 무관한 개발 폴더 변경은 코드 교체로 분류하지 않는다. 전역 module epoch 변경이나 전체 파일 트리 변경만으로 세션을 실패시키지 않는다. 수집 프로세스에 실제 코드 변경·컴파일·패치가 확인되면 해당 세션을 실패 처리하고 완료 확인값을 발행하지 않는다.

#### 시작 기록의 필드

시작 기록(`session_start_evidence`)은 다음 필드를 가진다.

| 구분 | 필드 |
|---|---|
| 형식 | `format`, `version` |
| 수집과 빌드 연결 | `session_id`, `runtime_build_evidence_sha256` |
| 실제 프로세스 | `process_id`, `process_start_identity`, `launch_argv` |
| 실행 파일과 로드 목록 | `executable`, `loaded_module_inventory` |
| source와 관측 기록 | `source_inventory`, `loader_log` |
| 코드 교체 기능의 상태 | `live_coding_state`, `hot_reload_state` |

`process_start_identity`는 OS가 제공한 프로세스 시작 식별값이다. `live_coding_state="disabled"`와 `hot_reload_state="disabled"`는 실제 실행의 비활성 설정과 해당 기능을 사용하지 않는 운영 규칙을 나타낸다. 모든 상태 변화를 감시했다는 인증값이 아니다. 실제 설정·관측 사실·운영 전제는 기존 `launch_argv`와 `loader_log`에 구분해 남긴다. closed Schema에 새 상태 필드를 추가하지 않는다.

수집 화면에서 시작을 기다리는 실행은 `launch_argv` 끝에 `-ANPCCollectionUI`를 포함할 수 있다. 실행기 옵션은 `--collection-ui`다. 원래 인수열 또는 이 인수가 끝에 한 번 추가된 인수열만 허용한다. 실제 프로세스 인수와 기록의 일치는 유지한다. 이 옵션은 시작 대기 방식만 바꾼다. 준비할 때 정한 입력 출처·입력 주체·실행 방식과 학습 승인은 바꾸지 않는다.

시작 기록의 형식은 유지한다. Runtime 연결의 코드 작성과 실제 실행 확인은 구분한다. 현재 구현 범위는 [일반 플레이 수집 구현계획](scenario-collection-play-session-index-v1-implementation-plan.md)을 따른다.

#### 보관된 과거 수집 자료를 가져올 때

과거 자료 가져오기(`offline historical import`)는 당시 보관한 source, binary, receipt, 시작 기록과 외부 완료 확인값을 사용한다. 이 고정된 과거 완료 묶음(`pinned historical closure`)을 확인한다.

현재 설치된 다른 binary로 과거 결과를 재해석하지 않는다. 현재 source hash를 과거 값에 덮어쓰지도 않는다. 과거 산출물이 없거나 decoder가 해당 의미 계약을 지원하지 않으면 거부한다.

당시 설치·로드 상태는 신뢰한 수집기가 남긴 기록으로 확인한다. 현재 설치 상태 확인은 새 수집 세션을 시작할 때 수행한다.

<!-- P2:source-enum -->
## 4. Capture에서 Snapshot으로의 정확한 변환

변환은 기존 decoder가 확인한 원본 bytes와 값의 의미를 보존한다.

입력은 `decode_committed_capture_bytes`가 검증한 같은 bytes의 payload다. 별도 parser를 추가하지 않는다.

원본 source enum(`EDecisionRecordSourceType`)의 대응은 다음과 같다. 수집 모드는 raw `2/Dagger`를 요구한다. 이 값은 원본의 기록 분류이며 정답 승인 권한과 구분한다.

| 저장된 source 값(`source_type`) | Runtime enum | Snapshot 값(`source_type`) |
|---|---|---|
| `0` | `Silver` | `silver` |
| `1` | `Gold` | `gold` |
| `2` | `Dagger` | `dagger` |

<!-- P2:field-mapping -->
### 4.1 identity·label·부가 metadata

가져오기 도구는 원본 입력과 정답 후보를 보존한 Snapshot을 만든다.

고정 정책은 다음과 같다.

- Snapshot 버전은 `snapshot_version="anpc_decision_snapshot_v1"`이다.
- 범위는 `scope="production_candidate"`다.
- 원본 wire에 없는 가중치는 `source_weight=0.0`으로 둔다.
- 판단 보류(`abstain`)는 `len(acceptable_candidate_indices) == 0`으로만 계산한다.
- 허용 후보 목록을 지워 판단 보류를 만들지 않는다.

Snapshot manifest는 기존 `anpc_snapshot_manifest_v1` 형식을 사용한다. `production_eligible=false`를 유지한다. `profile_sha256`에는 수집 실행 설정 digest를 넣는다. exact shard bytes와 row·source·family 개수를 함께 연결한다. 여기서 source 개수는 원본 enum의 집계다. 승인된 Gold 정답 수와 구분한다.

#### 원본 필드 대응

| 원본 decoder 또는 확인된 완료 묶음의 필드 | Snapshot 필드 | 변환 규칙 |
|---|---|---|
| `episode_id` | `episode_id` | exact text를 보존한다. 수집 회차 UUID와 구분한다. |
| `decision_id` | `decision_id` | exact uint64를 보존한다. |
| `captured_at_server_time` | `captured_at_server_time` | 원본의 유한 float64다. wall-clock으로 바꾸지 않는다. |
| `scenario_family_id` | `scenario_family_id` | 원본 text를 보존하고 episode/catalog와 대조한다. |
| `episode.family.template_family` | `template_id` | 고정된 catalog와 같은 exact text다. 원본 wire 밖에서 얻은 값으로 기록한다. |
| `generator_version` | `generator_template_version` | 원본 text를 보존한다. |
| `map_seed` | `map_seed` | exact uint64를 보존하고 확정된 episode와 대조한다. |
| `simulation_seed` | `simulation_seed` | exact uint64를 보존하고 확정된 episode와 대조한다. |
| `candidate_bytes` | `candidate_set_canonical_bytes` | 같은 bytes를 standard base64 ASCII로 인코딩한다. |
| `candidate_set_hash` | `candidate_set_hash` | 원본 digest와 다시 계산한 값이 같아야 한다. |
| `input_content_hash` | `input_content_hash` | 원본 digest와 다시 계산한 값이 같아야 한다. |
| `feature_contract_hash` | `feature_contract_hash` | 원본 digest와 생성된 의미 계약이 같아야 한다. |
| `switch_cost_terms` | `switch_cost_terms` | 272×4 exact bool과 항목 순서를 보존한다. |
| `captured_switch_cost` | `captured_switch_cost` | 272개 float32 값을 보존한다. 다시 pack한 bytes가 같아야 한다. |
| `target_handles` | `target_handles` | 17개 `{kind,stable_id,generation,revision}`의 exact unsigned integer와 slot 순서를 보존한다. |
| `labels.acceptable_candidate_indices` | `acceptable_candidate_indices` | 정렬된 exact indices를 보존한다. |
| `labels.preference_pairs` | `preference_pairs` | 원본 ordered pair 배열을 보존한다. |
| `labels.parameter_target_norm` | `parameter_target_norm` | 272×4 flattened float32 값을 보존한다. |
| `labels.parameter_label_mask` | `parameter_label_mask` | 272×4 flattened bool을 보존한다. |
| `labels.selected_is_acceptable` | `selected_is_acceptable` | 원본 bool/null을 보존한다. 선택 결과를 추측하지 않는다. |
| `labels.label_confidence` | `label_confidence` | 원본 float32 값을 보존한다. |
| `labels.reason_tags` | `reason_tags` | 원본 canonical 순서와 text를 보존한다. |
| `prompt_version` | `prompt_or_teacher_version` | 빈 문자열을 포함한 원본 text를 보존한다. |
| `parent_policy_hash` | `parent_policy_sha256` | optional hash의 빈 문자열만 `None`으로 바꾼다. 나머지 digest는 그대로 둔다. |

#### Snapshot과 원본 보관 정보의 구분

부모 정책 digest(`parent_policy_sha256`)는 Snapshot의 추가 출처 정보로 허용한다. Dataset의 기존 같은 필드로 전달한다.

가져오기 목록(`import index`)의 원본 보관 항목(`raw_capture`)에는 다음 값을 연결한다.

- 원본 `sample_id`, `label_block_hash`, `selected_candidate_index`, `record_version`.
- 원본 `annotator_set_hash`, `annotator_agreement`.
- 원본 input/label CBOR.
- 정규화 전 optional hash 문자열.
- 원본 source enum, group 배열, generator/prompt text와 그 밖의 원본 값.

빈 annotator hash도 그대로 보존한다. 임의 digest를 채우지 않는다. Snapshot 소비자가 쓰지 않는 원본 필드를 새 Dataset column으로 만들지 않는다.

binary blob은 standard base64 ASCII로 저장하고 파일 명세의 원본 bytes와 대조한다. 가져오기 목록은 Capture/sample 식별자와 Snapshot shard digest, row 순번·식별자를 연결한다.

각 metadata가 원본 wire, 완료 묶음, 가져오기 정책 중 어디서 왔는지 기록한다. row에 없는 선택값을 새 정답으로 추정하지 않는다. 정답·출처·가중치 변경을 입력 보존으로 보고하지 않는다.

#### 정답 승인 뒤의 sample 식별자

정답 승인 뒤에는 기존 규칙으로 새 Dataset sample 식별자를 계산한다.

```text
sample_id(input_content_hash, episode_id, decision_id, label_block_hash)
```

파생 목록(`derived index`)은 원본 sample과 새 정답을 가진 sample을 각각 연결한다. 원본 sample ID는 유지한다.

Dataset manifest의 `generation_code_sha256`는 변환에 사용한 ML 코드의 식별자다. row의 Runtime build digest는 원본 생산 코드의 식별자다. 두 값을 서로 대신 넣지 않는다.

<!-- P2:groups -->
<a id="42-여덟-group의-wire-순서"></a>
### 4.2 여덟 상황 분류의 저장 순서

상황 분류는 원본의 여덟 위치를 같은 순서로 복사한다. scenario family는 별도 필드다.

| 원본 위치 | Snapshot 필드 |
|---|---|
| `group_dimensions[0]` | `map_family` |
| `group_dimensions[1]` | `occlusion_layout_family` |
| `group_dimensions[2]` | `goal_sequence_family` |
| `group_dimensions[3]` | `role_id` |
| `group_dimensions[4]` | `personality_cluster_id` |
| `group_dimensions[5]` | `perception_modality_family` |
| `group_dimensions[6]` | `target_composition_family` |
| `group_dimensions[7]` | `event_sequence_family` |

catalog의 family 이름을 위 위치에 임의로 재배치하지 않는다. 필수 생산 정보가 비었거나 실제 phase·Role과 충돌하면 수집 또는 가져오기를 거부한다. 기본값으로 수선하지 않는다.

<!-- P2:tensors -->
### 4.3 Tensor blocks

Tensor는 원본 block bytes와 해석된 값 배열을 모두 보존한다.

`tensor_blocks[i]`와 Snapshot의 `tensor_order`는 아래 `TENSOR_ORDER` 및 생성된 `MODEL_INPUT_NAMES` 순서를 따른다.

| 순서 | 이름 | dtype | batch 축을 뺀 shape |
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

원본 block은 `tensors[name]={dtype,shape,data_base64}`에 그대로 인코딩한다.

최상위의 같은 이름 값 배열은 little-endian float32/int64 또는 0/1 bool로 decode한 row-major flattened 값이다. shape에서는 batch 축만 뺀다.

`decode_tensor`와 `encode_tensor`로 왕복한 결과는 `tensor_block_bytes`와 byte-for-byte로 같아야 한다. 재정규화나 float smoothing은 수행하지 않는다.

<!-- P2:contract-metadata -->
### 4.4 contract hashes와 semantic versions

계약 hash는 원본 위치와 확인된 의미 계약의 대응을 유지한다.

| 원본 위치 | Snapshot 필드 | 확인 기준 |
|---|---|---|
| `contract_hashes[0]` | `schema_sha256` | 고정된 생성 의미 계약 |
| `contract_hashes[1]` | `skill_registry_sha256` | 고정된 생성 의미 계약 |
| `contract_hashes[2]` | `goal_registry_sha256` | 고정된 생성 의미 계약 |
| `contract_hashes[3]` | `target_slotter_sha256` | 현재 지원 계약의 schema digest |
| `contract_hashes[4]` | `normalization_sha256` | 현재 지원 계약의 schema digest |
| `contract_hashes[5]` | `postprocess_sha256` | 현재 지원 계약의 schema digest |
| `contract_hashes[6]` | `generator_or_runtime_build_sha256` | 외부 `runtime_build_evidence_sha256` |
| `contract_hashes[7]` | `source_decision_contract_hash` | 빈 문자열만 `None`으로 바꾼다. 값이 있으면 원본 digest를 보존한다. |

#### 의미 버전의 취득원

의미 버전 필드는 원본 wire에 없다(`absent from wire`). 고정된 생성 계약에서 가져온다. 먼저 원본 wire의 digest와 그 생성 계약의 digest가 같은지 확인한다.

| Snapshot 필드 | 생성 계약의 값 |
|---|---|
| `schema_version` | `SCHEMA_VERSION` |
| `schema_revision` | `CONTRACT_REVISION` |
| `skill_registry_version` | `CONSTANTS["skill_registry_version"]` |
| `goal_registry_version` | `GOAL_REGISTRY_VERSION` |
| `target_slotter_version` | `CONSTANTS["target_slotter_version"]` |
| `normalization_version` | `CONSTANTS["normalization_version"]` |
| `postprocess_version` | `CONSTANTS["postprocess_version"]` |

기존 `contract_metadata()`의 의미 검사는 유지한다. 전체 값을 덮어쓰지 않는다. build와 optional source-decision 값만 출처 확인 컨텍스트가 확인한 원본 값으로 판단한다.

`raw_capture.contract_hashes`에는 빈 문자열도 그대로 남긴다. `feature_contract_hash`는 기존 `ANPCFEAT1`과 여섯 raw digest 규칙으로 다시 계산한다. 지원하지 않는 의미 계약은 거부한다.

#### 수집 전용 기록의 이름과 표식

수집 생산자는 모든 phase에 아래 규칙을 적용한다.

- Capture의 회차 이름(`episode_id`): `scenario_capture_<session UUID>_<collection episode UUID>_<process sequence>`.
- process sequence: 0이 아닌 20자리 unsigned decimal.
- 생성 버전(`generator_template_version`): `neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1`.
- reason tag: `scenario_collection_utility_unreviewed` 포함.

원본 build, namespace, tag, family, seed와 실제 group·phase를 완료 묶음과 대조한다. 기존 일반 플레이·fixture namespace는 소급 변경하지 않는다. tag만으로 발행 권한을 부여하지 않는다.

<!-- P3:policy-lineage -->
### 4.5 독립적인 정책 lineage

판단 계약과 부모 정책은 서로 다른 원본 이력이다.

- 원본 판단 계약: `source_decision_contract_hash`.
- 원본 부모 정책: `parent_policy_sha256`.

정규화 뒤에는 다음 네 조합을 Snapshot, annotation mapping, 최종 Dataset에서 그대로 보존한다.

| 원본 판단 계약 | 원본 부모 정책 | Dataset의 `source_decision_contract_hash` | Dataset의 `parent_policy_sha256` |
|---|---|---|---|
| `None` | `None` | `None` | `None` |
| `S` | `None` | `S` | `None` |
| `None` | `P` | `None` | `P` |
| `S` | `P (S != P)` | `S` | `P` |

Runtime 전용 `_annotation_provenance`는 판단 계약을 부모 정책의 대체값으로 사용하지 않는다(`no source-decision fallback`).

- annotation에 parent field가 없으면 컨텍스트가 확인한 원본 parent 값을 사용한다.
- parent field가 있으면 `None`도 명시된 값으로 비교한다.
- 명시된 값이 원본과 다르면 거부한다.

Teacher나 사람이 정답을 붙여도 원본 rollout policy 이력은 유지한다. 두 digest가 우연히 같아도 각 필드의 출처를 따로 확인한다.

<!-- R2:labels -->
## 5. Teacher와 Human label 발행 권한

정답 권한은 허용된 실행·검토 주체가 실제로 남긴 완료 기록에서 얻는다.

### 5.1 기존 경로와 새 Runtime-only 권한

기존 `gold.py`의 queue parser와 decision join은 자료 간 일관성을 확인한다. version marker와 Snapshot hash를 맞춘 손작성 대기열도 이 검사를 통과할 수 있다.

검토자 ID의 nonempty/NFC/sorted 검사는 표기 검사다. 검토자의 권한 확인은 별도다. 기존 Teacher mapper의 요청·원본 응답 재구성도 실제 provider 실행의 증명과 구분한다.

#### Teacher 권한에 필요한 근거

Runtime 정답 factory는 다음 근거를 같은 불변 bytes로 재구성한다.

**1. 허용된 입력과 Teacher 설정**

가져오기 권한을 확인한 Snapshot과 별도로 허용한 Teacher 설정 digest(`permitted_teacher_profile_sha256`)를 사용한다.

다음 내용을 연결한다.

- 설정의 exact YAML.
- prompt와 요청·응답 Schema.
- provider 유형, model identifier, revision과 decoding 설정.

허용 목록은 소유자가 운영하는 Teacher 절차에서 얻는다. 공개 Profile 이름이나 `provider.type=command`라는 값만으로 권한을 부여하지 않는다.

**2. 모델에 실제 전달한 요청**

기존 `build_teacher_request`가 모델용으로 구성한 exact request를 사용한다.

모델 입력에는 collection 설명, 미래 사건, 기대 행동, Utility 정답 후보와 sidecar 전체를 넣지 않는다.

**3. 다섯 번의 원본 호출 기록**

다섯 번의 원본 시도(`all five raw attempts`)를 모두 보존한다.

- 실제 bytes.
- 순서와 call index.
- hash와 path.
- provider 호출 결과와 `provider_error`.

실패한 호출도 보존한다. 현재 generator가 오류 호출을 빈 response로 consensus에 전달하는 규칙을 그대로 재구성한다. 오류 호출의 원본 stdout bytes는 별도로 보존한다.

**4. 합의와 검토 분기 재구성**

같은 `aggregate_responses`로 응답 형식, 합의 결과, confidence와 검토 분기(`review-routing`)를 다시 계산한다.

학습 annotation과 검토 대기열을 모두 exact 비교한다. 낮은 confidence, 충돌, 응답 부족으로 검토에 보낸 row를 임의로 학습 row로 바꾸지 않는다. 합의 알고리즘은 기존 것을 유지한다.

**5. Teacher 실행의 외부 완료 확인값**

신뢰한 Teacher runner는 다음 자료를 완료 묶음으로 발행하고 다시 읽어 확인한다.

- 요청과 모든 원본 시도.
- annotation과 검토 대기열.
- 원본 Snapshot shard와 manifest.
- 가져오기 목록.
- 허용된 Teacher 설정.

runner는 소유자 저장소에 Teacher 실행 완료 확인값(`teacher_run_completion_pin`)을 예치한다. 호출자는 이를 `independent_out_of_band`로 얻는다.

최소 완료 기록(receipt)은 각 파일 명세, provider/profile 식별자와 호출 결과를 묶는다. 그 exact receipt digest를 외부에 고정한다. 제출한 응답과 대기열을 다시 hash해도 원래 실행 확인값을 대신할 수 없다. bundle 내부의 `expected`나 `approved` 값은 권한 입력으로 허용하지 않는다.

#### Teacher 결과의 사용 범위

정답 권한에는 자료 재구성과 실제 실행의 발행 근거가 모두 필요하다.

허용된 실제 provider 또는 실행 확인값이 없으면 Runtime row는 다음 상태로 남는다.

```text
label_status=utility_unreviewed
source_weight=0.0
training_eligible=false
```

성공한 Teacher 합의 결과만 새 `silver/0.25` Dataset row로 변환한다. 원본 Utility의 `Dagger` 표기와 선택 결과만으로 전문가 correction이나 `dagger/1.0` row를 만들지 않는다.

### 5.2 Human Gold의 추가 권한

V1 사람 검토는 확인된 Teacher 실행에서 재구성한 검토 대기열을 입력으로 사용한다. Capture에서 사람 대기열로 바로 가는 새 경로는 포함하지 않는다.

기존 decision·label·parameter 검사는 유지한다. 별도의 소유자 검토 절차는 허용된 검토자의 실제 결정을 확인한다. 다음 값을 소유자 저장소에 발행한다.

| 근거 | 연결할 값 |
|---|---|
| 결정 파일 | YAML 원본 exact bytes의 `decision_set_sha256` |
| 결정이 참조한 자료 | `review_queue_sha256`, `snapshot_shard_sha256`, `snapshot_manifest_sha256` |
| 이전 발행 근거 | Teacher 실행 완료 확인값, Runtime 가져오기 목록, 수집 완료 항목 식별자 |
| 검토자 권한(`reviewer_authorization`) | 소유자가 허용한 reviewer principal 목록, 정확한 결정 묶음과 원본 자료에 대한 결정 권한, 해당 절차의 기록 식별자 |

검토자 권한은 decision YAML에 적힌 검토자 목록과 별도로 얻는다.

위 내용을 묶은 사람 검토 완료 항목에서 `human_review_completion_pin`을 독립적으로 취득한다. 실제 승인된 결정 묶음과 검토자 목록이 exact 일치할 때만 새 `gold/1.0` row를 만든다. 오류, 누락과 권한 불일치는 거부한다.

파일에 reviewer 이름을 적거나 이름 배열을 hash한 것만으로 Gold 권한을 부여하지 않는다(`reviewer_id text is insufficient`).

#### 새 프로세스에서 이어받기

새 프로세스는 아래 근거를 다시 취득하고 재구성한다.

- 수집·가져오기 완료 묶음.
- 허용된 Teacher 설정.
- Teacher 실행 완료 확인값, 원본 시도와 검토 대기열.
- 사람 검토 완료 확인값, 결정 파일, 원본 자료와 검토자 권한.

이전 프로세스의 bool이나 직렬화한 권한 객체를 복원하지 않는다. 이 신뢰는 소유자 절차와 runner의 정직한 발행을 전제로 한다. 외부 암호 서명 서비스의 신원 증명을 제공하지 않는다.

#### 과거 Gold 보존

과거 Gold(`historical Gold`)의 기록 수와 사용자 결정은 유지한다. 기존 자료를 삭제하지 않는다. 이 문서만으로 새 사람 승인을 부여하지도 않는다(`no new human approval`).

기존 일관성 검사는 암호학적 인증 결과가 아니다(`not cryptographically authenticated`). 과거 자료를 새 Runtime 권한 기준으로 소급 인증한 Gold라고 표시하지 않는다. 과거 데이터에 대한 사용자의 판단과 새 Runtime 자료의 권한은 구분한다.

<!-- R2:fixtures -->
### 5.3 fixture provider와 테스트 산출물

fixture는 정해진 테스트 입력과 결과를 사용하는 격리된 검사 자료다. 실제 Teacher나 사람의 승인 자료와 구분한다.

기존 `load_teacher_profile`은 `replay_fixture`를 `integration_fixture` Profile로 제한한다. 현재 generator는 Profile 범위와 원본 Snapshot 범위의 동일성을 보장하지 않는다.

새 Runtime 경로는 fixture 응답의 정답 권한 부여를 거부한다(`reject Runtime candidate label authorization`). 원본이 `production_candidate`여도 같은 규칙을 적용한다. fixture Profile을 잘못 넣은 원본 Runtime Snapshot은 Utility 미검토·가중치 0 상태를 유지한다.

#### fixture 결과의 표시

fixture 실행은 격리된 integration 테스트에서만 허용한다. 외부 권한 보고서는 다음 상태를 사용한다.

```text
authorization_status=fixture_only
label_authorized=false
training_eligible=false
```

실제 provider나 사람이 실행했다고 보고하지 않는다. 불변 원본 Snapshot의 scope를 덮어쓰지 않는다. fixture용 입력 복사본은 원본 digest와 테스트 목적을 외부 테스트 기록에 연결한다.

#### Dataset 형식 보존

Dataset v2의 필드 집합과 가중치는 테스트에서도 유지한다.

- Silver fixture Dataset은 `silver/0.25`를 사용한다.
- Gold 형식 fixture는 `gold/1.0`을 사용한다.
- 가중치 0인 새 Dataset 형식은 만들지 않는다.
- 가능한 경로는 `integration_fixture` scope를 사용한다.

legacy Gold loader처럼 `production_candidate`만 받는 기존 API의 합성 회귀는 기존 scope로 실행할 수 있다. 외부 fixture 보고서와 격리된 test root를 명시한다. 새 Runtime 권한 채택에서는 이 결과를 거부한다.

scope 문자열은 테스트 형식의 일부다. 실제 정답 권한은 별도다. fixture 권한과 테스트 runner가 만든 가짜 확인값은 실제 권한 구역으로 가져오지 않는다.

<!-- P4:context-api -->
## 6. Context API와 불변 lifecycle

출처 확인 컨텍스트는 §2–5의 factory가 확인한 원본·정답 정보를 소유하는 불변 객체다.

컨텍스트의 코드 이름은 `RuntimeProvenanceContext`다. 임의 JSON의 `allow_runtime`, flag나 hash 목록으로 만들지 않는다. 신뢰한 프로세스 내부의 임의 코드 실행 위협은 §2.2의 제외 범위다.

컨텍스트는 외부 mutable dict와 내부 bytes·row·label을 공유하지 않는다. 다음 내용을 함께 연결한다.

- row 식별자.
- Tensor와 Candidate.
- mask와 switch facts.
- 모든 group과 시각.
- 원본 정답 후보와 출처 정보.

### 6.1 공통 API 인수

관련 경로는 keyword-only 인수 `origin_context=None`을 사용한다.

기존 `_base_record`의 세 번째 positional 인수 `provenance`는 label metadata mapping으로 유지한다. 같은 이름의 새 인수를 추가하지 않는다.

아래는 목표 API 형식이다.

```python
def validate_snapshot_row(row, *, origin_context=None): ...
def read_snapshot_shard_bytes(shard_bytes, manifest_bytes=None, *, shard_filename=None, origin_context=None): ...
def read_snapshot_shard(path, manifest_path=None, *, origin_context=None): ...
def _base_record(snapshot, labels, provenance, *, origin_context=None): ...
def _validate_record(record, *, origin_context=None): ...
def validate_dataset_shard(parquet_path, manifest_path, *, require_production=False, origin_context=None, require_authorization=False): ...
```

다음 경로는 기존 positional·keyword 인수를 유지하면서 `origin_context`를 명시적으로 전달한다.

- Teacher의 request, generate, authenticate, mapper.
- Gold의 immutable bundle, promote, authenticate, map.
- Dataset의 mapping-input, base-record, record, write, final-validation.

`origin_context=None` 호출은 §7의 구조 검사를 수행한다. 전달된 컨텍스트가 불일치하면 실패한다. 컨텍스트를 빼고 구조 검사로 낮추어 재시도하지 않는다.

### 6.2 가져오기부터 최종 발행까지

컨텍스트는 실제로 완료한 단계의 범위만 허용한다.

**1. 원본 가져오기 승인(`import-authorized`)**

완료 확인값과 과거 완료 묶음 확인 → 같은 Capture bytes decode → §4 Snapshot 재구성 → 새 Snapshot·manifest readback → 가져오기 목록 발행 순서다.

가져오는 도중의 임시 컨텍스트는 원본 bytes와 정규화 row를 연결한다. 발행된 가져오기 목록까지 확인한 컨텍스트는 Snapshot shard와 manifest digest도 연결한다. 이 단계에는 정답 권한이 없다.

**2. 정답 승인·발행 전(`label-authorized prepublication`)**

원본 가져오기 컨텍스트와 §5의 독립 Teacher·사람 근거를 사용한다. exact annotation, row 식별자, 정답과 가중치를 연결한다.

매핑 전에는 미래 Dataset의 hash를 요구하지 않는다(`Dataset hash not required before mapping`). 이 단계의 컨텍스트는 매핑과 발행 전 최종 readback 검사에만 사용한다.

**3. 최종 파생 목록 발행(`final-derived-index`)**

정답 승인 컨텍스트로 Dataset과 manifest를 새 경로에 작성한다. 같은 bytes를 공개 검사기 `validate_dataset_shard`로 확인한다.

완료된 Dataset·manifest, 이전 가져오기 목록, 정답 근거의 파일 명세를 새 파생 목록에 넣는다. 파생 목록을 마지막에 발행한다(`publish derived index last`). 후속 단계는 이 최종 파생 목록에 연결된 컨텍스트·권한 결과만 채택한다.

### 6.3 재구성과 재사용 제한

원본 가져오기 목록과 파생 목록은 append-only로 관리한다. 기존 Dataset manifest의 `snapshot_manifest_sha256`를 원본 연결점으로 사용한다.

파생 목록은 자신의 hash를 담지 않는다. 발행 전 컨텍스트도 미래 Dataset hash를 요구하지 않는다.

최종 컨텍스트는 확인된 원본·정답 근거로 출력 bytes를 다시 구성해 대조한다. 제출된 파생 목록을 다시 hash한 것만으로 권한을 얻지 못한다.

새 프로세스는 root, 외부 수집·정답 완료 확인값, 가져오기·파생 목록의 exact bytes로 각 단계를 재구성한다. 다음 입력은 거부한다.

- 다른 row의 식별자만 복사한 컨텍스트.
- 같은 식별자의 정답을 변경한 자료.
- 교체된 최종 파일.
- 이전 파일에 대한 낡은 결과.

procedural 출처는 §7.3의 독립 재생성 factory를 사용한다. 같은 명시적 권한 인터페이스를 제공하되 Runtime 컨텍스트로 위장하지 않는다.

<!-- R3:public-acceptance -->
## 7. Public final validator의 acceptance 경계

공개 최종 검사기는 구조 검사와 사용 권한 확인을 구분해 반환한다.

### 7.1 proofless 호출의 의미

외부 출처 확인 컨텍스트가 없는 기본 호출(`origin_context=None`)은 구조와 일관성만 검사한다(`STRUCTURE/CONSISTENCY ONLY`). 기존 호출 형식과 의미 검사는 유지한다.

기존 procedural·Teacher·Gold 호출의 성공을 원본 출처 인증으로 격상하지 않는다. Runtime 표식, episode, build, label과 manifest를 모두 고치고 다시 hash한 Gold는 구조적으로 유효할 수 있다. 기본 검사기는 지워진 모든 출처를 식별한다고 보장하지 않는다.

기존 summary의 `row_count`, `source_counts`, `group_counts`와 source·weight·label 주장은 선언값 또는 구조적으로 재구성한 값이다. bytes에서 다시 센 개수도 인증된 Gold 수나 학습 준비 상태와 구분한다. 구조상의 source 개수와 권한이 확인된 row 개수에는 서로 다른 이름을 사용한다.

#### 별도 권한 결과

공개 검사기 `validate_dataset_shard`는 exact 최종 파일 bytes와 컨텍스트를 확인해 불변 권한 결과(`DatasetAuthorizationResult`)를 만든다.

기존 summary에 별도 `authorization` 항목을 제공한다. 상태와 flag는 레코드·manifest의 기존 필드 집합 밖에 둔다(`outside record/manifest exact-field sets`). 직렬화한 보고서는 읽기용이다. 권한 객체로 재사용하지 않는다.

| 상태 | 원본 권한 | 정답 권한 | 학습 자격 |
|---|---|---|---|
| 구조 검사만 완료(`structure_only`) | `origin_authorized=false` | `label_authorized=false` | `training_eligible=false` |
| 원본 가져오기만 확인(`origin_only`) | true | false | false |
| 격리 테스트 결과(`fixture_only`) | 실제 원본 권한 false | 실제 정답 권한 false | false |
| 원본·정답을 확인한 후보(`authorized_candidate`) | true | true | 별도 학습 조건 충족 시에만 true |

각 상태값은 `authorization_status`에 둔다.

원본만 확인한 Snapshot에는 Utility 정답 후보를 Dataset으로 만들 권한이 없다. 권한이 확인된 후보는 exact shard, manifest, 가져오기 목록, 파생 목록의 digest와 권한 항목 식별자를 함께 연결한다.

학습 자격(`training_eligible`)에는 다음 조건이 모두 필요하다.

- 원본과 정답의 유효한 권한.
- 기존 소유자 허용 데이터 품질 조건(data qualification).
- 필요한 scope, Profile, 데이터 분할과 coverage 조건.

품질 조건의 근거가 없으면 권한이 확인된 후보도 `training_eligible=false`다. 이 계약은 새 qualification 정책이나 학습기를 구현하지 않는다. 새 수집 자료는 허용된 정답 권한과 qualification을 확보할 때까지 false를 유지한다. 모든 경우 collection의 `production_eligible=false`도 유지한다.

### 7.2 강한 acceptance를 요청하는 호출

원본 가져오기 단계는 원본 권한만 요구한다(`import acceptance requires origin_only`). 확인된 미검토 Snapshot을 검토 입력으로 만드는 단계까지 허용한다. 아직 수행하지 않은 Teacher·사람의 미래 정답은 요구하지 않는다.

Runtime Dataset 매핑·최종 채택과 학습·qualification 채택에는 원본과 정답의 권한이 모두 필요하다.

최종 Dataset 권한 확인 호출은 다음과 같다.

```python
validate_dataset_shard(..., origin_context=context, require_authorization=True)
```

원본 또는 정답 권한 중 하나라도 유효하지 않으면 오류로 끝낸다. 호출자는 `require_authorization=False` 결과의 truthiness나 row count를 학습 준비로 받아들이지 않는다.

- qualification 입력 채택은 권한이 확인된 후보 결과를 요구한다.
- 실제 학습 채택은 별도의 qualification까지 요구한다.
- 근거 없는 위조 row는 학습 준비 완료로 처리하지 않는다(`proofless forged row never training-ready`).

#### 직접 호출과 발행 전 검사

공개 최종 검사기는 mapper를 거치지 않은 직접 호출에서도 모든 row를 확인한다.

확인 대상은 원본, 정답, source·weight, 원본 Snapshot·manifest와 파생 목록의 연결이다.

발행 전 검사는 정답 승인 컨텍스트에 연결된 정확한 변환 결과를 확인한다. 후속 단계가 사용할 권한은 최종 파생 목록까지 연결한 뒤 발행한다.

위조한 context/status dict와 이전 파일에 대한 결과는 권한 입력으로 받지 않는다. `require_production=True`는 이 권한 확인과 기존 Production 조건을 모두 요구한다. candidate와 fixture는 Production에서 계속 거부한다.

실제 승인 주체가 없으면 실제 긍정 사례를 실행했다고 보고하지 않는다. 격리된 합성 권한으로 재구성 경로를 시험한 결과는 fixture-only다. 실제 Teacher·사람·학습 증거로 집계하지 않는다. 실제 허용된 실행·검토 근거가 있는 경우만 실제 권한 채택의 성공 근거로 기록한다.

<!-- R3:procedural -->
### 7.3 procedural mapper의 독립적인 보강

procedural 매핑은 허용된 생성 설정과 코드로 원본 전체를 다시 만들어 확인한다.

`map_procedural_dataset`은 실제 procedural 생성 결과와 정확한 `silver/0.25`만 허용한다. Runtime 컨텍스트는 받지 않는다.

- 허용된 procedural Profile의 exact bytes와 digest를 사용한다.
- 허용된 generator source를 사용한다.
- row와 manifest 전체를 재생성해 입력과 대조한다.
- 기존 호출은 digest로 등록된 bundled Profile을 찾는다(`registered bundled profile`).
- custom Profile에는 명시적으로 고정한 경로와 digest가 필요하다.

임의 디렉터리를 탐색하거나 제출 Snapshot의 Profile 선언을 외부 기준으로 사용하지 않는다.

이 확인은 mapper에서 출처를 바꾸어 세탁하는 일을 막는다. 공개 최종 Dataset 검사의 범용 출처 증명을 대신하지 않는다.

공개 최종 채택용 procedural 컨텍스트도 같은 재생성과 결정적인 정답·출처·가중치 정책을 확인해야 한다. procedural Snapshot에 Teacher·사람 정답이 붙으면 원본 재생성과 §5의 정답 발행 근거를 각각 요구한다.

legacy의 근거 없는 Teacher·Gold 성공은 구조 검사 결과로 유지한다. 이 V1은 새 DAgger 정답 발행·승인 경로를 추가하지 않는다.

<!-- publication -->
## 8. 산출물·명령·발행 순서

가져오기 목록과 파생 목록은 원본 자료에서 최종 Dataset까지의 연결을 보존한다.

### 8.1 산출물

새 출처 Schema의 대상 파일은 `contracts/current/capture_import_provenance_v1.schema.json`이다. 가져오기 목록(`anpc_runtime_import_provenance_v1`)과 새 파생 목록을 정의한다.

기존 collection index와 Dataset v2의 필드 집합은 늘리지 않는다.

가져오기 목록은 다음 내용을 연결한다.

- 완료 묶음과 완료 확인값의 항목 식별자.
- parser와 importer의 exact source digest 및 version.
- 원본 Capture, sample, episode, decision과 input 식별자.
- §4의 원본-to-Snapshot 대응.
- Snapshot shard와 manifest 파일 명세.
- `scope=production_candidate`.
- `production_eligible=false`.
- `label_status=utility_unreviewed`.
- `training_eligible=false`.

파생 목록은 위 원본, 독립적인 정답 권한과 최종 Dataset·manifest를 연결한다.

### 8.2 목표 명령

아래 CLI는 구현 목표다. ML 작업 디렉터리는 `NeuralGame/ML`이다. 기존 `python -m anpc_ml`에 연결한다. 이 목록은 명령의 현재 구현 완료를 나타내지 않는다.

| 명령 | 입력과 결과 |
|---|---|
| `capture import` | root, 최종 수집 목록, 소유자 저장소에서 독립적으로 얻은 완료 확인값·묶음, catalog·수집 설정·build 확인값을 받아 Snapshot·manifest·가져오기 목록을 만든다. |
| `collection validate` | 같은 외부 기준과 불변 원본 묶음을 다시 확인한다. 구조 검사와 발행 권한 결과를 구분한다. |
| `collection coverage` | source별 시도, 진단, committed, 고유 model input, 중복, 관측 적합, 원본 정답 후보, 승인된 정답과 Dataset row를 따로 집계한다. |
| Teacher·Gold·Dataset 명령 | proof index/root와 독립적으로 얻은 수집·정답 완료 확인값을 신뢰한 호출 경로로 전달한다. |

새 권한 채택 명령은 공개 최종 검사기의 `require_authorization=True`를 강제한다. 기존 기본 validate 결과는 구조 검사 결과로 표시한다.

### 8.3 파일 발행

ML이 문서 저장소의 decoder·검사 도구를 읽을 때는 실제 의존 root와 source digest를 고정한다. import 오류를 가짜 parser로 대체하지 않는다.

1. 새 이름으로 산출물을 배타적으로 만든다.
2. 저장한 exact bytes를 다시 읽어 확인한다.
3. 각 단계의 목록을 마지막에 발행한다.

충돌이나 중간 실패가 생기면 기존 파일을 보존한다. 완료 목록·파생 목록은 발행하지 않는다. 저장 flag를 재사용해 부분 결과를 정상 자료로 처리하지 않는다.

<!-- regression-matrix -->
## 9. 먼저 실패시킬 회귀와 이 개정의 검증 범위

이 절은 후속 제품 코드가 거부하거나 허용해야 할 동작을 정한다.

문서 전용 검사는 문구·표·API 형식의 일관성을 확인한다(`document consistency tests`). 실제 Runtime/ML의 공격 차단 구현과 구분한다(`not executable security fixes`). 문서 검사의 통과를 제품의 동작 확인으로 표시하지 않는다.

아래 항목은 후속 실행 가능한 보안 검사(`executable security harness`)의 채택 기준이다. 검사 실행과 결과 판단의 담당은 사용자의 최신 작업 지침을 따른다.

| 사례 | 요구할 동작 |
|---|---|
| `R1-substitute-rehashed` | 공개 build/profile 값을 복사하고 Capture·marker·session·episodes·index 전체를 다시 작성·hash해도 원래 외부 목록 확인값과 완료 묶음에서 거부한다. 내부 expected 선언으로 우회하지 못한다. |
| `R1-trusted-publication` | 지정 생산자가 readback한 뒤 마지막에 발행한 목록과 같은 소유자 완료 묶음은 원본 가져오기 승인까지 허용한다. 목록만 같고 세션·회차가 바뀌면 거부한다. |
| `R2-forged-queue` | 손작성 대기열, 다른 Profile, 누락·재정렬한 원본 시도, provider_error 조작과 합의·검토 분기 교체를 거부한다. 전체를 다시 hash해도 독립 Teacher 실행 확인값에서 실패한다. |
| `R2-forged-reviewer` | reviewer_id와 결정·원본 hash만 맞춘 Gold는 소유자의 검토 권한이 없으면 거부한다. 결정·대기열·원본·허용 principal 교체도 거부한다. |
| `R2-fixture-candidate` | replay_fixture Profile과 production_candidate 원본의 조합에 실제 정답·학습 권한을 부여하지 않는다. 격리 fixture는 fixture_only와 false 상태를 유지한다. |
| `R2-authorized-teacher` | 실제 허용 Profile, runner 완료 확인값, 모든 원본 시도의 재구성과 학습용 합의 결과가 있으면 Silver 매핑부터 공개 최종 권한 확인까지 허용한다. 검토로 분기한 row는 제외한다. |
| `R2-authorized-human` | 확인된 Teacher 검토 근거와 독립적인 소유자의 결정·원본·검토자 권한이 있으면 Gold 매핑부터 최종 권한 확인까지 허용한다. 새 프로세스에서도 같은 결과를 얻는다. |
| `R3-public-proofless-forgery` | 출처를 지우고 전체를 다시 hash한 Gold는 기존 구조 호출에서 통과할 수 있다. 권한을 요구하는 채택에서는 거부한다. 학습 준비 완료로 처리하지 않는다. |
| `R3-public-authorized-origins` | 재생성한 procedural Silver, Runtime+허용된 Teacher Silver, Runtime+허용된 Human Gold의 정상 최종 컨텍스트를 각각 허용한다. 다른 row·파일 컨텍스트와 누락된 정답 근거는 거부한다. 실제 권한이 없는 긍정 시뮬레이션은 fixture-only로 보고한다. |
| `P1-cold-start-historical` | 고정 source·receipt·실행물의 불일치, incremental-only의 강제 빌드 위장, 실제 patch 적용, 재사용 프로세스와 bool-only 빌드 근거를 거부한다. 비활성 운영 설정의 정상 시작은 Live Coding 조회 부재·미관측 Starting·일반 DLL 로딩·무관한 개발 폴더 변경만으로 거부하지 않는다. 일치하는 과거 완료 묶음은 현재 설치가 달라졌다는 이유로 재해석하지 않는다. |
| `P2-full-parity` | 모든 Tensor·Candidate·handle·switch·label·group·identity와 원본 optional 값의 Snapshot 대응을 확인한다. 의미 버전의 원본 wire 부재, template 출처와 허용 후보 목록 보존을 확인한다. |
| `P3-four-policy-combinations` | null/null, value/null, null/value, 서로 다른 value/value를 exact 보존한다. 판단 계약을 부모 정책에 대신 넣으면 거부한다. |
| `P4-prepublication-lifecycle` | positional label metadata와 keyword-only origin_context 전달을 유지한다. Dataset digest 없이 발행 전 컨텍스트를 만들고 최종 bytes 확인 뒤 파생 목록을 발행한다. 새 프로세스 재구성에서 가변 값과 낡은 결과 치환을 거부한다. |

추가로 다음 동작을 유지한다.

- Capture·marker와 Snapshot·manifest의 single-read 및 ABA 치환 방어.
- 출처·가중치·정답을 모두 다시 hash한 자료와 procedural 재생성 불일치의 거부.
- 원본 Utility 기록을 procedural·Gold·Dagger 승인 자료로 승격하는 경로의 거부.
- Teacher 요청에서 숨겨진 scenario 정보와 Utility 정답 후보의 비간섭.
- 기존 procedural·Teacher·Gold 구조 검사의 회귀 보존.
- 모든 candidate의 Production 거부.

### 후속 구현 범위

이 계약의 후속 대상은 실제 빌드·실행기·수집기와 외부 확인값 저장소 연결, 출처 Schema와 실행 가능한 실패 검사, Runtime 전용 컨텍스트·권한 API, 허용된 Teacher·사람 검토 절차와 데이터 qualification이다.

계약에서 정한 후속 순서는 완료 묶음의 독립 검토 뒤 Schema·실패 검사 구현이다. 실제 검토·검증·구현 확인의 담당과 실행 권한은 사용자의 최신 작업 지침을 따른다. 이 문서는 각 대상의 승인 완료나 데이터 생산 완료를 선언하지 않는다.
