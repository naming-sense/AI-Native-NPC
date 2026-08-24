// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include "AINativeNPCContracts.generated.h"

namespace AINativeNPC::SkillExecutionV1 {
inline constexpr const char* SkillRegistrySha256 = "15b47b23066c2b64f4228dadd21dd36d0cf2681a9e387c624a1111965b952467";
inline constexpr double EvaluationIntervalSeconds = 0.050000000000000003;
inline constexpr double IntensitySpeedBase = 0.5;
inline constexpr double IntensitySpeedScale = 0.5;
inline constexpr double NavProjectionHorizontalCm = 100;
inline constexpr double NavProjectionVerticalCm = 200;
inline constexpr double TurnPlanarCoincidentDistanceCm = 1;
inline constexpr double TurnFacingToleranceDegrees = 5;
inline constexpr double TurnSuccessStableSeconds = 0.10000000000000001;
inline constexpr double InvestigateFacingToleranceDegrees = 15;
inline constexpr double InvestigateSuccessStableSeconds = 0.5;
inline constexpr double InvestigateBaseTurnSpeedDegreesPerSecond = 360;
inline constexpr double SearchPointAcceptanceRadiusCm = 100;
inline constexpr double GreetDurationMinSeconds = 1;
inline constexpr double GreetDurationMaxSeconds = 5;
inline constexpr double GreetDurationDefaultSeconds = 2;
inline constexpr double GreetIntensityMin = 0;
inline constexpr double GreetIntensityMax = 1;
inline constexpr double GreetIntensityDefault = 0.5;
inline constexpr bool GreetRequiresLos = true;
inline constexpr std::size_t GreetDurationParameterSlot = 0;
inline constexpr std::size_t GreetIntensityParameterSlot = 3;
inline constexpr const char* GreetSocialSignal = "server_authoritative_greet_one_shot";
inline constexpr const char* GreetCue = "source_guard_world_space_visible";
inline constexpr bool GreetCueBaseVisibleAtZeroIntensity = true;
inline constexpr bool GreetTargetReceiverComponentRequired = false;
inline constexpr const char* GreetLifecycleStartPublication = "effect_start_succeeds";
inline constexpr const char* GreetLifecycleSuccess = "signal_started_once_and_authoritative_cue_duration_completed";
inline constexpr std::array<const char*, 6> GreetLifecycleCancelOn{{"GoalChanged", "AuthorityLost", "TargetInvalidated", "LosLost", "ExecutorQuarantined", "StateTreeExit"}};
inline constexpr const char* GreetStaleCallbackPolicy = "reject_exact_identity_mismatch";
inline constexpr const char* GreetDuplicateScope = "pawn_session";
inline constexpr const char* GreetDuplicateDecisionRule = "strictly_greater_than_highest_applied";
inline constexpr std::array<const char*, 5> GreetDuplicateIdentityFields{{"SessionId", "DecisionId", "GoalToken", "SkillId", "TargetHandle"}};
inline constexpr const char* GreetDuplicateSessionChangePolicy = "close_old_authority_before_reset_high_water";
inline constexpr const char* GreetDuplicateGuarantee = "in_process_session_lifetime_at_most_once";
inline constexpr std::size_t SearchPointCount = 9;
struct FSearchOffset { double X; double Y; };
inline constexpr std::array<FSearchOffset, SearchPointCount> SearchNormalizedOffsets{{
    FSearchOffset{0, 0},
    FSearchOffset{0.5, 0},
    FSearchOffset{0, 0.5},
    FSearchOffset{-0.5, 0},
    FSearchOffset{0, -0.5},
    FSearchOffset{0.70710678118654757, 0.70710678118654757},
    FSearchOffset{-0.70710678118654757, 0.70710678118654757},
    FSearchOffset{-0.70710678118654757, -0.70710678118654757},
    FSearchOffset{0.70710678118654757, -0.70710678118654757}
}};
inline constexpr bool IsTargetKindAllowed(
    const SchemaV2::ESkillId Skill,
    const SchemaV2::ETargetKind Kind)
{
    switch (Skill)
    {
    case SchemaV2::ESkillId::TurnTo:
        return Kind == SchemaV2::ETargetKind::Entity
            || Kind == SchemaV2::ETargetKind::SoundEvent
            || Kind == SchemaV2::ETargetKind::LastKnownPosition
            || Kind == SchemaV2::ETargetKind::Waypoint
            || Kind == SchemaV2::ETargetKind::WorldPosition;
    case SchemaV2::ESkillId::Approach:
        return Kind == SchemaV2::ETargetKind::Entity
            || Kind == SchemaV2::ETargetKind::LastKnownPosition
            || Kind == SchemaV2::ETargetKind::CoverSlot
            || Kind == SchemaV2::ETargetKind::SmartObject
            || Kind == SchemaV2::ETargetKind::Waypoint
            || Kind == SchemaV2::ETargetKind::WorldPosition;
    case SchemaV2::ESkillId::Investigate:
        return Kind == SchemaV2::ETargetKind::SoundEvent
            || Kind == SchemaV2::ETargetKind::LastKnownPosition
            || Kind == SchemaV2::ETargetKind::SmartObject
            || Kind == SchemaV2::ETargetKind::Waypoint
            || Kind == SchemaV2::ETargetKind::WorldPosition;
    case SchemaV2::ESkillId::SearchArea:
        return Kind == SchemaV2::ETargetKind::LastKnownPosition
            || Kind == SchemaV2::ETargetKind::Waypoint
            || Kind == SchemaV2::ETargetKind::WorldPosition;
    case SchemaV2::ESkillId::Greet:
        return Kind == SchemaV2::ETargetKind::Entity;
    default:
        return false;
    }
}
inline constexpr double EffectiveSpeed(double Speed, double Intensity) {
    return Speed * (IntensitySpeedBase + IntensitySpeedScale * std::clamp(Intensity, 0.0, 1.0));
}
static_assert(SearchNormalizedOffsets.size() == SearchPointCount);
} // namespace AINativeNPC::SkillExecutionV1
