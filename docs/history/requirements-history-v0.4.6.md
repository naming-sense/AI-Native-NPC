# AI Native NPC 요구사항 v0.4.6 검증·개정 이력

- 현행 요구사항: [`docs/current/requirements.md`](../current/requirements.md)
- 현행 구현 계획: [`docs/current/implementation-plan.md`](../current/implementation-plan.md)
- 현행 계약 부록: [`docs/current/contract-appendices.md`](../current/contract-appendices.md)
- 이력 기준일: 2026-08-03
- 성격: 감사와 변경 추적을 위한 참고 문서

> 이 문서는 과거 판정과 검증 범위를 보존한다. 현재 구현 계약과 작업 가능 범위는 Requirements 본문 상단의 `현재 상태`를 따른다. 이력 문서의 과거 `GO`를 현재 Runtime 승인으로 해석하면 안 된다.

---

## 1. v0.4.2에서 해결한 범위

v0.4.2는 cross-environment release와 Python↔C++ Golden parity를 도입했다. 이후 검토에서 다음 빈틈이 확인됐다.

- YAML 필드 변경이 문서 Appendix에 자동 반영되지 않음
- Normalizer의 역전 범위와 0 이하 divisor 같은 의미 오류를 충분히 차단하지 못함
- Hash serializer 일부가 YAML이 아니라 생성기 코드에 하드코딩됨

---

## 2. v0.4.6 RC5 Validation Scope & Catalog Closure

v0.4.6 RC5는 기존 계약에 다음 검증 범위를 추가했다.

1. PyYAML `safe_load` 기반 전체 Schema 의미 검증
2. Enum ID·Tensor Shape·Field Index·Target Payload·Output·Normalizer·Hash 계약 검증
3. `skill_registry_v1.yaml`, `goal_registry_v1.yaml`
4. YAML에서 생성한 C++/Python 코드와 생성 Manifest
5. Candidate Set canonical bytes와 정수 Slotter quantization Golden fixture
6. Lock 등록 파일과 실제 ZIP 파일 집합의 역방향 일치 검사
7. 모든 Freeze Gate의 상태·증거·도구 버전을 기록하는 통합 Manifest
8. Contract mismatch와 OOD 분리
9. Slotter 정렬용 정수 quantization
10. bounded cosine scorer와 Skill별 Parameter 계약
11. 규범 테스트 리포트에서 compiler version·실행시간·stdout/stderr 제거
12. 환경 진단을 `dist/local/`의 비규범 파일로 분리하고 ZIP에서 제외
13. `release` 단일 명령으로 생성→테스트→Manifest→Lock→Strict Validate→Double Pack 실행
14. 생성 C++에 quantization·normalizer·canonical serialization·bit packing·SHA-256·parameter clamp 구현
15. 동일 Golden vector를 Python과 C++ 양쪽에서 실행
16. Harness tree digest와 file count를 Validator가 직접 재계산
17. Schema·Registry에서 Appendix A~D를 자동 생성하고 Requirements/UE marker block과 byte 단위 비교
18. 모든 Normalizer에 finite·min≤max·positive divisor·log1p domain·missing/sentinel/valid-range 정합성 강제
19. Candidate/Decision Hash serializer를 YAML의 ordered field contract에서 Python/C++로 생성
20. Candidate Hash magic 변경, field rename, reversed clamp를 검출하는 mutation regression test
21. Decision Contract Hash의 Python↔C++ Golden vector 추가
22. Hash magic literal을 자동 생성 영역 밖에서 수기 중복하지 못하도록 strict guard 추가
23. constant normalizer·missing·must_equal·valid range·padding_zero 교차 정합성 검증 추가
24. Mutation probe가 현재 Schema와 충돌하지 않도록 동적으로 다른 값을 생성

고정 태그 `full-harness-v0.4.6-rc5`는 위 Schema·생성 코드·문서 parity를 검증한 보관 증거다.

### 당시 판정

| 범위 | 당시 상태 |
|---|---|
| Phase 0 | GO |
| Schema 코드 생성 | GO |
| 대량 학습 데이터 생성 | HOLD |
| Schema 2.0 최종 Freeze | Float/ONNX parity와 Runtime Gate 전 NO-GO / Conditional |

이 표는 2026-08-02 Requirements Review 이전 기록이다.

---

