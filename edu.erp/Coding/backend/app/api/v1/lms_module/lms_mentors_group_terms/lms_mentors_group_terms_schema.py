from pydantic import BaseModel
from typing import Optional


class MentorsGroupTermCreate(BaseModel):
    mentors_group_terms_id: Optional[int] = None

    mentors_group_id: int
    academic_batch_id: int
    semester_id: int