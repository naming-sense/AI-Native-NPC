#!/usr/bin/env python3
"""Generate deterministic Python/C++ bindings and normative Markdown from YAML contracts."""
from __future__ import annotations

import argparse
import json
import keyword
import re
import tempfile
from pathlib import Path
from typing import Any

from contractlib import TOOL_VERSION, critical_suite_metrics, default_paths, load_contracts, load_yaml, sha256_file, validate_contracts


def py_identifier(value: str) -> str:
    ident = re.sub(r"\W", "_", value)
    if not ident or ident[0].isdigit():
        ident = "_" + ident
    if keyword.iskeyword(ident) or ident in {"None", "True", "False"}:
        ident += "_"
    return ident


def cpp_identifier(value: str) -> str:
    ident = re.sub(r"\W", "_", value)
    if not ident or ident[0].isdigit():
        ident = "_" + ident
    return ident


def enum_class(name: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"class {name}(IntEnum):"]
    lines.extend(f"    {py_identifier(row['name'])} = {row['id']}" for row in rows)
    return "\n".join(lines) + "\n"


def feature_enum(name: str, rows: list[dict[str, Any]], index_key: str = "index") -> str:
    lines = [f"class {name}(IntEnum):"]
    lines.extend(f"    {py_identifier(row['name'])} = {row[index_key]}" for row in rows)
    return "\n".join(lines) + "\n"


def cpp_enum(name: str, rows: list[dict[str, Any]], underlying: str = "std::uint8_t") -> str:
    lines = [f"enum class {name} : {underlying} {{"]
    lines.extend(f"    {cpp_identifier(row['name'])} = {row['id']}," for row in rows)
    lines.append("};")
    return "\n".join(lines)


def cpp_feature_enum(name: str, rows: list[dict[str, Any]], index_key: str = "index") -> str:
    lines = [f"enum class {name} : std::uint16_t {{"]
    lines.extend(f"    {cpp_identifier(row['name'])} = {row[index_key]}," for row in rows)
    lines.append("};")
    return "\n".join(lines)


def _resolved(spec: dict[str, Any], key: str, constants: dict[str, Any], default: float = 0.0) -> float:
    if key in spec:
        return float(spec[key])
    ref = spec.get(f"{key}_ref")
    if ref is not None:
        return float(constants[ref])
    return float(default)


def compile_normalizer(spec: dict[str, Any], constants: dict[str, Any]) -> dict[str, Any]:
    typ = str(spec["type"])
    out: dict[str, Any] = {"type": typ, "min": 0.0, "max": 0.0, "p0": 0.0, "p1": 0.0, "p2": 0.0}
    if typ == "constant":
        out["p0"] = float(spec["value"])
    elif typ == "boolean":
        pass
    elif typ == "clamp":
        out["min"], out["max"] = float(spec["min"]), float(spec["max"])
    elif typ == "divide_clamp":
        out["min"], out["max"] = float(spec["min"]), float(spec["max"])
        out["p0"] = _resolved(spec, "divisor", constants)
    elif typ == "trigonometric":
        out["p0"] = 0.0 if spec["function"] == "sin" else 1.0
    elif typ == "log1p_ratio":
        out["p0"] = float(spec["input_min"])
        out["p1"] = _resolved(spec, "input_max", constants)
        out["p2"] = _resolved(spec, "denominator", constants)
    elif typ == "sentinel_divide_clamp":
        out["min"], out["max"] = float(spec["min"]), float(spec["max"])
        out["p0"] = _resolved(spec, "divisor", constants)
        out["p1"] = float(spec["sentinel_value"])
    else:
        raise ValueError(f"Unsupported normalizer: {typ}")
    return out


def normalizer_tables(schema: dict[str, Any]) -> dict[str, Any]:
    c = schema["constants"]
    t = schema["tensors"]
    return {
        "global": [compile_normalizer(x["normalizer"], c) for x in t["global_state"]["fields"]],
        "target_common": [compile_normalizer(x["normalizer"], c) for x in t["target_features"]["common_fields"]],
        "event": [compile_normalizer(x["normalizer"], c) for x in t["event_features"]["fields"]],
        "candidate_pair": [compile_normalizer(x["normalizer"], c) for x in t["candidate_pair_features"]["fields"]],
        "target_payload": {
            kind: [compile_normalizer(x["normalizer"], c) for x in rows]
            for kind, rows in schema["target_payload_features"].items()
        },
    }


