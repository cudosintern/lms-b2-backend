from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StudentRequest(BaseModel):
    student_id: int = Field(..., gt=0)


class ScheduleListRequest(StudentRequest):
    academic_batch_id: int = Field(..., gt=0)
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class SessionRequest(StudentRequest):
    schedule_id: int = Field(..., gt=0)


class DeleteAttachmentRequest(SessionRequest):
    generic_comment_id: int = Field(..., gt=0)


class QuestionnaireAnswer(BaseModel):
    questionnaire_que_id: int = Field(..., gt=0)
    selected_option_ids: List[int] = Field(default_factory=list)
    text_answer: Optional[str] = None
    specifications: Dict[int, str] = Field(default_factory=dict)


class SaveQuestionnaireResponse(SessionRequest):
    sub_group_date_id: int = Field(..., gt=0)
    answers: List[QuestionnaireAnswer]
