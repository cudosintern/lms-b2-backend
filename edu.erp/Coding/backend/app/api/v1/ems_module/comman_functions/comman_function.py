from typing import Dict, Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy import and_, or_, asc, distinct, func, text, update
from sqlalchemy.orm import Session
from datetime import datetime

from app.utils.set_password_helper import set_private_password, validate_old_password
from .comman_function_utils import attendance_processing, cia_evaluate_processing, cia_processing, cia_see_processing, \
    drop, faculty_cia_processing, faculty_tw_processing, fetch_branch_change_students, fetch_evaluate_list, \
    fetch_in_eligible_list, fetch_students_attendance, get_absentee, get_branch_change, get_grace_attendance, \
    get_student_course, get_viva_absentee, grade_processing, result_finalize_grade_processing, see_evaluate_processing, \
    see_processing, tw_grade_processing, viva_processing, withdraw
from .....utils.comman_function import get_department_permission
from .comman_function_schema import AcademicBatchRequest, BatchCycleFilter, BloomDomainRequest, ChangePasswordRequest, \
    CheckCourseRequest, CheckEligibilityRequest, CheckGradeEvaluateRequest, CheckRevalDatesRequest, CityListRequest, \
    CycleRequest, CycleSemesterResponse, FetchStudentCourseRequest, ForgotPasswordRequest, GetAcademicBatchRequest, \
    GetProgramOptionsRequest, GetSemesterListRequest, GetSemesterRequest, GradeTypeRequest, IsResultYearBacklog, \
    ParamRequestModel, DepartmentListReq, ProgramTypeListReq, ResultYearRequest, SectionRequest, SemesterCheckRequest, \
    SemesterRequest, SetApproveRequest, SoftDeleteRequest, StateRequest, StudentProgramRequest, \
    StudentSectionListRequest, ComputeOpenElectiveCIARequest, StudentCourseRequestParams
from .....db.models import Caste, City, Country, IEMExamEvent, IEMExamHallMaster, IEMExamSession, IEMGrade, \
    IEMLabCourseBatch, IEMOrgConfigs, IEMOrganisation, IEMParentsOccupationMaster, IEMSAcademicBatch, IEMSBatchCycle, \
    IEMSCIAExamMaster, IEMSCIAStudentCourses, IEMSCIOccasionType, IEMSClassTimings, IEMSCourseType, IEMSCourses, \
    IEMSCrsFaculty, IEMSEventCalenderDetails, IEMSEventStatus, IEMSDepartment, IEMProgramType, IEMProgram, \
    IEMSEventTypeMaster, IEMSProgressionRules, IEMSTemplate, IEMSTtDaysSet, IEMSUserCourseMgmt, IEMSUserRoleMaster, \
    IEMSUserRoles, IEMSUsers, IEMSection, IEMSemTimeTable, IEMSemester, IEMStudents, PhysicallyChallengedDescription, \
    State, StudentCourse
from ...cudo_module.bloom_domain.model.bloom_domain_model import BloomDomain
from .....utils.auth_helper import get_current_user
from .....utils.http_return_helper import returnSuccess, returnException
from .....core.database import get_db, get_db_pool

router = APIRouter()


@router.post("/fetch_result_year")
def fetch_result_year(
        request_data: ResultYearRequest, current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        # Unpack the parameters
        flag = request_data.flag
        show_all = request_data.show_all

        # Query the database
        query = db.query(
            IEMExamEvent.result_year,
            IEMExamEvent.event_type,
            IEMExamEvent.event_status,
            IEMExamEvent.result_year,
            IEMExamEvent.semester_start_date,
            IEMExamEvent.semester_end_date,
            IEMExamEvent.see_start_date,
            IEMExamEvent.see_end_date
        ).join(
            IEMSEventStatus, IEMExamEvent.event_status == IEMSEventStatus.id
        ).filter(IEMExamEvent.status == 1, IEMExamEvent.org_id == org_id)

        query = query.distinct(IEMExamEvent.result_year)
        # Handle flag conditions
        if flag == 'time_table':
            query = query.add_columns(IEMExamEvent.see_start_date, IEMExamEvent.see_end_date)

        # Show all or filter by current
        if not show_all:
            query = query.filter(IEMSEventStatus.event_status == "Current")

        # Apply flag-specific filters
        if flag == 'belonging_years':
            query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3, 5, 6]))
        elif flag == 'course_years':
            query = query.filter(IEMExamEvent.event_type.in_([1, 2]))
        elif flag == 'fastrack':
            query = query.filter(IEMExamEvent.event_type == 5)
        elif flag == 'makeup':
            query = query.filter(IEMExamEvent.event_type == 4)
        elif flag == 'backlog':
            query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3]))
        elif flag == 'gc_years':
            query = query.filter(IEMExamEvent.event_type.in_([1, 2, 5, 6]))
        elif flag == 'supplementary':
            query = query.filter(IEMExamEvent.event_type == 6)
        elif flag == 'reeval_marks':
            query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3, 4, 5, 6]))

        result_years = query.order_by(IEMExamEvent.result_year.desc()).all()

        # unique_result_years = {}
        # for year in result_years:
        #     if year.result_year not in unique_result_years:
        #         # Add the first occurrence of the result_year to the dictionary
        #         unique_result_years[year.result_year] = {
        #             'result_year': year.result_year,
        #             'event_type': year.event_type,
        #             'event_status': year.event_status,
        #             'result_year_dd': year.result_year,
        #             'see_start_date': year.see_start_date if year.see_start_date else '',
        #             'see_end_date': year.see_end_date if year.see_end_date else '',
        #             'semester_start_date': year.semester_start_date,
        #             'semester_end_date': year.semester_end_date,
        #         }

        # Prepare the result year data
        result_year_data = []
        for year in result_years:
            result_year_data.append({
                'result_year': year.result_year,
                'event_type': year.event_type,
                'event_status': year.event_status,
                'result_year_dd': year.result_year,
                'see_start_date': year.see_start_date if year.see_start_date else '',
                'see_end_date': year.see_end_date if year.see_end_date else '',
                'semester_start_date': year.semester_start_date,
                'semester_end_date': year.semester_end_date,
            })

        return returnSuccess(result_year_data)
    except Exception as e:
        raise e


@router.post("/fetch_result_year_options")
async def fetch_result_year_options(
        request: ParamRequestModel,
        db: Session = Depends(get_db), current_user: str = Depends(get_current_user),
        org_id: Optional[int] = Header(None)
):
    if org_id is None:
        org_id = 1
    result_years = fetch_result_year(request, db, org_id)
    if not result_years:
        return returnException("No result years found")

    return returnSuccess(result_years)


def fetch_result_year(param: ParamRequestModel, db: Session, org_id: int):
    # Base query
    query = db.query(
        IEMExamEvent.result_year,
        IEMExamEvent.event_type,
        IEMExamEvent.semester_start_date,
        IEMExamEvent.semester_end_date,
        IEMExamEvent.result_year.label('result_year_dd')
    )
    if param.flag == 'time_table':
        query = query.add_columns(IEMExamEvent.see_end_date, IEMExamEvent.see_start_date)

    # Apply joins and filters
    query = query.join(IEMSEventStatus, IEMExamEvent.event_status == IEMSEventStatus.id)
    query = query.filter(IEMExamEvent.status == 1, IEMExamEvent.org_id == org_id)

    # Conditional filtering based on `show_all` flag
    if not param.show_all:
        query = query.filter(IEMSEventStatus.event_status == 'Current')

    # Apply ordering
    query = query.order_by(IEMExamEvent.result_year.desc())

    # Apply filtering based on `flag`
    if param.flag == 'belonging_years':
        query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3, 5, 6]))
    elif param.flag == 'course_years':
        query = query.filter(IEMExamEvent.event_type.in_([1, 2]))
    elif param.flag == 'fastrack':
        query = query.filter(IEMExamEvent.event_type.in_([5]))
    elif param.flag == 'makeup':
        query = query.filter(IEMExamEvent.event_type.in_([4]))
    elif param.flag == 'backlog':
        query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3]))
    elif param.flag == 'gc_years':
        query = query.filter(IEMExamEvent.event_type.in_([1, 2, 5, 6]))
    elif param.flag == 'supplementary':
        query = query.filter(IEMExamEvent.event_type.in_([6]))
    elif param.flag == 'reeval_marks':
        query = query.filter(IEMExamEvent.event_type.in_([1, 2, 3, 4, 5, 6]))

    # Execute the query and fetch results
    result = query.all()

    # Convert the result to a list of Pydantic models
    result_array = [
        {
            'result_year': row.result_year,
            'event_type': row.event_type,
            'result_year_dd': row.result_year_dd,
            'semester_start_date': row.semester_start_date.strftime("%d-%m-%Y") if row.semester_start_date else None,
            'semester_end_date': row.semester_end_date.strftime("%d-%m-%Y") if row.semester_end_date else None
        } for row in result
    ]
    return result_array


