from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import os

from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter()

# ---------------- 1. FETCH DEPARTMENTS ----------------
@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    sql = """
        SELECT dept_id, dept_name 
        FROM iems_department 
        WHERE status = 1
    """
    results = db.execute(text(sql)).mappings().all()
    return {"status": "success", "data": list(results)}

# ---------------- 2. FETCH PROGRAMS BASED ON DEPARTMENT ----------------
@router.get("/programs")
def get_programs(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    sql = """
        SELECT pgm_id, pgm_title, pgm_acronym 
        FROM iems_program 
        WHERE dept_id = :dept_id AND status = 1
    """
    results = db.execute(text(sql), {"dept_id": dept_id}).mappings().all()
    return {"status": "success", "data": list(results)}

# ---------------- 3. FETCH CURRICULUM (ACADEMIC BATCH) ----------------
@router.get("/curriculums")
def get_curriculums(
    dept_id: int,
    pgm_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    # Fetch curriculums assigned to this logged-in mentor (regular or cross-department)
    sql = """
        SELECT DISTINCT ab.academic_batch_id, ab.academic_batch_code, ab.academic_batch_desc
        FROM iems_academic_batch ab
        JOIN lms_mentors_group_terms mgt ON ab.academic_batch_id = mgt.academic_batch_id
        JOIN lms_group_mentors gm ON mgt.mentors_group_terms_id = gm.mentors_group_terms_id
        WHERE gm.mentor_id = :mentor_id 
          AND ab.dept_id = :dept_id 
          AND ab.pgm_id = :pgm_id
          AND ab.status = 1
        UNION
        SELECT DISTINCT ab.academic_batch_id, ab.academic_batch_code, ab.academic_batch_desc
        FROM iems_academic_batch ab
        JOIN lms_cross_dept_users_crclms cduc ON ab.academic_batch_id = cduc.academic_batch_id
        WHERE cduc.faculty_user_id = :mentor_id
          AND ab.dept_id = :dept_id
          AND ab.pgm_id = :pgm_id
          AND ab.status = 1
    """
    results = db.execute(text(sql), {
        "mentor_id": mentor_id,
        "dept_id": dept_id,
        "pgm_id": pgm_id
    }).mappings().all()

    return {"status": "success", "data": list(results)}


# ---------------- 4. FETCH MENTORS & MENTEES LIST ----------------
@router.get("/list")
def get_mentor_mentees_list(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")

    sql = """
        SELECT 
            gm.mentor_id, 
            s.erp_student_id AS mentee_id, 
            s.first_name, 
            s.last_name, 
            s.email_id AS email,
            s.erp_student_usn AS usno
        FROM erp_student s
        JOIN lms_group_mentees gm_mentee ON s.erp_student_id = gm_mentee.student_id
        JOIN lms_group_mentors gm ON gm_mentee.group_mentor_id = gm.group_mentor_id
        JOIN lms_mentors_group_terms mgt ON gm.mentors_group_terms_id = mgt.mentors_group_terms_id
        WHERE mgt.academic_batch_id = :curriculum_id
    """
    mentees = db.execute(text(sql), {"curriculum_id": curriculum_id, "mentor_id": mentor_id}).mappings().all()

    return {"status": "success", "data": list(mentees)}

# ---------------- 5. EXPORT TO PDF ----------------
@router.get("/export/pdf")
def export_mentor_mentees_pdf(
    curriculum_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    mentor_id = current_user.get("user_id")
    
    # Fetch Data for PDF
    sql = """
        SELECT 
            s.first_name, 
            s.last_name, 
            s.erp_student_usn AS usno
        FROM erp_student s
        JOIN lms_group_mentees gm_mentee ON s.erp_student_id = gm_mentee.student_id
        JOIN lms_group_mentors gm ON gm_mentee.group_mentor_id = gm.group_mentor_id
        JOIN lms_mentors_group_terms mgt ON gm.mentors_group_terms_id = mgt.mentors_group_terms_id
        WHERE mgt.academic_batch_id = :curriculum_id
    """
    mentees = db.execute(text(sql), {"curriculum_id": curriculum_id}).mappings().all()

    # Generate PDF
    file_path = f"app/uploads/mentor_mentees_{curriculum_id}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Mentor & Mentee List - Curriculum {curriculum_id}")
    
    c.setFont("Helvetica", 12)
    y_position = height - 100
    
    c.drawString(50, y_position, "USN")
    c.drawString(200, y_position, "Mentee Name")
    y_position -= 20
    
    for mentee in mentees:
        if y_position < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 50
            
        name = f"{mentee['first_name']} {mentee['last_name']}"
        usno = mentee['usno'] or "N/A"
        
        c.drawString(50, y_position, str(usno))
        c.drawString(200, y_position, name)
        y_position -= 20
        
    c.save()

    return FileResponse(path=file_path, filename=f"mentor_mentees_{curriculum_id}.pdf", media_type='application/pdf')
