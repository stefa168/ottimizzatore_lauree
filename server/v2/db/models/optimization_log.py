from dataclasses import dataclass

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from v2.db.models import OptimizationConfiguration


@dataclass
class OptimizationLog(IdentityAuditBase):
    __tablename__ = "optimization_logs"

    opt_config_id = mapped_column(sa.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: Mapped[OptimizationConfiguration] = relationship("OptimizationConfiguration")

    # todo add all the other variables...
