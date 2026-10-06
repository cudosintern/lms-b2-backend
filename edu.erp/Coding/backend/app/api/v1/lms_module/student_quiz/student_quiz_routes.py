# Student Quiz routes - student-facing endpoints for My Quiz feature
# These wrap the existing manage-quiz student endpoints into a dedicated student prefix.
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.utils.http_return_helper import returnSuccess
from typing import Optional, Any
from .student_quiz_schema import StudentQuizSubmitRequest, StudentQuizIdentity, StudentQuizListRequest, StudentQuizSaveRequest
from .quiz_rules import availability, india_now, calculate_score
import random

router = APIRouter(tags=["Student Quiz"])


@router.get("/dropdowns")
def get_student_quiz_dropdowns(
    student_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    # Catalog courses must not depend on a student enrollment row or quiz assignment.
    batches = db.execute(text("""
        SELECT ab.academic_batch_id, ab.academic_batch_desc
        FROM iems_students s
        JOIN iems_academic_batch ab ON ab.academic_batch_id = s.academic_batch_id
        WHERE s.student_id = :student_id
        UNION
        SELECT ab.academic_batch_id, ab.academic_batch_desc
        FROM cudos_map_courseto_student cms
        JOIN iems_academic_batch ab ON ab.academic_batch_id = cms.academic_batch_id
        WHERE cms.student_id = :student_id
    """), {"student_id": student_id}).mappings().all()
    terms = db.execute(text("""
        SELECT sem.semester_id, sem.semester, sem.academic_batch_id
        FROM iems_semester sem
        WHERE sem.academic_batch_id IN (
            SELECT academic_batch_id FROM iems_students WHERE student_id=:student_id
            UNION SELECT academic_batch_id FROM cudos_map_courseto_student WHERE student_id=:student_id
        )
        ORDER BY sem.semester_id
    """), {"student_id": student_id}).mappings().all()
    enrollments = db.execute(text("""
        SELECT DISTINCT cms.academic_batch_id, cms.semester_id, cms.crs_id,
            c.crs_code, c.crs_title, cms.section_id,
            sec.mt_details_name AS section_name
        FROM cudos_map_courseto_student cms
        JOIN iems_students s ON s.student_id = cms.student_id

        JOIN iems_courses c ON c.crs_id = cms.crs_id
        LEFT JOIN cudos_master_type_details sec ON sec.mt_details_id = cms.section_id
        WHERE cms.student_id = :student_id
        ORDER BY c.crs_code, cms.section_id
    """), {"student_id": student_id}).mappings().all()
    courses = db.execute(text("""
        SELECT DISTINCT c.academic_batch_id, sem.semester_id, c.crs_id,
            c.crs_code, c.crs_title
        FROM iems_courses c
        JOIN iems_semester sem ON sem.academic_batch_id = c.academic_batch_id
            AND sem.semester = c.semester
        WHERE c.academic_batch_id IN (
            SELECT academic_batch_id FROM iems_students WHERE student_id=:student_id
            UNION SELECT academic_batch_id FROM cudos_map_courseto_student WHERE student_id=:student_id
        )
        ORDER BY c.crs_code
    """), {"student_id": student_id}).mappings().all()
    return returnSuccess({
        "batches": [dict(row) for row in batches],
        "semesters": [dict(row) for row in terms],
        "enrollments": [dict(row) for row in enrollments],
        "courses": [dict(row) for row in courses],
    })


# ── My Quizzes: list all quizzes shared to this student ──────────────────────
@router.get("/my-quizzes")
def get_student_quizzes(
    student_id: int = Query(..., gt=0, description="student_id of the logged-in student"),
    academic_batch_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    crs_id: Optional[int] = Query(default=None),
    section_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    filters = """WHERE qs.ssd_id = :student_id
        AND EXISTS (SELECT 1 FROM iems_students s WHERE s.student_id = :student_id)
        AND EXISTS (SELECT 1 FROM cudos_map_courseto_student cms
            WHERE cms.student_id = :student_id
              AND cms.academic_batch_id = q.academic_batch_id
              AND cms.semester_id = q.semester_id AND cms.crs_id = q.crs_id
              AND (:section_id IS NULL OR cms.section_id = :section_id))"""
    params: dict[str, Any] = {"student_id": student_id, "section_id": section_id}

    if academic_batch_id is not None:
        filters += " AND q.academic_batch_id = :academic_batch_id"
        params["academic_batch_id"] = academic_batch_id
    if semester_id is not None:
        filters += " AND q.semester_id = :semester_id"
        params["semester_id"] = semester_id
    if crs_id is not None:
        filters += " AND q.crs_id = :crs_id"
        params["crs_id"] = crs_id
    if section_id is not None:
        # Direct student assignments can exist without quiz-level section rows.
        # If section restrictions exist, enforce them; otherwise the student's
        # course enrollment above supplies the selected section.
        filters += """ AND (
            NOT EXISTS (SELECT 1 FROM lms_quiz_section_mapping qsec
                WHERE qsec.quiz_id = q.quiz_id)
            OR EXISTS (SELECT 1 FROM lms_quiz_section_mapping qsec
                WHERE qsec.quiz_id = q.quiz_id AND qsec.section_id = :section_id))"""

    query = f"""
        SELECT
            qs.qs_map_id,
            qs.quiz_id,
            qs.ssd_id,
            qs.student_usn,
            qs.q_secured_marks,
            qs.secured_marks,
            qs.is_submitted,
            qs.accept_rework_flag,
            qs.rework_comment,
            qs.remarks,
            q.show_date, q.show_time, qs.answer_key_flag,
            q.quiz_title,
            q.quiz_description,
            q.quiz_instruction,
            q.quiz_date,
            q.quiz_time,
            q.duration,
            q.marks_flag,
            q.practice_quiz,
            q.file_name,
            q.file_path,
            COALESCE(c.crs_code, '') AS crs_code,
            COALESCE(c.crs_title, '') AS crs_title,
            (SELECT COUNT(*) FROM lms_quiz_questions qq WHERE qq.quiz_id = q.quiz_id) AS question_count,
            (SELECT COUNT(DISTINCT qa.qq_id) FROM lms_quiz_student_answer qa
             WHERE qa.quiz_id = q.quiz_id AND qa.ssd_id = qs.ssd_id) AS answered_count
        FROM lms_quiz_student_mapping qs
        JOIN lms_manage_quiz q ON q.quiz_id = qs.quiz_id
        LEFT JOIN iems_courses c ON c.crs_id = q.crs_id
        {filters}
        ORDER BY qs.quiz_id DESC
    """
    rows = db.execute(text(query), params).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        try:
            state = availability(item, item)
        except ValueError as exc:
            state = {"can_start": False, "unavailable_reason": str(exc), "visible": True}
        if state.pop("visible"):
            item.update(state)
            items.append(item)
    return returnSuccess({"items": items, "total": len(items)})



# JSON payload alternatives for demo clients; GET remains available.
@router.post('/dropdowns')
def dropdowns_payload(payload: StudentQuizIdentity, db: Session = Depends(get_db)):
    return get_student_quiz_dropdowns(payload.student_id, db)

@router.post('/my-quizzes')
def quizzes_payload(payload: StudentQuizListRequest, db: Session = Depends(get_db)):
    return get_student_quizzes(payload.student_id, payload.academic_batch_id,
                              payload.semester_id, payload.crs_id, payload.section_id, db)

def _assigned(db, quiz_id, student_id, lock=False):
    quiz = db.execute(text('SELECT * FROM lms_manage_quiz WHERE quiz_id=:qid'),
                      {'qid': quiz_id}).mappings().first()
    mapping = db.execute(text('SELECT * FROM lms_quiz_student_mapping '
                              'WHERE quiz_id=:qid AND ssd_id=:sid' + (' FOR UPDATE' if lock else '')),
                         {'qid': quiz_id, 'sid': student_id}).mappings().first()
    if not quiz or not mapping:
        raise HTTPException(404, 'Quiz is not assigned to this student')
    enrolled = db.execute(text('''
        SELECT 1 FROM cudos_map_courseto_student cms
        JOIN iems_students s ON s.student_id = cms.student_id
        WHERE cms.student_id=:sid AND cms.academic_batch_id=:batch
          AND cms.semester_id=:term AND cms.crs_id=:course
          AND (
              NOT EXISTS (SELECT 1 FROM lms_quiz_section_mapping sec WHERE sec.quiz_id=:qid)
              OR EXISTS (SELECT 1 FROM lms_quiz_section_mapping sec
                         WHERE sec.quiz_id=:qid AND sec.section_id=cms.section_id))
        LIMIT 1
    '''), {'sid': student_id, 'qid': quiz_id, 'batch': quiz['academic_batch_id'],
          'term': quiz['semester_id'], 'course': quiz['crs_id']}).first()
    if not enrolled:
        raise HTTPException(403, 'Student is not enrolled in the assigned course and section')
    return dict(quiz), dict(mapping)

def _state(quiz, mapping):
    try:
        return availability(quiz, mapping)
    except ValueError as exc:
        raise HTTPException(409, str(exc))

def _questions(db, quiz_id, student_id, reveal=False):
    questions = [dict(q) for q in db.execute(text('''
        SELECT qq_id, question, question_type, marks FROM lms_quiz_questions
        WHERE quiz_id=:qid ORDER BY qq_id
    '''), {'qid': quiz_id}).mappings()]
    for question in questions:
        fields = ', is_answer, option_explanation' if reveal else ''
        question['options'] = [dict(o) for o in db.execute(text(
            'SELECT qq_option_id, option_value' + fields +
            ' FROM lms_quiz_que_options WHERE qq_id=:qqid ORDER BY qq_option_id'),
            {'qqid': question['qq_id']}).mappings()]
        saved_answers = list(db.execute(text('''
            SELECT qq_option_id, answer_text FROM lms_quiz_student_answer
            WHERE quiz_id=:qid AND ssd_id=:sid AND qq_id=:qqid
        '''), {'qid': quiz_id, 'sid': student_id, 'qqid': question['qq_id']}).mappings())
        question['selected_option_ids'] = [a['qq_option_id'] for a in saved_answers
                                            if a['qq_option_id'] is not None]
        question['answer_text'] = next((a['answer_text'] for a in saved_answers
                                        if a['answer_text'] is not None), '')
    return questions

@router.post('/{quiz_id}/start')
def start_student_quiz(quiz_id: int, payload: StudentQuizIdentity, db: Session = Depends(get_db)):
    quiz, mapping = _assigned(db, quiz_id, payload.student_id, lock=True)
    state = _state(quiz, mapping)
    if not state['can_start']:
        raise HTTPException(409, state['unavailable_reason'])
    questions = _questions(db, quiz_id, payload.student_id)
    if not questions:
        raise HTTPException(409, 'Quiz has no questions')
    existing = db.execute(text('SELECT quiz_log_id FROM lms_quiz_start_log '
                               'WHERE quiz_id=:qid AND ssd_id=:sid LIMIT 1'),
                          {'qid': quiz_id, 'sid': payload.student_id}).first()
    if not existing:
        db.execute(text('''
            INSERT INTO lms_quiz_start_log
                (quiz_id, ssd_id, student_usn, academic_batch_id, semester_id, crs_id,
                 quiz_from_web, quiz_start_datetime, created_datetime)
            VALUES (:qid, :sid, :usn, :batch, :term, :course, 1, :now, :now)
        '''), {'qid': quiz_id, 'sid': payload.student_id,
               'usn': mapping.get('student_usn') or '', 'now': india_now(),
               'batch': quiz['academic_batch_id'], 'term': quiz['semester_id'], 'course': quiz['crs_id']})
    # A stable shuffle also keeps the order unchanged after resuming.
    rng = random.Random(f'{quiz_id}:{payload.student_id}')
    if quiz.get('shuffle_questions') == 1:
        rng.shuffle(questions)
    if quiz.get('shuffle_options') == 1:
        for question in questions:
            rng.shuffle(question['options'])
    db.commit()
    return returnSuccess({'quiz': quiz, 'questions': questions, **state})

def _validate_answers(db, quiz_id, answers):
    seen = set()
    for answer in answers:
        if answer.qq_id in seen:
            raise HTTPException(422, 'Duplicate question in answers')
        seen.add(answer.qq_id)
        question = db.execute(text('SELECT question_type FROM lms_quiz_questions '
                                   'WHERE quiz_id=:qid AND qq_id=:qqid'),
                              {'qid': quiz_id, 'qqid': answer.qq_id}).mappings().first()
        if not question:
            raise HTTPException(422, 'Question does not belong to this quiz')
        valid = set(db.execute(text('SELECT qq_option_id FROM lms_quiz_que_options WHERE qq_id=:qqid'),
                               {'qqid': answer.qq_id}).scalars())
        chosen = answer.option_ids()
        if question['question_type'] == 3:
            if chosen:
                raise HTTPException(422, 'Short-answer question accepts text only')
        elif answer.answer_text is not None and answer.answer_text.strip():
            raise HTTPException(422, 'Choice question accepts options only')
        if not chosen.issubset(valid):
            raise HTTPException(422, 'Option does not belong to this question')
        if question['question_type'] == 2 and len(chosen) > 1:
            raise HTTPException(422, 'Single-answer question accepts only one option')

def _save_answers(db, quiz_id, student_id, mapping, answers):
    for answer in answers:
        db.execute(text('DELETE FROM lms_quiz_student_answer '
                        'WHERE quiz_id=:qid AND ssd_id=:sid AND qq_id=:qqid'),
                   {'qid': quiz_id, 'sid': student_id, 'qqid': answer.qq_id})
        if answer.answer_text is not None and answer.answer_text.strip():
            db.execute(text('''
                INSERT INTO lms_quiz_student_answer
                    (quiz_id, ssd_id, student_usn, qq_id, qq_option_id, answer_text, created_by, created_date)
                VALUES (:qid, :sid, :usn, :qqid, NULL, :answer, :sid, :now)
            '''), {'qid': quiz_id, 'sid': student_id, 'usn': mapping.get('student_usn') or '',
                   'qqid': answer.qq_id, 'answer': answer.answer_text, 'now': india_now()})
        for option_id in answer.option_ids():
            db.execute(text('''
                INSERT INTO lms_quiz_student_answer
                    (quiz_id, ssd_id, student_usn, qq_id, qq_option_id, created_by, created_date)
                VALUES (:qid, :sid, :usn, :qqid, :oid, :sid, :now)
            '''), {'qid': quiz_id, 'sid': student_id, 'usn': mapping.get('student_usn') or '',
                   'qqid': answer.qq_id, 'oid': option_id, 'now': india_now()})

def _started(db, quiz_id, student_id):
    if not db.execute(text('SELECT 1 FROM lms_quiz_start_log WHERE quiz_id=:qid AND ssd_id=:sid LIMIT 1'),
                      {'qid': quiz_id, 'sid': student_id}).first():
        raise HTTPException(409, 'Start the quiz before saving answers')

@router.post('/{quiz_id}/answers')
def save_student_answer(quiz_id: int, payload: StudentQuizSaveRequest, db: Session = Depends(get_db)):
    quiz, mapping = _assigned(db, quiz_id, payload.student_id, lock=True)
    state = _state(quiz, mapping)
    if not state['can_start']:
        raise HTTPException(409, state['unavailable_reason'])
    _started(db, quiz_id, payload.student_id)
    _validate_answers(db, quiz_id, [payload.answer])
    _save_answers(db, quiz_id, payload.student_id, mapping, [payload.answer])
    db.commit()
    return returnSuccess({'remaining_seconds': state['remaining_seconds']})

@router.post('/{quiz_id}/submit')
def submit_student_quiz(quiz_id: int, payload: StudentQuizSubmitRequest, db: Session = Depends(get_db)):
    quiz, mapping = _assigned(db, quiz_id, payload.student_id, lock=True)
    state = _state(quiz, mapping)
    _started(db, quiz_id, payload.student_id)
    if mapping.get('is_submitted') == 1:
        raise HTTPException(409, 'Quiz already submitted')
    # At expiry finalize persisted answers, without accepting late answer changes.
    expired = state['unavailable_reason'] == 'Quiz has ended'
    if not state['can_start'] and not expired:
        raise HTTPException(409, state['unavailable_reason'])
    _validate_answers(db, quiz_id, payload.answers)
    try:
        if not expired:
            _save_answers(db, quiz_id, payload.student_id, mapping, payload.answers)
        questions = _questions(db, quiz_id, payload.student_id, reveal=True)
        if not expired and any(
                not (q['answer_text'].strip() if q['question_type'] == 3 else q['selected_option_ids'])
                for q in questions):
            raise HTTPException(422, 'All questions are mandatory. Please answer every question.')
        correct = {q['qq_id']: {o['qq_option_id'] for o in q['options'] if o['is_answer'] == 1}
                   for q in questions}
        selected = {q['qq_id']: set(q['selected_option_ids']) for q in questions}
        score = calculate_score(questions, correct, selected)
        db.execute(text('UPDATE lms_quiz_student_mapping SET is_submitted=1, secured_marks=:score '
                        'WHERE quiz_id=:qid AND ssd_id=:sid'),
                   {'score': score, 'qid': quiz_id, 'sid': payload.student_id})
        db.commit()
        return returnSuccess({'quiz_id': quiz_id, 'student_id': payload.student_id, 'score': score},
                             'Quiz submitted successfully')
    except Exception:
        db.rollback()
        raise

@router.post('/{quiz_id}/answer-key')
def student_answer_key(quiz_id: int, payload: StudentQuizIdentity, db: Session = Depends(get_db)):
    quiz, mapping = _assigned(db, quiz_id, payload.student_id)
    if mapping.get('is_submitted') != 1 or mapping.get('answer_key_flag') != 1:
        raise HTTPException(403, 'Answer key has not been released for this student')
    return returnSuccess({'questions': _questions(db, quiz_id, payload.student_id, reveal=True)})

@router.get('/{quiz_id}/file')
@router.get('/{quiz_id}/download')
def download_quiz_file(quiz_id: int, student_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    import os
    quiz, mapping = _assigned(db, quiz_id, student_id)
    if not _state(quiz, mapping)['visible']:
        raise HTTPException(403, 'Quiz is not yet visible')
    if not quiz.get('file_path') or not os.path.isfile(quiz['file_path']):
        raise HTTPException(404, 'File not found on server')
    return FileResponse(path=quiz['file_path'], filename=quiz.get('file_name'))
