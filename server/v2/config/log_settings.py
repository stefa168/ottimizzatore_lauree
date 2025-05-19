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


class LogSettings(BaseModel):
    """Logger configuration"""

    exclude_paths: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""

    http_event: str = "HTTP"
    """Log event name for logs from Litestar handlers."""

    include_compressed_body: bool = False
    """Include 'body' of compressed responses in log output."""

    level: int = 30
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

    saq_level: int = 50
    """Level to log SAQ logs."""

    sqlalchemy_level: int = 30
    """Level to log SQLAlchemy logs."""

    asgi_access_level: int = 30
    """Level to log uvicorn access logs."""

    asgi_error_level: int = 30
    """Level to log uvicorn error logs."""

    @property
    def structlog_plugin(self) -> StructlogPlugin:
        _render_as_json = not _is_tty()
        _structlog_default_processors = default_structlog_processors(as_json=_render_as_json)
        _structlog_default_processors.insert(1, structlog.processors.EventRenamer("message"))
        _structlog_standard_lib_processors = default_structlog_standard_lib_processors(as_json=_render_as_json)
        _structlog_standard_lib_processors.insert(1, structlog.processors.EventRenamer("message"))

        return StructlogPlugin(config=StructlogConfig(
            structlog_logging_config=StructLoggingConfig(
                log_exceptions="always",
                processors=_structlog_default_processors,
                logger_factory=default_logger_factory(as_json=_render_as_json),
                standard_lib_logging_config=LoggingConfig(
                    root={"level": logging.getLevelName(self.level), "handlers": ["queue_listener"]},
                    formatters={
                        "standard": {
                            "()": structlog.stdlib.ProcessorFormatter,
                            "processors": _structlog_standard_lib_processors,
                        },
                    },
                    loggers={
                        "sqlalchemy.engine": {
                            "propagate": False,
                            "level": self.sqlalchemy_level,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.pool": {
                            "propagate": False,
                            "level": self.sqlalchemy_level,
                            "handlers": ["queue_listener"],
                        },
                    },
                ),
            ),
            middleware_logging_config=LoggingMiddlewareConfig(
                request_log_fields=self.request_fields,
                response_log_fields=self.response_fields,
            ),
        ))


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())
