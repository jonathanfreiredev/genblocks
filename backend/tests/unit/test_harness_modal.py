"""The sandbox's own fence: what the page is served with and what it may reach."""

from types import SimpleNamespace

import pytest

from app.harness import modal_app


def test_the_page_is_served_with_a_closed_policy():
    policy = modal_app._policy()

    assert "default-src 'none'" in policy
    assert "connect-src 'none'" in policy
    assert "frame-src 'none'" in policy
    assert "object-src 'none'" in policy
    assert "form-action 'none'" in policy
    assert "script-src 'self'" in policy


def test_the_cloudinary_path_is_narrowed_to_the_deployment(monkeypatch):
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "ours")

    assert "https://res.cloudinary.com/ours/" in modal_app._policy()


class Route:
    """The two things a Playwright route does, recorded."""

    def __init__(self, url: str, resource_type: str = "document") -> None:
        self.request = SimpleNamespace(url=url, resource_type=resource_type)
        self.done: str | None = None

    def continue_(self) -> None:
        self.done = "continue"

    def abort(self) -> None:
        self.done = "abort"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://127.0.0.1:4321/assets/app.js", "continue"),
        ("data:image/png;base64,AAAA", "continue"),
        (f"{modal_app._cloudinary_prefix()}image/upload/x.png", "continue"),
        ("https://evil.test/x.png", "abort"),
        ("http://169.254.169.254/latest/meta-data", "abort"),
        ("http://127.0.0.1:9999/other", "abort"),
    ],
)
def test_only_the_project_server_is_reachable(url, expected):
    route = Route(url, "image" if url.startswith("data:") else "document")

    modal_app._only_local(route, 4321)

    assert route.done == expected


def test_a_data_url_cannot_navigate_the_page():
    route = Route("data:text/html,<script>alert(1)</script>", "document")

    modal_app._only_local(route, 4321)

    assert route.done == "abort"


def test_a_project_beyond_the_file_count_never_reaches_the_copier(tmp_path):
    files = [
        {"path": f"src/{index}.tsx", "content": "x"} for index in range(modal_app.MAX_FILES + 1)
    ]

    with pytest.raises(ValueError, match="at most"):
        modal_app._lay_out(tmp_path / "project", files)


def test_the_sandbox_repeats_the_scaffold_ownership_rule(tmp_path):
    with pytest.raises(ValueError, match="scaffold owns"):
        modal_app._lay_out(
            tmp_path / "project",
            [{"path": "src/main.tsx", "content": "alert(1)"}],
        )
