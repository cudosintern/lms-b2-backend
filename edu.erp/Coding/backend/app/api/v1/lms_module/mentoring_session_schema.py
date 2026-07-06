from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time

# --- Subgroup for Session Creation ---
class SubGroupCreate(BaseModel):
    sub_group_name: Optional[str] = None
    location: str
    start_date: date
    start_time: time
    end_time: time

# --- Session Creation Request ---
class MentoringSessionCreate(BaseModel):
    mentors_group_terms_id: int
    questionnaire_id: int
    session_agenda: Optional[str] = None
    sub_groups: List[SubGroupCreate]

# --- Message Creation Request ---
class MessageCreate(BaseModel):
    comment: str
    attachment: Optional[str] = None
    suggestion_type: int = 0
    # 0 = generic group message, 1 = individual message
    user_type: Optional[int] = 0 # 0 for Mentor, 1 for Mentee
    mentee_id: Optional[int] = None # required if it's an individual chat

