from __future__ import annotations

import itertools

from litestar import get, Controller, patch
from litestar.di import Provide
from litestar.dto import DTOConfig, DTOData
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from litestar.plugins.pydantic import PydanticDTO
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import ProfessorAvailability, SessionEntry, Professor
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import (
    SessionProfessorAvailabilityRepository,
    SessionEntryRepository,
    ProfessorRepository
)
from v2.domain.grad_sessions.schemas import UpdateProfessorAvailability, ProfessorWithAvailability


class ProfAvailabilityReadDTO(SQLAlchemyDTO[ProfessorAvailability]):
    config = DTOConfig(
        max_nested_depth=0
    )


class ProfessorDTO(SQLAlchemyDTO[Professor]):
    config = DTOConfig(
        partial=True,
        exclude={"created_at", "updated_at"}
    )


class ProfessorController(Controller):
    """Professor Controller"""

    tags = ["Graduation Sessions", "Availabilities", "Professors"]
    dependencies = {
        "availability_repository": Provide(SessionProfessorAvailabilityRepository.provide),
        "session_entry_repository": Provide(SessionEntryRepository.provide),
        "professor_repository": Provide(ProfessorRepository.provide)
    }

    @get(urls.GRAD_SESSION_PROFESSOR_LIST)
    async def get_session_professors(self,
                                     sid: int,
                                     availability_repository: SessionProfessorAvailabilityRepository
                                     ) -> list[ProfessorWithAvailability]:
        # entries = await session_entry_repository.list(
        #     SessionEntry.session_id == sid
        # )
        #
        # # We could also check if the session id actually corresponds to an existing entry in its own table,
        # # however we already have all the session entries and they only exist when a session exists,
        # # so this shouldn't be an issue in any case.
        # if len(entries) <= 0:
        #     raise HTTPException(
        #         detail="The specified Graduation Session doesn't exist.",
        #         status_code=http_statuses.HTTP_404_NOT_FOUND
        #     )
        #
        # prof_ids = [
        #     [entry.supervisor_id, entry.counter_supervisor_id, entry.supervisor2_id, entry.supervisor_assistant_id]
        #     for entry in entries
        # ]
        #
        # prof_ids = set(filter(None, itertools.chain.from_iterable(prof_ids)))
        #
        # professor_repository.list()

        # I'm keeping the above (partial) implementation in case we need to do some more complex queries when I'll add
        # `split professors` and professor substitutes...
        availabilities = await availability_repository.list(
            ProfessorAvailability.session_id == sid,
            load=ProfessorAvailability.professor
        )

        return [ProfessorWithAvailability.factory(av.professor, av) for av in availabilities]

    @get(urls.GRAD_SESSION_PROF_AVAILABILITY_LIST, return_dto=ProfAvailabilityReadDTO)
    async def get_session_availabilities(
            self,
            sid: int,
            availability_repository: SessionProfessorAvailabilityRepository
    ) -> list[ProfessorAvailability]:
        availabilities = await availability_repository.list(
            ProfessorAvailability.session_id == sid
        )
        return availabilities

    @patch(urls.GRAD_SESSION_PROFESSOR_UPDATE, dto=ProfessorDTO)
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

        # return professor

    @patch(urls.GRAD_SESSION_PROF_AVAILABILITY_UPDATE, return_dto=ProfAvailabilityReadDTO)
    async def update_professor_availability(
            self,
            sid: int,
            data: UpdateProfessorAvailability,
            availability_repository: SessionProfessorAvailabilityRepository
    ) -> ProfessorAvailability:
        old_av = await availability_repository.get_one_or_none(
            ProfessorAvailability.session_id == sid, ProfessorAvailability.professor_id == data.professor_id
        )

        if old_av is None:
            raise HTTPException(
                detail="Specified Availability Entry does not exist.",
                status_code=http_statuses.HTTP_422_UNPROCESSABLE_ENTITY
            )

        old_av.availability = data.availability
        return await availability_repository.update(old_av)
