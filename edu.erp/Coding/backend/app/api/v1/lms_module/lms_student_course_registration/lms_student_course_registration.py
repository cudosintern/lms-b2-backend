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
import json

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
    crs_code: str
    course_title: str
    credits: float
    students_registered: int

class CourseTypeDetail(BaseModel):
    type: str
    courses: List[CourseDetailItem]

class ExportPDFRequest(BaseModel):
    semester_id: Optional[int] = None  # Made optional
    institute_name: Optional[str] = ""
    department: Optional[str] = ""
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
    max_credits: Optional[float] = 0
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

    @root_validator(skip_on_failure=True)
    def validate_all(cls, values):
        """Validate all fields together"""
        course_limits = values.get('course_limits', [])
        
        if not course_limits:
            return values
        
        for idx, limit in enumerate(course_limits):
            if not limit.course_type:
                raise ValueError(f"course_type is required for item {idx}")
            
            if limit.max_students is not None and limit.max_students < 0:
                raise ValueError(f"max_students cannot be negative for {limit.course_type}")
            if limit.min_credits is not None and limit.min_credits < 0:
                raise ValueError(f"min_credits cannot be negative for {limit.course_type}")
            if limit.max_credits is not None and limit.max_credits < 0:
                raise ValueError(f"max_credits cannot be negative for {limit.course_type}")
        
        return values


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
                
                # Get course structure with student counts - USING CORRECT FIELD NAMES
                await cursor.execute("""
                    SELECT 
                        ct.course_type_desc AS course_type,
                        lms.crs_type_total AS total_credits,
                        lms.stud_min_crs_enroll AS stud_min_crs_enroll,
                        lms.stud_max_crs_enroll AS stud_max_crs_enroll,
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
                
                # Debug: Print the data
                print("\n📊 Course Structure Data from DB:")
                for item in course_structure:
                    print(f"   {item['course_type']}: total={item['total_credits']}, min={item['stud_min_crs_enroll']}, max={item['stud_max_crs_enroll']}")
                
                # Format response with CORRECT field names
                response = {
                    "semester": {
                        "semester_id": semester_data['semester_id'],
                        "semester": semester_data['semester'],
                        "start_date": semester_data['enroll_start_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_start_date') else None,
                        "start_time": format_time_for_display(semester_data.get('enroll_start_time')) if semester_data.get('enroll_start_time') else None,
                        "end_date": semester_data['enroll_end_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_end_date') else None,
                        "end_time": format_time_for_display(semester_data.get('enroll_end_time')) if semester_data.get('enroll_end_time') else None,
                        "min_credit": float(semester_data.get('sem_min_credits')) if semester_data.get('sem_min_credits') is not None else 0,
                        "max_credit": float(semester_data.get('sem_max_credits')) if semester_data.get('sem_max_credits') is not None else 0,
                        "own_elective": int(semester_data.get('own_crclm_elective')) if semester_data.get('own_crclm_elective') is not None else 0,
                        "other_elective": int(semester_data.get('other_crclm_elective')) if semester_data.get('other_crclm_elective') is not None else 0
                    },
                    "course_structure": [
                        {
                            "sl_no": idx + 1,
                            "course_type": item['course_type'] or f"Type {idx + 1}",
                            "total_credits": float(item['total_credits']) if item['total_credits'] else 0,
                            "min_credits": float(item['stud_min_crs_enroll']) if item['stud_min_crs_enroll'] is not None else 0,
                            "max_credits": float(item['stud_max_crs_enroll']) if item['stud_max_crs_enroll'] is not None else 0,
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
    pool = None
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed", 500)
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                print(f"🔍 Fetching curriculums for program_id: {program_id}")
                
                await cursor.execute("""
                    SELECT
                        ab.academic_batch_id AS curriculum_id,
                        CONCAT(pgm_acronym, ' ', start_year, '-', end_year) AS curriculum_name
                    FROM iems_academic_batch ab
                    JOIN iems_program p ON ab.pgm_id = p.pgm_id
                    WHERE ab.pgm_id = %s
                    ORDER BY start_year DESC
                """, (program_id,))
                data = await cursor.fetchall()
                
                print(f"📊 Data returned: {data}")
                
                return returnSuccess(data, "Curriculums fetched successfully")
                
    except Exception as e:
        print(f"❌ Error in get_curriculums: {str(e)}")
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

@router.get("/registration-setup/{semester_id}")
async def get_registration_setup(semester_id: int):
    """Get complete registration setup data with grouping"""
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
                
                # Get course structure
                await cursor.execute("""
                    SELECT 
                        ct.course_type_desc AS course_type,
                        lms.crs_type_total AS total_credits,
                        lms.stud_min_crs_enroll AS stud_min_crs_enroll,
                        lms.stud_max_crs_enroll AS stud_max_crs_enroll,
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
                
                # ============================================
                # GROUP THE DATA - Manual grouping for AI
                # ============================================
                grouped = {}
                
                for item in course_structure:
                    course_type = item['course_type'] or 'Other'
                    
                    # Group AI Elective together
                    if course_type == 'AI Elective' or course_type == 'AI Elective -1' or course_type == 'AI Elective -2':
                        main_type = 'AI Elective'
                    else:
                        main_type = course_type
                    
                    if main_type not in grouped:
                        grouped[main_type] = {
                            'total_credits': 0,
                            'stud_min_crs_enroll': 0,
                            'stud_max_crs_enroll': 0,
                            'students_registered': 0
                        }
                    
                    grouped[main_type]['total_credits'] += float(item['total_credits']) if item['total_credits'] else 0
                    grouped[main_type]['stud_min_crs_enroll'] += float(item['stud_min_crs_enroll']) if item['stud_min_crs_enroll'] is not None else 0
                    grouped[main_type]['stud_max_crs_enroll'] += float(item['stud_max_crs_enroll']) if item['stud_max_crs_enroll'] is not None else 0
                    grouped[main_type]['students_registered'] += int(item['students_registered']) if item['students_registered'] else 0
                
                # Format response
                response = {
                    "semester": {
                        "semester_id": semester_data['semester_id'],
                        "semester": semester_data['semester'],
                        "start_date": semester_data['enroll_start_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_start_date') else None,
                        "start_time": format_time_for_display(semester_data.get('enroll_start_time')) if semester_data.get('enroll_start_time') else None,
                        "end_date": semester_data['enroll_end_date'].strftime("%d-%m-%Y") if semester_data.get('enroll_end_date') else None,
                        "end_time": format_time_for_display(semester_data.get('enroll_end_time')) if semester_data.get('enroll_end_time') else None,
                        "min_credit": float(semester_data.get('sem_min_credits')) if semester_data.get('sem_min_credits') is not None else 0,
                        "max_credit": float(semester_data.get('sem_max_credits')) if semester_data.get('sem_max_credits') is not None else 0,
                        "own_elective": int(semester_data.get('own_crclm_elective')) if semester_data.get('own_crclm_elective') is not None else 0,
                        "other_elective": int(semester_data.get('other_crclm_elective')) if semester_data.get('other_crclm_elective') is not None else 0
                    },
                    "course_structure": [
                        {
                            "sl_no": idx + 1,
                            "course_type": key,
                            "total_credits": float(value['total_credits']),
                            "min_credits": float(value['stud_min_crs_enroll']),
                            "max_credits": float(value['stud_max_crs_enroll']),
                            "students_registered": int(value['students_registered'])
                        }
                        for idx, (key, value) in enumerate(grouped.items())
                    ]
                }
                
                return returnSuccess(response)
                
    except Exception as e:
        print(f"❌ Error in get_registration_setup: {str(e)}")
        traceback.print_exc()
        return returnException(str(e))


@router.get("/course-enroll-details/{semester_id}/{course_type}")
async def get_course_enroll_details(semester_id: int, course_type: str):
    """
    Get courses for a specific course type with registered students count.
    FULLY DYNAMIC - Includes all sub-types when fetching courses.
    """
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
                
                print(f"🔍 [Enroll] Looking for course type: '{course_type}'")
                
                # STEP 1: Find the course type
                course_type_result = None
                
                # Try exact match
                await cursor.execute("""
                    SELECT course_type_id, course_type_desc
                    FROM iems_course_type
                    WHERE course_type_desc = %s
                """, (course_type,))
                course_type_result = await cursor.fetchone()
                
                # If not found, try LIKE
                if not course_type_result:
                    await cursor.execute("""
                        SELECT course_type_id, course_type_desc
                        FROM iems_course_type
                        WHERE course_type_desc LIKE %s
                    """, (f"%{course_type}%",))
                    course_type_result = await cursor.fetchone()
                
                if not course_type_result:
                    return returnException(f"Course type '{course_type}' not found")
                
                course_type_id = course_type_result['course_type_id']
                course_type_name = course_type_result['course_type_desc']
                print(f"✅ [Enroll] Found course_type_id: {course_type_id} for '{course_type_name}'")
                
                # STEP 2: Get ALL course_type_ids for this main type (including sub-types)
                # Get the base name without -1, -2, etc.
                import re
                base_name = re.sub(r'\s*-\d+$', '', course_type_name)
                
                # Get all course types that start with the base name
                await cursor.execute("""
                    SELECT course_type_id, course_type_desc
                    FROM iems_course_type
                    WHERE course_type_desc LIKE %s
                """, (f"{base_name}%",))
                
                all_related_types = await cursor.fetchall()
                type_ids = [t['course_type_id'] for t in all_related_types]
                
                print(f"🔍 Found {len(type_ids)} related course types: {[t['course_type_desc'] for t in all_related_types]}")
                
                # If no related types found, use the original
                if not type_ids:
                    type_ids = [course_type_id]
                
                # STEP 3: Get ALL courses for these course types
                placeholders = ','.join(['%s'] * len(type_ids))
                query = f"""
                    SELECT
                        c.crs_id,
                        c.crs_code,
                        c.crs_title,
                        c.total_credits,
                        c.course_type_id,
                        COALESCE((
                            SELECT COUNT(DISTINCT sc.regno)
                            FROM iems_student_courses sc
                            WHERE sc.crs_code = c.crs_code
                            AND sc.is_registered = 1
                        ), 0) AS registered_count
                    FROM iems_courses c
                    WHERE c.academic_batch_id = %s
                        AND c.semester = %s
                        AND c.course_type_id IN ({placeholders})
                        AND c.status = 1
                    ORDER BY c.crs_code
                """
                params = [academic_batch_id, semester_num] + type_ids
                
                await cursor.execute(query, params)
                courses = await cursor.fetchall()
                
                print(f"✅ [Enroll] Found {len(courses)} courses for '{base_name}'")
                for course in courses:
                    print(f"   {course['crs_code']} - {course['crs_title']}")
                
                formatted_courses = []
                for course in courses:
                    formatted_courses.append({
                        'crs_id': course['crs_id'],
                        'crs_code': course['crs_code'],
                        'crs_title': course['crs_title'],
                        'total_credits': float(course['total_credits']) if course['total_credits'] else 0,
                        'registered_count': int(course['registered_count']) if course['registered_count'] else 0
                    })
                
                return returnSuccess({
                    "semester_id": semester_id,
                    "course_type": base_name,
                    "course_type_id": course_type_id,
                    "courses": formatted_courses,
                    "total_courses": len(formatted_courses),
                    "total_registered": sum(c['registered_count'] for c in formatted_courses),
                    "total_credits": sum(c['total_credits'] for c in formatted_courses)
                })
                
    except Exception as e:
        print(f"❌ Error in get_course_enroll_details: {str(e)}")
        traceback.print_exc()
        return returnException(str(e))



# ============================================
# UPDATE REGISTRATION SETTINGS
# ============================================

@router.post("/update-registration-settings")
async def update_registration_settings(request: RegistrationUpdateRequest):
    """Update registration settings"""
    print(f"\n{'='*80}")
    print(f"🔍 [UPDATE] Request received")
    print(f"🔍 [UPDATE] semester_id: {request.semester_id}")
    print(f"🔍 [UPDATE] course_limits count: {len(request.course_limits) if request.course_limits else 0}")
    
    if request.course_limits:
        for idx, limit in enumerate(request.course_limits):
            print(f"   [{idx+1}] {limit.course_type}: min_credits={limit.min_credits}, max_credits={limit.max_credits}")
    print(f"{'='*80}")
    
    pool = None
    conn = None
    
    try:
        pool = await get_db_pool()
        if pool is None:
            return returnException("Database connection failed")
        
        conn = await pool.acquire()
        
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Get semester info
            await cursor.execute("""
                SELECT academic_batch_id
                FROM iems_semester
                WHERE semester_id = %s
            """, (request.semester_id,))
            
            semester_info = await cursor.fetchone()
            if not semester_info:
                return returnException("Semester not found")
            
            academic_batch_id = semester_info['academic_batch_id']
            print(f"🔍 academic_batch_id: {academic_batch_id}")
            
            # STEP 1: Update semester table
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
                await cursor.execute(query, params)
                await conn.commit()
                print(f"✅ Semester table updated")
            
            # STEP 2: Update course limits
            if request.course_limits:
                print(f"\n🔍 [UPDATE] Updating {len(request.course_limits)} course limits...")
                
                for limit in request.course_limits:
                    if not limit.course_type:
                        continue
                    
                    print(f"\n🔍 Processing: '{limit.course_type}'")
                    print(f"   min_credits: {limit.min_credits}, max_credits: {limit.max_credits}")
                    
                    course_type_desc = limit.course_type
                    
                    # Special handling for Core
                    if course_type_desc.lower() == 'core':
                        print(f"   🔍 Special case: Core detected")
                        await cursor.execute("""
                            SELECT course_type_id, course_type_desc
                            FROM iems_course_type
                            WHERE course_type_desc = 'Core'
                        """)
                    else:
                        await cursor.execute("""
                            SELECT course_type_id, course_type_desc
                            FROM iems_course_type
                            WHERE course_type_desc = %s
                        """, (course_type_desc,))
                    
                    course_type_result = await cursor.fetchone()
                    
                    if not course_type_result:
                        print(f"   ⚠️ Exact match not found, trying LIKE...")
                        await cursor.execute("""
                            SELECT course_type_id, course_type_desc
                            FROM iems_course_type
                            WHERE course_type_desc LIKE %s
                        """, (f"%{course_type_desc}%",))
                        course_type_result = await cursor.fetchone()
                    
                    if not course_type_result:
                        print(f"   ❌ Course type not found: {course_type_desc}")
                        continue
                    
                    course_type_id = course_type_result['course_type_id']
                    course_type_desc_found = course_type_result['course_type_desc']
                    print(f"   ✅ Found course_type_id: {course_type_id} for '{course_type_desc_found}'")
                    
                    # Check if record exists
                    await cursor.execute("""
                        SELECT ctcs_id, stud_min_crs_enroll, stud_max_crs_enroll
                        FROM lms_academic_batch_semester_crs_structure
                        WHERE academic_batch_id = %s
                        AND semester_id = %s
                        AND crs_type_id = %s
                    """, (academic_batch_id, request.semester_id, course_type_id))
                    
                    existing_record = await cursor.fetchone()
                    
                    if existing_record:
                        print(f"   📝 Existing record: ctcs_id={existing_record['ctcs_id']}")
                        print(f"      Current: min={existing_record['stud_min_crs_enroll']}, max={existing_record['stud_max_crs_enroll']}")
                        print(f"      New: min={limit.min_credits}, max={limit.max_credits}")
                        
                        update_query = """
                            UPDATE lms_academic_batch_semester_crs_structure
                            SET stud_min_crs_enroll = %s,
                                stud_max_crs_enroll = %s,
                                modified_date = NOW()
                            WHERE ctcs_id = %s
                        """
                        await cursor.execute(update_query, (
                            limit.min_credits or 0,
                            limit.max_credits or 0,
                            existing_record['ctcs_id']
                        ))
                        print(f"   ✅ Updated {course_type_desc_found}: min={limit.min_credits}, max={limit.max_credits}")
                    else:
                        print(f"   📝 No existing record, inserting new...")
                        insert_query = """
                            INSERT INTO lms_academic_batch_semester_crs_structure
                            (academic_batch_id, semester_id, crs_type_id, 
                             stud_min_crs_enroll, stud_max_crs_enroll, created_date)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """
                        await cursor.execute(insert_query, (
                            academic_batch_id,
                            request.semester_id,
                            course_type_id,
                            limit.min_credits or 0,
                            limit.max_credits or 0
                        ))
                        print(f"   ✅ Inserted {course_type_desc_found}: min={limit.min_credits}, max={limit.max_credits}")
                    
                    await conn.commit()
                    print(f"   ✅ Transaction committed")
            
            # STEP 3: Verify updates
            await cursor.execute("""
                SELECT 
                    ct.course_type_desc,
                    lms.stud_min_crs_enroll,
                    lms.stud_max_crs_enroll,
                    lms.modified_date
                FROM lms_academic_batch_semester_crs_structure lms
                JOIN iems_course_type ct ON ct.course_type_id = lms.crs_type_id
                WHERE lms.academic_batch_id = %s
                AND lms.semester_id = %s
                ORDER BY ct.course_type_desc
            """, (academic_batch_id, request.semester_id))
            
            course_after = await cursor.fetchall()
            print(f"\n🔍 [UPDATE] Final data in database:")
            for item in course_after:
                print(f"   {item['course_type_desc']}: min={item['stud_min_crs_enroll']}, max={item['stud_max_crs_enroll']}")
            
            return returnSuccess({
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


# ============================================
# PDF EXPORT - FIXED
# ============================================

@router.post("/export-pdf")
async def export_registration_pdf(request: ExportPDFRequest):
    """Export registration setup as PDF - FETCHES FRESH DATA"""
    try:
        print(f"\n{'='*60}")
        print(f"🔍 [PDF] Export PDF called with semester_id: {request.semester_id}")
        
        semester_id = request.semester_id or 1
        print(f"🔍 [PDF] Using semester_id: {semester_id}")
        
        # FETCH FRESH DATA FROM DATABASE
        pool = await get_db_pool()
        if pool is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # 1. Get semester data
                await cursor.execute("""
                    SELECT 
                        semester_id,
                        semester,
                        academic_batch_id,
                        sem_min_credits,
                        sem_max_credits,
                        own_crclm_elective,
                        other_crclm_elective
                    FROM iems_semester
                    WHERE semester_id = %s
                """, (semester_id,))
                
                semester_data = await cursor.fetchone()
                if not semester_data:
                    raise HTTPException(status_code=404, detail="Semester not found")
                
                # 2. Get ALL courses grouped by course type
                await cursor.execute("""
                    SELECT 
                        c.crs_code,
                        c.crs_title,
                        c.total_credits,
                        c.course_type_id,
                        ct.course_type_desc,
                        COALESCE((
                            SELECT COUNT(DISTINCT sc.regno)
                            FROM iems_student_courses sc
                            WHERE sc.crs_code = c.crs_code
                            AND sc.is_registered = 1
                        ), 0) AS registered_count
                    FROM iems_courses c
                    LEFT JOIN iems_course_type ct ON ct.course_type_id = c.course_type_id
                    WHERE c.academic_batch_id = %s
                        AND c.semester = %s
                        AND c.status = 1
                    ORDER BY ct.course_type_desc, c.crs_code
                """, (
                    semester_data['academic_batch_id'], 
                    semester_data['semester']
                ))
                
                all_courses = await cursor.fetchall()
                
                # 3. Group courses by category
                import re
                grouped_courses = {}
                
                for course in all_courses:
                    course_type = course['course_type_desc'] or 'Other'
                    
                    # Remove sub-type suffix (-1, -2, -3)
                    main_type = re.sub(r'\s*-\d+$', '', course_type)
                    
                    if main_type not in grouped_courses:
                        grouped_courses[main_type] = []
                    
                    grouped_courses[main_type].append({
                        'course_title': f"{course['crs_code']} - {course['crs_title']}",
                        'credits': float(course['total_credits']) if course['total_credits'] else 0,
                        'students_registered': int(course['registered_count']) if course['registered_count'] else 0
                    })
                
                print(f"🔍 Grouped {len(all_courses)} courses into {len(grouped_courses)} categories")
                for cat, courses in grouped_courses.items():
                    print(f"   {cat}: {len(courses)} courses")
                
                # 4. Get LMS structure for summary
                await cursor.execute("""
                    SELECT 
                        ct.course_type_desc AS course_type,
                        lms.crs_type_total AS total_credits,
                        lms.stud_min_crs_enroll AS stud_min_crs_enroll,
                        lms.stud_max_crs_enroll AS stud_max_crs_enroll,
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
                """, (
                    semester_data['semester'], 
                    semester_data['academic_batch_id'], 
                    semester_data['academic_batch_id'], 
                    semester_id
                ))
                
                course_structure = await cursor.fetchall()
                
                # 5. Build PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    temp_path = tmp_file.name

                # ============================================
                # DOCUMENT SETUP - MATCHING FORMAT3
                # ============================================
                doc = SimpleDocTemplate(
                    temp_path,
                    pagesize=A4,
                    leftMargin=18,
                    rightMargin=18,
                    topMargin=18,
                    bottomMargin=20
                )

                # ============================================
                # DYNAMIC TABLE WIDTHS
                # ============================================
                PAGE_WIDTH = doc.width

                SUMMARY_COL_WIDTHS = [
                    PAGE_WIDTH * 0.30,
                    PAGE_WIDTH * 0.15,
                    PAGE_WIDTH * 0.18,
                    PAGE_WIDTH * 0.18,
                    PAGE_WIDTH * 0.19,
                ]

                COURSE_COL_WIDTHS = [
                    PAGE_WIDTH * 0.74,
                    PAGE_WIDTH * 0.13,
                    PAGE_WIDTH * 0.13,
                ]

                styles = getSampleStyleSheet()
                
                # ============================================
                # STYLES - MATCHING FORMAT3
                # ============================================
                
                # Header text style
                header_text_style = ParagraphStyle(
                    "HeaderText",
                    fontName="Helvetica",
                    fontSize=9,
                    alignment=TA_CENTER,
                    leading=10
                )
                
                # Logo style
                logo_style = ParagraphStyle(
                    'LogoStyle',
                    parent=styles['Normal'],
                    fontName='Helvetica-Bold',
                    fontSize=8,
                    alignment=TA_CENTER,
                    textColor=colors.HexColor('#1a2634'),
                    leading=9
                )
                
                # Page number style
                page_no_style = ParagraphStyle(
                    "PageNo",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    alignment=TA_RIGHT
                )
                
                # Powered by style
                powered_by_style = ParagraphStyle(
                    "Powered",
                    fontName="Helvetica",
                    fontSize=8,
                    textColor=colors.grey,
                    leading=8
                )
                
                # Title style - Dark Red, Bold
                title_style = ParagraphStyle(
                    "Title",
                    fontName="Helvetica-Bold",
                    fontSize=13,
                    textColor=colors.HexColor("#8B0000"),
                    leading=14,
                    spaceAfter=5,
                    alignment=TA_LEFT
                )
                
                # Summary heading style (for inside table)
                summary_heading_style = ParagraphStyle(
                    "SummaryHeading",
                    fontName="Helvetica-Bold",
                    fontSize=12,
                    alignment=TA_CENTER,
                    leading=14
                )
                
                # Table styles
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
                    fontSize=10,
                    alignment=TA_LEFT,
                    textColor=colors.HexColor('#000000'),
                    fontName='Helvetica-Bold',
                    leading=11
                )
                
                # Course type heading
                course_type_style = ParagraphStyle(
                    "CourseType",
                    parent=styles["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=11,
                    leading=13,
                    spaceBefore=10,
                    spaceAfter=5,
                    alignment=TA_LEFT,
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
                
                # ============================================
                # HEADER - FULLY DYNAMIC
                # ============================================
                # Get values from request with fallbacks
                institute_name = request.institute_name or "IonIdea Institute of Technology and Management"
                department_name = request.department or "Department of Computer Science & Engineering"
                
                # Logo text
                logo = Paragraph("", logo_style)
                
                # Header text with dynamic institute, address, department
                header_text = Paragraph(
                    f"""
                    <b>{institute_name}</b><br/>
                    {department_name}
                    """,
                    header_text_style
                )
                
                # Page number
                page_no = Paragraph("<b>1</b>", page_no_style)
                
                # Header table
                header = Table(
                    [[logo, header_text, page_no]],
                    colWidths=[2.0*cm, 14.5*cm, 1.0*cm]
                )
                
                header.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                story.append(header)
                story.append(Spacer(1, 2))
                
                # Powered by
                story.append(
                    Paragraph(
                        "Powered by www.ioncudos.com",
                        powered_by_style
                    )
                )
                
                story.append(Spacer(1, 6))
                
                # Title
                story.append(
                    Paragraph(
                        "Student Course Registration Setup",
                        title_style
                    )
                )
                
                # ============================================
                # CURRICULUM & TERM
                # ============================================
                curriculum_data = [
                    [
                        Paragraph(
                            f"<b>Curriculum:</b> {request.curriculum}",
                            td_bold_left_style
                        ),
                        Paragraph(
                            f"<b>Term:</b> {request.term}",
                            td_bold_left_style
                        )
                    ]
                ]
                
                curriculum_table = Table(
                    curriculum_data,
                    colWidths=[PAGE_WIDTH * 0.50, PAGE_WIDTH * 0.50]
                )
                
                curriculum_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(curriculum_table)
                story.append(Spacer(1, 12))
                
                # ============================================
                # SUMMARY SECTION - BORDERED TABLE (MATCHING FORMAT-3)
                # ============================================
                
                # Dynamic values from database
                total_credits = semester_data['sem_max_credits'] or 0
                enroll_credits = semester_data['sem_max_credits'] or 0
                
                # Build summary data with heading as first row (merged)
                summary_data = []
                
                # Row 1: Heading (merged across 2 columns)
                summary_data.append([
                    Paragraph(
                        "Students to Course Credits Registration Summary",
                        summary_heading_style
                    ),
                    ""  # Empty cell for right column (will be merged)
                ])
                
                # Row 2: Total credits
                summary_data.append([
                    Paragraph("Total credits:", td_left_style),
                    Paragraph(str(total_credits), td_right_style)
                ])
                
                # Row 3: Total credits student can enroll
                summary_data.append([
                    Paragraph(f"Total credits student can enroll for {request.term}:", td_left_style),
                    Paragraph(str(enroll_credits), td_right_style)
                ])
                
                # Create summary table with 2 columns
                summary_table_bordered = Table(
                    summary_data,
                    colWidths=[PAGE_WIDTH * 0.78, PAGE_WIDTH * 0.22],
                    repeatRows=0
                )
                
                summary_table_bordered.setStyle(TableStyle([
                    # Heading row - merged across both columns
                    ('SPAN', (0, 0), (1, 0)),
                    
                    # Borders - full grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    
                    # Alignment
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left column - left aligned
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),  # Right column - right aligned
                    
                    # Vertical alignment
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    
                    # Font sizes
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('FONTSIZE', (0, 0), (0, 0), 12),  # Heading row larger
                    
                    # Padding
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    
                    # No background color
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ]))
                
                story.append(summary_table_bordered)
                story.append(Spacer(1, 8))
                
                # ============================================
                # COURSE TYPE SUMMARY TABLE
                # ============================================
                course_summary_data = []
                course_summary_data.append([
                    Paragraph("Type of Course", th_style),
                    Paragraph("Total credits", th_style),
                    Paragraph("Min. credits student can enroll", th_style),
                    Paragraph("Max. credits student can enroll", th_style),
                    Paragraph("<para align='center'>Students Registered</para>", th_style)
                ])

                for item in course_structure:
                    course_type = item['course_type'] or 'Other'
                    main_type = re.sub(r'\s*-\d+$', '', course_type)
                    
                    total_credits_row = float(item['total_credits']) if item['total_credits'] else 0
                    min_credits = float(item['stud_min_crs_enroll']) if item['stud_min_crs_enroll'] is not None else 0
                    max_credits = float(item['stud_max_crs_enroll']) if item['stud_max_crs_enroll'] is not None else 0
                    students_registered = int(item['students_registered']) if item['students_registered'] else 0
                    
                    course_summary_data.append([
                        Paragraph(main_type, td_left_style),
                        Paragraph(f"{total_credits_row:.1f}".rstrip('0').rstrip('.'), td_center_style),
                        Paragraph(f"{min_credits:.1f}".rstrip('0').rstrip('.'), td_center_style),
                        Paragraph(f"{max_credits:.1f}".rstrip('0').rstrip('.'), td_center_style),
                        Paragraph(str(students_registered), td_center_style)
                    ])

                course_summary_table = Table(
                    course_summary_data,
                    colWidths=SUMMARY_COL_WIDTHS,
                    repeatRows=1
                )

                course_summary_table.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CFCFCF")),
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F7F7F7")),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('ALIGN', (0,1), (0,-1), 'LEFT'),
                    ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ]))

                story.append(course_summary_table)
                story.append(Spacer(1, 10))
                
                # ============================================
                # COURSE DETAILS - GROUPED BY TYPE
                # ============================================
                sorted_categories = sorted(grouped_courses.items(), key=lambda x: x[0])
                
                def create_course_section(category_name, courses_data):
                    """Create a single course section with heading and table"""
                    section_elements = []
                    
                    section_elements.append(Paragraph(category_name, course_type_style))
                    
                    course_data = []
                    course_data.append([
                        Paragraph("Course Title", th_style),
                        Paragraph("Credits", th_style),
                        Paragraph("<para align='center'>Students Registered</para>", th_style)
                    ])
                    
                    for course in sorted(courses_data, key=lambda x: x['course_title']):
                        course_data.append([
                            Paragraph(course['course_title'], course_title_style),
                            Paragraph(f"{course['credits']:.1f}".rstrip('0').rstrip('.'), td_center_style),
                            Paragraph(str(course['students_registered']), td_center_style)
                        ])
                    
                    course_table = Table(
                        course_data,
                        colWidths=COURSE_COL_WIDTHS,
                        repeatRows=1
                    )
                    
                    course_table.setStyle(TableStyle([
                        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CFCFCF")),
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F7F7F7")),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,-1), 8),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('ALIGN', (0,0), (-1,0), 'CENTER'),
                        ('ALIGN', (0,1), (0,-1), 'LEFT'),
                        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
                        ('TOPPADDING', (0,0), (-1,-1), 5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                        ('LEFTPADDING', (0,0), (-1,-1), 4),
                        ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ]))
                    
                    section_elements.append(course_table)
                    section_elements.append(Spacer(1, 0.05 * inch))
                    
                    return section_elements
                
                for category, courses in sorted_categories:
                    if not courses:
                        continue
                    
                    valid_courses = [c for c in courses if c['course_title'] and c['course_title'].strip()]
                    if not valid_courses:
                        continue
                    
                    story.extend(create_course_section(category, valid_courses))
                
                # Build the PDF
                doc.build(story)
                
                print(f"✅ [PDF] PDF generated successfully!")
                
                return FileResponse(
                    temp_path,
                    media_type='application/pdf',
                    filename=f"Student_Course_Registration_Setup_{request.curriculum}_{request.term}.pdf"
                )
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
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
    

    


