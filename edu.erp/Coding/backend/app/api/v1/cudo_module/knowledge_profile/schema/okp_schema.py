from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class OKPBase(BaseModel):
    okp_attr_code: str = Field(..., max_length=10)
    okp_attr_description: str = Field(..., max_length=5000)


class OKPCreate(OKPBase):
    pass


class OKPUpdate(BaseModel):
    okp_attr_code: Optional[str] = Field(None, max_length=10)
    okp_attr_description: Optional[str] = Field(None, max_length=5000)


class OKPResponse(OKPBase):
    okp_id: int
    created_by: Optional[int]
    modified_by: Optional[int]
    created_date: Optional[date]
    modified_date: Optional[date]

    class Config:
        from_attributes = True
