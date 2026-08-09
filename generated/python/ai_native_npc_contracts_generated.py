"""AUTO-GENERATED. DO NOT EDIT. Schema 2.0.0-rc5 bindings."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping
import hashlib, math, re, struct

GENERATOR_VERSION = '0.4.6'
SCHEMA_SOURCE_SHA256 = 'a7791004de0534f29198ebf5eaaff7cd764185b59b05446d419f5d0a3303f886'
SKILL_REGISTRY_SHA256 = '08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8'
GOAL_REGISTRY_SHA256 = 'ede7aaba704ecbbd9c6e1cb649c87e03fd24e9dc71ea4166f82baa42fb00ee43'
GOAL_REGISTRY_VERSION = '1.1.0'
GOAL_STATES = ['Inactive', 'Active', 'Suspended', 'Succeeded', 'Failed', 'Aborted']
GOAL_ARBITRATION = {'max_active_goals': 1, 'max_suspended_goals': 8, 'selection_key': [{'field': 'priority', 'direction': 'desc', 'dtype': 'uint8'}, {'field': 'source_priority', 'direction': 'desc', 'dtype': 'uint8'}, {'field': 'created_time_quantized_ms', 'direction': 'asc', 'dtype': 'uint64'}, {'field': 'goal_instance_id', 'direction': 'asc', 'dtype': 'uint64'}], 'preemption_margin': 50, 'interruptibility_modes': ['Always', 'PhaseBoundary', 'EmergencyOnly', 'Never'], 'resume_policies': ['ResumeSamePhase', 'RestartPhase', 'AbortOnPreempt'], 'on_new_goal_activation_failure': 'keep_previous_active_goal', 'terminal_goal_reactivation': False, 'suspended_resume_order': 'same_selection_key'}
GOAL_DEFINITIONS = [{'id': 1, 'name': 'IdleObserve', 'status': 'active_v1', 'default_priority': 10, 'source_priority': 'Routine', 'interruptibility': 'Always', 'resume_policy': 'ResumeSamePhase', 'initial_phase': 'Observe'}, {'id': 2, 'name': 'InvestigateDisturbance', 'status': 'active_v1', 'default_priority': 120, 'source_priority': 'Social', 'interruptibility': 'PhaseBoundary', 'resume_policy': 'ResumeSamePhase', 'initial_phase': 'Orient'}, {'id': 3, 'name': 'EnforceBoundary', 'status': 'active_v1', 'default_priority': 160, 'source_priority': 'Quest', 'interruptibility': 'PhaseBoundary', 'resume_policy': 'ResumeSamePhase', 'initial_phase': 'Observe'}, {'id': 4, 'name': 'CombatEngage', 'status': 'active_v1', 'default_priority': 220, 'source_priority': 'Combat', 'interruptibility': 'EmergencyOnly', 'resume_policy': 'RestartPhase', 'initial_phase': 'Orient'}]
GOAL_PHASE_SPECS = [{'goal': 'IdleObserve', 'phase': 'Observe', 'allowed_skills': ['Idle', 'ContinueCurrentAction', 'LookAt', 'TurnTo', 'Greet']}, {'goal': 'InvestigateDisturbance', 'phase': 'Orient', 'allowed_skills': ['ContinueCurrentAction', 'LookAt', 'TurnTo']}, {'goal': 'InvestigateDisturbance', 'phase': 'Navigate', 'allowed_skills': ['ContinueCurrentAction', 'Approach', 'Investigate', 'Flee']}, {'goal': 'InvestigateDisturbance', 'phase': 'Search', 'allowed_skills': ['ContinueCurrentAction', 'SearchArea', 'LookAt', 'TurnTo']}, {'goal': 'InvestigateDisturbance', 'phase': 'Resolve', 'allowed_skills': ['ContinueCurrentAction', 'Greet', 'Warn', 'CallForHelp', 'Attack', 'Flee']}, {'goal': 'InvestigateDisturbance', 'phase': 'Return', 'allowed_skills': ['ContinueCurrentAction', 'Approach', 'Idle']}, {'goal': 'EnforceBoundary', 'phase': 'Observe', 'allowed_skills': ['Idle', 'ContinueCurrentAction', 'LookAt', 'TurnTo']}, {'goal': 'EnforceBoundary', 'phase': 'Interact', 'allowed_skills': ['ContinueCurrentAction', 'LookAt', 'TurnTo', 'Greet', 'Warn']}, {'goal': 'EnforceBoundary', 'phase': 'Resolve', 'allowed_skills': ['ContinueCurrentAction', 'Warn', 'KeepDistance', 'CallForHelp', 'Attack', 'Flee']}, {'goal': 'EnforceBoundary', 'phase': 'Return', 'allowed_skills': ['ContinueCurrentAction', 'Approach', 'Idle']}, {'goal': 'CombatEngage', 'phase': 'Orient', 'allowed_skills': ['ContinueCurrentAction', 'LookAt', 'TurnTo', 'TakeCover']}, {'goal': 'CombatEngage', 'phase': 'Resolve', 'allowed_skills': ['ContinueCurrentAction', 'Attack', 'TakeCover', 'RetreatFrom', 'CallForHelp', 'Flee']}, {'goal': 'CombatEngage', 'phase': 'Search', 'allowed_skills': ['ContinueCurrentAction', 'Investigate', 'SearchArea', 'LookAt', 'TurnTo']}, {'goal': 'CombatEngage', 'phase': 'Return', 'allowed_skills': ['ContinueCurrentAction', 'Approach', 'Idle', 'TakeCover']}]
GOAL_TRIGGER_CONTRACT = {'allowed_kinds': ['event', 'timer', 'lifecycle', 'server_control'], 'active_v1_kinds': ['event', 'timer'], 'legacy_event_field_forbidden': True, 'timer_id_scope': 'goal_phase', 'timer_clock': 'server_monotonic_world_seconds', 'timer_duration_unit': 'second', 'timer_arm_on': {'phase_entry': 'full_after_seconds', 'resume_same_phase': 'stored_remaining_ms', 'restart_phase_resume': 'full_after_seconds'}, 'timer_suspend_policy': 'pause_and_store_remaining_ms', 'timer_cancel_on': 'phase_exit_or_terminal', 'timer_expiry_policy': 'enqueue_once_then_evaluate_in_transition_order', 'absolute_goal_deadline_while_suspended': 'continues', 'save_load_policy': 'persist_timer_id_contract_duration_remaining_ms_and_resume_policy', 'wall_clock_forbidden': True, 'current_v1_counts': {'event': 35, 'timer': 6}, 'reserved_kinds': {'lifecycle': 'reserved_until_field_contract_is_defined', 'server_control': 'reserved_until_field_contract_is_defined'}}
GOAL_REVISION_CONTRACT = {'type': 'uint64_monotonic_per_npc', 'increase_on': ['active_goal_changed', 'goal_suspended', 'goal_resumed', 'goal_aborted', 'phase_changed', 'authoritative_primary_target_changed', 'allowed_skill_set_changed', 'forbidden_skill_set_changed', 'deadline_contract_changed', 'interruptibility_changed', 'resume_policy_changed'], 'do_not_increase_on': ['progress_value_changed', 'per_frame_timer_changed', 'belief_revision_changed_without_goal_contract_change', 'event_buffer_append']}
GOAL_V1_PRODUCT_SCOPE = {'exact_goal_names': ['IdleObserve', 'InvestigateDisturbance', 'EnforceBoundary', 'CombatEngage'], 'deferred_goal_names': ['Disengage', 'Escort'], 'reserved_goal_names': ['Reserved']}
GOAL_TRANSITIONS = [{'goal': 'IdleObserve', 'phase': 'Observe', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SoundHeard'}, 'guard': 'valid_disturbance_target', 'to_goal': 'InvestigateDisturbance', 'effect': 'request_new_goal'}, {'goal': 'IdleObserve', 'phase': 'Observe', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SightAcquired'}, 'guard': 'social_subject', 'to_phase': 'Observe', 'effect': 'remain_and_replan'}, {'goal': 'InvestigateDisturbance', 'phase': 'Orient', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'orientation_complete', 'to_phase': 'Navigate'}, {'goal': 'InvestigateDisturbance', 'phase': 'Orient', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'no_valid_snapshot', 'terminal': 'Failed'}, {'goal': 'InvestigateDisturbance', 'phase': 'Orient', 'order': 2, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 2.0}, 'guard': 'phase_timeout', 'terminal': 'Failed'}, {'goal': 'InvestigateDisturbance', 'phase': 'Navigate', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'arrived_at_snapshot', 'to_phase': 'Search'}, {'goal': 'InvestigateDisturbance', 'phase': 'Navigate', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillFailed'}, 'guard': 'PathUnavailable', 'terminal': 'Failed'}, {'goal': 'InvestigateDisturbance', 'phase': 'Navigate', 'order': 2, 'trigger': {'kind': 'event', 'event_type': 'SightAcquired'}, 'guard': 'subject_identified', 'to_phase': 'Resolve'}, {'goal': 'InvestigateDisturbance', 'phase': 'Navigate', 'order': 3, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 15.0}, 'guard': 'phase_timeout', 'terminal': 'Failed'}, {'goal': 'InvestigateDisturbance', 'phase': 'Search', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SightAcquired'}, 'guard': 'subject_identified', 'to_phase': 'Resolve'}, {'goal': 'InvestigateDisturbance', 'phase': 'Search', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'search_budget_exhausted', 'to_phase': 'Return'}, {'goal': 'InvestigateDisturbance', 'phase': 'Search', 'order': 2, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 8.0}, 'guard': 'phase_timeout', 'to_phase': 'Return'}, {'goal': 'InvestigateDisturbance', 'phase': 'Resolve', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'resolution_complete', 'to_phase': 'Return'}, {'goal': 'InvestigateDisturbance', 'phase': 'Resolve', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'no_valid_belief', 'to_phase': 'Search'}, {'goal': 'InvestigateDisturbance', 'phase': 'Return', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'at_return_target', 'terminal': 'Succeeded'}, {'goal': 'InvestigateDisturbance', 'phase': 'Return', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillFailed'}, 'guard': 'PathUnavailable', 'terminal': 'Failed'}, {'goal': 'EnforceBoundary', 'phase': 'Observe', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SightAcquired'}, 'guard': 'boundary_intruder_is_primary_social_subject', 'to_phase': 'Interact'}, {'goal': 'EnforceBoundary', 'phase': 'Observe', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'no_boundary_intruder', 'to_phase': 'Return'}, {'goal': 'EnforceBoundary', 'phase': 'Observe', 'order': 2, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 4.0}, 'guard': 'phase_timeout', 'terminal': 'Failed'}, {'goal': 'EnforceBoundary', 'phase': 'Interact', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'WarningIssued'}, 'guard': 'warning_delivered', 'to_phase': 'Resolve'}, {'goal': 'EnforceBoundary', 'phase': 'Interact', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'subject_complied_before_warning', 'to_phase': 'Return'}, {'goal': 'EnforceBoundary', 'phase': 'Interact', 'order': 2, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'subject_left_boundary', 'to_phase': 'Return'}, {'goal': 'EnforceBoundary', 'phase': 'Interact', 'order': 3, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 6.0}, 'guard': 'phase_timeout', 'to_phase': 'Resolve'}, {'goal': 'EnforceBoundary', 'phase': 'Resolve', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'boundary_resolved', 'to_phase': 'Return'}, {'goal': 'EnforceBoundary', 'phase': 'Resolve', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'WarningIgnored'}, 'guard': 'escalation_allowed', 'to_phase': 'Resolve', 'effect': 'remain_and_replan'}, {'goal': 'EnforceBoundary', 'phase': 'Resolve', 'order': 2, 'trigger': {'kind': 'event', 'event_type': 'Damaged'}, 'guard': 'combat_goal_allowed', 'to_goal': 'CombatEngage', 'effect': 'request_new_goal'}, {'goal': 'EnforceBoundary', 'phase': 'Resolve', 'order': 3, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'subject_no_longer_relevant', 'to_phase': 'Return'}, {'goal': 'EnforceBoundary', 'phase': 'Return', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'at_return_target', 'terminal': 'Succeeded'}, {'goal': 'EnforceBoundary', 'phase': 'Return', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillFailed'}, 'guard': 'PathUnavailable', 'terminal': 'Failed'}, {'goal': 'CombatEngage', 'phase': 'Orient', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'combat_target_aligned', 'to_phase': 'Resolve'}, {'goal': 'CombatEngage', 'phase': 'Orient', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SightLost'}, 'guard': 'has_last_known_position', 'to_phase': 'Search'}, {'goal': 'CombatEngage', 'phase': 'Orient', 'order': 2, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'no_valid_combat_target', 'to_phase': 'Return'}, {'goal': 'CombatEngage', 'phase': 'Resolve', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SightLost'}, 'guard': 'has_last_known_position', 'to_phase': 'Search'}, {'goal': 'CombatEngage', 'phase': 'Resolve', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'combat_resolved', 'to_phase': 'Return'}, {'goal': 'CombatEngage', 'phase': 'Resolve', 'order': 2, 'trigger': {'kind': 'event', 'event_type': 'TargetInvalidated'}, 'guard': 'combat_target_invalid', 'to_phase': 'Return'}, {'goal': 'CombatEngage', 'phase': 'Resolve', 'order': 3, 'trigger': {'kind': 'event', 'event_type': 'ReservationLost'}, 'guard': 'cover_resource_lost', 'to_phase': 'Resolve', 'effect': 'remain_and_replan'}, {'goal': 'CombatEngage', 'phase': 'Search', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SightAcquired'}, 'guard': 'combat_target_reacquired', 'to_phase': 'Resolve'}, {'goal': 'CombatEngage', 'phase': 'Search', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'search_budget_exhausted', 'to_phase': 'Return'}, {'goal': 'CombatEngage', 'phase': 'Search', 'order': 2, 'trigger': {'kind': 'timer', 'timer_id': 'phase_timeout', 'after_seconds': 5.0}, 'guard': 'phase_timeout', 'to_phase': 'Return'}, {'goal': 'CombatEngage', 'phase': 'Return', 'order': 0, 'trigger': {'kind': 'event', 'event_type': 'SkillSucceeded'}, 'guard': 'combat_exit_complete', 'terminal': 'Succeeded'}, {'goal': 'CombatEngage', 'phase': 'Return', 'order': 1, 'trigger': {'kind': 'event', 'event_type': 'SkillFailed'}, 'guard': 'PathUnavailable', 'terminal': 'Failed'}]
SCHEMA_VERSION = '2.0.0'
CONTRACT_REVISION = '2.0.0-rc5'
CONSTANTS = {'schema_version': '2.0.0', 'skill_registry_version': '1.0.0', 'target_slotter_version': '1.0.0', 'postprocess_version': '1.0.0', 'normalization_version': '2.0.0', 'regular_target_slots': 16, 'no_target_slot': 16, 'total_target_slots': 17, 'skill_count': 16, 'candidate_count': 272, 'event_slots': 12, 'global_feature_count': 128, 'target_feature_count': 48, 'event_feature_count': 24, 'candidate_pair_feature_count': 16, 'parameter_count': 4, 'spatial_max_cm': 5000.0, 'path_distance_max_cm': 10000.0, 'speed_max_cm_s': 1200.0, 'acceleration_max_cm_s2': 4000.0, 'yaw_rate_max_deg_s': 720.0, 'target_age_max_s': 10.0, 'event_age_max_s': 10.0, 'visible_duration_max_s': 10.0, 'skill_time_max_s': 10.0, 'goal_phase_time_max_s': 30.0, 'goal_deadline_max_s': 120.0, 'count_max': 8.0, 'schema_contract_revision': '2.0.0-rc5', 'goal_registry_version': '1.1.0', 'goal_priority_max': 255.0, 'long_duration_max_s': 30.0, 'slotter_confidence_scale': 1000, 'slotter_age_centisecond_scale': 100, 'slotter_distance_bin_cm': 10, 'slotter_loudness_scale': 1000}
TENSOR_SHAPES = {'global_state': ['B', 128], 'target_features': ['B', 17, 48], 'target_kind_ids': ['B', 17], 'target_mask': ['B', 17], 'event_features': ['B', 12, 24], 'event_type_ids': ['B', 12], 'event_target_slots': ['B', 12], 'event_mask': ['B', 12], 'candidate_pair_features': ['B', 272, 16], 'candidate_mask': ['B', 272]}
TENSOR_DTYPES = {'global_state': 'float32', 'target_features': 'float32', 'target_kind_ids': 'int64', 'target_mask': 'bool', 'event_features': 'float32', 'event_type_ids': 'int64', 'event_target_slots': 'int64', 'event_mask': 'bool', 'candidate_pair_features': 'float32', 'candidate_mask': 'bool'}
SCORE_CONTRACT = {'query': {'projection_dim': 64, 'layer_norm': True, 'l2_normalize': True}, 'key': {'dimension': 64, 'layer_norm': True, 'l2_normalize': True}, 'cosine_temperature': 0.5, 'skill_bias_clamp': [-0.25, 0.25], 'target_kind_bias_clamp': [-0.25, 0.25], 'raw_score_clamp': [-2.5, 2.5], 'formula': 'clamp(cosine(q,key)/temperature + skill_bias + target_kind_bias, raw_min, raw_max)', 'switch_cost': {'min': 0.0, 'max': 1.0, 'lambda': 1.0, 'terms': [{'name': 'skill_changed', 'weight': 0.45}, {'name': 'target_changed', 'weight': 0.25}, {'name': 'before_min_duration', 'weight': 0.2}, {'name': 'release_or_transfer_reservation', 'weight': 0.1}]}, 'adjusted_score_formula': 'raw_score - lambda * switch_cost', 'masked_softmax': {'temperature': 1.0, 'invalid_value': 'negative_infinity', 'entropy_normalization': 'divide_by_log_valid_count_when_count_gt_1'}}
COMMIT_VALIDATION = {'Entity': {'mode': 'latest_valid_belief', 'identity_generation_must_match': True, 'requested_revision_policy': 'newer_valid_belief_allowed', 'requires_current_perception_when_skill_requires_tracking': True}, 'SoundEvent': {'mode': 'immutable_snapshot_exact', 'snapshot_revision': 'exact', 'ttl_required': True}, 'LastKnownPosition': {'mode': 'immutable_snapshot_exact', 'snapshot_revision': 'exact', 'ttl_required': True, 'origin_actor_lookup_for_tactical_update': False}, 'CoverSlot': {'mode': 'resource_compare_and_swap', 'compare': ['stable_id', 'generation', 'availability_revision'], 'reservation_id_created_at_commit': True}, 'SmartObject': {'mode': 'resource_compare_and_swap', 'compare': ['stable_id', 'generation', 'availability_revision'], 'reservation_id_created_at_commit': True}, 'Waypoint': {'mode': 'immutable_or_authoritative_definition', 'snapshot_revision': 'exact'}, 'WorldPosition': {'mode': 'immutable_snapshot_exact', 'snapshot_revision': 'exact', 'ttl_required_if_configured': True}, 'NoTarget': {'mode': 'none'}}
SKILL_PARAMETER_CONTRACTS = {0: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.5, 'max': 5.0, 'default': 1.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}], 1: [{'slot': 0, 'name': 'duration', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}], 2: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.25, 'max': 3.0, 'default': 1.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 3: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.25, 'max': 2.0, 'default': 0.75, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'degree_per_second', 'min': 90.0, 'max': 720.0, 'default': 360.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 4: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.5, 'max': 10.0, 'default': 3.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 150.0, 'max': 600.0, 'default': 350.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 100.0, 'max': 500.0, 'default': 200.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 5: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.5, 'max': 10.0, 'default': 3.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 150.0, 'max': 600.0, 'default': 300.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 200.0, 'max': 1000.0, 'default': 500.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 6: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.5, 'max': 10.0, 'default': 3.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 150.0, 'max': 650.0, 'default': 400.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 300.0, 'max': 1500.0, 'default': 700.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'decode': 'linear', 'commit_clamp': True}], 7: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.5, 'max': 10.0, 'default': 4.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 150.0, 'max': 600.0, 'default': 350.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 150.0, 'max': 700.0, 'default': 350.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 8: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 12.0, 'default': 5.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 100.0, 'max': 500.0, 'default': 280.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 100.0, 'max': 1200.0, 'default': 400.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.6, 'decode': 'linear', 'commit_clamp': True}], 9: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 3.0, 'max': 20.0, 'default': 8.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 80.0, 'max': 400.0, 'default': 220.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 200.0, 'max': 2000.0, 'default': 700.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.6, 'decode': 'linear', 'commit_clamp': True}], 10: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 5.0, 'default': 2.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.5, 'decode': 'linear', 'commit_clamp': True}], 11: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 5.0, 'default': 2.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'decode': 'linear', 'commit_clamp': True}], 12: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 4.0, 'default': 2.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.8, 'decode': 'linear', 'commit_clamp': True}], 13: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 10.0, 'default': 4.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 150.0, 'max': 650.0, 'default': 400.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'decode': 'linear', 'commit_clamp': True}], 14: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 1.0, 'max': 15.0, 'default': 6.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 1, 'unit': 'centimeter_per_second', 'min': 200.0, 'max': 700.0, 'default': 500.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 500.0, 'max': 3000.0, 'default': 1500.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.9, 'decode': 'linear', 'commit_clamp': True}], 15: [{'slot': 0, 'name': 'duration', 'active': 1, 'unit': 'second', 'min': 0.2, 'max': 5.0, 'default': 1.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 1, 'name': 'speed', 'active': 0, 'unit': 'none', 'min': 0.0, 'max': 0.0, 'default': 0.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 2, 'name': 'preferred_distance', 'active': 1, 'unit': 'centimeter', 'min': 100.0, 'max': 2000.0, 'default': 600.0, 'decode': 'linear', 'commit_clamp': True}, {'slot': 3, 'name': 'intensity', 'active': 1, 'unit': 'ratio', 'min': 0.0, 'max': 1.0, 'default': 0.7, 'decode': 'linear', 'commit_clamp': True}]}
SKILL_ALLOWED_TARGET_KINDS = {0: ['NoTarget'], 1: ['NoTarget', 'Entity', 'SoundEvent', 'LastKnownPosition', 'CoverSlot', 'SmartObject', 'Waypoint', 'WorldPosition'], 2: ['Entity', 'SoundEvent', 'LastKnownPosition', 'Waypoint', 'WorldPosition'], 3: ['Entity', 'SoundEvent', 'LastKnownPosition', 'Waypoint', 'WorldPosition'], 4: ['Entity', 'LastKnownPosition', 'CoverSlot', 'SmartObject', 'Waypoint', 'WorldPosition'], 5: ['Entity'], 6: ['Entity', 'LastKnownPosition'], 7: ['Entity'], 8: ['SoundEvent', 'LastKnownPosition', 'SmartObject', 'Waypoint', 'WorldPosition'], 9: ['LastKnownPosition', 'Waypoint', 'WorldPosition'], 10: ['Entity'], 11: ['Entity'], 12: ['NoTarget', 'Entity'], 13: ['CoverSlot'], 14: ['NoTarget', 'Waypoint', 'WorldPosition'], 15: ['Entity']}
NORMALIZER_TABLES = {'global': [{'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 4000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 4000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 4000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 720.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 255.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 30.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'sentinel_divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 120.0, 'p1': 1.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 16.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 16.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 8.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 12.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'target_common': [{'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'log1p_ratio', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 5000.0, 'p2': 5000.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 1.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 1.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 1200.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'sentinel_divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'sentinel_divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 1.0, 'p2': 0.0}, {'type': 'sentinel_divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 1.0, 'p2': 0.0}], 'event': [{'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': -1.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 5000.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'trigonometric', 'min': 0.0, 'max': 0.0, 'p0': 1.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'candidate_pair': [{'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'divide_clamp', 'min': 0.0, 'max': 1.0, 'p0': 10.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'target_payload': {'NoTarget': [{'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'Entity': [{'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'SoundEvent': [{'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'LastKnownPosition': [{'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'CoverSlot': [{'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'SmartObject': [{'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'Waypoint': [{'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}], 'WorldPosition': [{'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': -1.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'clamp', 'min': 0.0, 'max': 1.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'boolean', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}, {'type': 'constant', 'min': 0.0, 'max': 0.0, 'p0': 0.0, 'p1': 0.0, 'p2': 0.0}]}}
TARGET_HANDLE_FIELD_ORDER = ['kind:uint8', 'stable_id:uint64', 'generation:uint32', 'revision:uint64']
CANDIDATE_HASH_CONTRACT = {'algorithm': 'SHA-256', 'raw_float_included': False, 'byte_order': 'little', 'serialization_version': 1, 'fields': [{'name': 'magic', 'type': 'bytes[8]', 'value_ascii': 'ANPCSET2'}, {'name': 'serialization_version', 'type': 'uint16', 'value': 1}, {'name': 'schema_source_sha256', 'type': 'bytes[32]'}, {'name': 'target_slot_count', 'type': 'uint8', 'value_ref': 'total_target_slots'}, {'name': 'target_handles', 'type': 'target_handle[17]', 'field_order': ['kind:uint8', 'stable_id:uint64', 'generation:uint32', 'revision:uint64']}, {'name': 'target_mask', 'type': 'bitset', 'bit_count': 17, 'byte_count': 3, 'bit_order': 'LSB-first', 'unused_high_bits': 'zero'}, {'name': 'candidate_mask', 'type': 'bitset', 'bit_count': 272, 'byte_count': 34, 'bit_order': 'LSB-first', 'unused_high_bits': 'none'}], 'response_validation_order': ['compare_response_hash_to_pending_request_hash', 'then_validate_latest_world_state', 'never_recompute_current_hash_for_first_comparison']}
DECISION_HASH_CONTRACT = {'algorithm': 'SHA-256', 'raw_float_included': False, 'byte_order': 'little', 'serialization_version': 1, 'fields': [{'name': 'magic', 'type': 'bytes[8]', 'value_ascii': 'ANPCDEC2'}, {'name': 'serialization_version', 'type': 'uint16', 'value': 1}, {'name': 'schema_source_sha256', 'type': 'bytes[32]'}, {'name': 'skill_registry_sha256', 'type': 'bytes[32]'}, {'name': 'goal_registry_sha256', 'type': 'bytes[32]'}, {'name': 'model_sha256', 'type': 'bytes[32]'}, {'name': 'normalization_contract_sha256', 'type': 'bytes[32]'}, {'name': 'slotter_contract_sha256', 'type': 'bytes[32]'}, {'name': 'postprocess_contract_sha256', 'type': 'bytes[32]'}, {'name': 'calibration_ood_asset_sha256', 'type': 'bytes[32]'}], 'runtime_binding_required_before_final_freeze': True}

class TargetKind(IntEnum):
    NoTarget = 0
    Entity = 1
    SoundEvent = 2
    LastKnownPosition = 3
    CoverSlot = 4
    SmartObject = 5
    Waypoint = 6
    WorldPosition = 7

class SkillId(IntEnum):
    Idle = 0
    ContinueCurrentAction = 1
    LookAt = 2
    TurnTo = 3
    Approach = 4
    KeepDistance = 5
    RetreatFrom = 6
    Follow = 7
    Investigate = 8
    SearchArea = 9
    Greet = 10
    Warn = 11
    CallForHelp = 12
    TakeCover = 13
    Flee = 14
    Attack = 15

class GoalType(IntEnum):
    None_ = 0
    IdleObserve = 1
    InvestigateDisturbance = 2
    EnforceBoundary = 3
    CombatEngage = 4
    Disengage = 5
    Escort = 6
    Reserved = 7

class GoalPhase(IntEnum):
    None_ = 0
    Observe = 1
    Orient = 2
    Navigate = 3
    Interact = 4
    Search = 5
    Resolve = 6
    Return = 7

class EventType(IntEnum):
    NoneOrPadding = 0
    SightAcquired = 1
    SightLost = 2
    SoundHeard = 3
    Damaged = 4
    SkillSucceeded = 5
    SkillFailed = 6
    SkillInterrupted = 7
    WarningIssued = 8
    WarningIgnored = 9
    TargetMovedSignificantly = 10
    TargetInvalidated = 11
    GoalChanged = 12
    ReservationLost = 13
    SharedKnowledgeReceived = 14
    Other = 15

class GoalSourcePriority(IntEnum):
    Routine = 0
    Social = 1
    Combat = 2
    Quest = 3
    Emergency = 4

class GlobalFeature(IntEnum):
    self_health_norm = 0
    self_stamina_norm = 1
    self_speed_norm = 2
    self_local_velocity_x = 3
    self_local_velocity_y = 4
    self_local_velocity_z = 5
    self_local_acceleration_x = 6
    self_local_acceleration_y = 7
    self_local_acceleration_z = 8
    self_yaw_rate_norm = 9
    self_grounded = 10
    self_crouched = 11
    self_sprinting = 12
    self_in_combat = 13
    self_damaged_recently = 14
    self_recent_damage_norm = 15
    current_skill_Idle = 16
    current_skill_ContinueCurrentAction_reserved_zero = 17
    current_skill_LookAt = 18
    current_skill_TurnTo = 19
    current_skill_Approach = 20
    current_skill_KeepDistance = 21
    current_skill_RetreatFrom = 22
    current_skill_Follow = 23
    current_skill_Investigate = 24
    current_skill_SearchArea = 25
    current_skill_Greet = 26
    current_skill_Warn = 27
    current_skill_CallForHelp = 28
    current_skill_TakeCover = 29
    current_skill_Flee = 30
    current_skill_Attack = 31
    skill_elapsed_norm = 32
    skill_progress_norm = 33
    skill_min_duration_remaining_norm = 34
    skill_interruptible_now = 35
    skill_has_target = 36
    skill_target_still_believed_valid = 37
    last_skill_result_success = 38
    last_skill_result_failure = 39
    personality_aggression = 40
    personality_courage = 41
    personality_curiosity = 42
    personality_loyalty = 43
    personality_sociability = 44
    personality_impulsivity = 45
    personality_patience = 46
    personality_vigilance = 47
    personality_altruism = 48
    personality_rule_adherence = 49
    emotion_fear = 50
    emotion_anger = 51
    emotion_suspicion = 52
    emotion_curiosity = 53
    emotion_tension = 54
    emotion_affection = 55
    emotion_confusion = 56
    emotion_confidence = 57
    relationship_affinity = 58
    relationship_trust = 59
    relationship_respect = 60
    relationship_fear = 61
    relationship_debt = 62
    relationship_suspicion = 63
    relationship_loyalty = 64
    relationship_hostility = 65
    role_combatant = 66
    role_guard = 67
    role_civilian = 68
    role_companion = 69
    role_support = 70
    role_authority_level = 71
    role_social_authority = 72
    role_territory_ownership = 73
    role_mission_importance = 74
    role_risk_tolerance = 75
    goal_type_None = 76
    goal_type_IdleObserve = 77
    goal_type_InvestigateDisturbance = 78
    goal_type_EnforceBoundary = 79
    goal_type_CombatEngage = 80
    goal_type_Disengage = 81
    goal_type_Escort = 82
    goal_type_Reserved = 83
    goal_phase_None = 84
    goal_phase_Observe = 85
    goal_phase_Orient = 86
    goal_phase_Navigate = 87
    goal_phase_Interact = 88
    goal_phase_Search = 89
    goal_phase_Resolve = 90
    goal_phase_Return = 91
    goal_priority_norm = 92
    goal_time_in_phase_norm = 93
    goal_deadline_remaining_norm = 94
    goal_progress_norm = 95
    goal_interruptible = 96
    goal_has_primary_target = 97
    allowed_skill_fraction = 98
    forbidden_skill_fraction = 99
    world_safe_zone = 100
    world_restricted_zone = 101
    world_indoors = 102
    world_combat_allowed = 103
    world_perceived_ally_count_norm = 104
    world_perceived_hostile_count_norm = 105
    world_light_level_norm = 106
    world_crowd_density_norm = 107
    recent_sound_count_norm = 108
    recent_sight_change_count_norm = 109
    recent_damage_count_norm = 110
    recent_skill_failure_count_norm = 111
    recent_target_switch_count_norm = 112
    recent_warning_count_norm = 113
    recent_reservation_conflict_count_norm = 114
    event_buffer_fill_ratio = 115
    reserved_116 = 116
    reserved_117 = 117
    reserved_118 = 118
    reserved_119 = 119
    reserved_120 = 120
    reserved_121 = 121
    reserved_122 = 122
    reserved_123 = 123
    reserved_124 = 124
    reserved_125 = 125
    reserved_126 = 126
    reserved_127 = 127

class TargetCommonFeature(IntEnum):
    relative_position_x = 0
    relative_position_y = 1
    relative_position_z = 2
    distance_3d_norm = 3
    distance_planar_norm = 4
    log_distance_norm = 5
    bearing_sin = 6
    bearing_cos = 7
    elevation_sin = 8
    elevation_cos = 9
    relative_velocity_x = 10
    relative_velocity_y = 11
    relative_velocity_z = 12
    closing_speed_norm = 13
    path_distance_norm = 14
    path_reachable_belief = 15
    belief_age_norm = 16
    belief_confidence = 17
    source_sight = 18
    source_hearing = 19
    source_last_known = 20
    source_shared = 21
    source_scripted = 22
    position_valid = 23
    visible_now = 24
    line_of_sight_belief = 25
    sight_strength = 26
    visible_duration_norm = 27
    heard_recently = 28
    hearing_strength = 29
    time_since_seen_norm = 30
    time_since_heard_norm = 31

class EventFeature(IntEnum):
    age_norm = 0
    strength = 1
    confidence = 2
    relative_position_x = 3
    relative_position_y = 4
    relative_position_z = 5
    distance_norm = 6
    bearing_sin = 7
    bearing_cos = 8
    source_sight = 9
    source_hearing = 10
    source_damage = 11
    source_scripted = 12
    result_success = 13
    result_failure = 14
    result_interrupted = 15
    urgent = 16
    target_present_in_current_slots = 17
    same_as_current_skill_target = 18
    same_goal_revision = 19
    magnitude_norm = 20
    duration_norm = 21
    reserved_22 = 22
    reserved_23 = 23

class CandidatePairFeature(IntEnum):
    same_as_current_skill = 0
    same_as_current_target = 1
    target_present = 2
    target_visible_now = 3
    target_position_confidence = 4
    target_age_norm = 5
    distance_norm = 6
    path_distance_norm = 7
    path_reachable_belief = 8
    skill_requires_los = 9
    los_satisfied_belief = 10
    skill_requires_resource = 11
    resource_available_belief = 12
    skill_allowed_by_goal = 13
    target_kind_allowed = 14
    default_parameter_norm = 15

class NoTargetPayloadFeature(IntEnum):
    zero_0 = 0
    zero_1 = 1
    zero_2 = 2
    zero_3 = 3
    zero_4 = 4
    zero_5 = 5
    zero_6 = 6
    zero_7 = 7
    zero_8 = 8
    zero_9 = 9
    zero_10 = 10
    zero_11 = 11
    zero_12 = 12
    zero_13 = 13
    zero_14 = 14
    zero_15 = 15

class EntityPayloadFeature(IntEnum):
    alive_probability = 0
    armed_probability = 1
    attacking_probability = 2
    health_estimate = 3
    health_uncertainty = 4
    threat_estimate = 5
    interactable = 6
    same_faction_probability = 7
    affinity = 8
    trust = 9
    fear = 10
    hostility = 11
    debt = 12
    suspicion = 13
    current_action_confidence = 14
    identity_confidence = 15

class SoundEventPayloadFeature(IntEnum):
    loudness = 0
    danger_estimate = 1
    attribution_confidence = 2
    repetition_norm = 3
    class_footstep = 4
    class_weapon = 5
    class_explosion = 6
    class_voice = 7
    class_impact = 8
    class_door = 9
    class_vehicle = 10
    class_other = 11
    source_moving_probability = 12
    occluded_probability = 13
    ttl_remaining_norm = 14
    reserved = 15

class LastKnownPositionPayloadFeature(IntEnum):
    subject_is_player = 0
    subject_hostile_probability = 1
    subject_armed_probability = 2
    subject_alive_probability_at_observation = 3
    motion_direction_sin = 4
    motion_direction_cos = 5
    observed_speed_norm = 6
    reason_sight_lost = 7
    reason_shared = 8
    reason_scripted = 9
    goal_primary_target = 10
    search_radius_norm = 11
    confidence_decay_rate_norm = 12
    ttl_remaining_norm = 13
    subject_identity_confidence = 14
    reserved = 15

class CoverSlotPayloadFeature(IntEnum):
    cover_quality = 0
    exposure_reduction = 1
    flank_risk = 2
    distance_to_peek_norm = 3
    occupancy_ratio = 4
    available_belief = 5
    reserved_by_self = 6
    resource_generation_valid = 7
    low_cover = 8
    high_cover = 9
    left_peek = 10
    right_peek = 11
    destructible_probability = 12
    hazard_norm = 13
    lease_required = 14
    resource_age_norm = 15

class SmartObjectPayloadFeature(IntEnum):
    availability_belief = 0
    capacity_norm = 1
    occupancy_ratio = 2
    interaction_duration_norm = 3
    requires_item = 4
    hazard_norm = 5
    use_type_door = 6
    use_type_console = 7
    use_type_pickup = 8
    use_type_heal = 9
    use_type_vehicle = 10
    use_type_social = 11
    use_type_traversal = 12
    use_type_other = 13
    resource_generation_valid = 14
    resource_age_norm = 15

class WaypointPayloadFeature(IntEnum):
    goal_primary = 0
    goal_secondary = 1
    sequence_progress = 2
    wait_duration_norm = 3
    desired_facing_sin = 4
    desired_facing_cos = 5
    patrol_waypoint = 6
    return_point = 7
    search_point = 8
    escape_point = 9
    formation_point = 10
    scripted_point = 11
    path_index_norm = 12
    loop_flag = 13
    arrival_radius_norm = 14
    reserved = 15

class WorldPositionPayloadFeature(IntEnum):
    goal_primary = 0
    goal_secondary = 1
    safe_zone_probability = 2
    hazard_norm = 3
    search_radius_norm = 4
    arrival_radius_norm = 5
    desired_facing_sin = 6
    desired_facing_cos = 7
    source_goal = 8
    source_script = 9
    source_shared_knowledge = 10
    source_player_ping = 11
    immutable_flag = 12
    ttl_remaining_norm = 13
    authority_valid = 14
    reserved = 15

@dataclass(frozen=True)
class TargetHandle:
    kind: int
    stable_id: int
    generation: int
    revision: int

    def canonical_bytes(self) -> bytes:
        values = {"kind": self.kind, "stable_id": self.stable_id, "generation": self.generation, "revision": self.revision}
        return b"".join(_pack_unsigned(values[name], typ, CANDIDATE_HASH_CONTRACT["byte_order"]) for name, typ in (x.split(":", 1) for x in TARGET_HANDLE_FIELD_ORDER))


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
        fmt = formats[(type_name, byte_order)]
    except KeyError as exc:
        raise ValueError(f"unsupported integer type/order {type_name}/{byte_order}") from exc
    return struct.pack(fmt, int(value))


def _digest_bytes(value: str, size: int, name: str) -> bytes:
    raw = bytes.fromhex(value)
    if len(raw) != size:
        raise ValueError(f"{name} must be {size} bytes")
    return raw


def candidate_index(skill_id: int, target_slot: int) -> int:
    if not 0 <= skill_id < CONSTANTS["skill_count"]:
        raise ValueError("skill_id")
    if not 0 <= target_slot < CONSTANTS["total_target_slots"]:
        raise ValueError("target_slot")
    return skill_id * CONSTANTS["total_target_slots"] + target_slot


def round_half_away_from_zero(value: float) -> int:
    return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))


def quantize_confidence(value: float) -> int:
    x = min(1.0, max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_confidence_scale"])


def quantize_age_seconds(value: float) -> int:
    x = min(CONSTANTS["target_age_max_s"], max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_age_centisecond_scale"])


def quantize_distance_cm(value: float) -> int:
    x = min(CONSTANTS["spatial_max_cm"], max(0.0, float(value)))
    return round_half_away_from_zero(x / CONSTANTS["slotter_distance_bin_cm"])


def quantize_loudness(value: float) -> int:
    x = min(1.0, max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_loudness_scale"])


def pack_bits_lsb_first(bits: list[bool], bit_count: int) -> bytes:
    if len(bits) != bit_count:
        raise ValueError(f"expected {bit_count} bits")
    out = bytearray((bit_count + 7) // 8)
    for index, flag in enumerate(bits):
        if flag:
            out[index // 8] |= 1 << (index % 8)
    return bytes(out)


def candidate_set_canonical_bytes(handles: list[TargetHandle], target_mask: list[bool], candidate_mask: list[bool]) -> bytes:
    raw = bytearray()
    for field in CANDIDATE_HASH_CONTRACT["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(typ, "bytes"):
                raise ValueError("candidate magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, CANDIDATE_HASH_CONTRACT["byte_order"])
        elif name == "schema_source_sha256":
            raw += _digest_bytes(SCHEMA_SOURCE_SHA256, _array_count(typ, "bytes"), name)
        elif name == "target_slot_count":
            raw += _pack_unsigned(CONSTANTS[field["value_ref"]], typ, CANDIDATE_HASH_CONTRACT["byte_order"])
        elif name == "target_handles":
            count = _array_count(typ, "target_handle")
            if len(handles) != count:
                raise ValueError("handles")
            for handle in handles:
                raw += handle.canonical_bytes()
        elif name == "target_mask":
            raw += pack_bits_lsb_first(target_mask, int(field["bit_count"]))
        elif name == "candidate_mask":
            raw += pack_bits_lsb_first(candidate_mask, int(field["bit_count"]))
        else:
            raise ValueError(f"unsupported candidate hash field {name}")
    return bytes(raw)


def candidate_set_hash(handles: list[TargetHandle], target_mask: list[bool], candidate_mask: list[bool]) -> str:
    return hashlib.sha256(candidate_set_canonical_bytes(handles, target_mask, candidate_mask)).hexdigest()


def decision_contract_canonical_bytes(digests: Mapping[str, str]) -> bytes:
    raw = bytearray()
    for field in DECISION_HASH_CONTRACT["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(typ, "bytes"):
                raise ValueError("decision magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, DECISION_HASH_CONTRACT["byte_order"])
        else:
            raw += _digest_bytes(digests[name], _array_count(typ, "bytes"), name)
    return bytes(raw)


def decision_contract_hash(digests: Mapping[str, str]) -> str:
    return hashlib.sha256(decision_contract_canonical_bytes(digests)).hexdigest()


def decode_parameter(skill_id: int, slot: int, normalized: float) -> float:
    spec = SKILL_PARAMETER_CONTRACTS[int(skill_id)][int(slot)]
    if not spec["active"]:
        return float(spec["default"])
    normalized_value = min(1.0, max(0.0, float(normalized)))
    value = float(spec["min"]) + normalized_value * (float(spec["max"]) - float(spec["min"]))
    return min(float(spec["max"]), max(float(spec["min"]), value))


def apply_normalizer_spec(spec: dict, value: float | None, sentinel_matched: bool = False) -> float:
    typ = spec["type"]
    x = 0.0 if value is None else float(value)
    if typ == "constant":
        return float(spec["p0"])
    if typ == "boolean":
        return 1.0 if bool(value) else 0.0
    if typ == "clamp":
        return min(float(spec["max"]), max(float(spec["min"]), x))
    if typ == "divide_clamp":
        return min(float(spec["max"]), max(float(spec["min"]), x / float(spec["p0"])))
    if typ == "trigonometric":
        return math.sin(x) if float(spec["p0"]) == 0.0 else math.cos(x)
    if typ == "log1p_ratio":
        x = min(float(spec["p1"]), max(float(spec["p0"]), x))
        return math.log1p(x) / math.log1p(float(spec["p2"]))
    if typ == "sentinel_divide_clamp":
        if sentinel_matched:
            return float(spec["p1"])
        return min(float(spec["max"]), max(float(spec["min"]), x / float(spec["p0"])))
    raise ValueError(typ)


def normalize_global(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["global"][index], value, sentinel_matched)


def normalize_target_common(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["target_common"][index], value, sentinel_matched)


def normalize_target_payload(kind: int, index: int, value: float | None, sentinel_matched: bool = False) -> float:
    name = TargetKind(int(kind)).name
    return apply_normalizer_spec(NORMALIZER_TABLES["target_payload"][name][index], value, sentinel_matched)


def normalize_event(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["event"][index], value, sentinel_matched)


def normalize_candidate_pair(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["candidate_pair"][index], value, sentinel_matched)
