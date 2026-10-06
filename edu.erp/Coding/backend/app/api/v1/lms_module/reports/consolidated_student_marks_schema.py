from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class DropdownOption(BaseModel):
    id: int
    name: str


class CurriculumOption(BaseModel):
    academic_batch_id: int
    crclm_id: int
    name: str
    dept_id: Optional[int] = None
    pgm_id: Optional[int] = None


class TermOption(BaseModel):
    crclm_term_id: int
    semester_id: Optional[int] = None
    semester_number: int
    name: str


class SectionOption(BaseModel):
    section_id: int
    section_name: str


class CourseOption(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    semester: Optional[int] = None


class ReportComponent(BaseModel):
    component_id: str
    status: str = "missing"
    occasion_name: str
    max_marks: Optional[float] = None
    marks: Optional[float] = None
    source: Optional[str] = None


class ReportCourse(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    components: List[ReportComponent]
    total_marks: Optional[float] = None
    data_available: Optional[bool] = None


class ReportStudentRow(BaseModel):
    sl_no: int
    student_usn: str
    student_name: str
    regno: Optional[str] = None
    section: Optional[str] = None
    student_identity_status: Optional[str] = None
    courses: List[ReportCourse]


class ResolvedFilters(BaseModel):
    marks_source: Literal["lms", "ems"] = "lms"
    academic_batch_name: Optional[str] = None
    term_name: Optional[str] = None
    start_range: Optional[float] = None
    end_range: Optional[float] = None
    include_absents: bool = False
    department_id: Optional[int] = None
    academic_batch_id: int
    crclm_term_id: Optional[int] = None
    semester_id: Optional[int] = None
    semester_number: Optional[int] = None
    section_id: Optional[int] = None
    section_name: Optional[str] = None
    selected_course_ids: List[int] = Field(default_factory=list)
    include_total_marks: bool
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class ReportData(BaseModel):
    filters: ResolvedFilters
    rows: List[ReportStudentRow]
    courses: List[ReportCourse] = Field(default_factory=list)


class GraphAssessmentSummary(BaseModel):
    component_id: str
    occasion_name: str
    max_marks: Optional[float] = None
    student_count: int
    absent_count: int
    average_marks: Optional[float] = None


class GraphCourseSummary(BaseModel):
    assessments: List[GraphAssessmentSummary] = Field(default_factory=list)
    course_id: int
    course_code: str
    course_title: str
    student_count: int
    average_marks: Optional[float] = None
    highest_marks: Optional[float] = None
    lowest_marks: Optional[float] = None
    min_passing_marks: Optional[float] = None
    pass_count: Optional[int] = None
    fail_count: Optional[int] = None


class GraphData(BaseModel):
    filters: ResolvedFilters
    courses: List[GraphCourseSummary]


class ConsolidatedStudentMarksRequest(BaseModel):
    start_range: Optional[float] = Field(default=None, ge=0, le=100)
    end_range: Optional[float] = Field(default=None, ge=0, le=100)
    include_absents: bool = False
    department_id: Optional[int] = None
    academic_batch_id: int
    semester_id: Optional[int] = Field(
        default=None,
        description="Accepts semester_id or can be omitted when crclm_term_id is provided.",
    )
    crclm_term_id: Optional[int] = Field(
        default=None,
        description="Compatibility alias for the iems_semester semester_id.",
    )
    section_id: Optional[int] = None
    course_ids: Optional[List[int]] = None
    include_total_marks: bool = True
    from_date: Optional[date] = None
    to_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_filters(self):
        if (self.start_range is None) != (self.end_range is None):
            raise ValueError("Select both marks range limits")
        if self.start_range is not None and self.start_range > self.end_range:
            raise ValueError("Marks start range cannot exceed end range")
        if self.from_date is not None or self.to_date is not None:
            raise ValueError("This report uses a marks range; date filters are not supported")
        return self


class ExportRequest(ConsolidatedStudentMarksRequest):
    format: Literal["excel", "pdf", "csv"] = "excel"


class DropdownListResponse(BaseModel):
    status: bool
    message: str
    data: List[DropdownOption]


class CurriculumListResponse(BaseModel):
    status: bool
    message: str
    data: List[CurriculumOption]


class TermListResponse(BaseModel):
    status: bool
    message: str
    data: List[TermOption]


class SectionListResponse(BaseModel):
    status: bool
    message: str
    data: List[SectionOption]


class CourseListResponse(BaseModel):
    status: bool
    message: str
    data: List[CourseOption]


class ConsolidatedStudentMarksResponse(BaseModel):
    status: bool
    message: str
    data: ReportData


class ConsolidatedStudentMarksGraphResponse(BaseModel):
    status: bool
    message: str
    data: GraphData
