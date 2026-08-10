from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/attendance-status-report", tags=["Attendance Status Report"])


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


# Parses a date string and stops early on invalid input.
def _parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# Builds an attendance lookup keyed by class date, course, and section.
def _build_attendance_lookup(db: Session, from_date: str, to_date: str) -> dict:
    if not _table_exists(db, "lms_manage_attendance") or not _table_exists(db, "lms_map_student_attendance"):
        return {}

    manage_columns = _get_table_columns(db, "lms_manage_attendance")
    map_columns = _get_table_columns(db, "lms_map_student_attendance")

    manage_id_col = _pick_column(manage_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
    map_manage_fk_col = _pick_column(map_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
    date_col = _pick_column(
        manage_columns,
        ["attendance_date", "class_date", "taken_date", "date", "created_date"],
    )
    course_col = _pick_column(manage_columns, ["crs_id", "course_id"])
    section_col = _pick_column(manage_columns, ["section_id"])

    if not manage_id_col or not map_manage_fk_col or not date_col or not course_col:
        return {}

    rows = db.execute(
        text(
            f"""
            SELECT lma.{date_col} AS class_date,
                   lma.{course_col} AS crs_id,
                   {f'lma.{section_col} AS section_id,' if section_col else ''}
                   COUNT(msa.{map_manage_fk_col}) AS mapped_students
            FROM lms_manage_attendance lma
            LEFT JOIN lms_map_student_attendance msa
              ON msa.{map_manage_fk_col} = lma.{manage_id_col}
            WHERE DATE(lma.{date_col}) BETWEEN :from_date AND :to_date
            GROUP BY lma.{date_col}, lma.{course_col}{f', lma.{section_col}' if section_col else ''}
            """
        ),
        {"from_date": from_date, "to_date": to_date},
    ).mappings().all()

    attendance_lookup = {}
    for row in rows:
        key = (
            str(row.get("class_date")),
            row.get("crs_id"),
            row.get("section_id"),
        )
        attendance_lookup[key] = dict(row)
    return attendance_lookup


# Fetches curriculum options for the attendance status report dropdown.
@router.get("/meta/curriculums")
def get_attendance_status_curriculums(db: Session = Depends(get_db)):
    if not _table_exists(db, "iems_academic_batch"):
        return returnSuccess({"total": 0, "items": []})

    rows = db.execute(
        text(
            """
            SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year
            FROM iems_academic_batch
            ORDER BY academic_batch_id DESC
            """
        )
    ).mappings().all()
    return returnSuccess({"total": len(rows), "items": rows})


# Fetches course and section wise attendance status details for the selected curriculum and date range.
@router.get("/details")
def get_attendance_status_details(
    academic_batch_id: int,
    from_date: str,
    to_date: str,
    crs_id: Optional[int] = Query(default=None),
    section_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    parsed_from = _parse_date(from_date)
    parsed_to = _parse_date(to_date)
    if not parsed_from or not parsed_to:
        return returnException("from_date and to_date must be in YYYY-MM-DD format")
    if parsed_from > parsed_to:
        return returnException("from_date cannot be greater than to_date")

    if not _table_exists(db, "lms_lesson_schedule"):
        return returnSuccess(
            {
                "total": 0,
                "items": [],
                "summary": {"scheduled_classes": 0, "attendance_marked": 0, "attendance_pending": 0},
            }
        )

    lesson_columns = _get_table_columns(db, "lms_lesson_schedule")
    plan_date_col = _pick_column(lesson_columns, ["plan_date", "actual_start_date", "completion_date"])
    if not plan_date_col:
        return returnSuccess(
            {
                "total": 0,
                "items": [],
                "summary": {"scheduled_classes": 0, "attendance_marked": 0, "attendance_pending": 0},
            }
        )

    query = f"""
        SELECT
            ls.{plan_date_col} AS class_date,
            ls.academic_batch_id,
            ls.semester_id,
            ls.crs_id,
            ls.section_id,
            c.crs_code,
            c.crs_title,
            s.section,
            TRIM(CONCAT(IFNULL(u.first_name, ''), ' ', IFNULL(u.last_name, ''))) AS faculty
        FROM lms_lesson_schedule ls
        LEFT JOIN iems_courses c ON c.crs_id = ls.crs_id
        LEFT JOIN iems_section s ON s.id = ls.section_id
        LEFT JOIN iems_users u ON u.id = ls.created_by
        WHERE ls.academic_batch_id = :academic_batch_id
          AND DATE(ls.{plan_date_col}) BETWEEN :from_date AND :to_date
    """
    params = {
        "academic_batch_id": academic_batch_id,
        "from_date": from_date,
        "to_date": to_date,
    }
    if crs_id is not None:
        query += " AND ls.crs_id = :crs_id"
        params["crs_id"] = crs_id
    if section_id is not None:
        query += " AND ls.section_id = :section_id"
        params["section_id"] = section_id
    query += f" GROUP BY ls.{plan_date_col}, ls.academic_batch_id, ls.semester_id, ls.crs_id, ls.section_id, c.crs_code, c.crs_title, s.section, u.first_name, u.last_name"
    query += f" ORDER BY ls.{plan_date_col} DESC, ls.crs_id ASC, ls.section_id ASC"

    schedule_rows = db.execute(text(query), params).mappings().all()
    attendance_lookup = _build_attendance_lookup(db, from_date, to_date)

    items = []
    marked_count = 0
    pending_count = 0

    for row in schedule_rows:
        row_dict = dict(row)
        key = (
            str(row_dict.get("class_date")),
            row_dict.get("crs_id"),
            row_dict.get("section_id"),
        )
        attendance_row = attendance_lookup.get(key)
        attendance_status = "Attendance Pending"
        if attendance_row and (attendance_row.get("mapped_students") or 0) > 0:
            attendance_status = "Attendance Marked"
            marked_count += 1
        else:
            pending_count += 1

        items.append(
            {
                "lls_id": None,
                "class_date": row_dict.get("class_date"),
                "academic_batch_id": row_dict.get("academic_batch_id"),
                "semester_id": row_dict.get("semester_id"),
                "crs_id": row_dict.get("crs_id"),
                "crs_code": row_dict.get("crs_code"),
                "crs_title": row_dict.get("crs_title"),
                "section_id": row_dict.get("section_id"),
                "section": row_dict.get("section"),
                "faculty": row_dict.get("faculty"),
                "attendance_status": attendance_status,
                "attendance_student_count": 0 if not attendance_row else attendance_row.get("mapped_students", 0),
            }
        )

    return returnSuccess(
        {
            "total": len(items),
            "items": items,
            "summary": {
                "scheduled_classes": len(items),
                "attendance_marked": marked_count,
                "attendance_pending": pending_count,
            },
        }
    )
