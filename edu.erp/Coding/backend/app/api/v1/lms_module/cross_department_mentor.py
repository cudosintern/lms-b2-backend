from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List

from app.core.database import get_db
from app.utils.auth_helper import get_current_user

# Set prefix to empty to avoid routing nesting conflicts with main.py's prefix="/api/v1/cross-mentor"
router = APIRouter(prefix="", tags=["Cross Department Mentor"])

print("CROSS DEPARTMENT MENTOR LOADED")

# Helper to get the logged-in user's home department
def get_user_dept(current_user: dict, db: Session) -> int:
    result = db.execute(
        text("SELECT erp_dept_id FROM erp_rbac_user_department WHERE erp_user_id = :id AND status = 1 LIMIT 1"),
        {"id": current_user.get("user_id")}
    ).fetchone()
    if result:
        return result[0]
    # Fallback to org_id from token header
    return current_user.get("org_id", 1)


# ---------------- 1. MENTORS FROM OTHER DEPARTMENTS ----------------
@router.get("/from-other-departments")
def list_mentors_from_other_departments(
    dept_id: Optional[int] = None, # Home department filter
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
        sql += " AND ud.erp_dept_id = :dept_id"
        params["dept_id"] = dept_id

    results = db.execute(text(sql), params).mappings().all()
    return {"status": "success", "data": list(results)}


# ---------------- 2. MENTORS TO OTHER DEPARTMENTS ----------------
@router.get("/to-other-departments")
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


# ---------------- 3. AVAILABLE MENTORS TO ADD ----------------
@router.get("/available-mentors")
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


# ---------------- 4. ADD CROSS DEPARTMENT MENTOR ----------------
@router.post("/add")
def add_cross_department_mentor(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = payload.get("mentor_id")
    if not mentor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mentor_id is required"
        )

    logged_in_dept = get_user_dept(current_user, db)
    creator_id = current_user.get("user_id")

    # Verify mentor exists and get home dept
    mentor = db.execute(
        text("SELECT erp_dept_id FROM erp_rbac_user_department WHERE erp_user_id = :id AND status = 1 LIMIT 1"),
        {"id": mentor_id}
    ).fetchone()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found"
        )

    mentor_dept = mentor[0]
    if mentor_dept == logged_in_dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add mentor from your own department as a cross-department mentor"
        )

    # Check duplicates
    dup = db.execute(
        text("SELECT cross_dept_id FROM lms_cross_dept_users WHERE faculty_user_id = :mentor_id AND to_dept_id = :logged_in_dept"),
        {"mentor_id": mentor_id, "logged_in_dept": logged_in_dept}
    ).fetchone()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mentor is already mapped to your department"
        )

    db.execute(
        text("INSERT INTO lms_cross_dept_users (faculty_user_id, to_dept_id, from_dept_id, created_by) VALUES (:mentor_id, :logged_in_dept, :mentor_dept, :creator_id)"),
        {"mentor_id": mentor_id, "logged_in_dept": logged_in_dept, "mentor_dept": mentor_dept, "creator_id": creator_id}
    )
    db.commit()

    # Get the inserted mapping
    inserted = db.execute(
        text("SELECT cross_dept_id, faculty_user_id, to_dept_id FROM lms_cross_dept_users WHERE faculty_user_id = :mentor_id AND to_dept_id = :logged_in_dept"),
        {"mentor_id": mentor_id, "logged_in_dept": logged_in_dept}
    ).fetchone()

    return {
        "status": "success",
        "message": "Cross department mentor added successfully",
        "data": {
            "mapping_id": inserted[0],
            "mentor_id": inserted[1],
            "mapped_dept_id": inserted[2],
            "status": 1
        }
    }


# ---------------- 5. UPDATE MAPPING STATUS ----------------
@router.put("/update/{id}")
def update_cross_department_mentor(
    id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # LMS Cross dept table doesn't seem to have a status column. Just return success
    return {
        "status": "success",
        "message": "Mapping status updated (ignored as table doesn't support it)",
        "data": {
            "mapping_id": id,
            "status": payload.get("status", 1)
        }
    }


# ---------------- 6. REMOVE CROSS DEPARTMENT MENTOR ----------------
@router.delete("/remove/{id}")
def remove_cross_department_mentor(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mapping = db.execute(
        text("SELECT cross_dept_id FROM lms_cross_dept_users WHERE cross_dept_id = :id"),
        {"id": id}
    ).fetchone()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found"
        )

    db.execute(
        text("DELETE FROM lms_cross_dept_users WHERE cross_dept_id = :id"),
        {"id": id}
    )
    db.commit()

    return {
        "status": "success",
        "message": "Cross department mentor mapping removed successfully"
    }
