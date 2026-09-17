"""Student datewise attendance using student and attendance tables, without lesson rosters."""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, select, and_, exists
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess

router = APIRouter(tags=["Student Attendance Report"])

class ReportRequest(BaseModel):
    academic_batch_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    course_id: int = Field(..., gt=0)
    section_id: int = Field(..., gt=0)
    from_date: date
    to_date: date


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
    return None


@router.post("/summary")
def student_attendance_summary(request: ReportRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if request.from_date > request.to_date:
        raise HTTPException(422, detail="From Date cannot be later than To Date")
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(403, detail="Organization context is required")
    metadata = MetaData()
    def table(name):
        return Table(name, metadata, autoload_with=db.get_bind())
    batch, term, course, section, student, header, mark = [table(name) for name in (
        "iems_academic_batch", "iems_semester", "iems_courses", "cudos_master_type_details",
        "iems_students", "lms_manage_attendance", "lms_map_student_attendance",
    )]
    selected = db.execute(select(term.c.semester).select_from(term.join(batch,
        term.c.academic_batch_id == batch.c.academic_batch_id)).where(
        batch.c.academic_batch_id == request.academic_batch_id, batch.c.org_id == org_id,
        term.c.semester_id == request.semester_id,
    )).first()
    if selected is None:
        raise HTTPException(404, detail="Term not found for the selected curriculum")
    selected_course = db.execute(select(course.c.crs_id).where(
        course.c.crs_id == request.course_id, course.c.academic_batch_id == request.academic_batch_id,
        course.c.semester == request.semester_id, course.c.org_id == org_id,
    )).first()
    selected_section = db.execute(select(section.c.mt_details_name).where(
        section.c.mt_details_id == request.section_id,
    )).first()
    if selected_course is None or selected_section is None:
        raise HTTPException(404, detail="Invalid course or section")
    scope = and_(header.c.academic_batch_id == request.academic_batch_id,
        header.c.semester_id == request.semester_id, header.c.crs_id == request.course_id,
        header.c.section_id == request.section_id, header.c.status.in_([1, 2]))
    enrollment = table("cudos_map_courseto_student")
    mapped = exists(select(enrollment.c.student_id).where(
        enrollment.c.student_id == student.c.student_id,
        enrollment.c.academic_batch_id == request.academic_batch_id,
        enrollment.c.semester_id == request.semester_id,
        enrollment.c.crs_id == request.course_id,
        enrollment.c.section_id == request.section_id,
    ))
    # Enrollment defines the roster; current student batch/term/section may have changed.
    # EXISTS avoids duplicate students when multiple mapping rows exist.
    roster = db.execute(select(student.c.student_id, student.c.usno, student.c.name,
        student.c.first_name, student.c.middle_name, student.c.last_name).where(
        student.c.org_id == org_id, mapped,
    ).order_by(student.c.usno, student.c.student_id)).mappings().all()
    rows = {r['student_id']: {'id': str(r['student_id']), 'usn': r['usno'],
        'name': r['name'] or ' '.join(r[key] for key in ('first_name', 'middle_name', 'last_name') if r[key]),
        'present': 0, 'absent': 0, 'dates': {}} for r in roster}
    if not rows:
        return returnSuccess([])
    # Report columns come from active sessions, including sessions without marks.
    session_dates = db.execute(select(header.c.attendance_date).where(scope)).scalars().all()
    report_dates = set()
    for value in session_dates:
        day = parse_day(value)
        if day is None:
            raise HTTPException(409, detail="An attendance record has an invalid date")
        if request.from_date <= day <= request.to_date:
            report_dates.add(day.isoformat())
    for row in rows.values():
        row['dates'] = dict.fromkeys(sorted(report_dates), '')
    # attendance_date is VARCHAR in the supplied schema. Normalize before comparing;
    # SQL string comparisons would omit legacy DD-MM-YYYY records.
    records = db.execute(select(header.c.attendance_date, header.c.attendance_class_count,
        header.c.attendance_id, mark.c.ssd_id, mark.c.attendance_status, mark.c.stud_attendance_id
    ).select_from(header.join(mark, mark.c.attendance_id == header.c.attendance_id)).where(
        scope, mark.c.ssd_id.in_(rows),
    ).order_by(header.c.attendance_id, mark.c.stud_attendance_id)).mappings().all()
    latest = {}
    for record in records:
        latest[(record['attendance_id'], record['ssd_id'])] = record
    for record in latest.values():
        day = parse_day(record['attendance_date'])
        if day is None:
            raise HTTPException(409, detail="An attendance record has an invalid date")
        if not request.from_date <= day <= request.to_date:
            continue
        raw = str(record['attendance_status']).strip().lower()
        status = {'p': 'P', 'present': 'P', '1': 'P', 'a': 'A', 'absent': 'A', '0': 'A', 'l': 'L', 'late': 'L', '0.5': 'L'}.get(raw)
        if status is None:
            raise HTTPException(409, detail="An attendance record has an unsupported status")
        count = record['attendance_class_count'] if record['attendance_class_count'] is not None else 1
        if count < 1:
            raise HTTPException(409, detail="An attendance record has an invalid class count")
        row = rows[record['ssd_id']]
        if status == 'P':
            row['present'] += count
        elif status == 'A':
            row['absent'] += count
        key = day.isoformat()
        row['dates'][key] = ' '.join(filter(None, [row['dates'].get(key), f'{count}{status}']))
    return returnSuccess(list(rows.values()))


class TermsRequest(BaseModel):
    academic_batch_id: int = Field(..., gt=0)


@router.post("/terms")
def student_attendance_terms(request: TermsRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(403, detail="Organization context is required")
    metadata = MetaData()
    term = Table("iems_semester", metadata, autoload_with=db.get_bind())
    batch = Table("iems_academic_batch", metadata, autoload_with=db.get_bind())
    terms = db.execute(select(term.c.semester_id, term.c.semester).select_from(
        term.join(batch, term.c.academic_batch_id == batch.c.academic_batch_id)
    ).where(batch.c.org_id == org_id, batch.c.academic_batch_id == request.academic_batch_id)
      .order_by(term.c.semester, term.c.semester_id)).mappings().all()
    return returnSuccess([{"value": str(row['semester_id']), "label": f"{row['semester']} - Semester"} for row in terms])
