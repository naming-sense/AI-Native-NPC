# 일반 플레이 수집 세션·초기화와 최종 목록 저장 V1 구현 기준

**목표:** 사람이 일반 플레이에서 수집을 켜고 중단하거나 새 회차를 시작하며, 저장된 결과를 최종 index 파일로 남기는 최소 연결을 구현한다.

**구조:** GameInstance subsystem이 World보다 오래 살아 있는 session ledger·예산·metadata·발행 권한을 소유한다. Host는 실제 회차의 immutable context/lease만 소비한다. 최종 index는 종료된 session의 동결 ledger에서 만든다.

**기술:** Unreal Engine 5.7 C++, 기존 native FileStore·CaptureBridge, Python 문서 pytest 및 기존 collection validator.

**구현 대상:** 기존 `NeuralGame` Game target과 설치 엔진을 사용하는 별도 Development Game 경로다. 빌드·cook·게임 실행과 수집 통합 확인은 사용자 담당이다. 과거 실행 대상 선택은 유지하며 AI의 실행 권한은 아래 구현 전용 작업 방식으로 교체한다.

**함께 읽을 문서:** [Runtime 수집 자료의 ML 가져오기 V1 계약](runtime-capture-import-v1-contract.md), [별도 Development Game 보충 설계의 공개 보관본](development-game-launch-slice-01.md).

## 0. 현재 작업 방식 — 문서 태스크 단위 구현 전용

사용자는 이 문서의 태스크 덩어리를 한 번에 구현하고 검토·검증·구현 확인을 직접 담당한다. 이 절은 아래의 과거 하네스·실행 순서·검증 지시보다 우선한다.

- AI의 작업 단위는 §12.2의 구현 태스크 2–6이다. 태스크마다 선언·본문·호출 경로·관련 파일 연결을 한 묶음으로 작성한다.
- helper·함수·파일 읽기·통신 단계별 새 문서/검사/구현 위임으로 다시 쪼개지 않는다. 서브에이전트를 쓰면 문서 태스크 전체를 한 구현 작업자에게 맡긴다.
- AI는 구현에 필요한 문서·소스·API 정의를 읽고 코드를 작성한다. 검토, 코드 리뷰, 실패 재현, RED/GREEN, 검사 전용 하네스/probe 작성, 빌드·테스트·lint·정적 검사·전체 회귀·PIE·cook·게임 실행·해시 대조·실파일 재검증·보고 검사기를 수행하지 않는다.
- §11, §12.1 및 §12.4의 검사·실행 항목은 사용자 확인용 참고다. AI의 선행 조건이나 남은 실행 할 일로 사용하지 않는다. 과거 build/cook 승인은 현재 구현 작업의 실행 권한으로 재사용하지 않는다.
- 제품 자체의 입력 검증·권한·수명·예산·저장 보호 계약은 유지한다. 개발 검증 생략은 제품 보호 로직을 제거하거나 가짜 성공을 만드는 허가가 아니다.
- 기존 코드·테스트·수집 파일·역사적 실행 증거를 보존한다. 기존 검사를 다시 실행하거나 결과를 덮어쓰지 않는다.
- AI는 `코드 작성 완료`와 `남은 구현`을 인계한다. 검토·검증·구현 확인은 `사용자 담당`이다. 작성 완료를 동작 확인이나 승인 완료로 표현하지 않는다.
- 사용자가 이후 특정 검토나 실행을 직접 요청한 경우에만 그 요청 범위에 한정한다. commit/push·Shipping·관리자 실행은 계속 별도 명시 요청 사항이다.

**문서 작성자 인계 당시 상태:** 문서·문서 하네스 작성 단계다. **문서 하네스 미실행**, C++ 미수정, Unreal/build 미실행이다. 본문의 새 클래스·함수·명령·파일은 부모 구현 대상으로 제안한 이름이다. 부모의 후속 실행 상태는 별도 evidence에 기록한다. 독립 검토를 요청하거나 추가하지 않는다.

<!-- PS:scope -->
## 1. 적용 범위와 선행 기록

문서 작성자 인계 당시 상태는 **문서 하네스 미실행**이다. 부모의 후속 실행 결과는 별도 evidence에 기록한다.

- **PS01**: 이번 범위는 일반 플레이의 수동 수집 start/stop/new episode, 실제 GameInstance 소유 수명, 최종 index 저장이다. 독립 검토는 사용자 요청으로 생략한다.
- **PS02**: Approved=false; ResolvePolicyReady=false; production_eligible=false를 유지한다. 일반 플레이 수집 활성화 허용은 학습·Resolve policy·ML import 승인이 아니다.
- **PS03**: 문서 작성자는 신규 문서·신규 문서 하네스·지정 design-handoff만 작성한다. 기존 문서·tests·C++는 읽기 전용이며 Unreal/build/terminal/execute_code/commit/push/skill 변경은 수행하지 않는다.

권위는 `scenario-collection-v1-data-contract.md`, `scenario-host-capture-v1-contract.md`, `scenario-collection-v1-implementation-plan.md` Task 3, `runtime-capture-import-v1-contract.md` §§2–3과 `contracts/current/scenario_collection_v1.schema.json`, `contracts/current/scenario_catalog_v1.json`이다. 이번 문서는 Task 3 전체 UI/자동/replay 범위를 승인하지 않는다. 기존 문서의 production collection closed는 당시 단계의 경계다. 이번 요청은 아래 private runtime issuer와 수동 경로만 추가로 허용한다. 학습/정답/Resolve 승인 경계는 그대로다.

선행 실제 구현 기록은 `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/publication-runtime-implementation-01/implementation-result-01.md`다. 거기에는 Host 97·broad 347, 실행별 committed JSON 20·diagnostic JSON 4, macro-off compile 8 TU·preprocess 2 TU가 기록돼 있다. 이는 **역사적 선행 실행**이며 이 문서의 새 구현이나 문서 하네스 실행 결과가 아니다.

현 소스에서 확인한 경계:

- `Collection/AINativeNPCCollectionContext.h/.cpp`: Context/Lease/FixtureSession constructor와 fixture payload issuer가 dev-only다. World 독립 `FAINativeNPCCollectionFixtureSession`에 root, 누적 budget, index bytes, accepted/diagnostic entry 배열이 이미 있다.
- `Execution/AINativeNPCGoalHostComponent.cpp`: `TryAttachOwnedCollectionForTest`, `TryBindCollectionStorageForTest`는 테스트 경로다. `ReserveCollectionPublication`, `TryPublishCollectionReceipt`, failure diagnostic과 실제 phase hook은 runtime 경로다.
- `Collection/AINativeNPCCollectionFileStore.cpp::IsCanonicalJsonRelativePath`: 현재 entries/diagnostics의 네 segment만 받는다. session/episode/index를 저장할 새 purpose와 닫힌 경로 검사가 필요하다.
- `Execution/AINativeNPCSkillExecutorComponent.h/.cpp`: `GetStatus`, `IsIdleTimerActive`, `IsExecutionTimerActive`가 있다. `bResultDispatchInProgress`, `bExternalEffectInProgress`, `mCommittedGreetStartInProgress`는 내부 상태다. 기존 `EndPlay`는 dispatch 플래그를 초기화하므로 실제 drain 증명이 될 수 없다.
- `Config/DefaultEngine.ini`: 기본·Editor map은 ThirdPerson이다. 수집을 위해 Config를 바꾸지 않는다.
- `NeuralGame.Build.cs`: Engine/Json/UMG 및 Editor 조건 UnrealEd 의존성이 이미 있다. 새 UI나 모듈 의존성 추가는 필요하지 않다.

<!-- PS:files -->
## 2. 작성 범위와 부모 구현 exact allowlist

- **PS04**: 부모 구현은 아래 exact allowlist만 사용한다. Config·Content·PlayerController·Build.cs·Schema·catalog·generated·Builder·serializer·ObservationAdapter·Coordinator·ML과 기존 tests는 보존한다.

