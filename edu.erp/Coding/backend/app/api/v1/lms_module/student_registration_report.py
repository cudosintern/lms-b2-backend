"""Student registration report against the verified LMS database schema.

Enrollment home curriculum is std_crclm_id (the ORM currently names it differently).
Only read operations occur except the explicit, role-checked approval endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.auth_helper import get_current_user
from .course_registration_configuration.router import actor, bearer
from .course_registration_configuration.service import RegistrationService
from .registration_report_data import build_report, drilldown

router = APIRouter(prefix='/student-registration', tags=['Student Registration Report'])


def approval_context(db: Session = Depends(get_db), identity=Depends(actor)):
    return RegistrationService(db, identity)


def context(db: Session = Depends(get_db), user=Depends(get_current_user), token=Depends(bearer)):
    # Match the other LMS reports, including the application's development session.
    if not user.get('org_id'):
        raise HTTPException(403, 'Organisation context is required.')
    if token and token != 'demo-token-12345':
        return RegistrationService(db, actor(token=token, org_id=user['org_id'], db=db))
    identity = {'user_id': user['user_id'], 'org_id': user['org_id'],
                'department_id': user.get('user_dept_id'),
                'all_departments': bool(user.get('super_admin')),
                'instructor_only': not bool(user.get('super_admin')), 'read_only': True}
    return RegistrationService(db, identity)


def rows(svc, sql, **params):
    return [dict(r) for r in svc.db.execute(text(sql), {'org': svc.actor['org_id'], **params}).mappings()]


@router.get('/curriculums')
def curricula(svc=Depends(context)):
    return [{'id': b.academic_batch_id, 'name': b.academic_batch_desc}
            for b in svc.batches().order_by('academic_batch_desc').all()]


@router.get('/terms')
def terms(academic_batch_id: int = Query(..., gt=0), svc=Depends(context)):
    svc.batch(academic_batch_id)
    return rows(svc, '''SELECT semester_id AS id, CONCAT(semester, ' - Semester') AS name
        FROM iems_semester WHERE academic_batch_id=:batch AND org_id=:org AND status=1 ORDER BY semester''', batch=academic_batch_id)


def approval_allowed(svc):
    identity = svc.actor
    if identity.get('read_only'):
        return False
    role = rows(svc, '''SELECT 1 FROM iems_user_roles ur JOIN iems_user_role_master rm
        ON rm.user_role_id=ur.user_role_id WHERE ur.user_id=:user AND ur.org_id=:org
        AND rm.status=1 AND LOWER(rm.role_name) IN ('admin','administrator','director','chairman') LIMIT 1''', user=identity['user_id'])
    settings = rows(svc, 'SELECT marks_fetch_from FROM iems_organisation WHERE org_id=:org')
    return bool(role and settings and settings[0]['marks_fetch_from'] == 1)


def report_data(svc, batch, term_id, sections=()):
    term = svc.term(batch, term_id)
    curriculum = svc.batch(batch)
    params = {'batch': batch, 'term': term_id, 'semester': term.semester}
    flags = rows(svc, 'SELECT first_year_flag FROM iems_academic_batch WHERE academic_batch_id=:batch AND org_id=:org', **params)
    first_year = bool(flags[0]['first_year_flag'])
    students = rows(svc, '''SELECT s.student_id, s.usno AS usn,
        COALESCE(NULLIF(s.name,''), CONCAT_WS(' ',s.first_name,s.middle_name,s.last_name)) AS name,
        s.academic_batch_id AS home_batch_id, s.import_academic_batch_id,
        s.section_id, COALESCE(NULLIF(s.section,''),mt.mt_details_name,'Unassigned') AS section
        FROM iems_students s LEFT JOIN cudos_master_type_details mt ON mt.mt_details_id=s.section_id
        WHERE s.org_id=:org AND s.status=1
        AND (s.academic_batch_id=:batch OR (:first_year=1 AND s.import_academic_batch_id=:batch))''', **params, first_year=int(first_year))
    sections_available = {str(s['section_id']): {'id': str(s['section_id']), 'name': s['section']} for s in students}
    if any(str(section) not in sections_available for section in sections):
        raise HTTPException(422, 'Unknown section for this curriculum.')
    # Imported first-year cohorts may use a different curriculum with the same semester.
    source_batches = {batch}
    if first_year:
        source_batches.update(s['import_academic_batch_id'] for s in students if s['import_academic_batch_id'])
    course_rows, enrollments = {}, {}
    for source_batch in sorted(source_batches):
        source_terms = rows(svc, '''SELECT semester_id FROM iems_semester
            WHERE academic_batch_id=:source AND semester=:semester AND org_id=:org AND status=1''', **params, source=source_batch)
        if not source_terms:
            continue
        for source_term in source_terms:
            query_params = {**params, 'source': source_batch, 'source_term': source_term['semester_id']}
            for course in rows(svc, '''SELECT c.crs_id AS course_id,c.crs_code AS course_code,c.crs_title AS course_name,
                COALESCE(c.total_credits, c.credit_hours, 0) AS credits,c.course_type_id,ct.course_type_desc AS course_type,
                c.finalize_and_ready_for_ems_flag AS finalized
                FROM iems_courses c JOIN iems_course_type ct ON ct.course_type_id=c.course_type_id
                WHERE c.org_id=:org AND c.academic_batch_id=:source AND c.semester=:semester AND c.status>0''', **query_params):
                course_rows[course['course_id']] = course
            # Include outgoing electives by home curriculum and incoming students by course curriculum.
            for enrollment in rows(svc, '''SELECT e.mcstd_id, e.student_id,e.crs_id AS course_id,
                e.std_crclm_id AS home_batch_id,e.section_id,e.created_date AS registered_date,
                s.usno AS usn,COALESCE(NULLIF(s.name,''),CONCAT_WS(' ',s.first_name,s.middle_name,s.last_name)) AS name,
                COALESCE(mt.mt_details_name,NULLIF(s.section,''),'Unassigned') AS section,
                b.academic_batch_desc AS curriculum,c.crs_code AS course_code,c.crs_title AS course_name,
                COALESCE(c.total_credits, c.credit_hours, 0) AS credits,c.course_type_id,ct.course_type_desc AS course_type
                FROM cudos_map_courseto_student e
                JOIN iems_students s ON s.student_id=e.student_id AND s.status=1 AND s.org_id=:org
                JOIN iems_courses c ON c.crs_id=e.crs_id AND c.status>0 AND c.org_id=:org
                JOIN iems_course_type ct ON ct.course_type_id=c.course_type_id
                JOIN iems_academic_batch b ON b.academic_batch_id=e.std_crclm_id AND b.org_id=:org
                JOIN cudos_master_type_details st ON st.mt_details_id=e.status
                JOIN cudos_master_type status_type ON status_type.master_type_id=st.master_type_id
                LEFT JOIN cudos_master_type_details mt ON mt.mt_details_id=e.section_id
                WHERE status_type.master_type_name='student_registration_status'
                AND st.mt_details_name NOT IN ('Unregistered','Hospital')
                AND c.semester=:semester
                AND ((e.academic_batch_id=:source AND e.semester_id=:source_term)
                     OR (e.std_crclm_id=:source AND (e.std_term_id=:source_term OR e.std_term_id IS NULL)))
                ORDER BY e.created_date,e.mcstd_id''', **query_params):
                enrollments[enrollment['mcstd_id']] = enrollment
    result = build_report(students, list(course_rows.values()), list(enrollments.values()), batch, sections)
    result.update(curriculum=curriculum.academic_batch_desc, term=f'{term.semester} - Semester',
                  sections=list(sections_available.values()), can_approve=approval_allowed(svc),
                  finalized=bool(course_rows) and all(c['finalized'] for c in course_rows.values()))
    statuses = rows(svc, '''SELECT d.mt_details_id FROM cudos_master_type_details d
        JOIN cudos_master_type t ON t.master_type_id=d.master_type_id
        WHERE t.master_type_name='student_registration_status'
        AND d.mt_details_name NOT IN ('Unregistered','Hospital')''')
    result['warnings'] = [] if statuses else ['Registration status lookup values are missing. Registered counts cannot be determined until student_registration_status is configured.']
    result['_course_ids'] = list(course_rows)
    return result


@router.get('/report')
def report(academic_batch_id: int = Query(..., gt=0), semester_id: int = Query(..., gt=0),
           section: list[str] = Query(default=[]), svc=Depends(context)):
    data = report_data(svc, academic_batch_id, semester_id, section)
    data.pop('_course_ids')
    data.pop('registrations')
    return data


@router.get('/view-students')
def view_students(academic_batch_id: int = Query(..., gt=0), semester_id: int = Query(..., gt=0),
                  course_type_id: int = Query(..., gt=0), registered: bool = True,
                  course_id: int | None = Query(default=None, gt=0), other: bool = False,
                  by_course: bool = False, section: list[str] = Query(default=[]), svc=Depends(context)):
    data = report_data(svc, academic_batch_id, semester_id, section)
    # Incoming students are available only through courses owned by this report's curriculum.
    if course_id is not None and course_id not in data['_course_ids']:
        raise HTTPException(404, 'Course not found in this report.')
    if by_course:
        data['registrations'] = [r for r in data['registrations'] if r['course_id'] in data['_course_ids']]
    return drilldown(data, course_type_id, registered, course_id, other, academic_batch_id, by_course)


@router.post('/approve')
def approve(academic_batch_id: int = Query(..., gt=0), semester_id: int = Query(..., gt=0), svc=Depends(approval_context)):
    if not approval_allowed(svc):
        raise HTTPException(403, 'Approval requires Admin, Director or Chairman and EMS integration enabled.')
    try:
        term = svc.term(academic_batch_id, semester_id, lock=True)
        courses = rows(svc, '''SELECT crs_id FROM iems_courses WHERE academic_batch_id=:batch
            AND semester=:semester AND org_id=:org AND status>0 FOR UPDATE''', batch=academic_batch_id, semester=term.semester)
        if not courses:
            raise HTTPException(409, 'There are no active courses to approve.')
        # Approval always applies to the entire selected curriculum/term, irrespective of section filters.
        for course in courses:
            svc.db.execute(text('''UPDATE iems_courses SET finalize_and_ready_for_ems_flag=1
                WHERE crs_id=:course AND org_id=:org AND status>0'''), {'course': course['crs_id'], 'org': svc.actor['org_id']})
        svc.db.commit()
        return {'finalized': True}
    except Exception:
        svc.db.rollback()
        raise
