from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, validator, root_validator
from typing import List, Optional, Any
from datetime import datetime
import tempfile
import os
import io
import aiomysql

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

def is_elective_course(course_type: str) -> bool:
    """Determine if a course type is elective"""
    if not course_type:
        return False
    elective_keywords = ['Elective', 'elective']
    return any(keyword in course_type for keyword in elective_keywords)


def get_credit_limits(total_credits: float, is_elective: bool = False):
    """
    Get min and max credits based on total credits
    For ALL courses: Max = Total credits
    For Elective: Min = min(3, total_credits)
    For Non-Elective: Min = Total credits
    """
    if is_elective:
        return (min(3, total_credits), total_credits)  # Min=3, Max=Total
    else:
        return (total_credits, total_credits)  # Min=Max=Total


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
    max_students: Optional[int] = 0

class RegistrationUpdateRequest(BaseModel):
    semester_id: int
    total_credits: Optional[float] = None
    own_curriculum_electives: Optional[int] = None
    other_curriculum_electives: Optional[int] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    end_date: Optional[str] = None
    end_time: Optional[str] = None
    course_limits: Optional[List[CourseLimitUpdate]] = []

    @root_validator(skip_on_failure=True)
    def validate_all(cls, values):
        """Validate all fields together"""
        course_limits = values.get('course_limits', [])
        total_credits = values.get('total_credits')
        
        if not course_limits:
            return values
        
        for idx, limit in enumerate(course_limits):
            if not limit.course_type:
                raise ValueError(f"course_type is required for item {idx}")
            
            # Validate max_students is not negative
            if limit.max_students is not None and limit.max_students < 0:
                raise ValueError(f"max_students cannot be negative for {limit.course_type}")
        
        return values


# ============================================
# UPDATE REGISTRATION SETTINGS ENDPOINT
# ============================================