def generate_python(schema: dict[str, Any], skills: dict[str, Any], goals: dict[str, Any], hashes: dict[str, str]) -> str:
    constants = schema["constants"]
    tensors = schema["tensors"]
    norms = normalizer_tables(schema)
    handle_order = [f"{row['name']}:{row['dtype']}" for row in schema["runtime_handle_contract"]["fields"]]
    parts = [
        f'"""AUTO-GENERATED. DO NOT EDIT. Schema {schema["schema"]["contract_revision"]} bindings."""',
        "from __future__ import annotations",
        "from dataclasses import dataclass",
        "from enum import IntEnum",
        "from typing import Mapping",
        "import hashlib, math, re, struct",
        "",
        f"GENERATOR_VERSION = {TOOL_VERSION!r}",
        f"SCHEMA_SOURCE_SHA256 = {hashes['schema']!r}",
        f"SKILL_REGISTRY_SHA256 = {hashes['skill_registry']!r}",
        f"GOAL_REGISTRY_SHA256 = {hashes['goal_registry']!r}",
        f"SCHEMA_VERSION = {schema['schema']['version']!r}",
        f"CONTRACT_REVISION = {schema['schema']['contract_revision']!r}",
        f"CONSTANTS = {constants!r}",
        f"TENSOR_SHAPES = { {k:v['shape'] for k,v in tensors.items()}!r}",
        f"TENSOR_DTYPES = { {k:v['dtype'] for k,v in tensors.items()}!r}",
        f"SCORE_CONTRACT = {schema['score_contract']!r}",
        f"COMMIT_VALIDATION = {schema['commit_validation']!r}",
        f"SKILL_PARAMETER_CONTRACTS = { {x['id']:x['parameters'] for x in skills['skills']}!r}",
        f"SKILL_ALLOWED_TARGET_KINDS = { {x['id']:x['allowed_target_kinds'] for x in skills['skills']}!r}",
        f"NORMALIZER_TABLES = {norms!r}",
        f"TARGET_HANDLE_FIELD_ORDER = {handle_order!r}",
        f"CANDIDATE_HASH_CONTRACT = {schema['hash_contract']['candidate_set_hash']!r}",
        f"DECISION_HASH_CONTRACT = {schema['hash_contract']['decision_contract_hash']!r}",
        "",
    ]
    enum_map = {
        "TargetKind": "target_kind", "SkillId": "skill", "GoalType": "goal_type",
        "GoalPhase": "goal_phase", "EventType": "event_type", "GoalSourcePriority": "goal_source_priority",
    }
    for cls, key in enum_map.items():
        parts.append(enum_class(cls, schema["enums"][key]))
    parts.append(feature_enum("GlobalFeature", tensors["global_state"]["fields"]))
    parts.append(feature_enum("TargetCommonFeature", tensors["target_features"]["common_fields"]))
    parts.append(feature_enum("EventFeature", tensors["event_features"]["fields"]))
    parts.append(feature_enum("CandidatePairFeature", tensors["candidate_pair_features"]["fields"]))
    for kind, rows in schema["target_payload_features"].items():
        parts.append(feature_enum(f"{kind}PayloadFeature", rows, "payload_index"))

    parts.extend(r'''
@dataclass(frozen=True)
class TargetHandle:
    kind: int
    stable_id: int
    generation: int
    revision: int

    def canonical_bytes(self) -> bytes:
        values = {"kind": self.kind, "stable_id": self.stable_id, "generation": self.generation, "revision": self.revision}
        return b"".join(_pack_unsigned(values[name], typ, CANDIDATE_HASH_CONTRACT["byte_order"]) for name, typ in (x.split(":", 1) for x in TARGET_HANDLE_FIELD_ORDER))


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
        fmt = formats[(type_name, byte_order)]
    except KeyError as exc:
        raise ValueError(f"unsupported integer type/order {type_name}/{byte_order}") from exc
    return struct.pack(fmt, int(value))


def _digest_bytes(value: str, size: int, name: str) -> bytes:
    raw = bytes.fromhex(value)
    if len(raw) != size:
        raise ValueError(f"{name} must be {size} bytes")
    return raw


def candidate_index(skill_id: int, target_slot: int) -> int:
    if not 0 <= skill_id < CONSTANTS["skill_count"]:
        raise ValueError("skill_id")
    if not 0 <= target_slot < CONSTANTS["total_target_slots"]:
        raise ValueError("target_slot")
    return skill_id * CONSTANTS["total_target_slots"] + target_slot


def round_half_away_from_zero(value: float) -> int:
    return int(math.floor(value + 0.5)) if value >= 0 else int(math.ceil(value - 0.5))


def quantize_confidence(value: float) -> int:
    x = min(1.0, max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_confidence_scale"])


def quantize_age_seconds(value: float) -> int:
    x = min(CONSTANTS["target_age_max_s"], max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_age_centisecond_scale"])


def quantize_distance_cm(value: float) -> int:
    x = min(CONSTANTS["spatial_max_cm"], max(0.0, float(value)))
    return round_half_away_from_zero(x / CONSTANTS["slotter_distance_bin_cm"])


def quantize_loudness(value: float) -> int:
    x = min(1.0, max(0.0, float(value)))
    return round_half_away_from_zero(x * CONSTANTS["slotter_loudness_scale"])


def pack_bits_lsb_first(bits: list[bool], bit_count: int) -> bytes:
    if len(bits) != bit_count:
        raise ValueError(f"expected {bit_count} bits")
    out = bytearray((bit_count + 7) // 8)
    for index, flag in enumerate(bits):
        if flag:
            out[index // 8] |= 1 << (index % 8)
    return bytes(out)


def candidate_set_canonical_bytes(handles: list[TargetHandle], target_mask: list[bool], candidate_mask: list[bool]) -> bytes:
    raw = bytearray()
    for field in CANDIDATE_HASH_CONTRACT["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(typ, "bytes"):
                raise ValueError("candidate magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, CANDIDATE_HASH_CONTRACT["byte_order"])
        elif name == "schema_source_sha256":
            raw += _digest_bytes(SCHEMA_SOURCE_SHA256, _array_count(typ, "bytes"), name)
        elif name == "target_slot_count":
            raw += _pack_unsigned(CONSTANTS[field["value_ref"]], typ, CANDIDATE_HASH_CONTRACT["byte_order"])
        elif name == "target_handles":
            count = _array_count(typ, "target_handle")
            if len(handles) != count:
                raise ValueError("handles")
            for handle in handles:
                raw += handle.canonical_bytes()
        elif name == "target_mask":
            raw += pack_bits_lsb_first(target_mask, int(field["bit_count"]))
        elif name == "candidate_mask":
            raw += pack_bits_lsb_first(candidate_mask, int(field["bit_count"]))
        else:
            raise ValueError(f"unsupported candidate hash field {name}")
    return bytes(raw)


def candidate_set_hash(handles: list[TargetHandle], target_mask: list[bool], candidate_mask: list[bool]) -> str:
    return hashlib.sha256(candidate_set_canonical_bytes(handles, target_mask, candidate_mask)).hexdigest()


def decision_contract_canonical_bytes(digests: Mapping[str, str]) -> bytes:
    raw = bytearray()
    for field in DECISION_HASH_CONTRACT["fields"]:
        name, typ = field["name"], field["type"]
        if name == "magic":
            value = field["value_ascii"].encode("ascii")
            if len(value) != _array_count(typ, "bytes"):
                raise ValueError("decision magic size")
            raw += value
        elif name == "serialization_version":
            raw += _pack_unsigned(field["value"], typ, DECISION_HASH_CONTRACT["byte_order"])
        else:
            raw += _digest_bytes(digests[name], _array_count(typ, "bytes"), name)
    return bytes(raw)


def decision_contract_hash(digests: Mapping[str, str]) -> str:
    return hashlib.sha256(decision_contract_canonical_bytes(digests)).hexdigest()


def decode_parameter(skill_id: int, slot: int, normalized: float) -> float:
    spec = SKILL_PARAMETER_CONTRACTS[int(skill_id)][int(slot)]
    if not spec["active"]:
        return float(spec["default"])
    normalized_value = min(1.0, max(0.0, float(normalized)))
    value = float(spec["min"]) + normalized_value * (float(spec["max"]) - float(spec["min"]))
    return min(float(spec["max"]), max(float(spec["min"]), value))


def apply_normalizer_spec(spec: dict, value: float | None, sentinel_matched: bool = False) -> float:
    typ = spec["type"]
    x = 0.0 if value is None else float(value)
    if typ == "constant":
        return float(spec["p0"])
    if typ == "boolean":
        return 1.0 if bool(value) else 0.0
    if typ == "clamp":
        return min(float(spec["max"]), max(float(spec["min"]), x))
    if typ == "divide_clamp":
        return min(float(spec["max"]), max(float(spec["min"]), x / float(spec["p0"])))
    if typ == "trigonometric":
        return math.sin(x) if float(spec["p0"]) == 0.0 else math.cos(x)
    if typ == "log1p_ratio":
        x = min(float(spec["p1"]), max(float(spec["p0"]), x))
        return math.log1p(x) / math.log1p(float(spec["p2"]))
    if typ == "sentinel_divide_clamp":
        if sentinel_matched:
            return float(spec["p1"])
        return min(float(spec["max"]), max(float(spec["min"]), x / float(spec["p0"])))
    raise ValueError(typ)


def normalize_global(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["global"][index], value, sentinel_matched)


def normalize_target_common(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["target_common"][index], value, sentinel_matched)


def normalize_target_payload(kind: int, index: int, value: float | None, sentinel_matched: bool = False) -> float:
    name = TargetKind(int(kind)).name
    return apply_normalizer_spec(NORMALIZER_TABLES["target_payload"][name][index], value, sentinel_matched)


def normalize_event(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["event"][index], value, sentinel_matched)


def normalize_candidate_pair(index: int, value: float | None, sentinel_matched: bool = False) -> float:
    return apply_normalizer_spec(NORMALIZER_TABLES["candidate_pair"][index], value, sentinel_matched)
'''.strip("\n").splitlines())
    parts.append("")
    return "\n".join(parts)


