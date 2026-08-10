from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...utils.http_return_helper import returnException, returnSuccess

router = APIRouter(prefix="/schedule-class", tags=["Schedule Class"])


# Carries the payload required to create a scheduled class entry.
class ScheduleClassCreateRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    crs_id: int
    section_id: int
    topic_id: Optional[int] = None
    plan_date: date
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)
    portion_ref: Optional[str] = None
    portion_per_hour: Optional[str] = None
    video_link: Optional[str] = None
    status: int = 1
    created_by: int


# Carries the payload required to update a scheduled class entry.
class ScheduleClassUpdateRequest(BaseModel):
    academic_batch_id: Optional[int] = None
    semester_id: Optional[int] = None
    crs_id: Optional[int] = None
    section_id: Optional[int] = None
    topic_id: Optional[int] = None
    plan_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    portion_ref: Optional[str] = None
    portion_per_hour: Optional[str] = None
    video_link: Optional[str] = None
    status: Optional[int] = None
    modified_by: int


# Carries the payload used to check duplicate scheduled class timings.
class ScheduleClassDuplicateRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    crs_id: Optional[int] = None
    section_id: int
    plan_date: date
    start_time: str = Field(..., min_length=1)
    end_time: str = Field(..., min_length=1)
    exclude_lls_id: Optional[int] = None


# Fetches available column names for a table.
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


# Checks whether a referenced master row exists.
def _record_exists(db: Session, table_name: str, key_column: str, value: Optional[int]) -> bool:
    if value is None:
        return False
    exists = db.execute(
        text(f"SELECT COUNT(*) FROM {table_name} WHERE {key_column} = :value"),
        {"value": value},
    ).scalar()
    return bool(exists)


# Resolves the matching timetable context for the selected class slot when it exists.
def _resolve_timetable_context(
    db: Session,
    academic_batch_id: int,
    semester_id: int,
    crs_id: int,
    section_id: int,
    plan_date: date,
    start_time: str,
    end_time: str,
) -> dict:
    weekday_name = plan_date.strftime("%A")
    row = db.execute(
        text(
            """
            SELECT
                td.tt_detail_id,
                tt.time_table_id,
                dm.tt_day_map_id,
                dm.day_id,
                dm.week_day_name,
                dm.allot_by,
                u.username,
                TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS faculty_name
            FROM lms_tt_time_table_details td
            LEFT JOIN lms_tt_time_table tt
              ON tt.tt_detail_id = td.tt_detail_id
             AND tt.crs_id = :crs_id
             AND tt.class_start_time = :start_time
             AND tt.class_end_time = :end_time
            LEFT JOIN lms_tt_time_table_day_mapping dm
              ON dm.time_table_id = tt.time_table_id
             AND DATE(dm.class_date) = :plan_date
            LEFT JOIN iems_users u
              ON u.id = dm.allot_by
            WHERE td.academic_batch_id = :academic_batch_id
              AND td.semester_id = :semester_id
              AND td.section_id = :section_id
            ORDER BY
              CASE
                WHEN DATE(dm.class_date) = :plan_date THEN 0
                WHEN dm.week_day_name = :weekday_name THEN 1
                ELSE 2
              END,
              dm.tt_day_map_id DESC,
              tt.time_table_id DESC
            LIMIT 1
            """
        ),
        {
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "section_id": section_id,
            "crs_id": crs_id,
            "start_time": start_time,
            "end_time": end_time,
            "plan_date": plan_date,
            "weekday_name": weekday_name,
        },
    ).mappings().first()
    return {} if not row else dict(row)


# Checks for another scheduled class in the same time slot.
def _find_duplicate_schedule(
    db: Session,
    academic_batch_id: int,
    semester_id: int,
    section_id: int,
    plan_date: date,
    start_time: str,
    end_time: str,
    crs_id: Optional[int] = None,
    exclude_lls_id: Optional[int] = None,
):
    query = """
        SELECT lls_id, academic_batch_id, semester_id, crs_id, section_id, plan_date, start_time, end_time
        FROM lms_lesson_schedule
        WHERE academic_batch_id = :academic_batch_id
          AND semester_id = :semester_id
          AND section_id = :section_id
          AND plan_date = :plan_date
          AND start_time = :start_time
          AND end_time = :end_time
    """
    params = {
        "academic_batch_id": academic_batch_id,
        "semester_id": semester_id,
        "section_id": section_id,
        "plan_date": plan_date,
        "start_time": start_time,
        "end_time": end_time,
    }
    if crs_id is not None:
        query += " AND crs_id = :crs_id"
        params["crs_id"] = crs_id
    if exclude_lls_id is not None:
        query += " AND lls_id <> :exclude_lls_id"
        params["exclude_lls_id"] = exclude_lls_id
    query += " LIMIT 1"
    return db.execute(text(query), params).mappings().first()


