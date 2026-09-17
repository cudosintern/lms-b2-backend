"""Attendance-specific dropdown APIs.

Registered by app.api.v1.routes under /attendance.
"""

from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, and_, inspect, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import (
    IEMSAcademicBatch, IEMSCourses, IEMSemester, LMSLessonSchedule,
    LMSTimetableDetails, LMSTimetable, LMSTimetableDayMapping, LMSTimetableBatchMap,
)
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess

router = APIRouter(tags=["LMS-Attendance"])


class AttendanceClassRequest(BaseModel):
    academic_batch_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    crs_id: int = Field(..., gt=0)
    section_id: int = Field(..., gt=0)
    class_date: date
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)
    lls_id: int | None = Field(None, gt=0)
    tt_day_map_id: int | None = Field(None, gt=0)
    tt_detail_id: int | None = Field(None, gt=0)
    time_table_id: int | None = Field(None, gt=0)


def _attendance_table(db, name, metadata):
    if not inspect(db.get_bind()).has_table(name) and name in ("lms_manage_attendance", "lms_map_student_attendance"):
        name = "cudos_" + name
    if not inspect(db.get_bind()).has_table(name):
        raise HTTPException(503, detail="Attendance storage is not configured")
    return Table(name, metadata, autoload_with=db.get_bind())


def _attendance_column(table, *names):
    for name in names:
        if name in table.c:
            return table.c[name]
    raise HTTPException(503, detail="Attendance storage does not support class-specific records")


@router.post("/class-students")
def fetch_class_students(
    request: AttendanceClassRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(403, detail="Organization context is required")
    course = db.query(IEMSCourses.crs_id).filter(
        IEMSCourses.crs_id == request.crs_id,
        IEMSCourses.academic_batch_id == request.academic_batch_id,
        IEMSCourses.semester == request.semester_id,
        IEMSCourses.org_id == org_id,
    ).first()
    if course is None:
        raise HTTPException(404, detail="Course not found for the selected curriculum and term")
    lesson_table = _attendance_table(db, "lms_lesson_schedule", MetaData())
    query = select(lesson_table).where(
        lesson_table.c.academic_batch_id == request.academic_batch_id,
        lesson_table.c.semester_id == request.semester_id,
        lesson_table.c.crs_id == request.crs_id,
        lesson_table.c.section_id == request.section_id,
    )
    mapping_names = ("tt_day_map_id", "tt_detail_id", "time_table_id")
    mapped = any(getattr(request, name) is not None for name in mapping_names)
    if mapped:
        if not all(getattr(request, name) is not None for name in mapping_names):
            raise HTTPException(422, detail="All three timetable mapping IDs are required")
        for name in mapping_names:
            column = _attendance_column(lesson_table, name)
            if name == "tt_day_map_id":
                query = query.where(or_(column == request.tt_day_map_id, and_(
                    column.is_(None), lesson_table.c.plan_date == request.class_date,
                )))
            else:
                query = query.where(column == getattr(request, name))
    else:
        query = query.where(lesson_table.c.plan_date == request.class_date)
    if request.lls_id is not None:
        query = query.where(lesson_table.c.lls_id == request.lls_id)
    lessons = db.execute(query).all()
    if not mapped:
        lessons = [lesson for lesson in lessons if
                   str(lesson.start_time)[:5] == request.start_time[:5] and
                   str(lesson.end_time)[:5] == request.end_time[:5]]
    if not lessons:
        return returnSuccess({"students": [], "state": "pending", "message": "Lesson schedule setup is pending for this class."})
    if len(lessons) != 1:
        raise HTTPException(409, detail="Select a unique lesson schedule for this class")
    lesson = lessons[0]
    metadata = MetaData()
    students = _attendance_table(db, "iems_students", metadata)
    attendance = _attendance_table(db, "lms_manage_attendance", metadata)
    marks = _attendance_table(db, "lms_map_student_attendance", metadata)
    student_id = _attendance_column(students, "student_id")
    attendance_id = _attendance_column(attendance, "attendance_id", "lma_id", "manage_attendance_id")
    if "lls_id" in attendance.c:
        header_query = select(attendance).where(attendance.c.lls_id == lesson.lls_id)
    else:
        # Legacy attendance headers identify a date and timetable detail.
        header_query = select(attendance).where(
            attendance.c.academic_batch_id == request.academic_batch_id,
            attendance.c.semester_id == request.semester_id,
            attendance.c.crs_id == request.crs_id,
            attendance.c.section_id == request.section_id,
            attendance.c.attendance_date == request.class_date,
            attendance.c.tt_detail_id == lesson.tt_detail_id,
        )
    header = db.execute(header_query.order_by(attendance_id.desc())).mappings().first()
    records = []
    if header is not None and str(header.get("status")) in ("1", "2"):
        records = db.execute(select(marks).where(
            _attendance_column(marks, "attendance_id", "lma_id", "manage_attendance_id") == header[attendance_id.name],
        )).mappings().all()
    mark_student = _attendance_column(marks, "ssd_id", "student_id")
    mark_status = _attendance_column(marks, "attendance_status", "status")
    if header is None or str(header.get("status")) == "0":
        # First attendance: the lesson mapping defines the initial roster.
        enrollment = _attendance_table(db, "lms_ls_student_map", metadata)
        roster_query = select(students).join(
            enrollment, _attendance_column(enrollment, "ssd_id", "student_id") == student_id,
        ).where(_attendance_column(enrollment, "lls_id") == lesson.lls_id).distinct()
        if "status" in students.c:
            roster_query = roster_query.where(students.c.status == 1)
    else:
        # Saved attendance owns its roster, even if lesson enrollment changes later.
        roster_query = select(students).join(marks, mark_student == student_id).where(
            _attendance_column(marks, "attendance_id", "lma_id", "manage_attendance_id") == header[attendance_id.name],
        ).distinct()
    if "org_id" in students.c:
        roster_query = roster_query.where(students.c.org_id == org_id)
    roster = db.execute(roster_query).mappings().all()
    by_student = {str(row[mark_student.name]): row for row in records}
    result = []
    for student in roster:
        sid = student[student_id.name]
        record = by_student.get(str(sid))
        raw_status = str(record[mark_status.name]).lower() if record is not None else ""
        statuses = {"0": "absent", "a": "absent", "absent": "absent", "1": "present", "p": "present", "present": "present", "late": "late", "l": "late"}
        if record is not None and raw_status not in statuses:
            raise HTTPException(409, detail="The class contains an unsupported attendance status")
        result.append({
            "student_id": sid,
            "roll_number": student.get("roll_number") or student.get("usno") or str(sid),
            "name": student.get("name") or " ".join(str(student.get(key)).strip() for key in ("first_name", "middle_name", "last_name") if student.get(key)),
            "email": student.get("email") or "",
            "status": statuses.get(raw_status, "present"),
            "is_marked": record is not None,
            "remarks": (record.get("remarks") or record.get("notes") or "") if record is not None else "",
        })
    result.sort(key=lambda student: (student["roll_number"], student["name"]))
    state = "not_taken" if header is None or str(header.get("status")) == "0" else "finalized" if str(header.get("status")) == "2" else "draft"
    return returnSuccess({"students": result, "state": state, "lls_id": lesson.lls_id,
                          "attendance_id": header[attendance_id.name] if header is not None else None})


class AttendanceScheduleRequest(BaseModel):
    academic_batch_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    crs_id: int = Field(..., gt=0)
    section_id: int = Field(..., gt=0)


def schedule_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    for pattern in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), pattern).date().isoformat()
        except ValueError:
            pass
    return None


