from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Caste, IEMExamSession, IEMExamStudentCourses, IEMParentsOccupationMaster, IEMProgram, IEMProgramType, IEMSAcademicBatch, IEMSCIAStudentCourses, IEMSCIOccasionType, IEMSCourseType, IEMSDepartment, IEMSEventTypeMaster, IEMSUserRoleMaster, IEMSUserRoles, IEMSUsers, IEMStudents


def check_common_validation(
    db: Session, 
    flag: str, 
    value_to_check: str, 
    id: int, 
    org_id: int, 
    is_org_id: bool = True, 
    is_status_check: bool = False
) -> int:
    """Common validation function to check for duplicates based on the case provided."""
    column_name, condition_name, model_class = None, None, None

    # Determine the model class and attributes based on the flag
    if flag == 'program_type':
        column_name = 'pgmtype_id'
        condition_name = 'pgmtype_name'
        model_class = IEMProgramType
    elif flag == 'program':
        column_name = 'pgm_id'
        condition_name = 'pgm_title'
        model_class = IEMProgram
    elif flag == 'academic_batch':
        column_name = 'academic_batch_id'
        condition_name = 'academic_batch_code'
        model_class = IEMSAcademicBatch
    elif flag == 'department':
        column_name = 'dept_id'
        condition_name = 'dept_name'
        model_class = IEMSDepartment
    elif flag == 'cia_occasion_type':
        column_name = 'cia_occasion_type_id'
        condition_name = 'cia_occasion_type_code'
        model_class = IEMSCIOccasionType
    elif flag == 'cia_occasion':
        column_name = 'occasion_id'
        condition_name = 'occasion_id'
        model_class = IEMSCIAStudentCourses
        is_org_id = False
    elif flag == 'mobile':
        column_name = 'student_id'
        condition_name = 'mobile'
        model_class = IEMStudents
        is_org_id = False
    elif flag == 'usn':
        column_name = 'student_id'
        condition_name = 'usno'
        model_class = IEMStudents
        is_org_id = False
        is_status_check = True
    elif flag == 'course_type':
        column_name = 'course_type_id'
        condition_name = 'course_type_code'
        model_class = IEMSCourseType
    elif flag == 'username':
        column_name = 'id'
        condition_name = 'username'
        model_class = IEMSUsers
        is_org_id = False
    elif flag == 'user_email':
        column_name = 'id'
        condition_name = 'email'
        model_class = IEMSUsers
        is_org_id = False
    elif flag == 'session':
        column_name = 'exam_session_id'
        condition_name = 'session'
        model_class = IEMExamSession
    elif flag == 'hall_master':
        column_name = 'id'
        condition_name = 'hall_id'
        model_class = IEMExamStudentCourses
        is_org_id = False
        is_status_check = True
    elif flag == 'event_master':
        column_name = 'event_master_id'
        condition_name = 'event_master_type'
        model_class = IEMSEventTypeMaster
        is_org_id = False
        is_status_check = True
    elif flag == 'user_role':
        column_name = 'userrole_id'
        condition_name = 'role_id'
        model_class = IEMSUserRoles
    elif flag == 'user_role_name':
        column_name = 'user_role_id'
        condition_name = 'user_role'
        model_class = IEMSUserRoleMaster
        is_org_id = False
    elif flag == 'parents_occupation':  # New case for occupation
        column_name = 'occupation_id'
        condition_name = 'occupation_description'
        model_class = IEMParentsOccupationMaster
    elif flag == 'caste':  # New case for caste
        column_name = 'caste_id'
        condition_name = 'name'
        model_class = Caste
    else:
        return 1  

    # Build the query
    query = select(model_class).where(getattr(model_class, condition_name) == value_to_check.strip())

     # Check for org_id only if the model supports it
    if is_org_id and hasattr(model_class, 'org_id'):
        query = query.where(getattr(model_class, 'org_id') == org_id)
    # Check for status only if the model supports it   
    if is_status_check and hasattr(model_class, 'status'):
        query = query.where(getattr(model_class, 'status') == 1)

    result = db.execute(query).scalars().all()
    
    # Check if any records exist
    if result:
        if getattr(result[0], column_name) == id:
            return 1  # Duplicate found but same ID
        return 0  # Duplicate found with different ID

    return 1  # No duplicates found


def check_duplicateemail(
    db: Session,email: str, user_id: Optional[int], user_type: int
):
    email = email.strip()
    if user_type == 0:
        user = db.query(IEMSUsers).filter(IEMSUsers.email == email, IEMSUsers.status == 1).first()
        user_id_field = 'id'
    else:
        user = db.query(IEMStudents).filter(IEMStudents.email == email, IEMStudents.status == 1).first()
        user_id_field = 'student_id'
    # Check if email exists and matches the provided ID
    if user:
        if getattr(user, user_id_field) == user_id:
            return 1
        return 0
    return 1


def check_roll_number(request,db: Session):
    query = db.query(IEMStudents.student_id).filter(
        IEMStudents.roll_number == request.roll_number,
        IEMStudents.academic_batch_id == request.academic_batch_id,
        IEMStudents.current_semester == request.current_semester,
        IEMStudents.program_id == request.program_id
    )
    if request.student_id:
        query = query.filter(IEMStudents.student_id != request.student_id)
    exists = db.query(query.exists()).scalar()
    return 1 if exists else 0