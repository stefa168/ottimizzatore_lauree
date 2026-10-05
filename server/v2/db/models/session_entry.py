from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models import Degree, SessionProfessor
from v2.utils.auto_named_enum import auto_named_enum

if TYPE_CHECKING:
    from v2.db.models import Student, GradSession
    from v2.db.models.optimization_configuration import DiscussionDurations


@dataclass
class SessionEntry(IdentityAuditBase):
    __tablename__ = "session_entries"
    __table_args__ = (
        sa.CheckConstraint("bonus_minutes >= 0", name="ck_session_entries_bonus_minutes_non_negative"),
    )

    # Session Foreign Key
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[GradSession] = relationship("GradSession", back_populates="entries", lazy="selectin")

    # Student Foreign Key
    candidate_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("students.id"), nullable=False)
    candidate: Mapped[Student] = relationship(
        "Student",
        foreign_keys=[candidate_id],
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="joined"
    )

    degree_level: Mapped[Degree] = mapped_column(auto_named_enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        ForeignKey('session_professors.id', ondelete="RESTRICT", deferrable=True, initially="DEFERRED"),
        nullable=False)
    supervisor: Mapped[SessionProfessor] = relationship('SessionProfessor', foreign_keys=[supervisor_id])

    supervisor2_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        ForeignKey('session_professors.id', ondelete="RESTRICT", deferrable=True, initially="DEFERRED"),
        nullable=True)
    supervisor2: Mapped[SessionProfessor | None] = relationship('SessionProfessor', foreign_keys=[supervisor2_id])

    supervisor_assistant_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        ForeignKey('session_professors.id', ondelete="RESTRICT", deferrable=True, initially="DEFERRED"),
        nullable=True)
    supervisor_assistant: Mapped[SessionProfessor | None] = relationship(
        'SessionProfessor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        ForeignKey('session_professors.id', ondelete="RESTRICT", deferrable=True, initially="DEFERRED"),
        nullable=True)
    counter_supervisor: Mapped[SessionProfessor | None] = relationship(
        'SessionProfessor', foreign_keys=[counter_supervisor_id])

    # Extra minutes granted to the student for the discussion (e.g. for students entitled to more time)
    bonus_minutes: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default='0')

    @property
    def has_counter_supervisor(self) -> bool:
        return self.counter_supervisor_id is not None

    def get_duration(self, durations: DiscussionDurations) -> int:
        """Length of the discussion in minutes: the configured length for the kind of degree, plus the bonus."""
        if self.degree_level == Degree.BACHELORS:
            base = durations.bachelors
        elif self.has_counter_supervisor:
            base = durations.masters_counter
        else:
            base = durations.masters
        return base + self.bonus_minutes

    def __repr__(self):
        return f"CommissionEntry({self.id=}, {self.session_id=}, {self.candidate.full_name}, {self.degree_level=}, " \
               f"{self.supervisor=} {self.supervisor2=} {self.supervisor_assistant=}, {self.counter_supervisor=})"
