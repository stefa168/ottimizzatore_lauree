from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.utils.auto_named_enum import auto_named_enum

if TYPE_CHECKING:
    from v2.db.models import OptimizationConfiguration


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class OptimizationJob(IdentityAuditBase):
    """
    A request to solve an optimization configuration, consumed by the optimization workers.

    Workers claim jobs with ``SELECT ... FOR UPDATE SKIP LOCKED`` so each job is processed by a single worker.
    Running jobs are kept alive with a heartbeat; jobs whose heartbeat goes stale are re-queued.
    """
    __tablename__ = "optimization_jobs"
    __table_args__ = (
        # A configuration can have at most one job waiting or running at any time.
        Index(
            "uq_optimization_jobs_active_config",
            "opt_config_id",
            unique=True,
            postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        ),
        Index("ix_optimization_jobs_status_available_at", "status", "available_at"),
    )

    opt_config_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        ForeignKey("optimization_configurations.id", ondelete="CASCADE"),
        nullable=False
    )
    opt_config: Mapped['OptimizationConfiguration'] = relationship("OptimizationConfiguration", lazy="noload")

    status: Mapped[JobStatus] = mapped_column(
        auto_named_enum(JobStatus),
        nullable=False,
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value)

    attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default='0')
    max_attempts: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=3, server_default='3')

    available_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    locked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    worker: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    last_error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