## 3. 2026-07-30 ML/NNE 구현 보강

이 보강은 Schema·Enum·Registry·Tensor Shape·Hash 값을 바꾸지 않고 모델 Layer, Dataset Record, Loss, 학습 설정, Calibration/OOD, ONNX Export, Unreal NNE 적용 절차를 문서에 추가했다.

작은 fixture model과 end-to-end smoke는 허용했지만 Feature Capture parity와 split validator 전에는 V1 대량 데이터 생성을 계속 보류했다. 해당 Supplement는 기존 90파일 Lock bundle에 포함되지 않았으므로 최종 Freeze 시 새 문서 버전과 Harness baseline이 필요하다.

---

## 4. 2026-08-02 Requirements Review Remediation 1

검토 보고서:

`docs/history/reviews/requirements-review-v0.4.6.md`

검토는 RC5 Harness PASS와 Runtime/ML 승인을 분리했다. 다음 항목이 구조화된 Schema·Registry·Generator와 Runtime evidence에 아직 반영되지 않았음을 확인했다.

1. Unreal Runtime OOD 계산용 `tactical_context [B,128]` ONNX output
2. 학습·평가에서 Runtime Switch Cost를 재현하는 Candidate별 component record
3. Goal arbitration의 `preemption_margin`, 생성시간 quantization, suspended resume, revision 계약
4. Event/Timer/Lifecycle을 분리한 Typed Goal Trigger와 phase timeout Registry
5. Identity/Snapshot equality, async stale bound, 실제 case catalog, non-vacuous Calibration Gate

### Remediation 이후 작업 범위

| 범위 | 상태 | 의미 |
|---|---|---|
| 기존 RC5 Schema/Generated Harness | PASS | 현 RC5의 생성·Golden·문서 parity 증거 |
| Phase 0 Utility Baseline 수직 슬라이스 | 조건부 GO | fallback·capture·commit 경로 구현 가능 |
| Phase 0 RC5 Neural smoke | 조건부 GO | score/parameter 연결 확인만 가능 |
| V1 Neural Training/Calibration | HOLD | Dataset·output·Goal 계약 patch 필요 |
| 대량 학습 데이터 생성 | HOLD | hash·split·case catalog validator 필요 |
| Schema 2.0 최종 Freeze | NO-GO | 생성·Golden·Runtime Gate·Formal Approval 필요 |

Remediation은 목표 계약을 Requirements에 기록했지만 RC5 YAML·Generated output을 수동으로 바꾸지 않았다. 구조화된 계약 변경은 후속 patch release에서 Generator로 재생성하고 새 Decision Contract Hash를 발급해야 한다.

---

## 5. 2026-08-02 문서 분리와 Teacher LLM 계약 복원

결합 문서를 독자와 집행 단계에 따라 세 문서로 분리했다.

- Requirements: Runtime·데이터·안전 규범
- Implementation Plan: Reference Model·학습·릴리스·Phase 실행 절차
- Contract Appendices: 생성 Schema/Registry 표와 승인 기준

개발 단계의 `Teacher LLM Silver Label` 계약에는 입력 경계, strict response, 5-sample 합의, Dataset Record mapping, annotation provenance, Gold Validation 승격 Gate를 추가했다. Teacher Profile·request/response Schema·Golden parity가 구현되기 전 Teacher Silver 생성은 HOLD다.

생성 Appendix의 단일 문서 경로 변경은 Schema와 Test Taxonomy의 `documentation_contract`에 반영했다.

2026-08-03에는 `DOC-GENERATOR-001`을 완료했다. Candidate Hash는 Appendix D.3, Decision Hash는 D.4, Normalizer는 D.5에서 생성한다. Generator 회귀 테스트는 Appendix D 번호의 중복과 비연속을 차단한다.

---

## 6. 상태 용어 해석

- `Harness PASS`: Schema, 생성 코드, Golden fixture, 문서 marker의 정적 정합성 증거다.
- `Runtime PASS`: 실제 Unreal/서버 경로가 실행되고 필요한 Runtime test가 통과했다는 뜻이다.
- `Quality/Safety PASS`: 잠긴 Dataset과 평가 Gate가 통과했다는 뜻이다.
- `Freeze`: 위 증거와 Formal Approval이 모두 잠겼다는 뜻이다.

이 단계들을 서로 대신할 수 없다.
