from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.access_control.models.session import UserSession
from app.access_control.schemas.user_sessions import SessionCreate, SessionOut, SessionUpdate
from app.core.database import get_db

router = APIRouter(prefix="/sessions", tags=["user sessions"])


@router.post("/", response_model=SessionOut)
def create(session: SessionCreate, db: Session = Depends(get_db)):
    return create_session(db, session)


@router.get("/{session_id}", response_model=SessionOut)
def read(session_id: int, db: Session = Depends(get_db)):
    db_session = get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.get("/", response_model=list[SessionOut])
def read_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_sessions(db, skip, limit)


@router.put("/{session_id}", response_model=SessionOut)
def update(session_id: int, session: SessionUpdate, db: Session = Depends(get_db)):
    updated = update_session(db, session_id, session)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.delete("/{session_id}", response_model=SessionOut)
def delete(session_id: int, db: Session = Depends(get_db)):
    deleted = delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return deleted


def create_session(db: Session, session: SessionCreate):
    db_session = UserSession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: int):
    return (
        db.query(UserSession).filter(UserSession.id == session_id).first()
    )


def get_sessions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UserSession).offset(skip).limit(limit).all()


def update_session(db: Session, session_id: int, session_update: SessionUpdate):
    db_session = (
        db.query(UserSession).filter(UserSession.id == session_id).first()
    )
    if not db_session:
        return None
    for key, value in session_update.dict(exclude_unset=True).items():
        setattr(db_session, key, value)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_session(db: Session, session_id: int):
    db_session = (
        db.query(UserSession).filter(UserSession.id == session_id).first()
    )
    if db_session:
        db.delete(db_session)
        db.commit()
    return db_session