@router.post("/department_list")
def department_list(
        params: DepartmentListReq,
        current_user: str = Depends(get_current_user),
        org_id: Optional[int] = Header(None),
        db: Session = Depends(get_db)
):
    try:
        if org_id is None:
            # print("DEBUG: org_id header missing, defaulting to 1")
            org_id = 1
            
        # print(f"DEBUG: department_list called with params: {params}, org_id: {org_id}")
        
        logged_user_id = current_user.get("user_id")
        
        # FIX: Allow departments with NULL org_id (legacy data support)
        query = db.query(IEMSDepartment).filter(or_(IEMSDepartment.org_id == org_id, IEMSDepartment.org_id == None))

        if logged_user_id != 1:
            # Also allow NULL org_id for non-superusers if that's the intended behavior for shared depts
            query = query.filter(or_(IEMSDepartment.org_id == org_id, IEMSDepartment.org_id == None))

        if params.equal_or_not_equal and params.dept_id:
            query = query.filter(IEMSDepartment.dept_id != params.dept_id)

        departments = query.order_by(IEMSDepartment.dept_name).all()
        print(f"DEBUG: Found {len(departments)} departments")

        return returnSuccess([{
            "department_id": d.dept_id,
            "dept_name": d.dept_name,
            "dept_acronym": d.dept_acronym,
            "dept_code_usn": d.dept_code_usn,
            "dept_description": d.dept_description,
            "no_batch_dept": d.no_batch_dept,
            "status": 1 if d.status else 0,
            "org_id": d.org_id,
            "create_date": d.create_date,
            "created_by": d.created_by,
            "modify_date": d.modify_date,
            "modified_by": d.modified_by
        } for d in departments])

    except Exception as e:
        print(f"DEBUG: Exception in department_list: {e}")
        raise e


@router.post("/program_type_list")
def program_type_list(
        req: ProgramTypeListReq,
        current_user: str = Depends(get_current_user),
        db: Session = Depends(get_db),
        org_id: int = Header(...)
):
    try:
        program_type_list = fetch_program_type_list(db, req.show_delete, org_id)
        program_type_data = [
            {
                'pgmtype_id': p.pgmtype_id,
                'pgmtype_name': p.pgmtype_name,
                'program_type_code': p.program_type_code,
                'pgmtype_description': p.pgmtype_description,
                'status': p.status
            } for p in program_type_list
        ]
        return returnSuccess(program_type_data)
    except Exception as e:
        raise e


def fetch_program_type_list(db: Session, show_delete: ProgramTypeListReq, org_id: int):
    query = db.query(
        IEMProgramType.pgmtype_id,
        IEMProgramType.pgmtype_name,
        IEMProgramType.program_type_code,
        IEMProgramType.pgmtype_description,
        IEMProgramType.status
    ).filter(IEMProgramType.org_id == org_id)

    if show_delete != 1:
        query = query.filter(IEMProgramType.status == 1)
    return query.all()


