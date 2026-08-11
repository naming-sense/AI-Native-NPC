from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from tools.validate_anpc_capture_v2 import (
    CborReader,
    Reader,
    SAMPLE_MAGIC,
    ValidationError,
    cbor_encode,
    validate_capture,
)


FIXTURE = Path(__file__).parent / "fixtures" / "phase0_golden.anpcv2"


def _parse_capture(data: bytes) -> list:
    reader = Reader(data)
    if reader.take(8) != b"ANPCCAP2":
        raise AssertionError("fixture magic")
    version = reader.u32()
    texts = [reader.text() for _ in range(8)]
    decision_id = reader.u64()
    captured_at = reader.f64()
    selected = reader.u32()
    source_type = reader.u8()
    map_seed, simulation_seed = reader.u64(), reader.u64()
    contracts = [reader.text() for _ in range(8)]
    groups = [reader.text() for _ in range(8)]
    provenance = [reader.text() for _ in range(3)]
    agreement = reader.f64()
    parent_policy = reader.text()
    blobs = [reader.blob() for _ in range(3)]
    switch_costs = reader.take(272 * 4)
    reader.take(32)
    return [version, texts, decision_id, captured_at, selected, source_type, map_seed, simulation_seed,
            contracts, groups, provenance, agreement, parent_policy, blobs, switch_costs]


