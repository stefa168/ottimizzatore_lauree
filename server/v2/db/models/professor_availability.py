from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models import Professor, TimeAvailability

if TYPE_CHECKING:
    from .graduation_session import GradSession


@dataclass
class ProfessorAvailability(IdentityAuditBase):
    __tablename__ = "professor_availabilities"

    professor_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("professors.id"), nullable=False)
    professor: Mapped[Professor] = relationship("Professor", lazy="joined")

    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[GradSession] = relationship(
        "GradSession",
        back_populates="availabilities",
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin"
    )

    availability: Mapped[TimeAvailability] = mapped_column(sa.Enum(TimeAvailability), nullable=False)
