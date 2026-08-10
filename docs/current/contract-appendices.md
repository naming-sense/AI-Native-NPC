# AI Native NPC Contract Appendices
## 생성 Schema·Registry 계약과 승인 기준

- 문서 버전: **v0.4.13**
- 개정일: 2026-08-10
- 주 독자: **Gameplay AI, ML, Data, Unreal NNE, QA, Release 승인자**
- 범위: **Appendix A–D generated 공통 계약, Appendix BP generated Boss Pattern 계약, Appendix E 품질·안전·성능 Gate, UE 구현 승인 체크리스트**
- 제품 요구사항: [AI Native NPC 제품 요구사항](requirements.md)
- 세부 기술 요구사항: [AI Native NPC 세부 기술 요구사항](technical-requirements.md)
- 구현 계획: [AI Native NPC 구현 계획](implementation-plan.md)
- Unreal 구현 계획: [UE 5.7 Manny·Quinn 구현 계획](unreal-implementation-plan.md)

Appendix A–D와 BP의 생성 marker 내부는 구조화된 YAML과 Generator가 소유한다. 이 문서에서 수동 편집하지 않는다.

---

## Appendix A–D 사용 안내

Appendix A–D는 Schema와 Registry에서 생성한 enum ID·Tensor index·Target payload·Skill parameter·Goal·Hash를 제공한다. 값 변경은 구조화된 원본과 Generator에 적용한다.

<!-- BEGIN AUTO-GENERATED SCHEMA CONTRACT -->

# Appendix A–D. AUTO-GENERATED Schema·Registry 계약

> 이 구간은 `contracts/current/*.yaml`에서 자동 생성된다. 수동 편집하지 않는다.

- Generator: `0.4.6`
- Contract revision: `2.0.0-rc5`
- Schema SHA-256: `a7791004de0534f29198ebf5eaaff7cd764185b59b05446d419f5d0a3303f886`
- Skill Registry SHA-256: `08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8`
- Goal Registry SHA-256: `ede7aaba704ecbbd9c6e1cb649c87e03fd24e9dc71ea4166f82baa42fb00ee43`
- Test Taxonomy SHA-256: `2c4f911c23c8502231351fd2a1ffc606a04c29c4c3e39ea384099462811dad79`

## A. Constants와 Enum

### A.1 Constants

| Name | Value |
|---|---:|
| `schema_version` | `2.0.0` |
| `skill_registry_version` | `1.0.0` |
| `target_slotter_version` | `1.0.0` |
| `postprocess_version` | `1.0.0` |
| `normalization_version` | `2.0.0` |
| `regular_target_slots` | `16` |
| `no_target_slot` | `16` |
| `total_target_slots` | `17` |
| `skill_count` | `16` |
| `candidate_count` | `272` |
| `event_slots` | `12` |
| `global_feature_count` | `128` |
| `target_feature_count` | `48` |
| `event_feature_count` | `24` |
| `candidate_pair_feature_count` | `16` |
| `parameter_count` | `4` |
| `spatial_max_cm` | `5000.0` |
| `path_distance_max_cm` | `10000.0` |
| `speed_max_cm_s` | `1200.0` |
| `acceleration_max_cm_s2` | `4000.0` |
| `yaw_rate_max_deg_s` | `720.0` |
| `target_age_max_s` | `10.0` |
| `event_age_max_s` | `10.0` |
| `visible_duration_max_s` | `10.0` |
| `skill_time_max_s` | `10.0` |
| `goal_phase_time_max_s` | `30.0` |
| `goal_deadline_max_s` | `120.0` |
| `count_max` | `8.0` |
| `schema_contract_revision` | `2.0.0-rc5` |
| `goal_registry_version` | `1.1.0` |
| `goal_priority_max` | `255.0` |
| `long_duration_max_s` | `30.0` |
| `slotter_confidence_scale` | `1000` |
| `slotter_age_centisecond_scale` | `100` |
| `slotter_distance_bin_cm` | `10` |
| `slotter_loudness_scale` | `1000` |

### A.target_kind

| ID | Name |
|---:|---|
| 0 | `NoTarget` |
| 1 | `Entity` |
| 2 | `SoundEvent` |
| 3 | `LastKnownPosition` |
| 4 | `CoverSlot` |
| 5 | `SmartObject` |
| 6 | `Waypoint` |
| 7 | `WorldPosition` |

### A.skill

| ID | Name |
|---:|---|
| 0 | `Idle` |
| 1 | `ContinueCurrentAction` |
| 2 | `LookAt` |
| 3 | `TurnTo` |
| 4 | `Approach` |
| 5 | `KeepDistance` |
| 6 | `RetreatFrom` |
| 7 | `Follow` |
| 8 | `Investigate` |
| 9 | `SearchArea` |
| 10 | `Greet` |
| 11 | `Warn` |
| 12 | `CallForHelp` |
| 13 | `TakeCover` |
| 14 | `Flee` |
| 15 | `Attack` |

### A.goal_type

| ID | Name |
|---:|---|
| 0 | `None` |
| 1 | `IdleObserve` |
| 2 | `InvestigateDisturbance` |
| 3 | `EnforceBoundary` |
| 4 | `CombatEngage` |
| 5 | `Disengage` |
| 6 | `Escort` |
| 7 | `Reserved` |

### A.goal_phase

| ID | Name |
|---:|---|
| 0 | `None` |
| 1 | `Observe` |
| 2 | `Orient` |
| 3 | `Navigate` |
| 4 | `Interact` |
| 5 | `Search` |
| 6 | `Resolve` |
| 7 | `Return` |

### A.event_type

| ID | Name |
|---:|---|
| 0 | `NoneOrPadding` |
| 1 | `SightAcquired` |
| 2 | `SightLost` |
| 3 | `SoundHeard` |
| 4 | `Damaged` |
| 5 | `SkillSucceeded` |
| 6 | `SkillFailed` |
| 7 | `SkillInterrupted` |
| 8 | `WarningIssued` |
| 9 | `WarningIgnored` |
| 10 | `TargetMovedSignificantly` |
| 11 | `TargetInvalidated` |
| 12 | `GoalChanged` |
| 13 | `ReservationLost` |
| 14 | `SharedKnowledgeReceived` |
| 15 | `Other` |

### A.goal_source_priority

| ID | Name |
|---:|---|
| 0 | `Routine` |
| 1 | `Social` |
| 2 | `Combat` |
| 3 | `Quest` |
| 4 | `Emergency` |

## B. Tensor 계약

### B.1 Tensor Summary

| Name | Shape | dtype |
|---|---|---|
| `global_state` | `["B",128]` | `float32` |
| `target_features` | `["B",17,48]` | `float32` |
| `target_kind_ids` | `["B",17]` | `int64` |
| `target_mask` | `["B",17]` | `bool` |
| `event_features` | `["B",12,24]` | `float32` |
| `event_type_ids` | `["B",12]` | `int64` |
| `event_target_slots` | `["B",12]` | `int64` |
| `event_mask` | `["B",12]` | `bool` |
| `candidate_pair_features` | `["B",272,16]` | `float32` |
| `candidate_mask` | `["B",272]` | `bool` |
| `candidate_raw_scores` | `["B",272]` | `float32` |
| `candidate_parameter_proposals` | `["B",272,4]` | `float32` |

