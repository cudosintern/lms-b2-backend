"""Course-mapped attendance roster, using the migrated LMS schema."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess

router = APIRouter(prefix="/consolidated-attendance-report", tags=["Consolidated Attendance Report"])


def tables(db, *names):
    metadata = MetaData()
    return [Table(name, metadata, autoload_with=db.get_bind()) for name in names]


def organization(user):
    if not user.get("org_id"):
        raise HTTPException(403, detail="Organization context is required")
    return user["org_id"]


def validate_term(db, batch_id, term_id, user):
    batch, term = tables(db, "iems_academic_batch", "iems_semester")
    found = db.execute(select(term.c.semester_id).select_from(term.join(batch,
        batch.c.academic_batch_id == term.c.academic_batch_id)).where(
        batch.c.academic_batch_id == batch_id, batch.c.org_id == organization(user),
        term.c.semester_id == term_id)).first()
    if found is None:
        raise HTTPException(404, detail="Term not found for the selected curriculum")


def items(db, statement):
    result = [dict(row) for row in db.execute(statement).mappings()]
    return returnSuccess({"total": len(result), "items": result})


@router.get("/meta/curriculums")
def get_curriculums(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batch, = tables(db, "iems_academic_batch")
    return items(db, select(batch.c.academic_batch_id, batch.c.academic_batch_code,
        batch.c.academic_batch_desc).where(batch.c.org_id == organization(user))
        .order_by(batch.c.academic_batch_id.desc()))


@router.get("/meta/terms")
def get_terms(academic_batch_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batch, term = tables(db, "iems_academic_batch", "iems_semester")
    return items(db, select(term.c.semester_id, term.c.semester, term.c.semester_desc)
        .select_from(term.join(batch, batch.c.academic_batch_id == term.c.academic_batch_id))
        .where(batch.c.academic_batch_id == academic_batch_id, batch.c.org_id == organization(user))
        .order_by(term.c.semester, term.c.semester_id))


@router.get("/meta/courses")
def get_courses(academic_batch_id: int, semester_id: int, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    validate_term(db, academic_batch_id, semester_id, user)
    course, = tables(db, "iems_courses")
    # In this LMS migration, iems_courses.semester contains the semester primary key.
    return items(db, select(course.c.crs_id, course.c.crs_code, course.c.crs_title).where(
        course.c.academic_batch_id == academic_batch_id, course.c.semester == semester_id,
        course.c.org_id == organization(user)).order_by(course.c.crs_code))


@router.get("/meta/sections")
def get_sections(academic_batch_id: int, semester_id: int,
                 crs_ids: List[int] = Query(...), db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    validate_term(db, academic_batch_id, semester_id, user)
    section, instructor, course = tables(db, "cudos_master_type_details",
        "cudos_map_courseto_course_instructor", "iems_courses")
    return items(db, select(section.c.mt_details_id.label("section_id"),
        section.c.mt_details_name.label("section")).select_from(instructor.join(section,
        instructor.c.section_id == section.c.mt_details_id).join(course,
        instructor.c.crs_id == course.c.crs_id)).where(
        instructor.c.academic_batch_id == academic_batch_id, instructor.c.semester_id == semester_id,
        instructor.c.crs_id.in_(crs_ids), course.c.org_id == organization(user))
        .distinct().order_by(section.c.mt_details_name))


def parse_day(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for pattern in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip()[:10], pattern).date()
        except ValueError:
            pass
    raise HTTPException(409, detail="An attendance record has an invalid date")


def present_units(value, held):
    """Legacy numeric statuses store attended units; textual statuses describe the session."""
    raw = str(value).strip().lower()
    if value is None or raw == "":
        return None
    if raw in ("p", "present"):
        return held
    if raw in ("a", "absent"):
        return Decimal(0)
    if raw in ("l", "late"):
        return Decimal("0.5")
    try:
        units = Decimal(raw)
    except InvalidOperation:
        raise HTTPException(409, detail="An attendance record has an unsupported status")
    if not units.is_finite() or not 0 <= units <= held:
        raise HTTPException(409, detail="Attendance units must be between zero and the class count")
    return units


def build_report(roster, sessions, marks, from_date, to_date, range_min, range_max,
                 range_max_inclusive, report_type):
    # Latest mark wins for duplicate student/session records, without multiplying class totals.
    latest = {}
    for mark in sorted(marks, key=lambda m: m["stud_attendance_id"]):
        latest[(mark["attendance_id"], mark["ssd_id"])] = mark["attendance_status"]
    scoped, days = {}, set()
    for session in sessions:
        day = parse_day(session["attendance_date"])
        if not from_date <= day <= to_date:
            continue
        held = Decimal(session["attendance_class_count"] if session["attendance_class_count"] is not None else 1)
        if not held.is_finite() or held <= 0:
            raise HTTPException(409, detail="An attendance record has an invalid class count")
        scoped.setdefault((session["crs_id"], session["section_id"]), []).append((session, day.isoformat(), held))
        days.add(day.isoformat())
    rows, seen = [], set()
    for student in roster:
        identity = (student["student_id"], student["crs_id"], student["section_id"])
        if identity in seen:
            continue
        seen.add(identity)
        held = present = absent = unmarked = Decimal(0)
        daily = {}
        for session, day, count in scoped.get(identity[1:], []):
            held += count
            units = present_units(latest.get((session["attendance_id"], student["student_id"])), count)
            totals = daily.setdefault(day, [Decimal(0), Decimal(0), Decimal(0)])
            if units is None:
                unmarked += count
                totals[2] += count
            else:
                present += units
                absent += count - units
                totals[0] += units
                totals[1] += count - units
        pct = present * 100 / held if held else Decimal(0)
        if pct < Decimal(str(range_min)) or pct > Decimal(str(range_max)):
            continue
        if not range_max_inclusive and pct == Decimal(str(range_max)):
            continue
        row = {**student, "sl_no": len(rows) + 1, "total_classes": float(held),
               "present": float(present), "absent": float(absent), "unmarked": float(unmarked),
               "attendance_pct": round(float(pct), 2)}
        if report_type == "horizontal":
            for day in sorted(days):
                row[day] = " ".join(f"{float(count):g}{label}" for count, label in
                    zip(daily.get(day, []), ("P", "A", "U")) if count) or "—"
        rows.append(row)
    headers = [{"key": key, "label": label} for key, label in (
        ("sl_no", "Sl No"), ("usno", "USN"), ("student_name", "Student Name"),
        ("crs_code", "Course"), ("crs_title", "Course Title"), ("section", "Section"),
        ("total_classes", "Total Classes"), ("present", "Present"), ("absent", "Absent"),
        ("unmarked", "Unmarked"), ("attendance_pct", "Attendance %"))]
    if report_type == "horizontal":
        headers.extend({"key": day, "label": day} for day in sorted(days))
    return {"total": len(rows), "headers": headers, "rows": rows,
        "summary": {"total_students": len({r["student_id"] for r in rows}),
                    "total_classes": float(sum((count for group in scoped.values() for _, _, count in group), Decimal(0))),
                    "average_attendance_pct": round(sum(r["attendance_pct"] for r in rows) / len(rows), 2) if rows else 0},
        "report_type": report_type, "date_range": {"from": from_date.isoformat(), "to": to_date.isoformat()}}


@router.get("/report")
def get_consolidated_attendance_report(
    academic_batch_id: int, semester_id: int, from_date: date, to_date: date,
    crs_ids: List[int] = Query(...), section_id: Optional[int] = None,
    range_min: float = Query(0, ge=0, le=100), range_max: float = Query(100, ge=0, le=100),
    range_max_inclusive: bool = True, report_type: Literal["vertical", "horizontal"] = "vertical",
    db: Session = Depends(get_db), user: dict = Depends(get_current_user),
):
    if from_date > to_date or range_min > range_max:
        raise HTTPException(422, detail="The start of the date or percentage range exceeds its end")
    if not crs_ids:
        raise HTTPException(422, detail="Select at least one course")
    validate_term(db, academic_batch_id, semester_id, user)
    course, enrollment, student, section, header, mark = tables(db, "iems_courses",
        "cudos_map_courseto_student", "iems_students", "cudos_master_type_details",
        "lms_manage_attendance", "lms_map_student_attendance")
    selected = db.execute(select(course.c.crs_id).where(course.c.crs_id.in_(crs_ids),
        course.c.academic_batch_id == academic_batch_id, course.c.semester == semester_id,
        course.c.org_id == organization(user))).scalars().all()
    if set(selected) != set(crs_ids):
        raise HTTPException(404, detail="A selected course does not belong to this curriculum and term")
    scope = [enrollment.c.academic_batch_id == academic_batch_id,
             enrollment.c.semester_id == semester_id, enrollment.c.crs_id.in_(selected),
             student.c.org_id == organization(user)]
    attendance_scope = [header.c.academic_batch_id == academic_batch_id,
        header.c.semester_id == semester_id, header.c.crs_id.in_(selected), header.c.status.in_([1, 2])]
    if section_id is not None:
        scope.append(enrollment.c.section_id == section_id)
        attendance_scope.append(header.c.section_id == section_id)
    roster = db.execute(select(student.c.student_id, student.c.usno,
        student.c.name.label("student_name"), student.c.first_name, student.c.middle_name, student.c.last_name,
        course.c.crs_id, course.c.crs_code, course.c.crs_title, enrollment.c.section_id,
        section.c.mt_details_name.label("section")).select_from(enrollment.join(student,
        enrollment.c.student_id == student.c.student_id).join(course, enrollment.c.crs_id == course.c.crs_id)
        .outerjoin(section, enrollment.c.section_id == section.c.mt_details_id))
        .where(*scope).distinct().order_by(course.c.crs_code, student.c.usno)).mappings().all()
    roster = [dict(r) for r in roster]
    instructor, faculty = tables(db, "cudos_map_courseto_course_instructor", "iems_users")
    name_columns = [faculty.c[name] for name in ("title", "first_name", "middle_name", "last_name")
                    if name in faculty.c]
    assigned = db.execute(select(instructor.c.crs_id, instructor.c.section_id, faculty.c.id,
        *name_columns).select_from(instructor.join(faculty,
        instructor.c.course_instructor_id == faculty.c.id)).where(
        instructor.c.academic_batch_id == academic_batch_id, instructor.c.semester_id == semester_id,
        instructor.c.crs_id.in_(selected), faculty.c.org_id == organization(user))
        .distinct().order_by(faculty.c.id)).mappings().all()
    instructors = {}
    for assignment in assigned:
        name = " ".join(str(assignment[column.name]).strip() for column in name_columns
                        if assignment[column.name] and str(assignment[column.name]).strip())
        if name:
            instructors.setdefault((assignment["crs_id"], assignment["section_id"]), []).append(name)
    for row in roster:
        row["course_instructor"] = ", ".join(instructors.get((row["crs_id"], row["section_id"]), []))
        row["student_name"] = row["student_name"] or " ".join(row[k] for k in
            ("first_name", "middle_name", "last_name") if row[k])
    sessions = db.execute(select(header).where(*attendance_scope)).mappings().all()
    # Restrict marks to the requested scope and dates before loading them. Dates may be legacy strings.
    session_ids = [s["attendance_id"] for s in sessions if from_date <= parse_day(s["attendance_date"]) <= to_date]
    marks = db.execute(select(mark).where(mark.c.attendance_id.in_(session_ids),
        mark.c.ssd_id.in_({r["student_id"] for r in roster}))).mappings().all() if session_ids and roster else []
    return returnSuccess(build_report(roster, sessions, marks, from_date, to_date,
        range_min, range_max, range_max_inclusive, report_type))
