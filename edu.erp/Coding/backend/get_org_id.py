from app.core.database import engine
from sqlalchemy import text

print("--- Valid Org IDs ---")
with engine.connect() as conn:
    try:
        orgs = conn.execute(text("SELECT DISTINCT org_id FROM iems_department LIMIT 5")).fetchall()
        for o in orgs:
            print(f"Org ID: {o[0]}")
    except Exception as e:
        print("Could not query iems_department:", e)

    try:
        orgs2 = conn.execute(text("SELECT DISTINCT org_id FROM erp_users LIMIT 5")).fetchall()
        for o in orgs2:
            print(f"User Org ID: {o[0]}")
    except Exception as e:
        pass
