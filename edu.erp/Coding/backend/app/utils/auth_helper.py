from typing import Optional
from fastapi import HTTPException,Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from fastapi import Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..db.models import IEMSUsers
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from Crypto.Cipher import AES
import base64
import hashlib
from Crypto.Util.Padding import unpad


import os
from dotenv import load_dotenv
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
# ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# def decrypted_values(encrypted_value: str, secret_key: str) -> str:
#     # Decode the base64 encoded string
#     encrypted_data = base64.b64decode(encrypted_value)
#     # Ensure the key length matches AES requirements
#     padded_key = pad_key(secret_key)
#     # Create AES cipher using EAX mode with the nonce extracted from the encrypted data
#     cipher = AES.new(padded_key, AES.MODE_EAX, nonce=encrypted_data[:16])
#     # Decrypt the data (excluding the nonce)
#     decrypted_data = cipher.decrypt(encrypted_data[16:])
#     # Assuming you had used padding while encrypting, unpad the decrypted data
#     try:
#         decrypted_data = unpad(decrypted_data, AES.block_size)
#     except ValueError as e:
#         raise ValueError("Decryption failed: Incorrect padding") from e
#     # Convert bytes back to UTF-8 string
#     return decrypted_data.decode('utf-8')


# Function to pad the key to be 16 bytes for AES
# def pad_key(key):
#     return hashlib.sha256(key.encode()).digest()

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db), org_id: Optional[int] = Header(None)):
    try:
        is_auth_required = False
        if is_auth_required:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("username")
            first_name: str = payload.get("first_name")
            last_name: str = payload.get("last_name")
            user_id: int = payload.get("id")
            user_type: str = payload.get("user_type")
            super_admin: bool = payload.get("super_admin")
            technical_admin: bool = payload.get("technical_admin")
            status: int = payload.get("status")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")

            user = db.query(IEMSUsers).filter(IEMSUsers.username == username).first()
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")

            if org_id is None:
                raise HTTPException(status_code=400, detail="Organization ID header is required")
            
            # decrypted_org_id = decrypted_values(org_id, ENCRYPTION_KEY)
            # if not decrypted_org_id:  # Handle the case where decryption fails
            #     raise HTTPException(status_code=400, detail="Incorrect organization ID")
            
            
            return {
                "token": token,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user_id,
                "org_id": org_id,
                "user_type": user_type,
                "super_admin": super_admin,
                "technical_admin": technical_admin,
                "status": status
            }
        else:
            # return None
            return {
                "token": 'token',
                "username": 'test',
                "first_name": 'Coe',
                "last_name": 'staff',
                "user_id": 1,
                "org_id": 1,
                "user_type": 'U',
                "super_admin": True,
                "technical_admin": False,
                "status": True
            }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
