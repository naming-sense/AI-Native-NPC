# 학습용 시나리오 실행·수집 도구 V1 구현 계획

> **For Hermes:** `subagent-driven-development`로 문서·하네스, Runtime, ML 연결을 순서대로 구현하고 독립 검토한다. 이번 요청에는 commit/push가 포함되지 않는다.

**Goal:** 하나의 시나리오 정의로 직접 플레이·자동 실행·조건 재실행을 제공하고, 실제 Unreal 판단 기록을 출처와 함께 안전하게 수집한다.

**Architecture:** 기존 `L_AINativeNPC_MVP`와 정확한 native Guard·Quinn 플레이어를 재사용한다. 세션 소유자는 world 재생성 사이에도 실행 조건·예산을 유지하고, 회차마다 새 World에서 실제 이동·감지·Goal·Commit을 거친다. 원본 ANPCCAP2와 Dataset v2는 유지하며 수집 정보는 별도 sidecar/index로 결속한다.

**Tech Stack:** Unreal Engine 5.7 C++·native UMG, 기존 GameDevMCP, Python ML CLI, JSON 계약·pytest·Unreal Automation.

**상태:** 수집 검증기와 디코더의 독립 명세·품질 검토를 마쳤다. 순수 관측 adapter도 구현·Unreal 자동검사·독립 명세·품질 검토를 마쳤다. Runtime import 설계의 지정 문제도 독립 재검토를 통과했다. provenance Schema·구조 검증기는 구현·자동검사·독립 명세·품질 검토를 마쳤다. 품질 검토의 오류 처리 문제도 수정 뒤 독립 재검토를 통과했다. Task 2B Host 관측 연결 코드와 Host 9·Observation 37 실행 증거가 존재한다. S01만 좁게 승인됐으며 `whole_task2b_closed=false`다. [Task 2C context/lease](scenario-collection-context-v1-implementation-plan.md)는 아래 copy 구현·실행 checkpoint까지 진행됐다. 수집 저장·발행, 실제 runner/reset/화면, 출처·정답 승인 및 ML 가져오기는 후속이다. 이 문서는 기능 전체 완료나 Production 승인을 뜻하지 않는다.

<!-- T2C:historical -->
**역사적 문서 단계:** Task 2C 계획·문서 하네스 작성 당시의 **C++ 미수정, Unreal build/run 미실행**은 **문서-only checkpoint에 한한 역사적 사실**이다.

<!-- T2C:current -->
**현재 Task 2C:** 허용된 **copy 5파일 구현**을 최신 소스로 다시 검증했다. **부모 확인 last runtime checkpoint**는 `c2-final-build-01`의 build 성공, `c2-final-host-01`의 **Host 25 PASS**(warning 53), `c2-final-observation-01`의 **Observation 37 PASS**(warning 0), `c2-final-broad-01`의 **broad 229 PASS**(warning 72)다. 관련 snapshot·run 증거 root는 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/final-05`다. WeakObjectPtr header include 보완 뒤 `c2-nodev-compile-02`의 3개 TU compile-only 검사도 통과했다(noShipping/noLink/noRuntime). runtime checkpoint 자체의 판정은 **최종 최신 bytes 실행 검증 완료; 독립 승인 아님**이며, 고정 부분 범위의 독립 승인은 아래 approval-record에 별도로 기록한다. `final-verification-02/result.json`은 exact test-name multiset, 원본 입력·Capture 보존, source delta 5개, 기존 H01–H09 본문 보존 및 focused/broad 입력 동일성을 확인한다.

<!-- T2C:limits -->
**독립 SPEC→QUALITY 승인 완료; 고정된 Task2C 부분 범위만**, **production collection closed**다. `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다. **실제 collection 저장 미구현**, **실제 reset 미구현**이다. **terminal/reset/dispatch-drain receipt는 dev fixture 값**이며 **실제 Executor drain 측정 미구현**이다. **GameInstance owner·production issuer·ML import 미구현**, **원본 승격 없음**, **commit/push 없음**이다. 이 결과는 학습/Production 승인으로 확대하지 않는다.
<!-- T2C:approval-record -->
**고정 후보의 최종 검토 기록:** 독립 SPEC와 QUALITY가 같은 `final-05` source와 실행 증거의 Task2C 부분 범위를 승인했다. 부모는 subject 전체 파일과 두 검토 산출물의 동일성을 재검증했다. 승인 기록은 `/home/namingsense/AI-Native-NPC-evidence/collection-next-uq63w5dx/review-01/acceptance/acceptance.json`이다. **원본 승격 없음**이며 실제 저장·reset·production authority·학습 준비 완료는 이 승인에 포함하지 않는다. 검토 당시의 상태 문서와 기존 증거는 read-only subject에 그대로 보존하고, 이 단락과 승인 상태 문구만 현재 문서에 갱신했다.
<!-- T2C:end -->

