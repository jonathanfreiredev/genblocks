from app.db.models import utcnow


def test_utcnow_is_truncated_to_whole_seconds():
    # JWT `iat`/`exp` have second precision, so we keep timestamps on the same grid.
    assert utcnow().microsecond == 0
