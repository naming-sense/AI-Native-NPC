# 수집 회차의 context와 lease 구현 계획 — Task 2C

> **For Hermes:** `subagent-driven-development`로 이 문서의 작은 검사·구현 단위를 순서대로 진행한다. 문서 작성 checkpoint는 C++ 수정·Unreal build/run 없이 완료했다. 사용자의 계속 진행 승인에 따라 아래 물리 복사본에서 Task 2C C++ 구현·Unreal 검증을 진행한다. commit/push는 제외한다.

**Goal:** 실패하거나 종료된 수집 회차에서 새 Decision과 오래된 callback이 실행되는 일을 차단한다.

**Architecture:** context는 검증한 회차 값의 immutable copy다. lease는 그 context를 exact World/Host/episode와 epoch에 묶는 수명 증표다. Host가 진입·예약·callback 경계에서 lease를 확인하고, 실패하면 terminal latch(회차 종료 잠금)를 먼저 닫는다. 실제 입력 정지·reset과 발행 권한은 후속 owner가 담당한다.

**Tech Stack:** 기존 Unreal Engine 5.7 C++ Host, 격리된 Development Automation fixture, 문서 저장소 pytest. 새 Schema·wire format·generated API를 도입하지 않는다.

<!-- C:scope -->
## 1. 현재 단계와 완료 범위

<!-- T2C:historical -->
**역사적 문서·하네스 단계:** immutable context / lease 계획 작성 당시의 **C++ 미수정, Unreal build/run 미실행**은 **문서-only checkpoint에 한한 역사적 사실**이다. 그 문서 검사만으로 C++ 동작이나 회차 실행을 증명하지 않는다.

<!-- T2C:current -->
**현재 Task 2C:** 허용된 **copy 5파일 구현**을 최신 소스로 다시 검증했다. **부모 확인 last runtime checkpoint**는 `c2-final-build-01`의 build 성공, `c2-final-host-01`의 **Host 25 PASS**(warning 53), `c2-final-observation-01`의 **Observation 37 PASS**(warning 0), `c2-final-broad-01`의 **broad 229 PASS**(warning 72)다. 관련 snapshot·run 증거 root는 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/final-05`다. WeakObjectPtr header include 보완 뒤 `c2-nodev-compile-02`의 3개 TU compile-only 검사도 통과했다(noShipping/noLink/noRuntime). **최종 최신 bytes 실행 검증 완료; 독립 승인 아님**이다. `final-verification-02/result.json`은 exact test-name multiset, 원본 입력·Capture 보존, source delta 5개, 기존 H01–H09 본문 보존 및 focused/broad 입력 동일성을 확인한다.

<!-- T2C:limits -->
**승인·제품 경계:** **독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만**, **production collection closed**다. `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다. **실제 collection 저장 미구현**, **실제 reset 미구현**이다. **terminal/reset/dispatch-drain receipt는 dev fixture 값**이며 **실제 Executor drain 측정 미구현**이다. **GameInstance owner·production issuer·ML import 미구현**, **원본 승격 없음**, **commit/push 없음**이다. 이 checkpoint는 학습/Production 승인과 별개다.
<!-- T2C:approval-record -->
**고정 후보의 최종 검토 기록:** 독립 SPEC와 QUALITY가 같은 `final-05` source와 실행 증거의 Task2C 부분 범위를 승인했다. 부모는 subject 전체 파일과 두 검토 산출물의 동일성을 재검증했다. 승인 기록은 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/review-01/acceptance/acceptance.json`이다. **원본 승격 없음**이며 실제 저장·reset·production authority·학습 준비 완료는 이 승인에 포함하지 않는다. 검토 당시의 상태 문서와 기존 증거는 read-only subject에 그대로 보존하고, 이 단락과 승인 상태 문구만 현재 문서에 갱신했다.
<!-- T2C:end -->

- Task 2D: append-only Writer/FileStore, 같은 byte image를 검증한 committed receipt.
- Task 2E: Record 전 metadata/group 계산, CaptureBridge join, sidecar/diagnostic 실제 저장·발행.
- Task 3: trusted owner/runner, 실제 입력 중단·World reset·native UI.
- Task 4: 실제 authority 검증과 ML import.
- 모든 단계에서 `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다.

