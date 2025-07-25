from __future__ import annotations

import datetime
from dataclasses import dataclass

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO
from litestar.datastructures import UploadFile
from litestar.dto import DTOConfig

from pydantic import BaseModel, ConfigDict

from v2.db.models import TimeAvailability, UniversityRole, Professor, ProfessorAvailability, OptimizationConfiguration, \
    SolverEnum


@dataclass
class NewCommissionForm:
    file: UploadFile
    title: str | None = None


@dataclass
class UpdateProfessorAvailability(BaseModel):
    professor_id: int
    availability: TimeAvailability


class AvailabilityWithAudit(BaseModel):
    availability: TimeAvailability
    updated_at: datetime.datetime


class ProfessorWithAvailability(BaseModel):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    first_name: str
    surname: str
    role: UniversityRole

    availability: AvailabilityWithAudit

    @staticmethod
    def factory(professor: Professor, pa: ProfessorAvailability) -> ProfessorWithAvailability:
        availability = AvailabilityWithAudit(availability=pa.availability, updated_at=pa.updated_at)
        prof = ProfessorWithAvailability(
            id=professor.id,
            created_at=professor.created_at,
            updated_at=professor.updated_at,
            first_name=professor.first_name,
            surname=professor.surname,
            role=professor.role,
            availability=availability
        )

        return prof


# Optimization Configuration DTOs

class OptConfDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0
    )


class OptConfPatchDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0,
        partial=True,
        exclude={"id", "created_at", "updated_at", "session_id"}
    )


class OptConfListDTO(SQLAlchemyDTO[OptimizationConfiguration]):
    config = DTOConfig(
        max_nested_depth=0,
        include={"session_id", "id", "title", "created_at", "updated_at"}
    )


class OptimizationLogDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opt_config_id: int


class SolutionCommissionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_key: int
    morning: bool

    session_id: int
    opt_config_id: int

    # professors_ids: list[int]
    # students_ids: list[int]
    # @computed_field
    # def professors_ids(self) -> list[int]:
    #     # `self` is the ORM object (since from_attributes=True)
    #     return [p.id for p in self.professors]


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
    commissions: list[None]