문서 작성자의 쓰기 허용 파일은 다음뿐이다. 나머지는 읽기 전용이다.

- `/home/namingsense/AI-Native-NPC/docs/current/scenario-collection-play-session-index-v1-implementation-plan.md`
- `/home/namingsense/AI-Native-NPC/tests/test_collection_play_session_index_document.py`
- `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/design-handoff-01.md`
- `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/design-handoff-01.json`

위 목록과 PS03은 최초 문서 작성 인계의 범위를 보존한 기록이다. 이번 실행 대상 보정 작성자는 이 활성 계획과 evidence root의 `development-game-launch-slice-01.md`, `play_session_game_plan.py`, `test_play_session_game_plan.py`, `development-game-plan-red-handoff-01.json/.md`, 추가 문서 하네스 `tests/test_collection_game_launch_document.py`만 쓴다. 기존 문서 하네스·L1/L2a·launcher·normative Schema/validator는 동결한다. Engine·Target.cs·Build.cs·plugin·Content·Config 편집 권한을 추가하지 않는다.

후속 사용자의 `해당 설정 수정 승인`에 따라 §12.4 DG09의 조건부 public-header include 경로 한 항목과 대응 문서·검사를 추가로 허용한다. 이 한정 예외가 PS04와 위 실행 대상 보정의 Build.cs 보존 범위에 우선한다. 나머지 보존 조건과 기존 검사 본문은 유지한다.

다음 경로의 기준 root는 `/mnt/d/Codex-cli/NeuralProject/NeuralGame`이다. 부모는 실행 소유자이며, 실제 수정 전에 이 범위와 최신 작업 중 변경을 고정한다. 아래 범위로 해결되지 않으면 무관한 파일을 조용히 추가하지 말고 인계 범위 변경을 명시한다.

| 파일 | 작업 | 허용 변경 |
|---|---|---|
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionSessionSubsystem.h | 신규 | GameInstance owner·typed 공개 요청 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionSessionSubsystem.cpp | 신규 | nondev console·수명·reset·최종 저장 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionRuntimeInputs.h | 신규 | owned validated inputs·private issuer |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionRuntimeInputs.cpp | 신규 | strict metadata·실제 build/start binding |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionContext.h | 수정 | runtime-private 생성·session ledger 재사용 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionContext.cpp | 수정 | 공통 검증·runtime namespace·lease 발급 |
| Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGoalHostComponent.h | 수정 | owner-only attach/stop/관측 경계 |
| Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGoalHostComponent.cpp | 수정 | 실제 assembly rendezvous·stop·ledger 연결 |
| Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSkillExecutorComponent.h | 수정 | collection-only stop/drain 관측 |
| Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSkillExecutorComponent.cpp | 수정 | 실제 timer/move/dispatch 정지 확인 |
| Source/NeuralGame/AINativeNPC/Player/PlayerNoiseEmitterComponent.cpp | 수정 | collection preparing/stop 때 발소리 발행 차단 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionCaptureBridge.h | 수정 | typed session/episode/index encoding |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionCaptureBridge.cpp | 수정 | canonical JSON·ledger index·budget 경계 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionFileStore.h | 수정 | owner-private purpose publication 요청 |
| Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionFileStore.cpp | 수정 | 닫힌 path grammar·nonreplace/readback |
| Source/NeuralGame/AINativeNPC/Tests/AINativeNPCCollectionPlaySessionTests.cpp | 신규 | AINativeNPC.Collection.Host.PlaySession.* |

`FAINativeNPCCollectionFixtureSession` 이름은 변경폭을 줄이기 위해 유지한다. subsystem의 실제 owned instance가 일반 session ledger가 된다. ctor를 그냥 public으로 풀지 않는다. owner-private runtime constructor/factory를 추가하고 dev-only라는 현재 주석을 역할에 맞춘다. 테스트 namespace와 minting은 계속 dev-only다. 이름 변경 자체를 GameInstance ownership의 증거로 사용하지 않는다. 새 멤버는 protected `m` 접두어, 실패 우선, 다음 줄 중괄호를 따른다.

<!-- PS:entry -->
## 3. 실제 일반 플레이 진입과 닫힌 옵션

- **PS05**: UAINativeNPCCollectionSessionSubsystem은 새 UGameInstanceSubsystem owner다. 실제 nondev console WithWorld 진입이 typed closed parameters로 owner를 호출하며 dev wrapper를 production 진입으로 사용하지 않는다.
- **PS06**: 기본 수집은 꺼져 있다. start는 MVP Game/PIE World·authority·exact native Guard/Host·단일 local Player.Main·실제 controller provenance·owned runtime inputs를 모두 검사한다. 잘못된 map은 거부하며 기본 ThirdPerson Config를 바꾸지 않는다.
- **PS07**: collection intent의 preparing/missing context/stale lease는 legacy fallback을 금지한다. intent 없는 일반 플레이의 입력·Goal·Capture·ResolveShadow 동작은 보존한다.

아래는 **새로 제안**하는 공개 경계다. `FAutoConsoleCommandWithWorldAndArgs`를 subsystem cpp에 등록한다. `FConsoleCommandWithWorldAndArgsDelegate`가 준 exact World에서 GameInstance와 subsystem을 찾는다. 전역 첫 World나 첫 Player를 대신 선택하지 않는다. Unreal의 bool parser로 authority 인수를 받지 않는다.

| 명령 | 인수 | 효과 |
|---|---|---|
| anpc.Collection.Start | 인수 없음 또는 scenario distance angle seed | 닫힌 값 파싱 후 RequestStartManual |
| anpc.Collection.NewEpisode | 인수 없음 | 현재 조건 유지·새 ID·실제 fresh World barrier |
| anpc.Collection.Stop | 인수 없음 | cancel 또는 기존 terminal 유지·drain·최종 index |

새 C++ entry는 `RequestStartManual`, `RequestNewEpisode`, `RequestStop`이다. 첫 요청은 공개 mutable ContextInput 대신 `FAINativeNPCCollectionManualOptions`라는 신규 값 타입으로 받는다. scenario는 닫힌 enum, distance는 400/600, angle은 0, seed는 0/1/2만 표현한다. 문자열 console 경계는 정확한 인수 수·철자·정수 문법을 검사하여 이 타입으로 바꾼다. option에는 path, hash, controller/source/mode, 승인 bool, reset receipt, class/asset/command가 없다. public start 결과는 started/pending/rejected 및 reason을 나타내는 값이며 authority 객체가 아니다.

| 항목 | 고정 기본값 |
|---|---|
| enabled | false |
| scenario_id | hearing_only |
| distance_cm | 400 |
| approach_angle_deg | 0 |
| seed | 0 |
| max_episodes | 2 |
| episode_timeout_seconds | 30 |
| preparation_timeout_seconds | 10 |
| max_decisions | 100 |
| storage_limit_bytes | 67108864 |
| split | unassigned |

이 예산과 회차 수는 이번 최소 수동 도구의 보수적인 실행 기본값이다. 학습량·coverage 기준이 아니다. 예산은 첫 쓰기 전 필요한 reservation을 만족하는지 실제 계산하며 부족하면 시작을 거부한다. 공개 명령으로 limits를 변경하지 않는다. 신뢰한 실행 profile과 이 기본값이 다르면 실패한다.

카탈로그의 `hearing_only`, `hearing_appearance`, `hearing_appearance_loss`만 선택한다. `relationship_friendly`, `relationship_hostile`, `low_identity`, `unreachable_greet`는 기존 제외 이유를 반환한다. `support_semantics=code_supported_pending_runtime_validation`을 유지한다. scene 성공이나 벽 가림이 이미 검증됐다고 표시하지 않는다.

