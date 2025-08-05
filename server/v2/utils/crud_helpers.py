from typing import TypeVar, Optional

import structlog
from advanced_alchemy.base import ModelProtocol
from advanced_alchemy.filters import StatementFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository, LoadSpec
from litestar import status_codes as http_statuses
from litestar.exceptions import HTTPException
from sqlalchemy import ColumnElement

logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger()

T = TypeVar("T", bound=ModelProtocol)


async def exists_or_raise(
        repo: SQLAlchemyAsyncRepository[T],
        *filters: StatementFilter | ColumnElement[bool],
        not_found_msg: str = "Resource not found",
        status_code: int = http_statuses.HTTP_404_NOT_FOUND
) -> bool:
    """
    Checks if an entity exists matching the given filters from `repo`.
    Raises HTTPException(status_code) if none is found.
    Returns True if entity exists.
    """
    exists = await repo.exists(*filters)
    if not exists:
        logger.error(f"{not_found_msg}; filters={filters}")
        raise HTTPException(not_found_msg, status_code=status_code)
    return exists


async def get_one_or_raise(
        repo: SQLAlchemyAsyncRepository[T],
        *filters: StatementFilter | ColumnElement[bool],
        load: Optional[LoadSpec] = None,
        not_found_msg: str = "Resource not found",
        status_code: int = http_statuses.HTTP_404_NOT_FOUND
) -> T:
    """
    Fetches exactly one entity matching the given filters from `repo`.
    Raises HTTPException(status_code) if none is found.
    """
    entity = await repo.get_one_or_none(*filters, load=load)
    if entity is None:
        logger.error(f"{not_found_msg}; filters={filters}")
        raise HTTPException(not_found_msg, status_code=status_code)
    return entity