@router.post("/get_programs")
def get_programs(
        request: StudentProgramRequest,
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        programs_data = get_programs_list(db, request, current_user, org_id)
        return returnSuccess(programs_data)
    except Exception as e:
        raise e


def get_programs_list(db: Session, request: StudentProgramRequest, current_user: str, org_id: int):
    dept_id = request.dept_id
    show_delete = request.show_delete
    equal_or_not_equal = request.equal_or_not_equal
    user_id = current_user.get('user_id')

    results = db.query(
        IEMSDepartment.dept_id,
        IEMSDepartment.dept_name,
        IEMProgram.pgm_id,
        IEMProgram.pgm_title,
        IEMProgram.pgm_acronym,
        IEMProgramType.pgmtype_id,
        IEMProgramType.pgmtype_name,
        IEMProgram.status,
        IEMProgram.pgm_specialization,
    ).join(IEMSDepartment, IEMProgram.dept_id == IEMSDepartment.dept_id) \
        .join(IEMProgramType, IEMProgram.pgmtype_id == IEMProgramType.pgmtype_id) \
        .filter(IEMProgram.org_id == org_id)

    no_permission = get_department_permission(user_id, current_user, db)
    if no_permission:
        results = results.join(IEMSUserCourseMgmt, IEMSUserCourseMgmt.program_id == IEMProgram.pgm_id) \
            .filter(IEMSUserCourseMgmt.user_id == user_id)

    if show_delete != 1:
        results = results.filter(IEMProgram.status == 1)

    # if equal_or_not_equal:
    #     results = results.filter(IEMProgram.dept_id == dept_id)

    if dept_id:
        results = results.filter(IEMProgram.dept_id == dept_id)

    # Order by program title
    results = results.order_by(IEMProgram.pgm_id).all()

    # Convert results to a list of dictionaries
    programs_list = [dict(result._mapping) for result in results]
    return programs_list


@router.post("/is_result_yearbacklog")
def is_result_yearbacklog(
        request: IsResultYearBacklog,
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        data = is_result_yearbacklog_db(db, request, current_user, org_id)
        return returnSuccess(data)
    except Exception as e:
        raise e


def is_result_yearbacklog_db(db: Session, request: IsResultYearBacklog, current_user: str, org_id: int):
    belonging_year_query = db.query(IEMExamEvent.belonging_year).filter(
        IEMExamEvent.result_year == request.result_year, IEMExamEvent.org_id == org_id
    ).first()

    if not belonging_year_query:
        return returnException("Belonging year not found")

    belonging_year = belonging_year_query[0]

    query = db.query(StudentCourse.regno).filter(
        StudentCourse.result_year == belonging_year,
        StudentCourse.is_backlog == True
    )
    # Apply optional filtering for program_id and batch_id
    if request.program_id is not None:
        query = query.filter(StudentCourse.program_id == request.program_id)

    if request.batch_id is not None:
        query = query.filter(StudentCourse.batch_id == request.batch_id)

    rowcount = query.count()
    return rowcount


@router.post("/academic_batch_list")
def academic_batch_list(
        request: AcademicBatchRequest,
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        academic_batch_data = fetch_academic_batch_list_data(db, request, current_user, org_id)
        return returnSuccess(academic_batch_data)
    except Exception as e:
        raise e


def fetch_academic_batch_list_data(db: Session, request: AcademicBatchRequest, current_user: str, org_id: int):
    show_delete = request.show_delete
    program_id = request.program_id
    org_id = org_id
    user_id = current_user.get('user_id')

    # Query building
    query = db.query(
        IEMSAcademicBatch.academic_batch_id,
        IEMSAcademicBatch.academic_batch_code,
        IEMSAcademicBatch.academic_batch_desc,
        IEMSAcademicBatch.academic_year,
        IEMSAcademicBatch.status,
        IEMSAcademicBatch.grade_type,
        IEMSAcademicBatch.is_tw_course,
        IEMSAcademicBatch.regulation_year,
        IEMSAcademicBatch.program_duration,
        IEMProgram.pgm_id,
        IEMProgram.pgm_title,
        IEMProgram.pgm_acronym,
        IEMProgram.pgm_specialization,
        IEMSDepartment.dept_id,
        IEMSDepartment.dept_name
    ).join(
        IEMProgram, IEMSAcademicBatch.pgm_id == IEMProgram.pgm_id
    ).join(
        IEMSDepartment, IEMSAcademicBatch.dept_id == IEMSDepartment.dept_id
    ).filter(
        IEMSAcademicBatch.org_id == org_id
    )

    # Check department permission
    no_permission = get_department_permission(user_id, current_user, db)
    if no_permission:
        query = query.join(IEMSUserCourseMgmt,
                           IEMSUserCourseMgmt.academic_batch_id == IEMSAcademicBatch.academic_batch_id) \
            .filter(IEMSUserCourseMgmt.user_id == user_id)

    # Filter by batch status (show_delete)
    if show_delete != 1:
        query = query.filter(IEMSAcademicBatch.status == 1)

    # Filter by program ID
    if program_id:
        query = query.filter(IEMProgram.pgm_id == program_id)

    # Order and execute query
    result = query.order_by(IEMSAcademicBatch.academic_batch_code).all()
    academic_batch_data = []
    for row in result:
        academic_batch_data.append({
            'academic_batch_id': row.academic_batch_id,
            'academic_batch_code': row.academic_batch_code,
            'academic_batch_desc': row.academic_batch_desc,
            'academic_year': row.academic_year,
            'program_duration': row.program_duration,
            'dept_id': row.dept_id,
            'dept_name': row.dept_name,
            'pgm_id': row.pgm_id,
            'pgm_title': row.pgm_title,
            'pgm_acronym': row.pgm_acronym,
            'pgm_specialization': row.pgm_specialization,
            'status': row.status,
            'grade_type': row.grade_type,
            'is_tw_course': row.is_tw_course if row.is_tw_course else '',
            'regulation_year': row.regulation_year if row.regulation_year else ''
        })

    return academic_batch_data


@router.post("/get_semester_list")
def get_semester_list(
        request: GetSemesterRequest,
        db: Session = Depends(get_db),
        org_id: int = Header(...),
        current_user: str = Depends(get_current_user)
):
    try:
        # Fetch the semester list based on the request
        semester_data = fetch_semester_data(request, db, current_user, org_id)
        return returnSuccess(semester_data)
    except Exception as e:
        raise e


def fetch_semester_data(request: GetSemesterRequest, db: Session, current_user: str, org_id: int):
    # Extract request parameters
    academic_batch_id = request.academic_batch_id
    result_year = request.result_year
    is_course = request.is_course
    is_first_year = request.is_first_year
    flag = request.flag

    result_list = []
    unique_semesters = {}
    # Check for 'makeup_semester' flag condition
    if flag == 'makeup_semester':
        # Fetch event status for makeup semester
        event_status = db.query(IEMExamEvent.event_status) \
            .filter(IEMExamEvent.result_year == result_year, IEMExamEvent.org_id == org_id) \
            .first()

        # Proceed if event_status exists and is 1
        if event_status and event_status[0] == 1:
            semesters = db.query(
                StudentCourse.semester,
                IEMSemester.semester_id,
                IEMSemester.semester_desc,
                IEMSemester.branch_cycle,
                IEMSemester.academic_year_planned,
                db.query(IEMSBatchCycle.batch_cycle_id)
                .filter(
                    IEMSBatchCycle.status == 1,
                    IEMSBatchCycle.batch_cycle_code == IEMSemester.branch_cycle
                ).label("batch_cycle_id")  # Batch cycle ID subquery
            ) \
                .join(IEMSemester, (IEMSemester.semester == StudentCourse.semester) &
                      (IEMSemester.academic_batch_id == academic_batch_id)) \
                .filter(
                StudentCourse.batch_id == academic_batch_id,
                StudentCourse.result_year == result_year
            ) \
                .distinct() \
                .all()

            # Build list of dictionaries for 'makeup_semester'
            for row in semesters:
                if row.semester not in unique_semesters:
                    unique_semesters[row.semester] = True
                    result_list.append({
                        "semester": row.semester,
                        "semester_id": row.semester_id,
                        "semester_desc": row.semester_desc,
                        "branch_cycle": row.branch_cycle,
                        "academic_year_planned": row.academic_year_planned,
                        "batch_cycle_id": row.batch_cycle_id
                    })

    else:
        # General query construction for non-makeup semesters
        query = db.query(
            IEMSemester.semester,
            IEMSemester.semester_id,
            IEMSemester.semester_desc,
            IEMSemester.branch_cycle,
            IEMSemester.academic_year_planned,
            db.query(IEMSBatchCycle.batch_cycle_id)
            .filter(
                IEMSBatchCycle.status == 1,
                IEMSBatchCycle.batch_cycle_code == IEMSemester.branch_cycle
            ).label("batch_cycle_id")
        ).filter(
            IEMSemester.org_id == org_id,
            IEMSemester.status == 1
        )

        # Check for permissions and join with user course management table if needed
        no_permission = get_department_permission(None, current_user, db)
        if no_permission:
            query = query.join(
                IEMSUserCourseMgmt,
                (IEMSUserCourseMgmt.semester == IEMSemester.semester) &
                (IEMSUserCourseMgmt.academic_batch_id == academic_batch_id) &
                (IEMSUserCourseMgmt.user_id == current_user.get("user_id"))
            )

        # Apply filters based on request parameters
        if academic_batch_id:
            query = query.filter(IEMSemester.academic_batch_id == academic_batch_id)

        # Filter semesters by course status
        if is_course == 1:
            query = query.filter(IEMSemester.semester_status.in_(['Current', 'Completed']))
        elif is_course == 2:
            query = query.filter(IEMSemester.semester_status == 'Completed')
        else:
            query = query.filter(IEMSemester.semester_status == 'Current')

        # Filter by program year if 'is_first_year' is true
        if is_first_year:
            query = query.filter(IEMSemester.program_year == 1)

        # Execute query and build result list
        semesters = query.distinct().all()
        for row in semesters:
            if row.semester not in unique_semesters:
                unique_semesters[row.semester] = True
                result_list.append({
                    "semester": row.semester,
                    "semester_id": row.semester_id,
                    "semester_desc": row.semester_desc,
                    "branch_cycle": row.branch_cycle,
                    "academic_year_planned": row.academic_year_planned,
                    "batch_cycle_id": row.batch_cycle_id
                })

    return result_list


@router.post("/get_cycle_semester_list")
def get_cycle_semester_list(request: CycleSemesterResponse, current_user: str = Depends(get_current_user),
                            org_id: int = Header(...),
                            db: Session = Depends(get_db)):
    try:
        return returnSuccess(fetch_cycle_semester_list(request, org_id, db))
    except Exception as e:
        raise e


def fetch_cycle_semester_list(request: CycleSemesterResponse, org_id: int, db: Session):
    semester_data = []

    if request.flag == '1':
        # Query for IEMSStudentCourses
        result = db.query(distinct(StudentCourse.semester)).filter(
            StudentCourse.result_year == request.result_year,
            StudentCourse.org_id == org_id
        ).all()

    else:
        # Query for IEMSStudents and join with other necessary tables
        result = db.query(distinct(IEMStudents.current_semester)).join(
            IEMSemester,
            IEMStudents.academic_batch_id == IEMSemester.academic_batch_id
        ).filter(
            IEMStudents.result_year == request.result_year,
            IEMStudents.org_id == org_id,
            IEMStudents.status == 1
        ).all()

    # Prepare the response data
    for row in result:
        semester_data.append({"semester": row[0]})  # row[0] since we are fetching distinct values
    return semester_data


@router.post("/batch_cycle_list")
def get_batch_cycle_list(
        request: BatchCycleFilter,
        current_user: str = Depends(get_current_user), org_id: int = Header(...), db: Session = Depends(get_db)
):
    batch_cycle_list = fetch_batch_cycle_list(db, request, org_id)
    try:
        return returnSuccess(batch_cycle_list)
    except Exception as e:
        raise e


def fetch_batch_cycle_list(db: Session, request: BatchCycleFilter, org_id: int):
    # Create base query
    query = db.query(
        IEMSBatchCycle.batch_cycle_id,
        IEMSBatchCycle.batch_cycle_code,
        IEMSBatchCycle.batch_cycle_desc
    ).filter(IEMSBatchCycle.status == 1)

    # Apply filters based on parameters
    if request.show_branch == '0':
        query = query.filter(IEMSBatchCycle.batch_cycle_code != 'Branch')

    if request.show_both == '0':
        query = query.filter(IEMSBatchCycle.batch_cycle_code != 'Both')

    if request.show_na == '0':
        query = query.filter(IEMSBatchCycle.batch_cycle_code != 'N/A')

    # Execute the query and fetch results
    result = query.all()

    # Convert the result into a list of dictionaries for easier serialization
    batch_cycle_data = [
        {
            "batch_cycle_id": batch_cycle.batch_cycle_id,
            "batch_cycle_code": batch_cycle.batch_cycle_code,
            "batch_cycle_desc": batch_cycle.batch_cycle_desc
        }
        for batch_cycle in result
    ]
    return batch_cycle_data


# @router.post("/fetch_student_section_list")
# def fetch_student_section_list(request_data: SectionListRequest,current_user: str = Depends(get_current_user),org_id: int = Header(...),
#  db: Session = Depends(get_db)):
#     try:
#         result_year = request_data.result_year
#         crs_code = request_data.crs_code
#         academic_batch_id = request_data.academic_batch_id
#         flag = request_data.flag
#         not_na = request_data.not_na
#         crs_id = request_data.crs_id
#         faculty_id = request_data.faculty_id
#         is_class_attendance = request_data.is_class_attendance

#         # Start building the query
#         query = db.query(IEMSection).distinct(IEMSection.section, IEMSection.id)

#         # Add academic batch filter
#         if academic_batch_id:
#             query = query.filter(IEMSUserCourseMgmt.academic_batch_id == academic_batch_id)

#         # Join with user course management table for permission checks
#         user_id=current_user.get('user_id')
#         no_permission = True

#         if no_permission:
#             query = query.join(
#                 IEMSUserCourseMgmt,
#                 and_(
#                     IEMSUserCourseMgmt.section == IEMSection.section,
#                     IEMSUserCourseMgmt.crs_code == crs_code,
#                     IEMSUserCourseMgmt.user_id == user_id,
#                     IEMSUserCourseMgmt.result_year == result_year
#                 ),
#                 isouter=True
#             )

#         # Class attendance logic
#         if is_class_attendance:
#             query = query.join(
#                 IEMSemTimeTable,
#                 IEMSemTimeTable.section == IEMSection.section
#             ).join(
#                 IEMSCrsFaculty,
#                 and_(
#                     IEMSCrsFaculty.sem_time_table_id == IEMSemTimeTable.id,
#                     IEMSCrsFaculty.crs_id == crs_id,
#                     IEMSCrsFaculty.faculty_id == faculty_id
#                 )
#             )

#         # Exclude 'N/A' sections if applicable
#         if not_na:
#             query = query.filter(IEMSection.section != 'N/A')

#         # Execute the query and fetch results
#         sections = query.all()

#         # Prepare the response data
#         section_data = []
#         for section in sections:
#             section_data.append({
#                 'id': section.id if section.id else '',
#                 'section': section.section
#             })

#         return returnSuccess(section_data)
#     except Exception as e:
#         raise e


@router.post("/garde_type_list")
def garde_type_list(
        request: GradeTypeRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        # Fetch the grade type list
        grade_type_data = fetch_grade_type_list(db, org_id, request.show_delete)

        # Format the response as per the original structure
        formatted_data = [
            {
                "grade_id": grade.grade_id,
                "grade": grade.grade,
                "grade_level": grade.grade_level,
                "min_range": grade.min_range,
                "max_range": grade.max_range,
                "grade_point": grade.grade_point,
                "grade_type": grade.grade_type
            }
            for grade in grade_type_data
        ]

        return returnSuccess(formatted_data)  # Using your custom returnSuccess method
    except Exception as e:
        raise e


@router.post("/bloom_domain_list")
def bloom_domain_list(
        params: BloomDomainRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        query = db.query(BloomDomain).filter(BloomDomain.org_id == org_id, BloomDomain.status != 2)

        if params.show_delete != 1:
            query = query.filter(BloomDomain.status == 1)

        bloom_domains = query.order_by(BloomDomain.bloom_domain_id).all()

        return returnSuccess([{
            "bloom_domain_id": d.bloom_domain_id,
            "bloom_domain_name": d.bloom_domain_name,
            "bloom_domain_acronym": d.bloom_domain_acronym,
            "bloom_domain_description": d.bloom_domain_description,
            "status": d.status,
            "org_id": d.org_id,
            "create_date": d.create_date.strftime("%Y-%m-%d %H:%M:%S") if d.create_date else None,
            "created_by": d.created_by,
            "modify_date": d.modify_date.strftime("%Y-%m-%d %H:%M:%S") if d.modify_date else None,
            "modified_by": d.modified_by
        } for d in bloom_domains])

    except Exception as e:
        raise e


def fetch_grade_type_list(db: Session, org_id: int, show_delete: bool):
    # Query to fetch distinct grade types based on org_id
    query = (
        db.query(IEMGrade.grade_id, IEMGrade.grade, IEMGrade.grade_level,
                 IEMGrade.min_range, IEMGrade.max_range, IEMGrade.grade_point,
                 IEMGrade.grade_type)
        .filter(IEMGrade.org_id == org_id)
        .distinct()
        .group_by(IEMGrade.grade_type)
        .order_by(IEMGrade.grade_id)
    )

    # If show_delete flag is set, modify query accordingly (if needed)
    if show_delete:
        # Apply any filter based on 'show_delete' value if required
        pass

    return query.all()


@router.post("/fetch_org_configs")
def fetch_org_configs_route(
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        # Fetch organization configurations using the helper function
        org_configs = fetch_org_configs(db, org_id)
        return returnSuccess(org_configs)
    except Exception as e:
        # Handle any exceptions and return a 500 response
        raise e


def fetch_org_configs(db: Session, org_id: int):
    # Perform the query using SQLAlchemy's func to call the database function
    result = (
        db.query(
            func.get_configs_value(org_id, None, None, "viva_course").label("check_viva"),
            func.get_configs_value(org_id, None, None, "combine_course").label("check_combine_course"),
            func.get_configs_value(org_id, None, None, "is_ise_mse").label("check_is_ise_mse"),
            func.get_configs_value(org_id, None, None, "link_course").label("check_link_course"),
            func.get_configs_value(org_id, None, None, "is_dvs").label("is_dvs"),
            func.get_configs_value(org_id, None, None, "is_dvs_encrypt").label("is_dvs_encrypt"),
            func.get_configs_value(org_id, None, None, "is_egov_sync").label("is_egov_sync"),
            func.get_configs_value(org_id, None, None, "is_tw_course").label("check_tw_course"),
            func.get_configs_value(org_id, None, None, "cia_master_wise").label("check_ise_course")
        )
    ).all()

    # Convert the result into a dictionary
    org_configs_array = [
        {
            "check_viva": row.check_viva,
            "check_combine_course": row.check_combine_course,
            "check_is_ise_mse": row.check_is_ise_mse,
            "check_link_course": row.check_link_course,
            "is_dvs": row.is_dvs,
            "is_dvs_encrypt": row.is_dvs_encrypt,
            "is_egov_sync": row.is_egov_sync,
            "check_tw_course": row.check_tw_course,
            "check_ise_course": row.check_ise_course
        }
        for row in result
    ]

    return org_configs_array


@router.get("/is_cia_master_wise")
def check_cia_master_wise(org_id: int = Header(...), db: Session = Depends(get_db)):
    try:
        # Call the helper function to check if CIA master wise
        value = is_cia_master_wise(db, org_id)
        if value is not None:
            return returnSuccess(value)
        else:
            return returnException("Configuration not found")
    except Exception as e:
        raise e


def is_cia_master_wise(db: Session, org_id: int) -> str:
    # Query the iems_org_configs table for the specific org_id and config_type
    result = (
        db.query(IEMOrgConfigs.value)
        .filter(IEMOrgConfigs.config_type == "cia_master_wise")
        .filter(IEMOrgConfigs.org_id == org_id)
        .first()
    )
    return result.value if result else None


@router.post("/do_check_course")
def do_check_course(course_data: CheckCourseRequest, db: Session = Depends(get_db)):
    try:
        has_marks = do_check_course(db, course_data)
        return returnSuccess(has_marks)
    except Exception as e:
        raise e


def do_check_course(db: Session, course_data: CheckCourseRequest) -> str:
    query = (
        db.query(
            func.if_(func.max(StudentCourse.is_grade_evaluated) == 0, "n", "y").label("has_marks")
        )
        .filter(
            StudentCourse.crs_code == course_data.crs_code,
            StudentCourse.result_year == course_data.result_year,
            StudentCourse.program_id == course_data.program_id,
            StudentCourse.batch_id == course_data.batch_id,
            StudentCourse.semester == course_data.semester,
        )
        .group_by(StudentCourse.regno)
    )

    # Execute the query
    result = query.first()

    # Check if result is found
    if result is None:
        return 1  # No rows, return 1
    return result.has_marks


@router.post("/fetch_section_list")
def fetch_section_list(
        section_request: SectionRequest,
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        flag = section_request.flag
        section_list = fetch_section_list_service(section_request, db, current_user)
        if flag:
            section_data = [
                {
                    "id": section.id or "",
                    "section": section.section,
                }
                for section in section_list
            ]
            return section_data
        else:
            return section_list
    except Exception as e:
        raise e


def fetch_section_list_service(section_request, db: Session, current_user: str):
    # Extract parameters
    result_year = section_request.result_year
    crs_code = section_request.crs_code
    academic_batch_id = section_request.academic_batch_id
    not_na = section_request.not_na
    crs_id = section_request.crs_id
    faculty_id = section_request.faculty_id
    is_class_attendance = section_request.is_class_attendance

    # Get user information
    user_id = current_user.get("user_id")
    no_permission = get_department_permission(None, current_user, db)

    query = db.query(IEMSection).distinct()

    # Handle user management joining condition
    if no_permission:
        query = query.join(
            IEMSUserCourseMgmt,
            and_(
                IEMSUserCourseMgmt.section == IEMSection.section,
                IEMSUserCourseMgmt.crs_code == crs_code,
                IEMSUserCourseMgmt.user_id == user_id,
                IEMSUserCourseMgmt.result_year == result_year,
                IEMSUserCourseMgmt.academic_batch_id == academic_batch_id if academic_batch_id else None
            ),
        )

    # Handle class attendance joining
    if is_class_attendance:
        query = query.join(IEMSemTimeTable, IEMSemTimeTable.section == IEMSection.section) \
            .join(IEMSCrsFaculty, and_(
            IEMSCrsFaculty.sem_time_table_id == IEMSemTimeTable.id,
            IEMSCrsFaculty.crs_id == crs_id,
            IEMSCrsFaculty.faculty_id == faculty_id,
        ))

    # Exclude N/A sections if specified
    if not_na:
        query = query.filter(IEMSection.section != "N/A")

    results = query.all()
    return results


# @router.get("/get_physically_challenged_descriptions")
# def get_physically_challenged_descriptions(current_user: str = Depends(get_current_user),org_id: int = Header(...),
# db: Session = Depends(get_db)):
#     try:
#         descriptions = db.query(PhysicallyChallengedDescription).all()
#         data = [{"pc_description_id": desc.pc_description_id, "description": desc.description} for desc in descriptions]
#         return returnSuccess(data)
#     except Exception as e:
#         raise e

@router.get("/country_list")
def country_list(
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        country_data = get_country_list(db)
        return returnSuccess(country_data)
    except Exception as e:
        raise e


def get_country_list(db: Session):
    country_list = db.query(Country).distinct().all()
    return [
        {
            'country_id': country.country_id,
            'country_name': country.name,
            'country_sortname': country.sortname
        }
        for country in country_list
    ]


@router.post("/state_list")
def state_list(request: StateRequest, db: Session = Depends(get_db)):
    try:
        query = db.query(State).order_by(State.name).distinct()
        if request.country_id and request.country_id != 0:
            query = query.filter(State.country_id == request.country_id)
        states = query.all()
        data = [{"state_id": state.state_id, "name": state.name, "country_id": state.country_id} for state in states]
        return returnSuccess(data)
    except Exception as e:
        raise e


@router.post("/city_list")
def city_list(
        request: CityListRequest,
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve the city list.
    """
    try:
        city_data = get_city_list(db, request.state_id, request.status)
        return returnSuccess(city_data)
    except Exception as e:
        raise e


def get_city_list(
        db: Session,
        state_id: Optional[int],
        status: int
):
    """
    Fetch the city list from the database.
    """
    # Construct query to join 'city' and 'state' tables
    query = db.query(City, State).join(State, City.state_id == State.state_id)

    # Apply filters based on state_id and status
    if state_id:
        query = query.filter(City.state_id == state_id)

    if status is not None:
        query = query.filter(City.status == status)

    # Execute query
    city_list = query.order_by(City.city_id).all()

    # Prepare response data
    city_data = [
        {
            'city_id': city.city_id,
            'city_name': city.name,
            'state_id': city.state_id,
            'country_id': state.country_id,
            'status': int(city.status)
        }
        for city, state in city_list
    ]
    return city_data


@router.post("/is_cycle")
def is_cycle(request: CycleRequest, db: Session = Depends(get_db)):
    try:
        # Query the database for branch_cycle based on academic_batch_id and semester
        result = db.query(IEMSemester.branch_cycle).filter(
            IEMSemester.academic_batch_id == request.academic_batch_id,
            IEMSemester.semester == request.semester
        ).first()

        # If result is found, return the branch_cycle; otherwise, return None
        branch_cycle = result.branch_cycle if result else None
        return returnSuccess(branch_cycle)

    except Exception as e:
        db.rollback()
        # Raise an HTTP exception for any errors encountered
        raise e


@router.post("/soft_delete")
def soft_delete(
        req: SoftDeleteRequest,
        current_user: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        message = soft_delete_record(req, db)
        return returnSuccess(f"Record {message} successfully.")
    except Exception as e:
        db.rollback()
        raise e


def soft_delete_record(req: SoftDeleteRequest, db: Session):
    # Get the appropriate table name based on the flag
    table_model, primary_key = get_flag_table(req.flag)
    if table_model is None:
        returnException("Invalid table name provided.")

    # If status is 2, perform a hard delete (remove from database)
    if req.status == 2:
        db.query(table_model).filter(getattr(table_model, primary_key) == req.record_id).delete()
        db.commit()
        return "deleted"

    # Determine the status message based on the status field (0 or 1)
    status_message = "activated" if req.status == 1 else "deactivated" if req.status == 0 else None
    if status_message is None:
        return returnException("Invalid status provided. Must be 1 for activated, 0 for deactivated, or 2 for deleted.")

    # Update the status for the given record ID (Soft Delete / Toggle)
    db.query(table_model).filter(getattr(table_model, primary_key) == req.record_id).update({"status": req.status})
    db.commit()
    return status_message


def get_flag_table(flag: str):
    table_mapping = {
        "academic_calender": (IEMExamEvent, "id"),
        "user_mgmt": (IEMSUsers, "id"),
        "department": (IEMSDepartment, "dept_id"),
        "pgm_type": (IEMProgramType, "pgmtype_id"),
        "program": (IEMProgram, "pgm_id"),
        "academic_batch": (IEMSAcademicBatch, "academic_batch_id"),
        "cia_occasion": (IEMSCIOccasionType, "cia_occasion_type_id"),
        "course_type": (IEMSCourseType, "course_type_id"),
        "course": (IEMSCourses, "crs_id"),
        "exam_session": (IEMExamSession, "exam_session_id"),
        "event_type_master": (IEMSEventTypeMaster, "event_master_id"),
        "event_calender": (IEMSEventCalenderDetails, "event_calender_id"),
        "course_lab_batch": (IEMLabCourseBatch, "lab_course_batch_id"),
        "parents_occupation_master": (IEMParentsOccupationMaster, "occupation_id"),
        "student": (IEMStudents, "student_id"),
        "caste_master_dlt": (Caste, "caste_id"),
        "city_master_dlt": (City, "city_id"),
        "tt_type_dlt": (IEMSTtDaysSet, "tt_days_set_id"),
        "timing_dlt": (IEMSClassTimings, "class_timing_id"),
        "cia_master_dlt": (IEMSCIAExamMaster, "id"),
        "hall_master_dlt": (IEMExamHallMaster, "exam_hall_master_id"),
        "progression_rules": (IEMSProgressionRules, "progression_rule_id"),
        "bloom_domain": (BloomDomain, "bloom_domain_id"),
    }
    return table_mapping.get(flag, (None, None))


@router.get("/get_dept_programtype")
def get_dept_programtype_data(
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        departments, program_types = fetch_dept_programtype_data(db, org_id)

        if departments or program_types:
            return returnSuccess({
                "departments": departments,
                "program_types": program_types
            })
        else:
            return returnException("Data not found")
    except Exception as e:
        raise e


def fetch_dept_programtype_data(db: Session, org_id: int):
    departments = db.query(IEMSDepartment).filter(IEMSDepartment.org_id == org_id).all()
    program_types = db.query(IEMProgramType).filter(IEMProgramType.org_id == org_id).all()

    dept_data = [
        {
            "department_id": dept.dept_id,
            "dept_name": dept.dept_name,
            "status": 1 if dept.status else 0,
        }
        for dept in departments
    ]
    pgmtype_data = [
        {
            "pgmtype_id": program_type.pgmtype_id,
            "pgmtype_name": program_type.pgmtype_name,
            "program_type_code": program_type.program_type_code,
        }
        for program_type in program_types
    ]

    return dept_data, pgmtype_data


@router.post("/semester_list")
def semester_list(
        request: SemesterRequest,
        current_user: dict = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        if request.academic_batch_id:
            semester_data = fetch_semester_list(request.academic_batch_id, org_id, db)
            return returnSuccess(semester_data)
        else:
            return returnException("Academic Batch ID is required.")
    except Exception as e:
        return returnException(str(e))


def fetch_semester_list(academic_batch_id: int, org_id: int, db: Session):
    # Query to get semester list
    semester_list = db.query(
        IEMSemester.semester_id,
        IEMSemester.semester_code,
        IEMSemester.academic_batch_id,
        IEMSAcademicBatch.academic_batch_code,
        IEMSemester.academic_year_planned,
        IEMSemester.program_year,
        IEMSemester.semester,
        IEMSemester.semester_desc,
        IEMSemester.semester_flag,
        IEMSemester.semester_status,
        IEMSemester.branch_cycle,
        IEMSemester.sem_min_credits,
        IEMSemester.sem_max_credits
    ).join(
        IEMSAcademicBatch, IEMSAcademicBatch.academic_batch_id == IEMSemester.academic_batch_id
    ).filter(
        IEMSemester.academic_batch_id == academic_batch_id,
        IEMSemester.status == 1,
        IEMSemester.org_id == org_id
    ).all()

    # Convert results to structured response
    semester_data = []
    for semester_value in semester_list:
        semester_data.append({
            'semester_id': semester_value.semester_id,
            'semester_code': semester_value.semester_code,
            'academic_batch_id': semester_value.academic_batch_id,
            'academic_batch_code': semester_value.academic_batch_code,
            'academic_year_planned': semester_value.academic_year_planned,
            'program_year': semester_value.program_year,
            'semester': semester_value.semester,
            'semester_desc': semester_value.semester_desc,
            'semester_flag': semester_value.semester_flag,
            'semester_status': semester_value.semester_status,
            'branch_cycle': semester_value.branch_cycle,
            'sem_min_credits': semester_value.sem_min_credits,
            'sem_max_credits': semester_value.sem_max_credits
        })

    return semester_data


@router.post("/current_sem_check")
def current_sem_check(
        sem_check_data: SemesterCheckRequest,
        current_user: dict = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        return do_current_sem_check(db, sem_check_data.academic_batch_id, org_id)
    except Exception as e:
        raise e


def do_current_sem_check(db: Session, academic_batch_id: int, org_id: int):
    semester_record = db.query(IEMSemester).filter(
        and_(
            IEMSemester.academic_batch_id == academic_batch_id,
            IEMSemester.org_id == org_id,
            IEMSemester.semester_status == "Current",
            IEMSemester.status == 1
        )
    ).first()

    if not semester_record:
        return returnException("Current semester not found")

    return returnSuccess('Semester Found')


@router.post("/fetch_student_section_list")
def fetch_student_section_list(
        request: StudentSectionListRequest,
        db: Session = Depends(get_db),
        org_id: int = Header(...),
):
    try:
        section_data = get_student_section_list(db, request, org_id)
        return returnSuccess(section_data)
    except Exception as e:
        raise e


def get_student_section_list(db: Session, request: StudentSectionListRequest, org_id: int):
    if request.flag == 1:
        query = (
            db.query(distinct(IEMStudents.section))
            .filter(
                IEMStudents.status == 1,
                IEMStudents.result_year == request.result_year,
                IEMStudents.org_id == org_id,
            )
        )
        if request.not_na:
            query = query.filter(IEMStudents.section != "N/A")
        if request.academic_batch_id and request.academic_batch_id != "false":
            query = query.filter(IEMStudents.academic_batch_id == request.academic_batch_id)
        if request.semester != "All":
            query = query.filter(IEMStudents.current_semester == request.semester)
        query = query.order_by(IEMStudents.section.asc())

    # Query for flag != 1
    else:
        query = (
            db.query(distinct(StudentCourse.section))
            .join(
                IEMStudents,
                and_(
                    IEMStudents.regno == StudentCourse.regno,
                    IEMStudents.status == 1,
                ),
            )
            .filter(
                StudentCourse.result_year == request.result_year,
                StudentCourse.is_backlog == request.is_backlog,
                StudentCourse.org_id == org_id,
            )
        )
        if request.not_na:
            query = query.filter(StudentCourse.section != "N/A")
        if request.academic_batch_id and request.academic_batch_id != "false":
            query = query.filter(StudentCourse.batch_id == request.academic_batch_id)
        if request.branch_cycle and request.branch_cycle != "All":
            query = query.filter(StudentCourse.batch_cycle_id == request.branch_cycle)
        if request.semester != "All":
            query = query.filter(StudentCourse.semester == request.semester)
        query = query.order_by(StudentCourse.section.asc())

    # Execute query and return results
    results = query.all()
    section_data = [{"section": row[0]} for row in results]  # Adjusted for single column query
    return section_data


# Fetch student course based on flag
def fetch_student_course(
        request: FetchStudentCourseRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db),
):
    try:
        # Map flags to corresponding processing functions and select types
        flag_to_function = {
            "cia_see": {"func": cia_see_processing, "select_type": 1},
            "grade": {"func": grade_processing, "select_type": 2},
            "attendance": {"func": attendance_processing, "select_type": 3},
            "see": {"func": see_processing, "select_type": 4},
            "cia_evaluate": {"func": cia_evaluate_processing, "select_type": 5},
            "cia": {"func": get_student_course, "select_type": 6},
            "faculty_cia": {"func": faculty_cia_processing, "select_type": 6},
            "withdraw": {"func": withdraw, "select_type": 7},
            "see_evaluate": {"func": see_evaluate_processing, "select_type": 9},
            "see_absentee": {"func": get_absentee, "select_type": 11},
            "grace_attendance": {"func": get_grace_attendance, "select_type": 12},
            "in_eligible": {"func": fetch_in_eligible_list, "select_type": 13},
            "students_usn": {"func": get_student_course, "select_type": 14},
            "eligibility": {"func": fetch_evaluate_list, "select_type": 15, "org_id": org_id},
            "students_usn_withdrawl": {"func": get_student_course, "select_type": 16},
            "students_attendance": {"func": fetch_students_attendance, "select_type": 17},
            "viva": {"func": viva_processing, "select_type": 4},
            "viva_absentee": {"func": get_viva_absentee, "select_type": 11},
            "branch_change_usn": {"func": fetch_branch_change_students, "select_type": 34},
            "branch_change_store": {"func": get_branch_change, "select_type": 35},
            "dvs_see": {"func": see_processing, "select_type": 40},
            "drop": {"func": drop, "select_type": 41},
            "faculty_tw": {"func": faculty_tw_processing, "select_type": None},
            "tw_grade": {"func": tw_grade_processing, "select_type": 43},
            "result_finalize_grade": {"func": result_finalize_grade_processing, "select_type": 44},
        }

        # Get the processing function and select_type based on the flag
        flag_info = flag_to_function.get(request.flag)
        if not flag_info:
            return returnException("Invalid flag")

        # Call the processing function with the provided request and select_type
        processing_func = flag_info["func"]
        select_type = flag_info["select_type"]

        # Adjust call to include org_id where necessary
        if processing_func == grade_processing:
            student_course_data = processing_func(request, select_type, db)  # grade_processing expects only 2 arguments
        else:
            student_course_data = processing_func(request, select_type, org_id, db)

        return student_course_data

    except Exception as e:
        raise e


@router.post("/set_approve")
async def set_approve(
        request: SetApproveRequest,
        current_user: dict = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        # Get the asynchronous DB pool for the stored procedure call
        db_pool = await get_db_pool()

        # Call the approval logic with the required parameters
        await approve_logic(
            db_pool=db_pool,
            approve_type=request.approve_type,
            result_year=request.result_year,
            crs_code=request.crs_code,
            section_name=request.section_name,
            batch_id=request.batch_id,
            program_id=request.program_id,
            sem=request.sem,
            org_id=org_id,
            user_id=current_user.get("user_id"),
        )

        return returnSuccess("Approval process completed successfully")
    except Exception as e:
        raise e


async def approve_logic(
        db_pool,
        approve_type: str,
        result_year: str,
        crs_code: str,
        section_name: Optional[str],
        batch_id: Optional[int],
        program_id: Optional[int],
        sem: Optional[int],
        org_id: int,
        user_id: int
):
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:

            try:
                # Prepare parameters and handle NULLs for optional values
                section_name = None if section_name is None else section_name
                batch_id = None if batch_id is None else batch_id
                program_id = None if program_id is None else program_id
                sem = None if sem is None else sem

                # Build the stored procedure call query
                query = """
                    CALL approve(%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                # Execute the query with parameters
                await cursor.execute(query, (
                    result_year, org_id, crs_code, section_name, approve_type,
                    user_id, sem, batch_id, program_id
                ))

            except Exception as e:
                raise e

            # @router.post("/set_approve")


# def set_approve(
#     request: SetApproveRequest,
#     current_user: dict = Depends(get_current_user),
#     org_id: int = Header(...),
#     db: Session = Depends(get_db),
# ):
#     try:
#         # Call the approval logic function
#         approve_logic(
#             db=db,
#             approve_type=request.approve_type,
#             result_year=request.result_year,
#             crs_code=request.crs_code,
#             section=request.section_name,
#             batch_id=request.batch_id,
#             program_id=request.program_id,
#             sem=request.sem,
#             org_id=org_id,
#             user_id=current_user.get("user_id"),
#         )
#         return returnSuccess("Approval process completed successfully")
#     except Exception as e:
#         db.rollback()
#         raise e

# # Converted approve procedure to approval Logic Function
# def approve_logic(
#     db: Session,
#     approve_type: str,
#     result_year: str,
#     crs_code: str,
#     section: Optional[str],
#     batch_id: Optional[str],
#     program_id: Optional[str],
#     sem: Optional[str],
#     org_id: int,
#     user_id: int,
# ):
#     # Retrieve `belonging_year` from the exam event
#     belonging_year = (
#         db.query(IEMExamEvent.belonging_year)
#         .filter(IEMExamEvent.org_id == org_id, IEMExamEvent.result_year == result_year, IEMExamEvent.status == 1)
#         .scalar()
#     )

#     if not belonging_year:
#         return returnException("Invalid result_year or no corresponding exam event found.")

#     # Common Filters
#     common_filters = [
#         IEMStudents.status == 1,
#         IEMStudents.org_id == org_id,
#         IEMSDepartment.status == 1,
#         IEMSDepartment.org_id == org_id,
#         IEMProgram.status == 1,
#         IEMProgram.org_id == org_id,
#         StudentCourse.result_year == result_year,
#         StudentCourse.crs_code == crs_code,
#         StudentCourse.is_withdrawn == 0,
#         StudentCourse.is_drop == 0,
#         IEMSCourses.status == 1,
#         IEMSCourses.result_year == belonging_year,
#         IEMSCourses.crs_code == crs_code,
#         IEMSCourses.org_id == org_id,
#     ]

#     # Add dynamic filters
#     if section:
#         common_filters.append(func.trim(StudentCourse.section) == func.trim(section))
#     if batch_id:
#         common_filters.append(StudentCourse.batch_id == batch_id)
#     if program_id:
#         common_filters.append(StudentCourse.program_id == program_id)
#     if sem:
#         common_filters.append(StudentCourse.semester == sem)

#     # Handle Approval Types
#     if approve_type == "attendance":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"attendance_approved": 1}, synchronize_session=False
#         )

#     elif approve_type == "attendance_rollback":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"attendance_approved": 0, "is_evaluated": 0}, synchronize_session=False
#         )

#     elif approve_type == "cia":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"cia_approved": 1}, synchronize_session=False
#         )

#     elif approve_type == "cia_rollback":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"cia_approved": 0, "is_evaluated": 0, "total_cia": None}, synchronize_session=False
#         )

#     elif approve_type == "reeval":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters, StudentCourse.is_reeval == 1)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"reeval_approved": 1}, synchronize_session=False
#         )

#     elif approve_type == "ch_reeval":
#         subquery = (
#             db.query(StudentCourse.std_crs_id)
#             .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
#             .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
#             .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
#             .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
#             .filter(*common_filters, StudentCourse.is_challenge_reeval == 1)
#             .subquery()
#         )

#         db.query(StudentCourse).filter(StudentCourse.std_crs_id.in_(subquery)).update(
#             {"challenge_reeval_approved": 1}, synchronize_session=False
#         )

#     else:
#         return returnException("Invalid approve_type")

#     db.commit()


@router.post("/check_grade_evaluate")
def check_grade_evaluate(
        request: CheckGradeEvaluateRequest,
        current_user: dict = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db),
):
    try:
        response = do_check_grade_evaluate(request, org_id, db)
        if not response:
            return returnSuccess([])
        return returnSuccess(response)
    except Exception as e:
        raise e


# Function to Perform Grade Evaluation Check
def do_check_grade_evaluate(request: CheckGradeEvaluateRequest, org_id: int, db: Session):
    query = (
        db.query(
            StudentCourse.std_crs_id.label("std_crs_id"),
            func.min(StudentCourse.is_grade_evaluated).label("is_grade_evaluated"),
            func.min(StudentCourse.is_see_consolidate).label("see_consolidate"),
            func.min(StudentCourse.is_evaluated).label("evaluated"),
            func.max(StudentCourse.is_grade_evaluated).label("grade_evaluated_all_batch"),
        )
        .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)  # Join with IEMStudents table
        .filter(
            StudentCourse.result_year == request.result_year,
            StudentCourse.is_backlog == request.is_backlog,
            func.coalesce(request.program_id, StudentCourse.program_id) == StudentCourse.program_id,
            func.coalesce(request.batch_cycle_id, StudentCourse.batch_cycle_id) == StudentCourse.batch_cycle_id,
            func.coalesce(request.batch_id, StudentCourse.batch_id) == StudentCourse.batch_id,
            StudentCourse.crs_code == request.crs_code,
            func.ifnull(StudentCourse.attendance_eligibility, 0) == 1,
            func.ifnull(StudentCourse.cia_eligibility, 0) == 1,
            StudentCourse.org_id == org_id,
            StudentCourse.is_reeval == 0,
            StudentCourse.is_challenge_reeval == 0,
            func.ifnull(StudentCourse.see_absentee, 0) == 1,
            StudentCourse.is_evaluated == 1,
            IEMStudents.status == 1
        )
        .group_by(StudentCourse.crs_code)
    )

    result = query.all()

    grade_evaluate_data = []
    for grade_evaluate_value in result:
        grade_evaluate_data.append({
            "std_crs_id": grade_evaluate_value.std_crs_id,
            "is_grade_evaluated": grade_evaluate_value.is_grade_evaluated,
            "see_consolidate": grade_evaluate_value.see_consolidate,
            "evaluated": grade_evaluate_value.evaluated,
            "grade_evaluated_all_batch": grade_evaluate_value.grade_evaluated_all_batch,
        })

    return grade_evaluate_data


def calculate_open_elective_cia(
        request: ComputeOpenElectiveCIARequest,
        org_id: int,
        db: Session,
):
    try:
        # Step 1: Get `belonging_year`
        belonging_year = (
            db.query(IEMExamEvent.belonging_year)
            .filter(IEMExamEvent.org_id == org_id, IEMExamEvent.result_year == request.result_year,
                    IEMExamEvent.status == 1)
            .scalar()
        )

        if not belonging_year:
            return {"status": False, "message": "Invalid result_year or no corresponding exam event found."}

        # Step 2: Get `best_of` configuration
        best_of = (
            db.query(IEMOrgConfigs.value)
            .filter(IEMOrgConfigs.config_type == "best_of", IEMOrgConfigs.org_id == org_id)
            .scalar()
        )
        if not best_of or best_of.strip() == "":
            best_of = 0

        # Step 3: Common filters
        common_filters = [
            StudentCourse.result_year == request.result_year,
            StudentCourse.crs_code == request.crs_code,
            StudentCourse.is_withdrawn == 0,
            StudentCourse.is_drop == 0,
            IEMStudents.status == 1,
            IEMStudents.org_id == org_id,
            IEMSDepartment.status == 1,
            IEMSDepartment.org_id == org_id,
            IEMProgram.status == 1,
            IEMProgram.org_id == org_id,
            IEMSCourses.status == 1,
            IEMSCourses.result_year == belonging_year,
            IEMSCourses.org_id == org_id,
        ]

        if request.pgm_id:
            common_filters.append(StudentCourse.program_id == request.pgm_id)
        if request.academic_batch_id:
            common_filters.append(StudentCourse.batch_id == request.academic_batch_id)
        if request.semester:
            common_filters.append(StudentCourse.semester == request.semester)
        if request.section_name:
            common_filters.append(func.trim(StudentCourse.section) == func.trim(request.section_name))

        # Step 4: Subquery for best_of = 1
        subquery_best_of = (
            db.query(
                IEMSCIAStudentCourses.std_crs_id,
                func.sum(IEMSCIAStudentCourses.compute_cia).label("compute_cia"),
            )
            .join(StudentCourse, IEMSCIAStudentCourses.std_crs_id == StudentCourse.std_crs_id)
            .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
            .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
            .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
            .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
            .filter(*common_filters, IEMSCIAStudentCourses.is_bestof == 1)
            .group_by(IEMSCIAStudentCourses.std_crs_id)
            .subquery()
        )

        # Step 5: Subquery for best_of = 0
        subquery_no_best_of = (
            db.query(
                IEMSCIAStudentCourses.std_crs_id,
                func.sum(IEMSCIAStudentCourses.compute_cia).label("compute_cia"),
            )
            .join(StudentCourse, IEMSCIAStudentCourses.std_crs_id == StudentCourse.std_crs_id)
            .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
            .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
            .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
            .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
            .filter(*common_filters, IEMSCIAStudentCourses.is_bestof == 0)
            .group_by(IEMSCIAStudentCourses.std_crs_id)
            .subquery()
        )

        # Step 6: Merge both subqueries
        total_cia_data = (
            db.query(
                subquery_best_of.c.std_crs_id,
                (func.coalesce(subquery_best_of.c.compute_cia, 0) + func.coalesce(subquery_no_best_of.c.compute_cia,
                                                                                  0)).label("total_cia"),
            )
            .outerjoin(
                subquery_no_best_of,
                subquery_best_of.c.std_crs_id == subquery_no_best_of.c.std_crs_id,
            )
            .all()
        )

        # Step 7: Update StudentCourse table
        for std_crs_id, total_cia in total_cia_data:
            db.query(StudentCourse).filter(StudentCourse.std_crs_id == std_crs_id).update(
                {"total_cia": total_cia, "updated_at": datetime.now()}, synchronize_session=False
            )

        db.commit()
        return {"status": True, "message": "CIA calculation completed successfully."}

    except Exception as e:
        db.rollback()
        return {"status": False, "message": f"Error: {str(e)}"}


# Define FastAPI Endpoint
def fetch_course(params: StudentCourseRequestParams, db: Session, org_id: int):
    try:
        # Retrieve belonging year
        belonging_year = (
            db.query(IEMExamEvent.belonging_year)
            .filter(
                IEMExamEvent.org_id == org_id,
                IEMExamEvent.result_year == params.result_year,
                IEMExamEvent.status == 1,
            )
            .scalar()
        )

        if not belonging_year:
            return {"status": False, "message": "Invalid result_year or no matching exam event found."}

        # Handle select_type conditions
        if params.select_type == 1:
            result = (
                db.query(
                    StudentCourse.std_crs_id,
                    IEMStudents.usno,
                    IEMStudents.first_name,
                    IEMStudents.name,
                    StudentCourse.crs_code,
                    StudentCourse.see,
                    StudentCourse.total_cia,
                    StudentCourse.cia_see,
                )
                .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
                .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
                .filter(
                    IEMStudents.status == 1,
                    IEMSCourses.result_year == belonging_year,
                    IEMSCourses.org_id == org_id,
                )
                .order_by(IEMSCourses.crs_order)
                .all()
            )
        elif params.select_type == 2:
            result = (
                db.query(
                    StudentCourse.std_crs_id,
                    IEMSCourses.crs_code,
                    func.sum(StudentCourse.total_cia).label("total_cia"),
                )
                .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
                .filter(
                    IEMSCourses.status == 1,
                    IEMSCourses.result_year == belonging_year,
                    IEMSCourses.org_id == org_id,
                    StudentCourse.program_id == params.program_id,
                )
                .group_by(IEMSCourses.crs_code)
                .all()
            )
        elif params.select_type == 3:
            result = (
                db.query(
                    StudentCourse.std_crs_id,
                    IEMSCourses.crs_code,
                    StudentCourse.attendance,
                    StudentCourse.attendance_percentage,
                )
                .join(IEMSCourses, IEMSCourses.crs_code == StudentCourse.crs_code)
                .filter(
                    StudentCourse.result_year == params.result_year,
                    IEMSCourses.result_year == belonging_year,
                    IEMSCourses.org_id == org_id,
                )
                .all()
            )
        else:
            return {"status": False, "message": "Invalid select_type provided."}

        return {"status": True, "data": result}

    except Exception as e:
        return {"status": False, "message": str(e)}


@router.post("/get_batch_options")
def get_batch_options(
        request: GetAcademicBatchRequest,
        db: Session = Depends(get_db),
        org_id: int = Header(...),
):
    try:
        # Fetch academic batch options from DB
        batches = fetch_academic_batch_list(
            db=db,
            show_delete=request.show_delete,
            program_id=request.program_id,
            org_id=org_id
        )

        # Create options list
        options = [{"value": batch.academic_batch_id, "label": batch.academic_batch_code} for batch in batches]

        return returnSuccess(options)

    except Exception as e:
        return returnException(str(e))


def fetch_academic_batch_list(db: Session, show_delete: Optional[int], program_id: Optional[int], org_id: int):
    query = db.query(
        IEMSAcademicBatch.academic_batch_id,
        IEMSAcademicBatch.academic_batch_code,
        IEMSAcademicBatch.academic_batch_desc,
        IEMSAcademicBatch.academic_year,
        IEMSAcademicBatch.status,
        IEMSAcademicBatch.grade_type,
        IEMSAcademicBatch.is_tw_course,
        IEMSAcademicBatch.regulation_year,
        IEMSAcademicBatch.program_duration,
        IEMProgram.pgm_id,
        IEMProgram.pgm_title,
        IEMProgram.pgm_acronym,
        IEMSDepartment.dept_id,
        IEMSDepartment.dept_name,
        IEMProgram.pgm_specialization
    ).join(
        IEMProgram, IEMSAcademicBatch.pgm_id == IEMProgram.pgm_id
    ).join(
        IEMSDepartment, IEMSAcademicBatch.dept_id == IEMSDepartment.dept_id
    ).filter(
        IEMSAcademicBatch.org_id == org_id
    )

    if show_delete != 1:
        query = query.filter(IEMSAcademicBatch.status == 1)

    if program_id:
        query = query.filter(IEMProgram.pgm_id == program_id)

    return query.all()


def get_college_details(org_id: int, db: Session):
    college = db.query(IEMOrganisation).filter(IEMOrganisation.org_id == org_id).first()
    if college is None:
        return returnException("College not found")

    return {
        "org_name": college.org_name,
        "org_desc": college.org_desc,
        "profile_image": college.profile_image,
        "other_profile_image": college.other_profile_image,
    }


@router.post("/get_program_options")
def get_program_options(
        request: GetProgramOptionsRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        programs = db.query(IEMProgram).join(IEMSDepartment, IEMProgram.dept_id == IEMSDepartment.dept_id).join(
            IEMProgramType, IEMProgram.pgmtype_id == IEMProgramType.pgmtype_id
        ).filter(IEMProgram.org_id == org_id)

        if request.show_delete != 1:
            programs = programs.filter(IEMProgram.status == 1)

        if request.is_encoded:
            programs = programs.filter(IEMProgram.dept_id.in_(request.dept_id))
        elif request.dept_id:
            programs = programs.filter(IEMProgram.dept_id == request.dept_id)

        if request.program_type:
            programs = programs.filter(IEMProgram.pgmtype_id == request.program_type)

        programs = programs.all()
        options = [{"pgm_id": program.pgm_id, "pgm_acronym": program.pgm_acronym} for program in programs]
        return returnSuccess(options)
    except Exception as e:
        raise e


@router.post("/get_semester_list_options")
def get_semester_list_options(
        request: GetSemesterListRequest,
        current_user: dict = Depends(get_current_user),  # Ensure current_user is a dict
        org_id: int = Header(...),  # Org ID passed via header
        db: Session = Depends(get_db)  # Database session via dependency
):
    try:
        result_array = []

        # Check if the user has department-wise permissions
        department_permission = get_department_permission(current_user['user_id'], current_user, db)

        # Handle 'makeup_semester' flag
        if request.flag == 'makeup_semester':
            # Fetch exam event status for the given result year and org_id
            exam_event = db.query(IEMExamEvent).filter(
                IEMExamEvent.result_year == request.result_year,
                IEMExamEvent.org_id == org_id
            ).first()

            if exam_event and exam_event.event_status == 1:
                # Query semester details for the makeup semester case
                result_array = db.query(
                    func.distinct(IEMSemester.semester),
                    IEMSemester.semester_id,
                    IEMSemester.semester_desc,
                    IEMSemester.branch_cycle,
                    IEMSemester.academic_year_planned,
                    # Subquery for batch_cycle_id
                    db.query(IEMSBatchCycle.batch_cycle_id)
                    .filter(IEMSBatchCycle.status == 1)
                    .filter(IEMSBatchCycle.batch_cycle_code == IEMSemester.branch_cycle)
                    .label('batch_cycle_id')
                ).select_from(IEMSemester).join(
                    IEMSemester,  # Make sure the join happens on the correct columns
                    IEMSemester.semester == IEMSemester.semester
                ).join(
                    IEMSemester,  # Another join on the correct column
                    IEMSemester.academic_batch_id == request.academic_batch_id
                ).filter(
                    IEMSemester.batch_id == request.academic_batch_id,
                    IEMSemester.result_year == request.result_year
                ).group_by(IEMSemester.semester).all()

        else:
            # Handle standard semester query
            semester_query = db.query(
                func.distinct(IEMSemester.semester),
                IEMSemester.semester,
                IEMSemester.semester_desc,
                IEMSemester.branch_cycle,
                IEMSemester.academic_year_planned,
                # Subquery for batch_cycle_id
                db.query(IEMSBatchCycle.batch_cycle_id)
                .filter(IEMSBatchCycle.status == 1)
                .filter(IEMSBatchCycle.batch_cycle_code == IEMSemester.branch_cycle)
                .label('batch_cycle_id')
            ).select_from(IEMSemester)  # Explicitly set the base table to IEMSemester

            # Apply permissions check if necessary
            if department_permission:
                semester_query = semester_query.join(
                    IEMSUserCourseMgmt,
                    IEMSUserCourseMgmt.semester == IEMSemester.semester
                ).filter(
                    IEMSUserCourseMgmt.academic_batch_id == request.academic_batch_id,
                    IEMSUserCourseMgmt.user_id == current_user['user_id']
                )

            if not request.is_course:
                semester_query = semester_query.filter(IEMSemester.semester_status.in_(['Current', 'Completed']))
            elif request.is_course == 2:
                semester_query = semester_query.filter(IEMSemester.semester_status == 'Completed')
            else:
                semester_query = semester_query.filter(IEMSemester.semester_status == 'Current')

            # Additional filters
            if request.academic_batch_id:
                semester_query = semester_query.filter(IEMSemester.academic_batch_id == request.academic_batch_id)

            # Filter by organization and status
            semester_query = semester_query.filter(IEMSemester.org_id == org_id, IEMSemester.status == 1)

            # Filter for first year if needed
            if request.is_first_year:
                semester_query = semester_query.filter(IEMSemester.program_year == 1)

            # Fetch results
            result_array = semester_query.all()

        # Return the result
        data = [dict(query_data._mapping) for query_data in result_array]
        return returnSuccess(data)

    except Exception as e:
        raise e


def get_template_details(param: Dict, db: Session, org_id: int):
    # Extract parameters
    department_id = param.get("department_id")
    program = param.get("program")
    template_type = param.get("template_type")
    org_id = org_id

    # Query to fetch template details using SQLAlchemy ORM
    template_details_query = db.query(IEMSTemplate.template_name).filter(
        IEMSTemplate.dept_id == department_id,
        IEMSTemplate.program_id == program,
        IEMSTemplate.org_id == org_id,
        IEMSTemplate.template_type == template_type
    ).first()

    # Check if a matching template was found for the department and program
    if template_details_query:
        # Template found for the specific department and program
        template_details = template_details_query[0]
    else:
        # Fallback query for the case where no matching department/program is found
        template_details_query = db.query(IEMSTemplate.template_name).filter(
            IEMSTemplate.dept_id == None,
            IEMSTemplate.program_id == None,
            IEMSTemplate.org_id == org_id,
            IEMSTemplate.template_type == template_type
        ).first()

        if template_details_query:
            template_details = template_details_query[0]
        else:
            return returnException("Template not found")

    # Split the template details by "/" and handle the template file name
    template_array = template_details.split("/")
    template_name = template_details if len(template_array) == 1 else template_array[-1]

    return template_name


@router.post("/forgot_password")
async def forgot_password(
        request: ForgotPasswordRequest,
        db: Session = Depends(get_db),
):
    try:
        # Check if the email exists in the database
        user = db.query(IEMSUsers).filter(IEMSUsers.email == request.email).first()

        if not user:
            return returnException("User with this email does not exist")

        # need to add email functioanlity loading email
        return returnSuccess("Password reset email has been sent")
    except Exception as e:
        raise e


@router.post("/change_password")
async def change_password(
        request: ChangePasswordRequest,
        current_user: str = Depends(get_current_user),
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    if request.newpassword != request.confirmpassword:
        return returnException("User with this email does not exist")
    try:
        username = current_user.get('username')
        # Fetch user data from DB
        user = db.query(IEMSUsers).filter(IEMSUsers.username == username, IEMSUsers.org_id == org_id).first()

        if not user:
            return returnException("User not found.")
        # Validate old password
        if not validate_old_password(request.oldpassword, user):
            return returnException("Old password is incorrect.")

        # Generate new password hash and salt
        updated_data = set_private_password(request.confirmpassword)

        # Update password and salt
        user.password = updated_data['password']
        user.salt = updated_data['salt']

        db.commit()

        return returnSuccess("Password changed successfully.")

    except Exception as e:
        db.rollback()
        raise e


@router.post("/check_eligibility")
def check_eligibility_validation(
        request: CheckEligibilityRequest,
        org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        # Query the database for eligibility data based on the parameters
        eligibility_data = db.query(
            StudentCourse.std_crs_id,
            func.sum(StudentCourse.is_evaluated > 0).label('is_evaluated'),
            func.sum(StudentCourse.is_see_consolidate > 0).label('is_see_consolidate'),
            func.sum(StudentCourse.is_grade_evaluated > 0).label('is_grade_evaluated')
        ).filter(
            StudentCourse.result_year == request.result_year,
            StudentCourse.crs_code == request.crs_code,
            StudentCourse.org_id == org_id,
            StudentCourse.is_backlog == request.is_backlog,
            StudentCourse.is_reeval == 0,
            StudentCourse.is_challenge_reeval == 0
        ).group_by(StudentCourse.crs_code).first()

        # Prepare the response data
        if eligibility_data:
            data = {
                "std_crs_id": eligibility_data.std_crs_id,
                "is_evaluated": eligibility_data.is_evaluated,
                "is_see_consolidate": eligibility_data.is_see_consolidate,
                "is_grade_evaluated": eligibility_data.is_grade_evaluated,
            }
        else:
            data = {}

        return data

    except Exception as e:
        raise e


@router.post("/check_reval_dates")
def check_reval_dates(request: CheckRevalDatesRequest, current_user: str = Depends(get_current_user),
                      org_id: int = Header(...), db: Session = Depends(get_db)):
    try:
        # Call the function to check reval dates based on result_year and eval_type
        result = check_reval_dates_validation(request.result_year, request.eval_type, org_id, db)
        return returnSuccess({"result": result})
    except Exception as e:
        raise e


def check_reval_dates_validation(result_year: int, eval_type: int, org_id: int, db: Session):
    if eval_type == 0:
        # Check for reeval dates
        exam_event = db.query(IEMExamEvent).filter(
            IEMExamEvent.result_year == result_year,
            IEMExamEvent.org_id == org_id,
            IEMExamEvent.reeval_start_date <= func.current_date(),
            IEMExamEvent.reeval_end_date >= func.current_date()
        ).first()
        return 1 if exam_event else 0
    else:
        # Check for challenge reevaluation dates
        exam_event = db.query(IEMExamEvent).filter(
            IEMExamEvent.result_year == result_year,
            IEMExamEvent.org_id == org_id,
            IEMExamEvent.challenge_reeval_start_date <= func.current_date(),
            IEMExamEvent.challenge_reeval_end_date >= func.current_date()
        ).first()
        return 1 if exam_event else 0


@router.get("/is_backlog_with_cia_see")
def is_backlog_with_cia_see(
        current_user: str = Depends(get_current_user), org_id: int = Header(...),
        db: Session = Depends(get_db)
):
    try:
        data = is_backlog_with_cia_see_db(db, current_user, org_id)
        return returnSuccess(data)
    except Exception as e:
        raise e


def is_backlog_with_cia_see_db(db: Session, current_user: str, org_id: int):
    query = db.query(IEMOrgConfigs.value).filter(
        IEMOrgConfigs.config_type == 'backlog_with_cia_see'
    )
    rowcount = query.count()
    return rowcount