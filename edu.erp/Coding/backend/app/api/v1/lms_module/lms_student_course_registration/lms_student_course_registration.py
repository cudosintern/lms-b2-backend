from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, validator, root_validator
from typing import List, Optional, Any, Dict
from datetime import datetime
import tempfile
import os
import io
import aiomysql
import traceback

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.core.database import get_db_pool
from app.utils.auth_helper import get_current_user
from app.utils.http_return_helper import returnException, returnSuccess

router = APIRouter()

# ============================================
# Helper Functions
# ============================================

def format_time_for_display(time_value):
    """Format time for display"""
    if time_value:
        total_seconds = int(time_value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        suffix = "AM" if hours < 12 else "PM"
        display_hour = hours % 12 or 12
        return f"{display_hour:02d}:{minutes:02d} {suffix}"
    return None


# ============================================
# Pydantic Models
# ============================================

class CourseCreditSummaryItem(BaseModel):
    type_of_course: str
    total_credits: float

class CourseTypeLimitItem(BaseModel):
    course_type_desc: str
    stud_min_crs_enroll: Optional[float] = 0
    stud_max_crs_enroll: Optional[float] = 0
    students_registered: Optional[int] = 0

class StudentRegisteredItem(BaseModel):
    course_type_desc: str
    students_registered: int

class CourseDetailItem(BaseModel):
    course_title: str
    credits: float
    students_registered: int

class CourseTypeDetail(BaseModel):
    type: str
    courses: List[CourseDetailItem]

class ExportPDFRequest(BaseModel):
    institute_name: Optional[str] = ""
    department: str
    program: str
    curriculum: str
    term: str
    startDate: str
    startTime: str
    endDate: str
    endTime: str
    totalCredits: float
    ownCurriculumElectives: int
    otherCurriculumElectives: int
    minCredits: float
    maxCredits: float
    courseCreditSummary: List[CourseCreditSummaryItem]
    courseTypeLimits: List[CourseTypeLimitItem]
    studentsRegistered: List[StudentRegisteredItem]
    courseDetails: Optional[List[CourseTypeDetail]] = []

class CourseLimitUpdate(BaseModel):
    course_type: str
    min_credits: Optional[float] = 0
    max_students: Optional[int] = 0

class RegistrationUpdateRequest(BaseModel):
    semester_id: int
    min_credits: Optional[float] = None
    total_credits: Optional[float] = None
    own_curriculum_electives: Optional[int] = None
    other_curriculum_electives: Optional[int] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    course_limits: Optional[List[CourseLimitUpdate]] = []


# ============================================
# GET REGISTRATION SETUP
# ============================================

@router.get("/registration-setup/{semester_id}")
async def get_registration_setup(semester_id: int):
    """Get complete registration setup data with student counts"""
    print(f"\n{'='*60}")
    print(f"🔍 [registration-setup] Called with semester_id: {semester_id}")
    
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get semester data
                await cursor.execute("""
                    SELECT 
                        semester_id,
                        semester,
                        academic_batch_id,
                        enroll_start_date,
                        enroll_start_time,
                        enroll_end_date,
                        enroll_end_time,
                        sem_min_credits,
                        sem_max_credits,
                        own_crclm_elective,
                        other_crclm_elective
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                
                semester_data = await cursor.fetchone()
                if not semester_data:
                    return returnException(f"Semester with ID {semester_id} not found")
                
                academic_batch_id = semester_data['academic_batch_id']
                semester_num = semester_data['semester']
                
                print(f"🔍 academic_batch_id: {academic_batch_id}, semester_num: {semester_num}")
                
                # Get course structure with student counts
                await cursor.execute("""
                    SELECT 
                        ct.course_type_desc AS course_type,
                        lms.crs_type_total AS total_credits,
                        lms.stud_min_crs_enroll AS min_credits,
                        lms.stud_max_crs_enroll AS max_credits,
                        COALESCE((
                            SELECT COUNT(DISTINCT sc.regno)
                            FROM iems_student_courses sc
                            JOIN iems_courses c ON c.crs_code = sc.crs_code
                            WHERE c.course_type_id = lms.crs_type_id
                            AND c.semester = %s
                            AND c.academic_batch_id = %s
                            AND sc.is_registered = 1
                            AND c.status = 1
                        ), 0) AS students_registered
                    FROM lms_academic_batch_semester_crs_structure lms
                    LEFT JOIN iems_course_type ct ON ct.course_type_id = lms.crs_type_id
                    WHERE lms.academic_batch_id = %s 
                        AND lms.semester_id = %s
                    ORDER BY ct.course_type_desc
                """, (semester_num, academic_batch_id, academic_batch_id, semester_id))
                
                course_structure = await cursor.fetchall()
                print(f"🔍 course_structure rows: {len(course_structure)}")
                
                # Format response
                response = {
                    "semester": {
                        "start_date": semester_data['enroll_start_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_start_date') else None,
                        "start_time": format_time_for_display(semester_data.get('enroll_start_time')) if semester_data.get('enroll_start_time') else None,
                        "end_date": semester_data['enroll_end_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_end_date') else None,
                        "end_time": format_time_for_display(semester_data.get('enroll_end_time')) if semester_data.get('enroll_end_time') else None,
                        "min_credit": semester_data.get('sem_min_credits') or 0,
                        "max_credit": semester_data.get('sem_max_credits') or 0,
                        "own_elective": semester_data.get('own_crclm_elective') or 0,
                        "other_elective": semester_data.get('other_crclm_elective') or 0
                    },
                    "course_structure": [
                        {
                            "course_type": item['course_type'] or f"Type {idx + 1}",
                            "total_credits": float(item['total_credits']) if item['total_credits'] else 0,
                            "min_credits": float(item['min_credits']) if item['min_credits'] else 0,
                            "max_credits": float(item['max_credits']) if item['max_credits'] else 0,
                            "students_registered": int(item['students_registered']) if item['students_registered'] else 0
                        }
                        for idx, item in enumerate(course_structure)
                    ]
                }
                
                return returnSuccess(response)
                
    except Exception as e:
        print(f"❌ Error in get_registration_setup: {str(e)}")
        traceback.print_exc()
        return returnException(str(e))


# ============================================
# GET CURRICULUMS
# ============================================

@router.get("/curriculums/{program_id}")
async def get_curriculums(program_id: int):
    """Get curriculums for a specific program"""
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT
                        ab.academic_batch_id AS curriculum_id,
                        CONCAT(
                            p.pgm_acronym,
                            ' in ',
                            d.dept_name,
                            ' ',
                            ab.start_year,
                            '-',
                            ab.end_year
                        ) AS curriculum_name,
                        ab.pgm_id
                    FROM iems_academic_batch ab
                    JOIN iems_program p ON ab.pgm_id = p.pgm_id
                    JOIN iems_department d ON ab.dept_id = d.dept_id
                    WHERE ab.pgm_id = %s
                    ORDER BY ab.academic_batch_id
                """, (program_id,))
                
                data = await cursor.fetchall()
                return returnSuccess(data, "Curriculums fetched successfully")
                
    except Exception as e:
        print(f"Error in get_curriculums: {str(e)}")
        return returnException(str(e))


# ============================================
# GET TERMS
# ============================================

@router.get("/terms/{curriculum_id}")
async def get_terms(curriculum_id: int):
    """Get terms for a specific curriculum"""
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT
                        semester_id,
                        CONCAT(semester, ' - Semester') AS term_name
                    FROM iems_semester
                    WHERE academic_batch_id = %s
                    AND status = 1
                    ORDER BY semester
                """, (curriculum_id,))
                data = await cursor.fetchall()
                return returnSuccess(data, "Terms fetched successfully")
                
    except Exception as e:
        print(f"Error in get_terms: {str(e)}")
        return returnException(str(e))


# ============================================
# GET COURSE ENROLL DETAILS
# ============================================

@router.get("/course-enroll-details/{semester_id}/{course_type}")
async def get_course_enroll_details(semester_id: int, course_type: str):
    """Get courses for a specific course type with registered students count"""
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get semester info
                await cursor.execute("""
                    SELECT semester, academic_batch_id
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                
                semester_info = await cursor.fetchone()
                if not semester_info:
                    return returnException("Semester not found")
                
                semester_num = semester_info['semester']
                academic_batch_id = semester_info['academic_batch_id']
                
                # Find course type
                await cursor.execute("""
                    SELECT course_type_id
                    FROM iems_course_type
                    WHERE course_type_desc = %s OR course_type_desc LIKE %s
                """, (course_type, f"%{course_type}%"))
                
                course_type_result = await cursor.fetchone()
                
                if not course_type_result:
                    return returnException(f"Course type '{course_type}' not found")
                
                course_type_id = course_type_result['course_type_id']
                
                # Get courses with registered count
                await cursor.execute("""
                    SELECT
                        c.crs_id,
                        c.crs_code,
                        c.crs_title,
                        c.total_credits,
                        COALESCE((
                            SELECT COUNT(DISTINCT sc.regno)
                            FROM iems_student_courses sc
                            WHERE sc.crs_code = c.crs_code
                            AND sc.is_registered = 1
                        ), 0) AS registered_count
                    FROM iems_courses c
                    WHERE c.academic_batch_id = %s
                        AND c.semester = %s
                        AND c.course_type_id = %s
                        AND c.status = 1
                    ORDER BY c.crs_code
                """, (academic_batch_id, semester_num, course_type_id))
                
                courses = await cursor.fetchall()
                return returnSuccess(courses)
                
    except Exception as e:
        print(f"❌ Error in get_course_enroll_details: {str(e)}")
        traceback.print_exc()
        return returnException(str(e))


# ============================================
# UPDATE REGISTRATION SETTINGS - COMPLETE FIX
# ============================================

@router.post("/update-registration-settings")
async def update_registration_settings(request: RegistrationUpdateRequest):
    """Update registration settings - COMPLETE FIX with course min_credits"""
    print(f"\n{'='*80}")
    print(f"🔍 [UPDATE] Request received")
    print(f"🔍 [UPDATE] semester_id: {request.semester_id}")
    print(f"🔍 [UPDATE] min_credits: {request.min_credits}")
    print(f"🔍 [UPDATE] total_credits: {request.total_credits}")
    print(f"🔍 [UPDATE] own_curriculum_electives: {request.own_curriculum_electives}")
    print(f"🔍 [UPDATE] other_curriculum_electives: {request.other_curriculum_electives}")
    print(f"🔍 [UPDATE] course_limits count: {len(request.course_limits) if request.course_limits else 0}")
    if request.course_limits:
        for idx, limit in enumerate(request.course_limits):
            print(f"   [{idx+1}] {limit.course_type}: min_credits={limit.min_credits}, max_students={limit.max_students}")
    print(f"{'='*80}")
    
    pool = None
    conn = None
    
    try:
        pool = await get_db_pool()
        if pool is None:
            print(f"❌ [UPDATE] Database pool is None")
            return returnException("Database connection failed")
        
        conn = await pool.acquire()
        print(f"✅ [UPDATE] Connection acquired")
        
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Check database
            await cursor.execute("SELECT DATABASE() as db")
            db_info = await cursor.fetchone()
            print(f"🔍 [UPDATE] Connected to database: {db_info}")
            
            # Check if semester exists
            await cursor.execute("SELECT * FROM iems_semester WHERE semester_id = %s", (request.semester_id,))
            semester_before = await cursor.fetchone()
            print(f"🔍 [UPDATE] Semester before update: {semester_before}")
            
            if not semester_before:
                print(f"❌ [UPDATE] Semester {request.semester_id} does NOT exist!")
                return returnException(f"Semester {request.semester_id} not found", 404)
            
            # Build update query for semester
            update_fields = []
            params = []
            
            if request.min_credits is not None:
                update_fields.append("sem_min_credits = %s")
                params.append(request.min_credits)
                print(f"   ✅ sem_min_credits = {request.min_credits}")
            
            if request.total_credits is not None:
                update_fields.append("sem_max_credits = %s")
                params.append(request.total_credits)
                print(f"   ✅ sem_max_credits = {request.total_credits}")
                
            if request.own_curriculum_electives is not None:
                update_fields.append("own_crclm_elective = %s")
                params.append(request.own_curriculum_electives)
                print(f"   ✅ own_crclm_elective = {request.own_curriculum_electives}")
                
            if request.other_curriculum_electives is not None:
                update_fields.append("other_crclm_elective = %s")
                params.append(request.other_curriculum_electives)
                print(f"   ✅ other_crclm_elective = {request.other_curriculum_electives}")
                
            if request.start_date:
                update_fields.append("enroll_start_date = STR_TO_DATE(%s, '%%d-%%m-%%Y')")
                params.append(request.start_date)
                print(f"   ✅ enroll_start_date = {request.start_date}")
                
            if request.start_time:
                update_fields.append("enroll_start_time = STR_TO_DATE(%s, '%%h:%%i %%p')")
                params.append(request.start_time)
                print(f"   ✅ enroll_start_time = {request.start_time}")
                
            if request.end_date:
                update_fields.append("enroll_end_date = STR_TO_DATE(%s, '%%d-%%m-%%Y')")
                params.append(request.end_date)
                print(f"   ✅ enroll_end_date = {request.end_date}")
                
            if request.end_time:
                update_fields.append("enroll_end_time = STR_TO_DATE(%s, '%%h:%%i %%p')")
                params.append(request.end_time)
                print(f"   ✅ enroll_end_time = {request.end_time}")
            
            if update_fields:
                params.append(request.semester_id)
                query = f"""
                    UPDATE iems_semester
                    SET {', '.join(update_fields)}
                    WHERE semester_id = %s
                """
                
                print(f"\n🔍 [UPDATE] Executing query:")
                print(f"   Query: {query}")
                print(f"   Params: {params}")
                
                await cursor.execute(query, params)
                rows_affected = cursor.rowcount
                print(f"\n📊 [UPDATE] Rows affected: {rows_affected}")
                await conn.commit()
                print(f"✅ [UPDATE] Transaction committed successfully!")
            else:
                print(f"⚠️ [UPDATE] No fields to update!")
            
            # Update course limits - FIXED: Update both min_credits and max_students
            if request.course_limits:
                print(f"\n🔍 [UPDATE] Updating {len(request.course_limits)} course limits...")
                
                for idx, limit in enumerate(request.course_limits):
                    print(f"   [{idx+1}] {limit.course_type}: min_credits={limit.min_credits}, max_students={limit.max_students}")
                    
                    if limit.course_type:
                        # Find course type
                        await cursor.execute("""
                            SELECT course_type_id
                            FROM iems_course_type
                            WHERE course_type_desc LIKE %s
                        """, (f"%{limit.course_type}%",))
                        
                        course_type_result = await cursor.fetchone()
                        
                        if course_type_result:
                            course_type_id = course_type_result['course_type_id']
                            print(f"      Found course_type_id: {course_type_id}")
                            
                            # UPDATE BOTH min_credits AND max_students
                            update_query = """
                                UPDATE lms_academic_batch_semester_crs_structure
                                SET stud_min_crs_enroll = %s,
                                    stud_max_crs_enroll = %s
                                WHERE academic_batch_id = %s
                                AND semester_id = %s
                                AND crs_type_id = %s
                            """
                            await cursor.execute(update_query, (
                                limit.min_credits or 0,
                                limit.max_students or 0,
                                semester_before['academic_batch_id'],
                                request.semester_id,
                                course_type_id
                            ))
                            print(f"      ✅ Updated {limit.course_type}: min={limit.min_credits}, max_students={limit.max_students}")
                            await conn.commit()
                            print(f"      ✅ Transaction committed for {limit.course_type}")
                        else:
                            print(f"      ⚠️ Course type not found: {limit.course_type}")
            
            # Verify semester update
            await cursor.execute("SELECT * FROM iems_semester WHERE semester_id = %s", (request.semester_id,))
            semester_after = await cursor.fetchone()
            print(f"\n🔍 [UPDATE] Semester after update: {semester_after}")
            
            # Verify course structure update
            await cursor.execute("""
                SELECT 
                    ct.course_type_desc,
                    lms.stud_min_crs_enroll,
                    lms.stud_max_crs_enroll,
                    lms.crs_type_total
                FROM lms_academic_batch_semester_crs_structure lms
                JOIN iems_course_type ct ON ct.course_type_id = lms.crs_type_id
                WHERE lms.academic_batch_id = %s
                AND lms.semester_id = %s
                ORDER BY ct.course_type_desc
            """, (semester_before['academic_batch_id'], request.semester_id))
            
            course_after = await cursor.fetchall()
            print(f"🔍 [UPDATE] Course structure after update: {course_after}")
            print(f"{'='*80}\n")
            
            return returnSuccess({
                "semester": semester_after,
                "course_structure": course_after
            }, "Registration settings updated successfully")
            
    except Exception as e:
        if conn:
            await conn.rollback()
        print(f"❌ [UPDATE] Error: {str(e)}")
        traceback.print_exc()
        return returnException(str(e))
    finally:
        if conn:
            await pool.release(conn)
            print(f"✅ [UPDATE] Connection released")


# ============================================
# PDF EXPORT
# ============================================

@router.post("/export-pdf")
async def export_registration_pdf(request: ExportPDFRequest):
    """Export registration setup as PDF"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            temp_path = tmp_file.name

        doc = SimpleDocTemplate(
            temp_path,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=35,
            bottomMargin=35,
        )

        styles = getSampleStyleSheet()
        
        # Define styles
        page_number_style = ParagraphStyle(
            'PageNumberStyle',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica',
            leading=10
        )
        
        logo_style = ParagraphStyle(
            'LogoStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=9
        )
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=13,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#8B0000'),
            fontName='Helvetica-Bold',
            leading=16,
            spaceAfter=4
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=12,
            spaceAfter=3
        )
        
        th_style = ParagraphStyle(
            'THStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=9
        )
        
        td_center_style = ParagraphStyle(
            'TDCenterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica',
            leading=9
        )
        
        td_left_style = ParagraphStyle(
            'TDLeftStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica',
            leading=9
        )
        
        td_right_style = ParagraphStyle(
            'TDRightStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica',
            leading=9
        )
        
        td_bold_left_style = ParagraphStyle(
            'TDBoldLeftStyle',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=10
        )
        
        course_type_style = ParagraphStyle(
            'CourseTypeStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold',
            leading=11,
            spaceAfter=2
        )

        course_title_style = ParagraphStyle(
            'CourseTitleStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica',
            leading=9
        )

        story = []
        
        # HEADER
        institute_name = request.institute_name or "IonIdea Institute of Technology and Management"
        department_name = request.department or "Department of Computer Science & Engineering"
        
        header_data = [
            [
                Paragraph("LOGO", logo_style),
                Paragraph(f"{institute_name}<br/>{department_name}", 
                         ParagraphStyle(
                             'HeaderTextStyle',
                             parent=styles['Normal'],
                             fontSize=9,
                             alignment=TA_CENTER,
                             textColor=colors.HexColor('#1a2634'),
                             fontName='Helvetica',
                             leading=10
                         ))
            ]
        ]
        
        header_table = Table(header_data, colWidths=[2.5*cm, 15.5*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f8f9fa')),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.04 * inch))
        
        story.append(Paragraph("1", page_number_style))
        story.append(Spacer(1, 0.04 * inch))
        
        story.append(Paragraph("Student Course Registration Setup", title_style))
        story.append(Spacer(1, 0.04 * inch))
        
        # CURRICULUM & TERM TABLE
        curriculum_data = [
            [
                Paragraph(f"<b>Curriculum:</b> {request.curriculum}", td_bold_left_style),
                Paragraph(f"<b>Term:</b> {request.term}", td_bold_left_style)
            ]
        ]
        
        curriculum_table = Table(curriculum_data, colWidths=[9*cm, 9*cm])
        curriculum_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        story.append(curriculum_table)
        story.append(Spacer(1, 0.08 * inch))
        
        # SECTION TITLE
        story.append(Paragraph("Students to Course Credits Registration Summary", section_style))
        story.append(Spacer(1, 0.04 * inch))
        
        # SUMMARY CONTENT
        summary_content_data = [
            [
                Paragraph("Total credits:", td_left_style),
                Paragraph(str(request.totalCredits), td_right_style)
            ],
            [
                Paragraph(f"Total credits student can enroll for {request.term}:", td_left_style),
                Paragraph(str(request.maxCredits), td_right_style)
            ]
        ]
        
        summary_content_table = Table(summary_content_data, colWidths=[12.5*cm, 5.5*cm])
        summary_content_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        story.append(summary_content_table)
        story.append(Spacer(1, 0.06 * inch))
        
        # COURSE CREDIT SUMMARY TABLE
        limits_map = {}
        for item in request.courseTypeLimits:
            limits_map[item.course_type_desc] = {
                'min': item.stud_min_crs_enroll or 0,
                'max': item.stud_max_crs_enroll or 0
            }
        
        registered_map = {}
        for item in request.studentsRegistered:
            registered_map[item.course_type_desc] = item.students_registered
        
        summary_data = []
        summary_data.append([
            Paragraph("Type of Course", th_style),
            Paragraph("Total credits", th_style),
            Paragraph("Min. credits student can enroll", th_style),
            Paragraph("Max. credits student can enroll", th_style),
            Paragraph("Students Registered", th_style)
        ])
        
        for item in request.courseCreditSummary:
            course_type = item.type_of_course
            total_credits = item.total_credits
            
            limits = limits_map.get(course_type, {'min': 0, 'max': 0})
            
            if limits['max'] != total_credits:
                limits['max'] = total_credits
            
            registered = registered_map.get(course_type, 0)
            
            summary_data.append([
                Paragraph(course_type, td_left_style),
                Paragraph(str(total_credits), td_center_style),
                Paragraph(str(limits['min']), td_center_style),
                Paragraph(str(limits['max']), td_center_style),
                Paragraph(str(registered), td_center_style)
            ])
        
        summary_table = Table(summary_data, colWidths=[4.2*cm, 2.8*cm, 3.2*cm, 3.2*cm, 3.2*cm])
        summary_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.12 * inch))
        
        # COURSE DETAILS SECTION
        if request.courseDetails:
            for course_type in request.courseDetails:
                story.append(Paragraph(course_type.type, course_type_style))
                story.append(Spacer(1, 0.02 * inch))
                
                course_data = []
                course_data.append([
                    Paragraph("Course Title", th_style),
                    Paragraph("Credits", th_style),
                    Paragraph("Students Registered", th_style)
                ])
                
                for course in course_type.courses:
                    course_data.append([
                        Paragraph(course.course_title, course_title_style),
                        Paragraph(str(course.credits), td_center_style),
                        Paragraph(str(course.students_registered), td_center_style)
                    ])
                
                course_table = Table(course_data, colWidths=[10.5*cm, 3.2*cm, 3.2*cm])
                course_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ]))
                
                story.append(course_table)
                story.append(Spacer(1, 0.06 * inch))
        
        doc.build(story)
        
        return FileResponse(
            temp_path,
            media_type='application/pdf',
            filename=f"Student_Course_Registration_Setup_{request.curriculum}_{request.term}.pdf"
        )
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OTHER ENDPOINTS
# ============================================

@router.get("/departments")
async def get_departments():
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT dept_id, dept_name
                    FROM iems_department
                    WHERE status = 1
                    ORDER BY dept_name
                """)
                data = await cursor.fetchall()
                return returnSuccess(data, "Departments fetched successfully")
                
    except Exception as e:
        print(f"Error in get_departments: {str(e)}")
        return returnException(str(e))


@router.get("/programs/{dept_id}")
async def get_programs(dept_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT pgm_id, pgm_acronym AS program_name
                    FROM iems_program
                    WHERE dept_id = %s AND status = 1
                    ORDER BY pgm_title
                """, (dept_id,))
                data = await cursor.fetchall()
                return returnSuccess(data, "Programs fetched successfully")
                
    except Exception as e:
        print(f"Error in get_programs: {str(e)}")
        return returnException(str(e))