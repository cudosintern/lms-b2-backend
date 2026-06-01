from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, SmallInteger
)
from sqlalchemy.orm import relationship
from ...core.database import Base


class Menu(Base):
    __tablename__ = "menus"

    menu_id = Column(Integer, primary_key=True, autoincrement=True)
    menu_name = Column(String(45), nullable=True)
    parent = Column(Integer, ForeignKey("menus.menu_id"), nullable=True)
    menu_level = Column(SmallInteger, nullable=True)
    menu_url = Column(String(255), nullable=True)
    parent_class = Column(String(255), nullable=False)
    menu_class = Column(String(100), nullable=True)
    menu_icon = Column(String(100), nullable=True)
    menu_order = Column(Integer, nullable=True)
    show_menu = Column(Boolean, default=True)
    status = Column(Boolean, default=True)
    module_id = Column(
        Integer, ForeignKey("iems_modules.module_id"), nullable=True
    )

    module = relationship("Module", lazy="joined")
    # Self-referencing menu hierarchy
    parent_menu = relationship(
        "Menu", remote_side=[menu_id], backref="sub_menus"
    )