입력·대상 검사는 Game/PIE와 해당 GameInstance, standalone authority, local player 목록과 실제 소유 Controller/Pawn 관계, 단 하나의 `Player.Main`, exact native `AAINativeNPCGuardPawn`와 연결된 GuardController/Host/Knowledge/Executor/StateTree/GoalTimer를 함께 본다. Quinn mesh·noise emitter·sensor profile 준비도 실제 객체에서 검사한다. dedicated server, client, split screen, 추가 Guard, transient test World를 manual 경로에서 거부한다. `GetPlayerController(0)` 성공 하나만으로 단일 플레이어를 증명하지 않는다.

설치된 UE 5.7 소스에서 확인한 API 근거:

- `Engine/Source/Runtime/Engine/Public/Subsystems/GameInstanceSubsystem.h`: GameInstance 수명과 `GetGameInstance`.
- `Engine/Source/Runtime/Engine/Classes/Engine/GameInstance.h`: `GetSubsystem`, `GetLocalPlayers`.
- `Engine/Source/Runtime/Core/Public/HAL/IConsoleManager.h`: `FAutoConsoleCommandWithWorldAndArgs`, delegate의 `(TArray<FString> const&, UWorld*)` 입력.
- `Engine/Source/Runtime/Engine/Classes/Kismet/GameplayStatics.h`: `OpenLevel`은 반환값 없는 travel 요청이다. 호출 성공을 reset 성공으로 사용할 수 없다.

<!-- PS:inputs -->
## 4. 실제 metadata package와 private issuer

- **PS08**: context/lease/session 생성과 Host attach는 owner-private runtime 경로다. public bool/digest/fixtureResetReceipt와 TryAttachOwnedCollectionForTest 또는 TryBindCollectionStorageForTest 호출로 실제 허가를 만들지 않는다.
- **PS09**: catalog/profile/schema/build는 실제 파일 bytes와 독립 launcher 관측을 검증해 owned 값으로 고정한다. FApp::GetBuildVersion 문자열 hash·임의 hex·caller expected 값은 실제 runtime build identity를 대체하지 않는다.

### 4.1 현재 저장 위치와 새 배치 위치

권위 catalog/schema는 현재 문서 저장소의 `contracts/current/`에 있다. project Source/Config/Build.cs 검색에서 이 catalog를 일반 runtime에 전달하는 package 경로는 확인되지 않았다. 현재 Host `ComputeRuntimeBuildHash()`는 `FApp::GetBuildVersion()` 또는 fallback 문자열을 사용한다. fixture 테스트는 입력 문자열을 공급한다. 이 두 경로를 실제 수집 metadata로 재사용하지 않는다. 따라서 **catalog package availability**와 **actual runtime build identity**의 배치·실제 로딩이 이번 runtime 연결의 필수 작업이다.

Development 실행용 고정 package root를 project `Saved/AINativeNPC/CollectionRuntime`로 새로 정한다. 부모의 신뢰한 준비/launch 도구가 현재 source로 실제 build를 완료한 뒤 exclusive staging·readback하여 공급한다. 기존 runtime package를 임의로 덮어쓰지 않고 실행별 고정 하위 디렉터리를 선택하는 bootstrap이 소유한다. public console에서 그 경로를 받지 않는다. 이 경로는 Development용 loose metadata다. cooked Content나 Shipping package availability를 주장하지 않는다.

package 파일 이름은 `catalog.json`, `collection-schema.json`, `capture-schema.yaml`, `skill-registry.yaml`, `goal-registry.yaml`, `execution-profile.json`, `utility-profile-source.json`, `runtime-build-evidence.json`, `session-start-evidence.json`이다. 원본 Schema/registry bytes와 compiled/generated contract identity를 대조한다. catalog만 strict parse 뒤 `catalog_digest`와 같은 canonical object without LF로 hash한다. descriptor는 원본 파일 exact bytes를 hash한다. profile/build/start evidence의 JSON은 기존 provenance schema와 계약에 따른다.

### 4.2 검증과 소유권

1. 부모 launcher가 `independent_out_of_band`로 선택한 trusted project/authority/evidence base, source inventories, 실제 강제 build command·exit·log·receipt·module artifacts·engine/toolchain identity를 고정한다. `source_inventory_before`와 `source_inventory_after`는 membership까지 같아야 한다. `build_mode=clean_or_forced_project_modules`이며 incremental 성공만으로 채우지 않는다. 선택 MVP Content dependency closure도 포함한다.
2. 새 process를 시작해 PID와 OS process-start identity, actual executable/loaded-module 경로·크기·digest, Live Coding/hot reload 부재를 관측한다. 기존 Editor 재사용이나 가장 최근 DLL 선택으로 대신하지 않는다. `loaded_module_inventory`는 실제 loaded module을 receipt와 대조한다. 최소 변경으로 live module identity 관측이 구현되지 않았다면 실제 수집을 열지 않고 해당 blocker를 명시한다.
3. 신규 RuntimeInputs loader는 trusted bootstrap이 소유한 package와 독립 pin을 읽는다. 제출 JSON에 담긴 expected digest와 같은 JSON의 digest를 비교하는 self-assertion 경로를 만들지 않는다. root의 물리적 identity·alias·stable ownership, schema closed fields·duplicate keys·정수/유한값, 현재 source/loaded binary와 고정 build evidence를 검사한다. launcher 설정 bool만으로 통과시키지 않는다.
4. session ID는 owner가 발급·영구 예약한다. start evidence는 그 ID와 실제 실행 중인 process 관측을 결속해 저장한다. launcher가 미리 만든 process 관측 부분을 쓰더라도 다른 session ID를 복사하지 않는다. 읽은 profile/build/catalog/schema와 start evidence는 immutable owned 값 및 보관 bytes로 고정한다.
5. 신규 `FAINativeNPCCollectionValidatedRuntimeInputs`의 생성은 검증 구현 내부로 제한한다. owner는 이 객체와 실제 World/Host 준비 관측으로 ContextInput을 구성한다. 독립 검증이 필요한 값과 caller 선언을 구조적으로 분리한다. Context/Lease의 runtime constructor는 private friend 경계로만 호출한다.
6. collection runtime namespace는 새 `play_session_runtime_v1`, fixture namespace는 기존 `host_transient_fixture_v1`로 구분한다. fixture minting·test-only expected의 이름을 바꾸거나 macro를 걷어내는 구현은 금지한다. 공통 구조 검증은 분리할 수 있으나 runtime authority 획득은 별도다.

기존 FixtureSession ledger를 GameInstance owner가 실제 strong ownership한다. owner는 root/thread/limits/used IDs/previous lease/index reservations를 World 교체 동안 유지한다. Host storage bind는 owner가 획득한 같은 native root를 이용하는 새 private runtime 경로다. 빈 constructor 또는 hash 문자열 비교만으로 issuer가 완성됐다고 표시하지 않는다.

신뢰 전제는 설치 engine/toolchain과 collector/launcher가 소유한 private stable 저장소다. hostile arbitrary in-process C++·관리자 권한 process를 방어하는 완전한 원격 attestation은 이번 범위가 아니다. local 파일 hash 성공도 ML completion authority를 만들지 않는다.

<!-- PS:lifecycle -->
## 5. 처음 시작·다음 회차·실제 사건 관측

- **PS10**: session_id와 collection_episode_id는 재사용 없는 lowercase UUIDv4다. Capture episode_id와 process-wide nonzero sequence는 별개이며 World reset·session 종료로 재설정하지 않는다.
- **PS11**: 첫 회차는 현재 World/Host/Player의 pristine 준비 관측을 요구한다. 다음 회차는 이전 terminal persist/readback·실제 drain·이전 World cleanup·다른 World identity·새 assembly 준비·reset 결과 persist/readback 뒤에만 fresh ID로 attach한다.
- **PS12**: 동시 회차는 하나다. preparation 포함 monotonic deadline을 사용하며 at/after deadline은 timed_out 우선이다. completed는 실제 사건 전체 prefix가 deadline 전에 관측됐을 때만 허용한다.

### 5.1 상태와 실제 작업

