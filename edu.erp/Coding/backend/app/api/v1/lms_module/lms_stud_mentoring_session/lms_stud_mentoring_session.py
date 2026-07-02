from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from datetime import datetime
from app.core.database import get_db
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)
from app.utils.auth_helper import get_current_user

from app.db.models import (
   IEMSAcademicBatch,
    IEMSemester,
    LMSMentorsGroup,
    LMSMentorsGroupTerms,
    LMSGroupMentees,
    LMSMentoringSchedule,
    LMSMentoringSubGroup,
    LMSMentoringSubGrpDate,
    LMSMapMenteeSchedule,

    LMSQuestionnaires,
    LMSQuestionType,
    LMSQuestionnaireType,
    LMSQuestionnairesOptions,
    LMSQuestionnairesQuestions,

    LMSMenteeQuestionnaireResponse,
    LMSMenteeQuestionnaireResponseQue,
    LMSMenteeQuestionnaireResponseOption,

    LMSMMPSessionSuggestion,
    LMSMMPSessionSuggestionGenericComments,
    LMSMMPSessionSuggestionIndividualComments,

    LMSQuestionnairesQuestions,
    LMSQuestionnairesOptions,

    IEMStudents,
    IEMSUsers
)

from .lms_stud_mentoring_session_schema import *

router = APIRouter()


# ==========================================================
# GET ACADEMIC BATCHES MAPPED TO STUDENT
# ==========================================================
@router.get("/get_student_academic_batches/{student_id}")
def get_student_academic_batches(
    student_id: int,
    db: Session = Depends(get_db)
):
    try:

        batches = (
            db.query(IEMSAcademicBatch)
            .join(
                LMSMentorsGroupTerms,
                LMSMentorsGroupTerms.academic_batch_id == IEMSAcademicBatch.academic_batch_id
            )
            .join(
                LMSGroupMentees,
                LMSGroupMentees.mentors_group_terms_id == LMSMentorsGroupTerms.mentors_group_terms_id
            )
            .filter(
                LMSGroupMentees.student_id == student_id
            )
            .distinct()
            .order_by(IEMSAcademicBatch.academic_batch_desc)
            .all()
        )

        result = []

        for batch in batches:
            result.append({
                "academic_batch_id": batch.academic_batch_id,
                "academic_batch_code": batch.academic_batch_code,
                "academic_batch_desc": batch.academic_batch_desc
            })

        return returnSuccess(result)

    except Exception as e:
        return returnException(str(e))

