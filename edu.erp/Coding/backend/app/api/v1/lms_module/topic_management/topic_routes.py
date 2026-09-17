"""Manage topic instructors using the current CUDOS/IEMS models.

LMS portions, including their dates, are section-specific. A schedule_id in
this API is lms_map_portion_ls.mtp_id, not a global CUDOS schedule ID.
"""
from datetime import date, datetime
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .topic_calendar import sync_calendar, delivery_slots
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from app.db.models import (
    CudosTopic, CudosTopicLessonSchedule, IEMSAcademicBatch, IEMSemester,
    IEMSCourses, MasterTypeDetails, CudosMapCoursetoCourseInstructor,
    IEMSUsers, LMSMapInstructorTopic, LMSMapPortionLS,
)
from .topic_schema import (
    TopicContext, TopicListRequest, TopicCreateRequest, NewTopicRequest,
    ImportTopicRequest, AssignTopicsRequest, TopicAssignment,
    UpdateInstructorRequest, ScheduleInput, AddScheduleRequest,
    SaveSchedulesRequest, ExtraClassRequest, BulkDeleteRequest,
)

router = APIRouter(tags=['Topic Management'])

def success(data=None, message='Success'):
    return {'success': True, 'data': data, 'message': message}

def actor(user):
    user_id = user.get('user_id') or user.get('id')
    if not user_id:
        raise HTTPException(401, 'Authentication required')
    return int(user_id)

def mapping_query(db, context):
    return db.query(LMSMapInstructorTopic).filter_by(
        academic_batch_id=context.academic_batch_id, semester_id=context.semester_id,
        crs_id=context.course_id, section_id=context.section_id)

def topic_query(db, context):
    return db.query(CudosTopic).filter_by(academic_batch_id=context.academic_batch_id,
        semester_id=context.semester_id, crs_id=context.course_id)

def validate_context(db, context):
    semester = db.query(IEMSemester).filter_by(semester_id=context.semester_id,
        academic_batch_id=context.academic_batch_id).first()
    course = db.query(IEMSCourses).filter_by(crs_id=context.course_id,
        academic_batch_id=context.academic_batch_id).first()
    if not semester or not course or course.semester != semester.semester:
        raise HTTPException(422, 'Course, semester and academic batch do not match')
    if not db.query(CudosMapCoursetoCourseInstructor).filter_by(
        academic_batch_id=context.academic_batch_id, semester_id=context.semester_id,
        crs_id=context.course_id, section_id=context.section_id).first():
        raise HTTPException(422, 'Section is not assigned to this course')
    return course

def validate_instructor(db, context, instructor_id):
    if not instructor_id or not db.query(CudosMapCoursetoCourseInstructor).filter_by(
        academic_batch_id=context.academic_batch_id, semester_id=context.semester_id,
        crs_id=context.course_id, section_id=context.section_id,
        course_instructor_id=instructor_id).first():
        raise HTTPException(422, 'Select an instructor assigned to this course and section')

def get_mapping(db, mapping_id):
    mapping = db.query(LMSMapInstructorTopic).filter_by(inst_map_id=mapping_id).first()
    if not mapping:
        raise HTTPException(404, 'Topic mapping not found')
    return mapping

def context_for(mapping):
    return TopicContext(academic_batch_id=mapping.academic_batch_id,
        semester_id=mapping.semester_id, course_id=mapping.crs_id,
        section_id=mapping.section_id)

def portions(db, mapping):
    return db.query(LMSMapPortionLS).filter_by(topic_id=mapping.topic_id,
        section_id=mapping.section_id).order_by(LMSMapPortionLS.portion_id).all()

def serialize_portion(p, index):
    return {'schedule_id': p.portion_id, 'portion_id': p.portion_id,
        'lesson_schedule_id': p.lesson_schedule_id, 'topic_id': p.topic_id,
        'session_number': int(p.portion_ref) if (p.portion_ref or '').isdigit() else index,
        'portion_to_be_covered': p.portion_per_hour or '',
        'conduction_date': p.planned_date, 'actual_delivery_date': p.delivery_date,
        'start_time': p.start_time, 'end_time': p.end_time}

