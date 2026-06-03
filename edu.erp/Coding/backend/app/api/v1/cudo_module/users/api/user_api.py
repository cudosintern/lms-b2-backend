from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.db.models import IEMSUsers, CUDOSBoS, IEMSDepartment, IEMSUserDesignation
from typing import List
from app.api.v1.cudo_module.users.schema.user_schema import UserCreate, BoSAddExisting, UserListResponse

from app.utils.set_password_helper import set_private_password
# from app.api.v1.cudo_module.board_of_studies.designation_helper import map_designation_to_id
from app.api.v1.cudo_module.board_of_studies.faculty_helper import map_faculty_type_to_id

router = APIRouter()

# iems user creating api
@router.post("/create")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    if db.query(IEMSUsers).filter(IEMSUsers.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Map helpers
    # Designation lookup from DB
    designation = db.query(IEMSUserDesignation).filter(IEMSUserDesignation.designation_name == payload.designation).first()
    if not designation:
        raise HTTPException(status_code=400, detail="Invalid Designation")
    designation_id = designation.designation_id
    
    faculty_type_id = map_faculty_type_to_id(payload.faculty_type)
    
    # Resolve department (school) to get org_id if needed, or just handle logic
    department = db.query(IEMSDepartment).filter(IEMSDepartment.dept_name == payload.school).first()
    dept_id = department.dept_id if department else None
    
    hashed_password = set_private_password(payload.password)
    
    new_user = IEMSUsers(
        email=payload.email,
        username=payload.email,
        password=hashed_password["password"],
        salt=hashed_password["salt"],
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        mobile=payload.contact_number,
        aadhar_number=payload.aadhar_number,
        emp_no=payload.employee_no,
        
        user_dept_id=dept_id,
        designation_id=designation_id,
        faculty_type=faculty_type_id,
        # Truncate user_group to 1 char as IEMSUsers.user_type is VARCHAR(1)
        user_type=payload.user_group[:1].upper() if payload.user_group else None, 
        
        user_qualification=payload.highest_qualification,
        user_experience=payload.experience,
        
        title=payload.title,
        create_date=date.today(),
        status=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}

@router.get("/by_school/{school_name}", response_model=List[UserListResponse])
def get_users_by_school(school_name: str, db: Session = Depends(get_db)):
    # Lookup department by name
    department = db.query(IEMSDepartment).filter(IEMSDepartment.dept_name == school_name).first()
    if not department:
        raise HTTPException(status_code=404, detail="School/Department not found")
        
    users = db.query(IEMSUsers).filter(IEMSUsers.user_dept_id == department.dept_id).all()
    # Filter for active users if needed, e.g., status=1. Assuming all for now or status=1.
    return [
        {
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email
        }
        for user in users
    ]