owner 내부 상태는 Idle → Preparing → Running → StopRequested → Draining → TerminalPersisted로 진행한다. 그 뒤 사용자가 NewEpisode를 요청하면 AwaitingFreshWorld → Idle/Preparing, Stop을 요청하면 Finalizing → Finalized로 진행한다. Blocked는 sticky다. 이 이름은 내부 enum 설계이며 collection wire state를 확장하지 않는다.

시작 전에 limits·metadata·native root·session ID inventory와 필요한 terminal/index 예산을 확보한다. `sessions/<id>/session.json`의 CREATE_NEW/readback은 session ID의 영구 예약이 된다. 기존 root에서 이미 예약된 ID를 재사용하지 않는다. `mUsedEpisodeIds`와 immutable preparing 파일이 episode 재사용을 막는다. 생성 실패 ID도 재활용하지 않는다. 프로세스 간 crash-recovery/resume는 구현 범위 밖이며 남아 있는 이름·bytes는 계속 충돌 대상이다.

현재 MVP World가 이미 진행돼 pristine하지 않으면 기록을 조작해 첫 회차에 붙이지 않는다. 최소 구현은 명시적 Start를 받은 뒤, 소유한 입력/old assembly를 안전하게 정지하고 같은 map을 한 번 새로 열어 bootstrap한다. 이는 episode를 아직 붙이지 않은 초기화다. old World에서 발생한 판단을 새 회차로 소급 수집하지 않는다. 초기화가 없던 경우에도 현재 World가 해당 process/GameInstance의 준비 조건을 충족했다는 관측이 필요하다.

Host `BeginPlay::TryInstallAssembly`와 최초 dispatch 사이에 owner rendezvous를 새로 연결한다. owner에 시작/회차 준비 intent가 있으면 이 World의 Host는 preparing collection fence를 먼저 설치한다. running context가 아직 없을 때 legacy decision으로 빠지지 않는다. intent가 없는 Host의 기존 BeginPlay 흐름은 그대로다. 자동 Start를 모든 map BeginPlay에 넣지 않는다.

### 5.2 placement와 수동 사건

`distance_cm`, `approach_angle_deg`, seed는 이름표가 아니라 실제 준비 조건이다. 준비 단계는 catalog가 허용한 player/Guard 배치만 수행한다. 신규 preparation에서 Guard의 초기 home transform을 기준으로 player를 선택 거리의 시야 밖 위치에 배치하고, angle=0의 접근 기준을 고정한다. 실제 collision/sweep·nav/ground/mesh/emitter 준비와 readback pose를 확인한다. 배치가 허용 오차 안에 실제 성립하지 않으면 preparing 실패/timeout이며 다른 조건으로 조용히 변경하지 않는다. 구체적인 좌표계·허용 오차는 기존 catalog에 정의돼 있지 않으므로 §12의 구현 전 확정 항목으로 남긴다. scene 편집·벽 가림 가정·Knowledge/Tensor/센서 값 주입은 허용하지 않는다.

준비 중에는 입력과 emitter를 막고 collection decision을 시작하지 않는다. `HasBegunPlay`, exact native assembly·identity, 새 Knowledge/Timer/Executor 상태, player 준비를 관측한 뒤 immutable context/lease를 같은 GameThread 경계에서 설치한다. preparation 시작 origin을 running attach에서 재설정하지 않는다. 첫 running tick 전에 입력 제한을 소유량만 해제한다.

수동 실행은 실제 `ANeuralGameCharacter::DoMove` → Animation Notify → `UPlayerNoiseEmitterComponent` → Hearing/Sight → Knowledge → Host의 기존 경로를 사용한다. source의 실제 hearing, appearance, target loss 사실을 owner에게 read-only 관측으로 전달한다. `event_observations`는 순서가 맞는 prefix만 기록한다. `move_for_hearing`은 실제 movement와 authored notify/hearing 관측을 요구한다. `appear`와 `lose_target`는 앞 사건 이후 실제 sight 획득/상실을 요구한다. catalog timeout·movement duration을 위반하면 성공 사건을 만들지 않는다. 자동 player 이동 연출·NPC 상태 강제 변경은 추가하지 않는다.

모든 prefix가 기한 전에 성립하면 completed로 종료할 수 있다. 사용자가 먼저 Stop/NewEpisode를 요청하면 cancelled와 실제 reason을 남긴다. 관측 오류는 deadline 전 failed, 이후 timed_out이다. max_decisions 도달은 더 쓰지 않고 cancelled/decision_limit_reached로 종료한다. full-prefix completed 또는 timeout이 이미 관측됐다면 그 결과를 보존한다. max_episodes가 소진되면 NewEpisode를 거부하고 Stop을 통한 최종화를 허용한다.

### 5.3 새 World 장벽

`UGameplayStatics::OpenLevel`은 고정 catalog MVP map에만 호출한다. 호출 후 반환은 성공 receipt가 아니다. `FWorldDelegates::OnPostWorldCleanup`에서 exact old World의 종료를 관측하고, 같은 GameInstance에 속한 새 World의 준비를 따로 기다린다. `UWorld::OnWorldBeginPlay`/`HasBegunPlay`와 현재 객체를 검사한다. 기존 코드의 `Lease::IsBoundToWorld`처럼 WeakObject index+serial로 비교하며 두 null weak pointer의 같음을 새로운 World 증거로 사용하지 않는다.

새 Pawn/Controller/Host/Knowledge/StateTree/Timer/emitter identity를 이전 것과 대조한다. old input target·예약 callback·executor result sink가 새 객체를 가리키면 실패다. 소멸/cleanup·drain·준비를 전부 확인하고 이전 회차의 reset_result=verified 파일을 publish/readback한 뒤에만 다음 ID를 발급·attach한다. failed/unverified는 세션을 막는다. guard나 Pawn transform만 되돌리는 soft reset은 fresh World를 대신하지 않는다.

NewEpisode는 같은 조건의 새 수동 회차다. 실행 mode를 replay로 바꾸지 않으며 `replay_of`를 추가하지 않는다. 자동/replay 제품 경로는 후속이다.

<!-- PS:drain -->
## 6. 정지·입력·Timer·Executor drain

- **PS13**: stop/cancel/error는 callback·I/O 전에 terminal latch·retry epoch·lease를 닫는다. committed-start/receipt stack 안에서는 World·authority를 파괴하거나 새 회차를 붙이지 않는다.
- **PS14**: owner는 입력·emitter·예약 사건·retry·GoalTimer·Executor timer/move·StateTree를 실제 정지하고 attempt depth와 Executor result/external-effect dispatch가 0인 관측을 확인한다. fixture drain bool이나 EndPlay 플래그 초기화는 증거가 아니다.

정지 순서는 다음과 같다.

