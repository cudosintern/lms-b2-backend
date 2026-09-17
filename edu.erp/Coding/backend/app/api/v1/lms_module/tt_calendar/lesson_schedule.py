
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

router = APIRouter()


class LessonScheduleDetailsRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    crs_id: int
    section_id: int
    plan_date: date
    topic_id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    lls_id: Optional[int] = None
    tt_day_map_id: Optional[int] = None

    @field_validator("plan_date", mode="before")
    @classmethod
    def parse_plan_date(cls, value):
        if isinstance(value, date):
            return value
        value = str(value).strip()
        for date_format in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value[:10], date_format).date()
            except ValueError:
                continue
        raise ValueError("plan_date must use YYYY-MM-DD or DD-MM-YYYY")


def _table_columns(db: Session, table_name: str) -> set[str]:
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    return {row[0] for row in rows}


def _time_text(value) -> Optional[str]:
    return None if value is None else str(value)[:8]


@router.post("/lesson-schedule-details")
def get_lesson_schedule_details(
    request: LessonScheduleDetailsRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all data needed by the Add Lesson Schedule modal."""

    try:
        user_id = current_user.get("user_id") or current_user.get("id") or 0
        params = {
            "academic_batch_id": request.academic_batch_id,
            "semester_id": request.semester_id,
            "crs_id": request.crs_id,
            "section_id": request.section_id,
            "plan_date": request.plan_date,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "lls_id": request.lls_id,
            "tt_day_map_id": request.tt_day_map_id,
            "user_id": user_id,
        }

        course = db.execute(
            text(
                """
                SELECT crs_id, crs_code, crs_title
                FROM iems_courses
                WHERE crs_id = :crs_id
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()
        if not course:
            return returnException("Course not found")

        section = db.execute(
            text(
                """
                SELECT mt_details_id AS section_id, mt_details_name AS section_name, parent_id
                FROM cudos_master_type_details
                WHERE mt_details_id = :section_id
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()

        topics = db.execute(
            text(
                """
                SELECT DISTINCT t.topic_id, t.topic_code, t.topic_title,
                       t.topic_content, t.topic_hrs, t.num_of_sessions,
                       mit.inst_map_id AS mapping_id, mit.instructor_id,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM lms_ls_topic_map ltm
                           WHERE ltm.lls_id = :selected_lls_id
                             AND ltm.topic_id = t.topic_id
                       ) THEN 1 ELSE 0 END AS is_selected
                FROM lms_map_instructor_topic mit
                JOIN cudos_topic t ON t.topic_id = mit.topic_id
                WHERE mit.academic_batch_id = :academic_batch_id
                  AND mit.semester_id = :semester_id
                  AND mit.crs_id = :crs_id
                  AND mit.section_id = :section_id
                ORDER BY t.topic_id DESC
                """
            ),
            {**params, "selected_lls_id": request.lls_id or 0},
        ).mappings().all()

        lls_columns = _table_columns(db, "lms_lesson_schedule")
        optional_columns = [
            name for name in (
                "topic_id", "portion_ref", "portion_per_hour", "video_link",
                "tt_day_map_id", "time_table_id", "tt_detail_id",
            ) if name in lls_columns
        ]
        select_columns = ", ".join(["lls_id", "status"] + optional_columns)
        lesson_conditions = [
            "academic_batch_id = :academic_batch_id",
            "semester_id = :semester_id",
            "crs_id = :crs_id",
            "section_id = :section_id",
            "plan_date = :plan_date",
        ]
        if request.lls_id:
            lesson_conditions = ["lls_id = :lls_id"]
        elif request.start_time:
            lesson_conditions.append("LEFT(start_time, 5) = LEFT(:start_time, 5)")
        if request.end_time and not request.lls_id:
            lesson_conditions.append("LEFT(end_time, 5) = LEFT(:end_time, 5)")

        lesson = db.execute(
            text(
                f"SELECT {select_columns} FROM lms_lesson_schedule "
                f"WHERE {' AND '.join(lesson_conditions)} ORDER BY lls_id DESC LIMIT 1"
            ),
            params,
        ).mappings().first()
        lesson_data = dict(lesson) if lesson else {}

        # selected_topic_id = lesson_data.get("topic_id")

        selected_topic_id = request.topic_id or lesson_data.get("topic_id")
        portions = db.execute(
            text(
                """
                SELECT DISTINCT p.mtp_id AS portion_id, p.topic_id, p.lesson_schedule_id,
                       p.portion_ref, p.portion_per_hour, p.planned_date,
                       p.delivery_date, p.start_time, p.end_time, p.status,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM lms_ls_lesson_schedule_map lm
                           WHERE lm.lls_id = :selected_lls_id
                             AND lm.mtp_id = p.mtp_id
                       ) THEN 1 ELSE 0 END AS is_selected
                FROM lms_map_portion_ls p
                JOIN lms_map_instructor_topic mit
                  ON mit.topic_id = p.topic_id
                 AND mit.academic_batch_id = :academic_batch_id
                 AND mit.semester_id = :semester_id
                 AND mit.crs_id = :crs_id
                 AND mit.section_id = :section_id
                WHERE p.section_id = :section_id
                  AND (:topic_id IS NULL OR p.topic_id = :topic_id)
                ORDER BY p.topic_id, p.planned_date, p.mtp_id
                """
            ),
            {**params, "topic_id": selected_topic_id,
             "selected_lls_id": lesson_data.get("lls_id") or 0},
        ).mappings().all()

        delivery_methods = []
        if selected_topic_id:
            delivery_methods = db.execute(
                text(
                    """
                    SELECT DISTINCT dm.delivery_mtd_id, dm.delivery_mtd_name,
                           dm.delivery_mtd_desc
                    FROM cudos_topic_delivery_method tdm
                    JOIN cudos_delivery_method dm
                      ON dm.delivery_mtd_id = tdm.delivery_mtd_id
                    WHERE tdm.topic_id = :topic_id
                    ORDER BY dm.delivery_mtd_name
                    """
                ),
                {"topic_id": selected_topic_id},
            ).mappings().all()

        bloom_levels = db.execute(
            text(
                """
                SELECT bloom_id, bld_id, level, learning, description
                FROM cudos_bloom_level
                ORDER BY bld_id, bloom_id
                """
            )
        ).mappings().all()

        course_list = db.execute(
            text(
                """
                SELECT DISTINCT c.crs_id, c.crs_code, c.crs_title
                FROM cudos_map_courseto_course_instructor m
                JOIN iems_courses c ON c.crs_id = m.crs_id
                WHERE m.academic_batch_id = :academic_batch_id
                  AND m.semester_id = :semester_id
                  AND m.section_id = :section_id
                ORDER BY c.crs_code
                """
            ),
            params,
        ).mappings().all()

        students = db.execute(
            text(
                """
                SELECT DISTINCT s.student_id, s.usno, s.regno, s.roll_number,
                       s.name, s.first_name, s.middle_name, s.last_name,
                       s.academic_batch_id, s.current_semester, s.section,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM lms_ls_student_map sm
                           WHERE sm.lls_id = :selected_lls_id
                             AND sm.ssd_id = s.student_id
                       ) THEN 1 ELSE 0 END AS is_selected,
                       TRIM(
                           CONCAT_WS(' ', NULLIF(s.first_name, ''),
                                          NULLIF(s.middle_name, ''),
                                          NULLIF(s.last_name, ''))
                       ) AS student_name
                FROM iems_students s
                JOIN cudos_map_courseto_student mcs
                  ON mcs.student_id = s.student_id
                WHERE mcs.academic_batch_id = :academic_batch_id
                  AND mcs.semester_id = :semester_id
                  AND mcs.crs_id = :crs_id
                  AND mcs.status = 1
                  AND mcs.crs_reg_flag = 1
                  AND s.status = 1
                ORDER BY s.usno, s.student_id
                """
            ),
            {**params, "selected_lls_id": lesson_data.get("lls_id") or 0},
        ).mappings().all()

        notifications = db.execute(
            text(
                """
                SELECT lmsn_id AS notification_id, notify_description AS description,
                       delivery_date, delivery_time
                FROM lms_notifications
                WHERE created_by = :user_id
                  AND display_to_timetable = 1
                  AND delivery_date = :plan_date
                ORDER BY lmsn_id DESC
                """
            ),
            params,
        ).mappings().all()

        data = {
            "course": dict(course),
            "section": None if not section else dict(section),
            "course_list": [dict(row) for row in course_list],
            "topic_list": [dict(row) for row in topics],
            "portion_list": [
                {**dict(row), "start_time": _time_text(row["start_time"]), "end_time": _time_text(row["end_time"])}
                for row in portions
            ],
            "delivery_method_list": [dict(row) for row in delivery_methods],
            "bloom_level_list": [dict(row) for row in bloom_levels],
            "student_list": [dict(row) for row in students],
            "student_count": len(students),
            "lesson_schedule": lesson_data or None,
            "notification_count": len(notifications),
            "notifications": [dict(row) for row in notifications],
            "video_link": lesson_data.get("video_link") or "",
            "status": lesson_data.get("status", 0),
            "data_status": 1 if lesson_data else 0,
            "delete_schedule_class": bool(lesson_data),
            "delete_comments_class": False,
            "lms_topic_import_type_flag": 1,
        }
        return returnSuccess(data)

    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to load lesson schedule details: {str(exc)}")

class ExtraClassRequest(BaseModel):
    academic_batch_id: int
    semester_id: int
    crs_id: int
    section_id: int
    extra_class_date: date
    start_time: str
    end_time: str
    tt_detail_id: Optional[int] = None
    time_table_id: Optional[int] = None
    tt_day_map_id: Optional[int] = None
    lls_id: Optional[int] = None

    @field_validator("extra_class_date", mode="before")
    @classmethod
    def parse_class_date(cls, value):
        if isinstance(value, date):
            return value
        for date_format in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(value)[:10], date_format).date()
            except ValueError:
                continue
        raise ValueError("extra_class_date must use YYYY-MM-DD or DD-MM-YYYY")

    @model_validator(mode="after")
    def validate_times(self):
        try:
            start = datetime.strptime(self.start_time[:5], "%H:%M").time()
            end = datetime.strptime(self.end_time[:5], "%H:%M").time()
        except ValueError as exc:
            raise ValueError("start_time and end_time must use HH:MM") from exc
        if start >= end:
            raise ValueError("end_time must be later than start_time")
        return self


@router.post("/extra-class")
def save_extra_class(
    request: ExtraClassRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update an extra class after checking date/time overlap."""

    try:
        user_id = current_user.get("user_id") or current_user.get("id") or 0
        class_date_db = request.extra_class_date.strftime("%d-%m-%Y")
        weekday_name = request.extra_class_date.strftime("%A")
        start_time = request.start_time[:5]
        end_time = request.end_time[:5]
        params = {
            "academic_batch_id": request.academic_batch_id,
            "semester_id": request.semester_id,
            "crs_id": request.crs_id,
            "section_id": request.section_id,
            "class_date": request.extra_class_date,
            "start_time": start_time,
            "end_time": end_time,
            "time_table_id": request.time_table_id,
        }

        overlap = db.execute(
            text(
                """
                SELECT tt.time_table_id, tt.crs_id, tt.crs_code,
                       c.crs_title, tt.week_day_name,
                       tt.class_start_time, tt.class_end_time
                FROM lms_tt_time_table_day_mapping dm
                JOIN lms_tt_time_table tt ON tt.time_table_id = dm.time_table_id
                JOIN lms_tt_time_table_details td ON td.tt_detail_id = tt.tt_detail_id
                LEFT JOIN iems_courses c ON c.crs_id = tt.crs_id
                WHERE td.academic_batch_id = :academic_batch_id
                  AND td.semester_id = :semester_id
                  AND td.section_id = :section_id
                  AND tt.crs_id = :crs_id
                  AND COALESCE(
                        STR_TO_DATE(dm.class_date, '%d-%m-%Y'),
                        STR_TO_DATE(dm.class_date, '%Y-%m-%d')
                      ) = :class_date
                  AND (:time_table_id IS NULL OR tt.time_table_id <> :time_table_id)
                  AND TIME(tt.class_start_time) < TIME(:end_time)
                  AND TIME(tt.class_end_time) > TIME(:start_time)
                ORDER BY tt.class_start_time
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()

        if overlap:
            return returnException(
                "Class overlapped on "
                f"{overlap['week_day_name']} with course - "
                f"{overlap['crs_code']} {overlap['crs_title'] or ''} at "
                f"{overlap['class_start_time']}-{overlap['class_end_time']}."
            )

        course = db.execute(
            text("SELECT crs_id, crs_code FROM iems_courses WHERE crs_id = :crs_id LIMIT 1"),
            params,
        ).mappings().first()
        if not course:
            return returnException("Course not found")

        day_id = db.execute(
            text("SELECT day_id FROM lms_tt_weekdays WHERE week_day_name = :weekday LIMIT 1"),
            {"weekday": weekday_name},
        ).scalar()
        if day_id is None:
            return returnException(f"Weekday configuration not found for {weekday_name}")

        tt_detail_id = request.tt_detail_id
        if not tt_detail_id:
            tt_detail_id = db.execute(
                text(
                    """
                    SELECT tt_detail_id
                    FROM lms_tt_time_table_details
                    WHERE academic_batch_id = :academic_batch_id
                      AND semester_id = :semester_id
                      AND section_id = :section_id
                    ORDER BY tt_detail_id DESC
                    LIMIT 1
                    """
                ),
                params,
            ).scalar()
        if not tt_detail_id:
            return returnException("Timetable details not found for the selected filters")

        now = datetime.now()
        if request.time_table_id:
            db.execute(
                text(
                    """
                    UPDATE lms_tt_time_table
                    SET day_id=:day_id, week_day_name=:weekday,
                        class_start_time=:start_time, class_end_time=:end_time,
                        modified_by=:user_id, modified_date=:now
                    WHERE time_table_id=:time_table_id
                    """
                ),
                {**params, "day_id": day_id, "weekday": weekday_name, "user_id": user_id, "now": now},
            )
            if not request.tt_day_map_id:
                return returnException("tt_day_map_id is required while updating an extra class")
            db.execute(
                text(
                    """
                    UPDATE lms_tt_time_table_day_mapping
                    SET day_id=:day_id, week_day_name=:weekday, class_date=:class_date_db,
                        modified_by=:user_id, modified_date=:now
                    WHERE tt_day_map_id=:tt_day_map_id
                    """
                ),
                {"day_id": day_id, "weekday": weekday_name, "class_date_db": class_date_db,
                 "user_id": user_id, "now": now, "tt_day_map_id": request.tt_day_map_id},
            )
            if request.lls_id:
                db.execute(
                    text(
                        """
                        UPDATE lms_lesson_schedule
                        SET plan_date=:plan_date, start_time=:start_time, end_time=:end_time,
                            modified_by=:user_id, modified_date=:now
                        WHERE lls_id=:lls_id
                        """
                    ),
                    {"plan_date": request.extra_class_date, "start_time": start_time, "end_time": end_time,
                     "user_id": user_id, "now": now, "lls_id": request.lls_id},
                )
            message = "Extra class updated successfully."
            time_table_id = request.time_table_id
            tt_day_map_id = request.tt_day_map_id
        else:
            result = db.execute(
                text(
                    """
                    INSERT INTO lms_tt_time_table
                    (tt_detail_id, day_id, week_day_name, crs_id, crs_code,
                     class_start_time, class_end_time, extra_class_flag,
                     extra_class_created, created_by, modified_by, created_date, modified_date)
                    VALUES
                    (:tt_detail_id, :day_id, :weekday, :crs_id, :crs_code,
                     :start_time, :end_time, 1, :user_id, :user_id, :user_id, :now, :now)
                    """
                ),
                {**params, "tt_detail_id": tt_detail_id, "day_id": day_id, "weekday": weekday_name,
                 "crs_code": course["crs_code"], "user_id": user_id, "now": now},
            )
            time_table_id = result.lastrowid

            parent_id = db.execute(
                text("SELECT parent_id FROM cudos_master_type_details WHERE mt_details_id=:section_id LIMIT 1"),
                params,
            ).scalar()
            if parent_id:
                db.execute(
                    text(
                        """
                        INSERT INTO lms_tt_time_table_batch_map
                        (time_table_id, tt_detail_id, batch_id, crs_id, created_by, created_date)
                        VALUES (:time_table_id, :tt_detail_id, :section_id, :crs_id, :user_id, :now)
                        """
                    ),
                    {**params, "time_table_id": time_table_id, "tt_detail_id": tt_detail_id,
                     "user_id": user_id, "now": now},
                )

            mapping = db.execute(
                text(
                    """
                    INSERT INTO lms_tt_time_table_day_mapping
                    (time_table_id, tt_detail_id, day_id, week_day_name, class_date,
                     allot_crs_id, allot_by, extra_class_flag, extra_class_created,
                     created_by, modified_by, created_date, modified_date)
                    VALUES
                    (:time_table_id, :tt_detail_id, :day_id, :weekday, :class_date_db,
                     :crs_id, :user_id, 1, :user_id, :user_id, :user_id, :now, :now)
                    """
                ),
                {**params, "time_table_id": time_table_id, "tt_detail_id": tt_detail_id,
                 "day_id": day_id, "weekday": weekday_name, "class_date_db": class_date_db,
                 "user_id": user_id, "now": now},
            )
            tt_day_map_id = mapping.lastrowid
            message = "Extra class added successfully."

        db.commit()
        return returnSuccess(
            {"time_table_id": time_table_id, "tt_day_map_id": tt_day_map_id,
             "tt_detail_id": tt_detail_id},
            message,
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to save extra class: {str(exc)}")
