from typing import Any, Dict
from sqlalchemy import and_, asc, func, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Any
from .comman_function_schema import FetchStudentCourseRequest
from .....db.models import IEMExamEvent, IEMProgram, IEMSBacklogCourseMap, IEMSCIAStudentCourses, IEMSCourseType, IEMSCourses, IEMSDepartment, IEMStudents, StudentCourse
from .....utils.http_return_helper import returnException
from sqlalchemy.orm import aliased


#------------start attendance_processing ---------#
def attendance_processing(request: FetchStudentCourseRequest, select_type: int, org_id: int, db: Session):
    # Fetch student attendance data from the database
    student_attendance = get_student_attendance(request, org_id, db)
    student_attendance_data = []

    # Process each student's attendance record
    for attendance in student_attendance:
        attendance_percentage_value = (
            "" if attendance["attendance_percentage"] is None else round(attendance["attendance_percentage"], 2)
        )
        attendance_value = "" if attendance["attendance"] is None else attendance["attendance"]
        student_attendance_data.append({
            "id": attendance["std_crs_id"],
            "usno": attendance["usno"],
            "student_name": attendance["name"].strip(),
            "is_attendance_evaluated": attendance["attendance_approved"],
            "attendance": attendance_value,
            "attendance_percentage": attendance_percentage_value,
            "total_classes": attendance["total_classes"],
        })

    return student_attendance_data


def get_student_attendance(request: FetchStudentCourseRequest, org_id: int, db: Session):
    try:
        # Get the belonging year for the result year
        belonging_year_query = (
            db.query(IEMExamEvent.belonging_year)
            .filter(
                IEMExamEvent.result_year == request.result_year,
                IEMExamEvent.org_id == org_id,
                IEMExamEvent.status == 1,
            )
            .first()
        )
        result_year_belonging = belonging_year_query.belonging_year if belonging_year_query else request.result_year

        # Default cycle to null if not provided
        cycle = request.cycle if request.cycle else None

        # Map section_name to section
        section = request.section_name if request.section_name else None

        # Main query for regular students
        main_query = (
            db.query(
                StudentCourse.std_crs_id.label("std_crs_id"),
                IEMStudents.student_id.label("student_id"),
                func.coalesce(IEMStudents.usno, IEMStudents.roll_number).label("usno"),
                IEMStudents.name.label("name"),
                StudentCourse.attendance.label("attendance"),
                StudentCourse.attendance_approved.label("attendance_approved"),
                StudentCourse.attendance_percentage.label("attendance_percentage"),
                IEMSCourses.total_classes.label("total_classes"),
            )
            .join(
                IEMStudents,
                IEMStudents.regno == StudentCourse.regno,
            )
            .join(
                IEMSCourses,
                and_(
                    IEMSCourses.crs_code == StudentCourse.crs_code,
                    IEMSCourses.result_year == result_year_belonging,
                    IEMSCourses.status == 1,
                    IEMSCourses.org_id == org_id,
                    IEMSCourses.program_id == StudentCourse.program_id,
                    StudentCourse.batch_id == IEMSCourses.academic_batch_id,
                ),
            )
            .filter(
                StudentCourse.result_year == request.result_year,
                IEMStudents.status == 1,
                StudentCourse.batch_id == (request.batch_id or StudentCourse.batch_id),
                StudentCourse.semester == (request.semester or StudentCourse.semester),
                StudentCourse.crs_code == request.crs_code,
                StudentCourse.is_withdrawn == 0,
                StudentCourse.is_drop == 0,
                func.trim(StudentCourse.section) == func.trim(section) if section else True,
                StudentCourse.batch_cycle_id == (cycle or StudentCourse.batch_cycle_id),
                or_(StudentCourse.sup_type.is_(None), StudentCourse.sup_type == 1),
            )
        )

        # Query for backlog students
        backlog_query = (
            db.query(
                StudentCourse.std_crs_id.label("std_crs_id"),
                IEMStudents.student_id.label("student_id"),
                func.coalesce(IEMStudents.usno, IEMStudents.roll_number).label("usno"),
                IEMStudents.name.label("name"),
                StudentCourse.attendance.label("attendance"),
                StudentCourse.attendance_approved.label("attendance_approved"),
                StudentCourse.attendance_percentage.label("attendance_percentage"),
                IEMSCourses.total_classes.label("total_classes"),
            )
            .join(
                IEMStudents,
                IEMStudents.regno == StudentCourse.regno,
            )
            .join(
                IEMSCourses,
                and_(
                    IEMSCourses.crs_code == request.crs_code,
                    IEMSCourses.result_year == result_year_belonging,
                    IEMSCourses.program_id == StudentCourse.program_id,
                    IEMSCourses.status == 1,
                    IEMSCourses.org_id == org_id,
                ),
            )
            .filter(
                StudentCourse.result_year == request.result_year,
                StudentCourse.batch_id == None,
                StudentCourse.crs_code.in_(
                    db.query(IEMSBacklogCourseMap.map_crs_code)
                    .filter(
                        IEMSBacklogCourseMap.crs_code == request.crs_code,
                        or_(
                            IEMSBacklogCourseMap.batch_cycle_id.is_(None),
                            IEMSBacklogCourseMap.batch_cycle_id == StudentCourse.batch_cycle_id,
                        ),
                        IEMSBacklogCourseMap.org_id == org_id,
                        IEMSBacklogCourseMap.result_year == request.result_year,
                    )
                ),
                StudentCourse.is_withdrawn == 0,
                StudentCourse.is_drop == 0,
                func.trim(StudentCourse.section) == func.trim(section) if section else True,
                StudentCourse.batch_cycle_id == (cycle or StudentCourse.batch_cycle_id),
                StudentCourse.is_backlog == 1,
                or_(
                    StudentCourse.batch_cycle_id != 3,
                    StudentCourse.semester == (request.semester or StudentCourse.semester),
                ),
                or_(StudentCourse.sup_type.is_(None), StudentCourse.sup_type == 1),
            )
            .group_by(StudentCourse.regno)
        )

        # Combine main query and backlog query using union
        combined_query = main_query.union_all(backlog_query).order_by("usno")
        # Execute query and fetch results
        result = [dict(course._mapping) for course in combined_query]
        # result = db.execute(combined_query).mappings().all()
        return result

    except Exception as e:
        raise e
