# 로컬 작업 인계 — 2026-11-03

로컬 작업 인계는 사용자가 현재 파일을 이어서 개발할 수 있도록 변경과 남은 문제를 정리한 기록이다. **AI의 후속 수정은 중단했으며, 이번 작업은 변경 요약과 기존 Git 저장소의 커밋·push에 한정한다.**

## 1. 작업 전환과 맵 변경 정정

사용자는 NPC 초기 방향만 바꾸는 맵 수정의 승인을 요청받은 적이 없다고 밝혔다. 기존 구현계획과 보충 설계의 승인 단정을 철회했다. AI가 작성한 과거 요약이나 백업 설명은 사용자 승인 증거가 아니다.

보존된 변경 전후 기록에는 같은 NPC의 방향이 `Yaw 180`에서 `Yaw 0`으로 바뀐 사실이 있다. 두 기록의 위치는 `(5500, 0, 146)`이며 크기는 `(1, 1, 1)`이다. 이는 당시 관측한 변경의 설명이다. 현재 열린 Editor의 상태를 새로 조회한 결과는 아니다.

이번 인계에서는 NPC·맵을 추가 수정하거나 되돌리지 않았다. 원본 백업과 기존 수집 자료를 그대로 보존했다. 백업의 `backup-manifest.json`에 적힌 `approved` 표현도 승인 근거로 사용하지 않는다. 원본 기록 자체는 덮어쓰지 않았다.

직전의 시야 상실·선택 목록·검사 실패 수정 요청은 소스와 기록을 읽던 중 중단됐다. 그 수정 요청으로 제품 코드나 검사 기대값을 편집하지 않았다. 세 문제는 모두 미해결이다.

## 2. 이번 Git 게시 범위

게시 대상은 `AI-Native-NPC` 저장소의 현재 문서와 문서 검사 파일이다. 기존 게시 기준은 `3c155f9`다.

- README와 문서 작성 지침을 갱신했다.
- 일반 플레이 수집 구현계획에 세션 시작, 다음 회차, 중단, 최종 목록 저장과 빌드 재사용 흐름을 정리했다.
- 별도 Development Game 설계와 Runtime 가져오기 계약에 고정 빌드 재사용과 실제 실행 기록의 구분을 반영했다.
- 시나리오 수집·ML 계획에 선택 화면의 현재 상태와 남은 학습 입력 연결을 반영했다.
- 출처·결과 연결 구현계획과 관련 문서 검사 파일을 포함했다.
- 수집 화면의 실제 확인 결과와 이 인계 문서를 포함했다.
- NPC 맵 수정이 승인됐다는 문구를 정정했다.

**Unreal 프로젝트와 실행 도구는 이 Git 저장소 밖에 있다.** 원본 `NeuralGame` 폴더는 이번 확인에서 Git 저장소로 인식되지 않았다. C++ 소스, 맵, 실행기, 준비 빌드와 수집 원본은 이 커밋에 포함하지 않는다. 원래 위치에 보존하며 아래에 찾는 위치를 기록한다. 이 문서의 push를 게임 소스 전체의 Git 백업으로 해석하지 않는다.

## 3. 로컬에 작성된 기능

### 수집 화면

게임에서 시나리오, 거리, 방향과 seed를 고르는 화면을 작성했다. 기본값 복원, 직접 플레이 시작, 자동 시작, 다음 회차, 종료·저장, 저장 위치 복사와 닫기 경로를 연결했다. 실제 시작 가능 여부는 준비할 때 정한 입력 출처에 따라 달라진다.

`F8`로 화면을 열고 닫으며 `Esc`와 닫기 버튼도 제공한다. 화면을 닫을 때 이전 마우스 캡처·잠금·입력 무시 설정을 복원하도록 수정했다.

### 세션과 실행기

세션 관리자는 시작, 회차 전환, 정지와 최종 목록 저장을 소유한다. 화면형 자동 수집은 첫 시작과 회차 종료 뒤에 버튼 요청을 기다린다. 시작 전 실행기 연결 오류는 대기 상태로 숨기지 않는다.

