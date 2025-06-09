import io
from dataclasses import dataclass

import pandas as pd
import sqlalchemy as sa
from advanced_alchemy.base import IdentityAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from v2.db.models import SessionEntry, ProfessorAvailability, Professor, TimeAvailability


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
    availabilities: Mapped[dict[int, 'ProfessorAvailability']] = relationship(
        "ProfessorAvailability",
        back_populates="session",
        collection_class=attribute_mapped_collection("professor_id"),
        cascade="all, delete-orphan",
        lazy="subquery"
    )

    # configurations

    def availability_dict(self) -> dict[Professor, TimeAvailability]:
        avs = {}
        for av in self.availabilities.values():
            avs[av.professor] = av.availability
        return avs

    def __repr__(self):
        return f"Commission({self.id=}, {self.title=}, {self.entries=})"

    def export_xls(self) -> bytes:
        def si_no(yes: bool) -> str:
            return 'SI' if yes else 'NO'

        # There is a specific possibility that has been intentionally omitted:
        # It might happen that we have a professor that has to be split, however he/she also is a counter-supervisor.
        # This could cause the problem to be unsolvable.
        # A better solution has to be discussed. fixme
        students_by_professor: dict[Professor, list[SessionEntry]] = {}
        for entry in self.entries:
            p = entry.supervisor

            if p not in students_by_professor:
                students_by_professor[p] = []

            students_by_professor[p].append(entry)

        availabilities = self.availability_dict()
        data_rows: list[list[str | int | bool]] = []

        for p in students_by_professor:
            pe = students_by_professor[p]
            should_split = availabilities[p] == TimeAvailability.SPLIT

            for index, entry in enumerate(pe):
                morning_supervisor_availability: bool
                afternoon_supervisor_availability: bool

                supervisor = entry.supervisor

                if should_split:
                    # Corrected logic for splitting more evenly (e.g. 5 students -> 3 morning, 2 afternoon)
                    if index < (len(pe) + 1) // 2:
                        morning_supervisor_availability = True
                        afternoon_supervisor_availability = False
                    else:
                        morning_supervisor_availability = False
                        afternoon_supervisor_availability = True
                else:
                    morning_supervisor_availability = availabilities[supervisor].available_morning
                    afternoon_supervisor_availability = availabilities[supervisor].available_afternoon

                try:
                    current_supervisor = entry.supervisor
                    entity = [
                        entry.candidate.id,
                        entry.candidate.surname,
                        entry.candidate.first_name,
                        entry.get_duration(),
                        current_supervisor.id,
                        current_supervisor.full_name,
                        current_supervisor.role.abbr,
                        si_no(morning_supervisor_availability),
                        si_no(afternoon_supervisor_availability)
                    ]
                except AttributeError as e:
                    raise ValueError(
                        f"Professor '{entry.supervisor.full_name}' "
                        f"might be missing role information or other attributes.") from e

                if entry.counter_supervisor is not None:
                    cs = entry.counter_supervisor
                    try:
                        entity.extend([
                            cs.id,
                            cs.full_name,
                            cs.role.abbr,
                            si_no(availabilities[cs].available_morning),
                            si_no(availabilities[cs].available_afternoon)
                        ])
                    except AttributeError as e:  # Changed from ValueError
                        raise ValueError(
                            f"Professor '{entry.counter_supervisor.full_name}' "
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
