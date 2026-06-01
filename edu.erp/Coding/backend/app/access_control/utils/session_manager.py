from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from ..models.session import UserSession, BlacklistedToken
from ..config.settings import settings


def create_session(
    db: Session, user_id: int, access_token: str, refresh_token: str,
    ip_address: str, user_agent: str
):
    # Fetch active sessions for the user
    user_sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).order_by(UserSession.created_at).all()

    # If max session limit exceeded, remove the oldest session
    if len(user_sessions) >= settings.MAX_SESSIONS:
        db.delete(user_sessions[0])  # Deletes the oldest session

    # Set session expiration
    expiry_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.SESSION_EXPIRY_MINUTES
    )
    session = UserSession(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        created_at=datetime.utcnow(),
        expires_at=expiry_time,
        last_active_at=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def blacklist_token(db: Session, token: str):
    """Blacklist a token to prevent reuse."""
    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    db.commit()


def is_token_blacklisted(db: Session, token: str) -> bool:
    """Check if a token is blacklisted."""
    if not isinstance(db, Session):
        raise ValueError(
            "Invalid database session passed to is_token_blacklisted"
        )

    return db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first() is not None


def get_active_sessions(db: Session, user_id: int):
    """Get all active sessions for a user."""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id
    ).all()
    return [{
        "access_token": s.access_token, "created_at": s.created_at,
        "expires_at": s.expires_at
    } for s in sessions]


def revoke_session(db: Session, user_id: int, token: str):
    """Remove a session & blacklist the token."""
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.access_token == token
    ).first()

    if session:
        db.delete(session)
        db.commit()

    # Blacklist the token so it cannot be used again
    blacklist_token(db, token)
