// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace AINativeNPC::SchemaV2 {
inline constexpr const char* SchemaVersion = "2.0.0";
inline constexpr const char* ContractRevision = "2.0.0-rc5";
inline constexpr const char* SchemaSourceSha256 = "8c72e1a6aa94399b5748c3ec7bfdaf31beb7148cc5f228eb86c88cee60b67baf";
inline constexpr const char* SkillRegistrySha256 = "08141111029cc43aa7abe6c52668719fd3d5f1927fc497a7c122ce22d83665d8";
inline constexpr const char* GoalRegistrySha256 = "b6ed883e39f8da4f792b2ad4542b4cf7045ff5fe00147a9eba15eac61fa67ac2";
inline constexpr std::array<std::uint8_t, 32> SchemaSourceSha256Bytes{{0x8c, 0x72, 0xe1, 0xa6, 0xaa, 0x94, 0x39, 0x9b, 0x57, 0x48, 0xc3, 0xec, 0x7b, 0xfd, 0xaf, 0x31, 0xbe, 0xb7, 0x14, 0x8c, 0xc5, 0xf2, 0x28, 0xeb, 0x86, 0xc8, 0x8c, 0xee, 0x60, 0xb6, 0x7b, 0xaf}};
inline constexpr std::array<std::uint8_t, 8> CandidateHashMagic{{65, 78, 80, 67, 83, 69, 84, 50}};
inline constexpr std::uint16_t CandidateHashSerializationVersion = 1U;
inline constexpr std::array<std::uint8_t, 8> DecisionHashMagic{{65, 78, 80, 67, 68, 69, 67, 50}};
inline constexpr std::uint16_t DecisionHashSerializationVersion = 1U;
inline constexpr std::size_t RegularTargetSlots = 16;
inline constexpr std::size_t NoTargetSlot = 16;
inline constexpr std::size_t TotalTargetSlots = 17;
inline constexpr std::size_t SkillCount = 16;
inline constexpr std::size_t CandidateCount = 272;
inline constexpr std::size_t EventSlots = 12;
inline constexpr std::size_t GlobalFeatureCount = 128;
inline constexpr std::size_t TargetFeatureCount = 48;
inline constexpr std::size_t EventFeatureCount = 24;
inline constexpr std::size_t CandidatePairFeatureCount = 16;
inline constexpr double SpatialMaxCm = 5000;
inline constexpr double TargetAgeMaxS = 10;
inline constexpr double SlotterConfidenceScale = 1000;
inline constexpr double SlotterAgeCentisecondScale = 100;
inline constexpr double SlotterDistanceBinCm = 10;
inline constexpr double SlotterLoudnessScale = 1000;

enum class ETargetKind : std::uint8_t {
    NoTarget = 0,
    Entity = 1,
    SoundEvent = 2,
    LastKnownPosition = 3,
    CoverSlot = 4,
    SmartObject = 5,
    Waypoint = 6,
    WorldPosition = 7,
};

enum class ESkillId : std::uint8_t {
    Idle = 0,
    ContinueCurrentAction = 1,
    LookAt = 2,
    TurnTo = 3,
    Approach = 4,
    KeepDistance = 5,
    RetreatFrom = 6,
    Follow = 7,
    Investigate = 8,
    SearchArea = 9,
    Greet = 10,
    Warn = 11,
    CallForHelp = 12,
    TakeCover = 13,
    Flee = 14,
    Attack = 15,
};

enum class EGoalType : std::uint8_t {
    None = 0,
    IdleObserve = 1,
    InvestigateDisturbance = 2,
    EnforceBoundary = 3,
    CombatEngage = 4,
    Disengage = 5,
    Escort = 6,
    Reserved = 7,
};

enum class EGoalPhase : std::uint8_t {
    None = 0,
    Observe = 1,
    Orient = 2,
    Navigate = 3,
    Interact = 4,
    Search = 5,
    Resolve = 6,
    Return = 7,
};

