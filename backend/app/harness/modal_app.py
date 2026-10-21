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
import os
import posixpath
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

# The viewports a block is rendered at, widest first so the last pass before the
# phone-specific checks is already at 390px. The desktop one is kept as the
# screenshot, because that is the one the registry shows; the others exist so the
# gate sees a laptop, a tablet and a phone rather than trusting the block to have
# thought about them.
VIEWPORTS = (
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "laptop", "width": 1024, "height": 768},
    {"name": "tablet", "width": 834, "height": 1112},
    {"name": "phone", "width": 390, "height": 844},
)
KEPT_VIEWPORT = "desktop"

# A screenshot is a picture of text on a flat ground, not a transparent asset.
# JPEG at this quality is a fraction of the PNG and is what Cloudinary delivers
# anyway; there is no reason to pay to store the uncompressed frame.
SCREENSHOT_TYPE = "jpeg"
SCREENSHOT_QUALITY = 85
SCREENSHOT_MEDIA_TYPE = "image/jpeg"

# The catalogue's thumbnail is not the judge's render. At 1440px a block is a wide
# band on a 900px page, and a square tile cannot be filled with that without
# cutting the composition or leaving the page's white below it. At 390px — the
# phone the harness already renders — a block is compact and nearly square, so the
# wall shows the block and nothing else (PLAN.md, decision 49). The top of a
# taller one is what a thumbnail shows anyway.
THUMBNAIL_WIDTH = 390
THUMBNAIL_VIEWPORT_HEIGHT = 844
THUMBNAIL_MAX_HEIGHT = 390
THUMBNAIL_QUALITY = 82

# axe findings that fail the accessibility check. A minor finding is recorded and
# left to the judge; contrast failures and unlabelled controls are not minor, and
# the backend treats this check as a gate.
SERIOUS_IMPACTS = ("serious", "critical")

# The checks this module adds for the parts of the interface a screenshot cannot
# prove. The names are repeated in ``app/harness/schemas.py``, which is where the
# pipeline decides they are gates.
ACCESSIBILITY = "accessibility"
TARGETS = "targets"
FOCUS = "focus"
MOTION_REDUCED = "motion:reduce"

# WCAG 2.2's minimum target size (AA), in CSS pixels. Apple's 44px is advice, not
# the bar: a 44px gate would fail half the legitimate inline controls on the web.
MIN_TARGET_PX = 24

# What counts as motion someone asked not to see. A state change of 150–200ms is
# a transition; anything still running after that, or repeating for ever, is the
# kind of movement `prefers-reduced-motion` exists for.
REDUCED_MOTION_MAX_MS = 200
REDUCED_MOTION_SETTLE_MS = 320

# Every control a visitor can operate. Inline links inside a sentence are exempt
# from the target-size rule, which the script applies by display.
INTERACTIVE = (
    'a[href], button, input:not([type="hidden"]), select, textarea, summary, '
    '[role="button"], [role="link"], [role="checkbox"], [role="radio"], '
    '[role="switch"], [role="tab"]'
)

# The class the registry puts on the page to switch the library to dark. It is the
# one the scaffold's `dark:` variant answers to (see the scaffold's `index.css`).
DARK_CLASS = "dark"

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

# The animations the page started, as the browser reports them: state, duration
# and whether they repeat. Read twice — once at load for evidence, once with
# reduced motion on to see whether the block honoured it.
ANIMATIONS = """() => document.getAnimations().map((animation) => {
    const timing = animation.effect && animation.effect.getComputedTiming
        ? animation.effect.getComputedTiming()
        : {};

    return {
        state: animation.playState,
        duration: typeof timing.duration === "number" ? timing.duration : 0,
        iterations: timing.iterations === Infinity ? "infinite" : (timing.iterations || 1),
    };
})"""

