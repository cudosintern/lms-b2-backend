from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class CurriculumResponse(BaseModel):
    id: int
    name: str

class TermResponse(BaseModel):
    id: int
    name: str

class CourseResponse(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    section: Optional[str] = None
    instructor: Optional[str] = None

class TopicResponse(BaseModel):
    topic_id: int
    topic_code: str
    topic_title: str
    topic_content: Optional[str] = None

class TopicStatusResponse(BaseModel):
    topic_id: int
    status: str  # LS Not Added, LS Planned, Completed, Pending
    color: str   # Blue, Yellow, Green, Red

class TopicDatesResponse(BaseModel):
    topic_id: int
    dates: List[date]

class CourseTopicStatusItem(BaseModel):
    topic_id: int
    topic_code: str
    topic_title: str
    status: str
    color: str
    class_dates: List[date]

class CourseTopicsStatusResponse(BaseModel):
    course_id: int
    section_id: int
    topics: List[CourseTopicStatusItem]

class TopicScheduleCreate(BaseModel):
    topic_id: int
    academic_batch_id: int
    semester_id: int
    course_id: int
    conduction_date: Optional[date] = None
    portion_ref: Optional[str] = None
    portion_per_hour: Optional[float] = None
    created_by: Optional[int] = None

class TopicScheduleUpdate(BaseModel):
    conduction_date: Optional[date] = None
    portion_ref: Optional[str] = None
    portion_per_hour: Optional[float] = None
    modified_by: Optional[int] = None