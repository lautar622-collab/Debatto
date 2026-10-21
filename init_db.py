import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE = os.path.join(INSTANCE_DIR, "debatto.db")
SCHEMA = os.path.join(BASE_DIR, "schema.sql")


def init_db():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    connection = sqlite3.connect(DATABASE)

    try:
        with open(SCHEMA, "r", encoding="utf-8") as file:
            schema = file.read()
            connection.executescript(schema)
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
