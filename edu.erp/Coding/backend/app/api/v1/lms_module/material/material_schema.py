from pydantic import BaseModel
from typing import List, Optional


class MaterialCreateRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    course_id: int
    section_id: int
    title: str
    description: Optional[str] = None
    created_by: int


class MaterialListRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    course_id: int
    section_id: int


class ShareMaterialRequest(BaseModel):
    material_id: int
    academic_batch_id: int
    section_id: int
    student_usns: List[str]

class MaterialMappingRequest(BaseModel):
    material_id: int


class MaterialMappingResponse(BaseModel):
    student_usn: str
    student_name: str
    section_id: int


class UpdateMaterialRequest(BaseModel):
    title: str
    description: Optional[str] = None
