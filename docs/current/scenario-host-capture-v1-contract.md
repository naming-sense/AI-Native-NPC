# Host 관측 연결과 수집 Capture 발행 V1 계약

<!-- H:status -->
## 1. 목적과 현재 상태

이 **활성 구현 계약**은 Task 2의 Host 관측 연결, 수집 context, 충돌 없는 저장과 발행 bridge를 정의한다. bridge는 producer가 검증한 Capture를 수집 sidecar에 연결하는 경계다.

**상태: Task 2B의 Host 관측 연결과 Task 2C copy context/lease 구현·실행 checkpoint가 존재한다.** `PrepareDecisionFeatures`는 승격 전 복사와 Finalize 앞 Populate를 수행한다. 2026-10-25의 `fresh-host-02` **Host 9**와 `fresh-observation-01` **Observation 37** 실행은 S01의 fixture asset closure·fail-closed 입력 검사·실행 결속·원본 보호 범위에서 승인됐다. `whole_task2b_closed=false`를 유지한다. 해당 S01 승인은 H10·broad·Task 2C–2E·실제 수집·학습 readiness를 포함하지 않는다. Task 2C의 별도 승인은 아래 기록을 따른다. 근거는 `/home/namingsense/AI-Native-NPC-evidence/task2b-s01-narrow-tvrp81au/acceptance/acceptance.json`과 같은 root의 `packet/SCOPE.md`다. old438의 INCOMPLETE 판정도 보존한다.

<!-- T2C:historical -->
**역사적 문서 단계:** Task 2C 문서 일관성 검사 당시의 **C++ 미수정, Unreal build/run 미실행**은 **문서-only checkpoint에 한한 역사적 사실**이다.

<!-- T2C:current -->
**현재 Task 2C:** 허용된 **copy 5파일 구현**을 최신 소스로 다시 검증했다. **부모 확인 last runtime checkpoint**는 `c2-final-build-01`의 build 성공, `c2-final-host-01`의 **Host 25 PASS**(warning 53), `c2-final-observation-01`의 **Observation 37 PASS**(warning 0), `c2-final-broad-01`의 **broad 229 PASS**(warning 72)다. 관련 snapshot·run 증거 root는 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/final-05`다. WeakObjectPtr header include 보완 뒤 `c2-nodev-compile-02`의 3개 TU compile-only 검사도 통과했다(noShipping/noLink/noRuntime). runtime checkpoint 자체의 판정은 **최종 최신 bytes 실행 검증 완료; 독립 승인 아님**이며, 고정 부분 범위의 독립 승인은 아래 approval-record에 별도로 기록한다. `final-verification-02/result.json`은 exact test-name multiset, 원본 입력·Capture 보존, source delta 5개, 기존 H01–H09 본문 보존 및 focused/broad 입력 동일성을 확인한다.

<!-- T2C:limits -->
**독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만**, **production collection closed**다. `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다. **실제 collection 저장 미구현**, **실제 reset 미구현**이다. **terminal/reset/dispatch-drain receipt는 dev fixture 값**이며 **실제 Executor drain 측정 미구현**이다. **GameInstance owner·production issuer·ML import 미구현**, **원본 승격 없음**, **commit/push 없음**이다. 학습/Production 승인으로 해석하지 않는다.
<!-- T2C:approval-record -->
**고정 후보의 최종 검토 기록:** 독립 SPEC와 QUALITY가 같은 `final-05` source와 실행 증거의 Task2C 부분 범위를 승인했다. 부모는 subject 전체 파일과 두 검토 산출물의 동일성을 재검증했다. 승인 기록은 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/review-01/acceptance/acceptance.json`이다. **원본 승격 없음**이며 실제 저장·reset·production authority·학습 준비 완료는 이 승인에 포함하지 않는다. 검토 당시의 상태 문서와 기존 증거는 read-only subject에 그대로 보존하고, 이 단락과 승인 상태 문구만 현재 문서에 갱신했다.
<!-- T2C:end -->

<!-- T2D:active -->
**현재 후속 단계:** [Task2D 안전 저장·동일 이미지 검증 세부 계획](scenario-collection-storage-v1-implementation-plan.md)이 활성 계획이다. 문서/하네스 작성 뒤 부모가 lower Store/Dataset과 실제 Host wiring을 따로 구현·실행한다. **Task2D 전체 완료는 lower test만으로 주장 금지**다. metadata/group/context join·sidecar·diagnostic은 Task2E, 실제 owner/reset/UI는 Task3, authority/import는 Task4로 남긴다. 새 문서 하네스는 C++ 행동 검증을 대체하지 않는다.

순수 관측 adapter의 기존 Development Editor focused 37·broad 204와 독립 명세/품질 검토는 별도 과거 단계의 증거다. 보조 검사 44·242는 Unreal 실행 수에 합산하지 않는다. provenance 구조 단계의 완료도 보존한다. 이번 하네스는 문서 일관성만 검사하며 C++ 동작·새 Capture·실제 입력·reset·발행 권한을 실행 검증하지 않는다. Task 2C의 좁은 파일 경계·실패 검사·남은 acceptance는 [수집 context/lease 구현 계획](scenario-collection-context-v1-implementation-plan.md)에 둔다.

- 계산 의미의 권위: [순수 관측 adapter 계약 §§1–6](scenario-observation-adapter-v1-contract.md).
- 닫힌 artifact/lifecycle의 권위: [수집 데이터 계약](scenario-collection-v1-data-contract.md), [collection Schema](../../contracts/current/scenario_collection_v1.schema.json), [catalog](../../contracts/current/scenario_catalog_v1.json).
- raw wire/namespace/build/권한의 권위: [Runtime import 계약 §§2–4](runtime-capture-import-v1-contract.md). 이 문서는 그 요구를 생산자 호출 경계에 연결한다.
- 실행 순서와 파일 범위: [구현 계획 Task 2](scenario-collection-v1-implementation-plan.md#task-2-실제-관측과-capture-bridge).

Task 3의 trusted owner·runner·화면·실제 reset과 Task 4의 발행 권한 검증·ML import는 후속이다. `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다. Utility 선택·Capture 저장·문서 검사 통과는 Teacher/Human label 또는 학습/Production 승인을 부여하지 않는다.

### 소스 기준과 읽는 방법

아래 경로의 project 기준은 읽기 전용 원본 `/mnt/d/Codex-cli/NeuralProject/NeuralGame`이다. 표의 축약 경로는 `Source/NeuralGame/AINativeNPC/` 아래다. 행 번호와 동작은 Task 2B source snapshot의 안내이며 함수 이름이 추적 기준이다. copy의 Task 2C 구현·실행 상태는 §1과 세부 계획 §2/§10을 따른다. 후속 보완 때 copy source inventory를 다시 고정한다.

| 확인한 현재 소스 | 현재 동작 | Task 2의 연결 책임 |
|---|---|---|
| `Execution/AINativeNPCGoalHostComponent.cpp:1856–1966,2026–2033`, `PrepareDecisionFeatures` / `TryStartCurrentDecision` | capture 직후 승격 전 복사, 현재 pose로 Populate, false이면 Finalize 앞 반환 | Task 2B 연결 보존; 2C는 collection terminal/retry 경계 추가 |
| 같은 파일 `:1664–1842`, `CaptureDecisionForCommit` | Record Build와 pending exact readback이 Commit보다 먼저 실행 | immutable collection metadata와 additive Writer 경로 |
| 같은 파일 `:2071–2115`, `:2156–2231`, `AtomicReserveAndStart` | final 이동·private Skill start 뒤 marker/readback·verified ID | 실제 순서를 보존한 same-image receipt와 bridge |
| 같은 파일 `:3340–3394`, `ScheduleDecisionForAuthority` | Goal instance/revision별 최대 한 번 next-tick retry; weak Host/authority·epoch 비교 | collection terminal latch/lease 검사, legacy 동작 보존 |
| `Knowledge/TypedTargetKnowledge.cpp:55–91`, `Capture` | 저장 위치 유지, 만료 제외, age 갱신 | stale scalar distance 대신 저장 위치 사용 |
| `Feature/DecisionObservationFeatureAdapter.cpp:177–245`, `Populate` | 임시 배열 계산, 성공 시 owned 배열만 publish | 순수 Core 동결, 실제 Host callsite에서 소비 |
| `Dataset/DecisionRecordV2.cpp:592–634` | Writer가 temp 삭제 후 replacing move | additive exclusive/non-replace 경로 필요 |
| 같은 파일 `:637–668` | committed Reader가 Capture 재개방 | additive same-immutable-image receipt 필요 |
| `Dataset/DecisionRecordV2.cpp:386–393`와 `.h:28–39` | 여덟 group의 wire 순서 | 위치·필드 추가 없이 아래 결정론적 값 생산 |

