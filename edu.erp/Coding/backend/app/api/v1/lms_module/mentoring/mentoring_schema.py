from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class CreateSessionPayload(BaseModel):
    curriculum_id: int
    group_id: Optional[int] = None
    session_date: str
    session_time: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None


class SendChatPayload(BaseModel):
    mentee_id: Optional[int] = None
    comment: Optional[str] = ""
    attachment: Optional[str] = None
