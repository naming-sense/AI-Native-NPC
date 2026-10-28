# 시나리오 수집용 관측 Feature 연결 V1 계약

**상태:** 순수 adapter 구현·검증 완료. Host 연결은 Runtime 구현 전이다. 기존 Schema·Normalizer·hard mask·Utility Profile은 바꾸지 않는다. §§1–6의 순수 변환 의미를 보존하며 Host 집행은 §7에서 연결한다.

## 1. 목적과 입력

현재 Host가 확보한 Knowledge와 Goal 위치를 모델 입력의 정해진 칸에 연결한다. 시나리오의 기대 행동·미래 사건·정답은 입력으로 받지 않는다.

추가 파일은 `Source/NeuralGame/AINativeNPC/Feature/DecisionObservationFeatureAdapter.h/.cpp`와 `Tests/AINativeNPCObservationFeatureTests.cpp`다.

```cpp
class FDecisionObservationFeatureAdapter final
{
public:
    static bool Populate(FTransform const& ObserverTransform, FGoalRuntimeToken const& GoalToken, FTargetUniverseSnapshot const& KnowledgeBeforePromotion, FTargetUniverseSnapshot const& FinalUniverse, AINativeNPC::SchemaV2::FTargetHandleWire const& PrimaryTarget, FDecisionFeatureBuilderInput& InOutDraft);
};
```

이 adapter는 UObject·World query·파일·라벨·scenario ID를 읽지 않는 순수 값 변환이다. Host는 `CaptureTargetUniverse` 직후, primary target을 추가·승격하기 전에 Knowledge 복사본을 확보한다. `Finalize` 직전에 현재 Pawn pose와 같은 Goal token을 넘긴다.

## 2. identity와 실패 원칙

- `(Kind, StableId, Generation, Revision)` 전부 일치하는 handle만 연결한다. revision 또는 generation을 생략하지 않는다.
- observer의 위치·rotation, 사용하는 위치·거리·각도·confidence·age는 finite여야 한다. rotation은 유효한 정규화 quaternion이어야 한다.
- Knowledge·FinalUniverse·Draft.Targets의 Knowledge/Goal revision은 일치해야 한다. 활성 Goal token의 instance/revision/phase generation이 유효해야 한다.
- 같은 exact handle의 중복, 연결할 수 없는 유효 slot, 음수 age, 범위 밖 confidence, 비유한 입력은 실패다.
- 검증과 계산은 임시 복사본에서 수행한다. 실패하면 Draft의 raw 배열·mask·후보·identity를 모두 보존한다.
- 성공해도 Targets·Candidates·hard mask·CandidatePairRaw·switch facts는 변경하지 않는다.

## 3. 위치와 관측의 구분

유효 Target slot의 위치는 promotion 전 Knowledge의 exact entry를 우선한다. 이 경우 현재 actor의 숨은 위치로 교체하지 않는다.

Knowledge에 없는 synthetic primary는 FinalUniverse에서 exact PrimaryTarget이며 Goal-owned인 항목의 이미 검증된 Goal 위치만 사용한다. synthetic `Confidence=1`, 기본 age 또는 상수 `bPathReachable=true`는 관측 사실로 복사하지 않는다.

Knowledge 안의 Entity·LastKnownPosition·SoundEvent에만 관측 confidence·age·visibility를 연결한다. Home·기타 Goal/configuration 위치는 위치 정보로만 다루며 센서 관측의 confidence·age로 승격하지 않는다.

## 4. 소유하는 Feature와 단위

아래 번호는 각 배열 내부 index이며 실제 구현에서는 generated enum 이름을 사용한다.

| 배열 | index | 입력과 계산 |
|---|---|---|
| Target common | 0–2 | 관측/Goal 위치 − 현재 NPC 위치를 rotation만으로 NPC local frame에 변환한 cm. scale을 공간 거리 배율로 쓰지 않음 |
| Target common | 3–5 | 3D 거리 cm, 평면 거리 cm, 다시 3D 거리 cm. 로그 변환은 generated normalizer가 담당 |
| Target common | 6–7 | 같은 bearing radian. sin/cos 결과를 미리 넣지 않음 |
| Target common | 8–9 | 같은 elevation radian. generated sin/cos를 한 번만 적용 |
| Target common | 16 | 센서 provenance가 있는 exact Knowledge entry의 AgeSeconds |
| Target common | 17 | 같은 entry의 Confidence, 0…1 |
| Target common | 23 | 위 규칙으로 유효한 위치를 확보했으면 1 |
| Target common | 24 | 같은 관측 entry의 bVisibleNow |
| Global | 76–83 | GoalToken.Goal one-hot |
| Global | 84–91 | GoalToken.Phase one-hot |
| Global | 97 | 검증된 exact PrimaryTarget이 유효한 slot에 존재하면 1 |

