from pydantic import BaseModel, Field
from typing import Optional

class StudentQuizIdentity(BaseModel):
    student_id: int = Field(..., gt=0)

class StudentQuizListRequest(StudentQuizIdentity):
    academic_batch_id: Optional[int] = Field(None, gt=0)
    semester_id: Optional[int] = Field(None, gt=0)
    crs_id: Optional[int] = Field(None, gt=0)
    section_id: Optional[int] = Field(None, gt=0)

class QuizAnswerItem(BaseModel):
    qq_id: int = Field(..., gt=0)
    qq_option_id: Optional[int] = Field(None, gt=0)
    qq_option_ids: list[int] = Field(default_factory=list)
    answer_text: Optional[str] = None

    def option_ids(self):
        return set(self.qq_option_ids) | ({self.qq_option_id} if self.qq_option_id else set())

class StudentQuizSubmitRequest(StudentQuizIdentity):
    answers: list[QuizAnswerItem] = Field(default_factory=list)

class StudentQuizSaveRequest(StudentQuizIdentity):
    answer: QuizAnswerItem
