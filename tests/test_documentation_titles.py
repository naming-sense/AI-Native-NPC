"""Keep repository documentation focused on its actual subject."""
from pathlib import Path
import hashlib
import importlib.util
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_documentation_contains_no_personal_contact_number() -> None:
    documents = [ROOT / "README.md"]
    for directory in ("docs", "generated/docs"):
        documents.extend((ROOT / directory).rglob("*.md"))
    contact_pattern = re.compile(r"(?<!\d)01[016789][- ]\d{3,4}[- ]\d{4}(?!\d)")
    violations = [str(path.relative_to(ROOT)) for path in documents
                  if contact_pattern.search(path.read_text(encoding="utf-8"))]
    assert not violations, f"Personal contact text remains in: {violations}"


@pytest.mark.parametrize("kind,title", [
    ("goal", "# General NPC Goal Gameplay Semantics V1"),
    ("skill", "# General NPC Skill Execution Semantics V1"),
])
def test_generated_document_starts_with_its_subject(kind: str, title: str) -> None:
    suffix = "goal_gameplay_semantics_v1" if kind == "goal" else "skill_execution_semantics_v1"
    path = ROOT / "tools" / f"generate_{suffix}.py"
    spec = importlib.util.spec_from_file_location(f"doc_title_{kind}", path)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    registry_path = ROOT / "contracts/current" / f"{kind}_registry_v1.yaml"
    registry_bytes = registry_path.read_bytes()
    registry = yaml.safe_load(registry_bytes)
    digest = hashlib.sha256(registry_bytes).hexdigest()
    if kind == "goal":
        skills = yaml.safe_load((ROOT / "contracts/current/skill_registry_v1.yaml").read_text())
        schema = yaml.safe_load((ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml").read_text())
        text = generator.generate_markdown(registry, skills, schema, digest)
    else:
        text = generator.generate_markdown(registry, digest)
    assert text.splitlines()[0] == title
    assert (ROOT / "generated/docs" / f"{suffix}.md").read_text(encoding="utf-8") == text
