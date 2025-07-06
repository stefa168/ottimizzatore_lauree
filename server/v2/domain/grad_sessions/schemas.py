from __future__ import annotations

import datetime
from dataclasses import dataclass

from litestar.datastructures import UploadFile

from pydantic import BaseModel

from v2.db.models import TimeAvailability, UniversityRole, Professor, ProfessorAvailability


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

