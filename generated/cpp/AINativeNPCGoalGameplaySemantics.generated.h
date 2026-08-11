// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include "AINativeNPCContracts.generated.h"

namespace AINativeNPC::GoalGameplayV1 {
inline constexpr const char* GoalRegistrySha256 = "d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e";
inline constexpr const char* GoalRegistryVersion = "1.1.0";
inline constexpr const char* GameplaySemanticsVersion = "1.0.0";
inline constexpr const char* ProfileId = "GuardPhase0";
inline constexpr const char* UtilityProfileId = "GuardPhase0UtilityV1";

enum class EGuardId : std::uint8_t {
    valid_disturbance_target = 0,
    social_subject = 1,
    orientation_complete = 2,
    no_valid_snapshot = 3,
    phase_timeout = 4,
    arrived_at_snapshot = 5,
    PathUnavailable = 6,
    subject_identified = 7,
    search_budget_exhausted = 8,
    resolution_complete = 9,
    no_valid_belief = 10,
    at_return_target = 11,
};

enum class EFactSource : std::uint8_t {
    None = 0,
    Knowledge = 1,
    SkillExecutor = 2,
    GoalTimer = 3,
    GoalAuthority = 4,
    Unavailable = 5,
};

enum class ERequirementId : std::uint8_t {
    ExactCurrentGoalToken = 0,
    NonzeroTargetIdentity = 1,
    ExactCurrentKnowledgeRevision = 2,
    ExactCurrentAvailableSoundCapture = 3,
    FiniteStimulusLocation = 4,
    DisturbancePositionPrepareSucceeds = 5,
    ExactCurrentVisibleEntityBinding = 6,
    ExactPrimarySocialSubject = 7,
    ExactCurrentDecisionId = 8,
    ExactTargetIdentityAndRevision = 9,
    ExecutionStatusSucceeded = 10,
    ExactCurrentPrimaryTarget = 11,
    GoalOwnedResolverCannotResolve = 12,
    SourceSoundExpiryAloneForbidden = 13,
    ExactTransitionTimerId = 14,
    NonzeroTimerRuntimeEpoch = 15,
    CurrentOneShotTimerEpoch = 16,
    WallClockForbidden = 17,
    ExecutionStatusFailed = 18,
    ExactFailureReason = 19,
    ProviderUnavailableFailClosed = 20,
    AtLeastOneSearchPointVisitedWhenDeadlineSucceeded = 21,
};

enum class EFailureReason : std::uint8_t {
    None = 0,
    TargetInvalid = 1,
    TargetGenerationChanged = 2,
    PreconditionChanged = 3,
    GoalChanged = 4,
    PathUnavailable = 5,
    ReservationConflict = 6,
    Interrupted = 7,
    TimedOut = 8,
    AuthorityRejected = 9,
    ExecutionError = 10,
    CancelledByNewDecision = 11,
    ContractMismatch = 12,
};

enum class ETargetAuthorityId : std::uint8_t {
    None = 0,
    HomeWaypoint = 1,
    SourceSoundHandle = 2,
    DisturbancePosition = 3,
};

enum class ETargetPolicy : std::uint8_t {
    AnyAllowedTargetOrNoTarget = 0,
    ActiveGoalPrimaryTargetOnly = 1,
    UnavailableInGuardPhase0 = 2,
};

enum class EGuardAvailability : std::uint8_t {
    executable = 0,
    provider_unavailable = 1,
};

enum class ETriggerKind : std::uint8_t { Event, Timer };

struct FInitialProfile {
    const char* Profile;
    SchemaV2::EGoalType Goal;
    SchemaV2::EGoalPhase Phase;
    std::uint64_t InitialGoalRevision;
    std::uint64_t InitialPhaseGeneration;
    const char* GoalInstanceIdPolicy;
    const char* Lifecycle;
    const char* ActivationPreconditionTarget;
    const char* FailurePolicy;
};
struct FTransitionBinding {
    SchemaV2::EGoalType Goal;
    SchemaV2::EGoalPhase Phase;
    std::uint8_t Order;
    EGuardId Guard;
    EGuardAvailability Availability;
    ETriggerKind TriggerKind;
    SchemaV2::EEventType EventType;
    const char* TimerId;
    EFactSource FactSource;
    std::uint64_t AcceptedSkillMask;
    std::uint64_t AcceptedTargetKindMask;
    std::uint64_t TargetAuthorityMask;
    std::uint64_t AcceptedFailureMask;
    std::uint64_t RequirementMask;
};
struct FPhaseTargetPolicy {
    SchemaV2::EGoalType Goal;
    SchemaV2::EGoalPhase Phase;
    ETargetPolicy Policy;
    ETargetAuthorityId TargetAuthority;
    SchemaV2::ETargetKind RequiredTargetKind;
    bool ExactIdentityAndRevision;
    const char* ContinuePolicy;
    const char* EntryTargetChange;
};
struct FTargetAuthority {
    ETargetAuthorityId Id;
    SchemaV2::ETargetKind TargetKind;
    const char* Owner;
    const char* Lifetime;
    const char* StableIdPolicy;
    bool OwnedByGameplayGoalAuthority;
    bool OwnedByKnowledge;
    bool AuthoritySessionLifetime;
    bool SourceKnowledgeFactLifetime;
    bool InvestigateGoalInstanceLifetime;
    bool SessionMonotonicGoalTargetAllocator;
    bool ExactSourceHandleStableId;
    std::uint64_t Generation;
    std::uint64_t InitialRevision;
    bool Mutable;
    bool StoredInKnowledge;
    bool ProvenanceOnly;
    bool CandidateUsable;
    const char* CaptureSource;
    bool FirstExactAssemblyPawnCapture;
    bool ExactCurrentSoundEventHandleCapture;
    bool ExactSoundEventStimulusLocationCapture;
    bool ActorTransformLookup;
    const char* SourceTtlExpiryPolicy;
};
struct FEffectAuthority {
    const char* Name;
    const char* ApplyEffectPolicy;
    const char* PumpResult;
    bool StageIntentOnly;
    bool RequestsGoal;
    bool OwnerBoundedPrepareInterruptCommit;
    const char* TransactionPolicy;
    const char* FailureBeforeInterrupt;
    const char* InterruptFailure;
    const char* FailureAfterInterrupt;
    const char* PostCommitSkillStartFailure;
    const char* CallbackFreeAtomicSteps;
    const char* Preserve;
    const char* RevisionWithoutTargetChange;
    const char* RevisionWithTargetChange;
};

inline constexpr std::array<FInitialProfile, 1> InitialProfiles{{
    FInitialProfile{"GuardPhase0", SchemaV2::EGoalType::IdleObserve, SchemaV2::EGoalPhase::Observe, 1ULL, 1ULL, "session_monotonic_nonzero", "Active", "HomeWaypoint", "remain_dormant_fail_closed"},
}};
inline constexpr std::array<FTransitionBinding, 16> TransitionBindings{{
    FTransitionBinding{SchemaV2::EGoalType::IdleObserve, SchemaV2::EGoalPhase::Observe, 0U, EGuardId::valid_disturbance_target, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SoundHeard, "", EFactSource::Knowledge, 0ULL, 4ULL, 4ULL, 0ULL, 63ULL},
    FTransitionBinding{SchemaV2::EGoalType::IdleObserve, SchemaV2::EGoalPhase::Observe, 1U, EGuardId::social_subject, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SightAcquired, "", EFactSource::Knowledge, 0ULL, 2ULL, 0ULL, 0ULL, 197ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Orient, 0U, EGuardId::orientation_complete, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillSucceeded, "", EFactSource::SkillExecutor, 8ULL, 128ULL, 8ULL, 0ULL, 1793ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Orient, 1U, EGuardId::no_valid_snapshot, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::TargetInvalidated, "", EFactSource::GoalAuthority, 0ULL, 128ULL, 8ULL, 0ULL, 14337ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Orient, 2U, EGuardId::phase_timeout, EGuardAvailability::executable, ETriggerKind::Timer, SchemaV2::EEventType::NoneOrPadding, "phase_timeout", EFactSource::GoalTimer, 0ULL, 0ULL, 0ULL, 0ULL, 245761ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Navigate, 3U, EGuardId::phase_timeout, EGuardAvailability::executable, ETriggerKind::Timer, SchemaV2::EEventType::NoneOrPadding, "phase_timeout", EFactSource::GoalTimer, 0ULL, 0ULL, 0ULL, 0ULL, 245761ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Search, 2U, EGuardId::phase_timeout, EGuardAvailability::executable, ETriggerKind::Timer, SchemaV2::EEventType::NoneOrPadding, "phase_timeout", EFactSource::GoalTimer, 0ULL, 0ULL, 0ULL, 0ULL, 245761ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Navigate, 0U, EGuardId::arrived_at_snapshot, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillSucceeded, "", EFactSource::SkillExecutor, 272ULL, 128ULL, 8ULL, 0ULL, 1793ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Navigate, 1U, EGuardId::PathUnavailable, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillFailed, "", EFactSource::SkillExecutor, 272ULL, 128ULL, 8ULL, 32ULL, 787201ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Return, 1U, EGuardId::PathUnavailable, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillFailed, "", EFactSource::SkillExecutor, 16ULL, 64ULL, 2ULL, 32ULL, 787201ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Navigate, 2U, EGuardId::subject_identified, EGuardAvailability::provider_unavailable, ETriggerKind::Event, SchemaV2::EEventType::SightAcquired, "", EFactSource::Unavailable, 0ULL, 0ULL, 0ULL, 0ULL, 1048576ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Search, 0U, EGuardId::subject_identified, EGuardAvailability::provider_unavailable, ETriggerKind::Event, SchemaV2::EEventType::SightAcquired, "", EFactSource::Unavailable, 0ULL, 0ULL, 0ULL, 0ULL, 1048576ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Search, 1U, EGuardId::search_budget_exhausted, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillSucceeded, "", EFactSource::SkillExecutor, 512ULL, 128ULL, 8ULL, 0ULL, 2098945ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Resolve, 0U, EGuardId::resolution_complete, EGuardAvailability::provider_unavailable, ETriggerKind::Event, SchemaV2::EEventType::SkillSucceeded, "", EFactSource::Unavailable, 0ULL, 0ULL, 0ULL, 0ULL, 1048576ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Resolve, 1U, EGuardId::no_valid_belief, EGuardAvailability::provider_unavailable, ETriggerKind::Event, SchemaV2::EEventType::TargetInvalidated, "", EFactSource::Unavailable, 0ULL, 0ULL, 0ULL, 0ULL, 1048576ULL},
    FTransitionBinding{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Return, 0U, EGuardId::at_return_target, EGuardAvailability::executable, ETriggerKind::Event, SchemaV2::EEventType::SkillSucceeded, "", EFactSource::SkillExecutor, 16ULL, 64ULL, 2ULL, 0ULL, 1793ULL},
}};
inline constexpr std::array<FPhaseTargetPolicy, 6> PhaseTargetPolicies{{
    FPhaseTargetPolicy{SchemaV2::EGoalType::IdleObserve, SchemaV2::EGoalPhase::Observe, ETargetPolicy::AnyAllowedTargetOrNoTarget, ETargetAuthorityId::None, SchemaV2::ETargetKind::NoTarget, false, "running_skill_target_must_match_when_targeted", "none"},
    FPhaseTargetPolicy{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Orient, ETargetPolicy::ActiveGoalPrimaryTargetOnly, ETargetAuthorityId::DisturbancePosition, SchemaV2::ETargetKind::WorldPosition, true, "running_skill_target_must_equal_current_primary", "none"},
    FPhaseTargetPolicy{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Navigate, ETargetPolicy::ActiveGoalPrimaryTargetOnly, ETargetAuthorityId::DisturbancePosition, SchemaV2::ETargetKind::WorldPosition, true, "running_skill_target_must_equal_current_primary", "none"},
    FPhaseTargetPolicy{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Search, ETargetPolicy::ActiveGoalPrimaryTargetOnly, ETargetAuthorityId::DisturbancePosition, SchemaV2::ETargetKind::WorldPosition, true, "running_skill_target_must_equal_current_primary", "none"},
    FPhaseTargetPolicy{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Resolve, ETargetPolicy::UnavailableInGuardPhase0, ETargetAuthorityId::None, SchemaV2::ETargetKind::NoTarget, false, "unavailable", "none"},
    FPhaseTargetPolicy{SchemaV2::EGoalType::InvestigateDisturbance, SchemaV2::EGoalPhase::Return, ETargetPolicy::ActiveGoalPrimaryTargetOnly, ETargetAuthorityId::HomeWaypoint, SchemaV2::ETargetKind::Waypoint, true, "running_skill_target_must_equal_current_primary", "install_home_waypoint_and_increment_goal_revision_once"},
}};
inline constexpr std::array<FTargetAuthority, 3> TargetAuthorities{{
    FTargetAuthority{ETargetAuthorityId::HomeWaypoint, SchemaV2::ETargetKind::Waypoint, "GameplayGoalAuthority", "AuthoritySession", "session_monotonic_nonzero_goal_target_allocator", true, false, true, false, false, true, false, 1ULL, 1ULL, false, false, false, true, "FirstExactAssemblyPawnFiniteWorldPosition", true, false, false, false, "not_applicable"},
    FTargetAuthority{ETargetAuthorityId::SourceSoundHandle, SchemaV2::ETargetKind::SoundEvent, "Knowledge", "SourceKnowledgeFact", "exact_source_handle", false, true, false, true, false, false, true, 0ULL, 0ULL, false, true, true, false, "ExactCurrentSoundEventHandleAtRequest", false, true, false, false, "may_expire_after_goal_activation"},
    FTargetAuthority{ETargetAuthorityId::DisturbancePosition, SchemaV2::ETargetKind::WorldPosition, "GameplayGoalAuthority", "InvestigateGoalInstance", "session_monotonic_nonzero_goal_target_allocator", true, false, false, false, true, true, false, 1ULL, 1ULL, false, false, false, true, "ExactSoundEventStimulusLocation", false, false, true, false, "preserve_immutable_position"},
}};
inline constexpr std::array<FEffectAuthority, 2> EffectAuthorities{{
    FEffectAuthority{"request_new_goal", "stage_intent_only_no_external_mutation", "GoalRequested", true, true, true, "owner_bounded_prepare_interrupt_commit", "preserve_old_goal_timer_and_running_skill", "keep_old_goal_active_and_replan", "keep_old_goal_active_without_running_skill_and_replan", "keep_new_goal_and_replan_or_wait_timeout", "suspend_old_goal_and_pause_timer|activate_new_goal_and_install_primary_target|arm_new_phase_timer|supersede_pending_old_decision", "", "not_applicable", "active_goal_transaction_single_publication"},
    FEffectAuthority{"remain_and_replan", "stage_intent_only_no_external_mutation", "ReplanRequested", true, false, false, "supersede_pending_decision_then_request_new_snapshot", "not_applicable", "not_applicable", "preserve_current_goal_and_pending_state", "remain_in_current_phase_and_replan", "", "GoalInstance|Lifecycle|Phase|PhaseGeneration|PhaseDeadline|TimerRuntimeEpoch", "unchanged", "increment_once_authoritative_primary_target_changed"},
}};
inline constexpr std::size_t ExecutableUniqueGuardCount = 9U;
inline constexpr std::size_t UnavailableUniqueGuardCount = 3U;
inline constexpr std::size_t ExecutableTransitionBindingCount = 12U;
inline constexpr std::uint64_t ProductionSkillMask = 793ULL;
inline constexpr SchemaV2::ESkillId ControlSkill = SchemaV2::ESkillId::ContinueCurrentAction;
inline constexpr std::uint8_t SkillCountSentinel = static_cast<std::uint8_t>(SchemaV2::SkillCount);
inline constexpr std::array<double, 16> CandidatePairFeatureWeights{{0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0}};

inline constexpr const FInitialProfile* FindInitialProfile(const char* Profile) {
    for (const auto& Row : InitialProfiles) {
        const char* A = Row.Profile;
        const char* B = Profile;
        while (*A != '\0' && *A == *B) { ++A; ++B; }
        if (*A == *B) return &Row;
    }
    return nullptr;
}
inline constexpr const FTransitionBinding* FindTransitionBinding(
    const SchemaV2::EGoalType Goal,
    const SchemaV2::EGoalPhase Phase,
    const std::uint8_t Order) {
    for (const auto& Row : TransitionBindings) {
        if (Row.Goal == Goal && Row.Phase == Phase && Row.Order == Order) return &Row;
    }
    return nullptr;
}
inline constexpr const FPhaseTargetPolicy* FindPhaseTargetPolicy(
    const SchemaV2::EGoalType Goal,
    const SchemaV2::EGoalPhase Phase) {
    for (const auto& Row : PhaseTargetPolicies) {
        if (Row.Goal == Goal && Row.Phase == Phase) return &Row;
    }
    return nullptr;
}
inline constexpr bool StringsEqual(const char* A, const char* B) {
    while (*A != '\0' && *A == *B) { ++A; ++B; }
    return *A == *B;
}
inline constexpr const FTargetAuthority* FindTargetAuthority(const ETargetAuthorityId Id) {
    for (const auto& Row : TargetAuthorities) {
        if (Row.Id == Id) return &Row;
    }
    return nullptr;
}
inline constexpr const FEffectAuthority* FindEffectAuthority(const char* Name) {
    for (const auto& Row : EffectAuthorities) {
        if (StringsEqual(Row.Name, Name)) return &Row;
    }
    return nullptr;
}
inline constexpr bool IsProductionExecutableSkill(const SchemaV2::ESkillId Skill) {
    const auto Index = static_cast<unsigned>(Skill);
    return Index < SchemaV2::SkillCount && (ProductionSkillMask & (1ULL << Index)) != 0ULL;
}
inline constexpr bool HasRequirement(const FTransitionBinding& Binding, const ERequirementId Requirement) {
    const auto Index = static_cast<unsigned>(Requirement);
    return Index < 64U && (Binding.RequirementMask & (1ULL << Index)) != 0ULL;
}
inline constexpr double GetUtilityBias(const SchemaV2::ESkillId Skill) {
    switch (Skill) {
    case SchemaV2::ESkillId::SearchArea: return 1.5;
    case SchemaV2::ESkillId::Investigate: return 1.25;
    case SchemaV2::ESkillId::TurnTo: return 1.0;
    case SchemaV2::ESkillId::Approach: return 0.75;
    case SchemaV2::ESkillId::ContinueCurrentAction: return 0.5;
    case SchemaV2::ESkillId::Idle: return 0.0;
    default: return -2.5;
    }
}
static_assert(InitialProfiles.size() == 1U);
static_assert(TransitionBindings.size() == 16U);
static_assert(PhaseTargetPolicies.size() == 6U);
static_assert(TargetAuthorities.size() == 3U);
static_assert(EffectAuthorities.size() == 2U);
} // namespace AINativeNPC::GoalGameplayV1