# Fetches distinct course types available in the course master.
@router.get("/meta/course-types")
def get_schedule_course_types(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT DISTINCT course_type_id
            FROM iems_courses
            WHERE course_type_id IS NOT NULL
            ORDER BY course_type_id ASC
            """
        )
    ).mappings().all()
    data = [{"course_type_id": row["course_type_id"], "label": f"Course Type {row['course_type_id']}"} for row in rows]
    return returnSuccess({"total": len(data), "items": data})


# Fetches courses for the selected course type and optional academic filters.
@router.get("/meta/courses")
def get_schedule_courses(
    course_type_id: Optional[int] = Query(default=None),
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = """
        SELECT crs_id, crs_code, crs_title, course_type_id, academic_batch_id, semester
        FROM iems_courses
        WHERE 1 = 1
    """
    params = {}
    if course_type_id is not None:
        query += " AND course_type_id = :course_type_id"
        params["course_type_id"] = course_type_id
    if academic_batch_id is not None:
        query += " AND academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    if semester_id is not None:
        query += " AND semester = (SELECT semester FROM iems_semester WHERE semester_id = :semester_id)"
        params["semester_id"] = semester_id
    query += " ORDER BY crs_id DESC"
    rows = db.execute(text(query), params).mappings().all()
    return returnSuccess({"total": len(rows), "items": rows})


# Fetches batch, semester, section, topic, and timetable slot data for the selected course.
@router.get("/meta/batches-sections")
def get_schedule_batches_sections(crs_id: int, db: Session = Depends(get_db)):
    course = db.execute(
        text(
            """
            SELECT crs_id, crs_code, crs_title, academic_batch_id, semester, course_type_id
            FROM iems_courses
            WHERE crs_id = :crs_id
            LIMIT 1
            """
        ),
        {"crs_id": crs_id},
    ).mappings().first()
    if not course:
        return returnException("Course not found")

    batch = db.execute(
        text(
            """
            SELECT academic_batch_id, academic_batch_code, academic_batch_desc, academic_year
            FROM iems_academic_batch
            WHERE academic_batch_id = :academic_batch_id
            LIMIT 1
            """
        ),
        {"academic_batch_id": course["academic_batch_id"]},
    ).mappings().first()

    semesters = db.execute(
        text(
            """
            SELECT semester_id, semester, semester_desc, academic_batch_id
            FROM iems_semester
            WHERE academic_batch_id = :academic_batch_id
              AND semester = :semester
            ORDER BY semester_id DESC
            """
        ),
        {"academic_batch_id": course["academic_batch_id"], "semester": course["semester"]},
    ).mappings().all()

    semester_ids = [row["semester_id"] for row in semesters]

    topics = db.execute(
        text(
            """
            SELECT topic_id, topic_code, topic_title, academic_batch_id, semester_id, course_id
            FROM cudos_topic
            WHERE course_id = :crs_id
            ORDER BY topic_id DESC
            """
        ),
        {"crs_id": crs_id},
    ).mappings().all()

    time_slots = db.execute(
        text(
            """
            SELECT
                tt.time_table_id,
                tt.tt_detail_id,
                tt.crs_id,
                tt.crs_code,
                tt.class_start_time,
                tt.class_end_time,
                td.academic_batch_id,
                td.semester_id,
                td.section_id,
                s.section,
                dm.tt_day_map_id,
                dm.class_date,
                dm.day_id,
                dm.week_day_name,
                dm.allot_by,
                u.username,
                TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS faculty_name
            FROM lms_tt_time_table tt
            JOIN lms_tt_time_table_details td
              ON td.tt_detail_id = tt.tt_detail_id
            LEFT JOIN iems_section s
              ON s.id = td.section_id
            LEFT JOIN lms_tt_time_table_day_mapping dm
              ON dm.time_table_id = tt.time_table_id
            LEFT JOIN iems_users u
              ON u.id = dm.allot_by
            WHERE tt.crs_id = :crs_id
            ORDER BY dm.class_date DESC, tt.class_start_time ASC
            """
        ),
        {"crs_id": crs_id},
    ).mappings().all()

    if semester_ids:
        section_rows = db.execute(
            text(
                """
                SELECT id AS section_id, section, academic_batch_id, semester_id
                FROM iems_section
                WHERE academic_batch_id = :academic_batch_id
                  AND semester_id IN :semester_ids
                ORDER BY id DESC
                """
            ).bindparams(bindparam("semester_ids", expanding=True)),
            {"academic_batch_id": course["academic_batch_id"], "semester_ids": tuple(semester_ids)},
        ).mappings().all()
    else:
        section_rows = []

    return returnSuccess(
        {
            "course": dict(course),
            "academic_batch": None if not batch else dict(batch),
            "semesters": semesters,
            "sections": section_rows,
            "topics": topics,
            "time_slots": time_slots,
        }
    )


# Fetches topics for the selected batch, semester, and course.
@router.get("/meta/topics")
def get_schedule_topics(
    academic_batch_id: int,
    semester_id: int,
    crs_id: int,
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT topic_id, topic_code, topic_title, academic_batch_id, semester_id, course_id
            FROM cudos_topic
            WHERE academic_batch_id = :academic_batch_id
              AND semester_id = :semester_id
              AND course_id = :crs_id
            ORDER BY topic_id DESC
            """
        ),
        {
            "academic_batch_id": academic_batch_id,
            "semester_id": semester_id,
            "crs_id": crs_id,
        },
    ).mappings().all()
    return returnSuccess({"total": len(rows), "items": rows})


