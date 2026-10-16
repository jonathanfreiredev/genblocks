import json
import logging

import pytest
import structlog

from app.logging_config import configure_logging
from app.settings import settings


@pytest.fixture
def preserve_logging():
    """Restore the logging configuration after a test reconfigures it."""
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_config = structlog.get_config()

    yield

    root.handlers = saved_handlers
    root.setLevel(saved_level)
    structlog.configure(**saved_config)


def test_production_logs_are_json(monkeypatch, capsys, preserve_logging):
    monkeypatch.setattr(settings, "env", "production")
    configure_logging()

    structlog.get_logger("app.test_logging").info("user_provisioned", user_id="u1")

    lines = capsys.readouterr().out.strip().splitlines()
    payload = json.loads(lines[-1])

    assert payload["event"] == "user_provisioned"
    assert payload["user_id"] == "u1"
    assert payload["level"] == "info"
