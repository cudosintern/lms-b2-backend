"""Pydantic schemas matching the supplied attendance table fields."""
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class AttendanceHeaderCreate(BaseModel):
    academic_batch_id: int | None = Field(None, gt=0)
    semester_id: int | None = Field(None, gt=0)
    crs_id: int | None = Field(None, gt=0)
    section_id: int | None = Field(None, gt=0)
    attendance_date: str | None = Field(None, max_length=50)
    created_by: int | None = None
    created_at: date | None = None
    modified_by: int | None = None
    modified_at: date | None = None
    status: int | None = None
    attendance_class_count: int | None = None
    tt_detail_id: int | None = Field(None, gt=0)


class AttendanceHeaderRead(AttendanceHeaderCreate):
    model_config = ConfigDict(from_attributes=True)
    attendance_id: int


class StudentAttendanceCreate(BaseModel):
    attendance_id: int | None = Field(None, gt=0)
    ssd_id: int | None = Field(None, gt=0)
    student_usn: str | None = Field(None, max_length=20)
    a_type_id: int = Field(..., ge=0)
    attendance_status: str | None = Field(None, max_length=10)
    refer_absent_status: int | None = None
    remarks: str | None = None
    activity: int | None = 0
    sms_sent: int | None = 0
    notification_sent: int = 0
    accept_flag: int | None = 0
    stud_attendance_doc_url: str | None = Field(None, max_length=1000)


class StudentAttendanceRead(StudentAttendanceCreate):
    model_config = ConfigDict(from_attributes=True)
    stud_attendance_id: int
