from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, func
)
from sqlalchemy.orm import relationship
from ...core.database import Base


class Permission(Base):
    __tablename__ = "iems_permissions"

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String(100), nullable=False, unique=True)
    method = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    user_permissions = relationship(
        "UserPermission", back_populates="permission",
        cascade="all, delete-orphan"
    )
    role_permissions = relationship(
        "UserRolePermission", back_populates="permission",
        cascade="all, delete-orphan"
    )
