import httpx
from fastapi import HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from ...core.database import get_db
from ..models.user import User
from ..config.settings import settings


#  Google OAuth2 - Get Access Token
async def get_google_access_token(code: str, redirect_uri: str):
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to get Google access token"
        )
    return response.json()["access_token"]


#  Google OAuth2 - Get User Info
async def get_google_user_info(access_token: str):
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to fetch Google user info"
        )
    return response.json()


#  GitHub OAuth2 - Get Access Token
async def get_github_access_token(code: str):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to get GitHub access token"
        )
    return response.json()["access_token"]


#  GitHub OAuth2 - Get User Info
async def get_github_user_info(access_token: str):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to fetch GitHub user info"
        )
    return response.json()


#  Authenticate OAuth2 User (Google or GitHub)
def authenticate_oauth_user(
    db: Session = Depends(get_db),
    provider: Optional[str] = None,
    user_info: dict = {}
):
    if "email" not in user_info:
        raise HTTPException(
            status_code=400, detail="Email is required for authentication"
        )

    user = db.query(User).filter(
        User.email == user_info["email"]
    ).first()

    # If user does not exist, create a new user
    if not user:
        user = User(
            email=user_info["email"],
            username=user_info.get(
                "name", user_info["email"].split("@")[0]
            ),
            provider=provider
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
