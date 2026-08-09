# Requirements History — v0.4.10

- 날짜: 2026-08-09
- phase: Boss Pattern Encounter Session Host / StateTree Start Handoff
- 판정: **COMPLETE — PHASE PASS**

## 변경 계약

1. Production Pawn은 Session/EventSource/Host component를 각각 exact-one 소유한다.
2. Host 설치·pending·Commit ingress는 private friend 경로다.
3. exact production Pawn generated class와 server authority만 Host를 설치한다.
4. private unique-owned authority provider가 selection snapshot과 Commit-time current state를 별도로 capture한다.
5. typed `(TargetHandle, Actor)` binding은 exact identity·generation·revision·World·owner를 Commit에서 재검증한다.
6. Commit publish 뒤에만 StateTree를 exact-once start한다.
7. Task 진입은 durable acquisition과 exact queued fact로 관찰한다.
8. start 실패는 dedicated `ExecutionHost` one-shot fact로 terminalize하고 Success-unlock 없이 fail-closed한다.
9. concrete gameplay authority provider와 production selector trigger는 후속 범위다.

## 증거

- focused `2/2`, full Boss Pattern `53/53`, warning/failure `0/0`
- clean+cold UBT/UHT PASS
- Data Validation `290 / 0 / 0`
- generated lock sync
- changed-file SARIF `15 / 0`
- MCP restart Host/Session/EventSource `1/1/1`
- StateTree ready/hash/clean, map dirty/unsaved `false/false`, active/interrupted ChangeSet `0/0`

상세 구현·transient failure·검토 기록은 NeuralGame repo-local closure를 따른다:

`/mnt/d/Codex-cli/NeuralProject/NeuralGame/.hermes/plans/2026-08-09-boss-pattern-encounter-session-host-start-handoff-closure.md`
