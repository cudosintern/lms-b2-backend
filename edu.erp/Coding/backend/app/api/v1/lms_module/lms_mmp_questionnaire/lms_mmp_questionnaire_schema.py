from pydantic import BaseModel
from typing import Optional, List


class OptionCreate(BaseModel):
    questionnaire_options_id: Optional[int] = None
    que_option: str
    specify_flag: bool = False


class QuestionCreate(BaseModel):
    questionnaire_que_id: Optional[int] = None

    que_type_id: int
    que_no: int
    question: str

    questionnaire_type_id: int
    que_is_mandatory: bool = True

    options: List[OptionCreate] = []


class QuestionnaireSave(BaseModel):
    questionnaire_id: Optional[int] = None

    questionnaire_name: str
    message_to_mentees: Optional[str] = None

    access_level: int = 0
    parent_id: Optional[int] = None

    questions: List[QuestionCreate]