from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

class LabCategoryBase(BaseModel):
    lab_cat_name: str
    lab_cat_description: Optional[str] = None

    @field_validator('lab_cat_name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Lab Category Name is required')
        if len(v.strip()) > 100:
            raise ValueError('Name must not exceed 100 characters')
        return v.strip()

    @field_validator('lab_cat_description')
    @classmethod
    def validate_description(cls, v):
        if v and len(v.strip()) > 2000:
            raise ValueError('Description must not exceed 2000 characters')
        return v.strip() if v else v

class LabCategoryCreate(LabCategoryBase):
    created_by: Optional[int] = None

class LabCategoryUpdate(BaseModel):
    lab_cat_name: Optional[str] = None
    lab_cat_description: Optional[str] = None
    modified_by: Optional[int] = None

    @field_validator('lab_cat_name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
             if not v.strip():
                 raise ValueError('Lab Category Name cannot be empty')
             if len(v.strip()) > 100:
                 raise ValueError('Name must not exceed 100 characters')
             return v.strip()
        return v

    @field_validator('lab_cat_description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 2000:
            raise ValueError('Description must not exceed 2000 characters')
        return v.strip() if v else v

class LabCategoryResponse(LabCategoryBase):
    lab_cat_id: int
    created_by: Optional[int] = None
    modified_by: Optional[int] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
