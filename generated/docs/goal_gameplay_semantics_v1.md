# General NPC Goal Gameplay Semantics V1

**Status: BOUNDED PRODUCTION AUTHORITY — PASS**

- Approved: `2026-08-20`
- Profile: `GuardPhase0`
- Goal Registry: `1.2.0`
- Gameplay semantics: `1.2.0`
- Goal Registry SHA-256: `2fe47b0376427c3c086e6d899b934d3d59ddbbd672c3b98900cf84837d1a8dda`
- 14 executable unique guards
- 0 provider-unavailable unique guards
- 18 executable transition bindings
- 0 unavailable transition bindings
- 6 production executable Skills
- Gameplay Goal FSM: **HOLD**

This authority is bounded to the listed profile and supported Goals. The complete guard catalog, other Goals, full arbitration/save archive, and whole Gameplay Goal FSM remain HOLD.

## Initial profile

| Profile | Initial Goal | Initial Phase | Goal Revision | Phase Generation |
|---|---|---|---:|---:|
| `GuardPhase0` | `IdleObserve` | `Observe` | 1 | 1 |

## Target authorities

| Authority | Kind | Owner | Lifetime | Stable ID policy | Capture source | Generation | Initial revision | Mutable | Stored in Knowledge | Provenance only | Candidate usable | Actor transform lookup | Source TTL expiry policy |
|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|
| `HomeWaypoint` | `Waypoint` | `GameplayGoalAuthority` | `AuthoritySession` | `session_monotonic_nonzero_goal_target_allocator` | `FirstExactAssemblyPawnFiniteWorldPosition` | 1 | 1 | `false` | `false` | `false` | `true` | `false` | `not_applicable` |
| `SourceSoundHandle` | `SoundEvent` | `Knowledge` | `SourceKnowledgeFact` | `exact_source_handle` | `ExactCurrentSoundEventHandleAtRequest` | 0 | 0 | `false` | `true` | `true` | `false` | `false` | `may_expire_after_goal_activation` |
| `DisturbancePosition` | `WorldPosition` | `GameplayGoalAuthority` | `InvestigateGoalInstance` | `session_monotonic_nonzero_goal_target_allocator` | `ExactSoundEventStimulusLocation` | 1 | 1 | `false` | `false` | `false` | `true` | `false` | `preserve_immutable_position` |
| `IdentifiedSubject` | `Entity` | `GameplayGoalAuthority` | `InvestigateGoalInstance` | `exact_sight_event_entity_stable_id` | `ExactCurrentVisibleEntityBindingFromAcceptedSightAcquired` | 0 | 0 | `true` | `true` | `false` | `true` | `true` | `fail_closed_when_current_visible_identity_cannot_resolve` |

## Subject identification

- Policy: `InvestigateVisibleSubjectV1`
- Applicable: `InvestigateDisturbance` / `Navigate, Search`
- Distance: `planar_xy_center_to_center_cm <= 700.0`
- Subject authority: `IdentifiedSubject`
- Committed Target: `frozen_after_commit`

## General policy orchestration

- Policy: `NeuralFirstUtilityFallbackV1`
- Primary: `NeuralPolicy`
- Fallback: `GeneratedUtilityProfile` / `GuardPhase0UtilityV1`
- Fallback on: `Unavailable, Failed, Abstained, Invalid`
- Snapshot: `exact_same_immutable_snapshot`
- Production Neural evaluator: `available_only_when_resolve_policy_ready`

## Production Skills

- `Idle`
- `TurnTo`
- `Approach`
- `Investigate`
- `SearchArea`
- `Greet`

Control candidate: `ContinueCurrentAction`

## Phase Target Policies

| Goal | Phase | Policy | Target authority |
|---|---|---|---|
| `IdleObserve` | `Observe` | `AnyAllowedTargetOrNoTarget` | `none` |
| `InvestigateDisturbance` | `Orient` | `ActiveGoalPrimaryTargetOnly` | `DisturbancePosition` |
| `InvestigateDisturbance` | `Navigate` | `ActiveGoalPrimaryTargetOnly` | `DisturbancePosition` |
| `InvestigateDisturbance` | `Search` | `ActiveGoalPrimaryTargetOnly` | `DisturbancePosition` |
| `InvestigateDisturbance` | `Resolve` | `ActiveGoalPrimaryTargetOnly` | `IdentifiedSubject` |
| `InvestigateDisturbance` | `Return` | `ActiveGoalPrimaryTargetOnly` | `HomeWaypoint` |

