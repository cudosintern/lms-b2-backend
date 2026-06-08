from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import LMSQuestionnaireType

router = APIRouter()


@router.get("/get_questionnaire_type_list")
def get_questionnaire_type_list(
    db: Session = Depends(get_db)
):
    data = db.query(
        LMSQuestionnaireType
    ).order_by(
        LMSQuestionnaireType.questionnaire_type_id
    ).all()

    result = []

    for row in data:
        result.append({
            "questionnaire_type_id": row.questionnaire_type_id,
            "questionnaire_type_name": row.questionnaire_type_name,
            "questionnaire_type_desc": row.questionnaire_type_desc
        })

    return returnSuccess(result)