enum class EEventType : std::uint8_t {
    NoneOrPadding = 0,
    SightAcquired = 1,
    SightLost = 2,
    SoundHeard = 3,
    Damaged = 4,
    SkillSucceeded = 5,
    SkillFailed = 6,
    SkillInterrupted = 7,
    WarningIssued = 8,
    WarningIgnored = 9,
    TargetMovedSignificantly = 10,
    TargetInvalidated = 11,
    GoalChanged = 12,
    ReservationLost = 13,
    SharedKnowledgeReceived = 14,
    Other = 15,
};

enum class EGoalSourcePriority : std::uint8_t {
    Routine = 0,
    Social = 1,
    Combat = 2,
    Quest = 3,
    Emergency = 4,
};

enum class EGlobalFeature : std::uint16_t {
    self_health_norm = 0,
    self_stamina_norm = 1,
    self_speed_norm = 2,
    self_local_velocity_x = 3,
    self_local_velocity_y = 4,
    self_local_velocity_z = 5,
    self_local_acceleration_x = 6,
    self_local_acceleration_y = 7,
    self_local_acceleration_z = 8,
    self_yaw_rate_norm = 9,
    self_grounded = 10,
    self_crouched = 11,
    self_sprinting = 12,
    self_in_combat = 13,
    self_damaged_recently = 14,
    self_recent_damage_norm = 15,
    current_skill_Idle = 16,
    current_skill_ContinueCurrentAction_reserved_zero = 17,
    current_skill_LookAt = 18,
    current_skill_TurnTo = 19,
    current_skill_Approach = 20,
    current_skill_KeepDistance = 21,
    current_skill_RetreatFrom = 22,
    current_skill_Follow = 23,
    current_skill_Investigate = 24,
    current_skill_SearchArea = 25,
    current_skill_Greet = 26,
    current_skill_Warn = 27,
    current_skill_CallForHelp = 28,
    current_skill_TakeCover = 29,
    current_skill_Flee = 30,
    current_skill_Attack = 31,
    skill_elapsed_norm = 32,
    skill_progress_norm = 33,
    skill_min_duration_remaining_norm = 34,
    skill_interruptible_now = 35,
    skill_has_target = 36,
    skill_target_still_believed_valid = 37,
    last_skill_result_success = 38,
    last_skill_result_failure = 39,
    personality_aggression = 40,
    personality_courage = 41,
    personality_curiosity = 42,
    personality_loyalty = 43,
    personality_sociability = 44,
    personality_impulsivity = 45,
    personality_patience = 46,
    personality_vigilance = 47,
    personality_altruism = 48,
    personality_rule_adherence = 49,
    emotion_fear = 50,
    emotion_anger = 51,
    emotion_suspicion = 52,
    emotion_curiosity = 53,
    emotion_tension = 54,
    emotion_affection = 55,
    emotion_confusion = 56,
    emotion_confidence = 57,
    relationship_affinity = 58,
    relationship_trust = 59,
    relationship_respect = 60,
    relationship_fear = 61,
    relationship_debt = 62,
    relationship_suspicion = 63,
    relationship_loyalty = 64,
    relationship_hostility = 65,
    role_combatant = 66,
    role_guard = 67,
    role_civilian = 68,
    role_companion = 69,
    role_support = 70,
    role_authority_level = 71,
    role_social_authority = 72,
    role_territory_ownership = 73,
    role_mission_importance = 74,
    role_risk_tolerance = 75,
    goal_type_None = 76,
    goal_type_IdleObserve = 77,
    goal_type_InvestigateDisturbance = 78,
    goal_type_EnforceBoundary = 79,
    goal_type_CombatEngage = 80,
    goal_type_Disengage = 81,
    goal_type_Escort = 82,
    goal_type_Reserved = 83,
    goal_phase_None = 84,
    goal_phase_Observe = 85,
    goal_phase_Orient = 86,
    goal_phase_Navigate = 87,
    goal_phase_Interact = 88,
    goal_phase_Search = 89,
    goal_phase_Resolve = 90,
    goal_phase_Return = 91,
    goal_priority_norm = 92,
    goal_time_in_phase_norm = 93,
    goal_deadline_remaining_norm = 94,
    goal_progress_norm = 95,
    goal_interruptible = 96,
    goal_has_primary_target = 97,
    allowed_skill_fraction = 98,
    forbidden_skill_fraction = 99,
    world_safe_zone = 100,
    world_restricted_zone = 101,
    world_indoors = 102,
    world_combat_allowed = 103,
    world_perceived_ally_count_norm = 104,
    world_perceived_hostile_count_norm = 105,
    world_light_level_norm = 106,
    world_crowd_density_norm = 107,
    recent_sound_count_norm = 108,
    recent_sight_change_count_norm = 109,
    recent_damage_count_norm = 110,
    recent_skill_failure_count_norm = 111,
    recent_target_switch_count_norm = 112,
    recent_warning_count_norm = 113,
    recent_reservation_conflict_count_norm = 114,
    event_buffer_fill_ratio = 115,
    reserved_116 = 116,
    reserved_117 = 117,
    reserved_118 = 118,
    reserved_119 = 119,
    reserved_120 = 120,
    reserved_121 = 121,
    reserved_122 = 122,
    reserved_123 = 123,
    reserved_124 = 124,
    reserved_125 = 125,
    reserved_126 = 126,
    reserved_127 = 127,
};

