from dataclasses import dataclass

import sqlalchemy as sqla
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, registry

from model.commission import Commission
from model.enums import Degree
from model.hashable import Hashable
from model.professor import Professor
from model.student import Student

mapper_registry = registry()
metadata = mapper_registry.metadata


@mapper_registry.mapped
@dataclass
class CommissionEntry(Hashable):
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
    supervisor_assistant: Professor | None = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: int = Column(sqla.Integer, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Professor | None = relationship('Professor', foreign_keys=[counter_supervisor_id])

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

    @property
    def duration(self):
        return 15 if self.degree_level == Degree.BACHELORS else 20 if self.counter_supervisor is None else 30

    def __repr__(self):
        return f"CommissionEntry({self.id=}, {self.commission_id=}, {self.candidate=}, {self.degree_level=}, " \
               f"{self.supervisor=} {self.supervisor_assistant=}, {self.counter_supervisor=})"

    def hash(self):
        return Hashable.hash_data(repr(self))
