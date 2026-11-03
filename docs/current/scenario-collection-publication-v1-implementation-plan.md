# 수집 출처·결과 연결 구현 계획 (Task2E)

<!-- E:purpose -->
## 1. 목적

- **E01**: 출처·결과 연결은 회차의 고정 출처와 실제 저장된 판단 기록을 대조하고 연결 파일까지 재검증한 뒤 수락하는 기능이다.

실행 조건에서 얻은 출처를 판단 기록에 먼저 넣는다. 저장된 기록의 출처가 회차와 일치하면 별도 연결 파일을 발행한다.
실패한 경우에는 원본 기록과 이미 실행한 행동의 사실을 보존하고 이후 수집을 막는다.

> **작성 당시 작업 방식:** 아래의 부모·작성자 분담과 test-first 절차는 이 계획을 작성하던 때의 기록이다. 2026-11-03 사용자가 로컬 직접 작업으로 전환했으며 AI의 후속 구현은 중단했다. 현재 인계 상태는 [로컬 작업 인계](../history/local-development-handoff-2026-11-03.md)를 따른다.

**Goal:** 회차 출처 → 원본 판단 기록 → 검증 영수증 → 연결 파일의 일치를 확인한다.
**Architecture:** 기존 Host의 판단·저장 순서를 유지한다. 연결 담당 코드는 Reader가 발급한 결과와 불변 회차 정보를 대조하고 기존 FileStore에 JSON 발행을 추가한다.
**Tech Stack:** Unreal Engine 5.7 C++·기존 Windows FileStore·JSON Schema·pytest·Unreal Automation.

<!-- E:terms -->
## 2. 먼저 알아둘 용어

- **고정 출처(context)**는 회차 ID, 실행 주체, 조건, build와 예산을 검증해 값 복사한 정보다.
- **판단 기록(Record/Capture)**은 한 번의 판단과 원본 identity를 담은 저장 자료다. 수집 회차와 Capture의 episode ID는 별개다.
- **검증 영수증(receipt)**은 Reader가 실제 Capture와 marker를 같은 byte image로 검증한 불변 결과다.
- **연결 파일(sidecar)**은 영수증의 원본 identity·파일 descriptor와 회차 출처를 결속한 JSON이다.
- **연결 담당(bridge)**은 영수증과 context의 일치를 확인하고 sidecar·진단을 발행한다.
- **producer verified**는 원본 Capture와 marker 검증까지 끝난 상태다. **collection accepted**는 sidecar의 실제 재읽기까지 끝난 상태다.
- **수명 증표(lease)**는 현재 World·Host·회차와 epoch를 결속한다. revoke는 같은 증표의 후속 사용을 막는다.
- **고정 차단(session sticky block)**은 같은 세션에서 retry와 다음 회차를 계속 거부하는 상태다.

<!-- E:scope -->
## 3. 현재 상태와 이번 범위

- **E02**: Task2D는 native FileStore·same-image Dataset·Reader-owned receipt·실제 Host 저장 연결의 지정 범위에서 승인됐다. 이 계획은 Task2E 구현·실행 승인을 주장하지 않는다.
- **E03**: production collection closed; Approved=false; ResolvePolicyReady=false; production_eligible=false를 유지한다.
- **E04**: Task3 GameInstance·issuer·실제 reset·UI와 Task4 ML·authority/import는 제외한다. fixture reset/drain은 실제 측정으로 승격하지 않는다.

이 계획과 pytest는 Task2E의 문서-only 산출물이다. 부모의 C++·실행 결과는 별도 evidence로 판정한다.
Task2D의 역사적 문서 단계에 쓰인 ‘저장 미구현’은 그 시점에 한정한다.
현재 지정 범위 승인은 `task2d-final-acceptance-01.json`의 `ACCEPTED_SCOPED`다.
Task2C의 copy 승인, Task2D의 원본 프로젝트 승인, Task2E의 미완료 구현을 구분한다.

개발 기준 root는 `/mnt/d/Codex-cli/NeuralProject/NeuralGame`이다.
이번 계획의 읽기 기준은 `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/before-source/Source`다.
같은 evidence root의 `before-docs`와 `predecessor/task2d-final-acceptance-01.json`을 보존한다.
실시간 원본 소스를 다시 읽어 frozen 기준을 바꾸지 않는다. 부모의 수정·실행은 별도 단계다.

권위는 [Host 계약 §§4–11](scenario-host-capture-v1-contract.md), [Runtime import 계약 §§2–4](runtime-capture-import-v1-contract.md),
[수집 데이터 계약](scenario-collection-v1-data-contract.md), [collection Schema](../../contracts/current/scenario_collection_v1.schema.json),
[catalog](../../contracts/current/scenario_catalog_v1.json)다. 이 계획은 제품 정책·wire/Schema를 변경하지 않는다.
[Task2D 계획](scenario-collection-storage-v1-implementation-plan.md)은 그 당시 작업 기준과 보존 조건으로 읽는다.

<!-- E:order -->
## 4. 결과를 수락하는 순서

- **E05**: Record Build 전에 immutable context에서 metadata를 고정한다. Build 뒤 원본 Record의 family·seed·build·source·identity를 수선하지 않는다.
- **E06**: Skill start는 marker보다 앞이다. pending write 성공·producer verified·collection accepted를 별도로 유지하며 sidecar 실패로 과거 counter를 rollback하지 않는다.

| 순서 | 작업 | 책임 | 관찰 기준 |
|---|---|---|---|
| 1 | Finalize | Host | 승격 전 관측과 같은 Snapshot |
| 2 | policy selection | 기존 orchestrator | 기존 Utility 의미 보존 |
| 3 | Request | Host | 같은 token/identity |
| 4 | metadata + Record Build | Host | immutable context·여덟 group 고정 |
| 5 | pending write + exact readback | Dataset/FileStore | 실패: Commit/start 0 |
| 6 | Commit + final promote + private Skill start | Coordinator/Host | 실제 start 사실 보존 |
| 7 | marker publish | Dataset/FileStore | 실패: verified/accepted 0 |
| 8 | same-image committed readback | Reader | Capture 1회 + marker 1회 |
| 9 | producer verified | Host | SlotHistory·VerifiedCaptureDecisionIds |
| 10 | bridge context join | CaptureBridge | 불일치: session block |
| 11 | sidecar exclusive publish + actual exact readback | CaptureBridge/FileStore | 실패: accepted 0 |
| 12 | collection accepted | CaptureBridge | entry/count 한 번 발행 |

