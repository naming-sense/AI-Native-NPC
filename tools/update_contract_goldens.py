#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_PY = ROOT / "generated/python/ai_native_npc_contracts_generated.py"
GENERATED_CPP = ROOT / "generated/cpp/AINativeNPCContracts.generated.h"
DISCRETE = ROOT / "tests/golden/discrete_hash_vectors.json"
NORMALIZER = ROOT / "tests/golden/normalizer_vectors.json"


def _load_generated():
    spec = importlib.util.spec_from_file_location("anpc_contracts_for_golden_update", GENERATED_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATED_PY}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    generated = _load_generated()
    discrete = json.loads(DISCRETE.read_text(encoding="utf-8"))
    discrete["contract_revision"] = generated.CONTRACT_REVISION
    discrete["schema_source_sha256"] = generated.SCHEMA_SOURCE_SHA256
    discrete["generated_cpp_sha256"] = hashlib.sha256(GENERATED_CPP.read_bytes()).hexdigest()
    discrete["generated_python_sha256"] = hashlib.sha256(GENERATED_PY.read_bytes()).hexdigest()

    decision = discrete["decision_contract"]
    digests = decision["digests"]
    digests["schema_source_sha256"] = generated.SCHEMA_SOURCE_SHA256
    digests["skill_registry_sha256"] = generated.SKILL_REGISTRY_SHA256
    digests["goal_registry_sha256"] = generated.GOAL_REGISTRY_SHA256
    raw = generated.decision_contract_canonical_bytes(digests)
    decision["canonical_bytes_hex"] = raw.hex()
    decision["sha256"] = hashlib.sha256(raw).hexdigest()

    candidate_count = int(generated.CONSTANTS["candidate_count"])
    target_slot_count = int(generated.CONSTANTS["total_target_slots"])
    for vector in discrete["vectors"]:
        handles = [generated.TargetHandle(**handle) for handle in vector["handles"]]
        target_mask = vector["target_mask"]
        candidate_mask = [False] * candidate_count
        for index in vector["candidate_mask_true_indices"]:
            candidate_mask[index] = True
        canonical = generated.candidate_set_canonical_bytes(handles, target_mask, candidate_mask)
        vector["canonical_bytes_hex"] = canonical.hex()
        vector["sha256"] = hashlib.sha256(canonical).hexdigest()
        vector["target_mask_bytes_hex"] = generated.pack_bits_lsb_first(
            target_mask, target_slot_count
        ).hex()
        vector["candidate_mask_bytes_hex"] = generated.pack_bits_lsb_first(
            candidate_mask, candidate_count
        ).hex()

    normalizer = json.loads(NORMALIZER.read_text(encoding="utf-8"))
    normalizer["contract_revision"] = generated.CONTRACT_REVISION

    DISCRETE.write_text(json.dumps(discrete, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    NORMALIZER.write_text(json.dumps(normalizer, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"contract_revision": generated.CONTRACT_REVISION, "vectors": len(discrete["vectors"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
