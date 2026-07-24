from pydantic import BaseModel
from typing import List, Optional


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

class AvailableCourseRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    section_id: int

    parent_academic_batch_id: int
    parent_semester_id: int

    student_id: int

class CourseRegistrationRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    section_id: int

    parent_academic_batch_id: int
    parent_semester_id: int

    student_id: int

    open_elective_flag: int = 0

class SectionListRequest(BaseModel):
    academic_batch_id: int
    semester_id: int


class SectionResponse(BaseModel):
    section_id: int
    section_name: str

class RegisteredCourseRequest(BaseModel):
    parent_academic_batch_id: int
    parent_semester_id: int
    student_id: int