`DecisionCaptureWriteSuccessCount`는 pending write 성공 사실이다. pending readback 실패도 이 사실을 소급 삭제하지 않는다.
`VerifiedCaptureDecisionIds`는 marker와 committed readback 뒤에만 추가한다.
sidecar가 실패하면 producer verified는 남고 collection accepted는 증가하지 않는다. multi-file/gameplay atomic rollback은 약속하지 않는다.

<!-- E:failures -->
## 5. 실패했을 때

- **E07**: 실패는 callback·I/O 전에 terminal latch와 epoch/lease를 닫는다. deadline 전 failed, at/after deadline timed_out을 유지하며 진단 실패도 memory terminal과 실패 반환을 보존한다.
- **E08**: context join·sidecar·diagnostic 저장 실패는 session sticky block이다. 같은 회차 retry·다음 회차·completion pin을 차단하고 기존 Capture/marker와 이미 발생한 Commit/start/verified 사실을 보존한다.
- **E09**: collection intent에 context 부재·stale lease가 있으면 legacy fallback 금지다. intent 없는 legacy general/ResolveShadow 동작은 보존한다.

진단은 실제 실패 경계와 실제 관측값만 남긴다. 현재 회차를 닫고 stop을 요청한 뒤, strong pin으로 고정한 같은 회차의 진단 저장을 시도한다.
reentrant committed-start stack 안에서 authority나 World를 파괴하거나 새 회차를 붙이지 않는다.
A의 오래된 callback이 B를 차단·변경하지 못하게 exact 객체·lease 결속을 매번 검사한다.

잘못된 관측은 해당 회차 종료와 검증된 초기화 뒤 새 회차 정책을 유지한다.
정상 sensor 부재·event 미충족은 기존 wait/timeout이며 위치 전용 입력과 missing sentinel은 정상 입력이다.
실제 stop/drain/reset, terminal episode·reset 결과 보존과 다음 회차 발급은 Task3 책임이다.
Task2E는 진단 실패 receipt와 차단 신호까지만 제공한다. 유효한 monotonic 시간이 없으면 시간을 발명하지 않고 차단을 유지한다.

<!-- E:done -->
## 6. 완료 조건과 적용 경로

- **E10**: 문서 pytest는 계약 일관성만 검사한다. Task2E 완료는 실제 Host 경로의 metadata→receipt→bridge→disk readback과 C01–C07/P14–P18 행동 증거 및 고정 subject 독립 SPEC→QUALITY 검토를 요구한다.

문서 단계 완료는 이 계획, entrypoint 링크, 문서 RED/GREEN·in-memory hostile mutation과 원본 보존이다.
구현 단계 완료는 아래 행위 검사를 실제 통과한 뒤 부모가 판정한다. lower JSON 검사만으로 Host 통합 완료를 주장하지 않는다.

- 모든 생산 phase에서 정확한 metadata·여덟 group과 원본 identity가 유지된다. Observe의 가짜 Capture는 0이다.
- 실제 Reader 영수증만 받아 sidecar bytes를 재읽고 검증한다. 중복 수락은 0이다.
- 저장 실패·stale/reentrant 실패·진단 저장 실패에서 원본과 기존 성공 사실을 보존한다.
- 저장 예산, session sticky block, legacy 회귀와 기존 Task2D 안전 경계가 유지된다.
- 새 테스트 TU 재컴파일과 실행 binary 결속, exact 이름·report·exit, 보존 inventory를 확인한다.

이 문서의 독자는 부모 구현자와 검토자다. README·상위 수집 계획이 이 파일로 연결한다.
`tests/test_collection_publication_contract_document.py`는 명시한 pytest 명령에서만 문서 의무를 검사한다.
실제 집행은 Host의 Build 전 경계, bridge의 join/accepted 경계, FileStore의 native create/move/readback 경계에 둔다.
문서·수동 체크리스트만으로 런타임 집행을 주장하지 않는다. production issuer가 생기기 전에는 dev fixture만 실행 가능하다.

---

<!-- E:files -->
## 7. 개발자용 계약과 파일 경계

### 7.1 정확한 허용 파일

기준은 `Source/NeuralGame/AINativeNPC/`다. 조건부 파일은 필요한 좁은 delta가 입증될 때만 수정한다.

- **E11**: Builder·serializer·Adapter·Observation tests·Coordinator·Knowledge·Schema·catalog·generated·Content·ML은 동결한다. Dataset은 필요한 additive read-only accessor만 허용한다.
- **E12**: CollectionContext는 필요한 read-only getter 또는 좁은 lifecycle 경계만 허용한다. public authority mint·mutable setter·production issuer는 금지한다.

| 파일 | 작업 | 허용 변경 |
|---|---|---|
| Execution/AINativeNPCGoalHostComponent.h | 수정 | metadata 전달·bridge 호출·terminal 연결 |
| Execution/AINativeNPCGoalHostComponent.cpp | 수정 | metadata 전달·bridge 호출·terminal 연결 |
| Collection/AINativeNPCCollectionCaptureBridge.h | 신규 | receipt/context join·entry/diagnostic |
| Collection/AINativeNPCCollectionCaptureBridge.cpp | 신규 | receipt/context join·entry/diagnostic |
| Collection/AINativeNPCCollectionFileStore.h | 수정 | bounded JSON publication·readback |
| Collection/AINativeNPCCollectionFileStore.cpp | 수정 | bounded JSON publication·readback |
| Collection/AINativeNPCCollectionContext.h | 조건부 | read-only getter·좁은 lifecycle 경계 |
| Collection/AINativeNPCCollectionContext.cpp | 조건부 | read-only getter·좁은 lifecycle 경계 |
| Dataset/DecisionRecordV2.h | 조건부 | 필요한 additive read-only accessor만 |
| Dataset/DecisionRecordV2.cpp | 조건부 | 필요한 additive read-only accessor만 |
| Tests/AINativeNPCCollectionHostTests.cpp | 수정 | 실제 Host C01–C07/P14–P18 |
| Tests/AINativeNPCCollectionCaptureBridgeTests.cpp | 신규 | join·JSON·진단·budget hostile |
| Tests/DecisionRecordV2Tests.cpp | 조건부 | Reader-only·legacy 회귀 |

