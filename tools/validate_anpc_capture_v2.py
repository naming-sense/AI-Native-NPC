#!/usr/bin/env python3
"""Validate Unreal ANPCCAP2 captures and prove Python/C++ canonical parity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

MAGIC = b"ANPCCAP2"
SAMPLE_MAGIC = b"ANPCSAMPLE2"
FEATURE_MAGIC = b"ANPCFEAT1"
CANDIDATE_MAGIC = b"ANPCSET2"
CANDIDATE_COUNT = 272
SCHEMA_SHA256 = "a7791004de0534f29198ebf5eaaff7cd764185b59b05446d419f5d0a3303f886"
SKILL_REGISTRY_SHA256 = "ed0454691c17761d81ee52ac0c729f6f83adec97a954a4808107d078ba49975d"
GOAL_REGISTRY_SHA256 = "d9eb13898cf2d066320977073b1e82458cc0d7bdfd512ef6983ad9a2d44c8f3e"
GOAL_REGISTRY_VERSION = "1.1.0"
ACTIVE_PARAMETER_SLOTS = (
    (True, False, False, False),
    (False, False, False, False),
    (True, False, False, True),
    (True, True, False, True),
    (True, True, True, True),
    (True, True, True, True),
    (True, True, True, True),
    (True, True, True, True),
    (True, True, True, True),
    (True, True, True, True),
    (True, False, False, True),
    (True, False, False, True),
    (True, False, False, True),
    (True, True, False, True),
    (True, True, True, True),
    (True, False, True, True),
)
TENSOR_LENGTHS = (512, 3264, 136, 17, 1152, 96, 96, 12, 17408, 272)
FLOAT_TENSORS = (0, 1, 4, 8)


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def is_lower_hash(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass
class Reader:
    data: bytes
    offset: int = 0

    def take(self, size: int) -> bytes:
        require(size >= 0 and self.offset + size <= len(self.data), "truncated capture")
        result = self.data[self.offset : self.offset + size]
        self.offset += size
        return result

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return int.from_bytes(self.take(2), "little")

    def u32(self) -> int:
        return struct.unpack("<I", self.take(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self.take(8))[0]

    def f64(self) -> float:
        return struct.unpack("<d", self.take(8))[0]

    def blob(self) -> bytes:
        return self.take(self.u32())

    def text(self) -> str:
        raw = self.blob()
        try:
            value = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValidationError("metadata must be ASCII") from exc
        require(all(0x20 <= b <= 0x7E for b in raw), "metadata contains control byte")
        return value


class CborReader:
    def __init__(self, data: bytes):
        self.reader = Reader(data)

    def _argument(self, additional: int) -> int:
        if additional < 24:
            return additional
        sizes = {24: 1, 25: 2, 26: 4, 27: 8}
        require(additional in sizes, "indefinite/reserved CBOR is forbidden")
        raw = self.reader.take(sizes[additional])
        value = int.from_bytes(raw, "big")
        thresholds = {24: 24, 25: 256, 26: 65536, 27: 4294967296}
        require(value >= thresholds[additional], "non-minimal CBOR integer/length")
        return value

    def item(self) -> Any:
        initial = self.reader.u8()
        major, additional = initial >> 5, initial & 0x1F
        if major == 7:
            require(additional in (20, 21, 22), "unsupported CBOR simple value")
            return {20: False, 21: True, 22: None}[additional]
        value = self._argument(additional)
        if major == 0:
            return value
        if major == 2:
            return self.reader.take(value)
        if major == 3:
            raw = self.reader.take(value)
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValidationError("invalid UTF-8 CBOR text") from exc
        if major == 4:
            return [self.item() for _ in range(value)]
        if major == 5:
            result: dict[Any, Any] = {}
            previous_key_bytes: bytes | None = None
            for _ in range(value):
                start = self.reader.offset
                key = self.item()
                key_bytes = self.reader.data[start : self.reader.offset]
                require(previous_key_bytes is None or key_bytes > previous_key_bytes, "CBOR map keys are not canonical")
                require(key not in result, "duplicate CBOR map key")
                previous_key_bytes = key_bytes
                result[key] = self.item()
            return result
        raise ValidationError(f"unsupported CBOR major type {major}")

    def complete(self) -> Any:
        value = self.item()
        require(self.reader.offset == len(self.reader.data), "trailing CBOR bytes")
        return value


def cbor_head(major: int, value: int) -> bytes:
    require(value >= 0, "negative CBOR argument")
    prefix = major << 5
    if value < 24:
        return bytes((prefix | value,))
    if value <= 0xFF:
        return bytes((prefix | 24, value))
    if value <= 0xFFFF:
        return bytes((prefix | 25,)) + value.to_bytes(2, "big")
    if value <= 0xFFFFFFFF:
        return bytes((prefix | 26,)) + value.to_bytes(4, "big")
    return bytes((prefix | 27,)) + value.to_bytes(8, "big")


def cbor_encode(value: Any) -> bytes:
    if value is None:
        return b"\xf6"
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if isinstance(value, int):
        return cbor_head(0, value)
    if isinstance(value, bytes):
        return cbor_head(2, len(value)) + value
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return cbor_head(3, len(raw)) + raw
    if isinstance(value, list):
        return cbor_head(4, len(value)) + b"".join(cbor_encode(item) for item in value)
    if isinstance(value, dict):
        encoded = [(cbor_encode(key), cbor_encode(item)) for key, item in value.items()]
        encoded.sort(key=lambda pair: pair[0])
        return cbor_head(5, len(encoded)) + b"".join(key + item for key, item in encoded)
    raise ValidationError(f"unsupported CBOR value {type(value)!r}")


def is_negative_zero(value: float) -> bool:
    return value == 0.0 and math.copysign(1.0, value) < 0.0


def has_exact_integer_keys(value: Any, expected: set[int]) -> bool:
    return type(value) is dict and len(value) == len(expected) and all(type(key) is int for key in value) and set(value) == expected


def unpack_bits(block: bytes, count: int, name: str) -> list[bool]:
    require(len(block) == (count + 7) // 8, f"{name} packed length")
    require(not (count % 8) or block[-1] >> (count % 8) == 0, f"{name} nonzero padding bits")
    return [bool(block[index // 8] & (1 << (index % 8))) for index in range(count)]


def validate_text(value: str, name: str, allow_empty: bool = True) -> None:
    require(type(value) is str, f"{name} is not text")
    require(allow_empty or bool(value), f"{name} is empty")
    require(unicodedata.normalize("NFC", value) == value, f"{name} is not NFC")
    require(all(0x20 <= ord(character) <= 0x7E for character in value), f"{name} contains control/non-ASCII text")


def validate_float32_block(block: bytes, name: str, normalized: bool = False) -> None:
    require(len(block) % 4 == 0, f"{name} float byte count")
    for index in range(0, len(block), 4):
        bits = int.from_bytes(block[index : index + 4], "little")
        value = struct.unpack("<f", block[index : index + 4])[0]
        require(math.isfinite(value), f"{name} contains nonfinite float")
        require(not (bits == 0x80000000), f"{name} contains negative zero")
        if normalized:
            require(0.0 <= value <= 1.0, f"{name} normalized value out of range")


def validate_capture(path: Path) -> dict[str, Any]:
    capture_bytes = path.read_bytes()
    reader = Reader(capture_bytes)
    require(reader.take(8) == MAGIC, "capture magic mismatch")
    require(reader.u32() == 1, "unsupported capture envelope version")
    record_version, sample_id, input_hash, label_hash = (reader.text() for _ in range(4))
    episode_id, candidate_hash, feature_hash, scenario_family = (reader.text() for _ in range(4))
    decision_id = reader.u64()
    captured_at = reader.f64()
    selected_index = reader.u32()
    source_type = reader.u8()
    map_seed, simulation_seed = reader.u64(), reader.u64()
    contract_hashes = [reader.text() for _ in range(8)]
    group_values = [reader.text() for _ in range(8)]
    generator_version, prompt_version, annotator_hash = (reader.text() for _ in range(3))
    agreement = reader.f64()
    parent_policy = reader.text()
    input_cbor, label_cbor, candidate_bytes = reader.blob(), reader.blob(), reader.blob()
    switch_cost_bytes = reader.take(CANDIDATE_COUNT * 4)
    envelope_digest = reader.take(32)
    require(reader.offset == len(reader.data), "trailing capture bytes")
    require(hashlib.sha256(capture_bytes[:-32]).digest() == envelope_digest, "capture envelope checksum mismatch")

    for name, value in (("sample_id", sample_id), ("input_hash", input_hash), ("label_hash", label_hash),
                        ("candidate_hash", candidate_hash), ("feature_hash", feature_hash)):
        require(is_lower_hash(value), f"{name} is not lowercase SHA-256")
    for index, value in enumerate(contract_hashes[:7]):
        require(is_lower_hash(value), f"contract hash {index} invalid")
    require(contract_hashes[7] == "" or is_lower_hash(contract_hashes[7]), "source decision contract hash invalid")
    require(contract_hashes[:3] == [SCHEMA_SHA256, SKILL_REGISTRY_SHA256, GOAL_REGISTRY_SHA256], "generated contract digest mismatch")
    computed_feature_hash = hashlib.sha256(
        FEATURE_MAGIC + b"".join(bytes.fromhex(value) for value in contract_hashes[:6])
    ).hexdigest()
    require(computed_feature_hash == feature_hash, "feature_contract_hash formula mismatch")
    require(parent_policy == "" or is_lower_hash(parent_policy), "parent policy hash invalid")
    require(record_version == "anpc_decision_record_v2", "record version mismatch")
    require(decision_id > 0 and math.isfinite(captured_at) and captured_at >= 0.0 and not is_negative_zero(captured_at), "decision/time invalid")
    require(selected_index < CANDIDATE_COUNT and source_type <= 2, "selection/source invalid")
    validate_text(episode_id, "episode_id", allow_empty=False)
    validate_text(scenario_family, "scenario_family_id", allow_empty=False)
    for index, value in enumerate(group_values):
        validate_text(value, f"group[{index}]")
    validate_text(generator_version, "generator_version")
    validate_text(prompt_version, "prompt_version")
    validate_text(annotator_hash, "annotator_set_hash")
    require(math.isfinite(agreement) and 0.0 <= agreement <= 1.0 and not is_negative_zero(agreement), "annotator agreement invalid")

    require(hashlib.sha256(input_cbor).hexdigest() == input_hash, "input_content_hash mismatch")
    require(hashlib.sha256(label_cbor).hexdigest() == label_hash, "label_block_hash mismatch")
    require(hashlib.sha256(candidate_bytes).hexdigest() == candidate_hash, "candidate_set_hash mismatch")

    input_obj = CborReader(input_cbor).complete()
    label_obj = CborReader(label_cbor).complete()
    require(cbor_encode(input_obj) == input_cbor, "Python input CBOR parity mismatch")
    require(cbor_encode(label_obj) == label_cbor, "Python label CBOR parity mismatch")
    require(has_exact_integer_keys(input_obj, {0, 1, 2, 3, 4}), "input CBOR keys mismatch")
    require(type(input_obj[0]) is str and type(input_obj[1]) is bytes and type(input_obj[2]) is list
            and type(input_obj[3]) is bytes and type(input_obj[4]) is bytes, "input CBOR value types mismatch")
    require(input_obj[0] == record_version and input_obj[1].hex() == feature_hash, "input contract binding mismatch")
    require(input_obj[3] == candidate_bytes, "candidate canonical bytes mismatch")
    raw_tensors = input_obj[2]
    require(type(raw_tensors) is list and len(raw_tensors) == len(TENSOR_LENGTHS)
            and all(type(block) is bytes for block in raw_tensors), "tensor block types mismatch")
    tensors = cast(list[bytes], raw_tensors)
    require(tuple(map(len, tensors)) == TENSOR_LENGTHS, "tensor count/length mismatch")
    for index in FLOAT_TENSORS:
        validate_float32_block(tensors[index], f"tensor[{index}]")
    for index in (3, 7, 9):
        require(all(value in (0, 1) for value in tensors[index]), f"tensor[{index}] bool encoding")
    candidate_mask = tensors[9]
    require(candidate_mask[selected_index] == 1, "selected candidate is masked")

    candidate_reader = Reader(candidate_bytes)
    require(candidate_reader.take(8) == CANDIDATE_MAGIC, "candidate magic mismatch")
    require(candidate_reader.u16() == 1, "candidate serialization version mismatch")
    require(candidate_reader.take(32).hex() == contract_hashes[0], "candidate schema digest mismatch")
    require(candidate_reader.u8() == 17, "candidate target-slot count mismatch")
    handles: list[tuple[int, int, int, int]] = []
    for _ in range(17):
        handles.append((candidate_reader.u8(), candidate_reader.u64(), candidate_reader.u32(), candidate_reader.u64()))
    packed_target_mask = unpack_bits(candidate_reader.take(3), 17, "candidate target mask")
    packed_candidate_mask = unpack_bits(candidate_reader.take(34), CANDIDATE_COUNT, "candidate mask")
    require(candidate_reader.offset == len(candidate_bytes), "trailing candidate canonical bytes")
    target_mask = [bool(value) for value in tensors[3]]
    tensor_candidate_mask = [bool(value) for value in candidate_mask]
    require(packed_target_mask == target_mask, "candidate/tensor target mask mismatch")
    require(packed_candidate_mask == tensor_candidate_mask, "candidate/tensor candidate mask mismatch")
    target_kind_ids = list(struct.unpack("<17q", tensors[2]))
    for slot, (kind, stable_id, generation, revision) in enumerate(handles):
        require(0 <= target_kind_ids[slot] <= 7, f"target kind id out of range at slot {slot}")
        if slot == 16:
            require(target_mask[slot] and kind == 0 and stable_id == generation == revision == 0
                    and target_kind_ids[slot] == 0, "NoTarget slot invalid")
        elif target_mask[slot]:
            require(1 <= kind <= 7 and target_kind_ids[slot] == kind and stable_id > 0 and generation > 0, f"valid target handle mismatch at slot {slot}")
        else:
            require(kind == 0 and stable_id == generation == revision == 0 and target_kind_ids[slot] == 0, f"padded target handle mismatch at slot {slot}")
            require(tensors[1][slot * 48 * 4 : (slot + 1) * 48 * 4] == bytes(48 * 4), f"padded target features nonzero at slot {slot}")
    event_types = struct.unpack("<12q", tensors[5])
    event_slots = struct.unpack("<12q", tensors[6])
    event_mask = [bool(value) for value in tensors[7]]
    for slot in range(12):
        if event_mask[slot]:
            require(1 <= event_types[slot] <= 15, f"event type out of range at slot {slot}")
            require(0 <= event_slots[slot] <= 16, f"event target slot out of range at slot {slot}")
            require(event_slots[slot] == 16 or target_mask[event_slots[slot]], f"event maps to padded target at slot {slot}")
        else:
            require(event_types[slot] == 0 and event_slots[slot] == 16, f"padded event ids invalid at slot {slot}")
            require(tensors[4][slot * 24 * 4 : (slot + 1) * 24 * 4] == bytes(24 * 4), f"padded event features nonzero at slot {slot}")

    for candidate, valid in enumerate(tensor_candidate_mask):
        if not valid:
            require(tensors[8][candidate * 16 * 4 : (candidate + 1) * 16 * 4] == bytes(16 * 4), f"masked candidate features nonzero at row {candidate}")

    terms = input_obj[4]
    require(len(terms) == CANDIDATE_COUNT * 4 and all(value in (0, 1) for value in terms), "switch terms invalid")
    for candidate in range(CANDIDATE_COUNT):
        row = terms[candidate * 4 : candidate * 4 + 4]
        if 17 <= candidate <= 33:
            require(row == b"\0\0\0\0", "Continue switch terms must be zero")
            cost = 0.0
        else:
            cost = min(1.0, max(0.0, 0.45 * row[0] + 0.25 * row[1] + 0.20 * row[2] + 0.10 * row[3]))
        expected = struct.pack("<f", cost)
        actual = switch_cost_bytes[candidate * 4 : candidate * 4 + 4]
        require(actual == expected, f"switch cost mismatch at candidate {candidate}")

    require(has_exact_integer_keys(label_obj, {0, 1, 2, 3, 4, 5, 6}), "label CBOR keys mismatch")
    require(type(label_obj[0]) is bytes and type(label_obj[1]) is list and type(label_obj[2]) is bytes
            and type(label_obj[3]) is bytes and (label_obj[4] is None or type(label_obj[4]) is bool)
            and type(label_obj[5]) is bytes and type(label_obj[6]) is list, "label CBOR value types mismatch")
    acceptable = label_obj[0]
    require(len(acceptable) == 34, "acceptable bitset invalid")
    acceptable_bits = [(acceptable[i // 8] >> (i % 8)) & 1 for i in range(CANDIDATE_COUNT)]
    require(all(not acceptable_bits[i] or candidate_mask[i] for i in range(CANDIDATE_COUNT)), "acceptable candidate is masked")
    pairs = label_obj[1]
    require(all(type(pair) is list and len(pair) == 2
                and type(pair[0]) is int and type(pair[1]) is int
                and 0 <= pair[0] < CANDIDATE_COUNT and 0 <= pair[1] < CANDIDATE_COUNT
                for pair in pairs), "preference pair invalid")
    require(all(candidate_mask[pair[0]] and candidate_mask[pair[1]] for pair in pairs), "preference pair contains masked candidate")
    require(pairs == sorted(pairs) and len({tuple(pair) for pair in pairs}) == len(pairs), "preference pairs noncanonical")
    require(len(label_obj[2]) == CANDIDATE_COUNT * 4 * 4, "parameter target size")
    validate_float32_block(label_obj[2], "parameter_target", normalized=True)
    parameter_mask = label_obj[3]
    require(len(parameter_mask) == CANDIDATE_COUNT * 4 and all(v in (0, 1) for v in parameter_mask), "parameter mask invalid")
    for candidate in range(CANDIDATE_COUNT):
        for parameter in range(4):
            if parameter_mask[candidate * 4 + parameter]:
                require(bool(acceptable_bits[candidate]), f"parameter label on unacceptable candidate {candidate}")
                require(ACTIVE_PARAMETER_SLOTS[candidate // 17][parameter], f"parameter label on inactive slot {candidate}:{parameter}")
    selected_acceptable = label_obj[4]
    require(selected_acceptable is None or selected_acceptable == bool(acceptable_bits[selected_index]), "selected acceptable mismatch")
    require(len(label_obj[5]) == 4, "confidence size")
    confidence_bits = int.from_bytes(label_obj[5], "little")
    confidence = struct.unpack("<f", label_obj[5])[0]
    require(math.isfinite(confidence) and 0.0 <= confidence <= 1.0 and confidence_bits != 0x80000000, "confidence invalid")
    reason_tags = label_obj[6]
    require(reason_tags == sorted(set(reason_tags)), "reason tags noncanonical")
    for index, tag in enumerate(reason_tags):
        validate_text(tag, f"reason_tag[{index}]", allow_empty=False)

    episode = episode_id.encode("ascii")
    sample_material = SAMPLE_MAGIC + bytes.fromhex(input_hash) + struct.pack("<I", len(episode)) + episode + struct.pack("<Q", decision_id) + bytes.fromhex(label_hash)
    require(hashlib.sha256(sample_material).hexdigest() == sample_id, "sample_id mismatch")

    return {
        "path": str(path),
        "bytes": len(reader.data),
        "record_version": record_version,
        "sample_id": sample_id,
        "input_content_hash": input_hash,
        "label_block_hash": label_hash,
        "candidate_set_hash": candidate_hash,
        "feature_contract_hash": feature_hash,
        "episode_id": episode_id,
        "decision_id": decision_id,
        "selected_candidate_index": selected_index,
        "source_type": source_type,
        "map_seed": map_seed,
        "simulation_seed": simulation_seed,
        "scenario_family_id": scenario_family,
        "group_dimensions": group_values,
        "generator_version": generator_version,
        "prompt_version": prompt_version,
        "annotator_set_hash": annotator_hash,
        "tensor_lengths": list(TENSOR_LENGTHS),
        "valid_candidate_count": sum(candidate_mask),
        "acceptable_candidate_count": sum(acceptable_bits),
        "canonical_cbor_parity": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_capture(args.capture)
    except (OSError, ValidationError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"PASS: {result['sample_id']} tensors={result['tensor_lengths']} valid_candidates={result['valid_candidate_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
