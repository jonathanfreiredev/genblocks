"""The harness: an agent that builds a block with its eyes on it.

This is the step that used to be one call to a model. What changed is not the
model and not the prompt — it is that the builder now **sees** the artifact: it
writes the project, asks the sandbox to build and render it, reads what came back,
and fixes what it sees. The loop lives here, bounded, because a builder that cannot
look is guessing and a builder that never stops is an invoice.

**What the budget counts.** ``settings.harness_max_iterations`` counts *looks* —
builds of the project — not model turns. A turn that reads a skill or writes a file
costs tokens; the expensive thing is the sandbox and the render it produces. When
the budget is spent, ``look`` says so and the agent has to finish with what it has.
A look at an unchanged project does not build anything: it answers with the last
render and says nothing has changed, which is the loop catching itself going round.

**The eyes are a tool.** ``look`` returns the checker's findings *and the render*,
as an image inside the tool's own result. That the model this deployment uses reads
it was verified before this was written: the alternative was injecting a message by
hand, and that would have been a worse shape for the same loop.

**What it does not do.** No row, no upload, no judge: it hands back a project, the
pictures it asked for, and how many looks it needed. Everything that reaches the
database is the runner's (``app.tasks.runner``).
"""

import base64
import posixpath
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

import structlog
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError

from app.harness import checks, images, skills
from app.harness.prompts import ASK, HARNESS_PROMPT
from app.harness.schemas import SandboxFile, SandboxResult
from app.moderation import service as moderation
from app.settings import settings

logger = structlog.get_logger("app.harness.agent")

# Where the block goes: the path the scaffold's own page imports. The harness owns
# this half of the contract; the sandbox owns writing it wherever it is told.
ENTRY = "src/Block.tsx"

# What the agent may write, and what it may write there. It is handed the scaffold,
# and editing the scaffold is not building a block: a tool that allowed it would be
# a tool that lets a run change the ruler it is being measured with. The mount and
# the global stylesheet are part of the ruler even though they live under ``src``.
WRITABLE = "src/"
WRITABLE_SUFFIXES = (".tsx", ".ts", ".css")
RESERVED = frozenset({"src/main.tsx", "src/index.css"})

# A block is a component, not a project to smuggle a payload into. These are far
# above any real block and low enough that a runaway write cannot fill the sandbox.
MAX_FILES = 40
MAX_FILE_CHARS = 120_000
MAX_TOTAL_CHARS = 400_000

# How many model turns one look is allowed to take. The recursion limit is a safety
# net under the real budget (looks), not a second one: it is here so a model that
# decides to read the whole shelf, one turn each, cannot run for ever.
TURNS_PER_LOOK = 4
TURNS_HEADROOM = 8

# A render is an image inside the conversation, so it is worth bounding what the
# model is told about it.
ATTACHED = "The render is attached."
DARK_ATTACHED = "The same block on the dark page the registry switches to:"
NOTHING_RENDERED = "There is no render: the checker stopped before the page existed."
UNCHANGED = "Nothing has changed since this render."


class HarnessUnavailable(Exception):
    """There is no model to build with. The deployment has no key."""


class NothingWritten(Exception):
    """The run finished without a project: nothing to check and nothing to judge."""


@dataclass(frozen=True)
class Placed:
    """A picture, the slot it was asked for, and the type it was filed under.

    A run either makes a picture or finds one the library already had; both end up
    as an address and its proportions, and only the first has bytes behind it. The
    library id is what lets the runner link the block to the picture that already
    exists instead of filing a second copy of it.
    """

    slot: str
    category: str
    url: str
    width: int
    height: int
    image: images.Generated | None = None
    library_id: uuid.UUID | None = None


@dataclass(frozen=True)
class Built:
    """What one harness run produced, ready for the sandbox and the judge."""

    files: dict[str, str]
    images: list[Placed]
    iterations: int
    # The version of the shelf it worked against, so a score can be read back
    # against the standard of its day.
    skills: str
    # One entry per look: the sandbox's own report, so a trace can show what the
    # agent saw and what it changed between rounds. The registry has no column for
    # it and does not want one; the ledger keeps scores, the trace keeps the why.
    rounds: list[dict] = field(default_factory=list)


