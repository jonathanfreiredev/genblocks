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

The shape of the request and the answer is ``app/harness/schemas.py``, which is
the side that strictly reads it. What this module knows is only the names of the
checks, because it is the one that runs them.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
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

# A render with nothing in it is not a render. Characters, not nodes: a block
# that draws one empty div says nothing.
MIN_RENDERED_TEXT = 20

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
    style, then whether it bundles at all. A project that does not bundle is not
    rendered — there would be no page to render, and inventing a screenshot of
    one would be the worst thing this function could do.
    """
    with tempfile.TemporaryDirectory() as workdir:
        project = Path(workdir)
        _lay_out(project, request["files"])

        checks = [
            _npm(project, script="typecheck", name="typecheck"),
            _npm(project, script="lint", name="lint"),
            _npm(project, script="build", name="build"),
        ]

        if not next(check for check in checks if check["name"] == "build")["ok"]:
            return {"checks": checks, "violations": [], "screenshot": None}

        rendered = _render(project)
        checks.extend(rendered["checks"])

        return {
            "checks": checks,
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
    # megabytes, and moving them per run would cost more than the run.
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
    checks: list[dict[str, Any]] = []

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            desktop = next(one for one in VIEWPORTS if one["name"] == KEPT_VIEWPORT)
            page = browser.new_page(
                viewport={"width": desktop["width"], "height": desktop["height"]}
            )

            trouble: list[str] = []
            page.on("pageerror", lambda error: trouble.append(str(error)))
            page.on("console", lambda message: _kept(trouble, message))

            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            checks.append(_rendered(page, trouble))

            if checks[-1]["ok"]:
                checks.extend(_layouts(page, port))
                checks.append(_accessible(page))

            screenshot = page.screenshot() if checks[0]["ok"] else None
            violations = checks[-1]["violations"] if checks[-1]["name"] == "accessibility" else []
            browser.close()
    finally:
        server.shutdown()

    return {
        "checks": [{key: check[key] for key in ("name", "ok", "detail")} for check in checks],
        "violations": violations,
        "screenshot": screenshot,
    }


def _rendered(page: Page, trouble: list[str]) -> dict[str, Any]:
    """Whether the page came up, drew something, and kept quiet doing it."""
    try:
        # Not a sleep: the block is mounted when it has text, and a page that
        # never gets any is the failure this check exists for.
        page.wait_for_function(
            "() => document.body.innerText.trim().length > 0",
            timeout=COMMAND_TIMEOUT_SECONDS * 1000,
        )
        drawn = page.evaluate("() => document.body.innerText.trim().length")
    except Exception as drew_nothing:  # noqa: BLE001 - the page's failure is the report
        return {"name": "render", "ok": False, "detail": _trimmed(str(drew_nothing))}

    if trouble:
        return {"name": "render", "ok": False, "detail": _trimmed("; ".join(trouble))}

    ok = drawn >= MIN_RENDERED_TEXT
    return {
        "name": "render",
        "ok": ok,
        "detail": None if ok else "The block rendered without text of its own.",
    }


def _layouts(page: Page, port: int) -> list[dict[str, Any]]:
    """Whether the block fits each viewport, one check each."""
    found = []

    for viewport in VIEWPORTS:
        page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
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


def _accessible(page: Page) -> dict[str, Any]:
    """axe, in its own words, at the viewport the screenshot is taken at.

    The findings travel with the check rather than being summarised into it: the
    judge reads ids and impacts, and a count would be a worse answer than the
    list.
    """
    desktop = next(viewport for viewport in VIEWPORTS if viewport["name"] == KEPT_VIEWPORT)
    page.set_viewport_size({"width": desktop["width"], "height": desktop["height"]})
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
    return {
        "name": "accessibility",
        "ok": not serious,
        "detail": None
        if not serious
        else "; ".join(f"{one['id']} ({one['impact']}, {one['nodes']} nodes)" for one in serious),
        "violations": violations,
    }


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
