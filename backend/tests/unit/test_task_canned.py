"""The stand-in spec, which is the only thing a run varies by.

The copy that carries the brief into a title and a card line is what is left here
that has behaviour: the block comes from the generator and the judgement from the
judge (Fase 7 and Fase 8), so neither is tested as a stand-in any more.
"""

from app.tasks import canned


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
