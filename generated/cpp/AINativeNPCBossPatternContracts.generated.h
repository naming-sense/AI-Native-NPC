// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include "AINativeNPCContracts.generated.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace AINativeNPC::BossPatternV1 {
inline constexpr const char* GeneratorVersion = "0.4.6";
inline constexpr const char* ContractVersion = "1.0.0";
inline constexpr const char* ContractRevision = "2.0.0-rc5";
inline constexpr const char* BossPatternContractSha256 = "e4f828c114fcc5db1cb04b5d0a6e2b3d29dada7e45c60a3dd18c674baa78c789";
inline constexpr std::array<std::uint8_t, 32> BossPatternContractSha256Bytes{{0xe4, 0xf8, 0x28, 0xc1, 0x14, 0xfc, 0xc5, 0xdb, 0x1c, 0xb0, 0x4b, 0x5d, 0x0a, 0x6e, 0x2b, 0x3d, 0x29, 0xda, 0xda, 0x7e, 0x45, 0xc6, 0x0a, 0x3d, 0xd1, 0x8c, 0x67, 0x4b, 0xaa, 0x78, 0xc7, 0x89}};
inline constexpr std::size_t MaxPatternSlots = 32;
inline constexpr std::size_t PatternContextFeatureCount = 32;
inline constexpr std::size_t PatternFeatureCount = 24;
inline constexpr std::size_t PatternPairFeatureCount = 16;
inline constexpr std::size_t PatternParameterCount = 4;
inline constexpr std::uint16_t InvalidPatternId = 65535U;
inline constexpr std::array<std::uint8_t, 8> PatternCandidateHashMagic{{66, 80, 67, 83, 69, 84, 48, 49}};
inline constexpr std::uint16_t PatternCandidateHashSerializationVersion = 1U;
inline constexpr std::array<std::uint8_t, 8> BossPatternDecisionHashMagic{{66, 80, 68, 67, 84, 82, 48, 49}};
inline constexpr std::uint16_t BossPatternDecisionHashSerializationVersion = 1U;

enum class ESelectionBoundary : std::uint8_t {
    PreAttack = 0,
    BranchWindow = 1,
    RecoveryEnd = 2,
};

enum class EExecutionPhase : std::uint8_t {
    ReadyToSelect = 0,
    PreAttackTurn = 1,
    StartupTelegraph = 2,
    Active = 3,
    Recovery = 4,
    BranchWindow = 5,
    Completed = 6,
    Interrupted = 7,
};

enum class EInterruptKind : std::uint8_t {
    Death = 0,
    ActorDestroyed = 1,
    AuthorityLost = 2,
    Stun = 3,
    PostureBreak = 4,
    ScriptedPhaseTransition = 5,
    ArenaReset = 6,
};

enum class EPatternMaskReason : std::uint8_t {
    None = 0,
    Unoccupied = 1,
    WrongBossPhase = 2,
    TargetInvalid = 3,
    RangeMismatch = 4,
    AngleMismatch = 5,
    ElevationMismatch = 6,
    LineOfSightMissing = 7,
    CooldownActive = 8,
    ResourceUnavailable = 9,
    PredecessorMismatch = 10,
    BranchNotAllowed = 11,
    ArenaUnsafe = 12,
    NavigationUnavailable = 13,
    AssetUnavailable = 14,
    NotSelectionBoundary = 15,
    ReservationConflict = 16,
    ExecutorLocked = 17,
};

enum class EPatternContextFeature : std::uint16_t {
    boss_health_ratio = 0,
    boss_stamina_ratio = 1,
    boss_posture_ratio = 2,
    target_health_ratio_estimate = 3,
    target_distance_planar = 4,
    target_distance_3d = 5,
    target_bearing_sin = 6,
    target_bearing_cos = 7,
    target_elevation_sin = 8,
    target_elevation_cos = 9,
    target_relative_speed = 10,
    target_approach_velocity = 11,
    target_lateral_velocity = 12,
    has_line_of_sight = 13,
    path_available = 14,
    arena_edge_risk = 15,
    boss_phase_normalized = 16,
    elapsed_encounter_time = 17,
    elapsed_since_last_pattern = 18,
    same_pattern_streak_ratio = 19,
    recent_fast_pattern_ratio = 20,
    recent_heavy_pattern_ratio = 21,
    recent_gap_closer_ratio = 22,
    player_recent_damage_ratio = 23,
    boss_recent_damage_ratio = 24,
    selection_boundary_pre_attack = 25,
    selection_boundary_branch_window = 26,
    selection_boundary_recovery_end = 27,
    previous_pattern_family_fast = 28,
    previous_pattern_family_heavy = 29,
    previous_pattern_family_gap_closer = 30,
    target_health_estimate_confidence = 31,
};

