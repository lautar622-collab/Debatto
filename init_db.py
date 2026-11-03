import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE = os.path.abspath(
    os.environ.get("DATABASE_PATH", os.path.join(INSTANCE_DIR, "debatto.db"))
)
SCHEMA = os.path.join(BASE_DIR, "schema.sql")


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    connection = sqlite3.connect(DATABASE, timeout=30)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")

        with open(SCHEMA, "r", encoding="utf-8") as file:
            connection.executescript(file.read())

        connection.commit()

        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """).fetchall()

        print("DATABASE:", DATABASE, flush=True)
        print("TABLES:", [row[0] for row in tables], flush=True)

    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
