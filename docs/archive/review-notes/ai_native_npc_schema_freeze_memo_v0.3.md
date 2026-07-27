# AI Native NPC 요구사항 구현계획 v0.3 (Schema Freeze 준비판)

이 문서는 v0.2 리뷰에서 남은 구현 블로커를 해결하기 위한 변경사항만 정리한 보완판이다.

## 리뷰 검토

제시된 리뷰는 거의 전부 타당하다.

특히 반드시 반영해야 하는 항목은 다음 6가지이다.

1. Typed Target 계약
2. Target Slotter 계층
3. Goal Arbitration 계약
4. Adjusted Score 이후 Calibration
5. Atomic Commit
6. Schema 2.0 Tensor/Hash 계약

### 1. Typed Target

Target을 Entity 하나로 취급하지 않는다.

지원 Target
- Entity
- SoundEvent
- LastKnownPosition
- CoverSlot
- SmartObject
- Waypoint
- WorldPosition
- NoTarget

모든 Target은 Stable Handle(Kind, StableId, Generation)을 가진다.

### 2. Target Slotter

Pipeline

Perceived Universe
→ Target Universe
→ Target Slotter
→ Candidate Universe

Mandatory Preserve
- Current Target
- Current Attacker
- Goal Target
- Reserved Resource
- Active Dialogue Target

Target Recall을 Candidate Recall과 별도 KPI로 관리한다.

### 3. Goal Arbitration

Goal State
- Inactive
- Active
- Suspended
- Succeeded
- Failed
- Aborted

Active Goal은 하나만 허용한다.

Goal Revision 증가 조건을 명시한다.

### 4. Adjusted Score

Pipeline

Raw Score
→ Switch Cost
→ Adjusted Score
→ Candidate Selection
→ Calibration
→ OOD
→ Abstain

Calibration은 Adjusted Score 기준으로 수행한다.

### 5. Atomic Commit

Validate와 Resource Reservation을 하나의 트랜잭션으로 처리한다.

NPC당 동시에 In-flight Decision은 하나만 허용한다.

### 6. Hidden Information

LOS와 Path Projection은 Believed Position 기준으로만 계산한다.

Sight Lost 이후에는 LastKnownPositionTarget으로 변환한다.

### 7. Schema Freeze

V1에서 다음을 완전히 고정한다.

- Tensor Shape
- dtype
- enum
- field order
- padding
- mask
- normalization
- serialization
- candidate hash

Python과 Unreal은 동일 Schema Generator를 사용한다.

### 8. KPI

- Candidate Recall >=99.5%
- Critical Recall =100%
- Target Recall >=99.5%
- Safety 비열등
- Latency 비열등
- 최소 1개 핵심 품질 지표 우월

### 9. Dataset Gate

총 샘플 수 대신
- Role별 최소 표본
- Goal별 최소 표본
- Worst Group
- Confidence Interval
- Learning Curve

기준으로 관리한다.

### 10. 용어

Phase0 = MVP Vertical Slice
Phase1 = V1
