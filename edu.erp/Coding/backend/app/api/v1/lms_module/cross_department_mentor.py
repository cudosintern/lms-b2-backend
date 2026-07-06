from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.db.models import Base, IEMSDepartment, IEMSUsers, LMSCrossDeptMentor, ErpCurriculum
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

# Auto-create the table if it doesn't exist yet
try:
    LMSCrossDeptMentor.__table__.create(bind=engine, checkfirst=True)
    print("Table lms_cross_dept_mentor verified/created successfully.")
except Exception as e:
    print("Error auto-creating cross_dept_mentor table:", e)

router = APIRouter(tags=["LMS-Cross Department Mentor"])

print("CROSS DEPARTMENT MENTOR LOADED")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class AddCrossDeptMentorPayload(BaseModel):
    mentor_user_id: int     # the user being assigned as cross-dept mentor
    mentor_dept_id: int     # that user's home department
    curriculum_id: Optional[int] = None


class UpdateCrossDeptMentorPayload(BaseModel):
    assigned_dept_id: int   # re-target the mentor to a different department


# ---------------------------------------------------------------------------
# Helper: resolve a user's full name from IEMSUsers
# ---------------------------------------------------------------------------

def _build_mentor_row(record: LMSCrossDeptMentor, db: Session) -> dict:
    """Return a dict representation of one cross-dept assignment row."""
    mentor_user = db.query(IEMSUsers).filter(IEMSUsers.id == record.mentor_user_id).first()
    mentor_dept = db.query(IEMSDepartment).filter(IEMSDepartment.dept_id == record.mentor_dept_id).first()
    assigned_dept = db.query(IEMSDepartment).filter(IEMSDepartment.dept_id == record.assigned_dept_id).first()

    curriculum = None
    if getattr(record, "curriculum_id", None):
        curriculum = db.query(ErpCurriculum).filter(ErpCurriculum.erp_crclm_id == record.curriculum_id).first()

    return {
        "id": record.id,
        "mentor_user_id": record.mentor_user_id,
        "mentor_name": (
            f"{mentor_user.first_name or ''} {mentor_user.last_name or ''}".strip()
            if mentor_user else "Unknown"
        ),
        "mentor_email": mentor_user.email if mentor_user else None,
        "mentor_dept_id": record.mentor_dept_id,
        "mentor_dept_name": mentor_dept.dept_name if mentor_dept else None,
        "assigned_dept_id": record.assigned_dept_id,
        "assigned_dept_name": assigned_dept.dept_name if assigned_dept else None,
        "curriculum_id": record.curriculum_id if getattr(record, "curriculum_id", None) else None,
        "curriculum_name": curriculum.erp_crclm_name if curriculum else None,
    }


# ---------------------------------------------------------------------------
# GET /departments  ΓÇô dropdown list of all active depts in the org
# ---------------------------------------------------------------------------

