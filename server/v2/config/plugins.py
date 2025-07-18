from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.structlog import StructlogPlugin

from .settings import settings

alchemy_plugin = SQLAlchemyPlugin(config=settings.db.config())
structlog_plugin = StructlogPlugin(config=settings.log.structlog_config())
