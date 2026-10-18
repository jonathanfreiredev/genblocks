"""The sandbox, as a Modal app.

Deployed on its own, from ``backend/``:

    modal deploy app/harness/modal_app.py

It is not part of the service, and that is the point. It runs code a model wrote,
so it holds **no secret** and reaches nothing of ours: it is handed files and
answers with what it found. The backend calls it by name
(``app/harness/sandbox.py``) and this never calls back.

**The image is the project.** Node, Chromium and the scaffold's dependencies are
installed when the image is built, not on every run: a check that spent a minute
installing React is a check nobody runs twice. A run then gets a copy of the
scaffold, with the scaffold's ``node_modules`` symlinked in rather than copied.

**The container outlives the call.** Modal keeps containers warm and feeds them
one input at a time, so ``/root`` and ``/tmp`` survive between runs; that is why
every run works in a directory of its own (see :func:`check`).

To work on it by hand, ``modal run app/harness/modal_app.py`` calls the function
in the file — in a throwaway app, not the deployed one — and prints what it
found. The deployed app stays where it is.

The shape of the request and the answer is ``app/harness/schemas.py``, which is
the side that strictly reads it. What this module knows is only the names of the
checks, because it is the one that runs them.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

import modal

if TYPE_CHECKING:
    from playwright.sync_api import Page

APP_NAME = "genblocks-harness"
FUNCTION_NAME = "check"

# The scaffold as it stands in the repository, copied into the image when it is
# built. Local paths are relative to this file.
SCAFFOLD = Path(__file__).parent / "scaffold"
REMOTE_SCAFFOLD = Path("/root/scaffold")

# Where the block goes: the path the scaffold's entry point imports.
BLOCK_PATH = "src/Block.tsx"

# The viewports a block is rendered at. The desktop one is kept as the
# screenshot, because that is the one the registry shows.
VIEWPORTS = (
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "tablet", "width": 834, "height": 1112},
    {"name": "phone", "width": 390, "height": 844},
)
KEPT_VIEWPORT = "desktop"

# axe findings that fail the accessibility check. A minor finding is recorded
# and left to the judge: this phase reports, it does not rule.
SERIOUS_IMPACTS = ("serious", "critical")

# What counts as drawn: words, or something a reader sees instead of them (a
# chart, an illustration). The point is to tell a page that ran from one that
# threw on the way up, not to judge how much the block says — that is the judge's
# work, and a terse block is not a broken one.
DRAWN = """() => {
    if (document.body.innerText.trim().length > 0) return true;
    return document.querySelector("svg, canvas, img, picture, video") !== null;
}"""

# Waiting for the animations to land, written as JS with its bound as a name: the
# script is read by a person as much as by the browser, and a page with a loop
# forever in it never finishes.
SETTLE_SCRIPT = """() => {
    const moving = document.getAnimations().map((one) => one.finished);
    return Promise.race([
        Promise.allSettled(moving),
        new Promise((done) => setTimeout(done, SETTLE_MILLISECONDS)),
    ]);
}"""

# How long a page gets to draw, and how often it is looked at meanwhile. Short
# polls because the interesting answer is usually already in hand: a block that
# throws reports itself through the error listener a moment after it loads, and
# the bound is only for a page that mounts and never draws anything.
RENDER_TIMEOUT_SECONDS = 15
POLL_MILLISECONDS = 100

# How long a page is given to let its animations land before it is measured or
# photographed. A block that animates its content in has an empty first frame, and
# a screenshot of that is a picture of a block nobody wrote. The bound is what keeps
# an animation that repeats for ever — a marquee, a pulse — from being waited on,
# and it is short because entrances are: a page with one in it pays this bound on
# every load, and four loads per check.
SETTLE_TIMEOUT_MILLISECONDS = 1000

# A run that has already failed one of these will not be published, so there is
# nothing to photograph: the render is the most expensive thing this function
# does. The names are the checks above the render, in the order they run; what a
# failure *means* is decided on the other side (``app/harness/schemas.py``).
GATES = ("imports", "typecheck", "build")

# What an import looks like: ``from "x"``, ``import "x"``, and the dynamic form.
# Read rather than run: the point is to see what the project asks for, not to
# resolve it.
IMPORT = re.compile(r"""(?:from|import)\s*\(?\s*["']([^"']+)["']""")

# What the project may import, by suffix. ``.css`` files import each other by
# relative path, which is the project's business and not the shelf's.
SOURCE_SUFFIXES = (".ts", ".tsx", ".css")

# How long one command may take, and how much of its output is worth keeping. A
# typecheck error is in the first line; the rest is the same stack again.
COMMAND_TIMEOUT_SECONDS = 300
DETAIL_LIMIT = 400

IMAGE = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .pip_install("playwright")
    .run_commands("playwright install --with-deps chromium")
    # Copied in rather than mounted at startup, because the install below has to
    # run after it: the price is a rebuild whenever the scaffold changes, which is
    # right — the scaffold is part of what a check *is*.
    .add_local_dir(
        SCAFFOLD,
        remote_path=str(REMOTE_SCAFFOLD),
        copy=True,
        ignore=["node_modules", "dist"],
    )
    .run_commands(f"cd {REMOTE_SCAFFOLD} && npm install --no-audit --no-fund")
)

app = modal.App(APP_NAME)


@app.function(image=IMAGE, timeout=900, cpu=2, memory=4096)
def check(request: dict) -> dict[str, Any]:
    """Build, check and render one project, and say what happened.

    The commands run in the order a reader would run them: types first, then
    style, then whether it bundles at all. A project already refused by one of the
    gates is not rendered: there would be nothing published from it either way,
    and the render is the slow part.

    Every run gets a directory of its own. Modal keeps containers warm and hands
    them one input at a time, so a shared path would carry the last block's
    ``src/Block.tsx`` — and worse, its ``dist/`` — into this check, where a stale
    bundle could make a broken block pass.
    """
    with tempfile.TemporaryDirectory() as workdir:
        project = Path(workdir)
        _lay_out(project, request["files"])

        imports, dependencies = _imports(request["files"])
        checks = [
            imports,
            _npm(project, script="typecheck", name="typecheck"),
            _npm(project, script="lint", name="lint"),
            _npm(project, script="build", name="build"),
        ]

        if any(check["name"] in GATES and not check["ok"] for check in checks):
            return {
                "checks": checks,
                "violations": [],
                "dependencies": dependencies,
                "screenshot": None,
            }

        rendered = _render(project)

        return {
            "checks": [*checks, *rendered["checks"]],
            "violations": rendered["violations"],
            "dependencies": dependencies,
            "screenshot": rendered["screenshot"],
        }


def _imports(files: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, str]]:
    """Whether the block imports anything outside the shelf, and what it uses.

    The shelf is the scaffold's own ``dependencies``, read from the project rather
    than listed here: a package the image installs is one the person copying the
    block can install too, and a check with its own copy of that list would
    eventually disagree with the install.

    Only the files the caller sent are read — the block — and not the scaffold's
    own: the scaffold's stylesheet imports Tailwind because it is the scaffold, and
    reading the ruler as if it were the artifact would fail every block.

    What this answers is also what the block declares: the names and versions of
    the packages it imports, which is the install line a visitor needs and cannot
    derive from the code by hand.
    """
    shelf = dict(json.loads((REMOTE_SCAFFOLD / "package.json").read_text())["dependencies"])
    used: dict[str, str] = {}
    strange: list[str] = []

    for sent in files:
        if Path(sent["path"]).suffix not in SOURCE_SUFFIXES:
            continue

        for specifier in IMPORT.findall(sent["content"]):
            package = _package_of(specifier)
            if package is None:
                continue

            if package in shelf:
                used[package] = shelf[package]
            else:
                strange.append(f"{sent['path']} imports {package}")

    return (
        {
            "name": "imports",
            "ok": not strange,
            "detail": None if not strange else _trimmed("; ".join(strange)),
        },
        dict(sorted(used.items())),
    )


def _package_of(specifier: str) -> str | None:
    """The package an import names, or ``None`` when it is the project's own file.

    ``@base-ui/react/dialog`` is ``@base-ui/react``; ``./Field`` and ``/assets/x``
    belong to the project, and ``vite/client`` is a type reference.
    """
    if specifier.startswith((".", "/")):
        return None

    parts = specifier.split("/")
    if specifier.startswith("@"):
        return "/".join(parts[:2]) if len(parts) >= 2 else None

    return parts[0]


def _lay_out(project: Path, files: list[dict[str, str]]) -> None:
    """One project: the scaffold, then the files the caller sent."""
    shutil.copytree(
        REMOTE_SCAFFOLD,
        project,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("node_modules", "dist"),
    )

    # The image's install, not a copy of it: node_modules is hundreds of
    # megabytes, and moving them per run would cost more than the run. Shared by
    # every run in this container, which is safe while they go one at a time —
    # npm and Vite do write small things in there, and that is the first thing to
    # look at before ever running two inputs at once.
    (project / "node_modules").symlink_to(
        REMOTE_SCAFFOLD / "node_modules", target_is_directory=True
    )

    root = project.resolve()
    for sent in files:
        path = (project / sent["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"A file was sent outside the project: {sent['path']}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sent["content"], encoding="utf-8")


def _npm(project: Path, *, script: str, name: str) -> dict[str, Any]:
    """One of the scaffold's scripts, as a check."""
    try:
        done = subprocess.run(
            ["npm", "run", script],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"name": name, "ok": False, "detail": f"{script} ran past its bound."}

    return {
        "name": name,
        "ok": done.returncode == 0,
        "detail": None if done.returncode == 0 else _trimmed(f"{done.stdout}\n{done.stderr}"),
    }


def _render(project: Path) -> dict[str, Any]:
    """Serve the built page, look at it at every viewport, and photograph it."""
    # Imported here rather than at the top: Playwright lives in the image, not in
    # the service, and this module has to be importable wherever the service runs.
    from playwright.sync_api import sync_playwright

    server, port = _served(project / "dist")
    violations: list[dict[str, Any]] = []
    screenshot: bytes | None = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport=_size(KEPT_VIEWPORT))

            trouble: list[str] = []
            page.on("pageerror", lambda error: trouble.append(str(error)))
            page.on("console", lambda message: _kept(trouble, message))

            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            rendered = _rendered(page, trouble)
            rest: list[dict[str, Any]] = []

            # A page that did not come up is not measured and not photographed:
            # its layout and its contrast say nothing about the block, and the
            # picture would be of a blank page.
            if rendered["ok"]:
                _settled(page)
                rest.extend(_layouts(page, port))
                accessibility, violations = _accessible(page)
                rest.append(accessibility)
                screenshot = page.screenshot()

            browser.close()
    finally:
        server.shutdown()

    return {"checks": [rendered, *rest], "violations": violations, "screenshot": screenshot}