def cpp_norm_type(typ: str) -> str:
    return {
        "constant": "ENormalizerType::Constant", "boolean": "ENormalizerType::Boolean",
        "clamp": "ENormalizerType::Clamp", "divide_clamp": "ENormalizerType::DivideClamp",
        "trigonometric": "ENormalizerType::Trigonometric", "log1p_ratio": "ENormalizerType::Log1pRatio",
        "sentinel_divide_clamp": "ENormalizerType::SentinelDivideClamp",
    }[typ]


def cpp_norm(spec: dict[str, Any]) -> str:
    return (
        "FNormalizerSpec{" + cpp_norm_type(spec["type"]) + ", "
        f"{float(spec['min']):.17g}, {float(spec['max']):.17g}, "
        f"{float(spec['p0']):.17g}, {float(spec['p1']):.17g}, {float(spec['p2']):.17g}" + "}"
    )


def byte_array_literal(hex_string: str) -> str:
    return ", ".join(f"0x{x:02x}" for x in bytes.fromhex(hex_string))


def ascii_array_literal(value: str) -> str:
    return ", ".join(str(x) for x in value.encode("ascii"))


def cpp_digest_member(name: str) -> str:
    return {
        "schema_source_sha256": "SchemaSource", "skill_registry_sha256": "SkillRegistry",
        "goal_registry_sha256": "GoalRegistry", "model_sha256": "Model",
        "normalization_contract_sha256": "NormalizationContract", "slotter_contract_sha256": "SlotterContract",
        "postprocess_contract_sha256": "PostprocessContract", "calibration_ood_asset_sha256": "CalibrationOodAsset",
    }[name]


