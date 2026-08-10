from pydantic import BaseModel
from typing import Optional

class StudentQuizListRequest(BaseModel):
    student_id: Optional[int] = None
    academic_batch_id: int
    semester_id: int
    crs_id: int

class QuizAnswerItem(BaseModel):
    qq_id: int
    qq_option_id: Optional[int] = None   # None if student skipped the question

class StudentQuizSubmitRequest(BaseModel):
    ssd_id: int
    student_usn: Optional[str] = ''      # may be empty if USN not stored in mapping
    answers: list[QuizAnswerItem]