def harness_model() -> BaseChatModel:
    """The model that builds, or a refusal saying what is missing.

    No temperature and no other knob: this deployment's model refuses everything
    but its own default, and asking for one would fail a run over a setting nobody
    could honour.
    """
    if not settings.openai_api_key:
        raise HarnessUnavailable(
            "The harness has no model configured: set OPENAI_API_KEY on the API."
        )

    return ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)


@dataclass(frozen=True)
class Reused:
    """A picture the library already had, as the tool reads it back."""

    id: uuid.UUID
    url: str
    width: int
    height: int
    prompt: str


@dataclass
class _Draft:
    """One run's project, and what the agent has already been shown.

    The tools mutate this and the loop reads it at the end. It is a plain object
    rather than graph state because everything the loop decides about — did it
    look, did anything change, how many pictures — is a fact about the artifact,
    not about the conversation.

    ``library`` is the caller's way into the picture library: given a description
    and a type, it answers with what the registry already has. It is handed in
    rather than reached for, because the harness holds no session (PLAN.md,
    decision 33).
    """

    image_categories: list[str]
    files: dict[str, str] = field(default_factory=dict)
    pictures: list[Placed] = field(default_factory=list)
    looks: int = 0
    shown: SandboxResult | None = None
    digest: str | None = None
    rounds: list[dict] = field(default_factory=list)
    library: Callable[[str, str], Awaitable[Reused | None]] | None = None

    @property
    def project(self) -> list[SandboxFile]:
        """The project as the sandbox reads it: every file, in a stable order."""
        return [
            SandboxFile(path=path, content=content) for path, content in sorted(self.files.items())
        ]

    def digest_of(self, files: dict[str, str]) -> str:
        """A short hash of the project's contents, to tell a change from a look."""
        material = "\n".join(f"{path}\n{content}" for path, content in sorted(files.items()))

        return sha256(material.encode()).hexdigest()[:12]


async def build(
    *,
    brief: str,
    category: str,
    image_categories: list[str] | None = None,
    library: Callable[[str, str], Awaitable[Reused | None]] | None = None,
    model: BaseChatModel | None = None,
) -> Built:
    """Build one block for a brief, looking at it until it is worth keeping.

    ``model`` is how a test drives the loop without paying for it; production
    passes nothing and gets the configured one. ``image_categories`` is the image
    taxonomy the pictures may be filed under, read by the caller from the database
    — the harness is handed the list rather than reaching for it. ``library``
    answers with a picture the registry already has, so a run asks for what is
    missing instead of generating everything again.
    """
    draft = _Draft(image_categories=list(image_categories or []), library=library)
    agent = create_agent(
        model or harness_model(),
        tools=_tools(draft),
        system_prompt=HARNESS_PROMPT,
    )
    limit = TURNS_PER_LOOK * settings.harness_max_iterations + TURNS_HEADROOM

    try:
        await agent.ainvoke(
            {"messages": [HumanMessage(_ask(brief=brief, category=category, draft=draft))]},
            config={"recursion_limit": limit},
        )
    except GraphRecursionError:
        # Out of turns, not out of budget: the project does not live in the
        # conversation, so whatever it wrote is still here to be checked.
        logger.warning("harness ran out of turns", files=len(draft.files))

    if not draft.files:
        raise NothingWritten("The harness finished without writing anything into the project.")

    logger.info(
        "harness built",
        files=len(draft.files),
        images=len(draft.pictures),
        iterations=draft.looks,
    )

    return Built(
        files=dict(draft.files),
        images=list(draft.pictures),
        iterations=draft.looks,
        skills=skills.version(),
        rounds=list(draft.rounds),
    )


