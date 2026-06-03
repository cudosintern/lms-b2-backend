from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.access_control.models.common_models import University
from app.access_control.schemas.university import (
    UniversityCreate,
    UniversityResponce,
    UniversityUpdate,
)


from ...core.database import get_db

router = APIRouter(prefix="/universities", tags=["Universities"])


@router.post("/", response_model=UniversityResponce)
def create_university(unv: UniversityCreate, db: Session = Depends(get_db)):
    db_unv = University(**unv.dict())
    db.add(db_unv)
    db.commit()
    db.refresh(db_unv)
    return db_unv


@router.get("/", response_model=List[UniversityResponce])
def get_universities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(University).offset(skip).limit(limit).all()


@router.get("/{unv_id}", response_model=UniversityResponce)
def get_university(unv_id: int, db: Session = Depends(get_db)):
    unv = db.query(University).filter(University.unv_id == unv_id).first()
    if not unv:
        raise HTTPException(status_code=404, detail="University not found")
    return unv


@router.put("/{unv_id}", response_model=UniversityResponce)
def update_university(
    unv_id: int, unv_data: UniversityUpdate, db: Session = Depends(get_db)
):
    unv = db.query(University).filter(University.unv_id == unv_id).first()
    if not unv:
        raise HTTPException(status_code=404, detail="University not found")
    for key, value in unv_data.dict(exclude_unset=True).items():
        setattr(unv, key, value)
    db.commit()
    db.refresh(unv)
    return unv


@router.delete("/{unv_id}")
def delete_university(unv_id: int, db: Session = Depends(get_db)):
    unv = db.query(University).filter(University.unv_id == unv_id).first()
    if not unv:
        raise HTTPException(status_code=404, detail="University not found")
    db.delete(unv)
    db.commit()
    return {"message": "University deleted successfully"}
