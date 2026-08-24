#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


REQUIRED_EVIDENCE_IDS = {
    "contract_tests",
    "editor_build",
    "ort_nne_parity",
    "packaged_nne_smoke",
    "nne_perf",
    "focused_automation",
    "broad_automation",
    "production_build",
    "production_pie",
    "data_validation",
    "independent_review",
}
EXECUTION_EVIDENCE_IDS = REQUIRED_EVIDENCE_IDS - {"independent_review"}
RELEASE_SCOPE_ID = "GuardPhase0/InvestigateDisturbance/Resolve"
DEFAULT_UNREAL_ROOT = Path("/mnt/d/Codex-cli/NeuralProject/NeuralGame")
REQUIRED_BUNDLE_FILES = {
    "calibration_ood_asset.json",
    "dataset_manifest.json",
    "evaluation_report.json",
    "golden_inputs.npz",
    "golden_outputs_fp32.npz",
    "model.safetensors",
    "model_config.json",
    "perf_manifest.json",
    "policy.onnx",
    "split_assignment.csv",
    "train_config.json",
    "train_environment.lock.json",
    "train_report.json",
}
REQUIRED_ARTIFACTS = {
    ("contract", "docs/current/production-resolve-v1-implementation-plan.md"),
    ("contract", "docs/current/technical-requirements.md"),
    ("contract", "contracts/current/ai_native_npc_schema_v2_0.yaml"),
    ("contract", "contracts/current/goal_registry_v1.yaml"),
    ("contract", "contracts/current/skill_registry_v1.yaml"),
    ("contract", "tools/generate_contracts.py"),
    ("contract", "tools/generate_goal_gameplay_semantics_v1.py"),
    ("contract", "tools/generate_skill_execution_semantics_v1.py"),
    ("contract", "generated/contract_manifest.json"),
    ("contract", "generated/contract-lock.json"),
    ("contract", "generated/python/ai_native_npc_contracts_generated.py"),
    ("contract", "generated/cpp/AINativeNPCContracts.generated.h"),
    ("contract", "generated/cpp/AINativeNPCGoalGameplaySemantics.generated.h"),
    ("contract", "generated/cpp/AINativeNPCSkillExecutionSemantics.generated.h"),
    ("contract", "docs/current/contract-appendices.md"),
    ("unreal", "NeuralGame.uproject"),
    ("unreal", "Source/NeuralGame/NeuralGame.Build.cs"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGoalHostComponent.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSkillExecutorComponent.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Execution/AINativeNPCSocialActionComponent.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Execution/AINativeNPCGreetStateTreeTask.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Policy/AINativeNPCNNEPolicyEvaluator.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Policy/AINativeNPCPolicyModelData.cpp"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Policy/AINativeNPCResolvePolicyFreezeManifest.cpp"),
    ("unreal", "Content/AINativeNPC/Policy/MD_AINativeNPCResolvePolicyV1.uasset"),
    ("unreal", "Content/AINativeNPC/Policy/DA_AINativeNPCResolveCalibrationV1.uasset"),
    ("unreal", "Content/AINativeNPC/UI/WBP_AINativeNPCGreetCueV1.uasset"),
    ("unreal", "Content/AINativeNPC/StateTree/ST_AINativeNPCSkillHandoff.uasset"),
}


FORBIDDEN_DERIVED_ARTIFACTS = {
    ("contract", "generated/cpp/AINativeNPCResolvePolicyPromotion.generated.h"),
    ("unreal", "Source/NeuralGame/AINativeNPC/Generated/AINativeNPCResolvePolicyPromotion.generated.h"),
}


class PromotionError(RuntimeError):
    pass


def parse_json_snapshot(raw: bytes, source: Path) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PromotionError(f"cannot read JSON {source}: {error}") from error
    if not isinstance(value, dict):
        raise PromotionError(f"JSON root must be object: {source}")
    return value


