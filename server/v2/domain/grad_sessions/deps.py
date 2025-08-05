from __future__ import annotations

from typing import Type

import structlog.stdlib
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import update, ChunkedIteratorResult, select
from sqlalchemy.ext.asyncio import AsyncSession

from v2.db.models import Professor, GradSession, SessionEntry, ProfessorAvailability, OptimizationConfiguration, Student

logger = structlog.stdlib.get_logger()


class ProvideRepositoryMixin[T: SQLAlchemyAsyncRepository]:
    @classmethod
    async def provide(cls: Type[T], db_session: AsyncSession) -> T:  # type: ignore
        return cls(session=db_session)


class StudentRepository(SQLAlchemyAsyncRepository[Student], ProvideRepositoryMixin):
    model_type = Student


class ProfessorRepository(SQLAlchemyAsyncRepository[Professor], ProvideRepositoryMixin):
    model_type = Professor


class GradSessionRepository(SQLAlchemyAsyncRepository[GradSession], ProvideRepositoryMixin):
    model_type = GradSession


class SessionEntryRepository(SQLAlchemyAsyncRepository[SessionEntry], ProvideRepositoryMixin):
    model_type = SessionEntry


class SessionProfessorAvailabilityRepository(SQLAlchemyAsyncRepository[ProfessorAvailability], ProvideRepositoryMixin):
    model_type = ProfessorAvailability


class OptimizationConfigurationRepository(SQLAlchemyAsyncRepository[OptimizationConfiguration], ProvideRepositoryMixin):
    model_type = OptimizationConfiguration

    async def acquire_lock(self, config_id: int) -> bool:
        """
        Atomically sets run_lock=True if and only if it was False.
        Uses SELECT FOR UPDATE within a transaction for proper locking.
        """
        # Ensure we're in a transaction
        if not self.session.in_transaction():
            # If no transaction is active, start one
            async with self.session.begin():
                return await self._acquire_lock_impl(config_id)
        else:
            # If already in a transaction, just execute
            return await self._acquire_lock_impl(config_id)

    async def _acquire_lock_impl(self, config_id: int) -> bool:
        """Internal implementation of lock acquisition."""
        try:
            # Select and lock the row ONLY if it exists AND run_lock is False
            select_stmt = (
                select(OptimizationConfiguration)
                .where(
                    OptimizationConfiguration.id == config_id,
                    OptimizationConfiguration.run_lock.is_(False)
                )
                .with_for_update(nowait=True)  # Fail fast if already locked
            )

            result = await self.session.execute(select_stmt)
            config = result.scalar_one_or_none()

            if config is None:
                # Either config doesn't exist OR it's already locked
                logger.debug(f"Config {config_id} not found or already locked")
                return False

            # Update the lock
            config.run_lock = True
            logger.debug(f"Successfully acquired lock for config {config_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to acquire lock for config_id {config_id}: {e}")
            return False
