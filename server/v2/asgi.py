from __future__ import annotations

import io
import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Annotated, Final, Any

import pandas as pd

from litestar import Litestar, post, get
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.dto import DTOConfig, dto_field
from litestar.params import Body
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
import litestar.status_codes as http_statuses

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import AsyncSessionTransaction
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey
from advanced_alchemy.base import IdentityAuditBase
from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from model import UniversityRole, Degree, TimeAvailability
from v2.config.settings import Settings

EXCEL_MEDIA_TYPES: Final[list[str]] = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel"
]


@dataclass
class Student(IdentityAuditBase):
    """
    Student model with auto-incrementing ID and audit fields.

    Attributes:
        matriculation_number: A unique number assigned to the student by the university.
        name: The first name of the student.
        surname: The surname of the student.
        phone_number: The student's phone number. This is optional.
        personal_email: The student's personal email address. This is optional.
        university_email: The student's university email address. This is optional.
    """
    __tablename__ = "students"

    matriculation_number: Mapped[int] = mapped_column(sa.BigInteger, unique=False, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    surname: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(sa.String(128), nullable=False)
    personal_email: Mapped[str | None] = mapped_column(sa.String(128), nullable=False)
    university_email: Mapped[str | None] = mapped_column(sa.String(128), nullable=False)

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"

    def __repr__(self):
        return f"Student({self.id=}, {self.matriculation_number=}, {self.name=}, {self.surname=}, " \
               f"{self.phone_number=}, {self.personal_email=}, {self.university_email=})"


@dataclass
class Professor(IdentityAuditBase):
    """
    Professor model with auto-incrementing ID and audit fields.

    Attributes:
        name: The first name of the professor.
        surname: The surname of the professor.
        role: The professor's role in the university. By default, this is set to "UNSPECIFIED".
    """
    __tablename__ = "professors"

    __table_args__ = (
        sa.Index("idx_professors_name_surname_unique", "name", "surname", unique=True),
    )

    name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    surname: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    role: Mapped[UniversityRole] = mapped_column(sa.Enum(UniversityRole),
                                                 nullable=False,
                                                 default=UniversityRole.UNSPECIFIED,
                                                 server_default="UNSPECIFIED")

    @property
    def full_name(self):
        return f"{self.surname} {self.name}"

    def __repr__(self):
        return f"Professor({self.id=}, {self.name=}, {self.surname=}, {self.role=})"


@dataclass
class Session(IdentityAuditBase):
    __tablename__ = "sessions"

    title: Mapped[str] = mapped_column(sa.String(256), nullable=False)
    # date
    entries: Mapped[list[SessionEntry]] = relationship(
        "SessionEntry",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    availabilities: Mapped[list[ProfessorAvailability]] = relationship(
        "ProfessorAvailability",
        back_populates="session",
    )

    # configurations

    def availability_dict(self) -> dict[Professor, TimeAvailability]:
        avs = {}
        for av in self.availabilities:
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
                        entry.candidate.name,
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


@dataclass
class ProfessorAvailability(IdentityAuditBase):
    __tablename__ = "professor_availabilities"

    professor_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("professors.id"), nullable=False)
    professor: Mapped[Professor] = relationship("Professor")

    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[Session] = relationship(
        "Session",
        back_populates="availabilities",
        cascade="all, delete-orphan",
        single_parent=True,
        info=dto_field("private"),
    )

    availability: Mapped[TimeAvailability] = mapped_column(sa.Enum(TimeAvailability), nullable=False)


@dataclass
class SessionEntry(IdentityAuditBase):
    __tablename__ = "session_entries"

    # Session Foreign Key
    session_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("sessions.id"), nullable=False)
    session: Mapped[Session] = relationship("Session", back_populates="entries", info=dto_field("private"),
                                            viewonly=True)

    # Student Foreign Key
    candidate_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey("students.id"), nullable=False)
    candidate: Mapped[Student] = relationship(
        "Student",
        foreign_keys=[candidate_id],
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin"
    )

    degree_level: Mapped[Degree] = mapped_column(sa.Enum(Degree), nullable=False)

    # Professor-Entry Relationships
    supervisor_id: Mapped[int] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=False)
    supervisor: Mapped[Professor] = relationship('Professor', foreign_keys=[supervisor_id])

    supervisor2_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=True)
    supervisor2: Mapped[Professor | None] = relationship('Professor', foreign_keys=[supervisor2_id])

    supervisor_assistant_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'),
                                                                nullable=True)
    supervisor_assistant: Mapped[Professor | None] = relationship('Professor', foreign_keys=[supervisor_assistant_id])

    counter_supervisor_id: Mapped[int | None] = mapped_column(sa.BigInteger, ForeignKey('professors.id'), nullable=True)
    counter_supervisor: Mapped[Professor | None] = relationship('Professor', foreign_keys=[counter_supervisor_id])

    def get_duration(self) -> int:
        return 15 if self.degree_level == Degree.BACHELORS else 20 if self.counter_supervisor is None else 30

    def __repr__(self):
        return f"CommissionEntry({self.id=}, {self.session_id=}, {self.candidate=}, {self.degree_level=}, " \
               f"{self.supervisor=} {self.supervisor2=} {self.supervisor_assistant=}, {self.counter_supervisor=})"


