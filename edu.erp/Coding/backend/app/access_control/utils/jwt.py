from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta, timezone
from ..config.settings import settings

# Load JWT settings from config
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


# Function to create an access token
def create_access_token(
    data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """Generates a JWT access token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


# Function to create a refresh token
def create_refresh_token(
    data: dict, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS
) -> str:
    """Generates a JWT refresh token with a longer expiration time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_delta)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def generate_tokens(user):
    """Generate access & refresh tokens for authenticated user."""
    user_data = {
        "sub": str(user.id), "username": user.username
    }
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# Function to decode and verify a JWT token
# def decode_jwt(token: str, db: Session = Depends(get_db)) -> dict:
def decode_jwt(
    token: str
) -> dict:
    """Decodes a JWT token and validates expiration & blacklisting."""
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Extract expiration time
        exp = payload.get("exp")
        if not exp:
            raise HTTPException(
                status_code=401,
                detail="Invalid token format."
            )

        # Validate expiration
        if datetime.now(timezone.utc) > datetime.fromtimestamp(
            exp, tz=timezone.utc
        ):
            raise HTTPException(
                status_code=401,
                detail="Access token expired. Please refresh your token."
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Access token expired. Please refresh your token."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token. Please log in again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token validation failed: {str(e)}"
        )