def seed_portions(db, context, topic, user_id):
    existing = db.query(LMSMapPortionLS).filter_by(topic_id=topic.topic_id,
        section_id=context.section_id).all()
    # An imported section owns its lesson rows. Reassigning instructors must
    # not reseed them or overwrite edits made in LMS.
    if existing:
        return
    # The LMS foreign key targets topic_lesson_schedule, not the independent
    # cudos_topic_lesson_schedule ID space. Copy CUDOS content without that FK.
    source = db.query(CudosTopicLessonSchedule).filter_by(topic_id=topic.topic_id,
        academic_batch_id=context.academic_batch_id, crs_id=context.course_id).all()
    saved = {p.lesson_schedule_id for p in existing if p.lesson_schedule_id}
    for s in source:
        if s.lesson_schedule_id not in saved:
            db.add(LMSMapPortionLS(topic_id=topic.topic_id, section_id=context.section_id,
                lesson_schedule_id=None, portion_ref=s.portion_ref,
                portion_per_hour=s.portion_per_hour or '', planned_date=s.conduction_date,
                delivery_date=s.actual_delivery_date, created_by=user_id, created_date=datetime.now()))
    if not source and not existing:
        legacy = db.execute(text("""SELECT lesson_schedule_id,portion_ref,portion_per_hour,
            conduction_date,actual_delivery_date FROM topic_lesson_schedule
            WHERE topic_id=:topic AND academic_batch_id=:batch AND course_id=:course"""),
            {'topic': topic.topic_id, 'batch': context.academic_batch_id, 'course': context.course_id}).mappings().all()
        count = len(legacy) or max(1, int(topic.num_of_sessions or 1))
        for index in range(count):
            old = legacy[index] if legacy else None
            db.add(LMSMapPortionLS(topic_id=topic.topic_id, section_id=context.section_id,
                lesson_schedule_id=old['lesson_schedule_id'] if old else None,
                portion_ref=old['portion_ref'] if old else str(index + 1),
                portion_per_hour=old['portion_per_hour'] if old else topic.topic_content or '',
                planned_date=old['conduction_date'] if old else topic.conduction_date,
                delivery_date=old['actual_delivery_date'] if old else None,
                created_by=user_id, created_date=datetime.now()))

def assign(db, request, user_id):
    validate_context(db, request)
    result = []
    for assignment in request.assignments:
        topic = topic_query(db, request).filter_by(topic_id=assignment.topic_id).with_for_update().first()
        if not topic:
            raise HTTPException(422, 'A selected topic does not belong to this course and semester')
        existing_instructors = {r.instructor_id for r in mapping_query(db, request).filter_by(topic_id=topic.topic_id).all() if r.instructor_id}
        if len(existing_instructors | set(assignment.instructor_ids)) > 3:
            raise HTTPException(422, 'A topic can have at most three instructors')
        for instructor_id in set(assignment.instructor_ids):
            validate_instructor(db, request, instructor_id)
            mapping = mapping_query(db, request).filter_by(topic_id=topic.topic_id,
                instructor_id=instructor_id).first()
            if not mapping:
                mapping = LMSMapInstructorTopic(academic_batch_id=request.academic_batch_id,
                    semester_id=request.semester_id, crs_id=request.course_id,
                    section_id=request.section_id, topic_id=topic.topic_id,
                    instructor_id=instructor_id, created_by=user_id, created_date=datetime.now())
                db.add(mapping)
                db.flush()
            result.append({'topic_id': topic.topic_id, 'mapping_id': mapping.inst_map_id,
                'instructor_id': instructor_id})
        seed_portions(db, request, topic, user_id)
        db.flush()
    return result

