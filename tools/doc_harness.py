#!/usr/bin/env python3
"""AI Native NPC executable document/contract harness v0.4.6 Semantic Closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from contractlib import TOOL_VERSION, collect_hash_magic_tokens, critical_suite_metrics, default_paths, load_yaml, sha256_file, validate_contracts, validate_generated_block, validate_manual_hash_literal_policy
from generate_contracts import check as check_generated, produce as generate_contracts
from generate_golden import check as check_golden, write as generate_golden
from run_contract_tests import local_verify, validate_normative_report, write_report as write_contract_test_report
from run_release_mutation_tests import validate_report as validate_release_mutation_report, write_report as write_release_mutation_report
from validate_schema import build_report as build_schema_report

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "manifest"
CATALOG_PATH = MANIFEST_DIR / "catalog.json"
FREEZE_STATUS_PATH = MANIFEST_DIR / "freeze_status.json"
FREEZE_MANIFEST_PATH = MANIFEST_DIR / "freeze_manifest.json"
RELEASE_CONFIG_PATH = MANIFEST_DIR / "release_config.json"
LOCK_PATH = MANIFEST_DIR / "lock.json"
CHECKSUM_PATH = MANIFEST_DIR / "checksums.sha256"
VALIDATION_REPORT_PATH = ROOT / "reports/validation_report.md"
SCHEMA_REPORT_PATH = ROOT / "tests/reports/schema_semantic_validation.json"
CONTRACT_REPORT_PATH = ROOT / "tests/reports/contract_test_report.json"
INTEGRITY_EVIDENCE_PATH = ROOT / "tests/reports/harness_integrity_evidence.json"
RELEASE_MUTATION_REPORT_PATH = ROOT / "tests/reports/release_mutation_report.json"
SOURCE_FILE_MAP_PATH = ROOT / "reports/SOURCE_FILE_MAP.md"
LOCAL_DIAGNOSTICS_PATH = ROOT / "dist/local/contract_test_diagnostics.json"
CURRENT_REQUIREMENTS_PATH = ROOT / "docs/current/requirements/ai_native_npc_requirements_implementation_plan_v0.4.6.md"
CURRENT_UNREAL_PATH = ROOT / "docs/current/unreal/ai_native_npc_ue57_manny_spatial_vision_audio_implementation_plan_v0.4.6.md"
GENERATED_SCHEMA_REFERENCE_PATH = ROOT / "generated/docs/schema_reference.md"
GENERATED_REQUIREMENTS_KPI_PATH = ROOT / "generated/docs/requirements_kpi_appendix.md"
GENERATED_UNREAL_KPI_PATH = ROOT / "generated/docs/unreal_kpi_section.md"

LOCK_SELF_EXCLUSIONS = {"manifest/lock.json", "manifest/checksums.sha256"}
INTEGRITY_EXCLUSIONS = {
    "manifest/lock.json",
    "manifest/checksums.sha256",
    "manifest/freeze_manifest.json",
    "tests/reports/harness_integrity_evidence.json",
}

PASS_GATE_IDS = {
    "document_harness_integrity",
    "schema_semantic_validation",
    "skill_registry_validation",
    "goal_registry_validation",
    "test_taxonomy_validation",
    "generated_python_contract",
    "generated_cpp_contract",
    "generated_code_reproducibility",
    "golden_fixture_reproducibility",
    "python_golden_parity",
    "cpp_golden_parity",
    "environment_independent_normative_report",
    "lock_file_set_exact",
    "generated_document_appendix_parity",
    "normalizer_semantic_hardening",
    "hash_contract_codegen_parity",
    "decision_contract_hash_golden",
    "semantic_mutation_regression",
    "manual_hash_literal_guard",
    "normalizer_constraint_closure",
    "dynamic_mutation_probe_regression",
    "manual_hash_magic_full_context_guard",
    "critical_taxonomy_kpi_sync",
    "taxonomy_mutation_regression",
    "all_nonarchive_markdown_semantic_scope",
    "catalog_archive_exact_match",
    "release_end_to_end_mutation_regression",
    "source_file_map_currentness",
}
PENDING_GATE_IDS = {
    "float_tensor_python_unreal_parity",
    "onnx_unreal_output_parity",
    "target_recall",
    "candidate_recall",
    "critical_suite",
    "goal_fsm_runtime",
    "atomic_commit_runtime",
    "hidden_information_leakage",
    "safety_fuzz",
    "calibration_ood",
    "performance_budget",
    "save_load_hot_swap",
    "decision_contract_runtime_binding",
    "formal_freeze_approval",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def release_config() -> dict[str, Any]:
    return load_json(RELEASE_CONFIG_PATH)


def extract_markdown_value(text: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*(?:`|\*\*)?([^`\n*]+)(?:`|\*\*)?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def replace_markdown_value(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"(^- {re.escape(label)}:\s*)(?:`|\*\*)?([^`\n*]+)(?:`|\*\*)?(\s*$)", re.MULTILINE)
    if not pattern.search(text):
        raise ValueError(f"Markdown metadata label missing: {label}")
    return pattern.sub(rf"\g<1>`{value}`\g<3>", text, count=1)


def is_package_file(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    r = rel(path)
    if "__pycache__" in path.parts or r.endswith(".pyc") or r.startswith("dist/"):
        return False
    return True


def package_files() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if is_package_file(p)), key=lambda p: rel(p).encode("utf-8"))


def lock_scope_files() -> list[Path]:
    return [p for p in package_files() if rel(p) not in LOCK_SELF_EXCLUSIONS]


SEMANTIC_MARKDOWN_EXCLUDE_PREFIXES = (
    "docs/archive/",
    "contracts/archive/",
    "manifests/archive/",
    "generated/docs/",
)
ARCHIVE_PREFIXES = ("docs/archive/", "contracts/archive/", "manifests/archive/")


def semantic_markdown_files() -> list[Path]:
    return [
        path for path in lock_scope_files()
        if path.suffix.lower() == ".md"
        and not rel(path).startswith(SEMANTIC_MARKDOWN_EXCLUDE_PREFIXES)
    ]


def archive_scope_files(root: Path = ROOT) -> list[Path]:
    rows: list[Path] = []
    for prefix in ARCHIVE_PREFIXES:
        base = root / prefix.rstrip("/")
        if base.exists():
            rows.extend(path for path in base.rglob("*") if path.is_file() and not path.is_symlink())
    return sorted(rows, key=lambda path: path.relative_to(root).as_posix().encode("utf-8"))


def _archive_type(path: Path) -> str:
    name = path.name
    r = path.relative_to(ROOT).as_posix()
    if "/requirements/" in r:
        return "requirements"
    if "/unreal/" in r:
        return "unreal_profile"
    if "/review-notes/" in r:
        return "review_note"
    if name.startswith("ai_native_npc_schema"):
        return "schema"
    if name.startswith("skill_registry"):
        return "skill_registry"
    if name.startswith("goal_registry"):
        return "goal_registry"
    if name.startswith("test_taxonomy"):
        return "test_taxonomy"
    if "manifest" in name:
        return "freeze_manifest"
    return "archive_artifact"


def _archive_version(path: Path) -> str:
    name = path.name
    match = re.search(r"v(\d+\.\d+(?:\.\d+)?)", name)
    if match:
        return match.group(1)
    if "initial" in name:
        return "initial"
    if "legacy" in name:
        return "legacy"
    return "historical"


def build_archive_catalog(root: Path = ROOT) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in archive_scope_files(root):
        r = path.relative_to(root).as_posix()
        rows.append({
            "path": r,
            "type": _archive_type(path if root == ROOT else ROOT / r),
            "version": _archive_version(path),
            "status": "superseded_incompatible" if "legacy" in path.name else "superseded",
            "sha256": sha256_file(path),
        })
    return rows


def validate_catalog_data(root: Path, catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_roles = {"requirements", "unreal_profile", "schema", "skill_registry", "goal_registry", "test_taxonomy"}
    canonical = catalog.get("canonical", {})
    if set(canonical) != expected_roles:
        errors.append("catalog canonical role set mismatch")
    canonical_paths: list[str] = []
    for role, item in canonical.items():
        r = item.get("path", "")
        canonical_paths.append(r)
        path = root / r
        if not path.exists():
            errors.append(f"catalog path missing: {role}")
        elif item.get("sha256") != sha256_file(path):
            errors.append(f"catalog SHA mismatch: {role}")
        if r.startswith(ARCHIVE_PREFIXES):
            errors.append(f"catalog canonical path points into archive: {role}")
    if len(canonical_paths) != len(set(canonical_paths)):
        errors.append("catalog canonical path duplicate")

    archive_rows = catalog.get("archives", [])
    declared_paths = [row.get("path", "") for row in archive_rows if isinstance(row, dict)]
    if len(declared_paths) != len(set(declared_paths)):
        errors.append("catalog archive path duplicate")
    actual_paths = {path.relative_to(root).as_posix() for path in archive_scope_files(root)}
    declared_set = set(declared_paths)
    for r in sorted(actual_paths - declared_set):
        errors.append(f"catalog missing archive entry: {r}")
    for r in sorted(declared_set - actual_paths):
        errors.append(f"catalog ghost archive entry: {r}")
    for row in archive_rows:
        if not isinstance(row, dict):
            errors.append("catalog archive row must be object")
            continue
        r = row.get("path", "")
        if not r.startswith(ARCHIVE_PREFIXES):
            errors.append(f"catalog archive path outside archive roots: {r}")
            continue
        path = root / r
        if path.exists() and row.get("sha256") != sha256_file(path):
            errors.append(f"catalog archive SHA mismatch: {r}")
    return errors


def integrity_scope_files() -> list[Path]:
    return [p for p in package_files() if rel(p) not in INTEGRITY_EXCLUSIONS]


def compute_tree_digest(files: list[Path]) -> tuple[str, int]:
    digest = hashlib.sha256()
    for path in files:
        name = rel(path).encode("utf-8")
        file_hash = bytes.fromhex(sha256_file(path))
        digest.update(struct.pack("<I", len(name)))
        digest.update(name)
        digest.update(struct.pack("<Q", path.stat().st_size))
        digest.update(file_hash)
    return digest.hexdigest(), len(files)


def write_integrity_evidence() -> dict[str, Any]:
    digest, count = compute_tree_digest(integrity_scope_files())
    evidence = {
        "report_version": 2,
        "status": "pass",
        "tool": "tools/doc_harness.py",
        "tool_version": TOOL_VERSION,
        "tool_sha256": sha256_file(ROOT / "tools/doc_harness.py"),
        "tree_algorithm": "sha256(path_length_le32 || utf8_path || size_le64 || file_sha256_bytes)",
        "tree_scope_exclusions": sorted(INTEGRITY_EXCLUSIONS),
        "observed_file_count": count,
        "tree_digest_sha256": digest,
        "checks": [
            "actual_tree_digest_recomputed_by_strict_validator",
            "actual_file_count_recomputed_by_strict_validator",
            "lock_file_set_exact",
            "symlinks_forbidden",
            "zip_path_safety_enabled",
            "deterministic_double_pack_enabled",
        ],
    }
    write_json(INTEGRITY_EVIDENCE_PATH, evidence)
    return evidence


def validate_integrity_evidence() -> list[str]:
    if not INTEGRITY_EVIDENCE_PATH.exists():
        return ["harness integrity evidence missing"]
    evidence = load_json(INTEGRITY_EVIDENCE_PATH)
    digest, count = compute_tree_digest(integrity_scope_files())
    errors: list[str] = []
    if evidence.get("status") != "pass":
        errors.append("harness integrity evidence is not pass")
    if evidence.get("tool_version") != TOOL_VERSION:
        errors.append("harness integrity tool version mismatch")
    if evidence.get("tool_sha256") != sha256_file(ROOT / "tools/doc_harness.py"):
        errors.append("harness integrity tool hash mismatch")
    if set(evidence.get("tree_scope_exclusions", [])) != INTEGRITY_EXCLUSIONS:
        errors.append("harness integrity exclusion set mismatch")
    if evidence.get("observed_file_count") != count:
        errors.append(f"harness integrity file count mismatch expected={evidence.get('observed_file_count')} actual={count}")
    if evidence.get("tree_digest_sha256") != digest:
        errors.append("harness integrity tree digest mismatch")
    return errors


def documentation_contract() -> dict[str, Any]:
    schema = load_yaml(default_paths(ROOT).schema)
    return schema["documentation_contract"]


def taxonomy_documentation_contract() -> dict[str, Any]:
    taxonomy = load_yaml(default_paths(ROOT).test_taxonomy)
    return taxonomy["documentation_contract"]


def generated_appendix_block() -> str:
    contract = documentation_contract()
    generated = GENERATED_SCHEMA_REFERENCE_PATH.read_text(encoding="utf-8").rstrip()
    return f"{contract['marker_begin']}\n\n{generated}\n\n{contract['marker_end']}"


def generated_taxonomy_block(role: str) -> str:
    contract = taxonomy_documentation_contract()[role]
    generated_path = ROOT / contract["generated_reference"]
    generated = generated_path.read_text(encoding="utf-8").rstrip()
    return f"{contract['marker_begin']}\n\n{generated}\n\n{contract['marker_end']}"


def _replace_marked_block(text: str, begin: str, end: str, block: str, label: str) -> str:
    if text.count(begin) != 1 or text.count(end) != 1:
        raise SystemExit(f"generated marker count mismatch: {label}")
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    return text[:start] + block + text[finish:]


def sync_document_appendices() -> None:
    contract = documentation_contract()
    expected_paths = {rel(CURRENT_REQUIREMENTS_PATH), rel(CURRENT_UNREAL_PATH)}
    declared_paths = set(contract["required_documents"])
    if declared_paths != expected_paths:
        raise SystemExit(f"documentation_contract required_documents mismatch: {sorted(declared_paths)}")
    schema_block = generated_appendix_block()
    for path in [CURRENT_REQUIREMENTS_PATH, CURRENT_UNREAL_PATH]:
        text = path.read_text(encoding="utf-8")
        text = _replace_marked_block(text, contract["marker_begin"], contract["marker_end"], schema_block, rel(path))
        path.write_text(text, encoding="utf-8")

    taxonomy_contract = taxonomy_documentation_contract()
    role_paths = {"requirements": CURRENT_REQUIREMENTS_PATH, "unreal": CURRENT_UNREAL_PATH}
    for role, path in role_paths.items():
        spec = taxonomy_contract[role]
        if spec["path"] != rel(path):
            raise SystemExit(f"taxonomy documentation path mismatch for {role}: {spec['path']}")
        text = path.read_text(encoding="utf-8")
        text = _replace_marked_block(text, spec["marker_begin"], spec["marker_end"], generated_taxonomy_block(role), rel(path))
        path.write_text(text, encoding="utf-8")


def _validate_critical_count_references(text: str, expected: int, label: str) -> list[str]:
    errors: list[str] = []
    patterns = [
        re.compile(r"(?i)Critical Suite[^\n]{0,120}?\b(\d+)\s+sequences?"),
        re.compile(r"총\s*최소\s*(\d+)\s+sequences?", re.IGNORECASE),
        re.compile(r"(?i)critical_minimum_sequence_count\s*(?::=|=|:)\s*(\d+)"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            if int(match.group(1)) != expected:
                errors.append(f"{label}: stale Critical Suite denominator {match.group(1)}; expected {expected}")
    return errors


def validate_document_appendices() -> list[str]:
    errors: list[str] = []
    schema = load_yaml(default_paths(ROOT).schema)
    contract = schema["documentation_contract"]
    schema_block = generated_appendix_block()
    taxonomy = load_yaml(default_paths(ROOT).test_taxonomy)
    taxonomy_contract = taxonomy["documentation_contract"]
    role_paths = {"requirements": CURRENT_REQUIREMENTS_PATH, "unreal": CURRENT_UNREAL_PATH}

    for declared in contract["required_documents"]:
        path = ROOT / declared
        if not path.exists():
            errors.append(f"generated appendix document missing: {declared}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(validate_generated_block(text, contract["marker_begin"], contract["marker_end"], schema_block, declared))

    for role, path in role_paths.items():
        spec = taxonomy_contract[role]
        if spec["path"] != rel(path):
            errors.append(f"taxonomy documentation path mismatch for {role}: {spec['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        errors.extend(validate_generated_block(text, spec["marker_begin"], spec["marker_end"], generated_taxonomy_block(role), rel(path)))

    errors.extend(validate_all_markdown_semantics())
    return sorted(set(errors))

def update_ue_dependency_hashes() -> None:
    req = CURRENT_REQUIREMENTS_PATH
    ue = CURRENT_UNREAL_PATH
    paths = default_paths(ROOT)
    text = ue.read_text(encoding="utf-8")
    text = replace_markdown_value(text, "상위 기준서", req.name)
    text = replace_markdown_value(text, "상위 기준서 SHA-256", sha256_file(req))
    text = replace_markdown_value(text, "Schema YAML SHA-256", sha256_file(paths.schema))
    text = replace_markdown_value(text, "Skill Registry SHA-256", sha256_file(paths.skill_registry))
    text = replace_markdown_value(text, "Goal Registry SHA-256", sha256_file(paths.goal_registry))
    text = replace_markdown_value(text, "Test Taxonomy SHA-256", sha256_file(paths.test_taxonomy))
    ue.write_text(text, encoding="utf-8")


def _strip_allowed_generated_blocks(path: Path, text: str) -> str:
    if path not in {CURRENT_REQUIREMENTS_PATH, CURRENT_UNREAL_PATH}:
        return text
    schema_contract = documentation_contract()
    taxonomy_contract = taxonomy_documentation_contract()
    blocks = [(schema_contract["marker_begin"], schema_contract["marker_end"])]
    for spec in taxonomy_contract.values():
        if isinstance(spec, dict) and "marker_begin" in spec and "marker_end" in spec:
            blocks.append((spec["marker_begin"], spec["marker_end"]))
    outside = text
    for begin, end in blocks:
        start = outside.find(begin)
        finish = outside.find(end, start + len(begin)) if start >= 0 else -1
        if start >= 0 and finish >= 0:
            outside = outside[:start] + outside[finish + len(end):]
    return outside


def validate_all_markdown_semantics() -> list[str]:
    schema = load_yaml(default_paths(ROOT).schema)
    taxonomy = load_yaml(default_paths(ROOT).test_taxonomy)
    expected = critical_suite_metrics(taxonomy)["critical_minimum_sequence_count"]
    known_tokens = collect_hash_magic_tokens(ROOT)
    errors: list[str] = []
    for path in semantic_markdown_files():
        text = path.read_text(encoding="utf-8")
        if path in {CURRENT_REQUIREMENTS_PATH, CURRENT_UNREAL_PATH}:
            taxonomy_blocks = [
                (spec["marker_begin"], spec["marker_end"])
                for spec in taxonomy_documentation_contract().values()
                if isinstance(spec, dict) and "marker_begin" in spec
            ]
            errors.extend(validate_manual_hash_literal_policy(
                schema, text, rel(path), known_tokens, taxonomy_blocks, allow_schema_generated_block=True
            ))
        else:
            errors.extend(validate_manual_hash_literal_policy(
                schema, text, rel(path), known_tokens, allow_schema_generated_block=False
            ))
        errors.extend(_validate_critical_count_references(_strip_allowed_generated_blocks(path, text), expected, rel(path)))
    return sorted(set(errors))


def source_file_map_text() -> str:
    archives = build_archive_catalog(ROOT)
    lines = [
        "# v0.4.6 Source File Map",
        "",
        "## Current",
        "",
        "| 역할 | 경로 |",
        "|---|---|",
        f"| Requirements | `{rel(CURRENT_REQUIREMENTS_PATH)}` |",
        f"| Unreal Profile | `{rel(CURRENT_UNREAL_PATH)}` |",
        "| Schema | `contracts/current/ai_native_npc_schema_v2_0.yaml` |",
        "| Skill Registry | `contracts/current/skill_registry_v1.yaml` |",
        "| Goal Registry | `contracts/current/goal_registry_v1.yaml` |",
        "| Test Taxonomy | `contracts/current/test_taxonomy_v1.yaml` |",
        "",
        f"## Archive — {len(archives)} files",
        "",
        "| Type | Version | Path |",
        "|---|---:|---|",
    ]
    for row in archives:
        lines.append(f"| {row['type']} | {row['version']} | `{row['path']}` |")
    lines.extend([
        "",
        "Archive와 Legacy 계약은 역사적 기록이며 현재 구현 입력으로 사용할 수 없다.",
        "",
    ])
    return "\n".join(lines)


def write_source_file_map() -> None:
    SOURCE_FILE_MAP_PATH.write_text(source_file_map_text(), encoding="utf-8")


def validate_source_file_map() -> list[str]:
    if not SOURCE_FILE_MAP_PATH.exists():
        return ["source file map missing"]
    if SOURCE_FILE_MAP_PATH.read_text(encoding="utf-8") != source_file_map_text():
        return ["source file map missing or stale"]
    return []


def update_catalog() -> None:
    cfg = release_config()
    paths = default_paths(ROOT)
    canonical_paths = {
        "requirements": CURRENT_REQUIREMENTS_PATH,
        "unreal_profile": CURRENT_UNREAL_PATH,
        "schema": paths.schema,
        "skill_registry": paths.skill_registry,
        "goal_registry": paths.goal_registry,
        "test_taxonomy": paths.test_taxonomy,
    }
    versions = {
        "requirements": "0.4.6",
        "unreal_profile": "0.4.6",
        "schema": "2.0.0-rc5",
        "skill_registry": str(load_yaml(paths.skill_registry)["registry"]["version"]),
        "goal_registry": str(load_yaml(paths.goal_registry)["registry"]["version"]),
        "test_taxonomy": str(load_yaml(paths.test_taxonomy)["registry"]["version"]),
    }
    status = {
        "requirements": "current",
        "unreal_profile": "current",
        "schema": "rc5",
        "skill_registry": "current",
        "goal_registry": "current",
        "test_taxonomy": "current",
    }
    catalog = {
        "bundle": {
            "name": "ai_native_npc_document_harness",
            "version": cfg["bundle_version"],
            "language": "ko-KR",
            "release_epoch": cfg["release_epoch"],
            "purpose": "AI Native NPC 실행형 문서·Schema·Registry·Golden 계약 하네스",
        },
        "canonical": {
            role: {"path": rel(path), "version": versions[role], "status": status[role], "sha256": sha256_file(path)}
            for role, path in canonical_paths.items()
        },
        "contract_invariants": {
            "regular_target_slots": 16,
            "no_target_slot": 16,
            "total_target_slots": 17,
            "skill_count": 16,
            "candidate_count": 272,
            "event_slots": 12,
            "global_feature_count": 128,
            "target_feature_count": 48,
            "event_feature_count": 24,
            "candidate_pair_feature_count": 16,
            "candidate_formula": "skill_count * total_target_slots",
        },
        "archives": build_archive_catalog(ROOT),
        "excluded_duplicates": [],
    }
    write_json(CATALOG_PATH, catalog)

def update_freeze_status() -> None:
    cfg = release_config()
    write_json(
        FREEZE_STATUS_PATH,
        {
            "bundle_version": cfg["bundle_version"],
            "schema_version": cfg["schema_contract_revision"],
            "status": "SCHEMA_2_0_RC5",
            "phase0_decision": "GO",
            "schema_code_generation_decision": "GO",
            "schema_design_rc5_decision": "CONDITIONAL_GO",
            "mass_training_data_generation": "HOLD",
            "schema_final_freeze_decision": "NO_GO_CONDITIONAL",
            "schema_harness_freeze_readiness": "FREEZE_READY_RUNTIME_GATES_PENDING",
            "semantic_closure_decision": "PASS",
            "release_pipeline": "v0.4.6_semantic_closure",
        },
    )

def _gate(gate_id: str, status: str, tool: str, evidence_path: str | None, executed_at: str) -> dict[str, Any]:
    tool_path = ROOT / tool if tool != "pending" else None
    evidence_file = ROOT / evidence_path if evidence_path else None
    return {
        "id": gate_id,
        "normative": True,
        "status": status,
        "tool": tool,
        "tool_version": TOOL_VERSION if tool != "pending" else "pending",
        "tool_sha256": sha256_file(tool_path) if tool_path and tool_path.exists() else None,
        "executed_at": executed_at if status == "pass" else None,
        "evidence": {
            "path": evidence_path,
            "sha256": sha256_file(evidence_file) if status == "pass" and evidence_file and evidence_file.exists() else None,
        },
    }


def update_freeze_manifest() -> None:
    cfg = release_config()
    executed_at = cfg["release_epoch"]
    pass_defs = {
        "document_harness_integrity": ("tools/doc_harness.py", "tests/reports/harness_integrity_evidence.json"),
        "schema_semantic_validation": ("tools/validate_schema.py", "tests/reports/schema_semantic_validation.json"),
        "skill_registry_validation": ("tools/validate_schema.py", "tests/reports/schema_semantic_validation.json"),
        "goal_registry_validation": ("tools/validate_schema.py", "tests/reports/schema_semantic_validation.json"),
        "test_taxonomy_validation": ("tools/validate_schema.py", "tests/reports/schema_semantic_validation.json"),
        "generated_python_contract": ("tools/generate_contracts.py", "generated/python/ai_native_npc_contracts_generated.py"),
        "generated_cpp_contract": ("tools/generate_contracts.py", "generated/cpp/AINativeNPCContracts.generated.h"),
        "generated_code_reproducibility": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "golden_fixture_reproducibility": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "python_golden_parity": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "cpp_golden_parity": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "environment_independent_normative_report": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "lock_file_set_exact": ("tools/doc_harness.py", "tests/reports/harness_integrity_evidence.json"),
        "generated_document_appendix_parity": ("tools/doc_harness.py", "generated/docs/schema_reference.md"),
        "normalizer_semantic_hardening": ("tools/validate_schema.py", "tests/reports/schema_semantic_validation.json"),
        "hash_contract_codegen_parity": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "decision_contract_hash_golden": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "semantic_mutation_regression": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "manual_hash_literal_guard": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "normalizer_constraint_closure": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "dynamic_mutation_probe_regression": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "taxonomy_mutation_regression": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "critical_taxonomy_kpi_sync": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "manual_hash_magic_full_context_guard": ("tools/run_contract_tests.py", "tests/reports/contract_test_report.json"),
        "all_nonarchive_markdown_semantic_scope": ("tools/run_release_mutation_tests.py", "tests/reports/release_mutation_report.json"),
        "catalog_archive_exact_match": ("tools/doc_harness.py", "manifest/catalog.json"),
        "release_end_to_end_mutation_regression": ("tools/run_release_mutation_tests.py", "tests/reports/release_mutation_report.json"),
        "source_file_map_currentness": ("tools/doc_harness.py", "reports/SOURCE_FILE_MAP.md"),
    }
    planned = {
        "float_tensor_python_unreal_parity": "tests/reports/python_unreal_float_parity.json",
        "onnx_unreal_output_parity": "tests/reports/onnx_unreal_output_parity.json",
        "target_recall": "tests/reports/target_recall.json",
        "candidate_recall": "tests/reports/candidate_recall.json",
        "critical_suite": "tests/reports/critical_suite.json",
        "goal_fsm_runtime": "tests/reports/goal_fsm_runtime.json",
        "atomic_commit_runtime": "tests/reports/atomic_commit_runtime.json",
        "hidden_information_leakage": "tests/reports/hidden_information_leakage.json",
        "safety_fuzz": "tests/reports/safety_fuzz.json",
        "calibration_ood": "tests/reports/calibration_ood.json",
        "performance_budget": "tests/reports/performance_budget.json",
        "save_load_hot_swap": "tests/reports/save_load_hot_swap.json",
        "decision_contract_runtime_binding": "tests/reports/decision_contract_runtime_binding.json",
        "formal_freeze_approval": "governance/FREEZE_APPROVAL.md",
    }
    gates = [_gate(gate_id, "pass", tool, evidence, executed_at) for gate_id, (tool, evidence) in pass_defs.items()]
    gates.extend(_gate(gate_id, "pending", "pending", path, executed_at) for gate_id, path in planned.items())
    manifest = {
        "manifest_version": 5,
        "bundle_version": cfg["bundle_version"],
        "schema_contract_revision": cfg["schema_contract_revision"],
        "release_stage": "RC5",
        "status": "SCHEMA_2_0_RC5",
        "semantic_closure_decision": "PASS",
        "schema_design_rc5_decision": "CONDITIONAL_GO",
        "schema_final_freeze_decision": "NO_GO_CONDITIONAL",
        "mass_training_data_generation": "HOLD",
        "schema_harness_freeze_readiness": "FREEZE_READY_RUNTIME_GATES_PENDING",
        "test_taxonomy": {
            "path": "contracts/current/test_taxonomy_v1.yaml",
            "sha256": sha256_file(ROOT / "contracts/current/test_taxonomy_v1.yaml"),
            **critical_suite_metrics(load_yaml(ROOT / "contracts/current/test_taxonomy_v1.yaml")),
        },
        "gates": gates,
    }
    write_json(FREEZE_MANIFEST_PATH, manifest)


def write_validation_report() -> None:
    freeze = load_json(FREEZE_STATUS_PATH)
    manifest = load_json(FREEZE_MANIFEST_PATH)
    taxonomy = load_yaml(default_paths(ROOT).test_taxonomy)
    metrics = critical_suite_metrics(taxonomy)
    lines = [
        "# v0.4.6 Semantic Closure Validation Report",
        "",
        f'- Bundle: `{freeze["bundle_version"]}`',
        "- Result: **PASS**",
        f'- Schema status: `{freeze["status"]}`',
        f'- Release stage: `{manifest["release_stage"]}`',
        f'- Semantic closure: **{manifest["semantic_closure_decision"]}**',
        "- Normative report policy: compiler/version/timing/stdout/stderr excluded",
        "- Local diagnostics: `dist/local/` only, not locked or packed",
        "",
        "## Normative Gates",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]
    for gate in manifest["gates"]:
        evidence = gate.get("evidence") or {}
        lines.append(f'| `{gate["id"]}` | {gate["status"]} | `{evidence.get("path") or "-"}` |')
    lines.extend([
        "", "## Taxonomy-derived Critical Contract", "",
        f'- Critical contract: `{metrics["contract_id"]}`',
        f'- Family count: `{metrics["required_family_count"]}`',
        f'- Minimum cases per family: `{metrics["minimum_cases_per_family"]}`',
        f'- Critical minimum sequences: `{metrics["critical_minimum_sequence_count"]}`',
        "", "## Decision", "",
        "- Phase 0: GO",
        "- Schema design RC5: Conditional GO",
        "- Schema contract harness: FREEZE-READY / Runtime gates pending",
        "- Mass training data: HOLD",
        "- Final Schema Freeze: NO-GO / Conditional",
        "", "## Remaining Runtime Evidence", "",
        "- Python–Unreal Float Tensor parity",
        "- ONNX–Unreal output parity",
        "- Target/Candidate Recall",
        f'- Critical Suite {metrics["required_family_count"]} family × {metrics["minimum_cases_per_family"]} case = {metrics["critical_minimum_sequence_count"]} sequences',
        "- Goal FSM / Atomic Commit / Hidden Leakage",
        "- Safety Fuzz / Calibration OOD / Performance",
        "- Save/Load / Hot-swap / Formal Approval", "",
    ])
    VALIDATION_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

def rebuild_lock() -> None:
    records = {rel(path): {"sha256": sha256_file(path), "size": path.stat().st_size} for path in lock_scope_files()}
    lock = {
        "format_version": 3,
        "bundle_version": release_config()["bundle_version"],
        "self_excluded_paths": sorted(LOCK_SELF_EXCLUSIONS),
        "files": records,
    }
    write_json(LOCK_PATH, lock)
    CHECKSUM_PATH.write_text("".join(f"{meta['sha256']}  {path}\n" for path, meta in records.items()), encoding="utf-8")


def validate_lock() -> list[str]:
    if not LOCK_PATH.exists() or not CHECKSUM_PATH.exists():
        return ["lock/checksum missing"]
    lock = load_json(LOCK_PATH)
    errors: list[str] = []
    if set(lock.get("self_excluded_paths", [])) != LOCK_SELF_EXCLUSIONS:
        errors.append("lock self exclusion set mismatch")
    actual = {rel(path) for path in lock_scope_files()}
    locked = set(lock.get("files", {}))
    for path in sorted(actual - locked):
        errors.append(f"unlocked new file: {path}")
    for path in sorted(locked - actual):
        errors.append(f"locked file missing: {path}")
    for path, metadata in lock.get("files", {}).items():
        file_path = ROOT / path
        if not file_path.exists():
            continue
        if sha256_file(file_path) != metadata.get("sha256"):
            errors.append(f"SHA mismatch: {path}")
        if file_path.stat().st_size != metadata.get("size"):
            errors.append(f"size mismatch: {path}")
    expected_checksums = "".join(f"{metadata['sha256']}  {path}\n" for path, metadata in lock.get("files", {}).items())
    if CHECKSUM_PATH.read_text(encoding="utf-8") != expected_checksums:
        errors.append("checksums.sha256 does not match lock.json")
    all_package = {rel(path) for path in package_files()}
    if all_package != locked | LOCK_SELF_EXCLUSIONS:
        errors.append("actual package file set does not exactly equal lock set plus lock self files")
    return errors


def validate_catalog() -> list[str]:
    if not CATALOG_PATH.exists():
        return ["catalog missing"]
    return validate_catalog_data(ROOT, load_json(CATALOG_PATH))

def validate_schema_report() -> list[str]:
    if not SCHEMA_REPORT_PATH.exists():
        return ["schema semantic report missing"]
    expected = build_schema_report(ROOT)
    actual = load_json(SCHEMA_REPORT_PATH)
    errors: list[str] = []
    if actual != expected:
        errors.append("schema semantic report missing or stale")
    if actual.get("status") != "pass":
        errors.append("schema semantic report is not pass")
    return errors


def validate_freeze_manifest() -> list[str]:
    if not FREEZE_MANIFEST_PATH.exists():
        return ["freeze manifest missing"]
    manifest = load_json(FREEZE_MANIFEST_PATH)
    errors: list[str] = []
    gates = {gate.get("id"): gate for gate in manifest.get("gates", []) if isinstance(gate, dict)}
    expected = PASS_GATE_IDS | PENDING_GATE_IDS
    if set(gates) != expected:
        errors.append(f"freeze gate set mismatch missing={sorted(expected-set(gates))} extra={sorted(set(gates)-expected)}")
    for gate_id in PASS_GATE_IDS:
        gate = gates.get(gate_id, {})
        if gate.get("status") != "pass":
            errors.append(f"pass gate not pass: {gate_id}")
            continue
        tool_path = ROOT / gate.get("tool", "")
        evidence = gate.get("evidence") or {}
        evidence_path = ROOT / evidence.get("path", "")
        if not tool_path.exists() or gate.get("tool_sha256") != sha256_file(tool_path):
            errors.append(f"gate tool hash mismatch: {gate_id}")
        if not evidence_path.exists() or evidence.get("sha256") != sha256_file(evidence_path):
            errors.append(f"gate evidence hash mismatch: {gate_id}")
    for gate_id in PENDING_GATE_IDS:
        gate = gates.get(gate_id, {})
        if gate.get("status") != "pending":
            errors.append(f"pending gate status mismatch: {gate_id}")
        if (gate.get("evidence") or {}).get("sha256") is not None:
            errors.append(f"pending gate must not claim evidence hash: {gate_id}")
    if manifest.get("release_stage") != "RC5":
        errors.append("freeze manifest release stage must be RC5")
    if manifest.get("status") != "SCHEMA_2_0_RC5":
        errors.append("freeze manifest status must be SCHEMA_2_0_RC5")
    if manifest.get("semantic_closure_decision") != "PASS":
        errors.append("freeze manifest semantic_closure_decision must be PASS")
    if manifest.get("schema_final_freeze_decision") != "NO_GO_CONDITIONAL":
        errors.append("freeze manifest final decision must remain NO_GO_CONDITIONAL")
    taxonomy = manifest.get("test_taxonomy", {})
    taxonomy_path = ROOT / taxonomy.get("path", "")
    if not taxonomy_path.exists() or taxonomy.get("sha256") != sha256_file(taxonomy_path):
        errors.append("freeze manifest test taxonomy hash mismatch")
    else:
        expected_taxonomy = critical_suite_metrics(load_yaml(taxonomy_path))
        for key, expected_value in expected_taxonomy.items():
            if taxonomy.get(key) != expected_value:
                errors.append(f"freeze manifest taxonomy value mismatch: {key}")
    return errors


def validate_links(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#"):
            continue
        clean = target.split("#", 1)[0]
        candidate = (path.parent / clean).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{rel(path)}: link outside bundle {target}")
            continue
        if not candidate.exists():
            errors.append(f"{rel(path)}: missing link {target}")
    return errors


def run_validation(strict: bool = False, check_lock: bool = True, local_checks: bool = True) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = [CATALOG_PATH, FREEZE_STATUS_PATH, FREEZE_MANIFEST_PATH, RELEASE_CONFIG_PATH, SCHEMA_REPORT_PATH, CONTRACT_REPORT_PATH, INTEGRITY_EVIDENCE_PATH, RELEASE_MUTATION_REPORT_PATH, SOURCE_FILE_MAP_PATH, ROOT / "requirements.txt"]
    if check_lock:
        required.extend([LOCK_PATH, CHECKSUM_PATH])
    for path in required:
        if not path.exists():
            errors.append(f"required file missing: {rel(path)}")
    if errors:
        return errors, warnings

    errors.extend(validate_contracts(default_paths(ROOT)))
    errors.extend(check_generated(ROOT))
    errors.extend(validate_document_appendices())
    errors.extend(check_golden(ROOT))
    errors.extend(validate_schema_report())
    errors.extend(validate_normative_report(ROOT, CONTRACT_REPORT_PATH))
    errors.extend(validate_release_mutation_report(ROOT, RELEASE_MUTATION_REPORT_PATH))
    if local_checks:
        local_errors, local_warnings = local_verify(ROOT, require_cpp=False)
        errors.extend(local_errors)
        warnings.extend(local_warnings)
    errors.extend(validate_catalog())
    errors.extend(validate_source_file_map())
    errors.extend(validate_freeze_manifest())
    errors.extend(validate_integrity_evidence())
    if check_lock:
        errors.extend(validate_lock())

    catalog = load_json(CATALOG_PATH)
    canonical = catalog["canonical"]
    req = ROOT / canonical["requirements"]["path"]
    ue = ROOT / canonical["unreal_profile"]["path"]
    paths = default_paths(ROOT)
    req_text = req.read_text(encoding="utf-8")
    ue_text = ue.read_text(encoding="utf-8")
    if extract_markdown_value(req_text, "문서 버전") != "v0.4.6":
        errors.append("requirements version must be v0.4.6")
    if extract_markdown_value(ue_text, "문서 버전") != "v0.4.6":
        errors.append("UE profile version must be v0.4.6")
    dependencies = [
        ("상위 기준서 SHA-256", req),
        ("Schema YAML SHA-256", paths.schema),
        ("Skill Registry SHA-256", paths.skill_registry),
        ("Goal Registry SHA-256", paths.goal_registry),
        ("Test Taxonomy SHA-256", paths.test_taxonomy),
    ]
    for label, path in dependencies:
        if extract_markdown_value(ue_text, label) != sha256_file(path):
            errors.append(f"UE embedded dependency hash mismatch: {label}")

    for markdown in [ROOT / "README.md", ROOT / "INDEX.md"]:
        errors.extend(validate_links(markdown))
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            errors.append(f"symlink forbidden in bundle: {rel(path)}")
    if list((ROOT / "contracts/current").glob("*.json")):
        errors.append("JSON schema forbidden in contracts/current")

    freeze = load_json(FREEZE_STATUS_PATH)
    if freeze.get("schema_final_freeze_decision") != "NO_GO_CONDITIONAL":
        errors.append("freeze status final decision must be NO_GO_CONDITIONAL")
    if freeze.get("mass_training_data_generation") != "HOLD":
        errors.append("mass training data must remain HOLD")
    if freeze.get("schema_harness_freeze_readiness") != "FREEZE_READY_RUNTIME_GATES_PENDING":
        errors.append("schema harness readiness must be READY_RUNTIME_GATES_PENDING")
    if freeze.get("semantic_closure_decision") != "PASS":
        errors.append("semantic closure decision must be PASS")
    warnings.append("Unreal Float/ONNX/Runtime gates remain pending; Schema harness is RC5 Freeze-ready; Unreal Runtime gates remain pending.")
    if strict:
        unexpected = [warning for warning in warnings if not (warning.startswith("Unreal Float/ONNX/Runtime") or warning.startswith("local contract check not run: cpp_golden_parity"))]
        errors.extend(f"strict warning: {warning}" for warning in unexpected)
    return errors, warnings


def refresh_release_evidence() -> None:
    generate_contracts(ROOT, ROOT)
    sync_document_appendices()
    update_ue_dependency_hashes()
    update_catalog()
    write_source_file_map()
    document_errors = validate_document_appendices()
    if document_errors:
        raise SystemExit("Document semantic validation failed:\n- " + "\n- ".join(document_errors))
    generate_golden(ROOT)
    schema_report = build_schema_report(ROOT)
    write_json(SCHEMA_REPORT_PATH, schema_report)
    if schema_report["status"] != "pass":
        raise SystemExit("Schema semantic validation failed")
    if os.environ.get("ANPC_MUTATION_CHILD") != "1":
        mutation_report = write_release_mutation_report(ROOT, RELEASE_MUTATION_REPORT_PATH)
        if mutation_report["status"] != "pass":
            raise SystemExit("Release mutation regression failed")
    contract_report = write_contract_test_report(ROOT, CONTRACT_REPORT_PATH, LOCAL_DIAGNOSTICS_PATH, require_cpp=True)
    if contract_report["status"] != "pass":
        raise SystemExit("Contract test suite failed")
    update_freeze_status()
    update_freeze_manifest()
    write_validation_report()
    write_integrity_evidence()
    update_freeze_manifest()
    write_validation_report()
    write_integrity_evidence()
    update_freeze_manifest()
    rebuild_lock()

def zip_mode(path: Path) -> int:
    r = rel(path)
    if r.startswith("tools/") and path.suffix in {".py", ".sh"}:
        return 0o755
    return 0o644


def build_zip(output: Path) -> None:
    cfg = release_config()
    root_name = cfg["package_root_name"]
    zip_time = tuple(cfg["zip_time"])
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files():
            info = zipfile.ZipInfo(f"{root_name}/{rel(path)}")
            info.date_time = zip_time
            info.create_system = 3
            info.external_attr = (zip_mode(path) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def validate_zip(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            errors.append(f"ZIP CRC failure: {bad}")
        for info in archive.infolist():
            posix_path = PurePosixPath(info.filename)
            if posix_path.is_absolute() or ".." in posix_path.parts:
                errors.append(f"unsafe ZIP path: {info.filename}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                errors.append(f"symlink ZIP entry forbidden: {info.filename}")
            if info.flag_bits & 0x1:
                errors.append(f"encrypted ZIP entry forbidden: {info.filename}")
    return errors


def deterministic_pack(output: Path) -> Path:
    output = output.resolve()
    output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as td:
        first = Path(td) / "first.zip"
        second = Path(td) / "second.zip"
        build_zip(first)
        build_zip(second)
        if first.read_bytes() != second.read_bytes():
            raise SystemExit("non-deterministic ZIP build")
        shutil.copyfile(first, output)
    zip_errors = validate_zip(output)
    if zip_errors:
        raise SystemExit("\n".join(zip_errors))
    output.with_suffix(output.suffix + ".sha256").write_text(f"{sha256_file(output)}  {output.name}\n", encoding="utf-8")
    return output


def release(output: Path | None) -> Path:
    refresh_release_evidence()
    errors, warnings = run_validation(strict=True, check_lock=True, local_checks=False)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
    if output is None:
        output = ROOT.parent / f"ai_native_npc_document_harness_v{release_config()['bundle_version']}.zip"
    result = deterministic_pack(output)
    print(result)
    return result


def status() -> None:
    freeze = load_json(FREEZE_STATUS_PATH)
    print(f"Bundle {freeze['bundle_version']}")
    print(f"Schema {freeze['schema_version']} {freeze['status']}")
    print(f"Phase 0: {freeze['phase0_decision']}")
    print(f"Schema design RC5: {freeze['schema_design_rc5_decision']}")
    print(f"Schema harness: {freeze['schema_harness_freeze_readiness']}")
    print(f"Code generation: {freeze['schema_code_generation_decision']}")
    print(f"Mass training data: {freeze['mass_training_data_generation']}")
    print(f"Final Freeze: {freeze['schema_final_freeze_decision']}")


def inventory() -> None:
    catalog = load_json(CATALOG_PATH)
    for role, item in catalog["canonical"].items():
        print(f"{role:20} {item['version']:12} {item['status']:20} {item['path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("inventory")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--strict", action="store_true")
    sub.add_parser("report")
    sub.add_parser("refresh")
    sub.add_parser("rebuild-lock")
    for name in ["pack", "release"]:
        pack_parser = sub.add_parser(name)
        pack_parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.command == "status":
        status()
    elif args.command == "inventory":
        inventory()
    elif args.command == "validate":
        errors, warnings = run_validation(strict=args.strict)
        for warning in warnings:
            print(f"WARNING: {warning}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            raise SystemExit(1)
        print("PASS")
    elif args.command == "report":
        print(VALIDATION_REPORT_PATH)
    elif args.command == "refresh":
        refresh_release_evidence()
        print("PASS")
    elif args.command == "rebuild-lock":
        rebuild_lock()
        print(LOCK_PATH)
    elif args.command in {"pack", "release"}:
        release(args.output)


if __name__ == "__main__":
    main()
