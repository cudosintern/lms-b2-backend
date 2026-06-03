from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.models import IEMSProgramMode
from app.api.v1.cudo_module.program_mode.schema.program_mode_schema import ProgramModeInDB, CreateProgramMode, UpdateProgramMode
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException

router = APIRouter(
    tags=["Program Mode"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/")
def add_program_mode(
    program_mode: CreateProgramMode,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Use name as code since user didn't provide code and it is required
        code = program_mode.program_mode_name.upper().replace(" ", "_")[:50]
        
        new_program_mode = IEMSProgramMode(
            prg_mode_name=program_mode.program_mode_name,
            prg_mode_desc=program_mode.description if program_mode.description else "", # DB says Not Null
            prg_mode_code=code,
            status=1
        )
        
        db.add(new_program_mode)
        db.commit()
        db.refresh(new_program_mode)
        
        response_data = ProgramModeInDB.from_orm(new_program_mode).dict()
        return returnSuccess(response_data, message="Program Mode created successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Program Mode: {str(e)}")

@router.put("/{program_mode_id}")
def edit_program_mode(
    program_mode_id: int,
    program_mode: UpdateProgramMode,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        db_program_mode = db.query(IEMSProgramMode).filter(IEMSProgramMode.prg_mode_id == program_mode_id).first()
        
        if not db_program_mode:
            return returnException("Program Mode not found")
            
        if program_mode.program_mode_name is not None:
            db_program_mode.prg_mode_name = program_mode.program_mode_name
            # Also update code?
            db_program_mode.prg_mode_code = program_mode.program_mode_name.upper().replace(" ", "_")[:50]
            
        if program_mode.description is not None:
            db_program_mode.prg_mode_desc = program_mode.description
            
        db.commit()
        db.refresh(db_program_mode)
        
        response_data = ProgramModeInDB.from_orm(db_program_mode).dict()
        return returnSuccess(response_data, message="Program Mode updated successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Program Mode: {str(e)}")

@router.delete("/{program_mode_id}")
def delete_program_mode(
    program_mode_id: int,
    db: Session = Depends(get_db)
):
    try:
        program_mode = db.query(IEMSProgramMode).filter(IEMSProgramMode.prg_mode_id == program_mode_id).first()
        
        if not program_mode:
            return returnException("Program Mode not found")
            
        # Hard delete as per previous logic decision
        db.delete(program_mode)
        db.commit()
        
        return returnSuccess(None, message="Program Mode deleted successfully")
    except Exception as e:
        db.rollback()
        return returnException(f"Error deleting Program Mode: {str(e)}")

@router.get("/")
def get_all_program_modes(db: Session = Depends(get_db)):
    try:
        program_modes = db.query(IEMSProgramMode).all()
        data = [ProgramModeInDB.from_orm(pm).dict() for pm in program_modes]
        return returnSuccess(data)
    except Exception as e:
        return returnException(f"Error fetching Program Modes: {str(e)}")

@router.get("/{program_mode_id}")
def get_program_mode_by_id(program_mode_id: int, db: Session = Depends(get_db)):
    try:
        program_mode = db.query(IEMSProgramMode).filter(IEMSProgramMode.prg_mode_id == program_mode_id).first()
        if not program_mode:
            return returnException("Program Mode not found")
        
        response_data = ProgramModeInDB.from_orm(program_mode).dict()
        return returnSuccess(response_data)
    except Exception as e:
        return returnException(f"Error fetching Program Mode: {str(e)}")