# Controls smaller than the WCAG 2.2 minimum, by their own box or by the label
# that is the thing a finger actually hits. Inline links in a sentence are part of
# the text, not a target, and are exempt.
TARGETS_SCRIPT = """() => {
    const selector = 'SELECTOR';
    const small = [];

    const visible = (element) => {
        const style = getComputedStyle(element);

        return style.display !== "none"
            && style.visibility !== "hidden"
            && style.opacity !== "0"
            && element.getClientRects().length > 0;
    };

    const named = (element) =>
        (element.getAttribute("aria-label") || element.textContent || "")
            .trim()
            .replace(/\\s+/g, " ")
            .slice(0, 40);

    for (const element of document.querySelectorAll(selector)) {
        if (!visible(element)) {
            continue;
        }

        if (element.tagName === "A" && getComputedStyle(element).display === "inline") {
            continue;
        }

        const box = element.getBoundingClientRect();
        const label = element.labels && element.labels[0]
            ? element.labels[0].getBoundingClientRect()
            : null;
        const width = Math.max(box.width, label ? label.width : 0);
        const height = Math.max(box.height, label ? label.height : 0);

        if (width >= MIN_TARGET && height >= MIN_TARGET) {
            continue;
        }

        small.push({
            tag: element.tagName.toLowerCase(),
            name: named(element),
            width: Math.round(width),
            height: Math.round(height),
        });
    }

    return small.slice(0, 5);
}""".replace("MIN_TARGET", str(MIN_TARGET_PX)).replace("SELECTOR", INTERACTIVE)

# Whether a control shows that it has focus. The page is put in keyboard modality
# first (the caller presses Tab), so a `focus-visible:` ring counts, and the style
# of the element and of its parent are compared before and after: a wrapper is a
# legitimate place for the ring.
FOCUS_SCRIPT = r"""() => {
    const selector = 'SELECTOR';
    const missing = [];

    const visible = (element) => {
        const style = getComputedStyle(element);

        return style.display !== "none"
            && style.visibility !== "hidden"
            && style.opacity !== "0"
            && element.getClientRects().length > 0;
    };

    const named = (element) =>
        (element.getAttribute("aria-label") || element.textContent || "")
            .trim()
            .replace(/\s+/g, " ")
            .slice(0, 40);

    // A painted ring, not a computed one. Chrome reports an outline colour and a
    // width on a focused control even when `outline-style` is `none`; comparing
    // raw values would call that visible. Transparent counts as invisible.
    const clear = (color) =>
        /^transparent$/i.test(color)
        || (/^rgba\(/i.test(color) && /,\s*0(?:\.0+)?\)$/.test(color));

    const painted = (style) =>
        style.outlineStyle !== "none"
        && parseFloat(style.outlineWidth) > 0
        && !clear(style.outlineColor);

    const shape = (element) => {
        const own = getComputedStyle(element);
        const parent = element.parentElement ? getComputedStyle(element.parentElement) : null;

        return {
            outline: painted(own),
            outlineColor: own.outlineColor,
            shadow: own.boxShadow !== "none",
            shadowValue: own.boxShadow,
            border: own.borderColor,
            background: own.backgroundColor,
            decoration: own.textDecorationLine,
            parentOutline: parent ? painted(parent) : false,
            parentOutlineColor: parent ? parent.outlineColor : "",
            parentShadow: parent ? parent.boxShadow : "none",
        };
    };

    const shows = (before, after) =>
        (after.outline && (!before.outline || after.outlineColor !== before.outlineColor))
        || (after.shadow && (!before.shadow || after.shadowValue !== before.shadowValue))
        || after.border !== before.border
        || after.background !== before.background
        || after.decoration !== before.decoration
        || (after.parentOutline
            && (!before.parentOutline || after.parentOutlineColor !== before.parentOutlineColor))
        || (after.parentShadow !== "none" && after.parentShadow !== before.parentShadow);

    for (const element of [...document.querySelectorAll(selector)].filter(visible).slice(0, 24)) {
        element.blur();
        const before = shape(element);

        element.focus();
        const after = shape(element);

        element.blur();

        if (!shows(before, after)) {
            missing.push({ tag: element.tagName.toLowerCase(), name: named(element) });
        }
    }

    return missing.slice(0, 5);
}""".replace("SELECTOR", INTERACTIVE)

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
GATES = ("imports", "ast", "typecheck", "build", "bundle")

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

# The agent already bounds writes, but the sandbox is the last place that has to
# believe it. A corrupt or older caller cannot turn one render into a disk fill.
MAX_FILES = 40
MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 2_000_000

