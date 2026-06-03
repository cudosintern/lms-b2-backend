from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from ......core.database import get_db
from ......utils.auth_helper import get_current_user
from ......utils.http_return_helper import returnSuccess, returnException
from ..model.bloom_domain_model import BloomDomain
from ..schema.bloom_domain_schema import BloomDomainSaveRequest

router = APIRouter()


@router.post("/save_bloom_domain")
def save_bloom_domain(
        request: BloomDomainSaveRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        user_id = current_user.get("user_id")
        status = request.status if request.status is not None else 1

        if request.bld_id:
            # Update existing
            bloom_domain = db.query(BloomDomain).filter(BloomDomain.bld_id == request.bld_id).first()
            if not bloom_domain:
                return returnException("Bloom Domain not found")

            bloom_domain.bld_name = request.bld_name
            bloom_domain.bld_acronym = request.bld_acronym
            bloom_domain.bld_description = request.bld_description
            bloom_domain.status = status
            bloom_domain.modified_by = user_id
            db.commit()
            db.refresh(bloom_domain)
        else:
            # Create new
            # Check for max 3 domains
            count = db.query(BloomDomain).filter(BloomDomain.bld_code == org_id,BloomDomain.status == 1).count()
            if count >= 3:
                return returnException("Maximum 3 Bloom's Domains allowed.")

            bloom_domain = BloomDomain(
                bld_name=request.bld_name,
                bld_acronym=request.bld_acronym,
                bld_description=request.bld_description,
                status=status,
                bld_code=org_id,
                created_by=user_id,
                modified_by=user_id
            )
            db.add(bloom_domain)
            db.commit()
            db.refresh(bloom_domain)

        return returnSuccess({
            "bld_id": bloom_domain.bld_id,
            "bld_name": bloom_domain.bld_name,
            "bld_acronym": bloom_domain.bld_acronym,
            "bld_description": bloom_domain.bld_description,
            "status": bloom_domain.status,
            "bld_code": bloom_domain.bld_code,
            "create_date": bloom_domain.create_date.strftime("%Y-%m-%d %H:%M:%S") if bloom_domain.create_date else None,
            "created_by": bloom_domain.created_by,
            "modify_date": bloom_domain.modify_date.strftime("%Y-%m-%d %H:%M:%S") if bloom_domain.modify_date else None,
            "modified_by": bloom_domain.modified_by
        })
    except Exception as e:
        db.rollback()
        raise e


@router.post("/bloom_domain_list")
def bloom_domain_list(
        request: dict,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        show_delete = request.get("show_delete", 1)
        equal_or_not_equal = request.get("equal_or_not_equal", 0)
        no_batch = request.get("no_batch", 1)

        query = db.query(BloomDomain).filter(BloomDomain.bld_code == org_id)

        if equal_or_not_equal == 0:
            if show_delete == 0:
                query = query.filter(BloomDomain.status == 1)
            elif show_delete == 1:
                query = query.filter(BloomDomain.status.in_([0, 1]))
        else:
            if show_delete == 0:
                query = query.filter(BloomDomain.status != 1)
            elif show_delete == 1:
                query = query.filter(BloomDomain.status.notin_([0, 1]))

        bloom_domains = query.all()

        result = []
        for bd in bloom_domains:
            result.append({
                "bld_id": bd.bld_id,
                "bld_code": bd.bld_code,
                "bld_name": bd.bld_name,
                "bld_acronym": bd.bld_acronym,
                "bld_description": bd.bld_description,
                "status": bd.status,
                "created_by": bd.created_by,
                "modified_by": bd.modified_by,
                "create_date": bd.create_date.strftime("%Y-%m-%d %H:%M:%S") if bd.create_date else None,
                "modify_date": bd.modify_date.strftime("%Y-%m-%d %H:%M:%S") if bd.modify_date else None,
            })

        return returnSuccess(result)
    except Exception as e:
        raise e