@router.post("/scheduled-dates")
def fetch_attendance_schedule(
    request: AttendanceScheduleRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context is required")
    course = db.query(IEMSCourses.crs_id).filter(
        IEMSCourses.crs_id == request.crs_id,
        IEMSCourses.academic_batch_id == request.academic_batch_id,
        IEMSCourses.semester == request.semester_id,
        IEMSCourses.org_id == org_id,
    ).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found for the selected curriculum and term")

    # A date's course allocation overrides its usual timetable course.
    no_allocation = or_(LMSTimetableDayMapping.allot_crs_id.is_(None), LMSTimetableDayMapping.allot_crs_id == 0)
    rows = db.query(
        LMSTimetableDayMapping.tt_day_map_id,
        LMSTimetableDayMapping.class_date,
        LMSTimetable.tt_detail_id,
        LMSTimetable.time_table_id,
        LMSTimetable.class_start_time,
        LMSTimetable.class_end_time,
    ).join(
        LMSTimetable, LMSTimetable.time_table_id == LMSTimetableDayMapping.time_table_id,
    ).join(
        LMSTimetableDetails, LMSTimetableDetails.tt_detail_id == LMSTimetable.tt_detail_id,
    ).outerjoin(
        LMSTimetableBatchMap, LMSTimetableBatchMap.time_table_id == LMSTimetable.time_table_id,
    ).filter(
        LMSTimetableDetails.academic_batch_id == request.academic_batch_id,
        LMSTimetableDetails.semester_id == request.semester_id,
        or_(
            LMSTimetableBatchMap.batch_id == request.section_id,
            and_(LMSTimetableBatchMap.tt_batch_map_id.is_(None), LMSTimetableDetails.section_id == request.section_id),
        ),
        or_(
            LMSTimetableDayMapping.allot_crs_id == request.crs_id,
            and_(no_allocation, or_(
                LMSTimetableBatchMap.crs_id == request.crs_id,
                and_(LMSTimetableBatchMap.tt_batch_map_id.is_(None), LMSTimetable.crs_id == request.crs_id),
            )),
        ),
    ).distinct().all()
    classes = []
    for row in rows:
        day = schedule_date(row.class_date)
        if day:
            classes.append({"class_date": day, "tt_day_map_id": row.tt_day_map_id,
                            "tt_detail_id": row.tt_detail_id, "time_table_id": row.time_table_id,
                            "start_time": row.class_start_time,
                            "end_time": row.class_end_time})

    # Include standalone lesson/extra-class dates that have no timetable mapping.
    lesson_table = _attendance_table(db, "lms_lesson_schedule", MetaData())
    lessons = db.execute(select(lesson_table).where(
        lesson_table.c.academic_batch_id == request.academic_batch_id,
        lesson_table.c.semester_id == request.semester_id,
        lesson_table.c.crs_id == request.crs_id,
        lesson_table.c.section_id == request.section_id,
    )).mappings().all()
    mapping_names = ("tt_day_map_id", "tt_detail_id", "time_table_id")
    for lesson in lessons:
        mapped = any(lesson.get(name) for name in mapping_names)
        if mapped:
            # The timetable supplies the actual scheduled date and time.
            # Do not expose lessons whose mapping is outside these filters.
            continue
        day = schedule_date(lesson["plan_date"])
        if not day:
            continue
        classes.append({"class_date": day, "lls_id": lesson["lls_id"],
                        "start_time": lesson["start_time"], "end_time": lesson["end_time"]})
    classes.sort(key=lambda item: (item["class_date"], item["start_time"] or ""))
    return returnSuccess({"dates": sorted({item["class_date"] for item in classes}), "classes": classes})


class AttendanceCoursesRequest(BaseModel):
    academic_batch_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)