SHA_CPP = r'''
inline std::uint32_t RotateRight(std::uint32_t X, std::uint32_t N) { return (X >> N) | (X << (32U - N)); }
inline std::array<std::uint8_t, 32> Sha256(const std::vector<std::uint8_t>& Input) {
    static constexpr std::array<std::uint32_t, 64> K{{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U
    }};
    std::vector<std::uint8_t> Data = Input;
    const std::uint64_t BitLength = static_cast<std::uint64_t>(Data.size()) * 8U;
    Data.push_back(0x80U);
    while ((Data.size() % 64U) != 56U) Data.push_back(0U);
    for (int I = 7; I >= 0; --I) Data.push_back(static_cast<std::uint8_t>((BitLength >> (I * 8)) & 0xffU));
    std::array<std::uint32_t, 8> H{{0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U}};
    for (std::size_t Offset = 0; Offset < Data.size(); Offset += 64U) {
        std::array<std::uint32_t, 64> W{};
        for (std::size_t I = 0; I < 16U; ++I) {
            const std::size_t J = Offset + I * 4U;
            W[I] = (static_cast<std::uint32_t>(Data[J]) << 24U) | (static_cast<std::uint32_t>(Data[J+1]) << 16U) |
                   (static_cast<std::uint32_t>(Data[J+2]) << 8U) | static_cast<std::uint32_t>(Data[J+3]);
        }
        for (std::size_t I = 16U; I < 64U; ++I) {
            const std::uint32_t S0 = RotateRight(W[I-15U],7U) ^ RotateRight(W[I-15U],18U) ^ (W[I-15U] >> 3U);
            const std::uint32_t S1 = RotateRight(W[I-2U],17U) ^ RotateRight(W[I-2U],19U) ^ (W[I-2U] >> 10U);
            W[I] = W[I-16U] + S0 + W[I-7U] + S1;
        }
        std::uint32_t A=H[0],B=H[1],C=H[2],D=H[3],E=H[4],F=H[5],G=H[6],HH=H[7];
        for (std::size_t I=0; I<64U; ++I) {
            const std::uint32_t S1=RotateRight(E,6U)^RotateRight(E,11U)^RotateRight(E,25U);
            const std::uint32_t Ch=(E&F)^((~E)&G);
            const std::uint32_t Temp1=HH+S1+Ch+K[I]+W[I];
            const std::uint32_t S0=RotateRight(A,2U)^RotateRight(A,13U)^RotateRight(A,22U);
            const std::uint32_t Maj=(A&B)^(A&C)^(B&C);
            const std::uint32_t Temp2=S0+Maj;
            HH=G;G=F;F=E;E=D+Temp1;D=C;C=B;B=A;A=Temp1+Temp2;
        }
        H[0]+=A;H[1]+=B;H[2]+=C;H[3]+=D;H[4]+=E;H[5]+=F;H[6]+=G;H[7]+=HH;
    }
    std::array<std::uint8_t,32> Out{};
    for (std::size_t I=0; I<8U; ++I) {
        Out[I*4U]=static_cast<std::uint8_t>((H[I]>>24U)&0xffU);
        Out[I*4U+1U]=static_cast<std::uint8_t>((H[I]>>16U)&0xffU);
        Out[I*4U+2U]=static_cast<std::uint8_t>((H[I]>>8U)&0xffU);
        Out[I*4U+3U]=static_cast<std::uint8_t>(H[I]&0xffU);
    }
    return Out;
}

inline std::string HexLower(const std::array<std::uint8_t,32>& Bytes) {
    static constexpr char Hex[] = "0123456789abcdef";
    std::string Out; Out.resize(64U);
    for (std::size_t I=0; I<Bytes.size(); ++I) { Out[I*2U]=Hex[Bytes[I]>>4U]; Out[I*2U+1U]=Hex[Bytes[I]&0x0fU]; }
    return Out;
}
'''.strip("\n")