@router.post("/update-registration-settings")
async def update_registration_settings(request: RegistrationUpdateRequest):
    """
    Update registration settings for a semester
    """
    pool = None
    conn = None
    
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        conn = await pool.acquire()
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            
            # Get semester info
            await cursor.execute("""
                SELECT semester, academic_batch_id
                FROM iems_semester
                WHERE semester_id = %s
            """, (request.semester_id,))
            
            semester_info = await cursor.fetchone()
            if not semester_info:
                return returnException("Semester not found", 404)
            
            semester_num = semester_info['semester']
            
            # Update semester fields
            update_fields = []
            params = []
            
            if request.total_credits is not None:
                update_fields.append("sem_max_credits = %s")
                params.append(request.total_credits)
                
            if request.own_curriculum_electives is not None:
                update_fields.append("own_crclm_elective = %s")
                params.append(request.own_curriculum_electives)
                
            if request.other_curriculum_electives is not None:
                update_fields.append("other_crclm_elective = %s")
                params.append(request.other_curriculum_electives)
                
            if request.start_date:
                update_fields.append("enroll_start_date = STR_TO_DATE(%s, '%%d-%%m-%%Y')")
                params.append(request.start_date)
                
            if request.start_time:
                update_fields.append("enroll_start_time = STR_TO_DATE(%s, '%%h:%%i %%p')")
                params.append(request.start_time)
                
            if request.end_date:
                update_fields.append("enroll_end_date = STR_TO_DATE(%s, '%%d-%%m-%%Y')")
                params.append(request.end_date)
                
            if request.end_time:
                update_fields.append("enroll_end_time = STR_TO_DATE(%s, '%%h:%%i %%p')")
                params.append(request.end_time)
            
            if update_fields:
                params.append(request.semester_id)
                query = f"""
                    UPDATE iems_semester
                    SET {', '.join(update_fields)}
                    WHERE semester_id = %s
                """
                await cursor.execute(query, params)
                print(f"✅ Updated semester: {', '.join(update_fields)}")
            
            # Update course student limits
            if request.course_limits:
                for limit in request.course_limits:
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
                            
                            # Update courses with new max_students
                            update_query = """
                                UPDATE iems_courses
                                SET total_stud_enroll = %s
                                WHERE semester = %s
                                AND course_type_id = %s
                                AND status = 1
                            """
                            await cursor.execute(update_query, (
                                limit.max_students or 0,
                                semester_num,
                                course_type_id
                            ))
                            print(f"✅ Updated {limit.course_type} max students to {limit.max_students}")
                        else:
                            print(f"⚠️ Course type not found: {limit.course_type}")
            
            return returnSuccess(None, "Registration settings updated successfully")
            
    except Exception as e:
        print(f"❌ Error updating registration settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return returnException(str(e))
    finally:
        if conn:
            await pool.release(conn)


# ============================================
# GET COURSE TYPE LIMITS - DYNAMIC CALCULATION
# ============================================

@router.get("/course-type-limits/{semester_id}")
async def get_course_type_limits(semester_id: int):
    """
    Get course type limits with dynamic calculation
    Max = Total credits (always)
    Min = Total credits for non-electives, 3 for electives
    """
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Get semester info
                await cursor.execute("""
                    SELECT semester
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                semester_info = await cursor.fetchone()
                if not semester_info:
                    return returnException("Semester not found", 404)
                
                semester_num = semester_info['semester']
                
                # Get course type summary with total credits and registered students
                await cursor.execute("""
                    SELECT 
                        ct.course_type_desc,
                        SUM(c.total_credits) AS total_credits,
                        COALESCE((
                            SELECT COUNT(DISTINCT sc.regno)
                            FROM iems_student_courses sc
                            JOIN iems_courses c2 ON c2.crs_code = sc.crs_code
                            WHERE c2.course_type_id = ct.course_type_id
                            AND c2.semester = %s
                            AND sc.is_registered = 1
                            AND c2.status = 1
                        ), 0) AS students_registered
                    FROM iems_course_type ct
                    LEFT JOIN iems_courses c 
                        ON ct.course_type_id = c.course_type_id 
                        AND c.semester = %s
                        AND c.status = 1
                    WHERE ct.status = 1
                    GROUP BY ct.course_type_id, ct.course_type_desc
                    ORDER BY ct.course_type_desc
                """, (semester_num, semester_num))
                
                data = await cursor.fetchall()
                
                result = []
                for item in data:
                    total_credits = float(item['total_credits']) if item['total_credits'] else 0
                    course_type = item['course_type_desc']
                    
                    # Determine if elective
                    is_elective = is_elective_course(course_type)
                    
                    # Get dynamic limits
                    min_val, max_val = get_credit_limits(total_credits, is_elective)
                    
                    result.append({
                        'course_type_desc': course_type,
                        'stud_min_crs_enroll': min_val,
                        'stud_max_crs_enroll': max_val,  # Always equals total_credits
                        'students_registered': item['students_registered'] or 0
                    })
                
                return returnSuccess(result)
                
    except Exception as e:
        print(f"Error in get_course_type_limits: {str(e)}")
        import traceback
        traceback.print_exc()
        return returnException(str(e))


# ============================================
# PDF EXPORT - Uses the same data
# ============================================

@router.post("/export-pdf")
async def export_registration_pdf(request: ExportPDFRequest):
    """
    Export registration setup as PDF using the provided data
    """
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
        
        # Define styles (keep your existing styles here)
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

        story = []
        
        # Header
        header_data = [
            [
                Paragraph("YOUR LOGO HERE", logo_style),
                Paragraph("IonIdea Institute of Technology and Management<br/>IonIdea Institute of Technology and Management, Bangalore - Demo site<br/>Department of Computer Science & Engineering", 
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
        
        # Curriculum & Term Table
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
        
        story.append(Paragraph("Students to Course Credits Registration Summary", section_style))
        story.append(Spacer(1, 0.04 * inch))
        
        # Summary Content Table
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
        
        # Course Credit Summary Table - Use the data from request
        # Build lookup maps
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
            
            # Get limits from the courseTypeLimits data
            limits = limits_map.get(course_type, {'min': 0, 'max': 0})
            
            # Ensure max equals total credits (display the correct value)
            # If max doesn't match total, use total (this ensures consistency)
            if limits['max'] != total_credits:
                limits['max'] = total_credits
                # If it's non-elective, min should also equal total
                if not is_elective_course(course_type):
                    limits['min'] = total_credits
            
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
        
        # Course Details Section
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
                        Paragraph(course.course_title, td_left_style),
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Other endpoints (departments, programs, etc.)
# ============================================

@router.get("/departments")
async def get_departments():
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
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
        import traceback
        traceback.print_exc()
        return returnException(str(e))


@router.get("/programs/{dept_id}")
async def get_programs(dept_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
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


@router.get("/curriculums/{program_id}")
async def get_curriculums(program_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT
                        academic_batch_id AS curriculum_id,
                        CONCAT(pgm_acronym, ' ', start_year, '-', end_year) AS curriculum_name
                    FROM iems_academic_batch ab
                    JOIN iems_program p ON ab.pgm_id = p.pgm_id
                    WHERE ab.pgm_id = %s
                    ORDER BY start_year DESC
                """, (program_id,))
                data = await cursor.fetchall()
                return returnSuccess(data, "Curriculums fetched successfully")
                
    except Exception as e:
        print(f"Error in get_curriculums: {str(e)}")
        return returnException(str(e))


@router.get("/terms/{curriculum_id}")
async def get_terms(curriculum_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT
                        semester_id,
                        CONCAT(semester, ' - Semester') AS term_name
                    FROM iems_semester
                    WHERE status = 1
                    ORDER BY semester
                """)
                data = await cursor.fetchall()
                return returnSuccess(data, "Terms fetched successfully")
                
    except Exception as e:
        print(f"Error in get_terms: {str(e)}")
        return returnException(str(e))


@router.get("/course-credit-summary/{semester_id}")
async def get_course_credit_summary(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT semester 
                    FROM iems_semester 
                    WHERE semester_id = %s
                """, (semester_id,))
                semester_result = await cursor.fetchone()
                if not semester_result:
                    return returnException("Semester not found", 404)
                semester_num = semester_result['semester']
                
                query = """
                SELECT
                    CASE
                        WHEN ct.course_type_desc = 'Core' THEN 'Core'
                        WHEN ct.course_type_desc LIKE 'Open Elective%%' THEN 'Open Elective'
                        WHEN ct.course_type_desc LIKE 'Career Elective%%' THEN 'Career Elective'
                        WHEN ct.course_type_desc LIKE 'Professional Elective%%' THEN 'Professional Elective'
                        ELSE ct.course_type_desc
                    END AS type_of_course,
                    SUM(c.total_credits) AS total_credits
                FROM iems_courses c
                JOIN iems_course_type ct ON ct.course_type_id = c.course_type_id
                WHERE c.semester = %s AND c.status = 1
                GROUP BY type_of_course
                ORDER BY type_of_course
                """
                await cursor.execute(query, (semester_num,))
                data = await cursor.fetchall()
                return returnSuccess(data)
                
    except Exception as e:
        print(f"Error in get_course_credit_summary: {str(e)}")
        return returnException(str(e))


@router.get("/students-registered/{semester_id}")
async def get_students_registered(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT semester 
                    FROM iems_semester 
                    WHERE semester_id = %s
                """, (semester_id,))
                semester_result = await cursor.fetchone()
                if not semester_result:
                    return returnException("Semester not found", 404)
                semester_num = semester_result['semester']
                
                query = """
                SELECT 
                    ct.course_type_desc,
                    COUNT(DISTINCT sc.regno) AS students_registered
                FROM iems_student_courses sc
                JOIN iems_courses c ON c.crs_code = sc.crs_code
                JOIN iems_course_type ct ON ct.course_type_id = c.course_type_id
                WHERE sc.is_registered = 1
                    AND c.semester = %s
                    AND c.status = 1
                GROUP BY ct.course_type_desc
                """
                await cursor.execute(query, (semester_num,))
                data = await cursor.fetchall()
                return returnSuccess(data)
                
    except Exception as e:
        print(f"Error in get_students_registered: {str(e)}")
        return returnException(str(e))


@router.get("/course-enroll-details/{semester_id}/{course_type}")
async def get_course_enroll_details(semester_id: int, course_type: str):
    """
    Get courses for a specific course type in a semester
    """
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT semester, academic_batch_id
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                semester_info = await cursor.fetchone()
                if not semester_info:
                    return returnException("Semester not found", 404)
                
                semester_num = semester_info['semester']
                academic_batch_id = semester_info['academic_batch_id']
                
                course_type_mapping = {
                    'Core': 'Core',
                    'Open Elective': 'Open Elective',
                    'Career Elective': 'Career Elective',
                    'Professional Elective': 'Professional Elective',
                    'Basic': 'Basic',
                    'Theory Course': 'Theory Course'
                }
                
                search_type = course_type_mapping.get(course_type, course_type)
                
                await cursor.execute("""
                    SELECT course_type_id
                    FROM iems_course_type
                    WHERE course_type_desc = %s
                """, (search_type,))
                
                course_type_result = await cursor.fetchone()
                
                if not course_type_result:
                    if 'Open Elective' in course_type:
                        await cursor.execute("""
                            SELECT course_type_id
                            FROM iems_course_type
                            WHERE course_type_desc = 'Open Elective'
                        """)
                        course_type_result = await cursor.fetchone()
                    elif 'Career Elective' in course_type:
                        await cursor.execute("""
                            SELECT course_type_id
                            FROM iems_course_type
                            WHERE course_type_desc = 'Career Elective'
                        """)
                        course_type_result = await cursor.fetchone()
                    elif 'Professional Elective' in course_type:
                        await cursor.execute("""
                            SELECT course_type_id
                            FROM iems_course_type
                            WHERE course_type_desc = 'Professional Elective'
                        """)
                        course_type_result = await cursor.fetchone()
                    elif 'Core' in course_type:
                        await cursor.execute("""
                            SELECT course_type_id
                            FROM iems_course_type
                            WHERE course_type_desc = 'Core'
                        """)
                        course_type_result = await cursor.fetchone()
                
                if not course_type_result:
                    return returnException(f"Course type '{course_type}' not found", 404)
                
                course_type_id = course_type_result['course_type_id']
                
                await cursor.execute("""
                    SELECT
                        c.crs_id,
                        c.crs_code,
                        c.crs_title,
                        c.total_credits,
                        COALESCE(c.total_stud_enroll, 0) AS total_stud_enroll
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
        print(f"Error in get_course_enroll_details: {str(e)}")
        return returnException(str(e))


# ============================================
# DATE/TIME ENDPOINTS
# ============================================

@router.get("/start-date/{semester_id}")
async def get_start_date(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT enroll_start_date
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        
        if data and data["enroll_start_date"]:
            data = {"start_date": data["enroll_start_date"].strftime("%d-%m-%Y")}
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_start_date: {str(e)}")
        return returnException(str(e))


@router.get("/start-time/{semester_id}")
async def get_start_time(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT enroll_start_time
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        
        if data and data["enroll_start_time"]:
            time_value = data["enroll_start_time"]
            total_seconds = int(time_value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            suffix = "AM" if hours < 12 else "PM"
            display_hour = hours % 12 or 12
            data = {"start_time": f"{display_hour:02d}:{minutes:02d} {suffix}"}
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_start_time: {str(e)}")
        return returnException(str(e))


@router.get("/end-date/{semester_id}")
async def get_end_date(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT enroll_end_date
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        
        if data and data["enroll_end_date"]:
            data = {"end_date": data["enroll_end_date"].strftime("%d-%m-%Y")}
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_end_date: {str(e)}")
        return returnException(str(e))


@router.get("/end-time/{semester_id}")
async def get_end_time(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT enroll_end_time
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        
        if data and data["enroll_end_time"]:
            time_value = data["enroll_end_time"]
            total_seconds = int(time_value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            suffix = "AM" if hours < 12 else "PM"
            display_hour = hours % 12 or 12
            data = {"end_time": f"{display_hour:02d}:{minutes:02d} {suffix}"}
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_end_time: {str(e)}")
        return returnException(str(e))


# ============================================
# SEMESTER INFO ENDPOINTS
# ============================================

@router.get("/semester-credits/{semester_id}")
async def get_semester_credits(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT sem_max_credits
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_semester_credits: {str(e)}")
        return returnException(str(e))


@router.get("/semester-credit-range/{semester_id}")
async def get_semester_credit_range(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT IFNULL(sem_min_credits, 0) AS min_credits,
                           IFNULL(sem_max_credits, 0) AS max_credits
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
                if not data:
                    data = {"min_credits": 0, "max_credits": 0}
                return returnSuccess(data)
                
    except Exception as e:
        print(f"Error in get_semester_credit_range: {str(e)}")
        return returnException(str(e))


@router.get("/own-curriculum-electives/{semester_id}")
async def get_own_curriculum_electives(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT IFNULL(own_crclm_elective, 0) AS own_crclm_elective
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_own_curriculum_electives: {str(e)}")
        return returnException(str(e))


@router.get("/other-curriculum-electives/{semester_id}")
async def get_other_curriculum_electives(semester_id: int):
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT IFNULL(other_crclm_elective, 0) AS other_crclm_elective
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                data = await cursor.fetchone()
        return returnSuccess(data)
        
    except Exception as e:
        print(f"Error in get_other_curriculum_electives: {str(e)}")
        return returnException(str(e))