def _rendered(page: Page, trouble: list[str]) -> dict[str, Any]:
    """Whether the page came up, drew something, and kept quiet doing it.

    Looked at in a loop rather than waited on in one go, because the two failures
    announce themselves differently: a block that throws says so through the error
    listener a moment after it loads, and a block that mounts and draws nothing
    says so by never drawing. A single wait for the drawing would spend the whole
    bound learning what the first poll already knew.
    """
    deadline = time.monotonic() + RENDER_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if trouble:
            return _did_not_render(trouble)

        if page.evaluate(DRAWN):
            return {"name": "render", "ok": True, "detail": None}

        # Not a sleep in the Python sense: Playwright keeps delivering the page's
        # events while this wait runs, which is what fills ``trouble``.
        page.wait_for_timeout(POLL_MILLISECONDS)

    return _did_not_render(trouble, or_else="The block mounted and drew nothing.")


def _did_not_render(trouble: list[str], *, or_else: str | None = None) -> dict[str, Any]:
    """The render check, failed, saying what the page did instead."""
    said = "; ".join(trouble) or or_else or "The block drew nothing."

    return {"name": "render", "ok": False, "detail": _trimmed(said)}


def _layouts(page: Page, port: int) -> list[dict[str, Any]]:
    """Whether the block fits each viewport, one check each."""
    found = []

    for viewport in VIEWPORTS:
        page.set_viewport_size(_size(viewport["name"]))
        page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
        # Measured on a page that has arrived and settled: an entrance still in
        # flight is not the layout anybody ends up looking at.
        _painted(page)
        _settled(page)

        overflow = page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        found.append(
            {
                "name": f"layout:{viewport['name']}",
                "ok": overflow <= 0,
                "detail": None
                if overflow <= 0
                else f"The block is {overflow}px wider than a {viewport['width']}px viewport.",
            }
        )

    return found


