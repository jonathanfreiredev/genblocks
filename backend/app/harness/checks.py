"""What a project may not do, read before it is built.

The sandbox answers what a browser *sees* — it compiles, renders and photographs.
These questions are about the text, and answering them there instead has two
consequences worth the module:

- They cost nothing. A block that points at somebody else's host is refused before
  a container is asked to build it, which is a render not paid for.
- They can be answered *inside* the harness loop. The builder looks at the project
  it wrote and is told what is wrong with it while it can still fix it; a check
  that only ran at the end would fail a run whose author never got to hear why.

Two of these are gates and the rest are advice. ``ASSETS`` and ``SAFETY`` decide
whether a block may travel at all; the design checks below compare the project
with the plan it was asked to follow and report what drifted, without refusing a
run. A block can be good and disagree with its plan, and that is a judgement — the
judge's, not this module's.
"""

import re

from app.harness import sandbox
from app.harness.schemas import (
    ASSETS,
    PREVIEW,
    PREVIEW_MAX_BYTES,
    SAFETY,
    SandboxCheck,
    SandboxFile,
    SandboxResult,
)
from app.settings import settings

# How many findings one check reports before it says "and more". A reader fixes
# them one at a time; the rest of the list arrives on the next look.
MAX_FINDINGS = 5

# The advisory checks: what the project says about following its own plan.
DESIGN_TYPE = "design:type"
DESIGN_RADIUS = "design:radius"
DESIGN_ACCENT = "design:accent"

# A font is imported from the shelf one weight at a time. The package names the
# family, and it is the same string the plan stored.
FONT_IMPORT = re.compile(r"""@fontsource/([a-z0-9-]+)/latin-""")

# Every rounded surface a Tailwind file can name, including an arbitrary value.
ROUNDED = re.compile(r"\brounded(?:-(?:[a-z0-9]+|\[[^\]]+\]))?\b")

# A colour utility, as the family it spends: `text-emerald-700`, `bg-stone-50`.
COLOUR = re.compile(
    r"\b(?:text|bg|border|ring|from|via|to|decoration|outline|fill|stroke)-([a-z]+)-\d{2,3}\b"
)

# Families that are not a palette decision.
COLOURLESS = frozenset({"white", "black", "transparent", "current", "inherit"})

