from pydantic import BaseModel
from typing import Optional

class QuestionnaireCreate(BaseModel):
    questionnaire_id: Optional[int] = None
    questionnaire_name: str
    message_to_mentees: Optional[str] = None
    access_level: int = 0
    parent_id: Optional[int] = None