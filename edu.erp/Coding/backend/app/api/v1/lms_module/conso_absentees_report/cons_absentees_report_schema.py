from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# -------- Dropdown --------
class DropdownResponse(BaseModel):
    id: int
    name: str


# -------- Date Info --------
class DateInfoResponse(BaseModel):
    latest_attendance_date: Optional[date]
    scheduled_dates: List[date]


# -------- Main Report Request --------
class ReportRequest(BaseModel):
    start_date: date
    end_date: date

    department_ids: Optional[List[int]] = None
    program_ids: Optional[List[int]] = None
    curriculum_ids: Optional[List[int]] = None
    semester_ids: Optional[List[int]] = None   # ✅ ADD THIS
    section_ids: Optional[List[int]] = None


# -------- Main Report Response --------
class ReportRow(BaseModel):
    department: str
    term: str
    course: str
    section: str
    absent_count: int


# -------- Drilldown Request --------
class DrilldownRequest(BaseModel):
    course_id: int
    section_id: int
    start_date: date
    end_date: date


# -------- Drilldown Response --------
class DrilldownRow(BaseModel):
    date: date
    student_name: str
    usn: str
    parent_contact: Optional[str]
    student_contact: Optional[str]