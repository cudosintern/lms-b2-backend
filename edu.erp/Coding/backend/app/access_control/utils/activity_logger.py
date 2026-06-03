from sqlalchemy.orm import Session
from ..models.activity_log import ActivityLog
from datetime import datetime, timezone


def log_activity(
    db: Session, user_id: int, action: str, description: str,
    ip_address: str, user_agent: str
):
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(activity)
    db.commit()