#------------end attendance_processing ---------#


#------------start get_student_course ---------#
def get_student_course(param_list: FetchStudentCourseRequest, select_type: int, org_id: int, db: Session):
    org_id = org_id
    result_year = param_list.result_year
    program_id = param_list.program_id
    crs_code = param_list.crs_code
    section = param_list.section_name
    occasion = param_list.occasion
    cycle = param_list.cycle
    sem = param_list.semester
    is_cycle_wise = param_list.is_cycle_wise or False
    batch_id = param_list.batch_id
    usn = param_list.usn
    sessions = param_list.sessions
    attendance_date = param_list.attendance_date
    v_value = param_list.v_value
    reeval = param_list.reeval
    challengereeval = param_list.challengereeval

    if param_list.is_cycle_wise:
        # Cycle-wise query with ORM
        # Subquery for belonging year
        belonging_year_subquery = (
            db.query(IEMExamEvent.belonging_year)
            .filter(
                IEMExamEvent.org_id == org_id,
                IEMExamEvent.result_year == result_year,
                IEMExamEvent.status == 1,
            )
            .limit(1)
            .scalar_subquery()
        )

        # Aliases for tables
        ies = aliased(IEMStudents)
        id_ = aliased(IEMSDepartment)
        ip = aliased(IEMProgram)
        isc = aliased(StudentCourse)
        ic = aliased(IEMSCourses)
        icsc = aliased(IEMSCIAStudentCourses)
        backlog_map = aliased(IEMSBacklogCourseMap)

        # First part of the query
        query1 = (
            db.query(
                isc.std_crs_id,
                func.if_(
                    or_(ies.usno == None, ies.usno == ""),
                    ies.roll_number,
                    ies.usno,
                ).label("usno"),
                ies.regno,
                ies.name,
                icsc.secured_marks,
                icsc.is_absentee,
                isc.cia_approved,
                isc.total_cia,
                isc.see1,
            )
            .join(id_, and_(id_.dept_id == ies.department_id, id_.status == 1, id_.org_id == org_id))
            .join(ip, and_(ip.pgm_id == ies.program_id, ip.dept_id == id_.dept_id, ip.status == 1, ip.org_id == org_id))
            .join(
                isc,
                and_(
                    ies.regno == isc.regno,
                    ip.pgm_id == isc.program_id,
                    isc.result_year == result_year,
                    isc.crs_code == crs_code,
                    or_(isc.section == func.coalesce(func.trim(section), func.trim(isc.section))),
                    isc.is_withdrawn == 0,
                    isc.is_drop == 0,
                    isc.semester == func.coalesce(sem, isc.semester),
                    isc.batch_cycle_id == cycle,
                ),
            )
            .join(
                ic,
                and_(
                    ic.crs_code == isc.crs_code,
                    ic.status == 1,
                    ic.result_year == belonging_year_subquery,
                    ic.org_id == org_id,
                    ic.program_id == ip.pgm_id,
                    ic.department_id == id_.dept_id,
                    isc.batch_id == ic.academic_batch_id,
                ),
            )
            .outerjoin(icsc, and_(icsc.std_crs_id == isc.std_crs_id, icsc.occasion_id == occasion))
        )

        # Second part of the query for backlog
        query2 = (
            db.query(
                isc.std_crs_id,
                func.if_(
                    or_(ies.usno == None, ies.usno == ""),
                    ies.roll_number,
                    ies.usno,
                ).label("usno"),
                ies.regno,
                ies.name,
                icsc.secured_marks,
                icsc.is_absentee,
                isc.cia_approved,
                isc.total_cia,
                isc.see1,
            )
            .join(ies, and_(ies.regno == isc.regno, ies.program_id == isc.program_id))
            .filter(
                isc.result_year == result_year,
                isc.batch_cycle_id == cycle,
                isc.crs_code.in_(
                    db.query(backlog_map.map_crs_code)
                    .filter(
                        backlog_map.crs_code == crs_code,
                        backlog_map.batch_cycle_id == isc.batch_cycle_id,
                        backlog_map.org_id == org_id,
                        backlog_map.result_year == result_year,
                    )
                    .subquery()
                ),
                or_(isc.section == func.coalesce(func.trim(section), func.trim(isc.section))),
                isc.is_withdrawn == 0,
                isc.is_drop == 0,
                or_(
                    and_(isc.batch_cycle_id == 3, isc.semester == func.coalesce(sem, isc.semester)),
                    isc.semester == isc.semester,
                ),
                ies.status == 1,
            )
            .join(
                ic,
                and_(
                    ic.crs_code == crs_code,
                    ic.status == 1,
                    ic.result_year == result_year,
                    ic.org_id == org_id,
                    ic.program_id == isc.program_id,
                    isc.is_backlog == 1,
                ),
            )
            .outerjoin(icsc, and_(icsc.std_crs_id == isc.std_crs_id, icsc.occasion_id == occasion))
            .group_by(isc.regno)
        )

        # Combine both queries with UNION ALL
        results = query1.union_all(query2).order_by("usno")
        student_usn_data = [dict(course._mapping) for course in results]
    else:
        student_usn_data=fetch_student_course_procedure_data(param_list,db,select_type,org_id)
        
    return student_usn_data

