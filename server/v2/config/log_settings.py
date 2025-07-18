import enum
import logging
import sys
from functools import lru_cache

import structlog
from litestar.logging import StructLoggingConfig, LoggingConfig
from litestar.logging.config import (
    default_structlog_processors,
    default_structlog_standard_lib_processors,
    default_logger_factory
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin

from pydantic import BaseModel
from structlog.processors import CallsiteParameter
from structlog.typing import EventDict


class LoggingLevel(enum.Enum):
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class LogSettings(BaseModel):
    """Logger configuration"""

    exclude_paths: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""

    http_event: str = "HTTP"
    """Log event name for logs from Litestar handlers."""

    include_compressed_body: bool = False
    """Include 'body' of compressed responses in log output."""

    level: LoggingLevel = LoggingLevel.INFO
    """Stdlib log levels. Only emit logs at this level, or higher."""

    obfuscate_cookies: set[str] = {"session", "XSRF-TOKEN"}
    """Request cookie keys to obfuscate."""

    obfuscate_headers: set[str] = {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"}
    """Request header keys to obfuscate."""

    job_fields: list[str] = [
        "function",
        "kwargs",
        "key",
        "scheduled",
        "attempts",
        "completed",
        "queued",
        "started",
        "result",
        "error",
    ]
    """Attributes of the SAQ Job to be logged."""

    request_fields: list[str] = [
        "path",
        "method",
        "query",
        "path_params",
    ]
    """Attributes of the Request to be logged."""

    response_fields: list[str] = ["status_code"]
    """Attributes of the Response to be logged."""

    worker_event: str = "Worker"
    """Log event name for logs from SAQ worker."""

    pyomo_level: LoggingLevel = LoggingLevel.CRITICAL
    """Level to log Pyomo logs."""

    sqlalchemy_level: LoggingLevel = LoggingLevel.WARNING
    """Level to log SQLAlchemy logs."""

    asgi_access_level: LoggingLevel = LoggingLevel.WARNING
    """Level to log uvicorn access logs."""

    asgi_error_level: LoggingLevel = LoggingLevel.WARNING
    """Level to log uvicorn error logs."""

    watchdog_level: LoggingLevel = LoggingLevel.WARNING
    """Level to log watchdog logs."""

    def structlog_config(self) -> StructlogConfig:
        render_as_json = not _is_tty()

        cpa = structlog.processors.CallsiteParameterAdder({})

        processors = [
            cpa,
            structlog.processors.EventRenamer("message"),
            *default_structlog_processors(as_json=render_as_json)
        ]

        stdlib_processors = [
            cpa,
            structlog.processors.EventRenamer("message"),
            *default_structlog_standard_lib_processors(as_json=render_as_json)
        ]

        return StructlogConfig(
            structlog_logging_config=StructLoggingConfig(
                log_exceptions="always",
                processors=processors,
                logger_factory=default_logger_factory(as_json=render_as_json),
                standard_lib_logging_config=LoggingConfig(
                    root={"level": self.level.value, "handlers": ["queue_listener"]},
                    formatters={
                        "standard": {
                            "()": structlog.stdlib.ProcessorFormatter,
                            "processors": stdlib_processors,
                        },
                    },
                    loggers={
                        "sqlalchemy.engine": {
                            "propagate": False,
                            "level": self.sqlalchemy_level.value,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.pool": {
                            "propagate": False,
                            "level": self.sqlalchemy_level.value,
                            "handlers": ["queue_listener"],
                        },
                        "pyomo.core": {
                            "propagate": False,
                            "level": self.pyomo_level.value,
                            "handlers": ["queue_listener"],
                        },
                        "watchdog": {
                            "propagate": False,
                            "level": self.watchdog_level.value,
                            "handlers": ["queue_listener"],
                        },
                        "watchdog.observers": {
                            "propagate": False,
                            "level": self.watchdog_level.value,
                            "handlers": ["queue_listener"],
                        },
                        "watchdog.observers.inotify_buffer": {
                            "propagate": False,
                            "level": self.watchdog_level.value,
                            "handlers": ["queue_listener"],
                        }

                    },
                ),
            ),
            middleware_logging_config=LoggingMiddlewareConfig(
                request_log_fields=self.request_fields,
                response_log_fields=self.response_fields,
            ),
        )


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())
