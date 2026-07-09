from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class CurriculumResponse(BaseModel):
    curriculum_id: int
    curriculum_name: str

class CurriculumListResponse(BaseModel):
    status: str
    data: List[CurriculumResponse]

class TermResponse(BaseModel):
    term_id: int
    term_name: str

class TermListResponse(BaseModel):
    status: str
    data: List[TermResponse]

class GroupResponse(BaseModel):
    group_id: int
    group_name: str
    curriculum_id: int

class GroupListResponse(BaseModel):
    status: str
    data: List[GroupResponse]

class PersonalInfo(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None
    curriculum: Optional[str] = None

class AddressDetail(BaseModel):
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

class Addresses(BaseModel):
    permanent: Optional[AddressDetail] = None
    correspondence: Optional[AddressDetail] = None

class EducationDetails(BaseModel):
    tenth_percentage: Optional[float] = None
    tenth_board: Optional[str] = None
    tenth_year: Optional[int] = None
    twelfth_percentage: Optional[float] = None
    twelfth_board: Optional[str] = None
    twelfth_year: Optional[int] = None

class QuestionnaireResponse(BaseModel):
    question_id: Optional[int] = None
    question_text: Optional[str] = None
    response_value: Optional[str] = None
    submitted_at: Optional[str] = None

class Occasion(BaseModel):
    occasion_name: Optional[str] = None
    secured_marks: Optional[float] = None
    total_marks: Optional[float] = None

class MarkDetail(BaseModel):
    semester: Optional[int] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    occasions: Optional[List[Occasion]] = None

class StudentDetailData(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    addresses: Optional[Addresses] = None
    education_details: Optional[EducationDetails] = None
    questionnaire_responses: Optional[List[QuestionnaireResponse]] = None
    marks_details: Optional[List[MarkDetail]] = None
    attendance_details: Optional[List[CourseAttendance]] = None

from typing import Union
class StudentInfoResponse(BaseModel):
    status: str
    data: Union[StudentDetailData, List[StudentDetailData]]

class CourseAttendance(BaseModel):
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    attendance_percentage: Optional[float] = None

class SemesterAttendance(BaseModel):
    semester: Optional[int] = None
    semester_attendance_percentage: Optional[float] = None
    courses: Optional[List[CourseAttendance]] = None

class AttendanceResponse(BaseModel):
    status: str
    data: List[SemesterAttendance]

class CourseMarks(BaseModel):
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    marks_percentage: Optional[float] = None
    occasions: Optional[List[Occasion]] = None

class SemesterMarks(BaseModel):
    semester: Optional[int] = None
    semester_marks_percentage: Optional[float] = None
    courses: Optional[List[CourseMarks]] = None

class MarksResponse(BaseModel):
    status: str
    data: List[SemesterMarks]

class CoursePerformance(BaseModel):
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    attendance_percentage: Optional[float] = None
    marks_percentage: Optional[float] = None
    occasions: Optional[List[Occasion]] = None

class SemesterPerformance(BaseModel):
    semester: Optional[int] = None
    semester_attendance_percentage: Optional[float] = None
    semester_marks_percentage: Optional[float] = None
    courses: Optional[List[CoursePerformance]] = None

class PerformanceResponse(BaseModel):
    status: str
    data: List[SemesterPerformance]

