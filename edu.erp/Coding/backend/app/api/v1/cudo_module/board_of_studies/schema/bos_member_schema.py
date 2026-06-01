from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class BoSCreate(BaseModel):
    faculty_type: str
    title: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str

    organization: str
    org_id: Optional[int] = None

    email: EmailStr
    mobile: Optional[str] = None
    aadhar_number: Optional[str] = None

    highest_qualification: Optional[str] = None
    experience: Optional[float] = None

    password: str
    designation: str              
    bos_for: str                   


class BoSUpdate(BaseModel):
    faculty_type: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    mobile: Optional[str] = None
    aadhar_number: Optional[str] = None
    highest_qualification: Optional[str] = None
    experience: Optional[float] = None

    designation: Optional[str] = None
    bos_for: Optional[str] = None
    
    organization: Optional[str] = None
    email: Optional[EmailStr] = None


class BoSResponse(BaseModel):
    bos_id: int
    user_id: int
    
    # Personal Info
    faculty_type: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    
    organization: str
    org_id: Optional[int] = None
    
    email: Optional[str] = None
    mobile: Optional[str] = None
    aadhar_number: Optional[str] = None
    
    highest_qualification: Optional[str] = None
    experience: Optional[float] = None
    
    # Resolved fields 
    designation: Optional[str] = None
    designation_id: Optional[int] = None
    bos_for: Optional[str] = None
    
    # Meta
    status: Optional[int] = 1
    create_date: Optional[date] = None

    class Config:
        from_attributes = True

class DesignationResponse(BaseModel):
    designation_id: int
    designation_name: str
    designation_description: Optional[str] = None
    
    class Config:
        from_attributes = True

class UsersByDeptReq(BaseModel):
    dept_id: int

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class AddExistingBoS(BaseModel):
    user_id: int
    bos_dept_id: int
    bos_for: str # Assuming we might need this for consistency or validation, but ID is primary. Let's keep it to be safe or remove if redundant. Plan said bos_dept_id.
    # Actually based on UI "BoS for" is a dropdown of departments.
    # So we probably receive the selected department ID.
class BoSShortResponse(BaseModel):
    bos_id: int
    user_id: int

    class Config:
        from_attributes = True

from typing import List

class UsersAndBoSByDeptResponse(BaseModel):
    dept_id: int
    users: list[UserResponse]
    bos_members: list[BoSShortResponse]

    class Config:
        from_attributes = True