기존 serializer 동결은 ANPCCAP2/CBOR/marker 의미와 `BuildCaptureEnvelopeBytes`·`BuildCommittedMarkerBytes`의 재사용을 뜻한다.
새 collection JSON encoder는 아래 고정 grammar만 구현한다. 별도 capture parser·공개 wire serializer를 만들지 않는다.
`Build.cs`, 기존 ShippingGuardTests, asset, Saved의 기존 자료와 과거 evidence는 허용 수정 파일에 포함하지 않는다.

현재 `FAINativeNPCCollectionContextInput`의 대부분 payload는 protected다. `GetPayload()`가 있어도 일반 caller는 family/build/seed를 읽을 수 없다.
필요한 const getter만 추가하거나 좁은 내부 접근 경계를 사용한다. 새 mutable aggregate나 fixture Expected를 생산자 metadata 권위로 만들지 않는다.
기존 `FAINativeNPCCollectionHostTestAccess`의 정의는 기존 Host tests 한 TU에서 유지한다.
새 Bridge test access는 고유 이름을 사용하고 선언·정의·friend·wrapper 모두 `WITH_DEV_AUTOMATION_TESTS`로 제한한다.
새 멤버는 protected `m` 접두어, 지역 변수는 접두어 없음, postfix const·다음 줄 중괄호·early return 규칙을 따른다.

<!-- E:metadata -->
### 7.2 판단 기록에 먼저 넣는 출처

- **E13**: 모든 생산 phase는 raw source_type=2/Dagger와 scenario_collection_utility_unreviewed를 사용한다. 기존 phase reason tags와 Resolve capture-only 0.25·다른 phase 1.0 및 Utility label 의미를 보존한다.
- **E14**: source/controller/mode는 현재 context의 실제 조합이다. automatic·automated replay는 automated_runtime이며 family 문자열로 human_play를 추론하지 않는다.
- **E15**: 승격 전 KnowledgeBeforePromotion은 같은 preparation의 owned 값으로 보존한다. Finalize 뒤 같은 immutable Snapshot의 handles/mask/Tensor와 대조해 Record Build 전에 group을 만든다.

| 필드 | 고정 값 또는 대조 |
|---|---|
| EpisodeId | scenario_capture_<session UUID>_<collection episode UUID>_<process sequence> |
| sequence | 0이 아닌 20자리 unsigned decimal; process-wide checked allocator |
| GeneratorTemplateVersion | neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1 |
| GeneratorOrRuntimeBuildSha256 | runtime_build_evidence_sha256 = session.runtime_build_sha256 |
| ScenarioFamilyId | episode.family.scenario_family_id = catalog.scenario_family_id |
| MapSeed,SimulationSeed | episode.seeds.map_seed = episode.seeds.simulation_seed = conditions.seed |
| SourceType | 2/Dagger |
| ReasonTags | scenario_collection_utility_unreviewed + 기존 phase reason tags |

sequence와 경로는 기존 `TryBeginAttempt`와 `GetNamespace()`에서 받는다. 직접 발급하거나 실패 번호를 재사용하지 않는다.
MAX_uint64는 마지막 유효 번호이며 이후 영구 실패다. lowercase UUIDv4·20자리 표현을 그대로 검사한다.
`resolve_capture_only_utility_selected`와 `production_phase3b_commit`의 해당 phase 이유를 유지한다.
기존 중간 태그 `collection_unreviewed`만으로 새 exact tag를 충족했다고 판정하지 않는다.

frozen Host의 `CaptureCollectionDecision`은 binding에서 `mContract/mGroup/mProvenance`를 복사한다.
Host tests의 `BindStorage`는 `fixture_orient_v1`, `fixture_guard`, `host_storage_fixture_only_v1` 등을 넣는다.
이 fixture metadata 주입을 실제 context·현재 token·Snapshot에서 생산하는 경계로 교체한다.
`FDecisionRecordV2Builder::Build`와 `ValidateReplay`는 그대로 호출한다. Builder 성공 뒤 metadata 보정은 허용하지 않는다.

raw source와 collection `input_source`는 다른 계약이다. fixture는 `test_fixture`와 별도 namespace를 유지한다.
진짜 human/automated provenance 확인은 후속 issuer 권한이며 Task2E가 digest 모양만으로 발급하지 않는다.

<!-- E:groups -->
### 7.3 여덟 group의 고정 순서와 값

- **E16**: group 문자열은 canonical ASCII이며 trim/lowercase 수선 금지다. TargetCompositionFamily는 regular target_mask=true에서 NoTarget을 제외하고 중복 제거·generated enum 숫자 오름차순으로 + 연결한다. empty set -> reject다.
- **E17**: Entity/SoundEvent는 exact KnowledgeBeforePromotion entry와 대조한다. LastKnownPosition은 modality_unknown이며 visible_now=false·age>0도 kind evidence를 지우지 않는다.
- **E18**: GoalSequenceFamily는 현재 GoalToken과 G76–83/G84–91 one-hot를 대조한다. EventSequenceFamily는 catalog taxonomy이며 관측 prefix·미래 사건 완료·Teacher 입력으로 사용하지 않는다.

| wire index | producer field | exact 값 또는 닫힌 derivation | 원천/대조 oracle |
|---|---|---|---|
| 0 | MapFamily | l_ai_native_npc_mvp | episode.map + catalog.map |
| 1 | OcclusionLayoutFamily | mvp_unvalidated_layout_v1 | episode.family.layout_family + catalog.layout_family |
| 2 | GoalSequenceFamily | InvestigateDisturbance:<Phase> | GoalToken + global_state |
| 3 | RoleId | manny_guard | exact native Guard + pinned source/build |
| 4 | PersonalityClusterId | default_guard | compiled default profile + pinned source/build |
| 5 | PerceptionModalityFamily | kind_evidence:<Modalities> | finalized target_handles + target_mask + KnowledgeBeforePromotion |
| 6 | TargetCompositionFamily | <Kinds> | finalized target_handles + target_mask |
| 7 | EventSequenceFamily | catalog.event_sequence_family | episode.family.event_sequence_family + catalog.event_sequence_family |

