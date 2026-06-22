from datetime import date,time
from pydantic import BaseModel
from typing import List

class SessionDateCreate(BaseModel):

    start_date: date
    end_date: date

    start_time: time
    end_time: time

class SubGroupCreate(BaseModel):

    sub_group_name: str

    location: str

    dates: List[SessionDateCreate]

    mentee_ids: List[int]

class MentoringSessionCreate(BaseModel):

    academic_batch_id: int

    mentors_group_id: int

    semester_id: int

    session_agenda: str

    sub_groups: List[SubGroupCreate]