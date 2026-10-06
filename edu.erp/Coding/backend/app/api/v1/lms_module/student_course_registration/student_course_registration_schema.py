from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class StudentRequest(BaseModel):
    student_id: int = Field(..., gt=0)


class TermListRequest(StudentRequest):
    academic_batch_id: int = Field(..., gt=0)


class SectionListRequest(TermListRequest):
    semester_id: int = Field(..., gt=0)


class AvailableCourseRequest(SectionListRequest):
    section_id: Optional[int] = Field(None, gt=0)
    all_curricula: bool = False


class CourseSelection(BaseModel):
    academic_batch_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    crs_id: int = Field(..., gt=0)
    section_id: int = Field(..., gt=0)


class CourseRegistrationRequest(AvailableCourseRequest):
    course_ids: List[int] = Field(default_factory=list, max_length=100)
    course_selections: List[CourseSelection] = Field(default_factory=list, max_length=100)

    @model_validator(mode='after')
    def unique_positive_courses(self):
        if bool(self.course_ids) == bool(self.course_selections):
            raise ValueError('Provide either course_ids or course_selections')
        if self.course_ids and not self.section_id:
            raise ValueError('section_id is required with course_ids')
        ids = [course.crs_id for course in self.course_selections]
        if len(set(ids)) != len(ids):
            raise ValueError('Select each course only once')
        if any(course <= 0 for course in self.course_ids) or len(set(self.course_ids)) != len(self.course_ids):
            raise ValueError('course_ids must contain unique positive course IDs')
        return self


class UnregisterRequest(StudentRequest):
    registration_id: int = Field(..., gt=0)


class RegisteredCourseRequest(StudentRequest):
    # Accepted for compatibility, but authoritative context is resolved from the student.
    parent_academic_batch_id: Optional[int] = Field(None, gt=0)
    parent_semester_id: Optional[int] = Field(None, gt=0)
