from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from .schema import StudentRequest
from .service import list_notifications, notification_counts, mark_read

# Demo contract: explicit student_id in every JSON body. At ERP integration,
# replace this dependency with one that validates payload.student_id against
# the authenticated student. Never equate a faculty/user ID with a student ID.
def student_identity(payload: StudentRequest):
    return payload.student_id


router = APIRouter(prefix="/student/notifications", tags=["Student Notifications"])


@router.post("/unread")
def unread(student_id: int = Depends(student_identity), db: Session = Depends(get_db)):
    return {"status": True, "data": list_notifications(db, student_id, 0)}


@router.post("/read")
def read(student_id: int = Depends(student_identity), db: Session = Depends(get_db)):
    return {"status": True, "data": list_notifications(db, student_id, 1)}


@router.post("/all")
def all_notifications(student_id: int = Depends(student_identity), db: Session = Depends(get_db)):
    return {"status": True, "data": list_notifications(db, student_id)}


@router.post("/counts")
def counts(student_id: int = Depends(student_identity), db: Session = Depends(get_db)):
    return {"status": True, "data": notification_counts(db, student_id)}


@router.post("/{notification_id}/mark-read")
def update_seen(notification_id: int = Path(..., gt=0),
                student_id: int = Depends(student_identity), db: Session = Depends(get_db)):
    return mark_read(db, student_id, notification_id)
