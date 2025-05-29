from dataclasses import dataclass

from litestar.datastructures import UploadFile


@dataclass
class NewCommissionForm:
    file: UploadFile
    title: str | None = None
