from pydantic import BaseModel
from typing import Optional

class DepartmentCreate(BaseModel):
    dept_name: str
    dept_acronym: str
    dept_code_usn: str
    dept_description: Optional[str] = None