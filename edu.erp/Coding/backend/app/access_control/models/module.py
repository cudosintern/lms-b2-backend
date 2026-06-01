from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, func
)
from sqlalchemy.orm import relationship
from ...core.database import Base


class Module(Base):
    __tablename__ = "iems_modules"

    module_id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String(255), nullable=False, unique=True)
    module_type = Column(Integer, nullable=False, default=0)
    code = Column(String(255), nullable=False, unique=True)
    url = Column(String(255), nullable=False)
    icon_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    routes = relationship(
        "ModuleRoute", back_populates="module", cascade="all, delete-orphan"
    )
