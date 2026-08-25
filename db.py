import sqlite3
import os
DATABASE=os.path.join("instance","debatto.db")
def getdb():
    connection=sqlite3.connect(DATABASE)
    connection.row_factory=sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
