#!/usr/bin/env python3
"""Generate deterministic Python/C++ Golden fixtures and C++ parity source."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any


def load_generated(root: Path):
    path = root / "generated/python/ai_native_npc_contracts_generated.py"
    spec = importlib.util.spec_from_file_location("ai_native_npc_contracts_generated", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_boss_generated(root: Path):
    path = root / "generated/python/ai_native_npc_boss_pattern_contracts_generated.py"
    spec = importlib.util.spec_from_file_location("ai_native_npc_boss_pattern_contracts_generated", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_handles(g: Any, rows: list[tuple[int, int, int, int, int]]):
    handles = [g.TargetHandle(0, 0, 0, 0) for _ in range(g.CONSTANTS["total_target_slots"])]
    for slot, kind, stable, generation, revision in rows:
        handles[slot] = g.TargetHandle(kind, stable, generation, revision)
    return handles


def candidate_vector(g: Any, name: str, rows: list[tuple[int, int, int, int, int]], target_true: list[int], candidate_true: list[int]) -> dict[str, Any]:
    handles = make_handles(g, rows)
    target_mask = [False] * g.CONSTANTS["total_target_slots"]
    for index in target_true:
        target_mask[index] = True
    target_mask[g.CONSTANTS["no_target_slot"]] = True
    candidate_mask = [False] * g.CONSTANTS["candidate_count"]
    for index in candidate_true:
        candidate_mask[index] = True
    canonical = g.candidate_set_canonical_bytes(handles, target_mask, candidate_mask)
    return {
        "name": name,
        "handles": [
            {"kind": h.kind, "stable_id": h.stable_id, "generation": h.generation, "revision": h.revision}
            for h in handles
        ],
        "target_mask": target_mask,
        "candidate_mask_true_indices": [i for i, enabled in enumerate(candidate_mask) if enabled],
        "target_mask_bytes_hex": g.pack_bits_lsb_first(target_mask, len(target_mask)).hex(),
        "candidate_mask_bytes_hex": g.pack_bits_lsb_first(candidate_mask, len(candidate_mask)).hex(),
        "canonical_bytes_hex": canonical.hex(),
        "sha256": g.candidate_set_hash(handles, target_mask, candidate_mask),
    }


def build_decision_vector(g: Any) -> dict[str, Any]:
    digest_names = [
        field["name"]
        for field in g.DECISION_HASH_CONTRACT["fields"]
        if field["type"] == "bytes[32]"
    ]
    seeds = {
        "schema_source_sha256": g.SCHEMA_SOURCE_SHA256,
        "skill_registry_sha256": g.SKILL_REGISTRY_SHA256,
        "goal_registry_sha256": g.GOAL_REGISTRY_SHA256,
    }
    for index, name in enumerate(digest_names):
        seeds.setdefault(name, "")
    # Keep synthetic asset digests visually distinct and deterministic.
    for index, name in enumerate(digest_names):
        if not seeds.get(name):
            seeds[name] = (bytes([0x20 + index]) * 32).hex()
    canonical = g.decision_contract_canonical_bytes(seeds)
    return {
        "digests": seeds,
        "canonical_bytes_hex": canonical.hex(),
        "sha256": g.decision_contract_hash(seeds),
    }


def build_discrete(root: Path) -> dict[str, Any]:
    g = load_generated(root)
    vectors = [
        candidate_vector(g, "no_target_idle", [], [], [g.candidate_index(g.SkillId.Idle, 16)]),
        candidate_vector(
            g,
            "entity_and_sound",
            [
                (0, int(g.TargetKind.Entity), 0x1122334455667788, 2, 5),
                (1, int(g.TargetKind.SoundEvent), 0x0102030405060708, 1, 9),
            ],
            [0, 1],
            [
                g.candidate_index(g.SkillId.LookAt, 0),
                g.candidate_index(g.SkillId.TurnTo, 1),
                g.candidate_index(g.SkillId.Investigate, 1),
                g.candidate_index(g.SkillId.Idle, 16),
            ],
        ),
        candidate_vector(
            g,
            "last_known_and_cover",
            [
                (3, int(g.TargetKind.LastKnownPosition), 9001, 4, 77),
                (7, int(g.TargetKind.CoverSlot), 42, 11, 101),
            ],
            [3, 7],
            [
                g.candidate_index(g.SkillId.Approach, 3),
                g.candidate_index(g.SkillId.SearchArea, 3),
                g.candidate_index(g.SkillId.TakeCover, 7),
                g.candidate_index(g.SkillId.Flee, 16),
            ],
        ),
    ]
    quantization = {
        "confidence": [{"input": x, "expected": g.quantize_confidence(x)} for x in [-0.1, 0.0, 0.0005, 0.5, 0.9995, 1.0, 1.1]],
        "age_seconds": [{"input": x, "expected": g.quantize_age_seconds(x)} for x in [-1.0, 0.0, 0.005, 1.234, 9.999, 10.0, 12.0]],
        "distance_cm": [{"input": x, "expected": g.quantize_distance_cm(x)} for x in [-1.0, 0.0, 4.9, 5.0, 15.0, 4999.9, 5000.0, 6000.0]],
        "loudness": [{"input": x, "expected": g.quantize_loudness(x)} for x in [-0.1, 0.0, 0.0005, 0.5, 0.9995, 1.0, 1.1]],
    }
    parameter_decode = []
    for skill_id in range(g.CONSTANTS["skill_count"]):
        for slot in range(g.CONSTANTS["parameter_count"]):
            for normalized in [-0.25, 0.0, 0.5, 1.0, 1.25]:
                parameter_decode.append({
                    "skill_id": skill_id,
                    "slot": slot,
                    "normalized": normalized,
                    "expected": g.decode_parameter(skill_id, slot, normalized),
                })
    return {
        "fixture_version": 2,
        "contract_revision": g.CONTRACT_REVISION,
        "schema_source_sha256": g.SCHEMA_SOURCE_SHA256,
        "generated_python_sha256": hashlib.sha256((root / "generated/python/ai_native_npc_contracts_generated.py").read_bytes()).hexdigest(),
        "generated_cpp_sha256": hashlib.sha256((root / "generated/cpp/AINativeNPCContracts.generated.h").read_bytes()).hexdigest(),
        "vectors": vectors,
        "slotter_quantization": quantization,
        "parameter_decode": parameter_decode,
        "decision_contract": build_decision_vector(g),
    }


def build_boss_pattern(root: Path) -> dict[str, Any]:
    boss = load_boss_generated(root)
    pattern_ids = [101, 204, 409] + [boss.CONSTANTS["invalid_pattern_id"]] * 29
    pattern_mask = [True, True, False] + [False] * 29
    handle = boss.TargetHandle(kind=1, stable_id=0x1122334455667788, generation=7, revision=19)
    asset_hash = (bytes([0x31]) * 32).hex()
    canonical = boss.pattern_candidate_set_canonical_bytes(
        asset_hash,
        pattern_ids,
        pattern_mask,
        handle,
        int(boss.SelectionBoundary.BranchWindow),
        11,
        23,
    )
    digest_names = [
        field["name"]
        for field in boss.BOSS_PATTERN_DECISION_HASH_CONTRACT["fields"]
        if field["type"] == "bytes[32]" and field["name"] != "boss_pattern_contract_sha256"
    ]
    digests = {name: (bytes([0x41 + index]) * 32).hex() for index, name in enumerate(digest_names)}
    decision_canonical = boss.boss_pattern_decision_contract_canonical_bytes(digests)
    return {
        "fixture_version": 1,
        "contract_revision": boss.CONTRACT_REVISION,
        "boss_pattern_contract_sha256": boss.BOSS_PATTERN_CONTRACT_SHA256,
        "generated_python_sha256": hashlib.sha256((root / "generated/python/ai_native_npc_boss_pattern_contracts_generated.py").read_bytes()).hexdigest(),
        "generated_cpp_sha256": hashlib.sha256((root / "generated/cpp/AINativeNPCBossPatternContracts.generated.h").read_bytes()).hexdigest(),
        "candidate_set": {
            "pattern_asset_bundle_sha256": asset_hash,
            "pattern_ids": pattern_ids,
            "pattern_mask": pattern_mask,
            "attack_target_handle": {"kind": handle.kind, "stable_id": handle.stable_id, "generation": handle.generation, "revision": handle.revision},
            "selection_boundary": int(boss.SelectionBoundary.BranchWindow),
            "boss_phase_revision": 11,
            "combat_state_revision": 23,
            "canonical_bytes_hex": canonical.hex(),
            "sha256": boss.pattern_candidate_set_hash(asset_hash, pattern_ids, pattern_mask, handle, int(boss.SelectionBoundary.BranchWindow), 11, 23),
        },
        "decision_contract": {
            "digests": digests,
            "canonical_bytes_hex": decision_canonical.hex(),
            "sha256": boss.boss_pattern_decision_contract_hash(digests),
        },
    }


def representative_values(spec: dict[str, Any]) -> list[tuple[float, bool]]:
    typ = spec["type"]
    if typ == "constant":
        return [(-1.0, False), (0.0, False), (2.0, False)]
    if typ == "boolean":
        return [(0.0, False), (1.0, False), (-2.0, False)]
    if typ == "clamp":
        lo, hi = float(spec["min"]), float(spec["max"])
        return [(lo - 1.0, False), ((lo + hi) / 2.0, False), (hi + 1.0, False)]
    if typ == "divide_clamp":
        div = float(spec["p0"])
        return [(-2.0 * div, False), (0.0, False), (0.5 * div, False), (2.0 * div, False)]
    if typ == "trigonometric":
        return [(-1.2, False), (0.0, False), (0.7, False)]
    if typ == "log1p_ratio":
        return [(-1.0, False), (0.0, False), (0.5 * float(spec["p1"]), False), (2.0 * float(spec["p1"]), False)]
    if typ == "sentinel_divide_clamp":
        div = float(spec["p0"])
        return [(0.0, False), (0.5 * div, False), (2.0 * div, False), (123.0, True)]
    raise ValueError(typ)


def build_normalizers(root: Path) -> dict[str, Any]:
    g = load_generated(root)
    rows: list[dict[str, Any]] = []

    def add(table: str, specs: list[dict[str, Any]], kind: int | None = None) -> None:
        for index, spec in enumerate(specs):
            for value, sentinel in representative_values(spec):
                expected = g.apply_normalizer_spec(spec, value, sentinel)
                rows.append({
                    "table": table,
                    "kind": kind,
                    "index": index,
                    "value": value,
                    "sentinel_matched": sentinel,
                    "expected": expected,
                })

    add("global", g.NORMALIZER_TABLES["global"])
    add("target_common", g.NORMALIZER_TABLES["target_common"])
    add("event", g.NORMALIZER_TABLES["event"])
    add("candidate_pair", g.NORMALIZER_TABLES["candidate_pair"])
    for kind in g.TargetKind:
        add("target_payload", g.NORMALIZER_TABLES["target_payload"][kind.name], int(kind))
    return {
        "fixture_version": 1,
        "contract_revision": g.CONTRACT_REVISION,
        "abs_tolerance": 1e-9,
        "rel_tolerance": 1e-9,
        "vectors": rows,
    }


def cpp_bool(value: bool) -> str:
    return "true" if value else "false"


def generate_cpp_test(discrete: dict[str, Any], normalizers: dict[str, Any], boss_pattern: dict[str, Any]) -> str:
    lines = [
        "// AUTO-GENERATED Golden parity test. DO NOT EDIT.",
        '#include "../generated/cpp/AINativeNPCContracts.generated.h"',
        '#include "../generated/cpp/AINativeNPCBossPatternContracts.generated.h"',
        "#include <algorithm>",
        "#include <array>",
        "#include <cmath>",
        "#include <cstdint>",
        "#include <iostream>",
        "#include <sstream>",
        "#include <string>",
        "#include <vector>",
        "using namespace AINativeNPC::SchemaV2;",
        "",
        "static std::string Hex(const std::vector<std::uint8_t>& Bytes) {",
        '  static constexpr char H[]="0123456789abcdef"; std::string Out; Out.resize(Bytes.size()*2U);',
        "  for(std::size_t I=0;I<Bytes.size();++I){Out[I*2U]=H[Bytes[I]>>4U];Out[I*2U+1U]=H[Bytes[I]&0x0fU];} return Out;",
        "}",
        "template<std::size_t N> static std::string HexArray(const std::array<std::uint8_t,N>& Bytes){return Hex(std::vector<std::uint8_t>(Bytes.begin(),Bytes.end()));}",
        "static bool Almost(double A,double B,double Abs,double Rel){return std::abs(A-B)<=std::max(Abs,Rel*std::max(std::abs(A),std::abs(B)));}",
        "static int Fail(const std::string& What){std::cerr<<What<<'\\n';return 1;}",
        "int main(){",
        "  if(CandidateIndex(15,16)!=271) return Fail(\"candidate index\");",
    ]

    for vec_idx, vector in enumerate(discrete["vectors"]):
        lines.extend([
            f"  // {vector['name']}",
            f"  std::array<FTargetHandleWire,TotalTargetSlots> H{vec_idx}{{}};",
            f"  std::array<bool,TotalTargetSlots> TM{vec_idx}{{}}; TM{vec_idx}[NoTargetSlot]=true;",
            f"  std::array<bool,CandidateCount> CM{vec_idx}{{}};",
        ])
        for slot, handle in enumerate(vector["handles"]):
            if any([handle["kind"], handle["stable_id"], handle["generation"], handle["revision"]]):
                lines.append(
                    f"  H{vec_idx}[{slot}]=FTargetHandleWire{{static_cast<ETargetKind>({handle['kind']}), "
                    f"{handle['stable_id']}ULL, {handle['generation']}U, {handle['revision']}ULL}};"
                )
        for slot, enabled in enumerate(vector["target_mask"]):
            if enabled and slot != 16:
                lines.append(f"  TM{vec_idx}[{slot}]=true;")
        for index in vector["candidate_mask_true_indices"]:
            lines.append(f"  CM{vec_idx}[{index}]=true;")
        lines.extend([
            f"  if(HexArray(PackBitsLSBFirst(TM{vec_idx}))!=\"{vector['target_mask_bytes_hex']}\") return Fail(\"target mask {vector['name']}\");",
            f"  if(HexArray(PackBitsLSBFirst(CM{vec_idx}))!=\"{vector['candidate_mask_bytes_hex']}\") return Fail(\"candidate mask {vector['name']}\");",
            f"  if(Hex(CandidateSetCanonicalBytes(H{vec_idx},TM{vec_idx},CM{vec_idx}))!=\"{vector['canonical_bytes_hex']}\") return Fail(\"canonical {vector['name']}\");",
            f"  if(CandidateSetHashHex(H{vec_idx},TM{vec_idx},CM{vec_idx})!=\"{vector['sha256']}\") return Fail(\"hash {vector['name']}\");",
        ])

    decision = discrete["decision_contract"]
    lines.append("  FDecisionContractDigests DD{};")
    member_map = {
        "schema_source_sha256": "SchemaSource",
        "skill_registry_sha256": "SkillRegistry",
        "goal_registry_sha256": "GoalRegistry",
        "model_sha256": "Model",
        "normalization_contract_sha256": "NormalizationContract",
        "slotter_contract_sha256": "SlotterContract",
        "postprocess_contract_sha256": "PostprocessContract",
        "calibration_ood_asset_sha256": "CalibrationOodAsset",
    }
    for name, hex_value in decision["digests"].items():
        values = ",".join(f"0x{hex_value[i:i+2]}" for i in range(0, len(hex_value), 2))
        lines.append(f"  DD.{member_map[name]} = std::array<std::uint8_t,32>{{{values}}};")
    lines.extend([
        f"  if(Hex(DecisionContractCanonicalBytes(DD))!=\"{decision['canonical_bytes_hex']}\") return Fail(\"decision canonical\");",
        f"  if(DecisionContractHashHex(DD)!=\"{decision['sha256']}\") return Fail(\"decision hash\");",
    ])

    boss_candidate = boss_pattern["candidate_set"]
    asset_values = ",".join(f"0x{boss_candidate['pattern_asset_bundle_sha256'][index:index+2]}" for index in range(0, 64, 2))
    lines.extend([
        f"  std::array<std::uint8_t,32> BossAssetHash{{{asset_values}}};",
        "  std::array<std::uint16_t,AINativeNPC::BossPatternV1::MaxPatternSlots> BossPatternIds{};",
        "  BossPatternIds.fill(AINativeNPC::BossPatternV1::InvalidPatternId);",
        "  std::array<bool,AINativeNPC::BossPatternV1::MaxPatternSlots> BossPatternMask{};",
    ])
    for index, pattern_id in enumerate(boss_candidate["pattern_ids"]):
        if pattern_id != 65535:
            lines.append(f"  BossPatternIds[{index}]={pattern_id}U;")
    for index, enabled in enumerate(boss_candidate["pattern_mask"]):
        if enabled:
            lines.append(f"  BossPatternMask[{index}]=true;")
    handle = boss_candidate["attack_target_handle"]
    lines.append(
        "  FTargetHandleWire BossTarget{"
        f"static_cast<ETargetKind>({handle['kind']}), {handle['stable_id']}ULL, {handle['generation']}U, {handle['revision']}ULL"
        "};"
    )
    lines.extend([
        "  const auto BossCandidateBytes=AINativeNPC::BossPatternV1::PatternCandidateSetCanonicalBytes("
        f"BossAssetHash,BossPatternIds,BossPatternMask,BossTarget,static_cast<AINativeNPC::BossPatternV1::ESelectionBoundary>({boss_candidate['selection_boundary']}),{boss_candidate['boss_phase_revision']}ULL,{boss_candidate['combat_state_revision']}ULL);",
        f"  if(Hex(BossCandidateBytes)!=\"{boss_candidate['canonical_bytes_hex']}\") return Fail(\"boss pattern candidate canonical\");",
        "  if(AINativeNPC::BossPatternV1::PatternCandidateSetHashHex("
        f"BossAssetHash,BossPatternIds,BossPatternMask,BossTarget,static_cast<AINativeNPC::BossPatternV1::ESelectionBoundary>({boss_candidate['selection_boundary']}),{boss_candidate['boss_phase_revision']}ULL,{boss_candidate['combat_state_revision']}ULL)!=\"{boss_candidate['sha256']}\") return Fail(\"boss pattern candidate hash\");",
        "  auto InvalidBossPatternIds=BossPatternIds; std::swap(InvalidBossPatternIds[0],InvalidBossPatternIds[1]);",
        "  if(AINativeNPC::BossPatternV1::IsPatternSlotLayoutValid(InvalidBossPatternIds,BossPatternMask)) return Fail(\"boss unsorted pattern layout accepted\");",
        "  if(!AINativeNPC::BossPatternV1::PatternCandidateSetCanonicalBytes(BossAssetHash,InvalidBossPatternIds,BossPatternMask,BossTarget,AINativeNPC::BossPatternV1::ESelectionBoundary::PreAttack,1ULL,1ULL).empty()) return Fail(\"boss invalid layout serialized\");",
        "  auto InvalidBossPatternMask=BossPatternMask; InvalidBossPatternMask[31]=true;",
        "  if(AINativeNPC::BossPatternV1::IsPatternSlotLayoutValid(BossPatternIds,InvalidBossPatternMask)) return Fail(\"boss invalid padding mask accepted\");",
        "  std::array<std::uint16_t,AINativeNPC::BossPatternV1::MaxPatternSlots> AllPaddingBossPatternIds{}; AllPaddingBossPatternIds.fill(AINativeNPC::BossPatternV1::InvalidPatternId);",
        "  std::array<bool,AINativeNPC::BossPatternV1::MaxPatternSlots> AllPaddingBossPatternMask{};",
        "  if(AINativeNPC::BossPatternV1::IsPatternSlotLayoutValid(AllPaddingBossPatternIds,AllPaddingBossPatternMask)) return Fail(\"boss all-padding pattern layout accepted\");",
        "  if(!AINativeNPC::BossPatternV1::PatternCandidateSetCanonicalBytes(BossAssetHash,AllPaddingBossPatternIds,AllPaddingBossPatternMask,BossTarget,AINativeNPC::BossPatternV1::ESelectionBoundary::PreAttack,1ULL,1ULL).empty()) return Fail(\"boss all-padding layout serialized\");",
        "  AINativeNPC::BossPatternV1::FBossPatternDecisionDigests BossDD{};",
    ])
    boss_member_map = {
        "pattern_model_sha256": "PatternModel",
        "pattern_normalization_contract_sha256": "PatternNormalizationContract",
        "pattern_postprocess_contract_sha256": "PatternPostprocessContract",
        "pattern_calibration_ood_asset_sha256": "PatternCalibrationOodAsset",
        "pattern_executor_contract_sha256": "PatternExecutorContract",
    }
    boss_decision = boss_pattern["decision_contract"]
    for name, hex_value in boss_decision["digests"].items():
        values = ",".join(f"0x{hex_value[index:index+2]}" for index in range(0, len(hex_value), 2))
        lines.append(f"  BossDD.{boss_member_map[name]}=std::array<std::uint8_t,32>{{{values}}};")
    lines.extend([
        f"  if(Hex(AINativeNPC::BossPatternV1::BossPatternDecisionContractCanonicalBytes(BossDD))!=\"{boss_decision['canonical_bytes_hex']}\") return Fail(\"boss pattern decision canonical\");",
        f"  if(AINativeNPC::BossPatternV1::BossPatternDecisionContractHashHex(BossDD)!=\"{boss_decision['sha256']}\") return Fail(\"boss pattern decision hash\");",
        "  float BossNorm=0.0f;",
        "  if(!AINativeNPC::BossPatternV1::TryNormalizeFeature(5000.0f,AINativeNPC::BossPatternV1::PatternContextNormalizers[static_cast<std::size_t>(AINativeNPC::BossPatternV1::EPatternContextFeature::target_distance_planar)],BossNorm)||!Almost(BossNorm,0.5,1e-7,1e-7)) return Fail(\"boss context distance normalizer\");",
        "  if(!AINativeNPC::BossPatternV1::TryNormalizeFeature(-1000.0f,AINativeNPC::BossPatternV1::PatternContextNormalizers[static_cast<std::size_t>(AINativeNPC::BossPatternV1::EPatternContextFeature::target_relative_speed)],BossNorm)||!Almost(BossNorm,-0.5,1e-7,1e-7)) return Fail(\"boss context speed normalizer\");",
        "  if(!AINativeNPC::BossPatternV1::TryNormalizeFeature(15.0f,AINativeNPC::BossPatternV1::PatternFeatureNormalizers[static_cast<std::size_t>(AINativeNPC::BossPatternV1::EPatternFeature::telegraph_duration)],BossNorm)||!Almost(BossNorm,0.5,1e-7,1e-7)) return Fail(\"boss duration normalizer\");",
        "  if(!AINativeNPC::BossPatternV1::TryNormalizeFeature(999.0f,AINativeNPC::BossPatternV1::PatternFeatureNormalizers[static_cast<std::size_t>(AINativeNPC::BossPatternV1::EPatternFeature::reserved_zero)],BossNorm)||BossNorm!=0.0f) return Fail(\"boss constant-zero normalizer\");",
        "  if(AINativeNPC::BossPatternV1::TryNormalizeFeature(std::nanf(\"\"),AINativeNPC::BossPatternV1::PatternContextNormalizers[0],BossNorm)) return Fail(\"boss nonfinite normalizer\");",
    ])

    quant_functions = {
        "confidence": "QuantizeConfidence",
        "age_seconds": "QuantizeAgeSeconds",
        "distance_cm": "QuantizeDistanceCm",
        "loudness": "QuantizeLoudness",
    }
    for name, rows in discrete["slotter_quantization"].items():
        func = quant_functions[name]
        for index, row in enumerate(rows):
            lines.append(f"  if({func}({row['input']!r})!={row['expected']}) return Fail(\"quant {name} {index}\");")

    for index, row in enumerate(discrete["parameter_decode"]):
        lines.append(
            f"  if(!Almost(DecodeParameter({row['skill_id']},{row['slot']},{row['normalized']!r}),{row['expected']!r},1e-12,1e-12)) "
            f"return Fail(\"parameter {index}\");"
        )

    table_calls = {
        "global": "NormalizeGlobal",
        "target_common": "NormalizeTargetCommon",
        "event": "NormalizeEvent",
        "candidate_pair": "NormalizeCandidatePair",
    }
    for index, row in enumerate(normalizers["vectors"]):
        if row["table"] == "target_payload":
            call = f"NormalizeTargetPayload({row['kind']},{row['index']},{row['value']!r},{cpp_bool(row['sentinel_matched'])})"
        else:
            call = f"{table_calls[row['table']]}({row['index']},{row['value']!r},{cpp_bool(row['sentinel_matched'])})"
        lines.append(
            f"  if(!Almost({call},{row['expected']!r},{normalizers['abs_tolerance']!r},{normalizers['rel_tolerance']!r})) "
            f"return Fail(\"normalizer {index}\");"
        )

    lines.extend(["  return 0;", "}", ""])
    return "\n".join(lines)


def build_all(root: Path) -> dict[str, str]:
    discrete = build_discrete(root)
    normalizers = build_normalizers(root)
    boss_pattern = build_boss_pattern(root)
    outputs = {
        "tests/golden/discrete_hash_vectors.json": json.dumps(discrete, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "tests/golden/normalizer_vectors.json": json.dumps(normalizers, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "tests/golden/boss_pattern_hash_vectors.json": json.dumps(boss_pattern, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "tests/generated_cpp_golden_test.cpp": generate_cpp_test(discrete, normalizers, boss_pattern),
    }
    return outputs


def write(root: Path) -> None:
    for rel, content in build_all(root).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for rel, expected in build_all(root).items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing Golden output {rel}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"Golden output stale {rel}")
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
        write(root)
        for rel in build_all(root):
            print(root / rel)


if __name__ == "__main__":
    main()
