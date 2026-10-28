
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

conninfo = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "missing_person_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

with psycopg.connect(**conninfo) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), version()")
        database_name, version = cur.fetchone()
        print("Connected to:", database_name)
        print("PostgreSQL version:", version.split(",")[0])