# Checks whether the selected schedule timing already has a class booked.
@router.post("/check-duplicate")
def check_schedule_duplicate(payload: ScheduleClassDuplicateRequest, db: Session = Depends(get_db)):
    duplicate = _find_duplicate_schedule(
        db=db,
        academic_batch_id=payload.academic_batch_id,
        semester_id=payload.semester_id,
        section_id=payload.section_id,
        plan_date=payload.plan_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        crs_id=payload.crs_id,
        exclude_lls_id=payload.exclude_lls_id,
    )
    return returnSuccess({"is_duplicate": bool(duplicate), "duplicate": None if not duplicate else dict(duplicate)})


# Creates a scheduled class and stores the matched timetable context when available.
@router.post("/create")
def create_schedule_class(payload: ScheduleClassCreateRequest, db: Session = Depends(get_db)):
    if not _record_exists(db, "iems_academic_batch", "academic_batch_id", payload.academic_batch_id):
        return returnException("Academic batch not found")
    if not _record_exists(db, "iems_semester", "semester_id", payload.semester_id):
        return returnException("Semester not found")
    if not _record_exists(db, "iems_courses", "crs_id", payload.crs_id):
        return returnException("Course not found")
    if not _record_exists(db, "iems_section", "id", payload.section_id):
        return returnException("Section not found")
    if payload.topic_id is not None and not _record_exists(db, "cudos_topic", "topic_id", payload.topic_id):
        return returnException("Topic not found")

    duplicate = _find_duplicate_schedule(
        db=db,
        academic_batch_id=payload.academic_batch_id,
        semester_id=payload.semester_id,
        section_id=payload.section_id,
        plan_date=payload.plan_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        crs_id=payload.crs_id,
    )
    if duplicate:
        return returnException("Duplicate class already scheduled for same timing")

    timetable_context = _resolve_timetable_context(
        db=db,
        academic_batch_id=payload.academic_batch_id,
        semester_id=payload.semester_id,
        crs_id=payload.crs_id,
        section_id=payload.section_id,
        plan_date=payload.plan_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )

    try:
        result = db.execute(
            text(
                """
                INSERT INTO lms_lesson_schedule
                (
                    tt_day_map_id, time_table_id, tt_detail_id,
                    portion_ref, portion_per_hour,
                    academic_batch_id, semester_id, crs_id, topic_id, section_id,
                    plan_date, video_link, start_time, end_time,
                    status, created_by, created_date
                )
                VALUES
                (
                    :tt_day_map_id, :time_table_id, :tt_detail_id,
                    :portion_ref, :portion_per_hour,
                    :academic_batch_id, :semester_id, :crs_id, :topic_id, :section_id,
                    :plan_date, :video_link, :start_time, :end_time,
                    :status, :created_by, :created_date
                )
                """
            ),
            {
                "tt_day_map_id": timetable_context.get("tt_day_map_id"),
                "time_table_id": timetable_context.get("time_table_id"),
                "tt_detail_id": timetable_context.get("tt_detail_id"),
                "portion_ref": payload.portion_ref,
                "portion_per_hour": payload.portion_per_hour,
                "academic_batch_id": payload.academic_batch_id,
                "semester_id": payload.semester_id,
                "crs_id": payload.crs_id,
                "topic_id": payload.topic_id,
                "section_id": payload.section_id,
                "plan_date": payload.plan_date,
                "video_link": payload.video_link,
                "start_time": payload.start_time,
                "end_time": payload.end_time,
                "status": payload.status,
                "created_by": payload.created_by,
                "created_date": datetime.now(),
            },
        )
        db.commit()
        return returnSuccess(
            {
                "lls_id": result.lastrowid,
                "tt_day_map_id": timetable_context.get("tt_day_map_id"),
                "time_table_id": timetable_context.get("time_table_id"),
                "tt_detail_id": timetable_context.get("tt_detail_id"),
            },
            "Class scheduled successfully",
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to schedule class: {str(exc)}")


# Fetches scheduled classes with course, section, topic, weekday, and faculty context.
@router.get("/list")
def get_schedule_class_list(
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    crs_id: Optional[int] = Query(default=None),
    section_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = """
        SELECT
            ls.lls_id,
            ls.academic_batch_id,
            ls.semester_id,
            ls.crs_id,
            ls.topic_id,
            ls.section_id,
            ls.plan_date,
            ls.start_time,
            ls.end_time,
            ls.portion_ref,
            ls.portion_per_hour,
            ls.video_link,
            ls.status,
            ls.created_by,
            ls.created_date,
            c.crs_code,
            c.crs_title,
            s.section,
            t.topic_code,
            t.topic_title,
            wd.week_day_name,
            dm.allot_by,
            u.username,
            TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS faculty_name
        FROM lms_lesson_schedule ls
        LEFT JOIN iems_courses c
          ON c.crs_id = ls.crs_id
        LEFT JOIN iems_section s
          ON s.id = ls.section_id
        LEFT JOIN cudos_topic t
          ON t.topic_id = ls.topic_id
        LEFT JOIN lms_tt_time_table_day_mapping dm
          ON dm.tt_day_map_id = ls.tt_day_map_id
        LEFT JOIN lms_tt_weekdays wd
          ON wd.day_id = dm.day_id
        LEFT JOIN iems_users u
          ON u.id = dm.allot_by
        WHERE 1 = 1
    """
    params = {}
    if academic_batch_id is not None:
        query += " AND ls.academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    if semester_id is not None:
        query += " AND ls.semester_id = :semester_id"
        params["semester_id"] = semester_id
    if crs_id is not None:
        query += " AND ls.crs_id = :crs_id"
        params["crs_id"] = crs_id
    if section_id is not None:
        query += " AND ls.section_id = :section_id"
        params["section_id"] = section_id
    query += " ORDER BY ls.plan_date DESC, ls.start_time ASC"
    rows = db.execute(text(query), params).mappings().all()
    return returnSuccess({"total": len(rows), "items": rows})


# Fetches a single scheduled class by id.
@router.get("/{lls_id}")
def get_schedule_class_details(lls_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT
                ls.*,
                c.crs_code,
                c.crs_title,
                s.section,
                t.topic_code,
                t.topic_title,
                wd.week_day_name,
                dm.allot_by,
                u.username,
                TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS faculty_name
            FROM lms_lesson_schedule ls
            LEFT JOIN iems_courses c
              ON c.crs_id = ls.crs_id
            LEFT JOIN iems_section s
              ON s.id = ls.section_id
            LEFT JOIN cudos_topic t
              ON t.topic_id = ls.topic_id
            LEFT JOIN lms_tt_time_table_day_mapping dm
              ON dm.tt_day_map_id = ls.tt_day_map_id
            LEFT JOIN lms_tt_weekdays wd
              ON wd.day_id = dm.day_id
            LEFT JOIN iems_users u
              ON u.id = dm.allot_by
            WHERE ls.lls_id = :lls_id
            LIMIT 1
            """
        ),
        {"lls_id": lls_id},
    ).mappings().first()
    if not row:
        return returnException("Scheduled class not found")
    return returnSuccess(dict(row))


# Updates a scheduled class after checking for duplicate timing collisions.
@router.put("/{lls_id}")
def update_schedule_class(lls_id: int, payload: ScheduleClassUpdateRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        text("SELECT * FROM lms_lesson_schedule WHERE lls_id = :lls_id LIMIT 1"),
        {"lls_id": lls_id},
    ).mappings().first()
    if not existing:
        return returnException("Scheduled class not found")

    current = dict(existing)
    academic_batch_id = payload.academic_batch_id if payload.academic_batch_id is not None else current["academic_batch_id"]
    semester_id = payload.semester_id if payload.semester_id is not None else current["semester_id"]
    crs_id = payload.crs_id if payload.crs_id is not None else current["crs_id"]
    section_id = payload.section_id if payload.section_id is not None else current["section_id"]
    plan_date = payload.plan_date if payload.plan_date is not None else current["plan_date"]
    start_time = payload.start_time if payload.start_time is not None else current["start_time"]
    end_time = payload.end_time if payload.end_time is not None else current["end_time"]

    if not _record_exists(db, "iems_academic_batch", "academic_batch_id", academic_batch_id):
        return returnException("Academic batch not found")
    if not _record_exists(db, "iems_semester", "semester_id", semester_id):
        return returnException("Semester not found")
    if not _record_exists(db, "iems_courses", "crs_id", crs_id):
        return returnException("Course not found")
    if not _record_exists(db, "iems_section", "id", section_id):
        return returnException("Section not found")
    topic_id = payload.topic_id if payload.topic_id is not None else current["topic_id"]
    if topic_id is not None and not _record_exists(db, "cudos_topic", "topic_id", topic_id):
        return returnException("Topic not found")

    duplicate = _find_duplicate_schedule(
        db=db,
        academic_batch_id=academic_batch_id,
        semester_id=semester_id,
        section_id=section_id,
        plan_date=plan_date,
        start_time=start_time,
        end_time=end_time,
        crs_id=crs_id,
        exclude_lls_id=lls_id,
    )
    if duplicate:
        return returnException("Duplicate class already scheduled for same timing")

    timetable_context = _resolve_timetable_context(
        db=db,
        academic_batch_id=academic_batch_id,
        semester_id=semester_id,
        crs_id=crs_id,
        section_id=section_id,
        plan_date=plan_date,
        start_time=start_time,
        end_time=end_time,
    )

    try:
        db.execute(
            text(
                """
                UPDATE lms_lesson_schedule
                SET academic_batch_id = :academic_batch_id,
                    semester_id = :semester_id,
                    crs_id = :crs_id,
                    section_id = :section_id,
                    topic_id = :topic_id,
                    plan_date = :plan_date,
                    start_time = :start_time,
                    end_time = :end_time,
                    portion_ref = :portion_ref,
                    portion_per_hour = :portion_per_hour,
                    video_link = :video_link,
                    status = :status,
                    tt_day_map_id = :tt_day_map_id,
                    time_table_id = :time_table_id,
                    tt_detail_id = :tt_detail_id,
                    modified_by = :modified_by,
                    modified_date = :modified_date
                WHERE lls_id = :lls_id
                """
            ),
            {
                "academic_batch_id": academic_batch_id,
                "semester_id": semester_id,
                "crs_id": crs_id,
                "section_id": section_id,
                "topic_id": topic_id,
                "plan_date": plan_date,
                "start_time": start_time,
                "end_time": end_time,
                "portion_ref": payload.portion_ref if payload.portion_ref is not None else current["portion_ref"],
                "portion_per_hour": payload.portion_per_hour if payload.portion_per_hour is not None else current["portion_per_hour"],
                "video_link": payload.video_link if payload.video_link is not None else current["video_link"],
                "status": payload.status if payload.status is not None else current["status"],
                "tt_day_map_id": timetable_context.get("tt_day_map_id"),
                "time_table_id": timetable_context.get("time_table_id"),
                "tt_detail_id": timetable_context.get("tt_detail_id"),
                "modified_by": payload.modified_by,
                "modified_date": datetime.now(),
                "lls_id": lls_id,
            },
        )
        db.commit()
        return returnSuccess({"lls_id": lls_id}, "Scheduled class updated successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to update scheduled class: {str(exc)}")


# Deletes a scheduled class by id.
@router.delete("/{lls_id}")
def delete_schedule_class(lls_id: int, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT lls_id FROM lms_lesson_schedule WHERE lls_id = :lls_id"),
        {"lls_id": lls_id},
    ).scalar()
    if not exists:
        return returnException("Scheduled class not found")

    try:
        db.execute(text("DELETE FROM lms_lesson_schedule WHERE lls_id = :lls_id"), {"lls_id": lls_id})
        db.commit()
        return returnSuccess({"lls_id": lls_id}, "Scheduled class deleted successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete scheduled class: {str(exc)}")
