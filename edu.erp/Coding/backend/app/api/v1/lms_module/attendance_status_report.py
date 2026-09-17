# from datetime import datetime
# from typing import Optional

# from fastapi import APIRouter, Depends, Query
# from sqlalchemy import text
# from sqlalchemy.orm import Session

# from app.core.database import get_db
# from app.utils.http_return_helper import returnException, returnSuccess

# router = APIRouter(prefix="/attendance-status-report", tags=["Attendance Status Report"])


# # Checks whether a table exists in the active database.
# def _table_exists(db: Session, table_name: str) -> bool:
#     exists = db.execute(
#         text(
#             """
#             SELECT COUNT(*)
#             FROM information_schema.tables
#             WHERE table_schema = DATABASE() AND table_name = :table_name
#             """
#         ),
#         {"table_name": table_name},
#     ).scalar()
#     return bool(exists)


# # Returns available column names for a table.
# def _get_table_columns(db: Session, table_name: str) -> set[str]:
#     rows = db.execute(
#         text(
#             """
#             SELECT column_name
#             FROM information_schema.columns
#             WHERE table_schema = DATABASE() AND table_name = :table_name
#             """
#         ),
#         {"table_name": table_name},
#     ).fetchall()
#     return {row[0] for row in rows}


# # Picks the first matching column from a list of possible names.
# def _pick_column(columns: set[str], candidates: list[str]) -> Optional[str]:
#     for candidate in candidates:
#         if candidate in columns:
#             return candidate
#     return None


# # Parses a date string and stops early on invalid input.
# def _parse_date(value: str):
#     try:
#         return datetime.strptime(value, "%Y-%m-%d").date()
#     except ValueError:
#         return None


# # Builds an attendance lookup keyed by class date, course, and section.
# def _build_attendance_lookup(db: Session, from_date: str, to_date: str) -> dict:
#     if not _table_exists(db, "lms_manage_attendance") or not _table_exists(db, "lms_map_student_attendance"):
#         return {}

#     manage_columns = _get_table_columns(db, "lms_manage_attendance")
#     map_columns = _get_table_columns(db, "lms_map_student_attendance")

#     manage_id_col = _pick_column(manage_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
#     map_manage_fk_col = _pick_column(map_columns, ["lma_id", "attendance_id", "manage_attendance_id"])
#     date_col = _pick_column(
#         manage_columns,
#         ["attendance_date", "class_date", "taken_date", "date", "created_date"],
#     )
#     course_col = _pick_column(manage_columns, ["crs_id", "course_id"])
#     section_col = _pick_column(manage_columns, ["section_id"])

#     if not manage_id_col or not map_manage_fk_col or not date_col or not course_col:
#         return {}

#     rows = db.execute(
#         text(
#             f"""
#             SELECT lma.{date_col} AS class_date,
#                    lma.{course_col} AS crs_id,
#                    {f'lma.{section_col} AS section_id,' if section_col else ''}
#                    COUNT(msa.{map_manage_fk_col}) AS mapped_students
#             FROM lms_manage_attendance lma
#             LEFT JOIN lms_map_student_attendance msa
#               ON msa.{map_manage_fk_col} = lma.{manage_id_col}
#             WHERE DATE(lma.{date_col}) BETWEEN :from_date AND :to_date
#             GROUP BY lma.{date_col}, lma.{course_col}{f', lma.{section_col}' if section_col else ''}
#             """
#         ),
#         {"from_date": from_date, "to_date": to_date},
#     ).mappings().all()

#     attendance_lookup = {}
#     for row in rows:
#         key = (
#             str(row.get("class_date")),
#             row.get("crs_id"),
#             row.get("section_id"),
#         )
#         attendance_lookup[key] = dict(row)
#     return attendance_lookup


# # Fetches curriculum options for the attendance status report dropdown.
# @router.get("/meta/curriculums")
# def get_attendance_status_curriculums(db: Session = Depends(get_db)):
#     if not _table_exists(db, "iems_academic_batch"):
#         return returnSuccess({"total": 0, "items": []})

#     rows = db.execute(
#         text(
#             """
#             SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year
#             FROM iems_academic_batch
#             ORDER BY academic_batch_id DESC
#             """
#         )
#     ).mappings().all()
#     return returnSuccess({"total": len(rows), "items": rows})