# The scaffold owns these two even though they live under ``src``. The harness
# already refuses them; the sandbox repeats the rule because it is the last door.
RESERVED_PATHS = frozenset({"src/main.tsx", "src/index.css"})

# Where the interactive build lands once the page has been inlined, and how much
# of it this function will carry. This is the transport's bound, not the policy:
# what the registry publishes is decided in ``app/harness/schemas.py``, and a
# preview over its bar is refused there with the size in the finding.
PREVIEW_PATH = "dist/preview.html"
MAX_PREVIEW_TRANSPORT_BYTES = 4_000_000

# How long the browser may spend on one operation before Playwright gives up. The
# render loop has its own deadline; this is the net under a page that blocks its
# own JavaScript thread.
BROWSER_TIMEOUT_MS = 20_000

# A route and a CSP do not cover every browser side channel. WebRTC can reach a
# STUN server over UDP without passing through either, so the page is given no
# constructor to open it with.
_NO_SIDE_CHANNELS = """\
for (const name of ["RTCPeerConnection", "webkitRTCPeerConnection", "WebTransport"]) {
    try {
        Object.defineProperty(window, name, { value: undefined, configurable: false });
    } catch {
        // A browser that does not define it has nothing to remove.
    }
}
"""

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

    The answer carries both pictures: the desktop render the judge reads and the
    card crop the wall reads.

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
        asset_prefixes = tuple(request.get("asset_prefixes") or ())

        imports, dependencies = _imports(request["files"])
        checks = [
            imports,
            _npm(project, script="security:source", name="ast"),
        ]

        # The source scan is cheap and reads the project the model actually
        # wrote. A project that fails it never pays for a typecheck or a build.
        if any(check["name"] in GATES and not check["ok"] for check in checks):
            return _unrendered(checks, dependencies)

        checks.extend(
            [
                _npm(project, script="typecheck", name="typecheck"),
                _npm(project, script="lint", name="lint"),
                _npm(project, script="build", name="build"),
            ]
        )
        if any(check["name"] in GATES and not check["ok"] for check in checks):
            return _unrendered(checks, dependencies)

        # The bundle is the bytes a browser executes, not the source a reader
        # reviews. It is scanned after Vite has finished rewriting them.
        checks.append(_npm(project, script="security:bundle", name="bundle"))
        if any(check["name"] in GATES and not check["ok"] for check in checks):
            return _unrendered(checks, dependencies)

        rendered = _render(project, asset_prefixes=asset_prefixes)

        # The interactive build is made from the same bytes that were just
        # rendered: a page that did not come up has nothing to hand over, and a
        # page that did gets its `dist` folded into one document.
        preview, preview_error = (
            _inline(project) if rendered["screenshot"] is not None else (None, None)
        )

        return {
            "checks": [*checks, *rendered["checks"]],
            "violations": rendered["violations"],
            "dependencies": dependencies,
            "screenshot": rendered["screenshot"],
            "screenshot_dark": rendered["screenshot_dark"],
            "thumbnail": rendered["thumbnail"],
            "screenshot_media_type": rendered["screenshot_media_type"],
            "preview": preview,
            "preview_error": preview_error,
        }


def _unrendered(checks: list[dict[str, Any]], dependencies: dict[str, str]) -> dict[str, Any]:
    """A run that stopped before the render: the checks, and no page."""
    return {
        "checks": checks,
        "violations": [],
        "dependencies": dependencies,
        "screenshot": None,
        "screenshot_dark": None,
        "screenshot_media_type": SCREENSHOT_MEDIA_TYPE,
        "preview": None,
        "preview_error": None,
    }