<!-- H:observation -->
## 2. Host 입력과 관측 연결

Host의 `CaptureTargetUniverse` 성공 직후, 어떤 승격·revision 보정도 하기 전에 `KnowledgeBeforePromotion`을 값 복사한다. 기존 Universe로 primary 승격·추가, Slotter, CandidateBuilder를 수행한다. `Draft.Targets`와 `Draft.Candidates`를 채운 뒤 **Finalize 직전**, 다음 입력을 같은 preparation에서 전달한다.

| 입력 | 소유자·시점 | 검증 조건 |
|---|---|---|
| `ObserverTransform` | 현재 Pawn pose, Populate 호출 직전 | finite translation·정규화 quaternion; scale은 거리 배율에서 제외 |
| `GoalToken` | preparation에서 확보한 같은 Goal token | request/finalized 입력과 같은 Goal·phase·revision |
| `KnowledgeBeforePromotion` | capture 성공 직후의 승격 전 복사 | exact handle과 저장된 관측 사실 보존 |
| `FinalUniverse` | 기존 primary 승격/추가 뒤 universe | Slotter가 읽은 동일 universe |
| `PrimaryTarget` | 같은 Goal의 exact PrimaryTarget | Kind·StableId·Generation·Revision 전체 비교 |
| `InOutDraft` | Host가 보유한 실제 Draft | Targets/Candidates 작성 뒤, Finalize 이전 |

거리와 방향은 **stored WorldPosition − 현재 Pawn 위치**에서 계산한다. 저장된 `DistanceCm`를 복사하지 않는다. execution용 primary 승격 위치나 숨은 actor transform으로 관측 위치를 교체하지 않는다. Native store는 age를 갱신하며 저장 시점 distance는 남을 수 있다. `CaptureExecutionTarget`의 현재 actor 위치는 execution authority에만 사용한다.

`Populate=false`이면 전체 Draft를 보존하고 **Finalize·policy·Request·Capture·Commit을 모두 차단**한다. 이전 성공 Snapshot이나 기본값 배열을 새 성공으로 재사용하지 않는다. adapter의 bool은 상세 실패 코드를 제공하지 않는다.

| 보존 대상 | Host 통합 acceptance |
|---|---|
| owned geometry/Goal | cm/radian raw를 generated normalizer에 한 번 전달; Tensor·input hash 변화 확인 |
| observation provenance | exact Knowledge Entity/LastKnownPosition/SoundEvent의 age·confidence·visible만 연결 |
| 위치 전용 primary | Knowledge가 없는 exact Goal-owned primary의 검증된 위치 허용; sensor 사실 기본값 유지 |
| optional missing | T14·T30/T31·G94 sentinel, T15/T25의 기존 기본값 유지; path/LOS 관측 true 발명 금지 |
| 후보·정책 | Targets·Candidates·hard mask·CandidatePair·switch facts 보존; 같은 후보/switch fact에서 현재 Guard Utility 점수·선택 동일 |
| Builder 소유 영역 | reserved/padding/NoTarget zero 유지; adapter 외 health·관계·성격·velocity·event buffer·Entity payload 추정 금지 |

현재 Host의 `TargetLineOfSightValid.fill(true)`·synthetic `bPathReachable=true`는 센서 증거가 아니다. 이 단계에서 mask/Utility 설계를 바꾸지 않는다. 다른 Utility Profile에 점수 보존을 확대하지 않는다.

<!-- H:failure -->
## 3. 회차 실패와 초기화 장벽

승인된 정책은 잘못된 관측 또는 모순된 target 때문에 mapping이 실패하면 해당 수집 회차를 종료하고, 초기화를 확인한 뒤 **새 회차**로 진행하는 것이다. 같은 실패 회차의 Decision retry는 금지한다. 비수집 legacy retry는 유지한다.

Host는 adapter의 `bool` 실패에 `observation_mapping_failed`를 기록한다. 세부 reason은 Host가 **직접 검사한 precondition**이 있을 때만 사용한다. 예를 들어 기존 duplicate exact primary·conflicting mandatory source 분기가 실제로 실행되면 그 검증된 원인을 남길 수 있다. `Populate=false`만 보고 NaN, confidence, stale revision 중 하나를 추측하지 않는다. 모든 Host false를 관측 오류로 일괄 분류하지 않는다.

### 실패 집행 순서와 소유권

1. Host/context는 callback·파일 I/O 전에 현재 회차의 terminal latch를 닫고 epoch/lease를 revoke한다. retry 예약과 이미 예약된 callback, direct decision 진입, receipt publication은 이 latch와 exact World/Host/episode lease를 확인한다. revocation counter는 wrap/reuse를 허용하지 않는다.
2. 현재 authoritative monotonic 시각으로 기존 lifecycle terminal event를 적용한다. deadline 전에는 `failed`; at/after deadline에는 기존 우선순위의 `timed_out`을 보존한다. 실제 관측 실패는 diagnostic에 별도로 남긴다. lifecycle validity를 무시한 강제 failed 기록은 금지한다. lifecycle 검증 예외도 session을 차단한다.
3. Task 2 bridge는 실패 signal과 diagnostic persistence 결과를 owner에게 전달한다. Task 3 owner는 terminal evidence를 persist하고 exact readback한 뒤 reset을 수행한다. terminal evidence 미보존 상태에서는 다음 회차를 허용하지 않는다. terminal 기록과 reset 결과 기록은 새 immutable 파일로 남기고 마지막 episode descriptor는 completion closure에서 선택한다. 기존 terminal 파일을 덮어쓰지 않는다.
4. Task 3 owner가 입력·예약 사건을 정지하고 이전 World/입력/Timer/Skill/Knowledge 수명 종료와 새 World 준비를 확인한다. verified reset receipt는 exact 이전 episode/World lease에 결속한다. bool 성공 선언이나 오류 부재로 검증을 대신하지 않는다.
5. terminal evidence 보존과 verified reset을 모두 확인해야 `새 collection_episode_id`로 진행한다. process sequence는 유지한다. 같은 실패 회차를 retry/reopen하지 않는다. reset failed/unverified 및 저장·sidecar·diagnostic persistence 실패는 더 엄격한 session-blocking 규칙을 유지한다.

**reentrant committed-start stack 안전:** Task 2는 먼저 latch와 lease를 닫고 stop 요청을 보낸다. 현재 authority/context를 local strong pin으로 보존하고 callback 뒤 lease를 재검사한다. stack 안에서 authority/World를 파괴하거나 새 회차를 attach하지 않는다. Task 3 owner가 stack unwound/drained 확인 후 실제 stop/teardown/reset을 수행한다. Task 2의 signal/lease/latch 시험은 owner의 실제 초기화 구현을 대체하지 않는다.

