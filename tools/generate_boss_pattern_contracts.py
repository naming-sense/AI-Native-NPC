#!/usr/bin/env python3
"""Generate the optional Boss Pattern Selector Python/C++/Markdown contract bindings."""
from __future__ import annotations

import json
import keyword
import re
from typing import Any


def _py_identifier(value: str) -> str:
    ident = re.sub(r"\W", "_", value)
    if not ident or ident[0].isdigit():
        ident = "_" + ident
    if keyword.iskeyword(ident) or ident in {"None", "True", "False"}:
        ident += "_"
    return ident


def _cpp_identifier(value: str) -> str:
    ident = re.sub(r"\W", "_", value)
    return "_" + ident if not ident or ident[0].isdigit() else ident


def _bytes_literal(hex_string: str) -> str:
    return ", ".join(f"0x{value:02x}" for value in bytes.fromhex(hex_string))


def _ascii_literal(value: str) -> str:
    return ", ".join(str(byte) for byte in value.encode("ascii"))


def _resolved_normalizer_rows(contract: dict[str, Any], tensor_name: str) -> list[dict[str, Any]]:
    definitions = contract["normalization_contract"]["definitions"]
    assignments = contract["normalization_contract"]["assignments"][tensor_name]
    field_to_normalizer = {
        field_name: normalizer_name
        for normalizer_name, field_names in assignments.items()
        for field_name in field_names
    }
    rows: list[dict[str, Any]] = []
    for field in contract["tensors"][tensor_name]["fields"]:
        normalizer_name = field_to_normalizer[field["name"]]
        spec = definitions[normalizer_name]
        divisor = spec.get("divisor")
        if "divisor_ref" in spec:
            divisor = contract["constants"][spec["divisor_ref"]]
        rows.append({
            "index": field["index"],
            "field": field["name"],
            "normalizer": normalizer_name,
            "kind": spec["kind"],
            "min": float(spec["min"]),
            "max": float(spec["max"]),
            "divisor": float(divisor),
            "value": float(spec.get("value", 0.0)),
        })
    return rows


def _cpp_float(value: float) -> str:
    text = repr(float(value))
    if "e" not in text.lower() and "." not in text:
        text += ".0"
    return text + "f"


