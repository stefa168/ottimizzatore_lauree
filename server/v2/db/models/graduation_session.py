import io
from dataclasses import dataclass
from typing import Final

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

        def availability_flags(sp: SessionProfessor) -> tuple[str, str]:
            av = sp.availability
            # TimeAvailability exposes booleans for morning/afternoon
            return si_no(av.available_morning), si_no(av.available_afternoon)

        columns: Final = [
            "ID_Studente", "Cognome", "Nome", "Durata",
            # Supervisor columns (SessionProfessor + Professor)
            "ID_Relatore", "PID_Relatore", "Relatore", "Ruolo_Relatore", "Relatore_Mattina", "Relatore_Pomeriggio",
            # Counter-supervisor columns (optional; if absent the row cells will be NaN and are handled downstream)
            "ID_Controrelatore", "PID_Controrelatore", "Controrelatore", "Ruolo_Controrelatore",
            "Controrelatore_Mattina", "Controrelatore_Pomeriggio"
        ]

        # Group students by SessionProfessor to keep things deterministic
        students_by_session_prof: dict[SessionProfessor, list[SessionEntry]] = {}
        for entry in self.entries:
            sp = entry.supervisor
            students_by_session_prof.setdefault(sp, []).append(entry)

        data_rows: list[list[str | int | bool]] = []

        for sp, entries in students_by_session_prof.items():
            for entry in entries:
                supervisor_sp: SessionProfessor = entry.supervisor
                supervisor_prof: Professor = supervisor_sp.professor
                rel_morn, rel_aft = availability_flags(supervisor_sp)

                try:
                    entity = [
                        entry.candidate.id,
                        entry.candidate.surname,
                        entry.candidate.first_name,
                        entry.get_duration(),

                        # Supervisor (SessionProfessor + Professor IDs)
                        supervisor_sp.id,
                        supervisor_prof.id,
                        supervisor_prof.full_name,
                        supervisor_prof.role.abbr,
                        rel_morn,
                        rel_aft,
                    ]
                except AttributeError as e:
                    raise ValueError(
                        f"Professor '{supervisor_prof.full_name}' "
                        f"might be missing role information or other attributes."
                    ) from e

                # Counter-supervisor (optional)
                if entry.counter_supervisor is not None:
                    cs_sp: SessionProfessor = entry.counter_supervisor
                    cs_prof: Professor = cs_sp.professor
                    cs_morn, cs_aft = availability_flags(cs_sp)

                    try:
                        entity.extend([
                            cs_sp.id,
                            cs_prof.id,
                            cs_prof.full_name,
                            cs_prof.role.abbr,
                            cs_morn,
                            cs_aft
                        ])
                    except AttributeError as e:
                        raise ValueError(
                            f"Professor '{cs_prof.full_name}' "
                            f"might be missing role information or other attributes."
                        ) from e

                # Pad missing optional fields so every row matches the declared columns
                missing = len(columns) - len(entity)
                if missing > 0:
                    entity.extend([None] * missing)

                data_rows.append(entity)

        df = pd.DataFrame(data_rows, columns=columns)

        # Create an in-memory binary stream
        output = io.BytesIO()
        # Write the DataFrame to this stream as an Excel file
        df.to_excel(output, index=False)
        # Get the content of the stream
        xls_data = output.getvalue()
        output.close()

        return xls_data
