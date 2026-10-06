"""Student registration against the ERP schema (demo student_id boundary)."""
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import text

from app.api.v1.lms_module.course_registration_configuration.service import COURSE_TYPE_ALIASES


def fail(message, code=409):
    raise HTTPException(code, message)


def combine(day, clock):
    if day is None or clock is None:
        return None
    if isinstance(clock, timedelta):
        return datetime.combine(day, time()) + clock
    return datetime.combine(day, clock)


def window(term, now=None):
    now = now or datetime.now()
    start = combine(term.get('enroll_start_date'), term.get('enroll_start_time'))
    end = combine(term.get('enroll_end_date'), term.get('enroll_end_time'))
    opened = bool(start and end and start <= now <= end)
    if not start or not end or start >= end:
        message = 'Registration dates are not configured.'
        opened = False
    elif now < start:
        message = f'Registration opens on {start:%d-%m-%Y %I:%M %p}.'
    elif now > end:
        message = f'Registration closed on {end:%d-%m-%Y %I:%M %p}.'
    else:
        message = f'Registration is open until {end:%d-%m-%Y %I:%M %p}.'
    return dict(registration_open=opened, registration_start=start,
                registration_end=end, server_time=now, message=message)


def alias(code):
    return COURSE_TYPE_ALIASES.get((code or '').upper(), 'CORE')


def validate_selection(existing, selected, base, structures, mode):
    """Validate the combined selection, counting each course once across lab mappings."""
    combined = {row['crs_id']: row for row in existing}
    combined.update({row['crs_id']: row for row in selected})
    amount = lambda row: Decimal(str(row.get('total_credits') or 0)) if mode == 'credits' else Decimal(1)
    total = base.get('total_crs_enroll')
    if total is None:
        fail('Registration limits are not configured for the student term.')
    if sum((amount(row) for row in combined.values()), Decimal(0)) > Decimal(str(total)):
        fail(f'The selection exceeds the term limit of {total} {mode}.')
    by_type = defaultdict(Decimal)
    own = other = 0
    for row in combined.values():
        by_type[(row['academic_batch_id'], row['semester_id'], row['course_type_id'])] += amount(row)
        if alias(row['course_type_code']) == 'OPEN_ELECTIVE':
            if row['academic_batch_id'] == base['academic_batch_id']:
                own += 1
            else:
                other += 1
    if own > (base.get('own_crclm_elective') or 0):
        fail('The own-curriculum open-elective limit would be exceeded.')
    if other > (base.get('other_crclm_elective') or 0):
        fail('The other-curriculum open-elective limit would be exceeded.')
    for key in {(r['academic_batch_id'], r['semester_id'], r['course_type_id']) for r in selected}:
        limit = structures.get(key)
        if not limit or limit.get('stud_max_crs_enroll') is None:
            fail('Course-type registration limits are not configured.')
        if by_type[key] > Decimal(str(limit['stud_max_crs_enroll'])):
            fail(f'The selection exceeds the course-type maximum of {limit["stud_max_crs_enroll"]} {mode}.')
        if by_type[key] < Decimal(str(limit.get('stud_min_crs_enroll') or 0)):
            fail(f'Select at least {limit["stud_min_crs_enroll"]} {mode} for this course type.')