# # Fetches course and section wise attendance status details for the selected curriculum and date range.
# @router.get("/details")
# def get_attendance_status_details(
#     academic_batch_id: int,
#     from_date: str,
#     to_date: str,
#     crs_id: Optional[int] = Query(default=None),
#     section_id: Optional[int] = Query(default=None),
#     db: Session = Depends(get_db),
# ):
#     parsed_from = _parse_date(from_date)
#     parsed_to = _parse_date(to_date)
#     if not parsed_from or not parsed_to:
#         return returnException("from_date and to_date must be in YYYY-MM-DD format")
#     if parsed_from > parsed_to:
#         return returnException("from_date cannot be greater than to_date")

#     if not _table_exists(db, "lms_lesson_schedule"):
#         return returnSuccess(
#             {
#                 "total": 0,
#                 "items": [],
#                 "summary": {"scheduled_classes": 0, "attendance_marked": 0, "attendance_pending": 0},
#             }
#         )

#     lesson_columns = _get_table_columns(db, "lms_lesson_schedule")
#     plan_date_col = _pick_column(lesson_columns, ["plan_date", "actual_start_date", "completion_date"])
#     if not plan_date_col:
#         return returnSuccess(
#             {
#                 "total": 0,
#                 "items": [],
#                 "summary": {"scheduled_classes": 0, "attendance_marked": 0, "attendance_pending": 0},
#             }
#         )

#     query = f"""
#         SELECT
#             ls.{plan_date_col} AS class_date,
#             ls.academic_batch_id,
#             ls.semester_id,
#             ls.crs_id,
#             ls.section_id,
#             c.crs_code,
#             c.crs_title,
#             s.section,
#             TRIM(CONCAT(IFNULL(u.first_name, ''), ' ', IFNULL(u.last_name, ''))) AS faculty
#         FROM lms_lesson_schedule ls
#         LEFT JOIN iems_courses c ON c.crs_id = ls.crs_id
#         LEFT JOIN iems_section s ON s.id = ls.section_id
#         LEFT JOIN iems_users u ON u.id = ls.created_by
#         WHERE ls.academic_batch_id = :academic_batch_id
#           AND DATE(ls.{plan_date_col}) BETWEEN :from_date AND :to_date
#     """
#     params = {
#         "academic_batch_id": academic_batch_id,
#         "from_date": from_date,
#         "to_date": to_date,
#     }
#     if crs_id is not None:
#         query += " AND ls.crs_id = :crs_id"
#         params["crs_id"] = crs_id
#     if section_id is not None:
#         query += " AND ls.section_id = :section_id"
#         params["section_id"] = section_id
#     query += f" GROUP BY ls.{plan_date_col}, ls.academic_batch_id, ls.semester_id, ls.crs_id, ls.section_id, c.crs_code, c.crs_title, s.section, u.first_name, u.last_name"
#     query += f" ORDER BY ls.{plan_date_col} DESC, ls.crs_id ASC, ls.section_id ASC"

#     schedule_rows = db.execute(text(query), params).mappings().all()
#     attendance_lookup = _build_attendance_lookup(db, from_date, to_date)

#     items = []
#     marked_count = 0
#     pending_count = 0

#     for row in schedule_rows:
#         row_dict = dict(row)
#         key = (
#             str(row_dict.get("class_date")),
#             row_dict.get("crs_id"),
#             row_dict.get("section_id"),
#         )
#         attendance_row = attendance_lookup.get(key)
#         attendance_status = "Attendance Pending"
#         if attendance_row and (attendance_row.get("mapped_students") or 0) > 0:
#             attendance_status = "Attendance Marked"
#             marked_count += 1
#         else:
#             pending_count += 1

#         items.append(
#             {
#                 "lls_id": None,
#                 "class_date": row_dict.get("class_date"),
#                 "academic_batch_id": row_dict.get("academic_batch_id"),
#                 "semester_id": row_dict.get("semester_id"),
#                 "crs_id": row_dict.get("crs_id"),
#                 "crs_code": row_dict.get("crs_code"),
#                 "crs_title": row_dict.get("crs_title"),
#                 "section_id": row_dict.get("section_id"),
#                 "section": row_dict.get("section"),
#                 "faculty": row_dict.get("faculty"),
#                 "attendance_status": attendance_status,
#                 "attendance_student_count": 0 if not attendance_row else attendance_row.get("mapped_students", 0),
#             }
#         )

#     return returnSuccess(
#         {
#             "total": len(items),
#             "items": items,
#             "summary": {
#                 "scheduled_classes": len(items),
#                 "attendance_marked": marked_count,
#                 "attendance_pending": pending_count,
#             },
#         }
#     )


from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/attendance-status-report", tags=["Attendance Status Report"])


