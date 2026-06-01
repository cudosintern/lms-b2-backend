from pydantic import BaseModel
from typing import Optional


class BloomDomainSaveRequest(BaseModel):
    bld_id: Optional[int] = None
    bld_name: str
    bld_acronym: str
    bld_description: Optional[str] = None
    status: Optional[int] = 1