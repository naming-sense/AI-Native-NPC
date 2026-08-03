# Appendix A–D. AUTO-GENERATED Schema·Registry 계약

> 이 구간은 `contracts/current/*.yaml`에서 자동 생성된다. 수동 편집하지 않는다.

- Generator: `0.4.6`
- Contract revision: `2.0.0-rc5`
- Schema SHA-256: `56deff3a5f55ddad30864bcf7df4d100d2f1c5472f86f0a8b9e2599044c37385`
- Skill Registry SHA-256: `08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8`
- Goal Registry SHA-256: `b6ed883e39f8da4f792b2ad4542b4cf7045ff5fe00147a9eba15eac61fa67ac2`
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
| `goal_registry_version` | `1.0.1` |
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

### D.3 Hash: candidate_set_hash

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

### D.4 Hash: decision_contract_hash

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

### D.5 Normalizer 의미 규칙

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
