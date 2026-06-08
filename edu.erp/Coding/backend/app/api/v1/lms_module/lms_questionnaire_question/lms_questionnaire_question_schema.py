from typing import Optional
from pydantic import BaseModel


class QuestionnaireQuestionCreate(BaseModel):
    questionnaire_que_id: Optional[int] = None

    questionnaire_id: int

    que_type_id: int

    que_no: int

    question: str

    questionnaire_type_id: int

    que_is_mandatory: bool = True