def generate_cpp(schema: dict[str, Any], skills: dict[str, Any], goals: dict[str, Any], hashes: dict[str, str]) -> str:
    c = schema["constants"]
    tensors = schema["tensors"]
    norms = normalizer_tables(schema)
    candidate_contract = schema["hash_contract"]["candidate_set_hash"]
    decision_contract = schema["hash_contract"]["decision_contract_hash"]
    candidate_fields = {row["name"]: row for row in candidate_contract["fields"]}
    decision_fields = {row["name"]: row for row in decision_contract["fields"]}
    candidate_magic = candidate_fields["magic"]["value_ascii"]
    decision_magic = decision_fields["magic"]["value_ascii"]
    candidate_version = int(candidate_fields["serialization_version"]["value"])
    decision_version = int(decision_fields["serialization_version"]["value"])
    handle_order = candidate_fields["target_handles"]["field_order"]
    decision_digest_names = [row["name"] for row in decision_contract["fields"] if row["name"] not in {"magic", "serialization_version"}]

    lines = [
        "// AUTO-GENERATED. DO NOT EDIT.", "#pragma once", "#include <algorithm>", "#include <array>",
        "#include <cmath>", "#include <cstddef>", "#include <cstdint>", "#include <string>", "#include <vector>", "",
        "namespace AINativeNPC::SchemaV2 {",
        f'inline constexpr const char* SchemaVersion = "{schema["schema"]["version"]}";',
        f'inline constexpr const char* ContractRevision = "{schema["schema"]["contract_revision"]}";',
        f'inline constexpr const char* SchemaSourceSha256 = "{hashes["schema"]}";',
        f'inline constexpr const char* SkillRegistrySha256 = "{hashes["skill_registry"]}";',
        f'inline constexpr const char* GoalRegistrySha256 = "{hashes["goal_registry"]}";',
        f'inline constexpr std::array<std::uint8_t, 32> SchemaSourceSha256Bytes{{{{{byte_array_literal(hashes["schema"])}}}}};',
        f'inline constexpr std::array<std::uint8_t, {len(candidate_magic)}> CandidateHashMagic{{{{{ascii_array_literal(candidate_magic)}}}}};',
        f'inline constexpr std::uint16_t CandidateHashSerializationVersion = {candidate_version}U;',
        f'inline constexpr std::array<std::uint8_t, {len(decision_magic)}> DecisionHashMagic{{{{{ascii_array_literal(decision_magic)}}}}};',
        f'inline constexpr std::uint16_t DecisionHashSerializationVersion = {decision_version}U;',
        f'inline constexpr std::size_t RegularTargetSlots = {c["regular_target_slots"]};',
        f'inline constexpr std::size_t NoTargetSlot = {c["no_target_slot"]};',
        f'inline constexpr std::size_t TotalTargetSlots = {c["total_target_slots"]};',
        f'inline constexpr std::size_t SkillCount = {c["skill_count"]};',
        f'inline constexpr std::size_t CandidateCount = {c["candidate_count"]};',
        f'inline constexpr std::size_t EventSlots = {c["event_slots"]};',
        f'inline constexpr std::size_t GlobalFeatureCount = {c["global_feature_count"]};',
        f'inline constexpr std::size_t TargetFeatureCount = {c["target_feature_count"]};',
        f'inline constexpr std::size_t EventFeatureCount = {c["event_feature_count"]};',
        f'inline constexpr std::size_t CandidatePairFeatureCount = {c["candidate_pair_feature_count"]};',
        f'inline constexpr double SpatialMaxCm = {float(c["spatial_max_cm"]):.17g};',
        f'inline constexpr double TargetAgeMaxS = {float(c["target_age_max_s"]):.17g};',
        f'inline constexpr double SlotterConfidenceScale = {float(c["slotter_confidence_scale"]):.17g};',
        f'inline constexpr double SlotterAgeCentisecondScale = {float(c["slotter_age_centisecond_scale"]):.17g};',
        f'inline constexpr double SlotterDistanceBinCm = {float(c["slotter_distance_bin_cm"]):.17g};',
        f'inline constexpr double SlotterLoudnessScale = {float(c["slotter_loudness_scale"]):.17g};', "",
    ]
    for cls, key in [
        ("ETargetKind", "target_kind"), ("ESkillId", "skill"), ("EGoalType", "goal_type"),
        ("EGoalPhase", "goal_phase"), ("EEventType", "event_type"), ("EGoalSourcePriority", "goal_source_priority"),
    ]:
        lines.extend([cpp_enum(cls, schema["enums"][key]), ""])
    for cls, rows, key in [
        ("EGlobalFeature", tensors["global_state"]["fields"], "index"),
        ("ETargetCommonFeature", tensors["target_features"]["common_fields"], "index"),
        ("EEventFeature", tensors["event_features"]["fields"], "index"),
        ("ECandidatePairFeature", tensors["candidate_pair_features"]["fields"], "index"),
    ]:
        lines.extend([cpp_feature_enum(cls, rows, key), ""])
    for kind, rows in schema["target_payload_features"].items():
        lines.extend([cpp_feature_enum(f"E{kind}PayloadFeature", rows, "payload_index"), ""])

    lines.extend([
        "struct FTargetHandleWire {", "    ETargetKind Kind{ETargetKind::NoTarget};", "    std::uint64_t StableId{0};",
        "    std::uint32_t Generation{0};", "    std::uint64_t Revision{0};", "};", "",
        "struct FSkillParameterSpec { bool Active; double Min; double Max; double Default; };", "",
        "enum class ENormalizerType : std::uint8_t { Constant, Boolean, Clamp, DivideClamp, Trigonometric, Log1pRatio, SentinelDivideClamp };",
        "struct FNormalizerSpec { ENormalizerType Type; double Min; double Max; double P0; double P1; double P2; };", "",
        "inline constexpr std::size_t CandidateIndex(std::size_t SkillId, std::size_t TargetSlot) { return SkillId * TotalTargetSlots + TargetSlot; }", "",
        "inline constexpr std::array<std::array<FSkillParameterSpec, 4>, SkillCount> SkillParameterSpecs{{",
    ])
    for skill in skills["skills"]:
        specs = [
            "FSkillParameterSpec{" + str(bool(param["active"])).lower() + ", "
            f"{float(param['min']):.17g}, {float(param['max']):.17g}, {float(param['default']):.17g}" + "}"
            for param in skill["parameters"]
        ]
        lines.append("    std::array<FSkillParameterSpec, 4>{" + ", ".join(specs) + "},")
    lines.extend(["}};", ""])

    def add_norm_array(name: str, rows: list[dict[str, Any]]) -> None:
        lines.append(f"inline constexpr std::array<FNormalizerSpec, {len(rows)}> {name}{{{{")
        lines.extend(f"    {cpp_norm(row)}," for row in rows)
        lines.extend(["}};", ""])

    add_norm_array("GlobalNormalizers", norms["global"])
    add_norm_array("TargetCommonNormalizers", norms["target_common"])
    add_norm_array("EventNormalizers", norms["event"])
    add_norm_array("CandidatePairNormalizers", norms["candidate_pair"])
    lines.append("inline constexpr std::array<std::array<FNormalizerSpec, 16>, 8> TargetPayloadNormalizers{{")
    for kind_row in schema["enums"]["target_kind"]:
        rows = norms["target_payload"][kind_row["name"]]
        lines.append("    std::array<FNormalizerSpec, 16>{" + ", ".join(cpp_norm(row) for row in rows) + "},")
    lines.extend(["}};", ""])

    lines.extend(r'''
inline std::int64_t RoundHalfAwayFromZero(double Value) {
    return Value >= 0.0 ? static_cast<std::int64_t>(std::floor(Value + 0.5)) : static_cast<std::int64_t>(std::ceil(Value - 0.5));
}
inline std::int32_t QuantizeConfidence(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, 1.0) * SlotterConfidenceScale)); }
inline std::int32_t QuantizeAgeSeconds(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, TargetAgeMaxS) * SlotterAgeCentisecondScale)); }
inline std::int32_t QuantizeDistanceCm(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, SpatialMaxCm) / SlotterDistanceBinCm)); }
inline std::int32_t QuantizeLoudness(double Value) { return static_cast<std::int32_t>(RoundHalfAwayFromZero(std::clamp(Value, 0.0, 1.0) * SlotterLoudnessScale)); }

inline double ApplyNormalizer(const FNormalizerSpec& Spec, double Value, bool SentinelMatched = false) {
    switch (Spec.Type) {
        case ENormalizerType::Constant: return Spec.P0;
        case ENormalizerType::Boolean: return Value != 0.0 ? 1.0 : 0.0;
        case ENormalizerType::Clamp: return std::clamp(Value, Spec.Min, Spec.Max);
        case ENormalizerType::DivideClamp: return std::clamp(Value / Spec.P0, Spec.Min, Spec.Max);
        case ENormalizerType::Trigonometric: return Spec.P0 == 0.0 ? std::sin(Value) : std::cos(Value);
        case ENormalizerType::Log1pRatio: { const double X = std::clamp(Value, Spec.P0, Spec.P1); return std::log1p(X) / std::log1p(Spec.P2); }
        case ENormalizerType::SentinelDivideClamp: return SentinelMatched ? Spec.P1 : std::clamp(Value / Spec.P0, Spec.Min, Spec.Max);
    }
    return 0.0;
}
inline double NormalizeGlobal(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(GlobalNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeTargetCommon(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(TargetCommonNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeTargetPayload(std::size_t Kind, std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(TargetPayloadNormalizers.at(Kind).at(Index), Value, SentinelMatched); }
inline double NormalizeEvent(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(EventNormalizers.at(Index), Value, SentinelMatched); }
inline double NormalizeCandidatePair(std::size_t Index, double Value, bool SentinelMatched = false) { return ApplyNormalizer(CandidatePairNormalizers.at(Index), Value, SentinelMatched); }
inline double DecodeParameter(std::size_t SkillId, std::size_t Slot, double Normalized) {
    const auto& Spec = SkillParameterSpecs.at(SkillId).at(Slot);
    if (!Spec.Active) return Spec.Default;
    const double N = std::clamp(Normalized, 0.0, 1.0);
    return std::clamp(Spec.Min + N * (Spec.Max - Spec.Min), Spec.Min, Spec.Max);
}

template <typename T> inline void AppendLittleEndian(std::vector<std::uint8_t>& Out, T Value) {
    for (std::size_t I = 0; I < sizeof(T); ++I) Out.push_back(static_cast<std::uint8_t>((Value >> (I * 8U)) & static_cast<T>(0xffU)));
}
template <std::size_t N> inline std::array<std::uint8_t, (N + 7U) / 8U> PackBitsLSBFirst(const std::array<bool, N>& Bits) {
    std::array<std::uint8_t, (N + 7U) / 8U> Out{};
    for (std::size_t I = 0; I < N; ++I) if (Bits[I]) Out[I / 8U] |= static_cast<std::uint8_t>(1U << (I % 8U));
    return Out;
}
'''.strip("\n").splitlines())
    lines.append("")

    handle_cpp = {"kind": "Handle.Kind", "stable_id": "Handle.StableId", "generation": "Handle.Generation", "revision": "Handle.Revision"}
    lines.append("inline void AppendTargetHandle(std::vector<std::uint8_t>& Out, const FTargetHandleWire& Handle) {")
    for descriptor in handle_order:
        name, dtype = descriptor.split(":", 1)
        expression = handle_cpp[name]
        if dtype == "uint8":
            lines.append(f"    Out.push_back(static_cast<std::uint8_t>({expression}));")
        else:
            cpp_type = {"uint16": "std::uint16_t", "uint32": "std::uint32_t", "uint64": "std::uint64_t"}[dtype]
            lines.append(f"    AppendLittleEndian<{cpp_type}>(Out, static_cast<{cpp_type}>({expression}));")
    lines.extend(["}", ""])

    lines.extend([
        "inline std::vector<std::uint8_t> CandidateSetCanonicalBytes(",
        "    const std::array<FTargetHandleWire, TotalTargetSlots>& Handles,",
        "    const std::array<bool, TotalTargetSlots>& TargetMask,",
        "    const std::array<bool, CandidateCount>& CandidateMask) {",
        "    std::vector<std::uint8_t> Out;",
    ])
    for field in candidate_contract["fields"]:
        name = field["name"]
        if name == "magic": lines.append("    Out.insert(Out.end(), CandidateHashMagic.begin(), CandidateHashMagic.end());")
        elif name == "serialization_version": lines.append("    AppendLittleEndian<std::uint16_t>(Out, CandidateHashSerializationVersion);")
        elif name == "schema_source_sha256": lines.append("    Out.insert(Out.end(), SchemaSourceSha256Bytes.begin(), SchemaSourceSha256Bytes.end());")
        elif name == "target_slot_count": lines.append("    Out.push_back(static_cast<std::uint8_t>(TotalTargetSlots));")
        elif name == "target_handles": lines.append("    for (const auto& Handle : Handles) AppendTargetHandle(Out, Handle);")
        elif name == "target_mask": lines.extend(["    const auto PackedTargets = PackBitsLSBFirst(TargetMask);", "    Out.insert(Out.end(), PackedTargets.begin(), PackedTargets.end());"])
        elif name == "candidate_mask": lines.extend(["    const auto PackedCandidates = PackBitsLSBFirst(CandidateMask);", "    Out.insert(Out.end(), PackedCandidates.begin(), PackedCandidates.end());"])
        else: raise ValueError(name)
    lines.extend(["    return Out;", "}", ""])

    lines.append("struct FDecisionContractDigests {")
    for name in decision_digest_names:
        lines.append(f"    std::array<std::uint8_t, 32> {cpp_digest_member(name)}{{}};")
    lines.extend(["};", "", "inline std::vector<std::uint8_t> DecisionContractCanonicalBytes(const FDecisionContractDigests& Digests) {", "    std::vector<std::uint8_t> Out;"])
    for field in decision_contract["fields"]:
        name = field["name"]
        if name == "magic": lines.append("    Out.insert(Out.end(), DecisionHashMagic.begin(), DecisionHashMagic.end());")
        elif name == "serialization_version": lines.append("    AppendLittleEndian<std::uint16_t>(Out, DecisionHashSerializationVersion);")
        else:
            member = cpp_digest_member(name)
            lines.append(f"    Out.insert(Out.end(), Digests.{member}.begin(), Digests.{member}.end());")
    lines.extend(["    return Out;", "}", "", SHA_CPP, ""])
    lines.extend([
        "inline std::string CandidateSetHashHex(const std::array<FTargetHandleWire, TotalTargetSlots>& Handles, const std::array<bool, TotalTargetSlots>& TargetMask, const std::array<bool, CandidateCount>& CandidateMask) { return HexLower(Sha256(CandidateSetCanonicalBytes(Handles, TargetMask, CandidateMask))); }",
        "inline std::string DecisionContractHashHex(const FDecisionContractDigests& Digests) { return HexLower(Sha256(DecisionContractCanonicalBytes(Digests))); }",
        "", "static_assert(CandidateIndex(SkillCount - 1, TotalTargetSlots - 1) == CandidateCount - 1);",
        "static_assert(static_cast<std::size_t>(EGlobalFeature::current_skill_ContinueCurrentAction_reserved_zero) == 17);",
        "", "} // namespace AINativeNPC::SchemaV2", "",
    ])
    return "\n".join(lines)


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def markdown_field_table(title: str, fields: list[dict[str, Any]], index_key: str = "index") -> list[str]:
    lines = [title, "", "| Index | Name | Source | Unit | Normalizer | Valid range | Missing | Constraints |", "|---:|---|---|---|---|---|---|---|"]
    for field in fields:
        lines.append(
            f"| {field[index_key]} | `{field['name']}` | {field['source']} | `{field['unit']}` | "
            f"`{compact_json(field['normalizer'])}` | `{compact_json(field['valid_range'])}` | "
            f"`{compact_json(field['missing'])}` | `{compact_json(field.get('constraints', {}))}` |"
        )
    lines.append("")
    return lines


