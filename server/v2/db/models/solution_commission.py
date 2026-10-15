from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase, DefaultBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from v2.db.models.enums import SessionProfessorRelation, TimeAvailability
from v2.utils.auto_named_enum import auto_named_enum

if TYPE_CHECKING:
    from v2.db.models import GradSession, OptimizationConfiguration, Professor, SessionProfessor, Student


@dataclass
class SolutionCommissionProfessor(DefaultBase):
    """
    A member of a solved commission. It's a snapshot of how the professor sat in the commission when the solution was
    computed, so the solution stays the same even if the session professors (splits, substitutes) change later.
    """
    __tablename__ = 'solution_commission_professors'
    solution_commission_id: Mapped[int] = mapped_column(
        sa.Integer, ForeignKey('solution_commissions.id', ondelete='CASCADE'), primary_key=True)
    # The person: the model never puts two session professors of the same person in a commission
    professor_id: Mapped[int] = mapped_column(sa.Integer, ForeignKey('professors.id'), primary_key=True)
    # The session professor that sat in the commission; null once it's removed (e.g. a split is changed)
    session_professor_id: Mapped[int | None] = mapped_column(
        sa.Integer, ForeignKey('session_professors.id', ondelete='SET NULL'), nullable=True)

    relation: Mapped[SessionProfessorRelation] = mapped_column(
        auto_named_enum(SessionProfessorRelation), nullable=False, default=SessionProfessorRelation.ORIGINAL)
    # 1-based number of the split part (also for the substitute of a part)
    part: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    # The professor replaced by a substitute
    substitute_of_id: Mapped[int | None] = mapped_column(sa.Integer, ForeignKey('professors.id'), nullable=True)
    availability: Mapped[TimeAvailability] = mapped_column(
        auto_named_enum(TimeAvailability), nullable=False, default=TimeAvailability.ALWAYS)

    professor: Mapped[Professor] = relationship("Professor", foreign_keys=[professor_id], lazy="selectin")
    substitute_of: Mapped[Professor | None] = relationship(
        "Professor", foreign_keys=[substitute_of_id], lazy="selectin")

    @classmethod
    def snapshot(cls, sp: SessionProfessor, session_professors: list[SessionProfessor]) -> SolutionCommissionProfessor:
        """The member of a commission for the session professor `sp`, given all the session's professors."""
        by_id = {p.id: p for p in session_professors}

        def part_of(split: SessionProfessor) -> int:
            siblings = sorted(p.id for p in session_professors
                              if p.derived_from_id == split.derived_from_id
                              and p.relation is SessionProfessorRelation.SPLIT)
            return siblings.index(split.id) + 1

        part: int | None = None
        substitute_of_id: int | None = None
        if sp.relation is SessionProfessorRelation.SPLIT:
            part = part_of(sp)
        elif sp.relation is SessionProfessorRelation.SUBSTITUTE:
            parent = by_id.get(sp.derived_from_id)
            if parent is not None and parent.relation is SessionProfessorRelation.SPLIT:
                part = part_of(parent)
                parent = by_id.get(parent.derived_from_id)
            substitute_of_id = parent.professor_id if parent is not None else None

        return cls(
            professor_id=sp.professor_id,
            session_professor_id=sp.id,
            relation=sp.relation,
            part=part,
            substitute_of_id=substitute_of_id,
            availability=sp.availability,
        )

    @property
    def note(self) -> str:
        """How the professor sat in the commission, e.g. "parte 2" or "sostituto di Rossi Mario"."""
        notes = []
        if self.substitute_of is not None:
            notes.append(f"sostituto di {self.substitute_of.full_name}")
        if self.part is not None:
            notes.append(f"parte {self.part}")
        return ", ".join(notes)


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
    duration: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default='0', default=0)
    # Minutes of each student's discussion (by student id) as used by the solver, so the solution keeps them even if
    # the configured lengths or a student's bonus change later
    student_minutes: Mapped[dict[str, int]] = mapped_column(
        sa.JSON, nullable=False, server_default='{}', default=dict)

    # The commission that this solution is for
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[GradSession] = relationship("GradSession", lazy="selectin")

    # The optimization configuration that generated this solution
    opt_config_id = mapped_column(sa.Integer, ForeignKey('optimization_configurations.id'), nullable=False)
    opt_config: Mapped[OptimizationConfiguration] = relationship("OptimizationConfiguration")

    # Originally this class was intended to have a composite primary key, but it was bringing more problems than it
    # solved. So we are going to use a single primary key and just foreign keys to the other tables.
    members: Mapped[list[SolutionCommissionProfessor]] = relationship(
        "SolutionCommissionProfessor", cascade="all, delete-orphan", lazy="selectin")
    students: Mapped[list['Student']] = relationship("Student", secondary="solution_commission_students")

    @property
    def outdated(self) -> bool:
        """Whether some member's session professor was removed after solving (e.g. a split was changed)."""
        return any(m.session_professor_id is None for m in self.members)
