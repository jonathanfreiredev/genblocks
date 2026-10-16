"""The canned copy, which is the only thing a run varies by.

Everything else the stand-in produces is fixed, so these are the functions that
have to behave: a title that reads, a card line that fits, and a block whose
source survives whatever the caller typed into the brief.
"""

import json

from app.tasks import canned

# The six dimensions the component panel renders. The canned judge has to write
# all of them: a missing one would show as a blank row in the item's evidence.
COMPONENT_RUBRIC_KEYS = {
    "render",
    "accessibility",
    "visual",
    "copy",
    "novelty",
    "compliance",
}


def test_the_canned_scores_cover_the_component_rubric():
    assert set(canned.SCORES) == COMPONENT_RUBRIC_KEYS


def test_a_short_brief_is_its_own_title():
    assert canned.title_for("A pricing table") == "A pricing table"


def test_a_long_brief_titles_itself_with_its_first_clause():
    brief = "A pricing page for a developer tool, three tiers, with an annual toggle"

    assert canned.title_for(brief) == "A pricing page for a developer tool"


def test_a_long_brief_with_no_break_is_cut_between_words():
    brief = "Build me " + "an extremely elaborate marketing page for " * 3

    title = canned.title_for(brief)

    assert len(title) <= canned.TITLE_LIMIT
    assert brief.startswith(title)
    assert not title.endswith(" ")


def test_a_brief_of_one_long_word_is_still_a_title():
    assert canned.title_for("x" * 200) == "x" * canned.TITLE_LIMIT


def test_a_brief_loses_its_line_breaks_before_it_becomes_a_title():
    assert canned.title_for("A hero\n  on a rule grid") == "A hero on a rule grid"


def test_the_description_keeps_the_whole_brief_until_it_has_to_fit():
    assert canned.description_for("A pricing table") == "A pricing table"

    description = canned.description_for("A pricing table " * 40)

    assert description.endswith("…")
    assert len(description) <= canned.DESCRIPTION_LIMIT + 1


def test_the_code_carries_a_brief_that_would_break_it():
    """The brief is written into source code; the source has to survive it."""
    brief = 'A "quoted" brief with a \\ backslash, ${interpolation} and a\nnewline'

    code = canned.code_for(brief)

    assert code.count("const brief =") == 1
    assert f"const brief =\n    {json.dumps(brief)};" in code


def test_the_code_never_re_scans_what_it_inserted():
    """A brief that is itself the marker cannot inject a second one."""
    code = canned.code_for("__BRIEF__")

    assert code.count("const brief =") == 1
    assert '"__BRIEF__"' in code


def test_the_headline_is_the_flat_mean_of_the_scores():
    assert canned.headline_score({"a": 90, "b": 81}) == 86
