from pydantic import BaseModel
from typing import Optional


class GroupMenteeCreate(BaseModel):
    group_mentee_id: Optional[int] = None

    mentors_group_terms_id: int
    group_mentor_id: int
    student_id: int