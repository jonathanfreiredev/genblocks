"""The rubrics, as the judge reads them.

The dimension keys are a contract in three places — the judge answers with them,
an attempt stores them flat in ``scores``, and the panel labels them — and none
of those three owns it. These read the shipped rubrics the way the judge does,
which is what keeps the list and the prose from drifting apart.
"""

import pytest

from app.judge import rubrics
from app.judge.rubrics import COMPONENTS, IMAGES, BadRubric, Rubric, rubric_for

# The dimensions the component panel has a row for *and* the judge scores.
# Novelty is the panel's sixth row and is missing here on purpose: it is the
# distance to the nearest blocks in the library, and the library has no vectors
# until Fase 10.
COMPONENT_DIMENSIONS = ("render", "accessibility", "visual", "copy", "compliance")
IMAGE_DIMENSIONS = ("visual", "prompt_fit", "compliance")


def test_the_component_rubric_scores_the_panel_s_rows_in_its_order():
    assert COMPONENTS.dimensions == COMPONENT_DIMENSIONS


def test_the_image_rubric_is_the_shorter_one():
    assert IMAGES.dimensions == IMAGE_DIMENSIONS


def test_novelty_is_scored_by_nobody_yet():
    assert "novelty" not in COMPONENTS.dimensions


def test_a_rubric_carries_the_text_the_judge_reads():
    assert "## render" in COMPONENTS.text
    assert "## accessibility" in COMPONENTS.text
    assert "## prompt_fit" in IMAGES.text


def test_the_version_names_the_rubric_and_hashes_its_text():
    version = COMPONENTS.version

    assert version.startswith("components-")
    digest = version.split("-", 1)[1]
    assert len(digest) == rubrics.VERSION_LENGTH
    assert all(character in "0123456789abcdef" for character in digest)


def test_editing_what_a_rubric_says_changes_its_version():
    edited = Rubric(
        name=COMPONENTS.name,
        kind=COMPONENTS.kind,
        dimensions=COMPONENTS.dimensions,
        text=COMPONENTS.text.replace("Whether someone decided.", "Whether anyone cared."),
    )

    assert edited.version != COMPONENTS.version


def test_asking_for_another_dimension_changes_the_version():
    wider = Rubric(
        name=COMPONENTS.name,
        kind=COMPONENTS.kind,
        dimensions=(*COMPONENTS.dimensions, "novelty"),
        text=COMPONENTS.text,
    )

    assert wider.version != COMPONENTS.version


def test_a_rubric_that_never_describes_a_dimension_is_refused(tmp_path, monkeypatch):
    (tmp_path / "components.md").write_text("# Judging\n\n## render\n\nDid it come out.\n")
    monkeypatch.setattr(rubrics, "RUBRICS_DIR", tmp_path)

    with pytest.raises(BadRubric) as refused:
        rubrics._load("components", kind="component", dimensions=("render", "copy"))

    assert "copy" in str(refused.value)


def test_a_rubric_file_that_is_not_there_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(rubrics, "RUBRICS_DIR", tmp_path)

    with pytest.raises(BadRubric) as refused:
        rubrics._load("components", kind="component", dimensions=("render",))

    assert "components.md" in str(refused.value)


def test_the_two_kinds_are_looked_up_by_the_taxonomy_s_own_words():
    assert rubric_for("component") is COMPONENTS
    assert rubric_for("image") is IMAGES


def test_something_the_taxonomy_does_not_have_has_no_rubric():
    with pytest.raises(BadRubric) as refused:
        rubric_for("shader")

    assert "shader" in str(refused.value)
