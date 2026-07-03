from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class RegistrationSetupRequest(BaseModel):
    curriculum_id: int = Field(..., gt=0)
    term_id: int = Field(..., gt=0)


class RegistrationSetupCreateRequest(BaseModel):
    curriculum_id: int = Field(..., gt=0)
    term_id: int = Field(..., gt=0)
    min_credits: int = Field(..., ge=0, le=30)
    max_credits: int = Field(..., ge=0, le=30)
    enrollment_limit: int = Field(..., gt=0)
    registration_start_datetime: Optional[datetime] = None
    registration_end_datetime: Optional[datetime] = None
    status: str = Field(default="active")
    
    @model_validator(mode='after')
    def validate_credits(self):
        if self.min_credits > self.max_credits:
            raise ValueError('min_credits cannot be greater than max_credits')
        return self


class RegistrationSetupData(BaseModel):
    curriculum_id: int
    term_id: int
    min_credits: int
    max_credits: int
    enrollment_limit: int
    registration_start_datetime: Optional[str] = None
    registration_end_datetime: Optional[str] = None
    status: Optional[Any] = None
    no_of_oe_allowed_by_base_crlm: Optional[int] = None
    no_of_oe_allowed_by_other_crclm: Optional[int] = None


class RegistrationSetupResponse(BaseModel):
    status: bool
    message: str
    data: Optional[RegistrationSetupData] = None

class RegistrationSetupDetailsResponse(BaseModel):
    semester_id: int
    term: str

    start_date: Optional[str] = None
    start_time: Optional[str] = None

    end_date: Optional[str] = None
    end_time: Optional[str] = None

    min_credits: Optional[int] = None
    max_credits: Optional[int] = None
    enrollment_limit: Optional[int] = None
    registration_start_datetime: Optional[str] = None
    registration_end_datetime: Optional[str] = None
    no_of_oe_allowed_by_base_crlm: Optional[int] = None
    no_of_oe_allowed_by_other_crclm: Optional[int] = None