"""
Consolidated Attendance Report Backend
Endpoints:
  GET /meta/curriculums       — List of academic batches
  GET /meta/terms             — Semesters for a given academic_batch_id
  GET /meta/courses           — Courses for a given batch + semester_id
  GET /meta/sections          — Sections for a given batch + semester_id + crs_id
  GET /report                 — Consolidated attendance table (vertical / horizontal)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/consolidated-attendance-report", tags=["Consolidated Attendance Report"])


# ─── Utilities ────────────────────────────────────────────────────────────────

def _table_exists(db: Session, table_name: str) -> bool:
    return bool(db.execute(
        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=:t"),
        {"t": table_name}
    ).scalar())


def _get_columns(db: Session, table_name: str) -> set:
    rows = db.execute(
        text("SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=:t"),
        {"t": table_name}
    ).fetchall()
    return {r[0] for r in rows}


def _pick(cols: set, candidates: list) -> Optional[str]:
    for c in candidates:
        if c in cols:
            return c
    return None


# ─── Meta endpoints ───────────────────────────────────────────────────────────

@router.get("/meta/curriculums")
def get_curriculums(db: Session = Depends(get_db)):
    if not _table_exists(db, "iems_academic_batch"):
        return returnSuccess({"total": 0, "items": []})
    rows = db.execute(text(
        "SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year "
        "FROM iems_academic_batch ORDER BY academic_batch_id DESC"
    )).mappings().all()
    return returnSuccess({"total": len(rows), "items": [dict(r) for r in rows]})


@router.get("/meta/terms")
def get_terms(academic_batch_id: int, db: Session = Depends(get_db)):
    """Return distinct semesters for the given batch (from iems_semester if available,
    else fall back to iems_courses)."""
    if _table_exists(db, "iems_semester"):
        rows = db.execute(text(
            "SELECT semester_id, semester, semester_desc FROM iems_semester "
            "WHERE academic_batch_id = :b AND IFNULL(status,1) = 1 ORDER BY semester"
        ), {"b": academic_batch_id}).mappings().all()
        if rows:
            return returnSuccess({"total": len(rows), "items": [dict(r) for r in rows]})

    # Fallback: extract distinct semesters from iems_courses
    if _table_exists(db, "iems_courses"):
        rows = db.execute(text(
            "SELECT DISTINCT semester FROM iems_courses "
            "WHERE academic_batch_id = :b ORDER BY semester"
        ), {"b": academic_batch_id}).mappings().all()
        items = [{"semester_id": r["semester"], "semester": r["semester"],
                  "semester_desc": f"{r['semester']} - Semester"} for r in rows]
        return returnSuccess({"total": len(items), "items": items})

    return returnSuccess({"total": 0, "items": []})


@router.get("/meta/courses")
def get_courses(
    academic_batch_id: int,
    semester_id: Optional[int] = None,
    semester: Optional[int] = None,
    db: Session = Depends(get_db)
):
    sem = semester_id or semester
    if not _table_exists(db, "iems_courses"):
        return returnSuccess({"total": 0, "items": []})

    q = "SELECT crs_id, crs_code, crs_title FROM iems_courses WHERE academic_batch_id = :b"
    params: dict = {"b": academic_batch_id}
    if sem is not None:
        q += " AND semester = :s"
        params["s"] = sem
    q += " ORDER BY crs_code"
    rows = db.execute(text(q), params).mappings().all()
    return returnSuccess({"total": len(rows), "items": [dict(r) for r in rows]})


@router.get("/meta/find-perfect-test")
def find_perfect_test(db: Session = Depends(get_db)):
    manage_cols = _get_columns(db, "lms_manage_attendance") if _table_exists(db, "lms_manage_attendance") else []
    map_cols = _get_columns(db, "lms_map_student_attendance") if _table_exists(db, "lms_map_student_attendance") else []
    
    fk = "attendance_id" if "attendance_id" in map_cols else "manage_attendance_id"
    pk = "attendance_id" if "attendance_id" in manage_cols else "lma_id"
    date_col = "attendance_date" if "attendance_date" in manage_cols else "class_date"
    
    q = f"""
        SELECT m.crs_id, m.section_id, COUNT(a.{fk}) as total_attendance, 
               MIN(m.{date_col}) as first_date, MAX(m.{date_col}) as last_date
        FROM lms_manage_attendance m
        JOIN lms_map_student_attendance a ON m.{pk} = a.{fk}
        GROUP BY m.crs_id, m.section_id
        ORDER BY total_attendance DESC
        LIMIT 1
    """
    row = db.execute(text(q)).mappings().first()
    if not row:
        return {"error": "No attendance data found in the database!"}
        
    crs_id = row['crs_id']
    section_id = row['section_id']
    
    crs_q = "SELECT crs_title, academic_batch_id, semester FROM iems_courses WHERE crs_id = :c"
    crs_row = db.execute(text(crs_q), {"c": crs_id}).mappings().first() or {}
    
    batch_q = "SELECT academic_batch_desc FROM iems_academic_batch WHERE academic_batch_id = :b"
    batch_row = db.execute(text(batch_q), {"b": crs_row.get('academic_batch_id', 0)}).mappings().first() or {}
    
    sec_q = "SELECT section FROM iems_section WHERE id = :s"
    sec_row = db.execute(text(sec_q), {"s": section_id}).mappings().first() or {}
    
    try:
        curriculum = batch_row.get('academic_batch_desc', f"ID {crs_row.get('academic_batch_id')}")
        term = f"Semester {crs_row.get('semester', 'Unknown')}"
        course = crs_row.get('crs_title', f"ID {crs_id}")
        section = sec_row.get('section', f"ID {section_id}")
    except Exception as e:
        curriculum = "Error"
        term = "Error"
        course = "Error"
        section = "Error"
    
    return {
        "Curriculum": curriculum,
        "Term": term,
        "Course": course,
        "Section": section,
        "Select Date (From)": str(row['first_date']),
        "Select Date (To)": str(row['last_date']),
        "Total Records": row['total_attendance']
    }


@router.get("/meta/sections")
def get_sections(
    academic_batch_id: int,
    semester_id: Optional[int] = None,
    semester: Optional[int] = None,
    crs_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    sem = semester_id or semester
    if _table_exists(db, "iems_section"):
        q = "SELECT MIN(id) AS section_id, section FROM iems_section WHERE academic_batch_id = :b"
        params: dict = {"b": academic_batch_id}
        q += " GROUP BY section ORDER BY section"
        rows = db.execute(text(q), params).mappings().all()
        if rows:
            return returnSuccess({"total": len(rows), "items": [dict(r) for r in rows]})

    # Fallback: from cudos_map_courseto_student
    if _table_exists(db, "cudos_map_courseto_student"):
        cols = _get_columns(db, "cudos_map_courseto_student")
        section_col = _pick(cols, ["section_id", "section"])
        section_label_col = _pick(cols, ["section"])
        course_col = _pick(cols, ["crs_id", "course_id"])
        if section_col and course_col:
            q = f"SELECT DISTINCT {section_col} AS section_id FROM cudos_map_courseto_student WHERE 1=1"
            params = {}
            if crs_id:
                q += f" AND {course_col} = :c"
                params["c"] = crs_id
            rows2 = db.execute(text(q), params).mappings().all()
            items = [{"section_id": r["section_id"], "section": str(r["section_id"])} for r in rows2]
            return returnSuccess({"total": len(items), "items": items})

    return returnSuccess({"total": 0, "items": []})


# ─── Main Report Endpoint ─────────────────────────────────────────────────────

@router.get("/report")
def get_consolidated_attendance_report(
    academic_batch_id: int,
    semester_id: Optional[int] = Query(default=None),
    semester: Optional[int] = Query(default=None),
    crs_id: Optional[int] = Query(default=None),
    section_id: Optional[int] = Query(default=None),
    range_min: Optional[float] = Query(default=None),
    range_max: Optional[float] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    report_type: str = Query(default="vertical"),   # "vertical" | "horizontal"
    db: Session = Depends(get_db),
):
    sem = semester_id or semester

    # ── Step 1: Get enrolled students ─────────────────────────────────────────
    students = _get_students(db, academic_batch_id, sem, section_id)
    if not students:
        return returnSuccess({
            "total": 0,
            "headers": [],
            "rows": [],
            "summary": {},
            "report_type": report_type,
        })

    # ── Step 2: Determine date range ──────────────────────────────────────────
    date_from, date_to = _resolve_date_range(db, academic_batch_id, sem, crs_id, section_id, from_date, to_date)

    # ── Step 3: Fetch total classes held per student (from lms_manage_attendance) ─
    attendance_data = _get_attendance_counts(db, date_from, date_to, crs_id, section_id)

    # ── Step 4: Fetch per-student per-class records ────────────────────────────
    student_att = _get_per_student_attendance(db, date_from, date_to, crs_id, section_id)

    # ── Step 5: Get dates for horizontal report ────────────────────────────────
    class_dates = sorted(set(attendance_data.get("dates", [])))

    # ── Step 6: Course info ────────────────────────────────────────────────────
    course_info = _get_course_info(db, crs_id)
    total_classes = attendance_data.get("total_classes", 0)

    # ── Step 7: Build report rows ─────────────────────────────────────────────
    rows = []
    for idx, student in enumerate(students, start=1):
        usno = student.get("usno") or student.get("student_usn") or ""
        name = student.get("student_name") or student.get("name") or ""
        sid = student.get("student_id") or student.get("ssd_id")
        section_label = student.get("section", "")

        per_student = student_att.get(str(sid), {})
        present = per_student.get("present", 0)
        absent = per_student.get("absent", 0)
        total = present + absent
        pct = round((present / total) * 100, 2) if total > 0 else 0.0

        # Range filter
        if total_classes > 0:
            if range_min is not None and pct < range_min:
                continue
            if range_max is not None and pct > range_max:
                continue

        # If we have attendance data, only show students who actually have attendance records for this course/section.
        if total_classes > 0:
            if str(sid) not in student_att:
                continue
        else:
            # If we have NO attendance data (new course etc) but the user asked for a specific section,
            # strictly filter out students whose global section map differs (so we don't dump the entire batch).
            # If the student's section string exactly matches, allow it. If the global map is empty, we show them.
            if section_id is not None and student.get("raw_sec_id"):
                if str(student.get("raw_sec_id")) != str(section_id):
                    continue

        row: dict = {
            "sl_no": len(rows) + 1,
            "usno": usno,
            "student_name": name,
            "section": section_label,
            "total_classes": total_classes,
            "present": present,
            "absent": absent,
            "attendance_pct": pct,
        }

        if report_type == "horizontal":
            # Add per-date P/A for each class date
            for d in class_dates:
                row[str(d)] = per_student.get("dates", {}).get(str(d), "-")

        rows.append(row)

    # ── Step 8: Build headers ──────────────────────────────────────────────────
    base_headers = [
        {"key": "sl_no", "label": "Sl No"},
        {"key": "usno", "label": "USN"},
        {"key": "student_name", "label": "Student Name"},
        {"key": "section", "label": "Section"},
        {"key": "total_classes", "label": "Total Classes"},
        {"key": "present", "label": "Present"},
        {"key": "absent", "label": "Absent"},
        {"key": "attendance_pct", "label": "Attendance %"},
    ]
    if report_type == "horizontal":
        for d in class_dates:
            base_headers.append({"key": str(d), "label": str(d)})

    total_students = len(rows)
    avg_pct = round(sum(r["attendance_pct"] for r in rows) / total_students, 2) if total_students > 0 else 0.0

    return returnSuccess({
        "total": total_students,
        "headers": base_headers,
        "rows": rows,
        "summary": {
            "total_students": total_students,
            "total_classes": total_classes,
            "average_attendance_pct": avg_pct,
            "course": course_info,
        },
        "report_type": report_type,
        "date_range": {"from": str(date_from) if date_from else None, "to": str(date_to) if date_to else None},
    })


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_students(db: Session, academic_batch_id: int, semester, section_id):
    """Fetch enrolled students from iems_students or cudos_map_courseto_student."""
    if _table_exists(db, "iems_students"):
        cols = _get_columns(db, "iems_students")
        id_col = _pick(cols, ["student_id", "ssd_id", "id"])
        name_col = _pick(cols, ["name", "student_name", "first_name"])
        usn_col = _pick(cols, ["usno", "usn", "student_usno"])
        status_col = _pick(cols, ["delete_status", "status", "is_active", "active"])
        batch_col = _pick(cols, ["academic_batch_id", "batch_id"])
        sem_col = _pick(cols, ["current_semester", "semester_id", "semester"])
        sec_col = _pick(cols, ["section_id", "section"])

        if id_col and usn_col and name_col and batch_col:
            q = f"SELECT s.{id_col} AS student_id, s.{usn_col} AS usno, s.{name_col} AS student_name"
            if sec_col and _table_exists(db, "iems_section"):
                q += f", sec.section, s.{sec_col} AS raw_sec_id FROM iems_students s LEFT JOIN iems_section sec ON sec.id = s.{sec_col}"
            else:
                q += f", '' AS section, NULL AS raw_sec_id FROM iems_students s"
            
            q += f" WHERE s.{batch_col} = :b"
            params: dict = {"b": academic_batch_id}
            
            if status_col:
                if status_col in ["delete_status"]:
                    q += f" AND IFNULL(s.{status_col}, 0) = 0"
                else:
                    q += f" AND IFNULL(s.{status_col}, 1) = 1"
                    
            q += f" ORDER BY s.{usn_col}"
            rows = db.execute(text(q), params).mappings().all()

            student_dicts = [dict(r) for r in rows]
            
            # If we don't have attendance constraints (total_classes=0), optionally filter by student's global section
            # to prevent returning the entire batch. But if they have attendance maps, we trust the maps completely.
            if section_id is not None and not any(True for _ in student_dicts): pass  # Just logical placeholder
            
            return student_dicts

    return []


def _resolve_date_range(db, academic_batch_id, semester, crs_id, section_id, from_date, to_date):
    """If from_date/to_date not provided, derive from lms_lesson_schedule or iems_semester."""
    if from_date and to_date:
        return from_date, to_date

    if _table_exists(db, "lms_lesson_schedule"):
        cols = _get_columns(db, "lms_lesson_schedule")
        date_col = _pick(cols, ["plan_date", "actual_start_date", "class_date", "completion_date"])
        if date_col:
            q = f"SELECT MIN({date_col}), MAX({date_col}) FROM lms_lesson_schedule WHERE academic_batch_id=:b"
            params: dict = {"b": academic_batch_id}
            if crs_id:
                q += " AND crs_id=:c"
                params["c"] = crs_id
            if section_id:
                q += " AND section_id=:s"
                params["s"] = section_id
            row = db.execute(text(q), params).fetchone()
            if row and row[0]:
                return str(row[0]), str(row[1])

    # Default: past 6 months
    from datetime import date, timedelta
    today = date.today()
    return str(today - timedelta(days=180)), str(today)


def _get_attendance_counts(db: Session, date_from, date_to, crs_id, section_id):
    """Count total distinct class dates (total_classes) and list of dates."""
    if not _table_exists(db, "lms_manage_attendance"):
        return {"total_classes": 0, "dates": []}

    cols = _get_columns(db, "lms_manage_attendance")
    date_col = _pick(cols, ["attendance_date", "class_date", "taken_date", "date", "created_date"])
    crs_col = _pick(cols, ["crs_id", "course_id"])
    sec_col = _pick(cols, ["section_id"])

    if not date_col:
        return {"total_classes": 0, "dates": []}

    q = f"SELECT DISTINCT DATE({date_col}) AS class_date FROM lms_manage_attendance WHERE 1=1"
    params: dict = {}
    if date_from:
        q += f" AND DATE({date_col}) >= :fd"
        params["fd"] = date_from
    if date_to:
        q += f" AND DATE({date_col}) <= :td"
        params["td"] = date_to
    if crs_id and crs_col:
        q += f" AND {crs_col} = :c"
        params["c"] = crs_id
    if section_id and sec_col:
        q += f" AND {sec_col} = :s"
        params["s"] = section_id

    rows = db.execute(text(q), params).fetchall()
    dates = [str(r[0]) for r in rows if r[0]]
    return {"total_classes": len(dates), "dates": dates}


def _get_per_student_attendance(db: Session, date_from, date_to, crs_id, section_id):
    """Return {student_id: {present: N, absent: M, dates: {date: 'P'/'A'}}}."""
    result: dict = {}
    if not _table_exists(db, "lms_manage_attendance") or not _table_exists(db, "lms_map_student_attendance"):
        return result

    manage_cols = _get_columns(db, "lms_manage_attendance")
    map_cols = _get_columns(db, "lms_map_student_attendance")

    manage_id_col = _pick(manage_cols, ["lma_id", "attendance_id", "manage_attendance_id"])
    map_fk_col = _pick(map_cols, ["lma_id", "attendance_id", "manage_attendance_id"])
    student_col = _pick(map_cols, ["student_id", "ssd_id", "student_usno"])
    status_col = _pick(map_cols, ["attendance_status", "status"])
    date_col = _pick(manage_cols, ["attendance_date", "class_date", "taken_date", "date", "created_date"])
    crs_col = _pick(manage_cols, ["crs_id", "course_id"])
    sec_col = _pick(manage_cols, ["section_id"])

    if not all([manage_id_col, map_fk_col, student_col, status_col, date_col]):
        return result

    q = f"""
        SELECT
            msa.{student_col} AS student_id,
            DATE(lma.{date_col}) AS class_date,
            msa.{status_col} AS att_status
        FROM lms_map_student_attendance msa
        INNER JOIN lms_manage_attendance lma
          ON lma.{manage_id_col} = msa.{map_fk_col}
        WHERE 1=1
    """
    params: dict = {}
    if date_from:
        q += f" AND DATE(lma.{date_col}) >= :fd"
        params["fd"] = date_from
    if date_to:
        q += f" AND DATE(lma.{date_col}) <= :td"
        params["td"] = date_to
    if crs_id and crs_col:
        q += f" AND lma.{crs_col} = :c"
        params["c"] = crs_id
    if section_id and sec_col:
        q += f" AND lma.{sec_col} = :s"
        params["s"] = section_id

    rows = db.execute(text(q), params).mappings().all()

    for row in rows:
        sid = str(row["student_id"])
        if sid not in result:
            result[sid] = {"present": 0, "absent": 0, "dates": {}}
        status = str(row["att_status"] or "").lower()
        date_str = str(row["class_date"])
        if "present" in status or status == "p" or status == "1":
            result[sid]["present"] += 1
            result[sid]["dates"][date_str] = "P"
        else:
            result[sid]["absent"] += 1
            result[sid]["dates"][date_str] = "A"

    return result


def _get_course_info(db: Session, crs_id):
    if not crs_id or not _table_exists(db, "iems_courses"):
        return {}
    row = db.execute(
        text("SELECT crs_id, crs_code, crs_title FROM iems_courses WHERE crs_id=:c LIMIT 1"),
        {"c": crs_id}
    ).mappings().first()
    return dict(row) if row else {}