enum class EPatternFeature : std::uint16_t {
    preferred_distance_min = 0,
    preferred_distance_max = 1,
    allowed_bearing_abs_max = 2,
    allowed_elevation_abs_max = 3,
    telegraph_duration = 4,
    active_duration = 5,
    recovery_duration = 6,
    cooldown_duration = 7,
    stamina_cost_ratio = 8,
    startup_tracking_yaw_ratio = 9,
    active_tracking_yaw_ratio = 10,
    recovery_tracking_yaw_ratio = 11,
    startup_tracking_speed_ratio = 12,
    active_tracking_speed_ratio = 13,
    area_pressure_ratio = 14,
    gap_close_ratio = 15,
    damage_pressure_ratio = 16,
    posture_pressure_ratio = 17,
    family_fast = 18,
    family_heavy = 19,
    family_gap_closer = 20,
    family_area_control = 21,
    branch_capable = 22,
    reserved_zero = 23,
};

enum class EPatternPairFeature : std::uint16_t {
    distance_fit = 0,
    bearing_fit = 1,
    elevation_fit = 2,
    line_of_sight_fit = 3,
    phase_allowed = 4,
    cooldown_ready = 5,
    resource_ready = 6,
    predecessor_allowed = 7,
    branch_allowed = 8,
    arena_safe = 9,
    navigation_available = 10,
    repetition_penalty_feature = 11,
    timing_variety_feature = 12,
    target_motion_fit = 13,
    selection_boundary_fit = 14,
    reserved_zero = 15,
};

enum class EPatternParameter : std::uint16_t {
    tracking_fraction = 0,
    telegraph_extension_fraction = 1,
    recovery_extension_fraction = 2,
    reserved_zero = 3,
};

enum class ENormalizerKind : std::uint8_t { Clamp = 0, DivideClamp = 1, Constant = 2 };
struct FNormalizerSpec {
    ENormalizerKind Kind;
    float Min;
    float Max;
    float Divisor;
    float ConstantValue;
};

inline constexpr std::array<FNormalizerSpec, 32> PatternContextNormalizers{{
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 10000.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 10000.0f, 0.0f},
    {ENormalizerKind::Clamp, -1.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, -1.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, -1.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, -1.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::DivideClamp, -1.0f, 1.0f, 2000.0f, 0.0f},
    {ENormalizerKind::DivideClamp, -1.0f, 1.0f, 2000.0f, 0.0f},
    {ENormalizerKind::DivideClamp, -1.0f, 1.0f, 2000.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 1800.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 120.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
}};

inline constexpr std::array<FNormalizerSpec, 24> PatternFeatureNormalizers{{
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 10000.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 10000.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 180.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 90.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 30.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 30.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 30.0f, 0.0f},
    {ENormalizerKind::DivideClamp, 0.0f, 1.0f, 120.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Constant, 0.0f, 0.0f, 1.0f, 0.0f},
}};

inline constexpr std::array<FNormalizerSpec, 16> PatternPairFeatureNormalizers{{
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Clamp, 0.0f, 1.0f, 1.0f, 0.0f},
    {ENormalizerKind::Constant, 0.0f, 0.0f, 1.0f, 0.0f},
}};

inline bool TryNormalizeFeature(float Input, const FNormalizerSpec& Spec, float& Out) {
    if (!std::isfinite(Input)) return false;
    if (Spec.Kind == ENormalizerKind::Constant) { Out = Spec.ConstantValue; return true; }
    const float Value = Spec.Kind == ENormalizerKind::DivideClamp ? Input / Spec.Divisor : Input;
    Out = std::clamp(Value, Spec.Min, Spec.Max);
    return true;
}

inline bool IsPatternSlotLayoutValid(const std::array<std::uint16_t, MaxPatternSlots>& PatternIds, const std::array<bool, MaxPatternSlots>& PatternMask) {
    bool SeenPadding = false;
    std::uint16_t Previous = 0;
    bool HasPrevious = false;
    for (std::size_t Index = 0; Index < MaxPatternSlots; ++Index) {
        const auto PatternId = PatternIds[Index];
        if (PatternId >= InvalidPatternId) { SeenPadding = true; if (PatternMask[Index]) return false; continue; }
        if (SeenPadding || (HasPrevious && PatternId <= Previous)) return false;
        Previous = PatternId; HasPrevious = true;
    }
    return HasPrevious;
}

