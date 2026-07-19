from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_,Time

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import (IEMSAcademicBatch, 
IEMSemester,
IEMSCourses,
IEMSCourseType,
CudosCrclmComponent,
CudosMapCoursetoCourseInstructor,
LMSAcademicBatchSemesterCrsStructure,
CudosMapCoursetoStudent,
CudosCrclmComponent,
IEMStudents,
IEMSUsers,
MasterType,
MasterTypeDetails
)

from .student_course_registration_schema import *

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

    if not semester:
        return returnSuccess({
            "status": False,
            "message": "Registration dates are not configured.",
            "status_message": "Registration dates are not configured.",
            "status_color": "red"
        })

    # Combine date & time
    start_datetime = datetime.strptime(
        f"{semester.enroll_start_date.strftime('%Y-%m-%d')} {semester.enroll_start_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    end_datetime = datetime.strptime(
        f"{semester.enroll_end_date.strftime('%Y-%m-%d')} {semester.enroll_end_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    current_datetime = datetime.now()

    formatted_start_date = semester.enroll_start_date.strftime("%d-%m-%Y")
    formatted_start_time = semester.enroll_start_time.strftime("%I:%M %p")
    formatted_end_date = semester.enroll_end_date.strftime("%d-%m-%Y")
    formatted_end_time = semester.enroll_end_time.strftime("%I:%M %p")  


    if start_datetime <= current_datetime <= end_datetime:

        is_registration_open = True
        registration_status = "open"
        validate_date = 1
        status_message = (
            f"Registration is OPEN. Last date: "
            f"{formatted_end_date} {formatted_end_time}"
        )
        status_color = "green"
        remaining = end_datetime - current_datetime

    elif current_datetime > end_datetime:

        is_registration_open = False
        registration_status = "closed"
        validate_date = 0
        status_message = (
            f"Registration has been closed on "
            f"{formatted_end_date} {formatted_end_time}"
        )
        status_color = "maroon"
        remaining = None

    else:

        is_registration_open = False
        registration_status = "not_started"
        validate_date = 0
        status_message = (
            f"Registration will open at "
            f"{formatted_start_date} {formatted_start_time}"
        )
        status_color = "orange"
        remaining = start_datetime - current_datetime

    if remaining:
        total_seconds = int(remaining.total_seconds())

        days = total_seconds // 86400
        total_seconds %= 86400

        hours = total_seconds // 3600
        total_seconds %= 3600

        minutes = total_seconds // 60
        seconds = total_seconds % 60
    else:
        days = hours = minutes = seconds = 0

    result = {
        "status": True,
        "enroll_start_date": str(semester.enroll_start_date),
        "enroll_start_time": semester.enroll_start_time,
        "enroll_end_date": str(semester.enroll_end_date),
        "enroll_end_time": semester.enroll_end_time,
        "formatted_enroll_start_date": formatted_start_date,
        "formatted_enroll_start_time": formatted_start_time,
        "formatted_enroll_end_date": formatted_end_date,
        "formatted_enroll_end_time": formatted_end_time,
        "is_registration_open": is_registration_open,
        "registration_status": registration_status,
        "validate_date": validate_date,
        "status_message": status_message,
        "status_color": status_color,
        "remaining_days": days,
        "remaining_hours": hours,
        "remaining_minutes": minutes,
        "remaining_seconds": seconds
    }

    return returnSuccess(result)

@router.post("/available-courses")
def available_courses(
    request: CourseRegistrationRequest,
    db: Session = Depends(get_db)
):

    current_time = datetime.now()

    #############################################
    # Registered Courses
    #############################################

    registered_courses = db.query(
        CudosMapCoursetoStudent.crs_id,
        CudosMapCoursetoStudent.crs_reg_flag
    ).filter(
        CudosMapCoursetoStudent.student_id == request.student_id,
        CudosMapCoursetoStudent.academic_batch_id == request.academic_batch_id,
        CudosMapCoursetoStudent.semester_id == request.semester_id,
        CudosMapCoursetoStudent.section_id == request.section_id
    ).all()

    registered_dict = {
        x.crs_id: x.crs_reg_flag
        for x in registered_courses
    }

    #############################################
    # Student Registered Count
    #############################################

    registered_count = db.query(
        func.count(CudosMapCoursetoStudent.mcstd_id)
    ).filter(
        CudosMapCoursetoStudent.student_id == request.student_id,
        CudosMapCoursetoStudent.std_academic_batch_id == request.parent_academic_batch_id,
        CudosMapCoursetoStudent.std_semester_id == request.parent_semester_id
    ).scalar()

    #############################################
    # Course Structure
    #############################################

    structure = db.query(
        func.coalesce(
            func.sum(LMSAcademicBatchSemesterCrsStructure.stud_min_crs_enroll), 0
        ).label("min_count"),
        func.coalesce(
            func.sum(LMSAcademicBatchSemesterCrsStructure.stud_max_crs_enroll), 0
        ).label("max_count")
    ).filter(
        LMSAcademicBatchSemesterCrsStructure.academic_batch_id == request.academic_batch_id,
        LMSAcademicBatchSemesterCrsStructure.semester_id == request.semester_id
    ).first()

    min_count = structure.min_count or 0
    max_count = structure.max_count or 0

    #############################################
    # Courses
    #############################################

    query = db.query(

        IEMSCourses,

        IEMSCourseType,

        CudosCrclmComponent,

        CudosMapCoursetoCourseInstructor,

        IEMSemester,

        LMSAcademicBatchSemesterCrsStructure

    ).join(

        CudosMapCoursetoCourseInstructor,

        and_(
            IEMSCourses.crs_id ==
            CudosMapCoursetoCourseInstructor.crs_id,

            IEMSCourses.academic_batch_id ==
            CudosMapCoursetoCourseInstructor.academic_batch_id,

            IEMSCourses.semester ==
            CudosMapCoursetoCourseInstructor.semester_id
        )

    ).join(

        IEMSCourseType,
        IEMSCourseType.course_type_id ==
        IEMSCourses.course_type_id

    ).join(

        CudosCrclmComponent,
        CudosCrclmComponent.cc_id ==
        IEMSCourseType.crclm_component_id

    ).join(

        IEMSemester,

        and_(
            IEMSemester.academic_batch_id ==
            IEMSCourses.academic_batch_id,

            IEMSemester.semester_id ==
            IEMSCourses.semester
        )

    ).join(

        LMSAcademicBatchSemesterCrsStructure,

        and_(
            LMSAcademicBatchSemesterCrsStructure.academic_batch_id ==
            IEMSCourses.academic_batch_id,

            LMSAcademicBatchSemesterCrsStructure.semester_id ==
            IEMSCourses.semester,

            LMSAcademicBatchSemesterCrsStructure.crs_type_id ==
            IEMSCourses.course_type_id
        )

    ).filter(

        IEMSCourses.academic_batch_id ==
        request.academic_batch_id,

        IEMSCourses.semester ==
        request.semester_id,

        CudosMapCoursetoCourseInstructor.section_id ==
        request.section_id,

        IEMSCourses.status > 0

    )

    if request.open_elective_flag == 1:

        query = query.filter(
            CudosCrclmComponent.crclm_comp_alias_name ==
            "OPEN_ELECTIVE"
        )

    courses = query.all()

    result = []

    #############################################
    # Loop Courses
    #############################################

    for (
        course,
        course_type,
        component,
        instructor,
        semester,
        structure_row

    ) in courses:

        ####################################
        # Registered students
        ####################################

        course_registered = db.query(
            func.count(CudosMapCoursetoStudent.mcstd_id)
        ).filter(
            CudosMapCoursetoStudent.crs_id ==
            course.crs_id
        ).scalar()

        ####################################
        # Registration Window
        ####################################

        is_open = True

        if component.crclm_comp_alias_name == "OPEN_ELECTIVE":

            if course.reg_start_date and course.reg_end_date:

                is_open = (
                    course.reg_start_date
                    <= current_time
                    <= course.reg_end_date
                )

            else:

                start = datetime.combine(
                    semester.enroll_start_date,
                    semester.enroll_start_time
                )

                end = datetime.combine(
                    semester.enroll_end_date,
                    semester.enroll_end_time
                )

                is_open = start <= current_time <= end

        ####################################
        # Response
        ####################################

        result.append({

            "crs_id": course.crs_id,

            "course_code": course.crs_code,

            "course_name": course.crs_title,

            "course_type": course_type.course_type_desc,

            "course_type_id": course.course_type_id,

            "credits": course.total_credits,

            "component": component.crclm_comp_alias_name,

            "registered_count": course_registered,

            "enrollment_limit": course.total_stud_enroll,

            "already_registered":
                course.crs_id in registered_dict,

            "crs_reg_flag":
                registered_dict.get(course.crs_id),

            "registration_open": is_open,

            "stud_min_crs_enroll":
                structure_row.stud_min_crs_enroll,

            "stud_max_crs_enroll":
                structure_row.stud_max_crs_enroll

        })

    return returnSuccess({

        "registered_courses": registered_count,

        "minimum_courses": min_count,

        "maximum_courses": max_count,

        "remaining_courses": max(max_count - registered_count, 0),

        "course_list": result

    })

@router.post("/get_registration_section_list")
def get_registration_section_list(
    request: SectionListRequest,
    db: Session = Depends(get_db)
):

    sections = (
        db.query(
            MasterTypeDetails.mt_details_id.label("section_id"),
            MasterTypeDetails.mt_details_name.label("section_name")
        )
        .join(
            CudosMapCoursetoCourseInstructor,
            CudosMapCoursetoCourseInstructor.section_id
            == MasterTypeDetails.mt_details_id
        )
        .filter(
            CudosMapCoursetoCourseInstructor.academic_batch_id
            == request.academic_batch_id,

            CudosMapCoursetoCourseInstructor.semester_id
            == request.semester_id
        )
        .distinct()
        .order_by(MasterTypeDetails.mt_details_name)
        .all()
    )

    data = [
        {
            "section_id": sec.section_id,
            "section_name": sec.section_name
        }
        for sec in sections
    ]

    return returnSuccess(data)

@router.post("/registered-courses")
def get_registered_courses(
    request: RegisteredCourseRequest,
    db: Session = Depends(get_db)
):

    registered_courses = (
        db.query(

            CudosMapCoursetoStudent.mcstd_id,

            CudosMapCoursetoStudent.crs_id,

            CudosMapCoursetoStudent.section_id,

            CudosMapCoursetoStudent.batch_id,

            CudosMapCoursetoStudent.crs_reg_flag,

            CudosMapCoursetoStudent.status,

            CudosMapCoursetoStudent.created_date,

            IEMSCourses.crs_code,

            IEMSCourses.crs_title,

            IEMSCourses.total_credits,

            IEMSCourseType.course_type_desc,

            CudosCrclmComponent.crclm_comp_alias_name,

            MasterTypeDetails.mt_details_name.label("section_name")

        )

        .join(
            IEMSCourses,
            IEMSCourses.crs_id == CudosMapCoursetoStudent.crs_id
        )

        .join(
            IEMSCourseType,
            IEMSCourseType.course_type_id == IEMSCourses.course_type_id
        )

        .outerjoin(
            CudosCrclmComponent,
            CudosCrclmComponent.cc_id ==
            IEMSCourseType.crclm_component_id
        )

        .outerjoin(
            MasterTypeDetails,
            MasterTypeDetails.mt_details_id ==
            CudosMapCoursetoStudent.section_id
        )

        .filter(

            CudosMapCoursetoStudent.student_id ==
            request.student_id,

            CudosMapCoursetoStudent.std_academic_batch_id ==
            request.parent_academic_batch_id,

            CudosMapCoursetoStudent.std_semester_id ==
            request.parent_semester_id

        )

        .order_by(
            IEMSCourseType.course_type_desc,
            IEMSCourses.crs_code
        )

        .all()
    )

    result = []

    for row in registered_courses:

        result.append({

            "mcstd_id": row.mcstd_id,

            "course_id": row.crs_id,

            "course_code": row.crs_code,

            "course_name": row.crs_title,

            "course_type": row.course_type_desc,

            "component": row.crclm_comp_alias_name,

            "credits": row.total_credits,

            "section_id": row.section_id,

            "section_name": row.section_name,

            "batch_id": row.batch_id,

            "registration_flag": row.crs_reg_flag,

            "status": row.status,

            "registered_date": row.created_date

        })

    return returnSuccess(result)