from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.models import IEMSDepartment, IEMProgram, IEMSAcademicBatch, IEMSemester, IEMSCourses
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException

from ...api.auth import login, register, refresh_token

from ...api.auth import login

from ...api.v1.ems_module.configurations.department import department

from ...api.v1.ems_module.comman_functions import comman_function

from app.api.v1.cudo_module.program_mode.api.program_mode_api import (
    router as program_mode_router
)


router = APIRouter()

# Include auth routes
router.include_router(login.router, prefix="/auth", tags=["auth"])
router.include_router(register.router, prefix="/auth", tags=["auth"])
router.include_router(refresh_token.router, prefix="/auth", tags=["auth"])

# Include routes for registartion module
router.include_router(login.router, prefix="/staff_student_login", tags=["auth"])

# Include routes for comman function  module
router.include_router(comman_function.router, prefix="/comman_function", tags=["auth"])

router.include_router(department.router, prefix="/department", tags=["auth"])

router.include_router(login.router, prefix="/staff_student_login", tags=["Login"])

router.include_router(
    program_mode_router, prefix="/program_mode", tags=["Program Mode"]
)

router.include_router(
    department.router, prefix="/department", tags=["EMS-configuration"]
)