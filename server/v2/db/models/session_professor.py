from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa

from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models.enums import TimeAvailability, SessionProfessorRelation

if TYPE_CHECKING:
    from v2.db.models.graduation_session import GradSession
    from v2.db.models.professor import Professor


@dataclass
class SessionProfessor(IdentityAuditBase):
    __tablename__ = "session_professors"

    # ── Columns ─────────────────────────────────────────────────────────────
    session_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    professor_id: Mapped[int] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey("professors.id", ondelete="CASCADE"),
        nullable=False
    )

    relation: Mapped[SessionProfessorRelation] = mapped_column(
        sa.Enum(SessionProfessorRelation),
        default=SessionProfessorRelation.ORIGINAL,
        nullable=False
    )
    derived_from_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey("session_professors.id", ondelete="CASCADE"),
        nullable=True
    )
    availability: Mapped[TimeAvailability] = mapped_column(
        sa.Enum(TimeAvailability),
        default=TimeAvailability.ALWAYS,
        nullable=False
    )
    user_note: Mapped[str | None] = mapped_column(sa.String(256))
    # is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)

    __table_args__ = (
        # Exactly one ORIGINAL per (session, professor)
        sa.Index(
            "uq_original_prof",
            "session_id", "professor_id",
            unique=True,
            postgresql_where=text("relation = 'ORIGINAL'")
        ),
        # ORIGINAL ⇒ no derived_from_id; others ⇒ must have derived_from_id
        sa.CheckConstraint(
            "(relation = 'ORIGINAL' AND derived_from_id IS NULL) OR "
            "(relation <> 'ORIGINAL' AND derived_from_id IS NOT NULL)",
            name="chk_parent_presence"
        ),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    # 1) Parent pointer (for SPLIT or SUBSTITUTE rows)
    parent: Mapped[SessionProfessor | None] = relationship(
        "SessionProfessor",
        remote_side=lambda: SessionProfessor.id,
        foreign_keys=lambda: SessionProfessor.derived_from_id,
        back_populates="children",
        lazy='selectin'
    )

    # 2) Children collection (all splits & substitutes derived from this row)
    children: Mapped[list[SessionProfessor]] = relationship(
        "SessionProfessor",
        foreign_keys=lambda: SessionProfessor.derived_from_id,
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy='selectin'
    )

    professor: Mapped["Professor"] = relationship(
        "Professor",
        lazy='selectin'
    )
    session: Mapped["GradSession"] = relationship(
        "GradSession",
        back_populates="session_professors_entries",
        lazy='selectin'
    )