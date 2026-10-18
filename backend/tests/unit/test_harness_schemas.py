"""What the sandbox's answer means, read without a sandbox.

The two things that matter here are which findings stop a run and which are kept
as evidence: a check that fails for a wide hero at 390px is worth knowing and not
worth refusing, and getting that backwards would either publish broken blocks or
throw away good ones.
"""

from app.harness.schemas import SandboxCheck, SandboxResult, SandboxViolation


def result(*checks: tuple[str, bool]) -> SandboxResult:
    return SandboxResult(checks=[SandboxCheck(name=name, ok=ok) for name, ok in checks])


def test_a_fatal_check_that_failed_stops_the_run():
    found = result(("typecheck", True), ("build", False), ("lint", True))

    assert found.blocked is True
    assert found.record()["blocked"] is True
    assert [check.name for check in found.failures] == ["build"]


def test_findings_that_are_not_fatal_do_not_stop_the_run():
    # A block that is 40px too wide on a phone is a judgement call, and the phase
    # that judges has not run yet.
    found = result(("typecheck", True), ("build", True), ("layout:phone", False))

    assert found.blocked is False
    assert [check.name for check in found.failures] == ["layout:phone"]


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

    # The failing check is not fatal, so the run was not blocked: the record says
    # both things, and nothing reading it later has to know which checks are.
    assert record["blocked"] is False
    assert (record["passed"], record["total"]) == (2, 3)
    assert record["checks"][2]["detail"] == "color-contrast (serious, 2 nodes)"
    assert record["violations"][0]["id"] == "color-contrast"
    # The picture is not in the record: it is uploaded, and the public id is what
    # points at it.
    assert "screenshot" not in record
