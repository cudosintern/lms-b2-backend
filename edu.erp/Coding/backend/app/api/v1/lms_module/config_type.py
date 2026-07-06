from datetime import datetime
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.db.models import LMSConfigType, Base
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

try:
    LMSConfigType.__table__.create(bind=engine, checkfirst=True)
    print("Table lms_config_type verified/created successfully.")
except Exception as e:
    print("Error auto-creating table:", e)

router = APIRouter(tags=["LMS-Config Type"])

print("CONFIG TYPE LOADED")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class app_configs(BaseModel):
    config_type: str
    min_mentees: int
    max_mentees: int
    config_type_id: Optional[int] = None   # present on edit


# ---------------------------------------------------------------------------
# GET /list  ΓÇô fetch all active config types for the current org
# ---------------------------------------------------------------------------

@router.get("/list")
def list_config_type(
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    records = (
        db.query(LMSConfigType)
        .filter(LMSConfigType.org_id == org_id, LMSConfigType.status == 1)
        .order_by(LMSConfigType.id)
        .all()
    )
    data = [
        {
            "id": r.id,
            "config_type": r.config_type,
            "min_mentees": r.min_mentees,
            "max_mentees": r.max_mentees,
        }
        for r in records
    ]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# POST /save  ΓÇô create or update a config type
# ---------------------------------------------------------------------------

@router.post("/save")
def save_config_type(
    payload: app_configs,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")

    # --- Validate min/max ---
    if payload.min_mentees < 1:
        return returnException("Minimum mentees must be at least 1.")
    if payload.max_mentees < payload.min_mentees:
        return returnException("Maximum mentees cannot be less than minimum mentees.")

    # ---- UPDATE ----
    if payload.config_type_id:
        record = (
            db.query(LMSConfigType)
            .filter(
                LMSConfigType.id == payload.config_type_id,
                LMSConfigType.org_id == org_id,
                LMSConfigType.status == 1,
            )
            .first()
        )
        if not record:
            return returnException("Configuration type not found.")

        # Duplicate name check (exclude self)
        duplicate = (
            db.query(LMSConfigType)
            .filter(
                LMSConfigType.org_id == org_id,
                LMSConfigType.config_type == payload.config_type.strip(),
                LMSConfigType.status == 1,
                LMSConfigType.id != payload.config_type_id,
            )
            .first()
        )
        if duplicate:
            return returnException("Configuration type name already exists.")

        record.config_type = payload.config_type.strip()
        record.min_mentees = payload.min_mentees
        record.max_mentees = payload.max_mentees
        record.modified_by = user_id
        record.modify_date = datetime.now()
        db.commit()
        db.refresh(record)
        return returnSuccess(
            {
                "id": record.id,
                "config_type": record.config_type,
                "min_mentees": record.min_mentees,
                "max_mentees": record.max_mentees,
            },
            "Configuration type updated successfully.",
        )

    # ---- CREATE ----
    duplicate = (
        db.query(LMSConfigType)
        .filter(
            LMSConfigType.org_id == org_id,
            LMSConfigType.config_type == payload.config_type.strip(),
            LMSConfigType.status == 1,
        )
        .first()
    )
    if duplicate:
        return returnException("Configuration type name already exists.")

    new_record = LMSConfigType(
        config_type=payload.config_type.strip(),
        min_mentees=payload.min_mentees,
        max_mentees=payload.max_mentees,
        org_id=org_id,
        status=1,
        created_by=user_id,
        create_date=datetime.now(),
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return returnSuccess(
        {
            "id": new_record.id,
            "config_type": new_record.config_type,
            "min_mentees": new_record.min_mentees,
            "max_mentees": new_record.max_mentees,
        },
        "Configuration type saved successfully.",
    )


# ---------------------------------------------------------------------------
# PUT /update/{id}  ΓÇô update an existing config type
# ---------------------------------------------------------------------------

class UpdateConfigType(BaseModel):
    config_type: str
    min_mentees: int
    max_mentees: int


@router.put("/update/{id}")
def update_config_type(
    id: int,
    payload: UpdateConfigType,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")

    # --- Validate min/max ---
    if payload.min_mentees < 1:
        return returnException("Minimum mentees must be at least 1.")
    if payload.max_mentees < payload.min_mentees:
        return returnException("Maximum mentees cannot be less than minimum mentees.")

    # --- Fetch record ---
    record = (
        db.query(LMSConfigType)
        .filter(
            LMSConfigType.id == id,
            LMSConfigType.org_id == org_id,
            LMSConfigType.status == 1,
        )
        .first()
    )
    if not record:
        return returnException("Configuration type not found.")

    # --- Duplicate name check (exclude self) ---
    duplicate = (
        db.query(LMSConfigType)
        .filter(
            LMSConfigType.org_id == org_id,
            LMSConfigType.config_type == payload.config_type.strip(),
            LMSConfigType.status == 1,
            LMSConfigType.id != id,
        )
        .first()
    )
    if duplicate:
        return returnException("Configuration type name already exists.")

    record.config_type = payload.config_type.strip()
    record.min_mentees = payload.min_mentees
    record.max_mentees = payload.max_mentees
    record.modified_by = user_id
    record.modify_date = datetime.now()
    db.commit()
    db.refresh(record)
    return returnSuccess(
        {
            "id": record.id,
            "config_type": record.config_type,
            "min_mentees": record.min_mentees,
            "max_mentees": record.max_mentees,
        },
        "Configuration type updated successfully.",
    )


# ---------------------------------------------------------------------------
# DELETE /delete/{id}  ΓÇô soft delete
# ---------------------------------------------------------------------------

@router.delete("/delete/{id}")
def delete_config_type(
    id: int,
    current_user: dict = Depends(get_current_user),
    org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    record = (
        db.query(LMSConfigType)
        .filter(
            LMSConfigType.id == id,
            LMSConfigType.org_id == org_id,
            LMSConfigType.status == 1,
        )
        .first()
    )
    if not record:
        return returnException("Configuration type not found.")

    record.status = 0
    record.modified_by = user_id
    record.modify_date = datetime.now()
    db.commit()
    return returnSuccess({"id": id}, "Configuration type deleted successfully.")