# One radius used often enough that it is the shape of everything.
RADIUS_REPEATS = 5

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
ANCHOR = re.compile(
    r"""<a\b[^>]*?\bhref\s*=\s*
        (?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})""",
    re.VERBOSE | re.IGNORECASE,
)
SVG_REF = re.compile(
    r"""<(?:use|image)\b[^>]*?\b(?:xlink:)?href\s*=\s*
        (?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})""",
    re.VERBOSE | re.IGNORECASE,
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
    (
        "links a data: URL",
        re.compile(
            r"""<(?:a|use)\b[^>]*?\bhref\s*=\s*
                (?:"data:|'data:|\{\s*["'`]\s*data:)""",
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    # Tags that bring their own execution, framing or navigation. A block is a
    # component; it does not need any of them.
    ("embeds a script tag", re.compile(r"<\s*script\b", re.IGNORECASE)),
    ("embeds an iframe", re.compile(r"<\s*iframe\b", re.IGNORECASE)),
    ("embeds an object", re.compile(r"<\s*object\b", re.IGNORECASE)),
    ("embeds an embed", re.compile(r"<\s*embed\b", re.IGNORECASE)),
    ("embeds an applet", re.compile(r"<\s*applet\b", re.IGNORECASE)),
    ("embeds a frame", re.compile(r"<\s*frameset\b|<\s*frame\b", re.IGNORECASE)),
    ("sets a base URL", re.compile(r"<\s*base\b", re.IGNORECASE)),
    ("pings a link", re.compile(r"<a\b[^>]*?\bping\s*=", re.IGNORECASE)),
    (
        "refreshes the page",
        re.compile(
            r"<meta\b[^>]*?(?:http-equiv|httpEquiv)\s*=\s*[\"']refresh[\"']",
            re.IGNORECASE,
        ),
    ),
    (
        "posts a form to an address",
        re.compile(r"<form\b[^>]*?\baction\s*=", re.IGNORECASE),
    ),
    ("sets formAction", re.compile(r"\bformAction\s*=")),
    # A URL in CSS can hide behind image-set() without url().
    ("uses image-set", re.compile(r"\b(?:-webkit-)?image-set\s*\(", re.IGNORECASE)),
    # Browser globals that turn a presentational block into a script. The CSP and
    # route in the sandbox are the fence; these checks catch the obvious attempts
    # before a container is spent on them.
    ("reaches window", re.compile(r"\bwindow\s*[.\[]")),
    ("reaches globalThis", re.compile(r"\bglobalThis\s*[.\[]")),
    ("reaches self", re.compile(r"\bself\s*[.\[]")),
    ("reaches document", re.compile(r"\bdocument\s*[.\[]")),
    ("reaches navigator", re.compile(r"\bnavigator\s*[.\[]")),
    ("reaches a parent frame", re.compile(r"\b(?:top|parent|frames|opener)\s*[.\[]")),
    ("uses a service worker", re.compile(r"\bserviceWorker\b")),
    ("opens a peer connection", re.compile(r"\b(?:RTCPeerConnection|WebTransport)\b")),
    ("imports a worker script", re.compile(r"\bimportScripts\s*\(")),
    ("runs a timer as a string", re.compile(r"\b(?:setTimeout|setInterval)\s*\(\s*[\"'`]")),
    ("uses localStorage", re.compile(r"\blocalStorage\b")),
    ("uses sessionStorage", re.compile(r"\bsessionStorage\b")),
    ("uses indexedDB", re.compile(r"\bindexedDB\b")),
    ("navigates with location", re.compile(r"\blocation\s*(?:\.|\[|=)")),
    ("creates an Image", re.compile(r"\bnew\s+(?:Image|Audio)\b")),
    ("uses dynamic import", re.compile(r"\bimport\s*\(")),
    ("uses require(", re.compile(r"\brequire\s*\(")),
    ("reaches process", re.compile(r"\bprocess\s*[.\[]")),
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


async def check(files: list[SandboxFile], *, design: dict | None = None) -> SandboxResult:
    """Check the text first, and the sandbox only when the text lets it through.

    Same answer as :func:`app.harness.sandbox.check`, with the static checks in
    front, so every reader — the builder fixing from it, the runner gating on it,
    the judge scoring from it — sees one list. A project that fails the text never
    reaches Modal: an empty result with the findings is a refusal, not a run.

    The design checks are added only to a project that got as far as a page: there
    is nothing to compare a plan with before the block exists, and a run refused
    for loading a stranger's stylesheet has a more urgent thing to fix.
    """
    static = inspect(files)
    if any(not one.ok for one in static):
        return SandboxResult(checks=static)

    found = await sandbox.check(files)
    checks = [*static, *found.checks]

    # A run already refused before the page existed has no preview to judge: the
    # finding would say "there is no page" about a run that never asked for one.
    # Every run that got as far as the checks is held to it.
    if not found.blocked:
        checks.append(_preview(found))
        checks.extend(inspect_design(files, design=design))

    return found.model_copy(update={"checks": checks})


def inspect_design(files: list[SandboxFile], *, design: dict | None) -> list[SandboxCheck]:
    """What the project says about following the plan it was given.

    Three questions with an answer in the text, chosen because a person can check
    them by looking: are the planned families imported, is there more than one
    radius in play, and does the accent exist (and stop there). None is fatal.
    """
    if not design:
        return []

    return [
        _type_deviation(files, design),
        _one_radius(files),
        _accent_spend(files, design),
    ]


def _type_deviation(files: list[SandboxFile], design: dict) -> SandboxCheck:
    """Whether the families the plan named are the ones the project imports."""
    packages = {
        one.get("package")
        for one in (design.get("typography") or {}).values()
        if isinstance(one, dict) and one.get("package")
    }
    planned = {one.split("/")[-1] for one in packages}
    imported = set()
    for file in files:
        imported.update(FONT_IMPORT.findall(file.content))

    missing = sorted(planned - imported)
    if not missing:
        return SandboxCheck(name=DESIGN_TYPE, ok=True)

    return SandboxCheck(
        name=DESIGN_TYPE,
        ok=False,
        detail=(
            "the plan named "
            + ", ".join(sorted(planned))
            + ", and the project imports "
            + (", ".join(sorted(imported)) or "no family")
            + f" (missing: {', '.join(missing)})"
        ),
    )


def _one_radius(files: list[SandboxFile]) -> SandboxCheck:
    """Whether every rounded surface shares one radius, which is one decision lost."""
    counts: dict[str, int] = {}
    for file in files:
        for value in ROUNDED.findall(file.content):
            if value == "rounded-none":
                continue
            counts[value] = counts.get(value, 0) + 1

    if len(counts) != 1:
        return SandboxCheck(name=DESIGN_RADIUS, ok=True)

    value, times = next(iter(counts.items()))
    if times < RADIUS_REPEATS:
        return SandboxCheck(name=DESIGN_RADIUS, ok=True)

    return SandboxCheck(
        name=DESIGN_RADIUS,
        ok=False,
        detail=(
            f"every surface uses `{value}` ({times} times): buttons, containers and "
            "pictures share one radius, so none of them is saying anything"
        ),
    )


def _accent_spend(files: list[SandboxFile], design: dict) -> SandboxCheck:
    """Whether the planned accent is in the project, and whether it is alone."""
    accent = design.get("accent")
    hues: dict[str, int] = {}
    for file in files:
        for hue in COLOUR.findall(file.content):
            if hue not in COLOURLESS:
                hues[hue] = hues.get(hue, 0) + 1

    findings: list[str] = []
    if accent and accent != "neutral" and accent not in hues:
        findings.append(f"the plan's accent `{accent}` never appears in the project")
    if len(hues) > 4:
        findings.append(
            "colour families in play: "
            + ", ".join(sorted(hues))
            + " (four is already a lot for one block)"
        )

    if not findings:
        return SandboxCheck(name=DESIGN_ACCENT, ok=True)

    return SandboxCheck(name=DESIGN_ACCENT, ok=False, detail="; ".join(findings))


def _preview(found: SandboxResult) -> SandboxCheck:
    """Whether the block can be handed to a visitor as a live page.

    The size bar is applied here rather than in the sandbox because it is the
    registry's decision: the container carries a document, this side decides
    whether it is small enough to store. A missing document is a failure, not an
    absent check — an old or broken sandbox must not publish a block the item page
    cannot show.
    """
    if found.preview is None:
        return SandboxCheck(
            name=PREVIEW,
            ok=False,
            detail=found.preview_error or "the sandbox produced no interactive build.",
        )

    size = len(found.preview.encode("utf-8"))
    if size > PREVIEW_MAX_BYTES:
        return SandboxCheck(
            name=PREVIEW,
            ok=False,
            detail=(
                f"the interactive build is {size} bytes, over the registry's "
                f"limit of {PREVIEW_MAX_BYTES}."
            ),
        )

    return SandboxCheck(name=PREVIEW, ok=True)


def _external_assets(file: SandboxFile, hosts: tuple[str, ...]) -> list[str]:
    """Every value the browser would fetch from somewhere that is not ours."""
    found: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()

    for pattern in (LOADING, LINK, ANCHOR, SVG_REF, CSS_URL, CSS_IMPORT):
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
        return _host_allowed(value[2:], hosts)

    scheme, found, rest = value.partition(":")
    if not found or not SCHEME.match(scheme):
        # No scheme: a relative path, which travels with the project.
        return True
    if scheme.lower() in SCHEMES_THAT_TRAVEL:
        return True
    if scheme.lower() not in ("http", "https"):
        return False

    return _host_allowed(rest.lstrip("/"), hosts)


def _host_allowed(authority_and_path: str, hosts: tuple[str, ...]) -> bool:
    """Whether a URL is on an allowed host, and on our own Cloudinary account.

    A host allowlist alone would let a block load from any Cloudinary customer,
    which is both a third-party image and a way to put data in somebody else's
    access log. When the deployment names its cloud, the path has to belong to it.
    """
    host = _host_of(authority_and_path)
    if host not in hosts:
        return False
    if host != "res.cloudinary.com":
        return True

    cloud = settings.cloudinary_cloud_name
    if not cloud:
        return True

    _, _, path = authority_and_path.partition("/")
    return path.startswith(f"{cloud}/")


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
