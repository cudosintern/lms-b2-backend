from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, bindparam, or_
from datetime import datetime, timezone, date
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess, returnException
from app.db.models import (
    Announcement,
    StudentNotificationMap,
    IEMSDepartment,
    IEMProgram,
    IEMSAcademicBatch,
)

router = APIRouter(prefix="/announcements", tags=["Announcements"])


# ─── Request Models ──────────────────────────────────────────────────────────
class SendAnnouncementCreateRequest(BaseModel):
    notify_description: str = Field(..., min_length=1)
    created_by: int
    target_user_type: Literal["faculty", "student", "parent"]
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    delivery_hide_date: Optional[str] = None
    delivery_hide_time: Optional[str] = None
    display_to_timetable: int = 0
    dept_ids: List[int] = Field(default_factory=list)  # Changed to list
    pgm_ids: List[int] = Field(default_factory=list)  # Added for multiple programs
    academic_batch_ids: List[int] = Field(default_factory=list)  # Changed to list
    semester: Optional[int] = None
    section: Optional[str] = None
    recipient_ids: List[int] = Field(default_factory=list)
    recipient_usns: List[str] = Field(default_factory=list)

    @validator('delivery_date')
    def validate_delivery_date(cls, v):
        if v:
            delivery_dt = datetime.strptime(v, "%Y-%m-%d").date()
            if delivery_dt < date.today():
                raise ValueError("Delivery date must be today or in the future")
        return v

    @validator('delivery_hide_date')
    def validate_hide_date(cls, v, values):
        if v and 'delivery_date' in values and values['delivery_date']:
            hide_dt = datetime.strptime(v, "%Y-%m-%d").date()
            delivery_dt = datetime.strptime(values['delivery_date'], "%Y-%m-%d").date()
            if hide_dt <= delivery_dt:
                raise ValueError("Hide date must be after delivery date")
        return v


class SendAnnouncementUpdateRequest(BaseModel):
    notify_description: Optional[str] = None
    delivery_date: Optional[str] = None
    delivery_time: Optional[str] = None
    delivery_hide_date: Optional[str] = None
    delivery_hide_time: Optional[str] = None
    display_to_timetable: Optional[int] = None
    modified_by: int


# ─── Helper Functions ────────────────────────────────────────────────────────
def _normalize_user_type(value: str) -> str:
    return (value or "").strip().lower()


def _resolve_flags(user_type: str) -> tuple[int, int, int]:
    if user_type == "faculty":
        return 1, 0, 0
    if user_type == "student":
        return 0, 1, 0
    if user_type == "parent":
        return 0, 0, 1
    raise ValueError("Invalid target_user_type")


