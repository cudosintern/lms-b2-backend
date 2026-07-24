from typing import Optional, List, Union
from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    mentee_id: Optional[int] = None
    comment: Optional[str] = None
    attachment: Optional[str] = None


class OptionCreateCustom(BaseModel):
    questionnaire_options_id: Optional[int] = None
    que_option: str
    specify_flag: bool = False


class QuestionCreateCustom(BaseModel):
    questionnaire_que_id: Optional[int] = None
    que_type_id: int
    que_no: int
    question: str
    questionnaire_type_id: int
    que_is_mandatory: bool = True
    options: List[Union[str, OptionCreateCustom]] = []


class QuestionnaireSaveCustom(BaseModel):
    questionnaire_id: Optional[int] = None
    questionnaire_name: str
    message_to_mentees: Optional[str] = None
    access_level: int = 0
    parent_id: Optional[int] = None
    questions: List[QuestionCreateCustom]
