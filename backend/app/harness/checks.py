"""What a project may not do, read before it is built.

The sandbox answers what a browser *sees* — it compiles, renders and photographs.
These two questions are about the text, and answering them there instead has two
consequences worth the module:

- They cost nothing. A block that points at somebody else's host is refused before
  a container is asked to build it, which is a render not paid for.
- They can be answered *inside* the harness loop. The builder looks at the project
  it wrote and is told what is wrong with it while it can still fix it; a check
  that only ran at the end would fail a run whose author never got to hear why.

The bar is not "is this good" — that is the judge's. It is "may this travel": a
block is copied into somebody else's page, so it either brings what it shows or it
stops showing it. Both checks are fatal (``FATAL_CHECKS``): a project that loads
from elsewhere or reaches the network is not an attempt.
"""

import re

from app.harness import sandbox
from app.harness.schemas import ASSETS, SAFETY, SandboxCheck, SandboxFile, SandboxResult
from app.settings import settings

# How many findings one check reports before it says "and more". A reader fixes
# them one at a time; the rest of the list arrives on the next look.
MAX_FINDINGS = 5

# What a browser goes and gets, in the four ways a block can ask for it: an
# attribute that carries a file (a literal string, or a literal inside braces when
# the block is written as JSX), a stylesheet tag, a CSS ``url()`` and an
# ``@import``.
LOADING = re.compile(
    r"""\b(?:src|srcset|poster)\s*=\s*
        (?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})""",
    re.VERBOSE | re.IGNORECASE,
)
LINK = re.compile(
    r"""<link\b[^>]*?\bhref\s*=\s*(?:"([^"]*)"|'([^']*)')""",
    re.IGNORECASE,
)
CSS_URL = re.compile(
    r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"]*))\s*\)""",
    re.IGNORECASE,
)
CSS_IMPORT = re.compile(
    r"""@import\s+(?:url\(\s*)?["']([^"']+)["']""",
    re.IGNORECASE,
)

# What a block has no business doing inside somebody else's page. The network ones
# make the block depend on a service it does not own; the rest are ways of leaving
# React's escaping behind, which is the one thing that keeps a block from being a
# script.
FORBIDDEN: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("calls fetch(", re.compile(r"\bfetch\s*\(")),
    ("uses XMLHttpRequest", re.compile(r"\bXMLHttpRequest\b")),
    ("opens a WebSocket", re.compile(r"\bWebSocket\b")),
    ("opens an EventSource", re.compile(r"\bEventSource\b")),
    ("calls sendBeacon", re.compile(r"\bsendBeacon\b")),
    ("evaluates a string with eval(", re.compile(r"\beval\s*\(")),
    ("builds a function from a string", re.compile(r"\bnew\s+Function\b")),
    ("writes markup with document.write", re.compile(r"\bdocument\s*\.\s*write(?:ln)?\b")),
    ("injects HTML with dangerouslySetInnerHTML", re.compile(r"\bdangerouslySetInnerHTML\b")),
    ("links a javascript: URL", re.compile(r"""["'`]\s*javascript\s*:""", re.IGNORECASE)),
)

# Where a value the browser will fetch is allowed to come from: the library's own
# delivery hosts, or nowhere — a relative path and a ``data:`` URL travel with the
# block.
SCHEMES_THAT_TRAVEL = ("mailto", "tel")

# What a scheme looks like. A path that happens to hold a colon — ``images/2026:10/x``
# — is a path, not a scheme, and reading it as one would refuse a block for its
# folder name.
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*$", re.IGNORECASE)


def inspect(files: list[SandboxFile]) -> list[SandboxCheck]:
    """The two questions, answered over the project's text.

    One check per question rather than one long list, because a reader wants to
    know *which* rule broke, and the two mean different things: one is about what
    the block carries, the other about what it does.
    """
    hosts = _hosts()
    assets: list[str] = []
    unsafe: list[str] = []

    for file in files:
        assets += _external_assets(file, hosts)
        unsafe += _forbidden_uses(file)

    return [
        SandboxCheck(name=ASSETS, ok=not assets, detail=_report(assets)),
        SandboxCheck(name=SAFETY, ok=not unsafe, detail=_report(unsafe)),
    ]


