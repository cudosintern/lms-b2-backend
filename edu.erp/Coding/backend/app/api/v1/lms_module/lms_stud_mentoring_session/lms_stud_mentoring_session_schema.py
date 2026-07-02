from typing import List, Optional
from pydantic import BaseModel


class QuestionnaireAnswer(BaseModel):
    questionnaire_que_id: int
    selected_option_ids: List[int] = []
    text_answer: Optional[str] = None


class SaveQuestionnaireResponse(BaseModel):
    student_id: int
    schedule_id: int
    sub_group_date_id: int
    answers: List[QuestionnaireAnswer]