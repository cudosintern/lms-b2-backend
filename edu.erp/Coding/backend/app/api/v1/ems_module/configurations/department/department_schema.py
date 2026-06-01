from pydantic import BaseModel
from typing import Optional

class DepartmentCreate(BaseModel):
    department_id: Optional[int] = None
    dept_name: Optional[str]
    dept_acronym: Optional[str]
    dept_code_usn: Optional[str]
    dept_description: Optional[str]
    status: Optional[int] = 1
    no_batch_dept: Optional[int] = 0
    
