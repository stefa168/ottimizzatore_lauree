from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar import get, Controller
from litestar.di import Provide
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import SessionEntry
from v2.domain.grad_sessions.deps import SessionEntryRepository
from v2.domain.grad_sessions import urls


class StudentEntryReadDTO(SQLAlchemyDTO[SessionEntry]):
    config = SQLAlchemyDTOConfig(
        exclude={
            "session",
            "supervisor",
            "supervisor2",
            "supervisor_assistant",
            "counter_supervisor",
            "created_at",
            "updated_at",
            "candidate.created_at",
            "candidate.updated_at"
        }
        # max_nested_depth=0
    )


class StudentController(Controller):
    """Graduation Sessions Student Controller"""

    tags = ["Graduation Sessions", "Students"]
    dependencies = {
        "session_entry_repository": Provide(SessionEntryRepository.provide),
    }

    @get(urls.GRAD_SESSION_ENTRY_LIST, return_dto=StudentEntryReadDTO)
    async def get_session_entries(
            self,
            sid: int,
            session_entry_repository: SessionEntryRepository
    ) -> list[SessionEntry]:
        session_entries = await session_entry_repository.list(
            SessionEntry.session_id == sid
        )
        return session_entries