def generate_markdown(schema: dict[str, Any], skills: dict[str, Any], goals: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# Appendix A–D. AUTO-GENERATED Schema·Registry 계약", "",
        "> 이 구간은 `contracts/current/*.yaml`에서 자동 생성된다. 수동 편집하지 않는다.", "",
        f"- Generator: `{TOOL_VERSION}`", f"- Contract revision: `{schema['schema']['contract_revision']}`",
        f"- Schema SHA-256: `{hashes['schema']}`", f"- Skill Registry SHA-256: `{hashes['skill_registry']}`",
        f"- Goal Registry SHA-256: `{hashes['goal_registry']}`", f"- Test Taxonomy SHA-256: `{hashes['test_taxonomy']}`", "",
        "## A. Constants와 Enum", "", "### A.1 Constants", "", "| Name | Value |", "|---|---:|",
    ]
    for name, value in schema["constants"].items():
        lines.append(f"| `{name}` | `{value}` |")
    for enum_name, rows in schema["enums"].items():
        lines.extend(["", f"### A.{enum_name}", "", "| ID | Name |", "|---:|---|"])
        lines.extend(f"| {row['id']} | `{row['name']}` |" for row in rows)

    lines.extend(["", "## B. Tensor 계약", "", "### B.1 Tensor Summary", "", "| Name | Shape | dtype |", "|---|---|---|"])
    for name, tensor in schema["tensors"].items():
        lines.append(f"| `{name}` | `{compact_json(tensor['shape'])}` | `{tensor['dtype']}` |")
    for name, output in schema["outputs"].items():
        lines.append(f"| `{name}` | `{compact_json(output['shape'])}` | `{output['dtype']}` |")
    lines.extend([""])
    lines.extend(markdown_field_table("### B.2 global_state", schema["tensors"]["global_state"]["fields"]))
    lines.extend(markdown_field_table("### B.3 target_features common", schema["tensors"]["target_features"]["common_fields"]))
    lines.extend(markdown_field_table("### B.4 event_features", schema["tensors"]["event_features"]["fields"]))
    lines.extend(markdown_field_table("### B.5 candidate_pair_features", schema["tensors"]["candidate_pair_features"]["fields"]))

    lines.extend(["## C. Target Payload [32:47]", ""])
    for kind, fields in schema["target_payload_features"].items():
        lines.extend(markdown_field_table(f"### C.{kind}", fields, "payload_index"))

    lines.extend(["## D. Skill·Goal·Hash 계약", "", "### D.1 Skill Parameter", "", "| Skill ID | Skill | Slot | Parameter | Active | Unit | Min | Max | Default |", "|---:|---|---:|---|---:|---|---:|---:|---:|"])
    for skill in skills["skills"]:
        for param in skill["parameters"]:
            lines.append(f"| {skill['id']} | `{skill['name']}` | {param['slot']} | `{param['name']}` | {param['active']} | `{param['unit']}` | {param['min']} | {param['max']} | {param['default']} |")
    lines.extend(["", "### D.2 Goal Registry", "", "| Goal ID | Goal | Initial phase | Priority | Source | Interruptibility | Resume |", "|---:|---|---|---:|---|---|---|"])
    for goal in goals["goals"]:
        lines.append(
            f"| {goal['id']} | `{goal['name']}` | `{goal.get('initial_phase', '-')}` | "
            f"{goal.get('default_priority', '-')} | `{goal.get('source_priority', '-')}` | "
            f"`{goal.get('interruptibility', '-')}` | `{goal.get('resume_policy', '-')}` |"
        )
    hash_contracts = list(schema["hash_contract"].items())
    for section_number, (contract_name, contract) in enumerate(hash_contracts, start=3):
        lines.extend(["", f"### D.{section_number} Hash: {contract_name}", "", f"- Algorithm: `{contract['algorithm']}`", f"- Byte order: `{contract['byte_order']}`", "", "| Order | Name | Type | Contract |", "|---:|---|---|---|"])
        for order, field in enumerate(contract["fields"]):
            lines.append(f"| {order} | `{field['name']}` | `{field['type']}` | `{compact_json({k:v for k,v in field.items() if k not in {'name','type'}})}` |")
    normalizer_section_number = 3 + len(hash_contracts)
    lines.extend(["", f"### D.{normalizer_section_number} Normalizer 의미 규칙", "", f"```json\n{json.dumps(schema['normalizer_semantic_contract'], ensure_ascii=False, sort_keys=True, indent=2)}\n```", ""])
    return "\n".join(lines)



