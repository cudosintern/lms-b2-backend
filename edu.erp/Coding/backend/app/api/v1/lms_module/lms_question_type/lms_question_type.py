from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import LMSQuestionType

router = APIRouter()


@router.get("/get_question_type_list")
def get_question_type_list(
    db: Session = Depends(get_db)
):
    data = db.query(
        LMSQuestionType
    ).order_by(
        LMSQuestionType.que_type_id
    ).all()

    result = []

    for row in data:
        result.append({
            "que_type_id": row.que_type_id,
            "que_type_name": row.que_type_name,
            "que_type_desc": row.que_type_desc
        })

    return returnSuccess(result)