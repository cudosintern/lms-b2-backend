from pydantic import BaseModel
from typing import Optional


class AddCrossDeptMentorPayload(BaseModel):
    mentor_user_id: int     # the user being assigned as cross-dept mentor
    mentor_dept_id: int     # that user's home department
    curriculum_id: Optional[int] = None


class UpdateCrossDeptMentorPayload(BaseModel):
    assigned_dept_id: int   # re-target the mentor to a different department
