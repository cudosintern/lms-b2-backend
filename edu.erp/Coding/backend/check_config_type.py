from app.core.database import engine
from sqlalchemy import text

print("Checking config_type table...")
try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM config_type LIMIT 5")).fetchall()
        print(f"Found {len(res)} rows in config_type.")
        if len(res) == 0:
            print("Table is empty. Inserting sample data...")
            conn.execute(text("INSERT INTO config_type (name, status) VALUES ('System Theme', 1), ('Default Language', 1), ('Max File Upload Size', 1)"))
            conn.commit()
            print("Sample data inserted!")
        for r in conn.execute(text("SELECT * FROM config_type")).fetchall():
            print(r)
except Exception as e:
    print("Error:", e)
    print("Table likely doesn't exist. Creating it now...")
    try:
        with engine.connect() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS config_type (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                status INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
            """))
            conn.commit()
            print("Table created. Inserting sample data...")
            conn.execute(text("INSERT INTO config_type (name, status) VALUES ('System Theme', 1), ('Default Language', 1), ('Max File Upload Size', 1)"))
            conn.commit()
            print("Sample data inserted successfully.")
    except Exception as e2:
        print("Failed to create table:", e2)
