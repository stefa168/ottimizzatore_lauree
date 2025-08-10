import io
from dataclasses import dataclass

import pandas as pd
import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from v2.db.models import SessionEntry, Professor, TimeAvailability, OptimizationConfiguration, SessionProfessor


@dataclass
class GradSession(IdentityAuditBase):
    __tablename__ = "sessions"

    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    # date
    entries: Mapped[list['SessionEntry']] = relationship(
        "SessionEntry",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="subquery"
    )
    configurations: Mapped[list['OptimizationConfiguration']] = relationship(
        "OptimizationConfiguration",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="subquery"
    )
    session_professors_entries: Mapped[list['SessionProfessor']] = relationship(
        "SessionProfessor",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="subquery"
    )

    def availability_dict(self) -> dict[Professor, TimeAvailability]:
        avs = {}
        for p in self.session_professors_entries:
            avs[p.professor] = p.availability
        return avs

    def __repr__(self):
        return f"Commission({self.id=}, {self.title=}, {self.entries=})"

    def export_xls(self) -> bytes:
        def si_no(yes: bool) -> str:
            return 'SI' if yes else 'NO'

        students_by_professor: dict[SessionProfessor, list[SessionEntry]] = {}
        for entry in self.entries:
            p = entry.supervisor

            if p not in students_by_professor:
                students_by_professor[p] = []

            students_by_professor[p].append(entry)

        availabilities = self.availability_dict()
        data_rows: list[list[str | int | bool]] = []

        for p in students_by_professor:
            pe = students_by_professor[p]

            for index, entry in enumerate(pe):
                supervisor = entry.supervisor.professor

                try:
                    entity = [
                        entry.candidate.id,
                        entry.candidate.surname,
                        entry.candidate.first_name,
                        entry.get_duration(),
                        entry.supervisor.id,
                        supervisor.full_name,
                        supervisor.role.abbr,
                        si_no(availabilities[supervisor].available_morning),
                        si_no(availabilities[supervisor].available_afternoon)
                    ]
                except AttributeError as e:
                    raise ValueError(
                        f"Professor '{supervisor.full_name}' "
                        f"might be missing role information or other attributes.") from e

                if entry.counter_supervisor is not None:
                    cs: Professor = entry.counter_supervisor.professor
                    try:
                        entity.extend([
                            entry.counter_supervisor.id,
                            cs.full_name,
                            cs.role.abbr,
                            si_no(availabilities[cs].available_morning),
                            si_no(availabilities[cs].available_afternoon)
                        ])
                    except AttributeError as e:  # Changed from ValueError
                        raise ValueError(
                            f"Professor '{cs.full_name}' "
                            f"might be missing role information or other attributes.") from e

                # todo do the same for the supervisor assistant

                data_rows.append(entity)

        df = pd.DataFrame(
            data_rows,
            columns=["ID_Studente", "Cognome", "Nome", "Durata", "ID_Relatore", "Relatore", "Ruolo", "Mattina",
                     "Pomeriggio", "ID_Controrelatore", "Controrelatore", "Ruolo", "Mattina", "Pomeriggio"]
        )

        # Create an in-memory binary stream
        output = io.BytesIO()
        # Write the DataFrame to this stream as an Excel file
        df.to_excel(output, index=False)
        # Get the content of the stream
        xls_data = output.getvalue()
        output.close()

        return xls_data
