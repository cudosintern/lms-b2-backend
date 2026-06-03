from sqlalchemy import (
    Column, Integer, ForeignKey, Boolean, DateTime, func, Index
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from ...core.database import Base


class UserPermission(Base):
    __tablename__ = "iems_user_permissions"

    user_permission_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        INTEGER(unsigned=True), ForeignKey("iems_users.id"), nullable=False
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

    route = relationship("ModuleRoute", back_populates="user_permissions")
    permission = relationship("Permission", back_populates="user_permissions")

    __table_args__ = (
        Index(
            "ix_user_permissions_user_route", "user_id",
            "route_id", unique=True
        ),
    )