1. 현재 exact owner/session/episode/World/lease를 strong pin한다. terminal outcome·reason을 결정하고 Host와 owner latch/retry epoch를 먼저 닫는다. old callback은 새 회차를 poison하지 못한다. callback 안의 Stop은 요청만 누적한다.
2. owner가 보유한 local controller에 `SetIgnoreMoveInput`/`SetIgnoreLookInput`을 소유량만 적용하고 `FlushPressedKeys`를 호출한다. player `StopJumping`, movement `StopMovementImmediately` 및 필요 시 `DisableMovement`를 적용한다. 이번에 획득한 input ignore count와 원래 movement mode를 추적한다. 다른 시스템의 ignore count를 전체 reset하지 않는다. `PlayerNoiseEmitterComponent.cpp`는 collection preparing/stopping owner가 있는 경우에만 새 notify 발행을 막는다.
3. `FWorldDelegates::OnWorldTickEnd`에서 deferred stop을 진행한다. 이것만으로 drain을 단정하지 않고 Host의 `mCollectionAttemptDepth`, owner `mAttemptDepth`, publication in-flight/held image, retry pending 상태를 읽는다. 이미 예약된 retry callback은 exact epoch fence에서 실제로 소진/거부돼야 한다. sleep 한 번을 drain으로 쓰지 않는다.
4. Host authority를 통해 GoalTimer teardown, StateTree stop 및 Executor의 신규 collection-only stop을 수행한다. 기존 `QuarantineForAssemblyFailure`·`ClearTimers`·move stop·result sink 경계를 좁게 재사용한다. 정상 Goal/Skill 정책을 바꾸지 않는다. 실행 중 Greet는 기존 social cancellation 경로로 끝내며 여기서 public permit을 만들지 않는다.
5. Executor의 `bResultDispatchInProgress`, `bExternalEffectInProgress`, `mCommittedGreetStartInProgress`가 모두 false인지 실제 read-only snapshot을 얻는다. 실제 timer handles의 active 여부, running/move 종료, sink detach, StateTree/GoalTimer 상태도 확인한다. status만 보고 timer 없음으로 추론하지 않는다. 현재 public timer accessor가 Running 조건으로 감싸져 있으므로 신규 private drain 관측은 실제 handle 상태도 검사한다.
6. `UninstallResultSinkForAuthority` 반환과 Knowledge sink lease 해제를 확인한 뒤에만 authority/assembly를 해제한다. 현 `Shutdown()`은 반환값을 버리므로 collection 경로에 성공 관측을 추가해야 한다. 확인 전 mExternalDispatchDrained를 true로 세팅하지 않는다.
7. 종료 evidence를 저장하고 필요 시 새 World travel을 수행한다. 정상 Stop 뒤 일반 플레이를 돌려줄 때도 shutdown된 Host를 같은 World에서 collection이 없는 것처럼 다시 열지 않는다. 정지된 세션을 최종화한 뒤 fresh normal World로 복귀하거나 기존 assembly 보존이 실제 증명된 경우에만 소유한 input 제한을 해제한다. 반환 방식은 §12의 사용자 가시 결정이다.

정지 watchdog은 단조 시각의 bounded wait다. 관측이 끝나지 않으면 reset_result=unverified와 sticky block을 기록한다. World destroy/PIE end/GameInstance Deinitialize에서 디스크 기록이 불가능하면 성공으로 바꾸지 않는다. 기존 finals를 보존하고 index 미완료로 남긴다. owner thread 밖에서 native root의 마지막 pin을 해제하지 않는다.

<!-- PS:persist -->
## 7. session·회차·terminal 파일과 닫힌 발행 목적

- **PS15**: session descriptor·episode terminal·reset 결과·session terminal journal은 immutable 별도 파일로 exclusive publish와 exact readback을 수행한다. session/episode Schema에 terminal-history 필드를 끼워 넣지 않는다.
- **PS16**: storage/sidecar/diagnostic/terminal/index 저장 실패와 reset failed/unverified는 sticky session block이다. 원본 Capture/marker·수락 ledger·잔여 bytes를 보존하며 같은 세션 재개와 성공 index를 차단한다.

출력 root는 owner가 획득한 native private root이며 기본 namespace는 project `Saved/AINativeNPC/Collections`다. root 밖 절대 경로·backslash·parent traversal·reparse/alias escape를 허용하지 않는다. `PublishJsonExact`의 기존 CREATE_NEW → full write/flush/close → nonreplace MoveFileW → held-image actual exact readback을 재사용한다. `IsCanonicalJsonRelativePath`를 임의 `.json` 허용으로 넓히지 않는다.

| purpose | 상대 경로 | payload |
|---|---|---|
| Session | sessions/<session UUID>/session.json | scenario_collection_session_v1 |
| EpisodePreparing | episodes/<session UUID>/<episode UUID>/preparing.json | scenario_collection_episode_v1 |
| EpisodeTerminal | episodes/<session UUID>/<episode UUID>/terminal.json | scenario_collection_episode_v1 |
| EpisodeReset | episodes/<session UUID>/<episode UUID>/reset.json | scenario_collection_episode_v1 |
| SessionTerminal | sessions/<session UUID>/terminal.json | anpc_collection_session_terminal_v1 |
| Index | indexes/<session UUID>/index.json | scenario_collection_index_v1 |
| Metadata | metadata/<session UUID>/<closed name>.json | 검증한 원본 metadata bytes |

Metadata의 closed name은 `catalog`, `collection-schema`, `execution-profile`, `utility-profile-source`, `runtime-build-evidence`, `session-start-evidence`다. yaml/registry 원본은 trusted package에서 hash 검증한다. 필요한 장기 보관은 build evidence의 source inventory/archive로 결속하며 `.json` 이름으로 YAML을 저장하지 않는다. 저장 metadata가 canonical digest와 raw descriptor digest를 혼동하지 않게 한다.

FileStore request에 신규 닫힌 purpose와 exact owner/session/episode/finalization generation을 결속한다. 가능한 operation과 경로는 purpose로 결정한다. UUID·고정 파일명은 owner의 typed 입력에서만 만들며 경로 문자열을 external caller가 제공하지 못한다. request는 owner thread에서 한 번 소비한다. sidecar와 diagnostic 기존 lease predicate는 보존한다. 새 session/terminal/index publication은 Host의 revoked lease 대신 owner-private lifecycle receipt로 매 stage 전후·readback 뒤 현재성을 확인한다. callback bool을 authority로 받지 않는다.

session 파일은 기존 Schema의 immutable 시작 설정이다. wire session에는 terminal state가 없다. episode의 preparing 파일, terminal 파일, reset 파일은 각각 기존 episode Schema 전체를 지키며 바뀌는 state/reason/reset_result만 현재 관측에 따라 달라진다. terminal 파일은 reset_result=not_attempted로 먼저 저장한다. 새 회차 전에 reset 결과를 별도 파일로 보존한다. 이전 terminal 파일을 교체하지 않는다.

새 내부 `session_terminal` journal은 `format="anpc_collection_session_terminal_v1"`, `version=1`, `session_id`, `outcome`, `reason`, `observed_at_seconds`, `session`, `ordered_episodes`만 갖는 closed object로 구현한다. outcome은 finalized/cancelled/timed_out/failed 중 실제 session 종료 이유다. session과 ordered_episodes 항목은 FileStore가 실제 publish/readback한 `{path,size_bytes,sha256}` descriptor다. ordered_episodes는 실패·Capture 없는 회차도 포함하며 reset 파일이 있으면 그것을, 없으면 terminal 파일을 최종 descriptor로 선택한다. active episode를 넣지 않는다. 이 journal은 collection session Schema나 ML completion_closure가 아니다. format의 finalized는 ledger를 닫은 내부 상태이며 index I/O 성공을 선포하지 않는다. 최종 index readback 성공은 별도 owner 결과로만 반환한다.

preparation에서 실패한 경우 아직 DecisionId가 없다면 diagnostic observed_id=null, memory-only Snapshot이면 snapshot_present=false/snapshot_ref=null이다. 기존 Host의 storage scope가 없는 preparation/reset diagnostic도 신규 owner-private 경로로 실제 저장한 뒤 ledger에 넣는다. 필요할 때 진단 저장 실패는 재귀 진단 없이 memory failure를 남긴다. host에서 이미 저장한 diagnostic을 다시 accepted entry로 복제하지 않는다.

<!-- PS:index -->
## 8. 최종 index를 한 번 저장하는 알고리즘

- **PS17**: 최종 index의 필드는 format/version/session_id/entries뿐이다. entries는 readback된 accepted/diagnostic canonical entry 본문이며 descriptor 목록·counts·approval·session/episode 객체를 추가하지 않는다.
- **PS18**: 정지·drain·terminal 저장 뒤 ledger를 동결한다. accepted entries 다음 diagnostic entries의 기존 순서를 보존하고 각 마지막 LF만 제거해 합친 canonical UTF-8 index를 session당 한 번 nonreplace publish/readback한다.
- **PS19**: index 발행은 lease revoke 뒤에도 유효한 owner-private one-shot purpose 권한을 사용한다. sidecar current-lease 검사를 풀거나 public arbitrary-path writer를 만들지 않으며 중복 stop은 기존 결과만 반환한다.

