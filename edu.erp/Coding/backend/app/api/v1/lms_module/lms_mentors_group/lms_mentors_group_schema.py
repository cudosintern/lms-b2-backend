from pydantic import BaseModel
from typing import Optional, List

class MentorsGroupCreate(BaseModel):

    mentors_group_id: Optional[int] = None

    academic_batch_id: int

    config_type_id: int

    questionnaire_id: int

    mentors_pgm_title: str

    semester_ids: List[int]


class MentorsGroupEdit(BaseModel):
    mentors_group_id: int
    mentors_pgm_title: str

class MentorMapRequest(BaseModel):
    mentors_group_id: int
    mentor_ids: List[int]


class MenteeMapRequest(BaseModel):
    mentors_group_id: int
    mentor_ids: List[int]
    mentee_ids: List[int]