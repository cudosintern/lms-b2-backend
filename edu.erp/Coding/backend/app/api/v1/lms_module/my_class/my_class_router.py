from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime
from typing import Optional
from app.core.database import get_db

from .my_class_schema import *

router = APIRouter()

@router.get("/dropdowns", response_model=StudentDropdownResponse)
def get_student_dropdowns(
    student_id: int = Query(...),
    academic_batch_id: Optional[int] = Query(None),
    semester_id: Optional[int] = Query(None),
    course_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    # -------------------------
    # CURRICULUM
    # -------------------------
    curriculum_query = """
        SELECT ab.academic_batch_id, ab.academic_batch_desc AS batch_name
        FROM iems_students s
        JOIN iems_academic_batch ab ON s.academic_batch_id = ab.academic_batch_id
        WHERE s.student_id = :student_id
    """
    curriculum = db.execute(text(curriculum_query), {"student_id": student_id}).fetchall()

    # -------------------------
    # TERMS (SEMESTERS)
    # -------------------------
    term_query = "SELECT semester_id, semester_desc AS semester_name FROM iems_semester"
    if academic_batch_id:
        # If we want to filter semesters by academic batch, we might join with a mapping table.
        # For now, keeping it simple as per existing patterns unless a specific mapping exists.
        pass
    terms = db.execute(text(term_query)).fetchall()

    # -------------------------
    # COURSES + SECTIONS
    # -------------------------
    # Filter courses and sections based on student and selected filters
    cs_query = """
        SELECT DISTINCT
        c.crs_id AS course_id,
        c.crs_code AS course_code,
        c.crs_title AS course_title,
        s.id AS section_id,
        s.section AS section_name
    FROM lms_lesson_schedule ls

    JOIN iems_courses c 
        ON c.crs_id = ls.crs_id

    JOIN iems_section s 
        ON s.id = ls.section_id

    WHERE 1=1
    """
    params = {"student_id": student_id}
    
    if academic_batch_id:
        cs_query += " AND c.academic_batch_id = :batch_id"
        params["batch_id"] = academic_batch_id
    if semester_id:
        cs_query += " AND ls.semester_id = :semester_id"
        params["semester_id"] = semester_id
    if course_id:
        cs_query += " AND c.crs_id = :course_id"
        params["course_id"] = course_id

    course_section = db.execute(text(cs_query), params).fetchall()

    # Split courses & sections
    courses = []
    sections = []
    seen_courses = set()
    seen_sections = set()

    for row in course_section:
        if row.course_id not in seen_courses:
            courses.append({
                "course_id": row.course_id,
                "course_code": row.course_code,
                "course_title": row.course_title
            })
            seen_courses.add(row.course_id)

        if row.section_id not in seen_sections:
            sections.append({
                "section_id": row.section_id,
                "section_name": row.section_name
            })
            seen_sections.add(row.section_id)

    return {
        "curriculum": [
            {"academic_batch_id": c.academic_batch_id, "academic_batch_name": c.batch_name} 
            for c in curriculum
        ],
        "terms": [
            {"semester_id": t.semester_id, "semester_name": t.semester_name} 
            for t in terms
        ],
        "courses": courses,
        "sections": sections
    }

@router.get("/class-list", response_model=ClassListResponse)
def get_class_list(
    student_id: int,
    course_id: Optional[int] = None,
    section_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    selected_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = """
        SELECT 
            ls.lesson_schedule_id,
            ls.crs_id AS course_id,
            c.crs_title AS course_title,
            ls.section_id,
            s.section AS section_name,
            ls.plan_date AS class_date,
            ls.start_time,
            ls.end_time,
            ls.video_link,
            t.topic_id,
            t.topic_title,
            (SELECT portion_ref FROM lms_map_portion_ls ml WHERE ml.lesson_schedule_id = ls.lesson_schedule_id LIMIT 1) as portion_to_be_covered,
            CASE
    WHEN DATE(ls.plan_date) > CURDATE() THEN 'Scheduled'
    
    WHEN DATE(ls.plan_date) = CURDATE()
         AND TIME(NOW()) BETWEEN ls.start_time AND ls.end_time THEN 'Active'
    
    WHEN DATE(ls.plan_date) < CURDATE() 
         OR (DATE(ls.plan_date) = CURDATE() AND TIME(NOW()) > ls.end_time)
         THEN 'Completed'
    
    ELSE 'Scheduled'
END AS status
        FROM lms_lesson_schedule ls
        JOIN iems_courses c ON c.crs_id = ls.crs_id
        JOIN iems_section s ON s.id = ls.section_id
        LEFT JOIN topic_lesson_schedule tls ON tls.lesson_schedule_id = ls.lesson_schedule_id
        LEFT JOIN cudos_topic t ON t.topic_id = tls.topic_id
        JOIN cudos_map_courseto_student cs ON cs.crs_id = ls.crs_id AND cs.section_id = ls.section_id
        WHERE cs.student_id = :student_id
    """
    params = {"student_id": student_id}
    
    if course_id:
        query += " AND ls.crs_id = :course_id"
        params["course_id"] = course_id
    if section_id:
        query += " AND ls.section_id = :section_id"
        params["section_id"] = section_id
    if semester_id:
        query += " AND ls.semester_id = :semester_id"
        params["semester_id"] = semester_id
    if selected_date:
        query += " AND DATE(ls.plan_date) = :selected_date"
        params["selected_date"] = selected_date

    result = db.execute(text(query), params).fetchall()

    return {
        "classes": [
            {
                "lesson_schedule_id": r.lesson_schedule_id,
                "topic_id": r.topic_id,
                "course_id": r.course_id,
                "course_name": r.course_title,
                "section_id": r.section_id,
                "section_name": r.section_name,
                "topic_title": r.topic_title,
                "portion_to_be_covered": r.portion_to_be_covered,
                "status": r.status,
                "class_date": r.class_date,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "video_link": r.video_link
            } for r in result
        ]
    }

# # -------------------------------
# # CRUD OPERATIONS
# # -------------------------------

# @router.post("/create-class")
# def create_class(request: ClassCreateRequest, db: Session = Depends(get_db)):
#     try:
#         # Insert into lms_lesson_schedule
#         query = """
#             INSERT INTO lms_lesson_schedule 
#             (academic_batch_id, semester_id, crs_id, section_id, plan_date, start_time, end_time, video_link, status)
#             VALUES (:batch_id, :sem_id, :crs_id, :sec_id, :p_date, :s_time, :e_time, :v_link, 1)
#         """
#         result = db.execute(text(query), {
#             "batch_id": request.academic_batch_id,
#             "sem_id": request.semester_id,
#             "crs_id": request.course_id,
#             "sec_id": request.section_id,
#             "p_date": request.plan_date,
#             "s_time": request.start_time,
#             "e_time": request.end_time,
#             "v_link": request.video_link
#         })
#         lls_id = result.lastrowid
        
#         # Sync lesson_schedule_id column with lls_id if needed
#         db.execute(text("UPDATE lms_lesson_schedule SET lesson_schedule_id = :id WHERE lls_id = :id"), {"id": lls_id})
        
#         # If topic_id provided, also map it in topic_lesson_schedule
#         if request.topic_id:
#             db.execute(text("""
#                 INSERT INTO topic_lesson_schedule (lesson_schedule_id, topic_id, academic_batch_id, course_id, semester_id, conduction_date)
#                 VALUES (:ls_id, :t_id, :batch_id, :crs_id, :sem_id, :c_date)
#             """), {
#                 "ls_id": lls_id,
#                 "t_id": request.topic_id,
#                 "batch_id": request.academic_batch_id,
#                 "crs_id": request.course_id,
#                 "sem_id": request.semester_id,
#                 "c_date": request.plan_date
#             })
            
#         db.commit()
#         return {"success": True, "message": "Class created successfully", "lesson_schedule_id": lls_id}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @router.put("/update-class/{lls_id}")
# def update_class(lls_id: int, request: ClassUpdateRequest, db: Session = Depends(get_db)):
#     try:
#         # Update lms_lesson_schedule
#         update_ls_query = "UPDATE lms_lesson_schedule SET "
#         ls_params = {"lls_id": lls_id}
#         ls_updates = []
        
#         if request.plan_date:
#             ls_updates.append("plan_date = :p_date")
#             ls_params["p_date"] = request.plan_date
#         if request.start_time:
#             ls_updates.append("start_time = :s_time")
#             ls_params["s_time"] = request.start_time
#         if request.end_time:
#             ls_updates.append("end_time = :e_time")
#             ls_params["e_time"] = request.end_time
#         if request.video_link is not None:
#             ls_updates.append("video_link = :v_link")
#             ls_params["v_link"] = request.video_link
            
#         if ls_updates:
#             update_ls_query += ", ".join(ls_updates) + " WHERE lls_id = :lls_id"
#             db.execute(text(update_ls_query), ls_params)

#         # Update topic_lesson_schedule / status
#         if request.topic_id is not None or request.status is not None:
#             # Check if entry exists using lls_id as lesson_schedule_id
#             exists = db.execute(text("SELECT 1 FROM topic_lesson_schedule WHERE lesson_schedule_id = :ls_id"), {"ls_id": lls_id}).fetchone()
            
#             if exists:
#                 tls_updates = []
#                 tls_params = {"ls_id": lls_id}
#                 if request.topic_id is not None:
#                     tls_updates.append("topic_id = :t_id")
#                     tls_params["t_id"] = request.topic_id
#                 if request.status == "Completed":
#                     tls_updates.append("actual_delivery_date = :a_date")
#                     tls_params["a_date"] = date.today()
                
#                 if tls_updates:
#                     db.execute(text("UPDATE topic_lesson_schedule SET " + ", ".join(tls_updates) + " WHERE lesson_schedule_id = :ls_id"), tls_params)
#             elif request.topic_id:
#                 # Need batch/course for new insert in topic_lesson_schedule
#                 ls_info = db.execute(text("SELECT academic_batch_id, crs_id, semester_id FROM lms_lesson_schedule WHERE lls_id = :lls_id"), {"lls_id": lls_id}).fetchone()
#                 if ls_info:
#                     db.execute(text("""
#                         INSERT INTO topic_lesson_schedule (lesson_schedule_id, topic_id, academic_batch_id, course_id, semester_id, conduction_date)
#                         VALUES (:ls_id, :t_id, :batch_id, :crs_id, :sem_id, :c_date)
#                     """), {
#                         "ls_id": lls_id,
#                         "t_id": request.topic_id,
#                         "batch_id": ls_info.academic_batch_id,
#                         "crs_id": ls_info.crs_id,
#                         "sem_id": ls_info.semester_id,
#                         "c_date": date.today()
#                     })

#         db.commit()
#         return {"success": True, "message": "Class updated successfully"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/delete-class/{lls_id}")
# def delete_class(lls_id: int, db: Session = Depends(get_db)):
#     try:
#         # Delete from dependent tables first
#         db.execute(text("DELETE FROM topic_lesson_schedule WHERE lesson_schedule_id = :ls_id"), {"ls_id": lls_id})
#         db.execute(text("DELETE FROM lms_map_portion_ls WHERE lesson_schedule_id = :ls_id"), {"ls_id": lls_id})
#         # Delete from main table
#         db.execute(text("DELETE FROM lms_lesson_schedule WHERE lls_id = :lls_id"), {"lls_id": lls_id})
        
#         db.commit()
#         return {"success": True, "message": "Class deleted successfully"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=str(e))