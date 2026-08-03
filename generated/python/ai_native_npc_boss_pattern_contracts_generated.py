"""AUTO-GENERATED. DO NOT EDIT. Boss Pattern contract 1.0.0."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping
import hashlib, math, re, struct

GENERATOR_VERSION = '0.4.6'
BOSS_PATTERN_CONTRACT_SHA256 = 'e4f828c114fcc5db1cb04b5d0a6e2b3d29dada7e45c60a3dd18c674baa78c789'
CONTRACT_VERSION = '1.0.0'
CONTRACT_REVISION = '2.0.0-rc5'
CONSTANTS = {'boss_pattern_contract_version': '1.0.0', 'max_pattern_slots': 32, 'pattern_context_feature_count': 32, 'pattern_feature_count': 24, 'pattern_pair_feature_count': 16, 'pattern_parameter_count': 4, 'invalid_pattern_id': 65535, 'max_pattern_duration_s': 30.0, 'max_pattern_cooldown_s': 120.0, 'max_tracking_yaw_deg_s': 720.0, 'max_tracking_speed_cm_s': 1200.0, 'max_target_distance_cm': 10000.0, 'max_target_relative_speed_cm_s': 2000.0, 'max_encounter_elapsed_s': 1800.0}
TENSOR_SHAPES = {'pattern_context': ['B', 32], 'pattern_features': ['B', 32, 24], 'pattern_pair_features': ['B', 32, 16], 'pattern_ids': ['B', 32], 'pattern_mask': ['B', 32]}
TENSOR_DTYPES = {'pattern_context': 'float32', 'pattern_features': 'float32', 'pattern_pair_features': 'float32', 'pattern_ids': 'int64', 'pattern_mask': 'bool'}
OUTPUT_SHAPES = {'pattern_raw_scores': ['B', 32], 'pattern_parameter_proposals': ['B', 32, 4]}
OUTPUT_DTYPES = {'pattern_raw_scores': 'float32', 'pattern_parameter_proposals': 'float32'}
PATTERN_PARAMETERS = [{'index': 0, 'name': 'tracking_fraction', 'decode': 'authored_tracking_limit * clamp01(x)', 'authority': 'may_reduce_authored_maximum_only'}, {'index': 1, 'name': 'telegraph_extension_fraction', 'decode': 'telegraph_extension_max_s * clamp01(x)', 'authority': 'extension_only'}, {'index': 2, 'name': 'recovery_extension_fraction', 'decode': 'recovery_extension_max_s * clamp01(x)', 'authority': 'extension_only'}, {'index': 3, 'name': 'reserved_zero', 'decode': 'constant_zero', 'authority': 'none'}]
PATTERN_FORBIDDEN_OUTPUTS = ['damage', 'hitbox', 'active_window', 'root_motion', 'interruptibility', 'phase_transition']
FEATURE_NORMALIZERS = {'pattern_context': [{'index': 0, 'field': 'boss_health_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 1, 'field': 'boss_stamina_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 2, 'field': 'boss_posture_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 3, 'field': 'target_health_ratio_estimate', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 4, 'field': 'target_distance_planar', 'normalizer': 'distance_cm', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 10000.0, 'value': 0.0}, {'index': 5, 'field': 'target_distance_3d', 'normalizer': 'distance_cm', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 10000.0, 'value': 0.0}, {'index': 6, 'field': 'target_bearing_sin', 'normalizer': 'signed_unit', 'kind': 'clamp', 'min': -1.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 7, 'field': 'target_bearing_cos', 'normalizer': 'signed_unit', 'kind': 'clamp', 'min': -1.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 8, 'field': 'target_elevation_sin', 'normalizer': 'signed_unit', 'kind': 'clamp', 'min': -1.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 9, 'field': 'target_elevation_cos', 'normalizer': 'signed_unit', 'kind': 'clamp', 'min': -1.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 10, 'field': 'target_relative_speed', 'normalizer': 'signed_speed_cm_s', 'kind': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'divisor': 2000.0, 'value': 0.0}, {'index': 11, 'field': 'target_approach_velocity', 'normalizer': 'signed_speed_cm_s', 'kind': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'divisor': 2000.0, 'value': 0.0}, {'index': 12, 'field': 'target_lateral_velocity', 'normalizer': 'signed_speed_cm_s', 'kind': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'divisor': 2000.0, 'value': 0.0}, {'index': 13, 'field': 'has_line_of_sight', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 14, 'field': 'path_available', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 15, 'field': 'arena_edge_risk', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 16, 'field': 'boss_phase_normalized', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 17, 'field': 'elapsed_encounter_time', 'normalizer': 'encounter_elapsed_s', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1800.0, 'value': 0.0}, {'index': 18, 'field': 'elapsed_since_last_pattern', 'normalizer': 'cooldown_seconds', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 120.0, 'value': 0.0}, {'index': 19, 'field': 'same_pattern_streak_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 20, 'field': 'recent_fast_pattern_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 21, 'field': 'recent_heavy_pattern_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 22, 'field': 'recent_gap_closer_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 23, 'field': 'player_recent_damage_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 24, 'field': 'boss_recent_damage_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 25, 'field': 'selection_boundary_pre_attack', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 26, 'field': 'selection_boundary_branch_window', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 27, 'field': 'selection_boundary_recovery_end', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 28, 'field': 'previous_pattern_family_fast', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 29, 'field': 'previous_pattern_family_heavy', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 30, 'field': 'previous_pattern_family_gap_closer', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 31, 'field': 'target_health_estimate_confidence', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}], 'pattern_features': [{'index': 0, 'field': 'preferred_distance_min', 'normalizer': 'distance_cm', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 10000.0, 'value': 0.0}, {'index': 1, 'field': 'preferred_distance_max', 'normalizer': 'distance_cm', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 10000.0, 'value': 0.0}, {'index': 2, 'field': 'allowed_bearing_abs_max', 'normalizer': 'bearing_degrees', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 180.0, 'value': 0.0}, {'index': 3, 'field': 'allowed_elevation_abs_max', 'normalizer': 'elevation_degrees', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 90.0, 'value': 0.0}, {'index': 4, 'field': 'telegraph_duration', 'normalizer': 'pattern_duration_s', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 30.0, 'value': 0.0}, {'index': 5, 'field': 'active_duration', 'normalizer': 'pattern_duration_s', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 30.0, 'value': 0.0}, {'index': 6, 'field': 'recovery_duration', 'normalizer': 'pattern_duration_s', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 30.0, 'value': 0.0}, {'index': 7, 'field': 'cooldown_duration', 'normalizer': 'cooldown_seconds', 'kind': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'divisor': 120.0, 'value': 0.0}, {'index': 8, 'field': 'stamina_cost_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 9, 'field': 'startup_tracking_yaw_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 10, 'field': 'active_tracking_yaw_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 11, 'field': 'recovery_tracking_yaw_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 12, 'field': 'startup_tracking_speed_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 13, 'field': 'active_tracking_speed_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 14, 'field': 'area_pressure_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 15, 'field': 'gap_close_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 16, 'field': 'damage_pressure_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 17, 'field': 'posture_pressure_ratio', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 18, 'field': 'family_fast', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 19, 'field': 'family_heavy', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 20, 'field': 'family_gap_closer', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 21, 'field': 'family_area_control', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 22, 'field': 'branch_capable', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 23, 'field': 'reserved_zero', 'normalizer': 'constant_zero', 'kind': 'constant', 'min': 0.0, 'max': 0.0, 'divisor': 1.0, 'value': 0.0}], 'pattern_pair_features': [{'index': 0, 'field': 'distance_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 1, 'field': 'bearing_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 2, 'field': 'elevation_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 3, 'field': 'line_of_sight_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 4, 'field': 'phase_allowed', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 5, 'field': 'cooldown_ready', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 6, 'field': 'resource_ready', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 7, 'field': 'predecessor_allowed', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 8, 'field': 'branch_allowed', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 9, 'field': 'arena_safe', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 10, 'field': 'navigation_available', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 11, 'field': 'repetition_penalty_feature', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 12, 'field': 'timing_variety_feature', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 13, 'field': 'target_motion_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 14, 'field': 'selection_boundary_fit', 'normalizer': 'ratio_01', 'kind': 'clamp', 'min': 0.0, 'max': 1.0, 'divisor': 1.0, 'value': 0.0}, {'index': 15, 'field': 'reserved_zero', 'normalizer': 'constant_zero', 'kind': 'constant', 'min': 0.0, 'max': 0.0, 'divisor': 1.0, 'value': 0.0}]}
PADDING_CONTRACT = {'pattern_context': 'no_row_padding', 'unoccupied_pattern_features': 'all_zero_after_normalization', 'unoccupied_pattern_pair_features': 'all_zero_after_normalization', 'unoccupied_pattern_id': 'invalid_pattern_id', 'unoccupied_pattern_mask': False, 'masked_score_postprocess': 'negative_infinity_before_ranking', 'masked_parameter_proposals': 'ignored_and_zeroed_before_logging'}
PATTERN_CANDIDATE_HASH_CONTRACT = {'algorithm': 'SHA-256', 'raw_float_included': False, 'byte_order': 'little', 'fields': [{'name': 'magic', 'type': 'bytes[8]', 'value_ascii': 'BPCSET01'}, {'name': 'serialization_version', 'type': 'uint16', 'value': 1}, {'name': 'boss_pattern_contract_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_asset_bundle_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_slot_count', 'type': 'uint8', 'value_ref': 'max_pattern_slots'}, {'name': 'pattern_ids', 'type': 'uint16[32]', 'padding_value_ref': 'invalid_pattern_id'}, {'name': 'pattern_mask', 'type': 'bitset', 'bit_count': 32, 'byte_count': 4, 'bit_order': 'LSB-first', 'unused_high_bits': 'zero'}, {'name': 'attack_target_handle', 'type': 'target_handle', 'field_order': ['kind:uint8', 'stable_id:uint64', 'generation:uint32', 'revision:uint64']}, {'name': 'selection_boundary', 'type': 'uint8'}, {'name': 'boss_phase_revision', 'type': 'uint64'}, {'name': 'combat_state_revision', 'type': 'uint64'}], 'response_validation_order': ['CompareResponseHashToPendingRequestHash', 'CompareDecisionContractHash', 'ValidateLatestMutableState']}
BOSS_PATTERN_DECISION_HASH_CONTRACT = {'algorithm': 'SHA-256', 'raw_float_included': False, 'byte_order': 'little', 'fields': [{'name': 'magic', 'type': 'bytes[8]', 'value_ascii': 'BPDCTR01'}, {'name': 'serialization_version', 'type': 'uint16', 'value': 1}, {'name': 'boss_pattern_contract_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_model_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_normalization_contract_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_postprocess_contract_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_calibration_ood_asset_sha256', 'type': 'bytes[32]'}, {'name': 'pattern_executor_contract_sha256', 'type': 'bytes[32]'}]}

class SelectionBoundary(IntEnum):
    PreAttack = 0
    BranchWindow = 1
    RecoveryEnd = 2

class ExecutionPhase(IntEnum):
    ReadyToSelect = 0
    PreAttackTurn = 1
    StartupTelegraph = 2
    Active = 3
    Recovery = 4
    BranchWindow = 5
    Completed = 6
    Interrupted = 7

class InterruptKind(IntEnum):
    Death = 0
    ActorDestroyed = 1
    AuthorityLost = 2
    Stun = 3
    PostureBreak = 4
    ScriptedPhaseTransition = 5
    ArenaReset = 6

class PatternMaskReason(IntEnum):
    None_ = 0
    Unoccupied = 1
    WrongBossPhase = 2
    TargetInvalid = 3
    RangeMismatch = 4
    AngleMismatch = 5
    ElevationMismatch = 6
    LineOfSightMissing = 7
    CooldownActive = 8
    ResourceUnavailable = 9
    PredecessorMismatch = 10
    BranchNotAllowed = 11
    ArenaUnsafe = 12
    NavigationUnavailable = 13
    AssetUnavailable = 14
    NotSelectionBoundary = 15
    ReservationConflict = 16
    ExecutorLocked = 17

class PatternContextFeature(IntEnum):
    boss_health_ratio = 0
    boss_stamina_ratio = 1
    boss_posture_ratio = 2
    target_health_ratio_estimate = 3
    target_distance_planar = 4
    target_distance_3d = 5
    target_bearing_sin = 6
    target_bearing_cos = 7
    target_elevation_sin = 8
    target_elevation_cos = 9
    target_relative_speed = 10
    target_approach_velocity = 11
    target_lateral_velocity = 12
    has_line_of_sight = 13
    path_available = 14
    arena_edge_risk = 15
    boss_phase_normalized = 16
    elapsed_encounter_time = 17
    elapsed_since_last_pattern = 18
    same_pattern_streak_ratio = 19
    recent_fast_pattern_ratio = 20
    recent_heavy_pattern_ratio = 21
    recent_gap_closer_ratio = 22
    player_recent_damage_ratio = 23
    boss_recent_damage_ratio = 24
    selection_boundary_pre_attack = 25
    selection_boundary_branch_window = 26
    selection_boundary_recovery_end = 27
    previous_pattern_family_fast = 28
    previous_pattern_family_heavy = 29
    previous_pattern_family_gap_closer = 30
    target_health_estimate_confidence = 31

class PatternFeature(IntEnum):
    preferred_distance_min = 0
    preferred_distance_max = 1
    allowed_bearing_abs_max = 2
    allowed_elevation_abs_max = 3
    telegraph_duration = 4
    active_duration = 5
    recovery_duration = 6
    cooldown_duration = 7
    stamina_cost_ratio = 8
    startup_tracking_yaw_ratio = 9
    active_tracking_yaw_ratio = 10
    recovery_tracking_yaw_ratio = 11
    startup_tracking_speed_ratio = 12
    active_tracking_speed_ratio = 13
    area_pressure_ratio = 14
    gap_close_ratio = 15
    damage_pressure_ratio = 16
    posture_pressure_ratio = 17
    family_fast = 18
    family_heavy = 19
    family_gap_closer = 20
    family_area_control = 21
    branch_capable = 22
    reserved_zero = 23

class PatternPairFeature(IntEnum):
    distance_fit = 0
    bearing_fit = 1
    elevation_fit = 2
    line_of_sight_fit = 3
    phase_allowed = 4
    cooldown_ready = 5
    resource_ready = 6
    predecessor_allowed = 7
    branch_allowed = 8
    arena_safe = 9
    navigation_available = 10
    repetition_penalty_feature = 11
    timing_variety_feature = 12
    target_motion_fit = 13
    selection_boundary_fit = 14
    reserved_zero = 15

class PatternParameter(IntEnum):
    tracking_fraction = 0
    telegraph_extension_fraction = 1
    recovery_extension_fraction = 2
    reserved_zero = 3

def normalize_feature(tensor_name: str, field_index: int, value: float) -> float:
    rows = FEATURE_NORMALIZERS.get(tensor_name)
    if rows is None or not 0 <= field_index < len(rows):
        raise ValueError("unknown tensor or field index")
    if not math.isfinite(value):
        raise ValueError("non-finite Boss Pattern feature")
    spec = rows[field_index]
    if spec["kind"] == "constant":
        return float(spec["value"])
    normalized = value / float(spec["divisor"]) if spec["kind"] == "divide_clamp" else value
    return min(max(normalized, float(spec["min"])), float(spec["max"]))

@dataclass(frozen=True)
class TargetHandle:
    kind: int
    stable_id: int
    generation: int
    revision: int


def _array_count(type_name: str, prefix: str) -> int:
    match = re.fullmatch(re.escape(prefix) + r"\[(\d+)\]", type_name)
    if not match:
        raise ValueError(f"unsupported type {type_name}")
    return int(match.group(1))


def _pack_unsigned(value: int, type_name: str, byte_order: str = "little") -> bytes:
    formats = {
        ("uint8", "little"): "<B", ("uint16", "little"): "<H", ("uint32", "little"): "<I", ("uint64", "little"): "<Q",
        ("uint8", "big"): ">B", ("uint16", "big"): ">H", ("uint32", "big"): ">I", ("uint64", "big"): ">Q",
    }
    try:
        return struct.pack(formats[(type_name, byte_order)], int(value))
    except KeyError as exc:
        raise ValueError(f"unsupported integer type/order {type_name}/{byte_order}") from exc


def _digest_bytes(value: str, size: int, name: str) -> bytes:
    raw = bytes.fromhex(value)
    if len(raw) != size:
        raise ValueError(f"{name} must be {size} bytes")
    return raw


def _pack_mask(bits: list[bool], bit_count: int) -> bytes:
    if len(bits) != bit_count:
        raise ValueError(f"expected {bit_count} mask bits")
    out = bytearray((bit_count + 7) // 8)
    for index, value in enumerate(bits):
        if value:
            out[index // 8] |= 1 << (index % 8)
    return bytes(out)


def _target_handle_bytes(handle: TargetHandle, field_order: list[str], byte_order: str) -> bytes:
    values = {"kind": handle.kind, "stable_id": handle.stable_id, "generation": handle.generation, "revision": handle.revision}
    return b"".join(_pack_unsigned(values[name], dtype, byte_order) for name, dtype in (row.split(":", 1) for row in field_order))


def validate_pattern_slot_layout(pattern_ids: list[int], pattern_mask: list[bool]) -> None:
    count = int(CONSTANTS["max_pattern_slots"])
    if len(pattern_ids) != count or len(pattern_mask) != count:
        raise ValueError(f"Boss Pattern layout must contain {count} rows")
    invalid = int(CONSTANTS["invalid_pattern_id"])
    seen_padding = False
    previous = -1
    for index, (pattern_id, mask_value) in enumerate(zip(pattern_ids, pattern_mask, strict=True)):
        if not isinstance(mask_value, bool):
            raise ValueError(f"pattern_mask row {index} must be bool")
        if isinstance(pattern_id, bool) or not isinstance(pattern_id, int) or not 0 <= pattern_id <= invalid:
            raise ValueError(f"pattern_id row {index} is outside uint16")
        if pattern_id == invalid:
            seen_padding = True
            if bool(mask_value):
                raise ValueError(f"padding row {index} cannot be valid")
            continue
        if seen_padding:
            raise ValueError(f"occupied pattern row {index} appears after padding")
        if pattern_id <= previous:
            raise ValueError("occupied pattern_ids must be strictly ascending")
        previous = pattern_id
    if previous < 0:
        raise ValueError("Boss Pattern layout must contain at least one occupied row")


def pattern_candidate_set_canonical_bytes(
    pattern_asset_bundle_sha256: str,
    pattern_ids: list[int],
    pattern_mask: list[bool],
    attack_target_handle: TargetHandle,
    selection_boundary: int,
    boss_phase_revision: int,
    combat_state_revision: int,
) -> bytes:
    validate_pattern_slot_layout(pattern_ids, pattern_mask)
    contract = PATTERN_CANDIDATE_HASH_CONTRACT
    raw = bytearray()
    for field in contract["fields"]:
        name, type_name = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(type_name, "bytes"):
                raise ValueError("pattern candidate magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], type_name, contract["byte_order"])
        elif name == "boss_pattern_contract_sha256":
            raw += _digest_bytes(BOSS_PATTERN_CONTRACT_SHA256, _array_count(type_name, "bytes"), name)
        elif name == "pattern_asset_bundle_sha256":
            raw += _digest_bytes(pattern_asset_bundle_sha256, _array_count(type_name, "bytes"), name)
        elif name == "pattern_slot_count":
            raw += _pack_unsigned(CONSTANTS[field["value_ref"]], type_name, contract["byte_order"])
        elif name == "pattern_ids":
            count = _array_count(type_name, "uint16")
            if len(pattern_ids) != count:
                raise ValueError(f"pattern_ids must contain {count} rows")
            for pattern_id in pattern_ids:
                raw += _pack_unsigned(pattern_id, "uint16", contract["byte_order"])
        elif name == "pattern_mask":
            raw += _pack_mask(pattern_mask, int(field["bit_count"]))
        elif name == "attack_target_handle":
            raw += _target_handle_bytes(attack_target_handle, field["field_order"], contract["byte_order"])
        elif name == "selection_boundary":
            SelectionBoundary(int(selection_boundary))
            raw += _pack_unsigned(selection_boundary, type_name, contract["byte_order"])
        elif name == "boss_phase_revision":
            raw += _pack_unsigned(boss_phase_revision, type_name, contract["byte_order"])
        elif name == "combat_state_revision":
            raw += _pack_unsigned(combat_state_revision, type_name, contract["byte_order"])
        else:
            raise ValueError(f"unsupported boss pattern candidate hash field {name}")
    return bytes(raw)


def pattern_candidate_set_hash(*args, **kwargs) -> str:
    return hashlib.sha256(pattern_candidate_set_canonical_bytes(*args, **kwargs)).hexdigest()


def boss_pattern_decision_contract_canonical_bytes(digests: Mapping[str, str]) -> bytes:
    contract = BOSS_PATTERN_DECISION_HASH_CONTRACT
    raw = bytearray()
    for field in contract["fields"]:
        name, type_name = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(type_name, "bytes"):
                raise ValueError("boss pattern decision magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], type_name, contract["byte_order"])
        elif name == "boss_pattern_contract_sha256":
            raw += _digest_bytes(BOSS_PATTERN_CONTRACT_SHA256, _array_count(type_name, "bytes"), name)
        else:
            raw += _digest_bytes(digests[name], _array_count(type_name, "bytes"), name)
    return bytes(raw)


def boss_pattern_decision_contract_hash(digests: Mapping[str, str]) -> str:
    return hashlib.sha256(boss_pattern_decision_contract_canonical_bytes(digests)).hexdigest()
