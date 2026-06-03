from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException

from app.api.v1.cudo_module.knowledge_profile.model.okp_model import OrgKnowledgeProfile
from app.api.v1.cudo_module.knowledge_profile.schema.okp_schema import (
    OKPCreate,
    OKPUpdate,
    OKPResponse
)

router = APIRouter()


# ===================== LIST =====================
@router.get("")
def list_knowledge_profiles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    org_id: Optional[int] = Header(None)
):
    try:
        query = db.query(OrgKnowledgeProfile)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                func.lower(OrgKnowledgeProfile.okp_attr_code).like(func.lower(search_term)) |
                func.lower(OrgKnowledgeProfile.okp_attr_description).like(func.lower(search_term))
            )

        profiles = query.offset(skip).limit(limit).all()
        response = [OKPResponse.model_validate(p).model_dump() for p in profiles]

        return returnSuccess(response)
    except Exception as e:
        return returnException(f"Error fetching Knowledge Profiles: {str(e)}")


# ===================== GET BY ID =====================
@router.get("/{okp_id}")
def get_knowledge_profile(
    okp_id: int,
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    profile = db.query(OrgKnowledgeProfile).filter(
        OrgKnowledgeProfile.okp_id == okp_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Knowledge Profile not found")

    return returnSuccess(OKPResponse.model_validate(profile).model_dump())


# ===================== CREATE =====================
@router.post("")
def create_knowledge_profile(
    request: OKPCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    try:
        user_id = current_user.get("user_id")

        existing = db.query(OrgKnowledgeProfile).filter(
            func.lower(OrgKnowledgeProfile.okp_attr_code) ==
            func.lower(request.okp_attr_code.strip())
        ).first()

        if existing:
            return returnException(
                f"Attribute Code '{request.okp_attr_code}' already exists"
            )

        profile = OrgKnowledgeProfile(
            okp_attr_code=request.okp_attr_code.strip(),
            okp_attr_description=request.okp_attr_description.strip(),
            created_by=user_id,
            created_date=datetime.now()
        )

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return returnSuccess(
            OKPResponse.model_validate(profile).model_dump(),
            message="Knowledge Profile created successfully"
        )

    except Exception as e:
        db.rollback()
        return returnException(f"Error creating Knowledge Profile: {str(e)}")


# ===================== UPDATE =====================
@router.put("/{okp_id}")
def update_knowledge_profile(
    okp_id: int,
    request: OKPUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    try:
        user_id = current_user.get("user_id")

        profile = db.query(OrgKnowledgeProfile).filter(
            OrgKnowledgeProfile.okp_id == okp_id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Knowledge Profile not found")

        if request.okp_attr_code and request.okp_attr_code.strip() != profile.okp_attr_code:
            existing = db.query(OrgKnowledgeProfile).filter(
                func.lower(OrgKnowledgeProfile.okp_attr_code) ==
                func.lower(request.okp_attr_code.strip()),
                OrgKnowledgeProfile.okp_id != okp_id
            ).first()

            if existing:
                return returnException(
                    f"Attribute Code '{request.okp_attr_code}' already exists"
                )

            profile.okp_attr_code = request.okp_attr_code.strip()

        if request.okp_attr_description is not None:
            profile.okp_attr_description = request.okp_attr_description.strip()

        profile.modified_by = user_id
        profile.modified_date = datetime.now()

        db.commit()
        db.refresh(profile)

        return returnSuccess(
            OKPResponse.model_validate(profile).model_dump(),
            message="Knowledge Profile updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error updating Knowledge Profile: {str(e)}")


# ===================== DELETE =====================
@router.delete("/{okp_id}")
def delete_knowledge_profile(
    okp_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_id: Optional[int] = Header(None)
):
    try:
        rows = db.query(OrgKnowledgeProfile).filter(
            OrgKnowledgeProfile.okp_id == okp_id
        ).delete()

        if rows == 0:
            raise HTTPException(status_code=404, detail="Knowledge Profile not found")

        db.commit()
        return returnSuccess(None, message="Knowledge Profile deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return returnException(f"Error deleting Knowledge Profile: {str(e)}")
