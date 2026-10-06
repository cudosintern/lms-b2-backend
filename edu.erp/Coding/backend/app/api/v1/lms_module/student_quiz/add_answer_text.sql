-- Run once before deploying text-answer support.
ALTER TABLE lms_quiz_student_answer ADD COLUMN answer_text TEXT NULL;
