from __future__ import annotations

from io import BytesIO
from typing import Annotated, Final, Any

import pandas as pd

from litestar import post, get, Controller
from litestar.di import Provide
from litestar.dto import DTOConfig
from litestar.params import Body
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
import litestar.status_codes as http_statuses

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import AsyncSessionTransaction

from v2.db.models import Student, Professor, Degree, SessionEntry, GradSession, ProfessorAvailability, TimeAvailability
from v2.domain.grad_sessions.deps import (
    ProfessorRepository,
    GradSessionRepository,
    SessionProfessorAvailabilityRepository
)
from v2.domain.grad_sessions.schemas import NewCommissionForm
from v2.domain.grad_sessions import urls

EXCEL_MEDIA_TYPES: Final[list[str]] = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel"
]

MISSING: Final = {None, '', 'None'}


def is_missing(v: Any) -> bool:
    return v in MISSING


class SessionReadDTO(SQLAlchemyDTO[GradSession]):
    config = DTOConfig(
        max_nested_depth=0
    )


class GraduationSessionController(Controller):
    """Graduation Sessions Controller"""

    tags = ["Graduation Sessions"]
    dependencies = {
        "grad_session_repository": Provide(GradSessionRepository.provide),
        "professor_repository": Provide(ProfessorRepository.provide),
        "availability_repository": Provide(SessionProfessorAvailabilityRepository.provide),
    }

    @get(urls.GRAD_SESSIONS_LIST, return_dto=SessionReadDTO)
    async def get_sessions(self, grad_session_repository: GradSessionRepository) -> list[GradSession]:
        sessions_db = await grad_session_repository.list()
        return sessions_db

    @get(urls.GRAD_SESSION_RETRIEVE, return_dto=SessionReadDTO)
    async def get_session(self, sid: int, grad_session_repository: GradSessionRepository) -> GradSession:
        session_db = await grad_session_repository.get(sid)
        return session_db

    @post(urls.GRAD_SESSIONS_UPLOAD_EXCEL, return_dto=SessionReadDTO)
    async def upload_xls(
            self,
            data: Annotated[NewCommissionForm, Body(media_type=RequestEncodingType.MULTI_PART)],
            professor_repository: ProfessorRepository,
            grad_session_repository: GradSessionRepository,
            availability_repository: SessionProfessorAvailabilityRepository,
            db_session: AsyncSession
    ) -> GradSession:
        file = data.file
        file_data = await file.read()

        if len(file_data) <= 0:
            raise HTTPException(detail="File of 0 bytes uploaded.", status_code=http_statuses.HTTP_400_BAD_REQUEST)

        # Check if content type is of excel or libreoffice
        if file.content_type not in EXCEL_MEDIA_TYPES:
            raise HTTPException(
                detail="File is not an Excel file.",
                status_code=http_statuses.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                extra={
                    "content_type": file.content_type,
                    "supported_content_types": EXCEL_MEDIA_TYPES
                })

        excel = pd.read_excel(BytesIO(file_data)).fillna('None')

        # Ensure that the file has ALL the expected columns
        expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO',
                            'TIPO_CORSO_DESCRIZIONE',
                            'DATA_APPELLO', 'REL_COGNOME', 'REL_NOME', 'REL2_COGNOME', 'REL2_NOME', 'CORR_NOME',
                            'CORR_COGNOME', 'CONTROREL_COGNOME', 'CONTROREL_NOME'}

        actual_columns = set([col.upper() for col in excel.columns])
        missing_columns = expected_columns - actual_columns

        if len(missing_columns) > 0:
            raise HTTPException(
                detail="Some expected columns are missing.",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
                extra={
                    "missing_columns": list(missing_columns)
                })

        session_name = data.title or file.filename.removesuffix(".xlsx").removesuffix(".xls")

        async def get_or_create_professor(surname: str | None,
                                          name: str | None,
                                          prof_set: set[Professor]) -> Professor | None:
            if is_missing(name) or is_missing(surname):
                return None

            prof = await professor_repository.upsert(
                Professor(first_name=name, surname=surname),
                match_fields=['surname', 'name'],
                auto_commit=False
            )

            prof_set.add(prof)
            return prof

        txn: AsyncSessionTransaction
        async with db_session.begin():
            grad_session = GradSession(title=session_name)
            sp: set[Professor] = set()  # Session Professors

            for index, row in excel.iterrows():
                student = Student(
                    matriculation_number=int(row['MATRICOLA']),
                    first_name=row['NOME'],
                    surname=row['COGNOME'],
                    phone_number=row['CELLULARE'],
                    personal_email=row['EMAIL'],
                    university_email=row['EMAIL_ATENEO']
                )

                supervisor = await get_or_create_professor(row['REL_COGNOME'], row['REL_NOME'], sp)
                supervisor2 = await get_or_create_professor(row['REL2_COGNOME'], row['REL2_NOME'], sp)
                supervisor_assistant = await get_or_create_professor(row['CORR_COGNOME'], row['CORR_NOME'], sp)
                counter_supervisor = await get_or_create_professor(row['CONTROREL_COGNOME'], row['CONTROREL_NOME'], sp)

                # todo assert that the supervisor is not none

                # lowercase contains "magistrale" then it's a master degree
                if "magistrale" in row['TIPO_CORSO_DESCRIZIONE'].lower():
                    degree = Degree.MASTERS
                else:
                    degree = Degree.BACHELORS

                entry = SessionEntry(
                    session=grad_session,
                    candidate=student,
                    supervisor=supervisor,
                    supervisor2=supervisor2,
                    supervisor_assistant=supervisor_assistant,
                    counter_supervisor=counter_supervisor,
                    degree_level=degree
                )

                grad_session.entries.append(entry)

            await grad_session_repository.add(grad_session)

            # Now that we've prepared all the entries and professors we can create all the default availabilities
            availabilities = [
                ProfessorAvailability(
                    professor_id=professor.id,
                    session_id=grad_session.id,
                    availability=TimeAvailability.ALWAYS
                ) for professor in sp
            ]
            await availability_repository.add_many(availabilities)

            return grad_session
