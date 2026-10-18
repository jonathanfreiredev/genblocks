"""What the judge is asked for, and what its answer means.

The model's answer and the read verdict are two different shapes on purpose. The
model returns one entry per dimension — a number and the reason for it — and
:func:`app.judge.scoring.read` turns that into the flat ``scores`` the registry
stores, plus the dimensions that missed their threshold, which is what decides
between two attempts.

An answer that invents a dimension or forgets one is refused rather than
recorded: the panel has a row per dimension, and a missing one would be an empty
row on a published block, which reads as a zero.
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """One dimension, as the judge scored it: the number and what earned it."""

    score: int = Field(ge=0, le=100, description="Whole number, 0 to 100.")
    note: str = Field(description="One sentence saying what earned this number.")


class JudgeAnswer(BaseModel):
    """What the judge answered, as it comes back from the model."""

    dimensions: dict[str, DimensionScore] = Field(
        description="One entry per dimension named in the rubric, keyed by its name."
    )
    summary: str = Field(
        description="A short paragraph about the artifact, for a reader who cannot see it."
    )


@dataclass(frozen=True)
class Judged:
    """A judge's answer, read against its rubric and the thresholds.

    ``scores`` is the flat shape the registry and the panel use; ``notes`` and
    ``summary`` are the judge's own words, which the retry reads back to the
    writer and nothing else keeps (the trace that would is Fase 12).
    """

    scores: dict[str, int]
    notes: dict[str, str]
    summary: str
    version: str
    # The dimensions that missed their threshold, in rubric order, and the only
    # thing ``passed`` is about: a block is not published on a high mean while a
    # dimension it failed sits in the panel (PLAN.md, section 7).
    below: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.below