adapter가 소유하는 Target 칸은 먼저 0으로 초기화한 뒤 채운다. synthetic target의 age/confidence/visible은 이 초기값으로 남는다. 패딩·NoTarget target row zeroing과 reserved-zero는 기존 Builder가 처리한다.

### 동일 위치의 방향 convention

평면 차이가 정확히 0이면 bearing raw는 0으로 고정한다. 3D 차이도 0이면 elevation raw 역시 0으로 고정한다. 이때 generated cos 값 1은 **방향이 관측됐다는 의미가 아니라**, 거리 0과 함께 해석하는 결정론적 기본 convention이다. 아주 작은 유한 거리에는 정상 atan2를 사용한다. 임의 threshold로 서로 다른 위치를 같은 위치로 만들지 않는다.

### 미관측 값

- 실제 경로 길이 없는 T14는 sentinel을 사용한다. T15 reachable과 T25 LOS는 이번 adapter에서 관측 true로 채우지 않는다.
- 측정하지 않은 T30/T31은 schema의 missing sentinel(`never`, encoded 1), G94는 missing sentinel(`no_deadline`, encoded 1)을 사용한다. 이는 실제 never/no-deadline을 확인했다는 주장과 구분한다.
- 건강·stamina·관계·성격·위협·신원 확신·velocity·event buffer·Entity payload는 새로 추정하지 않는다. 기존 기본값을 유지하고 수집 도구의 지원 축에서 제외한다.
- CandidatePair feature는 이번 V1에서 변경하지 않는다. 추후 채울 때 P5는 초, P6는 normalized distance라는 별도 단위 계약이 필요하다.

수집 sidecar의 관측 연결 버전은 `observed_geometry_goal_v1`이다. 이 버전은 모든 게임 Feature의 관측 연결 완료를 뜻하지 않는다.

## 5. 실제 동작과 승인 경계

현재 Guard Utility의 CandidatePair 가중치는 전부 0이며 adapter도 CandidatePair와 mask를 보존한다. 같은 후보·switch fact에 대한 현재 Guard Utility 점수와 선택은 동일해야 한다. 이 보장을 임의의 다른 Profile로 확대하지 않는다.

새 raw 관측이 들어가므로 Tensor·input hash는 달라질 수 있다. Capture write/readback과 Python decoder가 같은 실제 값을 복원해야 한다. Neural evaluator를 켜거나 Production 준비 상태를 바꾸지 않는다.

## 6. 먼저 실패시킬 검사

1. 다른 거리·회전에서 예상한 cm/radian raw와 normalized Tensor가 변한다.
2. Knowledge의 저장된 관측 위치를 쓰며 현재 숨은 actor 위치를 요구하지 않는다.
3. confidence/age/visibility는 exact Knowledge handle에만 연결되고 synthetic primary의 기본값은 제외된다.
4. revision/generation mismatch·중복·NaN/Inf·음수 age·잘못된 pose는 실패하고 Draft가 보존된다.
5. 동일 위치 convention, missing sentinel, reserved/padding/NoTarget zero가 계약과 같다.
6. hard mask·후보·CandidatePair·현재 Guard Utility 선택은 동일하다.
7. 실제 Host의 새 Capture를 다시 읽었을 때 관측 값과 input identity가 유지된다.

검사·독립 검토를 마치기 전에는 Runtime 관측 연결 완료로 표시하지 않는다.

## 7. Host 호출과 수집 실패 집행

[Host 관측 연결과 수집 Capture 발행 V1 계약](scenario-host-capture-v1-contract.md)이 실제 호출자·순서·수집 회차 수명을 소유한다. 순수 adapter와 원래 37-case Automation은 동결한다. 기존 Development Editor focused 37·broad 204 및 독립 명세·품질 검토는 순수 adapter 단계의 완료 증거다. Host의 새 Capture/복원·실제 입력·reset 증거는 후속이다.

Host는 CaptureTargetUniverse 성공 직후 승격 전 KnowledgeBeforePromotion을 값 복사한다. Finalize 직전에 같은 Goal token·현재 Pawn pose·최종 universe·exact primary를 Populate에 전달한다. 실패하면 전체 Draft와 이전 성공 Snapshot을 새 Decision에 사용하지 않으며 Finalize·policy·Request·Capture·Commit을 차단한다.

수집 모드의 hard observation failure는 해당 회차의 retry epoch/lease를 무효화한다. deadline 전 failed, at/after deadline에는 기존 timed_out 우선순위를 유지하고 실제 오류를 diagnostic에 보존한다. terminal evidence 보존과 verified reset 뒤 새 회차만 허용한다. bool 실패는 observation_mapping_failed로 기록하며 직접 검사한 precondition 외의 상세 원인은 추측하지 않는다. 정상 sensor 부재·위치 전용 primary·missing sentinel은 §§1–6의 정상 의미를 유지한다. 저장·진단 실패와 reset failed/unverified는 session을 차단한다. 실제 stop/reset은 Task 3 owner 책임이다.
