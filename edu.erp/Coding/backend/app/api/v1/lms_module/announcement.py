from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, bindparam
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...utils.http_return_helper import returnSuccess, returnException
from ...db.models import (
    Announcement,
    StudentNotificationMap,
    IEMSDepartment,
    IEMProgram,
    IEMSAcademicBatch,
)

router = APIRouter(prefix="/announcements", tags=["Announcements"])


# Validates and carries input data for creating a send announcement.
class SendAnnouncementCreateRequest(BaseModel):
    notify_description: str = Field(..., min_length=1)
    created_by: int
    target_user_type: Literal["faculty", "student", "parent"]
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    delivery_hide_date: Optional[str] = None
    delivery_hide_time: Optional[str] = None
    display_to_timetable: int = 0
    dept_id: Optional[int] = None
    pgm_id: Optional[int] = None
    academic_batch_id: Optional[int] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    recipient_ids: list[int] = Field(default_factory=list)
    recipient_usns: list[str] = Field(default_factory=list)


# Validates and carries input data for updating a sent announcement.
class SendAnnouncementUpdateRequest(BaseModel):
    notify_description: Optional[str] = None
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    delivery_hide_date: Optional[str] = None
    delivery_hide_time: Optional[str] = None
    display_to_timetable: Optional[int] = None
    modified_by: int


# Normalizes incoming user type values for consistent processing.
def _normalize_user_type(value: str) -> str:
    return (value or "").strip().lower()


# Maps user type to notification detail flags.
def _resolve_flags(user_type: str) -> tuple[int, int, int]:
    if user_type == "faculty":
        return 1, 0, 0
    if user_type == "student":
        return 0, 1, 0
    if user_type == "parent":
        return 0, 0, 1
    raise ValueError("Invalid target_user_type")


# Builds recipient query SQL and params based on selected user type and filters.
def _recipient_scope_sql(
    user_type: str,
    dept_id: Optional[int],
    pgm_id: Optional[int],
    academic_batch_id: Optional[int],
    semester: Optional[int],
    section: Optional[str],
) -> tuple[str, dict]:
    params: dict = {}

    if user_type == "faculty":
        sql = """
            SELECT
                u.id AS recipient_id,
                u.username,
                TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS full_name,
                u.user_dept_id AS dept_id
            FROM iems_users u
            WHERE u.status = 1
        """
        if dept_id is not None:
            sql += " AND u.user_dept_id = :dept_id"
            params["dept_id"] = dept_id
        sql += " ORDER BY u.id DESC"
        return sql, params

    if user_type in {"student", "parent"}:
        sql = """
            SELECT
                s.student_id AS recipient_id,
                s.usno,
                s.ref_usno,
                TRIM(COALESCE(s.name, CONCAT(COALESCE(s.first_name, ''), ' ', COALESCE(s.last_name, '')))) AS full_name,
                s.department_id,
                s.program_id,
                s.academic_batch_id,
                s.current_semester,
                s.section
            FROM iems_students s
            WHERE s.status = 1 AND IFNULL(s.delete_status, 0) = 0
        """
        if dept_id is not None:
            sql += " AND s.department_id = :dept_id"
            params["dept_id"] = dept_id
        if pgm_id is not None:
            sql += " AND s.program_id = :pgm_id"
            params["pgm_id"] = pgm_id
        if academic_batch_id is not None:
            sql += " AND s.academic_batch_id = :academic_batch_id"
            params["academic_batch_id"] = academic_batch_id
        if semester is not None:
            sql += " AND s.current_semester = :semester"
            params["semester"] = semester
        if section is not None and section.strip():
            sql += " AND s.section = :section"
            params["section"] = section.strip()

        sql += " ORDER BY s.student_id DESC"
        return sql, params

    raise ValueError("Invalid user_type")


# Returns static user types for the send announcement UI dropdown.
@router.get("/send/user-types")
def get_send_user_types():
    return returnSuccess(
        [
            {"key": "faculty", "label": "Faculty"},
            {"key": "student", "label": "Student"},
            {"key": "parent", "label": "Parent"},
        ]
    )