enum class ETargetCommonFeature : std::uint16_t {
    relative_position_x = 0,
    relative_position_y = 1,
    relative_position_z = 2,
    distance_3d_norm = 3,
    distance_planar_norm = 4,
    log_distance_norm = 5,
    bearing_sin = 6,
    bearing_cos = 7,
    elevation_sin = 8,
    elevation_cos = 9,
    relative_velocity_x = 10,
    relative_velocity_y = 11,
    relative_velocity_z = 12,
    closing_speed_norm = 13,
    path_distance_norm = 14,
    path_reachable_belief = 15,
    belief_age_norm = 16,
    belief_confidence = 17,
    source_sight = 18,
    source_hearing = 19,
    source_last_known = 20,
    source_shared = 21,
    source_scripted = 22,
    position_valid = 23,
    visible_now = 24,
    line_of_sight_belief = 25,
    sight_strength = 26,
    visible_duration_norm = 27,
    heard_recently = 28,
    hearing_strength = 29,
    time_since_seen_norm = 30,
    time_since_heard_norm = 31,
};

enum class EEventFeature : std::uint16_t {
    age_norm = 0,
    strength = 1,
    confidence = 2,
    relative_position_x = 3,
    relative_position_y = 4,
    relative_position_z = 5,
    distance_norm = 6,
    bearing_sin = 7,
    bearing_cos = 8,
    source_sight = 9,
    source_hearing = 10,
    source_damage = 11,
    source_scripted = 12,
    result_success = 13,
    result_failure = 14,
    result_interrupted = 15,
    urgent = 16,
    target_present_in_current_slots = 17,
    same_as_current_skill_target = 18,
    same_goal_revision = 19,
    magnitude_norm = 20,
    duration_norm = 21,
    reserved_22 = 22,
    reserved_23 = 23,
};

enum class ECandidatePairFeature : std::uint16_t {
    same_as_current_skill = 0,
    same_as_current_target = 1,
    target_present = 2,
    target_visible_now = 3,
    target_position_confidence = 4,
    target_age_norm = 5,
    distance_norm = 6,
    path_distance_norm = 7,
    path_reachable_belief = 8,
    skill_requires_los = 9,
    los_satisfied_belief = 10,
    skill_requires_resource = 11,
    resource_available_belief = 12,
    skill_allowed_by_goal = 13,
    target_kind_allowed = 14,
    default_parameter_norm = 15,
};

enum class ENoTargetPayloadFeature : std::uint16_t {
    zero_0 = 0,
    zero_1 = 1,
    zero_2 = 2,
    zero_3 = 3,
    zero_4 = 4,
    zero_5 = 5,
    zero_6 = 6,
    zero_7 = 7,
    zero_8 = 8,
    zero_9 = 9,
    zero_10 = 10,
    zero_11 = 11,
    zero_12 = 12,
    zero_13 = 13,
    zero_14 = 14,
    zero_15 = 15,
};

