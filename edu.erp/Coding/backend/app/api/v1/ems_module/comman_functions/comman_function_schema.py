from pydantic import BaseModel
from typing import List, Optional


class ParamRequestModel(BaseModel):
    flag: Optional[str] = None
    show_all: Optional[bool] = None
    result_year: Optional[str] = None
    event_type: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    course_type: Optional[str] = None
    program_id: Optional[int] = None
    batch: Optional[str] = None
    academic_batch_id: Optional[int] = None
    department_ids: Optional[list] = None
    crs_code: Optional[str] = None


class DepartmentListReq(BaseModel):
    dept_id: Optional[int] = None
    show_delete: Optional[int] = None
    equal_or_not_equal: Optional[bool] = None


class ProgramTypeListReq(BaseModel):
    show_delete: Optional[int] = None


class BloomDomainRequest(BaseModel):
    show_delete: Optional[int] = None
    equal_or_not_equal: Optional[int] = None
    no_batch: Optional[int] = None


class StudentProgramRequest(BaseModel):
    dept_id: Optional[int] = None
    equal_or_not_equal: Optional[int] = None
    show_delete: Optional[int] = 1


class ResultYearRequest(BaseModel):
    flag: Optional[str] = None
    show_all: Optional[bool] = None


class AcademicBatchRequest(BaseModel):
    show_delete: Optional[int] = 0
    program_id: Optional[int] = None


class GetSemesterRequest(BaseModel):
    academic_batch_id: Optional[int] = None
    is_course: Optional[int] = None
    is_first_year: Optional[bool] = False
    is_batch_wise: Optional[bool] = False
    result_year: Optional[str] = None
    flag: Optional[str] = None


class CycleSemesterResponse(BaseModel):
    result_year: Optional[str] = None
    flag: Optional[str] = None


# class SectionListRequest(BaseModel):
#     result_year: Optional[str] = None
#     crs_code: Optional[str] = None
#     academic_batch_id: Optional[str] = None
#     flag: Optional[str] = None
#     not_na: Optional[bool] = None
#     crs_id: Optional[str] = None
#     faculty_id: Optional[str] = None
#     is_class_attendance: Optional[bool] = None

class StudentSectionListRequest(BaseModel):
    result_year: str
    semester: int
    branch_cycle: Optional[int] = None
    not_na: Optional[int] = None
    academic_batch_id: Optional[int] = None
    flag: Optional[int] = None
    is_backlog: Optional[int] = 0


class BatchCycleFilter(BaseModel):
    show_branch: Optional[str] = None
    show_both: Optional[str] = None
    show_na: Optional[str] = None


class GradeTypeRequest(BaseModel):
    show_delete: Optional[bool] = False


class CheckCourseRequest(BaseModel):
    crs_code: str
    program_id: int
    batch_id: int
    result_year: int
    semester: str


class SectionRequest(BaseModel):
    result_year: Optional[int] = None
    crs_code: Optional[str] = None
    academic_batch_id: Optional[int] = None
    flag: Optional[bool] = False
    not_na: Optional[bool] = False
    crs_id: Optional[int] = None
    faculty_id: Optional[int] = None
    is_class_attendance: Optional[bool] = None


class StateRequest(BaseModel):
    country_id: Optional[int] = None


class CityListRequest(BaseModel):
    state_id: Optional[int] = None
    name: Optional[str] = None
    status: Optional[int] = 1


class CycleRequest(BaseModel):
    academic_batch_id: int
    semester: int


class SoftDeleteRequest(BaseModel):
    flag: Optional[str]
    record_id: Optional[int] = None
    status: Optional[int] = None


class SemesterRequest(BaseModel):
    academic_batch_id: Optional[int]


class SemesterCheckRequest(BaseModel):
    academic_batch_id: int


class FetchStudentCourseRequest(BaseModel):
    result_year: Optional[str] = None
    crs_code: Optional[str] = None
    occasion: Optional[int] = None
    section_name: Optional[str] = None
    v_value: Optional[str] = None
    absentee: Optional[bool] = None
    program_id: Optional[int] = None
    batch_id: Optional[int] = None
    semester: Optional[int] = None
    usn: Optional[str] = None
    sessions: Optional[int] = None
    attendance_date: Optional[str] = None
    flag: Optional[str] = None
    is_backlog: Optional[bool] = None
    is_cycle_wise: Optional[bool] = None
    reeval: Optional[str] = None  # old code take key as eval_type
    lab_course_batch_id: Optional[int] = None
    cycle: Optional[int] = None
    is_extra_class: Optional[bool] = None
    challengereeval: Optional[bool] = None
    regno: Optional[str] = None  # Add regno field if necessary
    org_id: Optional[int] = None  # Add org_id if it's missing

    # Override the Pydantic method to convert the integer to a boolean for is_backlog
    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.is_backlog, int):
            self.is_backlog = bool(self.is_backlog)


class SetApproveRequest(BaseModel):
    result_year: Optional[str] = None
    crs_code: Optional[str] = None
    section_name: Optional[str] = None
    batch_id: Optional[int] = None
    program_id: Optional[int] = None
    sem: Optional[int] = None
    approve_type: Optional[str] = None
    is_backlog: Optional[int] = None
    batch_cycle_id: Optional[int] = None


class CheckGradeEvaluateRequest(BaseModel):
    result_year: str
    program_id: Optional[int] = None
    batch_id: Optional[int] = None
    batch_cycle_id: Optional[int] = None
    is_backlog: bool
    crs_code: str


class ComputeOpenElectiveCIARequest(BaseModel):
    result_year: str
    crs_code: str
    section_name: Optional[str] = None
    pgm_id: Optional[int] = None
    academic_batch_id: Optional[int] = None
    semester: Optional[int] = None


class StudentCourseRequestParams(BaseModel):
    result_year: str
    crs_code: str
    occasion: Optional[str] = None
    section: Optional[str] = None
    v_value: Optional[str] = None
    absentee: Optional[int] = None
    program_id: Optional[int] = None
    batch_id: Optional[int] = None
    semester: Optional[int] = None
    usn: Optional[str] = None
    sessions: Optional[int] = None
    attendance_date: Optional[str] = None  # Use `date` type if it's always a date value
    is_backlog: Optional[int] = 0
    select_type: int


class GetAcademicBatchRequest(BaseModel):
    show_delete: Optional[int] = None
    program_id: Optional[int] = None


class GetProgramOptionsRequest(BaseModel):
    dept_id: Optional[int] = None
    is_encoded: Optional[bool] = None
    show_delete: Optional[bool] = None
    program_type: Optional[int] = None


class GetSemesterListRequest(BaseModel):
    academic_batch_id: Optional[int] = None
    is_course: Optional[int] = None
    is_first_year: Optional[bool] = None
    is_batch_wise: Optional[bool] = None
    result_year: Optional[int] = None
    flag: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: Optional[str]


class ChangePasswordRequest(BaseModel):
    oldpassword: str
    newpassword: str
    confirmpassword: str


class CheckEligibilityRequest(BaseModel):
    result_year: str
    crs_code: str
    is_backlog: bool


class IsResultYearBacklog(BaseModel):
    program_id: Optional[int] = None
    batch_id: Optional[int] = None
    result_year: Optional[str]


class CheckRevalDatesRequest(BaseModel):
    result_year: str
    eval_type: int
