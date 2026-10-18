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

# How long a page gets to draw, and how often it is looked at meanwhile. Short
# polls because the interesting answer is usually already in hand: a block that
# throws reports itself through the error listener a moment after it loads, and
# the bound is only for a page that mounts and never draws anything.
RENDER_TIMEOUT_SECONDS = 15
POLL_MILLISECONDS = 100

# A run that has already failed one of these will not be published, so there is
# nothing to photograph: the render is the most expensive thing this function
# does. The names are the checks above the render, in the order they run; what a
# failure *means* is decided on the other side (``app/harness/schemas.py``).
GATES = ("typecheck", "build")

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

        checks = [
            _npm(project, script="typecheck", name="typecheck"),
            _npm(project, script="lint", name="lint"),
            _npm(project, script="build", name="build"),
        ]

        if any(check["name"] in GATES and not check["ok"] for check in checks):
            return {"checks": checks, "violations": [], "screenshot": None}

        rendered = _render(project)

        return {
            "checks": [*checks, *rendered["checks"]],
            "violations": rendered["violations"],
            "screenshot": rendered["screenshot"],
        }


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
