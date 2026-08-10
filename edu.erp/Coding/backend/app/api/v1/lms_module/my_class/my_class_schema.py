from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

# -------------------------------
# DROPDOWN RESPONSE
# -------------------------------

class CurriculumOut(BaseModel):
    academic_batch_id: int
    academic_batch_name: Optional[str] = None


class TermOut(BaseModel):
    semester_id: int
    semester_name: Optional[str] = None


class CourseOut(BaseModel):
    course_id: int
    course_code: str
    course_title: Optional[str] = None


class SectionOut(BaseModel):
    section_id: int
    section_name: Optional[str] = None


class StudentDropdownResponse(BaseModel):
    curriculum: List[CurriculumOut]
    terms: List[TermOut]
    courses: List[CourseOut]
    sections: List[SectionOut]


# -------------------------------
# CLASS LIST RESPONSE
# -------------------------------

class ClassListItem(BaseModel):
    lesson_schedule_id: int
    topic_id: Optional[int] = None
    course_id: int
    course_name: str
    section_id: int
    section_name: str
    topic_title: Optional[str] = None
    portion_to_be_covered: Optional[str] = None
    status: Optional[str] = "Planned"
    class_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    video_link: Optional[str] = None


class ClassListResponse(BaseModel):
    classes: List[ClassListItem]


# -------------------------------
# CRUD REQUEST SCHEMAS
# -------------------------------

class ClassCreateRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    course_id: int
    section_id: int
    topic_id: Optional[int] = None
    plan_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    video_link: Optional[str] = None


class ClassUpdateRequest(BaseModel):
    topic_id: Optional[int] = None
    plan_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    video_link: Optional[str] = None
    status: Optional[str] = None