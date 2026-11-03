import os
import sqlite3

from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Railway can point this at its mounted persistent volume, e.g. /data/debatto.db.
# Locally, the database remains in instance/debatto.db.
DATABASE = os.path.abspath(
    os.environ.get("DATABASE_PATH", os.path.join(INSTANCE_DIR, "debatto.db"))
)


def getdb():
    if "db" not in g:
        database_dir = os.path.dirname(DATABASE)
        os.makedirs(database_dir, exist_ok=True)

        g.db = sqlite3.connect(DATABASE, timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 30000")

    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