def fetch_student_course_procedure_data(param_list: FetchStudentCourseRequest, db: Session, select_type: int, org_id: int):
    try:
        result_year = param_list.result_year if hasattr(param_list, 'result_year') else None
        crs_code = param_list.crs_code if hasattr(param_list, 'crs_code') else None
        occasion = param_list.occasion if hasattr(param_list, 'occasion') else None
        section_name = param_list.section_name if hasattr(param_list, 'section_name') else None
        v_value = param_list.v_value if hasattr(param_list, 'v_value') else None
        absentee = param_list.absentee if hasattr(param_list, 'absentee') else None
        program_id = param_list.program_id if hasattr(param_list, 'program_id') else None
        batch_id = param_list.batch_id if hasattr(param_list, 'batch_id') else None
        semester = param_list.semester if hasattr(param_list, 'semester') else None
        usn = param_list.usn if hasattr(param_list, 'usn') else None
        sessions = param_list.sessions if hasattr(param_list, 'sessions') else None
        attendance_date = param_list.attendance_date if hasattr(param_list, 'attendance_date') else None
        flag = param_list.flag if hasattr(param_list, 'flag') else None
        is_backlog = param_list.is_backlog if hasattr(param_list, 'is_backlog') else None
        is_cycle_wise = param_list.is_cycle_wise if hasattr(param_list, 'is_cycle_wise') else None
        reeval = param_list.reeval if hasattr(param_list, 'reeval') else None
        lab_course_batch_id = param_list.lab_course_batch_id if hasattr(param_list, 'lab_course_batch_id') else None
        cycle = param_list.cycle if hasattr(param_list, 'cycle') else None
        is_extra_class = param_list.is_extra_class if hasattr(param_list, 'is_extra_class') else None
        challengereeval = param_list.challengereeval if hasattr(param_list, 'challengereeval') else None

        # Fetch the corresponding result_year_value
        result_year_value = db.query(IEMExamEvent.belonging_year).filter(
            IEMExamEvent.org_id == org_id,
            IEMExamEvent.result_year == result_year,
            IEMExamEvent.status == 1
        ).scalar()

        if select_type == 14:
            subquery = (
            db.query(
                func.coalesce(IEMStudents.usno, IEMStudents.roll_number).label('usno')  # If 'usno' is NULL, use 'roll_number'
            )
            .join(IEMSDepartment, IEMSDepartment.dept_id == IEMStudents.department_id)
            .join(IEMProgram, IEMProgram.pgm_id == IEMStudents.program_id)
            .filter(
                IEMSDepartment.status == 1,  
                IEMSDepartment.org_id == org_id,  
                IEMStudents.status == 1,  
                IEMStudents.org_id == org_id,  
                IEMStudents.current_semester == semester,  
                IEMProgram.status == 1,  
                IEMProgram.org_id == org_id,  
                IEMStudents.program_id == program_id, 
                IEMStudents.academic_batch_id == batch_id,  
                IEMStudents.result_year == result_year 
                )
            .subquery() 
            )
            query = (
            db.query(subquery.c.usno)  
            .group_by(subquery.c.usno)  
            .order_by(asc(subquery.c.usno)) 
            )
            data = query.all()
            return [{"usno": row.usno} for row in data]

        else:
            return returnException("Unsupported select_type")
    except Exception as e:
        raise e
    
