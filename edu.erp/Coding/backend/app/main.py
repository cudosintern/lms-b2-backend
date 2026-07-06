from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# -------------------- ROUTERS --------------------
from .api.v1.routes import router as api_router
from .api.v1.lms_module.department import router as department_router
from .api.v1.lms_module.config_type import router as config_type_router
from .api.v1.cudo_module.bloom_level.bloom_level import router as bloom_level_router
from .api.v1.cudo_module.curriculum.curriculum_list import router as curriculum_list_router
from .api.v1.lms_module.department_configuration import router as cross_dept_router
from .api.v1.lms_module.mentoring import router as mentoring_router
from .api.v1.lms_module.mentoring_session import router as mentoring_session_router
from .api.v1.lms_module.mentor_list import router as mentor_list_router
from .api.v1.lms_module.mentor_mentee_details import router as mentor_mentee_details_router
from .api.v1.lms_module.student_details import router as student_details_router
# Access control routers
from .access_control.api.activity_log import router as activity_log_router
from .access_control.api.auth import router as auth_router
from .access_control.api.auth_blacklisted_tokens import router as auth_blacklisted_tokens_router
from .access_control.api.menus import router as menus_router
from .access_control.api.module_routes import router as module_routes_router
from .access_control.api.modules import router as modules_router
from .access_control.api.organisation import router as organisation_router
from .access_control.api.organisation_type import router as organisation_type_router
from .access_control.api.permissions import router as permissions_router
from .access_control.api.role_menu import router as role_menu_router
from .access_control.api.roles import router as roles_router
from .access_control.api.university import router as university_router
from .access_control.api.user_permissions import router as user_permissions_router
from .access_control.api.user_role_permissions import router as user_role_permissions_router
from .access_control.api.user_roles import router as user_roles_router
from .access_control.api.user_sessions import router as user_sessions_router
from .access_control.api.users import router as users_router

# -------------------- DB --------------------
from .core.database import get_db

app = FastAPI(
    title="LMS API",
    version="1.0.0"
)

# -------------------- CORS --------------------
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTER REGISTRATION --------------------

app.include_router(api_router, prefix="/api/v1", tags=["Common APIs"])

app.include_router(
    department_router,
    prefix="/api/v1/department",
    tags=["Department"]
)

app.include_router(
    config_type_router,
    prefix="/api/v1/config-type",
    tags=["Config Type"]
)

app.include_router(
    bloom_level_router,
    prefix="/api/v1/cudo-module",
    tags=["Bloom Level"]
)

app.include_router(
    curriculum_list_router,
    prefix="/api/v1/curriculum",
    tags=["Curriculum List"]
)

app.include_router(
    cross_dept_router,
    prefix="/api/v1/cross-mentor",
    tags=["Cross Department Mentor"]
)

app.include_router(
    mentoring_router,
    prefix="/api/v1/mentoring",
    tags=["Mentoring"]
)

app.include_router(
    mentoring_session_router,
    prefix="/api/v1/mentoring-sessions",
    tags=["Mentoring Session"]
)

app.include_router(
    mentor_list_router,
    prefix="/api/v1/mentor-list",
    tags=["Mentor List"]
)

app.include_router(
    mentor_mentee_details_router,
    prefix="/api/v1/mentor-mentee-details",
    tags=["Mentor Mentee Details"]
)

app.include_router(
    student_details_router,
    prefix="/api/v1/student-details",
    tags=["MMP Report"]
)
# Access control router registrations
app.include_router(activity_log_router, prefix="/api/v1/activity-log", tags=["Activity Log"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(auth_blacklisted_tokens_router, prefix="/api/v1/auth-blacklisted-tokens", tags=["Auth Blacklisted Tokens"])
app.include_router(menus_router, prefix="/api/v1/menus", tags=["Menus"])
app.include_router(module_routes_router, prefix="/api/v1/module-routes", tags=["Module Routes"])
app.include_router(modules_router, prefix="/api/v1/modules", tags=["Modules"])
app.include_router(organisation_router, prefix="/api/v1/organisation", tags=["Organisation"])
app.include_router(organisation_type_router, prefix="/api/v1/organisation-type", tags=["Organisation Type"])
app.include_router(permissions_router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(role_menu_router, prefix="/api/v1/role-menus", tags=["Role Menus"])
app.include_router(roles_router, prefix="/api/v1/roles", tags=["Roles"])
app.include_router(university_router, prefix="/api/v1/universities", tags=["Universities"])
app.include_router(user_permissions_router, prefix="/api/v1/user-permissions", tags=["User Permissions"])
app.include_router(user_role_permissions_router, prefix="/api/v1/user-role-permissions", tags=["User Role Permissions"])
app.include_router(user_roles_router, prefix="/api/v1/user-roles", tags=["User Roles"])
app.include_router(user_sessions_router, prefix="/api/v1/sessions", tags=["User Sessions"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])

# -------------------- HEALTH CHECK --------------------
@app.get("/")
def root():
    return {"message": "LMS Backend is running 🚀"}

@app.get("/db-test")
def db_test(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "database connected 🚀"}
    except Exception as e:
        return {"status": "error", "message": str(e)}