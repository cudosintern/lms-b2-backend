from typing import Optional
from pydantic import BaseModel


class QuestionnaireQuestionOptionCreate(
    BaseModel
):
    questionnaire_options_id: Optional[int] = None

    questionnaire_que_id: int

    que_option: str

    specify_flag: bool = False