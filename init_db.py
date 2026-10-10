import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE=os.path.join("instance","debatto.db")
SCHEMA = os.path.join(BASE_DIR, "schema.sql")
def init_db():
    os.makedirs("instance",exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    try:
        with open(SCHEMA, "r", encoding="UTF-8") as file:
            schema=file.read()
            connection.executescript(schema)
            connection.commit()
    finally:
        connection.close()
if __name__ == "__main__":
    init_db()
    print("DB intialized")