@router.get("/get_my_mentoring_schedules/{academic_batch_id}/{student_id}")
def get_my_mentoring_schedules(
    academic_batch_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    try:

        student = (
            db.query(IEMStudents)
            .filter(IEMStudents.student_id == student_id)
            .first()
        )

        if not student:
            return returnException("Student not found")

        result = []

        mappings = (
            db.query(LMSMapMenteeSchedule)
            .filter(
                LMSMapMenteeSchedule.student_id == student_id
            )
            .all()
        )

        for mapping in mappings:

            schedule = (
                db.query(LMSMentoringSchedule)
                .filter(
                    LMSMentoringSchedule.schedule_id == mapping.schedule_id
                )
                .first()
            )

            if not schedule:
                continue

            group_term = (
                db.query(LMSMentorsGroupTerms)
                .filter(
                    LMSMentorsGroupTerms.mentors_group_terms_id ==
                    schedule.mentors_group_terms_id
                )
                .first()
            )

            if not group_term:
                continue

            group = (
                db.query(LMSMentorsGroup)
                .filter(
                    LMSMentorsGroup.mentors_group_id ==
                    group_term.mentors_group_id
                )
                .first()
            )

            if not group:
                continue

            if group.academic_batch_id != academic_batch_id:
                continue

            sub_group = (
                db.query(LMSMentoringSubGroup)
                .filter(
                    LMSMentoringSubGroup.sub_group_id ==
                    mapping.sub_group_id
                )
                .first()
            )

            dates = (
                db.query(LMSMentoringSubGrpDate)
                .filter(
                    LMSMentoringSubGrpDate.sub_group_id ==
                    mapping.sub_group_id
                )
                .all()
            )

            response = (
                db.query(LMSMenteeQuestionnaireResponse)
                .filter(
                    LMSMenteeQuestionnaireResponse.schedule_id == schedule.schedule_id,
                    LMSMenteeQuestionnaireResponse.student_id == student_id
                )
                .first()
            )

            questionnaire_status = (
                "Submitted"
                if response
                else "Pending"
            )

            for dt in dates:

                result.append({

                    "schedule_id": schedule.schedule_id,

                    "group_name": group.mentors_pgm_title,

                    "sub_group_name": sub_group.sub_group_name,

                    "session_agenda": schedule.session_agenda,

                    "location": sub_group.location,

                    "start_date": dt.start_date,

                    "end_date": dt.end_date,

                    "start_time": dt.start_time,

                    "end_time": dt.end_time,

                    "questionnaire_id": schedule.questionnaire_id,

                    "questionnaire_status": questionnaire_status

                })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    
@router.get("/get_questionnaire/{schedule_id}/{student_id}")
def get_questionnaire(
    schedule_id: int,
    student_id: int,
    db: Session = Depends(get_db)
):
    try:

        # --------------------------------------------------
        # Validate Student
        # --------------------------------------------------
        student = (
            db.query(IEMStudents)
            .filter(
                IEMStudents.student_id == student_id
            )
            .first()
        )

        if not student:
            return returnException(
                "Invalid student."
            )

        # --------------------------------------------------
        # Validate Student is mapped to Schedule
        # --------------------------------------------------
        mapping = (
            db.query(LMSMapMenteeSchedule)
            .filter(
                LMSMapMenteeSchedule.schedule_id == schedule_id,
                LMSMapMenteeSchedule.student_id == student_id
            )
            .first()
        )

        if not mapping:
            return returnException(
                "Student is not mapped to this mentoring schedule."
            )

        # --------------------------------------------------
        # Get Mentoring Schedule
        # --------------------------------------------------
        schedule = (
            db.query(LMSMentoringSchedule)
            .filter(
                LMSMentoringSchedule.schedule_id == schedule_id
            )
            .first()
        )

        if not schedule:
            return returnException(
                "Mentoring schedule not found."
            )

        # --------------------------------------------------
        # Get Questionnaire
        # --------------------------------------------------
        questionnaire = (
            db.query(LMSQuestionnaires)
            .filter(
                LMSQuestionnaires.questionnaire_id ==
                schedule.questionnaire_id
            )
            .first()
        )

        if not questionnaire:
            return returnException(
                "Questionnaire not found."
            )
         # --------------------------------------------------
        # Get Questionnaire response if submitted
        # --------------------------------------------------
        submitted_response = (
            db.query(LMSMenteeQuestionnaireResponse)
            .filter(
                LMSMenteeQuestionnaireResponse.student_id == student_id,
                LMSMenteeQuestionnaireResponse.schedule_id == schedule_id
            )
            .first()
        )

        is_submitted = submitted_response is not None
        # --------------------------------------------------
        # Get Questions with Question Type
        # --------------------------------------------------
        questions = (
            db.query(
                LMSQuestionnairesQuestions,
                LMSQuestionType
            )
            .join(
                LMSQuestionType,
                LMSQuestionType.que_type_id ==
                LMSQuestionnairesQuestions.que_type_id
            )
            .filter(
                LMSQuestionnairesQuestions.questionnaire_id ==
                questionnaire.questionnaire_id
            )
            .order_by(
                LMSQuestionnairesQuestions.que_no
            )
            .all()
        )

        question_list = []

        # --------------------------------------------------
        # Prepare Question List
        # --------------------------------------------------
        for question, que_type in questions:

            options = (
                db.query(
                    LMSQuestionnairesOptions
                )
                .filter(
                    LMSQuestionnairesOptions.questionnaire_que_id ==
                    question.questionnaire_que_id
                )
                .all()
            )

            option_list = []

            for option in options:

                option_list.append({

                    "option_id":
                        option.questionnaire_options_id,

                    "option":
                        option.que_option,

                    "specify_flag":
                        option.specify_flag

                })

            question_list.append({

                "question_id":
                    question.questionnaire_que_id,

                "question_no":
                    question.que_no,

                "question":
                    question.question,

                "que_type_id":
                    que_type.que_type_id,

                "question_type":
                    que_type.que_type_name,

                "mandatory":
                    question.que_is_mandatory,

                "options":
                    option_list

            })

        # --------------------------------------------------
        # Final Response
        # --------------------------------------------------
        result = {

            "schedule_id":
                schedule.schedule_id,

            "questionnaire_id":
                questionnaire.questionnaire_id,

            "questionnaire_name":
                questionnaire.questionnaire_name,

            "message_to_mentees":
                questionnaire.message_to_mentees,

            "questions":
                question_list

        }

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))


