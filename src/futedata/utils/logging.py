"""
Structured logging for FuteData.

Uses structlog for machine-readable JSON logs with human-friendly console output.
Every collector, validator, and pipeline step should use `get_logger(__name__)`.
"""

import logging
import sys

import structlog
from rich.console import Console

from futedata.config import settings

console = Console(stderr=True)

_configured = False


def configure_logging() -> None:
    """Configure structlog + stdlib logging. Call once at application startup."""
    global _configured
    if _configured:
        return

    log_level = getattr(logging, settings.log_level, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=log_level,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
    root_logger.setLevel(log_level)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger bound to the given module name.

    Usage:
        from futedata.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("collecting_data", source="statsbomb", rows=1500)
    """
    configure_logging()
    return structlog.get_logger(name)
