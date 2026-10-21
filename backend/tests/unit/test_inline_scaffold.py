"""The page a block is published as: one document, closed by construction.

The inliner is part of the scaffold and runs inside the sandbox, so this drives it
the way the sandbox does — with Node, against a hand-built ``dist``. What is under
test is the shape of what a visitor's browser receives: no sibling requests, a
policy in the document, and the bridge the item view talks to.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "app/harness/scaffold/scripts/inline.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node is not installed")


def build(tmp_path: Path, *, html: str | None = None, script: str = "console.log(1);") -> Path:
    """A ``dist`` the way Vite leaves one: an entry page and two assets."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "assets" / "index-abc.js").write_text(script, encoding="utf-8")
    (dist / "assets" / "index-abc.css").write_text("body{margin:0}", encoding="utf-8")
    (dist / "index.html").write_text(
        html
        or (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<link rel="modulepreload" href="./assets/index-abc.js">'
            '<link rel="stylesheet" href="./assets/index-abc.css">'
            '</head><body><div id="root"></div>'
            '<script type="module" crossorigin src="./assets/index-abc.js"></script>'
            "</body></html>"
        ),
        encoding="utf-8",
    )

    return dist


def inline(tmp_path: Path) -> str:
    done = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert done.returncode == 0, done.stderr

    return (tmp_path / "dist" / "preview.html").read_text(encoding="utf-8")


def test_everything_travels_with_the_document(tmp_path):
    build(tmp_path)

    html = inline(tmp_path)

    # The document is the artifact: no request for a chunk or a stylesheet, and
    # no preload pointing at either.
    assert "assets/" not in html
    assert "<style>body{margin:0}</style>" in html
    assert "console.log(1);" in html


def test_the_policy_is_in_the_document(tmp_path):
    build(tmp_path)

    html = inline(tmp_path)

    assert 'http-equiv="Content-Security-Policy"' in html
    assert "default-src 'none'" in html
    assert "script-src 'unsafe-inline'" in html
    assert "connect-src 'none'" in html
    assert "form-action 'none'" in html
    assert 'name="robots" content="noindex"' in html


def test_the_bridge_is_there_before_the_bundle(tmp_path):
    build(tmp_path)

    html = inline(tmp_path)

    # The theme has to be applied before React paints, so the bridge comes before
    # the inlined bundle and both are in the same document.
    assert "genblocks:preview" in html
    assert html.index("genblocks:preview") < html.index("console.log(1);")


def test_a_script_that_mentions_a_closing_tag_cannot_end_its_own_block(tmp_path):
    build(tmp_path, script='const warning = "</script>";')

    html = inline(tmp_path)

    # The document has exactly the closing tags of the wrapper: the string in the
    # bundle is escaped instead of ending the script element early.
    assert html.count("</script>") == html.count("<script")


def test_a_page_that_points_outside_the_dist_is_refused(tmp_path):
    build(tmp_path, html='<html><head><script src="https://cdn.test/x.js"></script></head></html>')

    done = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert done.returncode != 0
    # Whatever it could not read, it says which reference it was.
    assert "cdn.test" in done.stderr


def test_the_scaffold_command_matches_the_script(tmp_path):
    package = json.loads(
        (Path(__file__).parents[2] / "app/harness/scaffold/package.json").read_text(
            encoding="utf-8"
        )
    )

    # The sandbox runs `npm run preview`; renaming the file without the script
    # would turn every block into a preview-less run.
    assert package["scripts"]["preview"] == "node scripts/inline.mjs"
