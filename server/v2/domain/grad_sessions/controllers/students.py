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

from pydantic import BaseModel

from v2.db.models import Student, Professor, Degree, SessionEntry, GradSession
from v2.domain.grad_sessions.deps import ProfessorRepository, GradSessionRepository, SessionEntryRepository
from v2.domain.grad_sessions.schemas import NewCommissionForm
from v2.domain.grad_sessions import urls


class StudentEntryReadDTO(SQLAlchemyDTO[SessionEntry]):
    config = DTOConfig(
        exclude={
            "session",
            "supervisor",
            "supervisor2",
            "supervisor_assistant",
            "counter_supervisor"
        }
        # max_nested_depth=0
    )


class StudentController(Controller):
    """Graduation Sessions Student Controller"""

    tags = ["Graduation Sessions", "Students"]
    dependencies = {
        "session_entry_repository": Provide(SessionEntryRepository.provide),
    }

    @get(urls.GRAD_SESSION_STUDENTS_LIST, return_dto=StudentEntryReadDTO)
    async def get_session_students(self, sid: int, session_entry_repository: SessionEntryRepository) -> list[SessionEntry]:
        session_entries = await session_entry_repository.list(
            SessionEntry.session_id == sid
        )
        return session_entries
