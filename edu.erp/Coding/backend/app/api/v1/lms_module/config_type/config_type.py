from datetime import datetime
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.db.models import LMSConfigType, Base
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess
from app.api.v1.lms_module.config_type.config_type_schema import *

try:
    LMSConfigType.__table__.create(bind=engine, checkfirst=True)
    print("Table lms_config_type verified/created successfully.")
except Exception as e:
    print("Error auto-creating table:", e)

router = APIRouter(tags=["LMS-Config Type"])

print("CONFIG TYPE LOADED")


# ---------------------------------------------------------------------------
# GET /list – fetch all active config types for the current org
# ---------------------------------------------------------------------------

@router.get("/list")
def list_config_type(
    current_user: dict = Depends(get_current_user),
    # org_id: int = Header(...),
    db: Session = Depends(get_db),
):
    records = (
        db.query(LMSConfigType)
        # .filter(LMSConfigType.org_id == org_id, LMSConfigType.status == 1)
        .order_by(LMSConfigType.config_type_id)
        .all()
    )
    data = [
        {
            "config_type_id": r.config_type_id,
            "config_type_name": r.config_type_name,
            "min_mentees": r.min_mentees,
            "max_mentees": r.max_mentees,
        }
        for r in records
    ]
    return returnSuccess(data)


# ---------------------------------------------------------------------------
# POST /save – create or update a config type
# ---------------------------------------------------------------------------

@router.post("/save")
def save_config_type(
    payload: app_configs,
    current_user: dict = Depends(get_current_user),
    # org_id: int = Header(...),
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
                LMSConfigType.config_type_id == payload.config_type_id,
                # LMSConfigType.org_id == org_id,
                # LMSConfigType.status == 1,
            )
            .first()
        )
        if not record:
            return returnException("Configuration type not found.")

        # Duplicate name check (exclude self)
        duplicate = (
            db.query(LMSConfigType)
            .filter(
                # LMSConfigType.org_id == org_id,
                LMSConfigType.config_type_name == payload.config_type_name.strip(),
                # LMSConfigType.status == 1,
                LMSConfigType.config_type_id != payload.config_type_id,
            )
            .first()
        )
        if duplicate:
            return returnException("Configuration type name already exists.")

        record.config_type_name = payload.config_type_name.strip()
        record.min_mentees = payload.min_mentees
        record.max_mentees = payload.max_mentees
        record.modified_by = user_id
        record.modified_date = datetime.now()
        db.commit()
        db.refresh(record)
        return returnSuccess(
            {
                "config_type_id": record.config_type_id,
                "config_type_name": record.config_type_name,
                "min_mentees": record.min_mentees,
                "max_mentees": record.max_mentees,
            },
            "Configuration type updated successfully.",
        )

    # ---- CREATE ----
    duplicate = (
        db.query(LMSConfigType)
        .filter(
            # LMSConfigType.org_id == org_id,
            LMSConfigType.config_type_name == payload.config_type_name.strip(),
            # LMSConfigType.status == 1,
        )
        .first()
    )
    if duplicate:
        return returnException("Configuration type name already exists.")

    new_record = LMSConfigType(
        config_type_name=payload.config_type_name.strip(),
        min_mentees=payload.min_mentees,
        max_mentees=payload.max_mentees,
        # org_id=org_id,
        # status=1,
        created_by=user_id,
        created_date=datetime.now(),
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return returnSuccess(
        {
            "config_type_id": new_record.config_type_id,
            "config_type_name": new_record.config_type_name,
            "min_mentees": new_record.min_mentees,
            "max_mentees": new_record.max_mentees,
        },
        "Configuration type saved successfully.",
    )


# ---------------------------------------------------------------------------
# PUT /update/{id} – update an existing config type
# ---------------------------------------------------------------------------

@router.put("/update/{config_type_id}")
def update_config_type(
    config_type_id: int,
    payload: UpdateConfigType,
    current_user: dict = Depends(get_current_user),
    # org_id: int = Header(...),
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
            LMSConfigType.config_type_id == config_type_id,
        )
        .first()
    )
    if not record:
        return returnException("Configuration type not found.")

    # --- Duplicate name check (exclude self) ---
    duplicate = (
        db.query(LMSConfigType)
        .filter(
            LMSConfigType.config_type_name == payload.config_type_name.strip(),
            LMSConfigType.config_type_id != config_type_id,
        )
        .first()
    )
    if duplicate:
        return returnException("Configuration type name already exists.")

    record.config_type_name = payload.config_type_name.strip()
    record.min_mentees = payload.min_mentees
    record.max_mentees = payload.max_mentees
    record.modified_by = user_id
    record.modified_date = datetime.now()
    db.commit()
    db.refresh(record)
    return returnSuccess(
        {
            "config_type_id": record.config_type_id,
            "config_type_name": record.config_type_name,
            "min_mentees": record.min_mentees,
            "max_mentees": record.max_mentees,
        },
        "Configuration type updated successfully.",
    )


# ---------------------------------------------------------------------------
# DELETE /delete/{id} – soft delete
# ---------------------------------------------------------------------------

@router.delete("/delete/{id}")
def delete_config_type(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(LMSConfigType)
        .filter(LMSConfigType.config_type_id == id)
        .first()
    )

    if not record:
        return returnException("Configuration type not found.")

    db.delete(record)
    db.commit()

    return returnSuccess(
        {"id": id},
        "Configuration type deleted successfully."
    )
