"""The rubrics, as the judge reads them.

A rubric is a **skill**: a document in this package that says what each dimension
means, next to the list of dimensions it asks to be scored. The document is the
judge's standard, and the version it produces is what a run stamps on the attempt
— so a score can always be read back against the text that produced it, years
later, without anybody having to keep a changelog.

The version is a hash of the document and of the dimension list, not a number
somebody remembers to bump. Editing the rubric in any way that could change a
score changes the version, and a version that changed for no reason cannot
happen.

The **dimension keys** are a contract in three places and none of them owns it:
the judge answers with them (``schemas.JudgeAnswer``), the attempt stores them
flat in ``scores``, and the frontend labels them
(``frontend/lib/vault/rubric.ts``). The tests on both sides assert the same list,
because a dimension one side invents is a row that reads as a zero.

What is *not* here is the thresholds: they live in settings, because they are
calibrated against real generations, and a calibration is not a change to what
the rubric says.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

RUBRICS_DIR = Path(__file__).resolve().parent / "rubrics"

# How much of the hash names the version. Short enough to read next to a model
# name in the panel, long enough that two edits of one rubric do not collide by
# accident.
VERSION_LENGTH = 8


class BadRubric(Exception):
    """A rubric file is missing, or does not describe what it asks to be scored.

    Shipped text, so this is a mistake made in the repository rather than a run
    that went wrong: it fails at import, where whoever edited the file is looking.
    """


@dataclass(frozen=True)
class Rubric:
    """One rubric: what it is called, what it asks for, and what it says."""

    name: str
    kind: str
    dimensions: tuple[str, ...]
    text: str

    @property
    def version(self) -> str:
        """The name and the hash of everything the judge was given."""
        material = "\n".join((self.name, *self.dimensions, self.text))

        return f"{self.name}-{sha256(material.encode()).hexdigest()[:VERSION_LENGTH]}"


def _load(name: str, *, kind: str, dimensions: tuple[str, ...]) -> Rubric:
    """Read one rubric, and refuse one that does not describe its dimensions.

    The check is what keeps the list and the prose from drifting apart: adding a
    dimension to the tuple without a section that says how to score it is the one
    edit that would otherwise go unnoticed until a judge answered about a
    dimension it was never told about.
    """
    path = RUBRICS_DIR / f"{name}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as missing:
        raise BadRubric(f"There is no {path.name} in {RUBRICS_DIR}.") from missing

    for dimension in dimensions:
        if f"## {dimension}" not in text:
            raise BadRubric(f"The {name} rubric asks for {dimension!r} and never describes it.")

    return Rubric(name=name, kind=kind, dimensions=dimensions, text=text)


COMPONENTS = _load(
    "components",
    kind="component",
    # Novelty is not a judge dimension. Retrieval measures distance to the nearest
    # blocks; a judge asked to score that distance would be guessing at a number
    # another part of the system already computes. Seeded attempts may still carry
    # a legacy novelty score, but no production run does and no threshold gates it.
    dimensions=("render", "accessibility", "visual", "copy", "compliance"),
)

IMAGES = _load(
    "images",
    kind="image",
    dimensions=("visual", "prompt_fit", "compliance"),
)

BY_KIND = {rubric.kind: rubric for rubric in (COMPONENTS, IMAGES)}


def rubric_for(kind: str) -> Rubric:
    """The rubric that judges one kind of artifact, by the taxonomy's word for it."""
    try:
        return BY_KIND[kind]
    except KeyError as unknown:
        raise BadRubric(
            f"No rubric judges {kind!r}: there is one for {sorted(BY_KIND)}."
        ) from unknown
