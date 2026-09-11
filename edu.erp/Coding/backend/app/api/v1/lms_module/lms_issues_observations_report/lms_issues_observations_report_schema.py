from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ==========================================================
# CREATE ISSUE & OBSERVATION REPORT
# ==========================================================
class IssueObservationCreate(BaseModel):

    academic_batch_id: int

    semester_id: int

    ssd_id: int

    student_usn: str

    report_title: str

    counselling_date: datetime

    mentor_users_id: int

    purpose_of_meeting_desc: Optional[str] = None

    observation_desc: Optional[str] = None

    comm_parent_flag: int = 0

    comm_high_auth_flag: int = 0

    mentor_status: int = 0

    mentee_status: int = 0

    parent_guardian_status: int = 0


# ==========================================================
# UPDATE REPORT
# ==========================================================
class IssueObservationUpdate(BaseModel):

    report_title: Optional[str] = None

    counselling_date: Optional[datetime] = None

    purpose_of_meeting_desc: Optional[str] = None

    observation_desc: Optional[str] = None

    comm_parent_flag: Optional[int] = None

    comm_high_auth_flag: Optional[int] = None

    mentor_status: Optional[int] = None

    mentee_status: Optional[int] = None

    parent_guardian_status: Optional[int] = None


# ==========================================================
# DELETE REPORT
# ==========================================================
class DeleteIssueObservation(BaseModel):

    delete_reason_desc: str


# ==========================================================
# MENTOR STATUS
# ==========================================================
class MentorStatusUpdate(BaseModel):

    mentor_status: int

    mentor_agreed_date: Optional[datetime] = None


# ==========================================================
# MENTEE STATUS
# ==========================================================
class MenteeStatusUpdate(BaseModel):

    mentee_status: int


# ==========================================================
# PARENT STATUS
# ==========================================================
class ParentStatusUpdate(BaseModel):

    parent_guardian_status: int