def _painted(page: Page) -> bool:
    """Wait for the page to draw something, without judging it.

    The layout checks measure a page that exists: measuring an empty document
    would pass every block, because an empty document never overflows.
    """
    deadline = time.monotonic() + RENDER_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        if page.evaluate(DRAWN):
            return True

        page.wait_for_timeout(POLL_MILLISECONDS)

    return False


def _settled(page: Page) -> None:
    """Wait for the page's animations to land, up to a bound.

    A block that animates its content in has an empty first frame, and a screenshot
    of the first frame is a picture of a block nobody wrote — so the render waits
    for what is moving to stop. It cannot wait for ever: an animation that repeats
    (a marquee, a pulse) never finishes, and a page with one still has to be
    checked.
    """
    page.evaluate(SETTLE_SCRIPT.replace("SETTLE_MILLISECONDS", str(SETTLE_TIMEOUT_MILLISECONDS)))


def _size(name: str) -> dict[str, int]:
    """One viewport's dimensions, without its name: what Playwright takes."""
    viewport = next(one for one in VIEWPORTS if one["name"] == name)

    return {"width": viewport["width"], "height": viewport["height"]}


def _accessible(page: Page) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """axe's verdict as a check, and its findings as themselves.

    The findings travel separately rather than being summarised into the check:
    the judge reads ids and impacts, and a count would be a worse answer than the
    list.
    """
    page.set_viewport_size(_size(KEPT_VIEWPORT))
    page.add_script_tag(path=str(REMOTE_SCAFFOLD / "node_modules" / "axe-core" / "axe.min.js"))

    violations = page.evaluate(
        """async () => {
            const report = await axe.run(document);
            return report.violations.map((violation) => ({
                id: violation.id,
                impact: violation.impact,
                help: violation.help,
                nodes: violation.nodes.length,
            }));
        }"""
    )

    serious = [one for one in violations if one["impact"] in SERIOUS_IMPACTS]
    check = {
        "name": "accessibility",
        "ok": not serious,
        "detail": None
        if not serious
        else "; ".join(f"{one['id']} ({one['impact']}, {one['nodes']} nodes)" for one in serious),
    }

    return check, violations


