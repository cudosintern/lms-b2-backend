from typing import Any, Optional, List
from pydantic import BaseModel, Field, model_validator, validator, root_validator
from datetime import datetime


class RegistrationSetupRequest(BaseModel):
    curriculum_id: int = Field(..., gt=0)
    term_id: int = Field(..., gt=0)


class RegistrationSetupCreateRequest(BaseModel):
    curriculum_id: int = Field(..., gt=0)
    term_id: int = Field(..., gt=0)
    min_credits: int = Field(..., ge=0, le=30)
    max_credits: int = Field(..., ge=0, le=30)
    enrollment_limit: int = Field(..., gt=0)
    registration_start_datetime: Optional[datetime] = None
    registration_end_datetime: Optional[datetime] = None
    status: str = Field(default="active")
    
    @model_validator(mode='after')
    def validate_credits(self):
        if self.min_credits > self.max_credits:
            raise ValueError('min_credits cannot be greater than max_credits')
        return self


class RegistrationSetupData(BaseModel):
    curriculum_id: int
    term_id: int
    min_credits: int
    max_credits: int
    enrollment_limit: int
    registration_start_datetime: Optional[str] = None
    registration_end_datetime: Optional[str] = None
    status: Optional[Any] = None
    no_of_oe_allowed_by_base_crlm: Optional[int] = None
    no_of_oe_allowed_by_other_crclm: Optional[int] = None


class RegistrationSetupResponse(BaseModel):
    status: bool
    message: str
    data: Optional[RegistrationSetupData] = None


class RegistrationSetupDetailsResponse(BaseModel):
    semester_id: int
    term: str
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    min_credits: Optional[int] = None
    max_credits: Optional[int] = None
    enrollment_limit: Optional[int] = None
    registration_start_datetime: Optional[str] = None
    registration_end_datetime: Optional[str] = None
    no_of_oe_allowed_by_base_crlm: Optional[int] = None
    no_of_oe_allowed_by_other_crclm: Optional[int] = None


# ============================================
# Course Related Schemas
# ============================================

class CourseCreditSummaryItem(BaseModel):
    type_of_course: str
    total_credits: float


class CourseTypeLimitItem(BaseModel):
    course_type_desc: str
    stud_min_crs_enroll: Optional[float] = 0
    stud_max_crs_enroll: Optional[float] = 0
    students_registered: Optional[int] = 0


class StudentRegisteredItem(BaseModel):
    course_type_desc: str
    students_registered: int


class CourseDetailItem(BaseModel):
    crs_code: str
    course_title: str
    credits: float
    students_registered: int


class CourseTypeDetail(BaseModel):
    type: str
    courses: List[CourseDetailItem]


class ExportPDFRequest(BaseModel):
    semester_id: Optional[int] = None
    institute_name: Optional[str] = ""
    department: Optional[str] = ""
    program: str
    curriculum: str
    term: str
    startDate: str
    startTime: str
    endDate: str
    endTime: str
    totalCredits: float
    ownCurriculumElectives: int
    otherCurriculumElectives: int
    minCredits: float
    maxCredits: float
    courseCreditSummary: List[CourseCreditSummaryItem]
    courseTypeLimits: List[CourseTypeLimitItem]
    studentsRegistered: List[StudentRegisteredItem]
    courseDetails: Optional[List[CourseTypeDetail]] = []


class CourseLimitUpdate(BaseModel):
    course_type: str
    min_credits: Optional[float] = 0
    max_credits: Optional[float] = 0
    max_students: Optional[int] = 0


class RegistrationUpdateRequest(BaseModel):
    semester_id: int
    min_credits: Optional[float] = None
    total_credits: Optional[float] = None
    own_curriculum_electives: Optional[int] = None
    other_curriculum_electives: Optional[int] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    course_limits: Optional[List[CourseLimitUpdate]] = []

    @root_validator(skip_on_failure=True)
    def validate_all(cls, values):
        """Validate all fields together"""
        course_limits = values.get('course_limits', [])
        
        if not course_limits:
            return values
        
        for idx, limit in enumerate(course_limits):
            if not limit.course_type:
                raise ValueError(f"course_type is required for item {idx}")
            
            if limit.max_students is not None and limit.max_students < 0:
                raise ValueError(f"max_students cannot be negative for {limit.course_type}")
            if limit.min_credits is not None and limit.min_credits < 0:
                raise ValueError(f"min_credits cannot be negative for {limit.course_type}")
            if limit.max_credits is not None and limit.max_credits < 0:
                raise ValueError(f"max_credits cannot be negative for {limit.course_type}")
        
        return values