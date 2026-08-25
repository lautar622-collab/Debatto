import sqlite3
import os
DATABASE=os.path.join("instance","debatto.db")
def init_db():
    os.makedirs("instance",exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    with open("schema.sql", "r", encoding="UTF-8") as file:
        schema=file.read()
        connection.executescript(schema)
        connection.commit()
        connection.close()
if __name__ == "__main__":init_db()