import pymysql
import os
from dotenv import load_dotenv

load_dotenv(".env")
connection = pymysql.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=os.getenv("DB_USERNAME", "root"),
    password=os.getenv("DB_PASSWORD", "chaitra@09"),
    port=int(os.getenv("DB_PORT", 3306))
)

with connection.cursor() as cursor:
    cursor.execute("SHOW DATABASES;")
    for row in cursor.fetchall():
        print(row[0])