정상적인 아직 못 봄/못 들음, event trigger 미충족은 기존 wait/timeout이다. 유효한 위치 전용 입력·missing sentinel은 정상 입력이다. 이러한 상태를 hard observation failure로 승격하지 않는다.

<!-- H:policy-table -->
### 정책 일관성 표

이 표의 결과 이름은 문서 검사 표기다. 새로운 Schema field 또는 enum을 추가하지 않는다.

| 조건 | terminal outcome | Decision retry | 다음 회차 장벽 | 재개 범위 |
|---|---|---|---|---|
| hard_observation_failure | failed_before_deadline_else_timed_out | suppressed | persist_then_verified_reset | new_episode_only |
| normal_sensor_absence | wait_or_timeout | existing_wait | existing_lifecycle | no_hard_failure |
| position_only_or_missing_sentinel | valid_mapping | existing_policy | existing_lifecycle | no_hard_failure |
| storage_sidecar_diagnostic_failure | failed_before_deadline_else_timed_out | suppressed | session_blocked | never_in_session |
| reset_failed_or_unverified | preserve_terminal_outcome | suppressed | session_blocked | never_in_session |

<!-- H:context -->
## 4. 수집 context와 실제 권한 경계

context는 한 **running** 회차의 immutable 값 묶음이다. validated 값은 복사해서 고정하며 caller mutation이나 다음 회차 교체가 pending Record를 바꾸지 못한다. Host attach는 trusted issuer/owner만 수행할 private 경로다. `public bool/digest setter`로 권한 객체를 만들지 않는다.

| context 입력 | 출처·검사 | 사용 시점 |
|---|---|---|
| `session_id`, `collection_episode_id` | strict lowercase UUIDv4, 외부 session inventory, terminal/reset 이력 | attach·모든 callback |
| `catalog_sha256`, `profile_sha256` | 외부 pin과 validated catalog/execution profile | attach, Record Build 전 |
| `runtime_build_evidence_sha256` | import 계약 §3의 source/binary/receipt/start evidence; session.runtime_build_sha256과 같음 | attach, Record Build 전 |
| `observation_mapping_version` | `observed_geometry_goal_v1` exact | attach·sidecar join |
| `input_source`, `controller`, `execution_mode` | 실제 현재 입력 주체; replay도 현재 값을 사용 | Record Build 전 고정, sidecar |
| map, `family`, `seeds`, limits, root | resolved episode/catalog/profile 일치, stable-root 소유권 | metadata·budget·publication |
| exact World/Host lease + epoch | private owner가 실제 lifecycle에 결속 | direct decision·retry·receipt·detach |

`collection intent`가 있으면 context 부재·preparing/terminal·stale lease·wrong World/Host·invalid source/build를 실패로 처리한다. **legacy fallback 금지**다. intent 자체는 authorization이 아니다. intent가 없는 기존 Host 경로만 legacy 동작을 사용한다.

Task 2C는 [좁은 context/lease 계획](scenario-collection-context-v1-implementation-plan.md)에 따라 copy에 context 검증/attach seam·terminal latch·World 밖 fixture owner를 구현했다. C01–C07 중 context 입력·lease/lifecycle 부분만 다루며 Record metadata·group 생성·committed receipt·실제 저장 완료는 2D/2E acceptance로 남긴다. 실제 등록 test-name과 제한된 실행 checkpoint는 그 계획 §10에 연결한다. **실제 authority 검증은 미구현**이며 Task 3 trusted owner/launcher 및 Task 4 verifier가 외부 evidence를 획득·검사해야 real collection을 열 수 있다. 그 전에는 격리된 `WITH_DEV_AUTOMATION_TESTS` fixture만 허용한다. 일반 public caller가 profile/build digest를 전달하는 것만으로 실제 수집이 시작되는 stub은 금지한다. fixture와 real authority namespace를 분리한다.

World 종료·Host unregister/teardown·terminal/cancel은 lease를 무효화한다. reset 후 새 World에서 DecisionId가 같아도 old callback은 거부한다. root/sequence 수명은 World보다 길다. Task 2가 GameInstance owner를 구현했다고 표시하지 않는다.

<!-- H:metadata -->
## 5. Record 전에 고정하는 producer metadata

