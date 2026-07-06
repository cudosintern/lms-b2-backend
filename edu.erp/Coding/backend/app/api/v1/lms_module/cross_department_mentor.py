from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.api.v1.lms_module.cross_department_mentor_schema import (
    CrossDepartmentMentorCreate,
    CrossDepartmentMentorUpdate,
    CrossDepartmentMentorResponseWrapper,
    CrossDepartmentMentorToResponseWrapper,
    AvailableMentorResponseWrapper,
    FilterDepartmentResponseWrapper
)
from app.db.models import LMSCrossDeptUsers, LMSCrossDeptUsersCrclms

router = APIRouter(prefix="", tags=["Cross Department Mentor"])

# Helper to get the logged-in user's home department
def get_user_dept(current_user: dict, db: Session) -> int:
    result = db.execute(
        text("SELECT erp_dept_id FROM erp_rbac_user_department WHERE erp_user_id = :id AND status = 1 LIMIT 1"),
        {"id": current_user.get("user_id")}
    ).fetchone()
    if result:
        return result[0]
    return current_user.get("org_id", 1)


@router.get("/filter-departments", response_model=FilterDepartmentResponseWrapper)
def list_filter_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logged_in_dept = get_user_dept(current_user, db)

    sql = """
        SELECT DISTINCT d.dept_id, d.dept_name, d.dept_acronym, 
                        d.dept_code_usn, d.dept_description, d.status
        FROM lms_cross_dept_users m
        JOIN iems_department d ON m.from_dept_id = d.dept_id
        WHERE m.to_dept_id = :logged_in_dept
    """
    results = db.execute(text(sql), {"logged_in_dept": logged_in_dept}).mappings().all()
    return {"status": "success", "data": list(results)}

@router.get("/available-departments", response_model=FilterDepartmentResponseWrapper)
def list_available_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logged_in_dept = get_user_dept(current_user, db)

    sql = """
        SELECT dept_id, dept_name, dept_acronym, dept_code_usn, dept_description, status
        FROM iems_department
        WHERE dept_id != :logged_in_dept AND status = 1
    """
    results = db.execute(text(sql), {"logged_in_dept": logged_in_dept}).mappings().all()
    return {"status": "success", "data": list(results)}

