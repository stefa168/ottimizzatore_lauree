from __future__ import annotations

from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar import get, Controller, patch
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import Professor, SessionProfessor
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import (
    SessionEntryRepository,
    ProfessorRepository, SessionProfessorRepository, GradSessionRepository
)
from v2.domain.grad_sessions.services import get_session_professor_raise, check_gs_exists_raise


class SessionProfessorReadDTO(SQLAlchemyDTO[SessionProfessor]):
    config = SQLAlchemyDTOConfig(
        exclude={"session", "children", "parent"},
    )


class SessionProfessorPatchDTO(SQLAlchemyDTO[SessionProfessor]):
    config = SQLAlchemyDTOConfig(
        partial=True,
        include={"derived_from_id", "availability", "user_note"}
    )


class ProfessorDTO(SQLAlchemyDTO[Professor]):
    config = SQLAlchemyDTOConfig(
        partial=True,
        exclude={"created_at", "updated_at"}
    )


class SessionProfessorController(Controller):
    """Professor Controller"""

    tags = ["Graduation Sessions", "Availabilities", "Professors"]
    dependencies = {
        "session_entry_repository": Provide(SessionEntryRepository.provide),
        "professor_repository": Provide(ProfessorRepository.provide),
        "session_professor_repository": Provide(SessionProfessorRepository.provide),
        "grad_session_repo": Provide(GradSessionRepository.provide)
    }

    @get(urls.SESSION_PROFESSOR_LIST, return_dto=SessionProfessorReadDTO)
    async def get_session_professors(self,
                                     sid: int,
                                     session_professor_repository: SessionProfessorRepository,
                                     grad_session_repo: GradSessionRepository
                                     ) -> list[SessionProfessor]:
        await check_gs_exists_raise(grad_session_repo, sid)

        profs = await session_professor_repository.list(
            SessionProfessor.session_id == sid,
            load=[SessionProfessor.professor]
        )

        return profs

    @patch(urls.SESSION_PROFESSOR_UPDATE, dto=SessionProfessorPatchDTO, return_dto=SessionProfessorReadDTO)
    async def update_session_professor(self,
                                       data: DTOData[SessionProfessor],
                                       sid: int,
                                       session_professor_id: int,
                                       session_professor_repository: SessionProfessorRepository
                                       ) -> SessionProfessor:
        sp = await get_session_professor_raise(sid, session_professor_id, session_professor_repository)
        return data.update_instance(sp)

    @patch(urls.PROFESSOR_UPDATE, dto=ProfessorDTO)
    async def update_professor(
            self,
            data: DTOData[Professor],
            professor_repository: ProfessorRepository
    ) -> Professor:
        pid = data.as_builtins().get("id")
        if pid is None:
            raise HTTPException(detail="Field `id` is required for patch",
                                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY)

        professor: Professor | None = await professor_repository.get_one_or_none(Professor.id == pid)
        if professor is None:
            raise HTTPException(detail="Professor not found", status_code=http_statuses.HTTP_404_NOT_FOUND)

        # This method actually updates `professor`, not the `data` variable
        return data.update_instance(professor)
