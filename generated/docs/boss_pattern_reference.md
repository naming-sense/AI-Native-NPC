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