@router.get("/from-other-departments", response_model=CrossDepartmentMentorResponseWrapper)
def list_mentors_from_other_departments(
    dept_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logged_in_dept = get_user_dept(current_user, db)

    sql = """
        SELECT m.cross_dept_id AS mapping_id, u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS home_dept_id, d.dept_name AS home_dept_name, 1 AS status
        FROM lms_cross_dept_users m
        JOIN erp_users u ON m.faculty_user_id = u.erp_user_id
        JOIN erp_rbac_user_department ud ON u.erp_user_id = ud.erp_user_id AND ud.status = 1
        JOIN iems_department d ON ud.erp_dept_id = d.dept_id
        WHERE m.to_dept_id = :logged_in_dept
    """
    params = {"logged_in_dept": logged_in_dept}
    if dept_id is not None:
        sql += " AND m.from_dept_id = :dept_id"
        params["dept_id"] = dept_id

    results = db.execute(text(sql), params).mappings().all()
    return {"status": "success", "data": list(results)}


@router.get("/to-other-departments", response_model=CrossDepartmentMentorToResponseWrapper)
def list_mentors_to_other_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logged_in_dept = get_user_dept(current_user, db)

    sql = """
        SELECT m.cross_dept_id AS mapping_id, u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS mapped_dept_id, d.dept_name AS mapped_dept_name, 1 AS status
        FROM lms_cross_dept_users m
        JOIN erp_users u ON m.faculty_user_id = u.erp_user_id
        JOIN iems_department d ON m.to_dept_id = d.dept_id
        WHERE m.from_dept_id = :logged_in_dept
    """
    results = db.execute(text(sql), {"logged_in_dept": logged_in_dept}).mappings().all()
    return {"status": "success", "data": list(results)}


@router.get("/available-mentors", response_model=AvailableMentorResponseWrapper)
def list_available_mentors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logged_in_dept = get_user_dept(current_user, db)

    sql = """
        SELECT u.erp_user_id AS mentor_id, u.first_name, u.last_name, u.email_id AS email, 
               d.dept_id AS home_dept_id, d.dept_name AS home_dept_name
        FROM erp_users u
        JOIN erp_rbac_user_department ud ON u.erp_user_id = ud.erp_user_id AND ud.status = 1
        JOIN iems_department d ON ud.erp_dept_id = d.dept_id
        WHERE ud.erp_dept_id != :logged_in_dept
          AND u.erp_user_id NOT IN (
              SELECT faculty_user_id FROM lms_cross_dept_users WHERE to_dept_id = :logged_in_dept
          )
    """
    results = db.execute(text(sql), {"logged_in_dept": logged_in_dept}).mappings().all()
    return {"status": "success", "data": list(results)}


@router.post("/add")
def add_cross_department_mentor(
    payload: CrossDepartmentMentorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = payload.mentor_id
    logged_in_dept = get_user_dept(current_user, db)
    creator_id = current_user.get("user_id")

    mentor = db.execute(
        text("SELECT erp_dept_id FROM erp_rbac_user_department WHERE erp_user_id = :id AND status = 1 LIMIT 1"),
        {"id": mentor_id}
    ).fetchone()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")

    mentor_dept = mentor[0]
    if mentor_dept == logged_in_dept:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add mentor from your own department")

    dup = db.query(LMSCrossDeptUsers).filter(
        LMSCrossDeptUsers.faculty_user_id == mentor_id,
        LMSCrossDeptUsers.to_dept_id == logged_in_dept
    ).first()
    
    if dup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mentor is already mapped")

    new_mapping = LMSCrossDeptUsers(
        faculty_user_id=mentor_id,
        to_dept_id=logged_in_dept,
        from_dept_id=mentor_dept,
        created_by=creator_id
    )
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    # Insert academic batches mapping if provided
    if payload.academic_batch_ids:
        for batch_id in payload.academic_batch_ids:
            batch_map = LMSCrossDeptUsersCrclms(
                cross_dept_id=new_mapping.cross_dept_id,
                dept_id=logged_in_dept,
                faculty_user_id=mentor_id,
                academic_batch_id=batch_id,
                created_by=creator_id
            )
            db.add(batch_map)
        db.commit()

    return {
        "status": "success",
        "message": "Cross department mentor added successfully",
        "data": {
            "mapping_id": new_mapping.cross_dept_id,
            "mentor_id": new_mapping.faculty_user_id,
            "mapped_dept_id": new_mapping.to_dept_id,
            "status": 1
        }
    }


@router.put("/update/{id}")
def update_cross_department_mentor(
    id: int,
    payload: CrossDepartmentMentorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mapping = db.query(LMSCrossDeptUsers).filter(LMSCrossDeptUsers.cross_dept_id == id).first()
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")

    if payload.academic_batch_ids is not None:
        db.query(LMSCrossDeptUsersCrclms).filter(LMSCrossDeptUsersCrclms.cross_dept_id == id).delete()
        for batch_id in payload.academic_batch_ids:
            batch_map = LMSCrossDeptUsersCrclms(
                cross_dept_id=id,
                dept_id=mapping.to_dept_id,
                faculty_user_id=mapping.faculty_user_id,
                academic_batch_id=batch_id,
                created_by=current_user.get("user_id")
            )
            db.add(batch_map)
        db.commit()

    return {
        "status": "success",
        "message": "Mapping updated successfully",
        "data": {"mapping_id": id}
    }


@router.delete("/remove/{id}")
def remove_cross_department_mentor(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mapping = db.query(LMSCrossDeptUsers).filter(LMSCrossDeptUsers.cross_dept_id == id).first()
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")

    db.query(LMSCrossDeptUsersCrclms).filter(LMSCrossDeptUsersCrclms.cross_dept_id == id).delete()
    db.delete(mapping)
    db.commit()

    return {"status": "success", "message": "Cross department mentor mapping removed successfully"}
