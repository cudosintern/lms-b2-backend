from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

security = HTTPBearer()

# ---------------- CREATE TOKEN ----------------
def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=5)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ---------------- VERIFY TOKEN ----------------
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

