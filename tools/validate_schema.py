#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contractlib import TOOL_VERSION, default_paths, load_yaml, sha256_file, validate_contracts


def build_report(root: Path) -> dict:
    paths = default_paths(root)
    errors = validate_contracts(paths)
    schema = load_yaml(paths.schema)
    return {
        "report_version": 6,
        "tool": "tools/validate_schema.py",
        "tool_version": TOOL_VERSION,
        "tool_sha256": sha256_file(root / "tools/validate_schema.py"),
        "contract_revision": schema["schema"]["contract_revision"],
        "status": "pass" if not errors else "fail",
        "source_hashes": {
            "schema": sha256_file(paths.schema),
            "boss_pattern_contract": sha256_file(paths.boss_pattern_contract),
            "skill_registry": sha256_file(paths.skill_registry),
            "goal_registry": sha256_file(paths.goal_registry),
            "test_taxonomy": sha256_file(paths.test_taxonomy),
        },
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    result = build_report(root)
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    output = args.json_output or root / "tests/reports/schema_semantic_validation.json"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != text:
            print("Schema semantic report missing or stale")
            raise SystemExit(1)
        print("PASS")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
