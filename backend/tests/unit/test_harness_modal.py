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


def test_the_source_and_bundle_scans_are_gates():
    assert {"ast", "bundle"} <= set(modal_app.GATES)


def test_every_width_a_block_is_measured_at_is_declared():
    names = {viewport["name"] for viewport in modal_app.VIEWPORTS}

    # The judge is not sent the phone, so the gate is what sees it.
    assert names == {"phone", "tablet", "laptop", "desktop"}
    assert modal_app.KEPT_VIEWPORT in names


def test_motion_evidence_says_what_moved():
    assert modal_app._motion_summary([]) == "no animation"

    said = modal_app._motion_summary(
        [
            {"state": "finished", "duration": 420, "iterations": 1},
            {"state": "running", "duration": 900, "iterations": "infinite"},
        ]
    )

    assert "2 animation(s)" in said
    assert "longest 900ms" in said
    assert "1 repeating" in said


def test_only_motion_still_running_after_the_bound_is_flagged():
    animations = [
        {"state": "finished", "duration": 800, "iterations": 1},
        {"state": "paused", "duration": 100, "iterations": "infinite"},
        {"state": "running", "duration": 600, "iterations": 1},
        {"state": "running", "duration": 120, "iterations": "infinite"},
    ]

    flagged = modal_app._long_motion(animations)

    assert [one["duration"] for one in flagged] == [600, 120]


def test_a_short_block_is_captured_whole_for_the_card():
    clip = modal_app._thumbnail_clip({"x": 0, "y": 0, "width": 390, "height": 340})

    assert clip == {"x": 0, "y": 0, "width": 390, "height": 340}


def test_a_tall_block_is_cut_at_card_height():
    clip = modal_app._thumbnail_clip({"x": 0, "y": 0, "width": 390, "height": 844})

    assert clip == {"x": 0, "y": 0, "width": 390, "height": 390}


def test_a_narrower_block_keeps_its_own_width():
    clip = modal_app._thumbnail_clip({"x": 12, "y": 4, "width": 320, "height": 600})

    assert clip == {"x": 12, "y": 4, "width": 320, "height": 390}


def test_a_box_with_nothing_to_photograph_has_no_clip():
    assert modal_app._thumbnail_clip({"x": 0, "y": 0, "width": 0, "height": 0}) is None
