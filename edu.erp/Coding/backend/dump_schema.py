from app.core.database import engine
from sqlalchemy import text

tables_to_check = [
    "iems_curriculum",
    "iems_academic_batch",
    "lms_mentors_group_terms",
    "lms_group_mentors",
    "lms_mentoring_schedule",
    "lms_mentoring_sub_group"
]

with engine.connect() as conn:
    for t in tables_to_check:
        try:
            res = conn.execute(text(f"SHOW CREATE TABLE {t}")).fetchone()
            print(f"--- {t} ---")
            print(res[1])
            print("\n")
        except Exception as e:
            pass
