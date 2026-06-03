from fastapi import APIRouter, Depends, HTTPException, Request
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import or_
# from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta
from ...core.database import get_db
from ..models.user import User
from ..models.session import UserSession
from ..utils.jwt import decode_jwt, create_access_token, generate_tokens
from ..utils.activity_logger import log_activity
from ..auth.auth_handler import authenticate_user
from ...utils.comman_function import (
    all_masters_list, fetch_role_list, fetch_user_type, get_academics_event,
    get_academics_event_status, get_admission_type,
    get_blood_group_list_options, get_caste_list, get_category_options,
    get_certificate, get_coursetype_cia_marks, get_coursetype_list_options,
    get_coursetype_options, get_education_details, get_event_status_options,
    get_grade_type_list, get_hall_type_list, get_occupation_list,
    get_physically_challenged, check_user_type,
    get_quota, get_section_list_options, get_user_designation,
    organization_list, priority_list, religion_list
)
from ..auth.oauth import (
    get_google_access_token, get_google_user_info, get_github_access_token,
    get_github_user_info, authenticate_oauth_user
)
from ..schemas.auth import LoginSchema, TokenSchema
from ..schemas.user import UserResponse
from ..utils.session_manager import (
    create_session, is_token_blacklisted, blacklist_token,
    get_active_sessions, revoke_session
)
from ..config.settings import settings, limiter
from ..utils.response_utils import ResponseUtils

router = APIRouter(prefix="/auth", tags=["Authentication"])


# User Login (JWT Authentication)
@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    user_data: LoginSchema,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        or_(
            User.username == user_data.username,
            User.email == user_data.username
        )
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Fetch actual values using `getattr()`
    is_locked = getattr(user, "is_locked", False)
    lockout_until = getattr(user, "lockout_until", None)
    failed_attempts = getattr(user, "failed_login_attempts", 0) or 0

    # Ensure lockout_until is timezone-aware
    if lockout_until and lockout_until.tzinfo is None:
        lockout_until = lockout_until.replace(tzinfo=timezone.utc)

    # Auto-unlock if lockout period has passed
    if is_locked and lockout_until and datetime.now(
        timezone.utc
    ) >= lockout_until:
        setattr(user, "is_locked", False)
        setattr(user, "failed_login_attempts", 0)
        setattr(user, "lockout_until", None)
        db.commit()

    # Block login if user is still locked
    if is_locked:
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again after {user.lockout_until}"
        )

    # Authenticate User
    authenticated_user = authenticate_user(
        db, user_data.username, user_data.password
    )

    if not authenticated_user:
        failed_attempts += 1
        if failed_attempts >= settings.MAX_FAILED_ATTEMPTS:
            setattr(user, "is_locked", True)
            setattr(
                user, "lockout_until",
                datetime.utcnow() + settings.LOCKOUT_DURATION
            )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login: Reset failed attempts
    setattr(user, "failed_login_attempts", 0)
    setattr(user, "lockout_until", None)
    db.commit()

    tokens = generate_tokens(user)
    user_id = getattr(user, "id")
    ip_address = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")
    create_session(
        db, user_id, tokens["access_token"], tokens["refresh_token"],
        ip_address, user_agent
    )
    org_data = check_user_type(user_id, db)

    log_activity(
        db, user_id, "LOGIN", "User logged in successfully",
        ip_address, user_agent
    )

    user_res = UserResponse.model_validate(
        user
    ).model_dump()

    data = {
        **tokens, **user_res,
        "org_data": org_data,
        "options": {
            "user_type": fetch_user_type(),
            "role_list": fetch_role_list(db),
            "designations": get_user_designation(db),
            "organisations": organization_list(db),
            "all_masters_list": all_masters_list(db),
            "get_hall_type_list": get_hall_type_list(db),
            "priority_list": priority_list(db),
            "get_academics_event_status": get_academics_event_status(db),
            "get_academics_event": get_academics_event(db),
            "get_grade_type_list": get_grade_type_list(db),
            "get_coursetype_list": get_coursetype_list_options(),
            "get_coursetype_options": get_coursetype_options(),
            "get_event_status_options": get_event_status_options(),
            "get_section_list_options": get_section_list_options(db),
            "get_category_options": get_category_options(db),
            "get_religion_list": religion_list(db),
            "get_caste_list": get_caste_list(db),
            "get_quota_list": get_quota(db),
            "get_blood_group_list_options": get_blood_group_list_options(),
            "get_admission_type_list": get_admission_type(db),
            "get_occupation_list": get_occupation_list(db),
            "get_education_details_list": get_education_details(db),
            "get_physically_cha_desc_list": get_physically_challenged(db),
            "get_certificate_list": get_certificate(db),
            "get_coursetype_cia_marks": get_coursetype_cia_marks(db)
        }
    }
    return ResponseUtils.success(data, "User logged in successfully")


