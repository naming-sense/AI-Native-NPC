// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include "AINativeNPCContracts.generated.h"

namespace AINativeNPC::SkillExecutionV1 {
inline constexpr const char* SkillRegistrySha256 = "ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d";
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
    default:
        return false;
    }
}
inline constexpr double EffectiveSpeed(double Speed, double Intensity) {
    return Speed * (IntensitySpeedBase + IntensitySpeedScale * std::clamp(Intensity, 0.0, 1.0));
}
static_assert(SearchNormalizedOffsets.size() == SearchPointCount);
} // namespace AINativeNPC::SkillExecutionV1
