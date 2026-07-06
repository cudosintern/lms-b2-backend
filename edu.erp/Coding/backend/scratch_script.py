from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
sql1 = """
INSERT INTO iems_program (
    pgm_id, pgm_title, pgm_acronym, dept_id, pgmtype_id, status, org_id, total_credits, lateral_entry_credits
) VALUES (
    1, 'BE in AI', 'B.E in AI', 73, 233, 1, 1, 200, 0
) ON DUPLICATE KEY UPDATE pgm_title='BE in AI';
"""

sql2 = """
INSERT INTO iems_academic_batch (
    academic_batch_id, academic_batch_code, academic_batch_desc, dept_id, pgm_id, status, created_by, academic_batch_owner, start_year, end_year, total_credits, lateral_entry_credits, is_tw_course, total_terms, academic_batch_release_status, first_year_flag, oe_pi_flag, clo_bl_flag
) VALUES (
    1, 'AB2024AI', 'Sunway BE in AI JAN 2024', 73, 1, 1, 1, 1, 2024, 2028, 160, 120, 0, 8, 1, 1, 1, 0
) ON DUPLICATE KEY UPDATE status=1, academic_batch_desc='Sunway BE in AI JAN 2024';
"""

try:
    db.execute(text(sql1))
    db.execute(text(sql2))
    db.commit()
    print("Successfully inserted program and curriculum for pgm_id=1, dept_id=73")
except Exception as e:
    db.rollback()
    print("Error program/batch:", e)

sql3 = """
INSERT INTO iems_semester (
    semester_code, academic_batch_id, semester, semester_desc, status, created_by, term_name, semester_duration, total_theory_courses, total_practical_courses, enroll_start_time, enroll_end_time, mapping_date, sem_start_date, sem_end_date, term_max_credits, term_min_credits, min_unit_id, max_unit_id
) VALUES 
    ('SEM1_AI', 1, 1, 'Semester 1', 1, 1, 'Term 1', 4, 0, 0, '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', 0, 0, 0, 0),
    ('SEM2_AI', 1, 2, 'Semester 2', 1, 1, 'Term 2', 4, 0, 0, '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', 0, 0, 0, 0),
    ('SEM3_AI', 1, 3, 'Semester 3', 1, 1, 'Term 3', 4, 0, 0, '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', 0, 0, 0, 0),
    ('SEM4_AI', 1, 4, 'Semester 4', 1, 1, 'Term 4', 4, 0, 0, '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE status=1;
"""
try:
    db.execute(text(sql3))
    db.commit()
    print("Successfully inserted terms")
except Exception as e:
    db.rollback()
    print("Error terms:", e)

