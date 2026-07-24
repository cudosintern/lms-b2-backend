from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import json
import os
import shutil

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnSuccess, returnException
from app.db.models import (
    LMSMentoringSchedule,
    LMSMapMenteeSchedule,
    IEMStudents,
    LMSMenteeQuestionnaireResponse,
    LMSMenteeQuestionnaireResponseQue,
    LMSMenteeQuestionnaireResponseOption,
    LMSQuestionnairesQuestions,
    LMSQuestionnairesOptions,
    LMSQuestionnaires,
    LMSMentorsGroup,
    LMSMentorsGroupTerms
)

from .mentoring_schema import CreateSessionPayload, SendChatPayload

router = APIRouter()

# ---------------- 1. FETCH DASHBOARD STATS ----------------
@router.get("/dashboard-stats")
def get_dashboard_stats(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    # Mentees count
    mentees_sql = """
        SELECT COUNT(DISTINCT gm_mentee.student_id)
        FROM lms_group_mentees gm_mentee
        JOIN lms_group_mentors gm ON gm_mentee.group_mentor_id = gm.group_mentor_id
        JOIN lms_mentors_group_terms mgt ON gm.mentors_group_terms_id = mgt.mentors_group_terms_id
        WHERE mgt.academic_batch_id = :curriculum_id AND gm.mentor_id = :mentor_id
    """
    total_mentees = db.execute(text(mentees_sql), {
        "curriculum_id": curriculum_id,
        "mentor_id": mentor_id
    }).scalar()

    # Upcoming sessions (simplified map)
    sessions_sql = """
        SELECT COUNT(DISTINCT s.schedule_id)
        FROM lms_mentoring_schedule s
        JOIN lms_mentoring_sub_group sg ON s.schedule_id = sg.schedule_id
        JOIN lms_mentoring_sub_grp_date sgd ON sg.sub_group_id = sgd.sub_group_id
        JOIN lms_mentors_group_terms mgt ON s.mentors_group_terms_id = mgt.mentors_group_terms_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        WHERE mgt.academic_batch_id = :curriculum_id AND gm.mentor_id = :mentor_id
          AND sgd.start_date >= CURDATE()
    """
    upcoming_sessions = db.execute(text(sessions_sql), {
        "curriculum_id": curriculum_id,
        "mentor_id": mentor_id
    }).scalar()

    return {
        "status": "success",
        "data": {
            "total_mentees": total_mentees or 0,
            "upcoming_sessions": upcoming_sessions or 0,
            "pending_reviews": 0
        }
    }

# ---------------- 2. FETCH SESSION HISTORY ----------------
@router.get("/session/history")
def get_session_history(
    curriculum_id: int,
    month: int, # 1 to 12
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    sql = """
        SELECT s.schedule_id AS id, mgt.academic_batch_id AS curriculum_id, mg.mentors_group_id AS group_id,
               gm.mentor_id, sgd.start_date AS session_date, CAST(sgd.start_time AS CHAR) AS session_time,
               s.session_agenda AS topic, s.session_agenda AS description, mg.mentors_pgm_title AS group_name
        FROM lms_mentoring_schedule s
        JOIN lms_mentoring_sub_group sg ON s.schedule_id = sg.schedule_id
        JOIN lms_mentoring_sub_grp_date sgd ON sg.sub_group_id = sgd.sub_group_id
        JOIN lms_mentors_group_terms mgt ON s.mentors_group_terms_id = mgt.mentors_group_terms_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        JOIN lms_mentors_group mg ON mgt.mentors_group_id = mg.mentors_group_id
        WHERE gm.mentor_id = :mentor_id 
          AND mgt.academic_batch_id = :curriculum_id
          AND MONTH(sgd.start_date) = :month
    """
    results = db.execute(text(sql), {
        "mentor_id": mentor_id,
        "curriculum_id": curriculum_id,
        "month": month
    }).mappings().all()

    return {"status": "success", "data": list(results)}

# ---------------- 3. LIST GROUPS FOR SELECTED CURRICULUM ----------------
@router.get("/groups")
def list_groups(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    sql = """
        SELECT mg.mentors_group_id AS id, mg.mentors_pgm_title AS group_name,
               mgt.academic_batch_id AS curriculum_id, gm.mentor_id, 1 AS status
        FROM lms_mentors_group mg
        JOIN lms_mentors_group_terms mgt ON mg.mentors_group_id = mgt.mentors_group_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        WHERE gm.mentor_id = :mentor_id AND mgt.academic_batch_id = :curriculum_id
    """
    results = db.execute(text(sql), {
        "mentor_id": mentor_id,
        "curriculum_id": curriculum_id
    }).mappings().all()

    return {"status": "success", "data": list(results)}

# ---------------- 4. CREATE NEW MENTORING SESSION ----------------
@router.post("/session/create")
def create_session(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    curriculum_id = payload.get("curriculum_id")
    group_id = payload.get("group_id")
    session_date = payload.get("session_date") # YYYY-MM-DD
    session_time = payload.get("session_time") # HH:MM:SS
    topic = payload.get("topic")
    description = payload.get("description")

    if not curriculum_id or not session_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="curriculum_id and session_date are required"
        )

    mgt_id = db.execute(text("SELECT mentors_group_terms_id FROM lms_mentors_group_terms WHERE mentors_group_id = :group_id LIMIT 1"), {"group_id": group_id}).scalar()
    
    if not mgt_id:
        mgt_id = 1 # Fallback

    db.execute(
        text("""
            INSERT INTO lms_mentoring_schedule (mentors_group_terms_id, questionnaire_id, session_agenda, created_by)
            VALUES (:mgt_id, 1, :topic, :mentor_id)
        """),
        {"mgt_id": mgt_id, "topic": topic, "mentor_id": mentor_id}
    )
    schedule_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    
    db.execute(
        text("""
            INSERT INTO lms_mentoring_sub_group (schedule_id, sub_group_name, location, created_by)
            VALUES (:schedule_id, 'Default', 'Online', :mentor_id)
        """),
        {"schedule_id": schedule_id, "mentor_id": mentor_id}
    )
    sub_group_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    db.execute(
        text("""
            INSERT INTO lms_mentoring_sub_grp_date (sub_group_id, start_date, end_date, start_time, end_time, created_by)
            VALUES (:sub_group_id, :s_date, :s_date, :s_time, :s_time, :mentor_id)
        """),
        {"sub_group_id": sub_group_id, "s_date": session_date, "s_time": session_time, "mentor_id": mentor_id}
    )
    db.commit()

    return {"status": "success", "message": "Mentoring session created successfully"}

# ---------------- 5. FETCH MENTEES & QUESTIONNAIRE RESPONSES ----------------
@router.get("/mentees-responses")
def get_mentees_responses(
    group_id: int,
    questionnaire_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentees_sql = """
        SELECT s.erp_student_id AS mentee_id, s.first_name, s.last_name, s.email_id AS email
        FROM erp_student s
        JOIN lms_group_mentees gm_mentee ON s.erp_student_id = gm_mentee.student_id
        JOIN lms_group_mentors gm ON gm_mentee.group_mentor_id = gm.group_mentor_id
        JOIN lms_mentors_group_terms mgt ON gm.mentors_group_terms_id = mgt.mentors_group_terms_id
        WHERE mgt.mentors_group_id = :group_id
    """
    mentees = db.execute(text(mentees_sql), {"group_id": group_id}).mappings().all()

    data = []
    for mentee in mentees:
        response_sql = """
            SELECT rq.questionnaire_que_id AS question_id, q.question AS question_text, rq.text_answer AS response_value, r.created_date AS submitted_at
            FROM lms_mentee_questionnaire_response r
            JOIN lms_mentee_questionnaire_response_que rq ON r.questionnaire_response_id = rq.questionnaire_response_id
            JOIN lms_questionnaires_questions q ON rq.questionnaire_que_id = q.questionnaire_que_id
            WHERE r.student_id = :mentee_id AND r.questionnaire_id = :questionnaire_id
        """
        responses = db.execute(text(response_sql), {
            "mentee_id": mentee["mentee_id"],
            "questionnaire_id": questionnaire_id
        }).mappings().all()

        data.append({
            "mentee_id": mentee["mentee_id"],
            "first_name": mentee["first_name"],
            "last_name": mentee["last_name"],
            "email": mentee["email"],
            "responses": list(responses)
        })

    return {"status": "success", "data": data}

# ---------------- 6. CHAT MESSAGES & GENERAL GUIDANCE ----------------
@router.get("/sessions/{schedule_id}/chat")
def get_session_chat(
    schedule_id: int,
    mentee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        suggestion = db.execute(
            text("SELECT session_suggestion_id FROM lms_mmp_session_suggestion WHERE schedule_id = :schedule_id LIMIT 1"),
            {"schedule_id": schedule_id}
        ).fetchone()

        if not suggestion:
            return returnSuccess([])

        suggestion_id = suggestion[0]

        if mentee_id is None:
            sql = """
                SELECT c.comment, c.attachment, c.created_by, c.created_date,
                       CONCAT(u.first_name, ' ', COALESCE(u.last_name, '')) AS sender_name
                FROM lms_mmp_session_suggestion_generic_comments c
                LEFT JOIN iems_users u ON c.created_by = u.id
                WHERE c.session_suggestion_id = :suggestion_id
                ORDER BY c.created_date ASC
            """
            rows = db.execute(text(sql), {"suggestion_id": suggestion_id}).mappings().all()
        else:
            sql = """
                SELECT c.comment, c.attachment, c.created_by, c.created_date,
                       CONCAT(u.first_name, ' ', COALESCE(u.last_name, '')) AS sender_name
                FROM lms_mmp_session_suggestion_individual_comments c
                LEFT JOIN iems_users u ON c.created_by = u.id
                WHERE c.session_suggestion_id = :suggestion_id AND c.mentee_id = :mentee_id
                ORDER BY c.created_date ASC
            """
            rows = db.execute(text(sql), {"suggestion_id": suggestion_id, "mentee_id": mentee_id}).mappings().all()

        chat_messages = []
        for r in rows:
            chat_messages.append({
                "comment": r["comment"],
                "attachment": r["attachment"],
                "created_by": r["created_by"],
                "sender_name": r["sender_name"] or "Anonymous",
                "created_date": r["created_date"].strftime("%Y-%m-%d %H:%M:%S") if r["created_date"] else None
            })

        return returnSuccess(chat_messages)
    except Exception as e:
        return returnException(str(e))

@router.post("/sessions/{schedule_id}/chat/send")
def send_session_chat(
    schedule_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("user_id")
        mentee_id = payload.get("mentee_id")
        comment = payload.get("comment", "")
        attachment = payload.get("attachment")

        suggestion = db.execute(
            text("SELECT session_suggestion_id FROM lms_mmp_session_suggestion WHERE schedule_id = :schedule_id LIMIT 1"),
            {"schedule_id": schedule_id}
        ).fetchone()

        if not suggestion:
            db.execute(
                text("INSERT INTO lms_mmp_session_suggestion (schedule_id, created_by) VALUES (:schedule_id, :user_id)"),
                {"schedule_id": schedule_id, "user_id": user_id}
            )
            suggestion_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        else:
            suggestion_id = suggestion[0]

        if mentee_id is None:
            sql = """
                INSERT INTO lms_mmp_session_suggestion_generic_comments 
                (session_suggestion_id, comment, attachment, created_by)
                VALUES (:suggestion_id, :comment, :attachment, :user_id)
            """
            db.execute(text(sql), {
                "suggestion_id": suggestion_id,
                "comment": comment,
                "attachment": attachment,
                "user_id": user_id
            })
        else:
            sql = """
                INSERT INTO lms_mmp_session_suggestion_individual_comments 
                (session_suggestion_id, comment, attachment, created_by, mentee_id)
                VALUES (:suggestion_id, :comment, :attachment, :user_id, :mentee_id)
            """
            db.execute(text(sql), {
                "suggestion_id": suggestion_id,
                "comment": comment,
                "attachment": attachment,
                "user_id": user_id,
                "mentee_id": mentee_id
            })

        db.commit()
        return returnSuccess({"status": "success", "message": "Message sent successfully"})
    except Exception as e:
        db.rollback()
        return returnException(str(e))

# ---------------- 7. FETCH QUESTIONNAIRE ----------------
@router.get("/questionnaires/{id}")
@router.get("/questionnaire/{id}")
def fetch_questionnaire(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        q_sql = "SELECT questionnaire_id AS id, questionnaire_name AS title, message_to_mentees AS description, 1 AS status FROM lms_questionnaires WHERE questionnaire_id = :id"
        q_header = db.execute(text(q_sql), {"id": id}).fetchone()
        if not q_header:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found"
            )

        questions_sql = """
            SELECT questionnaire_que_id AS id, question AS question_text, 'text' AS field_type, NULL AS field_settings, 1 AS status
            FROM lms_questionnaires_questions
            WHERE questionnaire_id = :id
        """
        questions_raw = db.execute(text(questions_sql), {"id": id}).mappings().all()

        questions = []
        for q in questions_raw:
            questions.append({
                "questionnaire_que_id": q["id"],
                "question": q["question_text"],
                "field_type": q["field_type"],
                "field_settings": {},
                "status": q["status"]
            })

        return returnSuccess({
            "id": q_header[0],
            "title": q_header[1],
            "description": q_header[2],
            "status": q_header[3],
            "questions": questions
        })
    except Exception as e:
        return returnException(str(e))

# ---------------- 8. LIST CURRICULUMS FOR LOGGED IN MENTOR ----------------
@router.get("/curriculum")
def list_curriculum(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    sql = """
        SELECT DISTINCT b.academic_batch_id AS curriculum_id, b.academic_batch_code, b.academic_batch_desc
        FROM iems_academic_batch b
        JOIN lms_mentors_group_terms mgt ON b.academic_batch_id = mgt.academic_batch_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        WHERE gm.mentor_id = :mentor_id
    """
    results = db.execute(text(sql), {"mentor_id": mentor_id}).mappings().all()
    return {"status": "success", "data": list(results)}

# ---------------- 9. SESSIONS MENTEES & RESPONSES ----------------
@router.get("/sessions/{schedule_id}/mentees")
def get_session_mentees_list(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        schedule = db.query(LMSMentoringSchedule).filter(LMSMentoringSchedule.schedule_id == schedule_id).first()
        if not schedule:
            return returnException("Mentoring schedule not found.")

        mappings = db.query(LMSMapMenteeSchedule).filter(LMSMapMenteeSchedule.schedule_id == schedule_id).all()
        student_ids = [m.student_id for m in mappings]

        if not student_ids:
            return returnSuccess([])

        students = db.query(IEMStudents).filter(IEMStudents.student_id.in_(student_ids)).all()

        result = []
        for student in students:
            submitted_response = db.query(LMSMenteeQuestionnaireResponse).filter(
                LMSMenteeQuestionnaireResponse.student_id == student.student_id,
                LMSMenteeQuestionnaireResponse.schedule_id == schedule_id
            ).first()

            response_data = None
            if submitted_response:
                answers = []
                response_ques = db.query(LMSMenteeQuestionnaireResponseQue).filter(
                    LMSMenteeQuestionnaireResponseQue.questionnaire_response_id == submitted_response.questionnaire_response_id
                ).all()

                for rq in response_ques:
                    que = db.query(LMSQuestionnairesQuestions).filter(
                        LMSQuestionnairesQuestions.questionnaire_que_id == rq.questionnaire_que_id
                    ).first()
                    
                    sel_opts = db.query(
                        LMSMenteeQuestionnaireResponseOption,
                        LMSQuestionnairesOptions
                    ).join(
                        LMSQuestionnairesOptions,
                        LMSQuestionnairesOptions.questionnaire_options_id ==
                        LMSMenteeQuestionnaireResponseOption.questionnaire_options_id
                    ).filter(
                        LMSMenteeQuestionnaireResponseOption.questionnaire_response_que_id ==
                        rq.questionnaire_response_que_id
                    ).all()

                    selected_options = [
                        {
                            "questionnaire_options_id": opt.questionnaire_options_id,
                            "specification": opt_detail.specification or ""
                        }
                        for opt, opt_detail in sel_opts
                    ]

                    answers.append({
                        "questionnaire_que_id": rq.questionnaire_que_id,
                        "question_text": que.question if que else "",
                        "text_answer": rq.text_answer,
                        "selected_options": selected_options
                    })

                response_data = {
                    "submitted_at": submitted_response.created_date.strftime("%Y-%m-%d %H:%M:%S") if submitted_response.created_date else "Submitted",
                    "answers": answers
                }

            result.append({
                "student_id": student.student_id,
                "student_usn": student.usno,
                "student_name": student.name,
                "student_email": student.email,
                "response": response_data
            })

        return returnSuccess(result)
    except Exception as e:
        return returnException(str(e))

# ---------------- 10. ATTACHMENT UPLOAD ----------------
@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        upload_dir = "uploads/mentoring_comments"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        web_path = f"/uploads/mentoring_comments/{file.filename}"
        return returnSuccess({"file_path": web_path})
    except Exception as e:
        return returnException(str(e))

list_sessions = get_session_history
