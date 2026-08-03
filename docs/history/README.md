# AI Native NPC 문서 이력

이 폴더는 현재 구현에 직접 적용하지 않는 변경 기록을 보관합니다. 지금 읽고 구현할 기준은 [`docs/current/requirements.md`](../current/requirements.md)에서 시작하는 현행 문서 네 개입니다.

## 개정 이력

- [Requirements History v0.4.6](requirements-history-v0.4.6.md)
  - 현재 요구사항의 상태 변경, 검증 판정, 완료된 remediation을 기록합니다.

## 검토 기록

- [Requirements Review v0.4.6](reviews/requirements-review-v0.4.6.md)
  - 분리 전 결합 문서에 수행한 독립 검토와 당시 판정을 보존합니다.

## 완료된 요구사항 기록

- [보스 전용 Neural Pattern Selector 요구사항](requirements/2026-08-03-boss-pattern-neural-policy-requirements.md)
  - 공통 272 Candidate를 유지하는 보스 전용 32-row Pattern 하위 정책의 완료 계약을 기록합니다.

## 완료된 작업 계획

- [보스 전용 Neural Pattern Selector 구현 계획](plans/2026-08-03-boss-pattern-neural-policy-implementation-plan.md)
- [문서 분리와 Teacher LLM 계약 계획](plans/2026-08-02-requirements-document-split.md)
- [독자 중심 Requirements 재구성 계획](plans/2026-08-02-requirements-reader-first-restructure.md)
- [Requirements 검토 remediation 계획](plans/2026-08-02-requirements-review-remediation.md)
- [독자 중심 최종 정리 계획](plans/2026-08-03-reader-first-final-cleanup.md)
- [문서 정보 구조 정리 계획](plans/2026-08-03-docs-information-architecture-cleanup.md)

## History와 Archive의 차이

- `docs/history`는 현재 릴리스가 만들어진 과정과 판정을 설명합니다.
- 보관 Harness의 `docs/archive`는 이전 버전 문서 원본을 보존합니다.

History는 감사와 변경 추적에 사용합니다. 현재 계약과 충돌하면 `docs/current`와 `contracts/current`가 우선합니다.
