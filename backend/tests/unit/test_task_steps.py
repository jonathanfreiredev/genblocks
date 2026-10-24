"""The checklist's contract with the quota: the second step is where money starts."""

from app.tasks.steps import GENERATING_STEPS, IMAGE_STEP_NAMES, STEP_NAMES


def test_the_expensive_step_is_the_second_one_in_both_checklists():
    assert STEP_NAMES[1] == "Generating the block"
    assert IMAGE_STEP_NAMES[1] == "Generating the image"
    assert (STEP_NAMES[1], IMAGE_STEP_NAMES[1]) == GENERATING_STEPS