`<Phase>`는 `Orient,Navigate,Search,Resolve,Return` 중 현재 enum text 하나다.
`<Kinds>`의 허용 순서는 `Entity,SoundEvent,LastKnownPosition,CoverSlot,SmartObject,Waypoint,WorldPosition`이다.
예를 들어 `SoundEvent+LastKnownPosition+Waypoint`가 된다. unknown enum·mask/handle 모순·빈 집합은 실패다.
StableId/Generation/Revision/count를 group 문자열에 넣지 않는다. exact handle 비교에서는 네 identity 성분을 모두 사용한다.

`<Modalities>`는 Entity→sight, SoundEvent→hearing, LastKnownPosition→modality_unknown이다.
출력 순서는 `sight,hearing,modality_unknown`이고 `+`로 연결한다.
세 kind가 없으면 `kind_evidence:position_only`, 모두 있으면 `kind_evidence:sight+hearing+modality_unknown`이다.
다른 kind는 modality를 추가하지 않는다. confidence=0·age=0을 센서 부재 증명으로 쓰지 않는다.

MapFamily는 exact selected `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`만 대응한다. PIE prefix를 family로 쓰지 않는다.
layout은 검증된 벽/LOS 주장으로 승격하지 않는다. unsupported map/layout/role/profile·빈 값은 attach/생산 실패다.
현재 Host의 synthetic primary는 WorldPosition/Waypoint다. Resolve의 Entity는 Goal-owned이면서 Knowledge-backed다.
LastKnownPosition의 원래 sensor lineage는 wire만으로 완전히 복원되지 않으므로 보수적 분류를 유지한다.

EventSequenceFamily는 `hearing_only_v1`, `hearing_appearance_v1`, `hearing_appearance_loss_v1` 중 resolved catalog 값이다.
실제 관찰 prefix는 기존 `event_observations`에만 남긴다. `captured_at_server_time`과 elapsed monotonic clock의 원점은 다르다.
새 필드로 clock 원점을 만들거나 이후 사건을 완료로 추정하지 않는다. template family는 sidecar family에 남고 wire 위치를 늘리지 않는다.

<!-- E:join -->
### 7.4 영수증과 회차의 exact join

- **E19**: receipt는 FDecisionRecordV2Reader만 생성한다. GetRecord/GetContext/GetLease/GetEpoch/GetAuthority와 descriptor를 사용하고 public path+bool/digest mint·Capture/marker 재개방·새 parser를 금지한다.
- **E20**: bridge는 exact context/World/Host/episode/lease/epoch·namespace/build/family/seeds/source/tag·여덟 group을 대조한다. 같은 receipt/identity/sample/path 및 episode/decision pair 재발행은 reject한다.
- **E21**: accepted entry와 count는 sidecar exclusive publish + actual exact readback 및 마지막 current lease 검사 뒤 한 번만 발행한다. 불일치나 재진입은 미발행과 session block을 유지한다.

기존 `ReadCollectionCommittedReceipt`는 private Reader API이며 실제 bound attempt를 요구한다.
`FDecisionRecordV2CollectionReceipt`는 descriptor-only 불변 객체다. `GetRecord()`는 원본 metadata·Snapshot을 보유하고 Capture/marker native handle은 보유하지 않는다.
기존 same-image readback과 Reader-only 생성 경계를 그대로 소비한다. bridge가 receipt를 복제 발급하거나 caller-supplied expected 값으로 바꾸지 않는다.

bridge는 시작 때 receipt·context·lease·authority·root를 strong pin한다. 각 외부 callback·native I/O 뒤 같은 pin과 current 상태를 재검사한다.
reentrant 성공 발행을 막는 in-flight guard를 세운다. duplicate ledger는 성공한 identity/sample/path뿐 아니라 재진입 중인 publication도 충돌로 다룬다.
실패 후 같은 세션이 닫히므로 실패 번호 재시도나 overwrite로 복구하지 않는다. 성공 ledger는 회차·World 교체로 지우지 않는다.

대조 항목은 다음과 같다.

1. receipt의 exact 객체 결속과 현재 World/Host/episode/epoch, session source/controller/mode/mapping version.
2. raw EpisodeId에서 얻은 session·collection episode·20자리 sequence와 capture/marker 상대 경로.
3. 외부 build pin과 GeneratorTemplateVersion의 catalog/profile/mapping 결속, scenario family와 두 seed.
4. Dagger·필수 reason tag·기존 phase tag·현재 phase confidence, immutable Snapshot에서 재구성한 group bytes.
5. 원본 `episode_id/decision_id/input_content_hash/sample_id`와 receipt의 `path/size_bytes/sha256`.

sidecar에는 Schema의 기존 `committedEntry` 필드만 쓴다. build/profile이나 source 설명을 새 필드로 추가해 raw Record 불일치를 숨기지 않는다.
source/controller/mode 자체가 새 raw wire field로 들어가는 것은 아니다. immutable context/receipt 결속이 그 provenance를 묶는다.
Entity/SoundEvent의 승격 전 근거는 생산 시점의 검증된 owned evidence를 사용한다. bridge가 현재 Knowledge를 재조회해 과거 근거를 수선하지 않는다.

<!-- E:json -->
### 7.5 JSON 발행과 실제 재읽기

- **E22**: sidecar와 diagnostic은 sorted_json_bytes(value) + b"\n"의 exact UTF-8 bytes다. key sort·compact separators·ensure_ascii=False·allow_nan=False와 정확한 정수·JSON escaping을 지킨다.
- **E23**: FileStore의 실제 CREATE_NEW → full write/flush/close → nonreplace MoveFileW → bounded held-image readback을 사용한다. final/temp 충돌·race·ancestor 교체를 거부하고 exact owned temp만 cleanup한다.

