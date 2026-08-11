#!/usr/bin/env python3
"""Validate and deterministically generate bounded Goal gameplay semantics V1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

import yaml


CPP_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DOC_BEGIN = "<!-- BEGIN GOAL GAMEPLAY SEMANTICS V1 STATUS -->"
DOC_END = "<!-- END GOAL GAMEPLAY SEMANTICS V1 STATUS -->"


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and CPP_IDENTIFIER.fullmatch(value) is not None


def _unique_strings(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_identifier(item) for item in value)
        and len(set(value)) == len(value)
    )


def _rows_by_name(rows: Any, key: str = "name") -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        return {}
    return {
        row[key]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get(key), str)
    }


def _enum_map(rows: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if (
            isinstance(row, dict)
            and _identifier(row.get("name"))
            and isinstance(row.get("id"), int)
            and not isinstance(row.get("id"), bool)
        ):
            result[row["name"]] = row["id"]
    return result


def _transition_rows(registry: dict[str, Any], supported: set[str]) -> dict[tuple[str, str, int], dict[str, Any]]:
    result: dict[tuple[str, str, int], dict[str, Any]] = {}
    for goal in registry.get("goals", []):
        if not isinstance(goal, dict) or goal.get("name") not in supported:
            continue
        for phase, spec in goal.get("phases", {}).items():
            if not isinstance(spec, dict):
                continue
            for row in spec.get("transitions", []):
                if isinstance(row, dict) and isinstance(row.get("order"), int):
                    result[(goal["name"], phase, row["order"])] = row
    return result


def _field_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    event = contract.get("typed_event_fact", {})
    return _rows_by_name(event.get("fields", [])) if isinstance(event, dict) else {}


def validate_registry(
    registry: dict[str, Any],
    skill_registry: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    """Return every bounded-authority contract error without mutating inputs."""
    errors: list[str] = []
    contract = registry.get("goal_gameplay_semantics_v1")
    if not isinstance(contract, dict):
        return ["goal gameplay semantics authority missing"]

    header = registry.get("registry", {})
    schema_goal_version = schema.get("constants", {}).get("goal_registry_version")
    if not isinstance(header, dict) or header.get("version") != schema_goal_version:
        errors.append("goal registry version mismatch")
    if contract.get("version") != "1.0.0":
        errors.append("goal gameplay semantics version mismatch")
    if contract.get("status") != "approved_production_authority" or not isinstance(contract.get("approved_on"), str):
        errors.append("goal gameplay authority status mismatch")

    scope = contract.get("scope")
    if not isinstance(scope, dict):
        return errors + ["goal gameplay scope mismatch"]
    supported_list = scope.get("supported_goals")
    if not _unique_strings(supported_list, allow_empty=False):
        errors.append("supported goal scope mismatch")
        supported_list = []
    supported = set(supported_list)
    claims = scope.get("claims")
    claim_keys = {
        "executable_unique_guards",
        "unavailable_unique_guards",
        "executable_transition_bindings",
        "unavailable_transition_bindings",
        "effects",
        "production_executable_skills",
        "full_guard_catalog_pass",
    }
    if not isinstance(claims, dict) or set(claims) != claim_keys or claims.get("full_guard_catalog_pass") is not False:
        errors.append("bounded scope claims mismatch")
        claims = {}

    schema_enums = schema.get("enums", {}) if isinstance(schema.get("enums"), dict) else {}
    goal_ids = _enum_map(registry.get("goal_types"))
    phase_ids = _enum_map(registry.get("goal_phases"))
    skill_ids = _enum_map(skill_registry.get("skills"))
    target_kind_ids = _enum_map(schema_enums.get("target_kind"))
    event_ids = _enum_map(schema_enums.get("event_type"))
    schema_goal_ids = _enum_map(schema_enums.get("goal_type"))
    schema_phase_ids = _enum_map(schema_enums.get("goal_phase"))
    schema_skill_ids = _enum_map(schema_enums.get("skill"))
    if goal_ids != schema_goal_ids or phase_ids != schema_phase_ids or skill_ids != schema_skill_ids:
        errors.append("registry/schema enum parity mismatch")
    if not supported or not supported.issubset(goal_ids):
        errors.append("supported goal enum mismatch")

    profiles = contract.get("initial_profiles")
    profile_id = scope.get("profile_id")
    if not isinstance(profiles, list) or len(profiles) != 1 or not isinstance(profiles[0], dict):
        errors.append("initial profile authority mismatch")
        profiles = []
    else:
        profile = profiles[0]
        if (
            profile.get("profile_id") != profile_id
            or profile.get("initial_goal") not in supported
            or profile.get("initial_phase") not in phase_ids
            or profile.get("initial_goal_revision") != 1
            or profile.get("initial_phase_generation") != 1
            or profile.get("activation_precondition_target") in (None, "")
        ):
            errors.append("initial profile authority mismatch")

    targets = contract.get("target_authorities")
    target_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(targets, list) or not targets:
        errors.append("target authority table mismatch")
        targets = []
    for row in targets:
        if not isinstance(row, dict) or not _identifier(row.get("id")):
            errors.append("target authority row mismatch")
            continue
        target_id = row["id"]
        if target_id in target_by_id:
            errors.append("duplicate target authority")
        target_by_id[target_id] = row
        if row.get("target_kind") not in target_kind_ids or not isinstance(row.get("candidate_usable"), bool):
            errors.append(f"target authority {target_id} mismatch")
    for profile in profiles:
        if profile.get("activation_precondition_target") not in target_by_id:
            errors.append("initial profile target authority missing")

    policies = contract.get("phase_target_policies")
    policy_keys: set[tuple[str, str]] = set()
    if not isinstance(policies, list) or not policies:
        errors.append("phase target policy table mismatch")
        policies = []
    unavailable_pairs: set[tuple[str, str]] = set()
    for row in policies:
        if not isinstance(row, dict):
            errors.append("phase target policy row mismatch")
            continue
        key = (row.get("goal"), row.get("phase"))
        if key in policy_keys:
            errors.append("duplicate phase target policy")
        policy_keys.add(key)
        if key[0] not in supported or key[1] not in phase_ids:
            errors.append("phase target policy scope mismatch")
        authority_id = row.get("target_authority")
        if authority_id:
            target = target_by_id.get(authority_id)
            if not target or target.get("candidate_usable") is not True:
                errors.append("phase policy requires candidate-usable target authority")
            elif row.get("required_target_kind") != target.get("target_kind"):
                errors.append("phase target kind/authority mismatch")
        if row.get("continue_policy") == "unavailable":
            unavailable_pairs.add(key)

    skill_rows = _rows_by_name(skill_registry.get("skills"))
    production = contract.get("production_skills")
    if not isinstance(production, dict):
        errors.append("production skill authority mismatch")
        production = {}
    executable = production.get("executable")
    if not _unique_strings(executable, allow_empty=False):
        errors.append("production executable skill set mismatch")
        executable = []
    expected_count = claims.get("production_executable_skills")
    if len(executable) != expected_count:
        errors.append("production executable skill count mismatch")
    for name in executable:
        if name not in skill_rows or skill_rows[name].get("executable") is not True:
            errors.append("production executable skill mismatch")
    control = production.get("control")
    if control not in skill_rows or skill_rows[control].get("control_candidate") is not True:
        errors.append("production control skill mismatch")

    utility = contract.get("utility_profile")
    if not isinstance(utility, dict):
        errors.append("utility profile mismatch")
        utility = {}
    if utility.get("deterministic") is not True:
        errors.append("utility determinism mismatch")
    if not _identifier(utility.get("profile_id")):
        errors.append("utility profile id mismatch")
    biases = utility.get("skill_biases")
    if not isinstance(biases, dict) or not biases or not set(biases).issubset(skill_ids):
        errors.append("utility skill bias mismatch")
        biases = {}
    numeric_values = list(biases.values())
    numeric_values.append(utility.get("all_other_skill_bias"))
    weights = utility.get("candidate_pair_feature_weights")
    feature_count = schema.get("constants", {}).get("candidate_pair_feature_count")
    if not isinstance(weights, list) or len(weights) != feature_count:
        errors.append("utility feature weight count mismatch")
        weights = []
    numeric_values.extend(weights)
    if not all(_finite_number(value) for value in numeric_values):
        errors.append("utility numeric value must be finite")

    fields = _field_map(contract)
    expected_fields = (
        "EventSequence",
        "EventType",
        "Source",
        "GoalToken",
        "KnowledgeRevision",
        "DecisionId",
        "Skill",
        "Target",
        "ExecutionStatus",
        "FailureReason",
        "TimerId",
        "TimerRuntimeEpoch",
    )
    if tuple(fields) != expected_fields:
        errors.append("typed event field order mismatch")
    source_names: set[str] = set()
    for field in fields.values():
        required = field.get("required_for_sources")
        if not _unique_strings(required):
            errors.append("typed event source applicability mismatch")
        else:
            source_names.update(required)
    skill_field = fields.get("Skill", {})
    if skill_field.get("canonical_default") != f"{skill_field.get('name', '')}CountSentinel":
        errors.append("typed event non-applicable skill sentinel mismatch")

    transitions = _transition_rows(registry, supported)
    authorities = contract.get("guard_authorities")
    authority_names: list[str] = []
    flattened: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if not isinstance(authorities, list) or not authorities:
        errors.append("guard authority table mismatch")
        authorities = []
    for authority in authorities:
        if not isinstance(authority, dict) or not _identifier(authority.get("guard")):
            errors.append("guard authority row mismatch")
            continue
        guard = authority["guard"]
        authority_names.append(guard)
        availability = authority.get("availability")
        bindings = authority.get("bindings")
        if availability not in ("executable", "provider_unavailable") or not isinstance(bindings, list) or not bindings:
            errors.append(f"guard authority {guard} mismatch")
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                errors.append("transition binding row mismatch")
                continue
            flattened.append((authority, binding))
    if len(authority_names) != len(set(authority_names)):
        errors.append("duplicate guard authority")

    transition_guards = {row.get("guard") for row in transitions.values()}
    if set(authority_names) != transition_guards:
        errors.append("transition binding guard authority coverage mismatch")

    keys_seen: set[tuple[Any, Any, Any]] = set()
    executable_bindings = 0
    unavailable_bindings = 0
    executable_guards = 0
    unavailable_guards = 0
    failure_names = set(skill_registry.get("failure_taxonomy", []))
    skill_sources = set(skill_field.get("required_for_sources", [])) if isinstance(skill_field, dict) else set()
    for authority in authorities:
        if not isinstance(authority, dict):
            continue
        if authority.get("availability") == "executable":
            executable_guards += 1
        elif authority.get("availability") == "provider_unavailable":
            unavailable_guards += 1
    for authority, binding in flattened:
        key = (binding.get("goal"), binding.get("phase"), binding.get("order"))
        if key in keys_seen:
            errors.append("duplicate transition binding")
        keys_seen.add(key)
        transition = transitions.get(key)
        if (
            transition is None
            or transition.get("guard") != authority.get("guard")
            or transition.get("trigger") != binding.get("trigger")
        ):
            errors.append(f"transition binding mismatch at {key}")
        availability = authority.get("availability")
        if availability == "executable":
            executable_bindings += 1
        else:
            unavailable_bindings += 1
        if key[:2] in unavailable_pairs and availability == "executable":
            errors.append("unavailable phase has executable guard authority")
        fact_source = binding.get("fact_source")
        if fact_source not in source_names and fact_source != "Unavailable":
            errors.append("transition binding fact source mismatch")
        accepted_skills = binding.get("accepted_skills")
        accepted_kinds = binding.get("accepted_target_kinds")
        accepted_failures = binding.get("accepted_failure_reasons")
        target_refs = binding.get("target_authorities")
        requirements = binding.get("requirements")
        if not _unique_strings(accepted_skills) or not set(accepted_skills).issubset(skill_ids):
            errors.append("transition binding accepted Skill mismatch")
        if not _unique_strings(accepted_kinds) or not set(accepted_kinds).issubset(target_kind_ids):
            errors.append("transition binding accepted Target kind mismatch")
        if not _unique_strings(accepted_failures) or not set(accepted_failures).issubset(failure_names):
            errors.append("transition binding failure reason mismatch")
        if not _unique_strings(target_refs) or not set(target_refs).issubset(target_by_id):
            errors.append("transition binding target authority mismatch")
        if not _unique_strings(requirements, allow_empty=False):
            errors.append("transition binding requirement mismatch")
        if fact_source in skill_sources and not accepted_skills:
            errors.append("Skill event binding requires accepted Skill payload")
        if availability == "provider_unavailable" and fact_source != "Unavailable":
            errors.append("unavailable guard must fail closed")

    if keys_seen != set(transitions):
        errors.append("transition binding coverage mismatch")
    if executable_guards != claims.get("executable_unique_guards"):
        errors.append("executable unique guard count mismatch")
    if unavailable_guards != claims.get("unavailable_unique_guards"):
        errors.append("unavailable unique guard count mismatch")
    if executable_bindings != claims.get("executable_transition_bindings"):
        errors.append("executable transition binding count mismatch")
    if unavailable_bindings != claims.get("unavailable_transition_bindings"):
        errors.append("unavailable transition binding count mismatch")

    effects = contract.get("effects")
    effect_rows = _rows_by_name(effects)
    if not isinstance(effects, list) or len(effect_rows) != len(effects):
        errors.append("effect authority table mismatch")
        effects = []
    transition_effects = {row["effect"] for row in transitions.values() if isinstance(row.get("effect"), str)}
    if set(effect_rows) != transition_effects:
        errors.append("effect authority transition coverage mismatch")
    if len(effect_rows) != claims.get("effects"):
        errors.append("effect authority count mismatch")
    goal_request_effects = {
        row.get("effect")
        for row in transitions.values()
        if row.get("to_goal") is not None and isinstance(row.get("effect"), str)
    }
    rollback_keys = {
        "failure_before_interrupt",
        "interrupt_failure",
        "failure_after_interrupt",
        "post_commit_skill_start_failure",
        "callback_free_atomic_steps",
    }
    for name, effect in effect_rows.items():
        if effect.get("apply_effect_policy") != "stage_intent_only_no_external_mutation":
            errors.append(f"{name} effect must stage intent")
        if name in goal_request_effects and (not rollback_keys.issubset(effect) or not effect.get("callback_free_atomic_steps")):
            errors.append(f"{name} effect rollback transaction mismatch")

    terminal = contract.get("terminal_resume")
    if not isinstance(terminal, dict) or terminal.get("resume_goal") not in supported:
        errors.append("terminal resume authority mismatch")
    scheduling = contract.get("decision_scheduling")
    if not isinstance(scheduling, dict) or scheduling.get("component_tick") is not False or scheduling.get("max_pending_decisions_per_npc") != 1:
        errors.append("decision scheduling authority mismatch")
    return errors


def _py_name(name: str) -> str:
    return f"{name}_" if name in {"None", "True", "False"} else name


def _cpp_name(name: str) -> str:
    if not _identifier(name):
        raise ValueError(f"invalid C++ identifier: {name!r}")
    return name


def _cpp_number(value: Any) -> str:
    if not _finite_number(value):
        raise ValueError(f"non-finite number: {value!r}")
    text = format(float(value), ".17g")
    return text if any(character in text for character in ".eE") else f"{text}.0"


def _ordered_unique(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _mask(names: Iterable[str], ids: dict[str, int]) -> int:
    result = 0
    for name in names:
        result |= 1 << ids[name]
    return result


def _contract_maps(registry: dict[str, Any], skill_registry: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    contract = registry["goal_gameplay_semantics_v1"]
    schema_enums = schema["enums"]
    fields = _field_map(contract)
    fact_sources = ["None"] + list(fields["EventSequence"]["required_for_sources"])
    fact_sources += [
        binding["fact_source"]
        for authority in contract["guard_authorities"]
        for binding in authority["bindings"]
    ]
    requirements = _ordered_unique(
        requirement
        for authority in contract["guard_authorities"]
        for binding in authority["bindings"]
        for requirement in binding["requirements"]
    )
    target_authorities = ["None"] + [row["id"] for row in contract["target_authorities"]]
    target_policies = _ordered_unique(row["policy"] for row in contract["phase_target_policies"])
    availability = _ordered_unique(row["availability"] for row in contract["guard_authorities"])
    failure_reasons = ["None"] + list(skill_registry["failure_taxonomy"])
    return {
        "contract": contract,
        "goal_ids": _enum_map(registry["goal_types"]),
        "phase_ids": _enum_map(registry["goal_phases"]),
        "skill_ids": _enum_map(skill_registry["skills"]),
        "target_kind_ids": _enum_map(schema_enums["target_kind"]),
        "event_ids": _enum_map(schema_enums["event_type"]),
        "guard_ids": {row["guard"]: index for index, row in enumerate(contract["guard_authorities"])},
        "fact_source_ids": {name: index for index, name in enumerate(_ordered_unique(fact_sources))},
        "requirement_ids": {name: index for index, name in enumerate(requirements)},
        "target_authority_ids": {name: index for index, name in enumerate(target_authorities)},
        "target_policy_ids": {name: index for index, name in enumerate(target_policies)},
        "availability_ids": {name: index for index, name in enumerate(availability)},
        "failure_ids": {name: index for index, name in enumerate(failure_reasons)},
    }


def _py_enum(name: str, values: dict[str, int]) -> str:
    rows = "\n".join(f"    {_py_name(item)} = {value}" for item, value in values.items())
    return f"class {name}(IntEnum):\n{rows}\n"


def generate_python(
    registry: dict[str, Any],
    skill_registry: dict[str, Any],
    schema: dict[str, Any],
    digest: str,
) -> str:
    maps = _contract_maps(registry, skill_registry, schema)
    contract = maps["contract"]
    enum_blocks = [
        _py_enum("GoalType", maps["goal_ids"]),
        _py_enum("GoalPhase", maps["phase_ids"]),
        _py_enum("SkillId", {**maps["skill_ids"], "SkillCountSentinel": len(maps["skill_ids"])}),
        _py_enum("TargetKind", maps["target_kind_ids"]),
        _py_enum("EventType", maps["event_ids"]),
        _py_enum("GuardId", maps["guard_ids"]),
        _py_enum("FactSource", maps["fact_source_ids"]),
        _py_enum("RequirementId", maps["requirement_ids"]),
        _py_enum("FailureReason", maps["failure_ids"]),
        _py_enum("TargetAuthorityId", maps["target_authority_ids"]),
        _py_enum("TargetPolicy", maps["target_policy_ids"]),
        _py_enum("GuardAvailability", maps["availability_ids"]),
    ]
    profiles = []
    for row in contract["initial_profiles"]:
        profiles.append(
            "    InitialProfile("
            f"{row['profile_id']!r}, GoalType.{_py_name(row['initial_goal'])}, GoalPhase.{_py_name(row['initial_phase'])}, "
            f"{row['initial_goal_revision']}, {row['initial_phase_generation']}, {row['goal_instance_id_policy']!r}, "
            f"{row['lifecycle']!r}, {row['activation_precondition_target']!r}, {row['failure_policy']!r}),"
        )
    policy_rows = []
    for row in contract["phase_target_policies"]:
        authority = row["target_authority"] or "None"
        policy_rows.append(
            "    PhaseTargetPolicySpec("
            f"GoalType.{_py_name(row['goal'])}, GoalPhase.{_py_name(row['phase'])}, "
            f"TargetPolicy.{_py_name(row['policy'])}, TargetAuthorityId.{_py_name(authority)}, "
            f"TargetKind.{_py_name(row['required_target_kind'])}, {row['exact_identity_and_revision']!r}, "
            f"{row['continue_policy']!r}, {row['entry_target_change']!r}),"
        )
    binding_rows = []
    for authority in contract["guard_authorities"]:
        for row in authority["bindings"]:
            trigger = row["trigger"]
            event_name = trigger.get("event_type", "NoneOrPadding")
            binding_rows.append(
                "    TransitionBinding("
                f"GoalType.{_py_name(row['goal'])}, GoalPhase.{_py_name(row['phase'])}, {row['order']}, "
                f"GuardId.{_py_name(authority['guard'])}, GuardAvailability.{_py_name(authority['availability'])}, "
                f"{trigger['kind']!r}, EventType.{_py_name(event_name)}, {trigger.get('timer_id', '')!r}, "
                f"FactSource.{_py_name(row['fact_source'])}, {_mask(row['accepted_skills'], maps['skill_ids'])}, "
                f"{_mask(row['accepted_target_kinds'], maps['target_kind_ids'])}, "
                f"{_mask(row['target_authorities'], maps['target_authority_ids'])}, "
                f"{_mask(row['accepted_failure_reasons'], maps['failure_ids'])}, "
                f"{_mask(row['requirements'], maps['requirement_ids'])}),"
            )
    executable_mask = _mask(contract["production_skills"]["executable"], maps["skill_ids"])
    utility_biases = {
        maps["skill_ids"][name]: float(value)
        for name, value in contract["utility_profile"]["skill_biases"].items()
    }
    text = f'''"""AUTO-GENERATED. DO NOT EDIT. Bounded Goal gameplay semantics V1."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum

