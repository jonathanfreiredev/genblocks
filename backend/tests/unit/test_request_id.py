import re

from app.middleware.request_id import resolve_request_id

_GENERATED_ID = re.compile(r"^[0-9a-f]{32}$")


def test_keeps_a_valid_inbound_id():
    assert resolve_request_id("trace-42") == "trace-42"


def test_trims_a_valid_inbound_id():
    assert resolve_request_id("  trace-42  ") == "trace-42"


def test_generates_an_id_when_missing():
    assert _GENERATED_ID.match(resolve_request_id(None))


def test_generates_an_id_when_blank():
    assert _GENERATED_ID.match(resolve_request_id("   "))


def test_replaces_an_overlong_id():
    assert _GENERATED_ID.match(resolve_request_id("x" * 500))
