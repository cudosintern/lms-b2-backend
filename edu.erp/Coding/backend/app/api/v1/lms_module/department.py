from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import IEMSDepartment  # Adjust if your database model name differs
from app.api.v1.lms_module.department_schema import DepartmentCreate

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("/create")
def commit_department(dept_data: DepartmentCreate, db: Session = Depends(get_db)):
    # 1. Database check for duplicate entries
    check_duplication = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_name == dept_data.dept_name
    ).first()
    
    if check_duplication:
        raise HTTPException(status_code=400, detail="Department name already exists.")
    
    # 2. Map data to the database table model
    department_instance = IEMSDepartment(
        dept_name=dept_data.dept_name.strip(),
        dept_acronym=dept_data.dept_acronym.strip(),
        dept_code_usn=dept_data.dept_code_usn.strip(),
        dept_description=dept_data.dept_description.strip() if dept_data.dept_description else None,
        status=1
    )
    
    # 3. Save directly to XAMPP MySQL
    db.add(department_instance)
    db.commit()
    db.refresh(department_instance)
    
    return {
        "status": "success",
        "department_id": department_instance.dept_id,
        "dept_name": department_instance.dept_name
    }