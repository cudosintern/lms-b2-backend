from pydantic import BaseModel
from typing import Optional


class GroupMentorCreate(BaseModel):
    group_mentor_id: Optional[int] = None

    mentors_group_terms_id: int
    mentor_id: int