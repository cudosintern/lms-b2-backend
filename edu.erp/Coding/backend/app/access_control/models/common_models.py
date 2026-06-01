from sqlalchemy import (
    Column, Integer, Text, String, ForeignKey, Date, SmallInteger
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from ...core.database import Base


class University(Base):
    __tablename__ = "iems_university"

    unv_id = Column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    unv_name = Column(String(500), nullable=False)
    unv_desc = Column(Text, nullable=False)
    status = Column(SmallInteger)
    created_by = Column(SmallInteger, nullable=False)
    modified_by = Column(SmallInteger, nullable=False)
    created_date = Column(Date, nullable=False)
    modified_date = Column(Date, nullable=False)
    unv_code = Column(String(1), nullable=False)

    organisation_types = relationship(
        "OrganisationType", back_populates="university"
    )
    organisations = relationship(
        "Organisation", back_populates="university",
        cascade="all, delete-orphan"
    )


class Organisation(Base):
    __tablename__ = "iems_organisation"

    org_id = Column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    org_name = Column(String(500), nullable=False)
    org_society = Column(String(200))
    org_desc = Column(String(2500))
    unv_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_university.unv_id"),
        nullable=False
    )
    status = Column(SmallInteger, nullable=False)
    created_by = Column(SmallInteger)
    modified_by = Column(SmallInteger)
    create_date = Column(Date)
    modify_date = Column(Date)
    org_code = Column(String(10))
    org_type_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_organisation_type.org_type_id"),
        nullable=True
    )
    org_location = Column(String(100), nullable=True)
    org_contact_number = Column(String(100), nullable=True)
    org_email = Column(String(100), nullable=True)
    org_logo = Column(String(40), nullable=True)
    profile_image = Column(String(45))
    other_profile_image = Column(String(45))
    is_medical_flag = Column(Integer, nullable=False)
    certificate_tab_mandatory = Column(Integer, nullable=False)
    bank_tab_mandatory = Column(Integer, nullable=False)
    additional_fee_label = Column(String(32), nullable=False)
    DOB_format = Column(String(32), nullable=False)
    org_address = Column(Text, nullable=False)
    org_website = Column(String(250), nullable=False)

    users = relationship("User", back_populates="organisation")
    user_roles = relationship("UserRole", back_populates="organisation")
    university = relationship("University", back_populates="organisations")
    organisation_type = relationship(
        "OrganisationType", back_populates="organisations"
    )


class OrganisationType(Base):
    __tablename__ = "iems_organisation_type"

    org_type_id = Column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    org_type = Column(String(50), nullable=False)
    org_type_desc = Column(String(50), nullable=False)
    unv_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("iems_university.unv_id"),
        nullable=False
    )
    status = Column(Integer, nullable=False)

    university = relationship(
        "University", back_populates="organisation_types"
    )
    organisations = relationship(
        "Organisation", back_populates="organisation_type",
        cascade="all, delete-orphan"
    )