### B.2 global_state

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `self_health_norm` | self authoritative health ratio | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `self_stamina_norm` | self authoritative stamina ratio | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `self_speed_norm` | self speed | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `self_local_velocity_x` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `self_local_velocity_y` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `self_local_velocity_z` | self velocity in NPC-local frame | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `self_local_acceleration_x` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `self_local_acceleration_y` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `self_local_acceleration_z` | self acceleration in NPC-local frame | `cm/s²` | `{"divisor_ref":"acceleration_max_cm_s2","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `self_yaw_rate_norm` | self yaw angular speed | `deg/s` | `{"divisor_ref":"yaw_rate_max_deg_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `self_grounded` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `self_crouched` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `self_sprinting` | self movement state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `self_in_combat` | authoritative self combat state | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `self_damaged_recently` | damage event within 3 seconds | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `self_recent_damage_norm` | damage received in 3-second window / max health | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `current_skill_Idle` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `current_skill_ContinueCurrentAction_reserved_zero` | control candidate is never an executing skill | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 18 | `current_skill_LookAt` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `current_skill_TurnTo` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `current_skill_Approach` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `current_skill_KeepDistance` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `current_skill_RetreatFrom` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `current_skill_Follow` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 24 | `current_skill_Investigate` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 25 | `current_skill_SearchArea` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 26 | `current_skill_Greet` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 27 | `current_skill_Warn` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 28 | `current_skill_CallForHelp` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 29 | `current_skill_TakeCover` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 30 | `current_skill_Flee` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 31 | `current_skill_Attack` | current skill one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 32 | `skill_elapsed_norm` | elapsed time in current skill | `s` | `{"divisor_ref":"skill_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 33 | `skill_progress_norm` | skill-defined progress | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 34 | `skill_min_duration_remaining_norm` | remaining minimum hold time | `s` | `{"divisor_ref":"skill_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 35 | `skill_interruptible_now` | current skill may be interrupted | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 36 | `skill_has_target` | current skill has typed target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 37 | `skill_target_still_believed_valid` | current target remains valid in Belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 38 | `last_skill_result_success` | last terminal result | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 39 | `last_skill_result_failure` | last terminal result | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 40 | `personality_aggression` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 41 | `personality_courage` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 42 | `personality_curiosity` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 43 | `personality_loyalty` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 44 | `personality_sociability` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 45 | `personality_impulsivity` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 46 | `personality_patience` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 47 | `personality_vigilance` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 48 | `personality_altruism` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 49 | `personality_rule_adherence` | NPC profile | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 50 | `emotion_fear` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 51 | `emotion_anger` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 52 | `emotion_suspicion` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 53 | `emotion_curiosity` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 54 | `emotion_tension` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 55 | `emotion_affection` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 56 | `emotion_confusion` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 57 | `emotion_confidence` | authoritative event-driven state, read-only to policy | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 58 | `relationship_affinity` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 59 | `relationship_trust` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 60 | `relationship_respect` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 61 | `relationship_fear` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 62 | `relationship_debt` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 63 | `relationship_suspicion` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 64 | `relationship_loyalty` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 65 | `relationship_hostility` | relationship to primary social subject | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 66 | `role_combatant` | role attribute, not unseen Role ID | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 67 | `role_guard` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 68 | `role_civilian` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 69 | `role_companion` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 70 | `role_support` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 71 | `role_authority_level` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 72 | `role_social_authority` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 73 | `role_territory_ownership` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 74 | `role_mission_importance` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 75 | `role_risk_tolerance` | role attribute | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 76 | `goal_type_None` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 77 | `goal_type_IdleObserve` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 78 | `goal_type_InvestigateDisturbance` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 79 | `goal_type_EnforceBoundary` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 80 | `goal_type_CombatEngage` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 81 | `goal_type_Disengage` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 82 | `goal_type_Escort` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 83 | `goal_type_Reserved` | active goal type one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 84 | `goal_phase_None` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 85 | `goal_phase_Observe` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 86 | `goal_phase_Orient` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 87 | `goal_phase_Navigate` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 88 | `goal_phase_Interact` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 89 | `goal_phase_Search` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 90 | `goal_phase_Resolve` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 91 | `goal_phase_Return` | active goal phase one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 92 | `goal_priority_norm` | active goal priority uint8 / 255 | `ratio` | `{"divisor_ref":"goal_priority_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 93 | `goal_time_in_phase_norm` | time since phase entry | `s` | `{"divisor_ref":"goal_phase_time_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 94 | `goal_deadline_remaining_norm` | remaining authoritative deadline; 1 when no deadline | `s` | `{"divisor_ref":"goal_deadline_max_s","max":1.0,"min":0.0,"sentinel":"no_deadline","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"no_deadline"}` | `{}` |
| 95 | `goal_progress_norm` | goal-defined non-revision progress | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 96 | `goal_interruptible` | active phase interruptibility permits ordinary preemption | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 97 | `goal_has_primary_target` | active goal owns a typed target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 98 | `allowed_skill_fraction` | allowed skill count / 16 | `ratio` | `{"divisor_ref":"skill_count","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 99 | `forbidden_skill_fraction` | forbidden skill count / 16 | `ratio` | `{"divisor_ref":"skill_count","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 100 | `world_safe_zone` | authoritative zone flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 101 | `world_restricted_zone` | authoritative zone flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 102 | `world_indoors` | environment flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 103 | `world_combat_allowed` | authoritative rule flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 104 | `world_perceived_ally_count_norm` | count from Belief | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 105 | `world_perceived_hostile_count_norm` | count from Belief | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 106 | `world_light_level_norm` | environment sample available to NPC | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 107 | `world_crowd_density_norm` | perceived local density | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 108 | `recent_sound_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 109 | `recent_sight_change_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 110 | `recent_damage_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 111 | `recent_skill_failure_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 112 | `recent_target_switch_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 113 | `recent_warning_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 114 | `recent_reservation_conflict_count_norm` | valid events in 10-second buffer | `count` | `{"divisor_ref":"count_max","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 115 | `event_buffer_fill_ratio` | valid event slots / 12 | `ratio` | `{"divisor_ref":"event_slots","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 116 | `reserved_116` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 117 | `reserved_117` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 118 | `reserved_118` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 119 | `reserved_119` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 120 | `reserved_120` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 121 | `reserved_121` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 122 | `reserved_122` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 123 | `reserved_123` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 124 | `reserved_124` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 125 | `reserved_125` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 126 | `reserved_126` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 127 | `reserved_127` | reserved; must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### B.3 target_features common

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `relative_position_x` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `relative_position_y` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `relative_position_z` | perceived target position in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `distance_3d_norm` | distance to perceived position | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `distance_planar_norm` | planar distance to perceived position | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `log_distance_norm` | log distance | `cm` | `{"denominator_ref":"spatial_max_cm","input_max_ref":"spatial_max_cm","input_min":0.0,"type":"log1p_ratio"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `bearing_sin` | NPC-local bearing | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `bearing_cos` | NPC-local bearing | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `elevation_sin` | NPC-local elevation | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `elevation_cos` | NPC-local elevation | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `relative_velocity_x` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `relative_velocity_y` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `relative_velocity_z` | belief-derived velocity, never hidden Actor velocity | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `closing_speed_norm` | positive means approaching | `cm/s` | `{"divisor_ref":"speed_max_cm_s","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `path_distance_norm` | navigation estimate to believed position | `cm` | `{"divisor_ref":"path_distance_max_cm","max":1.0,"min":0.0,"sentinel":"invalid","sentinel_value":0.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":0.0,"policy":"sentinel","sentinel":"invalid"}` | `{}` |
| 15 | `path_reachable_belief` | path query to believed snapshot position | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `belief_age_norm` | now - observed_at | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `belief_confidence` | position/state confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 18 | `source_sight` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `source_hearing` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `source_last_known` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `source_shared` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `source_scripted` | Belief source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `position_valid` | perceived/snapshot position is valid | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 24 | `visible_now` | currently perceived by sight | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 25 | `line_of_sight_belief` | LOS query against believed/currently perceived target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 26 | `sight_strength` | sensor strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 27 | `visible_duration_norm` | continuous visibility duration | `s` | `{"divisor_ref":"visible_duration_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 28 | `heard_recently` | valid hearing event associated with target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 29 | `hearing_strength` | normalized loudness/strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 30 | `time_since_seen_norm` | time since last sight; 1 if never | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"sentinel":"never","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"never"}` | `{}` |
| 31 | `time_since_heard_norm` | time since last hearing; 1 if never | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"sentinel":"never","sentinel_value":1.0,"type":"sentinel_divide_clamp"}` | `[0.0,1.0]` | `{"encoded_value":1.0,"policy":"sentinel","sentinel":"never"}` | `{}` |

### B.4 event_features

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `age_norm` | now - event time | `s` | `{"divisor_ref":"event_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `strength` | event strength | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `confidence` | event confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `relative_position_x` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `relative_position_y` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `relative_position_z` | event snapshot in NPC-local frame | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":-1.0,"type":"divide_clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `distance_norm` | distance to event snapshot | `cm` | `{"divisor_ref":"spatial_max_cm","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `bearing_sin` | event bearing | `rad` | `{"function":"sin","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `bearing_cos` | event bearing | `rad` | `{"function":"cos","input_unit":"radian","type":"trigonometric"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `source_sight` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `source_hearing` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `source_damage` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `source_scripted` | event source one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `result_success` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `result_failure` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `result_interrupted` | skill result one-hot | `one-hot` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 16 | `urgent` | event urgency | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 17 | `target_present_in_current_slots` | stable handle remapped to current slot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 18 | `same_as_current_skill_target` | handle equality | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 19 | `same_goal_revision` | event goal revision equals current | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 20 | `magnitude_norm` | event-specific magnitude | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 21 | `duration_norm` | event-specific duration | `s` | `{"divisor_ref":"event_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 22 | `reserved_22` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 23 | `reserved_23` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### B.5 candidate_pair_features

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `same_as_current_skill` | candidate skill equals running skill | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `same_as_current_target` | typed handle equals running target | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `target_present` | target slot is valid; NoTarget is valid | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `target_visible_now` | copied from target belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `target_position_confidence` | copied from target belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `target_age_norm` | copied from target belief | `s` | `{"divisor_ref":"target_age_max_s","max":1.0,"min":0.0,"type":"divide_clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `distance_norm` | copied from target feature | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `path_distance_norm` | computed to believed snapshot | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `path_reachable_belief` | computed to believed snapshot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `skill_requires_los` | Skill Registry metadata | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `los_satisfied_belief` | computed against currently permitted belief | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `skill_requires_resource` | Skill Registry metadata | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `resource_available_belief` | latest allowed availability snapshot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `skill_allowed_by_goal` | Goal contract | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `target_kind_allowed` | Skill Registry matrix | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `default_parameter_norm` | Skill Registry default primary parameter | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

## C. Target Payload [32:47]

### C.NoTarget

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `zero_0` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 1 | `zero_1` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 2 | `zero_2` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 3 | `zero_3` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 4 | `zero_4` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 5 | `zero_5` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 6 | `zero_6` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 7 | `zero_7` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 8 | `zero_8` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 9 | `zero_9` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 10 | `zero_10` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 11 | `zero_11` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 12 | `zero_12` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 13 | `zero_13` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 14 | `zero_14` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |
| 15 | `zero_15` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.Entity

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `alive_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `armed_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `attacking_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `health_estimate` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `health_uncertainty` | estimate interval width | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `threat_estimate` | perception/classifier estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `interactable` | observed/known affordance | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `same_faction_probability` | Belief estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `affinity` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `trust` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `fear` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `hostility` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `debt` | relationship [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `suspicion` | relationship [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `current_action_confidence` | observed action classifier confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `identity_confidence` | entity attribution confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.SoundEvent

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `loudness` | normalized loudness | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `danger_estimate` | sensor/event semantic estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `attribution_confidence` | confidence in source attribution | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `repetition_norm` | repeat count / 8 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `class_footstep` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `class_weapon` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `class_explosion` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `class_voice` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `class_impact` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `class_door` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `class_vehicle` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `class_other` | sound class one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `source_moving_probability` | event inference | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `occluded_probability` | hearing propagation estimate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `ttl_remaining_norm` | remaining TTL / event max TTL | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.LastKnownPosition

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `subject_is_player` | Belief semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `subject_hostile_probability` | snapshot belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `subject_armed_probability` | snapshot belief | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `subject_alive_probability_at_observation` | snapshot belief; not updated from hidden truth | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `motion_direction_sin` | last observed motion | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `motion_direction_cos` | last observed motion | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `observed_speed_norm` | last observed speed / 1200 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `reason_sight_lost` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `reason_shared` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `reason_scripted` | snapshot reason one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `goal_primary_target` | owned by active goal | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `search_radius_norm` | search radius / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `confidence_decay_rate_norm` | configured decay rate | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `ttl_remaining_norm` | remaining snapshot TTL | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `subject_identity_confidence` | snapshot attribution confidence | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.CoverSlot

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `cover_quality` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `exposure_reduction` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `flank_risk` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `distance_to_peek_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `occupancy_ratio` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `available_belief` | latest known availability | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `reserved_by_self` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `resource_generation_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `low_cover` | one-hot/flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `high_cover` | one-hot/flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `left_peek` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `right_peek` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `destructible_probability` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `lease_required` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `resource_age_norm` | availability revision age / 10s | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.SmartObject

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `availability_belief` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `capacity_norm` | capacity / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `occupancy_ratio` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `interaction_duration_norm` | seconds / 30 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `requires_item` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `use_type_door` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `use_type_console` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `use_type_pickup` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `use_type_heal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `use_type_vehicle` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `use_type_social` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `use_type_traversal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `use_type_other` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `resource_generation_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `resource_age_norm` | availability revision age / 10s | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |

### C.Waypoint

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `goal_primary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `goal_secondary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `sequence_progress` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `wait_duration_norm` | seconds / 30 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `desired_facing_sin` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `desired_facing_cos` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `patrol_waypoint` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `return_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `search_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `escape_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `formation_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `scripted_point` | semantic flag | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `path_index_norm` | index / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 13 | `loop_flag` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `arrival_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

### C.WorldPosition

| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |
|---:|---|---|---|---|---|---|---|
| 0 | `goal_primary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 1 | `goal_secondary` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 2 | `safe_zone_probability` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 3 | `hazard_norm` | [0,1] | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 4 | `search_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 5 | `arrival_radius_norm` | cm / 5000 | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 6 | `desired_facing_sin` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 7 | `desired_facing_cos` | [-1,1] | `ratio` | `{"max":1.0,"min":-1.0,"type":"clamp"}` | `[-1.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 8 | `source_goal` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 9 | `source_script` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 10 | `source_shared_knowledge` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 11 | `source_player_ping` | one-hot | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 12 | `immutable_flag` | must be 1 in V1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"occupied_required_value":1.0,"policy":"padding_zero","value":0.0}` | `{"occupied_required_value":1.0}` |
| 13 | `ttl_remaining_norm` | remaining TTL / configured max | `ratio` | `{"max":1.0,"min":0.0,"type":"clamp"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 14 | `authority_valid` | 0 or 1 | `bool` | `{"type":"boolean"}` | `[0.0,1.0]` | `{"policy":"constant","value":0.0}` | `{}` |
| 15 | `reserved` | must be zero | `none` | `{"type":"constant","value":0.0}` | `[0.0,0.0]` | `{"policy":"constant","value":0.0}` | `{"must_equal":0.0}` |

## D. Skill·Goal·Hash 계약

### D.1 Skill Parameter

| Skill ID | Skill | Slot | Parameter | Active | Unit | Min | Max | Default |
|---:|---|---:|---|---:|---|---:|---:|---:|
| 0 | `Idle` | 0 | `duration` | 1 | `second` | 0.5 | 5.0 | 1.0 |
| 0 | `Idle` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 0 | `Idle` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 0 | `Idle` | 3 | `intensity` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 0 | `duration` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 1 | `ContinueCurrentAction` | 3 | `intensity` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 0 | `duration` | 1 | `second` | 0.25 | 3.0 | 1.0 |
| 2 | `LookAt` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 2 | `LookAt` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 3 | `TurnTo` | 0 | `duration` | 1 | `second` | 0.25 | 2.0 | 0.75 |
| 3 | `TurnTo` | 1 | `speed` | 1 | `degree_per_second` | 90.0 | 720.0 | 360.0 |
| 3 | `TurnTo` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 3 | `TurnTo` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 4 | `Approach` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 4 | `Approach` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 350.0 |
| 4 | `Approach` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 500.0 | 200.0 |
| 4 | `Approach` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 5 | `KeepDistance` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 5 | `KeepDistance` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 300.0 |
| 5 | `KeepDistance` | 2 | `preferred_distance` | 1 | `centimeter` | 200.0 | 1000.0 | 500.0 |
| 5 | `KeepDistance` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 6 | `RetreatFrom` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 3.0 |
| 6 | `RetreatFrom` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 650.0 | 400.0 |
| 6 | `RetreatFrom` | 2 | `preferred_distance` | 1 | `centimeter` | 300.0 | 1500.0 | 700.0 |
| 6 | `RetreatFrom` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 7 | `Follow` | 0 | `duration` | 1 | `second` | 0.5 | 10.0 | 4.0 |
| 7 | `Follow` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 600.0 | 350.0 |
| 7 | `Follow` | 2 | `preferred_distance` | 1 | `centimeter` | 150.0 | 700.0 | 350.0 |
| 7 | `Follow` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 8 | `Investigate` | 0 | `duration` | 1 | `second` | 1.0 | 12.0 | 5.0 |
| 8 | `Investigate` | 1 | `speed` | 1 | `centimeter_per_second` | 100.0 | 500.0 | 280.0 |
| 8 | `Investigate` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 1200.0 | 400.0 |
| 8 | `Investigate` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.6 |
| 9 | `SearchArea` | 0 | `duration` | 1 | `second` | 3.0 | 20.0 | 8.0 |
| 9 | `SearchArea` | 1 | `speed` | 1 | `centimeter_per_second` | 80.0 | 400.0 | 220.0 |
| 9 | `SearchArea` | 2 | `preferred_distance` | 1 | `centimeter` | 200.0 | 2000.0 | 700.0 |
| 9 | `SearchArea` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.6 |
| 10 | `Greet` | 0 | `duration` | 1 | `second` | 1.0 | 5.0 | 2.0 |
| 10 | `Greet` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 10 | `Greet` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 10 | `Greet` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.5 |
| 11 | `Warn` | 0 | `duration` | 1 | `second` | 1.0 | 5.0 | 2.0 |
| 11 | `Warn` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 11 | `Warn` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 11 | `Warn` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 12 | `CallForHelp` | 0 | `duration` | 1 | `second` | 1.0 | 4.0 | 2.0 |
| 12 | `CallForHelp` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 12 | `CallForHelp` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 12 | `CallForHelp` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.8 |
| 13 | `TakeCover` | 0 | `duration` | 1 | `second` | 1.0 | 10.0 | 4.0 |
| 13 | `TakeCover` | 1 | `speed` | 1 | `centimeter_per_second` | 150.0 | 650.0 | 400.0 |
| 13 | `TakeCover` | 2 | `preferred_distance` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 13 | `TakeCover` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |
| 14 | `Flee` | 0 | `duration` | 1 | `second` | 1.0 | 15.0 | 6.0 |
| 14 | `Flee` | 1 | `speed` | 1 | `centimeter_per_second` | 200.0 | 700.0 | 500.0 |
| 14 | `Flee` | 2 | `preferred_distance` | 1 | `centimeter` | 500.0 | 3000.0 | 1500.0 |
| 14 | `Flee` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.9 |
| 15 | `Attack` | 0 | `duration` | 1 | `second` | 0.2 | 5.0 | 1.0 |
| 15 | `Attack` | 1 | `speed` | 0 | `none` | 0.0 | 0.0 | 0.0 |
| 15 | `Attack` | 2 | `preferred_distance` | 1 | `centimeter` | 100.0 | 2000.0 | 600.0 |
| 15 | `Attack` | 3 | `intensity` | 1 | `ratio` | 0.0 | 1.0 | 0.7 |

### D.2 Goal Registry

| Goal ID | Goal | Initial phase | Priority | Source | Interruptibility | Resume |
|---:|---|---|---:|---|---|---|
| 1 | `IdleObserve` | `Observe` | 10 | `Routine` | `Always` | `ResumeSamePhase` |
| 2 | `InvestigateDisturbance` | `Orient` | 120 | `Social` | `PhaseBoundary` | `ResumeSamePhase` |
| 3 | `EnforceBoundary` | `Observe` | 160 | `Quest` | `PhaseBoundary` | `ResumeSamePhase` |
| 4 | `CombatEngage` | `Orient` | 220 | `Combat` | `EmergencyOnly` | `RestartPhase` |
| 5 | `Disengage` | `-` | - | `-` | `-` | `-` |
| 6 | `Escort` | `-` | - | `-` | `-` | `-` |
| 7 | `Reserved` | `-` | - | `-` | `-` | `-` |

### D.3 Goal Transition Trigger

| Goal | Phase | Order | Typed trigger | Guard | Destination | Effect |
|---|---|---:|---|---|---|---|
| `IdleObserve` | `Observe` | 0 | `{"event_type":"SoundHeard","kind":"event"}` | `valid_disturbance_target` | `{"to_goal":"InvestigateDisturbance"}` | `request_new_goal` |
| `IdleObserve` | `Observe` | 1 | `{"event_type":"SightAcquired","kind":"event"}` | `social_subject` | `{"to_phase":"Observe"}` | `remain_and_replan` |
| `InvestigateDisturbance` | `Orient` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `orientation_complete` | `{"to_phase":"Navigate"}` | `-` |
| `InvestigateDisturbance` | `Orient` | 1 | `{"event_type":"TargetInvalidated","kind":"event"}` | `no_valid_snapshot` | `{"terminal":"Failed"}` | `-` |
| `InvestigateDisturbance` | `Orient` | 2 | `{"after_seconds":2.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"terminal":"Failed"}` | `-` |
| `InvestigateDisturbance` | `Navigate` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `arrived_at_snapshot` | `{"to_phase":"Search"}` | `-` |
| `InvestigateDisturbance` | `Navigate` | 1 | `{"event_type":"SkillFailed","kind":"event"}` | `PathUnavailable` | `{"terminal":"Failed"}` | `-` |
| `InvestigateDisturbance` | `Navigate` | 2 | `{"event_type":"SightAcquired","kind":"event"}` | `subject_identified` | `{"to_phase":"Resolve"}` | `-` |
| `InvestigateDisturbance` | `Navigate` | 3 | `{"after_seconds":15.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"terminal":"Failed"}` | `-` |
| `InvestigateDisturbance` | `Search` | 0 | `{"event_type":"SightAcquired","kind":"event"}` | `subject_identified` | `{"to_phase":"Resolve"}` | `-` |
| `InvestigateDisturbance` | `Search` | 1 | `{"event_type":"SkillSucceeded","kind":"event"}` | `search_budget_exhausted` | `{"to_phase":"Return"}` | `-` |
| `InvestigateDisturbance` | `Search` | 2 | `{"after_seconds":8.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"to_phase":"Return"}` | `-` |
| `InvestigateDisturbance` | `Resolve` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `resolution_complete` | `{"to_phase":"Return"}` | `-` |
| `InvestigateDisturbance` | `Resolve` | 1 | `{"event_type":"TargetInvalidated","kind":"event"}` | `no_valid_belief` | `{"to_phase":"Search"}` | `-` |
| `InvestigateDisturbance` | `Return` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `at_return_target` | `{"terminal":"Succeeded"}` | `-` |
| `InvestigateDisturbance` | `Return` | 1 | `{"event_type":"SkillFailed","kind":"event"}` | `PathUnavailable` | `{"terminal":"Failed"}` | `-` |
| `EnforceBoundary` | `Observe` | 0 | `{"event_type":"SightAcquired","kind":"event"}` | `boundary_intruder_is_primary_social_subject` | `{"to_phase":"Interact"}` | `-` |
| `EnforceBoundary` | `Observe` | 1 | `{"event_type":"TargetInvalidated","kind":"event"}` | `no_boundary_intruder` | `{"to_phase":"Return"}` | `-` |
| `EnforceBoundary` | `Observe` | 2 | `{"after_seconds":4.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"terminal":"Failed"}` | `-` |
| `EnforceBoundary` | `Interact` | 0 | `{"event_type":"WarningIssued","kind":"event"}` | `warning_delivered` | `{"to_phase":"Resolve"}` | `-` |
| `EnforceBoundary` | `Interact` | 1 | `{"event_type":"SkillSucceeded","kind":"event"}` | `subject_complied_before_warning` | `{"to_phase":"Return"}` | `-` |
| `EnforceBoundary` | `Interact` | 2 | `{"event_type":"TargetInvalidated","kind":"event"}` | `subject_left_boundary` | `{"to_phase":"Return"}` | `-` |
| `EnforceBoundary` | `Interact` | 3 | `{"after_seconds":6.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"to_phase":"Resolve"}` | `-` |
| `EnforceBoundary` | `Resolve` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `boundary_resolved` | `{"to_phase":"Return"}` | `-` |
| `EnforceBoundary` | `Resolve` | 1 | `{"event_type":"WarningIgnored","kind":"event"}` | `escalation_allowed` | `{"to_phase":"Resolve"}` | `remain_and_replan` |
| `EnforceBoundary` | `Resolve` | 2 | `{"event_type":"Damaged","kind":"event"}` | `combat_goal_allowed` | `{"to_goal":"CombatEngage"}` | `request_new_goal` |
| `EnforceBoundary` | `Resolve` | 3 | `{"event_type":"TargetInvalidated","kind":"event"}` | `subject_no_longer_relevant` | `{"to_phase":"Return"}` | `-` |
| `EnforceBoundary` | `Return` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `at_return_target` | `{"terminal":"Succeeded"}` | `-` |
| `EnforceBoundary` | `Return` | 1 | `{"event_type":"SkillFailed","kind":"event"}` | `PathUnavailable` | `{"terminal":"Failed"}` | `-` |
| `CombatEngage` | `Orient` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `combat_target_aligned` | `{"to_phase":"Resolve"}` | `-` |
| `CombatEngage` | `Orient` | 1 | `{"event_type":"SightLost","kind":"event"}` | `has_last_known_position` | `{"to_phase":"Search"}` | `-` |
| `CombatEngage` | `Orient` | 2 | `{"event_type":"TargetInvalidated","kind":"event"}` | `no_valid_combat_target` | `{"to_phase":"Return"}` | `-` |
| `CombatEngage` | `Resolve` | 0 | `{"event_type":"SightLost","kind":"event"}` | `has_last_known_position` | `{"to_phase":"Search"}` | `-` |
| `CombatEngage` | `Resolve` | 1 | `{"event_type":"SkillSucceeded","kind":"event"}` | `combat_resolved` | `{"to_phase":"Return"}` | `-` |
| `CombatEngage` | `Resolve` | 2 | `{"event_type":"TargetInvalidated","kind":"event"}` | `combat_target_invalid` | `{"to_phase":"Return"}` | `-` |
| `CombatEngage` | `Resolve` | 3 | `{"event_type":"ReservationLost","kind":"event"}` | `cover_resource_lost` | `{"to_phase":"Resolve"}` | `remain_and_replan` |
| `CombatEngage` | `Search` | 0 | `{"event_type":"SightAcquired","kind":"event"}` | `combat_target_reacquired` | `{"to_phase":"Resolve"}` | `-` |
| `CombatEngage` | `Search` | 1 | `{"event_type":"SkillSucceeded","kind":"event"}` | `search_budget_exhausted` | `{"to_phase":"Return"}` | `-` |
| `CombatEngage` | `Search` | 2 | `{"after_seconds":5.0,"kind":"timer","timer_id":"phase_timeout"}` | `phase_timeout` | `{"to_phase":"Return"}` | `-` |
| `CombatEngage` | `Return` | 0 | `{"event_type":"SkillSucceeded","kind":"event"}` | `combat_exit_complete` | `{"terminal":"Succeeded"}` | `-` |
| `CombatEngage` | `Return` | 1 | `{"event_type":"SkillFailed","kind":"event"}` | `PathUnavailable` | `{"terminal":"Failed"}` | `-` |

### D.4 Goal Trigger·Timer Lifecycle

| Field | Value |
|---|---|
| `allowed_kinds[0]` | `"event"` |
| `allowed_kinds[1]` | `"timer"` |
| `allowed_kinds[2]` | `"lifecycle"` |
| `allowed_kinds[3]` | `"server_control"` |
| `active_v1_kinds[0]` | `"event"` |
| `active_v1_kinds[1]` | `"timer"` |
| `legacy_event_field_forbidden` | `true` |
| `timer_id_scope` | `"goal_phase"` |
| `timer_clock` | `"server_monotonic_world_seconds"` |
| `timer_duration_unit` | `"second"` |
| `timer_arm_on.phase_entry` | `"full_after_seconds"` |
| `timer_arm_on.resume_same_phase` | `"stored_remaining_ms"` |
| `timer_arm_on.restart_phase_resume` | `"full_after_seconds"` |
| `timer_suspend_policy` | `"pause_and_store_remaining_ms"` |
| `timer_cancel_on` | `"phase_exit_or_terminal"` |
| `timer_expiry_policy` | `"enqueue_once_then_evaluate_in_transition_order"` |
| `absolute_goal_deadline_while_suspended` | `"continues"` |
| `save_load_policy` | `"persist_timer_id_contract_duration_remaining_ms_and_resume_policy"` |
| `wall_clock_forbidden` | `true` |
| `current_v1_counts.event` | `35` |
| `current_v1_counts.timer` | `6` |
| `reserved_kinds.lifecycle` | `"reserved_until_field_contract_is_defined"` |
| `reserved_kinds.server_control` | `"reserved_until_field_contract_is_defined"` |

### D.5 Goal Revision

| Field | Value |
|---|---|
| `type` | `"uint64_monotonic_per_npc"` |
| `increase_on[0]` | `"active_goal_changed"` |
| `increase_on[1]` | `"goal_suspended"` |
| `increase_on[2]` | `"goal_resumed"` |
| `increase_on[3]` | `"goal_aborted"` |
| `increase_on[4]` | `"phase_changed"` |
| `increase_on[5]` | `"authoritative_primary_target_changed"` |
| `increase_on[6]` | `"allowed_skill_set_changed"` |
| `increase_on[7]` | `"forbidden_skill_set_changed"` |
| `increase_on[8]` | `"deadline_contract_changed"` |
| `increase_on[9]` | `"interruptibility_changed"` |
| `increase_on[10]` | `"resume_policy_changed"` |
| `do_not_increase_on[0]` | `"progress_value_changed"` |
| `do_not_increase_on[1]` | `"per_frame_timer_changed"` |
| `do_not_increase_on[2]` | `"belief_revision_changed_without_goal_contract_change"` |
| `do_not_increase_on[3]` | `"event_buffer_append"` |

### D.6 Hash: candidate_set_hash

- Algorithm: `SHA-256`
- Byte order: `little`

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"ANPCSET2"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `schema_source_sha256` | `bytes[32]` | `{}` |
| 3 | `target_slot_count` | `uint8` | `{"value_ref":"total_target_slots"}` |
| 4 | `target_handles` | `target_handle[17]` | `{"field_order":["kind:uint8","stable_id:uint64","generation:uint32","revision:uint64"]}` |
| 5 | `target_mask` | `bitset` | `{"bit_count":17,"bit_order":"LSB-first","byte_count":3,"unused_high_bits":"zero"}` |
| 6 | `candidate_mask` | `bitset` | `{"bit_count":272,"bit_order":"LSB-first","byte_count":34,"unused_high_bits":"none"}` |

### D.7 Hash: decision_contract_hash

- Algorithm: `SHA-256`
- Byte order: `little`

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"ANPCDEC2"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `schema_source_sha256` | `bytes[32]` | `{}` |
| 3 | `skill_registry_sha256` | `bytes[32]` | `{}` |
| 4 | `goal_registry_sha256` | `bytes[32]` | `{}` |
| 5 | `model_sha256` | `bytes[32]` | `{}` |
| 6 | `normalization_contract_sha256` | `bytes[32]` | `{}` |
| 7 | `slotter_contract_sha256` | `bytes[32]` | `{}` |
| 8 | `postprocess_contract_sha256` | `bytes[32]` | `{}` |
| 9 | `calibration_ood_asset_sha256` | `bytes[32]` | `{}` |

### D.8 Normalizer 의미 규칙

```json
{
  "clamp_bounds_order": "min_lte_max",
  "constant_and_sentinel_value_must_fit_valid_range": true,
  "constant_missing_value_must_equal_normalizer_constant": true,
  "constraint_and_missing_occupied_value_must_match": true,
  "divisor_and_referenced_scale_must_be_positive": true,
  "log1p_input_domain": {
    "denominator_must_be_positive": true,
    "exclusive_min": -1.0
  },
  "missing_contract_must_match_normalizer": true,
  "must_equal_requires_constant_normalizer": true,
  "must_equal_requires_matching_missing_value": true,
  "must_equal_requires_singleton_valid_range": true,
  "normalizer_output_must_fit_valid_range": true,
  "numeric_values_must_be_finite": true,
  "padding_zero_value_must_fit_valid_range": true,
  "valid_range_order": "min_lte_max"
}
```

<!-- END AUTO-GENERATED SCHEMA CONTRACT -->

## Goal Runtime 구현 상태 안내 — manual

Generated D.2–D.5는 Goal Registry `1.1.0`의 구조·순서·timer lifecycle·revision을 정확히 노출한다. 이것은 Runtime 구현 증거가 아니다.

| Gate | 현재 상태 |
|---|---|
| Authority→generated Python/C++ | PASS — Goal `4`, Goal/phase `14`, transition `41 = 35 event + 6 timer` |
| Consumer provenance | PASS — authority commit `2770b4a5a3aebd430420e5b330441aa044cc7db5`, generated header/hash lock과 sync `--check` |
| Contract Dispatcher·Timer Core | RED — `GoalFsmRuntimeTests.cpp`만 존재, Runtime `.h/.cpp`와 Timer Component 없음 |
| Production Integration | HOLD — Knowledge(코드·Schema: `Belief`)/Goal/Target의 종류와 식별 정보(코드: `Typed Target`) producer와 shipping owner 없음 |
| Gameplay Goal FSM | HOLD — 29 guard·2 effect semantics, 전체 arbitration/save archive 없음 |

Timer snapshot과 restore race의 실행 계약은 [세부 기술 요구사항 §5.9](technical-requirements.md#59-typed-goal-trigger와-phase-timeout)가 소유한다. 제한 Core는 format/Registry hash/Goal·phase generation/revision/timer identity에 결속된 versioned snapshot과 호출 시점의 비영속 `expected_current_token` CAS를 사용한다. mismatch는 live state를 바꾸지 않으며, expiry는 `phase_timeout` guard를 자동 true로 만들지 않는다.

Timeout `2/15/8/4/6/5초`는 정상 completion의 대체가 아니라 event 누락 fallback이다. 같은 World의 authoritative game-time을 사용하므로 World pause 중 멈추고 time dilation을 따른다.

## Boss Pattern 확장 사용 안내

Boss Pattern 계약은 공통 `Attack(Entity)` Commit 이후에만 사용하는 별도 32행 Pattern Candidate 공간을 정의한다. 일반 NPC의 272 Candidate layout과 index는 바뀌지 않는다.

<!-- BEGIN AUTO-GENERATED BOSS PATTERN CONTRACT -->

# BP. AUTO-GENERATED Boss Pattern Selector 계약

> 이 구간은 `contracts/current/boss_pattern_contract_v1.yaml`에서 자동 생성된다. 수동 편집하지 않는다.

- Generator: `0.4.6`
- Contract version: `1.0.0`
- Contract revision: `2.0.0-rc5`
- Boss Pattern Contract SHA-256: `e4f828c114fcc5db1cb04b5d0a6e2b3d29dada7e45c60a3dd18c674baa78c789`

## BP.1 공통 Candidate 보존

| Skill | Target Slots | 공통 Candidate | Boss Pattern Slots |
|---:|---:|---:|---:|
| 16 | 17 | 272 | 32 |

Boss Pattern Slot은 `Attack(Entity)` Commit 이후 사용하는 별도 namespace다.
hash 직렬화 전에 occupied row 1개 이상, occupied `pattern_id` 오름차순·trailing padding·padding mask=false를 검증한다.

## BP.2 Tensor

| Name | Shape | dtype |
|---|---|---|
| `pattern_context` | `["B",32]` | `float32` |
| `pattern_features` | `["B",32,24]` | `float32` |
| `pattern_pair_features` | `["B",32,16]` | `float32` |
| `pattern_ids` | `["B",32]` | `int64` |
| `pattern_mask` | `["B",32]` | `bool` |
| `pattern_raw_scores` | `["B",32]` | `float32` |
| `pattern_parameter_proposals` | `["B",32,4]` | `float32` |

### BP.2.1 Feature 정규화

#### `pattern_context`

| Index | Field | Source | Normalizer | Range | Divisor |
|---:|---|---|---|---|---:|
| 0 | `boss_health_ratio` | `observable_authoritative_self_state` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 1 | `boss_stamina_ratio` | `observable_authoritative_self_state` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 2 | `boss_posture_ratio` | `observable_authoritative_self_state` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 3 | `target_health_ratio_estimate` | `permitted_belief_snapshot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 4 | `target_distance_planar` | `locked_attack_target_snapshot` | `distance_cm` | `[0.0,1.0]` | 10000.0 |
| 5 | `target_distance_3d` | `locked_attack_target_snapshot` | `distance_cm` | `[0.0,1.0]` | 10000.0 |
| 6 | `target_bearing_sin` | `locked_attack_target_snapshot` | `signed_unit` | `[-1.0,1.0]` | 1.0 |
| 7 | `target_bearing_cos` | `locked_attack_target_snapshot` | `signed_unit` | `[-1.0,1.0]` | 1.0 |
| 8 | `target_elevation_sin` | `locked_attack_target_snapshot` | `signed_unit` | `[-1.0,1.0]` | 1.0 |
| 9 | `target_elevation_cos` | `locked_attack_target_snapshot` | `signed_unit` | `[-1.0,1.0]` | 1.0 |
| 10 | `target_relative_speed` | `permitted_belief_snapshot` | `signed_speed_cm_s` | `[-1.0,1.0]` | 2000.0 |
| 11 | `target_approach_velocity` | `permitted_belief_snapshot` | `signed_speed_cm_s` | `[-1.0,1.0]` | 2000.0 |
| 12 | `target_lateral_velocity` | `permitted_belief_snapshot` | `signed_speed_cm_s` | `[-1.0,1.0]` | 2000.0 |
| 13 | `has_line_of_sight` | `permitted_belief_snapshot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 14 | `path_available` | `authoritative_path_query` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 15 | `arena_edge_risk` | `authoritative_arena_query` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 16 | `boss_phase_normalized` | `authoritative_boss_phase` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 17 | `elapsed_encounter_time` | `server_monotonic_time` | `encounter_elapsed_s` | `[0.0,1.0]` | 1800.0 |
| 18 | `elapsed_since_last_pattern` | `server_monotonic_time` | `cooldown_seconds` | `[0.0,1.0]` | 120.0 |
| 19 | `same_pattern_streak_ratio` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 20 | `recent_fast_pattern_ratio` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 21 | `recent_heavy_pattern_ratio` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 22 | `recent_gap_closer_ratio` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 23 | `player_recent_damage_ratio` | `observable_committed_combat_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 24 | `boss_recent_damage_ratio` | `authoritative_self_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 25 | `selection_boundary_pre_attack` | `selection_boundary_one_hot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 26 | `selection_boundary_branch_window` | `selection_boundary_one_hot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 27 | `selection_boundary_recovery_end` | `selection_boundary_one_hot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 28 | `previous_pattern_family_fast` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 29 | `previous_pattern_family_heavy` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 30 | `previous_pattern_family_gap_closer` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 31 | `target_health_estimate_confidence` | `permitted_belief_snapshot` | `ratio_01` | `[0.0,1.0]` | 1.0 |

#### `pattern_features`

| Index | Field | Source | Normalizer | Range | Divisor |
|---:|---|---|---|---|---:|
| 0 | `preferred_distance_min` | `pattern_data_asset` | `distance_cm` | `[0.0,1.0]` | 10000.0 |
| 1 | `preferred_distance_max` | `pattern_data_asset` | `distance_cm` | `[0.0,1.0]` | 10000.0 |
| 2 | `allowed_bearing_abs_max` | `pattern_data_asset` | `bearing_degrees` | `[0.0,1.0]` | 180.0 |
| 3 | `allowed_elevation_abs_max` | `pattern_data_asset` | `elevation_degrees` | `[0.0,1.0]` | 90.0 |
| 4 | `telegraph_duration` | `pattern_data_asset` | `pattern_duration_s` | `[0.0,1.0]` | 30.0 |
| 5 | `active_duration` | `pattern_data_asset` | `pattern_duration_s` | `[0.0,1.0]` | 30.0 |
| 6 | `recovery_duration` | `pattern_data_asset` | `pattern_duration_s` | `[0.0,1.0]` | 30.0 |
| 7 | `cooldown_duration` | `pattern_data_asset` | `cooldown_seconds` | `[0.0,1.0]` | 120.0 |
| 8 | `stamina_cost_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 9 | `startup_tracking_yaw_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 10 | `active_tracking_yaw_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 11 | `recovery_tracking_yaw_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 12 | `startup_tracking_speed_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 13 | `active_tracking_speed_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 14 | `area_pressure_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 15 | `gap_close_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 16 | `damage_pressure_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 17 | `posture_pressure_ratio` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 18 | `family_fast` | `pattern_data_asset_tag` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 19 | `family_heavy` | `pattern_data_asset_tag` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 20 | `family_gap_closer` | `pattern_data_asset_tag` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 21 | `family_area_control` | `pattern_data_asset_tag` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 22 | `branch_capable` | `pattern_data_asset` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 23 | `reserved_zero` | `constant_zero` | `constant_zero` | `[0.0,0.0]` | 1.0 |

#### `pattern_pair_features`

| Index | Field | Source | Normalizer | Range | Divisor |
|---:|---|---|---|---|---:|
| 0 | `distance_fit` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 1 | `bearing_fit` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 2 | `elevation_fit` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 3 | `line_of_sight_fit` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 4 | `phase_allowed` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 5 | `cooldown_ready` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 6 | `resource_ready` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 7 | `predecessor_allowed` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 8 | `branch_allowed` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 9 | `arena_safe` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 10 | `navigation_available` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 11 | `repetition_penalty_feature` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 12 | `timing_variety_feature` | `committed_pattern_history` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 13 | `target_motion_fit` | `permitted_belief_snapshot` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 14 | `selection_boundary_fit` | `deterministic_builder` | `ratio_01` | `[0.0,1.0]` | 1.0 |
| 15 | `reserved_zero` | `constant_zero` | `constant_zero` | `[0.0,0.0]` | 1.0 |

Padding: unoccupied `pattern_features`와 `pattern_pair_features` row는 정규화 후 전부 0, `pattern_id=invalid_pattern_id`, `pattern_mask=false`다.
Masked score는 ranking 전에 `-∞`로 바꾸고 parameter proposal은 무시한 뒤 log에서 0으로 고정한다.


## BP.3 제한된 Parameter 권한

| Index | Name | Decode | Authority |
|---:|---|---|---|
| 0 | `tracking_fraction` | `authored_tracking_limit * clamp01(x)` | `may_reduce_authored_maximum_only` |
| 1 | `telegraph_extension_fraction` | `telegraph_extension_max_s * clamp01(x)` | `extension_only` |
| 2 | `recovery_extension_fraction` | `recovery_extension_max_s * clamp01(x)` | `extension_only` |
| 3 | `reserved_zero` | `constant_zero` | `none` |

신경망 출력에서 금지: `damage`, `hitbox`, `active_window`, `root_motion`, `interruptibility`, `phase_transition`

## BP.4 Selection Boundary와 실행 잠금

| Phase | Rule |
|---|---|
| `ReadyToSelect` | `selection_allowed_until_successful_commit` |
| `PreAttackTurn` | `selection_locked` |
| `StartupTelegraph` | `selection_locked` |
| `Active` | `selection_locked` |
| `Recovery` | `selection_locked_except_authored_branch_window` |
| `BranchWindow` | `authored_successor_selection_only` |
| `Completed` | `next_tactical_or_pattern_selection_allowed` |
| `Interrupted` | `deterministic_cleanup_before_replan` |

Model selection source: `parent_attack_target_permitted_belief_snapshot`
Executor post-lock transform source: `authoritative_combat_targeting_policy_only`
Executor transform feedback to model: `false`
Executor transform may change Pattern: `false`
Pattern Commit authority: `server_authority_only`
Hitbox/Damage/Root Motion authority: `deterministic_server_combat_module`
Client inference Gameplay authority: `false`

## BP.5 Hard Mask 순서

1. `SlotOccupied`
2. `BossPhaseAllowed`
3. `AttackTargetIdentityAndGenerationValid`
4. `RangeAllowed`
5. `BearingAllowed`
6. `ElevationAllowed`
7. `LineOfSightSatisfied`
8. `CooldownReady`
9. `ResourceReservable`
10. `PredecessorAllowed`
11. `BranchAllowedAtBoundary`
12. `ArenaSafe`
13. `NavigationAvailable`
14. `AuthoredAssetsLoaded`
15. `SelectionBoundaryEligible`
16. `ExecutorUnlocked`
17. `ReservationAvailable`

## BP.6 Pattern Set·Data Asset

### BP.6.1 Pattern Set 필수 필드

- `pattern_set_id`
- `patterns`
- `safe_default_pattern_id`
- `utility_profile_reference`
- `optional_model_bundle_reference`

### BP.6.2 Pattern 필수 필드

- `pattern_id`
- `pattern_name`
- `pattern_family_tags`
- `allowed_boss_phases`
- `allowed_predecessor_pattern_ids`
- `allowed_successor_pattern_ids`
- `preferred_distance_cm`
- `allowed_bearing_degrees`
- `allowed_elevation_degrees`
- `requires_line_of_sight`
- `stamina_cost`
- `cooldown_seconds`
- `startup_telegraph_seconds`
- `active_seconds`
- `recovery_seconds`
- `telegraph_extension_max_s`
- `recovery_extension_max_s`
- `montage_reference`
- `montage_section`
- `root_motion_mode`
- `hitbox_window_reference`
- `damage_profile_reference`
- `phase_tracking_limits`
- `branch_windows`
- `interruptibility_allowlist`
- `interrupt_cleanup_policy`
- `arena_safety_policy`
- `navigation_policy`

### BP.6.3 Fallback 결정론

- zero valid rows: `ReturnPatternUnavailableToAttackSkillWithoutInferenceOrUtility`
- Utility tie-break: `adjusted_score_desc_then_pattern_id_asc`
- safe default source: `PatternSetDataAsset.safe_default_pattern_id`
- safe default constraint: `referenced_pattern_must_be_occupied_and_currently_valid`
- snapshot: `same_immutable_request_only`

## BP.7 Hash 계약

### BP.7.0 Pattern Asset Bundle Digest

- status: `pending_unreal_commandlet_and_python_parity`
- build owner: `BossPatternValidationCommandlet`
- Pattern Set ID digest input: `{"algorithm":"SHA-256","case_policy":"case_sensitive","empty_allowed":false,"input_bytes":"normalized_utf8_without_bom","source_type":"string","text_encoding":"UTF-8","unicode_normalization":"NFC","whitespace_policy":"preserve"}`
- Pattern definition canonicalization: `RFC8785_JCS_UTF8`
- Asset reference substitution: `{"jcs_string_format":"lowercase_hex_64_no_prefix","jcs_value_type":"string","object_path_in_digest":false,"source_digest_algorithm":"SHA-256","source_digest_bytes":32}`

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"BPABND01"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `boss_pattern_contract_sha256` | `bytes[32]` | `{}` |
| 3 | `pattern_set_id_sha256` | `bytes[32]` | `{}` |
| 4 | `safe_default_pattern_id` | `uint16` | `{}` |
| 5 | `occupied_pattern_count` | `uint8` | `{}` |
| 6 | `pattern_ids` | `uint16[32]` | `{"padding_value_ref":"invalid_pattern_id"}` |
| 7 | `pattern_definition_sha256` | `bytes[32][32]` | `{"padding_value":"all_zero"}` |

### BP.7.pattern_candidate_set_hash

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"BPCSET01"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `boss_pattern_contract_sha256` | `bytes[32]` | `{}` |
| 3 | `pattern_asset_bundle_sha256` | `bytes[32]` | `{}` |
| 4 | `pattern_slot_count` | `uint8` | `{"value_ref":"max_pattern_slots"}` |
| 5 | `pattern_ids` | `uint16[32]` | `{"padding_value_ref":"invalid_pattern_id"}` |
| 6 | `pattern_mask` | `bitset` | `{"bit_count":32,"bit_order":"LSB-first","byte_count":4,"unused_high_bits":"zero"}` |
| 7 | `attack_target_handle` | `target_handle` | `{"field_order":["kind:uint8","stable_id:uint64","generation:uint32","revision:uint64"]}` |
| 8 | `selection_boundary` | `uint8` | `{}` |
| 9 | `boss_phase_revision` | `uint64` | `{}` |
| 10 | `combat_state_revision` | `uint64` | `{}` |

### BP.7.boss_pattern_decision_contract_hash

| Order | Name | Type | Contract |
|---:|---|---|---|
| 0 | `magic` | `bytes[8]` | `{"value_ascii":"BPDCTR01"}` |
| 1 | `serialization_version` | `uint16` | `{"value":1}` |
| 2 | `boss_pattern_contract_sha256` | `bytes[32]` | `{}` |
| 3 | `pattern_model_sha256` | `bytes[32]` | `{}` |
| 4 | `pattern_normalization_contract_sha256` | `bytes[32]` | `{}` |
| 5 | `pattern_postprocess_contract_sha256` | `bytes[32]` | `{}` |
| 6 | `pattern_calibration_ood_asset_sha256` | `bytes[32]` | `{}` |
| 7 | `pattern_executor_contract_sha256` | `bytes[32]` | `{}` |

## BP.8 Release 상태

| Gate | Status |
|---|---|
| `static_schema_generator_harness` | `pass` |
| `asset_bundle_digest_parity` | `pending` |
| `unreal_float_parity` | `pending` |
| `onnx_output_parity` | `pending` |
| `unreal_pattern_runtime` | `pending` |
| `fairness_quality` | `pending` |
| `performance_budget` | `pending` |

<!-- END AUTO-GENERATED BOSS PATTERN CONTRACT -->

## BP.9 현재 Unreal 구현 메모

이 표는 generated BP 계약을 수정하지 않고 현재 Unreal 진행 상황만 설명한다.

| 범위 | 상태 |
|---|---|
| Data Asset·validator·bundle report | 구현; Definition JCS/cooked parity pending |
| 32행 Hash·Hard Mask·Tensor Normalization | 구현·검증 완료 |
| Utility·Decision Pipeline·Commit·Handoff | 구현·검증 완료 |
| Neural raw-output canonicalization | 구현; NNE adapter와 ranking/tie/OOD pending |
| Execution Safety Policy | 정책 구현; 실제 cleanup effect pending |
| Session-owned Event-driven Phase Executor·terminal barrier/unlock C++ Core | 완료(PASS) |
| StateTree/Turn Task producer·Combat lifecycle event-source adapter | phase PASS |
| production StateTree asset·native authoring MCP tool | phase PASS |
| encounter Pawn/AIController Blueprint physical assembly | phase PASS |
| fixture-backed Session Host·Commit→StateTree start handoff | phase PASS |
| concrete gameplay authority provider·production PatternSet/selector trigger | pending |
| authored transition/condition·Montage·Hitbox·Damage·Root Motion | pending |
| Replication·Save/Load·quality·performance | pending |

따라서 BP.8의 `unreal_pattern_runtime`은 계속 `pending`이다. 위 phase PASS는 fixture-backed 실행 기반 증거이며 shipping gameplay provider와 실제 전투 효과 완료를 뜻하지 않는다.

# Appendix E. 품질·안전·성능 승인 기준

Appendix E는 Candidate/Target·안전·OOD·Calibration·품질·Dataset·latency 승격 기준을 정한다.

<!-- BEGIN AUTO-GENERATED TEST TAXONOMY KPI: REQUIREMENTS -->

## E.1 고정 평가 버전

- Utility Baseline: `utility_baseline_v1.0.0`
- Schema: `2.0.0`
- Target Slotter: `1.0.0`
- Post-process: `1.0.0`
- Critical Suite: `critical_suite_v1`, **576 sequences = 9 family × 64 case**

### E.1.1 Critical Family

1. `perception_belief_visibility`
2. `typed_target_slotting`
3. `goal_arbitration_transition`
4. `candidate_mask_and_hash`
5. `async_latest_only_and_atomic_commit`
6. `hidden_information_boundary`
7. `skill_parameter_and_resource_cas`
8. `save_load_hot_swap_recovery`
9. `boss_pattern_mask_lock_interrupt_fairness`

### E.1.2 OOD Family

1. `feature_range_shift`
2. `missing_modality_pattern`
3. `unseen_role_attribute_combination`
4. `candidate_count_pattern`
5. `belief_age_confidence_shift`
6. `environment_layout_density_shift`
7. `event_sequence_shift`
8. `sensor_noise_shift`
9. `boss_pattern_phase_composition_shift`

## E.2 Candidate/Target

| Metric | Dataset | Gate |
|---|---|---|
| Target Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Any-Acceptable Candidate Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Critical Target/Candidate Recall | Critical Suite 576 sequences | 100%, 분모와 miss 모두 보고 |
| MandatoryOverflow | Critical + General | 0건 |

## E.3 Safety

절대 Gate:

- Critical Suite 576 sequences에서 hard-constraint 위반 Commit 0건
- Randomized Safety Fuzz 100,000 decision에서 hard-constraint 위반 Commit 0건
- Hidden Information Leakage Test 10,000 pair에서 Tensor/행동 누출 0건
- Server authority 우회 0건

Safety는 Baseline 비열등만으로 대체할 수 없다.

<!-- END AUTO-GENERATED TEST TAXONOMY KPI: REQUIREMENTS -->

### E.3.1 Remediation 해석

- E.2의 Target Recall과 Any-Acceptable Candidate Recall은 각각 §3.8과 §4.6의 numerator/denominator를 사용한다.
- Critical `100%`는 576 sequence aggregate에서 miss 0건을 뜻하며 sequence·decision·target/candidate 분모를 모두 보고한다.
- 현재 V1 Mandatory source cap 합은 9다. `MandatoryOverflow 0건`은 Runtime 방어 invariant와 malformed-cap negative mutation test로 측정한다.
- Auto-generated E.2 표는 다음 Test Taxonomy patch에서 이 해석을 구조화된 metric contract로 흡수해야 한다.

## E.4 Calibration/OOD

| Metric | Gate |
|---|---|
| ECE | ≤0.05 |
| Brier Score | ≤0.18 |
| Global risk/coverage | accepted ≥400, coverage ≥80%, one-sided Wilson 95% risk upper bound ≤0.10 |
| Role×Goal actual threshold | 각 필수 group accepted ≥100, coverage ≥80%, one-sided Wilson 95% risk upper bound ≤0.10; global fallback에도 동일 적용 |
| OOD Runtime operating point | threshold `0.80`에서 recall ≥0.90, FPR ≤0.10 |
| 각 Role×Goal Calibration group | 최소 400 Gold states; 0 accepted/coverage는 Release 실패 |

## E.5 품질 승격

Primary superiority metric:

- Baseline과의 blind naturalness A/B
- 600 unique sequence, 각 3명 평가, Role×Goal group당 최소 50 sequence
- cluster bootstrap 10,000회
- 모델 point win rate ≥55%
- 95% CI lower bound >52%

동시에 다음 secondary metric은 비열등해야 한다.

| Metric | Non-inferiority Margin |
|---|---:|
| Goal completion rate | Neural - Baseline 95% CI lower bound ≥ -2.0 percentage points |
| Unnecessary skill switch rate | Neural - Baseline 95% CI upper bound ≤ +0.2 switch/10s |
| P95 stable-scenario switch count | 절대 ≤3 switch/10s |
| Player fairness/understandability rating | 95% CI lower bound ≥ -0.10 on 5-point normalized scale |

승격 조건은 다음 AND다.

```text
Safety absolute Gate
AND Candidate/Target Gate
AND Latency Gate
AND Calibration/OOD Gate
AND Primary quality superiority
AND 나머지 core quality non-inferiority
```

## E.6 Dataset 최소량

V1의 3 Role × 4 Goal = 12 group 기준:

| Split | Group당 최소 | 총 최소 |
|---|---:|---:|
| Gold Train | 800 | 9,600 |
| Gold Calibration | 400 | 4,800 |
| Gold Test | 400 | 4,800 |
| DAgger Intervention | 200 | 2,400 |
| OOD Test | 9 family당 200 | 1,800 이상 |
| Critical Suite | `test_taxonomy_v1.yaml`에서 파생 | Appendix E.1–E.3의 자동 생성 계약 참조 |

Silver는 25k→50k→100k→200k learning curve를 작성한다. 두 번 연속 doubling에서 전체 primary validation 개선 <0.5pp이고 worst-group 개선 <1.0pp이면 추가 합성의 한계로 판단한다. 최소 100k Silver 이전에는 V1 freeze 결정을 하지 않는다.

## E.7 Latency·성능

Reference Hardware의 정확한 CPU/GPU/Build/backend는 `perf_manifest.json`에 고정하고 변경 시 재승인한다.

부하:

```text
Typical: 100 decisions/sec
Burst:   250 decisions/sec for 1 second
Candidate: 272 fixed rows
```

최소 표본:

- Typical 10,000 decisions
- Burst 2,500 decisions
- warm-up 500 decisions 제외

Gate:

| Metric | Absolute Budget | Baseline Non-inferiority Margin |
|---|---:|---:|
| Neural batch inference p95 | ≤6ms | N/A — absolute budget |
| Neural batch inference p99 | ≤12ms | N/A — absolute budget |
| Request-to-Commit p95 | ≤20ms | `utility_baseline_v1.0.0` +15ms |
| Request-to-Commit p99 | ≤40ms | `utility_baseline_v1.0.0` +30ms |
| Typical deadline miss | <0.1% | +0.05pp |
| Burst deadline miss | <1.0% | +0.5pp |

## E.8 통계 방법

- 비율: 지정된 trial 단위의 Wilson 95% CI
- Target/Candidate Recall: point/Wilson과 episode-cluster bootstrap 10,000회 CI 동시 보고
- paired A/B: scenario-cluster bootstrap 10,000회
- Goal completion/oscillation 차이: Role×Goal stratified bootstrap 10,000회
- latency percentile: request bootstrap 10,000회 및 raw percentile 동시 보고
- worst-group는 평균으로 상쇄하지 않고 별도 Gate로 보고

---

# UE 구현 승인 체크리스트

## Schema Freeze

- [x] PyYAML 전체 semantic validation
- [x] C++/Python generated code
- [x] Discrete/Hash Golden fixture
- [ ] 17 Slot/272 Candidate parity
- [ ] Float Feature parity
- [ ] NNE output parity
- [ ] Candidate Set Hash parity
- [ ] Decision Contract Hash
- [ ] Target Kind payload 구현
- [x] Skill/Goal Registry semantic validation

## Phase 0

- [ ] Manny/Quinn 수직 슬라이스
- [ ] Knowledge/Ground Truth 분리
- [ ] Goal FSM
- [ ] Target Recall Critical 100%
- [ ] Candidate Recall Critical 100%
- [ ] stale Commit 0
- [ ] Hidden Leakage 0
- [ ] Utility fallback
- [ ] packaged build

## Phase 1

- [ ] all Target Kind
- [ ] 16 Skill
- [ ] Reservation
- [ ] Calibration/OOD
- [ ] multiplayer
- [ ] Gold/DAgger
- [ ] Safety/KPI/Latency Gate
