from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# Request Schemas
# ============================================================================
class TimetableFilterRequest(BaseModel):
    academic_batch_id: Optional[int] = None      # This maps to academic_batch_id
    semester_id: Optional[int] = None       # This maps to semester_id
    section_id: Optional[int] = None        # This maps to section_id
    tt_detail_id: Optional[int] = None


class GenerateTimetableRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    section_id: int
    crclm_title: str = ""
    start_date: str
    end_date: str
    start_time: str
    end_time: str
    tt_detail_id: int | None = None
    lms_reg_byp_flag: int = 0


class ScheduleClassRequest(BaseModel):
    tt_detail_id: int
    day_val_array: List[str]
    class_start_time_array: List[str]
    class_end_time_array: List[str]
    crs_id: List[int]
    crs_mode: List[int]
    batch: Optional[List[str]] = None
    crs_title: str


class UpdateClassRequest(BaseModel):
    time_table_id: int
    tt_detail_id: int
    crs_id: int
    old_crs_id: int
    class_start_time: str
    class_end_time: str


class DeleteTimetableRequest(BaseModel):
    del_tt_detail_id: int
    login_pwd: str


class CompensateClassRequest(BaseModel):
    comp_tt_detail_id: int
    from_val: int  # renamed from 'from' as it's a reserved keyword
    to_val: int    # renamed from 'to' as it's a reserved keyword
    term: int
    section: int
    confirm: int = 0


class CompensateClassDateRequest(BaseModel):
    comp_date_tt_detail_id: int
    from_date: str
    to_date: str
    term: int
    section: int
    confirm_date: int = 0


class CheckOverlapRequest(BaseModel):
    class_start_time: str
    class_end_time: str
    tt_detail_id: int
    crs_id: List[int]
    day: str
    start_date: str
    end_date: str
    sec_id: int
    batch_id: Optional[List[str]] = None


class SelectCourseRequest(BaseModel):
    term_id: int
    crs_mode: List[int]


class SelectBatchRequest(BaseModel):
    crclm_id: int
    crs_id: List[int]
    sec_id: int


class EditClassCourseRequest(BaseModel):
    crs_id: int
    term_id: int
    crs_mode: int


class FetchTermRequest(BaseModel):
    academic_batch_id: int


class GetSectionRequest(BaseModel):
    academic_batch_id: int
    semester_id: int


# ============================================================================
# Response Schemas
# ============================================================================

class TermResponse(BaseModel):
    crclm_term_id: int
    term_name: str


class SectionResponse(BaseModel):
    id: int
    name: str


class CourseOptionResponse(BaseModel):
    crs_id: int
    crs_code: str
    crs_title: str
    crs_mode: Optional[int] = None
    selected: Optional[bool] = False


class BatchOptionResponse(BaseModel):
    batch_id: int
    batch_name: str
    crs_id: int
    crs_code: str
    parent_id: int


class TTOptionResponse(BaseModel):
    tt_detail_id: Optional[int] = None
    label: str
    selected: bool = False


class DayResponse(BaseModel):
    day_id: int
    week_day_name: str


class ClassDetailResponse(BaseModel):
    time_table_id: int
    tt_detail_id: int
    day_id: int
    week_day_name: str
    crs_id: int
    crs_code: str
    class_start_time: str
    class_end_time: str
    extra_class_flag: int = 0
    batch_names: Optional[List[str]] = None
    course_instructor: Optional[str] = None
    crs_owner: Optional[str] = None
    attendance_taken: int = 0


class TTDetailsResponse(BaseModel):
    tt_detail_id: int
    tt_start_date: str
    tt_end_date: str
    tt_start_time: str
    tt_end_time: str
    lms_reg_byp_flag: int = 0
    crclm_name: Optional[str] = None
    term_name: Optional[str] = None
    mt_details_name: Optional[str] = None


class TimetableResponse(BaseModel):
    status: int
    tt_detail_id: Optional[int] = None
    tt_start_date: Optional[str] = None
    tt_end_date: Optional[str] = None
    tt_start_time: Optional[str] = None
    tt_end_time: Optional[str] = None
    tt_time_slot_gap: int = 5
    lms_reg_byp_flag: int = 0
    tt_options: List[TTOptionResponse] = []
    week_days: List[str] = []
    days: List[DayResponse] = []
    time_slots: List[str] = []
    tt_details: Optional[TTDetailsResponse] = None
    classes: List[ClassDetailResponse] = []
    crs_ids: List[Dict] = []


class OverlapResponse(BaseModel):
    class_overlap_day: str = ""
    class_overlap_time: str = ""
    course: str = ""
    faculty_name: str = ""
    another_class: str = ""

class ResetTimetableDateRequest(BaseModel):
    tt_detail_id: int
    end_date: str

class ExportTimetableRequest(BaseModel):
    expo_tt_detail_id: int


class TimetableDetailsRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    section_id: int