from advanced_alchemy.extensions.litestar import SQLAlchemyDTOConfig
from litestar import get, patch, Controller
from litestar.di import Provide
from litestar.plugins.sqlalchemy import SQLAlchemyDTO

from v2.db.models import SessionEntry
from v2.domain.grad_sessions.deps import SessionEntryRepository
from v2.domain.grad_sessions import urls
from pydantic import BaseModel, Field

from v2.utils.crud_helpers import get_one_or_raise


class SessionEntryBonus(BaseModel):
    # Extra minutes for the discussion; capped to keep typos (e.g. 300) from breaking the commissions
    bonus_minutes: int = Field(ge=0, le=120)


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

    @patch(urls.GRAD_SESSION_ENTRY_UPDATE, return_dto=StudentEntryReadDTO)
    async def update_session_entry(
            self,
            sid: int,
            entry_id: int,
            data: SessionEntryBonus,
            session_entry_repository: SessionEntryRepository
    ) -> SessionEntry:
        """Sets the bonus time of a student's discussion."""
        entry = await get_one_or_raise(
            session_entry_repository,
            SessionEntry.id == entry_id,
            SessionEntry.session_id == sid,
            not_found_msg=f"Student entry {entry_id} not found in session {sid}"
        )
        entry.bonus_minutes = data.bonus_minutes
        return entry