최종화 입력은 owner의 `mAcceptedEntries`, `mDiagnosticEntries`, readback된 session/episode descriptor 목록이다. disk 디렉터리 glob이나 raw 파일 개수로 ledger를 재구성하지 않는다. 기존 accepted identity/sample/path/episode-decision set과 `mIndexEntryCount`의 일관성을 검사한다. 모든 referenced episode는 terminal이며 마지막을 제외한 회차는 verified reset이어야 한다.

1. entry 발행·진단·stop stack이 모두 끝났고 sticky persistence/reset 오류가 없는지 검사한다. 성공한 Capture가 없어도 실제 종료 기록이 보존되었다면 empty index가 가능하다.
2. ledger를 frozen 상태로 전환해 mutation과 reentrant append를 막는다. accepted, diagnostic 배열 각각의 순서를 유지한 owned snapshot을 만든다. canonical entry를 의미 해석 없이 임의 JSON 문자열로 받지 않는다. 생성 당시 typed record와 exact sidecar readback에 결속된 body만 사용한다.
3. 각 body가 LF로 끝나는 검증된 canonical UTF-8 객체인지 확인한다. 끝 LF 하나만 제거한다. 본문 문자열을 trim하거나 double 기반 JSON 경로로 재직렬화하지 않는다. uint64 DecisionId의 정확성을 보존한다.
4. key 순서는 `entries`, `format`, `session_id`, `version`이다. entries 안의 body 사이에만 comma를 넣고 wrapper 뒤 LF 하나를 붙인다. 기준은 `sorted_json_bytes(value) + b"\n"`, UTF-8/BOM 없음·compact·ensure_ascii=False·allow_nan=False다. runtime 바이트 길이는 `mIndexBytes`와 같아야 한다.
5. native root가 idle이고 budget이 허용하면 exact Index purpose의 one-shot 권한을 mint한다. 최종 경로와 임시 sibling 충돌·symlink/ancestor 변경을 검사한다. `PublishJsonExact`의 actual exact readback 뒤 마지막 owner generation/current 검사를 수행한다.
6. 성공 descriptor를 owner에 한 번 저장한다. Stop 재호출은 pending이면 같은 pending 상태를 반환하고, 성공이면 같은 descriptor를 반환한다. 다시 I/O하거나 accepted count를 올리지 않는다. 실패 후 같은 session 경로로 재시도하거나 final을 덮어쓰지 않는다.
7. 부모 실파일 검사에서 session/ordered episodes/index를 strict parse하고 `validate_index(index, root, session, episodes, catalog, expected_profile_sha256=..., expected_runtime_build_sha256=...)`를 실제 신뢰 package의 pin과 실행한다. Capture/marker는 기존 동일 bytes decoder를 사용한다. catalog-only CLI 성공은 index 검사 성공이 아니다.

이미 실물 파일로 옮겨졌지만 readback/current 확인에 실패한 index는 보존하되 성공 descriptor를 반환하지 않는다. 파일 존재와 최종화 성공을 구분한다. 마지막 cancelled/timed_out/관측 실패 회차도 저장·drain이 정상이고 session block이 없으면 구조적으로 유효한 최종 index에 포함할 수 있다. reset failed/unverified 또는 저장 실패가 있으면 성공 index는 만들지 않는다.

<!-- PS:budget -->
## 9. 누적 저장 예산 보존

- **PS20**: 누적 budget은 Capture/marker/entry/diagnostic/index/session/episode/reset/journal/metadata와 in-flight overhead를 포함한다. checked arithmetic·쓰기 전 예약·실제 정산을 사용하며 World 교체·root/limit 변경으로 소비량을 지우지 않는다.
- **PS21**: mIndexBytes의 기존 예약은 최종 본문으로 한 번 전환한다. 빈 ledger도 wrapper를 예약하고 최종 bytes와 일치시킨다. 실패 final/residual 예약은 남기며 보존 자료 삭제로 예산을 확보하지 않는다.

현 Host `ReserveCollectionPublication`은 Capture/marker와 entry·diagnostic 및 향후 index body를 예약한다. `TryPublishCollectionReceipt`/diagnostic 완료는 `mIndexBytes`와 배열을 갱신한다. 이 회계와 별도의 새 세션 budget을 만들어 양쪽 제한을 우회하지 않는다.

owner의 `mBudgetBytes` 한 장부에 신규 descriptor/terminal/metadata 비용을 추가한다. 같은 native root와 storage limit을 lifetime 동안 고정한다. 모든 더하기·곱하기·length 변환은 checked로 처리한다. 메모리 배열 한도와 FileStore의 hash padding 한도도 쓰기 전에 검사한다. 신규 Session 시작 때 empty index wrapper 및 반드시 필요한 종료 기록 reservation을 먼저 만든다. 이후 첫 capture 예약이 wrapper를 다시 더하지 않도록 기존 `mIndexBytes==0` 경계와 통합한다.

index 저장 때 이미 예약된 본문 bytes를 실제 final 소비로 옮긴다. rename이 같은 bytes를 temp에서 final로 옮기는 부분을 중복 청구하지 않는다. 추가 실제 disk overhead가 필요한 경우만 별도 checked reservation을 확보한다. readback 실패·temp cleanup 실패·final 보존은 보수적으로 사용량에 남긴다. 중간 회차 terminal/reset 파일이 늘어나도 budget은 누적된다. 준비 실패·취소·빈 ledger에서도 초과 write를 허용하지 않는다.

native root와 마지막 strong pin은 owner thread에서만 해제한다. World 해제로 root를 재획득하거나 세션 중 output root/limit을 바꾸는 요청은 거부한다. parent validator의 referenced-artifact 합산은 producer의 이 누적 회계를 대체하지 않는다.

<!-- PS:provenance -->
## 10. 출처·검증 범위와 승인 경계

- **PS22**: 자동검사는 automated_runtime/automatic/automated 또는 격리 test_fixture로 기록한다. public manual start의 자동 호출은 human 허가를 만들지 않는다. 사람 플레이 확인은 사용자 실제 입력과 피드백으로만 완료한다.
- **PS23**: index readback 성공은 구조·저장 완료다. completion pin/ML importer/Teacher/Human label/Resolve readiness/Shipping/UI/자동 시나리오 연출/commit/push는 이번 범위 밖이다.

manual 공개 경로는 실제 local controller와 trusted launcher가 허용한 입력 주체를 확인한다. `GIsAutomationTesting` 및 automation/commandlet launch 상황에서 public manual 시작을 거부한다. 단순히 이 플래그가 false인 것만으로 사람을 인증하지 않는다. 자동 하네스는 private automation input adapter가 동일 nondev issuer·owner 본문을 실행하되 source/controller/mode를 실제 자동 실행으로 고정한다. 별도 테스트 fixture의 실제 관측을 general human input으로 승격하지 않는다.

Unreal latent PIE 검사에서 실제 movement/sensing/World reset/file I/O를 실행한 결과는 자동 통합 증거다. 사용자 피드백과 실제 입력이 없으면 사람 플레이 확인은 미완료다. screenshot·commandlet·모의 성공 count만으로 이를 대신하지 않는다.

이번 실행 대상 선택 이후 위 PIE 증거의 적용 범위는 Editor 하위 회귀다. 과거 PIE 증거를 Development Game 수집 통합 증거로 승격하지 않는다. 자동 Game 실행도 automated_runtime 출처로 남기며 사용자 실제 입력 확인과 분리한다.

기존 Utility label은 raw 2/Dagger와 scenario_collection_utility_unreviewed다. Resolve capture-only는 기존 confidence와 phase 의미를 유지하며 ResolvePolicyReady를 바꾸지 않는다. `validate_index` 결과의 validated_row_count=0, production_eligible=false는 최종 보고에도 유지한다. 외부 completion pin/closure의 authority 검증은 Task 4의 별도 작업이다. 이번 local terminal journal·index hash가 그 권한이 되지 않는다.

<!-- PS:matrix -->
## 11. 사용자 확인용 행동 하네스와 실패 대응표

