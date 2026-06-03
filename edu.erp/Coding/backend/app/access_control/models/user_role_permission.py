from sqlalchemy import (
    Column, Integer, ForeignKey, Boolean, DateTime, func, Index
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from ...core.database import Base


class UserRolePermission(Base):
    __tablename__ = "iems_user_role_permissions"

    user_role_permission_id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    user_role_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_user_role_master.user_role_id"),
        nullable=False
    )
    route_id = Column(
        Integer, ForeignKey("iems_module_routes.route_id"), nullable=False
    )
    permission_id = Column(
        Integer, ForeignKey("iems_permissions.permission_id"), nullable=True
    )
    status = Column(Boolean, default=True)
    org_id = Column(
        INTEGER(unsigned=True), ForeignKey("iems_organisation.org_id"),
        default=1
    )
    created_at = Column(DateTime, default=func.now())

    route = relationship("ModuleRoute", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        Index(
            "ix_role_permissions_role_route", "user_role_id",
            "route_id", unique=True
        ),
    )
