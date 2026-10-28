# 학습 데이터 생성·수집 계획

이 계획은 NPC의 판단 상황을 모으고, 적절한 행동을 판정해 학습 데이터로 만드는 순서를 정한다.

- 문서 버전: **v1.2.0**
- 개정일: **2026-10-28**
- 현재 상태: **데이터 생성·정답 기록과 저장 기반은 구현했다. 선택 화면과 자동 수집, 학습 데이터로의 연결은 남아 있다.**

<a id="plan-guide"></a>
## 1. 목표와 읽는 순서

목표는 사람이 모든 사례를 직접 플레이하지 않아도 다양한 판단 상황을 모을 수 있게 하는 것이다.
사람은 대표 사례의 행동을 확인하고, 정답이 불확실한 사례를 검토한다.

이 문서는 전체 작업의 상위 계획이다.
최근 저장·읽기와 NPC 실행 연결 작업은 이 계획에서 내려온 다음 세부 계획을 기준으로 진행했다.

```text
학습 데이터 생성·수집 계획 — 이 문서
  → 시나리오 실행·수집 계획 — 실제 게임에서 수집하는 도구
    → 안전 저장·읽기 계획 — 최근 완료한 저장 연결 작업
```

- **전체 흐름을 이해하려면:** [용어](#terms) → [현재 상태](#current-status) → [데이터 흐름](#data-flow)을 읽는다.
- **다음에 만들 기능을 보려면:** [시나리오 도구](#scenario-collection-plan)와 [다음 작업](#next-work)을 읽는다.
- **정확한 필드·공식·명령이 필요하면:** 뒤쪽 [개발자용 구현 참고](#implementation-reference)를 펼친다.
- **이전 검사 결과가 필요하면:** [개편 전 원문과 검증 이력](../history/ml-data-pipeline-v1-history-2026-10-28.md)을 읽는다.

<a id="terms"></a>
## 2. 먼저 알아둘 용어

이 문서는 게임에서 얻은 사실과 그 사실에 붙이는 행동 정답을 따로 다룬다.

| 독자용 명칭 | 뜻과 코드·Schema 명칭 |
|---|---|
| 상황 | NPC가 한 번 판단하는 시점의 상태 |
| 시나리오 | 초기 조건과 사건의 진행 순서를 정한 플레이 구성 |
| 변형 사례 | 같은 시나리오에서 거리·가림·사건 시점 등을 정한 실행 조건 |
| 실행 회차 | 한 시나리오를 시작하고 종료할 때까지의 한 번 실행 |
| 판단 입력 | 한 번의 판단에 사용한 정보를 고정한 기록 (`Decision Snapshot`, `Snapshot`) |
| 플레이 기록 | 실제 게임 실행에서 저장한 판단 기록 (`Capture`) |
| 행동 정답 | 그 상황에서 허용할 행동이나 행동 사이의 선호를 붙인 값 (`label`) |
| 학습 데이터 묶음 | 검증된 판단 입력과 행동 정답을 모은 자료 (`Dataset`) |
| 자동 생성기 | 설정된 조건으로 판단 입력을 만드는 도구 (`Procedural Generator`) |
| 자동 정답 판정 | 외부 AI의 여러 응답을 모아 행동 정답을 만드는 과정 (`Teacher Pipeline`) |
| 자동 정답 / 사람 정답 | 자동 판정한 정답은 `Silver`, 검증된 사람 판정은 `Human Gold`로 구분 |
| 실제 사용 승인 | 학습·실게임 적용에 필요한 범위와 품질을 승인하는 절차 (`production` 승인) |

예를 들어 한 회차에서 **벽 뒤 발소리 → 상대 등장 → 다시 가려짐**을 실행할 수 있다.
이때 **소리만 들림 → 상대 확인 → 대상 상실**이라는 여러 상황을 얻는다.
각 상황이 학습 데이터가 되려면 저장·정답 판정·검증을 통과해야 한다.

<a id="current-status"></a>
## 3. 완료된 일과 남은 일

저장 기반의 완료와 수집 도구 전체의 완료를 구분한다.

| 작업 | 현재 상태 | 확인된 범위 또는 남은 일 |
|---|---|---|
| 설정으로 판단 입력 생성 | 구현·검사 완료 | 같은 설정으로 같은 데이터를 만드는 경로 |
| 자동 정답 판정과 사람 정답 저장 | 후보 자료 생성·저장 확인 | 전체 품질 평가와 실제 사용 승인은 남음 |
| 관측값 변환·수집 형식 검사 | 구현·검토 완료 | 위치·거리 등 관측 정보 변환과 자료 구조 검사 |
| 저장·읽기와 NPC 실행 연결 | 해당 범위 구현·실행·독립 검토 완료 | 기존 파일 보존, 저장 후 재검증, 실패 처리. 세부 작업명은 Task 2D |
| 수집 출처·결과 발행 연결 | 후속 작업 | 어느 회차에서 누가 만든 자료인지 연결하고 발행 결과 확인 |
| 선택 화면·자동 실행·회차 초기화 | 구현 전 | 시나리오 선택, 반복 실행, 중단, 다음 회차 준비 |
| 실제 기록의 학습 데이터 가져오기 | 후속 작업 | 원본·정답 승인 확인과 학습 데이터 묶음 변환 |
| 모델 학습·실게임 적용 | 준비 조건 미충족 | 자료 다양성·품질·평가와 별도 승인 필요 |

Task 2D는 원본 Unreal 프로젝트의 빌드와 화면 없는 엔진 자동 실행을 거쳐 확인했다.
이 승인은 지정된 저장 연결 범위에 한정한다. 일반 플레이 수집 활성화는 남아 있다.
기존 기본 행동 흐름에는 자동 PIE 검사 기록이 있다. PIE는 에디터 안에서 게임을 실행하는 기능이다.
이번 저장 연결을 포함한 자연스러운 연속 실행, 장거리 이동 완료와 에디터 화면의 애니메이션 확인은 남아 있다.

<a id="data-flow"></a>
## 4. 데이터가 만들어지는 과정

데이터는 설정에서 생성하는 경로와 실제 플레이에서 수집하는 경로로 준비한다.

### 설정에서 만드는 경로 — 후보 데이터 생성까지 구현

1. **조건을 정한다.** 관계·거리·보이는 정도 등 허용된 값을 설정한다.
2. **판단 입력을 만든다.** 자동 생성기가 조건에 맞는 판단 입력을 만든다.
3. **정답을 붙인다.** 승인된 생성 규칙이나 자동 정답 판정을 사용한다. 불확실한 사례는 사람 검토로 보낸다.
4. **학습 데이터 묶음으로 저장한다.** 입력과 정답을 묶어 저장한 뒤, 다시 읽어 일치 여부를 검사한다.

현재 생성기는 설정값으로 판단 입력을 만든다. 게임 장면을 배치하고 플레이하는 기능은 후속 시나리오 도구가 맡는다.

### 실제 플레이에서 모으는 경로 — 저장 기반 구현, 전체 연결은 후속

1. **시나리오를 실행한다.** 사용자가 플레이하거나 자동 도구가 이동과 사건을 발생시킨다.
2. **NPC가 실제로 판단한다.** 감지한 정보를 바탕으로 행동을 선택하고 실행한다.
3. **판단과 출처를 저장한다.** 원본 플레이 기록과 실행 회차·조건·입력 주체를 함께 추적한다.
4. **자동 정답 판정 도구나 사람이 검토한다.** NPC가 실행한 행동과 학습에 사용할 정답을 구분한다.
5. **검증된 자료를 가져온다.** 원본과 정답 승인을 확인한 자료만 학습 데이터 묶음으로 변환한다.

대량 생성·수집은 자동화한다. 사람은 대표 사례와 불확실·불일치·실패 사례를 검토한다.
자료를 저장한 횟수와 학습에 쓸 수 있는 자료의 수는 따로 센다.

<a id="scenario-collection-plan"></a>
## 5. 학습용 시나리오 실행·수집 도구

이 도구는 같은 시나리오 정의로 직접 플레이·자동 수집·조건 재실행을 제공한다.
선택 화면과 자동 실행은 구현 전이다. 저장 기반의 현재 상태는 [§3](#current-status)을 따른다.

### 5.1 누가 무엇을 맡는가

| 담당 | 맡는 일 | 승인 범위 |
|---|---|---|
| AI 개발 에이전트 | 기존 행동 규칙에 맞는 시나리오·변형 규칙·검사를 만들고 도구 구현 | 새 게임 규칙·사람 정답의 승인은 사용자에게 요청 |
| 사용자 / 게임·데이터 책임자 (`Gameplay/Data owner`) | 원하는 행동·대표 사례·허용 분포와 정답 검토 기준 확정 | 시나리오 승인과 개별 정답·실제 사용 승인을 각각 결정 |
| 생성·실행 도구 | 승인된 조건으로 장면 준비·실행·수집·초기화 반복 | 미지원 조합은 실행에서 제외하고 이유 기록 |
| 자동 정답 판정 도구 / 사람 검토자 | 같은 판단 입력의 적절한 행동과 선호 판정 | 자동 정답과 검증된 사람 정답의 출처를 각각 기록 |

사람의 한두 번 플레이는 대표 사례의 화면·행동·저장 확인에 사용한다.
수집 완료는 [다양성과 품질 기준](#collection-coverage)으로 판단한다.

### 5.2 어떤 조건을 바꾸는가

시나리오는 다음 정보를 가진다.

- 이름·버전과 비슷한 시나리오를 묶는 분류(`scenario family`).
- 초기 배치와 허용된 변형 범위.
- 사건 순서와 종료 조건.
- 수집 대상 목표(`Goal`)와 그 진행 단계(`phase`).

변형 사례에서는 아래 조건을 구체적으로 정한다.

- **공간:** 시작 위치, 거리, 접근 방향, 벽·가림, 이동 경로.
- **게임 상태:** 지원되는 초기 관계·성격과 신원 확인에 영향을 주는 관측 조건.
- **사건:** 발소리, 접근, 등장, 가려짐, 대상 상실·회복의 순서와 시점.
- **재현 정보:** 시나리오·생성기 버전, 맵·배치, 조건 선택값인 seed, 실제 선택 조건, 실행 모드·코드·계약 버전.

초기 설계에는 우호·중립·적대 관계, 낮은 신원 확신, 가림, 경로 불가를 사용한다.
벽 뒤 소리 후 등장, 접근 중 대상 상실 같은 시간 순서 사례도 포함한다.
실제 게임 연결이 확인된 조건만 실행 대상으로 연다. 미지원 조건은 빠진 연결과 제외 이유를 표시한다.

### 5.3 화면에서 무엇을 하는가

목표 화면은 다음 기능을 제공한다. 아래 목록은 구현할 기능이다.

- **시나리오 선택:** 설명, 초기 조건, 변형 범위와 지원 상태 확인.
- **직접 플레이:** 선택한 장면을 준비하고 사용자 입력으로 실행.
- **자동 수집:** 승인된 조건·seed 목록으로 이동과 사건 반복 실행.
- **같은 조건 재실행:** 저장된 버전·조건·seed로 새 회차 시작.
- **중단·결과 확인:** 유효·실패·중복 수, 제외 이유와 저장 위치 확인.

회차는 **조건 검증 → 장면 준비 → 감지·이동 준비 확인 → 사건 실행 → 저장·검증 → 초기화** 순서로 진행한다.
최대 회차, 회차 시간 제한과 저장 용량 한도는 실행 전에 정한다.
준비 실패·시간 초과·사용자 중단은 각각 사유를 남긴다.

초기화는 이전 NPC·기억·목표·타이머·관계 변경·예약의 영향을 정리한다.
기존 유효 플레이 기록과 프로세스 전체의 증가 번호(`process-wide monotonic sequence`)는 보존한다.
초기화 실패 시 다음 회차를 시작하지 않는다. 병렬 실행은 상태·저장 경로 격리를 확인한 뒤 별도로 다룬다.

같은 seed는 같은 조건을 재구성하는 정보다. 사람 입력과 엔진 타이밍까지 같은 바이트(`byte-identical`)로 재현함을 보장하지 않는다.
실제 입력·사건 시점·판단 결과를 기록하고 비교해야 한다. 바이트 동일성 보장은 설정 기반 판단 입력 생성기에 적용한다.

### 5.4 무엇을 저장하고 정답으로 인정하는가

수집 출처와 라벨 출처를 별도로 추적한다.

- **수집 출처:** 사람 플레이, 자동 게임 실행, 설정 기반 생성, 검사 전용 입력을 구분한다.
- **라벨 출처:** 승인된 생성 규칙, 자동 정답, 사람 정답, 별도 요건을 충족한 개입 자료를 구분한다. 정확한 분류는 [구현 참고 C](#runtime-collection-contract)를 따른다.
- **원본 보존:** 자동·사람 판정은 같은 판단 입력에 별도 기록으로 연결한다. 원본 플레이 기록과 판정은 보존한다.
- **유효 기록:** `.anpccap2` 원본과 대응 `.committed` 실행 확정 표시가 있고, 저장 검사를 통과해야 한다.
- **유효 학습 항목:** 정책 범위·정답·학습 데이터 묶음 변환·사용 범위 검증까지 통과한 기록이다.

자동 실행을 사람 플레이 분포로 집계하지 않는다. 시나리오 승인과 정답 승인은 별개다.
현재 규칙 기반 선택기(`Utility`)의 선택은 출처와 사유를 가진 약한 참고 정답으로 보존한다.
학습에 사용하려면 자동 정답 판정 도구 또는 사람의 별도 판정과 학습 데이터 품질 검사가 필요하다.

성공한 인사와 함께 **인사하지 않음, 대상 상실, 판단 실패, 실행되지 않은 상태**도 관찰한다.
판단 입력이 없는 실패는 원인·단계만 진단 기록에 남긴다. 판단 입력이 있는 미실행 기록도 실행 확정 자료와 분리한다.
실패·미확정 기록은 실행 확정 기록으로 취급하지 않는다.
진단 기록은 현재 유효 플레이 기록 수와 학습 데이터 묶음에서 제외한다. 별도 학습 포맷·정답·변환·검증 계약이 필요하다.

실행 회차 수, 판단 상황 수, 저장된 플레이 기록 수와 유효 학습 항목 수를 각각 집계한다.
하네스는 규칙을 검사하는 자동검사 묶음이다.
추가 출처 필드와 보조 파일은 구현 전에 데이터 형식(Schema)·문서·하네스로 확정한다.
기존 출처 분류(`source_type`)는 임의로 확장하지 않는다.

<a id="collection-coverage"></a>
### 5.5 다양성과 평가 자료 분리

수집 완료는 조건별 범위, 고유 입력, 중복·근접 중복과 제외 이유로 판단한다.
같은 입력의 ID·seed만 바뀐 자료는 새로운 학습 상황으로 세지 않는다.
게임·데이터 책임자가 허용 조합·비율·수집 예산과 중단 기준을 승인한다.
승인한 값은 수집 설정(`Profile`)에 고정한다.

평가 자료는 모델이 학습에서 보지 않은 상황을 시험하는 데 쓴다.
자료를 용도별로 나누는 것을 분할이라 한다.
비슷한 시나리오 묶음(`scenario_family_id`)과 관련 장면·배치·사건 순서 묶음은 같은 분할에 둔다.
같은 묶음의 seed·거리 변형을 다음 용도에 나눠 넣지 않는다.

- 학습(`Train`)과 개발 중 검증(`Validation`).
- 신뢰도 보정(`Calibration`)과 일반 평가(`Test`).
- 학습 분포 밖 평가(`OOD`)와 치명적 오류 평가(`Critical`).

숨은 정보 유입, 분할 사이 완전히 같거나 거의 같은 입력과 출처 편향을 검사한다.
자동 실행·합성 자료는 사람 플레이와 분리해 조건·입력 특징·행동 후보 분포를 비교한다.
작은 사람 표본의 한계를 보고하고 기존 사람 정답의 최소 수량과 품질 기준을 유지한다.

<a id="next-work"></a>
## 6. 다음 작업과 완료 조건

다음 작업은 안전하게 저장한 판단 기록을 실제 수집 화면과 학습 입력까지 연결하는 것이다.

| 순서 | 작업 | 완료를 확인하는 결과 |
|---|---|---|
| 출처·결과 연결 | 회차·조건·입력 주체와 원본 기록을 연결 | 보조 기록을 다시 읽어 확인하고 실패 시 원본 보존·세션 중단 |
| 직접 플레이 | 단일 시나리오 장면 준비·실행·초기화와 화면 구현 | 대표 사례의 실제 사용자 입력·화면·행동·저장 확인 |
| 자동 수집 | 같은 정의로 반복 실행·시간 제한·중단·초기화 구현 | 실제 게임 경로 실행, 상태 누수와 파일 충돌 방지 |
| 학습 입력 연결 | 원본·정답 승인 확인 후 학습 데이터 묶음으로 가져오기 | 원본 입력 결속과 정답 출처를 재검증한 학습 항목 |
| 규모 확대 | 조건별 고유 입력·중복·제외 보고서 작성 | 승인된 조건 범위와 품질·평가 수량 충족 |

각 작업은 **문서·하네스 확정 → 실패 검사 → 최소 구현 → 실행·저장 확인 → 독립 검토** 순서로 진행한다.
검사에는 잘못된 조건, 미지원 조합, 상태 누수, 저장 충돌, 실패 기록의 부당 승격과 분할 누수를 포함한다.
도구 완료에는 실제 저장 파일의 재검증, 대표 사람 플레이와 독립 검토가 필요하다.

구현 순서와 파일 경계는 [시나리오 실행·수집 계획](scenario-collection-v1-implementation-plan.md)을 따른다.
최근 저장 작업의 기준은 [안전 저장·읽기 계획](scenario-collection-storage-v1-implementation-plan.md)이다.
기록을 학습 데이터로 가져오는 조건은 [Runtime Capture 가져오기 계약](runtime-capture-import-v1-contract.md)을 따른다.
현재 사용할 수 있는 구조 검사 명령은 [형식·검사 대응표](runtime-capture-import-v1-schema-map.md)에 정리돼 있다.

**수집 도구 완료와 모델 학습·배포 승인은 별도다.**
자료 생성·저장만으로 학습이나 배포를 승인하지 않는다. 정확한 승인 상태값은 아래 구현 참고에서 유지한다.

<a id="implementation-reference"></a>
## 개발자용 구현 참고

이 절은 코드와 검사에서 지켜야 하는 정확한 값을 보존한다. 전체 진행을 파악하려면 앞의 §1–§6으로 충분하다.

- 적용 계약: Schema `2.0.0-rc6`, Skill Registry `1.1.0`, Goal Registry `1.2.0`.
- 구현 루트: Unreal 프로젝트의 `NeuralGame/ML`.
- 기존 기술명: Procedural Generator와 Teacher Pipeline v1 구현 계획.
- 규칙의 우선순위: 기계 판독 계약 → [세부 기술 요구사항](technical-requirements.md)과 링크된 수집 계약 → 이 계획의 구현 절차.

<a id="pipeline-contract"></a>
<details>
<summary>A. 생성기·Teacher·Dataset의 입력과 저장 규칙</summary>

### A.1 전체 처리와 허용 범위

자동 생성기는 계약에 맞는 판단 입력을 만들고, Teacher는 모델에 보이는 정보로 정답을 판정한다.
Dataset Mapper는 입력과 정답을 `anpc_decision_record_v2` Parquet shard로 변환한다. shard는 여러 기록을 담은 파일 묶음이다.

예제 Profile과 smoke Dataset은 `integration_fixture`와 `production_candidate` 범위이며 production 학습·promotion authority가 아니다.
Profile은 생성·판정 조건을 고정한 설정이고, smoke는 작은 실행 확인이다.
이 Pipeline은 production `ResolvePolicyReady`를 변경하지 않는다.

### A.2 생성 설정

생성 설정(`procedural_profile_v1.yaml`)은 다음 값을 소유한다.

- `profile_version`, `scope`, `owner`.
- Schema·Skill·Goal source SHA-256.
- base seed와 scenario template 목록, group dimension.
- 행동 대상·사건·후보(`Target`·`Event`·`Candidate`) 구성.
- generated enum 이름을 사용하는 raw feature override.
- acceptable Candidate, preference와 parameter label.

Feature는 모델 입력 특징이다. override는 generated normalizer를 통과한다. Tensor index를 숫자로 직접 작성하지 않는다.

### A.3 판단 입력 파일

Snapshot shard는 UTF-8 JSON Lines와 manifest pair다. manifest는 파일의 크기·수량·내용 해시를 기록한다.
각 row는 한 번의 immutable Decision Snapshot이며 다음 값을 가진다.

- exact 10 Tensor canonical byte와 dtype·shape.
- `candidate_set_canonical_bytes`, `candidate_set_hash`.
- `switch_cost_terms`, `captured_switch_cost`.
- contract hash와 `input_content_hash`.
- episode·decision·group·provenance.
- procedural label block.

Binary field는 base64로 저장한다. JSON object는 key 오름차순·compact UTF-8로 기록한다.
Manifest는 shard byte 크기·row 수·SHA-256·profile hash·source/group 분모를 고정한다.

Snapshot Validator는 Candidate canonical bytes를 구조적으로 decode한다.
magic·version·Schema hash·17 Target Handle·Target mask·272 Candidate mask를 Tensor와 다시 비교한다.
Handle 정수 field는 bool·float coercion을 금지한다.
NoTarget·masked Target handle과 masked Tensor row는 canonical zero여야 한다.

### A.4 Teacher 입력과 합의

Teacher request는 Tensor에서 복원한 model-visible view만 포함한다.
허용 필드는 `global`, `targets`, `events`, `candidates`, `current_action`, contract·content hash다.
Runtime handle, Actor 이름, absolute world position, future event와 hidden Ground Truth는 제외한다.

Provider는 응답을 제공하는 연결 방식이며 Profile로 선택한다.

- `command`: request JSON을 stdin으로 전달하고 response JSON을 stdout으로 받는다.
- `replay_fixture`: 테스트용 고정 response를 읽는다. production scope에서 사용할 수 없다.

각 Snapshot은 정확히 5개 provider call provenance를 수집한다.
최소 3개 valid response, majority consensus, pairwise Jaccard와 `label_confidence`를 적용한다.
다음 경우는 training annotation에서 제외하고 사람 검토 대기열(`Gold review queue`)로 보낸다.

- valid response가 3개 미만.
- confidence 0.60 미만.
- hard conflict, preference cycle 또는 합의된 ambiguous.

Request Validator는 generated enum의 global·target·event·candidate feature 이름과 Skill·Target Kind·Event Type을 exact allowlist로 검사한다.
Dataset Mapper는 Teacher Profile을 다시 로드하고 Snapshot에서 request를 재생성한다.
raw provider payload 5개의 path·hash·response를 재검증한다.
consensus 결과가 annotation body와 byte-equivalent한 경우에만 mapping한다.

Teacher는 parameter label을 만들지 않는다.
Teacher mapper는 `parameter_target_norm=+0.0`, `parameter_label_mask=false`를 사용한다.

### A.5 Dataset 변환

Mapper는 Snapshot과 procedural 또는 Teacher annotation을 결합해 Zstandard Parquet를 작성한다.

- Tensor는 Arrow fixed-size list다.
- 10개 Tensor, mask와 Switch Cost를 다시 검증한다.
- `input_content_hash`, `label_block_hash`, `sample_id`를 다시 계산한다.
- `source_type`, `source_weight`, code/contract provenance를 기록한다.
- Snapshot·annotation join key는 `source_snapshot_shard_sha256 + episode_id + decision_id + input_content_hash`다.
- fixture source가 포함된 manifest는 `scope=integration_fixture`를 유지한다.
- `source_weight`는 `silver=0.25`, `gold=1.0`, `dagger=1.0`과 exact 일치해야 한다.

### A.6 검사 전용 Profile

Repository에는 작은 `integration_fixture` Profile과 별도 `production_candidate` Profile을 둔다.
검사 전용 Profile은 다음 범위를 고정한다.

- Goal `InvestigateDisturbance`, Phase `Resolve`, Role `Guard`.
- Target slot 0은 `Entity`, NoTarget slot 16은 항상 valid.
- valid Candidate는 `Greet(Entity)` index `170` 또는 target-loss case의 빈 mask.
- scenario family는 friendly-visible, hostile-visible, invalid-target.
- parameter label은 friendly-visible procedural row에서만 Greet active slot인 duration·intensity.

이 값은 Pipeline 검증 fixture다. production 범위·분포·비율·label 공식의 승인은 별도다.

### A.7 오류와 출력 처리

다음 구조 오류에서는 shard나 annotation을 publish하지 않는다.

- contract hash·version 불일치, unknown feature·enum·Profile field.
- non-finite·negative-zero·범위 밖 Tensor.
- invalid NoTarget slot 또는 Candidate layout.
- masked acceptable/preference index.
- request/response content hash 불일치.
- manifest에 없는 shard 또는 byte hash 불일치.
- production scope에서 `replay_fixture` 사용.

출력은 temporary file에 작성하고 validation을 통과한 뒤 atomic replace한다.
이 규칙은 offline 생성기 출력의 규칙이다. 실제 게임 수집 원본의 append-only 보존은 수집 저장 계약을 따른다.
valid Teacher response가 3개 미만인 개별 sample은 Gold review queue로 보낸다.

</details>

<a id="greet-and-qualification"></a>
<details>
<summary>B. 인사 후보·사람 정답·실제 사용 승인 기준</summary>

### B.1 인사 후보의 범위

첫 인사 후보는 current Test Taxonomy와 Case Catalog의 `GuardPhase0/InvestigateDisturbance/Resolve` 범위를 사용한다.
production action은 `Greet(Entity)`다. Profile 승인 전 산출물은 `production_candidate`로 표시한다.
이 scope는 값 범위·분포·parameter label 공식의 검토용이며 production 학습 authority가 아니다.
Generator와 Dataset validator는 이를 실행하되 `production_eligible=false`로 유지하고 `--require-production`에서 거부한다.

Runtime 검사의 최소 축은 다음 일곱 group이다.

- `greet_selected`
- `masked_or_nonfinite_output`
- `wrong_descriptor_or_artifact_identity`
- `neural_failure_or_deadline`
- `target_loss_recoverable`
- `target_loss_unrecoverable`
- `duplicate_or_stale_effect`

production scenario family와 학습 분포는 Gameplay/Data owner가 별도로 승인한다.
승인 항목은 아래와 같으며 새 Profile version으로 고정한다.

- friendly·neutral·hostile 관계 구간과 비율.
- Target visible·occluded·lost·invalid 구간과 비율.
- 거리, belief age·confidence, LOS와 path 상태 범위.
- Personality·Relationship 조합과 hold-out family.
- 현재 Skill 유지·Greet 전환의 Switch Cost 구성.
- `Greet` duration·intensity의 procedural/human label 공식.

Runtime 검사 group은 학습 분포를 대신하지 않는다.

### B.2 현재 실행하는 후보 규칙

사용자가 권장 기본값의 진행을 승인한 v1 후보는 다음 규칙을 사용한다.
이 규칙의 label은 heuristic Silver이며 Gold 또는 production authority가 아니다.

- Greet 허용: Entity Target과 Greet Candidate가 valid이고 아래 조건을 모두 만족한다.
  - `visible_now = 1`, `line_of_sight_belief ≥ 0.80`, `identity_confidence ≥ 0.80`.
  - `path_reachable_belief ≥ 0.50`, `hostility ≤ 0.35`.
- 그 밖의 anchor는 abstain으로 남긴다. Target·Candidate가 무효이면 Candidate mask를 비운다.
- duration = clamp(1.0, 5.0, 1.0 + 0.60 × affinity + 0.40 × sociability - 0.30 × hostility)
- intensity = clamp(0.0, 1.0, 0.20 + 0.35 × sociability + 0.30 × affinity + 0.15 × trust - 0.40 × hostility)

실행 가능한 `production_candidate` Profile은 7개 anchor를 고정한다.

1. friendly close visible
2. friendly far visible
3. neutral trusted visible
4. friendly low identity confidence
5. hostile visible
6. friendly recently occluded
7. friendly visible but path unreachable

이들은 Snapshot 생성기의 고정 사례다. 같은 사례의 생성 횟수만 늘려 다양성을 충족했다고 판단하지 않는다.
Target-invalid는 integration hostile fixture와 Runtime test case로 계속 검증한다.
Candidate Profile은 model-visible 관계·거리·인지·경로 경계 비교에 집중한다.
생성 Snapshot은 유효 Unreal Capture와 feature 구간·Candidate mask·abstain 비율을 비교한다.
이 비교 전에 합성 Dataset만으로 production 범위를 열지 않는다.

### B.3 Teacher 선정과 승인

Production Teacher Profile ID는 `teacher_silver_v1.0.0`이며 provider type은 `command`다.
`replay_fixture`는 integration 전용이다.

Provider 후보는 같은 고정 Gold Validation Dataset으로 비교한다.
Profile은 exact model identifier와 revision, prompt·Schema, decoding, prompt variant, consensus version과 reason-tag allowlist를 고정한다.
moving alias나 revision을 증명할 수 없는 연결은 smoke 후보로만 기록한다.

모든 승인 기준을 충족해야 한다.

- 12개 Role×Goal group마다 Gold sample 100개 이상.
- strict response valid rate ≥95%.
- Any-Acceptable Recall ≥95%.
- macro Role×Goal acceptable-set Jaccard ≥0.80.
- hard-invalid candidate 선택 0건.

한 기준이라도 실패하면 해당 Provider/Profile 조합을 차단한다.
복수 후보가 통과하면 worst Role×Goal 성능, 응답 형식 안정성, 처리 시간과 비용 순으로 선택한다.
Prompt, model revision, decoding 또는 consensus 변경 시 새 Profile version으로 전체 Gold Validation을 다시 실행한다.

재현용 unpinned Provider candidate Profile·prompt·Schema·command adapter는 `ML/teacher/candidates/production_resolve_v1_candidate/`에 보존한다.
기존 raw 응답 provenance와 같은 Profile hash를 유지한다.
해당 후보의 scope와 model revision은 Production 기준을 충족하지 않아 readiness audit에서 차단한다.
과거 연결 실행은 production Provider 승인 근거가 아니다.

### B.4 사람 정답 보존

사용자가 확정한 low identity confidence 사례의 정답은 **신원 확신이 낮으면 인사하지 않음**이다.

- `abstain=true`, acceptable set empty.
- parameter label mask all-false.
- `source_type=gold`, `source_weight=1.0`.

승격은 원본 review queue·Snapshot shard·Snapshot manifest의 exact hash와 `(episode_id, decision_id, input_content_hash)`를 묶는다.
원본 review queue와 Teacher 결과는 보존한다.
승인 record의 source queue 불일치·중복·누락·masked label·stale hash·비정규 YAML/JSON은 산출물 작성 전에 거부한다.
Gold 승격과 mapping은 decision·review queue·Snapshot·manifest의 각 파일을 한 번 읽는다.
같은 immutable byte image를 hash·parse·join에 사용한다.
Dataset validator도 한 번 읽은 Parquet bytes를 hash와 Arrow parsing에 함께 사용해 검증 중 path 교체를 허용하지 않는다.

Gold 1-row shard는 Snapshot의 `production_candidate` scope와 `production_eligible=false`를 상속한다.
Procedural·Teacher Silver·Human Gold candidate shard는 모두 `--require-production`에서 거부한다.

### B.5 준비 상태 검사

준비 상태 검사기(`ML/tools/audit_production_readiness.py`)는 아래 조건을 한 JSON으로 보고한다.

- Procedural, Teacher Silver, Human Gold manifest가 모두 validator를 통과한다.
- Teacher Provider Profile은 `scope=production`, exact model revision, 고정 prompt·Schema를 가진다.
- moving alias나 `integration_fixture` Profile은 차단한다.
- Provider 비교 전 Gold Validation Dataset은 12개 Role×Goal group마다 100개 이상, 총 1,200개 이상이다.
- Unreal Capture는 `.anpccap2`·동일 이름의 `.committed` marker가 있고 `tools/validate_anpc_capture_v2.py`를 통과한 파일만 센다.
- Calibration/OOD asset과 승인 모델 artifact는 파일 hash와 manifest가 모두 있어야 한다.
- 승인 artifact filename은 manifest directory 아래의 상대 경로만 허용한다.
- 같은 artifact bytes를 한 번 읽어 크기·hash를 검사한다. `..`, absolute path와 symlink escape를 거부한다.
- exact model revision은 `sha256:<64 lowercase hex>` 또는 64자리 digest만 허용한다.
- 날짜가 붙은 `main`, alias, latest와 unpinned 문자열은 승인하지 않는다.
- Gold 최소 분모와 Role×Goal coverage는 실제 Parquet에서 다시 계산한 denominator를 사용한다.

하나라도 실패하면 `production_ready=false`와 구체적인 blocker를 반환한다.
검사기는 `Approved`, `ResolvePolicyReady`, `production_eligible`을 바꾸지 않는다.
Train·Calibration·General Test·OOD·Critical 최소 분모도 채워야 한다.

</details>

<a id="runtime-collection-contract"></a>
<details>
<summary>C. 실제 게임 수집과 학습 가져오기의 경계</summary>

### C.1 실제 게임 경로

자동 모드는 실제 Pawn·Controller의 Perception → Knowledge → Goal → Candidate → Commit 경로를 사용한다.
각 단계는 감지 → 보관 정보 → 목표 → 행동 후보 → 최신 상태를 확인한 실행 승인이다.
도구가 제어하는 대상은 플레이어 이동·월드 사건과 적법한 초기 설정이다.
NPC 선택 결과와 정답은 강제하지 않는다.
Tensor나 Knowledge 결과를 직접 주입하는 검사는 fixture로 분리하고 실제 게임 실행 Capture로 집계하지 않는다.
숨은 월드 정답, 미래 사건과 시나리오 기대 결과는 모델·Teacher 입력에 넣지 않는다.

### C.2 인사 판단의 수집 전용 실행

첫 모델 전 실제 플레이 분포는 Editor 전용 `-AINativeNPCResolveCaptureOnly` 모드로 수집한다.

- `WITH_EDITOR`에서만 인식하며 Shipping에서는 활성화할 수 없다.
- `Approved=false`, `ResolvePolicyReady=false`, `production_eligible=false`를 유지한다.
- Resolve 진입의 exact authority·Target·Timer·Commit 검사는 Production과 동일하게 유지한다.
- Resolve 선택에서는 Neural evaluator를 반드시 `nullptr`로 두고 같은 Snapshot의 Utility 결과만 실행한다.
- label은 `Dagger` weak label이며 `resolve_capture_only_utility_selected` reason을 기록한다.
- 각 Editor process는 새 opaque session ID를 만든다. 모든 Host가 `Saved/AINativeNPC/Capture/ResolveShadow/<session-id>/`를 공유한다.
- 각 capture는 process-wide monotonic sequence를 받아 Episode ID와 filename에 함께 넣는다.
- Host별 `DecisionId`가 같거나 Pawn·PIE world가 다시 만들어져도 경로와 sample identity가 충돌하지 않는다.
- final·pending·marker 경로가 이미 존재하면 기존 committed Capture를 지우지 않고 새 capture를 fail-closed로 거부한다.
- `.anpccap2`는 Commit 성공 뒤 `.committed` marker와 exact readback이 모두 통과해야 유효하다.
- 사람 Play 비교에는 유효 Capture만 사용한다. Utility 선택 자체를 Gold 정답으로 승격하지 않는다.

Capture-only 활성화는 Production 승인이나 모델 준비로 계산하지 않는다.
약한 정답만으로 production 학습 대상에 넣지 않는다. Teacher 또는 사람의 별도 판정과 Dataset scope·품질 검사가 필요하다.
기존 raw Capture는 덮어쓰지 않는다. 유효 Resolve Capture를 확보한 뒤 실제/Procedural Resolve 분포를 비교한다.

### C.3 출처·정답 승인과 가져오기

[Runtime Capture 가져오기 계약](runtime-capture-import-v1-contract.md)은 검토 전 Runtime Snapshot에 `source_weight=0.0`과 학습 제외 상태를 부여한다.
원본 Utility 판정·출처를 보존하고, 인증된 Teacher/Human annotation을 거쳐 기존 Dataset weight 규칙을 적용한다.
Runtime build 출처를 Python generator 출처로 교체하거나 procedural mapper로 정답 검토를 우회하는 경로는 허용하지 않는다.
이 연결은 구현 전 계약이다. Dataset v2 필드·weight 규칙과 Production 승인 기준은 유지한다.

자료 구조·내부 일관성 검사와 실제 발행 주체·정답 승인 증명은 별도다.
Runtime 수집 자료는 제출 묶음 밖에서 고정한 최종 index와 별도 완료 closure로 session/episode·원본·시작 증거를 결속한다.
원본 증명만 있는 import는 검토 전 Snapshot까지 허용한다.
Dataset 최종 수락에는 독립적인 Teacher/Human 승인 증명이 추가로 필요하다.
qualification과 실제 학습 수락 조건도 별도로 유지한다. 증명 없는 source 수량은 승인된 학습량으로 집계하지 않는다.
Fixture provider는 통합 검사 전용이다.

출처 Schema·구조 검증기는 구현·독립 검토를 완료했다. Runtime/ML 연결과 실제 권한 증거는 남아 있다.
구조 검사 성공 응답은 원본·label·학습·Production 권한을 false로 유지한다.
기존 Human Gold 결정과 저장 결과는 소급 변경하지 않는다.

### C.4 수집량과 라벨 출처의 정확한 구분

수집량은 조건별 다양성과 검증된 유효 학습 row로 판단한다.
`Play 7회`는 학습량 기준이나 의무적인 수동 수집 횟수로 정하지 않는다.
생성기의 7개 고정 anchor와 Runtime Catalog의 일곱 검사 group도 수집량 기준과 분리한다.

라벨 출처는 승인된 procedural 규칙, Teacher Silver, Human Gold, 별도 요건을 충족한 DAgger 개입으로 구분한다.
현재 `Dagger` weak label은 기존 수집 출처와 reason을 보존한다.
Utility 선택을 정답으로 복사하지 않는다.
Teacher·사람은 동일한 판단 Snapshot에 별도 annotation을 연결한다.
실패·미확정 기록을 committed Capture로 위장하지 않는다.

</details>

<a id="implementation-files-and-checks"></a>
<details>
<summary>D. 구현 파일·기존 명령·검증 조건</summary>

### D.1 기존 생성 경로의 파일

다음 파일은 Unreal 프로젝트의 `NeuralGame/ML`을 기준으로 한다.

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

### D.2 사람 정답 명령

아래는 구현된 ML CLI다. 실행 위치는 **Unreal 프로젝트의 `NeuralGame/ML`**이다.
`uv`와 프로젝트 의존성, 해당 candidate의 기존 Snapshot·review queue·승인 결정 파일이 필요하다.
경로는 이 작업 디렉터리 기준이다. 결정 파일은 현재 존재하는 이름과 원본 해시 결속을 확인해 표기했다.
아래는 기존 후보 자료의 재현 예시다. 재실행할 때는 출력 파일을 새 위치로 지정해 기존 자료를 보존한다.
이번 개정에서는 CLI 도움말과 입력 파일만 확인했다. 정답 승격·Dataset 생성은 다시 실행하지 않았다.

```bash
uv run python -m anpc_ml gold promote \
  --decisions config/gold_review_decisions_production_candidate_v1.yaml \
  --review-queue out/production-candidate-v1/teacher-review.jsonl \
  --snapshots out/production-candidate-v1/snapshots.jsonl \
  --snapshot-manifest out/production-candidate-v1/snapshot-manifest.json \
  --output out/production-candidate-v1/gold-annotations.jsonl

uv run python -m anpc_ml gold map \
  --decisions config/gold_review_decisions_production_candidate_v1.yaml \
  --review-queue out/production-candidate-v1/teacher-review.jsonl \
  --snapshots out/production-candidate-v1/snapshots.jsonl \
  --snapshot-manifest out/production-candidate-v1/snapshot-manifest.json \
  --annotations out/production-candidate-v1/gold-annotations.jsonl \
  --output out/production-candidate-v1/gold-dataset.parquet \
  --manifest out/production-candidate-v1/gold-dataset-manifest.json
```

### D.3 생성 경로의 구현 순서

기존 생성 경로는 다음 순서로 구현·검증한다.

1. Profile·request·response Schema와 hostile fixture test를 먼저 작성한다.
2. 미구현 상태에서 검사가 실패하는지 확인한다.
3. contract loader와 canonical encoding을 구현한다.
4. Procedural Generator를 구현하고 같은 조건으로 두 번 실행해 비교한다.
5. Teacher request·strict parse·consensus·Gold queue를 구현한다.
6. Dataset mapper와 Zstandard Parquet writer를 구현한다.
7. 실제 CLI로 fixture Snapshot→Teacher annotation→Parquet를 생성한다.
8. focused test, 전체 Contract test와 `git diff --check`를 실행한다.

### D.4 생성 경로의 완료 조건

- 같은 Profile·seed의 Snapshot shard가 두 번 실행해 byte-identical하다.
- Greet candidate index, 10 Tensor shape·dtype·canonical byte와 candidate hash가 generated contract와 일치한다.
- hidden field, masked index, stale hash, low consensus와 preference cycle hostile test가 실패한다.
- 5개 응답 consensus와 Gold review queue가 문서 규칙과 일치한다.
- Mapper 출력은 Parquet Zstandard이고 Arrow fixed-size Tensor schema를 사용한다.
- Parquet row를 다시 읽어 Snapshot hash·label hash·sample identity를 검증한다.
- integration fixture manifest는 production으로 승격할 수 없다.
- 실제 CLI smoke 산출물이 생성되고 validator가 통과한다.

### D.5 상태의 근거와 이력

과거 ML 실행 수량·Teacher smoke·Capture 수정 과정은 [개편 전 원문](../history/ml-data-pipeline-v1-history-2026-10-28.md)에 보존한다.
Task 2D의 범위별 완료는 외부 evidence의 `task2d-final-acceptance-01.json`에 기록돼 있다.
확인 항목은 원본 빌드, Dataset·Host 실행, 회귀 검사, 파일 보존과 동일 소스의 독립 명세·품질 검토다.
이는 선택 화면·일반 플레이 수집 활성화·학습 가져오기·모델 배포의 완료를 포함하지 않는다.

</details>
