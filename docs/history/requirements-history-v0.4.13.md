# Requirements History — v0.4.13

- 날짜: 2026-08-10
- phase: Reader-facing Terminology Clarification
- 판정: **DOCUMENTATION TERMINOLOGY UPDATE — MACHINE CONTRACT UNCHANGED**

## 변경 이유

`Belief`와 `Typed Target`는 구현자에게는 정확하지만 처음 읽는 사람에게는 의미가 바로 전달되지 않았다. 특히 제품 요구사항의 Target 장과 세부 요구사항의 Typed Target 장이 같은 개념 계층이라는 점이 이름만으로 드러나지 않았다.

## 변경 내용

1. 독자용 `Belief` 표시를 **`Knowledge`**로 바꿨다.
2. 세부 요구사항의 `Typed Target` 장 제목을 **“Target의 종류와 식별 정보”**로 바꿨다.
3. `Knowledge`의 현재 코드·Schema 식별자는 `Belief`임을 최초 정의에 남겼다.
4. 기존 `#2-typed-target` anchor를 명시적으로 보존해 companion 링크를 깨지 않았다.
5. 제품 요구사항과 세부 요구사항의 hash pin을 다시 계산한다.

## 범위 경계

이번 개정은 사람이 읽는 표시 이름만 바꾼다. 다음 기계 계약과 코드 식별자는 변경하지 않는다.

- Schema·Registry YAML
- generated Python/C++
- `Belief`, `TypedTarget` 및 관련 API 이름
- Target identity, slot, Candidate, timer와 Commit semantics
- 현재 PASS/RED/HOLD 범위

Runtime 구현과 gameplay 기능은 추가하지 않았다.