@router.get("/departments")
def list_departments(
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    """
    Returns all active departments for the org.
    Used to populate the department filter dropdown on the frontend.
    """
    depts = (
        db.query(IEMSDepartment)
        .filter(
            ((IEMSDepartment.org_id == org_id) | (IEMSDepartment.org_id.is_(None))),
            IEMSDepartment.status == 1,
        )
        .order_by(IEMSDepartment.dept_name)
        .all()
    )
    data = [
        {
            "dept_id": d.dept_id,
            "dept_name": d.dept_name,
            "dept_acronym": d.dept_acronym,
        }
        for d in depts
    ]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# GET /users  ΓÇô list of all active users in the org
# ---------------------------------------------------------------------------

@router.get("/users")
def list_users(
    dept_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    """
    Returns all active users for the org to select from.
    Optionally filtered by department.
    """
    query = db.query(IEMSUsers).filter(
        IEMSUsers.org_id == org_id,
        IEMSUsers.status == 1,
    )
    if dept_id is not None:
        query = query.filter(IEMSUsers.user_dept_id == dept_id)

    users = query.order_by(IEMSUsers.first_name).all()
    data = [
        {
            "id": u.id,
            "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
            "email": u.email,
            "dept_id": u.user_dept_id,
        }
        for u in users
    ]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# GET /curriculums  ΓÇô list of all active curriculums
# ---------------------------------------------------------------------------

@router.get("/curriculums")
def list_curriculums(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all active curriculums.
    """
    curriculums = (
        db.query(ErpCurriculum)
        .filter(ErpCurriculum.status == 1)
        .order_by(ErpCurriculum.erp_crclm_name)
        .all()
    )
    data = [
        {
            "crclm_id": c.erp_crclm_id,
            "crclm_name": c.erp_crclm_name,
        }
        for c in curriculums
    ]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# GET /mentors-from-other-dept
# Tab 1 ΓÇô mentors assigned TO the logged-in faculty's department FROM other depts
# Optional ?filter_dept_id= to filter by the mentor's home department
# ---------------------------------------------------------------------------

@router.get("/mentors-from-other-dept")
def list_mentors_from_other_dept(
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    dept_id: Optional[int] = Header(None),
    filter_dept_id: Optional[int] = Query(None, description="Filter by mentor's home department"),
    db: Session = Depends(get_db),
):
    """
    Returns mentors from other departments who are assigned to the logged-in
    faculty's department (dept_id header).

    Optional query param `filter_dept_id` narrows results to mentors whose
    home department matches the given value.
    """
    if not dept_id:
        user_record = db.query(IEMSUsers).filter(IEMSUsers.id == current_user.get("user_id")).first()
        dept_id = user_record.user_dept_id if user_record else None

    if not dept_id:
        first_dept = db.query(IEMSDepartment).filter(IEMSDepartment.status == 1).order_by(IEMSDepartment.dept_id).first()
        dept_id = first_dept.dept_id if first_dept else None

    if not dept_id:
        return returnException("Department ID is required but could not be determined.")

    query = db.query(LMSCrossDeptMentor).filter(
        LMSCrossDeptMentor.assigned_dept_id == dept_id,
        LMSCrossDeptMentor.org_id == org_id,
        LMSCrossDeptMentor.status == 1,
    )

    if filter_dept_id is not None:
        query = query.filter(LMSCrossDeptMentor.mentor_dept_id == filter_dept_id)

    records = query.order_by(LMSCrossDeptMentor.id).all()
    data = [_build_mentor_row(r, db) for r in records]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# GET /mentors-to-other-dept
# Tab 2 ΓÇô mentors OF the logged-in faculty's department assigned elsewhere
# ---------------------------------------------------------------------------

@router.get("/mentors-to-other-dept")
def list_mentors_to_other_dept(
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    dept_id: Optional[int] = Header(None),
    filter_dept_id: Optional[int] = Query(None, description="Filter by assigned department"),
    db: Session = Depends(get_db),
):
    """
    Returns all mentors who belong to the logged-in faculty's department
    (mentor_dept_id == dept_id) and are assigned as cross-dept mentors
    to any other department.
    """
    if not dept_id:
        user_record = db.query(IEMSUsers).filter(IEMSUsers.id == current_user.get("user_id")).first()
        dept_id = user_record.user_dept_id if user_record else None

    if not dept_id:
        first_dept = db.query(IEMSDepartment).filter(IEMSDepartment.status == 1).order_by(IEMSDepartment.dept_id).first()
        dept_id = first_dept.dept_id if first_dept else None

    if not dept_id:
        return returnException("Department ID is required but could not be determined.")

    query = (
        db.query(LMSCrossDeptMentor)
        .filter(
            LMSCrossDeptMentor.mentor_dept_id == dept_id,
            LMSCrossDeptMentor.org_id == org_id,
            LMSCrossDeptMentor.status == 1,
        )
    )

    if filter_dept_id is not None:
        query = query.filter(LMSCrossDeptMentor.assigned_dept_id == filter_dept_id)

    records = query.order_by(LMSCrossDeptMentor.id).all()
    data = [_build_mentor_row(r, db) for r in records]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# POST /save  ΓÇô add a cross-dept mentor to the logged-in faculty's dept
# ---------------------------------------------------------------------------

@router.post("/add")
@router.post("/save")
def save_cross_dept_mentor(
    payload: AddCrossDeptMentorPayload,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    dept_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Assigns `mentor_user_id` (from `mentor_dept_id`) as a cross-dept mentor
    to the logged-in faculty's department (`dept_id` header).

    Validations:
    - Mentor's home dept must NOT be the same as the target dept.
    - No duplicate active assignment for the same mentor ΓåÆ same target dept.
    - The mentor user must exist and be active.
    """
    if not dept_id:
        user_record = db.query(IEMSUsers).filter(IEMSUsers.id == current_user.get("user_id")).first()
        dept_id = user_record.user_dept_id if user_record else None

    if not dept_id:
        first_dept = db.query(IEMSDepartment).filter(IEMSDepartment.status == 1).order_by(IEMSDepartment.dept_id).first()
        dept_id = first_dept.dept_id if first_dept else None

    if not dept_id:
        return returnException("Department ID is required but could not be determined.")

    user_id = current_user.get("user_id")

    # Guard: mentor must be from a different department
    if payload.mentor_dept_id == dept_id:
        return returnException(
            "The mentor belongs to the same department. Cross-department assignment requires a different department."
        )

    # Guard: mentor user must exist and be active
    mentor_user = db.query(IEMSUsers).filter(
        IEMSUsers.id == payload.mentor_user_id,
        IEMSUsers.status == 1,
    ).first()
    if not mentor_user:
        return returnException("Mentor user not found or inactive.")

    # Guard: no duplicate active assignment
    duplicate = db.query(LMSCrossDeptMentor).filter(
        LMSCrossDeptMentor.mentor_user_id == payload.mentor_user_id,
        LMSCrossDeptMentor.assigned_dept_id == dept_id,
        LMSCrossDeptMentor.org_id == org_id,
        LMSCrossDeptMentor.status == 1,
    ).first()
    if duplicate:
        return returnException(
            "This mentor is already assigned to your department."
        )

    new_record = LMSCrossDeptMentor(
        mentor_user_id=payload.mentor_user_id,
        mentor_dept_id=payload.mentor_dept_id,
        assigned_dept_id=dept_id,
        curriculum_id=payload.curriculum_id,
        org_id=org_id,
        status=1,
        created_by=user_id,
        create_date=datetime.now(),
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return returnSuccess(
        _build_mentor_row(new_record, db),
        "Cross-department mentor added successfully.",
    )


# ---------------------------------------------------------------------------
# PUT /update/{id}  ΓÇô re-target an assignment to a different department
# ---------------------------------------------------------------------------

@router.put("/update/{id}")
def update_cross_dept_mentor(
    id: int,
    payload: UpdateCrossDeptMentorPayload,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    dept_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Updates the `assigned_dept_id` of an existing cross-dept mentor assignment.
    Only assignments that belong to the logged-in faculty's department are editable.
    """
    user_id = current_user.get("user_id")

    record = db.query(LMSCrossDeptMentor).filter(
        LMSCrossDeptMentor.id == id,
        LMSCrossDeptMentor.org_id == org_id,
        LMSCrossDeptMentor.status == 1,
    ).first()
    if not record:
        return returnException("Cross-department mentor assignment not found.")

    # Guard: new target dept must differ from mentor's home dept
    if payload.assigned_dept_id == record.mentor_dept_id:
        return returnException(
            "Cannot assign a mentor to their own home department."
        )

    # Guard: no duplicate for the new target dept
    duplicate = db.query(LMSCrossDeptMentor).filter(
        LMSCrossDeptMentor.mentor_user_id == record.mentor_user_id,
        LMSCrossDeptMentor.assigned_dept_id == payload.assigned_dept_id,
        LMSCrossDeptMentor.org_id == org_id,
        LMSCrossDeptMentor.status == 1,
        LMSCrossDeptMentor.id != id,
    ).first()
    if duplicate:
        return returnException(
            "This mentor is already assigned to the target department."
        )

    record.assigned_dept_id = payload.assigned_dept_id
    record.modified_by = user_id
    record.modify_date = datetime.now()
    db.commit()
    db.refresh(record)

    return returnSuccess(
        _build_mentor_row(record, db),
        "Cross-department mentor assignment updated successfully.",
    )


# ---------------------------------------------------------------------------
# DELETE /delete/{id}  ΓÇô soft delete a cross-dept mentor assignment
# ---------------------------------------------------------------------------

@router.delete("/delete/{id}")
def delete_cross_dept_mentor(
    id: int,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    dept_id: Optional[int] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Soft-deletes (status=0) a cross-department mentor assignment.
    Only assignments visible within the caller's org are deletable.
    """
    user_id = current_user.get("user_id")

    record = db.query(LMSCrossDeptMentor).filter(
        LMSCrossDeptMentor.id == id,
        LMSCrossDeptMentor.org_id == org_id,
        LMSCrossDeptMentor.status == 1,
    ).first()
    if not record:
        return returnException("Cross-department mentor assignment not found.")

    record.status = 0
    record.modified_by = user_id
    record.modify_date = datetime.now()
    db.commit()

    return returnSuccess({"id": id}, "Cross-department mentor removed successfully.")
