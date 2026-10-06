"""ERP recipient mappings and the CodeIgniter delivery visibility rules."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
import os

from fastapi import HTTPException
from sqlalchemy import bindparam, text

IST = timezone(timedelta(hours=5, minutes=30))

# NULL programme/batch means all in the existing faculty announcement sender.
# Recipient membership is still mandatory; metadata never grants membership.
VISIBLE_FROM = """
    FROM lms_map_student_notifications m
    JOIN lms_notifications_details d
      ON d.lmsn_det_id = m.lmsn_det_id AND d.lmsn_id = m.lmsn_id
    JOIN lms_notifications n ON n.lmsn_id = m.lmsn_id
    JOIN iems_students s ON s.student_id = m.ssd_id
    WHERE m.ssd_id = :student_id AND d.student_flag = 1
      AND d.dept_id = s.department_id
      AND (d.pgm_id IS NULL OR d.pgm_id = s.program_id)
      AND (d.academic_batch_id IS NULL OR d.academic_batch_id = s.academic_batch_id)
      AND (n.delivery_date < :today
           OR (n.delivery_date = :today AND n.delivery_time <= :now_time))
      AND ((n.delivery_hide_date IS NULL AND n.delivery_hide_time IS NULL)
           OR n.delivery_hide_date > :today
           OR (n.delivery_hide_date = :today AND n.delivery_hide_time >= :now_time))
"""


def parameters(db, student_id, now=None):
    student = db.execute(text(
        "SELECT student_id FROM iems_students WHERE student_id = :student_id"
    ), {"student_id": student_id}).first()
    if student is None:
        raise HTTPException(404, "Student not found")
    local_now = (now or datetime.now(IST)).astimezone(IST)
    return {"student_id": student_id, "today": local_now.strftime("%Y-%m-%d"),
            "now_time": local_now.strftime("%H:%M:%S")}


def attachment_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme:
        return value if parsed.scheme.lower() in {"http", "https"} else ""
    if value.startswith("//") or "\\" in value:
        return ""
    base = os.getenv("LMS_NOTIFICATION_ATTACHMENT_BASE_URL", "")
    return urljoin(base.rstrip("/") + "/", value.lstrip("/")) if base else value


def list_notifications(db, student_id, seen=None, now=None):
    params = parameters(db, student_id, now)
    # Aggregate only recipient state; avoid legacy non-deterministic GROUP BY.
    query = """
        SELECT n.lmsn_id AS id, n.notify_description AS notice,
               n.notify_attachment AS file_name, n.notify_document_url AS file_url,
               n.delivery_date, n.delivery_time, state.is_read,
               u.title, u.first_name, u.middle_name, u.last_name,
               u.username, n.created_by AS sender_id
        FROM lms_notifications n
        JOIN (SELECT m.lmsn_id, MIN(COALESCE(m.notify_seen_flag, 0)) AS is_read
    """ + VISIBLE_FROM + """
          GROUP BY m.lmsn_id) state ON state.lmsn_id = n.lmsn_id
        LEFT JOIN iems_users u ON u.id = n.created_by
    """
    if seen is not None:
        query += " WHERE state.is_read = :seen"
        params["seen"] = seen
    query += " ORDER BY n.delivery_date DESC, n.lmsn_id DESC"
    result = []
    for row in db.execute(text(query), params).mappings():
        item = dict(row)
        day = item.pop("delivery_date")
        clock = item.pop("delivery_time")
        item["sent_on"] = f"{day}T{str(clock).zfill(8)}+05:30"
        username = str(item.pop("username") or "").strip()
        sender_id = item.pop("sender_id")
        item["sender"] = " ".join(filter(None, (str(item.pop(key) or "").strip()
                                    for key in ("title", "first_name", "middle_name", "last_name")))) or username or (f"User {sender_id}" if sender_id else "Unknown sender")
        item["is_read"] = bool(item["is_read"])
        item["file_url"] = attachment_url(item["file_url"])
        result.append(item)
    return result


def notification_counts(db, student_id, now=None):
    params = parameters(db, student_id, now)
    rows = db.execute(text("""
        SELECT state.is_read, COUNT(*) AS count FROM (
          SELECT m.lmsn_id, MIN(COALESCE(m.notify_seen_flag, 0)) AS is_read
    """ + VISIBLE_FROM + """
          GROUP BY m.lmsn_id) state GROUP BY state.is_read
    """), params).mappings()
    counts = {"unread_count": 0, "read_count": 0}
    for row in rows:
        counts["read_count" if row["is_read"] else "unread_count"] = row["count"]
    counts["total_count"] = counts["read_count"] + counts["unread_count"]
    return counts


def mark_read(db, student_id, notification_id, now=None):
    local_now = (now or datetime.now(IST)).astimezone(IST)
    try:
        params = parameters(db, student_id, local_now)
        params["notification_id"] = notification_id
        ids = db.execute(text("SELECT m.lms_msn_id " + VISIBLE_FROM +
                              " AND m.lmsn_id = :notification_id"), params).scalars().all()
        if not ids:
            raise HTTPException(404, "Notification not available for this student")
        # Only eligible mappings belonging to this student; repeat calls preserve
        # the first seen time, including after a retry or concurrent request.
        db.execute(text("""
            UPDATE lms_map_student_notifications
            SET notify_seen_flag = 1, notify_seenon_datetime = :seen_on
            WHERE ssd_id = :student_id AND lmsn_id = :notification_id
              AND lms_msn_id IN :ids AND COALESCE(notify_seen_flag, 0) = 0
        """).bindparams(bindparam("ids", expanding=True)), {
            "student_id": student_id, "notification_id": notification_id,
            "ids": ids, "seen_on": local_now.replace(tzinfo=None)})
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"status": True, "message": "Notification marked as read"}