<!-- T2D:active -->
**현재 후속 단계:** [Task2D 안전 저장·동일 이미지 검증 세부 계획](scenario-collection-storage-v1-implementation-plan.md)과 `tests/test_collection_storage_contract_document.py`를 먼저 확정한다. 부모가 lower Store/Dataset과 실제 Host wiring을 별도 구현·검증한다. **Task2D 전체 완료는 lower test만으로 주장 금지**다. Task2E metadata/group/context join·sidecar·diagnostic, Task3 실제 owner/reset/UI, Task4 authority/import는 후속으로 구분한다. 문서/하네스 작성자는 C++ 구현·실행을 수행하지 않는다.

---

## 1. 기준과 허용 범위

상위 요구는 [학습 데이터 계획의 시나리오 도구 설계](ml-data-pipeline-v1-implementation-plan.md#scenario-collection-plan)다. 상황·시나리오·변형 사례·실행 회차를 구분한다.

- 실제 Runtime 경로는 `ANeuralGameCharacter::DoMove` → Animation Notify·Hearing/Sight → Knowledge → Goal → Candidate → Commit이다.
- `InjectHearingForTest`·`InjectSightKnowledgeForTest`, Tensor 또는 Knowledge 답안 주입은 실제 수집 경로에서 금지한다.
- 초기 지원은 기존 단일 `Player.Main`과 Guard의 위치·거리·실제 이동·소리·등장·시야 상실이다. 실제 벽 가림은 collision/LOS 검증이 있을 때만 지원으로 바꾼다.
- 우호·중립·적대 관계 변경, 낮은 신원 확신 설정, 경로 불가 Greet는 현재 Runtime 연결을 확인하지 못했다. 목록에는 제외 이유를 표시하고 실행하지 않는다.
- 시나리오 조건은 관측을 발생시키는 원인이다. 숨은 기대 결과·향후 사건·정답은 모델과 Teacher 입력에 전달하지 않는다.
- `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다. 수집 후보의 저장·검증은 학습 데이터 전체 승인과 별개다.
- 사용자 직접 플레이의 확인은 사람의 실제 입력과 피드백이 있어야 완료다. 자동화 결과로 이를 대신하지 않는다.

## 2. 발견된 선행 보완

### 2.1 관측 Feature 연결

Task 2B의 현재 Host는 `PrepareDecisionFeatures`에서 승격 전 Knowledge를 복사하고 현재 Pawn pose로 Populate를 호출한 뒤 Finalize한다. Host 9·Observation 37 실행 증거와 S01의 제한된 승인을 보존한다. copy에는 Task 2C context/lease 구현·실행 checkpoint가 추가됐다. 실제 수집 Capture roundtrip인 H10과 collection 저장·발행은 남아 있다.

이 연결은 [관측 Feature 연결 V1 계약](scenario-observation-adapter-v1-contract.md)에 따라 작은 순수 adapter와 실패 검사로 검증한다. 위치·거리·방향·관측 age/confidence·Goal만 연결하고 CandidatePair는 보존한다. 관측 근거가 없는 관계·성격·경로 정보는 지원 축에서 제외한다. 순수 adapter의 단위·동일 위치 convention·missing sentinel·실패 시 Draft 보존 검토와 기존 Host 연결을 보존한다. collection 실패 수명은 Task 2C의 최신 copy 실행 검증 완료와 고정 부분 범위의 독립 SPEC→QUALITY 승인 완료로 구분한다.

### 2.2 모든 수집 단계의 충돌 없는 저장

현재 ResolveShadow는 process session/sequence를 사용하지만 일반 Phase3B 경로는 고정 이름의 파일을 삭제하고 다시 쓴다. 수집 모드에서는 Resolve 이전 단계까지 모두 새 session/sequence 경로를 사용하고 기존 final·pending·marker·임시 파일이 있으면 거부한다. 기존 일반 플레이의 계약 변경 여부는 회귀 검사와 함께 별도로 명시한다.

자동 실행이 `resolve_greet_user_play_v1`로 기록되지 않도록 capture producer가 현재 회차 context에서 family·seed·출처를 읽는다. 원본 기록의 identity를 사후 수정하지 않는다.

## 3. 수집 계약

권위 파일은 `contracts/current/scenario_collection_v1.schema.json`과 `contracts/current/scenario_catalog_v1.json`이다. 카탈로그는 버전·지원 상태·고정 허용 조건·사건 순서·family를 가진다. 임의 console 명령·클래스·에셋 경로를 실행하는 기능은 만들지 않는다.

### 세션과 회차

- `session_id`는 수집 세션, `collection_episode_id`는 한 번의 실행을 식별한다.
- Capture의 기존 `episode_id`는 capture별 identity로 보존한다. 수집 회차 ID로 덮어쓰지 않는다.
- 수동·자동·재실행은 같은 카탈로그와 확정된 조건을 사용한다. 재실행은 새 회차 ID와 `replay_of`를 가진다.
- `execution_mode`와 실제 입력 주체를 각각 기록한다. 재실행이라는 이유로 사람 플레이로 분류하지 않는다.
- catalog/profile·Runtime build·계약 identity, map/layout, seed, 조건, 실제 사건 시각, 종료·reset 결과를 고정한다.
- 동시 회차는 하나다. 기본 실행 예산은 도구 검증용이며 학습량 기준으로 해석하지 않는다.

### 원본·출처·진단

- committed 항목은 `.anpccap2`·`.committed`의 상대 경로·크기·SHA-256과 원본 sample/episode/decision/input identity를 결속한다.
- Capture producer가 marker 발행과 exact readback을 마친 뒤에만 수집 bridge에 성공을 알린다. sidecar 실패 시 세션을 중단하고 원본 Capture는 보존한다.
- 진단은 별도 파일에 단계·이유·시간·Snapshot 유무를 기록한다. 없는 Snapshot에 가짜 identity/hash를 넣지 않는다.
- Snapshot 없는 timeout·준비 실패·중단은 학습 row와 유효 Capture 분모에서 제외한다.
- 수집 출처와 label 출처는 분리한다. 기존 `source_type` enum은 확장하지 않으며 Utility 선택을 Teacher Silver/Human Gold로 자동 승격하지 않는다.
- 원본 index와 annotation은 append-only 산출물이다. 재실행·재분석은 새 파일을 만들며 기존 자료를 덮어쓰지 않는다.

### 검증과 분할

- 입력은 strict 필드·타입·유한값·범위·중복 검사를 통과해야 한다.
- 상대 경로는 신뢰한 수집 root 아래에 있어야 하며 absolute·`..`·symlink escape를 거부한다.
- catalog/build/contract mismatch, marker 누락·변조, sidecar identity 불일치, 자동 실행의 human 오분류를 거부한다.
- 기존 `input_content_hash`를 보존한다. coverage에는 entity/episode identity를 제외한 모델 입력 fingerprint를 별도로 사용한다.
- family별 split 배정을 명시하며 동일 family의 seed·거리 변형을 서로 다른 split으로 보내지 않는다. 미배정은 `unassigned`로 남긴다.
- 실행 회차·판단·committed·정책 적합·label·Dataset row 수를 따로 계산한다. 파일을 다시 검증해 집계하며 선언 수량을 그대로 믿지 않는다.

## 4. Runtime 실행 수명과 화면

세션 소유자는 `UGameInstanceSubsystem`, 회차 실행은 현재 World와 묶인다. 회차 사이에는 같은 MVP map을 새 World로 열어 Pawn·Controller·Knowledge·identity·StateTree·Timer·플레이어 emitter를 새로 만든다. 이전 World/입력/예약 사건의 종료를 확인하지 못하면 다음 회차를 시작하지 않는다. process-wide capture sequence와 기존 파일은 reset하지 않는다.

화면은 시나리오 선택·설명·지원/제외 이유·허용 seed/조건, 직접 플레이, 자동 실행, 같은 조건 재실행, 중단, 결과·저장 위치를 제공한다. 새 native `UUserWidget`을 사용하고 실제 화면·버튼 효과를 PIE에서 확인한다.

자동 실행은 플레이어 이동과 월드 사건만 제어한다. 기본 Resolve 사례는 시야 밖 실제 발소리 → Navigate/Search 관측 → 소리 위치 근처에 등장 순서를 사용한다. 목표 상태가 관측되지 않으면 준비/사건 timeout으로 남기며 NPC 상태를 강제로 바꾸지 않는다.

실행 전 최대 회차·회차/준비 시간·저장 byte 한도를 고정한다. 취소는 이동과 예약 사건을 정지하고 종료 기록을 보존한다. 저장 실패·초기화 실패는 다음 회차를 차단한다.

## 5. 구현 순서와 파일 경계

### Task 1: 계약과 hostile 하네스

- 추가: `contracts/current/scenario_collection_v1.schema.json`, `contracts/current/scenario_catalog_v1.json`.
- 추가: `tools/validate_scenario_collection.py`, `tests/test_scenario_collection_contract.py`.
- 범위 밖 조건·미지원 항목·duplicate ID·path escape·미확정 진단 승격·출처 오분류·split 누수·budget/reset 실패를 먼저 실패시킨다.
- 문서/Schema/하네스의 exact identity와 독립 검토를 확정한 뒤 Runtime 구현을 시작한다.

### Task 2: 실제 관측과 capture bridge

**상태:** 순수 adapter와 원래 37-case Automation은 구현·독립 명세/품질 검토 완료로 동결한다. Task 2B Host observation 코드는 존재하며 2026-10-25의 `fresh-host-02` Host 9·`fresh-observation-01` Observation 37 실행이 있다. S01은 fixture asset closure·fail-closed 입력 검사·실행 결속·원본 보호에 한정해 승인됐고 `whole_task2b_closed=false`다. 근거는 `/home/namingsense/AI-Native-NPC-evidence/task2b-s01-narrow-tvrp81au/acceptance/acceptance.json`과 `packet/SCOPE.md`다. H10·broad·실제 수집·학습 readiness는 그 승인에 포함하지 않으며 old438 INCOMPLETE도 유지한다. [활성 계약·문서 하네스](scenario-host-capture-v1-contract.md)를 따르는 [Task 2C context/lease 구현 계획](scenario-collection-context-v1-implementation-plan.md)의 copy 구현과 `c2-owner-host-01`·`c2-owner-observation-01`·`c2-owner-broad-01` 실행이 추가됐다. owner checkpoint 뒤 최신 `c2-final-*` 재검증과 고정 Task2C 부분 범위 독립 SPEC→QUALITY 승인을 완료했다. 해당 근거와 현재 제한은 상단 승인 기록을 따른다. 과거 S01 승인과 Task2D의 저장·Host 통합 acceptance는 별개다.

**Task 2 전체 코드의 exact allowlist:** `Source/NeuralGame/AINativeNPC/` 기준이다. **Task 2C는 기존 Host .h/.cpp, 새 CollectionContext .h/.cpp, 기존 CollectionHostTests.cpp만** 변경한다. Dataset/FileStore는 2D, metadata/CollectionCaptureBridge는 2E다. 과거 문서-only checkpoint와 이번 상태 문서 작업자는 C++ 수정·Unreal build/run을 수행하지 않았다. 부모의 copy 구현·실행과 구분한다.

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

`Feature/DecisionObservationFeatureAdapter.h/.cpp`와 `Tests/AINativeNPCObservationFeatureTests.cpp`는 변경하지 않는다. 새 고유 friend `FAINativeNPCCollectionHostTestAccess`는 선언·정의·wrapper 모두 WITH_DEV_AUTOMATION_TESTS로 제한한다. ShippingGuardTests의 기존 friend를 다른 TU에서 재정의하지 않는다. Task 3 GameInstance/runner/UMG·Task 4 ML·Schema/generated 변경은 제외한다.

각 substep은 test-first RED → 최소 변경 → focused GREEN → 기존 회귀 순서다. 실제 명령·실패 oracle은 연결 계약 §10–11에 따른다. 모든 Unreal build는 한 소유자가 직렬 수행한다.

| substep | 작업·실패 검사 | 완료 조건 |
|---|---|---|
| 2A 문서/하네스 | `tests/test_collection_host_bridge_contract_document.py`로 기존 계약의 missing/conflicting clause RED, 활성 문서 GREEN·부정 mutation | 정책·순서·group·allowlist 일관성, 원본 §§1–6/Schema/다른 phase 보존; C++ 실행과 구분 |
| 2B Host observation | 실제 preparation helper의 승격 전 복사·Finalize 앞 Populate 구현 존재; H01–H09 Host 9 실행 | 좁은 S01 승인 유지; H10·broad·whole Task2B 완료는 미승인 |
| 2C context/lease | immutable context attach·intent·exact World/Host/episode lease·terminal latch 구현; C01–C07 부분 범위의 실제 검사 연결표·과거 RED·last runtime checkpoint 보존 | callback 전 revoke·old retry 억제·monotonic deadline·strong pin/재검사; receipt owner seam은 fixture-only, production collection closed; 최신 bytes 실행 검증 완료·독립 SPEC→QUALITY 부분 범위 승인 완료 |
| 2D append-only/readback | [활성 세부 계획](scenario-collection-storage-v1-implementation-plan.md)의 문서/하네스→lower→Host 순서; P01–P13의 실제 Windows 충돌·race·ancestor·same-image 검사 | lower/Host oracle 분리; 모든 생산 phase·same DecisionId·World 재생성에서 이전 bytes 보존; Capture/marker 각 1회 committed readback receipt; 전체 완료는 lower test만으로 주장 금지 |
| 2E metadata/publication | Record 전 exact namespace/build/group/seed/source, producer receipt→bridge, P14–P18 RED | sidecar exact readback 뒤 accepted, 실제 Commit 뒤 sidecar 실패 원본/producer 사실 보존·session 차단·diagnostic 실패 차단 |

**Task 2 전체 acceptance 목표:** C01–C07의 metadata/group/Record 저장·receipt는 2C 완료 주장에 포함하지 않는다. 실제 owner/reset은 Task 3, authority/ML import는 Task 4다. 관측 값 변화가 실제 Tensor에 반영되고 reserved/padding/NoTarget·후보·CandidatePair·현재 Guard Utility 선택은 계약대로 보존된다. collection mode 모든 producing phase는 append-only다. hard observation failure는 해당 회차를 종료하고 terminal evidence persist/readback과 verified reset 뒤 새 회차만 허용한다. storage/sidecar/diagnostic 실패 또는 reset failed/unverified는 세션을 차단한다. bool-only 실패는 observation_mapping_failed로 남긴다. 정상 sensor 부재·위치 전용 입력·missing sentinel과 legacy retry를 보존한다.

후속 focused `AINativeNPC.Collection.Host`, `AINativeNPC.Collection.CaptureBridge`, `AINativeNPC.Dataset.RecordV2`와 broad는 실제 test-name multiset/report/exit를 대조한다. 기존 broad가 고정 `Saved/AINativeNPC/Capture/Phase3B`를 삭제하므로 preserved-source inventory/승인된 격리 실행을 선행한다. 고유 log 이름만으로 원본 보존을 주장하지 않는다. Task 3의 실제 입력 정지/World reset, Task 4 권한/importer, 사람 Play는 별도 미완료 acceptance다.

### Task 3: 세션·회차 runner와 native 화면

- 추가: `Collection/`의 GameInstance subsystem·runner·UMG widget, 전용 Automation/PIE 검사.
- 필요할 때만 `NeuralGame.Build.cs`의 UI 의존성과 PlayerController 연결을 최소 수정한다.
- 수동/자동/재실행의 동일 조건 사용, 한 회차만 실행, timeout/cancel/reset 실패를 검증한다.
- 실제 Editor에서 카탈로그 표시·버튼·이동·관측·저장·reset 결과를 확인한다.

### Task 4: ML import와 coverage

세부 기준은 [Runtime 수집 자료의 ML 가져오기 V1 계약](runtime-capture-import-v1-contract.md)이다. 검토 전 Runtime Snapshot의 weight 0, 별도 출처 index, 인증된 Teacher/Human label, 기존 procedural 경로의 생성 출처 재검증을 먼저 하네스로 고정한다. 기존 Dataset v2 형식과 weight 규칙은 유지한다.

독립 설계 검토의 발행 주체·정답 승인·최종 검증 의미 보완을 세부 계약과 문서 일관성 검사에 반영했고, 지정된 세 문제와 네 모호성의 독립 재검토를 통과했다. provenance Schema·구조 검증기와 전용 검사도 구현했고 독립 명세 검토를 통과했다. 품질 검토의 오류 처리 수정도 독립 재검토를 통과해 구조 단계를 확정했다. 실제 발행·정답 승인 권한 검증 구현은 남아 있다.

- trusted collector가 마지막에 발행한 collection index의 외부 고정값과 별도 `completion_closure`를 함께 검증한다. 기존 index에는 session/episode descriptor가 없으므로 closure가 그 이력·replay predecessor·시작 증거·catalog/execution-profile/build를 결속한다.
- 기존 증명 없는 validator 성공은 구조·내부 일관성 확인이다. Runtime import는 원본 발행 증명으로 검토 전 Snapshot까지만 허용한다. Dataset의 최종 수락은 별도 Teacher/Human 승인 증명과 `require_authorization=True`를 요구한다. qualification과 실제 학습 수락은 그 뒤의 별도 조건이다.
- 관련 API에는 keyword-only `origin_context`를 사용한다. 원본 import → label 승인 후 발행 전 변환 → 최종 derived index 순서로 결속하며, 변환 전에 미래 Dataset hash를 요구하지 않는다.
- 기존 Gold 저장 결과와 사용자의 실제 정답 결정은 보존한다. Fixture provider 결과는 통합 검사로 분리하고 실제 Teacher/Human 승인으로 집계하지 않는다. 문서 검사 통과를 실행 가능한 출처·정답 승인 검증의 완료로 표시하지 않는다.

- 기존 `tools/validate_anpc_capture_v2.py`의 동일 bytes parser/validator를 재사용하고 summary-only API를 복제하지 않는다.
- 먼저 `decode_committed_capture_bytes(capture_bytes, marker_bytes, *, path)`와 파일 wrapper `decode_committed_capture(path)`를 하네스에 추가한다. marker와 envelope·CBOR·Tensor·label 검증을 모두 마친 동일 immutable bytes에서 기존 요약과 원본 Tensor block·Candidate bytes·handle·switch term·label·시간·계약 metadata를 반환한다. 파일 wrapper는 Capture와 marker를 각각 한 번만 읽는다. 기존 `validate_capture`·`validate_committed_capture`의 요약 응답은 유지한다.
- decoder는 marker 없는 자료·변조된 자료를 반환하지 않으며, decoding 자체로 label 출처·weight·scope 또는 approval을 바꾸지 않는다. 기존 Golden fixture와 marker/path 교체·tamper 회귀로 먼저 검증한다.
- `contracts/current/capture_import_provenance_v1.schema.json`, `tools/validate_capture_import_provenance.py`, `tests/test_capture_import_provenance_contract.py`와 [형식·검사 대응표](runtime-capture-import-v1-schema-map.md)를 추가했다. 독립 명세·품질 검토와 오류 처리 수정의 독립 재검토를 마쳐 구조 단계를 확정했다. 성공은 artifact의 형식·선언된 내부 일관성 검사이며 발행 주체·정답 승인 권한을 만들지 않는다.
- 이후 실제 출처·label 증거를 사용하는 실행 가능한 보안 회귀를 작성하고 ML context/importer를 구현한다. Schema 검사, 권한 검증, 실제 데이터 생산을 별도 단계로 기록한다.
- 추가: `ML/anpc_ml/capture_import.py`, `ML/anpc_ml/collection.py`와 대응 tests.
- 수정: `ML/anpc_ml/cli.py`에 `capture import`, `collection validate`, `collection coverage`를 연결한다.
- 실제 저장된 committed 자료에서 Snapshot/manifest를 만들고 기존 Teacher/Gold/Dataset validator와 연결한다. 진단·Utility 원본을 Gold 정답으로 취급하지 않는다.
- 현재 Snapshot·Dataset validator는 `generator_or_runtime_build_sha256`를 Python generator source hash와 비교한다. Runtime import는 원본 build identity를 보존하고 이 출처 구분을 명시적으로 검증해야 한다. 통과를 위해 원본 값을 Python hash로 교체하거나 임의 runtime hash를 허용하지 않는다.
- 기존 Host의 `ComputeRuntimeBuildHash()`는 `FApp::GetBuildVersion()` 문자열 또는 fallback 문자열의 digest다. 이것만으로 최신 프로젝트 source/binary 결속을 주장하지 않는다. 수집 전용 build identity와 외부 pin의 실제 검증 경계를 Runtime bridge 계약·하네스에 먼저 확정한다.

### Task 5: 통합 검증과 사람 확인

- 문서 저장소 전체 pytest·생성기 검사, ML 전체 pytest와 focused lint.
- UE5.7 Development Editor build, focused Automation, 기존 전체 `AINativeNPC`, 실제 PIE 시나리오 연속 실행.
- 실제 파일 재검증, reset 간 출처·ID·입력 누수와 기존 Capture 보존, coverage와 split 검사.
- 실제 UI screenshot·저장 산출물을 남기고, 사용자 직접 플레이 확인은 별도로 요청한다.
- 최신 source에 결속된 독립 계약·품질 검토에서 중대한 문제가 없어야 구현 완료로 표시한다.
- Shipping/package는 이번 기능 검증 범위에 추가하지 않는다. commit/push도 이번 요청에서 수행하지 않는다.

## 6. 현재 검증 기준선

2026-10-25 작업 시작 기준 문서 저장소 100 tests·133 subtests와 ML 47 tests가 통과했다. 실행 중인 Unreal Editor/commandlet/build process는 없었다. 이전 MCP descriptor는 종료된 PID를 가리켰으므로 현재 연결 증거로 사용하지 않는다.

이 기준선은 새 시나리오 도구의 실행 증거가 아니다. 단계별 검증 결과와 남은 사람 확인을 완료 후 갱신한다.

관측 Feature 연결은 독립 설계 검토 뒤 Unreal 실패 하네스를 추가했다. adapter가 없는 상태에서 37개 검사가 의도한 동작 미구현으로 실패했고, 구현 후 Development Editor 빌드와 focused 37개·전체 204개 Automation이 성공했다. 모든 검사의 발견·시작·종료·보고서가 일치했고 전체 검사의 기존 경고 23건을 보존했다. 순수 adapter의 독립 명세·품질 검토를 마쳤다. 명세 검토의 Unreal 외부 보조 검사 44개와 품질 검토의 보조 검사 242개는 실제 엔진 실행 수에 합산하지 않는다. 이후 Task 2B Host 관측 연결과 2026-10-25 Host 9·Observation 37 실행이 추가됐다. S01의 제한된 승인만 현재 반영하며 `whole_task2b_closed=false`다. H10·실제 수집 Capture 저장·복원과 사람 플레이 확인은 후속이다. 그 뒤의 Task 2C copy Host 25·Observation 37·broad 229는 상단의 이름이 고정된 last runtime checkpoint로 구분한다. 새 문서 assertion과 최종 source bytes의 재검증은 부모 담당이며 이 문서 작업자는 실행하지 않았다.

Runtime import 구조 단계는 오류 처리 보완 뒤 전용 198개 검사와 저장소 전체 533개 검사·170 subtests를 통과했다. 앞선 독립 명세 검토는 당시 전용 189개와 추가 91개 검사를 실행했다. 품질 검토에서 매우 큰 정수를 이미 해석한 객체로 전달하면 전용 검증 예외 대신 일반 예외가 나오는 문제를 재현했다. 새 회귀·대조 검사 9개 중 실제 실패 2개를 확인한 뒤 같은 9개를 통과시켰고, 기존 품질 보조 검사 133개도 다시 통과했다. 잘못된 자료의 수락이나 권한 상승은 관찰되지 않았다. 이 수량은 위 Unreal 검사와 별도다. 아홉 artifact 형식의 성공 응답은 항상 `structure_only`이며 원본·label·학습·Production 권한은 모두 false다. 이 검사는 합성 선언의 구조 검증으로, 실제 발행·승인 권한 또는 학습 Capture 확보의 증거가 아니다. 오류 처리 수정의 독립 재검토를 통과해 구조 단계는 완료했다. 실제 authority/ML 구현은 남아 있다.
