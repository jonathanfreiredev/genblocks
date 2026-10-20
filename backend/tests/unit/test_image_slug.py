"""A picture's address, from what the row knows about it."""

from app.images.slug import image_slug


def test_a_descriptive_asset_path_is_the_slug():
    assert (
        image_slug(prompt="A bench at dusk", path="genblocks/images/bench-at-dusk")
        == "bench-at-dusk"
    )


def test_a_generated_asset_keeps_a_readable_stem_and_a_short_tail():
    slug = image_slug(
        prompt="A small stone harbour at dawn, still water",
        path="genblocks/images/6b6c75912dc5bf77",
    )

    assert slug == "a-small-stone-harbour-at-dawn-still-water-6b6c75"


def test_a_prompt_that_says_nothing_still_names_the_picture():
    assert image_slug(prompt="***", path="genblocks/images/bench-at-dusk") == "bench-at-dusk"
