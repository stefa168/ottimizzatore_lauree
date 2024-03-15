from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import sqlalchemy as sqla
from sqlalchemy import Column
from sqlalchemy.orm import relationship, registry

from model.hashable import Hashable
from model.commission_entry import CommissionEntry

mapper_registry = registry()
metadata = mapper_registry.metadata


@mapper_registry.mapped
@dataclass
class Commission(Hashable):
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

    def export_xls(self, base_path: Path):
        xls_path = base_path / "val.xls"

        entries = []
        for entry in self.entries:
            try:
                entity = [
                    entry.candidate.id,
                    entry.candidate.surname,
                    entry.candidate.name,
                    entry.duration,
                    entry.supervisor.id,
                    entry.supervisor.full_name,
                    entry.supervisor.role.abbr,
                    'SI',
                    'SI'
                ]
            except ValueError as e:
                raise ValueError(f"Professor '{entry.supervisor.full_name}' doesn't have a role") from e

            if entry.counter_supervisor is not None:
                try:
                    entity.extend([
                        entry.counter_supervisor.id,
                        entry.counter_supervisor.full_name,
                        entry.counter_supervisor.role.abbr,
                        'SI',
                        'SI'
                    ])
                except ValueError as e:
                    raise ValueError(f"Professor '{entry.counter_supervisor.full_name}' doesn't have a role") from e

            # todo do the same for the supervisor assistant

            entries.append(entity)

        df = pd.DataFrame(
            entries,
            columns=["ID_Studente", "Cognome", "Nome", "Durata", "ID_Relatore", "Relatore", "Ruolo", "Mattina",
                     "Pomeriggio", "ID_Controrelatore", "Controrelatore", "Ruolo", "Mattina", "Pomeriggio"]
        )

        df.to_excel(xls_path, index=False)

    def __repr__(self):
        return f"Commission({self.id=}, {self.title=}, {self.entries=})"

    def hash(self):
        # Hash all the entries
        return Hashable.hash_data(repr(self) + "".join([entry.hash() for entry in self.entries]))
