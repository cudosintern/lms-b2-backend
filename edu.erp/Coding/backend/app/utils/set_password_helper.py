import hashlib
import random

def set_salt(username: str) -> str:
    salt = hashlib.md5(f"{random.randint(100000, 999999)}{username}".encode()).hexdigest()
    return salt

def set_private_password(username: str) -> dict:
    salt = set_salt(username)
    password_hash = hashlib.sha1(f"{salt}{username}".encode()).hexdigest()
    return {
        'password': password_hash,
        'salt': salt
    }


def validate_old_password(oldpassword: str, user) -> bool:
    # Validate old password using user object (from ORM)
    password_hash = hashlib.sha1(f"{user.salt}{oldpassword}".encode()).hexdigest()
    return password_hash == user.password