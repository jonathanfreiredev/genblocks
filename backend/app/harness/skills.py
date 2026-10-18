"""The shelf: what the harness builds by.

A skill is a document in this package — the standard a block is held to, written
for this medium (one project, generic Tailwind, the packages on the shelf). The
agent gets the **index** in its system prompt and pulls a body with its
``read_skill`` tool, which is how six documents fit in a prompt that is paid for
on every turn: the index is stable and cached, and a body is read when it is
needed.

The **version** is a hash of the whole shelf, name by name, and a run stamps it in
its step. That is what makes a block readable years later: its scores were earned
against the standard of that day, and this is which day it was.

The skills are the harness's principles, not the judge's criteria. The judge has
its own document (``app/judge/rubrics``) and they have to agree — same tradition,
different reader — or the loop starts fixing what nobody scores (PLAN.md,
decision 37).
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# How much of the hash names the version: short enough to read beside a model name
# in a step's detail, long enough that two edits of the shelf do not collide.
VERSION_LENGTH = 8


class BadSkill(Exception):
    """A skill file is missing or is not a document.

    Shipped text, so this is a mistake in the repository rather than a run that
    went wrong: it fails at import, where whoever edited it is looking.
    """


class NotASkill(Exception):
    """The agent asked for something the shelf does not have."""


@dataclass(frozen=True)
class Skill:
    """One document: what it is called, what the index says about it, and it."""

    name: str
    summary: str
    text: str


# The shelf, in the order the index lists it: what a block is comes before how to
# build one, the craft comes next, and the list of what not to do closes it — the
# order somebody would read them in.
SHELF = (
    (
        "blocks",
        "what a block is here: one project, generic Tailwind, and the rules that make it copyable",
    ),
    ("dependencies", "what you may import, and when each package is the right answer"),
    ("accessibility", "contrast, structure, controls, names, focus, and reduced motion"),
    ("composition", "hierarchy, spacing rhythm, alignment, restraint and responsive behaviour"),
    ("motion", "when movement earns its place, and how to make it optional"),
    ("cliches", "the shapes this registry does not publish, and what to do instead"),
)


def _load(name: str, summary: str) -> Skill:
    path = SKILLS_DIR / f"{name}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as missing:
        raise BadSkill(f"There is no {path.name} in {SKILLS_DIR}.") from missing

    if not text.startswith("# "):
        raise BadSkill(f"{path.name} is not a document: it has no title.")

    return Skill(name=name, summary=summary, text=text)


ALL = {skill.name: skill for skill in (_load(name, summary) for name, summary in SHELF)}


def index() -> str:
    """The shelf as the system prompt lists it: one line per skill."""
    return "\n".join(f"- {skill.name}: {skill.summary}" for skill in ALL.values())


def read(name: str) -> str:
    """One skill's body, or a refusal that names what there is."""
    try:
        return ALL[name].text
    except KeyError as unknown:
        raise NotASkill(
            f"There is no {name!r} on the shelf. There is: {', '.join(ALL)}."
        ) from unknown


def version() -> str:
    """The shelf's version: a hash of every name, summary and body."""
    material = "\n".join(f"{skill.name}\n{skill.summary}\n{skill.text}" for skill in ALL.values())

    return sha256(material.encode()).hexdigest()[:VERSION_LENGTH]
