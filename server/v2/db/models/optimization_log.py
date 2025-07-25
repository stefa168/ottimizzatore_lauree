from dataclasses import dataclass
from datetime import datetime

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

    start_time = mapped_column(sa.DateTime(timezone=True), nullable=False)
    end_time = mapped_column(sa.DateTime(timezone=True), nullable=True)

    success: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    solver_reached_optimality: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    solver_time_limit_reached: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)
    error_message = mapped_column(sa.String(256), nullable=True)
    log = mapped_column(sa.Text, nullable=True)

    def started(self):
        self.start_time = datetime.now()

    def finished(self, ok: bool, optimality_reached: bool, time_limit_reached: bool):
        self.end_time = datetime.now()
        self.success = ok
        self.solver_reached_optimality = optimality_reached
        self.solver_time_limit_reached = time_limit_reached
