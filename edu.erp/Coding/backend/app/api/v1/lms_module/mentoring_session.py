from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from .mentoring_session_schema import (
    MentoringSessionCreate,
    MessageCreate
)

router = APIRouter(tags=["Mentoring Session"])

# -------------------------------------------------------------------------
# 1. Fetch list of curriculum assigned to logged in faculty
# -------------------------------------------------------------------------
@router.get("/curriculum")
def list_mentor_curriculum(
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

# -------------------------------------------------------------------------
# 2. List all mentoring sessions of selected curriculum & month
# -------------------------------------------------------------------------
@router.get("/sessions")
def list_mentoring_sessions(
    curriculum_id: int,
    month: Optional[str] = None, # format: YYYY-MM
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")
    
    # We fetch the schedule details including dates from the sub-groups
    sql = """
        SELECT s.schedule_id, s.session_agenda, s.questionnaire_id,
               sg.sub_group_id, sg.sub_group_name, sg.location,
               sgd.start_date, sgd.start_time, sgd.end_time
        FROM lms_mentoring_schedule s
        JOIN lms_mentors_group_terms mgt ON s.mentors_group_terms_id = mgt.mentors_group_terms_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        JOIN lms_mentoring_sub_group sg ON s.schedule_id = sg.schedule_id
        JOIN lms_mentoring_sub_grp_date sgd ON sg.sub_group_id = sgd.sub_group_id
        WHERE gm.mentor_id = :mentor_id AND mgt.academic_batch_id = :curriculum_id
    """
    params = {"mentor_id": mentor_id, "curriculum_id": curriculum_id}
    
    if month:
        sql += " AND DATE_FORMAT(sgd.start_date, '%Y-%m') = :month"
        params["month"] = month
        
    sql += " ORDER BY sgd.start_date ASC, sgd.start_time ASC"
    
    results = db.execute(text(sql), params).mappings().all()
    
    # Group results by schedule_id if needed, but returning flat list is fine too
    return {"status": "success", "data": list(results)}

# -------------------------------------------------------------------------
# 3. Create session for selected curriculum & month (mapped by mentors_group_terms_id)
# -------------------------------------------------------------------------
@router.post("/sessions")
def create_mentoring_session(
    payload: MentoringSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    creator_id = current_user.get("user_id")
    
    # 1. Insert Schedule
    sched_sql = """
        INSERT INTO lms_mentoring_schedule 
        (mentors_group_terms_id, questionnaire_id, session_agenda, created_by)
        VALUES (:mgt_id, :q_id, :agenda, :created_by)
    """
    res = db.execute(text(sched_sql), {
        "mgt_id": payload.mentors_group_terms_id,
        "q_id": payload.questionnaire_id,
        "agenda": payload.session_agenda,
        "created_by": creator_id
    })
    schedule_id = res.lastrowid
    
    # 2. Insert Sub-Groups and Dates
    for sg in payload.sub_groups:
        sg_sql = """
            INSERT INTO lms_mentoring_sub_group
            (schedule_id, sub_group_name, location, created_by)
            VALUES (:sched_id, :sg_name, :loc, :created_by)
        """
        sg_res = db.execute(text(sg_sql), {
            "sched_id": schedule_id,
            "sg_name": sg.sub_group_name,
            "loc": sg.location,
            "created_by": creator_id
        })
        sub_group_id = sg_res.lastrowid
        
        sgd_sql = """
            INSERT INTO lms_mentoring_sub_grp_date
            (sub_group_id, start_date, start_time, end_time, created_by)
            VALUES (:sg_id, :s_date, :s_time, :e_time, :created_by)
        """
        db.execute(text(sgd_sql), {
            "sg_id": sub_group_id,
            "s_date": sg.start_date,
            "s_time": sg.start_time,
            "e_time": sg.end_time,
            "created_by": creator_id
        })
        
    db.commit()
    return {"status": "success", "message": "Session created successfully", "data": {"schedule_id": schedule_id}}

# -------------------------------------------------------------------------
# 4. Fetch questionnaire & its respective field setting (allow/disallow)
# -------------------------------------------------------------------------
@router.get("/questionnaires/{questionnaire_id}")
def get_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    q_sql = """
        SELECT questionnaire_id, questionnaire_name, message_to_mentees, access_level
        FROM lms_questionnaires
        WHERE questionnaire_id = :q_id
    """
    questionnaire = db.execute(text(q_sql), {"q_id": questionnaire_id}).mappings().first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
        
    que_sql = """
        SELECT questionnaire_que_id, que_no, question, que_is_mandatory, que_type_id
        FROM lms_questionnaires_questions
        WHERE questionnaire_id = :q_id
        ORDER BY que_no ASC
    """
    questions = db.execute(text(que_sql), {"q_id": questionnaire_id}).mappings().all()
    
    return {
        "status": "success", 
        "data": {
            "questionnaire": dict(questionnaire),
            "questions": list(questions)
        }
    }

# -------------------------------------------------------------------------
# 5. List mentees of mentoring session & view responses
# -------------------------------------------------------------------------
@router.get("/sessions/{schedule_id}/mentees")
def list_session_mentees(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Fetch mentees connected to the schedule's mentors_group_terms_id
    # Also join with questionnaire response to check if they submitted
    sql = """
        SELECT st.erp_student_id, st.first_name, st.last_name, st.erp_student_usn AS usno, st.email_id AS email,
               IF(qr.questionnaire_response_id IS NOT NULL, 1, 0) AS has_responded,
               qr.questionnaire_response_id
        FROM lms_mentoring_schedule s
        JOIN lms_mentors_group_terms mgt ON s.mentors_group_terms_id = mgt.mentors_group_terms_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        JOIN lms_group_mentees gm_mentee ON gm.group_mentor_id = gm_mentee.group_mentor_id
        JOIN erp_student st ON gm_mentee.student_id = st.erp_student_id
        LEFT JOIN lms_mentee_questionnaire_response qr 
               ON qr.schedule_id = s.schedule_id AND qr.student_id = st.erp_student_id
        WHERE s.schedule_id = :schedule_id
    """
    mentees = db.execute(text(sql), {"schedule_id": schedule_id}).mappings().all()
    
    return {"status": "success", "data": list(mentees)}

# -------------------------------------------------------------------------
# 6. Send messages in group or chat with individual mentee
# -------------------------------------------------------------------------
@router.post("/sessions/{schedule_id}/messages")
def send_session_message(
    schedule_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("user_id")
    
    # Check or create lms_mmp_session_suggestion for this schedule
    sugg_sql = "SELECT session_suggestion_id FROM lms_mmp_session_suggestion WHERE schedule_id = :schedule_id LIMIT 1"
    suggestion = db.execute(text(sugg_sql), {"schedule_id": schedule_id}).fetchone()
    
    if not suggestion:
        ins_sugg = "INSERT INTO lms_mmp_session_suggestion (schedule_id, created_by) VALUES (:sched, :uid)"
        res = db.execute(text(ins_sugg), {"sched": schedule_id, "uid": user_id})
        session_suggestion_id = res.lastrowid
    else:
        session_suggestion_id = suggestion[0]
        
    if not payload.comment or not payload.comment.strip():
        if not payload.attachment:
            raise HTTPException(status_code=400, detail="Either comment or attachment must be provided.")

    if payload.mentee_id is not None and payload.mentee_id > 0:
        # Individual Comment
        ins_indiv = """
            INSERT INTO lms_mmp_session_suggestion_individual_comments
            (session_suggestion_id, comment, attachment, suggestion_type, from_user_id, mentee_id, from_user_type, created_by)
            VALUES (:s_id, :comment, :att, :stype, :uid, :mentee, :utype, :uid)
        """
        db.execute(text(ins_indiv), {
            "s_id": session_suggestion_id,
            "comment": payload.comment,
            "att": payload.attachment,
            "stype": payload.suggestion_type,
            "uid": user_id,
            "mentee": payload.mentee_id,
            "utype": payload.user_type
        })
    else:
        # Generic Group Comment
        ins_generic = """
            INSERT INTO lms_mmp_session_suggestion_generic_comments
            (session_suggestion_id, comment, attachment, suggestion_type, user_type, created_by)
            VALUES (:s_id, :comment, :att, :stype, :utype, :uid)
        """
        db.execute(text(ins_generic), {
            "s_id": session_suggestion_id,
            "comment": payload.comment,
            "att": payload.attachment,
            "stype": payload.suggestion_type,
            "utype": payload.user_type,
            "uid": user_id
        })
        
    db.commit()
    return {"status": "success", "message": "Message sent successfully"}
