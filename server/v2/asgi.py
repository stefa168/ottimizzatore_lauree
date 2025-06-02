# from __future__ import annotations

import os
from pathlib import Path

from litestar import Litestar, Router
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from v2.config.settings import Settings
from v2.domain.grad_sessions.controllers import GraduationSessionController

base_router = Router(
    path="/api/v1",
    route_handlers=[GraduationSessionController],
)


def create_app() -> Litestar:
    settings = Settings.from_yaml(Path(os.getcwd()) / "v2" / "config.yaml")

    app = Litestar(
        debug=True,
        dependencies={
            # "logger": Provide(provide_logger)
        },
        route_handlers=[base_router],
        cors_config=settings.cors_config,
        plugins=[
            settings.log.structlog_plugin,
            settings.db.alchemy_plugin
        ],
        openapi_config=OpenAPIConfig(
            title="Graduation Session Optimizer",
            version="0.1",
            render_plugins=[SwaggerRenderPlugin()]
        )
    )

    return app
