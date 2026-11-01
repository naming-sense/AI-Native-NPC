# 별도 Development Game 수집 연결과 read-only 실행 계획

> **문서 성격:** 기존 로컬 보충 설계의 공개 보관본이다. 아래 본문은 작성 당시의 계획과 미완료 상태를 보존한다.
>
> **현재 작업 방식:** [일반 플레이 구현계획 §0](scenario-collection-play-session-index-v1-implementation-plan.md#0-현재-작업-방식--문서-태스크-단위-구현-전용)을 따른다. AI는 태스크 단위로 코드를 작성한다. 검토·검증·빌드·실행 확인은 사용자 담당이다. 아래의 과거 RED/GREEN·부모 실행 절차는 현재 실행 지시가 아니다.
>
> **관련 계약:** [Runtime 수집 자료의 ML 가져오기 V1 계약](runtime-capture-import-v1-contract.md). 본문에 나오는 로컬 경로와 인계 파일은 당시 기록의 위치이며 GitHub 공개 위치를 뜻하지 않는다.

## 1. 선택·작성 범위·증거 강도

최종 수집 통합 대상은 기존 `NeuralGame`의 Win64/x64/Development/Game이다. 사용자는 설치 엔진을 유지하고 필요한 build·cook을 포함하는 별도 게임 창을 선택했다. 부모 결정 기록은 `development-game-path-decision-01.md`, 활성 기준은 `D/docs/current/scenario-collection-play-session-index-v1-implementation-plan.md` §12.4다.

- `D=/home/namingsense/AI-Native-NPC`
- `P=/mnt/d/Codex-cli/NeuralProject/NeuralGame`
- `S=/home/namingsense/AI-Native-NPC-evidence/collection-publication-c92d7rmc/play-session-index-implementation-01`
- `E=/mnt/c/Program Files/Epic Games/UE_5.7/Engine`

이 slice는 문서·검사·`return None` seam만 작성한다. `actual_execution=false`다. 실제 Python RED, planner GREEN, Windows/Unreal, build/cook/run은 부모 소유다. 독립 검토는 생략한다. Shipping/Release/commit/push는 범위 밖이다. Engine·Target.cs·Build.cs·plugin·Content·Config 및 기존 L1/L2a/문서 tests·normative Schema/validator는 편집하지 않는다. 다른 writer의 GoalHost.h/.cpp·play_session_native_io.py는 동결됐다고 주장하지 않는다.

### 기존 설계 중 바뀌는 부분

`runtime-inputs-launcher-design-01.md`는 당시 Development Editor + PIE 구상으로 보존한다. 이번 선택으로 그 문서의 실행 target, 두 project DLL/.modules 계획, Editor 초기화 뒤 GI claim 가정, Editor 전용 dependency helper의 실행 위치, 사람 Editor launch의 미결정만 이 문서가 supersede한다. `UnrealEditor.exe -game`은 선택된 Game executable과 다르다. 새 Game Target.cs도 만들지 않는다.

기존 Console 3개와 closed options/defaults/limits, owner-private issuer, PS13–PS14 stop/drain, native nonreplace publication, frozen ledger index, fresh World identity 및 승인 경계는 유지한다. 자동 입력은 `automated_runtime/automatic/automated`다. `human_play/manual/human`은 실제 사용자 입력·피드백이 있어야 확인한다. Editor/Host Automation과 과거 PIE는 lower regression이다. Game 증거로 승격하지 않는다.

## 2. 직접 읽은 현재 입력과 지원 범위

다음은 파일 열람 사실이다. 원본 bytes hash·snapshot 안정성·새 기능 build 성공을 확인했다는 뜻은 아니다.

| project-relative 입력 | 읽은 형태 | planner 역할 |
|---|---|---|
| `Binaries/Win64/NeuralGame.target` | TargetName=NeuralGame, Platform=Win64, Configuration=Development, Architecture=x64, TargetType=Game, TargetBuildEnvironment=Shared, BuildSettingsVersion=V6, IsTestTarget=false | actual stored receipt. stale여도 계획 입력이며 실행 freshness는 별도 증명 |
| `NeuralGame.uproject` | EngineAssociation=5.7, 단일 NeuralGame Runtime/Default module | 논리 project module 예상 집합 |
| `Source/NeuralGame.Target.cs` | Type Game, V6, Unreal5_7 include order, ExtraModuleNames NeuralGame. 별도 LinkType override 없음 | 현재 전체 source 형태만 지원 |
| `Source/NeuralGame/NeuralGame.Build.cs` | 현재 전체 dependency/include 목록, UnrealEd 등은 Target.bBuildEditor 조건 | 닫힌 source 형태와 Game/Editor 구분 |
| `Plugins/GameDevMCPPlugin/GameDevMCPPlugin.uplugin` | UnrealMCPEditor, Editor, Default, CanContainContent=false | Game에서 제외되는 module과 제외 근거 pin |

`Plugins`의 `.uplugin` 검색에서 위 descriptor만 반환됐다. 부모는 snapshot 앞뒤에 전체 project-local `.uplugin` membership을 다시 열거한다. `.uproject` Plugins 배열에 GameDevMCPPlugin이 없다는 이유로 생략하지 않는다. actual Game receipt의 BuildPlugins에 GameDevMCPPlugin이 있고 RuntimeDependencies에도 이 descriptor가 UFS로 기록돼 있다. **plugin descriptor가 receipt에 포함되는 것과 Editor module이 Game에서 compile/load되는 것은 별개다.**

현재 receipt의 Project는 정확히 `../../NeuralGame.uproject`다. 이것은 고정 receipt 위치 `Binaries/Win64/NeuralGame.target`에 대한 UBT의 알려진 reference literal로만 허용한다. 일반 artifact path resolver로 전달하거나 임의 `..`를 정규화하지 않는다. 그 외 입력·Launch·BuildProducts·RuntimeDependencies의 traversal은 거부한다.

### 현재 BuildProducts의 닫힌 지원 목록

각 Path는 아래 상대 경로 앞에 정확히 `$(ProjectDir)/`가 붙는다. 배열 순서는 계획 출력에서 UTF-8 path 순으로 정렬한다.

| relative_path | kind | 의미 |
|---|---|---|
| `Binaries/Win64/D3D12/x64/D3D12Core.dll` | DynamicLibrary | receipt의 배포 dependency, project logical module 아님 |
| `Binaries/Win64/D3D12/x64/d3d12SDKLayers.dll` | DynamicLibrary | 같은 구분 |
| `Binaries/Win64/DML/x64/DirectML.dll` | DynamicLibrary | 같은 구분 |
| `Binaries/Win64/NeuralGame.exe` | Executable | 유일 Launch image와 NeuralGame의 monolithic image |
| `Binaries/Win64/NeuralGame.pdb` | SymbolFile | debug symbol, 로드 module 아님 |
| `Binaries/Win64/tbb12.dll` | DynamicLibrary | receipt의 배포 dependency, project logical module 아님 |
| `Binaries/Win64/tbbmalloc.dll` | DynamicLibrary | 같은 구분 |

Launch는 정확히 `$(ProjectDir)/Binaries/Win64/NeuralGame.exe`이고 동일 Path·Type=Executable product가 정확히 하나 있어야 한다. 다른 executable·추가 project/plugin DLL·RequiredResource `.modules`·static/import library는 이 MVP에서 지원하지 않는다. 이 목록은 삭제 권한이 아니다. 특히 D3D/DML/TBB 파일을 project code artifact로 간주해 무조건 삭제하지 않는다.

## 3. 새 immutable API와 값 계약 — 본문 구현 전 확정

새 모듈은 `S/play_session_game_plan.py`다. 기존 `play_session_launcher.py`의 Editor planner 및 tests/oracle는 수정하거나 재사용하여 의미를 바꾸지 않는다.

```python
def derive_development_game_plan(
    *, receipt_image: GameInputImage, project_image: GameInputImage,
    plugin_images: tuple[GameInputImage, ...], target_image: GameInputImage,
    module_rules_image: GameInputImage,
) -> DevelopmentGamePlan | None:
    return None
```

이 함수는 supplied owned bytes만 읽는 순수 planner다. filesystem을 열거나 build/cook/delete/launch를 수행하지 않는다. valid shape이면 immutable plan을, malformed·unsupported면 `None`을 반환하는 것이 GREEN 목표다. 현재는 모든 호출에서 `None`이다. 무단 예외·부분 plan·부족한 descriptor 자동 보충은 성공으로 취급하지 않는다. 부모가 파일을 한 번 읽어 고정하고 독립 manifest로 결속하는 단계는 함수 밖이다.

모든 아래 값 타입은 `@dataclass(frozen=True)`다. 중첩 값은 tuple/string/int/bytes 및 frozen dataclass만 사용한다.

| 타입 | exact fields | 의미 |
|---|---|---|
| `GameInputImage` | relative_path: str, content: bytes | 읽은 원문과 project-relative 식별자. dict/bytearray 입력 거부 |
| `GameInputDigest` | relative_path: str, size_bytes: int, sha256: str | supplied 동일 bytes의 pin. 원본 파일 provenance 권한은 없음 |
| `GameBuildProduct` | receipt_path: str, relative_path: str, kind: str | actual receipt product, 삭제/실행 명령 아님 |
| `GameModuleImage` | module_name: str, image_path: str, artifact_kind: str | 논리 module과 실제 executable image의 계획 관계 |
| `GameExcludedModule` | module_name: str, descriptor_path: str, reason: str | descriptor에서 미리 결정한 제외 사유 |
| `DevelopmentGamePlan` | target, platform, architecture, configuration, target_type, build_id, link_basis, launch_path, modules, products, excluded_modules, input_inventory | 아래 고정 값과 owned nested tuple |

계획 값은 target=NeuralGame, platform=Win64, architecture=x64, configuration=Development, target_type=Game다. `build_id`는 실제 receipt.Version.BuildId다. `link_basis="closed_source_default_monolithic_pending_build_actions"`이며 source-level 추론과 실제 compile/link 증명을 구분한다. `launch_path="Binaries/Win64/NeuralGame.exe"`, modules는 `GameModuleImage("NeuralGame", launch_path, "Executable")` 하나다. excluded_modules는 `GameExcludedModule("UnrealMCPEditor", "Plugins/GameDevMCPPlugin/GameDevMCPPlugin.uplugin", "editor_module_ineligible_for_game_compile_and_runtime")` 하나다. products는 §2 exact 집합이다. input_inventory는 receipt를 포함한 모든 입력 images를 relative_path UTF-8 순으로 정렬하여 동일 bytes에서 만든 size/hash다. 이것은 build의 source_inventory를 대신하지 않는다.

### 3.1 지원되는 닫힌 source 형태

임의 C#를 실행하거나 `Type = TargetType.Game` 부분문자열만 보고 monolithic이라고 판정하지 않는다. 이번 parser는 직접 읽은 Target.cs와 Build.cs **전체 텍스트**가 고정된 reviewed literal과 일치하는 형태만 지원한다. 허용 표기 차이는 CRLF→LF와 마지막 LF 한 개의 유무뿐이다. UTF-8/BOM 없음·고립 CR 없음이며 공백·주석·statement 순서까지 그 외 모든 문자는 일치해야 한다. 전체 literal은 신규 test의 `TARGET_SOURCE_TEXT`와 `MODULE_RULES_TEXT`에 원문대로 적었다. GREEN 구현은 검토된 전체 literal을 자체 support table로 고정하며 test를 runtime에서 import하거나 caller가 준 expected source와 자기비교하지 않는다.

추가 partial class, preprocessor/함수 호출/정적 initializer, LinkType·ExtraModuleNames·BuildEnvironment·definitions 변경은 전부 unsupported다. 공백만 바뀌어도 이 닫힌 범위 밖이면 실패하므로 범용 C# 분석기라고 표시하지 않는다. 이후 지원 확대가 필요하면 문서·정상/실패 controls를 먼저 갱신한다. 현재 `E/Source/Programs/UnrealBuildTool/Configuration/TargetRules.cs:2527–2530`의 기본 LinkType은 Editor만 modular이고 나머지는 monolithic이다. 실제 build의 override/XML/argv/environment·action/rsp·link output은 후속 producer가 다시 검사한다.

uproject와 알려진 local plugin descriptor도 현재 읽은 전체 parsed object를 지원하는 닫힌 형태로 제한한다. 의미 필드의 삭제·추가·coercion·unsupported allow/deny policy는 거부한다. 두 JSON은 재직렬화 모양이 아니라 strict parsed type/value/field set을 비교한다. 테스트의 `PROJECT_OBJECT`, `PLUGIN_OBJECT`가 현재 지원 object 전체를 명시한다. 다른 local descriptor 또는 Runtime module을 단순히 제외 집합에 넣어 성공시키지 않는다.

### 3.2 receipt 검증 범위

receipt top-level은 현재 actual fields인 TargetName/Platform/Configuration/BuildSettingsVersion/TargetBuildEnvironment/TargetType/IsTestTarget/Architecture/Project/Launch/Version/BuildProducts/RuntimeDependencies/BuildPlugins/AdditionalProperties만 지원한다. identity 값은 §2와 exact type까지 맞아야 한다. Version은 현재 필드 집합과 finite exact integer/string 값을 검증한다. BuildId는 nonempty string이다. fresh build의 changelist/version이 다르면 설치 engine provenance와 별도 재확인이 필요하다.

모든 JSON은 UTF-8 단일 object, 중복 decoded key·NaN/Infinity/exponent overflow·BOM·trailing junk·잘못된 exact type를 거부한다. malformed를 정상값으로 수선하지 않는다. RuntimeDependencies row는 현재 `{Path,Type}`이며 Type은 UFS/NonUFS/DebugNonUFS다. EngineDir 경로는 token 뒤 lexical 검사를 수행하고 설치 엔진 trust 영역으로 분리한다. ProjectDir 경로는 §2의 배포 DLL NonUFS와 uproject/plugin descriptor UFS에 정확히 대응해야 한다. plugin descriptor의 receipt 누락·추가·Type 불일치는 거부한다.

BuildPlugins는 unique/case-unambiguous nonempty plugin-name string 배열이다. 알려진 local plugin 이름과 receipt local descriptor 및 supplied descriptor membership은 exact join한다. 나머지 engine plugin 이름은 설치 엔진 영역으로 기록한다. planner가 engine 전체 dependency completeness를 증명하지 않는다. AdditionalProperties는 현재 SDK/Not Applicable pair만 지원한다.

입력 relative_path·receipt product/dependency token은 검증 후 해석한다. absolute/drive/UNC/device/다른 token/backslash/empty segment/dot/parent/control/ADS/wildcard/trailing dot-space/Windows reserved name을 거부한다. 각 inventory와 각 receipt 배열의 duplicate/case alias도 거부한다. 동일 DLL이 BuildProducts와 RuntimeDependencies 양쪽에 정상적인 역할로 한 번씩 나타나는 것은 현재 actual shape이며 허용한다. 이것을 같은 배열의 중복으로 혼동하지 않는다.

## 4. Schema를 바꾸지 않는 monolithic 증거 표현

`D/contracts/current/capture_import_provenance_v1.schema.json`의 `$defs.module_descriptor`는 exact `{module_name,base,path,size_bytes,sha256}`, base=project_root, path=relative_path다. `.dll` suffix 제한은 없다. runtime_build_evidence.module_artifacts와 session_start_evidence.loaded_module_inventory는 비어 있으면 안 된다. `D/tools/validate_capture_import_provenance.py::_modules`는 `_inventory`의 unique `(base,path)`와 unique module_name을 요구한다. 같은 EXE를 두 이름으로 늘린 행은 허용하지 않는다.

따라서 **현재 단일 논리 project module 범위**에서 다음 표현이 구조적으로 가능하다. 실제 producer가 EXE를 native-held single read한 뒤에만 size/hash를 채운다. 계획 단계에서 fabricated artifact descriptor를 만들지 않는다.

- module_name: `NeuralGame` — uproject/Target/Build가 정한 논리 이름.
- base: `project_root`.
- path: `Binaries/Win64/NeuralGame.exe` — 실제 Launch Executable product와 OS image.
- size_bytes/sha256: 같은 held EXE file bytes에서 계산. OS mapped image size와 file byte size를 구분한다.

post-build `module_artifacts`와 start `loaded_module_inventory`에 이 행을 각각 한 번 기록한다. start.executable의 기존 installed descriptor는 실제 process EXE absolute path/version/size/hash를 별도로 기록한다. `engine_toolchain_identity.engine_executable`은 실제 cook/probe에 사용한 설치 engine executable이며 Game EXE로 엔진을 위장하지 않는다. 이 필드의 구체 선택은 producer가 실제 invocation과 결속한다. arch/type/link/action/plugin exclusion/cook/stage 관측은 기존 build_log/loader_log의 봉인된 내용에 보관하고 closed Schema에 새 필드를 추가하지 않는다.

이는 구조 표현 판단이다. validator는 descriptor target을 열지 않으며 build·loader 사실을 인증하지 않는다. 추가 runtime project/plugin module이 같은 EXE에 결합되면 여러 논리 module을 한 path로 표현해야 하는 문제가 생긴다. 현재 MVP는 해당 구성을 명시적으로 거절한다. 실제 loaded 목록을 보고 expected set을 줄이는 fallback은 없다. engine/system/third-party 전체 loaded 목록은 loader_log에 남기며 project module 행으로 오분류하지 않는다.

## 5. 부모 actual RED용 하네스

신규 `test_play_session_game_plan.py`의 단일 검사명은 `test_actual_game_plan_then_mutations`다. 부모가 frozen actual input snapshot과 독립 manifest pin을 제공해야 한다. 없는 snapshot을 합성하거나 기존 Editor fixture로 대체하지 않는다.

1. snapshot 환경·manifest/파일 membership·size/hash·actual receipt identity/product/descriptor/source control을 통과한다. marker는 `G1_PREREQUISITE actual Game input snapshot controls passed`다.
2. actual bytes를 `derive_development_game_plan`에 넣는다.
3. 첫 behavioral assertion은 정확히 `assert plan is not None, "G1: actual Development Game receipt must produce a read-only game plan"`다.
4. 현재 seam에서는 3에서 끝나야 한다. missing env/file/import/parse 오류·snapshot mismatch는 실제 RED로 세지 않는다.
5. GREEN 이후 exact plan projection·nested immutable 값·동일 입력 반복 결과를 확인한다. 모든 mutation 전에 actual positive control을 반복한다. 모두 거절하는 parser는 이 control을 통과할 수 없다.

후반 mutation은 actual frozen bytes의 메모리 사본만 바꾼다. wrong target/type/config/platform/architecture, missing/duplicate/wrong Launch Executable, traversal/absolute/token/case alias/duplicate keys/nonfinite, unexpected runtime project/plugin module, descriptor eligibility와 receipt product 불일치, unsupported Target/Build shape/artifact 종류를 검사한다. positive sample을 actual build 성공 receipt라고 부르지 않는다. 이 문서 작성 시 후반 cases는 전부 미도달이다.

추가 `test_collection_game_launch_document.py`는 새 실행 대상 보정·Schema 표현의 문서 coverage다. 초기 PASS는 behavioral RED가 아니다. 기존 문서 하네스 literal와 PS marker/table을 유지하고 새 DG clauses만 별도로 검사한다.

## 6. 후속 구현·실행 순서

### G2. 강제 Game project compile/link

writer 종료와 actual RED 확인 뒤 planner GREEN을 최소 구현한다. 이후 별도 부모 producer가 exact source/descriptor/engine source와 실제 도구를 pin한다. source before/after는 membership까지 같아야 한다. logical runtime project module은 NeuralGame 하나다. Game에서 제외되는 GameDevMCP descriptor와 그 제외 근거를 inventory/log에 남긴다. plugin Source/Config/Resources는 보수적 source closure·원본 보존 대상에 유지할 수 있으며 Game compile 대상이라고 주장하지 않는다.

Editor `.modules`/DLL 삭제 계획을 Game에 복사하지 않는다. forced rebuild의 exact project intermediate/output 목록·backup/readback·범위는 새 Game action graph/receipt에서 정한다. engine 설치물과 third-party dependency를 광범위 clean하지 않는다. 원본 보호 자료의 자동 삭제/덮어쓰기/rollback은 없다. 실제 Game build argv의 target은 NeuralGame이며 -Module 선택·export-only·incremental-only는 전체 coverage 성공이 아니다.

실제 local compile action 및 UHT-generated TU, PCH, link response/object 목록을 expected graph와 join한다. `UE_GAME`, `IS_MONOLITHIC`, `WITH_HOT_RELOAD`, `WITH_LIVE_CODING`의 실제 정의와 link의 NeuralGame.exe를 보관한다. flags·환경/XML이 닫힌 source의 의미를 바꾸지 않는지도 확인한다. project source closure의 compile/link가 불명확하면 `compile_action_coverage_unproven`으로 닫는다. fresh receipt와 EXE actual bytes는 이 실행 뒤에만 build evidence에 넣는다.

### G3. 선택 MVP dependency cook/staging과 원본 보존

선택 map은 `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`다. engine-supported Editor/cook 도구는 **부모 준비 단계**에서 dependency graph를 얻고 cook할 수 있다. Game runtime에서 Editor AssetRegistry helper/MCP를 쓸 수 있다고 가정하지 않는다. hard/soft/management/external actor-object/sidecar 및 실제 runtime soft loads의 closure를 기록한다. full Content 보수적 inventory는 실제 graph 조사를 대체하지 않는다.

original Source/Config/Content 및 보호 Saved의 전체 membership·bytes를 전후 보존한다. cook/staging/DDC/log/runtime Saved는 exclusive task root로 격리한다. 프로젝트 물리 copy가 필요하면 원본과의 byte 대응 및 실행에서 쓰는 trusted project_root를 고정한다. root 이동에 따른 receipt·source·actual image 경로를 숨기지 않는다. 원본 Content/Config를 편집하거나 기존 Saved를 비우는 방식은 허용하지 않는다.

정확한 설치 UAT/cook 옵션, dependency 보고서 출력, stage layout, loose metadata와 cooked EXE의 동일 project_root, `FPaths::ProjectSavedDir()`의 실제 격리 위치는 아직 pending이다. 부모가 설치 source/지원 인수와 실제 probe로 확인한 뒤 명령을 고정한다. 존재하지 않는 cook/stage 성공 로그를 만들지 않는다. Development startup과 authored map/mesh/animation/nav/StateTree 로드 성공을 각각 기록한다.

### G4. 새 Game process와 bootstrap rendezvous

새 `NeuralGame.exe`를 직접 시작하고 retained process handle에서 PID·creation FILETIME·actual EXE 경로·file identity·loaded inventory를 관측한다. 이전 process attach·Editor 재사용·DLL 최신 timestamp 선택은 없다. source-derived expected module set과 OS 전체 image 목록을 join한다. native notifications와 retained files/currentness는 최초 baseline 전에 시작하고 queue overflow·transient module 변경·source membership 변경·EOF를 sticky 실패로 연결한다.

`E/Source/Runtime/Engine/Private/GameEngine.cpp`의 GameInstance InitializeStandalone은 OnPostEngineInit보다 이르다는 선행 source 조사를 적용한다. GI owner는 bootstrap 미준비 상태로 먼저 등록될 수 있다. 이후 bootstrap-ready와 **동일 exact owner**가 game thread에서 rendezvous한다. 반대 순서도 한 번만 claim한다. owner Deinitialize/다른 GI/추가 World/stale generation은 거부한다. 명시적 collection intent의 Host preparing fence를 최초 dispatch 전에 세우며 일반 수집 off 플레이는 유지한다. 모든 map에서 자동 Start하지 않는다.

### G5. native pipe와 owner session ID

원본 설계 §5의 restricted inherited anonymous pipe 두 개, 환경 handle 두 개, uint32-LE 길이 + canonical UTF-8 JSON, 16 MiB/depth32, 방향별 nonzero uint64 sequence, run_id/body exact fields를 유지한다. bootstrap/bootstrap_ready/session_reserved/session_start_ready/session_armed/health_checkpoint/invalidate/session_closed의 exact body는 원본 설계 §5.2가 규범이다. Game 변경을 핑계로 wire fields를 늘리지 않는다. Game의 dependency report는 준비 단계 pin과 actual loaded/cooked 확인에 결속한다. 새 RPC/socket/원격 bridge나 public path/hash authority 입력은 추가하지 않는다.

owner가 UUIDv4를 발급·session.json을 영구 nonreplace publish/readback한다. 그 descriptor를 받은 부모가 실제 process/source/module 현재성을 재확인하여 해당 ID의 start evidence를 발행한다. RuntimeInputs가 same-held bytes·독립 pins·owner generation을 검증한 뒤에만 immutable inputs와 runtime Context/Lease를 만든다. N1의 raw file/pipe IO 성공만으로 이 authority 순서가 완료됐다고 표시하지 않는다.

### G6. private 자동 adapter와 실제 수집

Game용 private automation adapter는 기존 실제 owner 본문과 engine player 입력 경로를 호출한다. public manual을 자동 성공 경로로 쓰지 않는다. source/controller/mode는 automated_runtime/automated/automatic으로 고정한다. Editor latent PIE API를 Game에서 호출하지 않는다. 새 adapter를 어느 허용 C++ TU/Automation context에 둘지와 Game target discovery 여부는 첫 실제 compile/test에서 확인할 pending이다. 필요한 source allowlist 변화가 있으면 부모가 명시하고 임의 확장하지 않는다.

정상 control은 Start → owner reservation/handshake/preparation → 실제 Host attach/입력·authored notify·sensing → NewEpisode 요청에 따른 이전 terminal 저장·drain·old cleanup → 다른 World/assembly와 verified reset readback → 새 회차 → Stop → frozen ledger terminal/index readback → fresh normal World 복귀 순서다. NewEpisode 내부 stop/drain은 필요하지만 공개 Stop으로 세션을 최종화한 뒤 같은 세션에 NewEpisode를 붙이지 않는다.

PS13/14의 reentrant stack·retry epoch·dispatch/timer/move/input/emitter drain을 실제 관측한다. empty-index 준비/취소 smoke와 실제 Capture/marker가 생성되는 movement/sensing smoke를 구분한다. 기존 validate_index를 신뢰 package pins 및 실파일 session/ordered episodes/index/Capture/marker의 같은 bytes로 실행한다. startup만으로 gameplay 성공을 주장하지 않는다. 실제 사용자 입력 검사는 별도이고 validated_row_count=0, production_eligible=false, Approved/ResolvePolicyReady false를 유지한다.

## 7. HotReload와 LiveCoding의 별도 현재성 조건

### HotReload

직접 읽은 `E/Source/Runtime/Core/Public/Misc/Build.h:149–163`의 default는 `!IS_MONOLITHIC && !UE_BUILD_SHIPPING && !UE_BUILD_TEST && !UE_GAME && !UE_SERVER`다. 이 소스상 Game/monolithic 제외를 실제 후속 build definitions/preprocess/link와 연결해야 한다. `#ifndef` 기본식 열람만으로 새 EXE의 compile 증명을 끝내지 않는다. `UnrealEditor.exe -game`은 기존 Editor binary의 compile definitions를 바꾸지 않는다. 기존 unattended/commandlet manual 거부도 보존한다.

### LiveCoding

직접 읽은 `TargetRules.cs:1471–1479`에서 bWithLiveCoding과 -NoLiveCoding은 RequiresUniqueBuildEnvironment다. Win64 x64 Development Game은 기본 enabled 조건에 포함된다. installed/shared engine에서 임의 override·bOverrideBuildEnvironment로 ABI 검사를 건너뛰거나 -NoLiveCoding을 즉시 유효한 해법이라고 쓰지 않는다.

직접 읽은 지원 API와 한계:

| 설치 source | 확인 | 구현 판단 |
|---|---|---|
| `Source/Developer/Windows/LiveCoding/Public/ILiveCodingModule.h:41–67` | EnableForSession(false), IsEnabledForSession, HasStarted, IsCompiling, GetOnPatchCompleteDelegate | session 상태 API는 존재. 영구 잠금/모든 상태변경 event는 아님 |
| `.../LiveCoding/LiveCoding.Build.cs:8,38–49` | UseLiveCoding2=false, x64에서 LC_VERSION=1 선택 | source상 현재 선택. 실제 build 정의·설치 binary 대응은 추가 증명 |
| `.../Private/LiveCodingModule.cpp:487–508` | -LiveCoding=false는 auto-start 억제 | startup 옵션을 이후 재활성화 불가능 증거로 쓰지 않음 |
| 같은 파일 `548–615,640–655` | disable은 Starting에서 아무 일도 하지 않음. Starting에서 query/HasStarted(false)도 false | false 두 개만으로 async-start 부재를 증명할 수 없음 |
| 같은 파일 `674–680,698–706,750–778` | disabled session에서도 console process는 남을 수 있음. Compile은 EnableForSession(true). Tick도 재활성 가능 | EnableByDefault/Config 변경·직접 Shutdown/Unload로 우회하지 않음 |
| `.../Private/LiveCodingModule2.cpp:206–212` | 다른 variant는 disable no-op/query true | 이름이 같다는 이유로 variant2 성공을 가정하지 않음 |

후속 구현 후보는 fresh Game launch의 auto-start 억제 + 지원 session disable/query + 초기 시작 경쟁 확인 + runtime/parent의 연속 health 관측이다. 준비/attach/NewEpisode/publication/final readback 경계와 GameThread tick에서 enabled/compiling/patch를 관측하면 sticky invalidate한다. GetOnPatchCompleteDelegate와 native loader notifications도 결속한다. 하지만 이 API만으로 tick 사이의 enable→disable 변화나 Starting 상태를 모두 관측하는 방법은 확인되지 않았다. notification과 polling만으로 그 공백을 성공으로 덮지 않는다.

**pending 성공 조건:** 현재 Build.cs를 바꾸지 않고 ILiveCodingModule을 include/link하는 지원 경로, 실제 linked LC_VERSION/WITH_LIVE_CODING, fresh startup race 부재, session 상태의 연속 현재성에 대한 충분한 관측 접점. 이 조건을 설치 source·실제 build/probe에서 닫기 전에는 `live_coding_state="disabled"` 성공 evidence를 발행하지 않는다. 이 한계는 Game planner의 read-only RED를 막지 않는다. engine 편집·ABI 우회·provenance gate 완화는 대안으로 채택하지 않는다.

## 8. 인계 시점

문서·하네스·None seam의 source 편집만 끝낸다. source_editing_complete=true, will_make_no_further_edits=true, actual_execution=false다. 실제 hashes, RED 결과, 후반 case count/성공, cook/build/process/gameplay 성공을 계산하거나 발명하지 않았다. 부모 snapshot 형식·명령·첫 실패와 남은 기술 조건은 `development-game-plan-red-handoff-01.md/.json`에 고정한다.