class StudentRegistrationService:
    def __init__(self, db):
        self.db = db

    def rows(self, sql, **params):
        return [dict(row) for row in self.db.execute(text(sql), params).mappings()]

    def one(self, sql, **params):
        rows = self.rows(sql, **params)
        return rows[0] if rows else None

    def student(self, student_id, lock=False):
        # semester_id and the legacy std_* columns are present in the actual ERP DB,
        # but absent/misnamed in the shared ORM; do not load that stale enrollment model.
        row = self.one('''SELECT student_id, org_id, academic_batch_id, semester_id, current_semester
            FROM iems_students WHERE student_id=:id AND status=1''' + (' FOR UPDATE' if lock else ''), id=student_id)
        if not row:
            fail('Active student not found.', 404)
        if row['academic_batch_id'] and row.get('current_semester') is not None:
            # ERP current_semester is a semester number, not a term primary key.
            # Resolve it within this curriculum; semester_id can lag promotion data.
            terms = self.rows('''SELECT semester_id FROM iems_semester
                WHERE academic_batch_id=:batch AND org_id=:org AND semester=:number AND status=1''',
                batch=row['academic_batch_id'], org=row['org_id'], number=row['current_semester'])
            if len(terms) != 1:
                fail('The student current semester must match exactly one active curriculum term.')
            row['semester_id'] = terms[0]['semester_id']
        if not row['academic_batch_id'] or not row['semester_id']:
            fail('The student has no academic batch or semester assigned.')
        return row

    def settings(self, student):
        rows = self.rows('''SELECT config_type, value FROM iems_org_configs
            WHERE org_id=:org AND program_id IS NULL AND crs_code IS NULL
            AND config_type IN ('enable_crs_reg_by_stud','lms_stud_crs_reg')''', org=student['org_id'])
        values = {'enable_crs_reg_by_stud': '1', 'lms_stud_crs_reg': '1'}
        if len({r['config_type'] for r in rows}) != len(rows):
            fail('Duplicate organisation registration settings.')
        values.update({r['config_type']: r['value'] for r in rows})
        if any(v not in ('0', '1') for v in values.values()):
            fail('Invalid organisation registration settings.')
        if values['enable_crs_reg_by_stud'] != '1':
            fail('Student course registration is disabled.', 403)
        return 'credits' if values['lms_stud_crs_reg'] == '1' else 'courses'

    def batches(self, student):
        return self.rows('''SELECT b.academic_batch_id, b.academic_batch_code, b.academic_batch_desc
            FROM iems_academic_batch b JOIN iems_academic_batch base
              ON b.start_year=base.start_year AND b.end_year=base.end_year AND b.org_id=base.org_id
            WHERE base.academic_batch_id=:base AND base.org_id=:org AND b.status=1
            ORDER BY (b.academic_batch_id=:base) DESC, b.academic_batch_desc''',
            base=student['academic_batch_id'], org=student['org_id'])

    def term(self, student, batch_id, term_id, lock=False):
        if batch_id not in {r['academic_batch_id'] for r in self.batches(student)}:
            fail('Curriculum is not available for this student.', 403)
        term = self.one('''SELECT * FROM iems_semester WHERE semester_id=:term
            AND academic_batch_id=:batch AND org_id=:org AND status=1''' + (' FOR UPDATE' if lock else ''),
            term=term_id, batch=batch_id, org=student['org_id'])
        if not term:
            fail('Semester not found for this curriculum.', 404)
        base = self.one('SELECT semester FROM iems_semester WHERE semester_id=:term AND academic_batch_id=:batch',
                        term=student['semester_id'], batch=student['academic_batch_id'])
        if not base or term['semester'] != base['semester']:
            fail('The selected semester does not match the student semester.', 403)
        return term

    def terms(self, student, batch_id):
        self.term(student, student['academic_batch_id'], student['semester_id'])
        if batch_id not in {r['academic_batch_id'] for r in self.batches(student)}:
            fail('Curriculum is not available for this student.', 403)
        return self.rows('''SELECT semester_id, semester, semester_code, semester_desc, term_name
            FROM iems_semester WHERE academic_batch_id=:batch AND org_id=:org AND status=1
            AND semester=(SELECT semester FROM iems_semester WHERE semester_id=:base)
            ORDER BY semester_id''', batch=batch_id, org=student['org_id'], base=student['semester_id'])

    def sections(self, term):
        return self.rows('''SELECT DISTINCT d.mt_details_id AS section_id, d.mt_details_name AS section_name,
            d.parent_id FROM cudos_master_type_details d
            JOIN cudos_master_type mt ON mt.master_type_id=d.master_type_id AND mt.master_type_alias_name='SECTION'
            JOIN cudos_map_courseto_course_instructor i ON i.section_id=d.mt_details_id
            JOIN iems_courses c ON c.crs_id=i.crs_id AND c.academic_batch_id=i.academic_batch_id
            WHERE i.academic_batch_id=:batch AND i.semester_id=:number AND c.semester=:number
            AND c.org_id=:org AND c.status>0 AND d.mtd_status=1
            ORDER BY d.mt_details_name''', batch=term['academic_batch_id'], term=term['semester_id'],
            number=term['semester'], org=term['org_id'])

    def context(self, student_id):
        student = self.student(student_id)
        mode = self.settings(student)
        self.term(student, student['academic_batch_id'], student['semester_id'])
        return {**student, 'mode': mode, 'curriculums': self.batches(student)}

    def registered(self, student):
        rows = self.rows('''SELECT e.mcstd_id,e.crs_id,e.academic_batch_id,e.semester_id,e.section_id,e.batch_id,
            e.crs_reg_flag,e.status,e.created_date,c.crs_code,c.crs_title,c.total_credits,c.course_type_id,
            ct.course_type_code,ct.course_type_desc,d.mt_details_name AS section_name,
            batch.mt_details_name AS batch_name,st.mt_details_name AS registration_status,
            t.enroll_start_date,t.enroll_start_time,t.enroll_end_date,t.enroll_end_time,
            c.reg_start_date,c.reg_end_date
            FROM cudos_map_courseto_student e JOIN iems_courses c ON c.crs_id=e.crs_id
            JOIN iems_course_type ct ON ct.course_type_id=c.course_type_id
            JOIN cudos_master_type_details st ON st.mt_details_id=e.status
            JOIN cudos_master_type mt ON mt.master_type_id=st.master_type_id
            JOIN iems_semester t ON t.semester_id=e.semester_id AND t.academic_batch_id=e.academic_batch_id
            LEFT JOIN cudos_master_type_details d ON d.mt_details_id=e.section_id
            LEFT JOIN cudos_master_type_details batch ON batch.mt_details_id=e.batch_id
            WHERE e.student_id=:student AND e.std_crclm_id=:base
            AND (e.std_term_id=:term OR (e.std_term_id IS NULL
                AND t.semester=(SELECT semester FROM iems_semester WHERE semester_id=:term)))
            AND c.org_id=:org AND mt.master_type_name='student_registration_status'
            AND st.mt_details_name<>'Unregistered' ORDER BY c.crs_code,e.mcstd_id''',
            student=student['student_id'], base=student['academic_batch_id'], term=student['semester_id'], org=student['org_id'])
        base = self.term(student, student['academic_batch_id'], student['semester_id'])
        now = datetime.now()
        for row in rows:
            state, base_state = window(row, now), window(base, now)
            row['can_unregister'] = row['crs_reg_flag'] == 1 and state['registration_open'] and base_state['registration_open']
            ends = [state['registration_end'], base_state['registration_end']]
            if alias(row['course_type_code']) == 'OPEN_ELECTIVE' and (row['reg_start_date'] or row['reg_end_date']):
                row['can_unregister'] = bool(row['can_unregister'] and row['reg_start_date'] and row['reg_end_date']
                    and row['reg_start_date'] <= now <= row['reg_end_date'])
                ends.append(row['reg_end_date'])
            row['unregister_until'] = min((end for end in ends if end), default=None)
        return rows

    def structures(self, term):
        return {(r['academic_batch_id'], r['semester_id'], r['crs_type_id']): r for r in self.rows('''
            SELECT * FROM lms_academic_batch_semester_crs_structure
            WHERE academic_batch_id=:batch AND semester_id=:term''', batch=term['academic_batch_id'], term=term['semester_id'])}

    def offerings(self, student, term, section_id):
        sections = {r['section_id']: r for r in self.sections(term)}
        if section_id not in sections:
            fail('Select a section or lab batch offered in this semester.', 422)
        rows = self.rows('''SELECT c.crs_id,c.crs_code,c.crs_title,c.course_type_id,c.total_credits,
            c.total_marks,c.total_stud_enroll,c.reg_start_date,c.reg_end_date,c.academic_batch_id,
            :term AS semester_id,ct.course_type_code,ct.course_type_desc,
            GROUP_CONCAT(DISTINCT u.first_name ORDER BY u.first_name SEPARATOR ', ') AS instructor
            FROM iems_courses c JOIN iems_course_type ct ON ct.course_type_id=c.course_type_id
            JOIN cudos_map_courseto_course_instructor i ON i.crs_id=c.crs_id AND i.academic_batch_id=c.academic_batch_id
            LEFT JOIN iems_users u ON u.id=i.course_instructor_id
            WHERE c.academic_batch_id=:batch AND c.semester=:number AND c.org_id=:org AND c.status>0
            AND i.semester_id=:number AND i.section_id=:section
            GROUP BY c.crs_id,c.crs_code,c.crs_title,c.course_type_id,c.total_credits,c.total_marks,
            c.total_stud_enroll,c.reg_start_date,c.reg_end_date,c.academic_batch_id,
            ct.course_type_code,ct.course_type_desc ORDER BY c.crs_code''',
            term=term['semester_id'], batch=term['academic_batch_id'], number=term['semester'], org=student['org_id'], section=section_id)
        counts = {r['crs_id']: r['registered_count'] for r in self.rows('''
            SELECT e.crs_id,COUNT(DISTINCT e.student_id) AS registered_count FROM cudos_map_courseto_student e
            JOIN cudos_master_type_details st ON st.mt_details_id=e.status
            JOIN cudos_master_type mt ON mt.master_type_id=st.master_type_id
            WHERE e.academic_batch_id=:batch AND e.semester_id=:term
            AND mt.master_type_name='student_registration_status' AND st.mt_details_name<>'Unregistered'
            GROUP BY e.crs_id''', batch=term['academic_batch_id'], term=term['semester_id'])}
        lab_courses = {r['crs_id'] for r in self.rows('''SELECT DISTINCT i.crs_id
            FROM cudos_map_courseto_course_instructor i JOIN cudos_master_type_details d ON d.mt_details_id=i.section_id
            JOIN cudos_master_type mt ON mt.master_type_id=d.master_type_id AND mt.master_type_alias_name='SECTION'
            WHERE i.academic_batch_id=:batch AND i.semester_id=:number AND d.parent_id>0''',
            batch=term['academic_batch_id'], number=term['semester'])}
        registered = {r['crs_id']: r for r in self.registered(student)}
        limits = self.structures(term)
        now = datetime.now()
        base = self.term(student, student['academic_batch_id'], student['semester_id'])
        for row in rows:
            row['component'] = alias(row['course_type_code'])
            row['registered_count'] = counts.get(row['crs_id'], 0)
            row['seats_available'] = None if row['total_stud_enroll'] is None else max(0, row['total_stud_enroll'] - row['registered_count'])
            row['already_registered'] = row['crs_id'] in registered
            row['section_id'] = section_id
            row['section_name'] = sections[section_id]['section_name']
            row['type_limits'] = limits.get((row['academic_batch_id'], row['semester_id'], row['course_type_id']))
            reason = ''
            if row['academic_batch_id'] != student['academic_batch_id'] and row['component'] != 'OPEN_ELECTIVE':
                continue
            if not window(base, now)['registration_open']:
                reason = window(base, now)['message']
            elif not window(term, now)['registration_open']:
                reason = window(term, now)['message']
            elif row['component'] == 'OPEN_ELECTIVE' and (row['reg_start_date'] or row['reg_end_date']):
                if not row['reg_start_date'] or not row['reg_end_date'] or not row['reg_start_date'] <= now <= row['reg_end_date']:
                    reason = 'The course registration window is closed or not configured.'
            if not reason and not row['type_limits']:
                reason = 'Course-type registration limits are not configured.'
            if not reason and not sections[section_id]['parent_id'] and row['crs_id'] in lab_courses:
                reason = 'Select a lab batch to register this theory-with-lab course.'
            if not reason and row['seats_available'] == 0 and not row['already_registered']:
                reason = 'No seats available.'
            row['unavailable_reason'] = reason
            row['registration_open'] = not reason
        return [r for r in rows if r['academic_batch_id'] == student['academic_batch_id'] or r['component'] == 'OPEN_ELECTIVE']

    def cohort_offerings(self, student, selected_term):
        courses = {}
        base = self.term(student, student['academic_batch_id'], student['semester_id'])
        for batch in self.batches(student):
            other_curriculum = batch['academic_batch_id'] != student['academic_batch_id']
            if other_curriculum and (base.get('other_crclm_elective') or 0) <= 0:
                continue
            terms = self.terms(student, batch['academic_batch_id'])
            for candidate in terms:
                if candidate.get('semester_code') != selected_term.get('semester_code'):
                    continue
                term = self.term(student, batch['academic_batch_id'], candidate['semester_id'])
                for section in self.sections(term):
                    for row in self.offerings(student, term, section['section_id']):
                        if other_curriculum and row['component'] != 'OPEN_ELECTIVE':
                            continue
                        option = {key: row[key] for key in ('section_id', 'section_name', 'registration_open', 'unavailable_reason')}
                        if row['crs_id'] not in courses:
                            courses[row['crs_id']] = {**row, 'semester': term['semester'], 'curriculum_name': batch['academic_batch_desc'] or batch['academic_batch_code'], 'section_options': []}
                        course = courses[row['crs_id']]
                        course['section_options'].append(option)
                        if row['registration_open']:
                            course['registration_open'] = True
                            course['unavailable_reason'] = ''
        return sorted(courses.values(), key=lambda row: (row['curriculum_name'], row['crs_code']))

    def catalog(self, payload):
        student = self.student(payload.student_id)
        mode = self.settings(student)
        term = self.term(student, payload.academic_batch_id, payload.semester_id)
        base = self.term(student, student['academic_batch_id'], student['semester_id'])
        status = window(base if payload.all_curricula else term)
        if not window(base)['registration_open']:
            status = window(base)
        return {**status, 'mode': mode, 'total_limit': base['total_crs_enroll'],
            'own_elective_limit': base['own_crclm_elective'], 'other_elective_limit': base['other_crclm_elective'],
            'sections': self.sections(term), 'registered_courses': self.registered(student),
            'course_list': self.cohort_offerings(student, term) if payload.all_curricula else (self.offerings(student, term, payload.section_id) if payload.section_id else [])}

    def lock_context(self, student, batch_id, term_id):
        # Same term -> course lock order as the faculty configuration writer.
        # Sorted terms avoid deadlocks for students registering in each other's curriculum.
        terms = {}
        for b, t in sorted({(student['academic_batch_id'], student['semester_id']), (batch_id, term_id)}, key=lambda p: p[1]):
            terms[t] = self.term(student, b, t, lock=True)
        return terms[student['semester_id']], terms[term_id]

    def save(self, payload):
        try:
            # Avoid a REPEATABLE READ snapshot taken before waiting on faculty/seat locks.
            self.db.connection(execution_options={'isolation_level': 'READ COMMITTED'})
            student = self.student(payload.student_id, lock=True)
            mode = self.settings(student)
            # Validate list-screen scope, then lock all offering terms in a stable order.
            selected_term = self.term(student, payload.academic_batch_id, payload.semester_id)
            choices = [choice.model_dump() for choice in payload.course_selections] if payload.course_selections else [
                dict(crs_id=course, academic_batch_id=payload.academic_batch_id,
                     semester_id=payload.semester_id, section_id=payload.section_id) for course in payload.course_ids]
            scopes = {(student['academic_batch_id'], student['semester_id'])}
            scopes.update((choice['academic_batch_id'], choice['semester_id']) for choice in choices)
            terms = {}
            structures = {}
            for batch_id, term_id in sorted(scopes, key=lambda pair: pair[1]):
                term = self.term(student, batch_id, term_id, lock=True)
                if term.get('semester_code') != selected_term.get('semester_code'):
                    fail('A selected course does not match the selected term code.', 422)
                terms[(batch_id, term_id)] = term
                structures.update(self.structures(term))
            base = terms[(student['academic_batch_id'], student['semester_id'])]
            for term in terms.values():
                self.rows('''SELECT crs_id FROM iems_courses WHERE academic_batch_id=:batch
                    AND semester=:number AND org_id=:org ORDER BY crs_id FOR UPDATE''',
                    batch=term['academic_batch_id'], number=term['semester'], org=student['org_id'])
            selected = []
            offerings = {}
            for choice in choices:
                term = terms[(choice['academic_batch_id'], choice['semester_id'])]
                key = (choice['academic_batch_id'], choice['semester_id'], choice['section_id'])
                if key not in offerings:
                    offerings[key] = {r['crs_id']: r for r in self.offerings(student, term, choice['section_id'])}
                row = offerings[key].get(choice['crs_id'])
                if not row:
                    fail('A selected course is not offered for this curriculum, semester and section.', 422)
                if row['unavailable_reason']:
                    fail(f'{row["crs_code"]}: {row["unavailable_reason"]}')
                if not row['already_registered']:
                    selected.append(row)
            existing = self.registered(student)
            validate_selection(existing, selected, base, structures, mode)
            status = self.one('''SELECT d.mt_details_id FROM cudos_master_type_details d
                JOIN cudos_master_type t ON t.master_type_id=d.master_type_id
                WHERE t.master_type_name='student_registration_status' AND d.mt_details_name='Registered' ''')
            if not status:
                fail('The Registered master status is not configured.')
            for row in selected:
                term = terms[(row['academic_batch_id'], row['semester_id'])]
                section = next(r for r in self.sections(term) if r['section_id'] == row['section_id'])
                self.db.execute(text('''INSERT INTO cudos_map_courseto_student
                    (academic_batch_id,semester_id,crs_id,section_id,batch_id,student_id,std_crclm_id,std_term_id,
                     status,created_date,crs_reg_flag,opel_crs_flag)
                    VALUES (:batch,:term,:course,:section,:lab,:student,:base,:base_term,:status,:now,1,:oe)'''),
                    dict(batch=term['academic_batch_id'], term=term['semester_id'], course=row['crs_id'],
                         section=section['parent_id'] or row['section_id'],
                         lab=row['section_id'] if section['parent_id'] else None,
                         student=student['student_id'], base=student['academic_batch_id'], base_term=student['semester_id'],
                         status=status['mt_details_id'], now=datetime.now(), oe=int(row['component']=='OPEN_ELECTIVE')))
            self.db.commit()
            return {'registered_count': len(selected), 'message': 'Courses registered successfully.' if selected else 'Courses are already registered.'}
        except Exception:
            self.db.rollback()
            raise

    def unregister(self, payload):
        try:
            self.db.connection(execution_options={'isolation_level': 'READ COMMITTED'})
            student = self.student(payload.student_id, lock=True)
            self.settings(student)
            # Read the identity first; all enrollment writers lock this student first.
            rows = self.registered(student)
            row = next((r for r in rows if r['mcstd_id'] == payload.registration_id), None)
            if not row:
                fail('Registration not found for this student.', 404)
            base, term = self.lock_context(student, row['academic_batch_id'], row['semester_id'])
            self.rows('SELECT crs_id FROM iems_courses WHERE crs_id=:id FOR UPDATE', id=row['crs_id'])
            if row['crs_reg_flag'] != 1:
                fail('Faculty-assigned courses cannot be unregistered by the student.', 403)
            for scope in (base, term):
                state = window(scope)
                if not state['registration_open']:
                    fail(state['message'])
            course = self.one('SELECT reg_start_date,reg_end_date FROM iems_courses WHERE crs_id=:id', id=row['crs_id'])
            if alias(row['course_type_code']) == 'OPEN_ELECTIVE' and (course['reg_start_date'] or course['reg_end_date']):
                if not course['reg_start_date'] or not course['reg_end_date'] or not course['reg_start_date'] <= datetime.now() <= course['reg_end_date']:
                    fail('The course registration window is closed.')
            self.db.execute(text('DELETE FROM cudos_map_courseto_student WHERE mcstd_id=:id AND student_id=:student AND crs_reg_flag=1'),
                dict(id=payload.registration_id, student=student['student_id']))
            self.db.commit()
            return {'message': 'Course unregistered successfully.'}
        except Exception:
            self.db.rollback()
            raise
