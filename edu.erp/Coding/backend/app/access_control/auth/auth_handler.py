from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from ...core.database import get_db
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from ..models.user import User
from ..models.user_role import UserRole
from ..utils.jwt import decode_jwt
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha1(f"{salt}{password}".encode()).hexdigest()


def verify_password(
    entered_password: str, stored_password_hash: str, stored_salt: str
) -> bool:
    entered_hash = hash_password(entered_password, stored_salt)
    return entered_hash == stored_password_hash


def authenticate_user(
     db: Session, username: str, password: str
):
    user = db.query(User).filter(
        or_(
            User.username == username,
            User.email == username
        )
    ).first()
    if not user:
        return None
    hashed_password = getattr(user, "password", None)
    stored_salt = getattr(user, "salt", None)
    if not hashed_password or not stored_salt:
        return None

    if not verify_password(password, hashed_password, stored_salt):
        return None

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Gets the current authenticated user from the token."""
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(   
            status_code=401, detail="Invalid authentication credentials"
        )

    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