이 절은 사용자 확인용 참고다. 현재 구현 전용 작업에서 AI는 검사 작성·실행·결과 판정을 수행하지 않는다.

- **PS24**: 각 실패 검사는 정상 control과 실제 경계 도달을 함께 기록한다. 컴파일 실패·0 discovery·timeout·문서 mutation은 Unreal 행동 RED나 사람 플레이 증거가 아니다.

새 Unreal 검사명 prefix는 `AINativeNPC.Collection.Host.PlaySession.*`로 고정한다. 기존 runner의 Host filter를 재사용한다. source의 기존 `Tests/AINativeNPCProductionPIESmokeTests.cpp`는 `LoadMap(MVP)` → `FStartPIECommand(false)` → latent verify → `FEndPlayMapCommand` 예제다. 이 기존 테스트를 수정하지 않는다. 기존 PIE smoke가 Phase3B 디렉터리를 삭제하는 동작도 있으므로 부모는 반드시 격리 Saved와 preserved-source inventory를 사용한다.

| ID | 경계 | 입력·실패 | 필수 oracle |
|---|---|---|---|
| S01 | start | 정상 MVP/단일 local/assembly | nondev owner·첫 lease·session readback |
| S02 | start | ThirdPerson/wrong World/no authority/복수 player | attach와 Capture 0·일반 플레이 보존 |
| S03 | inputs | malformed catalog/profile/build·동일 forged digest | 실제 검증 실패·fixture 승격 0 |
| S04 | provenance | 자동 runner의 manual start | human 오분류 0·automation 출처 유지 |
| S05 | id | 중복 session/episode·sequence/epoch overflow | 재사용 0·기존 bytes 보존 |
| S06 | lifecycle | 동시 start/new·기한 경계·관측 prefix 부족 | 단일 회차·timeout 우선·completed 거부 |
| S07 | stop | committed-start/result callback 중 stop | revoke 선행·stack 내 teardown 0 |
| S08 | drain | 입력 held·emitter·timer·move·dispatch 진행 | 실제 정지/0 관측 전 reset 금지 |
| S09 | reset | old cleanup 누락·동일 World·재사용 Host·late callback | fresh barrier 거부·새 회차 불변 |
| S10 | persist | terminal/reset/session write/readback 실패 | sticky block·원본 보존·index 성공 0 |
| S11 | index | accepted+diagnostic·빈 ledger | strict fields·canonical bytes·실파일 재검증 |
| S12 | index | final/temp 충돌·alias·race·readback 변조 | nonreplace·실패 bytes 보존·재발행 0 |
| S13 | budget | wrapper/metadata/terminal/residual·overflow | 누적 선예약·이중 청구 0·초과 write 0 |
| S14 | cancel | 중복 stop·cancel 뒤 new·GameInstance 종료 | 일회 index·drain·오류 상태 보존 |
| S15 | normalgame | 수집 off·Resolve capture-only | legacy 동작·세 승인 false 유지 |
| S16 | nondev | macro-off compile/preprocess와 실제 entry | prod 경로 존재·test helper 의존 0 |
| S17 | realfile | session/episodes/index·Capture/marker 재읽기 | validate_index·validated_row_count=0·production_eligible=false |

각 관측 receipt는 실제 syscall·timer/dispatch·World identity에서 생성한다. hostile test injection은 실패를 발생시키거나 관측할 뿐 성공 권한을 대신 주입하지 않는다. old receipt와 새 lease 교차, session block 이후 new episode, preparation-only/capture 없는 cancel, max uint64 정밀도, index 최종 readback 후 재진입을 포함한다.

<!-- PS:execution -->
## 12. 부모 구현 순서·실행 소유·인계 결정

- **PS25**: AI는 문서 태스크 단위의 코드 작성만 소유한다. 검토·검증·구현 확인과 build·Automation·실파일 확인은 사용자가 담당한다. 과거 문서 작성 상태와 실행 기록은 당시 범위의 기록으로 보존한다.

### 12.1 기존 문서 하네스 — 사용자 참고

아래 명령과 실패 분류는 과거 절차의 참고 기록이다. AI는 이 하네스를 실행하거나 변경된 작업 방식에 맞춰 별도 검사 수정 작업을 시작하지 않는다.

새 pytest는 active exact tag·규범 문장·allowlist/명령/default/path/matrix 표, Schema의 closed index, 실제 catalog membership을 검사한다. 삭제·완화·fence/comment 은닉·잘못된 scope 이동·중복/누락/순서 변경·각 실패 oracle 삭제를 메모리 mutation으로 거부한다. 기존 문서나 tests를 쓰지 않는다. 아래 명령은 **실행 지시 예시이며 실행 결과가 아니다**. 새 evidence 하위 이름을 사용하고 이미 존재한 결과를 덮어쓰지 않는다.

```bash
cd /home/namingsense/AI-Native-NPC
PYTHONDONTWRITEBYTECODE=1 ANPC_PLAY_SESSION_DOCUMENT_MODE=before-plan python -B -m pytest tests/test_collection_play_session_index_document.py -q -p no:cacheprovider --basetemp=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/doc-red-tmp-01 --junitxml=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/doc-red-01.xml
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest tests/test_collection_play_session_index_document.py -q -p no:cacheprovider --basetemp=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/doc-green-tmp-01 --junitxml=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01/doc-green-01.xml
```

실행 옵션은 `ANPC_PLAY_SESSION_DOCUMENT_MODE=before-plan`, `PYTHONDONTWRITEBYTECODE=1`, `-B -m pytest`, `-p no:cacheprovider`, `--basetemp`, `--junitxml`로 고정한다. before-plan의 예상 실패는 active play-session clauses 부재 assertion이다. import/FileNotFound/환경 오류는 행동 RED가 아니다. 기존 문서 하네스도 부모가 필요한 회귀만 실행하고 문서 검사 수를 Unreal 수에 합산하지 않는다.

### 12.2 구현계획 태스크 단위의 일괄 구현

기존 제품 구현 항목 2–6의 번호와 기능 범위를 유지한다. 과거 항목 1의 검사 선행 단계와 항목 7–8의 실행 검증은 AI 구현 절차에서 제외한다. 태스크는 아래 덩어리 전체이며 내부 함수를 별도 위임 단계로 만들지 않는다.

- **구현 태스크 2 — RuntimeInputs와 일반 플레이 진입:** RuntimeInputs와 GameInstance owner, typed options·console 등록·disabled default·현재 World 검사와 필요한 실제 package/build/start 입력 연결을 함께 구현한다. 관측이 없는 입력에는 실패 reason을 반환하는 제품 계약을 유지한다.
- **구현 태스크 3 — 세션 소유와 회차 연결:** session/episode/root 소유와 private runtime Context/Lease/Host attach를 함께 구현한다. preparing intent rendezvous·실제 storage bind·runtime namespace를 연결한다.
- **구현 태스크 4 — 정지와 새 World 전환:** input/emitter/retry/timer/Executor drain 관측과 deferred stop, terminal persist/readback, fresh World/reset 결과 저장을 하나의 구현 태스크로 연결한다.
- **구현 태스크 5 — 수명 기록 저장:** FileStore의 purpose별 closed grammar와 owner-private one-shot current 확인, Bridge의 typed session/episode/journal/index serializer를 함께 구현한다. 기존 lower syscall/readback을 재사용한다.
- **구현 태스크 6 — 최종 목록과 누적 예산:** ledger frozen index와 empty wrapper·metadata/terminal reservation을 통합한다. collision/readback/budget 실패 처리와 일회 저장·결과 캐시를 제품 코드에 연결한다.

이미 작성된 부분은 이어서 사용한다. 새 태스크별 검사 문서·실패용 빈 본문·실행 증거를 작성하는 작업으로 되돌아가지 않는다. 태스크의 관련 코드를 작성한 뒤 `코드 작성 완료`와 `남은 구현`을 인계한다. 검토·검증·구현 확인은 사용자가 담당한다.

### 12.3 구현 기본안과 실행으로 확인할 조건