def generate_requirements_kpi(taxonomy: dict[str, Any]) -> str:
    m = critical_suite_metrics(taxonomy)
    total = m["critical_minimum_sequence_count"]
    family_count = m["required_family_count"]
    cases = m["minimum_cases_per_family"]
    lines = [
        "## E.1 고정 평가 버전", "",
        "- Utility Baseline: `utility_baseline_v1.0.0`",
        "- Schema: `2.0.0`",
        "- Target Slotter: `1.0.0`",
        "- Post-process: `1.0.0`",
        f"- Critical Suite: `{m['contract_id']}`, **{total} sequences = {family_count} family × {cases} case**",
        "", "### E.1.1 Critical Family", "",
    ]
    lines.extend(f"{index}. `{name}`" for index, name in enumerate(m["critical_family_names"], 1))
    lines.extend(["", "### E.1.2 OOD Family", ""])
    lines.extend(f"{index}. `{name}`" for index, name in enumerate(m["ood_family_names"], 1))
    lines.extend([
        "", "## E.2 Candidate/Target", "",
        "| Metric | Dataset | Gate |", "|---|---|---|",
        "| Target Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |",
        "| Any-Acceptable Candidate Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |",
        f"| Critical Target/Candidate Recall | Critical Suite {total} sequences | 100%, 분모와 miss 모두 보고 |",
        "| MandatoryOverflow | Critical + General | 0건 |",
        "", "## E.3 Safety", "", "절대 Gate:", "",
        f"- Critical Suite {total} sequences에서 hard-constraint 위반 Commit 0건",
        "- Randomized Safety Fuzz 100,000 decision에서 hard-constraint 위반 Commit 0건",
        "- Hidden Information Leakage Test 10,000 pair에서 Tensor/행동 누출 0건",
        "- Server authority 우회 0건", "",
        "Safety는 Baseline 비열등만으로 대체할 수 없다.", "",
    ])
    return "\n".join(lines)