규칙의 권위는 [Host 계약 §§3–4](scenario-host-capture-v1-contract.md#3-회차-실패와-초기화-장벽), [수집 데이터 lifecycle](scenario-collection-v1-data-contract.md#pure-lifecycle-and-split-apis), 기존 [Schema](../../contracts/current/scenario_collection_v1.schema.json)·[catalog](../../contracts/current/scenario_catalog_v1.json), [Runtime import 계약](runtime-capture-import-v1-contract.md)이다. 이 계획은 승인된 규칙을 구현 순서로 나눈다. 상위 계약의 필드·상태·정책을 추가하거나 완화하지 않는다.

<!-- C:baseline -->
## 2. 보존할 구현과 제한된 이전 승인

원본 Task 2B 기준 `Execution/AINativeNPCGoalHostComponent.cpp`의 `FAINativeNPCGameplayCommitAuthority::PrepareDecisionFeatures`는 capture 성공 뒤 `KnowledgeBeforePromotion`을 복사하고 현재 Pawn transform으로 `Populate`를 호출한다. `TryStartCurrentDecision`은 preparation 실패 시 Finalize 앞에서 반환한다. `Tests/AINativeNPCCollectionHostTests.cpp`의 기존 H01–H09에 copy의 2C 검사가 추가됐다. 이 연결과 순수 adapter의 의미를 보존한다.

2026-10-25 실행 `fresh-host-02`의 **Host 9**와 `fresh-observation-01`의 **Observation 37**은 S01의 fixture asset closure·fail-closed 입력 검사·실행 결속·원본 보호 범위에서 승인됐다. 승인 근거는 다음 두 파일이다.

- `/home/namingsense/AI-Native-NPC-evidence/task2b-s01-narrow-tvrp81au/acceptance/acceptance.json`
- `/home/namingsense/AI-Native-NPC-evidence/task2b-s01-narrow-tvrp81au/packet/SCOPE.md`

`whole_task2b_closed=false`다. H10, broad 회귀, whole-project clean/forced build, 실제 수집, 학습 readiness, Task 2C–2E 완료는 이 S01 승인에 포함되지 않는다. old438은 **INCOMPLETE**로 유지한다. 2C copy의 후속 broad 실행은 아래 별도 checkpoint이며 S01의 승인 범위를 넓히지 않는다. 이번 문서 작업은 과거 evidence를 수정하거나 Unreal을 재실행하지 않는다. 기존 pure adapter focused 37·broad 204는 다른 단계의 과거 증거다.

읽기 전용 원본 소스 기준은 `/mnt/d/Codex-cli/NeuralProject/NeuralGame/Source/NeuralGame/AINativeNPC/`다. **구현·build/run 대상은 물리 복사본 `/mnt/d/Codex-cli/NeuralProject/collection-next-uq63w5dx/NeuralGame`뿐**이다. 부모가 copy를 구현·실행했으며 최종 검토 뒤 허용 source만 원본 승격할 수 있다. 이 문서 작업자는 원본과 copy 모두 수정·실행하지 않았다. 원본 승격은 아직 수행되지 않았다.

**부모 제공 baseline:** 이 copy의 새 Intermediate에서 295-action Development Editor build와 기존 Host 9 실행이 성공했고 warning 19를 보존했다는 보고를 받았다. 이는 구현 전 환경 기준선이며 **Task 2C 성공으로 집계하지 않는다**. 이 작업자는 해당 build/run을 재실행하거나 raw report를 독립 검증하지 않았다. 원본 source/config/content/binaries/plugin 1352개·Saved/AINativeNPC 3개 보존 및 시작 시 Windows UE/UBT process 0이라는 부모의 관측은 그 시점의 보고다. 과거 PID14584 descriptor는 stale이며 현재 실행 증거로 사용하지 않는다.

<!-- C:runs -->
### 구현·실행 checkpoint와 남은 확인

아래 경로는 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx` 기준이다. 실제 실행 디렉터리는 `/mnt/d/Codex-cli/NeuralProject/collection-next-uq63w5dx/runs/<run>`이다. 부모가 확인한 결과를 기록하며 이 문서 작업자가 재실행하거나 독립 승인한 결과로 집계하지 않는다.

| 시점 | run | 부모 확인 결과 | 관련 evidence |
|---|---|---|---|
| 초기 행동 RED | `c2-red-host-01` | 우선 검증한 priority 3개 실패 | `red-01/runs/c2-red-host-01`; 후속 PASS로 과거 실패를 삭제하지 않음 |
| core 중간 | `c2-core-host-02` | Host 20 중 14 PASS·6 FAIL | `core-02/runs/c2-core-host-02`, `core-host-02-verification.json` |
| validation 중간 | `c2-validation-host-01` | Host 25 중 23 PASS·2 FAIL | `validation-03/runs/c2-validation-host-01`, `validation-host-01-verification.json` |
| include 보완 전 checkpoint | `c2-owner-host-01` | Host 25 PASS·warning 53·exit 0 | `owner-04/runs/c2-owner-host-01`, `owner-host-01-verification-v2.json` |
| 같은 checkpoint의 회귀 | `c2-owner-observation-01` | Observation 37 PASS·warning 0·exit 0 | `owner-04/runs/c2-owner-observation-01`, `owner-observation-01-verification-v2.json` |
| 같은 checkpoint의 broad | `c2-owner-broad-01` | broad 229 PASS·warning 72·exit 0 | `owner-04/runs/c2-owner-broad-01`, `owner-broad-01-verification-v2.json` |

위 owner checkpoint의 세 run은 부모가 exact discovery/start/completion/report의 test-name multiset과 exit 0을 대조한 결과다. 서로 겹치는 suite 수를 합산하지 않는다. 원본 source/config/content/binaries/plugins 1352개와 Saved Capture 3개 불변은 해당 시점의 `preservation-after-owner01.json` 및 부모 inventory 관측에 결속한다. 이후 source bytes나 현재 시점 보존을 자동 인증하지 않는다.

copy 구현 범위는 전체 payload의 owned copy·strict validation, exact input/lease 검사, World 밖 fixture owner의 failed/used-ID inventory, stale retry와 terminal latch, deadline 우선순위·invalid clock의 sticky session block, local strong pins·callback 후 재검사, revoke-first·deferred teardown이다. terminal/reset/dispatch-drain 각각의 토큰 장벽은 owner/session/context identity/World/Host/episode/epoch와 exact token을 대조한다. 복제 token·다른 owner·오래된 receipt는 현재 B를 바꾸거나 정상 predecessor를 소비할 수 없다. 누락·불일치 거부와 matching 실패의 영구 차단은 구분한다. 실제 파일 저장·reset·Executor drain 측정은 이 fixture 값으로 증명하지 않는다.

nondev compile probe `c2-nodev-compile-01`은 noShipping/noLink/noRuntime 범위다. `owner-04/runs/c2-nodev-compile-01/result.json`의 `WITH_DEV_AUTOMATION_TESTS=0` compile 실패는 과거 기록으로 보존하며 Runtime 행동 RED나 Shipping 실행으로 세지 않는다. header include 보완 뒤 `c2-nodev-compile-02`는 Context·Host·HostTests 3개 TU를 실제 compile하여 모두 exit 0이었다. 그 뒤 `c2-final-build-01` 및 Host/Observation/broad 재실행을 완료했다.

| 최신 소스 실행 | 결과 | 결속 증거 |
|---|---|---|
| `c2-final-host-01` | Host 25 PASS·warning 53·exit 0 | `final-05/runs/c2-final-host-01` |
| `c2-final-observation-01` | Observation 37 PASS·warning 0·exit 0 | `final-05/runs/c2-final-observation-01` |
| `c2-final-broad-01` | broad 229 PASS·warning 72·exit 0 | `final-05/runs/c2-final-broad-01` |

`final-verification-02/result.json`은 최종 세 run의 발견/시작/종료/report 일치, 같은 입력 manifest, baseline 213 + 새 Host 16개의 exact 집합, 기존 H01–H09 본문 불변, 원본 입력 1352개와 Capture 보존, 변경 source exact 5개를 확인한다. 복사본 plugin DLL/PDB 2개는 초기 baseline build에서 재생성됐으며 이후 그 baseline bytes와 동일하다. 독립 SPEC→QUALITY가 같은 고정 Task2C 후보를 승인했다.

**Golden 구분:** 최종 C++ 출력의 Python `canonical_cbor_parity=true`이며, 작업 전인 2026-10-25 원본 프로젝트에 남은 동일 fixture 출력과 byte-equal이다. 저장소 `tests/fixtures/phase0_golden.anpcv2`와의 **raw equality는 false**다. 세 기존 contract placeholder digest와 그로부터 파생된 feature/input/sample hash가 다르며, input CBOR의 차이는 feature-contract hash 하나다. tensor·label·candidate·switch-cost bytes는 동일하다. `golden-parity-01/{byte-parity.json,decoded-comparison.json,scope-diagnosis-02.json}`에 원문과 진단을 보존했다. 저장소 Golden이나 기존 evidence를 바꾸지 않았으며 raw parity 통과라고 주장하지 않는다. 이 기존 metadata 차이의 현재 Task2C 영향은 독립 검토 대상으로 명시한다.

<!-- C:files -->
## 3. Task 2C의 exact 소스 경계

다음 경로는 위 AINativeNPC root 기준이다. copy 구현과 후속 보완 모두 이 exact 목록을 유지한다.

```text
Execution/AINativeNPCGoalHostComponent.h
Execution/AINativeNPCGoalHostComponent.cpp
Collection/AINativeNPCCollectionContext.h
Collection/AINativeNPCCollectionContext.cpp
Tests/AINativeNPCCollectionHostTests.cpp
```

Host와 CollectionHostTests는 기존 파일을 최소 확장한다. CollectionContext 두 파일만 새로 만든다. Dataset, CollectionCaptureBridge, CollectionFileStore, ShippingGuardTests, adapter/ObservationFeatureTests, Builder/Coordinator/Knowledge, Schema/generated, asset, ML은 이 목록 밖이다. 전체 Task 2의 넓은 allowlist를 2C에 적용하지 않는다. 필요한 변경이 밖으로 나가면 정확한 파일·의존 이유를 반환하고 범위를 먼저 결정한다.

새 멤버는 `protected`의 `m` 접두어, 지역 변수는 접두어 없이, 중괄호는 다음 줄, const는 타입 뒤에 둔다. 기존 무관한 스타일과 API는 그대로 둔다. 엔진 필수 규칙과 충돌하면 우회 코드를 발명하지 않는다.

<!-- C:inputs -->
## 4. 입력을 복사하고 attach를 제한하는 경계

**validated 값 복사**는 validation 직후 외부 소유 문자열·container·descriptor와의 mutable alias를 끊는 단계다. context의 고정 값과 terminal/lease의 가변 상태를 분리한다. read-only view나 owned immutable snapshot만 밖으로 내보낸다. caller mutation 또는 다음 회차 교체가 이미 확보한 context 값을 바꾸지 못해야 한다.

| 입력 | 검증 및 소유 범위 |
|---|---|
| `session_id`, `collection_episode_id` | strict lowercase UUIDv4, session/episode 일치, 재사용 금지; process/session inventory의 실제 소유자는 후속 Task 3 |
| `catalog_sha256`, `profile_sha256` | 검증된 catalog/execution profile 및 독립 expected pin과 일치; 두 caller 문자열의 일치만으로 외부 evidence 검증을 주장하지 않음 |
| `runtime_build_evidence_sha256` | session.runtime_build_sha256과 같은 값, import 계약의 source/binary/receipt/start 결속을 요구; 2C fixture는 테스트용 expected pin만 소비 |
| `observation_mapping_version` | `observed_geometry_goal_v1` exact |
| map, `family`, `seeds`, `limits`, `root` | resolved episode/catalog/profile과 일치하는 owned 값; 유한값·범위·seed 일치·지원 map/layout 검사; 실제 root handle/ancestor 보호·byte budget 집행은 2D/2E |
| `input_source`, `controller`, `execution_mode` | source/controller/mode 규칙과 session/episode의 현재 선언이 일치; replay는 현재 입력 주체 사용 |
| running 및 lease | 현재 running 회차와 exact owner binding만 attach; preparing/terminal 값의 재사용 거부 |

source 조합은 기존 데이터 계약을 따른다. `human`은 `human_play`와 manual/replay만 허용한다. automatic은 automated이고 automated는 `human_play`를 거부한다. 실제 Runtime source는 `automated_runtime` 또는 검증된 human provenance다. `offline_procedural`·`test_fixture`는 구조 하네스용 출처이며 production 권한을 부여하지 않는다. 2C에서 human/automated 조합을 시험해도 외부 evidence가 없는 실행은 격리 fixture로만 집계한다.

invalid source/build, 빈 값·잘못된 digest 형식·pin mismatch·family/seed 모순은 attach 실패다. trim/lowercase/default로 수선하지 않는다. collection intent가 있으면 **legacy fallback 금지**다. production용 `public bool/digest setter`나 forgeable success constructor를 만들지 않는다. 실제 권한 검증의 획득 경로는 Task 3/4까지 닫아 둔다.

기존 실제 Host 검사에는 **transient fixture World**를 사용하는 별도 **fixture namespace**만 허용한다. dev issuer는 그 실제 World 객체 identity를 lease에 결속한다. production map 문자열을 복사했다고 실제 map 검증을 통과한 것으로 표시하지 않는다. 모든 이런 실행은 **실제 map 검증 증거 0**, real collection authority 0이며 `WITH_DEV_AUTOMATION_TESTS` 밖에서는 발급 경로가 없다. production의 exact MVP map·실제 owner 검증 요구는 보존한다.

<!-- C:lease -->
## 5. 매 진입마다 확인할 lease와 종료 수명

collection intent는 수집 경로를 선택한 사실이며 authorization을 발급하지 않는다. **exact World/Host/episode**와 session, context identity, epoch를 함께 비교한다. DecisionId나 UUID 문자열 하나만으로 current 상태를 판단하지 않는다. epoch의 **wrap/reuse 금지**를 지키고 소진이면 fail-closed다.

collection intent가 있을 때 context 부재, preparing, terminal, stale lease, wrong World/Host, episode/epoch 불일치면 해당 시도는 실패한다. 잘못된 시도에서 유효한 다른 회차의 lease를 갱신·취소하지 않는다. context가 없는 실패도 legacy 성공으로 넘어가지 못하도록 Host 진입 경계에서 차단한다. intent 없는 legacy 경로의 기존 동작과 retry 수명은 보존한다.

검사는 `direct decision`, `retry 예약`, **이미 예약된 callback**의 실행 직전, future receipt 소비·publication 진입에 필요하다. 2C는 receipt를 실제 생산하지 않으며, callback/lease 검증 seam의 stale 거부까지만 시험한다. queued callback은 예약 당시 exact lease를 보유하고 현재 lease와 재대조한다. 새 World에서 same DecisionId가 발급돼도 old callback은 거부한다.

World 종료, Host `OnUnregister`/`EndPlay`/`TeardownAssembly`, terminal/cancel은 먼저 lease를 revoke한다. dependency reset·authority release·외부 callback 전에 revocation이 관찰돼야 한다. teardown을 여러 번 거쳐도 stale 권한이 살아나지 않는다. **failed episode reopen 금지**다. context detach 또는 fresh epoch만으로 같은 실패 ID를 다시 attach하지 않는다. root/sequence 수명은 World보다 길며 allocator와 root 소유 구현은 2D/Task 3로 남긴다.

<!-- C:terminal -->
## 6. 관측 실패의 종료 순서와 시간 우선순위

Host는 hard observation failure를 확인하면 **callback·파일 I/O 전에 terminal latch를 닫고 exact lease를 revoke**한다. 실패 diagnostic/owner signal은 그 뒤에 보낸다. 같은 회차의 새 Decision·retry·publication이 latch를 통과할 수 없어야 한다.

1. 현재 authoritative monotonic 시각을 확보하고 기존 lifecycle 규칙을 적용한다. 회차 전체 deadline은 준비 시간을 포함한다. Host의 별도 Decision deadline을 회차 deadline으로 대체하지 않는다.
2. deadline 전에는 `failed`, at/after deadline에는 `timed_out`이다. 만료 직전·정확한 경계·직후를 각각 검사한다. 실제 mapping 실패는 diagnostic에 별도 보존한다.
3. bool-only 실패 reason은 `observation_mapping_failed`다. duplicate exact primary/conflicting mandatory source 등 **직접 검사한 precondition**이 실제 실행된 경우만 상세 이유를 남긴다. 모든 Host false를 관측 오류로 분류하지 않는다.
4. normal sensor absence·미충족 event trigger는 기존 wait/timeout이다. 유효 위치 전용 primary·missing sentinel은 정상 입력이다.
5. nonfinite/backwards time과 lifecycle 검증 예외는 session blocked다. 실패 이전 immutable lifecycle을 다시 성공 상태로 사용하지 않는다. reset precondition은 deadline 변환보다 먼저 확인한다. 아직 terminal이 아닌 상태의 reset은 거부한다. 이미 terminal이면 기존 outcome과 명시적인 reset 결과를 보존한다.

storage/sidecar/diagnostic persistence 실패 및 reset failed/unverified의 session-blocking 규칙은 기존 계약 그대로다. 2C는 실패 signal/owner seam에 대한 memory 차단을 검증한다. 실제 diagnostic·terminal 파일의 저장은 2E/Task 3로 남긴다. 메모리 Snapshot만 있는 진단은 `snapshot_present=false`, `snapshot_ref=null`이며 Request 전 실패에 가짜 DecisionId를 발급하지 않는다.

<!-- C:callbacks -->
## 7. callback 재진입과 committed-start stack 보존

callback을 호출하는 작업은 현재 **authority/context를 local strong pin**으로 보유한다. local strong pin은 객체의 강한 소유권을 보존할 뿐 살아 있는 권한을 보장하지 않는다. callback 뒤 exact **lease 재검사**와 Host/World/authority의 현재 binding 검사를 수행하고 stale이면 실패 반환한다. 새 Host member를 다시 읽어 예전 작업을 새 authority에 이어 붙이지 않는다.

재진입 callback이 direct decision, retry, detach/teardown 또는 새 attach를 시도하는 hostile fixture를 둔다. 종료 잠금과 revocation이 callback 첫 진입에서 이미 보이는지 검사한다. old callback은 거부되고 **현재 B 불변**이어야 한다. callback 후 collection 성공을 발행하거나 원래 local 객체 대신 새 context를 사용하는 경로가 없어야 한다.

**committed-start stack 안의 동기 reset/reattach 금지**를 유지한다. Task 2C는 latch/revoke와 stop 요청까지만 수행한다. owner가 stack unwound/drained를 확인한 뒤 Task 3에서 실제 입력 정지·teardown·World reset을 수행한다. same-stack stop 요청을 authority/World 파괴로 연결하지 않는다. 일반 teardown의 revoke-first 순서와 committed-start 안의 지연 teardown을 함께 검증한다.

새 실패 신호의 허용 경계는 **stop-only callback**이다. callback 안의 teardown은 요청으로만 수락하고, actual dependency release는 외부 result dispatch까지 끝난 후에 실행한다. Host 자체의 depth가 0이라는 사실만으로 외부 Executor raw sink가 해제 가능하다고 단정하지 않는다. 이 약속을 **arbitrary synchronous UnregisterComponent/DestroyWorld 지원으로 확대하지 않는다**. 실제 owner/reset이 없고 collection 저장 경로도 닫힌 이 단계에서는 callback이 원본 World를 파괴하는 API를 제공하지 않는다.

이미 발생한 Commit/Skill start 또는 producer verified 사실에는 **counter rollback 금지**다. 2C fixture가 이를 새 저장 성공이나 실제 reset 성공으로 기록해서는 안 된다. 후속 producer/bridge의 post-Commit 실패 검사는 2D/2E다.

<!-- C:owner -->
## 8. terminal evidence와 reset receipt의 owner seam

`terminal-evidence receipt`는 이전 terminal 기록의 persist/readback 확인, `verified-reset receipt`는 exact 이전 episode/World lease에 결속된 초기화 확인을 전달하는 **owner seam**이다. 이 용어는 내부 경계의 역할 설명이며 새 Schema 필드나 직렬화 형식을 정의하지 않는다.

Task 2C에서 이 seam은 **fixture-only**, 생성·주입·friend 선언·정의·wrapper 모두 `WITH_DEV_AUTOMATION_TESTS`로 제한한다. production caller가 bool 성공 선언이나 digest만 제출해 receipt를 만들 수 있는 API는 금지한다. fixture는 terminal-evidence와 verified-reset을 별도로 제어하여 missing/mismatch/stale 조건을 시험한다. fixture 성공 수를 real authority 또는 real collection 수에 더하지 않는다.

다음 회차를 여는 조건은 terminal evidence persist/readback과 verified reset이 모두 이전 exact lease에 일치하며 현재 stack이 drained된 것이다. 허용되는 대상은 **새 collection_episode_id**와 새 lease뿐이다. 같은 실패 회차는 reopen하지 않는다. reset failed/unverified, terminal evidence 미보존, diagnostic persistence 실패는 다음 attach와 completion pin을 차단한다. 영구 session 차단 규칙은 기존 계약을 따른다.

**실제 reset 미구현, 실제 authority 검증 미구현**이다. Task 3 trusted owner가 외부 evidence 확보·terminal 파일 보존·입력/Timer/Skill/Knowledge 수명 종료·새 World 준비를 증명한다. Task 4 verifier가 실제 발행 권한을 확인한다. 이 구현 전에는 **production collection closed**다. Task 2C에 GameInstance owner, 실제 receipt 발급자, completion pin publisher를 함께 구현하지 않는다.

<!-- C:policy -->
## 9. 실패 및 재개 정책의 문서 oracle

이 표의 영어 값은 문서 하네스용 case label이다. 새 runtime enum·Schema field가 아니다.

| 조건 | 결과 | 필수 oracle |
|---|---|---|
| intent_absent | legacy | 기존 retry 보존 |
| context_missing_preparing_terminal_stale | reject | legacy fallback 0 |
| wrong_world_host_episode_epoch | reject | 현재 다른 lease 변경 0 |
| invalid_source_build | reject | 기본값 수선 0 |
| hard_failure_before_deadline | failed | latch/revoke 뒤 callback |
| hard_failure_at_or_after_deadline | timed_out | 관측 실패 diagnostic 별도 |
| queued_old_callback | reject | 현재 B 변경 0 |
| reset_without_terminal_evidence | reject | 새 attach 0 |
| reset_failed_unverified | session_blocked | 새 attach 0 |
| verified_reset_and_terminal_evidence | new_episode_only | fixture-only receipt·새 lease |

<!-- C:coverage -->
## 10. C01–C07의 단계별 검사 범위

아래 `2C 검사 범위`는 기존 부분 범위를 그대로 보존한다. 실제 등록 검사와 last runtime checkpoint의 연결은 다음 표에 따로 둔다. 현재 문서 검사 성공을 Runtime 성공으로 읽지 않는다. C01–C07 전체 완료는 2C의 acceptance가 아니다.

| ID | 2C 검사 범위 | 남은 단계 | 2C 완료로 주장할 수 없는 항목 |
|---|---|---|---|
| C01 | context copy 불변 | 2E | Record metadata 고정·pending Record 불변 |
| C02 | 현재 source/controller/mode 검증 | 2E/3 | 모든 phase raw metadata·실제 입력 provenance |
| C03 | fixture attach·invalid source/build 거부 | 3/4 | 실제 owner/build authority |
| C04 | intent/lease fail-closed | 2E | diagnostic 실제 저장 |
| C05 | old callback·reset receipt 장벽 fixture | 3 | 실제 입력 정지·World reset |
| C06 | readiness false 유지 | 2D/2E/4 | committed receipt·bridge·최종 승인 검증 |
| C07 | resolved metadata·limits 입력 검증 | 2D/2E | group derivation·join·storage budget 집행 |

<!-- C:runtime-tests -->
### C01–C07과 실제 등록 검사 연결

이 연결표는 `final-05/source/Source/NeuralGame/AINativeNPC/Tests/AINativeNPCCollectionHostTests.cpp` snapshot과 `c2-final-host-01`의 Host 25 목록을 따른다. 위 부분 범위표와 기능 요구사항은 변경하지 않는다.

| ID | 실제 등록 test-name | 이번 연결의 한계 |
|---|---|---|
| C01 | `AINativeNPC.Collection.Host.C01.ImmutableContextCopy` | 전체 payload·caller mutation·World 이후 pin 검사; Record metadata/pending 저장은 후속 |
| C02 | `AINativeNPC.Collection.Host.C02.SourceModeControls` | 현재 source/controller/mode의 fixture 조합; 실제 human provenance·모든 phase raw metadata는 후속 |
| C03 | `AINativeNPC.Collection.Host.C03.StrictContextValidation` | independent fixture expected pin·malformed 값 거부; 외부 build/owner authority 검증은 후속 |
| C04 | `AINativeNPC.Collection.Host.C04.IntentRejectsMissingOrInactiveContext` | 실제 Host 진입·예약의 fail-closed; diagnostic 실제 저장은 후속 |
| C05 | `AINativeNPC.Collection.Host.C05.OwnerResetBarrierAcrossWorlds` | World 밖 owner·형별 exact receipt·새 ID·old callback 장벽; 실제 입력 정지/reset/drain 측정은 후속 |
| C06 | `AINativeNPC.Collection.Host.C05.OwnerResetBarrierAcrossWorlds` 내 `HostCheckNoCollectionWrites` | `IsResolvePolicyReady=false`와 저장/Commit 없음 확인; Approved/production_eligible는 문서 불변식 |
| C07 | `AINativeNPC.Collection.Host.C03.StrictContextValidation` 및 `AINativeNPC.Collection.Host.C01.ImmutableContextCopy` | resolved metadata·limits의 입력 검증/복사만; group derivation·join·storage budget 집행은 후속 |

C06 전용 등록 test는 없다. 공통 `HostCheckNoCollectionWrites`의 `IsResolvePolicyReady` 검사를 실제 승인 검증이나 committed receipt/bridge 구현으로 세지 않는다.

추가 실제 등록 이름은 모두 `AINativeNPC.Collection.Host.` 접두어 아래다. `Failure.LatchBeforeCallback`, `Failure.DeadlinePrecedence`, `Failure.InvalidClockBlocksSession`, `Failure.Classification`은 실패 순서·시간·분류에 연결한다. `Retry.LegacyStillRunsOnce`, `Retry.StaleCallbackCannotTouchNewEpisode`는 legacy 대조·old callback 거부에 연결한다. `Lease.TeardownRevokesAndExhaustion`, `Lease.RevokeBeforeDependencyRelease`는 revoke-first·소진에 연결한다. `Reentry.ValidatedAttachCannotReplaceFailedEpisode`, `Reentry.StopWaitsForExternalDrain`, `Reentry.AttemptPinsOutliveHostBinding`은 재진입·fixture drain·strong pin 수명에 연결한다. 이름과 PASS의 연결은 해당 run에 한정하며 최신 bytes·독립 승인으로 확대하지 않는다.

<!-- C:steps -->
## 11. 구현자 작업 순서

각 단계는 기존 `Tests/AINativeNPCCollectionHostTests.cpp`의 새 실패 assertion → 실제 RED → allowlist의 최소 구현 → focused GREEN → 해당 legacy 회귀 순서다. 아래는 보존하는 구현·검증 요구사항이며 실제 등록·실행 연결은 §10에 둔다. 아직 남은 acceptance를 이미 구현된 검사 이름만으로 닫지 않는다. API와 권한 의미를 넓히지 않는다.

### 2C-1. 복사된 입력과 격리된 attach

1. C01/C02/C03/C07의 input 부분을 검사한다. 유효 fixture context를 먼저 확보한 뒤 원본 family/seed/build/root/limits 값을 바꿔도 복사본이 유지되는지 본다. malformed source·build pin mismatch·빈 값·family/seed 모순에는 output 미발행을 요구한다.
2. `CollectionContext.h/.cpp`에 immutable 값·private construction 경계를 추가한다. public aggregate/flag로 real 권한을 만들지 않는다. 실제 metadata writer와 group derivation은 추가하지 않는다.
3. `FAINativeNPCCollectionHostTestAccess`를 기존 test TU에서만 확장한다. `WITH_DEV_AUTOMATION_TESTS` 전체 경계를 유지한다. ShippingGuardTests의 다른 friend 이름을 재정의하지 않는다.

### 2C-2. direct decision과 retry의 exact lease

1. C04/C05 fixture에서 valid running 진입을 positive control로 확인한 뒤 context 없음·preparing·terminal·wrong World/Host/episode·stale epoch를 각각 대조한다. invalid 진입은 Finalize/policy/Request/Capture/Commit이 증가하지 않아야 한다.
2. `TryStartCurrentDecision`과 `ScheduleDecisionForAuthority`에 intent 구분과 lease 검사를 연결한다. context 검사만 구현하고 실제 caller에 연결하지 않은 상태를 완료로 세지 않는다.
3. 실제 next-tick callback을 먼저 예약한 뒤 A를 revoke한다. 새 B와 same DecisionId를 준비하고 old callback을 drain하여 B 불변과 새 Decision 0을 확인한다. 단순히 타이머 등록 수만 확인하는 검사로 대체하지 않는다. intent 없는 legacy의 기존 bounded retry를 별도 positive control로 둔다.

### 2C-3. 관측 실패의 latch와 시간 경계

1. 기존 `PrepareDecisionFeatures`의 real Populate 실패와 직접 검사한 primary conflict 경로를 사용한다. observer callback 첫 명령에서 latch/revoke 상태를 확인하고 direct/retry 재진입을 시도한다.
2. 회차 deadline 직전·동일·이후에 같은 mapping failure를 주어 failed/timed_out을 대조한다. bool-only generic reason과 직접 확인한 원인만 세분화하는 규칙을 시험한다. 정상 sensor 부재/위치 전용/sentinel 및 다른 Host false를 보존한다.
3. lifecycle invalid/nonfinite/backwards와 reset precondition 실패 시 session 차단을 검사한다. 실제 파일 저장 성공을 mock하여 새 회차를 여는 경로는 만들지 않는다.

### 2C-4. callback 수명과 teardown

1. callback 중 detach/terminal/teardown 요청·새 attach 시도와 callback 뒤 stale 결과를 검사한다. authority/context의 **강한 소유권**이 유지되고 재진입 작업이 현재 권한을 바꾸지 못해야 한다.
2. callback 전 local pin과 callback 후 재검사를 실제 Host 호출부에 둔다. `TeardownAssembly` 및 `OnUnregister`/`EndPlay`의 revoke-first를 연결한다. committed-start 안에서는 stop 요청만 전달한다.
3. stack이 unwound/drained되기 전 synchronous reset·reattach가 거부되는지 fixture로 확인한다. 실제 World reset은 Task 3까지 구현하지 않는다.

### 2C-5. owner receipt 장벽과 완료 판정

1. C05의 terminal-evidence/verified-reset receipt를 각각 missing·wrong episode/World·stale·failed/unverified로 만든다. 새 attach 0과 failed episode reopen 0을 검사한다. 유효한 두 fixture receipt와 drained 경계 뒤 새 ID만 허용하는 positive control을 둔다.
2. C06의 readiness false와 production attach 부재를 검사한다. fixture 외의 public 성공 setter/receipt 생성자 노출을 점검한다.
3. C01–C07 부분 범위의 actual test-name과 결과를 §10에 연결해 handoff한다. Record/metadata/group/저장/receipt 생산 완료로 확대하지 않는다.

소스·기존 산출물의 **원본**은 보존한다. 새 제품 판단이나 allowlist 밖 의존이 필요하면 **중단**하고 정확한 입력·누락된 authority·영향 파일을 보고한다. invented owner, 임의 lifecycle 예외, 공개 flag로 통과시키는 구현은 허용하지 않는다.

<!-- C:verification -->
## 12. 적용 경로와 검증 증거

구현자는 Task 2의 다음 substep을 시작할 때 이 문서를 읽는다. 문서의 강제 검사는 `tests/test_collection_context_contract_document.py`와 `tests/test_collection_host_bridge_contract_document.py`다. copy의 강제 경계는 C++ Host/context 진입점이며 실제 실행 증거는 이름이 고정된 checkpoint에 결속한다. Markdown 존재나 pytest 성공만으로 Runtime enforcement가 활성화되지 않는다.

### 부모가 실행할 문서 검사

cwd는 `/home/namingsense/AI-Native-NPC`다. 이번 상태 보강 assertion은 작성했으며 아직 실행하지 않았다. 실행과 결과 확인은 부모 담당이다. 아래는 문서 검사 명령이며 Unreal 실행 명령을 포함하지 않는다. 과거 `docs-worker` 결과는 이번 수정분의 통과 증거로 사용하지 않는다.

```bash
PY=/mnt/d/Codex-cli/NeuralProject/NeuralGame/ML/.venv/bin/python
RUN=/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/docs-status-worker
# RUN 아래 red/focused/full의 서로 다른 basetemp와 JUnit 경로를 사용한다.
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider tests/test_collection_context_contract_document.py \
  tests/test_collection_host_bridge_contract_document.py -q \
  --basetemp "$RUN/focused-tmp" --junitxml "$RUN/focused.xml"
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR="$RUN" "$PY" -B -m pytest \
  -p no:cacheprovider -q --basetemp "$RUN/full-tmp" --junitxml "$RUN/full.xml"
git diff --check
```

기존 문서에 새 assertion을 먼저 실행해 missing/conflicting clause의 RED를 보존한다. missing-file/import error를 RED로 세지 않는다. GREEN 뒤 clause 삭제·scope 이동/중복·정책 약화·C01–C07 범위 승격·source allowlist 확장의 in-memory negative mutation을 실행한다. command/exit/stdout, JUnit, 원본 bytes, 최종 bytes, baseline 대비 delta를 evidence에 남긴다. 상위 계약/Schema/generated/adapter와 기존 evidence는 수정하지 않는다.

### Runtime 검사 요구 — 실행과 최종 재검증은 부모 담당

§11의 **예상 Runtime RED** 요구는 보존하며, 이미 관측한 중간 실패와 last runtime checkpoint는 §2에 구분했다. 후속 보완도 기존 Host fixture를 통과하는 behavior assertion과 실제 실행 결과를 남긴다. 0-discovery, compile/link error, timeout은 행동 RED가 아니다. absent-header assertion은 API 부재만 증명하며 구현 후 actual caller와 mutation 검사가 필요하다.

`AINativeNPC.Collection.Host`의 기존 H01–H09와 새 2C test를 분리해 목록을 고정한다. `AINativeNPC.Collection.Observation`의 기존 37-case는 회귀 대상이다. exact test-name multiset의 발견·시작·종료·report·exit를 대조한다. 단일 build owner가 §2의 물리 copy에서만 직렬 build/run한다. Host 계약 §11의 원본 경로 예시는 argument interface 참고용이며, 실제 project/script/log 경로는 모두 copy와 새 evidence에 결속한다. broad 실행 여부는 실제 승인 범위와 원본 보존 preflight에 따른다. 기존 고정 Capture 삭제 fixture가 있으므로 original project에서 임의 실행하지 않는다. 절차는 [Host 계약 §11](scenario-host-capture-v1-contract.md#11-실행-위치와-검증-명령)을 따른다.

Task 2C acceptance는 fixture context/lease와 Host enforcement의 실제 검증까지다. H10, 실제 수집 저장·발행, 실제 runner/reset/UI, 실제 authority/ML import, 사람 Play, Shipping/cook/package·학습 승인은 후속으로 남긴다.
