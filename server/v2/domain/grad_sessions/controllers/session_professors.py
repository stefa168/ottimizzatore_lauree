from __future__ import annotations

import itertools
from itertools import combinations

from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar import get, Controller, patch
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
from pydantic import BaseModel, ConfigDict

from v2.db.models import Professor, SessionProfessor, TimeAvailability, SessionEntry
from v2.db.models.enums import SessionProfessorRelation
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
        include={"availability", "user_note"}
    )


class ProfessorDTO(SQLAlchemyDTO[Professor]):
    config = SQLAlchemyDTOConfig(
        partial=True,
        exclude={"created_at", "updated_at"}
    )


class SessionProfessorSplit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    when: TimeAvailability
    note: str | None
    students: set[int]


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

    @patch("/sessions/{session_id:int}/professors/{session_professor_id:int}/split")
    async def split_session_professor(self,
                                      data: list[SessionProfessorSplit],
                                      session_id: int,
                                      session_professor_id: int,
                                      session_professor_repository: SessionProfessorRepository,
                                      session_entry_repository: SessionEntryRepository
                                      ) -> None:
        """
        Draft documentation: this endpoint will REPLACE all the children SessionProfessors with the new configuration
        supplied with the request.
        """
        # 1. Get the referred Session Professor
        original_sp = await get_session_professor_raise(session_id, session_professor_id,
                                                        session_professor_repository)

        # 1.1 The list of new splits must have len > 1
        if len(data) <= 1:
            raise HTTPException(
                detail="Cannot split a professor with less than two virtual professors.",
                status_code=http_statuses.HTTP_400_BAD_REQUEST
            )

        # 1.2 This is a bad request if you ask me to split something that isn't original.
        if original_sp.relation is not SessionProfessorRelation.ORIGINAL:
            raise HTTPException(
                detail="Can only split an ORIGINAL Session Professor",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        # 2. Check that the students of the different splits are not shared
        student_sets = [split.students for split in data]
        repeated_students: set[int] = set()

        for set1, set2 in combinations(student_sets, 2):
            intersection = set1 & set2
            if intersection:
                repeated_students.update(intersection)

        if repeated_students:
            raise HTTPException(
                detail="Some students have been repeated",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
                extra={"repeated_students": repeated_students}
            )

        # 3. Recover all the students owned by this professor.
        # We have two possible situations:
        #   a) the professor has never been split or doesn't have a substitute
        #   b) we have some splits or substitutes (or splits with SPs that substitute some of them)
        sp_ids = await original_sp.collect_descendants_ids()
        owned_students = await session_entry_repository.list(
            SessionEntry.session_id == original_sp.session_id,
            SessionEntry.supervisor_id.in_(sp_ids)
        )
        owned_students_dict = {s.id: s for s in owned_students}

        # 4. Verify that the students we received from the request are actually handled by this Session Professor
        request_students: set[int] = set(itertools.chain.from_iterable(student_sets))
        foreign_students = request_students - set(owned_students_dict.keys())
        if foreign_students:
            raise HTTPException(
                detail="Some students are not owned by the specified Session Professor",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
                extra={"foreign_students": foreign_students}
            )

        # 4. We're all set! Let's make the new session professors and assign the students.
        splits: list[SessionProfessor] = []
        for split in data:
            split_session_professor = SessionProfessor(
                parent=original_sp,
                relation=SessionProfessorRelation.SPLIT,
                professor=original_sp.professor,
                session=original_sp.session,
                availability=split.when,
                user_note=split.note
            )

            splits.append(split_session_professor)

            for student_se in split.students:
                session_entry = owned_students_dict[student_se]
                session_entry.supervisor = split_session_professor

        await session_professor_repository.add_many(splits)

        # Maybe we could improve this section, but it works fine for now.
        if len(sp_ids) > 1:
            await session_professor_repository.delete_many(list(sp_ids - {original_sp.id}))

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
