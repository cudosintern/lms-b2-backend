from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.access_control.schemas.acitivity_log import AcitivityCreate
from ..models.activity_log import ActivityLog
from ...core.database import get_db

router = APIRouter(tags=["Activity Logs"])


@router.get("/activity-logs")
def get_activity_logs(db: Session = Depends(get_db)):
    """Fetches all activity logs (Admin Only)."""
    return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).all()


@router.post("/activity-logs")
def post_acitivity_logs_by_user(
    activity_data: AcitivityCreate, db: Session = Depends(get_db)
):
    """Post all acitivty logs (Admin only)."""
    new_acitivity_data = ActivityLog(
        user_id=activity_data.user_id,
        action=activity_data.action,
        description=activity_data.description,
        ip_address=activity_data.ip_address,
        user_agent=activity_data.user_agent,
        timestamp=activity_data.timestamp,
    )

    db.add(new_acitivity_data)
    db.commit()


@router.put("/activity-logs/{log_id}")
def update_acitivity_logs(
    log_id: int, activity_data: AcitivityCreate, db: Session = Depends(get_db)
):
    db.query(ActivityLog).filter(ActivityLog.id == log_id).update(
        {
            ActivityLog.user_id: activity_data.user_id,
            ActivityLog.action: activity_data.action,
            ActivityLog.description: activity_data.description,
            ActivityLog.ip_address: activity_data.ip_address,
            ActivityLog.user_agent: activity_data.user_agent,
            ActivityLog.timestamp: activity_data.timestamp,
        },
        synchronize_session=False,
    )


@router.delete("/activity-logs/{log_id}")
def delete_acitivity_log(log_id: int, db: Session = Depends(get_db)):
    activity_log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not activity_log:
        raise HTTPException(status_code=404, detail="Activity log not found")
    db.delete(activity_log)
    db.commit()
    return {"message": "activity logs removed successfully"}
