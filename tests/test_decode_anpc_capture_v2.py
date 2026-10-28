from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable, cast
from unittest.mock import patch

from tools import validate_anpc_capture_v2 as capture
from tests.test_validate_anpc_capture_v2 import (
    FIXTURE,
    _parse_capture,
    _rebuild_capture,
    _refresh_identity,
)


SUMMARY_KEYS = {
    "path", "bytes", "record_version", "sample_id", "input_content_hash",
    "label_block_hash", "candidate_set_hash", "feature_contract_hash", "episode_id",
    "decision_id", "selected_candidate_index", "source_type", "map_seed",
    "simulation_seed", "scenario_family_id", "group_dimensions", "generator_version",
    "prompt_version", "annotator_set_hash", "tensor_lengths", "valid_candidate_count",
    "acceptable_candidate_count", "canonical_cbor_parity",
}
PAYLOAD_KEYS = {
    "captured_at_server_time", "contract_hashes", "annotator_agreement", "parent_policy_hash",
    "input_cbor", "label_cbor", "candidate_bytes", "tensor_blocks", "target_handles",
    "switch_cost_terms", "captured_switch_cost", "labels",
}


def _marker(data: bytes) -> bytes:
    prefix = (capture.COMMIT_MAGIC + struct.pack("<IQ", 1, len(data))
              + hashlib.sha256(data).digest())
    return prefix + hashlib.sha256(prefix).digest()