# Fetches active departments for send announcement filtering.
@router.get("/send/departments")
def get_send_departments(db: Session = Depends(get_db)):
    departments = (
        db.query(IEMSDepartment.dept_id, IEMSDepartment.dept_name)
        .filter(IEMSDepartment.status == 1)
        .order_by(IEMSDepartment.dept_name.asc())
        .all()
    )
    data = [{"dept_id": d.dept_id, "dept_name": d.dept_name} for d in departments]
    return returnSuccess(data)


# Fetches active programs with optional department filtering.
@router.get("/send/programs")
def get_send_programs(dept_id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    query = (
        db.query(IEMProgram.pgm_id, IEMProgram.pgm_title, IEMProgram.dept_id)
        .filter(IEMProgram.status == 1)
    )
    if dept_id is not None:
        query = query.filter(IEMProgram.dept_id == dept_id)
    programs = query.order_by(IEMProgram.pgm_title.asc()).all()
    data = [
        {"pgm_id": p.pgm_id, "pgm_title": p.pgm_title, "dept_id": p.dept_id}
        for p in programs
    ]
    return returnSuccess(data)


# Fetches academic batch (curriculum) options with optional department and program filtering.
@router.get("/send/curriculums")
def get_send_curriculums(
    dept_id: Optional[int] = Query(default=None),
    pgm_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        IEMSAcademicBatch.academic_batch_id,
        IEMSAcademicBatch.academic_batch_desc,
        IEMSAcademicBatch.dept_id,
        IEMSAcademicBatch.pgm_id,
    ).filter(IEMSAcademicBatch.status == 1)
    if dept_id is not None:
        query = query.filter(IEMSAcademicBatch.dept_id == dept_id)
    if pgm_id is not None:
        query = query.filter(IEMSAcademicBatch.pgm_id == pgm_id)

    rows = query.order_by(IEMSAcademicBatch.academic_batch_id.desc()).all()
    data = [
        {
            "crclm_id": row.academic_batch_id,
            "start_year": row.academic_batch_desc,
            "dept_id": row.dept_id,
            "pgm_id": row.pgm_id,
        }
        for row in rows
    ]
    return returnSuccess(data)


# Fetches recipient list by user type and academic filters.
@router.get("/send/recipients")
def get_send_recipients(
    user_type: str,
    dept_id: Optional[int] = Query(default=None),
    pgm_id: Optional[int] = Query(default=None),
    academic_batch_id: Optional[int] = Query(default=None),
    semester: Optional[int] = Query(default=None),
    section: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    normalized_user_type = _normalize_user_type(user_type)
    if normalized_user_type not in {"faculty", "student", "parent"}:
        return returnException("Invalid user_type. Use faculty/student/parent.")

    sql, params = _recipient_scope_sql(
        normalized_user_type,
        dept_id,
        pgm_id,
        academic_batch_id,
        semester,
        section,
    )
    rows = db.execute(text(sql), params).mappings().all()

    if normalized_user_type == "faculty":
        data = [
            {
                "recipient_id": row["recipient_id"],
                "username": row["username"],
                "full_name": row["full_name"].strip(),
                "dept_id": row["dept_id"],
            }
            for row in rows
        ]
    elif normalized_user_type == "student":
        data = [
            {
                "recipient_id": row["recipient_id"],
                "usn": row["usno"],
                "full_name": (row["full_name"] or "").strip(),
                "dept_id": row["department_id"],
                "pgm_id": row["program_id"],
                "academic_batch_id": row["academic_batch_id"],
                "semester": row["current_semester"],
                "section": row["section"],
            }
            for row in rows
        ]
    else:
        data = [
            {
                "recipient_id": row["recipient_id"],
                "parent_usn": row["ref_usno"] or row["usno"],
                "parent_name": f"{(row['full_name'] or '').strip()} Parent".strip(),
                "student_usn": row["usno"],
                "dept_id": row["department_id"],
                "pgm_id": row["program_id"],
                "academic_batch_id": row["academic_batch_id"],
                "semester": row["current_semester"],
                "section": row["section"],
            }
            for row in rows
        ]

    return returnSuccess({"total": len(data), "items": data})


# Creates a new announcement and maps it to selected recipients.
@router.post("/send/create")
def create_send_announcement(payload: SendAnnouncementCreateRequest, db: Session = Depends(get_db)):
    normalized_user_type = _normalize_user_type(payload.target_user_type)
    if normalized_user_type not in {"faculty", "student", "parent"}:
        return returnException("Invalid target_user_type. Use faculty/student/parent.")

    if not payload.notify_description.strip():
        return returnException("notify_description is required")

    faculty_flag, student_flag, parent_flag = _resolve_flags(normalized_user_type)

    # Creates the main announcement header record.
    try:
        announcement = Announcement(
            delivery_date=payload.delivery_date,
            delivery_time=payload.delivery_time,
            delivery_hide_date=payload.delivery_hide_date,
            delivery_hide_time=payload.delivery_hide_time,
            notify_description=payload.notify_description.strip(),
            display_to_timetable=payload.display_to_timetable,
            created_by=payload.created_by,
            created_at=datetime.now(timezone.utc),
        )
        db.add(announcement)
        db.flush()

        # Saves the targeting metadata for this announcement.
        detail_result = db.execute(
            text(
                """
                INSERT INTO lms_notifications_details
                (lmsn_id, dept_id, pgm_id, academic_batch_id, faculty_flag, student_flag, parent_flag, created_by)
                VALUES
                (:lmsn_id, :dept_id, :pgm_id, :academic_batch_id, :faculty_flag, :student_flag, :parent_flag, :created_by)
                """
            ),
            {
                "lmsn_id": announcement.lmsn_id,
                "dept_id": payload.dept_id,
                "pgm_id": payload.pgm_id,
                "academic_batch_id": payload.academic_batch_id,
                "faculty_flag": faculty_flag,
                "student_flag": student_flag,
                "parent_flag": parent_flag,
                "created_by": payload.created_by,
            },
        )
        lmsn_det_id = detail_result.lastrowid

        # Starts recipient insert count tracking for response and validation.
        inserted_recipients = 0

        # Resolves and saves faculty recipients.
        if normalized_user_type == "faculty":
            recipient_ids = payload.recipient_ids
            if not recipient_ids:
                sql, params = _recipient_scope_sql(
                    normalized_user_type,
                    payload.dept_id,
                    payload.pgm_id,
                    payload.academic_batch_id,
                    payload.semester,
                    payload.section,
                )
                recipient_ids = [
                    int(row["recipient_id"])
                    for row in db.execute(text(sql), params).mappings().all()
                ]

            if recipient_ids:
                recipients = db.execute(
                    text(
                        """
                        SELECT id, username
                        FROM iems_users
                        WHERE id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(recipient_ids)},
                ).mappings().all()

                for row in recipients:
                    db.execute(
                        text(
                            """
                            INSERT INTO lms_map_faculty_notifications
                            (lmsn_id, lmsn_det_id, faculty_id, username, notify_seen_flag, created_by)
                            VALUES
                            (:lmsn_id, :lmsn_det_id, :faculty_id, :username, 0, :created_by)
                            """
                        ),
                        {
                            "lmsn_id": announcement.lmsn_id,
                            "lmsn_det_id": lmsn_det_id,
                            "faculty_id": row["id"],
                            "username": row["username"],
                            "created_by": payload.created_by,
                        },
                    )
                    inserted_recipients += 1

        # Resolves and saves student recipients.
        elif normalized_user_type == "student":
            recipient_ids = payload.recipient_ids
            if not recipient_ids:
                sql, params = _recipient_scope_sql(
                    normalized_user_type,
                    payload.dept_id,
                    payload.pgm_id,
                    payload.academic_batch_id,
                    payload.semester,
                    payload.section,
                )
                recipient_ids = [
                    int(row["recipient_id"])
                    for row in db.execute(text(sql), params).mappings().all()
                ]

            if recipient_ids:
                students = db.execute(
                    text(
                        """
                        SELECT student_id, usno
                        FROM iems_students
                        WHERE student_id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(recipient_ids)},
                ).mappings().all()

                for row in students:
                    db.execute(
                        text(
                            """
                            INSERT INTO lms_map_student_notifications
                            (lmsn_id, lmsn_det_id, ssd_id, student_usn, notify_seen_flag, created_by)
                            VALUES
                            (:lmsn_id, :lmsn_det_id, :ssd_id, :student_usn, 0, :created_by)
                            """
                        ),
                        {
                            "lmsn_id": announcement.lmsn_id,
                            "lmsn_det_id": lmsn_det_id,
                            "ssd_id": row["student_id"],
                            "student_usn": row["usno"],
                            "created_by": payload.created_by,
                        },
                    )
                    inserted_recipients += 1

        # Resolves and saves parent recipients.
        else:
            selected_parent_usns = [u.strip() for u in payload.recipient_usns if u and u.strip()]
            if not selected_parent_usns and payload.recipient_ids:
                rows = db.execute(
                    text(
                        """
                        SELECT student_id, usno, ref_usno,
                               TRIM(COALESCE(name, CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')))) AS full_name
                        FROM iems_students
                        WHERE student_id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(payload.recipient_ids)},
                ).mappings().all()
            else:
                sql, params = _recipient_scope_sql(
                    normalized_user_type,
                    payload.dept_id,
                    payload.pgm_id,
                    payload.academic_batch_id,
                    payload.semester,
                    payload.section,
                )
                rows = db.execute(text(sql), params).mappings().all()
                if selected_parent_usns:
                    rows = [r for r in rows if (r["ref_usno"] or r["usno"]) in selected_parent_usns]

            for row in rows:
                parent_usn = row["ref_usno"] or row["usno"]
                if not parent_usn:
                    continue
                db.execute(
                    text(
                        """
                        INSERT INTO lms_map_parent_notifications
                        (lmsn_id, lmsn_det_id, parent_usn, parent_name, notify_seen_flag, created_by)
                        VALUES
                        (:lmsn_id, :lmsn_det_id, :parent_usn, :parent_name, 0, :created_by)
                        """
                    ),
                    {
                        "lmsn_id": announcement.lmsn_id,
                        "lmsn_det_id": lmsn_det_id,
                        "parent_usn": parent_usn,
                        "parent_name": f"{(row['full_name'] or '').strip()} Parent".strip(),
                        "created_by": payload.created_by,
                    },
                )
                inserted_recipients += 1

        # Prevents saving announcements without any mapped recipients.
        if inserted_recipients == 0:
            db.rollback()
            return returnException("No recipients found for the selected filters/user type")

        db.commit()

        return returnSuccess(
            {
                "lmsn_id": announcement.lmsn_id,
                "lmsn_det_id": lmsn_det_id,
                "target_user_type": normalized_user_type,
                "recipients_saved": inserted_recipients,
            },
            "Announcement created successfully",
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to create announcement: {str(exc)}")


# Fetches paginated list of sent announcements in latest-first order.
@router.get("/send/sent")
def get_sent_announcements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    total = db.query(func.count(Announcement.lmsn_id)).scalar() or 0

    rows = (
        db.query(
            Announcement.lmsn_id,
            Announcement.notify_description,
            Announcement.delivery_date,
            Announcement.delivery_time,
            Announcement.delivery_hide_date,
            Announcement.delivery_hide_time,
            Announcement.display_to_timetable,
            Announcement.created_by,
            Announcement.created_at,
        )
        .order_by(Announcement.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    data = [
        {
            "lmsn_id": r.lmsn_id,
            "notify_description": r.notify_description,
            "delivery_date": r.delivery_date,
            "delivery_time": r.delivery_time,
            "delivery_hide_date": r.delivery_hide_date,
            "delivery_hide_time": r.delivery_hide_time,
            "display_to_timetable": r.display_to_timetable,
            "created_by": r.created_by,
            "created_at": r.created_at,
        }
        for r in rows
    ]

    return returnSuccess(
        {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": data,
        }
    )


# Fetches one sent announcement with detail and recipient counts.
@router.get("/send/sent/{announcement_id}")
def get_sent_announcement_details(announcement_id: int, db: Session = Depends(get_db)):
    announcement = (
        db.query(Announcement)
        .filter(Announcement.lmsn_id == announcement_id)
        .first()
    )
    if not announcement:
        return returnException("Announcement not found")

    details = db.execute(
        text(
            """
            SELECT lmsn_det_id, dept_id, pgm_id, academic_batch_id, faculty_flag, student_flag, parent_flag, created_by, created_at
            FROM lms_notifications_details
            WHERE lmsn_id = :lmsn_id
            ORDER BY lmsn_det_id DESC
            LIMIT 1
            """
        ),
        {"lmsn_id": announcement_id},
    ).mappings().first()

    faculty_count = db.execute(
        text("SELECT COUNT(*) FROM lms_map_faculty_notifications WHERE lmsn_id = :lmsn_id"),
        {"lmsn_id": announcement_id},
    ).scalar() or 0
    student_count = db.execute(
        text("SELECT COUNT(*) FROM lms_map_student_notifications WHERE lmsn_id = :lmsn_id"),
        {"lmsn_id": announcement_id},
    ).scalar() or 0
    parent_count = db.execute(
        text("SELECT COUNT(*) FROM lms_map_parent_notifications WHERE lmsn_id = :lmsn_id"),
        {"lmsn_id": announcement_id},
    ).scalar() or 0

    data = {
        "lmsn_id": announcement.lmsn_id,
        "notify_description": announcement.notify_description,
        "delivery_date": announcement.delivery_date,
        "delivery_time": announcement.delivery_time,
        "delivery_hide_date": announcement.delivery_hide_date,
        "delivery_hide_time": announcement.delivery_hide_time,
        "display_to_timetable": announcement.display_to_timetable,
        "created_by": announcement.created_by,
        "created_at": announcement.created_at,
        "detail": details,
        "recipient_counts": {
            "faculty": int(faculty_count),
            "student": int(student_count),
            "parent": int(parent_count),
        },
    }
    return returnSuccess(data)


# Updates editable fields of an existing sent announcement.
@router.put("/send/sent/{announcement_id}")
def update_sent_announcement(
    announcement_id: int,
    payload: SendAnnouncementUpdateRequest,
    db: Session = Depends(get_db),
):
    announcement = db.query(Announcement).filter(Announcement.lmsn_id == announcement_id).first()
    if not announcement:
        return returnException("Announcement not found")

    if payload.notify_description is not None:
        announcement.notify_description = payload.notify_description.strip()
    if payload.delivery_date is not None:
        announcement.delivery_date = payload.delivery_date
    if payload.delivery_time is not None:
        announcement.delivery_time = payload.delivery_time
    if payload.delivery_hide_date is not None:
        announcement.delivery_hide_date = payload.delivery_hide_date
    if payload.delivery_hide_time is not None:
        announcement.delivery_hide_time = payload.delivery_hide_time
    if payload.display_to_timetable is not None:
        announcement.display_to_timetable = payload.display_to_timetable

    db.commit()

    return returnSuccess({"lmsn_id": announcement_id}, "Announcement updated successfully")


# Deletes a sent announcement and its related recipient mappings.
@router.delete("/send/sent/{announcement_id}")
def delete_sent_announcement(announcement_id: int, db: Session = Depends(get_db)):
    announcement = db.query(Announcement).filter(Announcement.lmsn_id == announcement_id).first()
    if not announcement:
        return returnException("Announcement not found")

    try:
        db.execute(text("DELETE FROM lms_map_faculty_notifications WHERE lmsn_id = :lmsn_id"), {"lmsn_id": announcement_id})
        db.execute(text("DELETE FROM lms_map_student_notifications WHERE lmsn_id = :lmsn_id"), {"lmsn_id": announcement_id})
        db.execute(text("DELETE FROM lms_map_parent_notifications WHERE lmsn_id = :lmsn_id"), {"lmsn_id": announcement_id})
        db.execute(text("DELETE FROM lms_notifications_details WHERE lmsn_id = :lmsn_id"), {"lmsn_id": announcement_id})
        db.delete(announcement)
        db.commit()
        return returnSuccess({"lmsn_id": announcement_id}, "Announcement deleted successfully")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete announcement: {str(exc)}")


# Fetches received announcements for a specific student user (only shows if delivery_date has passed).
@router.get("/received/student/{user_id}")
def get_received_announcements_student(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()  # naive datetime, consistent with DB stored naive datetimes

    rows = db.execute(
        text("""
            SELECT
                a.lmsn_id,
                a.notify_description,
                a.delivery_date,
                a.delivery_time,
                a.created_at,
                a.delivery_hide_date,
                a.delivery_hide_time,
                m.notify_seen_flag,
                m.notify_seenon_datetime
            FROM lms_notifications a
            JOIN lms_map_student_notifications m ON m.lmsn_id = a.lmsn_id
            WHERE m.ssd_id = :user_id
            ORDER BY a.created_at DESC
        """),
        {"user_id": user_id}
    ).mappings().all()

    data = []
    for n in rows:
        # Filter: only show if delivery_date is null (immediate) OR delivery datetime <= now
        delivery_date = n["delivery_date"]
        delivery_time = n["delivery_time"]
        if delivery_date:
            try:
                time_str = str(delivery_time)[:8] if delivery_time else "00:00:00"
                date_str = str(delivery_date)
                scheduled_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                if scheduled_dt > now:
                    continue  # Not yet time to show
            except Exception:
                pass  # Malformed date — show it anyway

        # Filter: hide if past hide date
        hide_date = n["delivery_hide_date"]
        hide_time = n["delivery_hide_time"]
        if hide_date:
            try:
                hide_time_str = str(hide_time)[:8] if hide_time else "23:59:59"
                hide_date_str = str(hide_date)
                hide_dt = datetime.strptime(f"{hide_date_str} {hide_time_str}", "%Y-%m-%d %H:%M:%S")
                if now > hide_dt:
                    continue  # Past the hide date — don't show
            except Exception:
                pass

        data.append({
            "id": n["lmsn_id"],
            "description": n["notify_description"],
            "delivery_date": str(n["delivery_date"]) if n["delivery_date"] else None,
            "delivery_time": str(n["delivery_time"]) if n["delivery_time"] else None,
            "created_at": n["created_at"],
            "seen_flag": n["notify_seen_flag"],
            "seen_on": n["notify_seenon_datetime"],
        })

    return returnSuccess(data)


# Fetches received announcements for a user, combining student and faculty checks since the legacy UI uses one universal endpoint.
@router.get("/received/{user_id}")
def get_received_announcements(user_id: int, db: Session = Depends(get_db)):
    student_resp = get_received_announcements_student(user_id, db)
    faculty_resp = get_received_announcements_faculty(user_id, db)
    
    student_data = student_resp.get("data", []) if hasattr(student_resp, "get") else student_resp.body.get("data", []) if hasattr(student_resp, "body") else []
    faculty_data = faculty_resp.get("data", []) if hasattr(faculty_resp, "get") else faculty_resp.body.get("data", []) if hasattr(faculty_resp, "body") else []
    
    # In case of custom ReturnSuccess class, we must extract
    if not isinstance(student_data, list):
        try: student_data = student_resp["data"]
        except: student_data = []
    if not isinstance(faculty_data, list):
        try: faculty_data = faculty_resp["data"]
        except: faculty_data = []

    combined = {v["id"]: v for v in student_data + faculty_data}.values()
    sorted_combined = sorted(combined, key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return returnSuccess(list(sorted_combined))


# Fetches received announcements for a faculty user (only shows if delivery_date has passed).
@router.get("/received/faculty/{user_id}")
def get_received_announcements_faculty(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()  # naive datetime, consistent with DB stored naive datetimes

    rows = db.execute(
        text("""
            SELECT
                a.lmsn_id,
                a.notify_description,
                a.delivery_date,
                a.delivery_time,
                a.created_at,
                a.delivery_hide_date,
                a.delivery_hide_time,
                f.notify_seen_flag,
                f.notify_seenon_datetime
            FROM lms_notifications a
            JOIN lms_map_faculty_notifications f ON f.lmsn_id = a.lmsn_id
            WHERE f.faculty_id = :user_id
            ORDER BY a.created_at DESC
        """),
        {"user_id": user_id}
    ).mappings().all()

    data = []
    for n in rows:
        delivery_date = n["delivery_date"]
        delivery_time = n["delivery_time"]
        if delivery_date:
            try:
                time_str = str(delivery_time)[:8] if delivery_time else "00:00:00"
                date_str = str(delivery_date)
                scheduled_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                if scheduled_dt > now:
                    continue
            except Exception:
                pass

        hide_date = n["delivery_hide_date"]
        hide_time = n["delivery_hide_time"]
        if hide_date:
            try:
                hide_time_str = str(hide_time)[:8] if hide_time else "23:59:59"
                hide_date_str = str(hide_date)
                hide_dt = datetime.strptime(f"{hide_date_str} {hide_time_str}", "%Y-%m-%d %H:%M:%S")
                if now > hide_dt:
                    continue
            except Exception:
                pass

        data.append({
            "id": n["lmsn_id"],
            "description": n["notify_description"],
            "delivery_date": str(n["delivery_date"]) if n["delivery_date"] else None,
            "delivery_time": str(n["delivery_time"]) if n["delivery_time"] else None,
            "created_at": n["created_at"],
            "seen_flag": n["notify_seen_flag"],
            "seen_on": n["notify_seenon_datetime"],
        })

    return returnSuccess(data)


# Fetches unseen announcement count for a specific student user.
@router.get("/unseen-count/{user_id}")
def get_unseen_count(user_id: int, db: Session = Depends(get_db)):

    count = (
        db.query(func.count(StudentNotificationMap.lms_msn_id))
        .join(
            Announcement,
            Announcement.lmsn_id == StudentNotificationMap.lmsn_id,
        )
        .filter(
            StudentNotificationMap.ssd_id == user_id,
            StudentNotificationMap.notify_seen_flag == 0,
        )
        .scalar()
    )

    return returnSuccess({"unseen_count": count or 0})

# Marks a specific announcement as seen for the given student user.
@router.post("/mark-seen/{announcement_id}/{user_id}")
def mark_announcement_seen(
    announcement_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):

    existing = db.query(StudentNotificationMap).filter(
        StudentNotificationMap.lmsn_id == announcement_id,
        StudentNotificationMap.ssd_id == user_id
    ).first()

    if existing:
        existing.notify_seen_flag = 1
        existing.notify_seenon_datetime = datetime.now(timezone.utc)
    else:
        return returnException("Notification mapping not found")

    db.commit()

    return returnSuccess(None, "Marked as seen")


# Deletes a received announcement for a specific student recipient (recipient-side delete).
@router.delete("/received/student/{announcement_id}/{user_id}")
def delete_received_student(announcement_id: int, user_id: int, db: Session = Depends(get_db)):
    try:
        db.execute(
            text("DELETE FROM lms_map_student_notifications WHERE lmsn_id = :lmsn_id AND ssd_id = :user_id"),
            {"lmsn_id": announcement_id, "user_id": user_id}
        )
        db.commit()
        return returnSuccess(None, "Announcement removed from your received list")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete: {str(exc)}")


# Deletes a received announcement for a specific faculty recipient (recipient-side delete).
@router.delete("/received/faculty/{announcement_id}/{user_id}")
def delete_received_faculty(announcement_id: int, user_id: int, db: Session = Depends(get_db)):
    try:
        db.execute(
            text("DELETE FROM lms_map_faculty_notifications WHERE lmsn_id = :lmsn_id AND faculty_id = :user_id"),
            {"lmsn_id": announcement_id, "user_id": user_id}
        )
        db.commit()
        return returnSuccess(None, "Announcement removed from your received list")
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to delete: {str(exc)}")
