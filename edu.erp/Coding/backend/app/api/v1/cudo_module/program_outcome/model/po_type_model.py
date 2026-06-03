from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class PoType(Base):
    """
    Program Outcome Type Model
    Maps to the existing 'cudos_po_type' table in the database
    """
    __tablename__ = "cudos_po_type"

    po_type_id = Column(Integer, primary_key=True, autoincrement=True)
    po_type_name = Column(String(255), nullable=False, unique=True)
    po_type_description = Column(String(1000), nullable=True)
    created_by = Column(Integer, nullable=False)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(Integer, nullable=True)
    modified_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)