enum class EEntityPayloadFeature : std::uint16_t {
    alive_probability = 0,
    armed_probability = 1,
    attacking_probability = 2,
    health_estimate = 3,
    health_uncertainty = 4,
    threat_estimate = 5,
    interactable = 6,
    same_faction_probability = 7,
    affinity = 8,
    trust = 9,
    fear = 10,
    hostility = 11,
    debt = 12,
    suspicion = 13,
    current_action_confidence = 14,
    identity_confidence = 15,
};

enum class ESoundEventPayloadFeature : std::uint16_t {
    loudness = 0,
    danger_estimate = 1,
    attribution_confidence = 2,
    repetition_norm = 3,
    class_footstep = 4,
    class_weapon = 5,
    class_explosion = 6,
    class_voice = 7,
    class_impact = 8,
    class_door = 9,
    class_vehicle = 10,
    class_other = 11,
    source_moving_probability = 12,
    occluded_probability = 13,
    ttl_remaining_norm = 14,
    reserved = 15,
};

enum class ELastKnownPositionPayloadFeature : std::uint16_t {
    subject_is_player = 0,
    subject_hostile_probability = 1,
    subject_armed_probability = 2,
    subject_alive_probability_at_observation = 3,
    motion_direction_sin = 4,
    motion_direction_cos = 5,
    observed_speed_norm = 6,
    reason_sight_lost = 7,
    reason_shared = 8,
    reason_scripted = 9,
    goal_primary_target = 10,
    search_radius_norm = 11,
    confidence_decay_rate_norm = 12,
    ttl_remaining_norm = 13,
    subject_identity_confidence = 14,
    reserved = 15,
};

enum class ECoverSlotPayloadFeature : std::uint16_t {
    cover_quality = 0,
    exposure_reduction = 1,
    flank_risk = 2,
    distance_to_peek_norm = 3,
    occupancy_ratio = 4,
    available_belief = 5,
    reserved_by_self = 6,
    resource_generation_valid = 7,
    low_cover = 8,
    high_cover = 9,
    left_peek = 10,
    right_peek = 11,
    destructible_probability = 12,
    hazard_norm = 13,
    lease_required = 14,
    resource_age_norm = 15,
};

enum class ESmartObjectPayloadFeature : std::uint16_t {
    availability_belief = 0,
    capacity_norm = 1,
    occupancy_ratio = 2,
    interaction_duration_norm = 3,
    requires_item = 4,
    hazard_norm = 5,
    use_type_door = 6,
    use_type_console = 7,
    use_type_pickup = 8,
    use_type_heal = 9,
    use_type_vehicle = 10,
    use_type_social = 11,
    use_type_traversal = 12,
    use_type_other = 13,
    resource_generation_valid = 14,
    resource_age_norm = 15,
};

enum class EWaypointPayloadFeature : std::uint16_t {
    goal_primary = 0,
    goal_secondary = 1,
    sequence_progress = 2,
    wait_duration_norm = 3,
    desired_facing_sin = 4,
    desired_facing_cos = 5,
    patrol_waypoint = 6,
    return_point = 7,
    search_point = 8,
    escape_point = 9,
    formation_point = 10,
    scripted_point = 11,
    path_index_norm = 12,
    loop_flag = 13,
    arrival_radius_norm = 14,
    reserved = 15,
};

enum class EWorldPositionPayloadFeature : std::uint16_t {
    goal_primary = 0,
    goal_secondary = 1,
    safe_zone_probability = 2,
    hazard_norm = 3,
    search_radius_norm = 4,
    arrival_radius_norm = 5,
    desired_facing_sin = 6,
    desired_facing_cos = 7,
    source_goal = 8,
    source_script = 9,
    source_shared_knowledge = 10,
    source_player_ping = 11,
    immutable_flag = 12,
    ttl_remaining_norm = 13,
    authority_valid = 14,
    reserved = 15,
};