def _kept(trouble: list[str], message: Any) -> None:
    """Keep what the page logged as an error, and nothing else.

    A block that warns is a block with an opinion; a block that logs an error is
    usually one that broke.
    """
    if message.type == "error":
        trouble.append(message.text)


def _served(directory: Path) -> tuple[ThreadingHTTPServer, int]:
    """Serve a built page over loopback, in a thread.

    Over HTTP rather than off the filesystem because Chromium refuses to load a
    module from ``file://``: serving it is also the only honest way to screenshot
    what a host would send.

    Port 0, so the system picks a free one. Containers take one input at a time by
    default, but nothing here should depend on that being true for ever.
    """
    handler = partial(_Quiet, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, server.server_address[1]


class _Quiet(SimpleHTTPRequestHandler):
    """A server that does not narrate every request into the logs."""

    def log_message(self, *args: Any) -> None:
        return None


def _trimmed(text: str) -> str:
    """The head of a command's output: where the reason is."""
    collapsed = " ".join(text.split())

    return collapsed[:DETAIL_LIMIT]


@app.local_entrypoint()
def main(file: str = str(SCAFFOLD / "src" / "Block.tsx")) -> None:
    """Check one file by hand: ``modal run app/harness/modal_app.py``."""
    source = Path(file)
    result = check.remote({"files": [{"path": BLOCK_PATH, "content": source.read_text()}]})

    for one in result["checks"]:
        print(f"{'ok  ' if one['ok'] else 'FAIL'} {one['name']}: {one['detail'] or ''}")

    for one in result["violations"]:
        print(f"  a11y {one['impact']} {one['id']}: {one['help']}")

    if result["screenshot"]:
        written = Path("render.png")
        written.write_bytes(result["screenshot"])
        print(f"screenshot: {written.resolve()}")
