from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase, DefaultBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

if TYPE_CHECKING:
    from v2.db.models import GradSession, OptimizationConfiguration, Professor, Student


@dataclass
class SolutionCommissionProfessor(DefaultBase):
    __tablename__ = 'solution_commission_professors'
    solution_commission_id = mapped_column(sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True)
    professor_id = mapped_column(sa.Integer, ForeignKey('professors.id'), primary_key=True)


@dataclass
class SolutionCommissionStudent(DefaultBase):
    __tablename__ = 'solution_commission_students'
    solution_commission_id = mapped_column(sa.Integer, ForeignKey('solution_commissions.id'), primary_key=True)
    student_id = mapped_column(sa.Integer, ForeignKey('students.id'), primary_key=True)


@dataclass
class SolutionCommission(IdentityAuditBase):
    __tablename__ = "solution_commissions"
    __table_args__ = (
        sa.UniqueConstraint('session_id', 'order_key', 'opt_config_id'),
    )

    # The specific commission number of the commission. It is just to have some sort of order, if needed.
    order_key: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    morning: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default='True', default=True)

    # The commission that this solution is for
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[GradSession] = relationship("GradSession", lazy="selectin")

    # The optimization configuration that generated this solution
    opt_config_id = mapped_column(sa.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: Mapped[OptimizationConfiguration] = relationship("OptimizationConfiguration")

    # Originally this class was intended to have a composite primary key, but it is bringing more problems than it
    # solves. So we are going to use a single primary key and just foreign keys to the other tables.
    professors: Mapped[list['Professor']] = relationship("Professor", secondary="solution_commission_professors")
    students: Mapped[list['Student']] = relationship("Student", secondary="solution_commission_students")