부모는 명시적 수집 요청에 아래 최소 기본안을 적용한다. 이 선택은 새 UI·자동 시나리오 연출을 추가하지 않는다. 실제 배치·관측 성공은 후속 Unreal 실행으로 확인한다.

- **배치 좌표계/오차:** Guard 초기 home의 수평 forward를 정규화한다. 목표 player XY는 home XY에서 선택 distance만큼 그 forward 반대 방향이다. angle=0은 player가 Guard 쪽을 향하는 접근 방향이다. 지면·capsule clearance를 실제 trace/sweep로 검사한 뒤 foot 기준 높이를 정한다. readback 수평 위치 오차 1cm 이하와 yaw 오차 1도 이하를 요구한다. 엔진의 충돌 보정으로 이 조건을 벗어나면 실패한다. 이 허용 오차는 센서 feature나 카탈로그 variation을 확장하지 않는 배치 검사 한도다. 실제 map에서 성립하는지는 별도 실행으로 증명한다.
- **정상 Stop 뒤 플레이 반환:** terminal/index를 저장한 뒤 같은 MVP map의 fresh normal World로 복귀한다. Start/NewEpisode는 명시적 수집 회차 초기화를 포함한다. 완료 index를 바꾸지 않는다. 복귀 실패는 별도 운영 오류로 보고한다. shutdown된 Host를 같은 World에서 재활성화하지 않는다.
- **trusted package/launcher 공급:** `RuntimeInputs`와 부모 전용 준비 도구가 실제 metadata·forced project-module build·receipt·source와 loaded module을 결속한다. 부모 도구가 별도 launch 환경에 package 위치와 exact digest pin을 전달한다. 제출 JSON의 expected 필드는 권한을 만들지 않는다. 실제 module 목록과 OS creation time은 Windows API로 관측한다. package root의 stable ownership과 시작 뒤 module 변경 검사는 계속 필수다. 이 기본안은 구현·실행 완료 주장이 아니다.
- **manual 완료 사건 관측:** 이동 사건은 Running 이후 실제 player 수평 이동 시간의 누적이 catalog의 movement_seconds를 만족하고, 같은 player의 성공한 authored Animation Notify 증가와 실제 SoundHeard를 관측한 때 성립한다. 준비 이전 관측을 재사용하지 않는다. 후속 appearance/loss는 같은 typed player의 실제 SightAcquired/SightLost 순서만 받는다. 매 사건의 trigger 이후 timeout과 전체 monotonic deadline을 함께 적용한다. 짧은 이동 한 번이나 Goal phase 진입을 전체 사건 완료로 바꾸지 않는다.

좌표·입력 종료·사건 기준은 구현 기본안이다. 실제 source 경계와 실행 결과가 이를 충족하지 못하면 실패를 기록하고 필요한 좁은 교정을 문서·하네스에 먼저 반영한다. stub 성공·허위 hash·fixture receipt로 미완료를 채우지 않는다.

### 12.4 별도 Development Game의 최종 수집 통합

<!-- GAME:decision -->
**적용 결정:** 기존 엔진과 별도 Development Game 대상 선택은 유지한다. 과거 build·cook 승인 기록의 근거는 evidence root의 `development-game-path-decision-01.md`다. 현재 §0의 지시에 따라 빌드·cook·실행 확인은 사용자 담당이며 AI는 이를 실행하지 않는다. Shipping 배포는 계속 제외한다.

- **DG01:** 최종 대상은 기존 Target=NeuralGame, Win64/x64/Development/Game이다. `UnrealEditor.exe -game`과 새 Game target 생성을 채택하지 않는다. 기존 Editor/Host Automation은 lower regression이며 최종 수집통합은 별도 Development Game에서 확인한다.
- **DG02:** PS01–PS25의 Console 3개·기본값·limits·PS13–PS14 drain·native publication·index·World identity 계약을 유지한다. 자동 Game 입력은 automated_runtime/automatic/automated다. human_play/manual/human은 실제 사용자 입력과 피드백으로 별도 확인한다.
- **DG03:** read-only Game planner는 actual receipt·uproject·모든 project-local uplugin descriptor·현재 Target.cs/Build.cs bytes를 고정 입력으로 받는다. 현재 receipt는 stale build여도 계획의 actual input이다. 최신 기능 build 성공은 별도 forced compile/link 증거를 요구한다.
- **DG04:** 현재 지원 범위는 단일 논리 project module NeuralGame이 기본 monolithic EXE에 결합되는 닫힌 source 형태다. module_descriptor{module_name,base,path,size_bytes,sha256}에 실제 EXE를 한 행으로 표현한다. 같은 EXE의 중복 path rows·빈 목록·DLL 위장은 거부한다. descriptor eligibility에서 예상 집합을 먼저 정하며 실제 observed module 누락에 맞춰 줄이지 않는다.
- **DG05:** 현재 GameDevMCPPlugin의 UnrealMCPEditor는 Editor module이므로 Game compile/runtime 대상에서 제외한다. 제외를 결정한 descriptor도 inventory/pin에 포함한다. Editor 전용 MCP를 Game runtime 제어에 사용한다고 가정하지 않는다. 새 runtime RPC/원격 bridge를 추가하지 않는다.
- **DG06:** HotReload와 LiveCoding은 별도 검증이다. WITH_HOT_RELOAD 기본식과 실제 Game build definitions/link를 대조한다. bWithLiveCoding/-NoLiveCoding의 RequiresUniqueBuildEnvironment를 우회하지 않는다. supported session query/disable API와 연속 현재성 관측의 미확인 성공 조건은 pending으로 남긴다.
- **DG07:** GameInstance early-init 이후 bootstrap rendezvous, 상속 native pipe protocol, private automation adapter를 연결한다. 현재 N1은 raw file/pipe IO만이며 전체 bootstrap authority가 아니다. startup만으로 gameplay 성공을 주장하지 않는다.
- **DG08:** 최종 증거는 forced Game compile/link action coverage → 선택 MVP asset dependency cook/staging → 새 Game PID/creation/EXE/loaded inventory → Start→NewEpisode→Stop→terminal/index readback이다. original Content/Saved는 보존하며 source/build/cook/startup/수집/재읽기 결과를 각각 기록한다.
- **DG09:** 사용자 승인으로 NeuralGame.Build.cs에 `if (Target.bWithLiveCoding)` 조건의 `PrivateIncludePathModuleNames.Add("LiveCoding")` 한 항목을 허용한다. planner는 기존 형태와 이 정확한 successor 형태만 허용하며 추가 의존성·macro·Target 변경은 거부한다. public header의 실제 compile로 소비를 확인한다. 이는 설정 보완이며 runtime disabled/currentness나 일반 플레이 수집 성공 증거가 아니다.

§12.2의 Editor build/Host filter와 자동 PIE 설명은 lower regression 절차로 보존한다. 최종 Game 수집 경로는 이 절이 추가로 요구한다. 원본 `runtime-inputs-launcher-design-01.md`의 Development Editor + PIE 대상, 두 DLL/.modules 계획, Editor 이후 GI claim 순서, Editor MCP/AssetRegistry 사용 위치와 사람 Editor launch 미결정은 이 선택 범위에서 `development-game-launch-slice-01.md`가 supersede한다. 원본 기록은 수정하거나 삭제하지 않는다. 상속 pipe의 닫힌 메시지·독립 pin·same-read bytes·source closure·sticky invalidation·owner SessionID 예약 순서는 유지한다.

새 planner의 immutable API·정확한 첫 실패 assertion·actual input snapshot 인계·실행별 미확정 조건은 같은 evidence root의 `development-game-launch-slice-01.md`와 `development-game-plan-red-handoff-01.md`에 있다. 추가 문서 하네스의 초기 PASS는 추가 문서 coverage이지 behavioral RED가 아니다. 작성자는 planner 본문을 `return None`에 두고 종료한다. 실제 Python RED와 후속 GREEN·Game 실행은 부모만 수행한다.