def generate_boss_python(contract: dict[str, Any], source_sha256: str, generator_version: str) -> str:
    constants = contract["constants"]
    tensors = contract["tensors"]
    outputs = contract["outputs"]
    candidate_hash = contract["hash_contract"]["pattern_candidate_set_hash"]
    decision_hash = contract["hash_contract"]["boss_pattern_decision_contract_hash"]
    normalizer_rows = {
        tensor_name: _resolved_normalizer_rows(contract, tensor_name)
        for tensor_name in ("pattern_context", "pattern_features", "pattern_pair_features")
    }
    parts = [
        f'"""AUTO-GENERATED. DO NOT EDIT. Boss Pattern contract {contract["contract"]["version"]}."""',
        "from __future__ import annotations",
        "from dataclasses import dataclass",
        "from enum import IntEnum",
        "from typing import Mapping",
        "import hashlib, math, re, struct",
        "",
        f"GENERATOR_VERSION = {generator_version!r}",
        f"BOSS_PATTERN_CONTRACT_SHA256 = {source_sha256!r}",
        f"CONTRACT_VERSION = {contract['contract']['version']!r}",
        f"CONTRACT_REVISION = {contract['contract']['contract_revision']!r}",
        f"CONSTANTS = {constants!r}",
        f"TENSOR_SHAPES = { {name: spec['shape'] for name, spec in tensors.items()}!r}",
        f"TENSOR_DTYPES = { {name: spec['dtype'] for name, spec in tensors.items()}!r}",
        f"OUTPUT_SHAPES = { {name: spec['shape'] for name, spec in outputs.items()}!r}",
        f"OUTPUT_DTYPES = { {name: spec['dtype'] for name, spec in outputs.items()}!r}",
        f"PATTERN_PARAMETERS = {outputs['pattern_parameter_proposals']['parameters']!r}",
        f"PATTERN_FORBIDDEN_OUTPUTS = {outputs['pattern_parameter_proposals']['forbidden_outputs']!r}",
        f"FEATURE_NORMALIZERS = {normalizer_rows!r}",
        f"PADDING_CONTRACT = {contract['normalization_contract']['padding']!r}",
        f"PATTERN_CANDIDATE_HASH_CONTRACT = {candidate_hash!r}",
        f"BOSS_PATTERN_DECISION_HASH_CONTRACT = {decision_hash!r}",
        "",
    ]
    for class_name, enum_name in [
        ("SelectionBoundary", "selection_boundary"),
        ("ExecutionPhase", "execution_phase"),
        ("InterruptKind", "interrupt_kind"),
        ("PatternMaskReason", "mask_reason"),
    ]:
        parts.append(f"class {class_name}(IntEnum):")
        parts.extend(f"    {_py_identifier(row['name'])} = {row['id']}" for row in contract["enums"][enum_name])
        parts.append("")
    for class_name, tensor_name in [
        ("PatternContextFeature", "pattern_context"),
        ("PatternFeature", "pattern_features"),
        ("PatternPairFeature", "pattern_pair_features"),
    ]:
        parts.append(f"class {class_name}(IntEnum):")
        parts.extend(f"    {_py_identifier(row['name'])} = {row['index']}" for row in tensors[tensor_name]["fields"])
        parts.append("")
    parts.append("class PatternParameter(IntEnum):")
    parts.extend(f"    {_py_identifier(row['name'])} = {row['index']}" for row in outputs["pattern_parameter_proposals"]["parameters"])
    parts.append("")

    parts.extend(r'''
def normalize_feature(tensor_name: str, field_index: int, value: float) -> float:
    rows = FEATURE_NORMALIZERS.get(tensor_name)
    if rows is None or not 0 <= field_index < len(rows):
        raise ValueError("unknown tensor or field index")
    if not math.isfinite(value):
        raise ValueError("non-finite Boss Pattern feature")
    spec = rows[field_index]
    if spec["kind"] == "constant":
        return float(spec["value"])
    normalized = value / float(spec["divisor"]) if spec["kind"] == "divide_clamp" else value
    return min(max(normalized, float(spec["min"])), float(spec["max"]))


'''.strip("\n").splitlines())
    parts.append("")

    parts.extend(r'''
@dataclass(frozen=True)
class TargetHandle:
    kind: int
    stable_id: int
    generation: int
    revision: int


def _array_count(type_name: str, prefix: str) -> int:
    match = re.fullmatch(re.escape(prefix) + r"\[(\d+)\]", type_name)
    if not match:
        raise ValueError(f"unsupported type {type_name}")
    return int(match.group(1))


def _pack_unsigned(value: int, type_name: str, byte_order: str = "little") -> bytes:
    formats = {
        ("uint8", "little"): "<B", ("uint16", "little"): "<H", ("uint32", "little"): "<I", ("uint64", "little"): "<Q",
        ("uint8", "big"): ">B", ("uint16", "big"): ">H", ("uint32", "big"): ">I", ("uint64", "big"): ">Q",
    }
    try:
        return struct.pack(formats[(type_name, byte_order)], int(value))
    except KeyError as exc:
        raise ValueError(f"unsupported integer type/order {type_name}/{byte_order}") from exc


def _digest_bytes(value: str, size: int, name: str) -> bytes:
    raw = bytes.fromhex(value)
    if len(raw) != size:
        raise ValueError(f"{name} must be {size} bytes")
    return raw


def _pack_mask(bits: list[bool], bit_count: int) -> bytes:
    if len(bits) != bit_count:
        raise ValueError(f"expected {bit_count} mask bits")
    out = bytearray((bit_count + 7) // 8)
    for index, value in enumerate(bits):
        if value:
            out[index // 8] |= 1 << (index % 8)
    return bytes(out)


def _target_handle_bytes(handle: TargetHandle, field_order: list[str], byte_order: str) -> bytes:
    values = {"kind": handle.kind, "stable_id": handle.stable_id, "generation": handle.generation, "revision": handle.revision}
    return b"".join(_pack_unsigned(values[name], dtype, byte_order) for name, dtype in (row.split(":", 1) for row in field_order))


def validate_pattern_slot_layout(pattern_ids: list[int], pattern_mask: list[bool]) -> None:
    count = int(CONSTANTS["max_pattern_slots"])
    if len(pattern_ids) != count or len(pattern_mask) != count:
        raise ValueError(f"Boss Pattern layout must contain {count} rows")
    invalid = int(CONSTANTS["invalid_pattern_id"])
    seen_padding = False
    previous = -1
    for index, (pattern_id, mask_value) in enumerate(zip(pattern_ids, pattern_mask, strict=True)):
        if not isinstance(mask_value, bool):
            raise ValueError(f"pattern_mask row {index} must be bool")
        if isinstance(pattern_id, bool) or not isinstance(pattern_id, int) or not 0 <= pattern_id <= invalid:
            raise ValueError(f"pattern_id row {index} is outside uint16")
        if pattern_id == invalid:
            seen_padding = True
            if bool(mask_value):
                raise ValueError(f"padding row {index} cannot be valid")
            continue
        if seen_padding:
            raise ValueError(f"occupied pattern row {index} appears after padding")
        if pattern_id <= previous:
            raise ValueError("occupied pattern_ids must be strictly ascending")
        previous = pattern_id
    if previous < 0:
        raise ValueError("Boss Pattern layout must contain at least one occupied row")


def pattern_candidate_set_canonical_bytes(
    pattern_asset_bundle_sha256: str,
    pattern_ids: list[int],
    pattern_mask: list[bool],
    attack_target_handle: TargetHandle,
    selection_boundary: int,
    boss_phase_revision: int,
    combat_state_revision: int,
) -> bytes:
    validate_pattern_slot_layout(pattern_ids, pattern_mask)
    contract = PATTERN_CANDIDATE_HASH_CONTRACT
    raw = bytearray()
    for field in contract["fields"]:
        name, type_name = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(type_name, "bytes"):
                raise ValueError("pattern candidate magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], type_name, contract["byte_order"])
        elif name == "boss_pattern_contract_sha256":
            raw += _digest_bytes(BOSS_PATTERN_CONTRACT_SHA256, _array_count(type_name, "bytes"), name)
        elif name == "pattern_asset_bundle_sha256":
            raw += _digest_bytes(pattern_asset_bundle_sha256, _array_count(type_name, "bytes"), name)
        elif name == "pattern_slot_count":
            raw += _pack_unsigned(CONSTANTS[field["value_ref"]], type_name, contract["byte_order"])
        elif name == "pattern_ids":
            count = _array_count(type_name, "uint16")
            if len(pattern_ids) != count:
                raise ValueError(f"pattern_ids must contain {count} rows")
            for pattern_id in pattern_ids:
                raw += _pack_unsigned(pattern_id, "uint16", contract["byte_order"])
        elif name == "pattern_mask":
            raw += _pack_mask(pattern_mask, int(field["bit_count"]))
        elif name == "attack_target_handle":
            raw += _target_handle_bytes(attack_target_handle, field["field_order"], contract["byte_order"])
        elif name == "selection_boundary":
            SelectionBoundary(int(selection_boundary))
            raw += _pack_unsigned(selection_boundary, type_name, contract["byte_order"])
        elif name == "boss_phase_revision":
            raw += _pack_unsigned(boss_phase_revision, type_name, contract["byte_order"])
        elif name == "combat_state_revision":
            raw += _pack_unsigned(combat_state_revision, type_name, contract["byte_order"])
        else:
            raise ValueError(f"unsupported boss pattern candidate hash field {name}")
    return bytes(raw)


def pattern_candidate_set_hash(*args, **kwargs) -> str:
    return hashlib.sha256(pattern_candidate_set_canonical_bytes(*args, **kwargs)).hexdigest()


def boss_pattern_decision_contract_canonical_bytes(digests: Mapping[str, str]) -> bytes:
    contract = BOSS_PATTERN_DECISION_HASH_CONTRACT
    raw = bytearray()
    for field in contract["fields"]:
        name, type_name = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(type_name, "bytes"):
                raise ValueError("boss pattern decision magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], type_name, contract["byte_order"])
        elif name == "boss_pattern_contract_sha256":
            raw += _digest_bytes(BOSS_PATTERN_CONTRACT_SHA256, _array_count(type_name, "bytes"), name)
        else:
            raw += _digest_bytes(digests[name], _array_count(type_name, "bytes"), name)
    return bytes(raw)


def boss_pattern_decision_contract_hash(digests: Mapping[str, str]) -> str:
    return hashlib.sha256(boss_pattern_decision_contract_canonical_bytes(digests)).hexdigest()
'''.strip("\n").splitlines())
    parts.append("")
    return "\n".join(parts)


