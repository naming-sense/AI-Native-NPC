# Requirements History — v0.4.12

- 날짜: 2026-08-10
- phase: Reader-first Requirements 재구성
- 판정: **DOCUMENTATION RESTRUCTURE — RUNTIME CONTRACT UNCHANGED**

## 변경 이유

기존 `requirements.md`는 구현 의존성 때문에 Typed Target부터 설명했다. 주제 목차는 Goal Manager를 2번으로 표시하면서 실제 §5로 연결했고, Typed Target와 Slotter를 한 링크로 표시하면서 §2 Typed Target만 열었다. 도메인 지식이 없는 독자는 문서 순서와 시스템 판단 순서를 연결하기 어려웠다.

## 변경 내용

1. `requirements.md`를 제품·기획·신규 독자용 설명으로 다시 작성했다.
2. 장 순서를 `제품 목표 → Goal → Belief → Target → Candidate → 선택 → Commit → Boss Pattern → 학습 → 상태`로 고정했다.
3. 목차 번호와 실제 장 번호를 1:1로 맞췄다.
4. 기존의 정확한 Runtime·데이터·안전 계약은 `technical-requirements.md`로 보존했다.
5. 기술 참조의 목차도 실제 §0–§11 순서와 맞췄다.
6. README와 Implementation/Unreal/Appendices의 세부 anchor를 새 기술 참조로 갱신했다.
7. 제품 요구사항, 세부 기술 요구사항, 기계 판독 계약의 우선순위를 명시했다.

## 범위 경계

이 개정은 정보 구조와 설명 방식만 바꾼다. Schema, Registry, generated Python/C++, Goal timeout, Runtime 구현 상태와 gameplay 범위는 변경하지 않는다.

- Goal Dispatcher·Timer Core: RED
- Gameplay Goal FSM: HOLD
- Boss Pattern fixture-backed Host/start handoff: phase PASS
- production gameplay provider·전투 효과·ML/NNE·Release: HOLD/NO-GO

이 개정에는 Runtime 구현이 포함되지 않는다. Git commit과 push는 검증 완료 뒤 별도 작업으로 처리한다.
