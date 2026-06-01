from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    faculty_type: str
    title: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    
    email: EmailStr
    employee_no: Optional[str] = None
    contact_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    
    school: str  # Assuming this maps to department name or ID
    designation: str
    user_group: str # Maps to user_type
    
    highest_qualification: Optional[str] = None
    experience: Optional[float] = None
    
    password: str

class UserListResponse(BaseModel):
    user_id: int
    name: str  # Full name
    email: str

class BoSAddExisting(BaseModel):
    user_id: int
    bos_for: Optional[str] = None # Department Name (keep for compatibility or alternative)
    bos_dept_id: Optional[int] = None # Department ID (Preferred)
