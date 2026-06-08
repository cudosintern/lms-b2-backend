from pydantic import BaseModel
from typing import Optional

class QuestionTypeCreate(BaseModel):
    que_type_id: Optional[int] = None
    que_type_name: str
    que_type_desc: Optional[str] = None