수집 context의 provenance는 **Record Build 전**에 설정한다. 원본 Record 생성 뒤 family·source·identity를 고쳐 맞추는 경로는 금지한다. [import 계약 §4.2/§4.4](runtime-capture-import-v1-contract.md#42-여덟-group의-wire-순서)의 wire 위치와 아래 기존 exact 규칙은 변경하지 않는다.

| 필드 | 수집 값 |
|---|---|
| Capture episode_id | `scenario_capture_<session UUID>_<collection episode UUID>_<process sequence>` |
| sequence | 0이 아닌 20자리 unsigned decimal, process-wide checked allocator |
| GeneratorTemplateVersion | `neuralgame_scenario_collection_v1:<catalog SHA256>:<collection execution profile SHA256>:observed_geometry_goal_v1` |
| GeneratorOrRuntimeBuildSha256 | 외부 `runtime_build_evidence_sha256`; session.runtime_build_sha256과 일치 |
| ScenarioFamilyId | resolved episode.family.scenario_family_id = catalog.scenario_family_id |
| MapSeed, SimulationSeed | resolved episode.seeds; 두 값 모두 chosen condition seed와 같음 |
| raw source_type | 모든 생산 phase에서 `2/Dagger` |
| reason tags | `scenario_collection_utility_unreviewed` 포함; 기존 phase별 raw 이유도 보존 |
| Utility label confidence | 기존 Resolve capture-only 0.25, 그 밖의 현재 생산 phase 1.0 보존 |

Utility acceptable mask·selected bool·label confidence는 원본 policy 결과다. Teacher/Human 신뢰도나 source weight로 재해석하지 않는다. raw source enum과 collection `input_source`는 별개다. source/controller/mode는 검증된 현재 context에만 따른다. `resolve_greet_user_play_v1` 문자열에서 `human_play`를 추론하지 않는다. 자동 실행과 automated replay는 `automated_runtime`이다. 실제 human control이 확인된 manual/replay만 human provenance를 가진다.

현재 생산 phase는 InvestigateDisturbance의 Orient/Navigate/Search/Resolve/Return이다. Observe에 가짜 Decision/Capture를 추가하지 않는다. Resolve capture-only를 production Resolve readiness로 승격하지 않는다. 일반 legacy namespace·build-version hash·phase별 metadata는 그대로 유지한다. 관측 연결로 Tensor/input hash가 바뀌는 것은 의도된 차이다.

<!-- H:group-table -->
### 여덟 group의 최소 vocabulary

문자열은 아래 표와 다음 derivation으로 완전히 결정한다. 이는 기존 provenance의 구현 세부사항이다.

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

<!-- H:group-grammar -->
### 값 생성 규칙

모든 값은 공백 없는 **canonical ASCII**다. 대소문자·구분자를 보존한다. string trim/lowercase를 통한 수선은 금지한다.

- `<Phase>` 허용 목록은 `Orient,Navigate,Search,Resolve,Return`이다. 현재 GoalToken의 정확한 enum text 하나만 사용한다. 예: `InvestigateDisturbance:Navigate`. 실제 현재 phase 분류이며 과거 전환 목록 또는 미래 sequence를 뜻하지 않는다.
- `<Kinds>`는 finalized의 `target_mask=true`인 regular slot에서 NoTarget을 제외한 **서로 다른** kind를 generated enum 숫자 오름차순으로 이어 붙인다. 구분자는 `+`다. 허용 enum 순서는 `Entity,SoundEvent,LastKnownPosition,CoverSlot,SmartObject,Waypoint,WorldPosition`이다. 예: `SoundEvent+LastKnownPosition+Waypoint`. count/StableId/Generation/Revision은 grouping 문자열에 넣지 않는다. `empty set -> reject`; 현재 Capture 생산 phase는 유효 primary를 가져야 한다. enum 밖 값·mask/handle 모순은 실패다. 이 목록은 새 scene/feature 지원을 추가하지 않는다.
- `<Modalities>`는 같은 masked kind set에서 Entity가 있으면 `sight`, SoundEvent가 있으면 `hearing`, LastKnownPosition이 있으면 `modality_unknown`을 하나씩 넣는다. 출력 순서는 `sight,hearing,modality_unknown`이며 `+`로 연결한다. 아무 항목도 없으면 정확히 `kind_evidence:position_only`다. 모두 있으면 `kind_evidence:sight+hearing+modality_unknown`이다. 다른 kind는 modality를 추가하지 않는다. visible_now=false 또는 age>0도 kind evidence를 지우지 않는다.

<!-- H:groups -->
### group의 의미·시점·검증 가능성

MapFamily는 실제 selected package `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`에만 `l_ai_native_npc_mvp`를 대응한다. PIE의 자동 prefix를 family로 쓰지 않는다. owner가 exact selected map을 확인한다. OcclusionLayoutFamily는 catalog의 `mvp_unvalidated_layout_v1`을 사용하며 벽/LOS 배치의 검증 완료를 주장하지 않는다. 다른 map/layout은 지원되지 않아 attach 실패다.

GoalSequenceFamily는 현재 GoalToken에서 생성하고 finalized `global_state`의 **G76–83 / G84–91** one-hot와 대조한다. 유효한 하나의 Goal·phase가 표의 허용 집합에 있어야 한다. import는 decoded bytes와 pinned generated enums로 같은 값을 재구성한다. 전체 Goal 이력을 wire에 덧붙이지 않는다.

PerceptionModalityFamily는 **현재 typed evidence 분류**다. Native `TypedTargetKnowledgeComponent.cpp`의 Sight→Entity/LastKnownPosition, Hearing→SoundEvent 경로와 최종 handle kind에 근거한다. Entity/SoundEvent의 sensor 연결은 producer가 같은 exact `KnowledgeBeforePromotion` entry와 대조한다. 현재 Host가 synthetic으로 만드는 primary는 WorldPosition/Waypoint이며, future synthetic Entity/SoundEvent 확장은 자동 허용하지 않는다.

Registry의 `target_authorities`와 `phase_target_policies` 기준 `Orient/Navigate/Search → DisturbancePosition(WorldPosition)`, `Return → HomeWaypoint(Waypoint)`는 `GameplayGoalAuthority` 소유이며 `stored_in_knowledge=false`다. `Resolve → IdentifiedSubject(Entity)`는 `GameplayGoalAuthority` 소유이며 `stored_in_knowledge=true`인 Knowledge-backed primary다.

LastKnownPosition은 Knowledge 관측일 수 있다. 순수 adapter가 허용하는 일반 입력으로는 Goal-owned LastKnownPosition도 가능하다. 이는 Knowledge에 없는 exact PrimaryTarget에 대한 위치 fallback의 허용 범위이며 현재 Host 생산 목록과 구분한다. wire handle만으로 둘의 lineage를 완전히 복원할 수 없으므로 **modality_unknown**으로 명시한다. 이를 hearing/sight로 추측하지 않는다. position_only는 위 세 kind가 없는 구성의 분류이며 센서가 세상에 전혀 없었다는 주장이 아니다. 이 보수적 vocabulary는 0인 confidence/age를 미관측 판정자로 사용하지 않는다. 관측 strength를 Human 신원 확신으로 해석하지 않는다.

TargetCompositionFamily는 finalized `target_mask`와 handle kind에서 NoTarget을 제외하고 중복 제거·enum 숫자 오름차순으로 재구성한다. producer는 Finalize 성공 뒤, Record Build 전에 같은 immutable Snapshot으로 두 group을 계산한다. 후속 importer는 decoded `target_handles`, `target_kind_ids`, `target_mask`의 일치를 먼저 검사한 뒤 문자열을 다시 계산한다. 임의 nonempty string만 통과시키지 않는다.

EventSequenceFamily는 **taxonomy/provenance**인 catalog family다. 현재 지원 값은 `hearing_only_v1`, `hearing_appearance_v1`, `hearing_appearance_loss_v1`이다. 회차 시작 전에 episode/catalog에서 고정한다. 이는 실제 관측 prefix나 미래 사건의 발생 완료 표시가 아니다. 실제 관찰 prefix는 기존 `event_observations`에만 기록한다. `captured_at_server_time`은 World 시각이고 event_observations는 elapsed monotonic 시각이다. 서로 다른 clock의 원점을 잇는 필드가 없으므로 Capture별 관측 prefix를 사후 만들어내지 않는다. 새 wire field·collection field·enum을 추가하지 않는다.

RoleId/PersonalityClusterId는 실제 exact native Guard와 compiled default profile의 식별자 `manny_guard`/`default_guard`다. source/build closure가 이를 결속한다. personality 관측 feature 지원은 추가하지 않는다. template family는 기존 closure에 남고 여덟 wire 위치에 끼워 넣지 않는다.

| 단계 | 검증 oracle | 한계·실패 |
|---|---|---|
| attach | pinned catalog/episode/map/source/build, native class/profile | 미지원·빈 값·모순은 실패; 기본값 수선 금지 |
| producer | current token·pre-promotion Knowledge·finalized handles/mask/Tensor | Record Build 전에 계산·일치 확인; metadata 실패로 production 성공 금지 |
| bridge | same-image expected Record receipt와 immutable context join | group bytes·family·seed·namespace·tag·build 불일치 시 session 차단 |
| 현재 validator | collection Schema·identity·scenario family·seed·same-byte decoder | 여섯 group derivation의 의미 검증 전체는 아직 구현하지 않음 |
| 후속 importer | catalog/episode closure + decoded G76–83/G84–91 + handles/kinds/masks + pinned source/build | 같은 규칙으로 group 대조; raw Knowledge 위치/시각 lineage는 wire만으로 독립 증명 불가 |

실제 Knowledge ingress와 map/Role source의 진실성은 trusted producer/build/start evidence에 의존한다. decoder와 unsigned marker는 이 authority를 발급하지 않는다. group 문자열·catalog 설명·미래 사건·기대 행동·정답은 Tensor/Teacher 입력에 전달하지 않는다. Teacher는 기존 model-visible projection만 받는다.

<!-- H:storage -->
## 6. append-only 저장과 경로 수명

수집 모드의 모든 생산 phase는 동일 저장 경로를 사용한다. process-wide sequence는 0을 쓰지 않고 checked 증가한다. `MAX_uint64` 소진은 영구 fail-closed다. 실패 번호도 재사용 금지다. World 재생성·Host 재설치·회차 종료가 sequence를 reset하지 않는다. 새 process는 새 session UUID와 외부 중복 inventory를 요구한다.

신뢰한 수집 root 아래 final 상대 경로는 `captures/<session UUID>/<collection episode UUID>/<process sequence>.anpccap2`다. sequence의 표현은 raw episode_id와 같은 20자리다. DecisionId를 파일명의 유일한 식별자로 쓰지 않는다. committed-entry sidecar는 `entries/<session UUID>/<collection episode UUID>/<process sequence>.json`, 그 temp는 `.tmp`다. diagnostic은 `diagnostics/<session UUID>/<collection episode UUID>/<diagnostic UUID>.json`과 `.tmp`를 사용한다. IDs/paths는 canonical POSIX 상대 이름이며 같은 path/identity/sample 재발행은 reject한다.

final을 기준으로 `final`, `final.tmp`, `final.pending`, `final.pending.tmp`, `final.committed`, `final.committed.tmp` 모두 예약 충돌 집합이다. 이 이름의 기존 file·directory·alias를 거부한다. final.tmp를 현재 staging 순서에서 사용하지 않아도 충돌 검사에서 제외하지 않는다. sidecar/diagnostic의 final/temp에도 같은 규칙을 적용한다.

### 낮은 Writer 경계의 집행

- `exclusive temp creation` 뒤 완전 write/flush/close를 확인하고 `non-replacing publication`으로 이동한다. pending→final과 marker/sidecar/diagnostic의 temp→final 모두 non-replace다. Host precheck만으로 append-only를 주장하지 않는다.
- precheck 뒤 race로 temp/destination/reserved 이름이 생겨도 이전 bytes/path membership을 보존하고 실패한다. 각 단계 직전 예약 이름·root lease를 다시 확인한다. exclusive root ownership으로 cooperating writers를 직렬화하고 실제 create/move primitive가 마지막 경쟁을 거부한다. 신뢰 root 안의 임의 악성 writer까지 보장하는 주장은 하지 않는다.
- `stable-root ancestors`는 root의 상위 경로부터 실제 목적지 parent까지 보호한다. lexical absolute/drive/UNC/backslash/`..`, resolved alias, symlink/junction·reparse 경로를 거부한다. Windows에서는 component별 reparse 검사를 거친 directory handle을 삭제/rename 공유 없이 유지하고 경로 identity와 root lease를 재검사한다. root/ancestor 치환을 막는 보장이 깨지면 쓰기 전에 session을 차단한다.
- file store는 **소유한** exact temp/pending의 handle/identity만 cleanup한다. 충돌한 파일·다른 attempt의 temp·marker를 지우거나 truncate/replace하지 않는다. 실패 때 기존 bytes/size/hash와 directory membership을 비교한다. 이미 committed된 Capture/marker는 storage 복구나 rollback용 삭제 대상에서 제외한다.
- 현재 `WriteCaptureAtomic`/`WriteCommittedMarkerAtomic`은 temp 삭제·replace를 수행한다. collection은 명시적인 additive API를 호출하며 legacy API/일반 fixed-file 동작은 보존한다. `FILEWRITE_NoReplaceExisting` 상수만 고르는 수정은 충분하지 않다. UE5.7 `FileManagerGeneric.cpp:95–116`은 `OpenWrite`에 전달하고 `WindowsPlatformFile.cpp:1552–1560`의 일반 write는 `CREATE_ALWAYS`다.
- Windows collection file store의 목표 primitive는 exclusive `CREATE_NEW`와 replace 없는 `MoveFileW`다. 후자는 설치 engine의 `WindowsPlatformFile.cpp:1216–1218` 경로도 사용한다. 실제 race·directory/alias/ancestor hostile 검사를 통과해야 한다. primitive·ancestor 보장을 입증할 수 없는 파일시스템 또는 지원하지 않는 플랫폼은 수집을 거부한다. 이 계약의 문서 작성 단계에서는 플랫폼 구현·실행을 하지 않았다. 후속 native root/POSIX artifact 입력 구분·root 소유 수명·실행 범위는 [Task2D 세부 계획](scenario-collection-storage-v1-implementation-plan.md)을 따른다.

이 순서는 파일별 publication이다. **multi-file/gameplay atomic rollback**을 약속하지 않는다. Commit/Skill start 이후 파일 실패는 실행 사실을 소급 취소할 수 없다. crash recovery/save-load는 이 Task의 구현 범위 밖이다. 미완료 pending/raw final은 committed reader에서 수집 성공으로 수락하지 않는다.

<!-- H:order -->
## 7. producer와 bridge의 순서

| 순서 | 작업 | 책임 caller | 실패 경계 |
|---|---|---|---|
| 1 | Finalize | Host, Populate 성공 뒤 | mapping 실패 Draft/이전 Snapshot 사용 금지 |
| 2 | policy selection | 기존 orchestrator | 유효 selected row 없음은 기존 실패 |
| 3 | Request | Host | 동일 Snapshot/token/identity로 pending 설정 |
| 4 | Record Build | CaptureDecisionForCommit | context metadata 고정·ValidateReplay 실패 시 Commit 금지 |
| 5 | pending write + exact readback | additive Writer/Reader | 실패 시 Commit/start 0; 소유 staging만 정리 |
| 6 | Commit + final promote + private Skill start | Coordinator/AtomicReserveAndStart | stale 요청·promotion/start 실패는 producer verified 0 |
| 7 | marker publish | additive Writer | Skill 시작 사실 유지; 미검증 producer 수집 성공 금지 |
| 8 | same-image committed readback | additive Reader | exact Record·marker·bytes 불일치 시 session 차단 |
| 9 | producer verified | Host | SlotHistory와 VerifiedCaptureDecisionIds의 기존 의미 유지 |
| 10 | bridge context join | CollectionCaptureBridge | stale lease·metadata·중복 실패 시 session 차단 |
| 11 | sidecar exclusive publish + exact readback | bridge/file store | 원본 보존, collection accepted 0, session 차단 |
| 12 | collection accepted | bridge | 검증된 entry 하나만 owner에게 반환 |

<!-- H:publication -->
### 같은 byte image의 receipt

**Skill start는 marker보다 앞**이다. `CaptureDecisionForCommit`의 이름은 Commit 이후 저장을 뜻하지 않는다. pending exact readback, Coordinator Commit 내부 final promote/private start, marker, committed readback 순서를 유지한다.

additive committed Reader는 **committed-readback 단계에서 Capture 1회 + marker 1회** 읽는다. pending 검사와 marker 생성의 앞선 I/O는 이 수에 합산하지 않으며, 그 앞선 image가 후속 committed readback을 대신하지 않는다. 읽은 same immutable images로 expected Record equality·marker binding·size/SHA-256을 함께 검증한다.

- 기존 `BuildCaptureEnvelopeBytes(ExpectedRecord)`와 `BuildCommittedMarkerBytes(CaptureBytes)`를 재사용한다. C++ 현재 exact Reader는 expected serialization byte equality를 검사한다. 새 parser 금지다. Python은 기존 `decode_committed_capture_bytes`를 그대로 쓴다.
- `ReadCommittedAndValidateExact`의 기존 signature/호출자는 보존한다. collection용 additive receipt API는 path 기반 기존 Reader를 연쇄 호출해 Capture를 다시 읽지 않는다. 검증 후 hash/parse를 위한 재개방 금지다.
- receipt는 Reader만 생성하는 불변 결과이며 expected Record identity, Capture/marker exact byte images 또는 이들로 계산한 descriptor, producer context/lease를 결속한다. public path+bool/digest 생성자로 성공을 꾸미지 않는다. caller output은 실패 때 미발행 상태로 유지한다.
- bridge는 receipt의 동일 검증 이미지·metadata와 attach context를 대조한다. Record Build 뒤 바뀐 family/build/source를 sidecar로 덮지 않는다. receipt에서 얻은 상대 path·size/hash와 원본 `episode_id/decision_id/input_content_hash/sample_id`를 기존 committed-entry 필드에 넣는다.
- sidecar JSON은 import 계약 §3.1의 `sorted_json_bytes(value) + b"\n"`을 사용한다. exclusive write와 **sidecar exact readback** 뒤에만 collection accepted count와 entry를 추가한다. storage budget에는 Capture·marker·sidecar·diagnostic·index 및 in-flight overhead를 포함한다.
- 같은 identity/sample/path 또는 중복 receipt는 reject한다. 중복 성공 추가·기존 sidecar 덮어쓰기를 허용하지 않는다. 실패 반환과 terminal latch를 함께 유지한다.

`DecisionCaptureWriteSuccessCount`는 pending write 성공, `VerifiedCaptureDecisionIds`는 producer verified, collection accepted는 sidecar까지 검증한 수다. sidecar 실패 뒤 producer verified·실제 Commit/Skill start의 **counter rollback 금지**다. 실패가 발생하면 그 회차/세션의 이후 작업을 막되 과거 성공 사실을 지우지 않는다. marker 이전 실패는 producer verified를 늘리지 않는다.

Task 2 receipt는 최종 발행 authority가 아니다. Task 3 trusted owner가 최종 session·ordered episodes·replay predecessors를 닫고 **publish index last**, exact readback 후 외부 owner storage에 completion pin을 예치한다. 기존 별도 completion_closure를 사용하며 base index에 descriptor/approval 필드를 추가하지 않는다. Task 4가 외부 pin과 closure의 실제 권한을 검증한다. 이 둘의 구현은 미완료다.

<!-- H:diagnostics -->
## 8. 실패 진단과 원본 보존

진단은 기존 diagnostic Schema의 필드만 사용한다. `observed_id`는 실제로 발급·관찰한 ID 또는 null이다. mapping 실패가 Request 생성 전이면 DecisionId를 만들지 않는다. stage는 실제 실패 경계에 맞춰 observation mapping은 `execution`, Capture 검증은 `capture`, I/O는 `storage`, owner 초기화는 `reset`으로 기록한다. bool-only mapping 실패 reason은 generic 값을 사용한다.

메모리 Snapshot/Draft만 있는 경우 `snapshot_present=false`, `snapshot_ref=null`이다. 실제 저장 artifact가 존재하고 immutable bytes의 size/hash가 검증됐을 때만 true/descriptor를 허용한다. **fake Snapshot/hash 금지**다. diagnostic에는 committed capture identity 필드를 추가하지 않는다. diagnostic 수는 committed/Dataset 분모에 들어가지 않는다.

sidecar write/promote/readback/context join 실패는 **session blocked**로 고정한다. **Capture/marker 보존**과 retry/다음 회차 차단을 동시에 검사한다. 이미 발생한 Commit/Skill start를 없던 일로 보고하지 않는다. diagnostic persistence 실패도 memory terminal 상태·실패 반환을 유지하며 completion pin 발행 금지다. 원본을 지워 공간을 확보하거나 로그만 출력하고 성공을 반환하지 않는다.

Task 2 bridge는 diagnostic artifact/실패 receipt를 owner에 전달한다. Task 3는 terminal episode와 reset 결과를 보존한다. owner 미구현 상태에서는 실제 input 중단·reset 성공을 주장할 수 없고 real collection 시작도 닫혀 있어야 한다.

<!-- H:runtime-files -->
## 9. 후속 Runtime의 exact 파일 경계

기준은 `Source/NeuralGame/AINativeNPC/`다. 아래는 Task 2 전체의 파일 경계다. Task 2B Host/tests의 기존 변경은 보존한다. **Task 2C allowlist는 Host .h/.cpp, CollectionContext .h/.cpp, 기존 CollectionHostTests.cpp뿐**이며 [세부 계획](scenario-collection-context-v1-implementation-plan.md)의 exact 목록을 따른다. Dataset/FileStore는 2D, metadata/CollectionCaptureBridge는 2E로 분리한다. 과거 문서-only checkpoint와 이번 상태 문서 작업자의 프로젝트 미수정 사실은 부모의 copy 5파일 구현과 구분한다.

```text
Execution/AINativeNPCGoalHostComponent.h
Execution/AINativeNPCGoalHostComponent.cpp
Dataset/DecisionRecordV2.h
Dataset/DecisionRecordV2.cpp
Collection/AINativeNPCCollectionContext.h
Collection/AINativeNPCCollectionContext.cpp
Collection/AINativeNPCCollectionCaptureBridge.h
Collection/AINativeNPCCollectionCaptureBridge.cpp
Collection/AINativeNPCCollectionFileStore.h
Collection/AINativeNPCCollectionFileStore.cpp
Tests/AINativeNPCCollectionHostTests.cpp
Tests/AINativeNPCCollectionCaptureBridgeTests.cpp
Tests/DecisionRecordV2Tests.cpp
```

<!-- H:boundary -->
### 역할·test seam·단계 경계

| 파일군 | 변경 책임 | 제한 |
|---|---|---|
| Host .h/.cpp | 실제 preparation helper, private context attach, latch/lease, metadata, publication 연결 | 기존 gameplay/Commit 의미 보존 |
| Dataset .h/.cpp | additive exclusive Writer와 same-image Reader receipt | envelope/marker serialization 재사용, legacy API 보존 |
| CollectionContext | immutable validated context, exact lease·revocation | trusted issuer를 public flag로 대체 금지 |
| CollectionFileStore | bounded root/ancestor 보호와 exclusive/non-replace/readback | 저장 framework·플랫폼 확장 제외 |
| CollectionCaptureBridge | receipt/context join, sidecar·diagnostic, 실패 신호 | owner의 입력 정지/World reset 구현 제외 |
| 새 Host/bridge tests | 실제 production seam·fault stage·비진공 oracle | 복제 assembly/mock 성공으로 대체 금지 |
| 기존 DecisionRecordV2Tests | additive writer/reader 및 legacy 회귀 최소 확장 | 기존 fixture 검사 보존 |

새 friend는 `FAINativeNPCCollectionHostTestAccess`로 고유하게 지정한다. forward declaration·friend declaration·정의·wrapper 모두 `WITH_DEV_AUTOMATION_TESTS`로 제한한다. 기존 `ShippingGuardTests`의 `FAINativeNPCGoalHostComponentTestAccess`를 새 translation unit에 다르게 정의하면 ODR 위반이다. 해당 파일 변경은 이 allowlist 밖이다. Host production helper를 호출하는 narrow wrapper를 사용한다.

완료된 `Feature/DecisionObservationFeatureAdapter.h/.cpp`와 원래 `Tests/AINativeNPCObservationFeatureTests.cpp` 37-case 파일은 동결한다. Builder·Coordinator·Knowledge·generated·Schema·asset·ML도 이 slice에서 수정하지 않는다. 필요한 변경이 이 범위를 넘으면 이유와 정확한 파일을 보고한 뒤 범위를 결정한다.

Task 3 GameInstance/runner/UMG와 Task 4 ML 구현은 제외한다. 이번 단계의 문서 검사와 후속 C++ RED/GREEN, 실제 수집, 실제 사람 Play를 별도 증거로 유지한다. Runtime substep은 Host observation → context/lease → store/Reader → metadata/bridge → focused/broad 순서이며 **단일 build owner**가 직렬 실행한다.

<!-- H:acceptance -->
## 10. 후속 실패 검사와 완료 조건

아래 표는 기존 **예상 Runtime RED**와 후속 acceptance를 추적한다. H01–H09에는 Task 2B의 Host 9 실행 증거가 있으며, S01 승인은 §1의 제한된 범위다. C01–C07은 [2C 부분 범위와 후속 범위](scenario-collection-context-v1-implementation-plan.md)로 나눈다. 문서-only checkpoint의 C++/build/Editor/PIE를 **실행하지 않았다**는 기록은 역사적 문서 작업 범위에 한정한다. 부모의 2C copy 실행은 §1에 별도 기록했다. 문서 검사는 표·정책·경계·불변 Schema와 부정 mutation의 일관성만 대상으로 하며 이번 상태 보강 assertion은 아직 실행하지 않았다. 순수 adapter 회귀에 가짜 RED를 만들지 않는다.

핵심 oracle은 nonzero populated Draft 이후 late-row failure, 실제 Host callsite, same DecisionId와 World 재생성, 각 path/race/ancestor, committed-readback의 Capture 1회 + marker 1회, sidecar failure after real commit이다. fake Snapshot/hash 금지와 counter rollback 금지를 독립 검사한다.

테스트는 성공 preparation으로 같은 Draft의 owned/unowned 값을 채운 뒤 앞 row를 바꾸고 늦은 row를 무효화한다. raw 배열·sentinel·mask·후보·identity·switch fact 전체를 field/canonical 기준으로 비교한다. padding을 포함한 C++ object memcmp를 oracle로 쓰지 않는다. 실제 production caller를 거치지 않은 helper 이름·문자열 검사는 Host 완료 증거로 쓰지 않는다.

Task 3 실제 reset/입력 중단 증거는 Task 2 lease/latch fixture와 구분한다. 새 namespace가 발견되지 않은 0-discovery, compile/link error, timeout, 잘못된 import는 행동 RED가 아니다. absent-header assertion은 해당 API 부재만 증명하며 실제 동작은 implementation/mutation에서 다시 검증한다. 새 header 뒤 owning test TU 재컴파일을 확인한다. 발견·시작·종료·report의 exact test-name multiset을 대조한다.

<!-- H:matrix -->
### Runtime 실패 검사와 단계별 증거 범위

아래 C01–C07 행의 마지막 열은 문서-only checkpoint 당시의 gap·단계 소유 설명으로 보존한다. copy에서 추가된 context/lease·owner seam의 현재 상태와 실제 test-name 연결은 [세부 계획 §10](scenario-collection-context-v1-implementation-plan.md#10-c01c07의-단계별-검사-범위)을 따른다. C03의 context 경계·C04의 intent 구분을 현재 copy에도 미구현이라고 재해석하지 않는다. 전체 metadata/저장/reset/권한 acceptance는 그대로 남아 있다.

| ID | 입력·hostile 조건 | 반드시 볼 oracle | 현 상태·소유자 |
|---|---|---|---|
| H01 | 관측 후 Pawn 이동/회전, stored 위치와 stale distance 분리 | cm/radian 및 normalized Tensor가 현재 pose/stored 위치에 맞음 | Task 2B H01 실행 존재; 현 source·새 변경 회귀는 별도 |
| H02 | exact Knowledge primary의 실행 위치를 다른 위치로 승격 | 승격 전 위치·age·confidence·visible 유지 | Task 2B H02 실행 존재; S01은 제한된 증거 결속 승인 |
| H03 | native store capture 시 시간 경과와 동일 관측 위치 | age만 갱신, 미측정 seen/heard 값 발명 없음 | Task 2B H03 NativeAge 실행 존재; 실제 수집 승인 제외 |
| H04 | sensor 없는 exact Goal-owned primary, Home 각각 | 위치 유효, sensor 기본값, sentinel·reserved/padding 유지 | Task 2B H04 실행 존재; owner/collection 저장은 후속 |
| H05 | 유효 slot의 exact 연결 누락/만료·hidden actor만 존재 | 실패 후 Finalize/policy/Request/Capture/Commit 0 | Task 2B H05 실행 존재; collection 종료 정책은 2C |
| H06 | Kind/Generation/Revision·Goal/Knowledge revision 각각 변경 | full handle mismatch 거부·다른 관측 재사용 0 | Task 2B H06 identity/conflict 실행 존재; lease는 2C |
| H07 | 같은 nonzero populated Draft, 앞 row 변경·late-row NaN/연결 실패 | 전체 Draft 보존·이전 Snapshot 새 제출 0 | Task 2B H07 실행 존재; collection terminal/retry는 2C |
| H08 | 같은 후보/switch fact에 서로 다른 관측 | Candidate bytes/mask/Pair·Guard Utility 동일, Tensor/hash 변화 | Task 2B H08 실행 존재; 현재 Guard Utility에 한정 |
| H09 | valid slot·NoTarget·padding·현재 Goal token 조합 | reserved zero·one-hot·primary present exact | Task 2B H09 Finalize 검사 존재; H10 Capture roundtrip 미완료 |
| H10 | 실제 Host Snapshot→Request→Record→Commit roundtrip | immutable Tensor/handle/input identity와 decoder bytes 동일 | fresh observed Capture 경로 미연결 |
| C01 | context 복사 후 caller 원본 family/seed/build 변경 | Build 전 metadata 고정·pending Record 불변 | 현재 hardcoded producer metadata |
| C02 | automatic 및 automated replay 각각 실행 | user_play 오분류 0·catalog family 모든 phase 일치 | 기존 ResolveShadow 상수와 collection 분리 필요 |
| C03 | valid human/fixture와 forged source/controller/build 비교 | 실제 조합만 attach, fixture authority/real count 0 | trusted context 경계 미구현 |
| C04 | collection intent + context 없음/stale/preparing/terminal | legacy fallback 0, 실패 signal/diagnostic | 현재 intent/context 구분 부재 |
| C05 | terminal A 뒤 verified-reset seam의 B, old retry/receipt 전달 | exact lease 거부·B 불변; unverified reset이면 B attach 0 | Task 2 seam 검사, 실제 owner/reset은 Task 3 |
| C06 | 유효 receipt/Utility acceptable mask의 승인 오인 시도 | Approved/ResolvePolicyReady/production_eligible false | 새 bridge가 readiness 권한을 만들지 못함 |
| C07 | group 표 전 조합·빈 값/phase·role·seed 모순, budget 부족 | deterministic oracle 일치, 기본값 수선·budget 초과 0 | 새 vocabulary와 producer/bridge join 미구현 |
| P01 | Orient/Navigate/Search/Resolve/Return 실제 생산 | 전 phase append-only, Observe fake Capture 0 | 현재 non-Resolve fixed-name 삭제 |
| P02 | 서로 다른 Host/episode의 same DecisionId=1 | 새 raw episode/sample/path와 증가 sequence | collection process allocator 미구현 |
| P03 | World A 종료 후 B 재생성, DecisionId 재시작 | A bytes/path 보존, process sequence 연속 | World-independent allocator/lease 신규 |
| P04 | 여섯 예약 path와 sidecar final/temp에 file·directory 각각 | collision 거부, 기존 전체 bytes/membership 보존 | lower Writer temp 삭제·replace 현재 존재 |
| P05 | precheck 뒤 temp/final/marker/reserved 이름 경쟁 | exclusive create/non-replace reject·경쟁 bytes 보존 | Host precheck만으로 막을 수 없는 race |
| P06 | absolute/UNC/../alias/symlink/junction·ancestor 치환 | root 밖 쓰기/삭제 0, root lease 깨지면 block | 실제 Windows root/primitive hostile 필요 |
| P07 | exclusive open/write/flush/close/promote 각 fault | 소유 temp만 cleanup, Commit/start/verified/accepted 0 | additive store fault seam 미구현 |
| P08 | 정상 pending 뒤 bytes 변조·short/trailing·wrong Record | 실제 exact Reader 거부, Commit/start 0 | 기존 Reader 회귀의 collection 경로 확장 |
| P09 | 정상 staging 뒤 stale Request/Goal/target Commit 거절 | 소유 pending retire·marker/verified/accepted 0 | Coordinator 실제 호출, fixture 성공 mock 금지 |
| P10 | final promotion 실패; 별도 start reject+quarantine/delete 실패 | residual raw final의 committed reader 거부 | 기존 start/cleanup 회귀 collection 확장 |
| P11 | 실제 start 성공 뒤 marker create/write/move 실패 | start 사실 유지, verified/accepted 0, session block | Commit 뒤 실패 경계의 신규 모드 검증 |
| P12 | 첫 Capture/marker image 뒤 path 교체·rebound·invalid-first | Capture/marker 각 1회, 동일 bytes equality/size/hash | 현재 C++ committed Reader 재개방 |
| P13 | envelope/marker 변조·rehash와 context/build/group join 불일치 | receipt/sidecar 성공 0·원본 rewrite 0 | same-image receipt/context 검증 신규 |
| P14 | real commit·marker·readback 성공 뒤 sidecar 각 stage 실패 | source Capture/marker 보존·accepted 0·retry/다음 회차 0 | producer verified/start 보존, counter rollback 금지 |
| P15 | same receipt·identity·sample·path 재발행 시도 | 중복 accepted/sidecar 교체 0, reject signal | bridge duplicate ledger 미구현 |
| P16 | memory-only Snapshot과 준비/timeout/mapping/reset 실패 | 실제 observed ID 또는 null, false/null·분모 분리 | fake Snapshot/hash 금지, diagnostic bridge 신규 |
| P17 | 실제 sidecar 실패 뒤 diagnostic 저장도 실패 | memory terminal·실패 반환, completion pin 0 | source 보존·session block 경계 신규 |
| P18 | collection intent 없는 general/ResolveShadow 재실행 | legacy namespace/metadata/cleanup 보존, tensor 변화 허용 | 기존 API 회귀·collection fallback 금지 |
| R01 | 후속 실제 DoMove→Notify→sensing→Knowledge→Goal→Commit | 새 root Capture/marker/sidecar와 관측 Tensor 검증 | Task 3 owner·real input 준비 뒤 별도 실행 |
| R02 | 실제 reset/입력 정지 확인 뒤 새 World 재실행 | 과거 bytes 보존·old events 차단·새 IDs/replay link | Task 3 실제 reset·runner integration pending |
| R03 | 실제 사람이 manual/replay를 조작하고 결과 확인 | 사람 입력·피드백만 사람 Play 증거로 보존 | Automation/facade로 사람 확인 대체 금지 |

<!-- H:commands -->
## 11. 실행 위치와 검증 명령

### 현재 문서 하네스

repo cwd는 `/home/namingsense/AI-Native-NPC`다. 새 private scratch를 만들고 command/exit/stdout/JUnit 및 원본/최종 inventory를 저장한다. 아래 pytest는 문서 검사·기존 repository 회귀다.

```bash
cd /home/namingsense/AI-Native-NPC
PY=/mnt/d/Codex-cli/NeuralProject/NeuralGame/ML/.venv/bin/python
RUN=$(mktemp -d /home/namingsense/.hermes/cache/scratch/host-contract-XXXXXXXX)
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider tests/test_collection_host_bridge_contract_document.py \
  tests/test_runtime_capture_import_contract_document.py tests/test_scenario_collection_contract.py \
  tests/test_decode_anpc_capture_v2.py -q --basetemp "$RUN/focused-tmp" --junitxml "$RUN/focused.xml"
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider -q --basetemp "$RUN/full-tmp" --junitxml "$RUN/full.xml"
git diff --check
```

RED는 새 문서가 없던 기존 계약의 missing/conflicting clause assertion으로 기록한다. missing-import/file-not-found를 행동 RED로 세지 않는다. GREEN 뒤 in-memory negative mutation으로 deadline/retry/reset·publication 순서·group vocabulary 약화를 검출한다. 생성 bytes·fixture·adapter §§1–6 의미·다른 phase 문서의 보존도 별도로 hash/diff 확인한다. 성공 수는 실제 출력과 JUnit을 대조하고 subtests는 별도 집계한다.

### Development Editor 명령 — 이번 문서 단계에서 실행 금지, 부모 전용

소스 확인 주소는 기존 scratch `observation-core-green-_dyczlpc/build-core.bat:2`, `run-core.ps1:33–59`, project `Intermediate/Hermes/RunNeuralGameTests.ps1:1–23`이다. 과거 script는 고정 log/object를 변경하므로 그대로 실행하지 않는다. 아래는 확인한 target/argument interface이며 이번 실행 증거가 아니다.

아래 원본 경로 예시는 과거 argument interface다. Task 2C의 실제 후속 작업은 [세부 계획 §2](scenario-collection-context-v1-implementation-plan.md#2-보존할-구현과-제한된-이전-승인)의 물리 copy `/mnt/d/Codex-cli/NeuralProject/collection-next-uq63w5dx/NeuralGame`에만 적용한다. 원본 경로의 build/script를 실행하지 않는다.

과거 interface의 Windows PowerShell cwd `D:\Codex-cli\NeuralProject\NeuralGame`:

```powershell
& 'C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat' `
  NeuralGameEditor Win64 Development `
  '-Project=D:\Codex-cli\NeuralProject\NeuralGame\NeuralGame.uproject' `
  -WaitMutex -NoHotReloadFromIDE
$buildExit = $LASTEXITCODE
if ($null -eq $buildExit) { throw 'Missing build exit code' }
```

일반 incremental 성공을 실제 collection build 증거로 승격하지 않는다. import 계약 §3의 `clean_or_forced_project_modules` source→binary 결속은 별도 필수다. 코드 단계 승인 뒤 한 build owner가 forced/clean 방식과 보존 범위를 확정하고 실제 compile actions·receipt/module/source closure를 기록한다. `Excluded from unity file`을 compile action으로 세지 않는다.

기존 Automation wrapper의 target interface:

```powershell
$run = 'Task2HostBridge_' + [Guid]::NewGuid().ToString('N')
$tests = @('AINativeNPC.Collection.Host', 'AINativeNPC.Collection.CaptureBridge', 'AINativeNPC.Dataset.RecordV2', 'AINativeNPC')
foreach ($test in $tests) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File 'D:\Codex-cli\NeuralProject\NeuralGame\Intermediate\Hermes\RunNeuralGameTests.ps1' `
    -Test $test -LogName ($run + '_' + $test + '.log') -ReportName ($run + '_' + $test)
  if ($null -eq $LASTEXITCODE -or $LASTEXITCODE -ne 0) { throw 'Automation failed or incomplete' }
}
```

Host filter의 Task 2B 기존 9개를 보존하며 Task 2C last runtime checkpoint에는 추가 검사까지 Host 25개가 있다. CaptureBridge filter는 **후속 등록 이름**이다. Task 2C의 추가 검사는 세부 계획 §10의 actual name과 run report에 결속한다. 기존 Host/Observation만 발견되면 새 context integration은 실행되지 않은 것이다. wrapper 자체에는 timeout/ownership 보호가 없으므로 실제 실행 harness는 retained `System.Diagnostics.Process`와 900초 timeout, owned PID/exit, unique evidence path, process preflight를 적용해야 한다. 다른 소유자 process는 종료하지 않는다. null exit/timeout/0-discovery는 실패다. command-line의 TestExit 문자열을 emitted queue completion으로 세지 않는다. StopTestSession·완료 report·실제 exit와 exact name multiset, warning/skipped/notRun/inProcess를 각각 대조한다.

**보존 전제:** 기존 `Tests/AINativeNPCShippingGuardTests.cpp:1576–1578,1635–1637,1682–1686`은 `Saved/AINativeNPC/Capture/Phase3B`를 삭제한다. broad 실행 전에 이 경로의 **preserved-source inventory**를 만들고 보존 대상이 있으면 live project 실행을 중단한다. 승인된 격리 workspace에서 source/binary를 새로 결속하거나 owner가 승인한 보존·복원 절차를 먼저 확정한다. 고유 log 이름만으로 destructive fixture 격리가 되지 않는다. 새 bridge disk case는 별도 private test root를 쓴다.

실제 Capture 검증은 후속 real run의 exact path로 `python -m tools.validate_anpc_capture_v2 "$CAPTURE" --json`을 사용한다. 상세 payload는 같은 module의 `decode_committed_capture_bytes` 함수다. 새 decoder CLI/parser를 만들지 않는다. `tools.validate_scenario_collection --catalog`는 catalog-only CLI이며 session/index는 기존 library API다. ML `capture import`/`collection validate`/`collection coverage`는 Task 4 목표 interface다. 이번 단계에서 ML·provider/network·training·Shipping/cook/package·commit/push는 수행하지 않는다.