# Token Refresh Endpoint
@router.post("/refresh")
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    token_data: TokenSchema,
    db: Session = Depends(get_db)
):
    # token = request.headers.get("Authorization")
    token = token_data.refresh_token

    if not token:
        raise HTTPException(status_code=401, detail="Token not found.")
    # if not token or not token.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Invalid token format")

    # token = token.split(" ")[1]
    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=401, detail="Token has been revoked / blacklisted."
        )

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate the session and refresh token
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.refresh_token == token
    ).first()

    if not session:
        raise HTTPException(
            status_code=401, detail="Invalid refresh token"
        )

    expires_at = getattr(session, "expires_at")
    refresh_token = getattr(session, "refresh_token")
    access_token = getattr(session, "access_token")

    # Auto-Logout If Refresh Token Expired
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        blacklist_token(db, refresh_token)
        db.delete(session)  # Remove session from database
        db.commit()
        raise HTTPException(
            status_code=401, detail="Session expired. Please log in again."
        )

    # Blacklist old access token
    blacklist_token(db, access_token)

    # Generate new access token
    new_access_token = create_access_token({
        "sub": str(user.id), "username": user.username
    })

    # Update session with the new access token
    setattr(session, "access_token", new_access_token)

    # ADDED: Update session timestamps to keep it in sync with refresh token
    current_time = datetime.utcnow()
    setattr(session, "last_active_at", current_time)

    # Calculate new expiry based on refresh token expiry
    # This ensures session doesn't expire before refresh token
    refresh_expiry_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    new_expires_at = current_time + timedelta(days=refresh_expiry_days)
    setattr(session, "expires_at", new_expires_at)

    # Log the session refresh activity
    ip_address = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("User-Agent", "Unknown")
    log_activity(
        db, user_id, "TOKEN_REFRESH", "Session refreshed successfully",
        ip_address, user_agent
    )

    db.commit()
    return ResponseUtils.success(new_access_token)


# OAuth2 Login (Google)
@router.get("/login/google")
@limiter.limit("5/minute")
async def google_oauth_callback(
    request: Request,
    code: str, redirect_uri: str, db: Session = Depends(get_db)
):
    try:
        access_token = await get_google_access_token(code, redirect_uri)
        user_info = await get_google_user_info(access_token)
        user = authenticate_oauth_user(db, "google", user_info)
        return ResponseUtils.success(generate_tokens(user))
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        return ResponseUtils.error(f"An error occurred: {str(e)}", status_code)


# OAuth2 Login (GitHub)
@router.get("/login/github")
@limiter.limit("5/minute")
async def github_oauth_callback(
    request: Request, code: str,
    db: Session = Depends(get_db)
):
    try:
        access_token = await get_github_access_token(code)
        user_info = await get_github_user_info(access_token)
        user = authenticate_oauth_user(db, "github", user_info)
        return ResponseUtils.success(generate_tokens(user))
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        return ResponseUtils.error(f"An error occurred: {str(e)}", status_code)


@router.post("/logout")
@limiter.limit("10/minute")
def logout(request: Request, db: Session = Depends(get_db)):
    try:
        """Logs out a user by blacklisting their token."""
        token = request.headers.get("Authorization")

        if not token or not token.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Invalid or missing token"
            )

        token = token.split(" ")[1]  # Extract the actual token
        payload = decode_jwt(token)

        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = payload["sub"]

        # Blacklist token and remove session
        # blacklist_token(db, token)
        revoke_session(db, user_id, token)

        ip_address = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")
        log_activity(
            db, user_id, "LOGOUT", "User logged out successfully",
            ip_address, user_agent
        )
        return ResponseUtils.success(message="Logged out successfully")
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        return ResponseUtils.error(f"An error occurred: {str(e)}", status_code)


@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: int, db: Session = Depends(get_db)):
    try:
        """Get all active sessions for a specific user (Admin only)."""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        sessions = get_active_sessions(db, user_id)

        data = {"user_id": user_id, "active_sessions": sessions}
        return ResponseUtils.success(data)
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        return ResponseUtils.error(f"An error occurred: {str(e)}", status_code)


@router.post("/sessions/revoke/{user_id}")
def revoke_user_session(
    user_id: int, token: str, db: Session = Depends(get_db)
):
    try:
        """Revoke a specific session for a user (Admin only)."""
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.access_token == token
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # blacklist_token(db, token)
        revoke_session(db, user_id, token)

        return ResponseUtils.success(message="Session revoked successfully")
    except Exception as e:
        status_code = getattr(e, "status_code", 500)
        return ResponseUtils.error(f"An error occurred: {str(e)}", status_code)
