"""What the sandbox's answer means, read without a sandbox.

The thing that matters here is which findings stop a run and which are kept as
evidence. The interface checks are gates: a block that overflows a phone, fails
contrast or ignores reduced motion is not published, because the judge never sees
the phone and the registry promised it works. Lint stays evidence — it is a
nitpick, not a broken interface.
"""

from app.harness.schemas import SandboxCheck, SandboxResult, SandboxViolation


def result(*checks: tuple[str, bool]) -> SandboxResult:
    return SandboxResult(checks=[SandboxCheck(name=name, ok=ok) for name, ok in checks])


def test_a_fatal_check_that_failed_stops_the_run():
    found = result(("typecheck", True), ("build", False), ("lint", True))

    assert found.blocked is True
    assert found.record()["blocked"] is True
    assert [check.name for check in found.failures] == ["build"]


def test_a_lint_finding_does_not_stop_the_run():
    # A lint nitpick is worth knowing and not worth refusing a whole block over.
    found = result(("typecheck", True), ("build", True), ("lint", False))

    assert found.blocked is False
    assert [check.name for check in found.failures] == ["lint"]


def test_a_layout_that_overflows_a_phone_stops_the_run():
    # The judge is not sent the phone render, so this cannot be left to taste.
    found = result(("typecheck", True), ("build", True), ("layout:phone", False))

    assert found.blocked is True


def test_interface_findings_stop_the_run():
    for name in ("accessibility", "accessibility:dark", "targets", "focus", "motion:reduce"):
        found = result((name, False))

        assert found.blocked is True, name


def test_an_import_outside_the_shelf_stops_the_run():
    # It would build — the package is installed in the sandbox — and the person
    # copying the block could not install it. That is the one thing the shelf
    # check is for.
    found = result(("imports", False), ("typecheck", True), ("build", True), ("render", True))

    assert found.blocked is True


def test_a_run_where_everything_passed_is_not_blocked():
    assert result(("typecheck", True), ("render", True)).blocked is False


def test_the_record_carries_the_checks_and_the_findings():
    found = SandboxResult(
        checks=[
            SandboxCheck(name="typecheck", ok=True),
            SandboxCheck(name="build", ok=True),
            SandboxCheck(
                name="accessibility", ok=False, detail="color-contrast (serious, 2 nodes)"
            ),
        ],
        violations=[
            SandboxViolation(
                id="color-contrast", impact="serious", help="Elements must meet contrast", nodes=2
            )
        ],
        screenshot=b"\x89PNG",
    )

    record = found.record()

    # A serious contrast finding is fatal, so the run was blocked: the record
    # says both things, and nothing reading it later has to know which checks are.
    assert record["blocked"] is True
    assert (record["passed"], record["total"]) == (2, 3)
    assert record["checks"][2]["detail"] == "color-contrast (serious, 2 nodes)"
    assert record["violations"][0]["id"] == "color-contrast"
    # The picture is not in the record: it is uploaded, and the public id is what
    # points at it.
    assert "screenshot" not in record


def test_the_dependencies_are_what_the_project_asked_for():
    found = SandboxResult(
        checks=[SandboxCheck(name="imports", ok=True)],
        dependencies={"motion": "^13.0.0", "react": "^19.2.4"},
    )

    assert found.dependencies == {"motion": "^13.0.0", "react": "^19.2.4"}
    assert found.blocked is False


def test_the_report_names_every_check_and_the_findings():
    found = SandboxResult(
        checks=[
            SandboxCheck(name="typecheck", ok=True),
            SandboxCheck(name="layout:phone", ok=False, detail="40px wider."),
        ],
        violations=[
            SandboxViolation(id="color-contrast", impact="serious", help="Contrast.", nodes=2)
        ],
    )

    said = found.report()

    assert "- typecheck: ok" in said
    assert "- layout:phone: failed — 40px wider." in said
    assert "- axe color-contrast (serious, 2 nodes): Contrast." in said
