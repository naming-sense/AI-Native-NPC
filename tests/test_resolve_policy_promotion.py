from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/promote_resolve_policy.py"
FIXTURE_BUNDLE = ROOT / "artifacts/resolve_policy_v1_fixture"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def import_tool():
    return import_module("resolve_policy_promotion_test_module", TOOL)


def file_record(path: Path) -> dict[str, object]:
    return {
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def rewrite_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_promotable_bundle(destination: Path, contract_root: Path | None = None) -> Path:
    shutil.copytree(FIXTURE_BUNDLE, destination)
    manifest_path = destination / "policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["production_eligible"] = True
    if contract_root is not None:
        for field, relative in {
            "schema_sha256": "contracts/current/ai_native_npc_schema_v2_0.yaml",
            "goal_registry_sha256": "contracts/current/goal_registry_v1.yaml",
            "skill_registry_sha256": "contracts/current/skill_registry_v1.yaml",
        }.items():
            manifest[field] = hashlib.sha256((contract_root / relative).read_bytes()).hexdigest()
    rewrite_json(manifest_path, manifest)
    return destination


def bundle_evidence_hashes(bundle: Path) -> dict[str, str]:
    manifest_path = bundle / "policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "policy_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "model_sha256": manifest["model_sha256"],
        "calibration_ood_sha256": manifest["calibration_ood_sha256"],
    }


def populate_artifact_roots(tool, contract_root: Path, unreal_root: Path) -> list[dict[str, str]]:
    paths = []
    for root_name, relative in sorted(tool.REQUIRED_ARTIFACTS):
        base = contract_root if root_name == "contract" else unreal_root
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture for {root_name}/{relative}\n", encoding="utf-8")
        paths.append({"root": root_name, "path": relative})
    return paths


def write_passed_evidence(
        tool,
        directory: Path,
        artifact_paths: list[dict[str, str]],
        artifact_hash: str,
        bundle_hashes: dict[str, str]) -> Path:
    entries = []
    for evidence_id in sorted(tool.REQUIRED_EVIDENCE_IDS):
        command = f"verify-{evidence_id}"
        body = {
            "id": evidence_id,
            "status": "passed",
            "artifact_set_sha256": artifact_hash,
            "timed_out": False,
            "full_report": True,
            "command": command,
            "exit_code": 0,
            "passed": True,
            "blocking_findings": [],
            **bundle_hashes,
        }
        report = directory / f"{evidence_id}.json"
        rewrite_json(report, body)
        entry = {
            "id": evidence_id,
            "status": "passed",
            "artifact_set_sha256": artifact_hash,
            "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
            "report_path": str(report),
            "handle": "current-evidence",
            "started_at": "2026-08-20T00:00:00Z",
            "ended_at": "2026-08-20T00:00:01Z",
            **bundle_hashes,
        }
        if evidence_id in tool.EXECUTION_EVIDENCE_IDS:
            entry["command"] = command
            entry["exit_code"] = 0
        entries.append(entry)
    index = {
        "artifact_set_sha256": artifact_hash,
        "greet_asset_set_sha256": "b" * 64,
        "artifact_paths": artifact_paths,
        "entries": entries,
        **bundle_hashes,
    }
    path = directory / "evidence-index.json"
    rewrite_json(path, index)
    return path


