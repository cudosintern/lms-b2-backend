from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class UniversityBase(BaseModel):
    unv_name: str
    unv_desc: str
    status: Optional[int] = None
    created_by: int
    modified_by: int
    created_date: date
    modified_date: date
    unv_code: str


class UniversityCreate(UniversityBase):
    pass


class UniversityUpdate(UniversityBase):
    pass


class UniversityResponce(UniversityBase):
    unv_id: int

    model_config = ConfigDict(from_attributes=True)
