from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProgramKPCreate(BaseModel):
    pgm_id: int
    pkp_attr_code: str
    pkp_attr_description: str
    created_by: Optional[int] = None


class ProgramKPUpdate(BaseModel):
    pkp_attr_code: str
    pkp_attr_description: str
    modified_by: Optional[int] = None


class ProgramKPResponse(BaseModel):
    pkp_id: int
    pgm_id: int
    pkp_attr_code: str
    pkp_attr_description: str

    class Config:
        from_attributes = True
