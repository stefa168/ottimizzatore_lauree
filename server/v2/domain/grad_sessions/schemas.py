from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.datastructures import UploadFile

from pydantic import BaseModel, ConfigDict, Field, field_validator

from v2.db.models import OptimizationConfiguration, SolverEnum, Degree


@dataclass
class NewCommissionForm:
    file: UploadFile
    title: str | None = None
    only: Degree | None = None
    # date


# Optimization Configuration DTOs

class OptConfDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = SQLAlchemyDTOConfig(
        max_nested_depth=0
    )


class CloneOptConfDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = SQLAlchemyDTOConfig(
        max_nested_depth=0,
        exclude={"id", "created_at", "updated_at", "run_lock", "optimization_log", "commissions"}
    )


class OptConfPatchDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = SQLAlchemyDTOConfig(
        max_nested_depth=0,
        partial=True,
        exclude={"id", "created_at", "updated_at", "session_id", "optimization_log", "commissions"}
    )


class OptConfListDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = SQLAlchemyDTOConfig(
        max_nested_depth=0,
        include={"session_id", "id", "title", "created_at", "updated_at"}
    )


class OptimizationLogDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opt_config_id: int

    start_time: datetime.datetime
    end_time: datetime.datetime

    success: bool
    solver_reached_optimality: bool
    solver_time_limit_reached: bool
    error_message: str | None
    log: str

    created_at: datetime.datetime
    updated_at: datetime.datetime


class SolutionCommissionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # from_attributes is crucial

    order_key: int
    morning: bool
    duration: int

    session_id: int
    opt_config_id: int

    # Use an alias to map from the ORM's attribute name
    professor_ids: list[int] = Field(..., alias='professors')
    student_ids: list[int] = Field(..., alias='students')

    # noinspection PyNestedDecorators
    @field_validator('professor_ids', 'student_ids', mode='before')
    @staticmethod
    def convert_objects_to_ids(v: Any) -> list[int]:
        """
        This validator runs before type validation and converts a list of ORM objects
        into a list of their IDs.

        Works only if the values are already present. If they're awaitable, please load them before
        """
        if isinstance(v, list):
            # Handles the case where the input is already a list of ints
            if not v or isinstance(v[0], int):
                return v
            # Assumes a list of objects with an 'id' attribute
            return [obj.id for obj in v]
        return v  # Should not happen with from_attributes, but good practice


class OptConfCompleteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    session_id: int

    max_duration: int
    max_commissions_morning: int
    max_commissions_afternoon: int

    online: bool
    min_professor_number: int | None
    min_professor_number_masters: int | None
    max_professor_number: int | None

    solver: SolverEnum

    optimization_time_limit: int
    optimization_gap: float
    run_lock: bool

    optimization_log: OptimizationLogDTO | None
    commissions: list[SolutionCommissionDTO]

    created_at: datetime.datetime
    updated_at: datetime.datetime
