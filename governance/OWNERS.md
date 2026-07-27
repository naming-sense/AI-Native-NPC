# 문서 Owner와 승인 책임

실제 담당자 이름은 프로젝트 착수 시 채운다.

| 영역 | Primary Owner | 필수 Reviewer | 승인 책임 |
|---|---|---|---|
| 요구사항·Goal·Skill 계약 | AI/Game Design Lead | Gameplay Lead, ML Lead | Product/AI Director |
| Schema YAML | ML Lead | UE Tech Lead, Server Lead | ML + UE 공동 승인 |
| UE 5.7 구현 프로필 | UE Tech Lead | Gameplay Lead, ML Lead | Engineering Lead |
| Candidate/Target Slotter | Gameplay AI Lead | ML Lead, QA Lead | Engineering Lead |
| Calibration/OOD | ML Lead | Gameplay AI Lead, Data Lead | AI Director |
| Atomic Commit/멀티플레이 | Server Lead | UE Tech Lead, QA Lead | Engineering Lead |
| Golden Tests | QA Automation Lead | ML/UE 담당자 | QA Lead |
| Freeze Manifest | Release Owner | 모든 필수 Reviewer | Release Approver |

## 최소 승인 규칙

- Schema Shape 또는 Enum ID 변경: ML Lead와 UE Tech Lead 모두 승인
- Hidden Information 경계 변경: Gameplay Lead와 QA Lead 승인
- Commit/Authority 변경: Server Lead 승인
- KPI Gate 변경: Product/AI Director 승인
