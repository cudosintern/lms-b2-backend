from pydantic import BaseModel
from typing import Optional


class MentorsGroupCreate(BaseModel):
    mentors_group_id: Optional[int] = None

    academic_batch_id: int
    semester_id: int

    config_type_id: Optional[int] = None
    questionnaire_id: Optional[int] = None

    mentors_pgm_title: str