from app.core.database import engine
from sqlalchemy import text

tables = ["iems_department", "iems_program", "erp_users"]
with engine.connect() as conn:
    for t in tables:
        try:
            res = conn.execute(text(f"SHOW CREATE TABLE {t}")).fetchone()
            print(res[1])
        except Exception as e:
            print(f"Error for {t}: {e}")
