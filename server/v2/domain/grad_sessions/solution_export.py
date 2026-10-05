"""Export of a solution (the commissions of an optimization configuration) to an Excel file."""
from __future__ import annotations

import io

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from v2.db.models import OptimizationConfiguration, SessionEntry, SessionProfessor
from v2.db.models.enums import Degree, SessionProfessorRelation

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def build_solution_xlsx(config: OptimizationConfiguration, db_session: AsyncSession) -> bytes:
    """
    Builds the commissions export of a solved configuration. `config.commissions` (with professors and students) must
    be loaded.

    - sheet "Commissioni": one row per student, grouped by commission;
    - sheet "Docenti": the professors of each commission, with their role.
    """
    sid = config.session_id

    session_professors = (await db_session.execute(
        select(SessionProfessor).where(SessionProfessor.session_id == sid)
    )).scalars().all()
    sp_by_id = {sp.id: sp for sp in session_professors}

    entries = (await db_session.execute(
        select(SessionEntry).where(SessionEntry.session_id == sid)
    )).unique().scalars().all()
    entry_by_student = {e.candidate_id: e for e in entries}

    def name(sp_id: int | None) -> str:
        sp = sp_by_id.get(sp_id) if sp_id is not None else None
        return sp.professor.full_name if sp else ""

    def note(sp: SessionProfessor) -> str:
        """How a split or a substitute relates to the professor it derives from."""
        parent = sp_by_id.get(sp.derived_from_id) if sp.derived_from_id is not None else None
        if parent is None:
            return ""
        if sp.relation is SessionProfessorRelation.SUBSTITUTE:
            return f"sostituto di {parent.professor.full_name}"
        if sp.relation is SessionProfessorRelation.SPLIT:
            parts = sorted(c.id for c in session_professors
                           if c.derived_from_id == parent.id and c.relation is SessionProfessorRelation.SPLIT)
            return f"parte {parts.index(sp.id) + 1}"
        return ""

    student_rows: list[dict] = []
    professor_rows: list[dict] = []
    for commission in sorted(config.commissions, key=lambda c: c.order_key):
        number = commission.order_key + 1
        turn = "Mattina" if commission.morning else "Pomeriggio"

        for student in sorted(commission.students, key=lambda s: (s.surname, s.first_name)):
            entry = entry_by_student.get(student.id)
            student_rows.append({
                "Commissione": number,
                "Turno": turn,
                "Matricola": student.matriculation_number,
                "Candidato": student.full_name,
                "Laurea": "Magistrale" if entry and entry.degree_level == Degree.MASTERS else "Triennale",
                "Minuti": commission.student_minutes.get(str(student.id)),
                "Relatore": name(entry.supervisor_id) if entry else "",
                "Correlatore": name(entry.supervisor_assistant_id) if entry else "",
                "Controrelatore": name(entry.counter_supervisor_id) if entry else "",
            })

        for sp in sorted(commission.professors, key=lambda p: (p.professor.surname, p.professor.first_name)):
            professor_rows.append({
                "Commissione": number,
                "Turno": turn,
                "Docente": sp.professor.full_name,
                "Ruolo": sp.professor.role.abbr,
                "Note": note(sp),
            })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet, rows, columns in (
                ("Commissioni", student_rows, ["Commissione", "Turno", "Matricola", "Candidato", "Laurea", "Minuti",
                                              "Relatore", "Correlatore", "Controrelatore"]),
                ("Docenti", professor_rows, ["Commissione", "Turno", "Docente", "Ruolo", "Note"]),
        ):
            pd.DataFrame(rows, columns=columns).to_excel(writer, sheet_name=sheet, index=False)
            worksheet = writer.sheets[sheet]
            worksheet.freeze_panes = "A2"
            # Fit the columns to their content
            for column_cells in worksheet.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(width + 2, 60)

    return output.getvalue()