## Guard authorities

| Guard | Availability | Bindings |
|---|---|---:|
| `valid_disturbance_target` | `executable` | 1 |
| `social_subject` | `executable` | 1 |
| `orientation_complete` | `executable` | 1 |
| `no_valid_snapshot` | `executable` | 1 |
| `phase_timeout` | `executable` | 3 |
| `arrived_at_snapshot` | `executable` | 1 |
| `PathUnavailable` | `executable` | 2 |
| `subject_identified` | `executable` | 2 |
| `search_budget_exhausted` | `executable` | 1 |
| `resolution_complete` | `executable` | 1 |
| `identified_subject_invalid_recoverable` | `executable` | 1 |
| `identified_subject_invalid_unrecoverable` | `executable` | 1 |
| `resolution_failed` | `executable` | 1 |
| `at_return_target` | `executable` | 1 |

## Utility

Profile: `GuardPhase0UtilityV1`

| Skill | Bias |
|---|---:|
| `SearchArea` | 1.5 |
| `Investigate` | 1.25 |
| `TurnTo` | 1.0 |
| `Approach` | 0.75 |
| `ContinueCurrentAction` | 0.5 |
| `Idle` | 0.0 |
| all other Skills | -2.5 |

## Effects

| Effect | Apply policy | Pump result | Transaction policy | Failure before interrupt | Interrupt failure | Failure after interrupt | Post-commit Skill start failure | Callback-free atomic steps | Preserve | Revision without target change | Revision with target change |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `request_new_goal` | `stage_intent_only_no_external_mutation` | `GoalRequested` | `owner_bounded_prepare_interrupt_commit` | `preserve_old_goal_timer_and_running_skill` | `keep_old_goal_active_and_replan` | `keep_old_goal_active_without_running_skill_and_replan` | `keep_new_goal_and_replan_or_wait_timeout` | `suspend_old_goal_and_pause_timer, activate_new_goal_and_install_primary_target, arm_new_phase_timer, supersede_pending_old_decision` | `none` | `not_applicable` | `active_goal_transaction_single_publication` |
| `remain_and_replan` | `stage_intent_only_no_external_mutation` | `ReplanRequested` | `supersede_pending_decision_then_request_new_snapshot` | `not_applicable` | `not_applicable` | `preserve_current_goal_and_pending_state` | `remain_in_current_phase_and_replan` | `none` | `GoalInstance, Lifecycle, Phase, PhaseGeneration, PhaseDeadline, TimerRuntimeEpoch` | `unchanged` | `increment_once_authoritative_primary_target_changed` |

## Typed event fields

| Field | Type | Required sources | Canonical default |
|---|---|---|---|
| `EventSequence` | `uint64` | Knowledge, SkillExecutor, GoalTimer, GoalAuthority | `0` |
| `EventType` | `EEventType` | Knowledge, SkillExecutor, GoalAuthority | `NoneOrPadding` |
| `Source` | `EFactSource` | Knowledge, SkillExecutor, GoalTimer, GoalAuthority | `None` |
| `GoalToken` | `FGoalToken` | Knowledge, SkillExecutor, GoalTimer, GoalAuthority | `ZeroGoalToken` |
| `KnowledgeRevision` | `uint64` | Knowledge | `0` |
| `DecisionId` | `uint64` | SkillExecutor | `0` |
| `Skill` | `ESkillId` | SkillExecutor | `SkillCountSentinel` |
| `Target` | `FTargetHandleWire` | Knowledge, SkillExecutor, GoalAuthority | `ZeroTargetHandle` |
| `ExecutionStatus` | `EExecutionStatus` | SkillExecutor | `None` |
| `FailureReason` | `EFailureReason` | conditional | `None` |
| `TimerId` | `string` | GoalTimer | `` |
| `TimerRuntimeEpoch` | `uint64` | GoalTimer | `0` |
