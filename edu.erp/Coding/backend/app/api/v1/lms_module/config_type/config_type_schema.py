from pydantic import BaseModel
from typing import Optional


class app_configs(BaseModel):
    config_type_name: str
    min_mentees: int
    max_mentees: int
    config_type_id: Optional[int] = None   # present on edit


class UpdateConfigType(BaseModel):
    config_type_name: str
    min_mentees: int
    max_mentees: int
