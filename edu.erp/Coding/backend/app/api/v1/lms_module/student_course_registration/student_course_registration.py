"""Demo integration: student_id is required on every student read and write.

At ERP integration, bind that ID to the authenticated student in one dependency;
an ID in a payload is context, not authentication.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from .registration_service import StudentRegistrationService, window
from .student_course_registration_schema import (
    StudentRequest, TermListRequest, SectionListRequest, AvailableCourseRequest,
    CourseRegistrationRequest, RegisteredCourseRequest, UnregisterRequest,
)

router = APIRouter()


@router.post('/context')
def context(request: StudentRequest, db: Session = Depends(get_db)):
    return returnSuccess(StudentRegistrationService(db).context(request.student_id))


@router.post('/terms')
def terms(request: TermListRequest, db: Session = Depends(get_db)):
    service = StudentRegistrationService(db)
    student = service.student(request.student_id)
    service.settings(student)
    return returnSuccess(service.terms(student, request.academic_batch_id))


@router.post('/available-courses')
def available_courses(request: AvailableCourseRequest, db: Session = Depends(get_db)):
    return returnSuccess(StudentRegistrationService(db).catalog(request))


@router.post('/get_registration_section_list')
def get_registration_section_list(request: SectionListRequest, db: Session = Depends(get_db)):
    service = StudentRegistrationService(db)
    student = service.student(request.student_id)
    service.settings(student)
    return returnSuccess(service.sections(service.term(student, request.academic_batch_id, request.semester_id)))


@router.post('/registered-courses')
def get_registered_courses(request: RegisteredCourseRequest, db: Session = Depends(get_db)):
    service = StudentRegistrationService(db)
    student = service.student(request.student_id)
    service.settings(student)
    return returnSuccess(service.registered(student))


@router.post('/register')
def register(request: CourseRegistrationRequest, db: Session = Depends(get_db)):
    result = StudentRegistrationService(db).save(request)
    return returnSuccess(result, result['message'])


@router.post('/unregister')
def unregister(request: UnregisterRequest, db: Session = Depends(get_db)):
    result = StudentRegistrationService(db).unregister(request)
    return returnSuccess(result, result['message'])


# Existing URL aliases remain, but require student context instead of trusting base IDs.
@router.get('/get_academic_batch_list')
@router.get('/get_registration_academic_batch_list')
def get_registration_academic_batch_list(student_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return returnSuccess(StudentRegistrationService(db).context(student_id)['curriculums'])


@router.get('/get_semester_list')
def get_semester_list(academic_batch_id: int, student_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return terms(TermListRequest(student_id=student_id, academic_batch_id=academic_batch_id), db)


@router.get('/get_registration_semester_list')
def get_registration_semester_list(registration_academic_batch_id: int, student_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return terms(TermListRequest(student_id=student_id, academic_batch_id=registration_academic_batch_id), db)


@router.get('/check_registration_status')
@router.get('/validate_registration_due_date')
def check_registration_status(academic_batch_id: int, semester_id: int, student_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    service = StudentRegistrationService(db)
    student = service.student(student_id)
    service.settings(student)
    state = window(service.term(student, academic_batch_id, semester_id))
    base_state = window(service.term(student, student['academic_batch_id'], student['semester_id']))
    if not base_state['registration_open']:
        state = base_state
    return returnSuccess({**state, 'is_registration_open': state['registration_open'],
        'status_message': state['message'], 'academic_batch_id': academic_batch_id, 'semester_id': semester_id}, state['message'])
