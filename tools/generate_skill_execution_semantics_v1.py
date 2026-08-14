#!/usr/bin/env python3
"""Validate and deterministically generate General NPC Skill execution semantics V1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import yaml


EXECUTION_SKILL_NAMES = ("TurnTo", "Approach", "Investigate", "SearchArea")
CPP_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _require_keys(value: Any, keys: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict) or set(value) != keys:
        errors.append(f"{label} structure mismatch")
        return False
    return True


def _validate_intensity(common: dict[str, Any], errors: list[str]) -> None:
    multiplier = common.get("intensity_speed_multiplier")
    keys = {"formula", "base", "scale", "input_min", "input_max", "output_min", "output_max"}
    if not _require_keys(multiplier, keys, "intensity multiplier contract", errors):
        return
    assert isinstance(multiplier, dict)
    numeric = [multiplier[key] for key in ("base", "scale", "input_min", "input_max", "output_min", "output_max")]
    if multiplier["formula"] != "base_plus_scale_times_intensity" or not all(_finite_number(value) for value in numeric):
        errors.append("intensity multiplier contract mismatch")
        return
    base, scale, input_min, input_max, output_min, output_max = map(float, numeric)
    if input_min > input_max or scale < 0.0:
        errors.append("intensity multiplier contract mismatch")
        return
    calculated_min = base + scale * input_min
    calculated_max = base + scale * input_max
    if not math.isclose(calculated_min, output_min, rel_tol=0.0, abs_tol=1e-12) or not math.isclose(
        calculated_max, output_max, rel_tol=0.0, abs_tol=1e-12
    ):
        errors.append("intensity multiplier contract mismatch")


def _validate_navigation(common: dict[str, Any], errors: list[str]) -> None:
    navigation = common.get("navigation")
    keys = {
        "path_mode",
        "allow_partial_path",
        "projection_horizontal_cm",
        "projection_vertical_cm",
        "include_agent_radius_in_acceptance",
        "include_goal_radius_in_acceptance",
    }
    if not _require_keys(navigation, keys, "navigation contract", errors):
        return
    assert isinstance(navigation, dict)
    if (
        navigation["path_mode"] != "complete_path_only"
        or navigation["allow_partial_path"] is not False
        or navigation["include_agent_radius_in_acceptance"] is not False
        or navigation["include_goal_radius_in_acceptance"] is not False
        or not _finite_number(navigation["projection_horizontal_cm"])
        or not _finite_number(navigation["projection_vertical_cm"])
        or float(navigation["projection_horizontal_cm"]) <= 0.0
        or float(navigation["projection_vertical_cm"]) <= 0.0
    ):
        errors.append("navigation contract mismatch")


def _validate_search_offsets(skill: dict[str, Any], errors: list[str]) -> None:
    offsets = skill.get("normalized_offsets")
    valid = False
    seen: set[tuple[float, float]] = set()
    if isinstance(offsets, list) and len(offsets) == 9:
        valid = True
        for index, offset in enumerate(offsets):
            if not isinstance(offset, list) or len(offset) != 2 or not all(_finite_number(value) for value in offset):
                valid = False
                break
            x, y = map(float, offset)
            key = (x, y)
            radius = math.hypot(x, y)
            if key in seen or radius > 1.0 + 1e-12 or (index == 0 and key != (0.0, 0.0)):
                valid = False
                break
            seen.add(key)
    if not valid:
        errors.append("SearchArea normalized_offsets mismatch")


def validate_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract = registry.get("execution_semantics_v1")
    if not isinstance(contract, dict):
        return ["execution_semantics_v1 missing"]
    if contract.get("status") != "approved_production_authority":
        errors.append("execution semantics status mismatch")
    if not isinstance(contract.get("approved_on"), str):
        errors.append("execution semantics approval date mismatch")

    common = contract.get("common")
    common_keys = {
        "authority",
        "target_position_policy",
        "evaluation_interval_seconds",
        "intensity_speed_multiplier",
        "same_time_resolution",
        "new_perception_policy",
        "decision_record_v2_layout",
        "tensor_contract",
        "navigation",
    }
    if _require_keys(common, common_keys, "common execution semantics", errors):
        assert isinstance(common, dict)
        if (
            common["authority"] != "server_game_thread"
            or common["target_position_policy"] != "recapture_at_execution_start_then_freeze"
            or not _finite_number(common["evaluation_interval_seconds"])
            or float(common["evaluation_interval_seconds"]) <= 0.0
            or common["same_time_resolution"] != "success_before_timeout"
            or common["new_perception_policy"] != "knowledge_only_until_next_selection"
            or common["decision_record_v2_layout"] != "unchanged"
            or common["tensor_contract"] != "unchanged"
        ):
            errors.append("common execution semantics mismatch")
        _validate_intensity(common, errors)
        _validate_navigation(common, errors)

    failures = contract.get("local_failure_reasons")
    if (
        not isinstance(failures, list)
        or not failures
        or len(set(failures)) != len(failures)
        or not all(isinstance(reason, str) and CPP_IDENTIFIER.fullmatch(reason) for reason in failures)
    ):
        errors.append("local failure reasons mismatch")

    execution_skills = contract.get("skills")
    if not isinstance(execution_skills, dict) or tuple(execution_skills) != EXECUTION_SKILL_NAMES:
        errors.append("execution skill set mismatch")
        execution_skills = execution_skills if isinstance(execution_skills, dict) else {}

    rows = {row.get("name"): row for row in registry.get("skills", []) if isinstance(row, dict)}
    known_target_kinds = set(registry.get("target_commit_policies", {}))
    seen_ids: set[int] = set()
    for name in EXECUTION_SKILL_NAMES:
        skill = execution_skills.get(name)
        row = rows.get(name)
        if not isinstance(skill, dict) or not isinstance(row, dict):
            errors.append(f"{name} execution semantics mismatch")
            continue
        skill_id = skill.get("skill_id")
        if not isinstance(skill_id, int) or isinstance(skill_id, bool) or skill_id < 0 or row.get("id") != skill_id or skill_id in seen_ids:
            errors.append(f"{name} skill_id mismatch")
        else:
            seen_ids.add(skill_id)
        parameters = row.get("parameters")
        valid_parameters = False
        if isinstance(parameters, list) and len(parameters) == 4:
            valid_parameters = True
            for slot, parameter in enumerate(parameters):
                if not isinstance(parameter, dict) or parameter.get("slot") != slot:
                    valid_parameters = False
                    break
                values = (parameter.get("min"), parameter.get("max"), parameter.get("default"))
                if not all(_finite_number(value) for value in values):
                    valid_parameters = False
                    break
                minimum = float(parameter["min"])
                maximum = float(parameter["max"])
                default = float(parameter["default"])
                if minimum > default or default > maximum:
                    valid_parameters = False
                    break
        if not valid_parameters:
            errors.append(f"{name} parameter range/default mismatch")
        allowed = row.get("allowed_target_kinds")
        if (
            not isinstance(allowed, list)
            or not allowed
            or len(set(allowed)) != len(allowed)
            or not all(isinstance(kind, str) and kind in known_target_kinds and CPP_IDENTIFIER.fullmatch(kind) for kind in allowed)
        ):
            errors.append(f"{name} allowed_target_kinds mismatch")

    if isinstance(execution_skills.get("SearchArea"), dict):
        _validate_search_offsets(execution_skills["SearchArea"], errors)
    return errors


def _py_repr(value: Any) -> str:
    return repr(value)


def _cpp_number(value: Any) -> str:
    if not _finite_number(value):
        raise ValueError(f"non-finite C++ number: {value!r}")
    return format(float(value), ".17g")


def generate_python(registry: dict[str, Any], digest: str) -> str:
    contract = registry["execution_semantics_v1"]
    common = contract["common"]
    multiplier = common["intensity_speed_multiplier"]
    navigation = common["navigation"]
    by_id = {spec["skill_id"]: spec for spec in contract["skills"].values()}
    allowed_by_id = {
        row["id"]: tuple(row["allowed_target_kinds"])
        for row in registry["skills"]
        if row.get("name") in EXECUTION_SKILL_NAMES
    }
    return f'''"""AUTO-GENERATED. DO NOT EDIT. Approved General NPC Skill execution semantics V1."""
from __future__ import annotations
import math

SKILL_REGISTRY_SHA256 = {digest!r}
EVALUATION_INTERVAL_SECONDS = {_cpp_number(common["evaluation_interval_seconds"])}
INTENSITY_SPEED_BASE = {_cpp_number(multiplier["base"])}
INTENSITY_SPEED_SCALE = {_cpp_number(multiplier["scale"])}
NAV_PROJECTION_HORIZONTAL_CM = {_cpp_number(navigation["projection_horizontal_cm"])}
NAV_PROJECTION_VERTICAL_CM = {_cpp_number(navigation["projection_vertical_cm"])}
SKILL_EXECUTION_SEMANTICS = {_py_repr(by_id)}
ALLOWED_TARGET_KINDS = {_py_repr(allowed_by_id)}


def effective_speed(speed: float, intensity: float) -> float:
    if not math.isfinite(speed) or not math.isfinite(intensity):
        raise ValueError("speed and intensity must be finite")
    if not 0.0 <= intensity <= 1.0:
        raise ValueError("intensity must be in [0, 1]")
    return speed * (INTENSITY_SPEED_BASE + INTENSITY_SPEED_SCALE * intensity)
'''


def generate_cpp(registry: dict[str, Any], digest: str) -> str:
    contract = registry["execution_semantics_v1"]
    common = contract["common"]
    multiplier = common["intensity_speed_multiplier"]
    navigation = common["navigation"]
    skills = contract["skills"]
    rows = {row["name"]: row for row in registry["skills"]}
    offsets = skills["SearchArea"]["normalized_offsets"]
    offset_rows = ",\n".join(f"    FSearchOffset{{{_cpp_number(x)}, {_cpp_number(y)}}}" for x, y in offsets)
    cases: list[str] = []
    for name in EXECUTION_SKILL_NAMES:
        comparisons = "\n            || ".join(
            f"Kind == SchemaV2::ETargetKind::{kind}" for kind in rows[name]["allowed_target_kinds"]
        )
        cases.append(f"    case SchemaV2::ESkillId::{name}:\n        return {comparisons};")
    target_cases = "\n".join(cases)
    return f'''// AUTO-GENERATED. DO NOT EDIT.
#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include "AINativeNPCContracts.generated.h"

namespace AINativeNPC::SkillExecutionV1 {{
inline constexpr const char* SkillRegistrySha256 = "{digest}";
inline constexpr double EvaluationIntervalSeconds = {_cpp_number(common["evaluation_interval_seconds"])};
inline constexpr double IntensitySpeedBase = {_cpp_number(multiplier["base"])};
inline constexpr double IntensitySpeedScale = {_cpp_number(multiplier["scale"])};
inline constexpr double NavProjectionHorizontalCm = {_cpp_number(navigation["projection_horizontal_cm"])};
inline constexpr double NavProjectionVerticalCm = {_cpp_number(navigation["projection_vertical_cm"])};
inline constexpr double TurnPlanarCoincidentDistanceCm = {_cpp_number(skills["TurnTo"]["planar_coincident_distance_cm"])};
inline constexpr double TurnFacingToleranceDegrees = {_cpp_number(skills["TurnTo"]["facing_tolerance_degrees"])};
inline constexpr double TurnSuccessStableSeconds = {_cpp_number(skills["TurnTo"]["success_stable_seconds"])};
inline constexpr double InvestigateFacingToleranceDegrees = {_cpp_number(skills["Investigate"]["facing_tolerance_degrees"])};
inline constexpr double InvestigateSuccessStableSeconds = {_cpp_number(skills["Investigate"]["success_stable_seconds"])};
inline constexpr double InvestigateBaseTurnSpeedDegreesPerSecond = {_cpp_number(skills["Investigate"]["base_turn_speed_degrees_per_second"])};
inline constexpr double SearchPointAcceptanceRadiusCm = {_cpp_number(skills["SearchArea"]["point_acceptance_radius_cm"])};
inline constexpr std::size_t SearchPointCount = {len(offsets)};
struct FSearchOffset {{ double X; double Y; }};
inline constexpr std::array<FSearchOffset, SearchPointCount> SearchNormalizedOffsets{{{{
{offset_rows}
}}}};
inline constexpr bool IsTargetKindAllowed(
    const SchemaV2::ESkillId Skill,
    const SchemaV2::ETargetKind Kind)
{{
    switch (Skill)
    {{
{target_cases}
    default:
        return false;
    }}
}}
inline constexpr double EffectiveSpeed(double Speed, double Intensity) {{
    return Speed * (IntensitySpeedBase + IntensitySpeedScale * std::clamp(Intensity, 0.0, 1.0));
}}
static_assert(SearchNormalizedOffsets.size() == SearchPointCount);
}} // namespace AINativeNPC::SkillExecutionV1
'''


def generate_markdown(registry: dict[str, Any], digest: str) -> str:
    contract = registry["execution_semantics_v1"]
    skills = contract["skills"]
    lines = [
        "# 🚨 분실한 iPad입니다 — 습득하신 분은 010-5184-5134로 연락주세요",
        "",
        "# General NPC Skill Execution Semantics V1",
        "",
        "**Status: PRODUCTION AUTHORITY**",
        "",
        f"- Approved: `{contract['approved_on']}`",
        f"- Skill Registry SHA-256: `{digest}`",
        "- Runtime authority: server GameThread",
        "- Target position: execution-start recapture, then frozen",
        "- DecisionRecord v2 layout: unchanged",
        "- 10-Tensor contract: unchanged",
        "",
        "## Common",
        "",
        "`effective_speed = speed × (base + scale × intensity)`; base and scale come from the Registry.",
        "",
        "Success wins when success and timeout are observed at the same authoritative server time.",
        "New perception updates Knowledge and affects the next selection. It does not reinterpret the running Skill.",
        "",
        "## Exact execution values",
        "",
        "| Skill | ID | Success | Stable | Fixed values |",
        "|---|---:|---|---:|---|",
        f"| TurnTo | {skills['TurnTo']['skill_id']} | yaw error ≤ {skills['TurnTo']['facing_tolerance_degrees']}° | {skills['TurnTo']['success_stable_seconds']} s | coincident ≤ {skills['TurnTo']['planar_coincident_distance_cm']} cm |",
        f"| Approach | {skills['Approach']['skill_id']} | planar distance ≤ preferred_distance | 0 s | complete path only |",
        f"| Investigate | {skills['Investigate']['skill_id']} | distance and yaw error ≤ {skills['Investigate']['facing_tolerance_degrees']}° | {skills['Investigate']['success_stable_seconds']} s | base turn {skills['Investigate']['base_turn_speed_degrees_per_second']}°/s |",
        f"| SearchArea | {skills['SearchArea']['skill_id']} | all valid points, or deadline after ≥1 visit | duration budget | {len(skills['SearchArea']['normalized_offsets'])} fixed world-axis points; {skills['SearchArea']['point_acceptance_radius_cm']} cm acceptance |",
        "",
        "## Deterministic SearchArea offsets",
        "",
        "| Order | X × radius | Y × radius |",
        "|---:|---:|---:|",
    ]
    lines.extend(
        f"| {index} | {_cpp_number(x)} | {_cpp_number(y)} |"
        for index, (x, y) in enumerate(skills["SearchArea"]["normalized_offsets"])
    )
    lines.extend(["", "## Local failure reasons", ""])
    lines.extend(f"- `{reason}`" for reason in contract["local_failure_reasons"])
    lines.append("")
    return "\n".join(lines)


def replace_exact_pattern(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise RuntimeError(f"digest consumer pattern missing: {path}")
    path.write_text(updated, encoding="utf-8")


def sync_digest_consumers(root: Path, digest: str) -> None:
    replace_exact_pattern(
        root / "generated/cpp/AINativeNPCContracts.generated.h",
        r'inline constexpr const char\* SkillRegistrySha256 = "[0-9a-f]{64}";',
        f'inline constexpr const char* SkillRegistrySha256 = "{digest}";',
    )
    replace_exact_pattern(
        root / "generated/python/ai_native_npc_contracts_generated.py",
        r"SKILL_REGISTRY_SHA256 = '[0-9a-f]{64}'",
        f"SKILL_REGISTRY_SHA256 = '{digest}'",
    )
    replace_exact_pattern(
        root / "tools/validate_anpc_capture_v2.py",
        r'SKILL_REGISTRY_SHA256 = "[0-9a-f]{64}"',
        f'SKILL_REGISTRY_SHA256 = "{digest}"',
    )
    for relative in ["docs/current/contract-appendices.md", "docs/current/unreal-implementation-plan.md"]:
        replace_exact_pattern(
            root / relative,
            r"(?<=Skill Registry SHA-256: `)[0-9a-f]{64}(?=`)",
            digest,
        )


def expected_outputs(root: Path, registry: dict[str, Any]) -> dict[Path, str]:
    registry_path = root / "contracts/current/skill_registry_v1.yaml"
    digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    return {
        root / "generated/python/ai_native_npc_skill_execution_semantics_generated.py": generate_python(registry, digest),
        root / "generated/cpp/AINativeNPCSkillExecutionSemantics.generated.h": generate_cpp(registry, digest),
        root / "generated/docs/skill_execution_semantics_v1.md": generate_markdown(registry, digest),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "contracts/current/skill_registry_v1.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    errors = validate_registry(registry)
    if errors:
        raise SystemExit("Contract validation failed:\n- " + "\n- ".join(errors))
    outputs = expected_outputs(root, registry)
    digest = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    if args.check:
        stale = [
            str(path.relative_to(root))
            for path, text in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        consumers = [
            root / "generated/cpp/AINativeNPCContracts.generated.h",
            root / "generated/python/ai_native_npc_contracts_generated.py",
            root / "tools/validate_anpc_capture_v2.py",
            root / "docs/current/contract-appendices.md",
            root / "docs/current/unreal-implementation-plan.md",
        ]
        stale.extend(str(path.relative_to(root)) for path in consumers if digest not in path.read_text(encoding="utf-8"))
        if stale:
            raise SystemExit("Generated outputs or digest consumers are stale:\n- " + "\n- ".join(stale))
        print(json.dumps({"status": "pass", "skill_registry_sha256": digest, "outputs": len(outputs)}, sort_keys=True))
        return
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    sync_digest_consumers(root, digest)
    print(json.dumps({"status": "generated", "skill_registry_sha256": digest, "outputs": len(outputs)}, sort_keys=True))


if __name__ == "__main__":
    main()
