from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from v2.db.models import GradSession, OptimizationLog, SolutionCommission

from v2.db.models.enums import SolverEnum


@dataclass
class OptimizationConfiguration(IdentityAuditBase):
    __tablename__ = "optimization_configurations"

    title: Mapped[str] = mapped_column(
        sa.String(256),
        nullable=False,
        server_default="Nuova configurazione",
        default="Nuova configurazione")

    # Session Foreign Key
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped['GradSession'] = relationship("GradSession", back_populates="configurations", lazy="selectin")

    max_duration: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='210', default=210)
    max_commissions_morning: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)
    max_commissions_afternoon: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='6', default=6)

    online: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='True', default=True)
    min_professor_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    min_professor_number_masters: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    max_professor_numer: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    solver: Mapped[SolverEnum] = mapped_column(
        sa.Enum(SolverEnum),
        nullable=False,
        default=SolverEnum.CPLEX,
        server_default=SolverEnum.CPLEX.value)

    optimization_time_limit: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='60', default=60)
    optimization_gap: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default='0.005', default=0.005)
    run_lock: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='False', default=False)

    optimization_log: Mapped[OptimizationLog] = relationship(
        "OptimizationLog",
        back_populates="opt_config",
        cascade="all, delete-orphan"
    )

    commissions: Mapped[list['SolutionCommission']] = relationship(
        "SolutionCommission",
        back_populates="opt_config",
        cascade="all, delete-orphan"
    )