실행기에 `--collection-ui`를 추가했다. `--reuse`는 준비 완료 기록을 읽고 같은 빌드를 새 세션에서 재사용한다. 이 옵션은 자동 입력을 사람 입력으로 바꾸지 않는다.

수집 자료는 판단 기록의 원본이다. 학습 데이터 승인이나 모델 학습 완료를 뜻하지 않는다.

## 4. 마지막 실행 결과

아래는 인계 이전에 수행한 결과다. 이번 커밋·push 작업에서는 빌드·테스트·게임 실행을 다시 수행하지 않았다.

- Editor·Development Game 빌드와 게임 자료 준비가 성공했다.
- 새 화면 빌드의 세 세션에서 네 회차를 실행했다. 정상 완료 두 회차, 시야 상실 시간 초과 한 회차, 요청 중단 한 회차다.
- 판단 기록 10개와 최종 목록을 저장했다. 이전 준비07의 기록 6개는 별도 자료로 보존했다.
- 실행기 관련 검사 11개가 통과했다.
- Unreal PlaySession 검사는 30개 중 29개가 통과했다. 하나가 실패했고 경고 이벤트는 5개였다.
- 과거 빌드 계획 검사 16개는 정상 입력의 예상값과 현재 계약이 달라 실패했다.

상세 근거와 미확인 범위는 [수집 화면 확인 기록](collection-ui-verification-2026-11-03.md)에 있다. 이번에 게시하는 문서 검사 파일의 현재 통과 여부는 새로 확인하지 않았다.

## 5. 사용자가 이어갈 작업

1. **시야 상실:** 발소리와 등장은 관측했지만 마지막 시야 상실 사건은 관측하지 못했다. 회차는 `timed_out / event_timeout`으로 끝났다. 자동 이동과 실제 시야 사건 전달의 연결을 확인해야 한다. 원인은 아직 확정하지 않았다. 제한 시간을 늘리는 방식의 수정은 하지 않았다.
2. **선택 목록 가독성:** 펼친 목록에서 선택되지 않은 글자가 어두운 배경과 겹친다. 목록 글자색과 항목 스타일의 대비 보완이 남아 있다.
3. **Unreal 검사:** 폴더 이름 변경 차단의 오류 코드 기대값 정리가 남아 있다. 별도 Windows 관측에서는 파일 접근이 오류 32, 폴더 이름 변경이 오류 5로 차단됐다. 기존 Unreal 검사는 폴더에도 오류 32를 기대한다. 그 관측만으로 제품 검사를 통과 처리하지 않았다.
4. **과거 계획 검사:** `link_basis`의 현재 값과 과거 fixture의 예상값이 다르다. 정상 입력을 현재 계약에 맞게 정리한 뒤 개별 실패 사례를 확인해야 한다. 현재 계약을 과거 예상값에 맞춰 완화하지 않았다.
5. **후속 기능:** 수집 자료의 학습 입력 연결, 정답 판정, 조건 확대와 모델 학습이 남아 있다. 사람 직접 플레이 수집과 전체 조건 조합의 성공도 확인하지 않았다.

기존의 `production collection closed`, `ResolvePolicyReady=false`, `production_eligible=false` 상태는 유지한다.

## 부록 A. 소스와 실행 도구 위치

### Unreal 원본 프로젝트

Windows 경로는 `D:\Codex-cli\NeuralProject\NeuralGame`이다. WSL 경로는 `/mnt/d/Codex-cli/NeuralProject/NeuralGame`이다.

화면과 수집 연결의 주요 파일은 프로젝트 기준으로 다음과 같다.

