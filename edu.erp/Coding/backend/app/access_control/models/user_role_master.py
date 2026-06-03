from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Text, func
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, backref
from ...core.database import Base


class UserRoleMaster(Base):
    __tablename__ = "iems_user_role_master"

    user_role_id = Column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    role_name = Column(String(100), nullable=False)
    description = Column(Text)
    inherits_from = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_user_role_master.user_role_id"),
        nullable=True
    )
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    inherited_roles = relationship(
        "UserRoleMaster", backref=backref(
            "parent_role", remote_side="[UserRoleMaster.user_role_id]"
        )
    )
    user_roles = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )
    role_permissions = relationship(
        "UserRolePermission", backref="role", cascade="all, delete-orphan"
    )