async def check(files: list[SandboxFile]) -> SandboxResult:
    """Check the text first, and the sandbox only when the text lets it through.

    Same answer as :func:`app.harness.sandbox.check`, with the static checks in
    front, so every reader — the builder fixing from it, the runner gating on it,
    the judge scoring from it — sees one list. A project that fails the text never
    reaches Modal: an empty result with the two findings is a refusal, not a run.
    """
    static = inspect(files)
    if any(not one.ok for one in static):
        return SandboxResult(checks=static)

    found = await sandbox.check(files)

    return found.model_copy(update={"checks": [*static, *found.checks]})


def _external_assets(file: SandboxFile, hosts: tuple[str, ...]) -> list[str]:
    """Every value the browser would fetch from somewhere that is not ours."""
    found: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()

    for pattern in (LOADING, LINK, CSS_URL, CSS_IMPORT):
        for match in pattern.finditer(file.content):
            # The patterns capture the same URL from different angles — an
            # ``@import url(...)`` is both — and one finding is enough.
            where = _line_of(file.content, match.start())
            if _is_commented(file.content, match.start()):
                continue

            value = next((group for group in match.groups() if group), "")
            for candidate in _values(value):
                if _travels(candidate, hosts) or (where, candidate) in seen:
                    continue

                seen.add((where, candidate))
                found.append(
                    (where, f"{file.path}:{where} loads {_short(candidate)}, which is not ours")
                )

    # In the order the block reads, not the order the patterns happen to find.
    return [said for _, said in sorted(found)]


def _forbidden_uses(file: SandboxFile) -> list[str]:
    """Every way the project leaves React or reaches the network."""
    found: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()

    for said, pattern in FORBIDDEN:
        for match in pattern.finditer(file.content):
            where = _line_of(file.content, match.start())
            if _is_commented(file.content, match.start()) or (where, said) in seen:
                continue

            seen.add((where, said))
            found.append((where, f"{file.path}:{where} {said}"))

    return [text for _, text in sorted(found)]


def _values(value: str) -> list[str]:
    """The URLs one attribute value names.

    ``srcset`` holds several candidates separated by commas and followed by a
    density or a width; the rest hold one. A ``data:`` URL is the exception to the
    comma rule — it carries one itself.
    """
    stripped = value.strip()
    if not stripped or stripped.startswith("data:"):
        return [stripped] if stripped else []

    return [part.strip().split(" ")[0] for part in stripped.split(",") if part.strip()]


def _travels(value: str, hosts: tuple[str, ...]) -> bool:
    """Whether the browser can fetch this value from us or from the block itself."""
    if not value:
        return True
    if value.startswith("#") or value.startswith("data:"):
        return True
    if value.startswith("//"):
        return _host_of(value[2:]) in hosts

    scheme, found, rest = value.partition(":")
    if not found or not SCHEME.match(scheme):
        # No scheme: a relative path, which travels with the project.
        return True
    if scheme.lower() in SCHEMES_THAT_TRAVEL:
        return True
    if scheme.lower() not in ("http", "https"):
        return False

    return _host_of(rest.lstrip("/")) in hosts


def _host_of(value: str) -> str:
    """The host part of ``host/path``, lowercased, without a port.

    Credentials are kept in the comparison on purpose: ``res.cloudinary.com@evil``
    is a request to ``evil``, and a check that read only the part before the ``@``
    would wave it through.
    """
    authority = value.split("/", 1)[0]
    if "@" in authority:
        return authority.lower()

    return authority.partition(":")[0].lower()


def _hosts() -> tuple[str, ...]:
    return tuple(
        one.strip().lower() for one in settings.allowed_asset_hosts.split(",") if one.strip()
    )


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _is_commented(text: str, index: int) -> bool:
    """Whether the match sits on a line that is only a comment.

    A line of prose that mentions ``fetch(`` is not a call to it. This is a cheap
    rule, not a parser: it catches the comment styles a block is written in, and
    the rest of the time the finding is true anyway.
    """
    start = text.rfind("\n", 0, index) + 1
    line = text[start:index].lstrip()

    return line.startswith(("//", "*", "/*", "*/", "{/*"))


def _short(value: str) -> str:
    return value if len(value) <= 160 else f"{value[:157]}…"


def _report(findings: list[str]) -> str | None:
    """The findings as one line, the first few and a count."""
    if not findings:
        return None

    said = "; ".join(findings[:MAX_FINDINGS])
    if len(findings) > MAX_FINDINGS:
        said += f"; and {len(findings) - MAX_FINDINGS} more"

    return said
