from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from v2.db.models import Professor, GradSession


class ProfessorRepository(SQLAlchemyAsyncRepository[Professor]):
    model_type = Professor

    @classmethod
    async def provide(cls, db_session: AsyncSession) -> 'ProfessorRepository':
        return cls(session=db_session)


class GradSessionRepository(SQLAlchemyAsyncRepository[GradSession]):
    model_type = GradSession

    @classmethod
    async def provide(cls, db_session: AsyncSession) -> 'GradSessionRepository':
        return cls(session=db_session)
