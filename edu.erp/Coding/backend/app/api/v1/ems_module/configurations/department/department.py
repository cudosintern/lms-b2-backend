from datetime import datetime
from fastapi import APIRouter,Depends, Header
from sqlalchemy.orm import Session
from ......utils.comman_validation import check_common_validation
from ......utils.auth_helper import get_current_user
from ......utils.http_return_helper import returnException, returnSuccess
from .department_schema import DepartmentCreate
from ......core.database import get_db
from ......db.models import IEMSDepartment

router = APIRouter()

@router.post("/save_department")
def save_department(
    dept_data: DepartmentCreate,
    current_user: str = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get("user_id")
        return commit_department(db, dept_data, user_id, org_id)
    except Exception as e:
        raise e

def commit_department(db: Session, dept_data: DepartmentCreate, user_id: int, org_id: int):
    check_duplication = check_common_validation(db,'department', dept_data.dept_name, dept_data.department_id, org_id)
    if check_duplication == 0:
        return returnException("Department name already exists.")
    department_instance = None

    if dept_data.department_id is None:
        department_instance = IEMSDepartment(
            dept_name=dept_data.dept_name.strip(),
            dept_acronym=dept_data.dept_acronym.strip() if dept_data.dept_acronym else None,
            dept_code_usn=dept_data.dept_code_usn.strip() if dept_data.dept_code_usn else None,
            dept_description=dept_data.dept_description.strip() if dept_data.dept_description else None,
            no_batch_dept=dept_data.no_batch_dept or 0,
            status=dept_data.status or 1,
            org_id=org_id,
            create_date=datetime.now(),
            created_by=user_id
        )
        db.add(department_instance)
        db.commit()
        db.refresh(department_instance)  
    else:
        department_instance = db.query(IEMSDepartment).filter(
            IEMSDepartment.dept_id == dept_data.department_id,
            IEMSDepartment.org_id == org_id
        ).first()

        if department_instance is None:
            return returnException("Department not found")

        department_instance.dept_name = dept_data.dept_name.strip()
        department_instance.dept_acronym = dept_data.dept_acronym.strip() if dept_data.dept_acronym else None
        department_instance.dept_code_usn = dept_data.dept_code_usn.strip() if dept_data.dept_code_usn else None
        department_instance.dept_description = dept_data.dept_description.strip() if dept_data.dept_description else None
        department_instance.no_batch_dept = dept_data.no_batch_dept or 0
        department_instance.status = dept_data.status or 1
        department_instance.modify_date = datetime.now()
        department_instance.modified_by = user_id
        db.commit()

    response_data = {
        "department_id": department_instance.dept_id,
        "dept_name": department_instance.dept_name,
        "dept_acronym": department_instance.dept_acronym,
        "dept_code_usn": department_instance.dept_code_usn,
        "dept_description": department_instance.dept_description,
        "no_batch_dept": department_instance.no_batch_dept,
        "status": 1 if department_instance.status else 0,
        "create_date": department_instance.create_date if hasattr(department_instance, 'create_date') else None,
        "created_by": department_instance.created_by if hasattr(department_instance, 'created_by') else None,
        "modify_date": department_instance.modify_date if hasattr(department_instance, 'modify_date') else None,
        "modified_by": department_instance.modified_by if hasattr(department_instance, 'modified_by') else None,
    }
    return returnSuccess(response_data)