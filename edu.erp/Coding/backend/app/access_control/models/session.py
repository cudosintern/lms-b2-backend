from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ...core.database import Base


class UserSession(Base):
    __tablename__ = "erp_auth_user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_users.id", ondelete="CASCADE"),
        nullable=False
    )
    access_token = Column(String(500), unique=True, nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    # school_id = Column(Integer, nullable=True)
    last_active_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=False)
    user = relationship("User", back_populates="sessions")


class BlacklistedToken(Base):
    __tablename__ = "erp_auth_blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
