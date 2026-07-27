#!/usr/bin/env python3
"""End-to-end release mutation regressions for global Markdown semantic scope."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from contractlib import TOOL_VERSION, default_paths, load_yaml, sha256_file

REPORT_VERSION = 1
TEST_IDS = [
    "readme_stale_archived_magic_rejected",
    "readme_lowercase_magic_assignment_rejected",
    "readme_stale_critical_denominator_rejected",
]


def _different_ascii_same_length(value: str) -> str:
    if not value:
        return "X"
    first = "Z" if value[0] != "Z" else "Y"
    return first + value[1:]


def _copy_root(root: Path, destination: Path) -> Path:
    clone = destination / root.name
    shutil.copytree(
        root,
        clone,
        ignore=shutil.ignore_patterns("dist", "__pycache__", "*.pyc"),
    )
    return clone


def _run_child_release(clone: Path, output: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env["ANPC_MUTATION_CHILD"] = "1"
    process = subprocess.run(
        [sys.executable, str(clone / "tools/doc_harness.py"), "release", "--output", str(output)],
        cwd=clone,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    return process.returncode, process.stdout


def _candidate_magic(root: Path) -> str:
    schema = load_yaml(default_paths(root).schema)
    return str(schema["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"])


def _mutate_stale_magic(clone: Path, old_magic: str) -> None:
    import yaml
    schema_path = default_paths(clone).schema
    data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    data["hash_contract"]["candidate_set_hash"]["fields"][0]["value_ascii"] = _different_ascii_same_length(old_magic)
    schema_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    with (clone / "README.md").open("a", encoding="utf-8") as f:
        f.write(f"\nCandidate magic is {old_magic}.\n")


def _mutate_lowercase_magic(clone: Path, _: str) -> None:
    with (clone / "README.md").open("a", encoding="utf-8") as f:
        f.write("\nCandidate magic is abcdefgh.\n")


def _mutate_critical(clone: Path, _: str) -> None:
    with (clone / "README.md").open("a", encoding="utf-8") as f:
        f.write("\nCritical Suite 256 sequences.\n")


def execute(root: Path) -> dict[str, Any]:
    root = root.resolve()
    old_magic = _candidate_magic(root)
    cases: list[tuple[str, Callable[[Path, str], None], tuple[str, ...]]] = [
        (TEST_IDS[0], _mutate_stale_magic, ("known hash magic token", "manual hash magic assignment")),
        (TEST_IDS[1], _mutate_lowercase_magic, ("manual hash magic assignment",)),
        (TEST_IDS[2], _mutate_critical, ("stale Critical Suite denominator",)),
    ]
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for index, (test_id, mutate, expected_fragments) in enumerate(cases):
            case_dir = base / f"case_{index}"
            case_dir.mkdir()
            clone = _copy_root(root, case_dir)
            mutate(clone, old_magic)
            output = case_dir / "mutated.zip"
            returncode, combined = _run_child_release(clone, output)
            passed = returncode != 0 and not output.exists() and any(fragment in combined for fragment in expected_fragments)
            rows.append({"id": test_id, "status": "pass" if passed else "fail"})
    return {
        "report_version": REPORT_VERSION,
        "contract_revision": load_yaml(default_paths(root).schema)["schema"]["contract_revision"],
        "status": "pass" if all(row["status"] == "pass" for row in rows) else "fail",
        "tool": "tools/run_release_mutation_tests.py",
        "tool_version": TOOL_VERSION,
        "tool_sha256": sha256_file(root / "tools/run_release_mutation_tests.py"),
        "input_hashes": {
            "schema": sha256_file(default_paths(root).schema),
            "readme": sha256_file(root / "README.md"),
            "doc_harness": sha256_file(root / "tools/doc_harness.py"),
            "contractlib": sha256_file(root / "tools/contractlib.py"),
        },
        "checks": rows,
    }


def write_report(root: Path, path: Path) -> dict[str, Any]:
    report = execute(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def validate_report(root: Path, path: Path) -> list[str]:
    if not path.exists():
        return ["release mutation report missing"]
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"release mutation report parse failure: {exc}"]
    errors: list[str] = []
    if report.get("report_version") != REPORT_VERSION:
        errors.append("release mutation report version mismatch")
    if report.get("tool_version") != TOOL_VERSION:
        errors.append("release mutation report tool version mismatch")
    if report.get("tool_sha256") != sha256_file(root / "tools/run_release_mutation_tests.py"):
        errors.append("release mutation report tool hash mismatch")
    expected_inputs = {
        "schema": sha256_file(default_paths(root).schema),
        "readme": sha256_file(root / "README.md"),
        "doc_harness": sha256_file(root / "tools/doc_harness.py"),
        "contractlib": sha256_file(root / "tools/contractlib.py"),
    }
    if report.get("input_hashes") != expected_inputs:
        errors.append("release mutation report input hashes mismatch")
    checks = report.get("checks", [])
    if [row.get("id") for row in checks if isinstance(row, dict)] != TEST_IDS:
        errors.append("release mutation report test id list mismatch")
    if report.get("status") != "pass" or any(row.get("status") != "pass" for row in checks if isinstance(row, dict)):
        errors.append("release mutation report is not pass")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "tests/reports/release_mutation_report.json"
    if args.check:
        errors = validate_report(root, output)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            raise SystemExit(1)
        print("PASS")
        return
    report = write_report(root, output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
