"""The AST scanner that runs inside the sandbox image.

The backend tests do not need Node for the rest of the suite. These tests skip
when it is absent, and otherwise run the real script against a throwaway project
so a rule cannot rot into a regex that only matches its own fixture.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

SCAFFOLD = Path(__file__).parents[2] / "app" / "harness" / "scaffold"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="the AST scanner runs on Node")


def scan(tmp_path: Path, source: str, *, mode: str = "source") -> subprocess.CompletedProcess:
    (tmp_path / "src").mkdir()
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCAFFOLD / "scripts" / "scan.mjs", tmp_path / "scripts" / "scan.mjs")
    (tmp_path / "node_modules").symlink_to(SCAFFOLD / "node_modules", target_is_directory=True)
    (tmp_path / "src" / "Block.tsx").write_text(source)

    return subprocess.run(
        ["node", "scripts/scan.mjs", mode],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_clean_block_passes(tmp_path):
    done = scan(tmp_path, "export function Block() { return <section>Hi</section>; }")

    assert done.returncode == 0, done.stderr
    assert "no AST findings" in done.stdout


def test_a_url_built_at_runtime_is_refused(tmp_path):
    done = scan(tmp_path, "export function Block() { return <img src={makeUrl()} />; }")

    assert done.returncode == 1
    assert "dynamic-url" in done.stderr


def test_an_infinite_loop_is_refused_before_the_render(tmp_path):
    done = scan(tmp_path, "export function Block() { while (true) {} return null; }")

    assert done.returncode == 1
    assert "infinite-loop" in done.stderr


def test_a_network_call_is_refused(tmp_path):
    done = scan(
        tmp_path,
        "export function Block() { fetch('/x'); return null; }",
    )

    assert done.returncode == 1
    assert "network-call" in done.stderr


def test_prose_in_a_comment_is_not_a_call(tmp_path):
    done = scan(
        tmp_path,
        "// fetch('/x') is what a network call would look like\n"
        "export function Block() { return <section>Hi</section>; }",
    )

    assert done.returncode == 0, done.stderr


def test_a_for_loop_with_no_condition_is_refused(tmp_path):
    done = scan(tmp_path, "export function Block() { for (;;) {} return null; }")

    assert done.returncode == 1
    assert "infinite-loop" in done.stderr


def test_the_bundle_finds_an_external_origin(tmp_path):
    (tmp_path / "dist" / "assets").mkdir(parents=True)
    (tmp_path / "node_modules").symlink_to(SCAFFOLD / "node_modules", target_is_directory=True)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCAFFOLD / "scripts" / "scan.mjs", tmp_path / "scripts" / "scan.mjs")
    (tmp_path / "dist" / "assets" / "app.js").write_text(
        'const image = "https://evil.test/collect.png";'
    )

    done = subprocess.run(
        ["node", "scripts/scan.mjs", "bundle"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 1
    assert "external-origin" in done.stderr


def test_the_bundle_finds_an_external_css_origin(tmp_path):
    (tmp_path / "dist" / "assets").mkdir(parents=True)
    (tmp_path / "node_modules").symlink_to(SCAFFOLD / "node_modules", target_is_directory=True)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(SCAFFOLD / "scripts" / "scan.mjs", tmp_path / "scripts" / "scan.mjs")
    (tmp_path / "dist" / "assets" / "app.css").write_text(
        '.hero { background: url("https://evil.test/collect.png"); }'
    )

    done = subprocess.run(
        ["node", "scripts/scan.mjs", "bundle"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 1
    assert "external-origin" in done.stderr