class CommittedCaptureDecoderTests(unittest.TestCase):
    def _decoder(self, name="decode_committed_capture_bytes") -> Callable[..., dict[str, Any]]:
        decoder = getattr(capture, name, None)
        if not callable(decoder):
            self.fail(f"{name} callable is required")
        return cast(Callable[..., dict[str, Any]], decoder)

    def _assert_payload_matches(self, decoded, parts):
        input_obj = capture.CborReader(parts[13][0]).complete()
        label_obj = capture.CborReader(parts[13][1]).complete()
        self.assertEqual(set(decoded), SUMMARY_KEYS | PAYLOAD_KEYS | {"committed_marker"})
        self.assertEqual(decoded["captured_at_server_time"], parts[3])
        self.assertEqual(decoded["contract_hashes"], parts[8])
        self.assertEqual(len(decoded["contract_hashes"]), 8)
        self.assertEqual(decoded["annotator_agreement"], parts[11])
        self.assertEqual(decoded["parent_policy_hash"], parts[12])
        for key, expected in zip(("input_cbor", "label_cbor", "candidate_bytes"), parts[13]):
            self.assertIs(type(decoded[key]), bytes)
            self.assertEqual(decoded[key], expected)
        self.assertEqual(decoded["tensor_blocks"], input_obj[2])
        self.assertEqual(len(decoded["tensor_blocks"]), 10)
        self.assertTrue(all(type(block) is bytes for block in decoded["tensor_blocks"]))

        reader = capture.Reader(parts[13][2])
        reader.take(8 + 2 + 32)
        expected_handles = [
            {"kind": reader.u8(), "stable_id": reader.u64(),
             "generation": reader.u32(), "revision": reader.u64()}
            for _ in range(reader.u8())
        ]
        self.assertEqual(decoded["target_handles"], expected_handles)
        self.assertEqual(len(decoded["target_handles"]), 17)
        expected_terms = [[bool(value) for value in input_obj[4][offset:offset + 4]]
                          for offset in range(0, 272 * 4, 4)]
        self.assertEqual(decoded["switch_cost_terms"], expected_terms)
        self.assertEqual(len(decoded["switch_cost_terms"]), 272)
        self.assertTrue(all(type(row) is list and len(row) == 4
                            and all(type(value) is bool for value in row)
                            for row in decoded["switch_cost_terms"]))
        self.assertEqual(decoded["captured_switch_cost"], list(struct.unpack("<272f", parts[14])))
        self.assertTrue(all(type(value) is float for value in decoded["captured_switch_cost"]))
        labels = decoded["labels"]
        self.assertEqual(labels, {
            "acceptable_candidate_indices": [i for i in range(272) if label_obj[0][i // 8] & (1 << (i % 8))],
            "preference_pairs": label_obj[1],
            "parameter_target_norm": list(struct.unpack("<1088f", label_obj[2])),
            "parameter_label_mask": [bool(value) for value in label_obj[3]],
            "selected_is_acceptable": label_obj[4],
            "label_confidence": struct.unpack("<f", label_obj[5])[0],
            "reason_tags": label_obj[6],
        })
        self.assertIs(labels["selected_is_acceptable"], label_obj[4])
        self.assertEqual(len(labels["parameter_target_norm"]), 1088)
        self.assertEqual(len(labels["parameter_label_mask"]), 1088)
        self.assertTrue(all(type(value) is float for value in labels["parameter_target_norm"]))
        self.assertTrue(all(type(value) is bool for value in labels["parameter_label_mask"]))

        # Rebuild canonical CBOR from the exposed values, not just retained raw blobs.
        rebuilt_input = capture.cbor_encode({
            0: decoded["record_version"], 1: bytes.fromhex(decoded["feature_contract_hash"]),
            2: decoded["tensor_blocks"], 3: decoded["candidate_bytes"],
            4: bytes(value for row in decoded["switch_cost_terms"] for value in row),
        })
        acceptable = bytearray(34)
        for index in labels["acceptable_candidate_indices"]:
            acceptable[index // 8] |= 1 << (index % 8)
        rebuilt_labels = capture.cbor_encode({
            0: bytes(acceptable), 1: labels["preference_pairs"],
            2: struct.pack("<1088f", *labels["parameter_target_norm"]),
            3: bytes(labels["parameter_label_mask"]), 4: labels["selected_is_acceptable"],
            5: struct.pack("<f", labels["label_confidence"]), 6: labels["reason_tags"],
        })
        self.assertEqual(rebuilt_input, decoded["input_cbor"])
        self.assertEqual(rebuilt_labels, decoded["label_cbor"])
        for blob, hash_key in ((rebuilt_input, "input_content_hash"),
                               (rebuilt_labels, "label_block_hash"),
                               (decoded["candidate_bytes"], "candidate_set_hash")):
            self.assertEqual(hashlib.sha256(blob).hexdigest(), decoded[hash_key])

    def test_golden_decode_preserves_validated_payload_and_summary(self):
        decoder = self._decoder()
        body = FIXTURE.read_bytes()
        decoded = decoder(body, _marker(body), path=FIXTURE)
        self._assert_payload_matches(decoded, _parse_capture(body))
        self.assertEqual({key: decoded[key] for key in SUMMARY_KEYS}, capture.validate_capture(FIXTURE))
        self.assertEqual(decoded["committed_marker"], str(FIXTURE) + ".committed")

    def test_bytes_decoder_has_no_filesystem_reads_and_defaults_to_memory_path(self):
        decoder = self._decoder()
        body = FIXTURE.read_bytes()
        marker = _marker(body)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("filesystem read")), \
             patch("builtins.open", side_effect=AssertionError("filesystem read")), \
             patch("io.open", side_effect=AssertionError("filesystem read")):
            decoded = decoder(body, marker)
        self.assertEqual(decoded["path"], "<memory>")
        self.assertEqual(decoded["committed_marker"], "<memory>.committed")
        self._assert_payload_matches(decoded, _parse_capture(body))

    def test_raw_sources_metadata_and_nonempty_labels_are_preserved(self):
        decoder = self._decoder()
        fixture_bytes = FIXTURE.read_bytes()
        for source in (0, 1, 2):
            for selected_acceptable in (None, False, True):
                with self.subTest(source=source, selected_acceptable=selected_acceptable):
                    parts = _parse_capture(fixture_bytes)
                    input_obj = capture.CborReader(parts[13][0]).complete()
                    labels = capture.CborReader(parts[13][1]).complete()
                    selected, extra = parts[4], 268
                    parts[3], parts[5], parts[6], parts[7] = 42.25, source, 0, 2**64 - 1
                    parts[1][7] = "decoder_raw_family"
                    parts[8][7] = hashlib.sha256(b"decoder-source-contract").hexdigest()
                    parts[11] = 0.375
                    parts[12] = hashlib.sha256(b"decoder-parent-policy").hexdigest()
                    mask = bytearray(input_obj[2][9])
                    mask[extra] = 1
                    input_obj[2][9] = bytes(mask)
                    candidate = bytearray(parts[13][2])
                    candidate[8 + 2 + 32 + 1 + 17 * 21 + 3 + extra // 8] |= 1 << (extra % 8)
                    input_obj[3] = bytes(candidate)
                    terms = bytearray(input_obj[4])
                    terms[selected * 4:selected * 4 + 4] = bytes((1, 0, 1, 0))
                    terms[extra * 4:extra * 4 + 4] = bytes((0, 1, 0, 1))
                    input_obj[4] = bytes(terms)
                    costs = bytearray(parts[14])
                    struct.pack_into("<f", costs, selected * 4, 0.45 + 0.20)
                    struct.pack_into("<f", costs, extra * 4, 0.25 + 0.10)
                    parts[14] = bytes(costs)
                    acceptable = bytearray(labels[0])
                    acceptable[extra // 8] |= 1 << (extra % 8)
                    if selected_acceptable is False:
                        acceptable[selected // 8] &= ~(1 << (selected % 8))
                    labels[0] = bytes(acceptable)
                    labels[1] = [[selected, extra], [extra, selected]]
                    labels[2] = struct.pack("<1088f", *([0.0, 0.25, 0.5, 0.75] * 272))
                    parameter_mask = bytearray(labels[3])
                    parameter_mask[extra * 4] = 1
                    labels[3] = bytes(parameter_mask)
                    labels[4], labels[5], labels[6] = selected_acceptable, struct.pack("<f", 0.375), ["decoder_test", "raw_label"]
                    _refresh_identity(parts, input_obj=input_obj, label_obj=labels, candidate_bytes=bytes(candidate))
                    body = _rebuild_capture(parts)
                    decoded = decoder(body, _marker(body))
                    self._assert_payload_matches(decoded, parts)
                    self.assertEqual(decoded["source_type"], source)
                    self.assertEqual(decoded["scenario_family_id"], parts[1][7])
                    self.assertEqual(decoded["map_seed"], parts[6])
                    self.assertEqual(decoded["simulation_seed"], parts[7])

    def test_file_decoder_reads_each_image_once_despite_path_replacement(self):
        decoder = self._decoder("decode_committed_capture")
        body = FIXTURE.read_bytes()
        original_parts = _parse_capture(body)
        replacement_parts = _parse_capture(body)
        labels = capture.CborReader(replacement_parts[13][1]).complete()
        labels[6] = ["replacement"]
        _refresh_identity(replacement_parts, label_obj=labels)
        replacement = _rebuild_capture(replacement_parts)
        path = Path("capture.anpcv2")
        marker_path = Path(str(path) + ".committed")
        images = {path: body, marker_path: _marker(body)}

        def read_image(requested):
            image = images[requested]
            if requested == marker_path:
                images.update({path: replacement, marker_path: _marker(replacement)})
            return image

        with patch.object(Path, "read_bytes", autospec=True, side_effect=read_image) as read_bytes:
            decoded = decoder(path)
        self.assertEqual(read_bytes.call_count, 2)
        self.assertEqual([call.args[0] for call in read_bytes.call_args_list], [path, marker_path])
        self._assert_payload_matches(decoded, original_parts)
        self.assertEqual(decoded["sample_id"], original_parts[1][1])
        self.assertNotEqual(decoded["sample_id"], replacement_parts[1][1])
        self.assertEqual(decoded["path"], str(path))
        self.assertEqual(decoded["committed_marker"], str(marker_path))

    def test_file_decoder_requires_marker(self):
        decoder = self._decoder("decode_committed_capture")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.anpcv2"
            path.write_bytes(FIXTURE.read_bytes())
            with self.assertRaises(OSError):
                decoder(path)

    def test_mutable_and_non_bytes_inputs_are_rejected(self):
        decoder = self._decoder()
        body = FIXTURE.read_bytes()
        marker = _marker(body)
        for convert in (bytearray, memoryview, lambda _: None, lambda _: ""):
            for field in ("body", "marker"):
                with self.subTest(convert=convert, field=field):
                    with self.assertRaises(capture.ValidationError):
                        decoder(convert(body) if field == "body" else body,
                                convert(marker) if field == "marker" else marker)

    def test_marker_length_hash_digest_and_exact_body_binding_are_required(self):
        decoder = self._decoder()
        body = FIXTURE.read_bytes()
        marker = _marker(body)
        malformed = {"absent": b"", "truncated": marker[:-1], "trailing": marker + b"\0",
                     "digest": marker[:-1] + bytes((marker[-1] ^ 1,))}
        for name, offset in (("magic", 0), ("version", 8), ("length", 12), ("body_hash", 20)):
            prefix = bytearray(marker[:-32])
            prefix[offset] ^= 1
            malformed[name] = bytes(prefix) + hashlib.sha256(prefix).digest()
        other_parts = _parse_capture(body)
        other_parts[5] = 1
        other_body = _rebuild_capture(other_parts)
        self.assertEqual(len(other_body), len(body))
        malformed["different_valid_body_same_length"] = _marker(other_body)
        for name, invalid_marker in malformed.items():
            with self.subTest(marker=name):
                with self.assertRaisesRegex(capture.ValidationError, "committed marker"):
                    decoder(body, invalid_marker)

    def test_rebound_marker_cannot_hide_envelope_tamper(self):
        decoder = self._decoder()
        body = FIXTURE.read_bytes()
        tampered = body[:-1] + bytes((body[-1] ^ 1,))
        with self.assertRaisesRegex(capture.ValidationError, "envelope checksum"):
            decoder(tampered, _marker(tampered))

    def test_rehashed_payloads_still_require_semantic_validation(self):
        decoder = self._decoder()
        fixture_bytes = FIXTURE.read_bytes()
        cases = (
            "selection", "tensor", "handle", "candidate_mask", "switch_terms", "switch_cost",
            "parameter_mask", "parameter_target", "selected_label", "reason_tag", "sample_id",
        )
        for case in cases:
            with self.subTest(case=case):
                parts = _parse_capture(fixture_bytes)
                input_obj = capture.CborReader(parts[13][0]).complete()
                labels = capture.CborReader(parts[13][1]).complete()
                if case == "selection":
                    parts[4] = 0
                    expected = "selected candidate is masked"
                elif case == "tensor":
                    input_obj[2][0] = struct.pack("<f", float("nan")) + input_obj[2][0][4:]
                    expected = "nonfinite float"
                elif case == "handle":
                    kinds = bytearray(input_obj[2][2])
                    struct.pack_into("<q", kinds, 0, 99)
                    input_obj[2][2] = bytes(kinds)
                    expected = "target kind id out of range"
                elif case == "candidate_mask":
                    candidate = bytearray(parts[13][2])
                    candidate[-1] ^= 1
                    input_obj[3] = bytes(candidate)
                    _refresh_identity(parts, candidate_bytes=bytes(candidate))
                    expected = "candidate/tensor candidate mask mismatch"
                elif case == "switch_terms":
                    terms = bytearray(input_obj[4])
                    terms[17 * 4] = 1
                    input_obj[4] = bytes(terms)
                    expected = "Continue switch terms must be zero"
                elif case == "switch_cost":
                    parts[14] = struct.pack("<f", 0.5) + parts[14][4:]
                    expected = "switch cost mismatch"
                elif case == "parameter_mask":
                    mask = bytearray(labels[3])
                    mask[parts[4] * 4 + 2] = 1
                    labels[3] = bytes(mask)
                    expected = "parameter label on inactive slot"
                elif case == "parameter_target":
                    labels[2] = struct.pack("<f", 1.25) + labels[2][4:]
                    expected = "normalized value out of range"
                elif case == "selected_label":
                    labels[4] = 1
                    expected = "label CBOR value types mismatch"
                elif case == "reason_tag":
                    labels[6] = ["bad\ntag"]
                    expected = "contains control/non-ASCII text"
                else:
                    expected = "sample_id mismatch"
                _refresh_identity(parts, input_obj=input_obj, label_obj=labels)
                if case == "sample_id":
                    parts[1][1] = "0" * 64
                body = _rebuild_capture(parts)
                with self.assertRaisesRegex(capture.ValidationError, expected):
                    decoder(body, _marker(body))

    def test_legacy_summary_shapes_and_cli_remain_unchanged(self):
        body = FIXTURE.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.anpcv2"
            path.write_bytes(body)
            marker_path = Path(str(path) + ".committed")
            marker_path.write_bytes(_marker(body))
            summary = capture.validate_capture(path)
            committed = capture.validate_committed_capture(path)
            self.assertEqual(set(summary), SUMMARY_KEYS)
            self.assertEqual(committed, dict(summary, committed_marker=str(marker_path)))
            command = [sys.executable, str(Path(capture.__file__)), str(path)]
            json_run = subprocess.run(command + ["--json"], capture_output=True, text=True)
            self.assertEqual(json_run.returncode, 0, json_run.stderr)
            self.assertEqual(json.loads(json_run.stdout), committed)
            text_run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(text_run.returncode, 0, text_run.stderr)
            self.assertEqual(text_run.stdout, f"PASS: {summary['sample_id']} tensors={summary['tensor_lengths']} valid_candidates={summary['valid_candidate_count']}\n")
            marker_path.unlink()
            failed_run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(failed_run.returncode, 1, failed_run.stderr)
            self.assertTrue(failed_run.stdout.startswith("FAIL: "))


if __name__ == "__main__":
    unittest.main()