class ResolvePolicyPromotionTests(unittest.TestCase):
    def test_fixture_bundle_can_never_be_promoted(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "evidence.json"
            evidence.write_text("{}\n", encoding="utf-8")
            output = root / "resolve_policy_freeze_manifest.json"
            authority = root / "AINativeNPCResolvePolicyPromotion.generated.h"
            with self.assertRaisesRegex(tool.PromotionError, "fixture/non-production"):
                tool.promote(
                    ROOT,
                    Path("/mnt/d/Codex-cli/NeuralProject/NeuralGame"),
                    FIXTURE_BUNDLE,
                    evidence,
                    output,
                    authority)
            self.assertFalse(output.exists())
            self.assertFalse(authority.exists())

    def test_bundle_requires_exact_documented_inventory(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            manifest_path = bundle / "policy_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["files"]["train_report.json"]
            rewrite_json(manifest_path, manifest)
            with self.assertRaisesRegex(tool.PromotionError, "inventory"):
                tool.validate_bundle(bundle)

    def test_bundle_rejects_unlisted_files_on_disk(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            (bundle / "unreviewed.bin").write_bytes(b"not in the manifest")
            with self.assertRaisesRegex(tool.PromotionError, "inventory"):
                tool.validate_bundle(bundle)

    def test_bundle_file_records_have_exact_size_and_hash_fields(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            manifest_path = bundle / "policy_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"]["policy.onnx"]["unreviewed"] = True
            rewrite_json(manifest_path, manifest)
            with self.assertRaisesRegex(tool.PromotionError, "file record"):
                tool.validate_bundle(bundle)

    def test_bundle_rejects_absolute_and_parent_traversal_manifest_paths(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.bin"
            outside.write_bytes(b"outside bundle")
            for index, malicious in enumerate((str(outside.resolve()), "../outside.bin")):
                with self.subTest(path=malicious):
                    bundle = make_promotable_bundle(root / f"bundle-{index}")
                    manifest_path = bundle / "policy_manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["files"][malicious] = file_record(outside)
                    rewrite_json(manifest_path, manifest)
                    with self.assertRaisesRegex(tool.PromotionError, "invalid policy file path"):
                        tool.validate_bundle(bundle)

    def test_bundle_rejects_symlinks_that_escape_bundle(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = make_promotable_bundle(root / "bundle")
            policy = bundle / "policy.onnx"
            outside = root / "outside.onnx"
            shutil.copyfile(policy, outside)
            policy.unlink()
            policy.symlink_to(outside)
            with self.assertRaisesRegex(tool.PromotionError, "escapes bundle"):
                tool.validate_bundle(bundle)

    def test_bundle_manifest_symlink_escape_is_rejected(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = make_promotable_bundle(root / "bundle")
            manifest_path = bundle / "policy_manifest.json"
            outside = root / "outside-policy-manifest.json"
            outside.write_bytes(manifest_path.read_bytes())
            manifest_path.unlink()
            manifest_path.symlink_to(outside)
            with self.assertRaisesRegex(tool.PromotionError, "policy manifest escapes bundle root"):
                tool.validate_bundle(bundle)

    def test_bundle_manifest_body_and_digest_use_one_snapshot(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            manifest_path = bundle / "policy_manifest.json"
            original = manifest_path.read_bytes()
            original_hash = hashlib.sha256(original).hexdigest()
            replacement = json.loads(original)
            replacement["snapshot_race_marker"] = "not validated"
            replacement_bytes = (json.dumps(replacement, indent=2, sort_keys=True) + "\n").encode()
            real_sha256 = tool.sha256

            def swap_before_separate_manifest_hash(path: Path) -> str:
                digest = real_sha256(path)
                if path == manifest_path:
                    manifest_path.write_bytes(replacement_bytes)
                return digest

            setattr(tool, "sha256", swap_before_separate_manifest_hash)
            try:
                _, validated_hash, _ = tool.validate_bundle(bundle)
            finally:
                setattr(tool, "sha256", real_sha256)
            self.assertEqual(validated_hash, original_hash)
            self.assertEqual(manifest_path.read_bytes(), original)

    def test_bundle_checkpoint_hash_matches_safetensors(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            manifest_path = bundle / "policy_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["checkpoint_sha256"] = "c" * 64
            rewrite_json(manifest_path, manifest)
            with self.assertRaisesRegex(tool.PromotionError, "checkpoint hash mismatch"):
                tool.validate_bundle(bundle)

    def test_calibration_checkpoint_hash_matches_manifest_checkpoint(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            bundle = make_promotable_bundle(Path(directory) / "bundle")
            calibration_path = bundle / "calibration_ood_asset.json"
            calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
            calibration["checkpoint_hash"] = "c" * 64
            rewrite_json(calibration_path, calibration)
            manifest_path = bundle / "policy_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"]["calibration_ood_asset.json"] = file_record(calibration_path)
            manifest["calibration_ood_sha256"] = file_record(calibration_path)["sha256"]
            rewrite_json(manifest_path, manifest)
            with self.assertRaisesRegex(tool.PromotionError, "calibration checkpoint hash mismatch"):
                tool.validate_bundle(bundle)

    def test_artifact_set_requires_full_contract_and_unreal_scope(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "contract"
            unreal = root / "unreal"
            path = contract / "contracts/current/ai_native_npc_schema_v2_0.yaml"
            path.parent.mkdir(parents=True)
            path.write_text("schema: fixture\n", encoding="utf-8")
            unreal.mkdir()
            with self.assertRaisesRegex(tool.PromotionError, "missing required production artifacts"):
                tool.artifact_set_sha256(
                    contract,
                    unreal,
                    [{"root": "contract", "path": "contracts/current/ai_native_npc_schema_v2_0.yaml"}],
                )

    def test_artifact_set_rejects_symlink_that_escapes_root(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "contract"
            unreal = root / "unreal"
            artifact_paths = populate_artifact_roots(tool, contract, unreal)
            victim = contract / "docs/current/technical-requirements.md"
            outside = root / "outside.md"
            outside.write_text("outside artifact root\n", encoding="utf-8")
            victim.unlink()
            victim.symlink_to(outside)
            with self.assertRaisesRegex(tool.PromotionError, "escapes artifact root"):
                tool.artifact_set_sha256(contract, unreal, artifact_paths)

    def test_failed_or_timeout_report_body_cannot_be_relabelled_passed(self) -> None:
        tool = import_tool()
        artifact_hash = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries = []
            for evidence_id in sorted(tool.REQUIRED_EVIDENCE_IDS):
                report = root / f"{evidence_id}.json"
                body = {
                    "id": evidence_id,
                    "status": "failed",
                    "artifact_set_sha256": artifact_hash,
                    "timed_out": True,
                    "full_report": False,
                    "command": "false",
                    "exit_code": 1,
                    "passed": False,
                    "blocking_findings": ["fixture failure"],
                }
                report.write_text(json.dumps(body) + "\n", encoding="utf-8")
                entry = {
                    "id": evidence_id,
                    "status": "passed",
                    "artifact_set_sha256": artifact_hash,
                    "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                    "report_path": str(report),
                    "handle": "forged-handle",
                    "started_at": "2026-08-20T00:00:00Z",
                    "ended_at": "2026-08-20T00:00:01Z",
                }
                if evidence_id in tool.EXECUTION_EVIDENCE_IDS:
                    entry["command"] = "false"
                    entry["exit_code"] = 0
                entries.append(entry)
            index = {
                "artifact_set_sha256": artifact_hash,
                "greet_asset_set_sha256": "b" * 64,
                "entries": entries,
            }
            with self.assertRaisesRegex(tool.PromotionError, "report body is not an exact passed report"):
                tool.validate_evidence(index, artifact_hash)

    def test_execution_report_cannot_contradict_passed_status(self) -> None:
        tool = import_tool()
        artifact_hash = "a" * 64
        bundle_hashes = {
            "policy_manifest_sha256": "c" * 64,
            "model_sha256": "d" * 64,
            "calibration_ood_sha256": "e" * 64,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_path = write_passed_evidence(tool, root, [], artifact_hash, bundle_hashes)
            index = json.loads(evidence_path.read_text(encoding="utf-8"))
            entry = next(row for row in index["entries"] if row["id"] in tool.EXECUTION_EVIDENCE_IDS)
            report_path = Path(entry["report_path"])
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["passed"] = False
            report["blocking_findings"] = ["contradictory execution failure"]
            rewrite_json(report_path, report)
            entry["report_sha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(tool.PromotionError, "exact passed report"):
                tool.validate_evidence(index, artifact_hash, bundle_hashes)

    def test_evidence_report_body_and_digest_use_one_snapshot(self) -> None:
        tool = import_tool()
        artifact_hash = "a" * 64
        bundle_hashes = {
            "policy_manifest_sha256": "c" * 64,
            "model_sha256": "d" * 64,
            "calibration_ood_sha256": "e" * 64,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_path = write_passed_evidence(tool, root, [], artifact_hash, bundle_hashes)
            index = json.loads(evidence_path.read_text(encoding="utf-8"))
            entry = index["entries"][0]
            report_path = Path(entry["report_path"])
            original = report_path.read_bytes()
            replacement = json.loads(original)
            replacement["snapshot_race_marker"] = "not hashed"
            replacement_bytes = (json.dumps(replacement, indent=2, sort_keys=True) + "\n").encode()
            real_sha256 = tool.sha256

            def swap_after_report_hash(path: Path) -> str:
                digest = real_sha256(path)
                if path == report_path:
                    report_path.write_bytes(replacement_bytes)
                return digest

            setattr(tool, "sha256", swap_after_report_hash)
            try:
                tool.validate_evidence(index, artifact_hash, bundle_hashes)
            finally:
                setattr(tool, "sha256", real_sha256)
            self.assertEqual(report_path.read_bytes(), original)

    def test_evidence_index_digest_binds_the_validated_snapshot(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract_root = root / "contract"
            unreal_root = root / "unreal"
            artifact_paths = populate_artifact_roots(tool, contract_root, unreal_root)
            artifact_hash = tool.artifact_set_sha256(contract_root, unreal_root, artifact_paths)
            bundle = make_promotable_bundle(root / "bundle", contract_root)
            bundle_hashes = bundle_evidence_hashes(bundle)
            evidence_path = write_passed_evidence(
                tool, root, artifact_paths, artifact_hash, bundle_hashes)
            original = evidence_path.read_bytes()
            original_hash = hashlib.sha256(original).hexdigest()
            replacement = json.loads(original)
            replacement["snapshot_race_marker"] = "not validated"
            replacement_bytes = (json.dumps(replacement, indent=2, sort_keys=True) + "\n").encode()
            real_artifact_set_sha256 = tool.artifact_set_sha256

            def swap_after_evidence_load(contract: Path, unreal: Path, records: list[dict]) -> str:
                digest = real_artifact_set_sha256(contract, unreal, records)
                evidence_path.write_bytes(replacement_bytes)
                return digest

            setattr(tool, "artifact_set_sha256", swap_after_evidence_load)
            try:
                manifest = tool.promote(
                    contract_root,
                    unreal_root,
                    bundle,
                    evidence_path,
                    root / "resolve_policy_freeze_manifest.json",
                    root / "AINativeNPCResolvePolicyPromotion.generated.h",
                )
            finally:
                setattr(tool, "artifact_set_sha256", real_artifact_set_sha256)
            self.assertEqual(manifest["evidence_index_sha256"], original_hash)

    def test_evidence_for_bundle_a_cannot_promote_bundle_b(self) -> None:
        tool = import_tool()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract_root = root / "contract"
            unreal_root = root / "unreal"
            artifact_paths = populate_artifact_roots(tool, contract_root, unreal_root)
            artifact_hash = tool.artifact_set_sha256(contract_root, unreal_root, artifact_paths)
            bundle = make_promotable_bundle(root / "bundle", contract_root)
            hashes_a = bundle_evidence_hashes(bundle)
            evidence_path = write_passed_evidence(tool, root, artifact_paths, artifact_hash, hashes_a)

            manifest_path = bundle / "policy_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            policy_path = bundle / "policy.onnx"
            policy_path.write_bytes(policy_path.read_bytes() + b"bundle-b")
            manifest["files"]["policy.onnx"] = file_record(policy_path)
            manifest["model_sha256"] = file_record(policy_path)["sha256"]
            checkpoint_path = bundle / "model.safetensors"
            checkpoint_path.write_bytes(checkpoint_path.read_bytes() + b"bundle-b")
            manifest["files"]["model.safetensors"] = file_record(checkpoint_path)
            manifest["checkpoint_sha256"] = file_record(checkpoint_path)["sha256"]
            calibration_path = bundle / "calibration_ood_asset.json"
            calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
            calibration["checkpoint_hash"] = manifest["checkpoint_sha256"]
            rewrite_json(calibration_path, calibration)
            manifest["files"]["calibration_ood_asset.json"] = file_record(calibration_path)
            manifest["calibration_ood_sha256"] = file_record(calibration_path)["sha256"]
            rewrite_json(manifest_path, manifest)
            hashes_b = bundle_evidence_hashes(bundle)
            self.assertTrue(all(hashes_a[field] != hashes_b[field] for field in hashes_a))
            evidence_index = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence_index.update(hashes_b)
            rewrite_json(evidence_path, evidence_index)

            output = root / "resolve_policy_freeze_manifest.json"
            authority = root / "AINativeNPCResolvePolicyPromotion.generated.h"
            with self.assertRaisesRegex(tool.PromotionError, "evidence bundle hash mismatch"):
                tool.promote(
                    contract_root,
                    unreal_root,
                    bundle,
                    evidence_path,
                    output,
                    authority,
                )
            self.assertFalse(output.exists())
            self.assertFalse(authority.exists())

    def test_fixture_split_assignment_uses_lf_and_catalog_proportions(self) -> None:
        assignment_path = FIXTURE_BUNDLE / "split_assignment.csv"
        assignment_bytes = assignment_path.read_bytes()
        self.assertNotIn(b"\r\n", assignment_bytes)
        with assignment_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 448)
        self.assertEqual(
            Counter(row["split"] for row in rows),
            {"train": 314, "calibration": 67, "general_test": 45, "ood_test": 22},
        )
        self.assertEqual(
            len({(row["case_group"], row["scenario_seed"]) for row in rows}),
            len(rows),
        )

    def test_runtime_authority_header_is_fail_closed_and_exact(self) -> None:
        tool = import_tool()
        dormant = tool.render_runtime_authority_header(None)
        generated = (ROOT / "generated/cpp/AINativeNPCResolvePolicyPromotion.generated.h").read_text(
            encoding="utf-8")
        self.assertEqual(dormant, generated)
        self.assertIn("Approved = false", dormant)

        artifact_hash = "a" * 64
        evidence_hash = "b" * 64
        approved = tool.render_runtime_authority_header({
            "artifact_set_sha256": artifact_hash,
            "evidence_index_sha256": evidence_hash,
        })
        self.assertIn("Approved = true", approved)
        self.assertIn(artifact_hash, approved)
        self.assertIn(evidence_hash, approved)
        with self.assertRaisesRegex(tool.PromotionError, "authority digests invalid"):
            tool.render_runtime_authority_header({
                "artifact_set_sha256": "0" * 63,
                "evidence_index_sha256": evidence_hash,
            })

    def test_zero_greet_asset_hash_is_rejected(self) -> None:
        tool = import_tool()
        artifact_hash = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries = []
            for evidence_id in sorted(tool.REQUIRED_EVIDENCE_IDS):
                report = root / f"{evidence_id}.json"
                command = f"verify-{evidence_id}"
                body = {
                    "id": evidence_id,
                    "status": "passed",
                    "artifact_set_sha256": artifact_hash,
                    "timed_out": False,
                    "full_report": True,
                    "command": command,
                    "exit_code": 0,
                    "passed": True,
                    "blocking_findings": [],
                }
                report.write_text(json.dumps(body) + "\n", encoding="utf-8")
                entry = {
                    "id": evidence_id,
                    "status": "passed",
                    "artifact_set_sha256": artifact_hash,
                    "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                    "report_path": str(report),
                    "handle": "current-evidence",
                    "started_at": "2026-08-20T00:00:00Z",
                    "ended_at": "2026-08-20T00:00:01Z",
                }
                if evidence_id in tool.EXECUTION_EVIDENCE_IDS:
                    entry["command"] = command
                    entry["exit_code"] = 0
                entries.append(entry)
            index = {
                "artifact_set_sha256": artifact_hash,
                "greet_asset_set_sha256": "0" * 64,
                "entries": entries,
            }
            with self.assertRaisesRegex(tool.PromotionError, "greet_asset_set_sha256 missing"):
                tool.validate_evidence(index, artifact_hash)


if __name__ == "__main__":
    unittest.main()
