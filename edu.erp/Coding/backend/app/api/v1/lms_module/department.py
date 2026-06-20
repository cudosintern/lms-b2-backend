from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import IEMSDepartment
from app.api.v1.lms_module.department_schema import DepartmentCreate
from app.utils.auth_helper import get_current_user

router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)

# ---------------- CREATE DEPARTMENT ----------------
@router.post(
    "/create",
    operation_id="create_department_api"
)
def commit_department(
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_duplication = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_name == dept_data.dept_name
    ).first()

    if check_duplication:
        raise HTTPException(status_code=400, detail="Department name already exists.")

    department_instance = IEMSDepartment(
        dept_name=dept_data.dept_name.strip(),
        dept_acronym=dept_data.dept_acronym.strip(),
        dept_code_usn=dept_data.dept_code_usn.strip(),
        dept_description=dept_data.dept_description.strip()
        if dept_data.dept_description else None,
        status=1
    )

    db.add(department_instance)
    db.commit()
    db.refresh(department_instance)

    return {
        "status": "success",
        "department_id": department_instance.dept_id,
        "dept_name": department_instance.dept_name
    }


# ---------------- LIST DEPARTMENTS ----------------

@router.get("/list")
def list_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    departments = db.query(IEMSDepartment).all()

    result = []
    for d in departments:
        result.append({
            "dept_id": d.dept_id,
            "dept_name": d.dept_name,
            "dept_acronym": d.dept_acronym,
            "dept_code_usn": d.dept_code_usn,
            "dept_description": d.dept_description,
            "status": d.status
        })

    return {
        "status": "success",
        "data": result
    }


# ---------------- GET BY ID ----------------
@router.get("/{dept_id}")
def get_department(
    dept_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 👇 THIS is where your line goes
    dept = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_id == dept_id
    ).first()

    if not dept:
        return {"status": "error", "message": "Department not found"}

    return {
        "status": "success",
        "data": {
            "dept_id": dept.dept_id,
            "dept_name": dept.dept_name,
            "dept_acronym": dept.dept_acronym,
            "dept_code_usn": dept.dept_code_usn,
            "dept_description": dept.dept_description,
            "status": dept.status
        }
    }

# ---------------- UPDATE DEPARTMENT ----------------
@router.put(
    "/update/{dept_id}",
    operation_id="update_department_api"
)
def update_department(
    dept_id: int,
    dept_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    department = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_id == dept_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    duplicate = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_name == dept_data.dept_name,
        IEMSDepartment.dept_id != dept_id
    ).first()

    if duplicate:
        raise HTTPException(status_code=400, detail="Department name already exists.")

    department.dept_name = dept_data.dept_name.strip()
    department.dept_acronym = dept_data.dept_acronym.strip()
    department.dept_code_usn = dept_data.dept_code_usn.strip()
    department.dept_description = (
        dept_data.dept_description.strip()
        if dept_data.dept_description else None
    )

    db.commit()
    db.refresh(department)

    return {
        "status": "success",
        "message": "Department updated successfully"
    }


# ---------------- DELETE DEPARTMENT ----------------
@router.delete(
    "/delete/{dept_id}",
    operation_id="delete_department_api"
)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    
):
    department = db.query(IEMSDepartment).filter(
        IEMSDepartment.dept_id == dept_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)
    db.commit()

    return {
        "status": "success",
        "message": "Department deleted successfully"
    }


# ---------------- EXPORT PDF ----------------
@router.get(
    "/export/pdf",
    operation_id="export_department_pdf_api"
)
async def export_department_pdf(
    current_user: dict = Depends(get_current_user)
):
    return {
        "status": "success",
        "message": "Department PDF export"
    }