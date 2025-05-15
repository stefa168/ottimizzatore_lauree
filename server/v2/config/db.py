from typing import Any

from advanced_alchemy.config import AsyncSessionConfig, AlembicAsyncConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

from litestar.serialization import encode_json, decode_json
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from pydantic import BaseModel, PostgresDsn
from sqlalchemy import NullPool, event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


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

    @property
    def alchemy_plugin(self) -> SQLAlchemyPlugin:
        return SQLAlchemyPlugin(config=SQLAlchemyAsyncConfig(
            engine_instance=self.get_engine(),
            before_send_handler="autocommit",
            session_config=AsyncSessionConfig(expire_on_commit=False),
            alembic_config=AlembicAsyncConfig(
                version_table_name=self.migration_ddl_version_table,
                script_config=self.migration_config,
                script_location=self.migration_path
            )
        ))

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
