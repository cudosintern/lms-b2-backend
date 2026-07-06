from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from io import BytesIO
from fpdf import FPDF
from pydantic import BaseModel

class ConfigTypeCreate(BaseModel):
    name: str
    status: int = 1
    min_mentees: int | None = None
    max_mentees: int | None = None

class ConfigTypeUpdate(BaseModel):
    name: str | None = None
    status: int | None = None
    min_mentees: int | None = None
    max_mentees: int | None = None

from app.core.database import get_db
from app.db.models import ConfigType
from app.utils.auth_helper import get_current_user

# Set prefix to empty string to avoid nesting conflict with main.py's prefix="/api/v1/config-type"
router = APIRouter(prefix="", tags=["Config Type"])

print("CONFIG TYPE LOADED")

# ---------------- LIST ----------------
@router.get("/")
def list_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    configs = db.query(ConfigType).all()
    result = []
    for c in configs:
        result.append({
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "created_at": c.created_at,
            "min_mentees": c.min_mentees,
            "max_mentees": c.max_mentees
        })
    return {"status": "success", "data": result}


# ---------------- ADD ----------------
@router.post("/")
def add_config(
    payload: ConfigTypeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    name = payload.name
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required"
        )
    
    name_clean = name.strip()
    status_val = payload.status

    # Check for duplicate
    duplicate = db.query(ConfigType).filter(ConfigType.name == name_clean).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate Config Type"
        )

    new_config = ConfigType(name=name_clean, status=status_val)
    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return {
        "status": "success",
        "message": "Created successfully",
        "data": {
            "id": new_config.id,
            "name": new_config.name,
            "status": new_config.status
        }
    }


# ---------------- UPDATE ----------------
@router.put("/{id}")
def update_config(
    id: int,
    payload: ConfigTypeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    config = db.query(ConfigType).filter(ConfigType.id == id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config Type not found"
        )

    name = payload.name
    if name is not None:
        name_clean = name.strip()
        if not name_clean:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name cannot be empty"
            )
        
        # Check if name is taken by another entry
        duplicate = db.query(ConfigType).filter(
            ConfigType.name == name_clean,
            ConfigType.id != id
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate Config Type"
            )
        config.name = name_clean

    if payload.status is not None:
        config.status = payload.status

    db.commit()
    db.refresh(config)

    return {
        "status": "success",
        "message": f"Updated {id} successfully",
        "data": {
            "id": config.id,
            "name": config.name,
            "status": config.status
        }
    }


# ---------------- DELETE ----------------
@router.delete("/{id}")
def delete_config(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    config = db.query(ConfigType).filter(ConfigType.id == id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config Type not found"
        )

    db.delete(config)
    db.commit()

    return {
        "status": "success",
        "message": f"Deleted {id} successfully"
    }


class ConfigTypePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Configuration Type Report', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# ---------------- PDF ----------------
@router.get("/export-pdf")
def export_pdf(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    configs = db.query(ConfigType).all()
    
    pdf = ConfigTypePDF()
    pdf.add_page()
    
    # Table headers
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(30, 10, 'ID', 1, 0, 'C')
    pdf.cell(100, 10, 'Config Type Name', 1, 0, 'L')
    pdf.cell(40, 10, 'Status', 1, 0, 'C')
    pdf.ln()
    
    # Table rows
    pdf.set_font('Arial', '', 10)
    for c in configs:
        status_text = "Active" if c.status == 1 else "Inactive"
        pdf.cell(30, 10, str(c.id), 1, 0, 'C')
        pdf.cell(100, 10, str(c.name), 1, 0, 'L')
        pdf.cell(40, 10, status_text, 1, 0, 'C')
        pdf.ln()
        
    pdf_content = pdf.output(dest='S').encode('latin1')
    stream = BytesIO(pdf_content)
    
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Config_Type_Report.pdf"}
    )