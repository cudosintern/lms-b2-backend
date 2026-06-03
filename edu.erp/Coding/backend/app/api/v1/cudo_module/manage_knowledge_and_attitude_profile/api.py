from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.db.models import CudosProgramKnowledgeProfile
from app.api.v1.cudo_module.manage_knowledge_and_attitude_profile.schema import (
    ProgramKPCreate,
    ProgramKPUpdate
)
from app.utils.http_return_helper import returnSuccess, returnException

router = APIRouter()

@router.post("/create")
def create_program_kp(payload: ProgramKPCreate, db: Session = Depends(get_db)):
    kp = CudosProgramKnowledgeProfile(
        pgm_id=payload.pgm_id,
        pkp_attr_code=payload.pkp_attr_code,
        pkp_attr_description=payload.pkp_attr_description,
        created_by=payload.created_by,
        created_date=date.today()
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return returnSuccess(kp)

@router.get("/list/{pgm_id}")
def list_program_kps(pgm_id: int, db: Session = Depends(get_db)):
    kps = db.query(CudosProgramKnowledgeProfile).filter(
        CudosProgramKnowledgeProfile.pgm_id == pgm_id
    ).all()

    return returnSuccess(kps)

@router.put("/update/{pkp_id}")
def update_program_kp(
    pkp_id: int,
    payload: ProgramKPUpdate,
    db: Session = Depends(get_db)
):
    kp = db.query(CudosProgramKnowledgeProfile).filter(
        CudosProgramKnowledgeProfile.pkp_id == pkp_id
    ).first()

    if not kp:
        return returnException("Knowledge Profile not found")

    kp.pkp_attr_code = payload.pkp_attr_code
    kp.pkp_attr_description = payload.pkp_attr_description
    kp.modified_by = payload.modified_by
    kp.modified_date = date.today()

    db.commit()
    return returnSuccess("Knowledge Profile updated successfully")

@router.delete("/delete/{pkp_id}")
def delete_program_kp(pkp_id: int, db: Session = Depends(get_db)):
    kp = db.query(CudosProgramKnowledgeProfile).filter(
        CudosProgramKnowledgeProfile.pkp_id == pkp_id
    ).first()

    if not kp:
        return returnException("Knowledge Profile not found")

    db.delete(kp)
    db.commit()
    return returnSuccess("Knowledge Profile deleted successfully")