def _build_recipient_query(
    user_type: str,
    dept_ids: Optional[List[int]] = None,
    pgm_ids: Optional[List[int]] = None,
    academic_batch_ids: Optional[List[int]] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
) -> tuple[str, dict]:
    params: dict = {}

    if user_type == "faculty":
        sql = """
            SELECT
                u.id AS recipient_id,
                u.username,
                TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))) AS full_name,
                u.user_dept_id AS dept_id,
                d.dept_name AS dept_name
            FROM iems_users u
            LEFT JOIN iems_department d ON u.user_dept_id = d.dept_id
            WHERE u.status = 1
        """
        if dept_ids:
            sql += " AND u.user_dept_id IN :dept_ids"
            params["dept_ids"] = tuple(dept_ids)
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
                s.section,
                d.dept_name,
                p.pgm_title,
                b.academic_batch_desc
            FROM iems_students s
            LEFT JOIN iems_department d ON s.department_id = d.dept_id
            LEFT JOIN iems_program p ON s.program_id = p.pgm_id
            LEFT JOIN iems_academic_batch b ON s.academic_batch_id = b.academic_batch_id
            WHERE s.status = 1 AND IFNULL(s.delete_status, 0) = 0
        """
        if dept_ids:
            sql += " AND s.department_id IN :dept_ids"
            params["dept_ids"] = tuple(dept_ids)
        if pgm_ids:
            sql += " AND s.program_id IN :pgm_ids"
            params["pgm_ids"] = tuple(pgm_ids)
        if academic_batch_ids:
            sql += " AND s.academic_batch_id IN :academic_batch_ids"
            params["academic_batch_ids"] = tuple(academic_batch_ids)
        if semester is not None:
            sql += " AND s.current_semester = :semester"
            params["semester"] = semester
        if section and section.strip():
            sql += " AND s.section = :section"
            params["section"] = section.strip()

        sql += " ORDER BY s.department_id, s.program_id, s.academic_batch_id, s.student_id DESC"
        return sql, params

    raise ValueError("Invalid user_type")


def _group_recipients(rows: list, user_type: str) -> dict:
    """Group recipients by department, curriculum, and user type"""
    grouped = {
        "user_type": user_type,
        "groups": []
    }
    
    if user_type == "faculty":
        # Group by department
        dept_groups = {}
        for row in rows:
            dept_id = row.get("dept_id")
            dept_name = row.get("dept_name") or f"Department {dept_id}"
            if dept_id not in dept_groups:
                dept_groups[dept_id] = {
                    "group_id": f"dept_{dept_id}",
                    "group_name": dept_name,
                    "group_type": "department",
                    "items": []
                }
            dept_groups[dept_id]["items"].append({
                "recipient_id": row["recipient_id"],
                "username": row["username"],
                "full_name": row["full_name"].strip(),
                "dept_id": row["dept_id"],
            })
        grouped["groups"] = list(dept_groups.values())
    
    else:  # student or parent
        # Group by department -> program -> curriculum
        dept_groups = {}
        for row in rows:
            dept_id = row.get("department_id")
            dept_name = row.get("dept_name") or f"Department {dept_id}"
            pgm_id = row.get("program_id")
            pgm_title = row.get("pgm_title") or f"Program {pgm_id}"
            batch_id = row.get("academic_batch_id")
            batch_desc = row.get("academic_batch_desc") or f"Batch {batch_id}"
            
            # Department level
            if dept_id not in dept_groups:
                dept_groups[dept_id] = {
                    "group_id": f"dept_{dept_id}",
                    "group_name": dept_name,
                    "group_type": "department",
                    "subgroups": {}
                }
            
            # Program level under department
            pgm_key = f"{dept_id}_{pgm_id}"
            if pgm_key not in dept_groups[dept_id]["subgroups"]:
                dept_groups[dept_id]["subgroups"][pgm_key] = {
                    "group_id": f"pgm_{pgm_id}",
                    "group_name": pgm_title,
                    "group_type": "program",
                    "subgroups": {}
                }
            
            # Curriculum level under program
            batch_key = f"{pgm_key}_{batch_id}"
            if batch_key not in dept_groups[dept_id]["subgroups"][pgm_key]["subgroups"]:
                dept_groups[dept_id]["subgroups"][pgm_key]["subgroups"][batch_key] = {
                    "group_id": f"batch_{batch_id}",
                    "group_name": batch_desc,
                    "group_type": "curriculum",
                    "items": []
                }
            
            # Add the student
            item = {
                "recipient_id": row["recipient_id"],
                "usn": row["usno"],
                "full_name": (row["full_name"] or "").strip(),
                "dept_id": row["department_id"],
                "pgm_id": row["program_id"],
                "academic_batch_id": row["academic_batch_id"],
                "semester": row["current_semester"],
                "section": row["section"],
            }
            if user_type == "parent":
                item["parent_usn"] = row.get("ref_usno") or row["usno"]
                item["parent_name"] = f"{(row['full_name'] or '').strip()} Parent".strip()
                item["student_usn"] = row["usno"]
            
            dept_groups[dept_id]["subgroups"][pgm_key]["subgroups"][batch_key]["items"].append(item)
        
        # Convert nested dict to list structure
        grouped["groups"] = []
        for dept in dept_groups.values():
            dept_copy = {
                "group_id": dept["group_id"],
                "group_name": dept["group_name"],
                "group_type": dept["group_type"],
                "subgroups": []
            }
            for pgm in dept["subgroups"].values():
                pgm_copy = {
                    "group_id": pgm["group_id"],
                    "group_name": pgm["group_name"],
                    "group_type": pgm["group_type"],
                    "subgroups": []
                }
                for batch in pgm["subgroups"].values():
                    batch_copy = {
                        "group_id": batch["group_id"],
                        "group_name": batch["group_name"],
                        "group_type": batch["group_type"],
                        "items": batch["items"]
                    }
                    pgm_copy["subgroups"].append(batch_copy)
                dept_copy["subgroups"].append(pgm_copy)
            grouped["groups"].append(dept_copy)
    
    return grouped


# ─── API Endpoints ──────────────────────────────────────────────────────────

@router.get("/send/user-types")
def get_send_user_types():
    return returnSuccess(
        [
            {"key": "faculty", "label": "Faculty"},
            {"key": "student", "label": "Student"},
            {"key": "parent", "label": "Parent"},
        ]
    )


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


@router.get("/send/programs")
def get_send_programs(
    dept_ids: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = (
        db.query(IEMProgram.pgm_id, IEMProgram.pgm_title, IEMProgram.dept_id)
        .filter(IEMProgram.status == 1)
    )
    if dept_ids:
        ids = [int(x.strip()) for x in dept_ids.split(",") if x.strip()]
        if ids:
            query = query.filter(IEMProgram.dept_id.in_(ids))
    programs = query.order_by(IEMProgram.pgm_title.asc()).all()
    data = [
        {"pgm_id": p.pgm_id, "pgm_title": p.pgm_title, "dept_id": p.dept_id}
        for p in programs
    ]
    return returnSuccess(data)


@router.get("/send/curriculums")
def get_send_curriculums(
    dept_ids: Optional[str] = Query(default=None),
    pgm_ids: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(
        IEMSAcademicBatch.academic_batch_id,
        IEMSAcademicBatch.academic_batch_desc,
        IEMSAcademicBatch.dept_id,
        IEMSAcademicBatch.pgm_id,
    ).filter(IEMSAcademicBatch.status == 1)
    
    if dept_ids:
        ids = [int(x.strip()) for x in dept_ids.split(",") if x.strip()]
        if ids:
            query = query.filter(IEMSAcademicBatch.dept_id.in_(ids))
    if pgm_ids:
        ids = [int(x.strip()) for x in pgm_ids.split(",") if x.strip()]
        if ids:
            query = query.filter(IEMSAcademicBatch.pgm_id.in_(ids))

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


@router.get("/send/recipients")
def get_send_recipients(
    user_type: str,
    dept_ids: Optional[str] = Query(default=None),
    pgm_ids: Optional[str] = Query(default=None),
    academic_batch_ids: Optional[str] = Query(default=None),
    semester: Optional[int] = Query(default=None),
    section: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    normalized_user_type = _normalize_user_type(user_type)
    if normalized_user_type not in {"faculty", "student", "parent"}:
        return returnException("Invalid user_type. Use faculty/student/parent.")

    # Parse comma-separated IDs
    dept_list = [int(x.strip()) for x in (dept_ids or "").split(",") if x.strip()]
    pgm_list = [int(x.strip()) for x in (pgm_ids or "").split(",") if x.strip()]
    batch_list = [int(x.strip()) for x in (academic_batch_ids or "").split(",") if x.strip()]

    sql, params = _build_recipient_query(
        normalized_user_type,
        dept_list if dept_list else None,
        pgm_list if pgm_list else None,
        batch_list if batch_list else None,
        semester,
        section,
    )
    rows = db.execute(text(sql), params).mappings().all()

    # Group the recipients
    grouped_data = _group_recipients(rows, normalized_user_type)

    return returnSuccess({
        "total": len(rows),
        "grouped": grouped_data,
        "items": rows,  # Keep flat list for backward compatibility
    })


@router.post("/send/create")
def create_send_announcement(payload: SendAnnouncementCreateRequest, db: Session = Depends(get_db)):
    normalized_user_type = _normalize_user_type(payload.target_user_type)
    if normalized_user_type not in {"faculty", "student", "parent"}:
        return returnException("Invalid target_user_type. Use faculty/student/parent.")

    if not payload.notify_description.strip():
        return returnException("notify_description is required")

    # Validate that at least one department is selected
    if not payload.dept_ids:
        return returnException("At least one department must be selected")

    faculty_flag, student_flag, parent_flag = _resolve_flags(normalized_user_type)

    try:
        # Create announcement
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

        # For each selected department, create a notification detail
        inserted_recipients = 0
        lmsn_det_ids = []

        for dept_id in payload.dept_ids:
            # Save targeting metadata for this announcement
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
                    "dept_id": dept_id,
                    "pgm_id": payload.pgm_ids[0] if payload.pgm_ids else None,
                    "academic_batch_id": payload.academic_batch_ids[0] if payload.academic_batch_ids else None,
                    "faculty_flag": faculty_flag,
                    "student_flag": student_flag,
                    "parent_flag": parent_flag,
                    "created_by": payload.created_by,
                },
            )
            lmsn_det_id = detail_result.lastrowid
            lmsn_det_ids.append(lmsn_det_id)

            # Get recipients for this department
            sql, params = _build_recipient_query(
                normalized_user_type,
                dept_ids=[dept_id],
                pgm_ids=payload.pgm_ids if payload.pgm_ids else None,
                academic_batch_ids=payload.academic_batch_ids if payload.academic_batch_ids else None,
                semester=payload.semester,
                section=payload.section,
            )
            dept_recipients = db.execute(text(sql), params).mappings().all()
            recipient_ids = [r["recipient_id"] for r in dept_recipients]

            # Filter by selected recipient IDs if provided
            if payload.recipient_ids:
                recipient_ids = [rid for rid in recipient_ids if rid in payload.recipient_ids]

            if not recipient_ids:
                continue

            # Save recipients based on user type
            if normalized_user_type == "faculty":
                faculty_rows = db.execute(
                    text(
                        """
                        SELECT id, username
                        FROM iems_users
                        WHERE id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(recipient_ids)},
                ).mappings().all()

                for row in faculty_rows:
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

            elif normalized_user_type == "student":
                student_rows = db.execute(
                    text(
                        """
                        SELECT student_id, usno
                        FROM iems_students
                        WHERE student_id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(recipient_ids)},
                ).mappings().all()

                for row in student_rows:
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

            else:  # parent
                parent_rows = db.execute(
                    text(
                        """
                        SELECT student_id, usno, ref_usno,
                               TRIM(COALESCE(name, CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')))) AS full_name
                        FROM iems_students
                        WHERE student_id IN :recipient_ids
                        """
                    ).bindparams(bindparam("recipient_ids", expanding=True)),
                    {"recipient_ids": tuple(recipient_ids)},
                ).mappings().all()

                for row in parent_rows:
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

        if inserted_recipients == 0:
            db.rollback()
            return returnException("No recipients found for the selected filters/user type")

        db.commit()

        return returnSuccess(
            {
                "lmsn_id": announcement.lmsn_id,
                "lmsn_det_ids": lmsn_det_ids,
                "target_user_type": normalized_user_type,
                "recipients_saved": inserted_recipients,
            },
            "Announcement created successfully",
        )
    except Exception as exc:
        db.rollback()
        return returnException(f"Failed to create announcement: {str(exc)}")


# ─── Remaining endpoints (sent, received, delete, etc.) ───────────────────

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
            """
        ),
        {"lmsn_id": announcement_id},
    ).mappings().all()

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
        "details": details,
        "recipient_counts": {
            "faculty": int(faculty_count),
            "student": int(student_count),
            "parent": int(parent_count),
        },
    }
    return returnSuccess(data)


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


@router.get("/received/student/{user_id}")
def get_received_announcements_student(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()

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


@router.get("/received/faculty/{user_id}")
def get_received_announcements_faculty(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()

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


@router.get("/received/{user_id}")
def get_received_announcements(user_id: int, db: Session = Depends(get_db)):
    # Try both student and faculty endpoints
    student_resp = get_received_announcements_student(user_id, db)
    faculty_resp = get_received_announcements_faculty(user_id, db)
    
    student_data = student_resp.get("data", []) if hasattr(student_resp, "get") else []
    faculty_data = faculty_resp.get("data", []) if hasattr(faculty_resp, "get") else []
    
    combined = {v["id"]: v for v in student_data + faculty_data}.values()
    sorted_combined = sorted(combined, key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return returnSuccess(list(sorted_combined))


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