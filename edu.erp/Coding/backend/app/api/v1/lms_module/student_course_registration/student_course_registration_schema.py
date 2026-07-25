from pydantic import BaseModel
from typing import List


class SemesterResponse(BaseModel):
    semester_id: int
    semester: int
    semester_desc: str


class AcademicBatchSemesterResponse(BaseModel):
    academic_batch_id: int
    academic_batch_code: str
    academic_batch_desc: str
    semesters: List[SemesterResponse]

class RegistrationStatusResponse(BaseModel):
    registration_open: bool
    academic_batch_id: int
    semester_id: int
    registration_start: Optional[str] = None
    registration_end: Optional[str] = None