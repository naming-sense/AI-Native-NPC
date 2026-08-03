#!/usr/bin/env python3
"""Shared contract loading, semantic validation, serialization, and code generation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math
import re
import struct

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required. Install with: python -m pip install -r requirements.txt"
    ) from exc

TOOL_VERSION = "0.4.6"
ALLOWED_DTYPES = {"float32", "int64", "bool"}
NORMALIZER_TYPES = {
    "boolean", "constant", "clamp", "divide_clamp", "trigonometric",
    "log1p_ratio", "sentinel_divide_clamp",
}


@dataclass(frozen=True)
class ContractPaths:
    root: Path
    schema: Path
    skill_registry: Path
    goal_registry: Path
    boss_pattern_contract: Path
    test_taxonomy: Path


def default_paths(root: Path) -> ContractPaths:
    current = root / "contracts/current"
    return ContractPaths(
        root=root,
        schema=current / "ai_native_npc_schema_v2_0.yaml",
        skill_registry=current / "skill_registry_v1.yaml",
        goal_registry=current / "goal_registry_v1.yaml",
        boss_pattern_contract=current / "boss_pattern_contract_v1.yaml",
        test_taxonomy=current / "test_taxonomy_v1.yaml",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be mapping: {path}")
    return data


def load_contracts(paths: ContractPaths) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return load_yaml(paths.schema), load_yaml(paths.skill_registry), load_yaml(paths.goal_registry)


def load_boss_pattern_contract(paths: ContractPaths) -> dict[str, Any]:
    return load_yaml(paths.boss_pattern_contract)


def _walk_value_ascii(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "value_ascii" and isinstance(child, str) and child:
                yield child
            yield from _walk_value_ascii(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_value_ascii(child)


def collect_hash_magic_tokens(root: Path) -> set[str]:
    """Collect every value_ascii token from current and archived YAML/JSON contracts."""
    tokens: set[str] = set()
    for base in [root / "contracts/current", root / "contracts/archive"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml", ".json"}:
                continue
            try:
                data = load_yaml(path)
            except Exception:
                # A malformed archive must not silently hide a token.
                for match in re.finditer(r"(?im)^\s*value_ascii\s*:\s*[\"']?([A-Za-z0-9_]{4,64})", path.read_text(encoding="utf-8", errors="ignore")):
                    tokens.add(match.group(1))
                continue
            tokens.update(_walk_value_ascii(data))
    return tokens


def critical_suite_metrics(taxonomy: dict[str, Any]) -> dict[str, Any]:
    critical = taxonomy.get("critical_suite", {})
    ood = taxonomy.get("ood_suite", {})
    family_count = int(critical["required_family_count"])
    cases_per_family = int(critical["minimum_cases_per_family"])
    return {
        "contract_id": str(critical.get("contract_id", "critical_suite_v1")),
        "required_family_count": family_count,
        "minimum_cases_per_family": cases_per_family,
        "critical_minimum_sequence_count": family_count * cases_per_family,
        "critical_family_names": [str(row["name"]) for row in critical.get("families", [])],
        "ood_contract_id": str(ood.get("contract_id", "ood_suite_v1")),
        "ood_required_family_count": int(ood["required_family_count"]),
        "ood_family_names": [str(row["name"]) for row in ood.get("families", [])],
    }


def validate_generated_block(text: str, begin: str, end: str, expected: str, label: str) -> list[str]:
    if text.count(begin) != 1 or text.count(end) != 1:
        return [f"{label}: generated marker count mismatch"]
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    if text[start:finish] != expected:
        return [f"{label}: generated block stale or manually changed"]
    return []


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_enum(name: str, values: Any, errors: list[str]) -> None:
    _expect(isinstance(values, list) and values, f"enums.{name} must be non-empty list", errors)
    if not isinstance(values, list):
        return
    ids: list[int] = []
    names: list[str] = []
    for pos, item in enumerate(values):
        if not isinstance(item, dict):
            errors.append(f"enums.{name}[{pos}] must be mapping")
            continue
        _expect(isinstance(item.get("id"), int), f"enums.{name}[{pos}].id must be int", errors)
        _expect(isinstance(item.get("name"), str) and item.get("name"), f"enums.{name}[{pos}].name invalid", errors)
        if isinstance(item.get("id"), int):
            ids.append(item["id"])
        if isinstance(item.get("name"), str):
            names.append(item["name"])
    _expect(len(ids) == len(set(ids)), f"enums.{name} has duplicate id", errors)
    _expect(len(names) == len(set(names)), f"enums.{name} has duplicate name", errors)
    if ids:
        _expect(sorted(ids) == list(range(len(ids))), f"enums.{name} ids must be contiguous 0..N-1", errors)
        _expect(ids == sorted(ids), f"enums.{name} must be ordered by id", errors)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return _is_number(value) and math.isfinite(float(value))


def _numeric_constant(constants: dict[str, Any], name: str, path: str, errors: list[str]) -> float | None:
    if name not in constants:
        errors.append(f"{path} unknown constant {name}")
        return None
    value = constants[name]
    if not _is_finite_number(value):
        errors.append(f"{path} constant {name} must be finite numeric")
        return None
    return float(value)


def _resolve_numeric(spec: dict[str, Any], key: str, constants: dict[str, Any], path: str, errors: list[str]) -> float | None:
    direct = spec.get(key)
    ref = spec.get(f"{key}_ref")
    if direct is not None and ref is not None:
        errors.append(f"{path} cannot contain both {key} and {key}_ref")
        return None
    if direct is not None:
        if not _is_finite_number(direct):
            errors.append(f"{path}.{key} must be finite numeric")
            return None
        return float(direct)
    if ref is not None:
        if not isinstance(ref, str) or not ref:
            errors.append(f"{path}.{key}_ref must be non-empty string")
            return None
        return _numeric_constant(constants, ref, f"{path}.{key}_ref", errors)
    errors.append(f"{path} missing {key} or {key}_ref")
    return None


def _range_pair(value: Any, path: str, errors: list[str]) -> tuple[float, float] | None:
    if not isinstance(value, list) or len(value) != 2 or not all(_is_finite_number(x) for x in value):
        errors.append(f"{path} must be [finite_min, finite_max]")
        return None
    lo, hi = float(value[0]), float(value[1])
    if lo > hi:
        errors.append(f"{path} reversed: min {lo} > max {hi}")
        return None
    return lo, hi


def _range_contains(outer: tuple[float, float], inner: tuple[float, float], tolerance: float = 1e-12) -> bool:
    return outer[0] <= inner[0] + tolerance and outer[1] + tolerance >= inner[1]


def _validate_normalizer(
    spec: Any,
    constants: dict[str, Any],
    path: str,
    errors: list[str],
    valid_range: tuple[float, float] | None,
    missing: Any,
) -> None:
    if not isinstance(spec, dict):
        errors.append(f"{path}.normalizer must be mapping")
        return
    typ = spec.get("type")
    _expect(typ in NORMALIZER_TYPES, f"{path}.normalizer.type unsupported: {typ}", errors)
    if typ not in NORMALIZER_TYPES:
        return

    output_range: tuple[float, float] | None = None
    sentinel_name: str | None = None
    sentinel_value: float | None = None

    if typ == "constant":
        value = spec.get("value")
        _expect(_is_finite_number(value), f"{path}.normalizer.value must be finite numeric", errors)
        if _is_finite_number(value):
            output_range = (float(value), float(value))
    elif typ == "boolean":
        extra = set(spec) - {"type"}
        _expect(not extra, f"{path}.normalizer boolean has unsupported keys {sorted(extra)}", errors)
        output_range = (0.0, 1.0)
    elif typ == "clamp":
        bounds = _range_pair([spec.get("min"), spec.get("max")], f"{path}.normalizer clamp bounds", errors)
        output_range = bounds
    elif typ == "divide_clamp":
        divisor = _resolve_numeric(spec, "divisor", constants, f"{path}.normalizer", errors)
        if divisor is not None:
            _expect(divisor > 0.0, f"{path}.normalizer divisor must be > 0, got {divisor}", errors)
        output_range = _range_pair([spec.get("min"), spec.get("max")], f"{path}.normalizer divide_clamp bounds", errors)
    elif typ == "trigonometric":
        _expect(spec.get("function") in {"sin", "cos"}, f"{path}.normalizer trig function invalid", errors)
        _expect(spec.get("input_unit") == "radian", f"{path}.normalizer trig input_unit must be radian", errors)
        output_range = (-1.0, 1.0)
    elif typ == "log1p_ratio":
        input_min = spec.get("input_min")
        _expect(_is_finite_number(input_min), f"{path}.normalizer input_min must be finite", errors)
        input_max = _resolve_numeric(spec, "input_max", constants, f"{path}.normalizer", errors)
        denominator = _resolve_numeric(spec, "denominator", constants, f"{path}.normalizer", errors)
        if _is_finite_number(input_min):
            input_min_f = float(input_min)
            _expect(input_min_f > -1.0, f"{path}.normalizer log1p input_min must be > -1", errors)
        else:
            input_min_f = 0.0
        if input_max is not None:
            _expect(input_max >= input_min_f, f"{path}.normalizer input_max must be >= input_min", errors)
            _expect(input_max > -1.0, f"{path}.normalizer input_max must be > -1", errors)
        if denominator is not None:
            _expect(denominator > 0.0, f"{path}.normalizer log1p denominator must be > 0", errors)
        if input_max is not None and denominator is not None and denominator > 0.0 and input_min_f > -1.0:
            den_log = math.log1p(denominator)
            _expect(math.isfinite(den_log) and den_log > 0.0, f"{path}.normalizer log1p denominator produces invalid log", errors)
            if den_log > 0.0:
                output_range = (math.log1p(input_min_f) / den_log, math.log1p(input_max) / den_log)
                if output_range[0] > output_range[1]:
                    output_range = (output_range[1], output_range[0])
    elif typ == "sentinel_divide_clamp":
        divisor = _resolve_numeric(spec, "divisor", constants, f"{path}.normalizer", errors)
        if divisor is not None:
            _expect(divisor > 0.0, f"{path}.normalizer divisor must be > 0, got {divisor}", errors)
        normal_range = _range_pair([spec.get("min"), spec.get("max")], f"{path}.normalizer sentinel bounds", errors)
        sentinel_name_raw = spec.get("sentinel")
        _expect(isinstance(sentinel_name_raw, str) and bool(sentinel_name_raw), f"{path}.normalizer sentinel must be non-empty string", errors)
        sentinel_name = sentinel_name_raw if isinstance(sentinel_name_raw, str) else None
        sentinel_raw = spec.get("sentinel_value")
        _expect(_is_finite_number(sentinel_raw), f"{path}.normalizer sentinel_value must be finite numeric", errors)
        sentinel_value = float(sentinel_raw) if _is_finite_number(sentinel_raw) else None
        if normal_range is not None and sentinel_value is not None:
            output_range = (min(normal_range[0], sentinel_value), max(normal_range[1], sentinel_value))

    if valid_range is not None and output_range is not None:
        _expect(
            _range_contains(valid_range, output_range),
            f"{path}.normalizer output range {output_range} exceeds valid_range {valid_range}",
            errors,
        )

    if not isinstance(missing, dict):
        errors.append(f"{path}.missing contract invalid")
        return
    policy = missing.get("policy")
    if policy == "constant":
        value = missing.get("value")
        _expect(_is_finite_number(value), f"{path}.missing.value must be finite numeric", errors)
        if valid_range is not None and _is_finite_number(value):
            _expect(valid_range[0] <= float(value) <= valid_range[1], f"{path}.missing.value outside valid_range", errors)
        if typ == "constant" and _is_finite_number(value) and _is_finite_number(spec.get("value")):
            _expect(
                math.isclose(float(value), float(spec["value"]), rel_tol=0.0, abs_tol=1e-12),
                f"{path}.constant normalizer value must equal missing constant value",
                errors,
            )
    elif policy == "sentinel":
        _expect(typ == "sentinel_divide_clamp", f"{path}.missing sentinel policy requires sentinel normalizer", errors)
        _expect(missing.get("sentinel") == sentinel_name, f"{path}.missing sentinel name mismatch", errors)
        encoded = missing.get("encoded_value")
        _expect(_is_finite_number(encoded), f"{path}.missing.encoded_value must be finite", errors)
        if _is_finite_number(encoded) and sentinel_value is not None:
            _expect(math.isclose(float(encoded), sentinel_value, rel_tol=0.0, abs_tol=1e-12), f"{path}.missing encoded value != normalizer sentinel_value", errors)
        if valid_range is not None and _is_finite_number(encoded):
            _expect(valid_range[0] <= float(encoded) <= valid_range[1], f"{path}.missing.encoded_value outside valid_range", errors)
    elif policy == "padding_zero":
        value = missing.get("value")
        _expect(_is_finite_number(value) and math.isclose(float(value), 0.0, rel_tol=0.0, abs_tol=0.0), f"{path}.missing padding_zero value must be exactly 0", errors)
        if valid_range is not None:
            _expect(valid_range[0] <= 0.0 <= valid_range[1], f"{path}.padding_zero value outside valid_range", errors)
        required = missing.get("occupied_required_value")
        _expect(_is_finite_number(required), f"{path}.missing occupied_required_value must be finite", errors)
        if valid_range is not None and _is_finite_number(required):
            _expect(valid_range[0] <= float(required) <= valid_range[1], f"{path}.occupied_required_value outside valid_range", errors)
    else:
        errors.append(f"{path}.missing.policy unsupported: {policy}")


def _validate_constraints(
    constraints: Any,
    normalizer: Any,
    valid_range: tuple[float, float] | None,
    missing: Any,
    path: str,
    errors: list[str],
) -> None:
    if constraints is None:
        return
    if not isinstance(constraints, dict):
        errors.append(f"{path}.constraints must be mapping")
        return
    allowed = {"must_equal", "occupied_required_value"}
    extra = set(constraints) - allowed
    _expect(not extra, f"{path}.constraints unsupported keys {sorted(extra)}", errors)

    if "must_equal" in constraints:
        required = constraints.get("must_equal")
        _expect(_is_finite_number(required), f"{path}.constraints.must_equal must be finite", errors)
        if not _is_finite_number(required):
            return
        required_f = float(required)
        _expect(isinstance(normalizer, dict) and normalizer.get("type") == "constant", f"{path}.must_equal requires constant normalizer", errors)
        if isinstance(normalizer, dict) and _is_finite_number(normalizer.get("value")):
            _expect(math.isclose(float(normalizer["value"]), required_f, rel_tol=0.0, abs_tol=1e-12), f"{path}.normalizer constant != constraints.must_equal", errors)
        if valid_range is not None:
            _expect(
                math.isclose(valid_range[0], required_f, rel_tol=0.0, abs_tol=1e-12)
                and math.isclose(valid_range[1], required_f, rel_tol=0.0, abs_tol=1e-12),
                f"{path}.constraints.must_equal requires singleton valid_range [{required_f}, {required_f}]",
                errors,
            )
        _expect(isinstance(missing, dict) and missing.get("policy") == "constant", f"{path}.must_equal requires constant missing policy", errors)
        if isinstance(missing, dict) and _is_finite_number(missing.get("value")):
            _expect(math.isclose(float(missing["value"]), required_f, rel_tol=0.0, abs_tol=1e-12), f"{path}.missing constant != constraints.must_equal", errors)

    if "occupied_required_value" in constraints:
        required = constraints.get("occupied_required_value")
        _expect(_is_finite_number(required), f"{path}.constraints.occupied_required_value must be finite", errors)
        if _is_finite_number(required):
            required_f = float(required)
            if valid_range is not None:
                _expect(valid_range[0] <= required_f <= valid_range[1], f"{path}.constraints.occupied_required_value outside valid_range", errors)
            _expect(isinstance(missing, dict) and missing.get("policy") == "padding_zero", f"{path}.occupied_required_value requires padding_zero missing policy", errors)
            if isinstance(missing, dict) and _is_finite_number(missing.get("occupied_required_value")):
                _expect(
                    math.isclose(float(missing["occupied_required_value"]), required_f, rel_tol=0.0, abs_tol=1e-12),
                    f"{path}.missing occupied_required_value != constraints.occupied_required_value",
                    errors,
                )


def strip_generated_document_block(text: str, documentation_contract: dict[str, Any]) -> str:
    begin = str(documentation_contract.get("marker_begin", ""))
    end = str(documentation_contract.get("marker_end", ""))
    if not begin or not end:
        return text
    start = text.find(begin)
    finish = text.find(end, start + len(begin)) if start >= 0 else -1
    if start < 0 or finish < 0:
        return text
    finish += len(end)
    return text[:start] + text[finish:]


def validate_manual_hash_literal_policy(
    schema: dict[str, Any],
    text: str,
    label: str,
    known_magic_tokens: Iterable[str] | None = None,
    additional_generated_blocks: Iterable[tuple[str, str]] | None = None,
    allow_schema_generated_block: bool = True,
) -> list[str]:
    contract = schema.get("documentation_contract", {})
    if not contract.get("forbid_manual_hash_literal_outside_generated_block"):
        return []

    outside = strip_generated_document_block(text, contract) if allow_schema_generated_block else text
    for begin, end in additional_generated_blocks or []:
        if begin and end:
            start = outside.find(begin)
            finish = outside.find(end, start + len(begin)) if start >= 0 else -1
            if start >= 0 and finish >= 0:
                outside = outside[:start] + outside[finish + len(end):]

    errors: list[str] = []
    tokens = set(known_magic_tokens or _walk_value_ascii(schema))
    for token in sorted(tokens):
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", outside):
            errors.append(f"{label}: known hash magic token {token!r} outside generated Appendix D.3-D.4")

    # Strip formatting quotes/backticks so Markdown, prose, JSON, and inline code share one parser.
    normalized = outside.replace("`", "").replace('"', "").replace("'", "")
    assignment = re.compile(
        r"(?m)(?i:\b(?:candidate\s+|decision\s+)?magic\b)\s*"
        r"(?:(?i:is)\b|[:=])\s*([A-Za-z0-9_]{4,64})"
    )
    for match in assignment.finditer(normalized):
        value = match.group(1)
        errors.append(f"{label}: manual hash magic assignment {value!r} outside generated Appendix D.3-D.4")

    value_ascii = re.compile(r"(?m)(?i:\bvalue_ascii\b)\s*:\s*([A-Za-z0-9_]{4,64})")
    for match in value_ascii.finditer(normalized):
        errors.append(f"{label}: manual hash value_ascii {match.group(1)!r} outside generated Appendix D.3-D.4")
    return sorted(set(errors))

def _validate_field(field: Any, expected_index: int, constants: dict[str, Any], path: str, errors: list[str]) -> None:
    if not isinstance(field, dict):
        errors.append(f"{path}[{expected_index}] must be mapping")
        return
    _expect(field.get("index", field.get("payload_index")) == expected_index, f"{path}[{expected_index}] index mismatch", errors)
    _expect(isinstance(field.get("name"), str) and field["name"], f"{path}[{expected_index}] name invalid", errors)
    _expect(isinstance(field.get("source"), str) and bool(field.get("source")), f"{path}[{expected_index}] source missing", errors)
    _expect(isinstance(field.get("unit"), str) and bool(field.get("unit")), f"{path}[{expected_index}] unit missing", errors)
    valid_range = _range_pair(field.get("valid_range"), f"{path}[{expected_index}].valid_range", errors)
    missing = field.get("missing")
    normalizer = field.get("normalizer")
    field_path = f"{path}[{expected_index}]"
    _validate_normalizer(normalizer, constants, field_path, errors, valid_range, missing)
    _validate_constraints(field.get("constraints"), normalizer, valid_range, missing, field_path, errors)
    _expect("normalization" not in field and "range" not in field, f"{path}[{expected_index}] contains legacy string normalization/range", errors)

def _shape_equals(shape: Any, expected: list[Any]) -> bool:
    return isinstance(shape, list) and shape == expected


def validate_boss_pattern_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = contract.get("contract", {})
    constants = contract.get("constants", {})
    enums = contract.get("enums", {})

    _expect(meta.get("name") == "ai_native_npc_boss_pattern_policy", "boss pattern contract name mismatch", errors)
    _expect(meta.get("version") == "1.0.0", "boss pattern contract version mismatch", errors)
    _expect(meta.get("contract_revision") == "2.0.0-rc5", "boss pattern contract revision mismatch", errors)
    _expect(meta.get("endianness") == "little", "boss pattern endianness must be little", errors)

    required_constants = {
        "max_pattern_slots": 32,
        "pattern_context_feature_count": 32,
        "pattern_feature_count": 24,
        "pattern_pair_feature_count": 16,
        "pattern_parameter_count": 4,
        "max_pattern_duration_s": 30.0,
        "max_pattern_cooldown_s": 120.0,
        "max_tracking_yaw_deg_s": 720.0,
        "max_tracking_speed_cm_s": 1200.0,
        "max_target_distance_cm": 10000.0,
        "max_target_relative_speed_cm_s": 2000.0,
        "max_encounter_elapsed_s": 1800.0,
        "invalid_pattern_id": 65535,
    }
    for name, expected in required_constants.items():
        _expect(constants.get(name) == expected, f"boss pattern constants.{name} expected {expected}, got {constants.get(name)}", errors)

    expected_enums = {
        "selection_boundary": ["PreAttack", "BranchWindow", "RecoveryEnd"],
        "execution_phase": ["ReadyToSelect", "PreAttackTurn", "StartupTelegraph", "Active", "Recovery", "BranchWindow", "Completed", "Interrupted"],
        "interrupt_kind": ["Death", "ActorDestroyed", "AuthorityLost", "Stun", "PostureBreak", "ScriptedPhaseTransition", "ArenaReset"],
        "mask_reason": ["None", "Unoccupied", "WrongBossPhase", "TargetInvalid", "RangeMismatch", "AngleMismatch", "ElevationMismatch", "LineOfSightMissing", "CooldownActive", "ResourceUnavailable", "PredecessorMismatch", "BranchNotAllowed", "ArenaUnsafe", "NavigationUnavailable", "AssetUnavailable", "NotSelectionBoundary", "ReservationConflict", "ExecutorLocked"],
    }
    for name, expected_names in expected_enums.items():
        rows = enums.get(name, [])
        _validate_enum(f"boss_pattern.{name}", rows, errors)
        names = [row.get("name") for row in rows if isinstance(row, dict)]
        _expect(names == expected_names, f"boss pattern enum {name} mismatch", errors)

    activation = contract.get("activation_contract", {})
    _expect(activation.get("parent_skill") == "Attack", "boss pattern parent skill must be Attack", errors)
    _expect(activation.get("required_target_kind") == "Entity", "boss pattern target kind must be Entity", errors)
    _expect(activation.get("selector_invoked_after_parent_attack_commit") is True, "boss pattern selector must run after parent Attack commit", errors)
    _expect(activation.get("selector_invoked_during_locked_execution") is False, "boss pattern selector cannot run during locked execution", errors)
    common = activation.get("common_candidate_layout_unchanged", {})
    _expect(common == {"skill_count": 16, "target_slot_count": 17, "candidate_count": 272}, "boss pattern common candidate layout must remain 16 x 17 = 272", errors)

    slots = contract.get("slot_assignment_contract", {})
    _expect(slots.get("max_occupied_slots_ref") == "max_pattern_slots", "boss pattern slot max reference mismatch", errors)
    _expect(slots.get("minimum_occupied_slots") == 1, "boss pattern slot layout must contain at least one occupied row", errors)
    _expect(slots.get("occupied_order") == "pattern_id_ascending", "boss pattern slots must be ordered by pattern_id", errors)
    _expect(slots.get("padding_pattern_id_ref") == "invalid_pattern_id", "boss pattern padding id reference mismatch", errors)
    _expect(slots.get("layout_validation_before_hash") is True, "boss pattern slot layout must validate before hash", errors)
    _expect(slots.get("row_removal_forbidden") is True and slots.get("invalid_row_policy") == "pattern_mask_false", "boss pattern invalid rows must remain masked", errors)

    expected_tensors = {
        "pattern_context": (["B", 32], "float32", 32),
        "pattern_features": (["B", 32, 24], "float32", 24),
        "pattern_pair_features": (["B", 32, 16], "float32", 16),
        "pattern_ids": (["B", 32], "int64", None),
        "pattern_mask": (["B", 32], "bool", None),
    }
    tensors = contract.get("tensors", {})
    for name, (shape, dtype, field_count) in expected_tensors.items():
        tensor = tensors.get(name, {})
        _expect(_shape_equals(tensor.get("shape"), shape), f"boss pattern tensor {name} shape expected {shape}, got {tensor.get('shape')}", errors)
        _expect(tensor.get("dtype") == dtype, f"boss pattern tensor {name} dtype expected {dtype}", errors)
        if field_count is not None:
            fields = tensor.get("fields", [])
            _expect(len(fields) == field_count, f"boss pattern tensor {name} field count expected {field_count}", errors)
            names: list[Any] = []
            for index, field in enumerate(fields):
                if not isinstance(field, dict):
                    errors.append(f"boss pattern tensor {name} field {index} must be mapping")
                    continue
                _expect(field.get("index") == index, f"boss pattern tensor {name} field index {index} mismatch", errors)
                _expect(isinstance(field.get("name"), str) and bool(field.get("name")), f"boss pattern tensor {name} field {index} name missing", errors)
                _expect(isinstance(field.get("source"), str) and bool(field.get("source")), f"boss pattern tensor {name} field {index} source missing", errors)
                names.append(field.get("name"))
            _expect(len(names) == len(set(names)), f"boss pattern tensor {name} duplicate field name", errors)

    expected_tensor_fields = {
        "pattern_context": [
            "boss_health_ratio", "boss_stamina_ratio", "boss_posture_ratio", "target_health_ratio_estimate",
            "target_distance_planar", "target_distance_3d", "target_bearing_sin", "target_bearing_cos",
            "target_elevation_sin", "target_elevation_cos", "target_relative_speed", "target_approach_velocity",
            "target_lateral_velocity", "has_line_of_sight", "path_available", "arena_edge_risk",
            "boss_phase_normalized", "elapsed_encounter_time", "elapsed_since_last_pattern", "same_pattern_streak_ratio",
            "recent_fast_pattern_ratio", "recent_heavy_pattern_ratio", "recent_gap_closer_ratio", "player_recent_damage_ratio",
            "boss_recent_damage_ratio", "selection_boundary_pre_attack", "selection_boundary_branch_window",
            "selection_boundary_recovery_end", "previous_pattern_family_fast", "previous_pattern_family_heavy",
            "previous_pattern_family_gap_closer", "target_health_estimate_confidence",
        ],
        "pattern_features": [
            "preferred_distance_min", "preferred_distance_max", "allowed_bearing_abs_max", "allowed_elevation_abs_max",
            "telegraph_duration", "active_duration", "recovery_duration", "cooldown_duration", "stamina_cost_ratio",
            "startup_tracking_yaw_ratio", "active_tracking_yaw_ratio", "recovery_tracking_yaw_ratio",
            "startup_tracking_speed_ratio", "active_tracking_speed_ratio", "area_pressure_ratio", "gap_close_ratio",
            "damage_pressure_ratio", "posture_pressure_ratio", "family_fast", "family_heavy", "family_gap_closer",
            "family_area_control", "branch_capable", "reserved_zero",
        ],
        "pattern_pair_features": [
            "distance_fit", "bearing_fit", "elevation_fit", "line_of_sight_fit", "phase_allowed", "cooldown_ready",
            "resource_ready", "predecessor_allowed", "branch_allowed", "arena_safe", "navigation_available",
            "repetition_penalty_feature", "timing_variety_feature", "target_motion_fit", "selection_boundary_fit", "reserved_zero",
        ],
    }
    for tensor_name, expected_names in expected_tensor_fields.items():
        actual_names = [row.get("name") for row in tensors.get(tensor_name, {}).get("fields", []) if isinstance(row, dict)]
        _expect(actual_names == expected_names, f"boss pattern tensor {tensor_name} semantic field order mismatch", errors)

    normalization = contract.get("normalization_contract", {})
    _expect(normalization.get("output_dtype") == "float32", "boss pattern normalizer output dtype mismatch", errors)
    _expect(normalization.get("nonfinite_input") == "hard_reject_pattern_request", "boss pattern nonfinite input policy mismatch", errors)
    _expect(normalization.get("all_fields_assigned_exactly_once") is True, "boss pattern normalizer closure flag must be true", errors)
    expected_normalizers = {
        "ratio_01": {"kind": "clamp", "min": 0.0, "max": 1.0, "divisor": 1.0},
        "signed_unit": {"kind": "clamp", "min": -1.0, "max": 1.0, "divisor": 1.0},
        "distance_cm": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor_ref": "max_target_distance_cm"},
        "signed_speed_cm_s": {"kind": "divide_clamp", "min": -1.0, "max": 1.0, "divisor_ref": "max_target_relative_speed_cm_s"},
        "encounter_elapsed_s": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor_ref": "max_encounter_elapsed_s"},
        "cooldown_seconds": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor_ref": "max_pattern_cooldown_s"},
        "bearing_degrees": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor": 180.0},
        "elevation_degrees": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor": 90.0},
        "pattern_duration_s": {"kind": "divide_clamp", "min": 0.0, "max": 1.0, "divisor_ref": "max_pattern_duration_s"},
        "constant_zero": {"kind": "constant", "min": 0.0, "max": 0.0, "divisor": 1.0, "value": 0.0},
    }
    definitions = normalization.get("definitions", {})
    _expect(definitions == expected_normalizers, "boss pattern normalizer definition mismatch", errors)
    for normalizer_name, spec in definitions.items() if isinstance(definitions, dict) else []:
        divisor = spec.get("divisor")
        if "divisor_ref" in spec:
            divisor = constants.get(spec.get("divisor_ref"))
        _expect(isinstance(divisor, (int, float)) and math.isfinite(float(divisor)) and float(divisor) > 0.0, f"boss pattern normalizer {normalizer_name} divisor must be finite and > 0", errors)
        _expect(spec.get("kind") in {"clamp", "divide_clamp", "constant"}, f"boss pattern normalizer {normalizer_name} kind invalid", errors)
        _expect(isinstance(spec.get("min"), (int, float)) and isinstance(spec.get("max"), (int, float)) and float(spec["min"]) <= float(spec["max"]), f"boss pattern normalizer {normalizer_name} range invalid", errors)

    assignments = normalization.get("assignments", {})
    _expect(set(assignments) == set(expected_tensor_fields) if isinstance(assignments, dict) else False, "boss pattern normalizer tensor assignment set mismatch", errors)
    for tensor_name, expected_names in expected_tensor_fields.items():
        groups = assignments.get(tensor_name, {}) if isinstance(assignments, dict) else {}
        assigned: list[str] = []
        for normalizer_name, names in groups.items() if isinstance(groups, dict) else []:
            _expect(normalizer_name in expected_normalizers, f"boss pattern tensor {tensor_name} unknown normalizer {normalizer_name}", errors)
            _expect(isinstance(names, list), f"boss pattern tensor {tensor_name} normalizer {normalizer_name} assignments must be list", errors)
            if isinstance(names, list):
                assigned.extend(names)
        _expect(len(assigned) == len(set(assigned)), f"boss pattern tensor {tensor_name} normalizer assignment duplicate", errors)
        _expect(set(assigned) == set(expected_names), f"boss pattern tensor {tensor_name} normalizer assignment closure mismatch", errors)

    _expect(normalization.get("padding") == {
        "pattern_context": "no_row_padding",
        "unoccupied_pattern_features": "all_zero_after_normalization",
        "unoccupied_pattern_pair_features": "all_zero_after_normalization",
        "unoccupied_pattern_id": "invalid_pattern_id",
        "unoccupied_pattern_mask": False,
        "masked_score_postprocess": "negative_infinity_before_ranking",
        "masked_parameter_proposals": "ignored_and_zeroed_before_logging",
    }, "boss pattern padding/masked-row contract mismatch", errors)

    expected_source_policy = {
        "forbidden_tokens": ["ground_truth", "omniscient", "hidden_actor", "raw_player_transform"],
        "allowed_by_tensor": {
            "pattern_context": [
                "observable_authoritative_self_state", "permitted_belief_snapshot", "locked_attack_target_snapshot",
                "authoritative_path_query", "authoritative_arena_query", "authoritative_boss_phase",
                "server_monotonic_time", "committed_pattern_history", "observable_committed_combat_history",
                "authoritative_self_history", "selection_boundary_one_hot",
            ],
            "pattern_features": ["pattern_data_asset", "pattern_data_asset_tag", "constant_zero"],
            "pattern_pair_features": ["deterministic_builder", "committed_pattern_history", "permitted_belief_snapshot", "constant_zero"],
        },
    }
    source_policy = contract.get("feature_source_policy", {})
    _expect(source_policy == expected_source_policy, "boss pattern feature source policy mismatch", errors)
    forbidden_tokens = expected_source_policy["forbidden_tokens"]
    for tensor_name, allowed_sources in expected_source_policy["allowed_by_tensor"].items():
        for field in tensors.get(tensor_name, {}).get("fields", []):
            source = str(field.get("source", ""))
            _expect(source in allowed_sources, f"boss pattern tensor {tensor_name} field {field.get('name')} source not allowed", errors)
            _expect(not any(token in source.lower() for token in forbidden_tokens), f"boss pattern tensor {tensor_name} field {field.get('name')} forbidden source", errors)

    outputs = contract.get("outputs", {})
    _expect(_shape_equals(outputs.get("pattern_raw_scores", {}).get("shape"), ["B", 32]), "boss pattern raw score shape mismatch", errors)
    proposals = outputs.get("pattern_parameter_proposals", {})
    _expect(_shape_equals(proposals.get("shape"), ["B", 32, 4]), "boss pattern parameter proposal shape mismatch", errors)
    expected_parameters = [
        {"index": 0, "name": "tracking_fraction", "decode": "authored_tracking_limit * clamp01(x)", "authority": "may_reduce_authored_maximum_only"},
        {"index": 1, "name": "telegraph_extension_fraction", "decode": "telegraph_extension_max_s * clamp01(x)", "authority": "extension_only"},
        {"index": 2, "name": "recovery_extension_fraction", "decode": "recovery_extension_max_s * clamp01(x)", "authority": "extension_only"},
        {"index": 3, "name": "reserved_zero", "decode": "constant_zero", "authority": "none"},
    ]
    _expect(proposals.get("parameters") == expected_parameters, "boss pattern parameter authority contract mismatch", errors)
    _expect(proposals.get("forbidden_outputs") == ["damage", "hitbox", "active_window", "root_motion", "interruptibility", "phase_transition"], "boss pattern forbidden output list mismatch", errors)
    _expect(proposals.get("commit_policy") == "decode_and_clamp_inside_pattern_data_asset_bounds", "boss pattern parameter proposals must clamp to authored bounds", errors)

    pattern_set = contract.get("pattern_set_asset_contract", {})
    _expect(pattern_set == {
        "storage": "Unreal_PrimaryDataAsset",
        "required_fields": ["pattern_set_id", "patterns", "safe_default_pattern_id", "utility_profile_reference", "optional_model_bundle_reference"],
        "invariants": {
            "pattern_count": "between_1_and_max_pattern_slots",
            "pattern_ids": "unique_uint16_and_strictly_ascending_after_canonicalization",
            "safe_default_pattern_id": "references_exactly_one_pattern_in_set",
            "pattern_references": "all_loaded_and_validated_before_request",
        },
    }, "boss pattern set asset contract mismatch", errors)

    asset = contract.get("pattern_asset_contract", {})
    required_asset_fields = [
        "pattern_id", "pattern_name", "pattern_family_tags", "allowed_boss_phases",
        "allowed_predecessor_pattern_ids", "allowed_successor_pattern_ids", "preferred_distance_cm",
        "allowed_bearing_degrees", "allowed_elevation_degrees", "requires_line_of_sight",
        "stamina_cost", "cooldown_seconds", "startup_telegraph_seconds", "active_seconds",
        "recovery_seconds", "telegraph_extension_max_s", "recovery_extension_max_s",
        "montage_reference", "montage_section", "root_motion_mode",
        "hitbox_window_reference", "damage_profile_reference", "phase_tracking_limits",
        "branch_windows", "interruptibility_allowlist", "interrupt_cleanup_policy",
        "arena_safety_policy", "navigation_policy",
    ]
    _expect(asset.get("required_fields") == required_asset_fields, "boss pattern asset required field order mismatch", errors)
    invariants = asset.get("invariants", {})
    _expect(invariants.get("startup_telegraph_seconds") == "finite_and_greater_than_zero", "boss pattern startup telegraph invariant must remain finite and > 0", errors)
    _expect(invariants.get("active_seconds") == "finite_and_greater_than_zero", "boss pattern active duration invariant must remain finite and > 0", errors)
    _expect(invariants.get("recovery_seconds") == "finite_and_greater_than_or_equal_to_zero", "boss pattern recovery invariant mismatch", errors)
    _expect(invariants.get("telegraph_extension_max_s") == "finite_and_greater_than_or_equal_to_zero", "boss pattern telegraph extension invariant mismatch", errors)
    _expect(invariants.get("recovery_extension_max_s") == "finite_and_greater_than_or_equal_to_zero", "boss pattern recovery extension invariant mismatch", errors)
    _expect(invariants.get("tracking_limits") == "finite_nonnegative_and_bounded_by_contract_maxima", "boss pattern tracking limit invariant mismatch", errors)

    expected_mask_rules = [
        "SlotOccupied", "BossPhaseAllowed", "AttackTargetIdentityAndGenerationValid", "RangeAllowed",
        "BearingAllowed", "ElevationAllowed", "LineOfSightSatisfied", "CooldownReady",
        "ResourceReservable", "PredecessorAllowed", "BranchAllowedAtBoundary", "ArenaSafe",
        "NavigationAvailable", "AuthoredAssetsLoaded", "SelectionBoundaryEligible", "ExecutorUnlocked",
        "ReservationAvailable",
    ]
    mask = contract.get("hard_mask_contract", {})
    _expect(mask.get("owner") == "BossPatternCandidateBuilder", "boss pattern hard mask owner mismatch", errors)
    _expect(mask.get("rules_in_order") == expected_mask_rules, "boss pattern hard mask rule order mismatch", errors)
    _expect(mask.get("zero_valid_rows", {}).get("inference_request_created") is False, "boss pattern zero-valid rows must skip inference", errors)

    authority = contract.get("authority_contract", {})
    _expect(authority == {
        "neural_and_utility_outputs": "advisory_only",
        "pattern_commit": "server_authority_only",
        "executor_phase": "server_authority_only",
        "hitbox_damage_root_motion": "deterministic_server_combat_module",
        "interrupt_result": "server_authority_only",
        "client_inference_gameplay_authority": False,
        "replicated_fields": ["committed_pattern_id", "pattern_start_server_time", "executor_phase", "authored_cue_state"],
        "save_load_policy": "pending_requests_discarded_locked_executor_state_restored_by_runtime_contract",
    }, "boss pattern authority contract mismatch", errors)

    lock = contract.get("selection_lock_contract", {})
    _expect(lock.get("inference_boundaries") == ["PreAttack", "BranchWindow", "RecoveryEnd"], "boss pattern inference boundary list mismatch", errors)
    phase_rules = lock.get("phase_rules", {})
    _expect(lock.get("lock_acquired_at") == "successful_pattern_commit_before_pre_attack_turn", "boss pattern lock acquisition point mismatch", errors)
    _expect(phase_rules.get("ReadyToSelect") == "selection_allowed_until_successful_commit", "boss pattern ReadyToSelect rule mismatch", errors)
    _expect(phase_rules.get("PreAttackTurn") == "selection_locked", "boss pattern PreAttackTurn must remain selection_locked", errors)
    _expect(phase_rules.get("StartupTelegraph") == "selection_locked", "boss pattern StartupTelegraph must remain selection_locked", errors)
    _expect(phase_rules.get("Active") == "selection_locked", "boss pattern Active must remain selection_locked", errors)
    _expect(phase_rules.get("Recovery") == "selection_locked_except_authored_branch_window", "boss pattern Recovery lock rule mismatch", errors)
    _expect(lock.get("ordinary_target_movement_interrupts") is False, "ordinary target movement cannot interrupt boss pattern", errors)
    _expect(lock.get("new_tactical_score_interrupts") is False and lock.get("new_pattern_score_interrupts") is False, "new scores cannot interrupt locked boss pattern", errors)
    _expect(lock.get("late_branch_response") == "reject_and_continue_authored_pattern_termination", "boss pattern late BranchWindow response policy mismatch", errors)

    hidden = contract.get("hidden_information_contract", {})
    for flag in ("ground_truth_target_transform_allowed", "post_lock_player_input_reselection_allowed", "post_lock_executor_transform_fed_back_to_model", "post_lock_executor_transform_may_change_pattern", "model_can_shorten_telegraph_or_recovery", "model_can_modify_active_window", "model_can_modify_hitbox_damage_root_motion"):
        _expect(hidden.get(flag) is False, f"boss pattern hidden-information/authority flag {flag} must be false", errors)
    _expect(hidden.get("model_may_extend_telegraph_or_recovery_inside_authored_bounds") is True, "boss pattern extension-only authority flag must be true", errors)
    _expect(hidden.get("post_lock_tracking") == "bounded_by_authored_phase_tracking_limits", "boss pattern post-lock tracking must be authored and bounded", errors)
    _expect(hidden.get("post_lock_executor_target_transform_source") == "authoritative_combat_targeting_policy_only", "boss pattern executor target transform source mismatch", errors)

    interrupts = contract.get("interrupt_contract", {})
    valid_interrupts = set(expected_enums["interrupt_kind"])
    forced = interrupts.get("forced", [])
    authored = interrupts.get("authored_allowlist_only", [])
    for value in forced:
        _expect(value in valid_interrupts, f"boss pattern unknown forced interrupt {value}", errors)
    for value in authored:
        _expect(value in valid_interrupts, f"boss pattern unknown authored interrupt {value}", errors)
    _expect(forced == ["Death", "ActorDestroyed", "AuthorityLost"], "boss pattern forced interrupt order mismatch", errors)
    _expect(authored == ["Stun", "PostureBreak", "ScriptedPhaseTransition", "ArenaReset"], "boss pattern authored interrupt allowlist mismatch", errors)

    request_fields = contract.get("request_contract", {}).get("fields", [])
    response_fields = contract.get("response_contract", {}).get("fields", [])
    _expect(request_fields == ["pattern_decision_id", "selection_boundary", "attack_target_handle", "boss_phase_revision", "combat_state_revision", "pattern_candidate_set_hash", "boss_pattern_decision_contract_hash"], "boss pattern request field order mismatch", errors)
    _expect(response_fields == ["pattern_decision_id", "selected_pattern_slot", "selected_pattern_id", "selected_parameter_proposals", "pattern_candidate_set_hash", "boss_pattern_decision_contract_hash"], "boss pattern response field order mismatch", errors)

    expected_commit_order = [
        "LatestPendingPatternDecisionIdMatches", "PatternDecisionContractHashMatches",
        "PatternCandidateSetHashMatches", "SelectionBoundaryStillEligible", "BossPhaseRevisionMatches",
        "CombatStateRevisionMatches", "AttackTargetIdentityAndGenerationMatch", "SelectedSlotAndPatternIdMatch",
        "SelectedPatternMaskStillTrue", "ResourcesCompareAndSwap", "ExecutorStillUnlocked",
    ]
    commit = contract.get("commit_validation", {})
    _expect(commit.get("owner") == "BossPatternCommitCoordinator", "boss pattern commit owner mismatch", errors)
    _expect(commit.get("order") == expected_commit_order, "boss pattern commit validation order mismatch", errors)
    _expect(commit.get("success_action") == "atomically_lock_pattern_and_enter_pre_attack_turn", "boss pattern commit success action mismatch", errors)
    _expect(commit.get("failure_action") == "reject_response_without_mutating_locked_pattern", "boss pattern commit failure action mismatch", errors)

    asset_bundle_digest = contract.get("pattern_asset_bundle_digest_contract", {})
    _expect(asset_bundle_digest == {
        "algorithm": "SHA-256",
        "status": "pending_unreal_commandlet_and_python_parity",
        "build_owner": "BossPatternValidationCommandlet",
        "pattern_set_id_digest": {
            "algorithm": "SHA-256",
            "source_type": "string",
            "text_encoding": "UTF-8",
            "unicode_normalization": "NFC",
            "case_policy": "case_sensitive",
            "whitespace_policy": "preserve",
            "input_bytes": "normalized_utf8_without_bom",
            "empty_allowed": False,
        },
        "canonical_manifest": {
            "byte_order": "little",
            "fields": [
                {"name": "magic", "type": "bytes[8]", "value_ascii": "BPABND01"},
                {"name": "serialization_version", "type": "uint16", "value": 1},
                {"name": "boss_pattern_contract_sha256", "type": "bytes[32]"},
                {"name": "pattern_set_id_sha256", "type": "bytes[32]"},
                {"name": "safe_default_pattern_id", "type": "uint16"},
                {"name": "occupied_pattern_count", "type": "uint8"},
                {"name": "pattern_ids", "type": "uint16[32]", "padding_value_ref": "invalid_pattern_id"},
                {"name": "pattern_definition_sha256", "type": "bytes[32][32]", "padding_value": "all_zero"},
            ],
        },
        "pattern_definition_digest": {
            "canonicalization": "RFC8785_JCS_UTF8",
            "field_set_ref": "pattern_asset_contract.required_fields",
            "numeric_policy": "finite_values_only_and_contract_units",
            "asset_reference_identity": "cooked_content_sha256_not_object_path",
            "asset_reference_substitution": {
                "jcs_value_type": "string",
                "jcs_string_format": "lowercase_hex_64_no_prefix",
                "source_digest_algorithm": "SHA-256",
                "source_digest_bytes": 32,
                "object_path_in_digest": False,
            },
        },
        "pattern_order": "pattern_id_ascending",
        "runtime_source": "validated_pattern_set_data_asset_embedded_digest",
    }, "boss pattern asset bundle digest contract mismatch", errors)

    hashes = contract.get("hash_contract", {})
    expected_hash_fields = {
        "pattern_candidate_set_hash": [
            "magic", "serialization_version", "boss_pattern_contract_sha256", "pattern_asset_bundle_sha256",
            "pattern_slot_count", "pattern_ids", "pattern_mask", "attack_target_handle", "selection_boundary",
            "boss_phase_revision", "combat_state_revision",
        ],
        "boss_pattern_decision_contract_hash": [
            "magic", "serialization_version", "boss_pattern_contract_sha256", "pattern_model_sha256",
            "pattern_normalization_contract_sha256", "pattern_postprocess_contract_sha256",
            "pattern_calibration_ood_asset_sha256", "pattern_executor_contract_sha256",
        ],
    }
    for hash_name, expected_names in expected_hash_fields.items():
        spec = hashes.get(hash_name, {})
        _expect(spec.get("algorithm") == "SHA-256", f"boss pattern {hash_name} algorithm mismatch", errors)
        _expect(spec.get("raw_float_included") is False, f"boss pattern {hash_name} must exclude raw float", errors)
        _expect(spec.get("byte_order") == "little", f"boss pattern {hash_name} byte order mismatch", errors)
        fields = spec.get("fields", [])
        names = [row.get("name") for row in fields if isinstance(row, dict)]
        _expect(names == expected_names, f"boss pattern {hash_name} field order mismatch: {names}", errors)
        if len(fields) >= 2 and isinstance(fields[0], dict) and isinstance(fields[1], dict):
            magic_match = re.fullmatch(r"bytes\[(\d+)\]", str(fields[0].get("type")))
            _expect(bool(magic_match), f"boss pattern {hash_name} magic type invalid", errors)
            if magic_match:
                _expect(len(str(fields[0].get("value_ascii", "")).encode("ascii", "ignore")) == int(magic_match.group(1)), f"boss pattern {hash_name} magic size mismatch", errors)
            _expect(fields[1].get("name") == "serialization_version" and fields[1].get("type") == "uint16", f"boss pattern {hash_name} serialization version invalid", errors)

    candidate_fields = {row.get("name"): row for row in hashes.get("pattern_candidate_set_hash", {}).get("fields", []) if isinstance(row, dict)}
    _expect(candidate_fields.get("pattern_slot_count", {}).get("value_ref") == "max_pattern_slots", "boss pattern candidate hash slot count reference mismatch", errors)
    _expect(candidate_fields.get("pattern_ids", {}).get("type") == "uint16[32]", "boss pattern candidate hash pattern id array mismatch", errors)
    _expect(candidate_fields.get("pattern_mask", {}).get("bit_count") == 32, "boss pattern candidate hash mask bit count mismatch", errors)

    fallback = contract.get("fallback_contract", {})
    _expect(fallback.get("zero_valid_rows") == "ReturnPatternUnavailableToAttackSkillWithoutInferenceOrUtility", "boss pattern zero-valid fallback mismatch", errors)
    _expect(fallback.get("order") == ["UtilityBaselineOnSameValidMask", "AuthoredSafeDefaultIfStillValid", "ReturnPatternUnavailableToAttackSkill", "ParentTacticalPolicyReplan"], "boss pattern fallback order mismatch", errors)
    _expect(fallback.get("utility_tie_break") == "adjusted_score_desc_then_pattern_id_asc", "boss pattern Utility tie-break mismatch", errors)
    _expect(fallback.get("authored_safe_default_source") == "PatternSetDataAsset.safe_default_pattern_id", "boss pattern safe-default source mismatch", errors)
    _expect(fallback.get("authored_safe_default_constraint") == "referenced_pattern_must_be_occupied_and_currently_valid", "boss pattern safe-default constraint mismatch", errors)
    _expect(fallback.get("fallback_snapshot_policy") == "same_immutable_request_only", "boss pattern fallback snapshot policy mismatch", errors)
    _expect(fallback.get("inference_failure_during_locked_pattern") == "continue_locked_pattern", "boss pattern locked inference failure must continue current pattern", errors)

    codegen = contract.get("code_generation", {})
    _expect(codegen.get("source_of_truth") == "contracts/current/boss_pattern_contract_v1.yaml", "boss pattern codegen source-of-truth mismatch", errors)
    _expect(codegen.get("generator") == "tools/generate_contracts.py", "boss pattern codegen generator mismatch", errors)
    _expect(codegen.get("outputs") == [
        "generated/python/ai_native_npc_boss_pattern_contracts_generated.py",
        "generated/cpp/AINativeNPCBossPatternContracts.generated.h",
        "generated/docs/boss_pattern_reference.md",
        "tests/golden/boss_pattern_hash_vectors.json",
    ], "boss pattern codegen output list mismatch", errors)
    _expect(codegen.get("generated_files_edit_policy") == "do_not_edit", "boss pattern generated file edit policy mismatch", errors)
    docs = contract.get("documentation_contract", {})
    _expect(docs == {
        "marker_begin": "<!-- BEGIN AUTO-GENERATED BOSS PATTERN CONTRACT -->",
        "marker_end": "<!-- END AUTO-GENERATED BOSS PATTERN CONTRACT -->",
        "generated_reference": "generated/docs/boss_pattern_reference.md",
        "required_document": "docs/current/contract-appendices.md",
        "strict_policy": "marker_content_must_equal_generated_reference",
    }, "boss pattern documentation marker contract mismatch", errors)

    release = contract.get("release_status", {})
    _expect(release.get("static_schema_generator_harness") == "pass", "boss pattern static harness status mismatch", errors)
    for gate in ("asset_bundle_digest_parity", "unreal_float_parity", "onnx_output_parity", "unreal_pattern_runtime", "fairness_quality", "performance_budget"):
        _expect(release.get(gate) == "pending", f"boss pattern release gate {gate} must remain pending", errors)

    return errors


def validate_contracts(paths: ContractPaths) -> list[str]:
    errors: list[str] = []
    try:
        schema, skills, goals = load_contracts(paths)
        boss_pattern = load_boss_pattern_contract(paths)
        taxonomy = load_yaml(paths.test_taxonomy)
    except Exception as exc:
        return [f"YAML parse/load failure: {exc}"]

    errors.extend(validate_boss_pattern_contract(boss_pattern))

    s_meta = schema.get("schema", {})
    constants = schema.get("constants", {})
    enums = schema.get("enums", {})
    _expect(s_meta.get("version") == "2.0.0", "schema.version must be 2.0.0", errors)
    _expect(s_meta.get("contract_revision") == "2.0.0-rc5", "schema.contract_revision must be 2.0.0-rc5", errors)
    _expect(s_meta.get("release_stage") == "rc5", "schema.release_stage must be rc5", errors)
    _expect(s_meta.get("bundle_version") == "0.4.6", "schema.bundle_version must be 0.4.6", errors)
    _expect(s_meta.get("endianness") == "little", "schema endianness must be little", errors)

    semantic_contract = schema.get("normalizer_semantic_contract", {})
    required_semantic_flags = {
        "constant_missing_value_must_equal_normalizer_constant",
        "must_equal_requires_constant_normalizer",
        "must_equal_requires_singleton_valid_range",
        "must_equal_requires_matching_missing_value",
        "padding_zero_value_must_fit_valid_range",
        "constraint_and_missing_occupied_value_must_match",
    }
    for flag in sorted(required_semantic_flags):
        _expect(semantic_contract.get(flag) is True, f"normalizer_semantic_contract.{flag} must be true", errors)

    documentation = schema.get("documentation_contract", {})
    _expect(documentation.get("forbid_manual_hash_literal_outside_generated_block") is True, "documentation contract must forbid manual hash literals", errors)
    manual_policy = documentation.get("manual_hash_literal_policy", {})
    for flag in ("forbid_known_value_ascii_token_anywhere_outside_generated_block", "forbid_general_magic_assignment_sentence"):
        _expect(manual_policy.get(flag) is True, f"documentation manual hash policy {flag} must be true", errors)

    markdown_scope = documentation.get("semantic_markdown_scope", {})
    _expect(markdown_scope.get("mode") == "all_locked_active_markdown", "documentation semantic markdown scope mode mismatch", errors)
    _expect(markdown_scope.get("exclude_prefixes") == ["docs/archive/", "docs/history/", "contracts/archive/", "manifests/archive/", "generated/docs/"], "documentation semantic markdown exclude prefixes mismatch", errors)
    _expect(markdown_scope.get("magic_value_pattern") == "[A-Za-z0-9_]{4,64}", "documentation magic value pattern mismatch", errors)
    _expect(markdown_scope.get("current_generated_blocks_may_be_stripped") is True, "documentation generated block stripping policy mismatch", errors)

    required_constants = {
        "regular_target_slots": 16,
        "no_target_slot": 16,
        "total_target_slots": 17,
        "skill_count": 16,
        "candidate_count": 272,
        "event_slots": 12,
        "global_feature_count": 128,
        "target_feature_count": 48,
        "event_feature_count": 24,
        "candidate_pair_feature_count": 16,
        "parameter_count": 4,
    }
    for key, expected in required_constants.items():
        _expect(constants.get(key) == expected, f"constants.{key} expected {expected}, got {constants.get(key)}", errors)
    _expect(constants.get("skill_count", 0) * constants.get("total_target_slots", 0) == constants.get("candidate_count"), "candidate formula invariant failed", errors)

    for enum_name, values in enums.items():
        _validate_enum(enum_name, values, errors)
    _expect(len(enums.get("target_kind", [])) == 8, "target_kind enum count must be 8", errors)
    _expect(len(enums.get("skill", [])) == constants.get("skill_count"), "skill enum count mismatch", errors)

    handle = schema.get("runtime_handle_contract", {})
    _expect(handle.get("model_input") is False, "runtime handle must not be model input", errors)
    field_names = [x.get("name") for x in handle.get("fields", []) if isinstance(x, dict)]
    _expect(field_names == ["kind", "stable_id", "generation", "revision"], "runtime handle field order mismatch", errors)
    exclusions = set(handle.get("model_feature_exclusions", []))
    for forbidden in ("stable_id", "generation", "revision", "absolute_world_position", "created_world_time"):
        _expect(forbidden in exclusions, f"model_feature_exclusions missing {forbidden}", errors)

    slots = schema.get("target_slots", {})
    _expect(slots.get("regular_slots") == 16 and slots.get("no_target_slot") == 16 and slots.get("total_slots") == 17, "target slot constants mismatch", errors)
    quota = slots.get("quota", {})
    _expect(sum(quota.values()) == 16, f"target quota must sum to 16, got {sum(quota.values()) if isinstance(quota, dict) else 'invalid'}", errors)
    quant = slots.get("quantization", {})
    _expect(quant.get("rounding") == "half_away_from_zero", "slotter quantization rounding mismatch", errors)
    for qname in ("confidence", "age_seconds", "distance_cm", "loudness"):
        _expect(isinstance(quant.get(qname), dict), f"slotter quantization missing {qname}", errors)
    for category in ("Entity", "SoundEvent", "CoverSlot", "SmartObject", "PositionLike"):
        keys = slots.get("category_sort_keys", {}).get(category)
        _expect(isinstance(keys, list) and keys and keys[-1].get("field") == "canonical_handle_bytes", f"slotter sort key for {category} must end in canonical handle", errors)

    layout = schema.get("candidate_layout", {})
    _expect(layout.get("count") == 272, "candidate_layout.count mismatch", errors)
    _expect(layout.get("order") == "skill_major_target_minor", "candidate order mismatch", errors)
    cont = layout.get("continue_control", {})
    _expect(cont.get("skill_id") == 1 and cont.get("executable_skill") is False, "Continue control contract invalid", errors)
    _expect(cont.get("current_skill_one_hot_index_17") == "reserved_zero", "Continue current skill feature must be reserved zero", errors)

    score = schema.get("score_contract", {})
    _expect(score.get("query", {}).get("layer_norm") is True and score.get("query", {}).get("l2_normalize") is True, "score query must be LayerNorm + L2 normalize", errors)
    _expect(score.get("key", {}).get("layer_norm") is True and score.get("key", {}).get("l2_normalize") is True, "score key must be LayerNorm + L2 normalize", errors)
    _expect(isinstance(score.get("cosine_temperature"), (int, float)) and score["cosine_temperature"] > 0, "cosine temperature invalid", errors)
    _expect(score.get("raw_score_clamp") == [-2.5, 2.5], "raw score clamp mismatch", errors)

    mismatch = schema.get("contract_mismatch_policy", {})
    _expect(mismatch.get("schema_or_registry_or_version_mismatch") == "hard_reject_before_feature_build_or_inference", "contract mismatch must hard reject before inference", errors)
    _expect(mismatch.get("ood_scope") == "valid_contract_inputs_only", "OOD scope must exclude contract mismatch", errors)

    tensors = schema.get("tensors", {})
    expected_shapes = {
        "global_state": (["B", 128], "float32"),
        "target_features": (["B", 17, 48], "float32"),
        "target_kind_ids": (["B", 17], "int64"),
        "target_mask": (["B", 17], "bool"),
        "event_features": (["B", 12, 24], "float32"),
        "event_type_ids": (["B", 12], "int64"),
        "event_target_slots": (["B", 12], "int64"),
        "event_mask": (["B", 12], "bool"),
        "candidate_pair_features": (["B", 272, 16], "float32"),
        "candidate_mask": (["B", 272], "bool"),
    }
    for name, (shape, dtype) in expected_shapes.items():
        t = tensors.get(name)
        _expect(isinstance(t, dict), f"tensor {name} missing", errors)
        if not isinstance(t, dict):
            continue
        _expect(_shape_equals(t.get("shape"), shape), f"tensor {name} shape expected {shape}, got {t.get('shape')}", errors)
        _expect(t.get("dtype") == dtype, f"tensor {name} dtype expected {dtype}, got {t.get('dtype')}", errors)
        _expect(t.get("dtype") in ALLOWED_DTYPES, f"tensor {name} unsupported dtype", errors)

    fielded = {"global_state": 128, "event_features": 24, "candidate_pair_features": 16}
    for name, count in fielded.items():
        fields = tensors.get(name, {}).get("fields", [])
        _expect(len(fields) == count, f"tensor {name} field count expected {count}, got {len(fields)}", errors)
        names: list[str] = []
        for i, field in enumerate(fields):
            _validate_field(field, i, constants, f"tensors.{name}.fields", errors)
            if isinstance(field, dict):
                names.append(field.get("name"))
        _expect(len(names) == len(set(names)), f"tensor {name} field names duplicate", errors)

    common = tensors.get("target_features", {}).get("common_fields", [])
    _expect(len(common) == 32, f"target common fields expected 32, got {len(common)}", errors)
    for i, field in enumerate(common):
        _validate_field(field, i, constants, "tensors.target_features.common_fields", errors)
    _expect(tensors.get("target_features", {}).get("payload_range") == [32, 47], "target payload range mismatch", errors)

    global_fields = tensors.get("global_state", {}).get("fields", [])
    if len(global_fields) > 17:
        f17 = global_fields[17]
        _expect(f17.get("name") == "current_skill_ContinueCurrentAction_reserved_zero", "global index 17 must be Continue reserved zero", errors)
        _expect(f17.get("normalizer") == {"type": "constant", "value": 0.0}, "global index 17 normalizer must be constant zero", errors)

    payloads = schema.get("target_payload_features", {})
    target_names = [x["name"] for x in enums.get("target_kind", [])]
    _expect(set(payloads) == set(target_names), "target payload kinds must exactly match target_kind enum", errors)
    for kind in target_names:
        fields = payloads.get(kind, [])
        _expect(len(fields) == 16, f"payload {kind} expected 16 fields, got {len(fields)}", errors)
        for i, field in enumerate(fields):
            _validate_field(field, i, constants, f"target_payload_features.{kind}", errors)
            if isinstance(field, dict):
                _expect(field.get("tensor_index") == 32 + i, f"payload {kind}[{i}] tensor_index must be {32+i}", errors)

    outputs = schema.get("outputs", {})
    _expect(_shape_equals(outputs.get("candidate_raw_scores", {}).get("shape"), ["B", 272]), "candidate_raw_scores shape mismatch", errors)
    params = outputs.get("candidate_parameter_proposals", {})
    _expect(_shape_equals(params.get("shape"), ["B", 272, 4]), "candidate parameter output shape mismatch", errors)
    _expect(len(params.get("fields", [])) == 4, "candidate parameter fields count mismatch", errors)
    _expect(params.get("commit_policy") == "decode_then_clamp_to_registry_min_max_on_server_game_thread", "candidate parameter commit clamp missing", errors)

    hash_contracts = schema.get("hash_contract", {})
    candidate_hash = hash_contracts.get("candidate_set_hash", {})
    decision_hash = hash_contracts.get("decision_contract_hash", {})

    def validate_hash_fields(contract_name: str, contract: Any, expected_names: list[str]) -> dict[str, dict[str, Any]]:
        if not isinstance(contract, dict):
            errors.append(f"hash_contract.{contract_name} must be mapping")
            return {}
        _expect(contract.get("algorithm") == "SHA-256", f"{contract_name} algorithm must be SHA-256", errors)
        _expect(contract.get("raw_float_included") is False, f"{contract_name} must exclude raw float", errors)
        _expect(contract.get("byte_order") == "little", f"{contract_name} byte_order must be little", errors)
        fields = contract.get("fields")
        _expect(isinstance(fields, list), f"{contract_name}.fields must be list", errors)
        if not isinstance(fields, list):
            return {}
        names = [row.get("name") for row in fields if isinstance(row, dict)]
        _expect(names == expected_names, f"{contract_name} field order mismatch: {names}", errors)
        _expect(len(names) == len(set(names)), f"{contract_name} duplicate field name", errors)
        result = {row.get("name"): row for row in fields if isinstance(row, dict)}
        for idx, row in enumerate(fields):
            if not isinstance(row, dict):
                errors.append(f"{contract_name}.fields[{idx}] must be mapping")
                continue
            _expect(isinstance(row.get("type"), str), f"{contract_name}.{row.get('name')} type missing", errors)
        return result

    candidate_names = ["magic", "serialization_version", "schema_source_sha256", "target_slot_count", "target_handles", "target_mask", "candidate_mask"]
    hash_fields = validate_hash_fields("candidate_set_hash", candidate_hash, candidate_names)
    magic = hash_fields.get("magic", {})
    magic_type = magic.get("type")
    magic_match = re.fullmatch(r"bytes\[(\d+)\]", str(magic_type))
    _expect(bool(magic_match), "candidate hash magic type must be bytes[N]", errors)
    if magic_match:
        _expect(len(str(magic.get("value_ascii", "")).encode("ascii", "ignore")) == int(magic_match.group(1)), "candidate hash magic byte length mismatch", errors)
    version_field = hash_fields.get("serialization_version", {})
    _expect(version_field.get("type") == "uint16" and isinstance(version_field.get("value"), int) and 0 <= version_field.get("value") <= 65535, "candidate hash serialization version invalid", errors)
    _expect(hash_fields.get("schema_source_sha256", {}).get("type") == "bytes[32]", "candidate hash schema digest type mismatch", errors)
    target_count = hash_fields.get("target_slot_count", {})
    _expect(target_count.get("type") == "uint8" and target_count.get("value_ref") == "total_target_slots", "candidate hash target count contract mismatch", errors)
    handle_field = hash_fields.get("target_handles", {})
    _expect(handle_field.get("type") == "target_handle[17]", "candidate hash target handle array mismatch", errors)
    _expect(handle_field.get("field_order") == ["kind:uint8", "stable_id:uint64", "generation:uint32", "revision:uint64"], "candidate hash target handle field order mismatch", errors)
    target_mask_field = hash_fields.get("target_mask", {})
    candidate_mask_field = hash_fields.get("candidate_mask", {})
    _expect(target_mask_field.get("type") == "bitset" and target_mask_field.get("bit_count") == 17 and target_mask_field.get("byte_count") == 3 and target_mask_field.get("bit_order") == "LSB-first" and target_mask_field.get("unused_high_bits") == "zero", "candidate hash target_mask contract mismatch", errors)
    _expect(candidate_mask_field.get("type") == "bitset" and candidate_mask_field.get("bit_count") == 272 and candidate_mask_field.get("byte_count") == 34 and candidate_mask_field.get("bit_order") == "LSB-first", "candidate hash candidate_mask contract mismatch", errors)
    order = candidate_hash.get("response_validation_order", [])
    _expect(order and order[0] == "compare_response_hash_to_pending_request_hash", "response hash must compare pending request first", errors)

    decision_names = ["magic", "serialization_version", "schema_source_sha256", "skill_registry_sha256", "goal_registry_sha256", "model_sha256", "normalization_contract_sha256", "slotter_contract_sha256", "postprocess_contract_sha256", "calibration_ood_asset_sha256"]
    decision_fields = validate_hash_fields("decision_contract_hash", decision_hash, decision_names)
    dmagic = decision_fields.get("magic", {})
    dmagic_match = re.fullmatch(r"bytes\[(\d+)\]", str(dmagic.get("type")))
    _expect(bool(dmagic_match), "decision hash magic type must be bytes[N]", errors)
    if dmagic_match:
        _expect(len(str(dmagic.get("value_ascii", "")).encode("ascii", "ignore")) == int(dmagic_match.group(1)), "decision hash magic byte length mismatch", errors)
    dver = decision_fields.get("serialization_version", {})
    _expect(dver.get("type") == "uint16" and isinstance(dver.get("value"), int), "decision hash serialization version invalid", errors)
    for name in decision_names[2:]:
        _expect(decision_fields.get(name, {}).get("type") == "bytes[32]", f"decision hash {name} must be bytes[32]", errors)

    # Skill registry cross-validation
    reg_meta = skills.get("registry", {})
    _expect(reg_meta.get("version") == constants.get("skill_registry_version"), "skill registry version mismatch", errors)
    _expect(reg_meta.get("contract_revision") == s_meta.get("contract_revision"), "skill registry contract revision mismatch", errors)
    reg_skills = skills.get("skills", [])
    _expect(len(reg_skills) == 16, "skill registry must contain 16 skills", errors)
    schema_skills = enums.get("skill", [])
    for i, item in enumerate(reg_skills):
        if i >= len(schema_skills):
            break
        _expect(item.get("id") == schema_skills[i].get("id") and item.get("name") == schema_skills[i].get("name"), f"skill registry row {i} enum mismatch", errors)
        allowed = item.get("allowed_target_kinds", [])
        _expect(len(allowed) == len(set(allowed)), f"skill {item.get('name')} duplicate target kind", errors)
        for kind in allowed:
            _expect(kind in target_names, f"skill {item.get('name')} unknown target kind {kind}", errors)
        parameters = item.get("parameters", [])
        _expect(len(parameters) == 4, f"skill {item.get('name')} parameter count must be 4", errors)
        for slot, param in enumerate(parameters):
            _expect(param.get("slot") == slot, f"skill {item.get('name')} parameter slot order mismatch", errors)
            for key in ("active", "unit", "min", "max", "default", "decode", "commit_clamp"):
                _expect(key in param, f"skill {item.get('name')} parameter {slot} missing {key}", errors)
            if all(isinstance(param.get(k), (int, float)) for k in ("min", "max", "default")):
                _expect(param["min"] <= param["default"] <= param["max"], f"skill {item.get('name')} parameter {slot} default out of range", errors)
            _expect(param.get("commit_clamp") is True, f"skill {item.get('name')} parameter {slot} must clamp at commit", errors)
    if len(reg_skills) > 1:
        continue_skill = reg_skills[1]
        _expect(continue_skill.get("control_candidate") is True and continue_skill.get("executable") is False, "Continue skill control semantics invalid", errors)
        _expect(continue_skill.get("current_skill_one_hot_allowed") is False, "Continue must not appear in current skill one-hot", errors)
        _expect(continue_skill.get("can_continue_contract", {}).get("validate_against_latest_belief") is True, "Continue requires CanContinue(latest belief)", errors)

    commit_policies = skills.get("target_commit_policies", {})
    _expect(set(commit_policies) == set(target_names), "skill target commit policies must cover all target kinds", errors)

    # Goal registry cross-validation
    gmeta = goals.get("registry", {})
    _expect(gmeta.get("version") == constants.get("goal_registry_version"), "goal registry version mismatch", errors)
    _expect(gmeta.get("contract_revision") == s_meta.get("contract_revision"), "goal registry contract revision mismatch", errors)
    arb = goals.get("arbitration", {})
    _expect(arb.get("max_active_goals") == 1, "exactly one active goal contract required", errors)
    key_fields = [x.get("field") for x in arb.get("selection_key", [])]
    _expect(key_fields == ["priority", "source_priority", "created_time_quantized_ms", "goal_instance_id"], "goal selection key mismatch", errors)
    _expect(goals.get("states") == ["Inactive", "Active", "Suspended", "Succeeded", "Failed", "Aborted"], "goal states mismatch", errors)
    increase = set(goals.get("revision_contract", {}).get("increase_on", []))
    no_inc = set(goals.get("revision_contract", {}).get("do_not_increase_on", []))
    _expect(not increase.intersection(no_inc), "goal revision increase/do-not-increase overlap", errors)
    schema_goal_names = {x["name"] for x in enums.get("goal_type", [])}
    registry_goal_names = {x.get("name") for x in goals.get("goals", [])}
    _expect(schema_goal_names - {"None"} == registry_goal_names, "goal registry names must match schema goal enum except None", errors)
    phase_names = {x["name"] for x in enums.get("goal_phase", [])}
    event_names = {x["name"] for x in enums.get("event_type", [])} | {"Timeout"}
    skill_names = {x["name"] for x in schema_skills}
    for goal in goals.get("goals", []):
        phases = goal.get("phases")
        if not isinstance(phases, dict):
            continue
        _expect(goal.get("initial_phase") in phases, f"goal {goal.get('name')} initial phase missing", errors)
        for phase_name, phase in phases.items():
            _expect(phase_name in phase_names, f"goal {goal.get('name')} unknown phase {phase_name}", errors)
            for skill in phase.get("allowed_skills", []):
                _expect(skill in skill_names, f"goal {goal.get('name')}/{phase_name} unknown skill {skill}", errors)
            transitions = phase.get("transitions", [])
            orders = [x.get("order") for x in transitions]
            _expect(orders == list(range(len(transitions))), f"goal {goal.get('name')}/{phase_name} transition order must be contiguous", errors)
            for tr in transitions:
                _expect(tr.get("event") in event_names, f"goal {goal.get('name')}/{phase_name} unknown event {tr.get('event')}", errors)
                _expect(not ("to_phase" in tr and "terminal" in tr), f"goal {goal.get('name')}/{phase_name} transition cannot have both to_phase and terminal", errors)
                if "to_phase" in tr:
                    _expect(tr["to_phase"] in phases, f"goal {goal.get('name')}/{phase_name} unknown target phase {tr['to_phase']}", errors)
                if "terminal" in tr:
                    _expect(tr["terminal"] in {"Succeeded", "Failed", "Aborted"}, f"goal {goal.get('name')}/{phase_name} invalid terminal", errors)
                if "to_goal" in tr:
                    _expect(tr["to_goal"] in registry_goal_names, f"goal {goal.get('name')}/{phase_name} unknown target goal {tr['to_goal']}", errors)

    v1_scope = goals.get("v1_product_scope", {})
    _expect(v1_scope.get("exact_goal_names") == ["IdleObserve", "InvestigateDisturbance", "EnforceBoundary", "CombatEngage"], "V1 exact goal list mismatch", errors)
    social = goals.get("primary_social_subject_selection", {})
    _expect(social.get("max_primary_subjects") == 1, "primary social subject count must be one", errors)
    _expect(social.get("raw_float_sorting_forbidden") is True, "primary social subject must forbid raw float sorting", errors)
    social_key = [x.get("field") for x in social.get("selection_key", []) if isinstance(x, dict)]
    _expect(social_key == ["active_dialogue_subject", "active_goal_primary_target", "visible_now", "identity_confidence_q", "belief_age_q", "distance_q", "stable_id", "generation"], "primary social subject selection key mismatch", errors)

    # Test taxonomy is the single source for Critical/OOD naming and minimum denominator.
    treg = taxonomy.get("registry", {})
    _expect(treg.get("version") == "1.0.0", "test taxonomy version mismatch", errors)
    _expect(treg.get("contract_revision") == s_meta.get("contract_revision"), "test taxonomy contract revision mismatch", errors)
    critical = taxonomy.get("critical_suite", {})
    ood = taxonomy.get("ood_suite", {})
    critical_count = critical.get("required_family_count")
    cases_per_family = critical.get("minimum_cases_per_family")
    ood_count = ood.get("required_family_count")
    _expect(isinstance(critical_count, int) and critical_count > 0, "critical required_family_count must be positive int", errors)
    _expect(isinstance(cases_per_family, int) and cases_per_family > 0, "critical minimum_cases_per_family must be positive int", errors)
    _expect(isinstance(ood_count, int) and ood_count > 0, "OOD required_family_count must be positive int", errors)
    _validate_enum("critical_suite.families", critical.get("families", []), errors)
    _validate_enum("ood_suite.families", ood.get("families", []), errors)
    _expect(len(critical.get("families", [])) == critical_count, "critical family count must equal family list length", errors)
    _expect(len(ood.get("families", [])) == ood_count, "OOD family count must equal family list length", errors)
    derived = critical.get("derived", {}).get("minimum_sequence_count", {})
    _expect(derived.get("operation") == "multiply", "critical minimum sequence derivation operation must be multiply", errors)
    _expect(derived.get("operands") == ["required_family_count", "minimum_cases_per_family"], "critical minimum sequence derivation operands mismatch", errors)
    _expect(isinstance(critical.get("contract_id"), str) and bool(critical.get("contract_id")), "critical contract_id missing", errors)
    _expect(isinstance(ood.get("contract_id"), str) and bool(ood.get("contract_id")), "OOD contract_id missing", errors)
    tdoc = taxonomy.get("documentation_contract", {})
    for role in ("requirements", "unreal"):
        spec = tdoc.get(role, {})
        _expect(isinstance(spec.get("path"), str) and bool(spec.get("path")), f"taxonomy documentation {role}.path missing", errors)
        _expect(isinstance(spec.get("marker_begin"), str) and bool(spec.get("marker_begin")), f"taxonomy documentation {role}.marker_begin missing", errors)
        _expect(isinstance(spec.get("marker_end"), str) and bool(spec.get("marker_end")), f"taxonomy documentation {role}.marker_end missing", errors)
        _expect(isinstance(spec.get("generated_reference"), str) and bool(spec.get("generated_reference")), f"taxonomy documentation {role}.generated_reference missing", errors)

    return errors


def round_half_away_from_zero(value: float) -> int:
    return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))


def resolve_ref(spec: dict[str, Any], key: str, constants: dict[str, Any]) -> float:
    if key in spec:
        return float(spec[key])
    ref = spec.get(f"{key}_ref")
    if ref is None:
        raise KeyError(key)
    return float(constants[ref])


def apply_normalizer(spec: dict[str, Any], value: float | None, constants: dict[str, Any], sentinel: str | None = None) -> float:
    typ = spec["type"]
    if typ == "constant":
        return float(spec["value"])
    if typ == "boolean":
        return 1.0 if bool(value) else 0.0
    if typ == "clamp":
        x = float(value or 0.0)
        return min(float(spec["max"]), max(float(spec["min"]), x))
    if typ == "divide_clamp":
        x = float(value or 0.0)
        div = resolve_ref(spec, "divisor", constants)
        return min(float(spec["max"]), max(float(spec["min"]), x / div))
    if typ == "trigonometric":
        x = float(value or 0.0)
        return math.sin(x) if spec["function"] == "sin" else math.cos(x)
    if typ == "log1p_ratio":
        x = float(value or 0.0)
        hi = float(constants[spec["input_max_ref"]])
        den = float(constants[spec["denominator_ref"]])
        x = min(hi, max(float(spec["input_min"]), x))
        return math.log1p(x) / math.log1p(den)
    if typ == "sentinel_divide_clamp":
        if sentinel == spec["sentinel"]:
            return float(spec["sentinel_value"])
        x = float(value or 0.0)
        div = resolve_ref(spec, "divisor", constants)
        return min(float(spec["max"]), max(float(spec["min"]), x / div))
    raise ValueError(f"Unsupported normalizer type {typ}")


def pack_bits_lsb_first(bits: Iterable[bool], bit_count: int) -> bytes:
    values = list(bits)
    if len(values) != bit_count:
        raise ValueError(f"Expected {bit_count} bits, got {len(values)}")
    out = bytearray((bit_count + 7) // 8)
    for i, flag in enumerate(values):
        if flag:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def _parse_array_type(type_name: str, prefix: str) -> int:
    match = re.fullmatch(rf"{re.escape(prefix)}\[(\d+)\]", type_name)
    if not match:
        raise ValueError(f"unsupported type {type_name}")
    return int(match.group(1))


def _pack_unsigned(value: int, type_name: str, byte_order: str = "little") -> bytes:
    formats = {
        ("uint8", "little"): "<B", ("uint16", "little"): "<H", ("uint32", "little"): "<I", ("uint64", "little"): "<Q",
        ("uint8", "big"): ">B", ("uint16", "big"): ">H", ("uint32", "big"): ">I", ("uint64", "big"): ">Q",
    }
    if (type_name, byte_order) not in formats:
        raise ValueError(f"unsupported integer type/order {type_name}/{byte_order}")
    return struct.pack(formats[(type_name, byte_order)], int(value))


def target_handle_bytes(handle: dict[str, int], field_order: list[str], byte_order: str = "little") -> bytes:
    raw = bytearray()
    for descriptor in field_order:
        name, type_name = descriptor.split(":", 1)
        raw += _pack_unsigned(int(handle[name]), type_name, byte_order)
    return bytes(raw)


def _hex_digest_bytes(value: str, expected_size: int, name: str) -> bytes:
    raw = bytes.fromhex(value)
    if len(raw) != expected_size:
        raise ValueError(f"{name} must be {expected_size} bytes")
    return raw


def candidate_set_canonical_bytes(
    schema: dict[str, Any],
    schema_source_sha256_hex: str,
    target_handles: list[dict[str, int]],
    target_mask: list[bool],
    candidate_mask: list[bool],
) -> bytes:
    contract = schema["hash_contract"]["candidate_set_hash"]
    constants = schema["constants"]
    byte_order = contract["byte_order"]
    raw = bytearray()
    for field in contract["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            size = _parse_array_type(typ, "bytes")
            value = field["value_ascii"].encode("ascii")
            if len(value) != size:
                raise ValueError("magic size mismatch")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, byte_order)
        elif name == "schema_source_sha256":
            raw += _hex_digest_bytes(schema_source_sha256_hex, _parse_array_type(typ, "bytes"), name)
        elif name == "target_slot_count":
            raw += _pack_unsigned(constants[field["value_ref"]], typ, byte_order)
        elif name == "target_handles":
            count = _parse_array_type(typ, "target_handle")
            if len(target_handles) != count:
                raise ValueError(f"target_handles must contain {count} rows")
            for handle in target_handles:
                raw += target_handle_bytes(handle, field["field_order"], byte_order)
        elif name == "target_mask":
            if len(target_mask) != int(field["bit_count"]):
                raise ValueError("target_mask bit count mismatch")
            raw += pack_bits_lsb_first(target_mask, int(field["bit_count"]))
        elif name == "candidate_mask":
            if len(candidate_mask) != int(field["bit_count"]):
                raise ValueError("candidate_mask bit count mismatch")
            raw += pack_bits_lsb_first(candidate_mask, int(field["bit_count"]))
        else:
            raise ValueError(f"unsupported candidate hash field {name}")
    return bytes(raw)


def candidate_set_hash(*args: Any, **kwargs: Any) -> str:
    return hashlib.sha256(candidate_set_canonical_bytes(*args, **kwargs)).hexdigest()


def decision_contract_canonical_bytes(schema: dict[str, Any], digests: dict[str, str]) -> bytes:
    contract = schema["hash_contract"]["decision_contract_hash"]
    raw = bytearray()
    byte_order = contract["byte_order"]
    for field in contract["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            size = _parse_array_type(typ, "bytes")
            value = field["value_ascii"].encode("ascii")
            if len(value) != size:
                raise ValueError("decision magic size mismatch")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, byte_order)
        else:
            raw += _hex_digest_bytes(digests[name], _parse_array_type(typ, "bytes"), name)
    return bytes(raw)


def decision_contract_hash(schema: dict[str, Any], digests: dict[str, str]) -> str:
    return hashlib.sha256(decision_contract_canonical_bytes(schema, digests)).hexdigest()