struct FTargetHandleWire {
    ETargetKind Kind{ETargetKind::NoTarget};
    std::uint64_t StableId{0};
    std::uint32_t Generation{0};
    std::uint64_t Revision{0};
};

struct FSkillParameterSpec { bool Active; double Min; double Max; double Default; };

enum class ENormalizerType : std::uint8_t { Constant, Boolean, Clamp, DivideClamp, Trigonometric, Log1pRatio, SentinelDivideClamp };
struct FNormalizerSpec { ENormalizerType Type; double Min; double Max; double P0; double P1; double P2; };

inline constexpr std::size_t CandidateIndex(std::size_t SkillId, std::size_t TargetSlot) { return SkillId * TotalTargetSlots + TargetSlot; }

inline constexpr std::array<std::array<FSkillParameterSpec, 4>, SkillCount> SkillParameterSpecs{{
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.5, 5, 1}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.25, 3, 1}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.25, 2, 0.75}, FSkillParameterSpec{true, 90, 720, 360}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.5, 10, 3}, FSkillParameterSpec{true, 150, 600, 350}, FSkillParameterSpec{true, 100, 500, 200}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.5, 10, 3}, FSkillParameterSpec{true, 150, 600, 300}, FSkillParameterSpec{true, 200, 1000, 500}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.5, 10, 3}, FSkillParameterSpec{true, 150, 650, 400}, FSkillParameterSpec{true, 300, 1500, 700}, FSkillParameterSpec{true, 0, 1, 0.69999999999999996}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.5, 10, 4}, FSkillParameterSpec{true, 150, 600, 350}, FSkillParameterSpec{true, 150, 700, 350}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 12, 5}, FSkillParameterSpec{true, 100, 500, 280}, FSkillParameterSpec{true, 100, 1200, 400}, FSkillParameterSpec{true, 0, 1, 0.59999999999999998}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 3, 20, 8}, FSkillParameterSpec{true, 80, 400, 220}, FSkillParameterSpec{true, 200, 2000, 700}, FSkillParameterSpec{true, 0, 1, 0.59999999999999998}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 5, 2}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.5}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 5, 2}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.69999999999999996}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 4, 2}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.80000000000000004}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 10, 4}, FSkillParameterSpec{true, 150, 650, 400}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 0, 1, 0.69999999999999996}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 1, 15, 6}, FSkillParameterSpec{true, 200, 700, 500}, FSkillParameterSpec{true, 500, 3000, 1500}, FSkillParameterSpec{true, 0, 1, 0.90000000000000002}},
    std::array<FSkillParameterSpec, 4>{FSkillParameterSpec{true, 0.20000000000000001, 5, 1}, FSkillParameterSpec{false, 0, 0, 0}, FSkillParameterSpec{true, 100, 2000, 600}, FSkillParameterSpec{true, 0, 1, 0.69999999999999996}},
}};

inline constexpr std::array<FNormalizerSpec, 128> GlobalNormalizers{{
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 4000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 4000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 4000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 720, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 255, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 30, 0, 0},
    FNormalizerSpec{ENormalizerType::SentinelDivideClamp, 0, 1, 120, 1, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 16, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 16, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 8, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 12, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
}};

inline constexpr std::array<FNormalizerSpec, 32> TargetCommonNormalizers{{
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::Log1pRatio, 0, 0, 0, 5000, 5000},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 1, 0, 0},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 1, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 1200, 0, 0},
    FNormalizerSpec{ENormalizerType::SentinelDivideClamp, 0, 1, 10000, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::SentinelDivideClamp, 0, 1, 10, 1, 0},
    FNormalizerSpec{ENormalizerType::SentinelDivideClamp, 0, 1, 10, 1, 0},
}};

inline constexpr std::array<FNormalizerSpec, 24> EventNormalizers{{
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, -1, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 5000, 0, 0},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Trigonometric, 0, 0, 1, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0},
}};

