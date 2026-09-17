from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TypeLimit(InputModel):
    course_type_id: int = Field(gt=0)
    minimum: Decimal = Field(ge=0, le=99.9, decimal_places=1)
    maximum: Decimal = Field(ge=0, le=99.9, decimal_places=1)


class ConfigurationSave(InputModel):
    start: datetime
    end: datetime
    total: Decimal = Field(ge=1, le=60, decimal_places=1)
    own_electives: int = Field(default=0, ge=0, le=9, strict=True)
    other_electives: int = Field(default=0, ge=0, le=9, strict=True)
    limits: List[TypeLimit] = Field(min_length=1)


class CourseLimit(InputModel):
    course_id: int = Field(gt=0)
    capacity: Optional[int] = Field(default=None, ge=0, strict=True)
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class CourseSave(InputModel):
    courses: List[CourseLimit] = Field(min_length=1)
