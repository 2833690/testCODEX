from __future__ import annotations

import logging
import sys

import structlog


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)


def get_logger(name: str):
    return structlog.get_logger(name)