sidecar 경로는 `entries/<session UUID>/<collection episode UUID>/<process sequence>.json`이다.
diagnostic 경로는 `diagnostics/<session UUID>/<collection episode UUID>/<diagnostic UUID>.json`이다.
각 temp는 final 뒤 `.tmp`이며 같은 final/temp identity 재발행을 거부한다. diagnostic UUID도 canonical lowercase UUIDv4다.
기존 native root의 thread-affinity·mutex·no-delete-sharing ancestor guard를 공유한다. root 위 ancestor부터 목적지 parent까지 보호한다.
unsupported filesystem/platform·query failure·alias/reparse·reserved name race는 fail closed다.
보장은 protected cooperating root에 한정하며 arbitrary malicious writer/crash durability로 확대하지 않는다.

frozen FileStore는 Capture/marker 단계만 제공한다. **JSON publication/readback API는 새 구현 대상**이다.
기존 `TryAcquireRoot`, native create/write/flush/close/move/read-image 내부 연산을 재사용해 작은 sibling publication 경계를 추가한다.
marker용 API에 JSON을 끼워 넣거나 일반 replacing `SaveStringToFile`로 우회하지 않는다.
생성 성공을 readback 성공으로 대체하지 않는다. 같은 final의 실제 bounded image를 기대 canonical bytes와 exact 비교한 뒤 descriptor를 낸다.
readback 실패로 남은 final은 삭제·재작성하지 않고 미수락 residual로 보존한다.

JSON 숫자는 typed 값을 보존한다. `decision_id=18446744073709551615`를 double로 통과시키지 않는다.
진단 시각은 유한한 수이며 Python canonical 표현과 exact bytes parity를 검사한다.
문자열 quote/backslash·control escaping·UTF-8 비ASCII·음의 zero·작은/큰 유한 지수 표기와 trailing LF 한 개를 비교한다.
잘못된 Unicode·NaN/Infinity·빈/초과 bytes·중복/미정의 key는 거부한다. collection용 제한 encoder를 Capture serializer와 분리한다.

Python oracle은 다음 exact 표현이다. 기존 import 계약의 `sorted_json_bytes` 이름은 byte grammar이며 이 저장소에 같은 이름의 새 helper가 존재한다고 가정하지 않는다.

```python
expected = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
assert actual_bytes == expected
```

closed key 집합은 Schema의 `$defs/committedEntry`와 `$defs/diagnostic`에 직접 대조한다.
공통 key는 `kind,collection_episode_id,input_source,execution_mode,controller,observation_mapping_version,family`다.
committedEntry의 추가 key는 `capture_identity,capture,committed`뿐이다.
diagnostic의 추가 key는 `diagnostic_id,observed_id,stage,reason,observed_at_seconds,snapshot_present,snapshot_ref`뿐이다.
wrapper `format/version/session_id`, approval flag, 선언 count를 entry에 추가하지 않는다.

<!-- E:diagnostics -->
### 7.6 진단의 관측값과 terminal 경계

- **E24**: observed_id는 실제 발급·관찰한 ID 또는 null이다. Request 전 실패에 DecisionId를 만들지 않으며 memory-only Snapshot/Draft는 snapshot_present=false, snapshot_ref=null이다.
- **E25**: snapshot_present=true는 실제 immutable artifact의 size/hash 검증 뒤에만 허용한다. fake Snapshot/hash와 diagnostic의 capture_identity/committed 필드 추가를 금지하며 committed/Dataset 분모에서 제외한다.
- **E26**: terminalization 뒤 진단 저장은 exact 실패 episode에 결속된 제한 경로로 수행한다. revoked lease를 일반 publication에 다시 허용하지 않으며 diagnostic persistence 실패도 성공·새 회차·completion pin을 만들지 않는다.

stage는 준비 실패 `preparation`, 관측 mapping `execution`, Capture 검증 `capture`, I/O `storage`, owner 초기화 `reset`이다.
Task3의 실제 reset은 미구현이므로 reset fixture를 실제 초기화 증거로 표시하지 않는다.
bool-only 관측 실패 reason은 `observation_mapping_failed`다. 세부 이유는 실제 실행한 precondition 검사만 사용한다.
`observed_at_seconds`는 준비 시작을 포함한 elapsed monotonic 시간이다. nonfinite/backwards clock과 수명 검증 오류는 차단한다.
World game time이나 `CapturedAtServerTime`을 진단 시간으로 대신 넣지 않는다.

Host의 기존 `FailCollectionStorage`·`FailCollectionObservation`은 revoke 이후 일반 current 검사를 통과할 수 없다.
따라서 실패를 먼저 닫은 뒤 진단을 쓰는 경계는 별도 제한이 필요하다.
구현은 실패를 관찰한 exact context/lease/root와 terminal 사실을 내부에서 결속한다.
이 경로는 해당 diagnostic 한 건의 저장과 readback만 허용하며 committed sidecar·새 decision·reset 발급 권한을 주지 않는다.
public bool로 ‘terminal 허용’을 넘기거나 모든 stale lease를 허용하는 방식은 금지한다.

진단 저장 자체가 실패하면 재귀적으로 무한 진단을 만들지 않는다. 원래 실패와 추가 persistence 실패를 메모리 결과로 남긴다.
파일이 없으면 diagnostic descriptor를 발명하지 않는다. validated context가 없어 Schema 공통 필드를 채울 수 없는 실패도 값 수선 없이 차단·실패 신호로 남긴다.
실제 persisted snapshot의 descriptor를 공급할 수 없으면 false/null을 유지한다. sidecar 실패 후 검증된 Capture가 존재하는 경우만 그 검증된 descriptor를 사용할 수 있다.

<!-- E:budget -->
### 7.7 누적 저장 예산

- **E27**: storage_limit_bytes는 Capture·marker·sidecar·diagnostic·index 및 in-flight overhead를 모두 포함한다. checked arithmetic과 쓰기 전 예약을 사용하며 World/reset으로 누적 소비량을 초기화하지 않는다.
- **E28**: 실패해도 보존된 final/residual bytes는 소비량에 남긴다. 진단/index 예약 부족도 fail closed이며 원본 삭제로 공간 확보·예산 초과 write·accepted 선증가를 금지한다.

