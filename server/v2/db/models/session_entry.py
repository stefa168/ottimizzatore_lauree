from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models import Degree

if TYPE_CHECKING:
    from v2.db.models import Student, Professor, GradSession


@dataclass
class SessionEntry(IdentityAuditBase):
    __tablename__ = "session_entries"

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

    degree_level: Mapped[Degree] = mapped_column(sa.Enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=False)
    supervisor: Mapped[Professor] = relationship('Professor', foreign_keys=[supervisor_id])

    supervisor2_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=True)
    supervisor2: Mapped[Professor | None] = relationship('Professor', foreign_keys=[supervisor2_id])

    supervisor_assistant_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'),
                                                                nullable=True)
    supervisor_assistant: Mapped[Professor | None] = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Mapped[Professor | None] = relationship('Professor', foreign_keys=[counter_supervisor_id])

    def get_duration(self) -> int:
        return 15 if self.degree_level == Degree.BACHELORS else 20 if self.counter_supervisor is None else 30

    def __repr__(self):
        return f"CommissionEntry({self.id=}, {self.session_id=}, {self.candidate=}, {self.degree_level=}, " \
               f"{self.supervisor=} {self.supervisor2=} {self.supervisor_assistant=}, {self.counter_supervisor=})"