@dataclass
class NewCommissionForm:
    file: UploadFile
    title: str | None = None


class ProfessorRepository(SQLAlchemyAsyncRepository[Professor]):
    model_type = Professor

    @classmethod
    async def provide(cls, db_session: AsyncSession) -> ProfessorRepository:
        return cls(session=db_session)


class SessionRepository(SQLAlchemyAsyncRepository[Session]):
    model_type = Session

    @classmethod
    async def provide(cls, db_session: AsyncSession) -> SessionRepository:
        return cls(session=db_session)


MISSING = {None, '', 'None'}


def is_missing(v: Any) -> bool:
    return v in MISSING


class SessionReadDTO(SQLAlchemyDTO[Session]):
    config = DTOConfig(
        exclude={"entries.0.session", "availabilities.0.session"},
    )


@get("/",
     dependencies={
         "session_repository": Provide(SessionRepository.provide)
     },
     return_dto=SessionReadDTO)
async def get_sessions(session_repository: SessionRepository) -> list[Session]:
    sessions_db = await session_repository.list(load=[Session.availabilities])
    return sessions_db


@post("/upload",
      dependencies={
          "professor_repository": Provide(ProfessorRepository.provide),
          "session_repository": Provide(SessionRepository.provide)
      })
async def new_session(
        data: Annotated[NewCommissionForm, Body(media_type=RequestEncodingType.MULTI_PART)],
        professor_repository: ProfessorRepository,
        session_repository: SessionRepository,
        db_session: AsyncSession
) -> Session:
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
    expected_columns = {'MATRICOLA', 'COGNOME', 'NOME', 'CELLULARE', 'EMAIL', 'EMAIL_ATENEO', 'TIPO_CORSO_DESCRIZIONE',
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

    async def get_or_create_professor(name: str | None, surname: str | None) -> Professor | None:
        if is_missing(name) or is_missing(surname):
            return None

        return await professor_repository.upsert(
            Professor(name=name, surname=surname),
            match_fields=['surname', 'name'],
            auto_commit=False
        )

    txn: AsyncSessionTransaction
    async with db_session.begin():
        grad_session = Session(title=session_name)

        for index, row in excel.iterrows():
            student = Student(
                matriculation_number=int(row['MATRICOLA']),
                name=row['NOME'],
                surname=row['COGNOME'],
                phone_number=row['CELLULARE'],
                personal_email=row['EMAIL'],
                university_email=row['EMAIL_ATENEO']
            )

            supervisor = await get_or_create_professor(row['REL_COGNOME'], row['REL_NOME'])
            supervisor2 = await get_or_create_professor(row['REL2_COGNOME'], row['REL2_NOME'])
            supervisor_assistant = await get_or_create_professor(row['CORR_COGNOME'], row['CORR_NOME'])
            counter_supervisor = await get_or_create_professor(row['CONTROREL_COGNOME'], row['CONTROREL_NOME'])

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

        await session_repository.add(grad_session)

        return grad_session


def create_app() -> Litestar:
    settings = Settings.from_yaml(Path(os.getcwd()) / "v2" / "config.yaml")

    app = Litestar(
        debug=True,
        dependencies={
            # "logger": Provide(provide_logger)
        },
        route_handlers=[new_session, get_sessions],
        cors_config=settings.cors_config,
        plugins=[
            settings.log.structlog_plugin,
            settings.db.alchemy_plugin
        ],
    )

    return app
