# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# Requirements History — v0.4.11

- 날짜: 2026-08-10
- phase: Goal Registry 1.1.0 / Goal FSM Runtime 문서 동기화
- 판정: **DOCUMENTATION SYNC COMPLETE — RUNTIME CORE RED / GAMEPLAY FSM HOLD**

## 반영한 계약

1. Goal Registry `1.1.0`은 Goal 4개, Goal/phase 14개, transition `41 = 35 event + 6 timer`를 소유한다.
2. Production phase timeout은 `2/15/8/4/6/5초`, clock은 `server_monotonic_world_seconds`다.
3. phase entry는 full duration, `ResumeSamePhase`는 stored remaining, `RestartPhase`는 중단됐던 같은 phase의 full duration을 사용한다.
4. phase exit·terminal은 timer를 취소하고 expiry는 typed timer trigger를 정확히 한 번 queue한다.
5. expiry와 `phase_timeout` guard truth는 별개다. trusted guard provider가 없으면 fail-closed한다.
6. World pause 중 timeout은 멈추고 time dilation을 따른다. wall clock과 client-local clock은 금지한다.
7. 제한 Core의 persisted form은 full Goal save가 아니라 Registry-bound versioned timer snapshot이다.
8. restore는 비영속 `expected_current_token` CAS를 요구하며 mismatch 시 live state를 바꾸지 않는다.
9. authority commit `2770b4a5a3aebd430420e5b330441aa044cc7db5` 기준 generated C++ binding과 consumer lock/sync는 PASS다.

## 현재 구현 경계

| Gate | 상태 |
|---|---|
| Contract/generator/consumer provenance | PASS |
| Goal Contract Dispatcher·Timer Core | RED — 테스트만 존재 |
| `GoalFsmRuntime.h/.cpp` | 미구현 |
| Server Timer Runtime Component | 미구현 |
| Production Belief/Goal/Typed Target provider | HOLD |
| 29 gameplay guard·2 effect provider | HOLD |
| 전체 arbitration/save archive | HOLD |
| Gameplay Goal FSM Runtime | HOLD |

RED 테스트:

`/mnt/d/Codex-cli/NeuralProject/NeuralGame/Source/NeuralGame/AINativeNPC/Tests/GoalFsmRuntimeTests.cpp`

현재 존재하지 않는 구현:

```text
Source/NeuralGame/AINativeNPC/Goal/GoalFsmRuntime.h
Source/NeuralGame/AINativeNPC/Goal/GoalFsmRuntime.cpp
Source/NeuralGame/AINativeNPC/Goal/GoalFsmRuntimeComponent.h
Source/NeuralGame/AINativeNPC/Goal/GoalFsmRuntimeComponent.cpp
```

## 문서 정리

- 루트 README와 현행 문서 네 개의 상태 표를 같은 경계로 맞췄다.
- Unreal 계획의 stale `1.5/8/10초`, legacy `OnEnter`·`ForceAbort` 수기 표를 제거했다.
- Contract Appendices의 A–D marker를 Goal Registry `1.1.0` generator 출력으로 수동 편집 없이 재생성·동기화했다.
- Boss Pattern·Test Taxonomy KPI generated marker는 보존했고, Goal Runtime status note는 marker 밖에 추가했다.
- `generated/docs/`는 `main`의 정식 소비 산출물이 아니므로 working tree에 남기지 않는다.
- 이 개정은 문서 동기화이며 Runtime 구현, commit, push를 포함하지 않는다.
