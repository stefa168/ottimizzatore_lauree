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
    _tablename = 'students'
    # _id_seq = sqla.Sequence(_tablename + "_id_seq")

    __table__ = sqla.Table(
        _tablename,
        mapper_registry.metadata,
        Column("id", sqla.Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("matriculation_number", sqla.Integer, nullable=False),
        Column("name", sqla.String(128), nullable=False),
        Column("surname", sqla.String(128), nullable=False),
        Column("phone_number", sqla.String(32), nullable=False),
        Column("personal_email", sqla.String(256), nullable=False),
        Column("university_email", sqla.String(256), nullable=False)
    )

    id: int
    matriculation_number: int
    name: str
    surname: str
    phone_number: str
    personal_email: str
    university_email: str

    def __init__(self, matriculation_number: int, name: str, surname: str, phone_number: str, personal_email: str,
                 university_email: str):
        self.matriculation_number = matriculation_number
        self.name = name
        self.surname = surname
        self.phone_number = phone_number
        self.personal_email = personal_email
        self.university_email = university_email

    def serialize(self):
        return {
            'id': self.id,
            'matriculation_number': self.matriculation_number,
            'name': self.name,
            'surname': self.surname,
            'phone_number': self.phone_number,
            'personal_email': self.personal_email,
            'university_email': self.university_email
        }


class UniversityRole(enum.Enum):
    ORDINARY = "ordinary"
    ASSOCIATE = "associate"
    RESEARCHER = "researcher"
    UNSPECIFIED = "unspecified"


@mapper_registry.mapped
@dataclass
class Professor:
    __tablename__ = 'professors'

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)
    name: str = Column(sqla.String(128), nullable=False)
    surname: str = Column(sqla.String(128), nullable=False)
    role: UniversityRole = Column(sqla.Enum(UniversityRole), nullable=False, default=UniversityRole.UNSPECIFIED)

    def __init__(self, name: str, surname: str, role: UniversityRole = UniversityRole.UNSPECIFIED):
        self.name = name
        self.surname = surname
        self.role = role

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'role': self.role.value
        }


@mapper_registry.mapped
@dataclass
class Commission:
    __tablename__ = "commissions"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)
    title: str = Column(sqla.String(256), nullable=False)
    entries: List['CommissionEntry'] = relationship(
        "CommissionEntry",
        back_populates="commission",
        cascade="all, delete-orphan"
    )

    def __init__(self, title: str):
        self.title = title
        self.entries = []

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'entries': [entry.serialize() for entry in self.entries]
        }


@mapper_registry.mapped
@dataclass
class CommissionEntry:
    __tablename__ = "commission_entries"

    id: int = Column(sqla.Integer, primary_key=True, autoincrement=True, nullable=False)

    commission_id = Column(sqla.Integer, ForeignKey('commissions.id'), nullable=False)
    commission: Commission = relationship("Commission", back_populates="entries")

    candidate_id: int = Column(sqla.Integer, ForeignKey('students.id'), nullable=False)
    candidate: Student = relationship(
        'Student',
        foreign_keys=[candidate_id],
        cascade="all, delete-orphan",
        single_parent=True
    )

    degree_level: Degree = Column(sqla.Enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=False)
    supervisor: Professor = relationship('Professor', foreign_keys=[supervisor_id])
    # Co-relatore
    supervisor_assistant_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=True)
    supervisor_assistant: Professor = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Professor = relationship('Professor', foreign_keys=[counter_supervisor_id])

    def __init__(self,
                 candidate: Student,
                 degree_level: Degree,
                 supervisor: Professor,
                 supervisor_assistant: Professor = None,
                 counter_supervisor: Professor = None):
        self.candidate = candidate
        self.degree_level = degree_level
        self.supervisor = supervisor
        self.supervisor_assistant = supervisor_assistant
        self.counter_supervisor = counter_supervisor

    def serialize(self):
        return {
            'id': self.id,
            'commission_id': self.commission_id,
            'candidate': self.candidate.serialize(),
            'degree_level': self.degree_level.value,
            'supervisor': self.supervisor.serialize(),
            'supervisor_assistant': self.supervisor_assistant.serialize() if self.supervisor_assistant else None,
            'counter_supervisor': self.counter_supervisor.serialize() if self.counter_supervisor else None
        }
