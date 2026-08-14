# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요

# General NPC Skill Execution Semantics V1

**Status: PRODUCTION AUTHORITY**

- Approved: `2026-08-11`
- Skill Registry SHA-256: `ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d`
- Runtime authority: server GameThread
- Target position: execution-start recapture, then frozen
- DecisionRecord v2 layout: unchanged
- 10-Tensor contract: unchanged

## Common

`effective_speed = speed × (base + scale × intensity)`; base and scale come from the Registry.

Success wins when success and timeout are observed at the same authoritative server time.
New perception updates Knowledge and affects the next selection. It does not reinterpret the running Skill.

## Exact execution values

| Skill | ID | Success | Stable | Fixed values |
|---|---:|---|---:|---|
| TurnTo | 3 | yaw error ≤ 5.0° | 0.1 s | coincident ≤ 1.0 cm |
| Approach | 4 | planar distance ≤ preferred_distance | 0 s | complete path only |
| Investigate | 8 | distance and yaw error ≤ 15.0° | 0.5 s | base turn 360.0°/s |
| SearchArea | 9 | all valid points, or deadline after ≥1 visit | duration budget | 9 fixed world-axis points; 100.0 cm acceptance |

## Deterministic SearchArea offsets

| Order | X × radius | Y × radius |
|---:|---:|---:|
| 0 | 0 | 0 |
| 1 | 0.5 | 0 |
| 2 | 0 | 0.5 |
| 3 | -0.5 | 0 |
| 4 | 0 | -0.5 |
| 5 | 0.70710678118654757 | 0.70710678118654757 |
| 6 | -0.70710678118654757 | 0.70710678118654757 |
| 7 | -0.70710678118654757 | -0.70710678118654757 |
| 8 | 0.70710678118654757 | -0.70710678118654757 |

## Local failure reasons

- `TargetInvalid`
- `TargetUnsupported`
- `PathUnavailable`
- `TimedOut`
- `MovementModeUnsupported`
- `AuthorityLost`
- `AssemblyInvalidated`
- `Interrupted`