#------------end get_student_course ---------#
    
#---------------------#
def fetch_evaluate_list(
    request: FetchStudentCourseRequest, select_type: int, org_id: int, db: Session
):
    try:
        if request.is_backlog == 1:
            evaluate_list = get_eligibility_backlog(request,org_id,db)
        else:
            evaluate_list = get_student_eligibility(request,org_id,db)

        evaluate_list_data = []
        for item in evaluate_list:
            evaluate_cia = "Yes" if item.cia_evaluated == 1 else "No"
            evaluate_attendance = "Yes" if item.attendance_evaluated == 1 else "No"
            show_evaluate = 1 if evaluate_cia == "Yes" and evaluate_attendance == "Yes" else 0
            evaluate_list_data.append({
                "crs_code": item.crs_code,
                "is_cia_evaluated": evaluate_cia,
                "is_attendance_evaluated": evaluate_attendance,
                "is_evaluated": item.is_evaluated,
                "show_evaluate": show_evaluate,
            })
        return evaluate_list_data
    except Exception as e:
        raise e
    
def get_eligibility_backlog(request: FetchStudentCourseRequest,org_id:int, db: Session):
    # Fetch belonging year
    belonging_year_query = (
        db.query(IEMExamEvent.belonging_year)
        .filter(IEMExamEvent.result_year == request.result_year)
        .first()
    )
    result_year_belonging = belonging_year_query.belonging_year if belonging_year_query else request.result_year

    # Main query
    result = (
        db.query(
            IEMSCourses.crs_code,
            func.min(StudentCourse.attendance_approved).label("attendance_evaluated"),
            func.min(StudentCourse.cia_approved).label("cia_evaluated"),
            StudentCourse.is_evaluated,
        )
        .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
        .join(
            IEMSDepartment,
            and_(
                IEMSDepartment.dept_id == IEMStudents.department_id,
                IEMSDepartment.status == 1,
                IEMSDepartment.org_id == org_id,
            ),
        )
        .join(
            IEMProgram,
            and_(
                IEMProgram.pgm_id == IEMStudents.program_id,
                IEMProgram.dept_id == IEMSDepartment.dept_id,
                IEMProgram.status == 1,
                IEMProgram.org_id == org_id,
                IEMStudents.program_id == request.program_id,
            ),
        )
        .join(
            IEMSCourses,
            and_(
                IEMSCourses.crs_code == StudentCourse.crs_code,
                IEMSCourses.status == 1,
                IEMSCourses.org_id == org_id,
                IEMSCourses.program_id == request.program_id,
                IEMSCourses.result_year == result_year_belonging,
                IEMSCourses.program_id == IEMProgram.pgm_id,
                IEMSCourses.department_id == IEMSDepartment.dept_id,
                StudentCourse.batch_id == IEMSCourses.academic_batch_id,
            ),
        )
        .filter(
            StudentCourse.result_year == request.result_year,
            StudentCourse.program_id == request.program_id,
            StudentCourse.is_withdrawn == 0,
            StudentCourse.is_drop == 0,
            StudentCourse.batch_id == request.batch_id,
            StudentCourse.is_backlog == 1,
        )
        .group_by(IEMSCourses.crs_code)
        .all()
    )

    return result