@router.post("/courses")
def fetch_attendance_courses(
    request: AttendanceCoursesRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return active, approved courses belonging to the selected batch and term.

    IEMSCourses.semester stores the semester_id used by the existing LMS
    timetable and course-registration APIs, not the displayed term label.
    """
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context is required")

    selected_term = (
        db.query(IEMSemester.semester_id)
        .join(
            IEMSAcademicBatch,
            IEMSAcademicBatch.academic_batch_id == IEMSemester.academic_batch_id,
        )
        .filter(
            IEMSAcademicBatch.academic_batch_id == request.academic_batch_id,
            IEMSAcademicBatch.org_id == org_id,
            IEMSemester.semester_id == request.semester_id,
        )
        .first()
    )
    if selected_term is None:
        raise HTTPException(status_code=404, detail="Term not found for the selected curriculum")

    courses = (
        db.query(
            IEMSCourses.crs_id,
            IEMSCourses.crs_code,
            IEMSCourses.crs_title,
            IEMSCourses.crs_mode,
            IEMSCourses.lab_course,
            IEMSCourses.tutorial,
            IEMSCourses.lms_crs_attendance_finalize,
        )
        .filter(
            IEMSCourses.academic_batch_id == request.academic_batch_id,
            IEMSCourses.semester == request.semester_id,
            IEMSCourses.org_id == org_id,
            IEMSCourses.status == 1,
            IEMSCourses.state_id == 4,
        )
        .order_by(IEMSCourses.crs_code.asc(), IEMSCourses.crs_id.asc())
        .all()
    )
    return returnSuccess([
        {
            "crs_id": course.crs_id,
            "crs_code": course.crs_code,
            "crs_title": course.crs_title,
            "crs_mode": course.crs_mode,
            "type": "Lab" if str(course.lab_course) == "1" else "Theory",
            "tutorial": course.tutorial,
            "lms_crs_attendance_finalize": course.lms_crs_attendance_finalize,
        }
        for course in courses
    ])


class AttendanceMarkItem(BaseModel):
    student_id: int = Field(..., gt=0)
    status: Literal["present", "absent", "late"]
    remarks: str = ""


class AttendanceMarkRequest(AttendanceClassRequest):
    state: Literal["draft", "finalized"] = "finalized"
    students: list[AttendanceMarkItem] = Field(..., min_length=1)


@router.post("/mark")
def mark_attendance(request: AttendanceMarkRequest,
                    current_user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    try:
        # Serialize saves for this course, including first-time attendance.
        db.query(IEMSCourses.crs_id).filter(
            IEMSCourses.crs_id == request.crs_id,
            IEMSCourses.org_id == current_user.get("org_id"),
        ).with_for_update().first()
        existing = fetch_class_students(request, current_user, db)["data"]
        if existing["state"] == "pending":
            raise HTTPException(409, detail="Map the lesson schedule before saving attendance")
        if existing["state"] == "finalized":
            raise HTTPException(409, detail="Attendance is already finalized")
        ids = [item.student_id for item in request.students]
        if len(ids) != len(set(ids)) or set(ids) != {s["student_id"] for s in existing["students"]}:
            raise HTTPException(422, detail="Submitted students must match the selected class roster")
        metadata = MetaData()
        header = _attendance_table(db, "lms_manage_attendance", metadata)
        marks = _attendance_table(db, "lms_map_student_attendance", metadata)
        lesson = _attendance_table(db, "lms_lesson_schedule", metadata)
        selected = db.execute(select(lesson).where(lesson.c.lls_id == existing["lls_id"])).mappings().one()
        detail_id = selected.get("tt_detail_id") or request.tt_detail_id
        if not detail_id and "lls_id" not in header.c:
            raise HTTPException(409, detail="A timetable detail is required to save this class")
        if "lls_id" not in header.c:
            siblings = db.execute(select(lesson.c.lls_id).where(
                lesson.c.academic_batch_id == request.academic_batch_id,
                lesson.c.semester_id == request.semester_id,
                lesson.c.crs_id == request.crs_id,
                lesson.c.section_id == request.section_id,
                lesson.c.tt_detail_id == detail_id,
                lesson.c.plan_date == request.class_date,
            )).all()
            if len(siblings) > 1:
                raise HTTPException(409, detail="Attendance storage needs a lesson ID to distinguish multiple classes on this date")
        actor = current_user.get("user_id") or current_user.get("id")
        values = dict(academic_batch_id=request.academic_batch_id, semester_id=request.semester_id,
                      crs_id=request.crs_id, section_id=request.section_id,
                      attendance_date=request.class_date.isoformat(), tt_detail_id=detail_id,
                      status=2 if request.state == "finalized" else 1, attendance_class_count=1, modified_by=actor, modified_at=date.today())
        if "lls_id" in header.c:
            values["lls_id"] = existing["lls_id"]
        values = {k:v for k,v in values.items() if k in header.c}
        attendance_id = existing.get("attendance_id")
        if attendance_id is None:
            values.update({k:v for k,v in dict(created_by=actor, created_at=date.today()).items() if k in header.c})
            saved = db.execute(header.insert().values(**values))
            attendance_id = saved.inserted_primary_key[0]
        else:
            db.execute(header.update().where(header.c.attendance_id == attendance_id).values(**values))
            db.execute(marks.delete().where(marks.c.attendance_id == attendance_id))
        roster = {s["student_id"]:s for s in existing["students"]}
        for item in request.students:
            values = dict(attendance_id=attendance_id, ssd_id=item.student_id,
                          attendance_status=item.status, remarks=item.remarks,
                          refer_absent_status=1 if item.status == "absent" else 0)
            # No attendance-type master is configured; zero denotes no custom type.
            if "a_type_id" in marks.c:
                values["a_type_id"] = 0
            db.execute(marks.insert().values(**{k:v for k,v in values.items() if k in marks.c}))
        db.commit()
        return returnSuccess({"attendance_id": attendance_id, "state": request.state, "saved_count": len(ids)})
    except Exception:
        db.rollback()
        raise


@router.post("/enable")
def enable_attendance(request: AttendanceClassRequest,
                      current_user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    try:
        db.query(IEMSCourses.crs_id).filter(
            IEMSCourses.crs_id == request.crs_id,
            IEMSCourses.org_id == current_user.get("org_id"),
        ).with_for_update().first()
        existing = fetch_class_students(request, current_user, db)["data"]
        if existing["state"] != "finalized":
            raise HTTPException(409, detail="Only finalized attendance can be enabled")
        header = _attendance_table(db, "lms_manage_attendance", MetaData())
        values = dict(status=1, modified_by=current_user.get("user_id") or current_user.get("id"), modified_at=date.today())
        db.execute(header.update().where(header.c.attendance_id == existing["attendance_id"]).values(
            **{k:v for k,v in values.items() if k in header.c}))
        db.commit()
        return returnSuccess({"attendance_id": existing["attendance_id"], "state": "draft"})
    except Exception:
        db.rollback()
        raise