def _parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _table_columns(db: Session, table_name: str) -> set[str]:
    rows = db.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = :table_name
        """),
        {"table_name": table_name},
    ).fetchall()
    return {r[0] for r in rows}


def _date_expr(alias: str, column: str) -> str:
    # Legacy attendance/timetable tables store dates as VARCHAR in some installations.
    return (
        f"COALESCE(STR_TO_DATE({alias}.{column}, '%d-%m-%Y'), "
        f"STR_TO_DATE({alias}.{column}, '%Y-%m-%d'), DATE({alias}.{column}))"
    )


def _month_key(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%m-%Y")
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value)[:10], fmt).strftime("%m-%Y")
        except ValueError:
            pass
    return ""


def _display_date(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y")
    raw = str(value)[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%d-%m-%Y")
        except ValueError:
            pass
    return raw


@router.get("/meta/curriculums")
def get_attendance_status_curriculums(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year
        FROM iems_academic_batch
        WHERE COALESCE(status, 1) = 1
        ORDER BY academic_batch_id DESC
    """)).mappings().all()
    return returnSuccess({"total": len(rows), "items": [dict(r) for r in rows]})


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
    if parsed_from >= parsed_to:
        return returnException("To Date must be greater than From Date (minimum one-day range).")

    attendance_columns = _table_columns(db, "lms_manage_attendance")
    attendance_table = "lms_manage_attendance"
    if not attendance_columns:
        attendance_table = "cudos_lms_manage_attendance"
        attendance_columns = _table_columns(db, attendance_table)
    day_date = _date_expr("dm", "class_date")
    lesson_date = _date_expr("ls", "plan_date")
    att_date = _date_expr("ma", "attendance_date")
    # Match the same lesson/header used by attendance.py. A detail ID alone
    # can cover several sessions and must not override an explicit lesson ID.
    attendance_match = (
        "ma.lls_id = ls.lls_id"
        if "lls_id" in attendance_columns else
        f"ma.academic_batch_id = d.academic_batch_id "
        f"AND ma.semester_id = d.semester_id AND ma.crs_id = c.crs_id "
        f"AND ma.section_id = COALESCE(bm.batch_id, d.section_id) "
        f"AND ma.tt_detail_id = d.tt_detail_id AND {att_date} = {day_date}"
    )
    attendance_state = f"""(
        SELECT ma.status FROM {attendance_table} ma
        WHERE {attendance_match}
        ORDER BY ma.attendance_id DESC LIMIT 1
    )"""

    query = f"""
        SELECT
            d.tt_detail_id,
            dm.tt_day_map_id,
            d.academic_batch_id,
            d.semester_id,
            COALESCE(s.term_name, s.semester_desc, CONCAT('Term ', s.semester)) AS term_name,
            COALESCE(s.semester, 0) AS term_order,
            c.crs_id,
            c.crs_code,
            c.crs_title,
            COALESCE(bm.batch_id, d.section_id) AS section_id,
            bm.batch_id,
            COALESCE(batch_mt.mt_details_name, sec_mt.mt_details_name, '--') AS section,
            tt.class_start_time,
            tt.class_end_time,
            {day_date} AS class_date,
            ls.status AS lesson_status,
            faculty.faculty,
            CASE
                WHEN {attendance_state} = 2 THEN 'Complete'
                WHEN {attendance_state} = 1 THEN 'In-progress'
                ELSE 'Not Started'
            END AS class_status
        FROM lms_tt_time_table_day_mapping dm
        INNER JOIN lms_tt_time_table tt
            ON tt.time_table_id = dm.time_table_id
           AND tt.tt_detail_id = dm.tt_detail_id
        INNER JOIN lms_tt_time_table_details d
            ON d.tt_detail_id = dm.tt_detail_id
        LEFT JOIN iems_semester s
            ON s.semester_id = d.semester_id
        LEFT JOIN cudos_master_type_details sec_mt
            ON sec_mt.mt_details_id = d.section_id
        LEFT JOIN lms_tt_time_table_batch_map bm
            ON bm.time_table_id = tt.time_table_id
           AND bm.tt_detail_id = d.tt_detail_id
        INNER JOIN iems_courses c
            ON c.crs_id = COALESCE(NULLIF(dm.allot_crs_id, 0), bm.crs_id, tt.crs_id)
        LEFT JOIN cudos_master_type_details batch_mt
            ON batch_mt.mt_details_id = bm.batch_id
        LEFT JOIN (
            SELECT
                m.academic_batch_id,
                m.semester_id,
                m.crs_id,
                m.section_id,
                GROUP_CONCAT(
                    DISTINCT TRIM(CONCAT_WS(' ', NULLIF(u.first_name, ''), NULLIF(u.middle_name, ''), NULLIF(u.last_name, '')))
                    ORDER BY u.first_name, u.last_name SEPARATOR ', '
                ) AS faculty
            FROM cudos_map_courseto_course_instructor m
            LEFT JOIN iems_users u ON u.id = m.course_instructor_id
            GROUP BY m.academic_batch_id, m.semester_id, m.crs_id, m.section_id
        ) faculty
            ON faculty.academic_batch_id = d.academic_batch_id
           AND faculty.semester_id = d.semester_id
           AND faculty.crs_id = c.crs_id
           AND faculty.section_id = COALESCE(bm.batch_id, d.section_id)
        LEFT JOIN lms_lesson_schedule ls
            ON ls.academic_batch_id = d.academic_batch_id
           AND ls.semester_id = d.semester_id
           AND ls.crs_id = c.crs_id
           AND ls.section_id = COALESCE(bm.batch_id, d.section_id)
           AND ls.tt_detail_id = d.tt_detail_id
           AND ls.time_table_id = tt.time_table_id
           AND (ls.tt_day_map_id = dm.tt_day_map_id
                OR (ls.tt_day_map_id IS NULL AND {lesson_date} = {day_date}))
        WHERE d.academic_batch_id = :academic_batch_id
          AND {day_date} BETWEEN :from_date AND :to_date
    """

    params = {
        "academic_batch_id": academic_batch_id,
        "from_date": parsed_from,
        "to_date": parsed_to,
    }
    if crs_id is not None:
        query += " AND c.crs_id = :crs_id"
        params["crs_id"] = crs_id
    if section_id is not None:
        query += " AND COALESCE(bm.batch_id, d.section_id) = :section_id"
        params["section_id"] = section_id

    query += """
        ORDER BY term_order, term_name, c.crs_code, section, class_date, tt.class_start_time
    """

    raw_rows = db.execute(text(query), params).mappings().all()

    grouped: dict[tuple, dict] = {}
    months: list[str] = []
    summary = {"scheduled_classes": 0, "complete": 0, "in_progress": 0, "not_started": 0}

    # Joins may return several lesson/batch records for one scheduled class.
    # Count each mapping and effective section once, with completion taking priority.
    unique_classes = {}
    priority = {"Not Started": 0, "In-progress": 1, "Complete": 2}
    for raw in raw_rows:
        identity = (raw["tt_day_map_id"], raw["crs_id"], raw["section_id"])
        previous = unique_classes.get(identity)
        if previous is None or priority[raw["class_status"]] > priority[previous["class_status"]]:
            unique_classes[identity] = raw

    for raw in unique_classes.values():
        row = dict(raw)
        month = _month_key(row.get("class_date"))
        if month and month not in months:
            months.append(month)

        key = (
            row.get("semester_id"),
            row.get("crs_id"),
            row.get("section_id"),
            row.get("batch_id"),
            row.get("faculty") or "--",
        )
        if key not in grouped:
            grouped[key] = {
                "semester_id": row.get("semester_id"),
                "term_name": row.get("term_name") or "--",
                "term_order": row.get("term_order") or 0,
                "crs_id": row.get("crs_id"),
                "crs_code": row.get("crs_code"),
                "crs_title": row.get("crs_title"),
                "section_id": row.get("section_id"),
                "batch_id": row.get("batch_id"),
                "section": row.get("section") or "--",
                "faculty": row.get("faculty") or "--",
                "months": {},
            }

        bucket = grouped[key]["months"].setdefault(
            month,
            {
                "Complete": {"count": 0, "classes": []},
                "In-progress": {"count": 0, "classes": []},
                "Not Started": {"count": 0, "classes": []},
            },
        )
        status = row["class_status"]
        bucket[status]["count"] += 1
        bucket[status]["classes"].append(
            {
                "date": _display_date(row.get("class_date")),
                "start_time": row.get("class_start_time") or "",
                "end_time": row.get("class_end_time") or "",
                "tt_day_map_id": row.get("tt_day_map_id"),
            }
        )

        summary["scheduled_classes"] += 1
        if status == "Complete":
            summary["complete"] += 1
        elif status == "In-progress":
            summary["in_progress"] += 1
        else:
            summary["not_started"] += 1

    def month_sort_key(value: str):
        return datetime.strptime(value, "%m-%Y")

    months.sort(key=month_sort_key)
    items = sorted(
        grouped.values(),
        key=lambda x: (x["term_order"], x["term_name"], x["crs_code"] or "", x["section"] or ""),
    )

    return returnSuccess({
        "total": len(items),
        "months": months,
        "items": items,
        "summary": summary,
    })
