#!/usr/bin/env python3
"""Run deterministic contract evidence tests.

The normative JSON deliberately excludes compiler version, wall-clock duration,
stdout ordering, and platform paths. Those values are written only to dist/local.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from contractlib import TOOL_VERSION, default_paths, sha256_file, validate_contracts
from generate_contracts import check as check_generated
from generate_golden import check as check_golden

PYTHON_TEST_IDS = [
    "candidate_formula",
    "contract_revision",
    "discrete_hash_vectors",
    "decision_contract_hash",
    "normalizer_vectors",
    "parameter_decode_and_clamp",
    "quantization",
    "semantic_mutation_regression",
    "manual_hash_literal_guard",
    "normalizer_constraint_closure",
    "padding_zero_range_closure",
    "dynamic_mutation_probes",
    "magic_context_mutations",
    "stale_old_magic_rejection",
    "critical_taxonomy_kpi_sync",
    "global_nonarchive_markdown_scope",
    "catalog_missing_archive_rejection",
    "catalog_ghost_archive_rejection",
    "source_file_map_exact",
]
CPP_TEST_IDS = [
    "candidate_index",
    "target_mask_lsb_pack",
    "candidate_mask_lsb_pack",
    "target_handle_canonical_serialization",
    "candidate_set_sha256",
    "decision_contract_sha256",
    "slotter_integer_quantization",
    "skill_parameter_decode_clamp",
    "generated_normalizer_parity",
]


def compiler_command() -> list[str] | None:
    configured = os.environ.get("CXX")
    candidates = [configured] if configured else []
    candidates.extend(["c++", "g++", "clang++"])
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate)
        if path:
            return [path]
    return None


def input_hashes(root: Path) -> dict[str, str]:
    paths = default_paths(root)
    files = {
        "schema": paths.schema,
        "skill_registry": paths.skill_registry,
        "goal_registry": paths.goal_registry,
        "test_taxonomy": paths.test_taxonomy,
        "generated_python": root / "generated/python/ai_native_npc_contracts_generated.py",
        "generated_cpp": root / "generated/cpp/AINativeNPCContracts.generated.h",
        "golden_discrete": root / "tests/golden/discrete_hash_vectors.json",
        "golden_normalizers": root / "tests/golden/normalizer_vectors.json",
        "cpp_golden_source": root / "tests/generated_cpp_golden_test.cpp",
        "python_test_source": root / "tests/test_generated_contract.py",
        "semantic_hardening_test_source": root / "tests/test_semantic_hardening.py",
        "contractlib": root / "tools/contractlib.py",
        "generator": root / "tools/generate_contracts.py",
        "golden_generator": root / "tools/generate_golden.py",
        "test_runner": root / "tools/run_contract_tests.py",
        "release_mutation_tool": root / "tools/run_release_mutation_tests.py",
        "source_file_map": root / "reports/SOURCE_FILE_MAP.md",
    }
    return {name: sha256_file(path) for name, path in files.items()}


def _run_python_suite(root: Path) -> tuple[bool, dict[str, Any]]:
    started = time.perf_counter()
    process = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests"), "-p", "test_*.py", "-v"],
        text=True,
        capture_output=True,
        cwd=root,
    )
    return process.returncode == 0, {
        "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "duration_seconds": time.perf_counter() - started,
        "python_version": sys.version,
    }


def _run_cpp_suite(root: Path, require_cpp: bool) -> tuple[str, dict[str, Any]]:
    compiler = compiler_command()
    if compiler is None:
        if require_cpp:
            return "fail", {"error": "C++17 compiler not found; set CXX or install c++/g++/clang++"}
        return "not_run", {"warning": "C++17 compiler not found"}

    version = subprocess.run(compiler + ["--version"], text=True, capture_output=True)
    source = root / "tests/generated_cpp_golden_test.cpp"
    with tempfile.TemporaryDirectory() as td:
        binary = Path(td) / ("contract_golden.exe" if os.name == "nt" else "contract_golden")
        compile_cmd = compiler + ["-std=c++17", "-O0", "-I", str(root), str(source), "-o", str(binary)]
        started = time.perf_counter()
        compiled = subprocess.run(compile_cmd, text=True, capture_output=True, cwd=root)
        compile_duration = time.perf_counter() - started
        if compiled.returncode != 0:
            return "fail", {
                "compiler_path": compiler[0],
                "compiler_version": version.stdout.splitlines()[0] if version.stdout else version.stderr.splitlines()[0] if version.stderr else "unknown",
                "compile_command": compile_cmd,
                "compile_returncode": compiled.returncode,
                "compile_stdout": compiled.stdout,
                "compile_stderr": compiled.stderr,
                "compile_duration_seconds": compile_duration,
            }
        started = time.perf_counter()
        executed = subprocess.run([str(binary)], text=True, capture_output=True, cwd=root)
        execute_duration = time.perf_counter() - started
        return ("pass" if executed.returncode == 0 else "fail"), {
            "compiler_path": compiler[0],
            "compiler_version": version.stdout.splitlines()[0] if version.stdout else version.stderr.splitlines()[0] if version.stderr else "unknown",
            "compile_command": compile_cmd,
            "compile_returncode": compiled.returncode,
            "compile_stdout": compiled.stdout,
            "compile_stderr": compiled.stderr,
            "compile_duration_seconds": compile_duration,
            "execute_returncode": executed.returncode,
            "execute_stdout": executed.stdout,
            "execute_stderr": executed.stderr,
            "execute_duration_seconds": execute_duration,
        }


def execute(root: Path, require_cpp: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {"diagnostic_only": True, "environment": {"platform": sys.platform}}

    semantic_errors = validate_contracts(default_paths(root))
    checks.append({"id": "schema_semantic_validation", "status": "pass" if not semantic_errors else "fail"})
    diagnostics["schema_semantic_validation"] = {"errors": semantic_errors}

    generated_errors = check_generated(root)
    checks.append({"id": "generated_code_reproducibility", "status": "pass" if not generated_errors else "fail"})
    diagnostics["generated_code_reproducibility"] = {"errors": generated_errors}

    golden_errors = check_golden(root)
    checks.append({"id": "golden_fixture_reproducibility", "status": "pass" if not golden_errors else "fail"})
    diagnostics["golden_fixture_reproducibility"] = {"errors": golden_errors}

    syntax_ok = True
    syntax_errors: list[str] = []
    for path in [
        root / "generated/python/ai_native_npc_contracts_generated.py",
        root / "tools/contractlib.py",
        root / "tools/validate_schema.py",
        root / "tools/generate_contracts.py",
        root / "tools/generate_golden.py",
        root / "tools/run_contract_tests.py",
        root / "tools/run_release_mutation_tests.py",
        root / "tools/doc_harness.py",
    ]:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # pragma: no cover
            syntax_ok = False
            syntax_errors.append(f"{path.name}: {exc}")
    checks.append({"id": "python_syntax", "status": "pass" if syntax_ok else "fail"})
    diagnostics["python_syntax"] = {"errors": syntax_errors}

    python_ok, python_diag = _run_python_suite(root)
    checks.append({"id": "python_golden_parity", "status": "pass" if python_ok else "fail", "test_ids": PYTHON_TEST_IDS})
    diagnostics["python_golden_parity"] = python_diag

    cpp_status, cpp_diag = _run_cpp_suite(root, require_cpp=require_cpp)
    checks.append({"id": "cpp_golden_parity", "status": cpp_status, "test_ids": CPP_TEST_IDS, "language_standard": "c++17"})
    diagnostics["cpp_golden_parity"] = cpp_diag

    accepted = {"pass"} if require_cpp else {"pass", "not_run"}
    status = "pass" if all(check["status"] in accepted for check in checks) else "fail"
    report = {
        "report_version": 6,
        "contract_revision": __import__("yaml").safe_load((root / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text(encoding="utf-8"))["schema"]["contract_revision"],
        "status": status,
        "tool": "tools/run_contract_tests.py",
        "tool_version": TOOL_VERSION,
        "tool_sha256": sha256_file(root / "tools/run_contract_tests.py"),
        "input_hashes": input_hashes(root),
        "checks": checks,
    }
    diagnostics["normative_report_sha256_if_written"] = None
    return report, diagnostics


def write_report(root: Path, report_path: Path, diagnostics_path: Path | None = None, require_cpp: bool = True) -> dict[str, Any]:
    report, diagnostics = execute(root, require_cpp=require_cpp)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if diagnostics_path is not None:
        diagnostics["normative_report_sha256_if_written"] = sha256_file(report_path)
        diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostics_path.write_text(json.dumps(diagnostics, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def validate_normative_report(root: Path, report_path: Path) -> list[str]:
    errors: list[str] = []
    if not report_path.exists():
        return ["contract test report missing"]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"contract test report parse failure: {exc}"]
    if report.get("report_version") != 6:
        errors.append("contract test report version must be 6")
    if report.get("tool_version") != TOOL_VERSION:
        errors.append("contract test report tool_version mismatch")
    if report.get("tool_sha256") != sha256_file(root / "tools/run_contract_tests.py"):
        errors.append("contract test report tool hash mismatch")
    if report.get("input_hashes") != input_hashes(root):
        errors.append("contract test report input hashes mismatch")
    if report.get("status") != "pass":
        errors.append("contract test report status is not pass")
    checks = {row.get("id"): row for row in report.get("checks", []) if isinstance(row, dict)}
    expected = {
        "schema_semantic_validation",
        "generated_code_reproducibility",
        "golden_fixture_reproducibility",
        "python_syntax",
        "python_golden_parity",
        "cpp_golden_parity",
    }
    if set(checks) != expected:
        errors.append(f"contract test check set mismatch: {sorted(checks)}")
    for check_id in expected:
        if checks.get(check_id, {}).get("status") != "pass":
            errors.append(f"contract test {check_id} is not pass")
    if checks.get("python_golden_parity", {}).get("test_ids") != PYTHON_TEST_IDS:
        errors.append("python Golden test id list mismatch")
    if checks.get("cpp_golden_parity", {}).get("test_ids") != CPP_TEST_IDS:
        errors.append("C++ Golden test id list mismatch")
    # Environment-dependent fields are forbidden in normative evidence.
    serialized = json.dumps(report, sort_keys=True)
    for forbidden in ["compiler_version", "duration_seconds", "stdout", "stderr", "python_version"]:
        if forbidden in serialized:
            errors.append(f"environment-dependent field leaked into normative report: {forbidden}")
    return errors


def local_verify(root: Path, require_cpp: bool = False) -> tuple[list[str], list[str]]:
    report, _ = execute(root, require_cpp=require_cpp)
    errors: list[str] = []
    warnings: list[str] = []
    for check in report["checks"]:
        if check["status"] == "fail":
            errors.append(f"local contract check failed: {check['id']}")
        elif check["status"] == "not_run":
            warnings.append(f"local contract check not run: {check['id']}")
    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diagnostics-output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-missing-cpp", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "tests/reports/contract_test_report.json"
    diagnostics = args.diagnostics_output or root / "dist/local/contract_test_diagnostics.json"
    if args.check:
        errors = validate_normative_report(root, output)
        local_errors, local_warnings = local_verify(root, require_cpp=not args.allow_missing_cpp)
        errors.extend(local_errors)
        for warning in local_warnings:
            print(f"WARNING: {warning}")
        if errors:
            print("\n".join(errors), file=sys.stderr)
            raise SystemExit(1)
        print("PASS")
        return
    report = write_report(root, output, diagnostics, require_cpp=not args.allow_missing_cpp)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
