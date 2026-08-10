from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/student-record-report", tags=["Reports - Student Record"])


# Checks whether a table exists in the active database.
def _table_exists(db: Session, table_name: str) -> bool:
    exists = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return bool(exists)


# Returns available column names for a table.
def _get_table_columns(db: Session, table_name: str) -> set[str]:
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    return {row[0] for row in rows}


# Picks the first matching column from a list of possible names.
def _pick_column(columns: set[str], candidates: list[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


# Builds a readable student name from the available fields.
def _build_student_name(student: dict) -> str:
    parts = [
        str(student.get("first_name") or "").strip(),
        str(student.get("middle_name") or "").strip(),
        str(student.get("last_name") or "").strip(),
    ]
    full_name = " ".join(part for part in parts if part)
    if full_name:
        return full_name
    return str(student.get("name") or "").strip()


# Fetches consolidated marks for a student using whichever mark columns are available.
def _fetch_student_marks(db: Session, student_id: int) -> dict:
    if not _table_exists(db, "cudos_map_courseto_student"):
        return {"total": 0, "items": []}

    course_map_columns = _get_table_columns(db, "cudos_map_courseto_student")
    course_student_col = _pick_column(course_map_columns, ["ssd_id", "student_id"])
    course_id_col = _pick_column(course_map_columns, ["crs_id", "course_id"])
    section_col = _pick_column(course_map_columns, ["section_id", "section"])
    usn_col = _pick_column(course_map_columns, ["student_usn", "usno"])

    if not course_student_col or not course_id_col:
        return {"total": 0, "items": []}

    course_map_rows = db.execute(
        text(
            f"""
            SELECT *
            FROM cudos_map_courseto_student
            WHERE {course_student_col} = :student_id
            ORDER BY {course_id_col} ASC
            """
        ),
        {"student_id": student_id},
    ).mappings().all()

    course_lookup = {}
    if _table_exists(db, "iems_courses"):
        course_rows = db.execute(
            text(
                """
                SELECT crs_id, crs_code, crs_title, academic_batch_id, semester
                FROM iems_courses
                """
            )
        ).mappings().all()
        course_lookup = {row["crs_id"]: dict(row) for row in course_rows}

    section_lookup = {}
    if _table_exists(db, "iems_section"):
        section_rows = db.execute(
            text("SELECT id, section, academic_batch_id, semester_id FROM iems_section")
        ).mappings().all()
        section_lookup = {row["id"]: dict(row) for row in section_rows}

    marks_items = []
    marks_table_exists = _table_exists(db, "cudos_student_assessment_totalmarks")
    qp_table_exists = _table_exists(db, "cudos_qp_definition")
    occasion_table_exists = _table_exists(db, "assessment_occasions")

    qp_lookup = {}
    occasion_lookup = {}
    if marks_table_exists and qp_table_exists:
        qp_columns = _get_table_columns(db, "cudos_qp_definition")
        qp_id_col = _pick_column(qp_columns, ["qpd_id", "qp_definition_id"])
        qp_title_col = _pick_column(qp_columns, ["qpd_title", "qp_title", "question_paper_name"])
        qp_rollout_col = _pick_column(qp_columns, ["qp_rollout", "rollout_status"])
        occasion_fk_col = _pick_column(qp_columns, ["ao_id", "occasion_id"])
        if qp_id_col:
            qp_select = [qp_id_col]
            if qp_title_col:
                qp_select.append(qp_title_col)
            if qp_rollout_col:
                qp_select.append(qp_rollout_col)
            if occasion_fk_col:
                qp_select.append(occasion_fk_col)
            qp_rows = db.execute(
                text(f"SELECT {', '.join(qp_select)} FROM cudos_qp_definition")
            ).mappings().all()
            for row in qp_rows:
                qp_lookup[row[qp_id_col]] = dict(row)

    if marks_table_exists and occasion_table_exists:
        occasion_columns = _get_table_columns(db, "assessment_occasions")
        occasion_id_col = _pick_column(occasion_columns, ["ao_id", "occasion_id"])
        occasion_name_col = _pick_column(
            occasion_columns,
            ["assessment_occasion", "occasion_name", "assessment_name", "ao_name"],
        )
        if occasion_id_col:
            select_columns = [occasion_id_col]
            if occasion_name_col:
                select_columns.append(occasion_name_col)
            occasion_rows = db.execute(
                text(f"SELECT {', '.join(select_columns)} FROM assessment_occasions")
            ).mappings().all()
            for row in occasion_rows:
                occasion_lookup[row[occasion_id_col]] = dict(row)

    if marks_table_exists:
        marks_columns = _get_table_columns(db, "cudos_student_assessment_totalmarks")
        marks_student_col = _pick_column(marks_columns, ["ssd_id", "student_id"])
        marks_course_col = _pick_column(marks_columns, ["crs_id", "course_id"])
        secured_marks_col = _pick_column(
            marks_columns,
            [
                "secured_marks",
                "marks_secured",
                "total_marks_secured",
                "total_secured_marks",
                "grand_total",
                "total_marks",
            ],
        )
        qpd_col = _pick_column(marks_columns, ["qpd_id", "qp_definition_id"])

        if marks_student_col:
            mark_rows = db.execute(
                text(
                    f"""
                    SELECT *
                    FROM cudos_student_assessment_totalmarks
                    WHERE {marks_student_col} = :student_id
                    """
                ),
                {"student_id": student_id},
            ).mappings().all()

            for row in mark_rows:
                row_dict = dict(row)
                course_id = row_dict.get(marks_course_col) if marks_course_col else None
                course_info = course_lookup.get(course_id, {})
                section_id = None
                if course_id is not None:
                    for course_map_row in course_map_rows:
                        if course_map_row.get(course_id_col) == course_id:
                            section_id = course_map_row.get(section_col) if section_col else None
                            break
                qp_definition = qp_lookup.get(row_dict.get(qpd_col)) if qpd_col else None
                occasion = None
                if qp_definition:
                    occasion = occasion_lookup.get(qp_definition.get("ao_id") or qp_definition.get("occasion_id"))

                marks_items.append(
                    {
                        "crs_id": course_id,
                        "crs_code": course_info.get("crs_code"),
                        "crs_title": course_info.get("crs_title"),
                        "section_id": section_id,
                        "section": section_lookup.get(section_id, {}).get("section"),
                        "qpd_id": row_dict.get(qpd_col) if qpd_col else None,
                        "assessment_occasion": None
                        if not occasion
                        else occasion.get("assessment_occasion")
                        or occasion.get("occasion_name")
                        or occasion.get("assessment_name")
                        or occasion.get("ao_name"),
                        "qp_rollout": None if not qp_definition else qp_definition.get("qp_rollout") or qp_definition.get("rollout_status"),
                        "secured_marks": row_dict.get(secured_marks_col) if secured_marks_col else None,
                        "raw_marks_row": row_dict,
                    }
                )

    if not marks_items:
        for course_map_row in course_map_rows:
            course_id = course_map_row.get(course_id_col)
            course_info = course_lookup.get(course_id, {})
            section_id = course_map_row.get(section_col) if section_col else None
            marks_items.append(
                {
                    "crs_id": course_id,
                    "crs_code": course_info.get("crs_code"),
                    "crs_title": course_info.get("crs_title"),
                    "section_id": section_id,
                    "section": section_lookup.get(section_id, {}).get("section"),
                    "student_usn": course_map_row.get(usn_col) if usn_col else None,
                    "secured_marks": None,
                }
            )

    return {"total": len(marks_items), "items": marks_items}


# Fetches enrolled courses from iems_courses based on student's academic_batch_id and current_semester.
# This is the primary fallback when cudos_map_courseto_student has no data for the student.
def _fetch_enrolled_courses(db: Session, student: dict) -> list:
    if not _table_exists(db, "iems_courses"):
        return []

    academic_batch_id = student.get("academic_batch_id")
    current_semester = student.get("current_semester")

    if not academic_batch_id:
        return []

    course_cols = _get_table_columns(db, "iems_courses")
    has_course_type = "course_type" in course_cols
    has_faculty = "faculty_id" in course_cols or "allocated_faculty" in course_cols
    has_credits = "credits" in course_cols or "credit" in course_cols
    credits_col = _pick_column(course_cols, ["credits", "credit", "total_credits"])
    course_type_col = _pick_column(course_cols, ["course_type", "crs_type", "type"])

    select_cols = ["crs_id", "crs_code", "crs_title", "academic_batch_id", "semester"]
    if course_type_col:
        select_cols.append(course_type_col)
    if credits_col:
        select_cols.append(credits_col)

    query = f"""
        SELECT {', '.join(select_cols)}
        FROM iems_courses
        WHERE academic_batch_id = :batch_id
    """
    params: dict = {"batch_id": academic_batch_id}

    if current_semester is not None:
        query += " AND semester = :semester"
        params["semester"] = current_semester

    query += " ORDER BY crs_code ASC"

    rows = db.execute(text(query), params).mappings().all()
    result = []
    for row in rows:
        rd = dict(row)
        result.append({
            "crs_id": rd.get("crs_id"),
            "crs_code": rd.get("crs_code"),
            "crs_title": rd.get("crs_title"),
            "semester": rd.get("semester"),
            "academic_batch_id": rd.get("academic_batch_id"),
            "course_type": rd.get(course_type_col) if course_type_col else None,
            "credits": rd.get(credits_col) if credits_col else None,
        })
    return result


# Fetches attendance summary and dated attendance rows for a student when attendance tables are available.
def _fetch_student_attendance(db: Session, student_id: int) -> dict:
    if not _table_exists(db, "lms_manage_attendance") or not _table_exists(db, "lms_map_student_attendance"):
        return {"summary": {"present": 0, "absent": 0, "other": 0}, "total": 0, "items": []}

    manage_columns = _get_table_columns(db, "lms_manage_attendance")
    map_columns = _get_table_columns(db, "lms_map_student_attendance")

    manage_id_col = _pick_column(manage_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
    map_manage_fk_col = _pick_column(map_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
    student_col = _pick_column(map_columns, ["ssd_id", "student_id"])
    status_col = _pick_column(
        map_columns,
        ["attendance_status", "attendance_flag", "status", "is_present", "present_status"],
    )
    date_col = _pick_column(
        manage_columns,
        ["attendance_date", "class_date", "taken_date", "date", "created_date"],
    )
    course_col = _pick_column(manage_columns, ["crs_id", "course_id"])
    section_col = _pick_column(manage_columns, ["section_id"])

    if not manage_id_col or not map_manage_fk_col or not student_col:
        return {"summary": {"present": 0, "absent": 0, "other": 0}, "total": 0, "items": []}

    select_parts = ["msa.*"]
    if date_col:
        select_parts.append(f"lma.{date_col} AS class_date")
    if course_col:
        select_parts.append(f"lma.{course_col} AS crs_id")
    if section_col:
        select_parts.append(f"lma.{section_col} AS section_id")

    rows = db.execute(
        text(
            f"""
            SELECT {', '.join(select_parts)}
            FROM lms_map_student_attendance msa
            JOIN lms_manage_attendance lma
              ON lma.{manage_id_col} = msa.{map_manage_fk_col}
            WHERE msa.{student_col} = :student_id
            ORDER BY {f'lma.{date_col} DESC' if date_col else 'msa.' + student_col}
            """
        ),
        {"student_id": student_id},
    ).mappings().all()

    course_lookup = {}
    if _table_exists(db, "iems_courses"):
        course_rows = db.execute(
            text("SELECT crs_id, crs_code, crs_title FROM iems_courses")
        ).mappings().all()
        course_lookup = {row["crs_id"]: dict(row) for row in course_rows}

    section_lookup = {}
    if _table_exists(db, "iems_section"):
        section_rows = db.execute(text("SELECT id, section FROM iems_section")).mappings().all()
        section_lookup = {row["id"]: dict(row) for row in section_rows}

    present_count = 0
    absent_count = 0
    other_count = 0
    attendance_items = []

    for row in rows:
        row_dict = dict(row)
        raw_status = row_dict.get(status_col) if status_col else None
        normalized = str(raw_status).strip().lower() if raw_status is not None else ""
        attendance_status = "Unknown"
        if normalized in {"1", "p", "present", "true", "yes"}:
            attendance_status = "Present"
            present_count += 1
        elif normalized in {"0", "a", "absent", "false", "no"}:
            attendance_status = "Absent"
            absent_count += 1
        else:
            other_count += 1

        course_id = row_dict.get("crs_id")
        section_id = row_dict.get("section_id")
        course_info = course_lookup.get(course_id, {})
        section_info = section_lookup.get(section_id, {})

        attendance_items.append(
            {
                "class_date": row_dict.get("class_date"),
                "crs_id": course_id,
                "crs_code": course_info.get("crs_code"),
                "crs_title": course_info.get("crs_title"),
                "section_id": section_id,
                "section": section_info.get("section"),
                "attendance_status": attendance_status,
                "raw_status": raw_status,
            }
        )

    return {
        "summary": {"present": present_count, "absent": absent_count, "other": other_count},
        "total": len(attendance_items),
        "items": attendance_items,
    }


# Fetches student USN suggestions for the student record report.
@router.get("/usn")
def get_student_usn_list(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = """
        SELECT student_id, usno, regno, roll_number, name, first_name, last_name
        FROM iems_students
        WHERE IFNULL(delete_status, 0) = 0 AND usno IS NOT NULL AND usno <> ''
    """
    params = {"limit": limit}
    if search and search.strip():
        query += " AND (usno LIKE :search OR regno LIKE :search OR roll_number LIKE :search)"
        params["search"] = f"%{search.strip()}%"
    query += " ORDER BY student_id DESC LIMIT :limit"
    rows = db.execute(text(query), params).mappings().all()

    items = []
    for row in rows:
        row_dict = dict(row)
        row_dict["student_name"] = _build_student_name(row_dict)
        items.append(row_dict)

    return returnSuccess({"total": len(items), "items": items})


# Fetches student personal info, marks, and attendance using the entered USN.
@router.get("/details")
def get_student_record_details(usno: str, db: Session = Depends(get_db)):
    normalized_usno = usno.strip()
    if not normalized_usno:
        return returnException("usno is required")

    student = db.execute(
        text(
            """
            SELECT *
            FROM iems_students
            WHERE usno = :usno AND IFNULL(delete_status, 0) = 0
            LIMIT 1
            """
        ),
        {"usno": normalized_usno},
    ).mappings().first()

    if not student:
        return returnException("Student not found")

    student_dict = dict(student)
    student_dict["student_name"] = _build_student_name(student_dict)

    academic_batch = None
    if student_dict.get("academic_batch_id") and _table_exists(db, "iems_academic_batch"):
        academic_batch = db.execute(
            text(
                """
                SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year
                FROM iems_academic_batch
                WHERE academic_batch_id = :academic_batch_id
                LIMIT 1
                """
            ),
            {"academic_batch_id": student_dict["academic_batch_id"]},
        ).mappings().first()

    semester = None
    if student_dict.get("semester_id") and _table_exists(db, "iems_semester"):
        semester = db.execute(
            text(
                """
                SELECT semester_id, semester, semester_desc
                FROM iems_semester
                WHERE semester_id = :semester_id
                LIMIT 1
                """
            ),
            {"semester_id": student_dict["semester_id"]},
        ).mappings().first()

    personal_info = {
        "student_id": student_dict.get("student_id"),
        "usno": student_dict.get("usno"),
        "regno": student_dict.get("regno"),
        "roll_number": student_dict.get("roll_number"),
        "student_name": student_dict.get("student_name"),
        "name": student_dict.get("name"),
        "first_name": student_dict.get("first_name"),
        "middle_name": student_dict.get("middle_name"),
        "last_name": student_dict.get("last_name"),
        "email": student_dict.get("email"),
        "mobile": student_dict.get("mobile"),
        "gender": student_dict.get("gender"),
        "dob": student_dict.get("dob"),
        "section": student_dict.get("section"),
        "current_semester": student_dict.get("current_semester"),
        "academic_batch": None if not academic_batch else dict(academic_batch),
        "semester": None if not semester else dict(semester),
    }

    marks = _fetch_student_marks(db, student_dict["student_id"])
    attendance = _fetch_student_attendance(db, student_dict["student_id"])
    enrolled_courses = _fetch_enrolled_courses(db, student_dict)

    return returnSuccess(
        {
            "personal_info": personal_info,
            "consolidated_marks": marks,
            "consolidated_attendance": attendance,
            "enrolled_courses": enrolled_courses,
            "generated_at": datetime.utcnow().isoformat(),
        }
    )
