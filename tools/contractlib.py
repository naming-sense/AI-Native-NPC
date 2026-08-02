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
    test_taxonomy: Path


def default_paths(root: Path) -> ContractPaths:
    current = root / "contracts/current"
    return ContractPaths(
        root=root,
        schema=current / "ai_native_npc_schema_v2_0.yaml",
        skill_registry=current / "skill_registry_v1.yaml",
        goal_registry=current / "goal_registry_v1.yaml",
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


def validate_contracts(paths: ContractPaths) -> list[str]:
    errors: list[str] = []
    try:
        schema, skills, goals = load_contracts(paths)
        taxonomy = load_yaml(paths.test_taxonomy)
    except Exception as exc:
        return [f"YAML parse/load failure: {exc}"]

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
    _expect(markdown_scope.get("mode") == "all_locked_non_archive_markdown", "documentation semantic markdown scope mode mismatch", errors)
    _expect(markdown_scope.get("exclude_prefixes") == ["docs/archive/", "contracts/archive/", "manifests/archive/", "generated/docs/"], "documentation semantic markdown exclude prefixes mismatch", errors)
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

