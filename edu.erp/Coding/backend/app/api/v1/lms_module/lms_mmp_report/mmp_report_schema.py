from pydantic import BaseModel

class StudentListRequest(BaseModel):
    academic_batch_id: int
    mentors_group_id: int
    semester_id: int

class StudentQuestionnaireRequest(BaseModel):

    academic_batch_id: int

    mentors_group_id: int

    semester_id: int

    student_usn: str

class StudentDetailsRequest(BaseModel):

    academic_batch_id: int

    mentors_group_id: int

    semester_id: int

    student_usn: str

class StudentQuestionnaireRequest(BaseModel):

    academic_batch_id: int

    mentors_group_id: int

    semester_id: int

    student_usn: str


class AcademicBatchResponse(BaseModel):
    academic_batch_id: int
    academic_batch_code: str
    academic_batch_desc: str | None = None

    class Config:
        from_attributes = True