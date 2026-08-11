"""AUTO-GENERATED. DO NOT EDIT. Approved General NPC Skill execution semantics V1."""
from __future__ import annotations
import math

SKILL_REGISTRY_SHA256 = 'ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d'
EVALUATION_INTERVAL_SECONDS = 0.050000000000000003
INTENSITY_SPEED_BASE = 0.5
INTENSITY_SPEED_SCALE = 0.5
NAV_PROJECTION_HORIZONTAL_CM = 100
NAV_PROJECTION_VERTICAL_CM = 200
SKILL_EXECUTION_SEMANTICS = {3: {'skill_id': 3, 'target_position_policy': 'frozen_execution_start_position', 'planar_coincident_distance_cm': 1.0, 'facing_tolerance_degrees': 5.0, 'success_stable_seconds': 0.1, 'rotation_axis': 'yaw_only', 'root_motion_policy': 'fail_movement_mode_unsupported', 'timeout_result': 'TimedOut'}, 4: {'skill_id': 4, 'target_position_policy': 'frozen_execution_start_position', 'success_distance': 'planar_center_to_frozen_target_lte_preferred_distance', 'already_inside_policy': 'succeed_without_move', 'completion_recheck': 'recompute_planar_distance', 'path_failure_result': 'PathUnavailable', 'timeout_result': 'TimedOut'}, 8: {'skill_id': 8, 'target_position_policy': 'frozen_execution_start_position', 'distance_condition': 'planar_distance_lte_preferred_distance', 'facing_tolerance_degrees': 15.0, 'success_stable_seconds': 0.5, 'condition_loss_policy': 'reset_stable_time_to_zero', 'base_turn_speed_degrees_per_second': 360.0, 'success_meaning': 'arrived_faced_and_observed_not_evidence_found', 'path_failure_result': 'PathUnavailable', 'timeout_result': 'TimedOut'}, 9: {'skill_id': 9, 'target_position_policy': 'frozen_execution_start_center', 'basis': 'world_positive_x_positive_y', 'point_acceptance_radius_cm': 100.0, 'revisit_policy': 'no_revisit_per_execution', 'invalid_point_policy': 'skip', 'all_points_invalid_result': 'PathUnavailable', 'deadline_without_visited_point_result': 'TimedOut', 'success_meaning': 'allocated_area_checked_not_evidence_found', 'normalized_offsets': [[0.0, 0.0], [0.5, 0.0], [0.0, 0.5], [-0.5, 0.0], [0.0, -0.5], [0.7071067811865476, 0.7071067811865476], [-0.7071067811865476, 0.7071067811865476], [-0.7071067811865476, -0.7071067811865476], [0.7071067811865476, -0.7071067811865476]]}}
ALLOWED_TARGET_KINDS = {3: ('Entity', 'SoundEvent', 'LastKnownPosition', 'Waypoint', 'WorldPosition'), 4: ('Entity', 'LastKnownPosition', 'CoverSlot', 'SmartObject', 'Waypoint', 'WorldPosition'), 8: ('SoundEvent', 'LastKnownPosition', 'SmartObject', 'Waypoint', 'WorldPosition'), 9: ('LastKnownPosition', 'Waypoint', 'WorldPosition')}


def effective_speed(speed: float, intensity: float) -> float:
    if not math.isfinite(speed) or not math.isfinite(intensity):
        raise ValueError("speed and intensity must be finite")
    if not 0.0 <= intensity <= 1.0:
        raise ValueError("intensity must be in [0, 1]")
    return speed * (INTENSITY_SPEED_BASE + INTENSITY_SPEED_SCALE * intensity)
