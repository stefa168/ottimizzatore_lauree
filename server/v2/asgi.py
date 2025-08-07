# from asyncio import Event

from litestar import Litestar, Router
from litestar.datastructures import State
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from v2.config.settings import settings
from v2.config.plugins import alchemy_plugin, structlog_plugin
from v2.domain.grad_sessions.controllers import (
    GraduationSessionController,
    StudentController,
    SessionProfessorController,
    OptimizationConfigurationController
)
from v2.opt_manager import OptimizationWorkersManager
from v2.utils.rabbit_messaging import RabbitMessaging

base_router = Router(
    path="/api/v1",
    route_handlers=[
        GraduationSessionController,
        StudentController,
        SessionProfessorController,
        OptimizationConfigurationController
    ],
)

app = Litestar(
    debug=settings.app.debug,
    dependencies={
        "pika": Provide(RabbitMessaging.provide)
    },
    route_handlers=[base_router],
    cors_config=settings.cors_config,
    plugins=[alchemy_plugin, structlog_plugin],
    openapi_config=OpenAPIConfig(
        title="Graduation Session Optimizer",
        version="0.1",
        render_plugins=[SwaggerRenderPlugin()]
    ),
    lifespan=[
        RabbitMessaging.lifespan,
        OptimizationWorkersManager.lifespan
    ],
    state=State({"settings": settings})
)
