from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

tables = ["curriculum", "iems_curriculum", "mentoring_group", "curriculum_mentor_map", "mentee_group_map", "iems_department", "iems_program"]

for t in tables:
    print(f"--- {t} ---")
    try:
        res = db.execute(text(f"DESCRIBE {t}")).fetchall()
        for r in res:
            print(r)
    except Exception as e:
        print("Error:", e)
