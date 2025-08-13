from __future__ import annotations

import itertools
from itertools import combinations

from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar import get, Controller, patch, delete
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
from v2.utils.crud_helpers import get_one_or_raise


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


class SessionProfessorSubstitute(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    availability: TimeAvailability = TimeAvailability.ALWAYS
    note: str = ""


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

    @patch(urls.SESSION_PROFESSOR_SPLIT)
    async def split_session_professor(self,
                                      data: list[SessionProfessorSplit],
                                      session_id: int,
                                      session_professor_id: int,
                                      session_professor_repository: SessionProfessorRepository,
                                      session_entry_repository: SessionEntryRepository,
                                      ignore_substitutes: bool | None = None,
                                      ) -> list[SessionProfessor]:
        """
        Draft documentation: this endpoint will REPLACE all the children SessionProfessors with the new configuration
        supplied with the request.
        """
        # 1. Get the referred Session Professor
        original_sp = await get_session_professor_raise(session_id, session_professor_id, session_professor_repository)

        # 1.1 This is a bad request if you ask me to split something that isn't original.
        if original_sp.relation is not SessionProfessorRelation.ORIGINAL:
            raise HTTPException(
                detail="Can only split an ORIGINAL Session Professor",
                status_code=http_statuses.HTTP_409_CONFLICT
            )

        student_sets: list[set[int]] = []
        # We do this only if we have at least two virtual professors. If we received a request with no virtual
        # professors, then it means that we want to remove all the splits.
        # 1.2 The list of new splits must have len > 1
        if len(data) == 1:
            raise HTTPException(
                detail="Cannot split a professor with less than two virtual professors.",
                status_code=http_statuses.HTTP_400_BAD_REQUEST
            )
        elif len(data) >= 2:
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

        substitute_ids = [idx for idx, rel in sp_ids.items() if rel is SessionProfessorRelation.SUBSTITUTE]

        if ignore_substitutes is False and substitute_ids:
            raise HTTPException(
                detail="Substitutes exist; operation cannot proceed. "
                       "Set query parameter `ignore_substitutes` to true to ignore this constraint and remove them",
                status_code=http_statuses.HTTP_409_CONFLICT,
                extra={
                    "substitute_session_professor_ids": substitute_ids,
                    "had_substitutes": True,
                }
            )

        owned_students = await session_entry_repository.list(
            SessionEntry.session_id == original_sp.session_id,
            SessionEntry.supervisor_id.in_(sp_ids.keys())
        )
        owned_students_dict = {s.id: s for s in owned_students}

        splits: list[SessionProfessor] = []
        if len(data) >= 2:
            # If we're here, we are creating or updating the SessionProfessor hierarchy.
            # 4. Verify that the students we received from the request are actually handled by this Session Professor.
            request_students: set[int] = set(itertools.chain.from_iterable(student_sets))
            foreign_students = request_students - set(owned_students_dict.keys())
            if foreign_students:
                raise HTTPException(
                    detail="Some students are not owned by the specified Session Professor",
                    status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY,
                    extra={"foreign_students": foreign_students}
                )

            # 5. We're all set! Let's make the new session professors and assign the students.
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

        else:
            # If we're here, we're moving all the students back to the root SessionProfessor.
            for s in owned_students:
                s.supervisor = original_sp

        # Finally, remove all the virtual SPs created in the past.
        if len(sp_ids) > 1:
            await session_professor_repository.delete_many(list(sp_ids.keys() - {original_sp.id}))

        return splits

    @patch(urls.SESSION_PROFESSOR_SUBSTITUTE)
    async def substitute_session_professor(self,
                                           session_id: int,
                                           session_professor_id: int,
                                           substitute_professor_id: int,
                                           session_professor_repository: SessionProfessorRepository,
                                           session_entry_repository: SessionEntryRepository,
                                           professor_repository: ProfessorRepository,
                                           data: SessionProfessorSubstitute = SessionProfessorSubstitute()
                                           ) -> SessionProfessor:
        # 1. Get the referred Session Professor
        original_sp = await get_session_professor_raise(session_id, session_professor_id, session_professor_repository)

        if original_sp.professor.id == substitute_professor_id:
            raise HTTPException(
                detail="The specified Professor is already substituting the specified Session Professor",
                status_code=http_statuses.HTTP_400_BAD_REQUEST
            )

        substitute_prof = await get_one_or_raise(professor_repository,
                                                 Professor.id == substitute_professor_id,
                                                 not_found_msg="The specified Professor doesn't exist")

        # 2. Is this a substitute? If so, just replace the SessionEntry.supervisor
        if original_sp.relation is SessionProfessorRelation.SUBSTITUTE:
            original_sp.professor = substitute_prof
            return await session_professor_repository.update(original_sp)

        sp_children = await original_sp.collect_descendants_ids()
        sp_children.pop(original_sp.id)  # -1 because the method returns also the original_sp's id
        if len(sp_children) > 0:
            raise HTTPException(
                detail="Cannot add a substitute to a Professor that has substitutes or SPLITs",
                status_code=http_statuses.HTTP_409_CONFLICT,
                extra={"children": sp_children}
            )

        substitute_sp = SessionProfessor(
            session=original_sp.session,
            professor=substitute_prof,
            relation=SessionProfessorRelation.SUBSTITUTE,
            parent=original_sp,
            availability=data.availability,
            user_note=data.note
        )

        substitute_sp = await session_professor_repository.add(substitute_sp)

        students = await session_entry_repository.list(
            SessionEntry.supervisor_id == original_sp.id,
            SessionEntry.session_id == original_sp.session_id
        )

        for student in students:
            student.supervisor = substitute_sp

        await session_entry_repository.update_many(students)

        return substitute_sp

    @delete("/sessions/{session_id:int}/professors/{session_professor_id:int}/substitute")
    async def delete_substitute_session_professor(self,
                                                  session_id: int,
                                                  session_professor_id: int,
                                                  session_professor_repository: SessionProfessorRepository,
                                                  session_entry_repository: SessionEntryRepository,
                                                  ) -> None:
        substitute_sp = await get_session_professor_raise(session_id, session_professor_id,
                                                          session_professor_repository)

        if substitute_sp.parent is None:
            raise HTTPException(
                detail="Substitute undefined",
                status_code=http_statuses.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if substitute_sp.relation is not SessionProfessorRelation.SUBSTITUTE:
            raise HTTPException(
                detail="The specified Session Professor is not a substitute",
                status_code=http_statuses.HTTP_409_CONFLICT,
                extra={"relation": substitute_sp.relation}
            )

        students = await session_entry_repository.list(
            SessionEntry.supervisor_id == substitute_sp.id,
            SessionEntry.session_id == substitute_sp.session_id
        )

        for student in students:
            student.supervisor = substitute_sp.parent

        await session_entry_repository.update_many(students)
        await session_professor_repository.delete(substitute_sp)

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
