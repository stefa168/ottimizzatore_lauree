from litestar import post, get, Controller, put
from litestar.di import Provide
from litestar.dto import DTOConfig
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import ProfessorAvailability
from v2.domain.grad_sessions import urls
from v2.domain.grad_sessions.deps import SessionProfessorAvailabilityRepository


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
