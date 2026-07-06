from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Curriculum(Base):
    __tablename__ = "curriculum"
    crclm_id = Column(Integer, primary_key=True, autoincrement=True)
    crclm_name = Column(String(255))
    status = Column(Integer, default=1)
    delivery_methods = relationship("CurriculumDeliveryMethod", back_populates="curriculum", cascade="all, delete-orphan")

class BloomLevel(Base):
    __tablename__ = "bloom_level"
    bloom_id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(255))
    delivery_blooms = relationship("CurriculumDeliveryBloom", back_populates="bloom_level", cascade="all, delete-orphan")

class CurriculumDeliveryMethod(Base):
    __tablename__ = "curriculum_delivery_method"
    crclm_dm_id = Column(Integer, primary_key=True, autoincrement=True)
    crclm_id = Column(Integer, ForeignKey("curriculum.crclm_id"))
    delivery_mtd_name = Column(String(800), nullable=False)
    delivery_mtd_desc = Column(String(2000))
    created_by = Column(Integer, nullable=True)
    modified_by = Column(Integer, nullable=True)
    curriculum = relationship("Curriculum", back_populates="delivery_methods")
    blooms = relationship("CurriculumDeliveryBloom", back_populates="delivery_method", cascade="all, delete-orphan")

class CurriculumDeliveryBloom(Base):
    __tablename__ = "curriculum_delivery_bloom"
    crclm_bloom_id = Column(Integer, primary_key=True, autoincrement=True)
    crclm_dm_id = Column(Integer, ForeignKey("curriculum_delivery_method.crclm_dm_id"))
    bloom_id = Column(Integer, ForeignKey("bloom_level.bloom_id"))
    delivery_method = relationship("CurriculumDeliveryMethod", back_populates="blooms")
    bloom_level = relationship("BloomLevel", back_populates="delivery_blooms")