@router.post("/save_questionnaire_response")
def save_questionnaire_response(
    req: SaveQuestionnaireResponse,
    db: Session = Depends(get_db)
):
    try:

        # ==========================================================
        # Validate Student
        # ==========================================================

        student = (
            db.query(IEMStudents)
            .filter(
                IEMStudents.student_id == req.student_id
            )
            .first()
        )

        if not student:
            return returnException("Invalid student.")

        # ==========================================================
        # Validate Schedule
        # ==========================================================

        schedule = (
            db.query(LMSMentoringSchedule)
            .filter(
                LMSMentoringSchedule.schedule_id ==
                req.schedule_id
            )
            .first()
        )

        if not schedule:
            return returnException("Invalid mentoring schedule.")

        # ==========================================================
        # Validate Student Mapping
        # ==========================================================

        mapping = (
            db.query(LMSMapMenteeSchedule)
            .filter(
                LMSMapMenteeSchedule.schedule_id ==
                req.schedule_id,

                LMSMapMenteeSchedule.student_id ==
                req.student_id
            )
            .first()
        )

        if not mapping:
            return returnException(
                "Student is not mapped to this mentoring schedule."
            )

        # ==========================================================
        # Duplicate Submission Validation
        # ==========================================================

        submitted = (
            db.query(
                LMSMenteeQuestionnaireResponse
            )
            .filter(
                LMSMenteeQuestionnaireResponse.student_id ==
                req.student_id,

                LMSMenteeQuestionnaireResponse.schedule_id ==
                req.schedule_id
            )
            .first()
        )

        if submitted:
            return returnException(
                "Questionnaire already submitted."
            )

        # ==========================================================
        # Validate Every Question
        # ==========================================================

        for answer in req.answers:

            question_data = (
                db.query(
                    LMSQuestionnairesQuestions,
                    LMSQuestionType
                )
                .join(
                    LMSQuestionType,
                    LMSQuestionType.que_type_id ==
                    LMSQuestionnairesQuestions.que_type_id
                )
                .filter(
                    LMSQuestionnairesQuestions.questionnaire_que_id ==
                    answer.questionnaire_que_id
                )
                .first()
            )

            if not question_data:

                return returnException(
                    f"Invalid Question : {answer.questionnaire_que_id}"
                )

            question, question_type = question_data

            # ===========================================
            # Mandatory Validation
            # ===========================================

            if question.que_is_mandatory:

                if question_type.que_type_id == 3:

                    if (
                        answer.text_answer is None
                        or
                        answer.text_answer.strip() == ""
                    ):

                        return returnException(
                            f"Question {question.que_no} is mandatory."
                        )

                else:

                    if len(answer.selected_option_ids) == 0:

                        return returnException(
                            f"Question {question.que_no} is mandatory."
                        )

            # ===========================================
            # Single Select Validation
            # ===========================================

            if question_type.que_type_id == 1:

                if len(answer.selected_option_ids) > 1:

                    return returnException(
                        f"Question {question.que_no} allows only one option."
                    )

            # ===========================================
            # Validate Selected Options
            # ===========================================

            if question_type.que_type_id != 3:

                for option_id in answer.selected_option_ids:

                    option = (
                        db.query(
                            LMSQuestionnairesOptions
                        )
                        .filter(
                            LMSQuestionnairesOptions.questionnaire_options_id ==
                            option_id,

                            LMSQuestionnairesOptions.questionnaire_que_id ==
                            question.questionnaire_que_id
                        )
                        .first()
                    )

                    if not option:

                        return returnException(
                            f"Invalid option selected for Question {question.que_no}"
                        )

        # ==========================================================
        # Save Questionnaire Response Header
        # ==========================================================

        response = LMSMenteeQuestionnaireResponse(

            student_id=req.student_id,

            schedule_id=req.schedule_id,

            questionnaire_id=schedule.questionnaire_id,

            sub_group_date_id=req.sub_group_date_id,

            created_date=datetime.now(),

            created_by=req.student_id,

            modified_by=req.student_id

        )

        db.add(response)

        db.flush()

        response_id = response.questionnaire_response_id

                # ==========================================================
        # Save Question Answers
        # ==========================================================

        for answer in req.answers:

            question = (
                db.query(LMSQuestionnairesQuestions)
                .filter(
                    LMSQuestionnairesQuestions.questionnaire_que_id ==
                    answer.questionnaire_que_id
                )
                .first()
            )

            question_response = LMSMenteeQuestionnaireResponseQue(

                questionnaire_response_id=response_id,

                questionnaire_que_id=question.questionnaire_que_id,

                text_answer=answer.text_answer,

                created_by=req.student_id,

                modified_by=req.student_id

            )

            db.add(question_response)

            db.flush()

            question_response_id = (
                question_response.questionnaire_response_que_id
            )

            # ================================================
            # Save Selected Options
            # ================================================

            if len(answer.selected_option_ids) > 0:

                for option_id in answer.selected_option_ids:

                    option_response = (
                        LMSMenteeQuestionnaireResponseOption(

                            questionnaire_response_que_id=
                                question_response_id,

                            questionnaire_options_id=
                                option_id,

                            created_by=req.student_id,

                            modified_by=req.student_id

                        )
                    )

                    db.add(option_response)

        # ==========================================================
        # Commit Transaction
        # ==========================================================

        db.commit()

        return returnSuccess(
            "Questionnaire submitted successfully."
        )

    except Exception as e:

        db.rollback()

        return returnException(str(e))