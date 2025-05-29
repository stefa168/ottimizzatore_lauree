# from __future__ import annotations

import os
from pathlib import Path

from litestar import Litestar

from v2.config.settings import Settings
from v2.domain.grad_sessions.controllers import GraduationSessionController


def create_app() -> Litestar:
    settings = Settings.from_yaml(Path(os.getcwd()) / "v2" / "config.yaml")

    app = Litestar(
        debug=True,
        dependencies={
            # "logger": Provide(provide_logger)
        },
        route_handlers=[GraduationSessionController],
        cors_config=settings.cors_config,
        plugins=[
            settings.log.structlog_plugin,
            settings.db.alchemy_plugin
        ],
    )

    return app