def _cpp_enum(class_name: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"enum class {class_name} : std::uint8_t {{"]
    lines.extend(f"    {_cpp_identifier(row['name'])} = {row['id']}," for row in rows)
    lines.append("};")
    return lines


def _cpp_feature_enum(class_name: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"enum class {class_name} : std::uint16_t {{"]
    lines.extend(f"    {_cpp_identifier(row['name'])} = {row['index']}," for row in rows)
    lines.append("};")
    return lines


def generate_boss_cpp(contract: dict[str, Any], source_sha256: str, generator_version: str) -> str:
    constants = contract["constants"]
    candidate = contract["hash_contract"]["pattern_candidate_set_hash"]
    decision = contract["hash_contract"]["boss_pattern_decision_contract_hash"]
    candidate_fields = {row["name"]: row for row in candidate["fields"]}
    decision_fields = {row["name"]: row for row in decision["fields"]}
    decision_digest_names = [row["name"] for row in decision["fields"] if row["name"] not in {"magic", "serialization_version", "boss_pattern_contract_sha256"}]
    normalizer_rows = {
        tensor_name: _resolved_normalizer_rows(contract, tensor_name)
        for tensor_name in ("pattern_context", "pattern_features", "pattern_pair_features")
    }
    digest_members = {
        "pattern_model_sha256": "PatternModel",
        "pattern_normalization_contract_sha256": "PatternNormalizationContract",
        "pattern_postprocess_contract_sha256": "PatternPostprocessContract",
        "pattern_calibration_ood_asset_sha256": "PatternCalibrationOodAsset",
        "pattern_executor_contract_sha256": "PatternExecutorContract",
    }
    lines = [
        "// AUTO-GENERATED. DO NOT EDIT.",
        "#pragma once",
        '#include "AINativeNPCContracts.generated.h"',
        "#include <algorithm>", "#include <array>", "#include <cmath>", "#include <cstddef>", "#include <cstdint>", "#include <string>", "#include <vector>", "",
        "namespace AINativeNPC::BossPatternV1 {",
        f'inline constexpr const char* GeneratorVersion = "{generator_version}";',
        f'inline constexpr const char* ContractVersion = "{contract["contract"]["version"]}";',
        f'inline constexpr const char* ContractRevision = "{contract["contract"]["contract_revision"]}";',
        f'inline constexpr const char* BossPatternContractSha256 = "{source_sha256}";',
        f'inline constexpr std::array<std::uint8_t, 32> BossPatternContractSha256Bytes{{{{{_bytes_literal(source_sha256)}}}}};',
        f"inline constexpr std::size_t MaxPatternSlots = {constants['max_pattern_slots']};",
        f"inline constexpr std::size_t PatternContextFeatureCount = {constants['pattern_context_feature_count']};",
        f"inline constexpr std::size_t PatternFeatureCount = {constants['pattern_feature_count']};",
        f"inline constexpr std::size_t PatternPairFeatureCount = {constants['pattern_pair_feature_count']};",
        f"inline constexpr std::size_t PatternParameterCount = {constants['pattern_parameter_count']};",
        f"inline constexpr std::uint16_t InvalidPatternId = {constants['invalid_pattern_id']}U;",
        f"inline constexpr std::array<std::uint8_t, 8> PatternCandidateHashMagic{{{{{_ascii_literal(candidate_fields['magic']['value_ascii'])}}}}};",
        f"inline constexpr std::uint16_t PatternCandidateHashSerializationVersion = {candidate_fields['serialization_version']['value']}U;",
        f"inline constexpr std::array<std::uint8_t, 8> BossPatternDecisionHashMagic{{{{{_ascii_literal(decision_fields['magic']['value_ascii'])}}}}};",
        f"inline constexpr std::uint16_t BossPatternDecisionHashSerializationVersion = {decision_fields['serialization_version']['value']}U;",
        "",
    ]
    for class_name, enum_name in [
        ("ESelectionBoundary", "selection_boundary"),
        ("EExecutionPhase", "execution_phase"),
        ("EInterruptKind", "interrupt_kind"),
        ("EPatternMaskReason", "mask_reason"),
    ]:
        lines.extend(_cpp_enum(class_name, contract["enums"][enum_name]))
        lines.append("")
    for class_name, tensor_name in [
        ("EPatternContextFeature", "pattern_context"),
        ("EPatternFeature", "pattern_features"),
        ("EPatternPairFeature", "pattern_pair_features"),
    ]:
        lines.extend(_cpp_feature_enum(class_name, contract["tensors"][tensor_name]["fields"]))
        lines.append("")
    lines.extend(_cpp_feature_enum("EPatternParameter", contract["outputs"]["pattern_parameter_proposals"]["parameters"]))
    lines.append("")

    lines.extend([
        "enum class ENormalizerKind : std::uint8_t { Clamp = 0, DivideClamp = 1, Constant = 2 };",
        "struct FNormalizerSpec {",
        "    ENormalizerKind Kind;",
        "    float Min;",
        "    float Max;",
        "    float Divisor;",
        "    float ConstantValue;",
        "};", "",
    ])
    normalizer_kind_names = {"clamp": "Clamp", "divide_clamp": "DivideClamp", "constant": "Constant"}
    for tensor_name, array_name in [
        ("pattern_context", "PatternContextNormalizers"),
        ("pattern_features", "PatternFeatureNormalizers"),
        ("pattern_pair_features", "PatternPairFeatureNormalizers"),
    ]:
        rows = normalizer_rows[tensor_name]
        lines.append(f"inline constexpr std::array<FNormalizerSpec, {len(rows)}> {array_name}{{{{")
        for row in rows:
            lines.append(
                "    {ENormalizerKind::%s, %s, %s, %s, %s}," % (
                    normalizer_kind_names[row["kind"]], _cpp_float(row["min"]), _cpp_float(row["max"]),
                    _cpp_float(row["divisor"]), _cpp_float(row["value"]),
                )
            )
        lines.extend(["}};", ""])
    lines.extend([
        "inline bool TryNormalizeFeature(float Input, const FNormalizerSpec& Spec, float& Out) {",
        "    if (!std::isfinite(Input)) return false;",
        "    if (Spec.Kind == ENormalizerKind::Constant) { Out = Spec.ConstantValue; return true; }",
        "    const float Value = Spec.Kind == ENormalizerKind::DivideClamp ? Input / Spec.Divisor : Input;",
        "    Out = std::clamp(Value, Spec.Min, Spec.Max);",
        "    return true;",
        "}", "",
    ])

    lines.extend([
        "inline bool IsPatternSlotLayoutValid(const std::array<std::uint16_t, MaxPatternSlots>& PatternIds, const std::array<bool, MaxPatternSlots>& PatternMask) {",
        "    bool SeenPadding = false;",
        "    std::uint16_t Previous = 0;",
        "    bool HasPrevious = false;",
        "    for (std::size_t Index = 0; Index < MaxPatternSlots; ++Index) {",
        "        const auto PatternId = PatternIds[Index];",
        "        if (PatternId >= InvalidPatternId) { SeenPadding = true; if (PatternMask[Index]) return false; continue; }",
        "        if (SeenPadding || (HasPrevious && PatternId <= Previous)) return false;",
        "        Previous = PatternId; HasPrevious = true;",
        "    }",
        "    return HasPrevious;",
        "}", "",
        "struct FBossPatternDecisionDigests {",
        *[f"    std::array<std::uint8_t, 32> {digest_members[name]}{{}};" for name in decision_digest_names],
        "};", "",
        "inline std::vector<std::uint8_t> PatternCandidateSetCanonicalBytes(",
        "    const std::array<std::uint8_t, 32>& PatternAssetBundleSha256,",
        "    const std::array<std::uint16_t, MaxPatternSlots>& PatternIds,",
        "    const std::array<bool, MaxPatternSlots>& PatternMask,",
        "    const SchemaV2::FTargetHandleWire& AttackTargetHandle,",
        "    ESelectionBoundary SelectionBoundary,",
        "    std::uint64_t BossPhaseRevision,",
        "    std::uint64_t CombatStateRevision) {",
        "    if (!IsPatternSlotLayoutValid(PatternIds, PatternMask)) return {};",
        "    std::vector<std::uint8_t> Out;",
    ])
    for field in candidate["fields"]:
        name = field["name"]
        if name == "magic":
            lines.append("    Out.insert(Out.end(), PatternCandidateHashMagic.begin(), PatternCandidateHashMagic.end());")
        elif name == "serialization_version":
            lines.append("    SchemaV2::AppendLittleEndian<std::uint16_t>(Out, PatternCandidateHashSerializationVersion);")
        elif name == "boss_pattern_contract_sha256":
            lines.append("    Out.insert(Out.end(), BossPatternContractSha256Bytes.begin(), BossPatternContractSha256Bytes.end());")
        elif name == "pattern_asset_bundle_sha256":
            lines.append("    Out.insert(Out.end(), PatternAssetBundleSha256.begin(), PatternAssetBundleSha256.end());")
        elif name == "pattern_slot_count":
            lines.append("    Out.push_back(static_cast<std::uint8_t>(MaxPatternSlots));")
        elif name == "pattern_ids":
            lines.append("    for (const auto PatternId : PatternIds) SchemaV2::AppendLittleEndian<std::uint16_t>(Out, PatternId);")
        elif name == "pattern_mask":
            lines.extend(["    const auto PackedPatternMask = SchemaV2::PackBitsLSBFirst(PatternMask);", "    Out.insert(Out.end(), PackedPatternMask.begin(), PackedPatternMask.end());"])
        elif name == "attack_target_handle":
            lines.append("    SchemaV2::AppendTargetHandle(Out, AttackTargetHandle);")
        elif name == "selection_boundary":
            lines.append("    Out.push_back(static_cast<std::uint8_t>(SelectionBoundary));")
        elif name == "boss_phase_revision":
            lines.append("    SchemaV2::AppendLittleEndian<std::uint64_t>(Out, BossPhaseRevision);")
        elif name == "combat_state_revision":
            lines.append("    SchemaV2::AppendLittleEndian<std::uint64_t>(Out, CombatStateRevision);")
        else:
            raise ValueError(name)
    lines.extend(["    return Out;", "}", ""])

    lines.extend([
        "inline std::vector<std::uint8_t> BossPatternDecisionContractCanonicalBytes(const FBossPatternDecisionDigests& Digests) {",
        "    std::vector<std::uint8_t> Out;",
    ])
    for field in decision["fields"]:
        name = field["name"]
        if name == "magic":
            lines.append("    Out.insert(Out.end(), BossPatternDecisionHashMagic.begin(), BossPatternDecisionHashMagic.end());")
        elif name == "serialization_version":
            lines.append("    SchemaV2::AppendLittleEndian<std::uint16_t>(Out, BossPatternDecisionHashSerializationVersion);")
        elif name == "boss_pattern_contract_sha256":
            lines.append("    Out.insert(Out.end(), BossPatternContractSha256Bytes.begin(), BossPatternContractSha256Bytes.end());")
        else:
            member = digest_members[name]
            lines.append(f"    Out.insert(Out.end(), Digests.{member}.begin(), Digests.{member}.end());")
    lines.extend([
        "    return Out;", "}", "",
        "inline std::string PatternCandidateSetHashHex(const std::array<std::uint8_t, 32>& AssetHash, const std::array<std::uint16_t, MaxPatternSlots>& PatternIds, const std::array<bool, MaxPatternSlots>& PatternMask, const SchemaV2::FTargetHandleWire& Target, ESelectionBoundary Boundary, std::uint64_t PhaseRevision, std::uint64_t CombatRevision) { const auto Bytes = PatternCandidateSetCanonicalBytes(AssetHash, PatternIds, PatternMask, Target, Boundary, PhaseRevision, CombatRevision); return Bytes.empty() ? std::string{} : SchemaV2::HexLower(SchemaV2::Sha256(Bytes)); }",
        "inline std::string BossPatternDecisionContractHashHex(const FBossPatternDecisionDigests& Digests) { return SchemaV2::HexLower(SchemaV2::Sha256(BossPatternDecisionContractCanonicalBytes(Digests))); }",
        "", "static_assert(MaxPatternSlots == 32);", "static_assert(SchemaV2::CandidateCount == 272);",
        "", "} // namespace AINativeNPC::BossPatternV1", "",
    ])
    return "\n".join(lines)


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def generate_boss_markdown(contract: dict[str, Any], source_sha256: str, generator_version: str) -> str:
    lines = [
        "# BP. AUTO-GENERATED Boss Pattern Selector 계약", "",
        "> 이 구간은 `contracts/current/boss_pattern_contract_v1.yaml`에서 자동 생성된다. 수동 편집하지 않는다.", "",
        f"- Generator: `{generator_version}`",
        f"- Contract version: `{contract['contract']['version']}`",
        f"- Contract revision: `{contract['contract']['contract_revision']}`",
        f"- Boss Pattern Contract SHA-256: `{source_sha256}`", "",
        "## BP.1 공통 Candidate 보존", "",
        "| Skill | Target Slots | 공통 Candidate | Boss Pattern Slots |", "|---:|---:|---:|---:|",
        f"| 16 | 17 | 272 | {contract['constants']['max_pattern_slots']} |", "",
        "Boss Pattern Slot은 `Attack(Entity)` Commit 이후 사용하는 별도 namespace다.",
        "hash 직렬화 전에 occupied row 1개 이상, occupied `pattern_id` 오름차순·trailing padding·padding mask=false를 검증한다.", "",
        "## BP.2 Tensor", "", "| Name | Shape | dtype |", "|---|---|---|",
    ]
    for name, spec in contract["tensors"].items():
        lines.append(f"| `{name}` | `{_compact(spec['shape'])}` | `{spec['dtype']}` |")
    for name, spec in contract["outputs"].items():
        lines.append(f"| `{name}` | `{_compact(spec['shape'])}` | `{spec['dtype']}` |")
    lines.extend(["", "### BP.2.1 Feature 정규화", ""])
    for tensor_name in ("pattern_context", "pattern_features", "pattern_pair_features"):
        fields = contract["tensors"][tensor_name]["fields"]
        normalizers = _resolved_normalizer_rows(contract, tensor_name)
        lines.extend([f"#### `{tensor_name}`", "", "| Index | Field | Source | Normalizer | Range | Divisor |", "|---:|---|---|---|---|---:|"])
        for field, normalizer in zip(fields, normalizers, strict=True):
            lines.append(
                f"| {field['index']} | `{field['name']}` | `{field['source']}` | `{normalizer['normalizer']}` "
                f"| `[{normalizer['min']},{normalizer['max']}]` | {normalizer['divisor']} |"
            )
        lines.append("")
    lines.extend([
        "Padding: unoccupied `pattern_features`와 `pattern_pair_features` row는 정규화 후 전부 0, `pattern_id=invalid_pattern_id`, `pattern_mask=false`다.",
        "Masked score는 ranking 전에 `-∞`로 바꾸고 parameter proposal은 무시한 뒤 log에서 0으로 고정한다.", "",
    ])
    parameters = contract["outputs"]["pattern_parameter_proposals"]["parameters"]
    lines.extend(["", "## BP.3 제한된 Parameter 권한", "", "| Index | Name | Decode | Authority |", "|---:|---|---|---|"])
    for parameter in parameters:
        lines.append(f"| {parameter['index']} | `{parameter['name']}` | `{parameter['decode']}` | `{parameter['authority']}` |")
    lines.extend(["", "신경망 출력에서 금지: " + ", ".join(f"`{name}`" for name in contract["outputs"]["pattern_parameter_proposals"]["forbidden_outputs"]), ""])
    lines.extend(["## BP.4 Selection Boundary와 실행 잠금", "", "| Phase | Rule |", "|---|---|"])
    for phase, rule in contract["selection_lock_contract"]["phase_rules"].items():
        lines.append(f"| `{phase}` | `{rule}` |")
    hidden = contract["hidden_information_contract"]
    authority = contract["authority_contract"]
    lines.extend([
        "", "Model selection source: `" + hidden["allowed_target_source"] + "`",
        "Executor post-lock transform source: `" + hidden["post_lock_executor_target_transform_source"] + "`",
        "Executor transform feedback to model: `" + str(hidden["post_lock_executor_transform_fed_back_to_model"]).lower() + "`",
        "Executor transform may change Pattern: `" + str(hidden["post_lock_executor_transform_may_change_pattern"]).lower() + "`",
        "Pattern Commit authority: `" + authority["pattern_commit"] + "`",
        "Hitbox/Damage/Root Motion authority: `" + authority["hitbox_damage_root_motion"] + "`",
        "Client inference Gameplay authority: `" + str(authority["client_inference_gameplay_authority"]).lower() + "`", "",
    ])
    lines.extend(["## BP.5 Hard Mask 순서", ""])
    lines.extend(f"{index}. `{rule}`" for index, rule in enumerate(contract["hard_mask_contract"]["rules_in_order"], 1))
    lines.extend(["", "## BP.6 Pattern Set·Data Asset", "", "### BP.6.1 Pattern Set 필수 필드", ""])
    lines.extend(f"- `{name}`" for name in contract["pattern_set_asset_contract"]["required_fields"])
    lines.extend(["", "### BP.6.2 Pattern 필수 필드", ""])
    lines.extend(f"- `{name}`" for name in contract["pattern_asset_contract"]["required_fields"])
    fallback = contract["fallback_contract"]
    lines.extend([
        "", "### BP.6.3 Fallback 결정론", "",
        f"- zero valid rows: `{fallback['zero_valid_rows']}`",
        f"- Utility tie-break: `{fallback['utility_tie_break']}`",
        f"- safe default source: `{fallback['authored_safe_default_source']}`",
        f"- safe default constraint: `{fallback['authored_safe_default_constraint']}`",
        f"- snapshot: `{fallback['fallback_snapshot_policy']}`", "",
    ])
    bundle_digest = contract["pattern_asset_bundle_digest_contract"]
    lines.extend([
        "## BP.7 Hash 계약", "", "### BP.7.0 Pattern Asset Bundle Digest", "",
        f"- status: `{bundle_digest['status']}`",
        f"- build owner: `{bundle_digest['build_owner']}`",
        f"- Pattern Set ID digest input: `{_compact(bundle_digest['pattern_set_id_digest'])}`",
        f"- Pattern definition canonicalization: `{bundle_digest['pattern_definition_digest']['canonicalization']}`",
        f"- Asset reference substitution: `{_compact(bundle_digest['pattern_definition_digest']['asset_reference_substitution'])}`",
        "", "| Order | Name | Type | Contract |", "|---:|---|---|---|",
    ])
    for index, field in enumerate(bundle_digest["canonical_manifest"]["fields"]):
        details = {key: value for key, value in field.items() if key not in {"name", "type"}}
        lines.append(f"| {index} | `{field['name']}` | `{field['type']}` | `{_compact(details)}` |")
    lines.append("")
    for name, spec in contract["hash_contract"].items():
        lines.extend([f"### BP.7.{name}", "", "| Order | Name | Type | Contract |", "|---:|---|---|---|"])
        for index, field in enumerate(spec["fields"]):
            details = {key: value for key, value in field.items() if key not in {"name", "type"}}
            lines.append(f"| {index} | `{field['name']}` | `{field['type']}` | `{_compact(details)}` |")
        lines.append("")
    lines.extend(["## BP.8 Release 상태", "", "| Gate | Status |", "|---|---|"])
    for name, status in contract["release_status"].items():
        lines.append(f"| `{name}` | `{status}` |")
    lines.append("")
    return "\n".join(lines)
