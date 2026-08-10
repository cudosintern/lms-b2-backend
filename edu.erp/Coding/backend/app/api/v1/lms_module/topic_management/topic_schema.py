from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class CurriculumListRequest(BaseModel):
    pass  # No parameters needed

class SemesterListRequest(BaseModel):
    pass  # No parameters needed

class CourseListRequest(BaseModel):
    curriculum_id: Optional[int] = None
    semester_id: Optional[int] = None

class TopicSectionListRequest(BaseModel):
    course_id: int
    semester_id: int

class ImportTopicRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    course_id: int
    section_id: int
    instructor_id: Optional[int] = None
    topic_ids: Optional[List[int]] = None
    created_by: int = 1

class TopicCreateRequest(BaseModel):
    topic_code: str
    topic_title: str
    topic_content: Optional[str] = None
    academic_batch_id: int
    semester_id: int
    course_id: int
    created_by: Optional[int] = 1
    
class TopicListRequest(BaseModel):
    academic_batch_id: int
    course_id: int
    semester_id: int
    section_id: Optional[int] = None
    user_id: Optional[int] = None


# ✅ Instructor list schema
class InstructorListRequest(BaseModel):
    course_id: int


# ✅ Import selected topics
class ImportCudosTopicsRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    course_id: int
    section_id: int
    instructor_id: int
    topic_ids: List[int]
    created_by: int = 1


# ✅ Topic schedule request
class TopicScheduleRequest(BaseModel):
    mapping_id: int

# ✅ NEW: Add New Schedule Request Schema
class AddScheduleRequest(BaseModel):
    mapping_id: int
    session_number: int
    academic_batch_id: Optional[int] = None
    conduction_date: Optional[date] = None
    created_by: int = 1

# ✅ Update instructor for a topic  
class UpdateInstructorRequest(BaseModel):
    course_instructor_id: Optional[int] = None
    instructor_id: Optional[int] = None