def get_student_eligibility(request: FetchStudentCourseRequest,org_id:int,db: Session):
    # Fetch belonging year for the result year
    belonging_year_query = (
        db.query(IEMExamEvent.belonging_year)
        .filter(
            IEMExamEvent.result_year == request.result_year,
            IEMExamEvent.org_id == org_id,
            IEMExamEvent.status == 1,
        )
        .first()
    )
    result_year_belonging = belonging_year_query.belonging_year if belonging_year_query else request.result_year

    # Query for student eligibility
    result = (
        db.query(
            IEMSCourses.crs_code,
            func.min(StudentCourse.attendance_approved).label("attendance_evaluated"),
            func.min(StudentCourse.cia_approved).label("cia_evaluated"),
            StudentCourse.is_evaluated,
        )
        .join(IEMStudents, IEMStudents.regno == StudentCourse.regno)
        .join(
            IEMSCourses,
            and_(
                IEMSCourses.crs_code == StudentCourse.crs_code,
                IEMSCourses.status == 1,
                IEMSCourses.org_id == org_id,
                IEMSCourses.result_year == result_year_belonging,
                IEMSCourses.program_id == (request.program_id or IEMSCourses.program_id),
                IEMSCourses.program_id == StudentCourse.program_id,
                StudentCourse.batch_id == IEMSCourses.academic_batch_id,
            ),
        )
        .filter(
            StudentCourse.result_year == request.result_year,
            IEMStudents.status == 1,
            StudentCourse.program_id == (request.program_id or StudentCourse.program_id),
            StudentCourse.is_withdrawn == 0,
            StudentCourse.semester == (request.semester or StudentCourse.semester),
            StudentCourse.batch_id == (request.batch_id or StudentCourse.batch_id),
            IEMStudents.batch_cycle_id == (request.cycle or IEMStudents.batch_cycle_id),
            ~IEMSCourses.course_type_id.in_(
                db.query(IEMSCourseType.course_type_id).filter(IEMSCourseType.course_type_code == "NO_RESULT_GRADE")
            ),
        )
        .group_by(IEMSCourses.crs_code)
        .all()
    )

    return result

#---------------------#

def cia_see_processing(params,select_type,db: Session):
    pass



# Grade processing function
def grade_processing(param_list: FetchStudentCourseRequest, select_type: int, db: Session):
    is_backlog = param_list.is_backlog  # Corrected line
    
    if is_backlog == 1:
        student_course = get_grade_backlog(param_list.dict(), db)
    else:
        student_course = get_student_course_data(param_list.dict(), db)
    
    student_course_data = []
    for student_course_value in student_course:
        student_course_data.append({
            "id": student_course_value.std_crs_id,
            "usno": student_course_value.usno,
            "student_name": student_course_value.name,
            "code": student_course_value.crs_code,
            "cia": student_course_value.total_cia,
            "see": student_course_value.see,
            "cia_see": student_course_value.cia_see,
            "max_marks": student_course_value.max_marks,
            "credits": student_course_value.credit_hours,
            "credits_earned": student_course_value.credits_earned,
            "grade": student_course_value.grade,
            "grade_point": student_course_value.grade_point,
            "viva": student_course_value.viva_marks if student_course_value.viva_marks else "",
            "ise_marks": student_course_value.ise_marks if student_course_value.ise_marks else "",
            "tw_marks": student_course_value.tw_marks if student_course_value.tw_marks else "",
        })
    return student_course_data


