from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, VARBINARY
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from datetime import datetime
from ...core.database import Base


class User(Base):
    __tablename__ = "iems_users"

    id = Column(
        INTEGER(unsigned=True), primary_key=True, index=True
    )
    ip_address = Column(VARBINARY(16), nullable=True)
    username = Column(String(40), unique=True, index=True, nullable=False)
    password = Column(String(80), nullable=False)
    salt = Column(String(80), nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    activation_code = Column(String(40), nullable=True)
    forgotten_password_code = Column(String(40), nullable=True)
    forgotten_password_time = Column(Integer, nullable=True)
    remember_code = Column(String(40), nullable=True)
    title = Column(String(8), nullable=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    org_id = Column(
        INTEGER(unsigned=True), ForeignKey("iems_organisation.org_id"),
        default=1
    )
    student_id = Column(INTEGER(unsigned=True), nullable=True)
    user_type = Column(String(80), nullable=False)
    user_dept_id = Column(INTEGER(unsigned=True), nullable=True)
    active = Column(Boolean, default=True)
    created_on = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    lockout_until = Column(DateTime, nullable=True)
    designation_id = Column(INTEGER(unsigned=True), nullable=True)
    mobile = Column(String(10), nullable=True)
    created_by = Column(INTEGER(unsigned=True), nullable=True)
    create_date = Column(DateTime, default=datetime.utcnow)
    modified_by = Column(INTEGER(unsigned=True), nullable=True)
    modify_date = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    super_admin = Column(Boolean, nullable=False, default=False)
    technical_admin = Column(Boolean, nullable=False, default=False)
    status = Column(Boolean, default=True)
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    permissions = relationship(
        "UserPermission", backref="user", cascade="all, delete-orphan"
    )
    organisation = relationship("Organisation", back_populates="users")

    # alias for id as user_id which is only accessible inside python
    @property
    def user_id(self):
        return self.id

    def __repr__(self):
        return f"<User {self.username} ({self.email}) StudentID {self.student_id} org_id {self.org_id}>"
