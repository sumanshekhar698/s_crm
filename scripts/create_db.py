import os
from pathlib import Path

import MySQLdb
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DB_NAME = os.environ.get("DB_NAME", "crm_db")

database = MySQLdb.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
)

cursor = database.cursor()

cursor.execute(
    f"""
    CREATE DATABASE IF NOT EXISTS {DB_NAME}
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    """
)

print(f"Database '{DB_NAME}' is ready!")

cursor.close()
database.close()

# uv run python scripts/create_db.py
