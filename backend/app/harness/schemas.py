"""What leaves for the sandbox, and what it is trusted to have found.

The sandbox is a separate program — ``app/harness/modal_app.py``, deployed to
Modal — that takes JSON and returns JSON. These types are the strict side of
that contract: the request is built here, and the answer is read back through
:class:`SandboxResult` before any of it reaches the database. A field the
sandbox renames is a task that fails loudly rather than an attempt that records
nothing.
"""

from pydantic import BaseModel, Field

# The checks the sandbox reports by name. Kept here rather than in the Modal app
# because this is the side that decides what they mean.
TYPECHECK = "typecheck"
LINT = "lint"
BUILD = "build"
RENDER = "render"
ACCESSIBILITY = "accessibility"

# A layout check per viewport, named ``layout:desktop`` and so on.
LAYOUT_PREFIX = "layout:"

# What a run cannot carry on from. Code that does not typecheck, does not bundle,
# or renders nothing is not an attempt: publishing it would put a broken block in
# the registry and call it a result. Lint, layout and accessibility findings are
# evidence for the judge, not gates — a wide hero at 390px is a judgement call,
# and the phase that judges has not run yet.
FATAL_CHECKS = (TYPECHECK, BUILD, RENDER)


class SandboxFile(BaseModel):
    """One file to write into the sandbox's project, path relative to its root."""

    path: str
    content: str


class SandboxRequest(BaseModel):
    """A project for the sandbox to check."""

    files: list[SandboxFile]


class SandboxCheck(BaseModel):
    """One thing the sandbox looked for, and what it found."""

    name: str
    ok: bool
    detail: str | None = None


class SandboxViolation(BaseModel):
    """One accessibility violation, in axe's own words."""

    id: str
    impact: str | None = None
    help: str
    nodes: int = 0


class SandboxResult(BaseModel):
    """Everything one run of the sandbox produced.

    ``screenshot`` is the desktop render as PNG bytes, or ``None`` when the run
    never got as far as a page. It is the only artifact that leaves this process
    as data: the reports are stored with the attempt, and the picture is uploaded
    before the attempt is written.
    """

    checks: list[SandboxCheck] = Field(default_factory=list)
    violations: list[SandboxViolation] = Field(default_factory=list)
    screenshot: bytes | None = None

    @property
    def blocked(self) -> bool:
        """Whether a check failed that the pipeline will not publish past."""

        return any(check.name in FATAL_CHECKS and not check.ok for check in self.checks)

    @property
    def failures(self) -> list[SandboxCheck]:
        """The checks that failed, fatal or not, for a reader in a hurry."""

        return [check for check in self.checks if not check.ok]

    def record(self) -> dict:
        """The result as it is stored on the attempt.

        What a reader and the judge need: every check with its verdict, the
        accessibility findings in axe's own words, the count, and ``blocked`` —
        the one field the pipeline acts on, so that nothing reading this later
        has to know which checks are fatal.
        """
        return {
            "blocked": self.blocked,
            "passed": sum(1 for check in self.checks if check.ok),
            "total": len(self.checks),
            "checks": [check.model_dump() for check in self.checks],
            "violations": [violation.model_dump() for violation in self.violations],
        }