GOAL_REGISTRY_SHA256 = {digest!r}
GOAL_REGISTRY_VERSION = {registry['registry']['version']!r}
GAMEPLAY_SEMANTICS_VERSION = {contract['version']!r}
PROFILE_ID = {contract['scope']['profile_id']!r}
UTILITY_PROFILE_ID = {contract['utility_profile']['profile_id']!r}

{chr(10).join(enum_blocks)}
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
{chr(10).join(profiles)}
)
PHASE_TARGET_POLICIES = (
{chr(10).join(policy_rows)}
)
TRANSITION_BINDINGS = (
{chr(10).join(binding_rows)}
)
EXECUTABLE_UNIQUE_GUARD_COUNT = {contract['scope']['claims']['executable_unique_guards']}
UNAVAILABLE_UNIQUE_GUARD_COUNT = {contract['scope']['claims']['unavailable_unique_guards']}
EXECUTABLE_TRANSITION_BINDING_COUNT = {contract['scope']['claims']['executable_transition_bindings']}
PRODUCTION_SKILL_MASK = {executable_mask}
CONTROL_SKILL = SkillId.{_py_name(contract['production_skills']['control'])}
ALL_OTHER_SKILL_BIAS = {_cpp_number(contract['utility_profile']['all_other_skill_bias'])}
UTILITY_SKILL_BIASES = {utility_biases!r}
CANDIDATE_PAIR_FEATURE_WEIGHTS = {tuple(float(value) for value in contract['utility_profile']['candidate_pair_feature_weights'])!r}
TYPED_EVENT_FIELDS = {tuple(contract['typed_event_fact']['fields'])!r}
TARGET_AUTHORITIES = {tuple(contract['target_authorities'])!r}
EFFECT_AUTHORITIES = {tuple(contract['effects'])!r}
TERMINAL_RESUME = {contract['terminal_resume']!r}
DECISION_SCHEDULING = {contract['decision_scheduling']!r}


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
'''
    return text


def _cpp_enum(name: str, values: dict[str, int], underlying: str = "std::uint8_t") -> str:
    rows = "\n".join(f"    {_cpp_name(item)} = {value}," for item, value in values.items())
    return f"enum class {name} : {underlying} {{\n{rows}\n}};"


def generate_cpp(
    registry: dict[str, Any],
    skill_registry: dict[str, Any],
    schema: dict[str, Any],
    digest: str,
) -> str:
    maps = _contract_maps(registry, skill_registry, schema)
    contract = maps["contract"]
    profiles = []
    for row in contract["initial_profiles"]:
        profiles.append(
            "    FInitialProfile{"
            f'"{row["profile_id"]}", SchemaV2::EGoalType::{_cpp_name(row["initial_goal"])}, '
            f'SchemaV2::EGoalPhase::{_cpp_name(row["initial_phase"])}, {row["initial_goal_revision"]}ULL, '
            f'{row["initial_phase_generation"]}ULL, "{row["goal_instance_id_policy"]}", '
            f'"{row["lifecycle"]}", "{row["activation_precondition_target"]}", "{row["failure_policy"]}"}},'
        )
    policies = []
    for row in contract["phase_target_policies"]:
        authority_name = row["target_authority"] or "None"
        policies.append(
            "    FPhaseTargetPolicy{"
            f"SchemaV2::EGoalType::{_cpp_name(row['goal'])}, SchemaV2::EGoalPhase::{_cpp_name(row['phase'])}, "
            f"ETargetPolicy::{_cpp_name(row['policy'])}, ETargetAuthorityId::{_cpp_name(authority_name)}, "
            f"SchemaV2::ETargetKind::{_cpp_name(row['required_target_kind'])}, "
            f"{'true' if row['exact_identity_and_revision'] else 'false'}, \"{row['continue_policy']}\", \"{row['entry_target_change']}\"}},"
        )
    target_authorities = []
    for row in contract["target_authorities"]:
        target_authorities.append(
            "    FTargetAuthority{"
            f"ETargetAuthorityId::{_cpp_name(row['id'])}, SchemaV2::ETargetKind::{_cpp_name(row['target_kind'])}, "
            f'"{row["owner"]}", "{row["lifetime"]}", "{row["stable_id_policy"]}", '
            f"{'true' if row['owner'] == 'GameplayGoalAuthority' else 'false'}, "
            f"{'true' if row['owner'] == 'Knowledge' else 'false'}, "
            f"{'true' if row['lifetime'] == 'AuthoritySession' else 'false'}, "
            f"{'true' if row['lifetime'] == 'SourceKnowledgeFact' else 'false'}, "
            f"{'true' if row['lifetime'] == 'InvestigateGoalInstance' else 'false'}, "
            f"{'true' if row['stable_id_policy'] == 'session_monotonic_nonzero_goal_target_allocator' else 'false'}, "
            f"{'true' if row['stable_id_policy'] == 'exact_source_handle' else 'false'}, "
            f"{int(row['generation'])}ULL, {int(row['initial_revision'])}ULL, "
            f"{'true' if row['mutable'] else 'false'}, {'true' if row['stored_in_knowledge'] else 'false'}, "
            f"{'true' if row['provenance_only'] else 'false'}, {'true' if row['candidate_usable'] else 'false'}, "
            f'"{row["capture_source"]}", '
            f"{'true' if row['capture_source'] == 'FirstExactAssemblyPawnFiniteWorldPosition' else 'false'}, "
            f"{'true' if row['capture_source'] == 'ExactCurrentSoundEventHandleAtRequest' else 'false'}, "
            f"{'true' if row['capture_source'] == 'ExactSoundEventStimulusLocation' else 'false'}, "
            f'{"true" if row["actor_transform_lookup"] else "false"}, '
            f'"{row["source_ttl_expiry_policy"]}"}},'
        )
    effect_authorities = []
    for row in contract["effects"]:
        effect_authorities.append(
            "    FEffectAuthority{"
            f'"{row["name"]}", "{row["apply_effect_policy"]}", "{row["pump_result"]}", '
            f"{'true' if row['apply_effect_policy'] == 'stage_intent_only_no_external_mutation' else 'false'}, "
            f"{'true' if row['pump_result'] == 'GoalRequested' else 'false'}, "
            f"{'true' if row['transaction_policy'] == 'owner_bounded_prepare_interrupt_commit' else 'false'}, "
            f'"{row["transaction_policy"]}", "{row["failure_before_interrupt"]}", '
            f'"{row["interrupt_failure"]}", "{row["failure_after_interrupt"]}", '
            f'"{row["post_commit_skill_start_failure"]}", '
            f'"{"|".join(row["callback_free_atomic_steps"])}", "{"|".join(row["preserve"])}", '
            f'"{row["revision_without_target_change"]}", "{row["revision_with_target_change"]}"}},'
        )
    bindings = []
    for authority in contract["guard_authorities"]:
        for row in authority["bindings"]:
            trigger = row["trigger"]
            event_name = trigger.get("event_type", "NoneOrPadding")
            bindings.append(
                "    FTransitionBinding{"
                f"SchemaV2::EGoalType::{_cpp_name(row['goal'])}, SchemaV2::EGoalPhase::{_cpp_name(row['phase'])}, {row['order']}U, "
                f"EGuardId::{_cpp_name(authority['guard'])}, EGuardAvailability::{_cpp_name(authority['availability'])}, "
                f"ETriggerKind::{_cpp_name(trigger['kind'].title())}, SchemaV2::EEventType::{_cpp_name(event_name)}, "
                f'"{trigger.get("timer_id", "")}", EFactSource::{_cpp_name(row["fact_source"])}, '
                f"{_mask(row['accepted_skills'], maps['skill_ids'])}ULL, {_mask(row['accepted_target_kinds'], maps['target_kind_ids'])}ULL, "
                f"{_mask(row['target_authorities'], maps['target_authority_ids'])}ULL, "
                f"{_mask(row['accepted_failure_reasons'], maps['failure_ids'])}ULL, "
                f"{_mask(row['requirements'], maps['requirement_ids'])}ULL}},"
            )
    utility_cases = "\n".join(
        f"    case SchemaV2::ESkillId::{_cpp_name(name)}: return {_cpp_number(value)};"
        for name, value in contract["utility_profile"]["skill_biases"].items()
    )
    weights = ", ".join(_cpp_number(value) for value in contract["utility_profile"]["candidate_pair_feature_weights"])
    executable_mask = _mask(contract["production_skills"]["executable"], maps["skill_ids"])
    enum_blocks = "\n\n".join(
        [
            _cpp_enum("EGuardId", maps["guard_ids"]),
            _cpp_enum("EFactSource", maps["fact_source_ids"]),
            _cpp_enum("ERequirementId", maps["requirement_ids"]),
            _cpp_enum("EFailureReason", maps["failure_ids"]),
            _cpp_enum("ETargetAuthorityId", maps["target_authority_ids"]),
            _cpp_enum("ETargetPolicy", maps["target_policy_ids"]),
            _cpp_enum("EGuardAvailability", maps["availability_ids"]),
            "enum class ETriggerKind : std::uint8_t { Event, Timer };",
        ]
    )
    return f'''// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include "AINativeNPCContracts.generated.h"