현재 `mMaxCaptureBytes/mMaxMarkerBytes`의 per-file 한도만으로 session budget을 충족했다고 판정하지 않는다.
session 수명에 결속한 누적 accounting과 in-flight reservation을 둔다. 새 GameInstance owner는 Task3까지 만들지 않는다.
Task2E fixture에서도 이 수명은 World보다 길어야 한다. `max_decisions`는 receipt 수락 전 확인하고 중복 성공으로 소모·증가시키지 않는다.

구현 순서는 기존 보존 bytes + 현재 in-flight 최대 동시 bytes + 새 요청 + 진단/index 예약을 checked 합산하는 것이다.
canonical byte 길이가 확정되는 단계마다 예약량과 실제 소비량을 대조한다. temp→final 이동은 같은 bytes의 이름 변경으로 다룬다.
소유 temp의 실제 삭제가 확인된 경우에만 그 예약을 해제한다. residual과 committed 원본의 공간은 계속 계산한다.
index의 최종 발행은 Task3다. Task2E는 현재 entries가 요구하는 index bytes와 후속 진단 overhead를 위한 공간을 예약한다.
임의 상수나 Capture 크기만으로 모든 overhead가 포함됐다고 표시하지 않는다.

<!-- E:steps -->
## 8. 작은 구현 단계

- **E29**: metadata slice → lower JSON publication → bridge/diagnostics → Host wiring 순서로 나눈다. 각 작은 단계는 행동 RED → 최소 구현 → focused GREEN이며 writer와 단일 build owner를 분리한다.

모든 단계에서 writer가 파일 변경을 마치면 exact source를 고정한다. build owner는 그 뒤 owning TU compile을 확인하고 실행한다.
writer가 편집 중일 때 다른 작업자가 build/run하지 않는다. 아래 test 이름은 **새로 등록할 목표 이름**이며 현재 발견됐다는 뜻이 아니다.
실행 filter는 §10의 기존 interface를 따른다. compile/link 오류·absent header만으로 행동 RED를 주장하지 않는다.

### 8.1 metadata slice — Build 전 값과 group

**파일:** Host .h/.cpp, 기존 Host tests; 필요한 Context const getter만. Builder/Dataset serializer는 그대로 둔다.

1. **첫 RED:** 기존 `FAINativeNPCCollectionHostTestAccess::BindStorage/RunStorage`와 private `RunCollectionStorageDecisionForTest`로 Orient를 한 번 실행하는 `AINativeNPC.Collection.Host.C01.BuildMetadataFromImmutableContext`를 추가한다. 새 Bridge header/API에 의존하지 않는다.
2. 기존 storage 성공 control에서 receipt nonnull·private start/verified 도달을 먼저 확인한다. 같은 test에서 receipt Record의 `MapFamily=l_ai_native_npc_mvp`, `GoalSequenceFamily=InvestigateDisturbance:Orient`, `RoleId=manny_guard`, exact GeneratorTemplateVersion과 필수 tag를 기대한다. frozen source의 fixture 값 때문에 생기는 assertion 실패를 기록한다.
3. `CaptureCollectionDecision`에서 namespace는 기존 attempt를 사용하고 context에서 contract build/family/seed/template을 고정한다. `FDecisionRecordV2Builder::Build` 직전 단일 값 전달 경계로 구현한다. 같은 test의 GREEN을 확인한다.
4. C01 caller 원본 변경과 C02 모든 phase/source 조합을 한 가지씩 추가해 RED→GREEN한다. immutable context 이후 caller/fixture metadata 변경은 pending Record를 바꾸지 못해야 한다.
5. `PrepareDecisionFeatures`의 지역 `KnowledgeBeforePromotion`을 같은 attempt 수명의 owned 값으로 전달한다. Finalize 뒤 Snapshot에서 kind/phase를 대조한다. Snapshot이나 Builder의 의미를 바꾸지 않는다.
6. C07의 kind 중복/정렬·NoTarget/mask·빈 집합·one-hot·Entity/SoundEvent 근거 누락을 각각 RED→GREEN한다. Finalize 실패·다른 회차에 이전 근거를 재사용하지 않는지도 확인한다.

첫 test의 최소 assertion 모양은 다음과 같다. 함수의 fixture 준비는 기존 Host test의 정상 control을 재사용한다.

```cpp
auto const Receipt = FAINativeNPCCollectionHostTestAccess::RunStorage(Host);
TestTrue(TEXT("actual Reader receipt exists"), Receipt.IsValid());
if (!Receipt.IsValid())
{
    return false;
}
TestEqual(TEXT("context-derived map family"), Receipt->GetRecord().Group.MapFamily,
    FString(TEXT("l_ai_native_npc_mvp")));
TestTrue(TEXT("required collection provenance tag"), Receipt->GetRecord().Labels.ReasonTags.Contains(
    TEXT("scenario_collection_utility_unreviewed")));
```

### 8.2 lower JSON publication — 저장 경계만 먼저

**파일:** FileStore .h/.cpp, 새 Bridge tests. JSON 값 조립은 다음 단계까지 분리한다.

1. private fresh root의 known bytes로 final/temp 충돌·각 native syscall fault·actual readback 실패 검사를 만든다. 정상 control과 단계 도달을 함께 확인한다. 신규 API 부재의 compile 결과는 행동 RED와 별도 기록한다.
2. 기존 native 보호 내부 연산을 재사용해 JSON sibling의 exclusive create/nonreplace/readback만 추가한다. 정체불명 cleanup이나 root guard 완화는 하지 않는다.
3. 실제 Windows 파일에 성공 readback, race sentinel 보존, ancestor/alias 거부를 실행한다. tests는 `AINativeNPC.Collection.CaptureBridge` 아래에 등록한다.
4. canonical bytes 조립을 추가하고 Python oracle로 integer/escape/Unicode/time·LF를 검증한다. JSON 키·숫자 타입 검사는 기존 `validate_structure`를 소비한다.

### 8.3 bridge/diagnostics — 연결·중복·실패 저장

**파일:** 새 CaptureBridge .h/.cpp, Bridge tests, 필요한 좁은 Context lifecycle 경계.

