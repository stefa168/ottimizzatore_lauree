import binascii
import logging
import os
import sys
from functools import lru_cache
from typing import Any

import structlog
from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.serialization import decode_json, encode_json
from litestar.plugins.sqlalchemy import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
    AsyncSessionConfig,
    AlembicAsyncConfig
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from pydantic import BaseModel, PostgresDsn, Field
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool
from advanced_alchemy.utils.text import slugify


@get("/")
async def hello_world() -> dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    return {"hello": "world"}


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    keepalive: int = 65
    reload: bool = False
    reload_dirs: list[str] = ["app"]


class AppSettings(BaseModel):
    # app_loc: str = "v2.asgi:create_app"
    url: str = "http://localhost:8000"
    debug: bool = False
    secret_key: str = Field(default_factory=lambda: binascii.hexlify(os.urandom(32)).decode(encoding="utf-8"))
    name: str = "app"
    allowed_cors_origins: list[str] = ["*"]

    # csrf_cookie_name: str = "XSRF-TOKEN"
    # csrf_cookie_secure: bool = False

    @property
    def slug(self) -> str:
        """Return a slugified name."""
        return slugify(self.name)


class DatabaseSettings(BaseModel):
    echo: bool = False
    """Enable SQLAlchemy engine logs."""
    echo_pool: bool = False
    """Enable SQLAlchemy connection pool logs."""
    pool_disabled: bool = False
    """Disable SQLAlchemy pool configuration."""
    pool_max_overflow: int = 10
    """Max overflow for SQLAlchemy connection pool"""
    pool_size: int = 5
    """Pool size for SQLAlchemy connection pool"""
    pool_timeout: int = 30
    """Time in seconds for timing connections out of the connection pool."""
    pool_recycle: int = 300
    """Amount of time to wait before recycling connections."""
    pool_pre_ping: bool = False
    """Optionally ping database before fetching a session from the connection pool."""
    url: PostgresDsn
    """SQLAlchemy Database URL."""
    migration_config: str = "db/migrations/alembic.ini"
    """The path to the `alembic.ini` configuration file."""
    migration_path: str = "db/migrations"
    """The path to the `alembic` database migrations."""
    migration_ddl_version_table: str = "ddl_version"
    """The name to use for the `alembic` versions table name."""
    fixture_path: str = "db/fixtures"
    """The path to JSON fixture files to load into tables."""
    _engine_instance: AsyncEngine | None = None
    """SQLAlchemy engine instance generated from settings."""

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        """Database session factory.

        See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
        """
        if self._engine_instance is not None:
            return self._engine_instance

        engine = create_async_engine(
            url=self.url.encoded_string(),
            json_serializer=encode_json,
            json_deserializer=decode_json,
            echo=self.echo,
            echo_pool=self.echo_pool,
            max_overflow=self.pool_max_overflow,
            pool_size=self.pool_size,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            pool_use_lifo=True,  # use LIFO to reduce the number of idle connections
            poolclass=NullPool if self.pool_disabled else None,
        )

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:  # pragma: no cover
            """Using msgspec for serialization of the json column values means that the
            output is binary, not `str` like `json.dumps` would output.
            SQLAlchemy expects that the json serializer returns `str` and calls `.encode()` on the value to
            turn it to bytes before writing to the JSONB column. I'd need to either wrap `serialization.to_json` to
            return a `str` so that SQLAlchemy could then convert it to binary, or do the following, which
            changes the behaviour of the dialect to expect a binary value from the serializer.
            """

            def encoder(bin_value: bytes) -> bytes:
                return b"\x01" + encode_json(bin_value)

            def decoder(bin_value: bytes) -> Any:
                return decode_json(bin_value[1:])

            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "jsonb",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )
            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "json",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )

        self._engine_instance = engine

        return self._engine_instance


def sql_config_factory(settings: DatabaseSettings) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        engine_instance=settings.get_engine(),
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
        alembic_config=AlembicAsyncConfig(
            version_table_name=settings.migration_ddl_version_table,
            script_config=settings.migration_config,
            script_location=settings.migration_path
        )
    )


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


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


def logging_config_factory(settings: LogSettings) -> StructlogConfig:
    _render_as_json = not _is_tty()
    _structlog_default_processors = default_structlog_processors(as_json=_render_as_json)
    _structlog_default_processors.insert(1, structlog.processors.EventRenamer("message"))
    _structlog_standard_lib_processors = default_structlog_standard_lib_processors(as_json=_render_as_json)
    _structlog_standard_lib_processors.insert(1, structlog.processors.EventRenamer("message"))

    return StructlogConfig(
        structlog_logging_config=StructLoggingConfig(
            log_exceptions="always",
            processors=_structlog_default_processors,
            logger_factory=default_logger_factory(as_json=_render_as_json),
            standard_lib_logging_config=LoggingConfig(
                root={"level": logging.getLevelName(settings.level), "handlers": ["queue_listener"]},
                formatters={
                    "standard": {
                        "()": structlog.stdlib.ProcessorFormatter,
                        "processors": _structlog_standard_lib_processors,
                    },
                },
                loggers={
                    "sqlalchemy.engine": {
                        "propagate": False,
                        "level": settings.sqlalchemy_level,
                        "handlers": ["queue_listener"],
                    },
                    "sqlalchemy.pool": {
                        "propagate": False,
                        "level": settings.sqlalchemy_level,
                        "handlers": ["queue_listener"],
                    },
                },
            ),
        ),
        middleware_logging_config=LoggingMiddlewareConfig(
            request_log_fields=settings.request_fields,
            response_log_fields=settings.response_fields,
        ),
    )


def create_app() -> Litestar:
    # settings = load_settings(settings_path)

    db_settings = DatabaseSettings(url=PostgresDsn("postgresql+psycopg://user:password@localhost:5432/postgres"))
    log_settings = LogSettings()

    structlog_plugin = StructlogPlugin(config=logging_config_factory(log_settings))

    alchemy_plugin = SQLAlchemyPlugin(config=sql_config_factory(db_settings))

    app_settings = AppSettings()
    cors_config = CORSConfig(allow_origins=app_settings.allowed_cors_origins)

    app = Litestar(
        route_handlers=[hello_world],
        cors_config=cors_config,
        plugins=[structlog_plugin, alchemy_plugin],
    )

    return app
