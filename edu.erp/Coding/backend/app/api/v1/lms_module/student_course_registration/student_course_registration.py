from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import IEMSAcademicBatch, IEMSemester

router = APIRouter()


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import IEMSAcademicBatch

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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import IEMSemester

router = APIRouter()


@router.get("/get_semester_list")
def get_semester_list(
    academic_batch_id: int,
    db: Session = Depends(get_db)
):

    semesters = (
        db.query(IEMSemester)
        .filter(
            IEMSemester.academic_batch_id == academic_batch_id,
            IEMSemester.status == 1
        )
        .order_by(IEMSemester.semester)
        .all()
    )

    result = [
        {
            "semester_id": row.semester_id,
            "semester": row.semester,
            "semester_desc": row.semester_desc,
            "term_name": row.term_name
        }
        for row in semesters
    ]

    return returnSuccess(result)

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import IEMSemester

router = APIRouter()


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
        return returnSuccess(
            data=None,
            message="Invalid Academic Batch or Semester."
        )

    # Combine date & time
    registration_start = datetime.strptime(
        f"{semester.enroll_start_date.strftime('%Y-%m-%d')} {semester.enroll_start_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    registration_end = datetime.strptime(
        f"{semester.enroll_end_date.strftime('%Y-%m-%d')} {semester.enroll_end_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    current_datetime = datetime.now()

    if current_datetime < registration_start:
        registration_open = False
        message = "Registration has not started yet."

    elif current_datetime > registration_end:
        registration_open = False
        message = "Registration is closed."

    else:
        registration_open = True
        message = "Registration is open."

    result = {
        "registration_open": registration_open,
        "academic_batch_id": academic_batch_id,
        "semester_id": semester_id,
        "registration_start": registration_start.strftime("%Y-%m-%d %H:%M:%S"),
        "registration_end": registration_end.strftime("%Y-%m-%d %H:%M:%S")
    }

    return returnSuccess(result, message)

@router.get("/get_registration_academic_batch_list")
def get_registration_academic_batch_list(
    base_academic_batch_id: int,
    db: Session = Depends(get_db)
):

    base_batch = db.query(
        IEMSAcademicBatch
    ).filter(
        IEMSAcademicBatch.academic_batch_id == base_academic_batch_id
    ).first()

    if not base_batch:
        return returnSuccess([], "Invalid Academic Batch.")

    academic_batches = (
        db.query(IEMSAcademicBatch)
        .filter(
            IEMSAcademicBatch.start_year == base_batch.start_year,
            IEMSAcademicBatch.end_year == base_batch.end_year,
            IEMSAcademicBatch.status == 1
        )
        .order_by(
            IEMSAcademicBatch.academic_batch_desc
        )
        .all()
    )

    result = []

    for row in academic_batches:
        result.append({
            "academic_batch_id": row.academic_batch_id,
            "academic_batch_code": row.academic_batch_code,
            "academic_batch_desc": row.academic_batch_desc
        })

    return returnSuccess(result)

@router.get("/get_registration_semester_list")
def get_registration_semester_list(
    registration_academic_batch_id: int,
    base_semester_id: int,
    db: Session = Depends(get_db)
):

    base_semester = db.query(
        IEMSemester
    ).filter(
        IEMSemester.semester_id == base_semester_id
    ).first()

    if not base_semester:
        return returnSuccess([], "Invalid Semester.")

    semesters = (
        db.query(IEMSemester)
        .filter(
            IEMSemester.academic_batch_id == registration_academic_batch_id,
            IEMSemester.semester == base_semester.semester,
            IEMSemester.status == 1
        )
        .order_by(
            IEMSemester.semester
        )
        .all()
    )

    result = []

    for row in semesters:
        result.append({
            "semester_id": row.semester_id,
            "semester": row.semester,
            "semester_code": row.semester_code,
            "semester_desc": row.semester_desc,
            "term_name": row.term_name
        })

    return returnSuccess(result)