# Get student course function
def get_student_course_data(params: dict, db: Session):
    regno = params["regno"]
    org_id = params["org_id"]
    result_year = params["result_year"]

    belonging_year = db.query(IEMExamEvent.belonging_year).filter(IEMExamEvent.result_year == result_year).scalar()
    if belonging_year is None:
        belonging_year = ""

    student_courses = db.query(
        StudentCourse.std_crs_id,
        StudentCourse.crs_code,
        StudentCourse.total_cia,
        StudentCourse.see,
        StudentCourse.cia_see,
        IEMSCourses.see_max_marks + IEMSCourses.cia_max_marks,
        IEMSCourses.credit_hours,
        StudentCourse.credits_earned,
        StudentCourse.grade,
        StudentCourse.grade_point,
    ).join(
        IEMSCourses, and_(
            StudentCourse.crs_code == IEMSCourses.crs_code,
            IEMSCourses.org_id == org_id,
            IEMSCourses.result_year == belonging_year,
            IEMSCourses.status == 1,
        )
    ).filter(
        StudentCourse.regno == regno,
        StudentCourse.result_year == result_year,
        StudentCourse.org_id == org_id,
        StudentCourse.is_withdrawn == 0,
        StudentCourse.is_drop == 0,
    ).order_by(IEMSCourses.crs_order).all()

    return [
        {
            "std_crs_id": sc.std_crs_id,
            "crs_code": sc.crs_code,
            "cia": sc.total_cia,
            "see": sc.see,
            "cia_see": sc.cia_see,
            "max_marks": sc[5],
            "credits": sc.credit_hours,
            "credits_earned": sc.credits_earned,
            "grade": sc.grade,
            "grade_point": sc.grade_point,
        }
        for sc in student_courses
    ]


# Get grade backlog function
def get_grade_backlog(params: dict, db: Session):
    result_year = params["result_year"]
    program_id = params["program_id"]
    batch_id = params["batch_id"]
    org_id = params["org_id"]

    belonging_year = db.query(IEMExamEvent.belonging_year).filter(IEMExamEvent.result_year == result_year).scalar()
    if belonging_year is None:
        belonging_year = ""

    student_courses = db.query(
        StudentCourse.std_crs_id,
        IEMStudents.usno,
        IEMStudents.name,
        StudentCourse.crs_code,
        StudentCourse.total_cia,
        StudentCourse.see,
        StudentCourse.cia_see,
        IEMSCourses.see_max_marks + IEMSCourses.cia_max_marks,
        IEMSCourses.credit_hours,
        StudentCourse.credits_earned,
        StudentCourse.grade,
        StudentCourse.grade_point,
    ).join(IEMStudents, StudentCourse.regno == IEMStudents.regno).join(
        IEMSDepartment, and_(
            IEMStudents.department_id == IEMSDepartment.dept_id,
            IEMSDepartment.status == 1,
            IEMSDepartment.org_id == org_id,
        )
    ).join(IEMProgram, and_(
        IEMProgram.pgm_id == IEMStudents.program_id,
        IEMProgram.dept_id == IEMSDepartment.dept_id,
        IEMProgram.status == 1,
        IEMProgram.org_id == org_id,
    )).join(IEMSCourses, and_(
        StudentCourse.crs_code == IEMSCourses.crs_code,
        IEMSCourses.program_id == program_id,
        IEMSCourses.department_id == IEMSDepartment.dept_id,
        IEMSCourses.org_id == org_id,
        IEMSCourses.result_year == belonging_year,
        IEMSCourses.status == 1,
    )).filter(
        StudentCourse.result_year == result_year,
        StudentCourse.program_id == program_id,
        StudentCourse.batch_id == batch_id,
        StudentCourse.is_evaluated == 1,
        StudentCourse.is_backlog == 1,
        IEMStudents.status == 1,
        StudentCourse.is_withdrawn == 0,
        StudentCourse.is_drop == 0,
    ).order_by(IEMSCourses.crs_order).all()

    return [
        {
            "std_crs_id": sc.std_crs_id,
            "usno": sc.usno,
            "student_name": sc.name,
            "crs_code": sc.crs_code,
            "cia": sc.total_cia,
            "see": sc.see,
            "cia_see": sc.cia_see,
            "max_marks": sc[6],
            "credits": sc.credit_hours,
            "credits_earned": sc.credits_earned,
            "grade": sc.grade,
            "grade_point": sc.grade_point,
        }
        for sc in student_courses
    ]


