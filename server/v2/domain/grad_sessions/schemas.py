from dataclasses import dataclass

from litestar.datastructures import UploadFile

from pydantic import BaseModel

from v2.db.models import TimeAvailability


@dataclass
class NewCommissionForm:
    file: UploadFile
    title: str | None = None


@dataclass
class UpdateProfessorAvailability(BaseModel):
    professor_id: int
    availability: TimeAvailability