@router.post('/curriculum_list')
def curriculum_list(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return success([{'value': r.academic_batch_id,
        'label': r.academic_batch_desc or str(r.academic_batch_id)}
        for r in db.query(IEMSAcademicBatch).all()])

@router.post('/semester_list')
def semester_list(request: dict = Body(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(IEMSemester)
    if request.get('academic_batch_id'):
        query = query.filter_by(academic_batch_id=request['academic_batch_id'])
    return success([{'value': s.semester_id, 'label': s.semester_desc or f'Semester {s.semester}'}
        for s in query.order_by(IEMSemester.semester).all()])

@router.post('/course_list')
def course_list(request: dict = Body(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    batch = request.get('academic_batch_id') or request.get('curriculum_id')
    query = db.query(IEMSCourses)
    if batch:
        query = query.filter_by(academic_batch_id=batch)
    if request.get('semester_id'):
        sem_query = db.query(IEMSemester).filter_by(semester_id=request['semester_id'])
        if batch:
            sem_query = sem_query.filter_by(academic_batch_id=batch)
        semester = sem_query.first()
        if not semester:
            return success([])
        query = query.filter_by(semester=semester.semester)
    return success([{'value': c.crs_id, 'label': f'{c.crs_code} - {c.crs_title}',
        'lms_topic_import_type_flag': c.lms_topic_import_type_flag} for c in query.all()])

@router.post('/section_list')
def section_list(request: dict = Body(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.query(MasterTypeDetails).join(CudosMapCoursetoCourseInstructor,
        MasterTypeDetails.mt_details_id == CudosMapCoursetoCourseInstructor.section_id).filter(
        CudosMapCoursetoCourseInstructor.academic_batch_id == request.get('academic_batch_id'),
        CudosMapCoursetoCourseInstructor.semester_id == request.get('semester_id'),
        CudosMapCoursetoCourseInstructor.crs_id == request.get('course_id')).distinct().all()
    return success([{'value': r.mt_details_id, 'label': r.mt_details_name} for r in rows])

@router.post('/instructor_list')
def instructor_list(request: dict = Body(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(IEMSUsers).join(CudosMapCoursetoCourseInstructor,
        IEMSUsers.id == CudosMapCoursetoCourseInstructor.course_instructor_id).filter(
        CudosMapCoursetoCourseInstructor.crs_id == request.get('course_id'))
    for key in ('academic_batch_id', 'semester_id', 'section_id'):
        if request.get(key):
            query = query.filter(getattr(CudosMapCoursetoCourseInstructor, key) == request[key])
    return success([{'value': r.id, 'label': ' '.join(filter(None, [r.first_name, r.last_name])) or r.username}
        for r in query.distinct().all()])

@router.post('/topic_list')
def topic_list(request: TopicListRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    validate_context(db, request)
    result = []
    for topic in topic_query(db, request).order_by(CudosTopic.topic_id).all():
        maps = mapping_query(db, request).filter_by(topic_id=topic.topic_id).all()
        if not maps or (request.instructor_id and request.instructor_id not in [m.instructor_id for m in maps]):
            continue
        instructors = db.query(IEMSUsers).filter(IEMSUsers.id.in_([m.instructor_id for m in maps])).all()
        ps = portions(db, maps[0])
        result.append({'topic_id': topic.topic_id, 'mapping_id': maps[0].inst_map_id,
            'course_id': topic.crs_id, 'section_id': request.section_id,
            'topic_code': topic.topic_code, 'topic_title': topic.topic_title,
            'topic_content': topic.topic_content, 'topic_hrs': topic.topic_hrs,
            'num_of_sessions': topic.num_of_sessions, 'marks_expt': topic.marks_expt,
            'instructor_id': maps[0].instructor_id, 'instructor_ids': [m.instructor_id for m in maps],
            'instructor_name': ', '.join(' '.join(filter(None, [i.first_name, i.last_name])) or i.username for i in instructors),
            'lesson_schedule': ', '.join(p.portion_per_hour for p in ps if p.portion_per_hour),
            'portions': [serialize_portion(p, n) for n, p in enumerate(ps, 1)],
            'actual_delivery_date': max((p.delivery_date for p in ps if p.delivery_date), default=None),
            'is_imported': True})
    return success(result)

@router.post('/cudos_topics')
def cudos_topics(request: TopicContext, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    validate_context(db, request)
    section = db.query(MasterTypeDetails).filter_by(mt_details_id=request.section_id).first()
    owner = db.query(CudosMapCoursetoCourseInstructor).filter_by(
        academic_batch_id=request.academic_batch_id, semester_id=request.semester_id,
        crs_id=request.course_id, section_id=request.section_id).filter(
        CudosMapCoursetoCourseInstructor.course_instructor_id.isnot(None)).order_by(
        CudosMapCoursetoCourseInstructor.mcci_id).first()
    result = []
    for topic in topic_query(db, request).all():
        if bool(topic.category_id) != bool(section.parent_id):
            continue
        mapped = mapping_query(db, request).filter_by(topic_id=topic.topic_id).all()
        has_portions = bool(db.query(LMSMapPortionLS.portion_id).filter_by(
            topic_id=topic.topic_id, section_id=request.section_id).first())
        if not has_portions:
            has_portions = bool(db.query(CudosTopicLessonSchedule.lesson_schedule_id).filter_by(
                topic_id=topic.topic_id, academic_batch_id=request.academic_batch_id,
                crs_id=request.course_id).first())
        if not has_portions:
            has_portions = bool(db.execute(text("""SELECT lesson_schedule_id FROM topic_lesson_schedule
                WHERE topic_id=:topic AND academic_batch_id=:batch AND course_id=:course LIMIT 1"""),
                {'topic': topic.topic_id, 'batch': request.academic_batch_id, 'course': request.course_id}).first())
        result.append({'topic_id': topic.topic_id, 'topic_code': topic.topic_code,
            'topic_title': topic.topic_title, 'topic_hrs': topic.topic_hrs,
            'num_of_sessions': topic.num_of_sessions, 'has_portions': has_portions,
            'instructor_ids': [m.instructor_id for m in mapped if m.instructor_id],
            'default_instructor_id': owner.course_instructor_id if owner else None})
    return success(result)

@router.post('/assign_topics')
def assign_topics(request: AssignTopicsRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        data = assign(db, request, actor(user))
        db.commit()
        return success(data, 'Topics assigned successfully')
    except Exception:
        db.rollback()
        raise

@router.post('/import_topic')
@router.post('/import_selected_topics')
@router.post('/import_cudos_topics')
def import_topics(request: ImportTopicRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return assign_topics(AssignTopicsRequest(**request.model_dump(), assignments=[
        TopicAssignment(topic_id=t, instructor_ids=[request.instructor_id]) for t in set(request.topic_ids)]), db, user)

@router.put('/update_mapping/{mapping_id}')
@router.put('/update_instructor/{mapping_id}')
def update_instructor(mapping_id: int, request: UpdateInstructorRequest,
        db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        mapping = get_mapping(db, mapping_id)
        instructor_id = request.instructor_id or request.course_instructor_id
        validate_instructor(db, context_for(mapping), instructor_id)
        duplicate = mapping_query(db, context_for(mapping)).filter_by(
            topic_id=mapping.topic_id, instructor_id=instructor_id).first()
        if duplicate and duplicate.inst_map_id != mapping_id:
            raise HTTPException(409, 'Instructor already assigned to this topic')
        mapping.instructor_id = instructor_id
        mapping.modified_by = actor(user)
        mapping.modified_date = datetime.now()
        db.commit()
        return success(message='Instructor updated')
    except Exception:
        db.rollback()
        raise

@router.put('/update_topic/{topic_id}')
def update_topic(topic_id: int, request: TopicCreateRequest,
        db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    topic = topic_query(db, request).filter_by(topic_id=topic_id).first()
    if not topic:
        raise HTTPException(404, 'Topic not found in this academic context')
    try:
        for field in ('topic_code', 'topic_title', 'topic_content', 'topic_hrs', 'num_of_sessions'):
            if field in request.model_fields_set:
                setattr(topic, field, getattr(request, field))
        topic.modified_by = actor(user)
        topic.modified_date = date.today()
        db.commit()
        return success({'topic_id': topic_id}, 'Topic updated')
    except Exception:
        db.rollback()
        raise

@router.post('/add_new_topic')
def add_new_topic(request: NewTopicRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        validate_context(db, request)
        validate_instructor(db, request, request.instructor_id)
        if not request.topic_title.strip() or not request.topic_code.strip():
            raise HTTPException(422, 'Topic title and code are required')
        if topic_query(db, request).filter_by(topic_code=request.topic_code.strip()).first():
            raise HTTPException(409, 'Topic code already exists in this course')
        topic = CudosTopic(crs_id=request.course_id, academic_batch_id=request.academic_batch_id,
            semester_id=request.semester_id, topic_code=request.topic_code.strip(),
            topic_title=request.topic_title.strip(), topic_content=request.topic_content,
            topic_hrs=request.topic_hrs, num_of_sessions=request.num_of_sessions,
            created_by=actor(user), created_date=date.today())
        db.add(topic)
        db.flush()
        assignments = assign(db, AssignTopicsRequest(**request.model_dump(), assignments=[
            TopicAssignment(topic_id=topic.topic_id, instructor_ids=[request.instructor_id])]), actor(user))
        if request.delivery_date:
            first = db.query(LMSMapPortionLS).filter_by(topic_id=topic.topic_id, section_id=request.section_id).order_by(LMSMapPortionLS.portion_id).first()
            first.planned_date = request.delivery_date
            first.delivery_date = request.delivery_date
        db.commit()
        return {'success': True, 'topic_id': topic.topic_id, 'mapping_id': assignments[0]['mapping_id']}
    except Exception:
        db.rollback()
        raise

@router.post('/topic_schedules')
def topic_schedules(mapping_id: int = Body(..., embed=True), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return success([serialize_portion(p, n) for n, p in enumerate(portions(db, get_mapping(db, mapping_id)), 1)])

def write_portion(db, mapping, request, user_id, portion=None):
    if bool(request.start_time) != bool(request.end_time):
        raise HTTPException(422, 'Both delivery times are required')
    if request.start_time and request.start_time >= request.end_time:
        raise HTTPException(422, 'End time must be after start time')
    if not portion:
        portion = LMSMapPortionLS(topic_id=mapping.topic_id, section_id=mapping.section_id,
            created_by=user_id, created_date=datetime.now())
        db.add(portion)
    portion.portion_ref = str(request.session_number)
    portion.portion_per_hour = request.portion_to_be_covered
    portion.planned_date = request.conduction_date
    portion.delivery_date = request.actual_delivery_date
    portion.start_time = request.start_time
    portion.end_time = request.end_time
    portion.status = int(bool(portion.delivery_date and portion.start_time))
    portion.modified_by = user_id
    portion.modified_date = datetime.now()
    db.flush()
    sync_calendar(db, mapping, portion, user_id)
    return portion

@router.post('/save_schedules')
def save_schedules(request: SaveSchedulesRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        mapping = get_mapping(db, request.mapping_id)
        if request.instructor_ids is not None:
            assign(db, AssignTopicsRequest(**context_for(mapping).model_dump(), assignments=[
                TopicAssignment(topic_id=mapping.topic_id, instructor_ids=request.instructor_ids)]), actor(user))
        existing = {p.portion_id: p for p in portions(db, mapping)}
        ids = [s.schedule_id for s in request.schedules]
        lectures = [s.session_number for s in request.schedules]
        if len(ids) != len(set(ids)) or len(lectures) != len(set(lectures)):
            raise HTTPException(422, 'Duplicate schedule or lecture number')
        for s in request.schedules:
            if s.schedule_id > 0 and s.schedule_id not in existing:
                raise HTTPException(404, 'Schedule does not belong to this topic and section')
            write_portion(db, mapping, s, actor(user), existing.get(s.schedule_id))
        db.commit()
        return success([serialize_portion(p, n) for n, p in enumerate(portions(db, mapping), 1)], 'Schedules saved')
    except Exception:
        db.rollback()
        raise

@router.post('/add_schedule')
def add_schedule(request: AddScheduleRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        p = write_portion(db, get_mapping(db, request.mapping_id), request, actor(user))
        db.commit()
        return {'success': True, 'schedule_id': p.portion_id}
    except Exception:
        db.rollback()
        raise

@router.put('/update_schedule/{schedule_id}')
def update_schedule(schedule_id: int, request: dict = Body(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        mapping = get_mapping(db, request.get('mapping_id'))
        portion = db.query(LMSMapPortionLS).filter_by(portion_id=schedule_id,
            topic_id=mapping.topic_id, section_id=mapping.section_id).first()
        if not portion:
            raise HTTPException(404, 'Schedule not found in this topic and section')
        values = serialize_portion(portion, 1)
        values.update(request)
        write_portion(db, mapping, ScheduleInput(**values), actor(user), portion)
        db.commit()
        return success(message='Schedule updated')
    except Exception:
        db.rollback()
        raise

@router.post('/add_extra_class')
def add_extra_class(request: ExtraClassRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    mapping = get_mapping(db, request.mapping_id)
    next_number = max([int(p.portion_ref) for p in portions(db, mapping) if (p.portion_ref or '').isdigit()] or [0]) + 1
    try:
        portion = write_portion(db, mapping, AddScheduleRequest(mapping_id=request.mapping_id,
            session_number=next_number, portion_to_be_covered=request.notes or 'Extra class',
            conduction_date=request.class_date, start_time=request.start_time,
            end_time=request.end_time), actor(user))
        sync_calendar(db, mapping, portion, actor(user), extra=True)
        db.commit()
        return {'success': True, 'schedule_id': portion.portion_id}
    except Exception:
        db.rollback()
        raise

@router.post('/delivery_slots')
def get_delivery_slots(mapping_id: int = Body(..., embed=True), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return success(delivery_slots(db, context_for(get_mapping(db, mapping_id))))

@router.post('/bulk_delete_topics')
def bulk_delete_topics(request: BulkDeleteRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        validate_context(db, request)
        ids = set(request.topic_ids)
        valid = {t.topic_id for t in topic_query(db, request).filter(CudosTopic.topic_id.in_(ids)).all()}
        if valid != ids:
            raise HTTPException(404, 'Topic not found in this academic context')
        # Match the legacy removal: remove instructor assignments only. Keep
        # section portions and delivered calendar/student history for reimport.
        mapping_query(db, request).filter(LMSMapInstructorTopic.topic_id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return success(message='Topics removed from the selected section')
    except Exception:
        db.rollback()
        raise

@router.delete('/delete_topic/{topic_id}')
def delete_topic(topic_id: int, request: TopicContext, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return bulk_delete_topics(BulkDeleteRequest(**request.model_dump(), topic_ids=[topic_id]), db, user)