namespace AINativeNPC::GoalGameplayV1 {{
inline constexpr const char* GoalRegistrySha256 = "{digest}";
inline constexpr const char* GoalRegistryVersion = "{registry['registry']['version']}";
inline constexpr const char* GameplaySemanticsVersion = "{contract['version']}";
inline constexpr const char* ProfileId = "{contract['scope']['profile_id']}";
inline constexpr const char* UtilityProfileId = "{contract['utility_profile']['profile_id']}";

{enum_blocks}

struct FInitialProfile {{
    const char* Profile;
    SchemaV2::EGoalType Goal;
    SchemaV2::EGoalPhase Phase;
    std::uint64_t InitialGoalRevision;
    std::uint64_t InitialPhaseGeneration;
    const char* GoalInstanceIdPolicy;
    const char* Lifecycle;
    const char* ActivationPreconditionTarget;
    const char* FailurePolicy;
}};
struct FTransitionBinding {{
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
}};
struct FPhaseTargetPolicy {{
    SchemaV2::EGoalType Goal;
    SchemaV2::EGoalPhase Phase;
    ETargetPolicy Policy;
    ETargetAuthorityId TargetAuthority;
    SchemaV2::ETargetKind RequiredTargetKind;
    bool ExactIdentityAndRevision;
    const char* ContinuePolicy;
    const char* EntryTargetChange;
}};
struct FTargetAuthority {{
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
}};
struct FEffectAuthority {{
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
}};

inline constexpr std::array<FInitialProfile, {len(profiles)}> InitialProfiles{{{{
{chr(10).join(profiles)}
}}}};
inline constexpr std::array<FTransitionBinding, {len(bindings)}> TransitionBindings{{{{
{chr(10).join(bindings)}
}}}};
inline constexpr std::array<FPhaseTargetPolicy, {len(policies)}> PhaseTargetPolicies{{{{
{chr(10).join(policies)}
}}}};
inline constexpr std::array<FTargetAuthority, {len(target_authorities)}> TargetAuthorities{{{{
{chr(10).join(target_authorities)}
}}}};
inline constexpr std::array<FEffectAuthority, {len(effect_authorities)}> EffectAuthorities{{{{
{chr(10).join(effect_authorities)}
}}}};
inline constexpr std::size_t ExecutableUniqueGuardCount = {contract['scope']['claims']['executable_unique_guards']}U;
inline constexpr std::size_t UnavailableUniqueGuardCount = {contract['scope']['claims']['unavailable_unique_guards']}U;
inline constexpr std::size_t ExecutableTransitionBindingCount = {contract['scope']['claims']['executable_transition_bindings']}U;
inline constexpr std::uint64_t ProductionSkillMask = {executable_mask}ULL;
inline constexpr SchemaV2::ESkillId ControlSkill = SchemaV2::ESkillId::{_cpp_name(contract['production_skills']['control'])};
inline constexpr std::uint8_t SkillCountSentinel = static_cast<std::uint8_t>(SchemaV2::SkillCount);
inline constexpr std::array<double, {len(contract['utility_profile']['candidate_pair_feature_weights'])}> CandidatePairFeatureWeights{{{{{weights}}}}};

inline constexpr const FInitialProfile* FindInitialProfile(const char* Profile) {{
    for (const auto& Row : InitialProfiles) {{
        const char* A = Row.Profile;
        const char* B = Profile;
        while (*A != '\\0' && *A == *B) {{ ++A; ++B; }}
        if (*A == *B) return &Row;
    }}
    return nullptr;
}}
inline constexpr const FTransitionBinding* FindTransitionBinding(
    const SchemaV2::EGoalType Goal,
    const SchemaV2::EGoalPhase Phase,
    const std::uint8_t Order) {{
    for (const auto& Row : TransitionBindings) {{
        if (Row.Goal == Goal && Row.Phase == Phase && Row.Order == Order) return &Row;
    }}
    return nullptr;
}}
inline constexpr const FPhaseTargetPolicy* FindPhaseTargetPolicy(
    const SchemaV2::EGoalType Goal,
    const SchemaV2::EGoalPhase Phase) {{
    for (const auto& Row : PhaseTargetPolicies) {{
        if (Row.Goal == Goal && Row.Phase == Phase) return &Row;
    }}
    return nullptr;
}}
inline constexpr bool StringsEqual(const char* A, const char* B) {{
    while (*A != '\\0' && *A == *B) {{ ++A; ++B; }}
    return *A == *B;
}}
inline constexpr const FTargetAuthority* FindTargetAuthority(const ETargetAuthorityId Id) {{
    for (const auto& Row : TargetAuthorities) {{
        if (Row.Id == Id) return &Row;
    }}
    return nullptr;
}}
inline constexpr const FEffectAuthority* FindEffectAuthority(const char* Name) {{
    for (const auto& Row : EffectAuthorities) {{
        if (StringsEqual(Row.Name, Name)) return &Row;
    }}
    return nullptr;
}}
inline constexpr bool IsProductionExecutableSkill(const SchemaV2::ESkillId Skill) {{
    const auto Index = static_cast<unsigned>(Skill);
    return Index < SchemaV2::SkillCount && (ProductionSkillMask & (1ULL << Index)) != 0ULL;
}}
inline constexpr bool HasRequirement(const FTransitionBinding& Binding, const ERequirementId Requirement) {{
    const auto Index = static_cast<unsigned>(Requirement);
    return Index < 64U && (Binding.RequirementMask & (1ULL << Index)) != 0ULL;
}}
inline constexpr double GetUtilityBias(const SchemaV2::ESkillId Skill) {{
    switch (Skill) {{
{utility_cases}
    default: return {_cpp_number(contract['utility_profile']['all_other_skill_bias'])};
    }}
}}
static_assert(InitialProfiles.size() == {len(profiles)}U);
static_assert(TransitionBindings.size() == {len(bindings)}U);
static_assert(PhaseTargetPolicies.size() == {len(policies)}U);
static_assert(TargetAuthorities.size() == {len(target_authorities)}U);
static_assert(EffectAuthorities.size() == {len(effect_authorities)}U);
}} // namespace AINativeNPC::GoalGameplayV1
'''


def generate_markdown(
    registry: dict[str, Any],
    skill_registry: dict[str, Any],
    schema: dict[str, Any],
    digest: str,
) -> str:
    del skill_registry, schema
    contract = registry["goal_gameplay_semantics_v1"]
    claims = contract["scope"]["claims"]
    lines = [
        "# General NPC Goal Gameplay Semantics V1",
        "",
        "**Status: BOUNDED PRODUCTION AUTHORITY — PASS**",
        "",
        f"- Approved: `{contract['approved_on']}`",
        f"- Profile: `{contract['scope']['profile_id']}`",
        f"- Goal Registry: `{registry['registry']['version']}`",
        f"- Gameplay semantics: `{contract['version']}`",
        f"- Goal Registry SHA-256: `{digest}`",
        f"- {claims['executable_unique_guards']} executable unique guards",
        f"- {claims['unavailable_unique_guards']} provider-unavailable unique guards",
        f"- {claims['executable_transition_bindings']} executable transition bindings",
        f"- {claims['unavailable_transition_bindings']} unavailable transition bindings",
        f"- {claims['production_executable_skills']} production executable Skills",
        "- Gameplay Goal FSM: **HOLD**",
        "",
        "This authority is bounded to the listed profile and supported Goals. The complete guard catalog, other Goals, full arbitration/save archive, and whole Gameplay Goal FSM remain HOLD.",
        "",
        "## Initial profile",
        "",
        "| Profile | Initial Goal | Initial Phase | Goal Revision | Phase Generation |",
        "|---|---|---|---:|---:|",
    ]
    for row in contract["initial_profiles"]:
        lines.append(
            f"| `{row['profile_id']}` | `{row['initial_goal']}` | `{row['initial_phase']}` | {row['initial_goal_revision']} | {row['initial_phase_generation']} |"
        )
    lines.extend(["", "## Target authorities", ""])
    lines.extend([
        "| Authority | Kind | Owner | Lifetime | Stable ID policy | Capture source | Generation | Initial revision | Mutable | Stored in Knowledge | Provenance only | Candidate usable | Actor transform lookup | Source TTL expiry policy |",
        "|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|",
    ])
    for row in contract["target_authorities"]:
        lines.append(
            f"| `{row['id']}` | `{row['target_kind']}` | `{row['owner']}` | `{row['lifetime']}` | "
            f"`{row['stable_id_policy']}` | `{row['capture_source']}` | {row['generation']} | "
            f"{row['initial_revision']} | `{str(row['mutable']).lower()}` | "
            f"`{str(row['stored_in_knowledge']).lower()}` | `{str(row['provenance_only']).lower()}` | "
            f"`{str(row['candidate_usable']).lower()}` | `{str(row['actor_transform_lookup']).lower()}` | "
            f"`{row['source_ttl_expiry_policy']}` |"
        )
    lines.extend(["", "## Production Skills", ""])
    lines.extend(f"- `{name}`" for name in contract["production_skills"]["executable"])
    lines.extend(["", f"Control candidate: `{contract['production_skills']['control']}`", "", "## Phase Target Policies", ""])
    lines.extend(["| Goal | Phase | Policy | Target authority |", "|---|---|---|---|"])
    for row in contract["phase_target_policies"]:
        lines.append(f"| `{row['goal']}` | `{row['phase']}` | `{row['policy']}` | `{row['target_authority'] or 'none'}` |")
    lines.extend(["", "## Guard authorities", "", "| Guard | Availability | Bindings |", "|---|---|---:|"])
    for row in contract["guard_authorities"]:
        lines.append(f"| `{row['guard']}` | `{row['availability']}` | {len(row['bindings'])} |")
    lines.extend(["", "## Utility", "", f"Profile: `{contract['utility_profile']['profile_id']}`", "", "| Skill | Bias |", "|---|---:|"])
    for name, value in contract["utility_profile"]["skill_biases"].items():
        lines.append(f"| `{name}` | {_cpp_number(value)} |")
    lines.append(f"| all other Skills | {_cpp_number(contract['utility_profile']['all_other_skill_bias'])} |")
    lines.extend([
        "", "## Effects", "",
        "| Effect | Apply policy | Pump result | Transaction policy | Failure before interrupt | Interrupt failure | Failure after interrupt | Post-commit Skill start failure | Callback-free atomic steps | Preserve | Revision without target change | Revision with target change |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in contract["effects"]:
        callback_steps = ", ".join(row["callback_free_atomic_steps"]) or "none"
        preserve = ", ".join(row["preserve"]) or "none"
        lines.append(
            f"| `{row['name']}` | `{row['apply_effect_policy']}` | `{row['pump_result']}` | "
            f"`{row['transaction_policy']}` | `{row['failure_before_interrupt']}` | "
            f"`{row['interrupt_failure']}` | `{row['failure_after_interrupt']}` | "
            f"`{row['post_commit_skill_start_failure']}` | `{callback_steps}` | `{preserve}` | "
            f"`{row['revision_without_target_change']}` | `{row['revision_with_target_change']}` |"
        )
    lines.extend(["", "## Typed event fields", "", "| Field | Type | Required sources | Canonical default |", "|---|---|---|---|"])
    for row in contract["typed_event_fact"]["fields"]:
        sources = ", ".join(row["required_for_sources"]) or "conditional"
        lines.append(f"| `{row['name']}` | `{row['type']}` | {sources} | `{row['canonical_default']}` |")
    lines.append("")
    return "\n".join(lines)


def _replace_exact(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise RuntimeError(f"consumer pattern missing: {path}")
    path.write_text(updated, encoding="utf-8")


def _doc_status_block(registry: dict[str, Any], digest: str) -> str:
    contract = registry["goal_gameplay_semantics_v1"]
    claims = contract["scope"]["claims"]
    return "\n".join(
        [
            DOC_BEGIN,
            "### Bounded Goal gameplay authority status",
            "",
            f"- Goal Registry: `{registry['registry']['version']}` / SHA-256 `{digest}`",
            f"- `{contract['scope']['profile_id']}` bounded semantics authority: **PASS**",
            f"- Authority scope: {claims['executable_unique_guards']} executable unique guards, {claims['unavailable_unique_guards']} provider-unavailable unique guards, {claims['executable_transition_bindings']} executable transition bindings, {claims['effects']} staged effects, {claims['production_executable_skills']} production executable Skills",
            "- Gameplay Goal FSM: **HOLD** — complete guard catalog, other Goals, full Utility/Commit/Skill-result progression, arbitration/save archive, and product release are not claimed by this bounded authority PASS.",
            DOC_END,
        ]
    )


def _sync_doc(path: Path, registry: dict[str, Any], digest: str) -> None:
    text = path.read_text(encoding="utf-8")
    block = _doc_status_block(registry, digest)
    marker = re.compile(re.escape(DOC_BEGIN) + r".*?" + re.escape(DOC_END), re.DOTALL)
    if marker.search(text):
        text = marker.sub(block, text)
    else:
        separator = "\n---\n"
        index = text.find(separator)
        if index < 0:
            raise RuntimeError(f"document insertion point missing: {path}")
        text = text[:index] + "\n\n" + block + "\n" + text[index:]
    version = registry["registry"]["version"]
    text = re.sub(r"(?<=Goal Registry `)\d+\.\d+\.\d+(?=`)", version, text)
    text = re.sub(r"(?<=Goal Registry )\d+\.\d+\.\d+", version, text)
    text = re.sub(r'(?<="goal_registry_version": ")\d+\.\d+\.\d+(?=")', version, text)
    text = re.sub(r"(?<=Registry             )\d+\.\d+\.\d+", version, text)
    text = re.sub(r"(?<=`goal_registry_version` \| `)\d+\.\d+\.\d+(?=`)", version, text)
    text = re.sub(r"(?<=Goal Registry SHA-256: `)[0-9a-f]{64}(?=`)", digest, text)
    path.write_text(text, encoding="utf-8")


def sync_consumers(root: Path, registry: dict[str, Any], digest: str) -> None:
    version = registry["registry"]["version"]
    _replace_exact(
        root / "generated/python/ai_native_npc_contracts_generated.py",
        r"GOAL_REGISTRY_SHA256 = '[0-9a-f]{64}'",
        f"GOAL_REGISTRY_SHA256 = '{digest}'",
    )
    _replace_exact(
        root / "generated/python/ai_native_npc_contracts_generated.py",
        r"GOAL_REGISTRY_VERSION = '\d+\.\d+\.\d+'",
        f"GOAL_REGISTRY_VERSION = '{version}'",
    )
    _replace_exact(
        root / "generated/cpp/AINativeNPCContracts.generated.h",
        r'inline constexpr const char\* GoalRegistrySha256 = "[0-9a-f]{64}";',
        f'inline constexpr const char* GoalRegistrySha256 = "{digest}";',
    )
    _replace_exact(
        root / "generated/cpp/AINativeNPCContracts.generated.h",
        r'inline constexpr const char\* GoalRegistryVersion = "\d+\.\d+\.\d+";',
        f'inline constexpr const char* GoalRegistryVersion = "{version}";',
    )
    validator_path = root / "tools/validate_anpc_capture_v2.py"
    _replace_exact(
        validator_path,
        r'GOAL_REGISTRY_SHA256 = "[0-9a-f]{64}"',
        f'GOAL_REGISTRY_SHA256 = "{digest}"',
    )
    validator_text = validator_path.read_text(encoding="utf-8")
    if "GOAL_REGISTRY_VERSION =" in validator_text:
        validator_text = re.sub(
            r'GOAL_REGISTRY_VERSION = "\d+\.\d+\.\d+"',
            f'GOAL_REGISTRY_VERSION = "{version}"',
            validator_text,
        )
    else:
        validator_text = validator_text.replace(
            f'GOAL_REGISTRY_SHA256 = "{digest}"',
            f'GOAL_REGISTRY_SHA256 = "{digest}"\nGOAL_REGISTRY_VERSION = "{version}"',
            1,
        )
    validator_path.write_text(validator_text, encoding="utf-8")
    for relative in (
        "docs/current/contract-appendices.md",
        "docs/current/implementation-plan.md",
        "docs/current/technical-requirements.md",
        "docs/current/unreal-implementation-plan.md",
    ):
        _sync_doc(root / relative, registry, digest)


def expected_outputs(
    root: Path,
    registry: dict[str, Any],
    skill_registry: dict[str, Any],
    schema: dict[str, Any],
) -> dict[Path, str]:
    registry_path = root / "contracts/current/goal_registry_v1.yaml"
    digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    return {
        root / "generated/python/ai_native_npc_goal_gameplay_semantics_generated.py": generate_python(registry, skill_registry, schema, digest),
        root / "generated/cpp/AINativeNPCGoalGameplaySemantics.generated.h": generate_cpp(registry, skill_registry, schema, digest),
        root / "generated/docs/goal_gameplay_semantics_v1.md": generate_markdown(registry, skill_registry, schema, digest),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "contracts/current/goal_registry_v1.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    skill_registry = yaml.safe_load((root / "contracts/current/skill_registry_v1.yaml").read_text(encoding="utf-8"))
    schema = yaml.safe_load((root / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))
    errors = validate_registry(registry, skill_registry, schema)
    if errors:
        raise SystemExit("Contract validation failed:\n- " + "\n- ".join(errors))
    outputs = expected_outputs(root, registry, skill_registry, schema)
    digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    version = registry["registry"]["version"]
    consumers = (
        root / "generated/python/ai_native_npc_contracts_generated.py",
        root / "generated/cpp/AINativeNPCContracts.generated.h",
        root / "tools/validate_anpc_capture_v2.py",
        root / "docs/current/contract-appendices.md",
        root / "docs/current/implementation-plan.md",
        root / "docs/current/technical-requirements.md",
        root / "docs/current/unreal-implementation-plan.md",
    )
    if args.check:
        stale = [
            str(path.relative_to(root))
            for path, text in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        stale.extend(
            str(path.relative_to(root))
            for path in consumers
            if digest not in path.read_text(encoding="utf-8") or version not in path.read_text(encoding="utf-8")
        )
        status_block = _doc_status_block(registry, digest)
        for path in consumers[3:]:
            if status_block not in path.read_text(encoding="utf-8"):
                stale.append(str(path.relative_to(root)))
        if stale:
            raise SystemExit("Generated outputs or Goal consumers are stale:\n- " + "\n- ".join(sorted(set(stale))))
        print(json.dumps({"goal_registry_sha256": digest, "outputs": len(outputs), "status": "pass", "version": version}, sort_keys=True))
        return
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    sync_consumers(root, registry, digest)
    print(json.dumps({"goal_registry_sha256": digest, "outputs": len(outputs), "status": "generated", "version": version}, sort_keys=True))


if __name__ == "__main__":
    main()
