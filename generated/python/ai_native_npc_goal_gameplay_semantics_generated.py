"""AUTO-GENERATED. DO NOT EDIT. Bounded Goal gameplay semantics V1."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

GOAL_REGISTRY_SHA256 = 'd9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e'
GOAL_REGISTRY_VERSION = '1.1.0'
GAMEPLAY_SEMANTICS_VERSION = '1.0.0'
PROFILE_ID = 'GuardPhase0'
UTILITY_PROFILE_ID = 'GuardPhase0UtilityV1'

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
    SkillCountSentinel = 16

class TargetKind(IntEnum):
    NoTarget = 0
    Entity = 1
    SoundEvent = 2
    LastKnownPosition = 3
    CoverSlot = 4
    SmartObject = 5
    Waypoint = 6
    WorldPosition = 7

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

class GuardId(IntEnum):
    valid_disturbance_target = 0
    social_subject = 1
    orientation_complete = 2
    no_valid_snapshot = 3
    phase_timeout = 4
    arrived_at_snapshot = 5
    PathUnavailable = 6
    subject_identified = 7
    search_budget_exhausted = 8
    resolution_complete = 9
    no_valid_belief = 10
    at_return_target = 11

class FactSource(IntEnum):
    None_ = 0
    Knowledge = 1
    SkillExecutor = 2
    GoalTimer = 3
    GoalAuthority = 4
    Unavailable = 5

class RequirementId(IntEnum):
    ExactCurrentGoalToken = 0
    NonzeroTargetIdentity = 1
    ExactCurrentKnowledgeRevision = 2
    ExactCurrentAvailableSoundCapture = 3
    FiniteStimulusLocation = 4
    DisturbancePositionPrepareSucceeds = 5
    ExactCurrentVisibleEntityBinding = 6
    ExactPrimarySocialSubject = 7
    ExactCurrentDecisionId = 8
    ExactTargetIdentityAndRevision = 9
    ExecutionStatusSucceeded = 10
    ExactCurrentPrimaryTarget = 11
    GoalOwnedResolverCannotResolve = 12
    SourceSoundExpiryAloneForbidden = 13
    ExactTransitionTimerId = 14
    NonzeroTimerRuntimeEpoch = 15
    CurrentOneShotTimerEpoch = 16
    WallClockForbidden = 17
    ExecutionStatusFailed = 18
    ExactFailureReason = 19
    ProviderUnavailableFailClosed = 20
    AtLeastOneSearchPointVisitedWhenDeadlineSucceeded = 21

class FailureReason(IntEnum):
    None_ = 0
    TargetInvalid = 1
    TargetGenerationChanged = 2
    PreconditionChanged = 3
    GoalChanged = 4
    PathUnavailable = 5
    ReservationConflict = 6
    Interrupted = 7
    TimedOut = 8
    AuthorityRejected = 9
    ExecutionError = 10
    CancelledByNewDecision = 11
    ContractMismatch = 12

class TargetAuthorityId(IntEnum):
    None_ = 0
    HomeWaypoint = 1
    SourceSoundHandle = 2
    DisturbancePosition = 3

class TargetPolicy(IntEnum):
    AnyAllowedTargetOrNoTarget = 0
    ActiveGoalPrimaryTargetOnly = 1
    UnavailableInGuardPhase0 = 2

class GuardAvailability(IntEnum):
    executable = 0
    provider_unavailable = 1

@dataclass(frozen=True)
class InitialProfile:
    profile_id: str
    goal: GoalType
    phase: GoalPhase
    initial_goal_revision: int
    initial_phase_generation: int
    goal_instance_id_policy: str
    lifecycle: str
    activation_precondition_target: str
    failure_policy: str

@dataclass(frozen=True)
class TransitionBinding:
    goal: GoalType
    phase: GoalPhase
    order: int
    guard: GuardId
    availability: GuardAvailability
    trigger_kind: str
    event_type: EventType
    timer_id: str
    fact_source: FactSource
    accepted_skill_mask: int
    accepted_target_kind_mask: int
    target_authority_mask: int
    accepted_failure_mask: int
    requirement_mask: int

@dataclass(frozen=True)
class PhaseTargetPolicySpec:
    goal: GoalType
    phase: GoalPhase
    policy: TargetPolicy
    target_authority: TargetAuthorityId
    required_target_kind: TargetKind
    exact_identity_and_revision: bool
    continue_policy: str
    entry_target_change: str

INITIAL_PROFILES = (
    InitialProfile('GuardPhase0', GoalType.IdleObserve, GoalPhase.Observe, 1, 1, 'session_monotonic_nonzero', 'Active', 'HomeWaypoint', 'remain_dormant_fail_closed'),
)
PHASE_TARGET_POLICIES = (
    PhaseTargetPolicySpec(GoalType.IdleObserve, GoalPhase.Observe, TargetPolicy.AnyAllowedTargetOrNoTarget, TargetAuthorityId.None_, TargetKind.NoTarget, False, 'running_skill_target_must_match_when_targeted', 'none'),
    PhaseTargetPolicySpec(GoalType.InvestigateDisturbance, GoalPhase.Orient, TargetPolicy.ActiveGoalPrimaryTargetOnly, TargetAuthorityId.DisturbancePosition, TargetKind.WorldPosition, True, 'running_skill_target_must_equal_current_primary', 'none'),
    PhaseTargetPolicySpec(GoalType.InvestigateDisturbance, GoalPhase.Navigate, TargetPolicy.ActiveGoalPrimaryTargetOnly, TargetAuthorityId.DisturbancePosition, TargetKind.WorldPosition, True, 'running_skill_target_must_equal_current_primary', 'none'),
    PhaseTargetPolicySpec(GoalType.InvestigateDisturbance, GoalPhase.Search, TargetPolicy.ActiveGoalPrimaryTargetOnly, TargetAuthorityId.DisturbancePosition, TargetKind.WorldPosition, True, 'running_skill_target_must_equal_current_primary', 'none'),
    PhaseTargetPolicySpec(GoalType.InvestigateDisturbance, GoalPhase.Resolve, TargetPolicy.UnavailableInGuardPhase0, TargetAuthorityId.None_, TargetKind.NoTarget, False, 'unavailable', 'none'),
    PhaseTargetPolicySpec(GoalType.InvestigateDisturbance, GoalPhase.Return, TargetPolicy.ActiveGoalPrimaryTargetOnly, TargetAuthorityId.HomeWaypoint, TargetKind.Waypoint, True, 'running_skill_target_must_equal_current_primary', 'install_home_waypoint_and_increment_goal_revision_once'),
)
TRANSITION_BINDINGS = (
    TransitionBinding(GoalType.IdleObserve, GoalPhase.Observe, 0, GuardId.valid_disturbance_target, GuardAvailability.executable, 'event', EventType.SoundHeard, '', FactSource.Knowledge, 0, 4, 4, 0, 63),
    TransitionBinding(GoalType.IdleObserve, GoalPhase.Observe, 1, GuardId.social_subject, GuardAvailability.executable, 'event', EventType.SightAcquired, '', FactSource.Knowledge, 0, 2, 0, 0, 197),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Orient, 0, GuardId.orientation_complete, GuardAvailability.executable, 'event', EventType.SkillSucceeded, '', FactSource.SkillExecutor, 8, 128, 8, 0, 1793),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Orient, 1, GuardId.no_valid_snapshot, GuardAvailability.executable, 'event', EventType.TargetInvalidated, '', FactSource.GoalAuthority, 0, 128, 8, 0, 14337),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Orient, 2, GuardId.phase_timeout, GuardAvailability.executable, 'timer', EventType.NoneOrPadding, 'phase_timeout', FactSource.GoalTimer, 0, 0, 0, 0, 245761),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Navigate, 3, GuardId.phase_timeout, GuardAvailability.executable, 'timer', EventType.NoneOrPadding, 'phase_timeout', FactSource.GoalTimer, 0, 0, 0, 0, 245761),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Search, 2, GuardId.phase_timeout, GuardAvailability.executable, 'timer', EventType.NoneOrPadding, 'phase_timeout', FactSource.GoalTimer, 0, 0, 0, 0, 245761),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Navigate, 0, GuardId.arrived_at_snapshot, GuardAvailability.executable, 'event', EventType.SkillSucceeded, '', FactSource.SkillExecutor, 272, 128, 8, 0, 1793),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Navigate, 1, GuardId.PathUnavailable, GuardAvailability.executable, 'event', EventType.SkillFailed, '', FactSource.SkillExecutor, 272, 128, 8, 32, 787201),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Return, 1, GuardId.PathUnavailable, GuardAvailability.executable, 'event', EventType.SkillFailed, '', FactSource.SkillExecutor, 16, 64, 2, 32, 787201),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Navigate, 2, GuardId.subject_identified, GuardAvailability.provider_unavailable, 'event', EventType.SightAcquired, '', FactSource.Unavailable, 0, 0, 0, 0, 1048576),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Search, 0, GuardId.subject_identified, GuardAvailability.provider_unavailable, 'event', EventType.SightAcquired, '', FactSource.Unavailable, 0, 0, 0, 0, 1048576),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Search, 1, GuardId.search_budget_exhausted, GuardAvailability.executable, 'event', EventType.SkillSucceeded, '', FactSource.SkillExecutor, 512, 128, 8, 0, 2098945),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Resolve, 0, GuardId.resolution_complete, GuardAvailability.provider_unavailable, 'event', EventType.SkillSucceeded, '', FactSource.Unavailable, 0, 0, 0, 0, 1048576),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Resolve, 1, GuardId.no_valid_belief, GuardAvailability.provider_unavailable, 'event', EventType.TargetInvalidated, '', FactSource.Unavailable, 0, 0, 0, 0, 1048576),
    TransitionBinding(GoalType.InvestigateDisturbance, GoalPhase.Return, 0, GuardId.at_return_target, GuardAvailability.executable, 'event', EventType.SkillSucceeded, '', FactSource.SkillExecutor, 16, 64, 2, 0, 1793),
)
EXECUTABLE_UNIQUE_GUARD_COUNT = 9
UNAVAILABLE_UNIQUE_GUARD_COUNT = 3
EXECUTABLE_TRANSITION_BINDING_COUNT = 12
PRODUCTION_SKILL_MASK = 793
CONTROL_SKILL = SkillId.ContinueCurrentAction
ALL_OTHER_SKILL_BIAS = -2.5
UTILITY_SKILL_BIASES = {9: 1.5, 8: 1.25, 3: 1.0, 4: 0.75, 1: 0.5, 0: 0.0}
CANDIDATE_PAIR_FEATURE_WEIGHTS = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
TYPED_EVENT_FIELDS = ({'name': 'EventSequence', 'type': 'uint64', 'required_for_sources': ['Knowledge', 'SkillExecutor', 'GoalTimer', 'GoalAuthority'], 'canonical_default': 0, 'constraint': 'nonzero', 'required_when': 'always'}, {'name': 'EventType', 'type': 'EEventType', 'required_for_sources': ['Knowledge', 'SkillExecutor', 'GoalAuthority'], 'canonical_default': 'NoneOrPadding', 'constraint': 'exact_generated_event_or_timer_default', 'required_when': 'source_applicable'}, {'name': 'Source', 'type': 'EFactSource', 'required_for_sources': ['Knowledge', 'SkillExecutor', 'GoalTimer', 'GoalAuthority'], 'canonical_default': 'None', 'constraint': 'exact_trusted_producer', 'required_when': 'always'}, {'name': 'GoalToken', 'type': 'FGoalToken', 'required_for_sources': ['Knowledge', 'SkillExecutor', 'GoalTimer', 'GoalAuthority'], 'canonical_default': 'ZeroGoalToken', 'constraint': 'full_exact_current_nonzero_token', 'required_when': 'always'}, {'name': 'KnowledgeRevision', 'type': 'uint64', 'required_for_sources': ['Knowledge'], 'canonical_default': 0, 'constraint': 'nonzero_when_required', 'required_when': 'source_applicable'}, {'name': 'DecisionId', 'type': 'uint64', 'required_for_sources': ['SkillExecutor'], 'canonical_default': 0, 'constraint': 'nonzero_when_required', 'required_when': 'source_applicable'}, {'name': 'Skill', 'type': 'ESkillId', 'required_for_sources': ['SkillExecutor'], 'canonical_default': 'SkillCountSentinel', 'constraint': 'exact_committed_skill_when_required', 'required_when': 'source_applicable'}, {'name': 'Target', 'type': 'FTargetHandleWire', 'required_for_sources': ['Knowledge', 'SkillExecutor', 'GoalAuthority'], 'canonical_default': 'ZeroTargetHandle', 'constraint': 'exact_identity_generation_revision_when_required', 'required_when': 'source_applicable'}, {'name': 'ExecutionStatus', 'type': 'EExecutionStatus', 'required_for_sources': ['SkillExecutor'], 'canonical_default': 'None', 'constraint': 'SucceededOrFailedWhenRequired', 'required_when': 'source_applicable'}, {'name': 'FailureReason', 'type': 'EFailureReason', 'required_for_sources': [], 'canonical_default': 'None', 'constraint': 'exact_nondefault_when_required', 'required_when': 'SkillExecutorAndExecutionStatusFailed'}, {'name': 'TimerId', 'type': 'string', 'required_for_sources': ['GoalTimer'], 'canonical_default': '', 'constraint': 'nonempty_when_required', 'required_when': 'source_applicable'}, {'name': 'TimerRuntimeEpoch', 'type': 'uint64', 'required_for_sources': ['GoalTimer'], 'canonical_default': 0, 'constraint': 'nonzero_when_required', 'required_when': 'source_applicable'})
TARGET_AUTHORITIES = ({'id': 'HomeWaypoint', 'target_kind': 'Waypoint', 'owner': 'GameplayGoalAuthority', 'lifetime': 'AuthoritySession', 'stable_id_policy': 'session_monotonic_nonzero_goal_target_allocator', 'generation': 1, 'initial_revision': 1, 'mutable': False, 'stored_in_knowledge': False, 'provenance_only': False, 'candidate_usable': True, 'capture_source': 'FirstExactAssemblyPawnFiniteWorldPosition', 'actor_transform_lookup': False, 'source_ttl_expiry_policy': 'not_applicable'}, {'id': 'SourceSoundHandle', 'target_kind': 'SoundEvent', 'owner': 'Knowledge', 'lifetime': 'SourceKnowledgeFact', 'stable_id_policy': 'exact_source_handle', 'generation': 0, 'initial_revision': 0, 'mutable': False, 'stored_in_knowledge': True, 'provenance_only': True, 'candidate_usable': False, 'capture_source': 'ExactCurrentSoundEventHandleAtRequest', 'actor_transform_lookup': False, 'source_ttl_expiry_policy': 'may_expire_after_goal_activation'}, {'id': 'DisturbancePosition', 'target_kind': 'WorldPosition', 'owner': 'GameplayGoalAuthority', 'lifetime': 'InvestigateGoalInstance', 'stable_id_policy': 'session_monotonic_nonzero_goal_target_allocator', 'generation': 1, 'initial_revision': 1, 'mutable': False, 'stored_in_knowledge': False, 'provenance_only': False, 'candidate_usable': True, 'capture_source': 'ExactSoundEventStimulusLocation', 'actor_transform_lookup': False, 'source_ttl_expiry_policy': 'preserve_immutable_position'})
EFFECT_AUTHORITIES = ({'name': 'request_new_goal', 'apply_effect_policy': 'stage_intent_only_no_external_mutation', 'pump_result': 'GoalRequested', 'transaction_policy': 'owner_bounded_prepare_interrupt_commit', 'failure_before_interrupt': 'preserve_old_goal_timer_and_running_skill', 'interrupt_failure': 'keep_old_goal_active_and_replan', 'failure_after_interrupt': 'keep_old_goal_active_without_running_skill_and_replan', 'post_commit_skill_start_failure': 'keep_new_goal_and_replan_or_wait_timeout', 'callback_free_atomic_steps': ['suspend_old_goal_and_pause_timer', 'activate_new_goal_and_install_primary_target', 'arm_new_phase_timer', 'supersede_pending_old_decision'], 'preserve': [], 'revision_without_target_change': 'not_applicable', 'revision_with_target_change': 'active_goal_transaction_single_publication'}, {'name': 'remain_and_replan', 'apply_effect_policy': 'stage_intent_only_no_external_mutation', 'pump_result': 'ReplanRequested', 'transaction_policy': 'supersede_pending_decision_then_request_new_snapshot', 'failure_before_interrupt': 'not_applicable', 'interrupt_failure': 'not_applicable', 'failure_after_interrupt': 'preserve_current_goal_and_pending_state', 'post_commit_skill_start_failure': 'remain_in_current_phase_and_replan', 'callback_free_atomic_steps': [], 'preserve': ['GoalInstance', 'Lifecycle', 'Phase', 'PhaseGeneration', 'PhaseDeadline', 'TimerRuntimeEpoch'], 'revision_without_target_change': 'unchanged', 'revision_with_target_change': 'increment_once_authoritative_primary_target_changed'})
TERMINAL_RESUME = {'terminal_states': ['Succeeded', 'Failed'], 'record_outcome': 'once_for_exact_goal_token', 'remove_terminal_goal': True, 'resume_goal': 'IdleObserve', 'resume_policy': 'ResumeSamePhase', 'required_suspended_goal_count': 1, 'timer_policy': 'reuse_stored_remaining', 'request_new_decision': True, 'missing_or_stale_idle_policy': 'dormant_fail_closed_no_synthetic_idle'}
DECISION_SCHEDULING = {'component_tick': False, 'max_pending_decisions_per_npc': 1, 'supersede_previous_pending': 'terminal_superseded', 'commit_deadline_policy': 'captured_ms_plus_40', 'request_edges': ['initial_goal_activation', 'committed_phase_change', 'remain_and_replan', 'terminal_goal_resume', 'running_skill_terminal_phase_unchanged', 'accepted_urgent_preemption']}


def find_initial_profile(profile_id: str) -> InitialProfile | None:
    return next((row for row in INITIAL_PROFILES if row.profile_id == profile_id), None)


def find_transition_binding(goal: GoalType, phase: GoalPhase, order: int) -> TransitionBinding | None:
    return next((row for row in TRANSITION_BINDINGS if (row.goal, row.phase, row.order) == (goal, phase, order)), None)


def phase_target_policy(goal: GoalType, phase: GoalPhase) -> PhaseTargetPolicySpec | None:
    return next((row for row in PHASE_TARGET_POLICIES if (row.goal, row.phase) == (goal, phase)), None)


def is_production_executable_skill(skill: SkillId) -> bool:
    return 0 <= int(skill) < int(SkillId.SkillCountSentinel) and bool(PRODUCTION_SKILL_MASK & (1 << int(skill)))


def utility_bias(skill: SkillId) -> float:
    return UTILITY_SKILL_BIASES.get(int(skill), ALL_OTHER_SKILL_BIAS)