1. Reader가 만든 실제 receipt 성공 control을 사용해 각 metadata/context 필드 불일치와 duplicate receipt를 RED로 만든다. boolean 성공 receipt를 합성하지 않는다.
2. immutable expected 값과 same Snapshot에서 join하고 sidecar canonical bytes를 조립한다. lower publisher의 actual readback 전에는 output/accepted를 발행하지 않는다.
3. P15 ledger·재진입, J03 revoke/replacement, 마지막 lease 검사 실패를 각각 RED→GREEN한다.
4. P16 실제 ID/null·false/null·persisted descriptor를 각각 검사한다. terminalization 선행과 제한된 failure publication을 연결한다.
5. P17 diagnostic 자체의 open/write/flush/close/move/readback 실패를 검사한다. 실패 반환·memory terminal·session block·원본 bytes가 보존돼야 한다.
6. J04 checked 누적 budget을 연결한다. index/diagnostic/in-flight 예약, overflow·residual·회차 변경 후 누적 보존을 각 단계에서 검증한다.

### 8.4 Host wiring — 실제 start 뒤 결과 발행

**파일:** Host .h/.cpp와 기존 Host tests; Dataset은 accessor 부족이 실제로 확인될 때만 수정한다.

1. `CompleteCollectionStorage`의 Reader 성공 → SlotHistory/VerifiedCaptureDecisionIds 갱신 뒤에 bridge 호출을 연결하는 P14 test를 먼저 만든다.
2. fixture-only receipt output을 성공 source로 삼지 않는다. 실제 production helper가 bridge에 전달하는 receipt를 observation seam으로 확인한다.
3. 실제 private Skill start·marker/readback·verified가 발생한 뒤 각 sidecar stage를 실패시킨다. accepted 0, start/verified 보존, Capture/marker bytes 보존, retry/다음 회차 차단을 검사한다.
4. `FailCollectionStorage`·`FailCollectionObservation`의 exact 실패 context와 monotonic 시각을 diagnostic에 전달한다. A revoke 뒤 B나 callback 재진입은 B를 변경하지 않아야 한다.
5. C03–C06과 P18을 실행한다. Task2D P01–P13 회귀, Observation 회귀, 허용된 broad·macro-off compile 검증을 별도 기록한다.
6. 원본·Schema/generated/Content/과거 evidence의 보존을 확인하고 고정 subject에 독립 SPEC→QUALITY 검토를 요청한다. 남은 Task3/4는 완료 범위에서 제외한다.

<!-- E:matrix -->
## 9. 기능별 실패 검사 matrix

- **E30**: hostile case마다 정상 control과 실제 stage 도달을 증명한다. compile/link 오류·0-discovery·timeout·mock 성공은 행동 RED가 아니며 문서 mutation 수를 Unreal 검사 수에 합산하지 않는다.

| ID | 입력·실패 주입 | 실제 경계 | 필수 oracle | 담당 검사 |
|---|---|---|---|---|
| C01 | caller family/seed/build 변경 | Build 전 고정과 pending mutation | 원본 Record 불변·context 값 일치 | Host |
| C02 | automatic·automated replay | 모든 생산 phase·현재 controller | human 오분류 0·Observe Capture 0 | Host |
| C03 | forged source/controller/build | fixture-only attach/receipt 경계 | real authority 0·위조 거부 | Host+Bridge |
| C04 | intent + missing/stale/preparing/terminal | Request 전 direct/retry 진입 | fallback 0·진단/실패 신호 | Host |
| C05 | A revoke 뒤 B·old receipt | current lease·World/Host/epoch | B 불변·old accepted 0 | Host+Bridge |
| C06 | Utility label·receipt 승인 오인 | readiness·분모 | false 유지·label 의미 보존 | Host+Bridge |
| C07 | 여덟 group·seed·budget | enum/mask/one-hot·Build 전 | 수선 0·닫힌 derivation 일치 | Host+Bridge |
| P14 | real commit 뒤 sidecar open/write/flush/close/move/readback | producer verified 이후 fault 도달 | Capture/marker 보존·start/verified 보존·accepted 0·retry/다음 회차 0 | Host+Bridge |
| P15 | receipt/identity/sample/path/episode-decision 중복 | ledger·in-flight 재진입 | accepted 증가 0·기존 sidecar 교체 0 | Host+Bridge |
| P16 | preparation/timeout/mapping/reset·memory-only | 실제 observed_id/null·stage·monotonic | false/null·분모 제외·fake hash 0 | Host+Bridge |
| P17 | sidecar 실패 뒤 diagnostic I/O 실패 | terminal 선행·failure-only publication | 실패 반환·session block·pin 0·원본 보존 | Host+Bridge |
| P18 | intent 없는 general/ResolveShadow | legacy Writer/Reader와 실제 Host | namespace/metadata/cleanup 보존·의도된 Tensor 변화 허용 | Host+Dataset |
| J01 | JSON final/temp file·directory·race·alias | native syscall·ancestor/root identity | 기존 bytes/type/membership 보존·owned cleanup만 | Bridge |
| J02 | MAX_uint64 DecisionId·escape·Unicode·finite time | Python canonical bytes·Schema keys | double 반올림 0·exact LF·unknown field 거부 | Bridge |
| J03 | join/publish/readback callback의 revoke·replacement | 같은 strong pin·reentrant guard | old accepted 0·B 불변·terminal 유지 | Host+Bridge |
| J04 | 누적·overflow·진단/index/in-flight 한도 | 쓰기 전 예약·residual accounting | budget 초과 0·원본 삭제 0 | Host+Bridge |

C01–C07의 기존 context/lease 부분 승인을 보존한다. 위 표는 아직 남은 metadata/publication과 회귀의 분리다.
J01–J04는 새 제품 정책이 아니라 Host 계약의 JSON·수명·예산 요구를 나눈 검사다.
P14/P17은 실제 producer 성공 사실이 양수인 control이 필수다. accepted=0만 확인하는 진공 검사는 통과 근거가 아니다.

<!-- E:commands -->
## 10. 실행 위치와 증거

- **E31**: 문서 작업자는 C++ 구현·Unreal/build 실행·commit/push를 수행하지 않는다. 부모 실행은 전용 Saved·고유 evidence·원본 preserved-source inventory와 단일 build owner를 전제로 한다.

### 문서 pytest — 현재 실행 가능한 명령

