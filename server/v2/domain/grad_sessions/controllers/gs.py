from __future__ import annotations

from io import BytesIO
from typing import Annotated, Final, Any

import pandas as pd

from litestar import post, get, delete, Controller
from litestar.di import Provide
from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar.params import Body
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
import litestar.status_codes as http_statuses
from sqlalchemy import select, tuple_

from advanced_alchemy.exceptions import NotFoundError

from v2.db.models import Student, Professor, Degree, SessionEntry, GradSession, SessionProfessor
from v2.domain.grad_sessions.deps import (
    ProfessorRepository,
    GradSessionRepository,
    SessionProfessorRepository, SessionEntryRepository
)
from v2.domain.grad_sessions.schemas import NewCommissionForm
from v2.domain.grad_sessions import urls

EXCEL_MEDIA_TYPES: Final[list[str]] = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.oasis.opendocument.spreadsheet"
]

MISSING: Final = {None, '', 'None'}


def is_missing(v: Any) -> bool:
    return v in MISSING


class SessionReadDTO(SQLAlchemyDTO[GradSession]):
    config = SQLAlchemyDTOConfig(
        max_nested_depth=0
    )


class GraduationSessionController(Controller):
    """Graduation Sessions Controller"""

    tags = ["Graduation Sessions"]
    dependencies = {
        "grad_session_repository": Provide(GradSessionRepository.provide),
        "professor_repository": Provide(ProfessorRepository.provide),
        "session_professor_repository": Provide(SessionProfessorRepository.provide),
        "session_entry_repository": Provide(SessionEntryRepository.provide)
    }

    @get(urls.GRAD_SESSIONS_LIST, return_dto=SessionReadDTO)
    async def get_sessions(self, grad_session_repository: GradSessionRepository) -> list[GradSession]:
        sessions_db = await grad_session_repository.list()
        return sessions_db

    @get(urls.GRAD_SESSION_RETRIEVE, return_dto=SessionReadDTO)
    async def get_session(self, sid: int, grad_session_repository: GradSessionRepository) -> GradSession:
        session_db = await grad_session_repository.get_one_or_none(GradSession.id == sid)

        if session_db is None:
            raise HTTPException(detail="Specified Session does not exist", status_code=http_statuses.HTTP_404_NOT_FOUND)

        return session_db

    @post(urls.GRAD_SESSIONS_UPLOAD_EXCEL, return_dto=SessionReadDTO)
    async def upload_xls(
            self,
            data: Annotated[NewCommissionForm, Body(media_type=RequestEncodingType.MULTI_PART)],
            professor_repository: ProfessorRepository,
            grad_session_repository: GradSessionRepository
    ) -> GradSession:
        file = data.file
        file_data = await file.read()

        if not file_data:
            raise HTTPException(detail="File of 0 bytes uploaded.", status_code=http_statuses.HTTP_400_BAD_REQUEST)

        if file.content_type not in EXCEL_MEDIA_TYPES:
            raise HTTPException(
                detail="File is not an Excel file.",
                status_code=http_statuses.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                extra={"content_type": file.content_type, "supported_content_types": EXCEL_MEDIA_TYPES}
            )

        excel = pd.read_excel(BytesIO(file_data)).fillna('None')

        if data.only:
            # Use == for Enum comparison (more robust and clear)
            # mode = 'MAGISTRALE' if data.only == Degree.MASTERS else 'TRIENNALE'
            mask = excel['TIPO_CORSO_DESCRIZIONE'].astype(str).str.upper().str.contains('MAGISTRALE')
            excel = excel[mask if data.only == Degree.MASTERS else ~mask]

        if len(excel) <= 0:
            raise HTTPException(
                detail="The excel file contains no rows or the specified filter returns no students",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO',
                            'TIPO_CORSO_DESCRIZIONE', 'DATA_APPELLO', 'REL_COGNOME', 'REL_NOME', 'REL2_COGNOME',
                            'REL2_NOME', 'CORR_NOME', 'CORR_COGNOME', 'CONTROREL_COGNOME', 'CONTROREL_NOME'}
        actual_columns = {col.upper() for col in excel.columns}
        missing_columns = expected_columns - actual_columns

        if missing_columns:
            raise HTTPException(
                detail="Some expected columns are missing.",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
                extra={"missing_columns": list(missing_columns)}
            )

        # Pass 1: Collect all unique professors
        unique_professors = set()
        prof_cols: Final = [
            ('REL_COGNOME', 'REL_NOME'),
            ('REL2_COGNOME', 'REL2_NOME'),
            ('CORR_COGNOME', 'CORR_NOME'),
            ('CONTROREL_COGNOME', 'CONTROREL_NOME')
        ]
        for _, row in excel.iterrows():
            for surname_col, name_col in prof_cols:
                surname, name = row[surname_col], row[name_col]
                if not is_missing(surname) and not is_missing(name):
                    unique_professors.add((str(surname), str(name)))

        # 2. Query existing professors in one DB call
        stmt = select(Professor).where(tuple_(Professor.surname, Professor.first_name).in_(unique_professors))
        existing_professors = await professor_repository.list(statement=stmt)

        # 2.1. Lookup map for quick access - (surname, name) -> Professor
        type ProfessorTupleMap = dict[tuple[str, str], Professor]
        professor_map: ProfessorTupleMap = {
            (p.surname, p.first_name): p for p in existing_professors
        }

        missing_professors = unique_professors - set(professor_map.keys())

        # 3. Build new Professor instances for what is missing
        if missing_professors:
            new_professors = [
                Professor(first_name=first_name, surname=surname)
                for surname, first_name in missing_professors
            ]

            added_professors = await professor_repository.add_many(new_professors)
            for p in added_professors:
                professor_map[(p.surname, p.first_name)] = p

        # 4. Prepare all the students. This process requires also the construction of SessionProfessors.
        session_name = data.title or file.filename.rsplit(".", 1)[0]
        grad_session = await grad_session_repository.add(GradSession(title=session_name))

        session_professor_map: dict[int, SessionProfessor] = {}

        async def resolve_prof(surname: str | None, first_name: str | None,
                               prof_map: ProfessorTupleMap, session: GradSession) -> SessionProfessor | None:
            # Early return on blanks
            if surname in MISSING or first_name in MISSING:
                return None

            professor = prof_map.get((surname, first_name))  # type: ignore[arg-type]
            if not professor:
                raise RuntimeError("Professor cache miss")

            sp = session_professor_map.get(professor.id)

            if sp is None:
                sp = SessionProfessor(
                    session=session,
                    professor=professor,
                )

                session_professor_map[professor.id] = sp

            return sp

        entries: list[SessionEntry] = []
        for student_row in excel.itertuples(index=False):
            supervisor = await resolve_prof(str(student_row.REL_COGNOME), str(student_row.REL_NOME),
                                            professor_map, grad_session)
            if supervisor is None:
                raise RuntimeError("Supervisor should not be none!!")

            supervisor2 = await resolve_prof(str(student_row.REL2_COGNOME), str(student_row.REL2_NOME),
                                             professor_map, grad_session)
            supervisor_assistant = await resolve_prof(str(student_row.CORR_COGNOME), str(student_row.CORR_NOME),
                                                      professor_map, grad_session)
            counter_supervisor = await resolve_prof(str(student_row.CONTROREL_COGNOME), str(student_row.CONTROREL_NOME),
                                                    professor_map, grad_session)

            # Contains "magistrale" => it's a master degree student
            degree = (Degree.MASTERS
                      if "MAGISTRALE" in str(student_row.TIPO_CORSO_DESCRIZIONE).upper()
                      else Degree.BACHELORS)

            entry = SessionEntry(
                candidate=Student(
                    matriculation_number=int(student_row.MATRICOLA),  # type: ignore
                    first_name=student_row.NOME, surname=student_row.COGNOME,  # type: ignore
                    phone_number=student_row.CELLULARE,  # type: ignore
                    personal_email=student_row.EMAIL,  # type: ignore
                    university_email=student_row.EMAIL_ATENEO,  # type: ignore
                ),
                supervisor=supervisor,
                supervisor2=supervisor2,
                supervisor_assistant=supervisor_assistant,
                counter_supervisor=counter_supervisor,
                degree_level=degree,
                session=grad_session
            )
            entries.append(entry)

        grad_session.entries = entries

        return await grad_session_repository.add(grad_session)

    @delete(urls.GRAD_SESSION_DELETE, status_code=http_statuses.HTTP_200_OK)
    async def delete_session(self, sid: int, grad_session_repository: GradSessionRepository) -> None:
        try:
            _ = await grad_session_repository.delete(sid)
        except NotFoundError:
            raise HTTPException(status_code=http_statuses.HTTP_404_NOT_FOUND)
