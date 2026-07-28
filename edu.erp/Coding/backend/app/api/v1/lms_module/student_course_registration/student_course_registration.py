from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import IEMSAcademicBatch, IEMSemester, IEMSCourses

router = APIRouter()


@router.get("/get_academic_batch_list")
def get_academic_batch_list(
    db: Session = Depends(get_db)
):
    academic_batches = (
        db.query(IEMSAcademicBatch)
        .filter(IEMSAcademicBatch.status == 1)
        .order_by(IEMSAcademicBatch.start_year.desc())
        .all()
    )

    result = [
        {
            "academic_batch_id": row.academic_batch_id,
            "academic_batch_code": row.academic_batch_code,
            "academic_batch_desc": row.academic_batch_desc,
            "academic_year": row.academic_year,
            "start_year": row.start_year,
            "end_year": row.end_year
        }
        for row in academic_batches
    ]

    return returnSuccess(result)


@router.get("/get_semester_list")
def get_semester_list(
    academic_batch_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(IEMSemester).filter(IEMSemester.status == 1)
    if academic_batch_id:
        query = query.filter(IEMSemester.academic_batch_id == academic_batch_id)

    semesters = query.order_by(IEMSemester.semester).all()

    result = [
        {
            "semester_id": row.semester_id,
            "semester": row.semester,
            "semester_code": row.semester_code,
            "semester_desc": row.semester_desc,
            "term_name": row.term_name
        }
        for row in semesters
    ]

    return returnSuccess(result)


@router.get("/check_registration_status")
def check_registration_status(
    academic_batch_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    semester = (
        db.query(IEMSemester)
        .filter(
            IEMSemester.academic_batch_id == academic_batch_id,
            IEMSemester.semester_id == semester_id,
            IEMSemester.status == 1
        )
        .first()
    )

    if not semester:
        return returnSuccess({
            "registration_open": True,
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "registration_start": "",
            "registration_end": ""
        }, "Registration is open.")

    registration_open = True
    message = "Registration is open."
    start_str = ""
    end_str = ""

    current_datetime = datetime.now()

    if semester.enroll_start_date and semester.enroll_start_time:
        try:
            start_dt = datetime.strptime(
                f"{semester.enroll_start_date.strftime('%Y-%m-%d')} {semester.enroll_start_time}",
                "%Y-%m-%d %H:%M:%S"
            )
            start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            if current_datetime < start_dt:
                registration_open = False
                message = "Registration has not started yet."
        except Exception:
            pass

    if semester.enroll_end_date and semester.enroll_end_time and registration_open:
        try:
            end_dt = datetime.strptime(
                f"{semester.enroll_end_date.strftime('%Y-%m-%d')} {semester.enroll_end_time}",
                "%Y-%m-%d %H:%M:%S"
            )
            end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            if current_datetime > end_dt:
                registration_open = False
                message = "Registration is closed."
        except Exception:
            pass

    result = {
        "registration_open": registration_open,
        "academic_batch_id": academic_batch_id,
        "semester_id": semester_id,
        "registration_start": start_str,
        "registration_end": end_str
    }

    return returnSuccess(result, message)


@router.get("/get_registration_academic_batch_list")
def get_registration_academic_batch_list(
    base_academic_batch_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    academic_batches = (
        db.query(IEMSAcademicBatch)
        .filter(IEMSAcademicBatch.status == 1)
        .order_by(IEMSAcademicBatch.start_year.desc(), IEMSAcademicBatch.academic_batch_desc)
        .all()
    )

    result = [
        {
            "academic_batch_id": row.academic_batch_id,
            "academic_batch_code": row.academic_batch_code,
            "academic_batch_desc": row.academic_batch_desc
        }
        for row in academic_batches
    ]

    return returnSuccess(result)


@router.get("/get_registration_semester_list")
def get_registration_semester_list(
    registration_academic_batch_id: Optional[int] = None,
    base_semester_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(IEMSemester).filter(IEMSemester.status == 1)

    if registration_academic_batch_id and registration_academic_batch_id > 0:
        query = query.filter(IEMSemester.academic_batch_id == registration_academic_batch_id)

    semesters = query.order_by(IEMSemester.semester).all()

    result = [
        {
            "semester_id": row.semester_id,
            "semester": row.semester,
            "semester_code": row.semester_code,
            "semester_desc": row.semester_desc,
            "term_name": row.term_name
        }
        for row in semesters
    ]

    return returnSuccess(result)


@router.get("/validate_registration_due_date")
def validate_registration_due_date(
    academic_batch_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    semester = (
        db.query(IEMSemester)
        .filter(
            IEMSemester.academic_batch_id == academic_batch_id,
            IEMSemester.semester_id == semester_id,
            IEMSemester.status == 1
        )
        .first()
    )

    is_open = True
    message = "Registration is open."
    color = "green"

    if semester:
        now = datetime.now()
        if semester.enroll_start_date:
            try:
                start_dt = semester.enroll_start_date
                if hasattr(start_dt, 'date') and semester.enroll_start_time:
                    start_dt = datetime.strptime(f"{semester.enroll_start_date.strftime('%Y-%m-%d')} {semester.enroll_start_time}", "%Y-%m-%d %H:%M:%S")
                if now < start_dt:
                    is_open = False
                    message = "Registration has not started yet."
                    color = "orange"
            except Exception:
                pass

        if semester.enroll_end_date and is_open:
            try:
                end_dt = semester.enroll_end_date
                if hasattr(end_dt, 'date') and semester.enroll_end_time:
                    end_dt = datetime.strptime(f"{semester.enroll_end_date.strftime('%Y-%m-%d')} {semester.enroll_end_time}", "%Y-%m-%d %H:%M:%S")
                if now > end_dt:
                    is_open = False
                    message = "Registration is closed."
                    color = "red"
            except Exception:
                pass

    return returnSuccess({
        "status": is_open,
        "is_registration_open": is_open,
        "status_message": message,
        "status_color": color,
        "enroll_start_date": str(semester.enroll_start_date) if semester and semester.enroll_start_date else None,
        "enroll_end_date": str(semester.enroll_end_date) if semester and semester.enroll_end_date else None
    })


@router.api_route("/get_registration_section_list", methods=["GET", "POST"])
def get_registration_section_list(
    db: Session = Depends(get_db)
):
    sections = [
        {"section_id": 1, "section_name": "Section A"},
        {"section_id": 2, "section_name": "Section B"},
        {"section_id": 3, "section_name": "Section C"}
    ]
    return returnSuccess(sections)


@router.api_route("/registered-courses", methods=["GET", "POST"])
def registered_courses(
    payload: dict = None,
    parent_academic_batch_id: Optional[int] = None,
    parent_semester_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    batch_id = (payload or {}).get("parent_academic_batch_id") or parent_academic_batch_id
    semester_id = (payload or {}).get("parent_semester_id") or parent_semester_id

    query = db.query(IEMSCourses).filter(IEMSCourses.status == 1)
    if batch_id:
        query = query.filter(IEMSCourses.academic_batch_id == batch_id)

    courses = query.order_by(IEMSCourses.crs_code).all()

    result = []
    for c in courses:
        result.append({
            "mcstd_id": c.crs_id,
            "course_id": c.crs_id,
            "course_code": c.crs_code,
            "course_name": c.crs_title,
            "course_type": c.crs_type or "Core",
            "component": c.crs_type,
            "credits": c.total_credits or c.credit_hours or 4,
            "section_id": 1,
            "section_name": "Section A",
            "registration_flag": "Registered",
            "status": 1
        })

    return returnSuccess(result)


@router.api_route("/available-courses", methods=["GET", "POST"])
def available_courses(
    payload: dict = None,
    academic_batch_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    batch_id = (payload or {}).get("academic_batch_id") or academic_batch_id

    query = db.query(IEMSCourses).filter(IEMSCourses.status == 1)
    if batch_id:
        query = query.filter(IEMSCourses.academic_batch_id == batch_id)

    courses = query.order_by(IEMSCourses.crs_code).all()

    result = []
    for c in courses:
        result.append({
            "course_id": c.crs_id,
            "course_code": c.crs_code,
            "course_name": c.crs_title,
            "course_type": c.crs_type or "Core",
            "credits": c.total_credits or c.credit_hours or 4,
            "status": 1
        })

    return returnSuccess(result)