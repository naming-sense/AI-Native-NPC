#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIXTURE = ROOT / "tests/fixtures/phase0_golden.anpcv2"
GENERATED = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
TEST_HELPERS = ROOT / "tests/test_validate_anpc_capture_v2.py"


def _import(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    generated = _import("anpc_generated_for_capture_update", GENERATED)
    helpers = _import("anpc_capture_test_helpers_for_update", TEST_HELPERS)
    parts = helpers._parse_capture(FIXTURE.read_bytes())
    parts[8][0:3] = [
        generated.SCHEMA_SOURCE_SHA256,
        generated.SKILL_REGISTRY_SHA256,
        generated.GOAL_REGISTRY_SHA256,
    ]
    feature_hash = hashlib.sha256(
        b"ANPCFEAT1" + b"".join(bytes.fromhex(value) for value in parts[8][:6])
    ).hexdigest()
    parts[1][6] = feature_hash
    input_obj = helpers.CborReader(parts[13][0]).complete()
    input_obj[1] = bytes.fromhex(feature_hash)
    candidate_bytes = bytearray(parts[13][2])
    if bytes(candidate_bytes[:8]) != b"ANPCSET2":
        raise RuntimeError("candidate fixture magic mismatch")
    candidate_bytes[10:42] = bytes.fromhex(generated.SCHEMA_SOURCE_SHA256)
    input_obj[3] = bytes(candidate_bytes)
    helpers._refresh_identity(parts, input_obj=input_obj, candidate_bytes=bytes(candidate_bytes))
    FIXTURE.write_bytes(helpers._rebuild_capture(parts))
    print(f"updated {FIXTURE} ({FIXTURE.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
