from sqlalchemy import (
    Column, Integer, Boolean, DateTime, ForeignKey, func
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, backref
from ...core.database import Base


class RoleMenu(Base):
    __tablename__ = "iems_role_menus"

    role_menu_id = Column(Integer, primary_key=True, autoincrement=True)
    user_role_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_user_role_master.user_role_id"),
        nullable=False
    )
    menu_id = Column(Integer, ForeignKey("menus.menu_id"), nullable=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    menu = relationship(
        "Menu", backref=backref("role_menus", cascade="all, delete-orphan")
    )
    user_role = relationship(
        "UserRoleMaster", backref=backref(
            "role_menus", cascade="all, delete-orphan"
        )
    )