cwd는 `/home/namingsense/AI-Native-NPC`다. 인터프리터의 `tools` import가 이 repo를 가리키는지 먼저 확인한다.
모든 출력·XML·pytest temp는 evidence의 `docs-work` 아래에 둔다. 기존 evidence 파일명은 재사용하지 않는다.

```bash
PY=/mnt/d/Codex-cli/NeuralProject/NeuralGame/ML/.venv/bin/python
E=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc
RUN=$(mktemp -d "$E/docs-work/check-XXXXXXXX")
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" \
  ANPC_PUBLICATION_DOCUMENT_MODE=before-plan "$PY" -B -m pytest -p no:cacheprovider \
  tests/test_collection_publication_contract_document.py::test_active_publication_contract \
  -q --basetemp "$RUN/red-tmp" --junitxml "$RUN/red.xml" > "$RUN/red.log" 2>&1
# 기대: missing-clause assertion, exit 1. missing-file/import 오류는 RED가 아니다.
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider tests/test_collection_publication_contract_document.py \
  tests/test_collection_storage_contract_document.py tests/test_collection_host_bridge_contract_document.py \
  tests/test_collection_context_contract_document.py tests/test_runtime_capture_import_contract_document.py \
  tests/test_scenario_collection_contract.py tests/test_decode_anpc_capture_v2.py \
  tests/test_ml_data_pipeline_plan.py -q --basetemp "$RUN/focused-tmp" \
  --junitxml "$RUN/focused.xml" > "$RUN/focused.log" 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider -q --basetemp "$RUN/full-tmp" --junitxml "$RUN/full.xml" \
  > "$RUN/full.log" 2>&1
git diff --check
```

GREEN 뒤 모든 hostile mutation은 메모리 사본만 바꾼다. active scope·exact 규범·파일 허용표·순서·group·matrix의 삭제/약화/중복/예제 은닉을 거부한다.
pytest exit와 JUnit의 test/subtest를 따로 집계한다. 이 결과는 native I/O 또는 C++ correctness 증거가 아니다.

### 부모의 C++ build/run — 문서 작업자는 실행 금지

기존 확인 interface는 원본 `Intermediate/Hermes/RunNeuralGameTests.ps1`의 `-Test`, `-LogName`, `-ReportName`이다.
이 wrapper는 고정 Saved를 쓰며 timeout·소유권·UserDir 격리가 없다. 아래 형태는 **interface 참고**이며 그대로 실행하지 않는다.

```powershell
# cwd: D:\Codex-cli\NeuralProject\NeuralGame; 부모 단일 build owner 전용
& 'C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat' `
  NeuralGameEditor Win64 Development `
  '-Project=D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject' `
  -WaitMutex -NoHotReloadFromIDE
$buildExit = $LASTEXITCODE
if ($null -eq $buildExit -or $buildExit -ne 0) { throw 'Build failed or incomplete' }

# 확인된 wrapper interface; 실제 실행은 부모의 Saved 격리 harness에서 수행
# powershell.exe -File .\Intermediate\Hermes\RunNeuralGameTests.ps1 `
#   -Test AINativeNPC.Collection.Host -LogName <unique.log> -ReportName <unique>
```

부모 harness는 기존 engine argument `-unattended -nop4 -nosplash -NoSound -nullrhi`,
`-ExecCmds="Automation RunTests <filter>; Quit"`, `-TestExit="Automation Test Queue Empty"`,
고유 `-ReportExportPath=`, `-abslog=`, 전용 `-UserDir=`를 사용하고 실제 Saved 해석 결과를 확인한다.
`System.Diagnostics.Process`를 보존해 owned PID/exit와 900초 timeout을 확인한다. 다른 소유자 process는 종료하지 않는다.
첫 filter는 `AINativeNPC.Collection.Host.C01.BuildMetadataFromImmutableContext`다.
이후 `AINativeNPC.Collection.CaptureBridge`, `AINativeNPC.Collection.Host`, `AINativeNPC.Dataset.RecordV2`,
`AINativeNPC.Collection.Observation`과 승인된 broad `AINativeNPC`를 실행한다.
등록·발견·시작·종료·report의 exact test-name multiset, emitted StopTestSession/queue 종료, warning/skipped/notRun/inProcess를 확인한다.
null exit·timeout·0-discovery·명령줄 문자열만 있는 queue 표기는 실패다.

Task2D broad는 content-authoring 두 항목을 제외한 범위였다. 동일 제외 여부·실행 대상은 부모가 원본 보호 범위와 함께 명시한다.
기존 `Saved/AINativeNPC/Capture/Phase3B` destructive fixture가 원본 자료를 삭제하지 못하도록 전용 Saved를 먼저 검증한다.
고유 log만으로 격리를 주장하지 않는다. owning TU 실제 compile과 module/receipt/source 결속을 남긴다.
`clean_or_forced_project_modules`는 외부 build evidence의 별도 의무다. incremental build를 full clean/reproducible build로 표시하지 않는다.

### 발행 산출물 검사 — 기존 Python library 사용

repo cwd에서 부모가 실제 fresh artifact 경로를 전달한다.
`python -m tools.validate_anpc_capture_v2 <actual-capture-path> --json`은 기존 CLI다.
`tools.validate_scenario_collection --catalog`는 catalog-only CLI이며 session/index 검증 CLI로 사용하지 않는다.
`validate_structure("committedEntry", entry)`, `validate_structure("diagnostic", diagnostic)`,
`validate_committed_entry(entry, root)`, `validate_index(index, root, session, episodes, catalog, *, expected_profile_sha256, expected_runtime_build_sha256, replay_originals=())`는 기존 library API다.
실제 Capture/marker 읽기와 `decode_committed_capture_bytes`를 재사용하며 새 decoder/parser는 만들지 않는다.
index의 fixture 검증 성공은 Task3의 index-last/외부 completion pin 발행이나 Task4 authority 구현을 의미하지 않는다.

제품 해석의 선택은 새로 만들지 않는다. canonical 숫자 parity, terminal 뒤 diagnostic의 좁은 권한 경계, 누적 budget을 구현할 수 없으면 해당 단계에서 fail closed하고 구체적 충돌을 부모에게 보고한다.
이유 없이 Schema를 늘리거나 source/build 값을 사후 수선해 검사를 통과시키지 않는다.
