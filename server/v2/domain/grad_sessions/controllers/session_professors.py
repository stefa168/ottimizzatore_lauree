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
    """Session Professor Controller"""

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
        """
        Retrieves a list of session professors associated with a specified session ID.

        This method fetches a list of professors linked to the session with the
        provided session ID, ensuring the session exists prior to retrieval. The
        professors' details are loaded for consumption.

        :param sid: The session ID for which professors are to be retrieved.
        :param session_professor_repository: Repository to handle session professor data access.
        :param grad_session_repo: Repository to handle graduate session data access.
        :return: A list of SessionProfessor objects associated with the given session ID.
        """
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
        """
        Updates a specific session professor using provided data. The method updates
        an instance of a session professor identified by `sid` and
        `session_professor_id`, leveraging the specified repository for data storage
        or retrieval.

        :param data: The DTOData instance containing the update information for a
                     session professor.
        :type data: DTOData[SessionProfessor]
        :param sid: The ID of the session to which the professor belongs.
        :type sid: int
        :param session_professor_id: The unique ID identifying the session professor
                                      to be updated.
        :type session_professor_id: int
        :param session_professor_repository: The repository responsible for session
                                              professor data access.
        :type session_professor_repository: SessionProfessorRepository
        :return: An updated instance of the session professor.
        :rtype: SessionProfessor
        """
        sp = await get_session_professor_raise(sid, session_professor_id, session_professor_repository)
        return data.update_instance(sp)

    # todo move to a separate Professors Controller
    @patch(urls.PROFESSOR_UPDATE, dto=ProfessorDTO)
    async def update_professor(
            self,
            data: DTOData[Professor],
            professor_repository: ProfessorRepository
    ) -> Professor:
        """
        Asynchronous function for updating a professor's details in the repository. It validates the presence
        of an ID in the provided data and determines if a professor with the specified ID exists. If the
        professor is found, their details are updated using the provided data.

        :param data: Data Transfer Object containing information for updating the professor
                     details. It must contain an 'id' field to match a professor.
        :type data: DTOData[Professor]
        :param professor_repository: Repository object that handles operations related to
                                      Professor entities.
        :type professor_repository: ProfessorRepository
        :return: Updated Professor instance with the new details.
        :rtype: Professor
        :raises HTTPException: - If the `id` field is missing from the data, raises an exception
                                  with a 422 status code.
                               - If no professor with the given ID is found, raises an exception
                                  with a 404 status code.
        """
        pid = data.as_builtins().get("id")
        if pid is None:
            raise HTTPException(detail="Field `id` is required for patch",
                                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY)

        professor: Professor | None = await professor_repository.get_one_or_none(Professor.id == pid)
        if professor is None:
            raise HTTPException(detail="Professor not found", status_code=http_statuses.HTTP_404_NOT_FOUND)

        # This method actually updates `professor`, not the `data` variable
        return data.update_instance(professor)
