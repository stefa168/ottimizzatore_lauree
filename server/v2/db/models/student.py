from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy.orm import Mapped, mapped_column
from litestar.dto import dto_field


@dataclass
class Student(IdentityAuditBase):
    """
    Student model with auto-incrementing ID and audit fields.

    Attributes:
        matriculation_number: A unique number assigned to the student by the university.
        first_name: The first name of the student.
        surname: The surname of the student.
        phone_number: The student's phone number. This is optional.
        personal_email: The student's personal email address. This is optional.
        university_email: The student's university email address. This is optional.
    """
    __tablename__ = "students"

    matriculation_number: Mapped[int] = mapped_column(sa.BigInteger, unique=False, nullable=False)
    first_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    surname: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(sa.String(128), nullable=False, info=dto_field("private"))
    personal_email: Mapped[str | None] = mapped_column(sa.String(128), nullable=False, info=dto_field("private"))
    university_email: Mapped[str | None] = mapped_column(sa.String(128), nullable=False)

    @property
    def full_name(self):
        return f"{self.surname} {self.first_name}"

    def __repr__(self):
        return f"Student({self.id=}, {self.matriculation_number=}, {self.first_name=}, {self.surname=}, " \
               f"{self.phone_number=}, {self.personal_email=}, {self.university_email=})"
