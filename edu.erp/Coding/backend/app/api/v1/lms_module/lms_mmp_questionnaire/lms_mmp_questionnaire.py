from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (
    LMSQuestionnaires,
    LMSQuestionnairesQuestions,
    LMSQuestionnairesOptions,
    LMSQuestionnaireFieldSetting
)

from .lms_mmp_questionnaire_schema import (
    QuestionnaireSave
)

router = APIRouter()

@router.post("/save_questionnaire")
def save_questionnaire(
    questionnaire_data: QuestionnaireSave,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = current_user.get("user_id")

    try:

        # -----------------------------
        # ADD QUESTIONNAIRE
        # -----------------------------

        if questionnaire_data.questionnaire_id is None:

            questionnaire = LMSQuestionnaires(
                questionnaire_name=
                questionnaire_data.questionnaire_name.strip(),

                message_to_mentees=
                questionnaire_data.message_to_mentees,

                access_level=
                questionnaire_data.access_level,

                parent_id=
                questionnaire_data.parent_id,

                created_by=user_id,
                created_date=datetime.now()
            )

            db.add(questionnaire)
            db.flush()

        # -----------------------------
        # EDIT QUESTIONNAIRE
        # -----------------------------

        else:

            questionnaire = db.query(
                LMSQuestionnaires
            ).filter(
                LMSQuestionnaires.questionnaire_id ==
                questionnaire_data.questionnaire_id
            ).first()

            if not questionnaire:

                return returnException(
                    "Questionnaire not found"
                )

            questionnaire.questionnaire_name = (
                questionnaire_data.questionnaire_name.strip()
            )

            questionnaire.message_to_mentees = (
                questionnaire_data.message_to_mentees
            )

            questionnaire.access_level = (
                questionnaire_data.access_level
            )

            questionnaire.parent_id = (
                questionnaire_data.parent_id
            )

            questionnaire.modified_by = user_id
            questionnaire.modified_date = datetime.now()

        # -----------------------------
        # QUESTIONS
        # -----------------------------

        for question_item in questionnaire_data.questions:

            # ADD QUESTION

            if question_item.questionnaire_que_id is None:

                question = LMSQuestionnairesQuestions(

                    questionnaire_id=
                    questionnaire.questionnaire_id,

                    que_type_id=
                    question_item.que_type_id,

                    que_no=
                    question_item.que_no,

                    question=
                    question_item.question,

                    questionnaire_type_id=
                    question_item.questionnaire_type_id,

                    que_is_mandatory=
                    question_item.que_is_mandatory,

                    created_by=user_id,
                    created_date=datetime.now()
                )

                db.add(question)
                db.flush()

            # EDIT QUESTION

            else:

                question = db.query(
                    LMSQuestionnairesQuestions
                ).filter(
                    LMSQuestionnairesQuestions.questionnaire_que_id ==
                    question_item.questionnaire_que_id
                ).first()

                if not question:
                    continue

                question.que_type_id = (
                    question_item.que_type_id
                )

                question.que_no = (
                    question_item.que_no
                )

                question.question = (
                    question_item.question
                )

                question.questionnaire_type_id = (
                    question_item.questionnaire_type_id
                )

                question.que_is_mandatory = (
                    question_item.que_is_mandatory
                )

                question.modified_by = user_id
                question.modified_date = datetime.now()

            # -----------------------------
            # OPTIONS
            # -----------------------------

            for option_item in question_item.options:

                # ADD OPTION

                if option_item.questionnaire_options_id is None:

                    option = LMSQuestionnairesOptions(

                        questionnaire_que_id=
                        question.questionnaire_que_id,

                        que_option=
                        option_item.que_option.strip(),

                        specify_flag=
                        option_item.specify_flag,

                        created_by=user_id,
                        created_date=datetime.now()
                    )

                    db.add(option)

                # EDIT OPTION

                else:

                    option = db.query(
                        LMSQuestionnairesOptions
                    ).filter(
                        LMSQuestionnairesOptions.questionnaire_options_id ==
                        option_item.questionnaire_options_id
                    ).first()

                    if not option:
                        continue

                    option.que_option = (
                        option_item.que_option.strip()
                    )

                    option.specify_flag = (
                        option_item.specify_flag
                    )

                    option.modified_by = user_id
                    option.modified_date = datetime.now()

        db.commit()

        return returnSuccess({
            "questionnaire_id":
            questionnaire.questionnaire_id,

            "questionnaire_name":
            questionnaire.questionnaire_name
        })

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
@router.get("/get_questionnaire_list")
def get_questionnaire_list(
    db: Session = Depends(get_db)
):
    data = db.query(
        LMSQuestionnaires
    ).order_by(
        LMSQuestionnaires.questionnaire_id.desc()
    ).all()

    result = []

    for row in data:

        result.append({
            "questionnaire_id":
            row.questionnaire_id,

            "questionnaire_name":
            row.questionnaire_name,

            "message_to_mentees":
            row.message_to_mentees,

            "access_level":
            row.access_level,

            "parent_id":
            row.parent_id
        })

    return returnSuccess(result)

@router.get(
    "/get_questionnaire_full/{questionnaire_id}"
)
def get_questionnaire_full(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):

    questionnaire = db.query(
        LMSQuestionnaires
    ).filter(
        LMSQuestionnaires.questionnaire_id ==
        questionnaire_id
    ).first()

    if not questionnaire:

        return returnException(
            "Questionnaire not found"
        )

    result = {
        "questionnaire_id":
        questionnaire.questionnaire_id,

        "questionnaire_name":
        questionnaire.questionnaire_name,

        "message_to_mentees":
        questionnaire.message_to_mentees,

        "access_level":
        questionnaire.access_level,

        "parent_id":
        questionnaire.parent_id,

        "questions": []
    }

    questions = db.query(
        LMSQuestionnairesQuestions
    ).filter(
        LMSQuestionnairesQuestions.questionnaire_id ==
        questionnaire_id
    ).order_by(
        LMSQuestionnairesQuestions.que_no
    ).all()

    for q in questions:

        question_obj = {

            "questionnaire_que_id":
            q.questionnaire_que_id,

            "que_type_id":
            q.que_type_id,

            "que_no":
            q.que_no,

            "question":
            q.question,

            "questionnaire_type_id":
            q.questionnaire_type_id,

            "que_is_mandatory":
            q.que_is_mandatory,

            "options": []
        }

        options = db.query(
            LMSQuestionnairesOptions
        ).filter(
            LMSQuestionnairesOptions.questionnaire_que_id ==
            q.questionnaire_que_id
        ).all()

        for op in options:

            question_obj["options"].append({

                "questionnaire_options_id":
                op.questionnaire_options_id,

                "que_option":
                op.que_option,

                "specify_flag":
                op.specify_flag
            })

        result["questions"].append(
            question_obj
        )

    return returnSuccess(result)

@router.delete("/delete_question/{questionnaire_que_id}")
def delete_question(
    questionnaire_que_id: int,
    db: Session = Depends(get_db)
):
    question = db.query(
        LMSQuestionnairesQuestions
    ).filter(
        LMSQuestionnairesQuestions.questionnaire_que_id
        == questionnaire_que_id
    ).first()

    if not question:
        return returnException(
            "Question not found"
        )

    db.delete(question)

    db.commit()

    return returnSuccess(
        "Question deleted successfully"
    )

@router.delete("/delete_option/{questionnaire_options_id}")
def delete_option(
    questionnaire_options_id: int,
    db: Session = Depends(get_db)
):
    option = db.query(
        LMSQuestionnairesOptions
    ).filter(
        LMSQuestionnairesOptions.questionnaire_options_id
        == questionnaire_options_id
    ).first()

    if not option:
        return returnException(
            "Option not found"
        )

    db.delete(option)

    db.commit()

    return returnSuccess(
        "Option deleted successfully"
    )

