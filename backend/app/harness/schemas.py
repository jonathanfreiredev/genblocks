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
IMPORTS = "imports"
AST = "ast"
BUNDLE = "bundle"

# The two that never reach the sandbox: they read the project's text.
ASSETS = "assets"
SAFETY = "safety"

# A layout check per viewport, named ``layout:desktop`` and so on.
LAYOUT_PREFIX = "layout:"

# What a run cannot carry on from. Code that does not typecheck, does not bundle,
# renders nothing, imports a package that is not on the shelf, loads from a host
# that is not ours, or reaches the network is not an attempt: publishing it would
# put a broken block in the registry and call it a result — and in the last two
# cases, a block that stops working the moment somebody copies it. Lint, layout and
# accessibility findings are evidence for the judge, not gates: a wide hero at
# 390px is a judgement call, and that is what the judge is for.
FATAL_CHECKS = (
    TYPECHECK,
    BUILD,
    RENDER,
    IMPORTS,
    AST,
    BUNDLE,
    ASSETS,
    SAFETY,
)


class SandboxFile(BaseModel):
    """One file to write into the sandbox's project, path relative to its root."""

    path: str
    content: str


class SandboxRequest(BaseModel):
    """A project for the sandbox to check."""

    files: list[SandboxFile]
    # URL prefixes the page may load pictures from. The backend sends its own
    # Cloudinary delivery prefix, so the sandbox does not have to infer the
    # account from the project or from a deployment environment.
    asset_prefixes: list[str] = Field(default_factory=list)


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
    # Which ground it was found on: "light" or "dark". A contrast failure in one
    # scheme and not the other is a different fact from the same failure in both,
    # and the judge reads them apart.
    scheme: str = "light"


class SandboxResult(BaseModel):
    """Everything one run of the sandbox produced.

    ``screenshot`` is the desktop render on a light page, as JPEG bytes, or ``None``
    when the run never got as far as a page. ``screenshot_dark`` is the same page
    with the theme the registry switches on: a block is expected to hold on both
    grounds, and the only way to know is to look. Only the light one is stored —
    it is the thumbnail — while both go to the judge.

    ``dependencies`` is what the project imports from packages, with the version it
    was built against — read by the sandbox from the project itself rather than
    declared by anybody, so a block's install line is a fact and not a promise.
    """

    checks: list[SandboxCheck] = Field(default_factory=list)
    violations: list[SandboxViolation] = Field(default_factory=list)
    dependencies: dict[str, str] = Field(default_factory=dict)
    screenshot: bytes | None = None
    screenshot_dark: bytes | None = None
    # The bytes above are JPEG from the sandbox, not the PNG a naive reader might
    # assume; the judge and the model both need the right data-URL media type.
    screenshot_media_type: str = "image/png"

    @property
    def blocked(self) -> bool:
        """Whether a check failed that the pipeline will not publish past."""

        return any(check.name in FATAL_CHECKS and not check.ok for check in self.checks)

    @property
    def failures(self) -> list[SandboxCheck]:
        """The checks that failed, fatal or not, for a reader in a hurry."""

        return [check for check in self.checks if not check.ok]

    def report(self) -> str:
        """The findings as text, one line each, in the order they were made.

        Written here rather than at each reader because both readers of it — the
        builder, who fixes from it, and the judge, who scores from it — have to be
        told the same thing: every check is named, passing or not, because a
        reader that only hears about failures cannot tell a block that passed seven
        checks from one that was never asked.
        """
        lines = [
            f"- {check.name}: {'ok' if check.ok else 'failed'}"
            + (f" — {check.detail}" if check.detail else "")
            for check in self.checks
        ]
        lines.extend(
            f"- axe{_on(violation.scheme)} {violation.id} "
            f"({violation.impact or 'unknown impact'}, {violation.nodes} nodes): "
            f"{violation.help}"
            for violation in self.violations
        )

        return "\n".join(lines) if lines else "- the sandbox reported nothing"

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


def _on(scheme: str) -> str:
    """Which ground a finding is on, said only when it is not the usual one."""
    return "" if scheme == "light" else f" on the {scheme} page"