def see_processing(params, db: Session):
    pass

def cia_evaluate_processing(params, db: Session):
    pass

def cia_processing(params, db: Session):
    pass

def faculty_cia_processing(params, db: Session):
    pass

def withdraw(params, db: Session):
    pass

def see_evaluate_processing(params, db: Session):
    pass

def get_absentee(params, db: Session):
    pass

def get_grace_attendance(params, db: Session):
    pass

def fetch_in_eligible_list(request, is_backlog: int, org_id: int, db: Session):
    try:
        if is_backlog == 1:
            ineligible_list = get_ineligibility_backlog(request, org_id, db)
        else:
            ineligible_list = get_student_eligibility_list(request, org_id, db)
        
        # Format the data
        ineligible_list_data = [
            {
                "id": row.std_crs_id,
                "usno": row.usno,
                "student_name": row.name,
                "code": row.crs_code,
                "cia_eligibility": row.cia_eligibility,
                "nsar_eligibility": row.nsar_eligibility,
                "attendance_eligibility": row.attendance_eligibility,
            }
            for row in ineligible_list
        ]
        return ineligible_list_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_student_eligibility_list(request, org_id: int, db: Session):
    try:
        # Fetch belonging year
        belonging_year_query = (
            db.query(IEMExamEvent.belonging_year)
            .filter(
                IEMExamEvent.result_year == request.result_year,
                IEMExamEvent.org_id == org_id,
                IEMExamEvent.status == 1,
            )
            .first()
        )
        result_year_belonging = belonging_year_query.belonging_year if belonging_year_query else request.result_year

        # Main query
        result = (
            db.query(
                StudentCourse.std_crs_id,
                IEMStudents.name,
                func.ifnull(IEMStudents.usno, IEMStudents.roll_number).label("usno"),
                StudentCourse.crs_code,
                func.if_(
                    StudentCourse.cia_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("cia_eligibility"),
                func.if_(
                    StudentCourse.attendance_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("attendance_eligibility"),
                func.if_(
                    StudentCourse.nsar_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("nsar_eligibility"),
            )
            .join(
                IEMStudents,
                and_(
                    IEMStudents.regno == StudentCourse.regno,
                    IEMStudents.status == 1,
                    IEMStudents.org_id == org_id,
                )
            )
            .join(
                IEMSCourses,
                and_(
                    IEMSCourses.crs_code == StudentCourse.crs_code,
                    IEMSCourses.status == 1,
                    IEMSCourses.org_id == org_id,
                    IEMSCourses.result_year == result_year_belonging,
                    IEMSCourses.program_id == (request.program_id or IEMSCourses.program_id),
                    IEMSCourses.program_id == StudentCourse.program_id,
                    StudentCourse.batch_id == IEMSCourses.academic_batch_id,
                )
            )
            .filter(
                StudentCourse.result_year == request.result_year,
                StudentCourse.program_id == (request.program_id or StudentCourse.program_id),
                StudentCourse.is_withdrawn == 0,
                StudentCourse.is_drop == 0,
                StudentCourse.attendance_approved == 1,
                StudentCourse.cia_approved == 1,
                StudentCourse.is_evaluated == 1,
                StudentCourse.semester == (request.semester or StudentCourse.semester),
                StudentCourse.batch_id == (request.batch_id or StudentCourse.batch_id),
                IEMStudents.batch_cycle_id == (request.cycle or IEMStudents.batch_cycle_id),
            )
            .group_by(StudentCourse.std_crs_id)
            .all()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_ineligibility_backlog(request, org_id: int, db: Session):
    try:
        # Fetch belonging year
        belonging_year_query = (
            db.query(IEMExamEvent.belonging_year)
            .filter(IEMExamEvent.result_year == request.result_year)
            .first()
        )
        result_year_belonging = belonging_year_query.belonging_year if belonging_year_query else request.result_year

        # Main query
        result = (
            db.query(
                StudentCourse.std_crs_id,
                IEMStudents.name,
                func.ifnull(IEMStudents.usno, IEMStudents.roll_number).label("usno"),
                IEMSCourses.crs_code,
                func.if_(
                    StudentCourse.cia_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("cia_eligibility"),
                func.if_(
                    StudentCourse.attendance_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("attendance_eligibility"),
                func.if_(
                    StudentCourse.nsar_eligibility == 0,
                    "Not Eligible",
                    "Eligible"
                ).label("nsar_eligibility"),
            )
            .join(
                IEMStudents,
                and_(
                    IEMStudents.regno == StudentCourse.regno,
                    IEMStudents.status == 1,
                    IEMStudents.org_id == org_id,
                )
            )
            .join(
                IEMSDepartment,
                and_(
                    IEMSDepartment.dept_id == IEMStudents.department_id,
                    IEMSDepartment.status == 1,
                    IEMSDepartment.org_id == org_id,
                )
            )
            .join(
                IEMProgram,
                and_(
                    IEMProgram.pgm_id == IEMStudents.program_id,
                    IEMProgram.dept_id == IEMSDepartment.dept_id,
                    IEMProgram.status == 1,
                    IEMProgram.org_id == org_id,
                    IEMStudents.program_id == request.program_id,
                )
            )
            .join(
                IEMSCourses,
                and_(
                    IEMSCourses.crs_code == StudentCourse.crs_code,
                    IEMSCourses.status == 1,
                    IEMSCourses.org_id == org_id,
                    IEMSCourses.result_year == result_year_belonging,
                    IEMSCourses.program_id == request.program_id,
                    IEMSCourses.program_id == IEMProgram.pgm_id,
                    IEMSCourses.department_id == IEMSDepartment.dept_id,
                    StudentCourse.batch_id == IEMSCourses.academic_batch_id,
                )
            )
            .filter(
                StudentCourse.result_year == request.result_year,
                StudentCourse.program_id == request.program_id,
                StudentCourse.is_withdrawn == 0,
                StudentCourse.is_drop == 0,
                StudentCourse.batch_id == request.batch_id,
                StudentCourse.is_backlog == 1,
                StudentCourse.attendance_approved == 1,
                StudentCourse.cia_approved == 1,
                StudentCourse.is_evaluated == 1,
            )
            .group_by(StudentCourse.std_crs_id)
            .all()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def fetch_students_attendance(params, db: Session):
    pass

def viva_processing(params, db: Session):
    pass

def get_viva_absentee(params, db: Session):
    pass

def fetch_branch_change_students(params, db: Session):
    pass

def get_branch_change(param_list: dict, db: Session) -> List[dict]:
    branch_list = db.query(StudentCourse).filter_by(**param_list).all()
    branch_data = []

    for branch_list_value in branch_list:
        branch_data.append({
            'student_id': branch_list_value.student_id,
            'regno': branch_list_value.regno,
            'username': branch_list_value.name,
            'previous_usn': branch_list_value.old_usno,
            'current_usn': branch_list_value.usno,
            'previous_dept': branch_list_value.old_dept_name,
            'previous_dept_id': branch_list_value.old_department_id,
            'current_dept': branch_list_value.new_dept_name,
            'current_dept_id': branch_list_value.department_id,
            'previous_pgm_name': branch_list_value.old_pgm_name,
            'previous_pgm_id': branch_list_value.old_program_id,
            'current_pgm_name': branch_list_value.new_pgm_name,
            'current_pgm_id': branch_list_value.program_id,
            'previous_academic_name': branch_list_value.old_academic_code,
            'previous_academic_id': branch_list_value.old_academic_batch_id,
            'current_academic_name': branch_list_value.new_academic_code,
            'current_academic_id': branch_list_value.academic_batch_id,
            'program_type': branch_list_value.program_type,
        })

    return branch_data


def drop(params, db: Session):
    pass

def faculty_tw_processing(params, db: Session):
    pass

def tw_grade_processing(params, db: Session):
    pass

def result_finalize_grade_processing(params, db: Session):
    pass