from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


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


class GraphCourseSummary(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    student_count: int
    average_marks: float
    highest_marks: float
    lowest_marks: float
    min_passing_marks: Optional[float] = None
    pass_count: Optional[int] = None
    fail_count: Optional[int] = None


class GraphData(BaseModel):
    filters: ResolvedFilters
    courses: List[GraphCourseSummary]


class ExportRequest(BaseModel):
    format: str = Field(default="excel", pattern="^(excel|pdf|csv)$")
    department_id: Optional[int] = None
    academic_batch_id: int
    semester_id: Optional[int] = None
    crclm_term_id: Optional[int] = None
    section_id: Optional[int] = None
    course_ids: Optional[List[int]] = None
    include_total_marks: bool = True
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class ConsolidatedStudentMarksRequest(BaseModel):
    department_id: Optional[int] = None
    academic_batch_id: int
    semester_id: Optional[int] = Field(
        default=None,
        description="Accepts semester_id or can be omitted when crclm_term_id is provided.",
    )
    crclm_term_id: Optional[int] = Field(
        default=None,
        description="UI term id from iems_crclm_term. Resolved internally to semester.",
    )
    section_id: Optional[int] = None
    course_ids: Optional[List[int]] = None
    include_total_marks: bool = True
    from_date: Optional[date] = None
    to_date: Optional[date] = None


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


class ExportPlaceholderData(BaseModel):
    format: str
    filters: ResolvedFilters
    export_ready: bool
    message: str


class ExportPlaceholderResponse(BaseModel):
    status: bool
    message: str
    data: ExportPlaceholderData
