"""Run with the backend virtual environment: python -m unittest discover -s app/api/v1/lms_module/student_quiz -p 'test_*.py'."""
import unittest
from datetime import timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.api.v1.lms_module.student_quiz import student_quiz_routes as routes
from app.api.v1.lms_module.student_quiz.student_quiz_schema import (
    StudentQuizIdentity, StudentQuizSaveRequest, StudentQuizSubmitRequest,
)
from app.api.v1.lms_module.student_quiz.quiz_rules import india_now

class TestStudentQuiz(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.session = Session(self.engine)
        # SQLite has no FOR UPDATE. Production keeps MySQL row locking.
        self.db = self
        self.now = india_now()
        definitions = {
            'lms_manage_quiz': 'quiz_id integer, academic_batch_id integer, semester_id integer, crs_id integer, quiz_date text, quiz_time text, duration text, show_date text, show_time text, shuffle_questions integer, shuffle_options integer',
            'lms_quiz_student_mapping': 'qs_map_id integer, quiz_id integer, ssd_id integer, student_usn text, is_submitted integer, secured_marks real, answer_key_flag integer',
            'iems_students': 'student_id integer, academic_batch_id integer',
            'iems_academic_batch': 'academic_batch_id integer, academic_batch_desc text',
            'iems_semester': 'semester_id integer, academic_batch_id integer, semester integer',
            'iems_courses': 'crs_id integer, academic_batch_id integer, semester integer, crs_code text, crs_title text',
            'cudos_master_type_details': 'mt_details_id integer, mt_details_name text',
            'cudos_map_courseto_student': 'student_id integer, academic_batch_id integer, semester_id integer, crs_id integer, section_id integer',
            'lms_quiz_section_mapping': 'quiz_id integer, section_id integer',
            'lms_quiz_questions': 'qq_id integer, quiz_id integer, question text, question_type integer, marks real',
            'lms_quiz_que_options': 'qq_option_id integer, qq_id integer, option_value text, is_answer integer, option_explanation text',
            'lms_quiz_student_answer': 'quiz_id integer, ssd_id integer, student_usn text, qq_id integer, qq_option_id integer, answer_text text, created_by integer, created_date text',
            'lms_quiz_start_log': 'quiz_log_id integer primary key, quiz_id integer, ssd_id integer, student_usn text, academic_batch_id integer, semester_id integer, crs_id integer, quiz_from_web integer, quiz_start_datetime text, created_datetime text',
        }
        for table, columns in definitions.items():
            self.execute(text(f'CREATE TABLE {table} ({columns})'))
        start = self.now - timedelta(minutes=10)
        self.execute(text('INSERT INTO lms_manage_quiz VALUES (1,1,1,1,:date,:time,"60",NULL,NULL,1,1)'),
                     {'date': start.strftime('%Y-%m-%d'), 'time': start.strftime('%H:%M:%S')})
        for sql in [
            'INSERT INTO lms_quiz_student_mapping VALUES (1,1,7,"USN7",0,NULL,0)',
            'INSERT INTO iems_students VALUES (7,1)',
            'INSERT INTO iems_academic_batch VALUES (1,"Demo batch")',
            'INSERT INTO iems_semester VALUES (40,1,4)',
            'INSERT INTO iems_courses VALUES (91,1,4,"COURSE4","Semester four course")',
            'INSERT INTO cudos_master_type_details VALUES (2,"A")',
            'INSERT INTO cudos_map_courseto_student VALUES (7,1,1,1,2)',
            'INSERT INTO lms_quiz_section_mapping VALUES (1,2)',
            'INSERT INTO lms_quiz_questions VALUES (10,1,"Choose both",1,5)',
            'INSERT INTO lms_quiz_questions VALUES (11,1,"Choose one",2,3)',
            'INSERT INTO lms_quiz_que_options VALUES (20,10,"A",1,"A explanation")',
            'INSERT INTO lms_quiz_que_options VALUES (21,10,"B",1,"B explanation")',
            'INSERT INTO lms_quiz_que_options VALUES (22,10,"C",0,"")',
            'INSERT INTO lms_quiz_que_options VALUES (23,11,"D",1,"")',
        ]:
            self.execute(text(sql))
        self.commit()

    def execute(self, statement, params=None):
        return self.session.execute(text(str(statement).replace(' FOR UPDATE', '')), params or {})

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def start(self, student_id=7):
        return routes.start_student_quiz(1, StudentQuizIdentity(student_id=student_id), self.db)['data']

    def save(self, options):
        return routes.save_student_answer(1, StudentQuizSaveRequest(
            student_id=7, answer={'qq_id':10, 'qq_option_ids':options}), self.db)

    def submit(self, answers=None):
        return routes.submit_student_quiz(1, StudentQuizSubmitRequest(student_id=7, answers=answers or []), self.db)['data']

    def test_catalog_courses_without_student_enrollment(self):
        self.execute(text('DELETE FROM cudos_map_courseto_student'))
        data = routes.get_student_quiz_dropdowns(7, self.db)['data']
        self.assertEqual(data['enrollments'], [])
        self.assertEqual(len(data['courses']), 1)
        self.assertEqual(data['courses'][0]['semester_id'], 40)
        self.assertEqual(data['courses'][0]['crs_id'], 91)

    def test_direct_assignment_without_quiz_section_mapping(self):
        self.execute(text('DELETE FROM lms_quiz_section_mapping'))
        self.assertEqual(len(self.start()['questions']), 2)
        with self.assertRaises(HTTPException):
            self.start(8)

    def test_explicit_quiz_section_restriction(self):
        self.execute(text('UPDATE lms_quiz_section_mapping SET section_id=3'))
        with self.assertRaises(HTTPException):
            self.start()

    def test_assignment_and_schedule(self):
        with self.assertRaises(HTTPException):
            self.start(8)
        future = self.now + timedelta(days=1)
        self.execute(text('UPDATE lms_manage_quiz SET quiz_date=:d'), {'d': future.strftime('%Y-%m-%d')})
        with self.assertRaises(HTTPException):
            self.start()

    def test_resume_and_no_answer_leak(self):
        first = self.start()
        self.save([20,21])
        resumed = self.start()
        q = next(q for q in resumed['questions'] if q['qq_id']==10)
        self.assertEqual(set(q['selected_option_ids']), {20,21})
        self.assertNotIn('is_answer', q['options'][0])
        self.assertNotIn('option_explanation', q['options'][0])
        self.assertLessEqual(resumed['remaining_seconds'], first['remaining_seconds'])
        self.assertEqual(self.execute(text('SELECT COUNT(*) FROM lms_quiz_start_log')).scalar(), 1)

    def test_validation_and_exact_set_scoring(self):
        self.start()
        with self.assertRaises(HTTPException):
            self.save([23])
        self.save([20])
        self.assertEqual(self.submit([{'qq_id':11,'qq_option_ids':[23]}])['score'], 3)
        with self.assertRaises(HTTPException):
            self.submit()

    def test_clear_full_score_and_answer_key(self):
        self.start()
        self.save([20])
        self.save([])
        self.assertEqual(self.execute(text('SELECT COUNT(*) FROM lms_quiz_student_answer')).scalar(), 0)
        self.assertEqual(self.submit([{'qq_id':10,'qq_option_ids':[20,21]}, {'qq_id':11,'qq_option_ids':[23]}])['score'], 8)
        with self.assertRaises(HTTPException):
            routes.student_answer_key(1, StudentQuizIdentity(student_id=7), self.db)
        self.execute(text('UPDATE lms_quiz_student_mapping SET answer_key_flag=1'))
        result = routes.student_answer_key(1, StudentQuizIdentity(student_id=7), self.db)['data']
        self.assertIn('is_answer', result['questions'][0]['options'][0])

    def test_late_submission_finalizes_saved_answers(self):
        self.start()
        self.save([20,21])
        self.execute(text('UPDATE lms_manage_quiz SET quiz_date="2000-01-01"'))
        with self.assertRaises(HTTPException):
            self.save([22])
        self.assertEqual(self.submit([{'qq_id':10,'qq_option_ids':[22]}])['score'], 5)

    def test_all_questions_required_and_blank_text_rejected(self):
        self.execute(text('INSERT INTO lms_quiz_questions VALUES (12,1,"Explain",3,2)'))
        self.start()
        with self.assertRaises(HTTPException) as error:
            self.submit([{'qq_id':10,'qq_option_ids':[20,21]},
                         {'qq_id':11,'qq_option_ids':[23]}, {'qq_id':12,'answer_text':'  '}])
        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(self.execute(text('SELECT is_submitted FROM lms_quiz_student_mapping')).scalar(), 0)

    def test_text_answer_save_resume_clear_and_submit(self):
        self.execute(text('INSERT INTO lms_quiz_questions VALUES (12,1,"Explain",3,2)'))
        self.start()
        def save_text(value):
            routes.save_student_answer(1, StudentQuizSaveRequest(
                student_id=7, answer={'qq_id':12,'answer_text':value}), self.db)
        save_text('A database stores data.\nSecond line.')
        question = next(q for q in self.start()['questions'] if q['qq_id'] == 12)
        self.assertEqual(question['answer_text'], 'A database stores data.\nSecond line.')
        self.assertEqual(question['selected_option_ids'], [])
        save_text('')
        self.assertEqual(next(q for q in self.start()['questions'] if q['qq_id'] == 12)['answer_text'], '')
        self.assertEqual(self.submit([{'qq_id':10,'qq_option_ids':[20,21]},
                                     {'qq_id':11,'qq_option_ids':[23]},
                                     {'qq_id':12,'answer_text':'My answer'}])['score'], 8)

    def test_true_false_rejects_multiple_options(self):
        self.execute(text('INSERT INTO lms_quiz_que_options VALUES (24,11,"False",0,"")'))
        self.start()
        with self.assertRaises(HTTPException):
            routes.save_student_answer(1, StudentQuizSaveRequest(
                student_id=7, answer={'qq_id':11,'qq_option_ids':[23,24]}), self.db)

if __name__ == '__main__':
    unittest.main()
