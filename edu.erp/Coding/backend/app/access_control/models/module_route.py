from sqlalchemy import (
    Column, Integer, Boolean, DateTime, String, ForeignKey, func, Index
)
from sqlalchemy.orm import relationship, backref
from ...core.database import Base


class ModuleRoute(Base):
    __tablename__ = "iems_module_routes"

    route_id = Column(Integer, primary_key=True, autoincrement=True)
    route_name = Column(String(255), nullable=False)
    route_path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    module_id = Column(
        Integer, ForeignKey("iems_modules.module_id"), nullable=False
    )
    menu_id = Column(Integer, ForeignKey("menus.menu_id"), nullable=True)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    module = relationship("Module", back_populates="routes")
    menu = relationship(
        "Menu", backref=backref("module_routes", cascade="all, delete-orphan")
    )
    user_permissions = relationship(
        "UserPermission", back_populates="route", cascade="all, delete-orphan"
    )
    role_permissions = relationship(
        "UserRolePermission", back_populates="route",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_routes_path_method", "route_path", "method"),
    )
