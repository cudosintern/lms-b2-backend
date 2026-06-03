from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.access_control.models.session import BlacklistedToken
from app.access_control.schemas.auth_blacklisted_tokens import BlackListedData

from ...core.database import get_db

router = APIRouter(tags=["Auth blacklisted tokens"])


@router.get("/auth-blacklisted-tokens")
def fetch_auth_blacklisted_tokens(db: Session = Depends(get_db)):
    return db.query(BlacklistedToken).all()


@router.post("/auth-blacklisted-tokens")
def post_auth_blacklisted_tokens_by_user(
    blacklist_data: BlackListedData, db: Session = Depends(get_db)
):
    new_blacklisted_data = BlacklistedToken(
        token=blacklist_data.token,
        blacklisted_at=blacklist_data.blacklisted_at
    )

    db.add(new_blacklisted_data)
    db.commit()
    return {"message": "auth blacklisted token added successfully"}


@router.put("/auth-blacklisted-tokens/{log_id}")
def update_auth_blacklisted_tokens(
    log_id: int, blacklist_data: BlackListedData, db: Session = Depends(get_db)
):
    db.query(BlacklistedToken).filter(BlacklistedToken.id == log_id).update(
        {
            BlacklistedToken.token: blacklist_data.token
        },
        synchronize_session=False,
    )

    return {"message": "auth blacklisted token updated successfully"}


@router.delete("/auth-blacklisted-tokens/{log_id}")
def delete_auth_blacklisted_tokens(log_id: int, db: Session = Depends(get_db)):
    auth_blacklisted_tokens_log = db.query(BlackListedData).filter(BlackListedData.id == log_id).first()
    if not auth_blacklisted_tokens_log:
        raise HTTPException(status_code=404, detail="auth blacklisted token not found")
    db.delete(auth_blacklisted_tokens_log)
    db.commit()
    return {"message": "auth blacklisted tokens removed successfully"}
