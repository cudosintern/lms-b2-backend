from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CrossDepartmentMentorBase(BaseModel):
    mentor_id: int
    academic_batch_ids: Optional[List[int]] = [] # For lms_cross_dept_users_crclms

class CrossDepartmentMentorCreate(CrossDepartmentMentorBase):
    pass

class CrossDepartmentMentorUpdate(BaseModel):
    status: Optional[int] = None
    academic_batch_ids: Optional[List[int]] = None

class MentorFromOtherDeptResponse(BaseModel):
    mapping_id: int
    mentor_id: int
    first_name: str
    last_name: Optional[str] = ""
    email: Optional[str] = None
    home_dept_id: int
    home_dept_name: str
    status: int

    class Config:
        from_attributes = True

class MentorToOtherDeptResponse(BaseModel):
    mapping_id: int
    mentor_id: int
    first_name: str
    last_name: Optional[str] = ""
    email: Optional[str] = None
    mapped_dept_id: int
    mapped_dept_name: str
    status: int

    class Config:
        from_attributes = True

class AvailableMentorResponse(BaseModel):
    mentor_id: int
    first_name: str
    last_name: Optional[str] = ""
    email: Optional[str] = None
    home_dept_id: int
    home_dept_name: str

    class Config:
        from_attributes = True

class CrossDepartmentMentorResponseWrapper(BaseModel):
    status: str
    data: List[MentorFromOtherDeptResponse]

class CrossDepartmentMentorToResponseWrapper(BaseModel):
    status: str
    data: List[MentorToOtherDeptResponse]

class AvailableMentorResponseWrapper(BaseModel):
    status: str
    data: List[AvailableMentorResponse]

class FilterDepartmentResponse(BaseModel):
    dept_id: int
    dept_name: str
    dept_acronym: Optional[str] = None
    dept_code_usn: Optional[str] = None
    dept_description: Optional[str] = None
    status: bool = True

    class Config:
        from_attributes = True

class FilterDepartmentResponseWrapper(BaseModel):
    status: str
    data: List[FilterDepartmentResponse]