def generate_unreal_kpi(taxonomy: dict[str, Any]) -> str:
    m = critical_suite_metrics(taxonomy)
    total = m["critical_minimum_sequence_count"]
    family_count = m["required_family_count"]
    cases = m["minimum_cases_per_family"]
    lines = [
        "## 25.8 KPI", "", "고정 평가 버전:", "", "```text",
        "utility_baseline_v1.0.0", "schema 2.0.0", "target_slotter 1.0.0", "postprocess 1.0.0", m["contract_id"], "```",
        "", "Gate:", "",
        "- General Target Recall 20,000 states: point ≥99.5%, Wilson lower ≥99.0%",
        "- Candidate Recall 동일",
        f"- Critical Suite {total} sequences: 100%",
        "- Safety Fuzz 100,000 decisions: hard-constraint Commit 0",
        "- Hidden Leakage 10,000 pair: 0",
        "- ECE ≤0.05", "- Brier ≤0.18", "- OOD recall ≥0.90 at FPR ≤0.10",
        "- Naturalness A/B: 600 sequence×3명, point ≥55%, CI lower >52%",
        "- Goal completion 비열등: lower bound ≥ -2.0pp",
        "- 불필요한 switch 비열등: upper ≤ +0.2 switch/10s",
        "- stable scenario p95 ≤3 switch/10s", "", "---", "",
        "## 25.9 고정 Critical/OOD Family", "",
        f"Critical {family_count} family와 OOD {m['ood_required_family_count']} family 이름은 `test_taxonomy_v1.yaml`을 단일 원본으로 사용한다. "
        f"Critical은 family당 최소 {cases} case, 총 최소 {total} sequences다.", "",
        "Critical family:", "",
    ]
    lines.extend(f"- `{name}`" for name in m["critical_family_names"])
    lines.extend(["", "OOD family:", ""])
    lines.extend(f"- `{name}`" for name in m["ood_family_names"])
    lines.append("")
    return "\n".join(lines)

def produce(root: Path, out_root: Path) -> dict[str, str]:
    paths = default_paths(root)
    errors = validate_contracts(paths)
    if errors:
        raise SystemExit("Contract validation failed before generation:\n- " + "\n- ".join(errors))
    schema, skills, goals = load_contracts(paths)
    taxonomy = load_yaml(paths.test_taxonomy)
    source_hashes = {
        "schema": sha256_file(paths.schema),
        "skill_registry": sha256_file(paths.skill_registry),
        "goal_registry": sha256_file(paths.goal_registry),
        "test_taxonomy": sha256_file(paths.test_taxonomy),
    }
    outputs = {
        "generated/python/ai_native_npc_contracts_generated.py": generate_python(schema, skills, goals, source_hashes),
        "generated/cpp/AINativeNPCContracts.generated.h": generate_cpp(schema, skills, goals, source_hashes),
        "generated/docs/schema_reference.md": generate_markdown(schema, skills, goals, source_hashes),
        "generated/docs/requirements_kpi_appendix.md": generate_requirements_kpi(taxonomy),
        "generated/docs/unreal_kpi_section.md": generate_unreal_kpi(taxonomy),
    }
    for relative, content in outputs.items():
        path = out_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    output_hashes = {relative: sha256_file(out_root / relative) for relative in outputs}
    manifest = {
        "generator": "tools/generate_contracts.py",
        "generator_version": TOOL_VERSION,
        "contract_revision": schema["schema"]["contract_revision"],
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
    }
    manifest_path = out_root / "generated/contract_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {**output_hashes, "generated/contract_manifest.json": sha256_file(manifest_path)}

def check(root: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        produce(root, temp)
        errors: list[str] = []
        for relative in [
            "generated/python/ai_native_npc_contracts_generated.py",
            "generated/cpp/AINativeNPCContracts.generated.h",
            "generated/docs/schema_reference.md",
            "generated/docs/requirements_kpi_appendix.md",
            "generated/docs/unreal_kpi_section.md",
            "generated/contract_manifest.json",
        ]:
            actual, expected = root / relative, temp / relative
            if not actual.exists():
                errors.append(f"missing generated file {relative}")
            elif actual.read_bytes() != expected.read_bytes():
                errors.append(f"generated file out of date {relative}")
        return errors

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.check:
        errors = check(root)
        if errors:
            print("\n".join(errors))
            raise SystemExit(1)
        print("PASS")
    else:
        print(json.dumps(produce(root, root), indent=2))


if __name__ == "__main__":
    main()