def _tools(draft: _Draft) -> list[Any]:
    """The tools one run works with. They are closures over its draft."""

    @tool
    def write_file(path: str, content: str) -> str:
        """Write one file of the block into the project.

        Args:
            path: Where it goes, under `src/` — `src/Block.tsx` is the entry point
                the page imports and has to exist.
            content: The whole file. Writing it again replaces what was there.
        """
        if complaint := _unwritable(path):
            return complaint
        if complaint := _too_large(draft.files, path=path, content=content):
            return complaint

        draft.files[path] = content

        return f"written: {path} ({len(content)} characters)"

    @tool
    def read_file(path: str) -> str:
        """Read one file of the block back.

        Args:
            path: The file to read, as you wrote it.
        """
        if path not in draft.files:
            return f"There is no {path} in the project. There is: {_paths(draft)}"

        return draft.files[path]

    @tool
    def list_files() -> str:
        """List the files of the project right now."""
        return _paths(draft)

    @tool
    def read_skill(name: str) -> str:
        """Read one of the skills: the standard the block is held to.

        Args:
            name: The skill's name, from the shelf in your instructions.
        """
        try:
            return skills.read(name)
        except skills.NotASkill as unknown:
            return str(unknown)

    @tool
    async def look() -> list[dict[str, Any]]:
        """Build the project and look at the render.

        The checker runs the types, the linter and the build, then renders the page
        at three widths and reports what it found. The render comes back with the
        report: that is what you fix from, and looking at the block you just wrote
        is the whole job.
        """
        if draft.looks >= settings.harness_max_iterations:
            return [
                _text(
                    f"You have used your {settings.harness_max_iterations} looks. Finish "
                    "now: stop calling tools and answer with what you built and what is "
                    "still weak."
                )
            ]

        if not draft.files:
            return [_text("Nothing is written yet: write the block first.")]

        draft.looks += 1
        digest = draft.digest_of(draft.files)
        if digest == draft.digest and draft.shown is not None:
            return _seen(draft.shown, note=UNCHANGED)

        draft.shown = await checks.check(draft.project)
        draft.digest = digest
        draft.rounds.append(
            {
                "iteration": draft.looks,
                "files": len(draft.files),
                "pictures": len(draft.pictures),
                "blocked": draft.shown.blocked,
                "passed": sum(1 for check in draft.shown.checks if check.ok),
                "total": len(draft.shown.checks),
                "report": draft.shown.report(),
            }
        )

        return _seen(draft.shown)

    @tool
    async def generate_image(
        slot: str,
        prompt: str,
        category: str,
        width: int,
        height: int,
    ) -> str:
        """Ask the library for a picture, and get back the address to use.

        The library is checked first: a picture the registry already holds for
        this description is handed back instead of being generated again, and the
        answer says which of the two happened. Do this once the layout is settled
        — the composition decides the prompt — and once per picture, not once per
        attempt. Then look at the block again with the picture in place.

        Args:
            slot: A short name for where it goes ("hero", "avatar-1"), unique in
                the block.
            prompt: What the picture is, in the words a photographer would need.
            category: Which type of image it is, from the library's types.
            width: In pixels, a multiple of 32.
            height: In pixels, a multiple of 32.
        """
        if draft.shown is None:
            return (
                "Look at the block first: the composition decides the prompt, and a "
                "picture asked for before it is a picture asked for twice."
            )
        if draft.shown.blocked:
            return (
                "The block is not building yet: fix what the checks report, look again, "
                "and ask for the picture once the project gets through. A picture in a "
                "project that cannot publish is paid for nothing."
            )
        if len(draft.pictures) >= settings.images_per_block:
            return (
                f"The block already has {len(draft.pictures)} pictures, which is the "
                "limit. Work with what you have."
            )
        if any(one.slot == slot for one in draft.pictures):
            return f"There is already a picture in slot {slot!r}: it has its own address."
        asked_for = [one.image.prompt.strip().lower() for one in draft.pictures]
        if prompt.strip().lower() in asked_for:
            # The library answers a prompt with the picture it describes, so the
            # same prompt twice is the same photograph twice — which is how a band
            # of three ends up looking like one picture cropped three ways, and
            # what the judge caught the first time this ran for real.
            return (
                "You have already asked for that picture, and the library answers a "
                "prompt with nearly the same image: say what is different about this "
                "one — another scene, another light, another subject."
            )
        if not draft.image_categories:
            return (
                "The image library has no types to file a picture under, so nothing "
                "can be generated: build the block without pictures."
            )
        if category not in draft.image_categories:
            return (
                f"There is no {category!r} type of image. The library has: "
                f"{', '.join(draft.image_categories)}."
            )

        why = await moderation.image_prompt_refusal(prompt)
        if why is not None:
            return (
                f"That picture cannot be made: {why} Describe a different scene, or "
                "build the block without it."
            )

        kept = await draft.library(prompt, category) if draft.library else None
        if kept is not None:
            # The registry already holds this picture, and a library is worth
            # what it can be reused for: asking the photographer again for a
            # photograph we have pays twice for the same thing.
            if any(one.library_id == kept.id for one in draft.pictures):
                return (
                    "That is a picture already in this block. Say what is different "
                    "about this one — another scene, another light, another subject."
                )

            draft.pictures.append(
                Placed(
                    slot=slot,
                    category=category,
                    url=kept.url,
                    width=kept.width,
                    height=kept.height,
                    library_id=kept.id,
                )
            )

            return (
                f"already in the library: use {kept.url} — it is {kept.width}x"
                f"{kept.height}, so give it a box with those proportions."
            )

        try:
            made = await images.generate(prompt=prompt, width=width, height=height)
        except images.ImagesRefused as refused:
            return (
                f"That picture cannot be made: {refused} Describe a different scene, "
                "or build the block without it."
            )

        draft.pictures.append(
            Placed(
                slot=slot,
                category=category,
                url=made.url,
                width=made.width,
                height=made.height,
                image=made,
            )
        )

        return (
            f"generated and filed: use {made.url} — it is {made.width}x{made.height}, "
            "so give it a box with those proportions."
        )

    return [write_file, read_file, list_files, read_skill, look, generate_image]


