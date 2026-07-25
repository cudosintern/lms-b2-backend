from datetime import date,time
from pydantic import BaseModel
from typing import Optional,List

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

class GroupCommentCreate(BaseModel):
    schedule_id: int
    comment: str
    attachment: Optional[str] = None

class IndividualCommentCreate(BaseModel):
    schedule_id: int
    mentee_id: int
    comment: str
    attachment: Optional[str] = None


class QuestionnaireResponseRequest(BaseModel):
    schedule_id: int
    student_id: int


class SessionMenteeRequest(BaseModel):
    schedule_id: int
    sub_group_id: Optional[int] = None

class MenteeResponseRequest(BaseModel):
    schedule_id: int
    student_id: int

class SaveGenericCommentRequest(BaseModel):
    schedule_id: int
    comment: str
    suggestion_type: int = 0
    user_type: int = 0

    attachment: Optional[str] = None

class SaveIndividualCommentRequest(BaseModel):
    schedule_id: int
    mentee_id: int
    comment: str
    attachment: Optional[str] = None

    suggestion_type: int = 0

    # 1 Faculty
    # 2 Student
    from_user_type: int = 1

class GroupCommentRequest(BaseModel):
    schedule_id: int

class IndividualCommentRequest(BaseModel):
    schedule_id: int
    mentee_id: int

class MenteeResponseRequest(BaseModel):
    student_id: int
    schedule_id: int


class UpdateSessionStatusRequest(BaseModel):
    schedule_id: int
    sub_group_id: int
    status: str