struct FBossPatternDecisionDigests {
    std::array<std::uint8_t, 32> PatternModel{};
    std::array<std::uint8_t, 32> PatternNormalizationContract{};
    std::array<std::uint8_t, 32> PatternPostprocessContract{};
    std::array<std::uint8_t, 32> PatternCalibrationOodAsset{};
    std::array<std::uint8_t, 32> PatternExecutorContract{};
};

inline std::vector<std::uint8_t> PatternCandidateSetCanonicalBytes(
    const std::array<std::uint8_t, 32>& PatternAssetBundleSha256,
    const std::array<std::uint16_t, MaxPatternSlots>& PatternIds,
    const std::array<bool, MaxPatternSlots>& PatternMask,
    const SchemaV2::FTargetHandleWire& AttackTargetHandle,
    ESelectionBoundary SelectionBoundary,
    std::uint64_t BossPhaseRevision,
    std::uint64_t CombatStateRevision) {
    if (!IsPatternSlotLayoutValid(PatternIds, PatternMask)) return {};
    std::vector<std::uint8_t> Out;
    Out.insert(Out.end(), PatternCandidateHashMagic.begin(), PatternCandidateHashMagic.end());
    SchemaV2::AppendLittleEndian<std::uint16_t>(Out, PatternCandidateHashSerializationVersion);
    Out.insert(Out.end(), BossPatternContractSha256Bytes.begin(), BossPatternContractSha256Bytes.end());
    Out.insert(Out.end(), PatternAssetBundleSha256.begin(), PatternAssetBundleSha256.end());
    Out.push_back(static_cast<std::uint8_t>(MaxPatternSlots));
    for (const auto PatternId : PatternIds) SchemaV2::AppendLittleEndian<std::uint16_t>(Out, PatternId);
    const auto PackedPatternMask = SchemaV2::PackBitsLSBFirst(PatternMask);
    Out.insert(Out.end(), PackedPatternMask.begin(), PackedPatternMask.end());
    SchemaV2::AppendTargetHandle(Out, AttackTargetHandle);
    Out.push_back(static_cast<std::uint8_t>(SelectionBoundary));
    SchemaV2::AppendLittleEndian<std::uint64_t>(Out, BossPhaseRevision);
    SchemaV2::AppendLittleEndian<std::uint64_t>(Out, CombatStateRevision);
    return Out;
}

inline std::vector<std::uint8_t> BossPatternDecisionContractCanonicalBytes(const FBossPatternDecisionDigests& Digests) {
    std::vector<std::uint8_t> Out;
    Out.insert(Out.end(), BossPatternDecisionHashMagic.begin(), BossPatternDecisionHashMagic.end());
    SchemaV2::AppendLittleEndian<std::uint16_t>(Out, BossPatternDecisionHashSerializationVersion);
    Out.insert(Out.end(), BossPatternContractSha256Bytes.begin(), BossPatternContractSha256Bytes.end());
    Out.insert(Out.end(), Digests.PatternModel.begin(), Digests.PatternModel.end());
    Out.insert(Out.end(), Digests.PatternNormalizationContract.begin(), Digests.PatternNormalizationContract.end());
    Out.insert(Out.end(), Digests.PatternPostprocessContract.begin(), Digests.PatternPostprocessContract.end());
    Out.insert(Out.end(), Digests.PatternCalibrationOodAsset.begin(), Digests.PatternCalibrationOodAsset.end());
    Out.insert(Out.end(), Digests.PatternExecutorContract.begin(), Digests.PatternExecutorContract.end());
    return Out;
}

inline std::string PatternCandidateSetHashHex(const std::array<std::uint8_t, 32>& AssetHash, const std::array<std::uint16_t, MaxPatternSlots>& PatternIds, const std::array<bool, MaxPatternSlots>& PatternMask, const SchemaV2::FTargetHandleWire& Target, ESelectionBoundary Boundary, std::uint64_t PhaseRevision, std::uint64_t CombatRevision) { const auto Bytes = PatternCandidateSetCanonicalBytes(AssetHash, PatternIds, PatternMask, Target, Boundary, PhaseRevision, CombatRevision); return Bytes.empty() ? std::string{} : SchemaV2::HexLower(SchemaV2::Sha256(Bytes)); }
inline std::string BossPatternDecisionContractHashHex(const FBossPatternDecisionDigests& Digests) { return SchemaV2::HexLower(SchemaV2::Sha256(BossPatternDecisionContractCanonicalBytes(Digests))); }

static_assert(MaxPatternSlots == 32);
static_assert(SchemaV2::CandidateCount == 272);

} // namespace AINativeNPC::BossPatternV1
