from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa

from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models.enums import TimeAvailability, SessionProfessorRelation
from v2.utils.auto_named_enum import auto_named_enum

if TYPE_CHECKING:
    from v2.db.models.graduation_session import GradSession
    from v2.db.models.professor import Professor


@dataclass(eq=False)
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
        auto_named_enum(SessionProfessorRelation),
        default=SessionProfessorRelation.ORIGINAL,
        nullable=False
    )
    derived_from_id: Mapped[int | None] = mapped_column(
        sa.BigInteger,
        sa.ForeignKey("session_professors.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    availability: Mapped[TimeAvailability] = mapped_column(
        auto_named_enum(TimeAvailability),
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
        back_populates="_children",
        lazy='selectin'
    )

    # 2) Children collection (all splits & substitutes derived from this row)
    _children: Mapped[list[SessionProfessor]] = relationship(
        "SessionProfessor",
        foreign_keys=lambda: SessionProfessor.derived_from_id,
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy='selectin'
    )

    @property
    async def children(self):
        # noinspection PyProtectedMember
        return await self.awaitable_attrs._children

    # Using trigger `trg_session_professors_guard_split` we're also ensuring that:
    # - the split professor tree has only one level (no split of a split)
    # - no substitute can be split
    # - there cannot be a substitute of a substitute

    professor: Mapped["Professor"] = relationship(
        "Professor",
        lazy='selectin'
    )
    session: Mapped["GradSession"] = relationship(
        "GradSession",
        back_populates="session_professors_entries",
        lazy='selectin'
    )

    async def collect_descendants_ids(self) -> dict[int, SessionProfessorRelation]:
        collected: dict[int, SessionProfessorRelation] = {self.id: self.relation}
        children: list[SessionProfessor] = await self.children
        stack = list(children)  # start with direct children
        while stack:
            node = stack.pop()
            if node.id not in collected:
                collected[node.id] = node.relation
                stack.extend(await node.children)
        return collected

    def __repr__(self):
        return f"SessionProfessor({self.id}, {self.session_id}, {self.professor}, {self.availability}, {self.relation}, {self.derived_from_id})"

    def __hash__(self) -> int:
        # Hash based on the primary key once persisted
        if getattr(self, "id", None) is None:
            # Unpersisted instances are not hashable to avoid duplicates in sets/dicts
            raise TypeError("SessionProfessor is not hashable until persisted")
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionProfessor):
            return NotImplemented
        if getattr(self, "id", None) is None or getattr(other, "id", None) is None:
            return False
        return self.id == other.id