def _ask(*, brief: str, category: str, draft: _Draft) -> str:
    """The brief, and the two things about this project it cannot guess.

    What the registry called it, and — when there is a library to file pictures
    under — the types it may ask for, so the agent does not have to guess a name
    and be told it was wrong.
    """
    ask = ASK.format(category=category, brief=brief)
    if draft.image_categories:
        ask += f"\nThe library files pictures under: {', '.join(draft.image_categories)}.\n"

    return ask


def _unwritable(path: str) -> str | None:
    """Why a file cannot go into the project, or ``None`` when it can."""
    if path.startswith("/") or ".." in path.split("/"):
        return f"{path!r} is not a path inside the project."
    if path != posixpath.normpath(path):
        return f"{path!r} is not a normalized path inside the project."
    if not path.startswith(WRITABLE):
        return f"Only files under {WRITABLE} belong to the block; {path!r} is the scaffold's."
    if path in RESERVED:
        return (
            f"{path!r} mounts the block or carries the registry's ground. It belongs "
            "to the scaffold and cannot be replaced by a block."
        )
    if not path.endswith(WRITABLE_SUFFIXES):
        return f"Only {', '.join(WRITABLE_SUFFIXES)} files can be written ({path!r})."

    return None


def _too_large(files: dict[str, str], *, path: str, content: str) -> str | None:
    """Why a project would be too large, or ``None`` when it still fits."""
    if path not in files and len(files) >= MAX_FILES:
        return f"The project already has {MAX_FILES} files, which is the limit."
    if len(content) > MAX_FILE_CHARS:
        return f"{path!r} is larger than the {MAX_FILE_CHARS:,}-character limit."

    total = sum(len(one) for name, one in files.items() if name != path) + len(content)
    if total > MAX_TOTAL_CHARS:
        return f"The project would exceed the {MAX_TOTAL_CHARS:,}-character limit."

    return None


def _paths(draft: _Draft) -> str:
    return ", ".join(sorted(draft.files)) or "nothing yet"


def _seen(found: SandboxResult, *, note: str | None = None) -> list[dict[str, Any]]:
    """The sandbox's answer as the message the agent reads it in.

    Both grounds are shown. The judge will be shown both, so a builder that only
    saw one of them would be fixing a block nobody is scoring.
    """
    said = note + "\n\n" if note else ""
    said += found.report()

    if found.screenshot is None:
        return [_text(f"{said}\n\n{NOTHING_RENDERED}")]

    parts: list[dict[str, Any]] = [
        {"type": "text", "text": f"{said}\n\n{ATTACHED}"},
        _image(found.screenshot, found.screenshot_media_type),
    ]
    if found.screenshot_dark is not None:
        parts += [
            {"type": "text", "text": DARK_ATTACHED},
            _image(found.screenshot_dark, found.screenshot_media_type),
        ]

    return parts


def _image(data: bytes, media_type: str = "image/png") -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{base64.b64encode(data).decode()}"},
    }


def _text(said: str) -> dict[str, str]:
    return {"type": "text", "text": said}
