from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from app.db.models import LMSQuestionnaireFieldSetting

router = APIRouter()


@router.get("/get_questionnaire_field_setting")
def get_questionnaire_field_setting(
    db: Session = Depends(get_db)
):
     return (
        db.query(LMSQuestionnaireFieldSetting)
        .filter(LMSQuestionnaireFieldSetting.status == 1)
        .order_by(LMSQuestionnaireFieldSetting.field_setting_id)
        .all()
    )