inline constexpr std::array<FNormalizerSpec, 16> CandidatePairNormalizers{{
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::DivideClamp, 0, 1, 10, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0},
    FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0},
}};

inline constexpr std::array<std::array<FNormalizerSpec, 16>, 8> TargetPayloadNormalizers{{
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}},
    std::array<FNormalizerSpec, 16>{FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, -1, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Clamp, 0, 1, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Boolean, 0, 0, 0, 0, 0}, FNormalizerSpec{ENormalizerType::Constant, 0, 0, 0, 0, 0}},
}};

inline std::int64_t RoundHalfAwayFromZero(double Value) {
    return Value >= 0.0 ? static_cast<std::int64_t>(std::floor(Value + 0.5)) : static_cast<std::int64_t>(std::ceil(Value - 0.5));
}
inline std::int32_t QuantizeConfidence(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, 1.0) * SlotterConfidenceScale)); }
inline std::int32_t QuantizeAgeSeconds(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, TargetAgeMaxS) * SlotterAgeCentisecondScale)); }
inline std::int32_t QuantizeDistanceCm(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, SpatialMaxCm) / SlotterDistanceBinCm)); }
inline std::int32_t QuantizeLoudness(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, 1.0) * SlotterLoudnessScale)); }

inline double ApplyNormalizer(const FNormalizerSpec& Spec, double Value, bool SentinelMatched = false) {
    switch (Spec.Type) {
        case ENormalizerType::Constant: return Spec.P0;
        case ENormalizerType::Boolean: return Value != 0.0 ? 1.0 : 0.0;
        case ENormalizerType::Clamp: return std::clamp(Value, Spec.Min, Spec.Max);
        case ENormalizerType::DivideClamp: return std::clamp(Value / Spec.P0, Spec.Min, Spec.Max);
        case ENormalizerType::Trigonometric: return Spec.P0 == 0.0 ? std::sin(Value) : std::cos(Value);
        case ENormalizerType::Log1pRatio: { const double X = std::clamp(Value, Spec.P0, Spec.P1); return std::log1p(X) / std::log1p(Spec.P2); }
        case ENormalizerType::SentinelDivideClamp: return SentinelMatched ? Spec.P1 : std::clamp(Value / Spec.P0, Spec.Min, Spec.Max);
    }
    return 0.0;
}
inline double NormalizeGlobal(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(GlobalNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeTargetCommon(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(TargetCommonNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeTargetPayload(std::size_t Kind, std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(TargetPayloadNormalizers.at(Kind).at(Index), Value, SentinelMatched); }
inline double NormalizeEvent(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(EventNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeCandidatePair(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(CandidatePairNormalizers.at(Index), Value, SentinelMatched); }
inline double DecodeParameter(std::size_t SkillId, std::size_t Slot, double Normalized) {
    const auto& Spec = SkillParameterSpecs.at(SkillId).at(Slot);
    if (!Spec.Active) return Spec.Default;
    const double N = std::clamp(Normalized, 0.0, 1.0);
    return std::clamp(Spec.Min + N * (Spec.Max - Spec.Min), Spec.Min, Spec.Max);
}

template <typename T> inline void AppendLittleEndian(std::vector<std::uint8_t>& Out, T Value) {
    for (std::size_t I = 0; I < sizeof(T); ++I) Out.push_back(static_cast<std::uint8_t>((Value >> (I * 8U)) & static_cast<T>(0xffU)));
}
template <std::size_t N> inline std::array<std::uint8_t, (N + 7U) / 8U> PackBitsLSBFirst(const std::array<bool, N>& Bits) {
    std::array<std::uint8_t, (N + 7U) / 8U> Out{};
    for (std::size_t I = 0; I < N; ++I) if (Bits[I]) Out[I / 8U] |= static_cast<std::uint8_t>(1U << (I % 8U));
    return Out;
}

inline void AppendTargetHandle(std::vector<std::uint8_t>& Out, const FTargetHandleWire& Handle) {
    Out.push_back(static_cast<std::uint8_t>(Handle.Kind));
    AppendLittleEndian<std::uint64_t>(Out, static_cast<std::uint64_t>(Handle.StableId));
    AppendLittleEndian<std::uint32_t>(Out, static_cast<std::uint32_t>(Handle.Generation));
    AppendLittleEndian<std::uint64_t>(Out, static_cast<std::uint64_t>(Handle.Revision));
}

inline std::vector<std::uint8_t> CandidateSetCanonicalBytes(
    const std::array<FTargetHandleWire, TotalTargetSlots>& Handles,
    const std::array<bool, TotalTargetSlots>& TargetMask,
    const std::array<bool, CandidateCount>& CandidateMask) {
    std::vector<std::uint8_t> Out;
    Out.insert(Out.end(), CandidateHashMagic.begin(), CandidateHashMagic.end());
    AppendLittleEndian<std::uint16_t>(Out, CandidateHashSerializationVersion);
    Out.insert(Out.end(), SchemaSourceSha256Bytes.begin(), SchemaSourceSha256Bytes.end());
    Out.push_back(static_cast<std::uint8_t>(TotalTargetSlots));
    for (const auto& Handle : Handles) AppendTargetHandle(Out, Handle);
    const auto PackedTargets = PackBitsLSBFirst(TargetMask);
    Out.insert(Out.end(), PackedTargets.begin(), PackedTargets.end());
    const auto PackedCandidates = PackBitsLSBFirst(CandidateMask);
    Out.insert(Out.end(), PackedCandidates.begin(), PackedCandidates.end());
    return Out;
}

struct FDecisionContractDigests {
    std::array<std::uint8_t, 32> SchemaSource{};
    std::array<std::uint8_t, 32> SkillRegistry{};
    std::array<std::uint8_t, 32> GoalRegistry{};
    std::array<std::uint8_t, 32> Model{};
    std::array<std::uint8_t, 32> NormalizationContract{};
    std::array<std::uint8_t, 32> SlotterContract{};
    std::array<std::uint8_t, 32> PostprocessContract{};
    std::array<std::uint8_t, 32> CalibrationOodAsset{};
};

inline std::vector<std::uint8_t> DecisionContractCanonicalBytes(const FDecisionContractDigests& Digests) {
    std::vector<std::uint8_t> Out;
    Out.insert(Out.end(), DecisionHashMagic.begin(), DecisionHashMagic.end());
    AppendLittleEndian<std::uint16_t>(Out, DecisionHashSerializationVersion);
    Out.insert(Out.end(), Digests.SchemaSource.begin(), Digests.SchemaSource.end());
    Out.insert(Out.end(), Digests.SkillRegistry.begin(), Digests.SkillRegistry.end());
    Out.insert(Out.end(), Digests.GoalRegistry.begin(), Digests.GoalRegistry.end());
    Out.insert(Out.end(), Digests.Model.begin(), Digests.Model.end());
    Out.insert(Out.end(), Digests.NormalizationContract.begin(), Digests.NormalizationContract.end());
    Out.insert(Out.end(), Digests.SlotterContract.begin(), Digests.SlotterContract.end());
    Out.insert(Out.end(), Digests.PostprocessContract.begin(), Digests.PostprocessContract.end());
    Out.insert(Out.end(), Digests.CalibrationOodAsset.begin(), Digests.CalibrationOodAsset.end());
    return Out;
}

inline std::uint32_t RotateRight(std::uint32_t X, std::uint32_t N) { return (X >> N) | (X << (32U - N)); }
inline std::array<std::uint8_t, 32> Sha256(const std::vector<std::uint8_t>& Input) {
    static constexpr std::array<std::uint32_t, 64> K{{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U
    }};
    std::vector<std::uint8_t> Data = Input;
    const std::uint64_t BitLength = static_cast<std::uint64_t>(Data.size()) * 8U;
    Data.push_back(0x80U);
    while ((Data.size() % 64U) != 56U) Data.push_back(0U);
    for (int I = 7; I >= 0; --I) Data.push_back(static_cast<std::uint8_t>((BitLength >> (I * 8)) & 0xffU));
    std::array<std::uint32_t, 8> H{{0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U}};
    for (std::size_t Offset = 0; Offset < Data.size(); Offset += 64U) {
        std::array<std::uint32_t, 64> W{};
        for (std::size_t I = 0; I < 16U; ++I) {
            const std::size_t J = Offset + I * 4U;
            W[I] = (static_cast<std::uint32_t>(Data[J]) << 24U) | (static_cast<std::uint32_t>(Data[J+1]) << 16U) |
                   (static_cast<std::uint32_t>(Data[J+2]) << 8U) | static_cast<std::uint32_t>(Data[J+3]);
        }
        for (std::size_t I = 16U; I < 64U; ++I) {
            const std::uint32_t S0 = RotateRight(W[I-15U],7U) ^ RotateRight(W[I-15U],18U) ^ (W[I-15U] >> 3U);
            const std::uint32_t S1 = RotateRight(W[I-2U],17U) ^ RotateRight(W[I-2U],19U) ^ (W[I-2U] >> 10U);
            W[I] = W[I-16U] + S0 + W[I-7U] + S1;
        }
        std::uint32_t A=H[0],B=H[1],C=H[2],D=H[3],E=H[4],F=H[5],G=H[6],HH=H[7];
        for (std::size_t I=0; I<64U; ++I) {
            const std::uint32_t S1=RotateRight(E,6U)^RotateRight(E,11U)^RotateRight(E,25U);
            const std::uint32_t Ch=(E&F)^((~E)&G);
            const std::uint32_t Temp1=HH+S1+Ch+K[I]+W[I];
            const std::uint32_t S0=RotateRight(A,2U)^RotateRight(A,13U)^RotateRight(A,22U);
            const std::uint32_t Maj=(A&B)^(A&C)^(B&C);
            const std::uint32_t Temp2=S0+Maj;
            HH=G;G=F;F=E;E=D+Temp1;D=C;C=B;B=A;A=Temp1+Temp2;
        }
        H[0]+=A;H[1]+=B;H[2]+=C;H[3]+=D;H[4]+=E;H[5]+=F;H[6]+=G;H[7]+=HH;
    }
    std::array<std::uint8_t,32> Out{};
    for (std::size_t I=0; I<8U; ++I) {
        Out[I*4U]=static_cast<std::uint8_t>((H[I]>>24U)&0xffU);
        Out[I*4U+1U]=static_cast<std::uint8_t>((H[I]>>16U)&0xffU);
        Out[I*4U+2U]=static_cast<std::uint8_t>((H[I]>>8U)&0xffU);
        Out[I*4U+3U]=static_cast<std::uint8_t>(H[I]&0xffU);
    }
    return Out;
}

inline std::string HexLower(const std::array<std::uint8_t,32>& Bytes) {
    static constexpr char Hex[] = "0123456789abcdef";
    std::string Out; Out.resize(64U);
    for (std::size_t I=0; I<Bytes.size(); ++I) { Out[I*2U]=Hex[Bytes[I]>>4U]; Out[I*2U+1U]=Hex[Bytes[I]&0x0fU]; }
    return Out;
}

inline std::string CandidateSetHashHex(const std::array<FTargetHandleWire, TotalTargetSlots>& Handles, const std::array<bool, TotalTargetSlots>& TargetMask, const std::array<bool, CandidateCount>& CandidateMask) { return HexLower(Sha256(CandidateSetCanonicalBytes(Handles, TargetMask, CandidateMask))); }
inline std::string DecisionContractHashHex(const FDecisionContractDigests& Digests) { return HexLower(Sha256(DecisionContractCanonicalBytes(Digests))); }

static_assert(CandidateIndex(SkillCount - 1, TotalTargetSlots - 1) == CandidateCount - 1);
static_assert(static_cast<std::size_t>(EGlobalFeature::current_skill_ContinueCurrentAction_reserved_zero) == 17);

} // namespace AINativeNPC::SchemaV2
