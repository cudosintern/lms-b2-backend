from fastapi import (
    APIRouter,
    Depends,
    Form,
    File,
    UploadFile
)
from sqlalchemy.orm import Session

from datetime import datetime
from app.core.database import get_db
from app.utils.http_return_helper import (
    returnSuccess,
    returnException
)

from app.db.models import (
   IEMSAcademicBatch,
    IEMSemester,
    LMSMentorsGroup,
    LMSGroupMentors,
    LMSMapMentor,
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


import uuid
import shutil
import os
UPLOAD_DIR = "uploads/mentoring_comments"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_EXTENSIONS = [
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "jpg",
    "jpeg",
    "png"
]

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

def validate_attachment(file):

    if not file:
        return

    ext = file.filename.split(".")[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise Exception(
            "Only pdf, doc, docx, xls, xlsx, jpg, jpeg, png allowed"
        )

    content = file.file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise Exception(
            "Maximum file size allowed is 2 MB"
        )

    file.file.seek(0)

def save_uploaded_file(file):

    if not file:
        return None

    ext = file.filename.split(".")[-1]

    file_name = (
        str(uuid.uuid4())
        + "."
        + ext
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        file_name
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return file_name

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

            if group_term.academic_batch_id != academic_batch_id:
                continue

            sub_group = (
                db.query(LMSMentoringSubGroup)
                .filter(
                    LMSMentoringSubGroup.sub_group_id ==
                    mapping.sub_group_id
                )
                .first()
            )

            if not sub_group or sub_group.schedule_id != schedule.schedule_id:
                continue
            semester = db.query(IEMSemester).filter(
                IEMSemester.semester_id == group_term.semester_id
            ).first()
            mentors = db.query(IEMSUsers).join(
                LMSGroupMentors, LMSGroupMentors.mentor_id == IEMSUsers.id
            ).filter(
                LMSGroupMentors.mentors_group_terms_id == group_term.mentors_group_terms_id
            ).all()
            if not mentors:
                mentors = db.query(IEMSUsers).join(
                    LMSMapMentor, LMSMapMentor.mentor_id == IEMSUsers.id
                ).filter(LMSMapMentor.mentors_group_id == group.mentors_group_id).all()
            mentor_names = [" ".join(filter(None, [
                mentor.first_name, mentor.last_name
            ])) for mentor in mentors]

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
                    "mentors_group_id": group.mentors_group_id,
                    "sub_group_id": sub_group.sub_group_id,
                    "sub_group_date_id": dt.sub_group_date_id,
                    "status": dt.status,
                    "semester_id": group_term.semester_id,
                    "semester_name": (semester.semester_desc or semester.term_name or str(semester.semester)) if semester else "",
                    "mentor_names": mentor_names,

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

        for question, que_type in questions:

            response_que = None

            if submitted_response:
                response_que = (
                    db.query(LMSMenteeQuestionnaireResponseQue)
                    .filter(
                        LMSMenteeQuestionnaireResponseQue.questionnaire_response_id ==
                        submitted_response.questionnaire_response_id,

                        LMSMenteeQuestionnaireResponseQue.questionnaire_que_id ==
                        question.questionnaire_que_id
                    )
                    .first()
                )

            # -----------------------------
            # Fetch Options
            # -----------------------------
            options = (
                db.query(LMSQuestionnairesOptions)
                .filter(
                    LMSQuestionnairesOptions.questionnaire_que_id ==
                    question.questionnaire_que_id
                )
                .all()
            )

            option_list = []

            for option in options:

                selected = False
                specification = None

                if response_que:

                    selected_option = (
                        db.query(LMSMenteeQuestionnaireResponseOption)
                        .filter(
                            LMSMenteeQuestionnaireResponseOption.questionnaire_response_que_id ==
                            response_que.questionnaire_response_que_id,

                            LMSMenteeQuestionnaireResponseOption.questionnaire_options_id ==
                            option.questionnaire_options_id
                        )
                        .first()
                    )

                    if selected_option:
                        selected = True
                        specification = selected_option.specification

                option_list.append({
                    "option_id": option.questionnaire_options_id,
                    "option": option.que_option,
                    "specify_flag": option.specify_flag,
                    "selected": selected,
                    "specification": specification
                })

            # -----------------------------
            # Append Question (OUTSIDE option loop)
            # -----------------------------
            question_list.append({

                "question_id": question.questionnaire_que_id,

                "question_no": question.que_no,

                "question": question.question,

                "que_type_id": que_type.que_type_id,

                "question_type": que_type.que_type_name,

                "mandatory": question.que_is_mandatory,

                "text_answer":
                    response_que.text_answer if response_que else None,

                "options": option_list

            })
        # --------------------------------------------------
        # Final Response
        # --------------------------------------------------
        result = {

            "is_submitted": is_submitted,

            "questionnaire_response_id":
                submitted_response.questionnaire_response_id
                if submitted_response else None,

            "schedule_id": schedule.schedule_id,

            "questionnaire_id": questionnaire.questionnaire_id,

            "questionnaire_name": questionnaire.questionnaire_name,

            "message_to_mentees": questionnaire.message_to_mentees,

            "questions": question_list
        }


        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))


@router.post("/save_questionnaire_response")
def save_questionnaire_response(req: SaveQuestionnaireResponse, db: Session = Depends(get_db)):
    try:
        if not db.query(IEMStudents).filter(IEMStudents.student_id == req.student_id).first():
            raise ValueError("Invalid student.")
        schedule = db.query(LMSMentoringSchedule).filter(
            LMSMentoringSchedule.schedule_id == req.schedule_id
        ).first()
        if not schedule:
            raise ValueError("Invalid mentoring schedule.")
        date = db.query(LMSMentoringSubGrpDate).join(
            LMSMentoringSubGroup,
            LMSMentoringSubGroup.sub_group_id == LMSMentoringSubGrpDate.sub_group_id
        ).join(LMSMapMenteeSchedule,
            (LMSMapMenteeSchedule.sub_group_id == LMSMentoringSubGroup.sub_group_id) &
            (LMSMapMenteeSchedule.schedule_id == LMSMentoringSubGroup.schedule_id)
        ).filter(
            LMSMentoringSubGrpDate.sub_group_date_id == req.sub_group_date_id,
            LMSMentoringSubGroup.schedule_id == req.schedule_id,
            LMSMapMenteeSchedule.student_id == req.student_id
        ).first()
        if not date:
            raise ValueError("Student is not mapped to this session date.")
        questions = db.query(LMSQuestionnairesQuestions).filter(
            LMSQuestionnairesQuestions.questionnaire_id == schedule.questionnaire_id
        ).all()
        options = db.query(LMSQuestionnairesOptions).join(
            LMSQuestionnairesQuestions,
            LMSQuestionnairesQuestions.questionnaire_que_id == LMSQuestionnairesOptions.questionnaire_que_id
        ).filter(LMSQuestionnairesQuestions.questionnaire_id == schedule.questionnaire_id).all()
        validate_answers(questions, options, req.answers)

        # Validate everything before replacing any existing response.
        response = db.query(LMSMenteeQuestionnaireResponse).filter(
            LMSMenteeQuestionnaireResponse.student_id == req.student_id,
            LMSMenteeQuestionnaireResponse.schedule_id == req.schedule_id
        ).with_for_update().first()
        if response:
            old_answers = db.query(LMSMenteeQuestionnaireResponseQue).filter(
                LMSMenteeQuestionnaireResponseQue.questionnaire_response_id == response.questionnaire_response_id
            ).all()
            for old in old_answers:
                db.query(LMSMenteeQuestionnaireResponseOption).filter(
                    LMSMenteeQuestionnaireResponseOption.questionnaire_response_que_id == old.questionnaire_response_que_id
                ).delete(synchronize_session=False)
                db.delete(old)
            db.flush()
        else:
            response = LMSMenteeQuestionnaireResponse(
                student_id=req.student_id, schedule_id=req.schedule_id,
                questionnaire_id=schedule.questionnaire_id, created_by=req.student_id
            )
            db.add(response)
        response.sub_group_date_id = req.sub_group_date_id
        response.sub_group_id = date.sub_group_id
        response.modified_by = req.student_id
        response.modified_date = datetime.now()
        db.flush()
        for answer in req.answers:
            row = LMSMenteeQuestionnaireResponseQue(
                questionnaire_response_id=response.questionnaire_response_id,
                questionnaire_que_id=answer.questionnaire_que_id,
                text_answer=answer.text_answer.strip() if answer.text_answer else None,
                created_by=req.student_id, modified_by=req.student_id
            )
            db.add(row)
            db.flush()
            for option_id in answer.selected_option_ids:
                db.add(LMSMenteeQuestionnaireResponseOption(
                    questionnaire_response_que_id=row.questionnaire_response_que_id,
                    questionnaire_options_id=option_id,
                    specification=answer.specifications.get(option_id, "").strip() or None,
                    created_by=req.student_id, modified_by=req.student_id
                ))
        db.commit()
        return returnSuccess("Questionnaire submitted successfully.")
    except Exception as e:
        db.rollback()
        return returnException(str(e))


def validate_answers(questions, options, answers):
    question_map = {q.questionnaire_que_id: q for q in questions}
    option_map = {o.questionnaire_options_id: o for o in options}
    answer_map = {a.questionnaire_que_id: a for a in answers}
    if len(answer_map) != len(answers):
        raise ValueError("Duplicate question answers are not allowed.")
    if set(answer_map) - set(question_map):
        raise ValueError("An answer does not belong to this questionnaire.")
    for qid, question in question_map.items():
        answer = answer_map.get(qid)
        selected = answer.selected_option_ids if answer else []
        text = (answer.text_answer or "").strip() if answer else ""
        mandatory = str(question.que_is_mandatory).lower() in ("1", "true")
        if question.que_type_id not in (1, 2, 3):
            raise ValueError(f"Unsupported type for Question {question.que_no}.")
        if mandatory and not (text if question.que_type_id == 3 else selected):
            raise ValueError(f"Question {question.que_no} is mandatory.")
        if len(selected) != len(set(selected)):
            raise ValueError("Duplicate options are not allowed.")
        if question.que_type_id == 1 and len(selected) > 1:
            raise ValueError(f"Question {question.que_no} allows only one option.")
        if (question.que_type_id == 3 and selected) or (question.que_type_id != 3 and text):
            raise ValueError(f"Invalid answer type for Question {question.que_no}.")
        for oid in selected:
            option = option_map.get(oid)
            if not option or option.questionnaire_que_id != qid:
                raise ValueError(f"Invalid option for Question {question.que_no}.")
            if mandatory and str(option.specify_flag).lower() in ("1", "true") and not answer.specifications.get(oid, "").strip():
                raise ValueError(f"Please specify your answer for Question {question.que_no}.")
        if answer and set(answer.specifications) - set(selected):
            raise ValueError("Specifications must refer to selected options.")


@router.post("/save_group_comment")
def save_group_comment(
    schedule_id: int = Form(...),
    student_id: int = Form(...),
    comment: str = Form(""),
    suggestion_type: int = Form(0),
    attachment: UploadFile = File(None),
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
        # Validate Schedule
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
                "Invalid mentoring schedule."
            )

        # --------------------------------------------------
        # Validate Student Mapping
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
        # Validate Attachment
        # --------------------------------------------------
        if not comment.strip() and not attachment:
            raise ValueError("Enter a comment or select an attachment.")
        if suggestion_type not in (0, 1):
            raise ValueError("Invalid suggestion type.")
        validate_attachment(attachment)

        file_name = save_uploaded_file(
            attachment
        )

        # --------------------------------------------------
        # Get/Create Session Suggestion
        # --------------------------------------------------
        suggestion = (
            db.query(LMSMMPSessionSuggestion)
            .filter(
                LMSMMPSessionSuggestion.schedule_id ==
                schedule_id
            )
            .first()
        )

        if not suggestion:

            suggestion = LMSMMPSessionSuggestion(

                schedule_id=schedule_id,

                created_by=student_id,

                modified_by=student_id

            )

            db.add(suggestion)

            db.flush()

        # --------------------------------------------------
        # Save Group Comment
        # --------------------------------------------------
        db_comment = (
            LMSMMPSessionSuggestionGenericComments(

                session_suggestion_id=
                    suggestion.session_suggestion_id,

                comment=comment,

                attachment=file_name,

                suggestion_type=suggestion_type,

                user_type=2,      # 2 = Mentee

                created_by=student_id,

                modified_by=student_id

            )
        )

        db.add(db_comment)

        db.commit()

        return returnSuccess(
            "Comment added successfully."
        )

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
@router.post("/save_individual_comment")
def save_individual_comment(
    schedule_id: int = Form(...),
    student_id: int = Form(...),
    comment: str = Form(""),
    suggestion_type: int = Form(0),
    attachment: UploadFile = File(None),
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
        # Validate Schedule
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
                "Invalid mentoring schedule."
            )

        # --------------------------------------------------
        # Validate Student Mapping
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
        # Validate Attachment
        # --------------------------------------------------
        if not comment.strip() and not attachment:
            raise ValueError("Enter a comment or select an attachment.")
        if suggestion_type not in (0, 1):
            raise ValueError("Invalid suggestion type.")
        validate_attachment(attachment)

        file_name = save_uploaded_file(
            attachment
        )

        # --------------------------------------------------
        # Get / Create Session Suggestion
        # --------------------------------------------------
        suggestion = (
            db.query(LMSMMPSessionSuggestion)
            .filter(
                LMSMMPSessionSuggestion.schedule_id ==
                schedule_id
            )
            .first()
        )

        if not suggestion:

            suggestion = LMSMMPSessionSuggestion(

                schedule_id=schedule_id,

                created_by=student_id,

                modified_by=student_id

            )

            db.add(suggestion)

            db.flush()

        # --------------------------------------------------
        # Save Individual Comment
        # --------------------------------------------------
        individual_comment = (
            LMSMMPSessionSuggestionIndividualComments(

                session_suggestion_id=
                    suggestion.session_suggestion_id,

                comment=comment,

                attachment=file_name,

                suggestion_type=suggestion_type,

                from_user_id=student_id,

                mentee_id=student_id,

                from_user_type=2,      # 2 = Mentee

                created_by=student_id,

                modified_by=student_id

            )
        )

        db.add(individual_comment)

        db.commit()

        return returnSuccess(
            "Individual comment saved successfully."
        )

    except Exception as e:

        db.rollback()

        return returnException(str(e))
    
@router.get("/get_group_comments/{schedule_id}/{student_id}")
def get_group_comments(
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
        # Validate Student Mapping
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
        # Get Session Suggestion
        # --------------------------------------------------
        suggestion = (
            db.query(LMSMMPSessionSuggestion)
            .filter(
                LMSMMPSessionSuggestion.schedule_id == schedule_id
            )
            .first()
        )

        if not suggestion:
            return returnSuccess([])

        # --------------------------------------------------
        # Get All Group Comments
        # --------------------------------------------------
        comments = (
            db.query(
                LMSMMPSessionSuggestionGenericComments
            )
            .filter(
                LMSMMPSessionSuggestionGenericComments.session_suggestion_id ==
                suggestion.session_suggestion_id
            )
            .order_by(
                LMSMMPSessionSuggestionGenericComments.created_date.asc()
            )
            .all()
        )

        result = []

        for row in comments:

            posted_by_name = ""

            # ------------------------------
            # Mentor
            # ------------------------------
            if row.user_type == 1:

                mentor = (
                    db.query(IEMSUsers)
                    .filter(
                        IEMSUsers.id == row.created_by
                    )
                    .first()
                )

                if mentor:
                    posted_by_name = mentor.first_name

                posted_by_type = "Mentor"

            # ------------------------------
            # Mentee
            # ------------------------------
            else:

                mentee = (
                    db.query(IEMStudents)
                    .filter(
                        IEMStudents.student_id ==
                        row.created_by
                    )
                    .first()
                )

                if mentee:
                    posted_by_name = mentee.name

                posted_by_type = "Mentee"

            result.append({

                "generic_comment_id":
                    row.generic_comment_id,

                "comment":
                    row.comment,

                "attachment":
                    row.attachment,

                "suggestion_type":
                    row.suggestion_type,

                "posted_by_id":
                    row.created_by,

                "posted_by_name":
                    posted_by_name,

                "posted_by_type":
                    posted_by_type,

                "created_date":
                    row.created_date

            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))
    

@router.get("/get_individual_comments/{schedule_id}/{student_id}")
def get_individual_comments(
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
        # Validate Student Mapping
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
        # Get Session Suggestion
        # --------------------------------------------------
        suggestion = (
            db.query(LMSMMPSessionSuggestion)
            .filter(
                LMSMMPSessionSuggestion.schedule_id ==
                schedule_id
            )
            .first()
        )

        if not suggestion:
            return returnSuccess([])

        # --------------------------------------------------
        # Get Conversation
        # --------------------------------------------------
        comments = (
            db.query(
                LMSMMPSessionSuggestionIndividualComments
            )
            .filter(
                LMSMMPSessionSuggestionIndividualComments.session_suggestion_id ==
                suggestion.session_suggestion_id,

                LMSMMPSessionSuggestionIndividualComments.mentee_id ==
                student_id
            )
            .order_by(
                LMSMMPSessionSuggestionIndividualComments.created_date.asc()
            )
            .all()
        )

        result = []

        for row in comments:

            posted_by_name = ""

            # ------------------------------------------
            # Comment posted by Mentor
            # ------------------------------------------
            if row.from_user_type == 1:

                mentor = (
                    db.query(IEMSUsers)
                    .filter(
                        IEMSUsers.id ==
                        row.from_user_id
                    )
                    .first()
                )

                if mentor:
                    posted_by_name = mentor.first_name

                posted_by_type = "Mentor"

            # ------------------------------------------
            # Comment posted by Mentee
            # ------------------------------------------
            else:

                mentee = (
                    db.query(IEMStudents)
                    .filter(
                        IEMStudents.student_id ==
                        row.from_user_id
                    )
                    .first()
                )

                if mentee:
                    posted_by_name = mentee.name

                posted_by_type = "Mentee"

            result.append({

                "individual_comment_id":
                    row.individual_comment_id,

                "comment":
                    row.comment,

                "attachment":
                    row.attachment,

                "suggestion_type":
                    row.suggestion_type,

                "posted_by_id":
                    row.from_user_id,

                "posted_by_name":
                    posted_by_name,

                "posted_by_type":
                    posted_by_type,

                "created_date":
                    row.created_date

            })

        return returnSuccess(result)

    except Exception as e:

        return returnException(str(e))

# JSON fetch endpoints keep student_id explicit during demo integration.
# Existing GET endpoints are retained for existing API clients.
@router.post("/get_student_academic_batches")
def fetch_student_batches(req: StudentRequest, db: Session = Depends(get_db)):
    return get_student_academic_batches(req.student_id, db)


@router.post("/get_my_mentoring_schedules")
def fetch_student_schedules(req: ScheduleListRequest, db: Session = Depends(get_db)):
    import calendar
    from datetime import date
    try:
        year, month = map(int, req.month.split("-"))
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        result = get_my_mentoring_schedules(req.academic_batch_id, req.student_id, db)
        if not isinstance(result, dict):
            return result
        rows = [row for row in result["data"] if row["start_date"] and row["end_date"]
                and row["start_date"] <= last and row["end_date"] >= first]
        rows = list({row["sub_group_date_id"]: row for row in rows}.values())
        rows.sort(key=lambda row: (row["start_date"], row["sub_group_date_id"]), reverse=True)
        return returnSuccess(rows)
    except Exception as e:
        return returnException(str(e))


@router.post("/get_questionnaire")
def fetch_student_questionnaire(req: SessionRequest, db: Session = Depends(get_db)):
    return get_questionnaire(req.schedule_id, req.student_id, db)


@router.post("/get_group_comments")
def fetch_student_group_comments(req: SessionRequest, db: Session = Depends(get_db)):
    return get_group_comments(req.schedule_id, req.student_id, db)


@router.post("/get_individual_comments")
def fetch_student_individual_comments(req: SessionRequest, db: Session = Depends(get_db)):
    return get_individual_comments(req.schedule_id, req.student_id, db)


@router.post("/delete_group_attachment")
def delete_group_attachment(req: DeleteAttachmentRequest, db: Session = Depends(get_db)):
    try:
        mapped = db.query(LMSMapMenteeSchedule).filter(
            LMSMapMenteeSchedule.schedule_id == req.schedule_id,
            LMSMapMenteeSchedule.student_id == req.student_id
        ).first()
        if not mapped:
            raise ValueError("Student is not mapped to this mentoring schedule.")
        row = db.query(LMSMMPSessionSuggestionGenericComments).join(
            LMSMMPSessionSuggestion,
            LMSMMPSessionSuggestion.session_suggestion_id == LMSMMPSessionSuggestionGenericComments.session_suggestion_id
        ).filter(
            LMSMMPSessionSuggestion.schedule_id == req.schedule_id,
            LMSMMPSessionSuggestionGenericComments.generic_comment_id == req.generic_comment_id,
            LMSMMPSessionSuggestionGenericComments.created_by == req.student_id,
            LMSMMPSessionSuggestionGenericComments.user_type == 2
        ).first()
        if not row or not row.attachment:
            raise ValueError("Attachment not found or not owned by this student.")
        # Unlink the attachment; do not delete potentially shared files from disk.
        row.attachment = None
        row.modified_by = req.student_id
        if not (row.comment or "").strip():
            db.delete(row)
        db.commit()
        return returnSuccess("Attachment removed.")
    except Exception as e:
        db.rollback()
        return returnException(str(e))
