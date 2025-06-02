from __future__ import annotations

from typing import TypeVar, Type

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy.ext.asyncio import AsyncSession

from v2.db.models import Professor, GradSession

T = TypeVar('T', bound=SQLAlchemyAsyncRepository)


class ProvideRepositoryMixin:
    @classmethod
    async def provide(cls: Type[T], db_session: AsyncSession) -> T:
        return cls(session=db_session)


class ProfessorRepository(SQLAlchemyAsyncRepository[Professor], ProvideRepositoryMixin):
    model_type = Professor


class GradSessionRepository(SQLAlchemyAsyncRepository[GradSession], ProvideRepositoryMixin):
    model_type = GradSession

    @classmethod
    async def provide(cls, db_session: AsyncSession) -> 'GradSessionRepository':
        return cls(session=db_session)
