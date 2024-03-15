from dataclasses import dataclass

import sqlalchemy as sqla
from sqlalchemy import Column
from sqlalchemy.orm import registry

from model.hashable import Hashable

mapper_registry = registry()
metadata = mapper_registry.metadata


# The annotation is needed to avoid having to declare a boilerplate class...
# https://docs.sqlalchemy.org/en/20/orm/declarative_styles.html#declarative-mapping-using-a-decorator-no-declarative-base
@mapper_registry.mapped
@dataclass
class Student(Hashable):
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

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"

    def __repr__(self):
        return f"Student({self.id=}, {self.matriculation_number=}, {self.name=}, {self.surname=}, " \
               f"{self.phone_number=}, {self.personal_email=}, {self.university_email=})"

    def hash(self):
        return Hashable.hash_data(repr(self))