- `Source/NeuralGame/NeuralGamePlayerController.h/.cpp`: 화면 생성·닫기와 입력 복귀.
- `Source/NeuralGame/NeuralGame.Build.cs`: 화면과 클립보드 모듈 의존성.
- `Source/NeuralGame/AINativeNPC/Collection/AINativeNPCCollectionScreenState.h`: 화면에 표시하는 상태.
- 같은 Collection 폴더의 `AINativeNPCCollectionWidget.h/.cpp`: 선택 목록과 버튼 구현.
- 같은 Collection 폴더의 `AINativeNPCCollectionSessionSubsystem.h/.cpp`: 세션·회차 수명과 자동 시나리오 실행.
- 같은 Collection 폴더의 `AINativeNPCCollectionRuntimeInputs.h/.cpp`: 실행기 입력과 화면 대기 옵션.
- `Source/NeuralGame/AINativeNPC/Tests/AINativeNPCCollectionPlaySessionTests.cpp`: 실패한 Unreal 검사를 포함한 세션 검사.

시야 상실 조사에서는 세션 관리자의 `TickAutomatedGame`, 시야 감각의 `AINativeNPCSightSense`, 지식 관측의 `TypedTargetKnowledgeComponent`를 읽었다. 이 목록은 원인 확정이나 수정 완료를 뜻하지 않는다.

실패한 Unreal 검사 이름은 `AINativeNPC.Collection.Host.PlaySession.BootstrapMetadata.ActualReadImageAndRetirement`다.

### 저장소 밖 실행 도구

WSL 경로는 `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01`이다.

- `play_session_launcher.py`: 준비·재사용·화면 대기 진입.
- `play_session_game_plan.py`: 빌드 대상 계획.
- `play_session_native_io.py`: Windows 파일·프로세스 연결.
- `prepare_play_session_metadata.py`: 수집 입력 준비.
- `test_collection_ui_launcher.py`: 화면 실행기 검사.
- `test_play_session_game_plan_livecoding_include.py`, `test_play_session_game_plan_v2.py`: 과거 빌드 계획 검사.

## 부록 B. 빌드와 원본 자료 위치

- 새 화면 준비 빌드: `D:\Codex-cli\NeuralProject\collection-ui-prepared-20261103-01`.
- 준비 완료 기록: 위 폴더의 `evidence/prepared-game-ready.json`.
- 새 화면 수집 원본: 위 폴더의 `NeuralGame/Saved/AINativeNPC/Collections`.
- 빌드·검사·화면 기록: `D:\Codex-cli\NeuralProject\collection-ui-validation-20261103-01`.
- 이전 준비07과 수집 원본: `D:\Codex-cli\NeuralProject\collection-prepared-20261103-07`.

실행기 종료와 게임 창 종료는 별개다. 기존 실행기들은 수집 최종 저장 후 종료됐다. 현재 게임 프로세스의 실행 여부는 이 인계에서 새로 확인하지 않았다.

## 부록 C. NPC 방향 변경과 백업

변경 기록과 백업은 `/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/npc-facing-adjustment-20261103-01`에 있다.

- `guard-before-resolved.json`: 변경 전 방향 `Yaw 180`의 관측 기록.
- `guard-reloaded.json`: 저장·다시 로드한 뒤 방향 `Yaw 0`의 관측 기록.
- `backup-manifest.json`: 변경 전 백업 파일 목록. 설명의 승인 표현은 이 인계에서 철회한다.
- `backup/Content/AINativeNPC/Maps/L_AINativeNPC_MVP.umap`: 변경 전 맵 백업.
- `backup/Content/__ExternalActors__/AINativeNPC/Maps/L_AINativeNPC_MVP/B/VX/VODDYPZYOUPVBVURRYCCJS.uasset`: 해당 NPC의 변경 전 외부 Actor 파일.

원본 프로젝트에서 해당 Actor 파일의 상대 경로도 `Content/__ExternalActors__/AINativeNPC/Maps/L_AINativeNPC_MVP/B/VX/VODDYPZYOUPVBVURRYCCJS.uasset`다. 이번 인계는 백업 복원 작업을 포함하지 않는다.
