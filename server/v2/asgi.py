import os
from pathlib import Path

from litestar import Litestar, get

from v2.config.settings import Settings


@get("/")
async def hello_world() -> dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    return {"hello": "world"}


def create_app() -> Litestar:
    settings = Settings.from_yaml(Path(os.getcwd()) / "config.yaml")

    app = Litestar(
        route_handlers=[hello_world],
        cors_config=settings.cors_config,
        plugins=[settings.log.structlog_plugin, settings.db.alchemy_plugin],
    )

    return app
