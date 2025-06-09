from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy.orm import Mapped, mapped_column

from .enums import UniversityRole


@dataclass
class Professor(IdentityAuditBase):
    """
    Professor model with auto-incrementing ID and audit fields.

    Attributes:
        first_name: The first name of the professor.
        surname: The surname of the professor.
        role: The professor's role in the university. By default, this is set to "UNSPECIFIED".
    """
    __tablename__ = "professors"

    __table_args__ = (
        sa.Index("idx_professors_name_surname_unique", "first_name", "surname", unique=True),
    )

    first_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    surname: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    role: Mapped[UniversityRole] = mapped_column(sa.Enum(UniversityRole),
                                                 nullable=False,
                                                 default=UniversityRole.UNSPECIFIED,
                                                 server_default="UNSPECIFIED")

    @property
    def full_name(self):
        return f"{self.surname} {self.first_name}"

    def __repr__(self):
        return f"Professor({self.id=}, {self.first_name=}, {self.surname=}, {self.role=})"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Professor) and self.id == other.id
