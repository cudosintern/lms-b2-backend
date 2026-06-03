from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ...core.database import Base


class ActivityLog(Base):
    __tablename__ = "erp_auth_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_users.id", ondelete="SET NULL"),
        nullable=True
    )
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
