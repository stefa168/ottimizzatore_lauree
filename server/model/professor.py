from dataclasses import dataclass

import sqlalchemy as sqla
from sqlalchemy import Column
from sqlalchemy.orm import registry

from model.enums import UniversityRole
from model.hashable import Hashable

mapper_registry = registry()
metadata = mapper_registry.metadata


@mapper_registry.mapped
@dataclass
class Professor(Hashable):
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

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"

    def __repr__(self):
        return f"Professor({self.id=}, {self.name=}, {self.surname=}, {self.role=})"

    def hash(self):
        return Hashable.hash_data(repr(self))
