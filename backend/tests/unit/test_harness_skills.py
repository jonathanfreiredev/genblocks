"""The shelf, read the way the agent reads it.

The index is what the model is told exists, and the bodies are the standard it is
held to. A shelf that drifts from its index would have the agent reading a
document about something else — so the name, the line and the file are checked
against each other here.
"""

import pytest

from app.harness import skills
from app.harness.skills import ALL, BadSkill, NotASkill

# The shelf by name, in the order the index lists it. Written out here rather than
# read from the module: a shelf that changed shape should have to change a test.
SHELF = (
    "blocks",
    "dependencies",
    "fonts",
    "accessibility",
    "composition",
    "copy",
    "motion",
    "cliches",
)


def test_the_shelf_is_the_one_the_index_lists():
    assert tuple(ALL) == SHELF


def test_the_index_is_one_line_per_skill():
    lines = skills.index().splitlines()

    assert len(lines) == len(SHELF)
    for name, line in zip(SHELF, lines, strict=True):
        assert line.startswith(f"- {name}: ")


def test_a_skill_reads_as_the_document_it_is():
    assert skills.read("motion").startswith("# Motion")
    assert "useReducedMotion" in skills.read("motion")
    assert "reduced motion" in skills.read("accessibility")
    # Composition carries numbers a builder can check, not adjectives.
    assert "60-75 characters" in skills.read("composition")
    assert "Three distances" in skills.read("composition")
    # Copy names the shapes instead of asking for "human" writing.
    assert "not just a scheduler" in skills.read("copy")
    assert "Sales fog" in skills.read("copy")


def test_reading_something_that_is_not_there_names_what_is():
    with pytest.raises(NotASkill) as unknown:
        skills.read("vibes")

    assert "vibes" in str(unknown.value)
    assert "motion" in str(unknown.value)


def test_the_version_names_the_whole_shelf():
    version = skills.version()

    assert len(version) == skills.VERSION_LENGTH
    assert all(character in "0123456789abcdef" for character in version)
    # Stable: the same shipped text hashes the same way on every import.
    assert version == skills.version()


def test_a_missing_document_is_a_mistake_in_the_repository(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, "SKILLS_DIR", tmp_path)

    with pytest.raises(BadSkill) as missing:
        skills._load("motion", "when movement earns its place")

    assert "motion.md" in str(missing.value)


def test_a_file_with_no_title_is_refused(tmp_path, monkeypatch):
    (tmp_path / "motion.md").write_text("just some words\n")
    monkeypatch.setattr(skills, "SKILLS_DIR", tmp_path)

    with pytest.raises(BadSkill):
        skills._load("motion", "when movement earns its place")
