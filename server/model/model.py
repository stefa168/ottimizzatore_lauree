import enum
from dataclasses import dataclass
from typing import List

import sqlalchemy as sqla
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, relationship, registry
from sqlalchemy.types import TypeDecorator, String

mapper_registry = registry()


class StringEnum(TypeDecorator):
    """
    A custom type for SQLAlchemy to store enums as strings in the database,
    while representing them as enum objects in Python.
    """
    impl = String

    def __init__(self, enum_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        """Convert enum object to string before storing in the database."""
        return value.value if value is not None else None

    def process_result_value(self, value, dialect):
        """Convert string back to enum object when loading from the database."""
        return self.enum_type(value) if value is not None else None


class Degree(enum.Enum):
    BACHELORS = "bachelors"
    MASTERS = "masters"


# The annotation is needed to avoid having to declare a boilerplate class...
# https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#declarative-mapping-using-a-decorator-no-declarative-base
@mapper_registry.mapped
@dataclass
class Student:
    __tablename__ = 'students'

    id: int = Column(sqla.Integer, primary_key=True)
    matriculation_number: int = Column(sqla.Integer)
    name: str = Column(sqla.String(128))
    surname: str = Column(sqla.String(128))
    phone_number: str = Column(sqla.String(32))
    personal_email: str = Column(sqla.String(256))
    university_email: str = Column(sqla.String(256))


class UniversityRole(enum.Enum):
    ORDINARY = "ordinary"
    ASSOCIATE = "associate"
    RESEARCHER = "researcher"


@mapper_registry.mapped
@dataclass
class Professor:
    __tablename__ = 'professors'

    id: int = Column(sqla.Integer, primary_key=True)
    name: str = Column(sqla.String(128))
    surname: str = Column(sqla.String(128))
    role: Mapped[UniversityRole] = Column(sqla.Enum(UniversityRole))


@mapper_registry.mapped
@dataclass
class Commission:
    __tablename__ = "commissions"

    id: int = Column(sqla.Integer, primary_key=True)
    title: str = Column(sqla.String(256))
    entries: List['CommissionEntry'] = relationship("CommissionEntry", back_populates="commission")

    def __init__(self, title: str):
        self.title = title
        self.entries = []


@mapper_registry.mapped
@dataclass
class CommissionEntry:
    __tablename__ = "commission_entries"

    id: int = Column(sqla.Integer, primary_key=True)

    commission_id = Column(sqla.Integer, ForeignKey('commissions.id'))
    commission: Commission = relationship("Commission", back_populates="entries")

    candidate_id: int = Column(sqla.Integer, ForeignKey('students.id'))
    candidate: Student = relationship(back_populates="entries")

    degree_level: Degree = Column(sqla.Enum(Degree))

    # Professor-Entry Relationships
    supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'))
    supervisor: Professor = relationship('Professor', foreign_keys='supervisor_id')
    # Co-relatore
    supervisor_assistant_id: int = Column(sqla.Integer, ForeignKey('professors.id'))
    supervisor_assistant: Professor = relationship('Professor', foreign_keys='supervisor_assistant_id')

    counter_supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'))
    counter_supervisor: Professor = relationship('Professor', foreign_keys='counter_supervisor_id')

    def __init__(self, candidate: Student, degree_level: Degree, supervisor: Professor, supervisor_assistant: Professor,
                 counter_supervisor: Professor):
        self.candidate = candidate
        self.degree_level = degree_level
        self.supervisor = supervisor