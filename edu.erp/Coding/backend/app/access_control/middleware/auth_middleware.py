from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Callable, Optional
from ...core.database import get_db
from ...core.database import SessionLocal
from ..utils.session_manager import is_token_blacklisted
from ..models.session import UserSession
from ..models.user import User
from ..models.module_route import ModuleRoute
from ..utils.permissions import has_role_permission, has_direct_permission, has_role
from ..auth.auth_handler import decode_jwt
from ..config.settings import settings
import logging
import re

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

security = HTTPBearer()

# Define public URLs that do NOT require authentication
PUBLIC_URLS = [
    "/",
    "/favicon.ico",
    # "/uploads/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/oauth/google",
    "/api/v1/auth/oauth/github",
    "/manage_students_router/register",
    "/manage_students_router/occupations",
    "/api/admissions/students/get_student_details",
    "/api/admissions/students/api/students/import_student_details",
    "/api/students/import_student_details",
    # "api/students/import_student_details",
    # "/api/students/import_student_details",
    "/dvs_integration/get_exam_event_data",
    "/dvs_integration/get_student_course_data",
    "/dvs_integration/user_designation_data",
]


class RBACBypass:
    def __init__(self):
        self.exempt_routes = set()

    def exempt(self, path: str):
        """Decorator to mark a route as RBAC-exempt."""

        def decorator(func: Callable):
            self.exempt_routes.add(path)
            return func

        return decorator

    def is_exempt(self, request: Request) -> bool:
        """Check if the request path is exempt from RBAC."""
        return request.url.path in self.exempt_routes


rbac_bypass = RBACBypass()


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, public_urls: Optional[list] = None):
        super().__init__(app)
        self.public_urls = public_urls or PUBLIC_URLS

    async def dispatch(self, request: Request, call_next) -> Response:
        db = SessionLocal()
        try:
            # Bypass token check for OPTIONS
            if request.method == "OPTIONS" or self._is_public_url(request):
                return await call_next(request)

            # Extract JWT token from headers
            token = request.headers.get("Authorization")
            if not token or not token.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Authentication required")

            token = token.split(" ")[1]

            payload = decode_jwt(token)
            if not payload or "sub" not in payload:
                raise HTTPException(status_code=401, detail="Invalid token")

            # # Check if token is blacklisted
            if is_token_blacklisted(db, token):
                raise HTTPException(status_code=401, detail="Token has been revoked.")

            user = db.query(User).filter(User.id == payload["sub"]).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            await self.validate_session(db, request, token, payload["sub"])

            if rbac_bypass.is_exempt(request):
                return await call_next(request)

            await self.enforce_role_permissions(db, request, payload["sub"])

            response = await call_next(request)
            # db.close() if hasattr(db, "close") else None
            return response
        finally:
            db.close()

    def _is_public_url(self, request: Request) -> bool:
        """Check if the requested URL is in the public URLs list."""
        base_path = request.scope.get("root_path", "").rstrip("/")
        full_path = request.url.path
        normal_path = full_path[len(base_path) :] if base_path else full_path

        # Exact match
        if (
            normal_path in self.public_urls
            or normal_path.strip("/") in self.public_urls
        ):
            return True

        # Allow static files or media from /uploads/
        if normal_path.startswith("/uploads/"):
            return True

        return False

    async def validate_session(
        self, db: Session, request: Request, token: str, user_id: int
    ):
        """🔍 Validates user session, auto-logs out if needed."""
        session = (
            db.query(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.access_token == token)
            .first()
        )

        if not session:
            raise HTTPException(status_code=401, detail="Session expired/invalid.")

        ip_address = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")

        session_ip = getattr(session, "ip_address", None)
        session_ua = getattr(session, "user_agent", None)
        last_active = getattr(session, "last_active_at", None)
        expires_at = getattr(session, "expires_at", None)

        # Auto Logout After Inactivity (30 min)
        inactivity = timedelta(minutes=settings.INACTIVITY_EXPIRY_MINUTES)
        if last_active and datetime.utcnow() - last_active > inactivity:
            db.delete(session)
            db.commit()
            raise HTTPException(
                status_code=401, detail="Session expired due to inactivity."
            )

        # Prevent Session Hijacking
        if session_ip != ip_address or session_ua != user_agent:
            db.delete(session)
            db.commit()
            raise HTTPException(
                status_code=401, detail="Session terminated due to security violation."
            )

        if expires_at and datetime.utcnow() > expires_at:
            db.delete(session)
            db.commit()
            raise HTTPException(
                status_code=401, detail="Session expired. Please log in again."
            )

        setattr(session, "last_active_at", datetime.utcnow())
        db.commit()

    async def enforce_role_permissions(
        self, db: Session, request: Request, user_id: int
    ) -> None:
        """Middleware to enforce role-based access for both modules & menus."""
        base_path = request.scope.get("root_path", "").rstrip("/")

        # Compute the full path
        full_path = request.url.path
        method = request.method
        route_path = full_path[len(base_path) :] if base_path else full_path
        route_path = re.sub(r"/{2,}", "/", route_path.strip("/"))
        route_path = "/" + route_path

        # Find route in module routes (exact or pattern match)
        module_route = (
            db.query(ModuleRoute)
            .filter(
                func.lower(ModuleRoute.route_path) == route_path.lower(),
                ModuleRoute.method == method,
                ModuleRoute.status == 1,
            )
            .first()
        )

        if not module_route:
            # Try pattern matching for dynamic routes
            partial_path = "/" + route_path.strip("/").split("/")[0] + "/"
            all_routes = (
                db.query(ModuleRoute)
                .filter(
                    ModuleRoute.status == 1,
                    ModuleRoute.method == method,
                    ModuleRoute.route_path.like(f"{partial_path}%"),
                )
                .all()
            )

            for route in all_routes:
                # Cast to str to avoid lint issues
                route_pattern = str(route.route_path)
                # Replace {param} with regex to match any non-slash part
                pattern = re.sub(r"\{[^/]+\}", r"[^/]+", route_pattern)
                # Now escape special regex characters EXCEPT for `[^/]+`
                pattern = re.escape(pattern)
                # Restore the dynamic part
                pattern = pattern.replace(re.escape("[^/]+"), "[^/]+")
                # Anchor the regex to ensure it matches the full path
                pattern = f"^{pattern}$"

                if re.fullmatch(pattern, route_path):
                    module_route = route
                    break

        if not module_route:
            raise HTTPException(
                status_code=403, detail="Route not registered under any module."
            )

        module_id = getattr(module_route, "module_id", None)
        route_id = getattr(module_route, "route_id", None)
        if not module_id or not route_id:
            raise HTTPException(
                status_code=403, detail="Invalid module or route reference."
            )

        # Check direct user permission
        if has_direct_permission(db, user_id, route_id):
            return

        # Check role-based permission
        if has_role_permission(db, user_id, route_id):
            return

        raise HTTPException(
            status_code=403, detail="Access denied: insufficient permissions."
        )


async def authorize(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = decode_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == payload["sub"]).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # this will return user data along with user roles
    # user_data = UserResponse.model_validate(user).model_dump()

    # await self.validate_session(db, request, token, payload["sub"])

    return user


def role_required(*roles: str):
    def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
    ):
        token = credentials.credentials
        payload = decode_jwt(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check if user has the required role
        if not has_role(db, user_id, roles):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {roles}",
            )

        return True

    return dependency