def _text(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("<I", len(raw)) + raw


def _blob(value: bytes) -> bytes:
    return struct.pack("<I", len(value)) + value


def _rebuild_capture(parts: list) -> bytes:
    (version, texts, decision_id, captured_at, selected, source_type, map_seed, simulation_seed,
     contracts, groups, provenance, agreement, parent_policy, blobs, switch_costs) = parts
    body = b"ANPCCAP2" + struct.pack("<I", version) + b"".join(_text(value) for value in texts)
    body += struct.pack("<QdIBQQ", decision_id, captured_at, selected, source_type, map_seed, simulation_seed)
    body += b"".join(_text(value) for value in contracts + groups + provenance)
    body += struct.pack("<d", agreement) + _text(parent_policy)
    body += b"".join(_blob(value) for value in blobs) + switch_costs
    return body + hashlib.sha256(body).digest()


def _refresh_identity(parts: list, input_obj=None, label_obj=None, candidate_bytes=None) -> None:
    texts, blobs = parts[1], parts[13]
    if candidate_bytes is not None:
        blobs[2] = candidate_bytes
        texts[5] = hashlib.sha256(candidate_bytes).hexdigest()
    if input_obj is not None:
        blobs[0] = cbor_encode(input_obj)
        texts[2] = hashlib.sha256(blobs[0]).hexdigest()
    if label_obj is not None:
        blobs[1] = cbor_encode(label_obj)
        texts[3] = hashlib.sha256(blobs[1]).hexdigest()
    episode = texts[4].encode("ascii")
    material = (SAMPLE_MAGIC + bytes.fromhex(texts[2]) + struct.pack("<I", len(episode)) + episode
                + struct.pack("<Q", parts[2]) + bytes.fromhex(texts[3]))
    texts[1] = hashlib.sha256(material).hexdigest()


class CaptureV2ValidatorTests(unittest.TestCase):
    def _expect_semantic_rejection(self, mutation) -> None:
        parts = _parse_capture(FIXTURE.read_bytes())
        input_obj = CborReader(parts[13][0]).complete()
        label_obj = CborReader(parts[13][1]).complete()
        mutation(parts, input_obj, label_obj)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "semantic_tamper.anpcv2"
            path.write_bytes(_rebuild_capture(parts))
            with self.assertRaises(ValidationError):
                validate_capture(path)

    def test_unreal_golden_has_python_canonical_parity(self) -> None:
        result = validate_capture(FIXTURE)
        self.assertTrue(result["canonical_cbor_parity"])
        self.assertEqual(result["feature_contract_hash"], "c6a063be57d82813ad6001af98b86c92ae9c5cf2d120bb7a2209e185bfb77634")
        self.assertEqual(result["record_version"], "anpc_decision_record_v2")
        self.assertEqual(result["tensor_lengths"], [512, 3264, 136, 17, 1152, 96, 96, 12, 17408, 272])
        self.assertEqual(result["valid_candidate_count"], 2)
        self.assertEqual(result["acceptable_candidate_count"], 1)

    def test_metadata_tamper_is_rejected(self) -> None:
        corrupted = bytearray(FIXTURE.read_bytes())
        offset = corrupted.find(b"phase0_test_map")
        self.assertGreaterEqual(offset, 0)
        corrupted[offset] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata_tamper.anpcv2"
            path.write_bytes(corrupted)
            with self.assertRaises(ValidationError):
                validate_capture(path)

    def test_single_byte_tamper_is_rejected(self) -> None:
        corrupted = bytearray(FIXTURE.read_bytes())
        corrupted[-1] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tampered.anpcv2"
            path.write_bytes(corrupted)
            with self.assertRaises(ValidationError):
                validate_capture(path)

    def test_candidate_tensor_mask_divergence_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            candidate = bytearray(parts[13][2])
            candidate[-1] ^= 1
            input_obj[3] = bytes(candidate)
            _refresh_identity(parts, input_obj=input_obj, candidate_bytes=bytes(candidate))
        self._expect_semantic_rejection(mutate)

    def test_out_of_range_target_kind_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            tensors = list(input_obj[2])
            kinds = bytearray(tensors[2])
            struct.pack_into("<q", kinds, 0, 99)
            tensors[2] = bytes(kinds)
            input_obj[2] = tensors
            _refresh_identity(parts, input_obj=input_obj)
        self._expect_semantic_rejection(mutate)

    def test_inactive_parameter_label_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            mask = bytearray(label_obj[3])
            mask[parts[4] * 4 + 2] = 1
            label_obj[3] = bytes(mask)
            _refresh_identity(parts, label_obj=label_obj)
        self._expect_semantic_rejection(mutate)

    def test_integer_selected_acceptable_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            label_obj[4] = 1
            _refresh_identity(parts, label_obj=label_obj)
        self._expect_semantic_rejection(mutate)

    def test_boolean_map_key_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            feature_contract = input_obj.pop(1)
            input_obj[True] = feature_contract
            _refresh_identity(parts, input_obj=input_obj)
        self._expect_semantic_rejection(mutate)

    def test_negative_zero_capture_time_is_rejected(self) -> None:
        def mutate(parts, input_obj, label_obj):
            parts[3] = -0.0
        self._expect_semantic_rejection(mutate)

    def test_negative_zero_annotator_agreement_is_rejected(self) -> None:
        def mutate(parts, input_obj, label_obj):
            parts[11] = -0.0
        self._expect_semantic_rejection(mutate)

    def test_nonzero_notarget_identity_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            candidate = bytearray(parts[13][2])
            slot_16_offset = 8 + 2 + 32 + 1 + 16 * 21
            struct.pack_into("<Q", candidate, slot_16_offset + 1, 1)
            input_obj[3] = bytes(candidate)
            _refresh_identity(parts, input_obj=input_obj, candidate_bytes=bytes(candidate))
        self._expect_semantic_rejection(mutate)

    def test_control_character_reason_tag_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            label_obj[6] = ["bad\ntag"]
            _refresh_identity(parts, label_obj=label_obj)
        self._expect_semantic_rejection(mutate)

    def test_non_text_reason_tag_is_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            label_obj[6] = [1]
            _refresh_identity(parts, label_obj=label_obj)
        self._expect_semantic_rejection(mutate)

    def test_tensor_blocks_must_remain_byte_strings_after_rehash(self) -> None:
        for tensor_index in (3, 7, 9):
            with self.subTest(tensor_index=tensor_index):
                def mutate(parts, input_obj, label_obj, index=tensor_index):
                    tensors = list(input_obj[2])
                    tensors[index] = list(tensors[index])
                    input_obj[2] = tensors
                    _refresh_identity(parts, input_obj=input_obj)
                self._expect_semantic_rejection(mutate)

    def test_boolean_preference_indices_are_rejected_after_rehash(self) -> None:
        def mutate(parts, input_obj, label_obj):
            tensors = list(input_obj[2])
            candidate_mask = bytearray(tensors[9])
            candidate_mask[1] = 1
            tensors[9] = bytes(candidate_mask)
            input_obj[2] = tensors

            candidate = bytearray(parts[13][2])
            candidate_mask_offset = 8 + 2 + 32 + 1 + 17 * 21 + 3
            candidate[candidate_mask_offset] |= 1 << 1
            input_obj[3] = bytes(candidate)
            label_obj[1] = [[True, True]]
            _refresh_identity(
                parts,
                input_obj=input_obj,
                label_obj=label_obj,
                candidate_bytes=bytes(candidate),
            )
        self._expect_semantic_rejection(mutate)

    def test_candidate_268_acceptable_bit_is_valid(self) -> None:
        parts = _parse_capture(FIXTURE.read_bytes())
        input_obj = CborReader(parts[13][0]).complete()
        label_obj = CborReader(parts[13][1]).complete()

        tensors = list(input_obj[2])
        candidate_mask = bytearray(tensors[9])
        candidate_mask[268] = 1
        tensors[9] = bytes(candidate_mask)
        input_obj[2] = tensors

        candidate = bytearray(parts[13][2])
        candidate_mask_offset = 8 + 2 + 32 + 1 + 17 * 21 + 3
        candidate[candidate_mask_offset + 268 // 8] |= 1 << (268 % 8)
        input_obj[3] = bytes(candidate)

        acceptable = bytearray(label_obj[0])
        acceptable[268 // 8] |= 1 << (268 % 8)
        label_obj[0] = bytes(acceptable)
        _refresh_identity(
            parts,
            input_obj=input_obj,
            label_obj=label_obj,
            candidate_bytes=bytes(candidate),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate_268_acceptable.anpcv2"
            path.write_bytes(_rebuild_capture(parts))
            result = validate_capture(path)
            self.assertEqual(result["acceptable_candidate_count"], 2)


if __name__ == "__main__":
    unittest.main()
