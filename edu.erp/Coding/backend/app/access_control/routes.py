from fastapi import APIRouter

from app.access_control.api.auth import router as auth_router
from app.access_control.api.users import router as user_router
from app.access_control.api.activity_log import router as activity_log_router
from app.access_control.api.auth_blacklisted_tokens import (
    router as auth_blacklisted_tokens_router,
)
from app.access_control.api.module_routes import router as module_routes
from app.access_control.api.modules import router as modules
from app.access_control.api.organisation import router as organisation
from app.access_control.api.organisation_type import (
    router as organisation_type
)
from app.access_control.api.role_menu import router as role_menu
from app.access_control.api.university import router as university
from app.access_control.api.user_permissions import router as user_permissions
from app.access_control.api.menus import router as menus
from app.access_control.api.roles import router as roles
from app.access_control.api.user_sessions import router as user_sessions
from app.access_control.api.user_role_permissions import (
    router as user_role_permissions
)
from app.access_control.api.user_roles import router as user_roles
from app.access_control.api.permissions import router as permissions

# from app.access_control.middleware.auth_middleware import authorize

router = APIRouter(
    # dependencies=[Depends(authorize)]
)

router.include_router(auth_router, prefix="/api/v1")
router.include_router(modules)
router.include_router(menus)
router.include_router(roles)
router.include_router(user_roles)
router.include_router(user_role_permissions)
router.include_router(user_router)
router.include_router(activity_log_router)
router.include_router(auth_blacklisted_tokens_router)
router.include_router(module_routes)
router.include_router(organisation)
router.include_router(organisation_type)
router.include_router(role_menu)
router.include_router(university)
router.include_router(user_permissions)
router.include_router(user_sessions)
router.include_router(permissions)