def _inline(project: Path) -> tuple[str | None, str | None]:
    """Fold the built page into one document, or say why it could not be done.

    The inliner is part of the scaffold, so the rules about what a preview may
    reach travel with the build. A document over the transport's bound is dropped
    and named: the registry's own bar is applied on the other side, where the
    finding is written.
    """
    done = _npm(project, script="preview", name="preview")
    if not done["ok"]:
        return None, done["detail"] or "the page could not be folded into one file."

    path = project / PREVIEW_PATH
    if not path.is_file():
        return None, "the inliner produced no preview."

    text = path.read_text(encoding="utf-8")
    size = len(text.encode("utf-8"))
    if size > MAX_PREVIEW_TRANSPORT_BYTES:
        return None, f"the interactive build is {size} bytes, more than the sandbox carries."

    return text, None


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
    if len(files) > MAX_FILES:
        raise ValueError(f"A project may hold at most {MAX_FILES} files.")

    total = sum(len(sent.get("content", "")) for sent in files)
    if total > MAX_TOTAL_BYTES:
        raise ValueError(f"A project may hold at most {MAX_TOTAL_BYTES} bytes.")

    root = project.resolve()
    for sent in files:
        if sent["path"] != posixpath.normpath(sent["path"]):
            raise ValueError(f"A file path was not normalized: {sent['path']}")
        if sent["path"] in RESERVED_PATHS:
            raise ValueError(f"The scaffold owns {sent['path']}.")

        path = (project / sent["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"A file was sent outside the project: {sent['path']}")
        if len(sent["content"]) > MAX_FILE_BYTES:
            raise ValueError(f"A file may hold at most {MAX_FILE_BYTES} bytes: {sent['path']}")

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

    for sent in files:
        path = (project / sent["path"]).resolve()
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


def _render(project: Path, *, asset_prefixes: tuple[str, ...] = ()) -> dict[str, Any]:
    """Serve the built page, look at it at every viewport, and photograph both grounds.

    The page is untrusted. It runs in a browser context with no network, no
    downloads, no popups, no service workers and no permissions; the HTTP server
    sends a CSP that repeats the same rules at the layer the page cannot argue
    with. The static checks catch what a reader can see; this is what catches the
    network a page tries to reach anyway.
    """
    # Imported here rather than at the top: Playwright lives in the image, not in
    # the service, and this module has to be importable wherever the service runs.
    from playwright.sync_api import sync_playwright

    # Axe travels through the project's own server, so the page's `script-src
    # 'self'` still holds: the checker is not an exception to the policy it checks.
    shutil.copyfile(
        REMOTE_SCAFFOLD / "node_modules" / "axe-core" / "axe.min.js",
        project / "dist" / "axe.min.js",
    )
    server, port = _served(project / "dist", asset_prefixes=asset_prefixes)
    violations: list[dict[str, Any]] = []
    screenshot: bytes | None = None
    screenshot_dark: bytes | None = None
    thumbnail: bytes | None = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=_browser_args())
            context = browser.new_context(
                viewport=_size(KEPT_VIEWPORT),
                accept_downloads=False,
                service_workers="block",
                permissions=[],
            )
            context.add_init_script(_NO_SIDE_CHANNELS)

            # Only the project's own server is reachable. A navigation, image,
            # stylesheet, fetch or module from anywhere else is aborted before a
            # packet leaves the container.
            context.route(
                "**/*",
                lambda route: _only_local(route, port, asset_prefixes=asset_prefixes),
            )
            if hasattr(context, "route_web_socket"):
                context.route_web_socket("**/*", lambda socket: socket.close())

            page = context.new_page()
            page.set_default_timeout(BROWSER_TIMEOUT_MS)
            page.on("popup", lambda popup: popup.close())
            page.on("download", lambda download: download.cancel())

            trouble: list[str] = []
            page.on("pageerror", lambda error: trouble.append(str(error)))
            page.on("console", lambda message: _kept(trouble, message))

            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            # Read before the page is allowed to settle: an entrance that has
            # already finished cannot be described. This is evidence for the
            # judge, not a gate — motion is scored, not mandated.
            motion = _motion_summary(page.evaluate(ANIMATIONS))
            rendered = _rendered(page, trouble)
            rest: list[dict[str, Any]] = []

            # A page that did not come up is not measured and not photographed:
            # its layout and its contrast say nothing about the block, and the
            # picture would be of a blank page.
            if rendered["ok"]:
                _settled(page)
                rest.extend(_layouts(page, port))
                # The layout pass ends at the phone, so the target sizes are
                # measured there without loading the page again.
                rest.append(_targets(page))
                rest.append(_focus(page, port))
                rest.append(_reduced_motion(page, port=port, motion=motion))

                # The photograph is the desktop page on a light ground; the
                # browser is put back where the picture expects it.
                page.emulate_media(color_scheme="light", reduced_motion="no-preference")
                page.set_viewport_size(_size(KEPT_VIEWPORT))
                page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
                _painted(page)
                _settled(page)
                accessibility, violations = _accessible(page, port=port)
                rest.append(accessibility)
                screenshot = _shot(page)

                # The registry switches the whole library at once, by putting on
                # the page the class the scaffold's `dark:` answers to. The same
                # page is then measured and photographed again: a block that only
                # holds on one ground is half a block, and nobody would find out
                # if the second ground were never rendered.
                page.evaluate(f"document.documentElement.classList.add('{DARK_CLASS}')")
                page.emulate_media(color_scheme="dark")
                _settled(page)
                dark, dark_violations = _accessible(page, port=port, scheme="dark")
                rest.append(dark)
                violations.extend(dark_violations)
                screenshot_dark = _shot(page)

                # One more page, at the width of a card. The wall crops to a
                # square, and this is the render it crops: at 520px a block stacks
                # enough to fill it, while the 1440px page is a wide band with the
                # rest of the viewport below. Light, because a thumbnail is a
                # catalogue picture and the catalogue has one ground.
                page.emulate_media(color_scheme="light", reduced_motion="no-preference")
                page.set_viewport_size(
                    {"width": THUMBNAIL_WIDTH, "height": THUMBNAIL_VIEWPORT_HEIGHT}
                )
                page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
                _painted(page)
                _settled(page)
                thumbnail = _thumbnail(page)

            context.close()
            browser.close()
    finally:
        server.shutdown()

    return {
        "checks": [rendered, *rest],
        "violations": violations,
        "screenshot": screenshot,
        "screenshot_dark": screenshot_dark,
        "thumbnail": thumbnail,
        "screenshot_media_type": SCREENSHOT_MEDIA_TYPE,
    }


def _shot(page: Page) -> bytes:
    """One screenshot, in the format the registry actually stores."""
    return page.screenshot(type=SCREENSHOT_TYPE, quality=SCREENSHOT_QUALITY)


def _thumbnail(page: Page) -> bytes | None:
    """The block at card width, clipped to the square the wall shows."""
    box = page.locator("main").bounding_box()
    clip = _thumbnail_clip(box) if box is not None else None

    if clip is None:
        return None

    return page.screenshot(
        clip=clip,
        type=SCREENSHOT_TYPE,
        quality=THUMBNAIL_QUALITY,
    )


def _thumbnail_clip(box: dict[str, float]) -> dict[str, float] | None:
    """The part of the page a card shows: the block, cut at card height.

    A short block is captured whole, with no page below it; a tall one is cut at
    the height of a card, which is the part ``object-cover`` would keep from the
    top anyway. The width is the viewport the caller set, unless the element is
    narrower.
    """
    width = min(THUMBNAIL_WIDTH, round(box["width"]))
    height = min(round(box["height"]), THUMBNAIL_MAX_HEIGHT)

    if width <= 0 or height <= 0:
        return None

    return {
        "x": round(box["x"]),
        "y": round(box["y"]),
        "width": width,
        "height": height,
    }


def _browser_args() -> list[str]:
    """Chromium flags that keep it from reaching anything but its own server."""
    return [
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-sync",
        "--no-first-run",
        "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    ]


def _cloudinary_prefix() -> str:
    """The delivery path a block is allowed to load from, when it is known."""
    cloud = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()

    return f"https://res.cloudinary.com/{cloud}/" if cloud else "https://res.cloudinary.com/"


def _only_local(route: Any, port: int, *, asset_prefixes: tuple[str, ...] = ()) -> None:
    """Let the project's server and our pictures through, and abort the rest.

    The prefixes come from the backend, which knows its own Cloudinary account.
    When they are absent the host is allowed as a fallback, but the static check
    still narrows the account. Everything else — a fetch, a stylesheet, a font, a
    navigation, a metadata endpoint — is aborted.
    """
    request = route.request
    url = request.url
    pictures = asset_prefixes or (_cloudinary_prefix(),)

    if url.startswith(f"http://127.0.0.1:{port}/"):
        route.continue_()
        return

    # A data URL is fine as a picture, font or media source; it is not a
    # navigable page and not a script.
    if url.startswith("data:"):
        if getattr(request, "resource_type", "") in ("image", "font", "media"):
            route.continue_()
        else:
            route.abort()
        return

    if any(url.startswith(prefix) for prefix in pictures):
        route.continue_()
        return

    route.abort()


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
    """Whether the block fits each viewport, one check each.

    Four widths, and each one is a gate: a block that scrolls sideways on a phone
    is not a responsive block, and the judge is not shown the phone to notice it.
    """
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


def _targets(page: Page) -> dict[str, Any]:
    """Whether every control is big enough for a finger at a phone's width.

    The caller leaves the page at 390px and settled, which is where this is
    measured: a control that is comfortable on a laptop can be a 16px hit area on
    a phone. The label is measured too, because a visually hidden input inside a
    large label is a large target in practice.

    Inline links are exempt — they are part of a sentence, not a button — and the
    page's own hidden controls are skipped rather than counted as failures.
    """
    small = page.evaluate(TARGETS_SCRIPT)

    if not small:
        return {"name": TARGETS, "ok": True, "detail": None}

    said = "; ".join(
        "<{tag}> {name} is {width}×{height}px".format(
            tag=one["tag"],
            name=f"“{one['name']}”" if one["name"] else "(unnamed)",
            width=one["width"],
            height=one["height"],
        )
        for one in small
    )

    return {"name": TARGETS, "ok": False, "detail": _trimmed(said)}


def _focus(page: Page, port: int) -> dict[str, Any]:
    """Whether a keyboard user can see which control they are on.

    The page is put in keyboard modality before the controls are focused, so a
    block that styles `:focus-visible:` rather than `:focus` is judged by what a
    keyboard user would actually see. A ring on the control's parent counts: some
    designs put it there and it is still a visible focus.
    """
    page.emulate_media(color_scheme="light", reduced_motion="no-preference")
    page.set_viewport_size(_size(KEPT_VIEWPORT))
    page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
    _painted(page)
    _settled(page)
    page.keyboard.press("Tab")

    missing = page.evaluate(FOCUS_SCRIPT)

    if not missing:
        return {"name": FOCUS, "ok": True, "detail": None}

    said = "; ".join(
        "<{tag}> {name}".format(
            tag=one["tag"],
            name=f"“{one['name']}”" if one["name"] else "(unnamed)",
        )
        for one in missing
    )

    return {
        "name": FOCUS,
        "ok": False,
        "detail": _trimmed(f"No visible focus on: {said}"),
    }


def _reduced_motion(page: Page, *, port: int, motion: str) -> dict[str, Any]:
    """Whether the block still arrives for somebody who asked for less motion.

    The page is loaded with the preference on and read twice: while an entrance
    would still be running, and again after a short bound. What is allowed is a
    state change that has already finished, not an entrance that ignores the
    preference or one that repeats for ever. A block that hides its content behind
    an animation is the failure this check exists for, and its normal-settings
    motion is carried in the detail as evidence for the judge.
    """
    page.emulate_media(color_scheme="light", reduced_motion="reduce")
    page.set_viewport_size(_size(KEPT_VIEWPORT))
    page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
    drawn = _painted(page)

    # Read while an entrance would still be running, then again after the bound so
    # an animation started by a timer is caught too. A short state change is fine;
    # an entrance that ignores the preference is not.
    running = _long_motion(page.evaluate(ANIMATIONS))
    page.wait_for_timeout(REDUCED_MOTION_SETTLE_MS)

    if not drawn:
        return {
            "name": MOTION_REDUCED,
            "ok": False,
            "detail": "The block drew nothing with reduced motion on.",
        }

    if not running:
        running = _long_motion(page.evaluate(ANIMATIONS))

    if running:
        return {
            "name": MOTION_REDUCED,
            "ok": False,
            "detail": (
                f"{len(running)} animation(s) still running with reduced motion on "
                f"({_motion_summary(running)}). Make the movement optional and keep "
                "the content."
            ),
        }

    return {
        "name": MOTION_REDUCED,
        "ok": True,
        "detail": f"Reduced motion honoured. At normal settings: {motion}.",
    }


def _motion_summary(animations: list[dict[str, Any]]) -> str:
    """What moved, in one line, for the judge to read without another image."""
    if not animations:
        return "no animation"

    longest = round(max(float(one.get("duration") or 0) for one in animations))
    repeating = sum(1 for one in animations if one.get("iterations") == "infinite")
    said = f"{len(animations)} animation(s), longest {longest}ms"

    return said + (f", {repeating} repeating" if repeating else "")


def _long_motion(animations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The animations that are still asking for attention after the bound."""
    return [
        one
        for one in animations
        if one.get("state") == "running"
        and (
            one.get("iterations") == "infinite"
            or float(one.get("duration") or 0) > REDUCED_MOTION_MAX_MS
        )
    ]


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


def _accessible(
    page: Page, *, port: int, scheme: str = "light"
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """axe's verdict as a check, and its findings as themselves.

    The findings travel separately rather than being summarised into the check:
    the judge reads ids and impacts, and a count would be a worse answer than the
    list. Each finding says which ground it was found on, because the same id on
    the dark page is a different fact from the same id on the light one.
    """
    page.set_viewport_size(_size(KEPT_VIEWPORT))
    page.add_script_tag(url=f"http://127.0.0.1:{port}/axe.min.js")

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

    for violation in violations:
        violation["scheme"] = scheme

    serious = [one for one in violations if one["impact"] in SERIOUS_IMPACTS]
    check = {
        "name": ACCESSIBILITY if scheme == "light" else f"{ACCESSIBILITY}:{scheme}",
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


def _served(
    directory: Path, *, asset_prefixes: tuple[str, ...] = ()
) -> tuple[ThreadingHTTPServer, int]:
    """Serve a built page over loopback, in a thread.

    Over HTTP rather than off the filesystem because Chromium refuses to load a
    module from ``file://``: serving it is also the only honest way to screenshot
    what a host would send.

    Port 0, so the system picks a free one. Containers take one input at a time by
    default, but nothing here should depend on that being true for ever.
    """
    handler = partial(
        _Quiet,
        directory=str(directory),
        asset_prefixes=asset_prefixes,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, server.server_address[1]


class _Quiet(SimpleHTTPRequestHandler):
    """A server that does not narrate every request into the logs.

    It also sends the policy the browser would otherwise have to infer from the
    code. The route handler stops requests that are already in flight; the CSP
    stops most of them from being attempted, and blocks a navigation that tries
    to leave the page.
    """

    asset_prefixes: tuple[str, ...] = ()

    def __init__(self, *args: Any, asset_prefixes: tuple[str, ...] = (), **kwargs: Any) -> None:
        self.asset_prefixes = asset_prefixes
        super().__init__(*args, **kwargs)

    def log_message(self, *args: Any) -> None:
        return None

    def end_headers(self) -> None:
        for name, value in _headers(self.asset_prefixes).items():
            self.send_header(name, value)

        super().end_headers()


def _headers(asset_prefixes: tuple[str, ...] = ()) -> dict[str, str]:
    """What every rendered page is served with."""
    return {
        "Content-Security-Policy": _policy(asset_prefixes),
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        "Cache-Control": "no-store",
    }


def _policy(asset_prefixes: tuple[str, ...] = ()) -> str:
    """A CSP for a page that may draw our pictures and nothing else.

    The Cloudinary path is narrowed to the deployment's own cloud when its
    prefix is available. The static check enforces the same account; this is the
    runtime half of that rule.
    """
    if asset_prefixes:
        pictures = " ".join(asset_prefixes)
    else:
        cloud = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
        pictures = f"https://res.cloudinary.com/{cloud}/" if cloud else "https://res.cloudinary.com"

    return (
        "default-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: {pictures}; "
        "font-src 'self' data:; "
        "media-src 'self' data:; "
        "connect-src 'none'; "
        "frame-src 'none'; "
        "child-src 'none'; "
        "worker-src 'none'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'"
    )


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
