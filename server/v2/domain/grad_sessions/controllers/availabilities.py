from litestar import get, Controller, patch
from litestar.di import Provide
from litestar.dto import DTOConfig
from litestar.exceptions import HTTPException
import litestar.status_codes as http_statuses
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import ProfessorAvailability
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import SessionProfessorAvailabilityRepository
from v2.domain.grad_sessions.schemas import UpdateProfessorAvailability


class ProfAvailabilityReadDTO(SQLAlchemyDTO[ProfessorAvailability]):
    config = DTOConfig(
        max_nested_depth=0
    )


class AvailabilityController(Controller):
    """Professor Availabilities Controller"""

    tags = ["Graduation Sessions", "Availabilities", "Professors"]
    dependencies = {
        "availability_repository": Provide(SessionProfessorAvailabilityRepository.provide),
    }

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

    @patch(urls.GRAD_SESSION_PROF_AVAILABILITY_CREATE, return_dto=ProfAvailabilityReadDTO)
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