def load_json_snapshot(path: Path) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise PromotionError(f"cannot read JSON {path}: {error}") from error
    return parse_json_snapshot(raw, path), hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict:
    return load_json_snapshot(path)[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def artifact_set_sha256(contract_root: Path, unreal_root: Path, records: list[dict]) -> str:
    digest = hashlib.sha256()
    roots = {
        "contract": contract_root.resolve(),
        "unreal": unreal_root.resolve(),
    }
    parsed: list[tuple[str, str]] = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {"root", "path"}:
            raise PromotionError("artifact_paths entries must contain exact root/path fields")
        root_name, relative = record.get("root"), record.get("path")
        if root_name not in {"contract", "unreal"} or not isinstance(relative, str):
            raise PromotionError("artifact path root/path is invalid")
        parsed.append((root_name, relative))
    normalized = sorted(set(parsed), key=lambda value: f"{value[0]}/{value[1]}".encode("utf-8"))
    if len(normalized) != len(records):
        raise PromotionError("artifact_paths contains duplicates")
    if not REQUIRED_ARTIFACTS.issubset(set(normalized)):
        missing = sorted(REQUIRED_ARTIFACTS - set(normalized))
        raise PromotionError(f"artifact_paths missing required production artifacts: {missing}")
    forbidden = sorted(FORBIDDEN_DERIVED_ARTIFACTS.intersection(normalized))
    if forbidden:
        raise PromotionError(f"artifact_paths contains circular derived promotion authority: {forbidden}")
    for root_name, relative in normalized:
        if "\x00" in relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise PromotionError(f"invalid artifact path: {relative!r}")
        base = roots[root_name]
        path = base / relative
        try:
            path.resolve(strict=True).relative_to(base)
        except (OSError, ValueError) as error:
            raise PromotionError(f"artifact path escapes artifact root: {root_name}/{relative}") from error
        if not path.is_file():
            raise PromotionError(f"missing artifact: {root_name}/{relative}")
        raw = path.read_bytes()
        canonical_path = f"{root_name}/{relative}"
        digest.update(canonical_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(raw)).encode("ascii"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(raw).digest())
    return digest.hexdigest()


def validate_bundle(bundle: Path) -> tuple[dict, str, str]:
    bundle = bundle.resolve()
    manifest_path = bundle / "policy_manifest.json"
    if not manifest_path.is_file():
        raise PromotionError("policy manifest missing")
    if manifest_path.is_symlink():
        raise PromotionError("policy manifest escapes bundle root")
    try:
        resolved_manifest = manifest_path.resolve(strict=True)
        resolved_manifest.relative_to(bundle)
    except (OSError, ValueError) as error:
        raise PromotionError("policy manifest escapes bundle root") from error
    manifest, manifest_hash = load_json_snapshot(resolved_manifest)
    if manifest.get("release_scope_id") != RELEASE_SCOPE_ID:
        raise PromotionError("policy release_scope_id mismatch")
    if manifest.get("runtime_name") != "NNERuntimeORTCpu":
        raise PromotionError("policy runtime mismatch")
    if manifest.get("production_eligible") is not True:
        raise PromotionError("fixture/non-production policy bundle cannot be promoted")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise PromotionError("policy manifest files missing")
    snapshots: dict[str, bytes] = {}
    for name, record in files.items():
        relative = Path(name)
        if (name == "policy_manifest.json"
                or not isinstance(record, dict)
                or relative.is_absolute()
                or relative.name != name
                or ".." in relative.parts
                or "\x00" in name):
            raise PromotionError(f"invalid policy file path: {name}")
        if set(record) != {"bytes", "sha256"}:
            raise PromotionError(f"invalid policy file record: {name}")
        path = bundle / name
        try:
            resolved_path = path.resolve(strict=True)
            resolved_path.relative_to(bundle)
        except (OSError, ValueError) as error:
            raise PromotionError(f"policy bundle file escapes bundle: {name}") from error
        if not resolved_path.is_file():
            raise PromotionError(f"policy bundle file mismatch: {name}")
        try:
            raw = resolved_path.read_bytes()
        except OSError as error:
            raise PromotionError(f"policy bundle file mismatch: {name}") from error
        if (not isinstance(record.get("bytes"), int)
                or isinstance(record.get("bytes"), bool)
                or record["bytes"] < 0
                or not is_sha256(record.get("sha256"))
                or len(raw) != record["bytes"]
                or hashlib.sha256(raw).hexdigest() != record["sha256"]):
            raise PromotionError(f"policy bundle file mismatch: {name}")
        snapshots[name] = raw
    if set(files) != REQUIRED_BUNDLE_FILES:
        raise PromotionError(
            f"policy bundle inventory mismatch: expected {sorted(REQUIRED_BUNDLE_FILES)}, got {sorted(files)}")
    disk_inventory = {path.name for path in bundle.iterdir()}
    expected_disk_inventory = REQUIRED_BUNDLE_FILES | {"policy_manifest.json"}
    if disk_inventory != expected_disk_inventory:
        raise PromotionError(
            f"policy bundle inventory mismatch on disk: expected {sorted(expected_disk_inventory)}, got {sorted(disk_inventory)}")
    model_hash = hashlib.sha256(snapshots["policy.onnx"]).hexdigest()
    if model_hash != manifest.get("model_sha256"):
        raise PromotionError("policy model hash mismatch")
    calibration_hash = hashlib.sha256(snapshots["calibration_ood_asset.json"]).hexdigest()
    if calibration_hash != manifest.get("calibration_ood_sha256"):
        raise PromotionError("calibration/OOD hash mismatch")
    checkpoint_hash = hashlib.sha256(snapshots["model.safetensors"]).hexdigest()
    if checkpoint_hash != manifest.get("checkpoint_sha256"):
        raise PromotionError("checkpoint hash mismatch")
    calibration = parse_json_snapshot(
        snapshots["calibration_ood_asset.json"], bundle / "calibration_ood_asset.json")
    if calibration.get("checkpoint_hash") != checkpoint_hash:
        raise PromotionError("calibration checkpoint hash mismatch")
    return manifest, manifest_hash, calibration_hash


def validate_evidence(
        index: dict,
        expected_artifact_set: str,
        expected_bundle_hashes: dict[str, str] | None = None) -> str:
    if index.get("artifact_set_sha256") != expected_artifact_set:
        raise PromotionError("evidence artifact_set_sha256 mismatch")
    if expected_bundle_hashes is not None:
        for field, expected in expected_bundle_hashes.items():
            if index.get(field) != expected:
                raise PromotionError(f"evidence bundle hash mismatch: {field}")
    entries = index.get("entries")
    if not isinstance(entries, list):
        raise PromotionError("evidence entries missing")
    by_id = {entry.get("id"): entry for entry in entries if isinstance(entry, dict)}
    if len(entries) != len(by_id) or set(by_id) != REQUIRED_EVIDENCE_IDS:
        raise PromotionError("evidence IDs are not exact")
    for evidence_id, entry in by_id.items():
        if entry.get("status") != "passed" or entry.get("artifact_set_sha256") != expected_artifact_set:
            raise PromotionError(f"evidence not passed/current: {evidence_id}")
        if expected_bundle_hashes is not None:
            for field, expected in expected_bundle_hashes.items():
                if entry.get(field) != expected:
                    raise PromotionError(f"evidence bundle hash mismatch: {evidence_id}/{field}")
        if not is_sha256(entry.get("report_sha256")):
            raise PromotionError(f"evidence report hash invalid: {evidence_id}")
        report_path = entry.get("report_path")
        if not isinstance(report_path, str) or not Path(report_path).is_file():
            raise PromotionError(f"evidence report missing/mismatched: {evidence_id}")
        report, report_hash = load_json_snapshot(Path(report_path))
        if report_hash != entry["report_sha256"]:
            raise PromotionError(f"evidence report missing/mismatched: {evidence_id}")
        if expected_bundle_hashes is not None:
            for field, expected in expected_bundle_hashes.items():
                if report.get(field) != expected:
                    raise PromotionError(f"evidence bundle hash mismatch: {evidence_id}/report/{field}")
        if (report.get("id") != evidence_id
                or report.get("status") != "passed"
                or report.get("artifact_set_sha256") != expected_artifact_set
                or report.get("timed_out") is not False
                or report.get("full_report") is not True
                or report.get("passed") is not True
                or report.get("blocking_findings") != []):
            raise PromotionError(f"evidence report body is not an exact passed report: {evidence_id}")
        if not isinstance(entry.get("handle"), str) or not entry["handle"]:
            raise PromotionError(f"evidence handle missing: {evidence_id}")
        if not isinstance(entry.get("started_at"), str) or not isinstance(entry.get("ended_at"), str):
            raise PromotionError(f"evidence timestamps missing: {evidence_id}")
        if evidence_id in EXECUTION_EVIDENCE_IDS:
            if (not isinstance(entry.get("command"), str)
                    or entry.get("exit_code") != 0
                    or report.get("command") != entry.get("command")
                    or report.get("exit_code") != 0):
                raise PromotionError(f"execution evidence command/exit invalid: {evidence_id}")

    greet_hash = index.get("greet_asset_set_sha256")
    if not is_sha256(greet_hash) or greet_hash == "0" * 64:
        raise PromotionError("greet_asset_set_sha256 missing")
    return str(greet_hash)


def write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        os.close(descriptor)


def render_runtime_authority_header(manifest: dict | None) -> str:
    if manifest is None:
        approved = "false"
        artifact_set = ""
        evidence_index = ""
    else:
        artifact_set = manifest.get("artifact_set_sha256")
        evidence_index = manifest.get("evidence_index_sha256")
        if not is_sha256(artifact_set) or not is_sha256(evidence_index):
            raise PromotionError("runtime promotion authority digests invalid")
        approved = "true"
    return (
        "// Generated promotion authority. Do not edit by hand.\n"
        "#pragma once\n\n"
        "namespace AINativeNPC::ResolvePolicyPromotionV1\n"
        "{\n"
        f"inline constexpr bool Approved = {approved};\n"
        f"inline constexpr const char* ArtifactSetSha256 = \"{artifact_set}\";\n"
        f"inline constexpr const char* EvidenceIndexSha256 = \"{evidence_index}\";\n"
        "}\n"
    )


def promote(
        root: Path,
        unreal_root: Path,
        bundle: Path,
        evidence_path: Path,
        output: Path,
        authority_header_output: Path | None = None) -> dict:
    if output.exists():
        raise PromotionError("Freeze Manifest already exists; remove it only through an explicit new promotion cycle")
    if authority_header_output is not None and authority_header_output.exists():
        raise PromotionError("runtime promotion authority already exists; remove it only through an explicit new promotion cycle")
    policy, policy_hash, calibration_hash = validate_bundle(bundle)
    evidence, evidence_hash = load_json_snapshot(evidence_path)
    paths = evidence.get("artifact_paths")
    if not isinstance(paths, list):
        raise PromotionError("evidence artifact_paths missing")
    computed_artifact_set = artifact_set_sha256(root, unreal_root, paths)
    bundle_hashes = {
        "policy_manifest_sha256": policy_hash,
        "model_sha256": str(policy["model_sha256"]),
        "calibration_ood_sha256": calibration_hash,
    }
    greet_hash = validate_evidence(evidence, computed_artifact_set, bundle_hashes)
    contracts = {
        "schema_sha256": sha256(root / "contracts/current/ai_native_npc_schema_v2_0.yaml"),
        "goal_registry_sha256": sha256(root / "contracts/current/goal_registry_v1.yaml"),
        "skill_registry_sha256": sha256(root / "contracts/current/skill_registry_v1.yaml"),
    }
    for key, value in contracts.items():
        if policy.get(key) != value:
            raise PromotionError(f"policy current contract mismatch: {key}")
    manifest = {
        "release_scope_id": RELEASE_SCOPE_ID,
        "release_status": "approved",
        "runtime_name": "NNERuntimeORTCpu",
        "runtime_plugin_version": "1.0",
        "engine_version": "5.7",
        "schema_contract_revision": "2.0.0-rc6",
        **contracts,
        "policy_manifest_sha256": policy_hash,
        "calibration_ood_asset_sha256": calibration_hash,
        "greet_asset_set_sha256": greet_hash,
        "evidence_index_sha256": evidence_hash,
        "artifact_set_sha256": computed_artifact_set,
    }
    if authority_header_output is None:
        raise PromotionError("runtime promotion authority output is required")
    manifest_payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    authority_payload = render_runtime_authority_header(manifest).encode("utf-8")
    authority_written = False
    manifest_written = False
    try:
        write_exclusive(authority_header_output, authority_payload)
        authority_written = True
        write_exclusive(output, manifest_payload)
        manifest_written = True
    except Exception as error:
        if authority_written:
            authority_header_output.unlink(missing_ok=True)
        if manifest_written:
            output.unlink(missing_ok=True)
        if isinstance(error, PromotionError):
            raise
        raise PromotionError(f"promotion outputs could not be committed: {error}") from error
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unreal-root", type=Path, default=DEFAULT_UNREAL_ROOT)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authority-header-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = promote(
            args.root.resolve(),
            args.unreal_root.resolve(),
            args.bundle.resolve(),
            args.evidence.resolve(),
            args.output.resolve(),
            args.authority_header_output.resolve())
    except PromotionError as error:
        print(f"PROMOTION_REJECTED: {error}")
        return 1
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
