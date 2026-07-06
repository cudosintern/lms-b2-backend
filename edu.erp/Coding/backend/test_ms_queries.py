from app.core.database import engine
from sqlalchemy import text

queries = [
    """
        SELECT DISTINCT b.academic_batch_id AS curriculum_id, b.academic_batch_code, b.academic_batch_desc
        FROM iems_academic_batch b
        JOIN lms_mentors_group_terms mgt ON b.academic_batch_id = mgt.academic_batch_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        WHERE gm.mentor_id = 1
    """,
    """
        SELECT s.schedule_id, s.session_agenda, s.questionnaire_id,
               sg.sub_group_id, sg.sub_group_name, sg.location,
               sgd.start_date, sgd.start_time, sgd.end_time
        FROM lms_mentoring_schedule s
        JOIN lms_mentors_group_terms mgt ON s.mentors_group_terms_id = mgt.mentors_group_terms_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        JOIN lms_mentoring_sub_group sg ON s.schedule_id = sg.schedule_id
        JOIN lms_mentoring_sub_grp_date sgd ON sg.sub_group_id = sgd.sub_group_id
        WHERE gm.mentor_id = 1 AND mgt.academic_batch_id = 1
    """,
    """
        SELECT questionnaire_id, questionnaire_name, message_to_mentees, access_level
        FROM lms_questionnaires
        WHERE questionnaire_id = 1
    """,
    """
        SELECT questionnaire_que_id, que_no, question, que_is_mandatory, que_type_id
        FROM lms_questionnaires_questions
        WHERE questionnaire_id = 1
    """,
    """
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
        WHERE s.schedule_id = 1
    """
]

with engine.connect() as conn:
    for i, q in enumerate(queries):
        print(f"Testing Query {i+1}...")
        try:
            conn.execute(text(q + " LIMIT 1"))
            print(f"Query {i+1} OK!")
        except Exception as e:
            print(f"Query {i+1} FAILED: {e}")
