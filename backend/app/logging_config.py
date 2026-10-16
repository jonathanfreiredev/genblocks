import logging
import sys

import structlog

from app.settings import settings

# Uvicorn installs its own handlers at startup; route them through our pipeline
# so the whole process emits a single format. Its native access log is dropped
# in favour of the structured one emitted per request (see RequestIdMiddleware).
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")
_UVICORN_ACCESS_LOGGER = "uvicorn.access"


def _shared_processors() -> list:
    """Processors that run for both structlog and stdlib (uvicorn) records."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]


def configure_logging() -> None:
    """Configure structlog on top of the standard library logging.

    Development renders human-readable lines; production renders one JSON
    object per line, ready for any log aggregator. Uvicorn's logs go through the
    same pipeline so there is no second, plain-text format.
    """
    shared = _shared_processors()

    if settings.debug:
        render_processors: list = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        render_processors = [
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=[
            *shared,
            structlog.processors.StackInfoRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=render_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for name in _UVICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(level)

    # Replaced by the structured request log in RequestIdMiddleware.
    access = logging.getLogger(_UVICORN_ACCESS_LOGGER)
    access.handlers = []
    access.propagate = False
